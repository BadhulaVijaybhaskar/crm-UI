"""Whitelisted Astra Connect webhook endpoints."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.integrations.astra_connect.auth import (
	WebhookAuthError,
	WebhookDisabledError,
	read_request_headers,
	require_webhook_secret,
	verify_signature,
)
from crm.integrations.astra_connect.processing import ProcessingError, process_event


def _json_response(payload: dict[str, Any], status_code: int = 200):
	frappe.local.response["http_status_code"] = status_code
	frappe.local.response["type"] = "json"
	frappe.local.response["message"] = payload
	return payload


@frappe.whitelist(allow_guest=True, methods=["POST"])
def receive() -> dict[str, Any]:
	"""Inbound Astra Connect webhook.

	Headers:
	  X-Astra-Event-Id, X-Astra-Timestamp (unix seconds),
	  X-Astra-Signature = hex HMAC-SHA256(secret, `${timestamp}.${raw_body}`)

	Secret: site_config key ``astra_connect_webhook_secret`` (disabled if missing).
	"""
	try:
		secret = require_webhook_secret()
	except WebhookDisabledError as exc:
		return _json_response({"status": "disabled", "error": str(exc)}, status_code=503)

	raw_body = frappe.request.get_data() or b""
	headers = read_request_headers()

	try:
		verify_signature(
			secret=secret,
			timestamp=headers.get("timestamp"),
			signature=headers.get("signature"),
			raw_body=raw_body,
		)
	except WebhookAuthError as exc:
		return _json_response({"status": "rejected", "error": str(exc)}, status_code=401)

	try:
		payload = json.loads(raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body)
		if not isinstance(payload, dict):
			raise ValueError("payload must be a JSON object")
	except Exception:
		return _json_response({"status": "rejected", "error": _("Invalid JSON body")}, status_code=400)

	event_id = (headers.get("event_id") or payload.get("event_id") or "").strip()
	event_type = (payload.get("type") or payload.get("event") or "").strip()
	if not event_id:
		return _json_response(
			{"status": "rejected", "error": _("Missing X-Astra-Event-Id")}, status_code=400
		)
	if not event_type:
		return _json_response({"status": "rejected", "error": _("Missing event type")}, status_code=400)

	# Idempotency: repeated event_id → 200 duplicate, no new records
	existing = frappe.db.get_value(
		"Astra Connect Event",
		{"event_id": event_id},
		["name", "status"],
		as_dict=True,
	)
	if existing:
		return _json_response(
			{
				"status": "duplicate",
				"event_id": event_id,
				"name": existing.name,
				"previous_status": existing.status,
			},
			status_code=200,
		)

	event = frappe.get_doc(
		{
			"doctype": "Astra Connect Event",
			"event_id": event_id,
			"event_type": event_type,
			"payload": payload,
			"status": "Received",
			"attempts": 0,
		}
	)
	event.insert(ignore_permissions=True)
	frappe.db.commit()

	return _finalize_event(event)


@frappe.whitelist()
def retry_event(event_id: str) -> dict[str, Any]:
	"""Admin-only reprocessing of a failed Astra Connect Event."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Managers can retry Connect events"), frappe.PermissionError)

	name = frappe.db.get_value("Astra Connect Event", {"event_id": event_id}, "name")
	if not name:
		frappe.throw(_("Event not found: {0}").format(event_id), frappe.DoesNotExistError)

	event = frappe.get_doc("Astra Connect Event", name)
	if event.status not in ("Failed", "Received"):
		frappe.throw(_("Only failed or received events can be retried"))

	return _finalize_event(event)


def _finalize_event(event) -> dict[str, Any]:
	event.attempts = int(event.attempts or 0) + 1
	try:
		result = process_event(event)
		event.status = "Processed"
		event.error = ""
		event.processed_at = now_datetime()
		event.save(ignore_permissions=True)
		frappe.db.commit()
		return _json_response(
			{
				"status": "processed",
				"event_id": event.event_id,
				"name": event.name,
				"result": result,
			}
		)
	except ProcessingError as exc:
		event.status = "Failed"
		event.error = str(exc)
		event.save(ignore_permissions=True)
		frappe.db.commit()
		return _json_response(
			{
				"status": "failed",
				"event_id": event.event_id,
				"name": event.name,
				"error": str(exc),
			},
			status_code=422,
		)
	except Exception:
		traceback = frappe.get_traceback()
		frappe.db.rollback()
		# Re-apply failure state after rollback
		frappe.db.set_value(
			"Astra Connect Event",
			event.name,
			{
				"status": "Failed",
				"error": traceback,
				"attempts": event.attempts,
			},
			update_modified=True,
		)
		frappe.db.commit()
		frappe.log_error(title="Astra Connect webhook processing failed")
		return _json_response(
			{
				"status": "failed",
				"event_id": event.event_id,
				"name": event.name,
				"error": _("Internal processing error"),
			},
			status_code=500,
		)
