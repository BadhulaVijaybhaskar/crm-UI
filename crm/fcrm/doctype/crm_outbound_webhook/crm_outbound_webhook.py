# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""CRM Outbound Webhooks — signed HTTPS callbacks, independent of Astra Connect."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import cint

from crm.integrations.astra_connect.auth import sign_payload

SUPPORTED_EVENTS = (
	"lead.created",
	"lead.updated",
	"deal.created",
	"deal.updated",
	"deal.stage_changed",
	"contact.created",
	"contact.updated",
)


class CRMOutboundWebhook(Document):
	def validate(self):
		events = _normalize_events(self.events)
		if not events:
			frappe.throw(frappe._("Select at least one event"))
		unknown = [e for e in events if e not in SUPPORTED_EVENTS and e != "*"]
		if unknown:
			frappe.throw(frappe._("Unknown events: {0}").format(", ".join(unknown)))
		self.events = ",".join(events)
		if self.endpoint_url and not str(self.endpoint_url).startswith(("http://", "https://")):
			frappe.throw(frappe._("Endpoint URL must start with http:// or https://"))


def _normalize_events(raw) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, (list, tuple)):
		parts = [str(x).strip() for x in raw]
	else:
		parts = [p.strip() for p in str(raw).replace("\n", ",").split(",")]
	return [p for p in parts if p]


@frappe.whitelist()
def list_outbound_webhooks():
	frappe.only_for("System Manager")
	return frappe.get_all(
		"CRM Outbound Webhook",
		fields=["name", "title", "enabled", "endpoint_url", "events", "modified"],
		order_by="modified desc",
	)


@frappe.whitelist()
def save_outbound_webhook(
	title: str,
	endpoint_url: str,
	events: str | list | None = None,
	secret: str | None = None,
	enabled: int | None = 1,
	name: str | None = None,
	timeout_seconds: int | None = 15,
):
	"""Create or update a CRM Outbound Webhook from Settings."""
	frappe.only_for("System Manager")
	events_list = _normalize_events(events)
	if not title or not str(title).strip():
		frappe.throw(frappe._("Title is required"))
	if not endpoint_url or not str(endpoint_url).strip():
		frappe.throw(frappe._("Endpoint URL is required"))
	if not events_list:
		frappe.throw(frappe._("Select at least one event"))

	if name and frappe.db.exists("CRM Outbound Webhook", name):
		doc = frappe.get_doc("CRM Outbound Webhook", name)
		doc.title = title.strip()
		doc.endpoint_url = endpoint_url.strip()
		doc.events = ",".join(events_list)
		doc.enabled = cint(enabled)
		doc.timeout_seconds = int(timeout_seconds or 15)
		if secret:
			doc.secret = secret
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "CRM Outbound Webhook",
				"title": title.strip(),
				"endpoint_url": endpoint_url.strip(),
				"events": ",".join(events_list),
				"enabled": cint(enabled),
				"timeout_seconds": int(timeout_seconds or 15),
				"secret": secret or "",
			}
		)
		doc.insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"title": doc.title,
		"enabled": doc.enabled,
		"endpoint_url": doc.endpoint_url,
		"events": doc.events,
	}


@frappe.whitelist()
def delete_outbound_webhook(name: str):
	frappe.only_for("System Manager")
	frappe.delete_doc("CRM Outbound Webhook", name, ignore_permissions=True)
	return {"name": name, "deleted": 1}


@frappe.whitelist()
def supported_outbound_events():
	frappe.only_for("System Manager")
	return list(SUPPORTED_EVENTS)


def emit_outbound_event(event_type: str, payload: dict[str, Any] | None = None):
	"""Fan-out to enabled CRM Outbound Webhook rows. Independent of Connect."""
	if not frappe.db.exists("DocType", "CRM Outbound Webhook"):
		return
	if not event_type:
		return
	body = dict(payload or {})
	body.setdefault("type", event_type)
	delivery_id = f"out_{uuid.uuid4().hex}"
	frappe.enqueue(
		"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.deliver_custom_webhooks",
		queue="short",
		event_type=event_type,
		payload=body,
		delivery_id=delivery_id,
		now=bool(getattr(frappe.flags, "in_test", False)),
	)


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


# --- Document event hooks (Connect-independent) ---


def on_lead_insert(doc, method=None):
	emit_outbound_event(
		"lead.created",
		{
			"type": "lead.created",
			"leadId": doc.name,
			"leadOwner": doc.lead_owner,
			"status": doc.status,
			"organization": doc.organization,
			"email": doc.email,
			"mobileNo": doc.mobile_no,
		},
	)


def on_lead_update(doc, method=None):
	emit_outbound_event(
		"lead.updated",
		{
			"type": "lead.updated",
			"leadId": doc.name,
			"leadOwner": doc.lead_owner,
			"status": doc.status,
			"organization": doc.organization,
		},
	)


def on_deal_insert(doc, method=None):
	emit_outbound_event(
		"deal.created",
		{
			"type": "deal.created",
			"dealId": doc.name,
			"dealOwner": doc.deal_owner,
			"stage": doc.status,
			"organization": doc.organization,
		},
	)


def on_deal_update(doc, method=None):
	emit_outbound_event(
		"deal.updated",
		{
			"type": "deal.updated",
			"dealId": doc.name,
			"dealOwner": doc.deal_owner,
			"stage": doc.status,
			"organization": doc.organization,
		},
	)
	if doc.has_value_changed("status"):
		prev = doc.get_doc_before_save()
		emit_outbound_event(
			"deal.stage_changed",
			{
				"type": "deal.stage_changed",
				"dealId": doc.name,
				"stage": doc.status,
				"previousStage": prev.status if prev else None,
				"organization": doc.organization,
				"dealOwner": doc.deal_owner,
			},
		)


def on_contact_insert(doc, method=None):
	emit_outbound_event(
		"contact.created",
		{
			"type": "contact.created",
			"contactId": doc.name,
			"fullName": doc.full_name or doc.first_name,
			"email": doc.email_id,
			"mobileNo": doc.mobile_no,
		},
	)


def on_contact_update(doc, method=None):
	emit_outbound_event(
		"contact.updated",
		{
			"type": "contact.updated",
			"contactId": doc.name,
			"fullName": doc.full_name or doc.first_name,
			"email": doc.email_id,
			"mobileNo": doc.mobile_no,
		},
	)
