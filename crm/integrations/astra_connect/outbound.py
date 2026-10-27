# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Signed outbound CRM → Astra Connect events (deal.stage_changed, lead.assigned)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import frappe
import requests
from frappe import _
from frappe.utils import cint, now_datetime

from crm.integrations.astra_connect.auth import get_webhook_secret, sign_payload


def connect_outbound_enabled() -> bool:
	if not frappe.db.exists("DocType", "Astra Connect Settings"):
		return False
	settings = frappe.get_cached_doc("Astra Connect Settings")
	if not cint(settings.enabled):
		return False
	if not (settings.connect_base_url or "").strip():
		return False
	return bool(get_webhook_secret())


def outbound_url() -> str | None:
	settings = frappe.get_cached_doc("Astra Connect Settings")
	base = (settings.connect_base_url or "").rstrip("/")
	if not base:
		return None
	return f"{base}/api/crm/events"


def on_deal_update(doc, method=None):
	if not connect_outbound_enabled():
		return
	if not doc.has_value_changed("status"):
		return
	enqueue_event(
		"deal.stage_changed",
		{
			"type": "deal.stage_changed",
			"dealId": doc.name,
			"stage": doc.status,
			"previousStage": doc.get_doc_before_save().status if doc.get_doc_before_save() else None,
			"organization": doc.organization,
			"dealOwner": doc.deal_owner,
		},
	)


def on_lead_update(doc, method=None):
	if not connect_outbound_enabled():
		return
	if not doc.has_value_changed("lead_owner"):
		return
	enqueue_event(
		"lead.assigned",
		{
			"type": "lead.assigned",
			"leadId": doc.name,
			"assignee": doc.lead_owner,
			"previousAssignee": doc.get_doc_before_save().lead_owner if doc.get_doc_before_save() else None,
		},
	)


def enqueue_event(event_type: str, payload: dict[str, Any]):
	delivery_id = f"out_{uuid.uuid4().hex}"
	event = frappe.get_doc(
		{
			"doctype": "Astra Connect Event",
			"event_id": delivery_id,
			"event_type": event_type,
			"payload": payload,
			"status": "Received",
			"attempts": 0,
		}
	)
	event.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.enqueue(
		"crm.integrations.astra_connect.outbound.deliver_event",
		queue="short",
		event_name=event.name,
		now=bool(getattr(frappe.flags, "in_test", False)),
	)
	# Fan-out to admin-configured CRM Outbound Webhook rows (CRM-25).
	frappe.enqueue(
		"crm.integrations.astra_connect.outbound.deliver_custom_webhooks",
		queue="short",
		event_type=event_type,
		payload=payload,
		delivery_id=delivery_id,
		now=bool(getattr(frappe.flags, "in_test", False)),
	)


def deliver_event(event_name: str, max_attempts: int = 3):
	doc = frappe.get_doc("Astra Connect Event", event_name)
	url = outbound_url()
	secret = get_webhook_secret()
	if not url or not secret:
		doc.status = "Failed"
		doc.error = "Outbound not configured"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return

	body = json.dumps(doc.payload or {}, separators=(",", ":"), default=str)
	raw = body.encode("utf-8")
	ts = int(time.time())
	sig = sign_payload(secret, ts, raw)
	headers = {
		"Content-Type": "application/json",
		"X-Astra-Delivery": doc.event_id,
		"X-Astra-Timestamp": str(ts),
		"X-Astra-Signature": f"sha256={sig}",
	}

	last_error = ""
	for attempt in range(1, max_attempts + 1):
		doc.attempts = attempt
		try:
			resp = requests.post(url, data=raw, headers=headers, timeout=15)
			if 200 <= resp.status_code < 300:
				doc.status = "Processed"
				doc.processed_at = now_datetime()
				doc.error = ""
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				return
			last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
			if resp.status_code < 500 and resp.status_code != 429:
				break  # permanent client error
		except Exception as exc:
			last_error = str(exc)
		frappe.db.commit()

	doc.status = "Failed"
	doc.error = last_error
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def deliver_custom_webhooks(event_type: str, payload: dict, delivery_id: str):
	"""POST to enabled CRM Outbound Webhook endpoints that subscribe to this event."""
	if not frappe.db.exists("DocType", "CRM Outbound Webhook"):
		return
	hooks = frappe.get_all(
		"CRM Outbound Webhook",
		filters={"enabled": 1},
		fields=["name", "endpoint_url", "events", "timeout_seconds"],
	)
	for hook in hooks:
		subscribed = {e.strip() for e in (hook.events or "").split(",") if e.strip()}
		if event_type not in subscribed and "*" not in subscribed:
			continue
		secret = None
		try:
			secret = frappe.get_doc("CRM Outbound Webhook", hook.name).get_password("secret")
		except Exception:
			secret = None
		body = json.dumps(payload or {}, separators=(",", ":"), default=str).encode("utf-8")
		ts = int(time.time())
		headers = {
			"Content-Type": "application/json",
			"X-Astra-Delivery": delivery_id,
			"X-Astra-Timestamp": str(ts),
		}
		if secret:
			headers["X-Astra-Signature"] = f"sha256={sign_payload(secret, ts, body)}"
		try:
			requests.post(
				hook.endpoint_url,
				data=body,
				headers=headers,
				timeout=int(hook.timeout_seconds or 15),
			)
		except Exception:
			frappe.log_error(title=f"CRM outbound webhook {hook.name}")


@frappe.whitelist()
def get_latest_call_summary(doctype: str, name: str):
	"""Latest Astra Connect call log for a Lead / Deal / Contact header chip."""
	if doctype not in ("CRM Lead", "CRM Deal", "Contact"):
		frappe.throw(_("Unsupported doctype"))
	frappe.has_permission(doctype, "read", name, throw=True)

	rows = frappe.get_all(
		"CRM Call Log",
		filters={"reference_doctype": doctype, "reference_docname": name},
		fields=["name", "outcome", "disposition", "qualified", "call_summary", "creation", "type", "duration"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not rows:
		# Fallback: match by phone on Lead/Deal/Contact
		phone = None
		if doctype == "CRM Lead":
			phone = frappe.db.get_value("CRM Lead", name, "mobile_no")
		elif doctype == "CRM Deal":
			phone = frappe.db.get_value("CRM Deal", name, "mobile_no")
		elif doctype == "Contact":
			phone = frappe.db.get_value("Contact", name, "mobile_no")
		if phone:
			rows = frappe.get_all(
				"CRM Call Log",
				filters={"to": phone},
				fields=[
					"name",
					"outcome",
					"disposition",
					"qualified",
					"call_summary",
					"creation",
					"type",
					"duration",
				],
				order_by="creation desc",
				limit_page_length=1,
			) or frappe.get_all(
				"CRM Call Log",
				filters={"from": phone},
				fields=[
					"name",
					"outcome",
					"disposition",
					"qualified",
					"call_summary",
					"creation",
					"type",
					"duration",
				],
				order_by="creation desc",
				limit_page_length=1,
			)
	return rows[0] if rows else None
