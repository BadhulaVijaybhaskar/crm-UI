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

	# Claim the delivery id first (unique event_id). Concurrent senders: one INSERT
	# wins; others see duplicate and return 200 without reprocessing a success.
	claimed = _run_as_integration_user(lambda: _claim_delivery(event_id, event_type, payload))
	if claimed["status"] == "duplicate":
		return _json_response(
			{
				"status": "duplicate",
				"event_id": event_id,
				"name": claimed["name"],
				"previous_status": claimed.get("previous_status"),
			},
			status_code=200,
		)

	event = frappe.get_doc("Astra Connect Event", claimed["name"])
	return _finalize_event(event)


def _is_retryable_event_save(exc: BaseException) -> bool:
	msg = str(exc).lower()
	if "deadlock" in msg or "1213" in msg or "lock wait" in msg or "1205" in msg:
		return True
	if "1020" in msg or "record has changed" in msg:
		return True
	errno = getattr(exc, "errno", None)
	if errno is None and getattr(exc, "args", None):
		errno = exc.args[0]
	return errno in (1213, 1205, 1020)


def _claim_delivery(event_id: str, event_type: str, payload: dict) -> dict[str, Any]:
	"""Insert-or-lock the Astra Connect Event for this X-Astra-Delivery.

	Returns ``{"status": "claimed"|"retry"|"duplicate", "name": ...}``.
	"""
	import time as _time

	owner = get_connect_integration_user()

	# Fast path: unique INSERT claims the delivery.
	try:
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
		return {"status": "claimed", "name": event.name}
	except Exception as exc:
		msg = str(exc).lower()
		if "duplicate" not in msg and "1062" not in msg and not isinstance(exc, frappe.DuplicateEntryError):
			raise
		frappe.db.rollback()

	# Another worker holds/held the row — lock it and decide.
	for attempt in range(5):
		try:
			rows = frappe.db.sql(
				"""
				SELECT name, status FROM `tabAstra Connect Event`
				WHERE event_id = %s
				FOR UPDATE
				""",
				(event_id,),
				as_dict=True,
			)
			if not rows:
				# Lost the race mid-delete; retry insert once more next loop.
				frappe.db.rollback()
				_time.sleep(0.02 * (attempt + 1))
				continue

			row = rows[0]
			if row.status in ("Failed", "Received"):
				event = frappe.get_doc("Astra Connect Event", row.name)
				event.event_type = event_type or event.event_type
				event.payload = payload
				event.status = "Received"
				event.error = ""
				event.save(ignore_permissions=True)
				frappe.db.commit()
				return {"status": "retry", "name": event.name}

			frappe.db.commit()
			return {
				"status": "duplicate",
				"name": row.name,
				"previous_status": row.status,
			}
		except Exception as exc:
			if not _is_retryable_event_save(exc):
				raise
			frappe.db.rollback()
			_time.sleep(0.05 * (attempt + 1))

	frappe.throw(_("Could not claim Connect delivery"))


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


def _save_event_with_retry(event) -> None:
	"""Persist event status; retry MariaDB 1020 / deadlock on concurrent writers."""
	import time as _time

	last_exc = None
	for attempt in range(5):
		try:
			event.save(ignore_permissions=True)
			frappe.db.commit()
			return
		except Exception as exc:
			last_exc = exc
			if not _is_retryable_event_save(exc):
				raise
			frappe.db.rollback()
			# Reload so we don't write a stale timestamp against a changed row.
			fresh = frappe.get_doc("Astra Connect Event", event.name)
			fresh.status = event.status
			fresh.error = event.error
			fresh.attempts = event.attempts
			fresh.processed_at = event.processed_at
			fresh.payload = event.payload
			fresh.event_type = event.event_type
			event = fresh
			_time.sleep(0.05 * (attempt + 1))
	raise last_exc


def _finalize_event(event) -> dict[str, Any]:
	# Serialise concurrent senders of the same X-Astra-Delivery.
	lock_name = f"astra_evt_{(event.event_id or '')[:48]}"
	got_lock = False
	try:
		got_lock = bool(frappe.db.sql("SELECT GET_LOCK(%s, %s)", (lock_name, 30))[0][0])
	except Exception:
		got_lock = False

	try:
		event.reload()
		if event.status == "Processed":
			return _json_response(
				{
					"status": "duplicate",
					"event_id": event.event_id,
					"name": event.name,
					"previous_status": event.status,
				},
				status_code=200,
			)

		event.attempts = int(event.attempts or 0) + 1

		def _process():
			return process_event(event)

		try:
			result = _run_as_integration_user(_process)
			event.status = "Processed"
			event.error = ""
			event.processed_at = now_datetime()
			_save_event_with_retry(event)
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
			_save_event_with_retry(event)
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
			try:
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
			except Exception as save_exc:
				if _is_retryable_event_save(save_exc):
					frappe.db.rollback()
					for attempt in range(4):
						try:
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
							break
						except Exception:
							frappe.db.rollback()
							import time as _time

							_time.sleep(0.05 * (attempt + 1))
				else:
					raise
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
	finally:
		if got_lock:
			try:
				frappe.db.sql("SELECT RELEASE_LOCK(%s)", (lock_name,))
			except Exception:
				pass
