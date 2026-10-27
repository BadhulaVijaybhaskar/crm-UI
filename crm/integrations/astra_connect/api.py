"""Whitelisted Astra Connect webhook endpoints."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime

from crm.integrations.astra_connect.auth import (
	WebhookAuthError,
	WebhookDisabledError,
	read_request_headers,
	require_webhook_secret,
	verify_signature,
)
from crm.integrations.astra_connect.processing import (
	ProcessingError,
	get_connect_integration_user,
	process_event,
)
from crm.utils.sanitize import sanitize_text


def _json_response(payload: dict[str, Any], status_code: int = 200):
	frappe.local.response["http_status_code"] = status_code
	frappe.local.response["type"] = "json"
	frappe.local.response["message"] = payload
	return payload


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Strip HTML/script from inbound webhook string fields before persistence."""

	def walk(value):
		if isinstance(value, str):
			return sanitize_text(value, max_length=4000)
		if isinstance(value, list):
			return [walk(v) for v in value]
		if isinstance(value, dict):
			return {k: walk(v) for k, v in value.items()}
		return value

	return walk(payload)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60, ip_based=True)
def receive() -> dict[str, Any]:
	"""Inbound Astra Connect webhook.

	Headers:
	  X-Astra-Delivery (dedupe; Replay reuses it) — fallback X-Astra-Event-Id
	  X-Astra-Signature: ``sha256=<hex>`` (+ X-Astra-Timestamp) or ``t=<ts>,v1=<hex>``

	Secret: site_config ``astra_connect_webhook_secret`` (disabled / 503 if missing).

	Status codes:
	  2xx success or duplicate (and business failures recorded as Failed)
	  400 malformed payload (final)
	  401 bad signature or stale timestamp (final)
	  5xx / 429 transient only (Connect outbox retries)
	"""
	try:
		secret = require_webhook_secret()
	except WebhookDisabledError as exc:
		# Transient from Connect's POV — site may be configured later.
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

	# Signature already bound this body to the per-site secret (frappe.conf).
	# Sanitise string fields so notes/summaries cannot carry script markup.
	payload = _sanitize_payload(payload)

	event_id = (headers.get("event_id") or "").strip()
	event_type = (payload.get("type") or payload.get("event") or "").strip()
	if not event_id:
		return _json_response(
			{"status": "rejected", "error": _("Missing X-Astra-Delivery (or X-Astra-Event-Id)")},
			status_code=400,
		)
	if not event_type:
		return _json_response({"status": "rejected", "error": _("Missing event type")}, status_code=400)

	# Idempotency on Delivery id → 200 duplicate only when prior attempt succeeded.
	# Failed / Received rows must stay retryable (Connect replays the same delivery id).
	existing = frappe.db.get_value(
		"Astra Connect Event",
		{"event_id": event_id},
		["name", "status"],
		as_dict=True,
	)
	if existing:
		if existing.status in ("Failed", "Received"):
			def _reuse_failed():
				event = frappe.get_doc("Astra Connect Event", existing.name)
				event.event_type = event_type or event.event_type
				event.payload = payload
				event.status = "Received"
				event.error = ""
				event.save(ignore_permissions=True)
				frappe.db.commit()
				return event

			event = _run_as_integration_user(_reuse_failed)
			return _finalize_event(event)
		return _json_response(
			{
				"status": "duplicate",
				"event_id": event_id,
				"name": existing.name,
				"previous_status": existing.status,
			},
			status_code=200,
		)

	def _create_event():
		owner = get_connect_integration_user()
		event = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": event_id,
				"event_type": event_type,
				"payload": payload,
				"status": "Received",
				"attempts": 0,
				"owner": owner,
			}
		)
		event.insert(ignore_permissions=True)
		if event.owner != owner:
			event.db_set("owner", owner, update_modified=False)
		frappe.db.commit()
		return event

	# Keep sync path fast (<10s). Event + processing run as integration user (not Guest).
	event = _run_as_integration_user(_create_event)
	return _finalize_event(event)


def _run_as_integration_user(fn):
	"""Guest webhooks must not leave owner=Guest on created docs."""
	prev = frappe.session.user
	try:
		frappe.set_user(get_connect_integration_user())
		return fn()
	finally:
		frappe.set_user(prev)


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

	def _process():
		return process_event(event)

	try:
		result = _run_as_integration_user(_process)
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
			},
			status_code=200,
		)
	except ProcessingError as exc:
		# Business failure is final for Connect's outbox — acknowledge with 2xx.
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
			status_code=200,
		)
	except Exception:
		# Transient — Connect should retry (5xx). Keep status Failed so the same
		# X-Astra-Delivery can be reprocessed (not counted as a successful duplicate).
		traceback = frappe.get_traceback()
		frappe.db.rollback()
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
