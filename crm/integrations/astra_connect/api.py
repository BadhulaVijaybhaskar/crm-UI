"""Whitelisted Astra Connect webhook endpoints.

Design (inbox + worker):
  receive()  — verify HMAC, INSERT durable inbox row (unique event_id), commit,
               enqueue worker, return 2xx accepted. Duplicate key → 200 duplicate
               with no other writes.
  worker     — claim via conditional UPDATE, upsert call log / note under unique
               indexes, commit data, then conditional status UPDATE. No GET_LOCK,
               no savepoints, never rewrite another request's inbox row.
"""

from __future__ import annotations

import json
import time
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
from crm.integrations.astra_connect.processing import (
	ProcessingError,
	get_connect_integration_user,
	process_event,
)

MAX_WORKER_ATTEMPTS = 5
WORKER_PATH = "crm.integrations.astra_connect.api.process_inbox_event"


def _json_response(payload: dict[str, Any], status_code: int = 200):
	frappe.local.response["http_status_code"] = status_code
	frappe.local.response["type"] = "json"
	frappe.local.response["message"] = payload
	return payload


def _is_duplicate_key(exc: BaseException) -> bool:
	msg = str(exc).lower()
	if "duplicate" in msg or "1062" in msg:
		return True
	errno = getattr(exc, "errno", None)
	if errno is None and getattr(exc, "args", None):
		errno = exc.args[0]
	return errno == 1062 or isinstance(exc, frappe.DuplicateEntryError)


def _is_retryable_db(exc: BaseException) -> bool:
	msg = str(exc).lower()
	if "deadlock" in msg or "1213" in msg or "lock wait" in msg or "1205" in msg:
		return True
	if "1020" in msg or "record has changed" in msg:
		return True
	if _is_duplicate_key(exc):
		return True
	errno = getattr(exc, "errno", None)
	if errno is None and getattr(exc, "args", None):
		errno = exc.args[0]
	return errno in (1213, 1205, 1020, 1062)


def _enqueue_processing(event_name: str, event_id: str) -> None:
	"""Enqueue (or run sync in tests). job_id dedupes concurrent accepts of one delivery."""
	job_id = f"astra-connect-{event_id}"
	if getattr(frappe.flags, "in_test", False) or frappe.conf.get("astra_connect_sync_processing"):
		process_inbox_event(event_name)
		return
	frappe.enqueue(
		WORKER_PATH,
		event_name=event_name,
		queue="short",
		timeout=300,
		job_id=job_id,
		deduplicate=True,
		enqueue_after_commit=True,
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def receive() -> dict[str, Any]:
	"""Inbound Astra Connect webhook — durable inbox insert only, then enqueue.

	Headers:
	  X-Astra-Delivery (dedupe; Replay reuses it) — fallback X-Astra-Event-Id
	  X-Astra-Signature: ``sha256=<hex>`` (+ X-Astra-Timestamp) or ``t=<ts>,v1=<hex>``

	Status codes:
	  200/202 accepted (inbox durable; worker will process)
	  200 duplicate (unique delivery already stored)
	  400 malformed payload (final)
	  401 bad signature or stale timestamp (final)
	  503 webhook disabled
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

	event_id = (headers.get("event_id") or "").strip()
	event_type = (payload.get("type") or payload.get("event") or "").strip()
	if not event_id:
		return _json_response(
			{"status": "rejected", "error": _("Missing X-Astra-Delivery (or X-Astra-Event-Id)")},
			status_code=400,
		)
	if not event_type:
		return _json_response({"status": "rejected", "error": _("Missing event type")}, status_code=400)

	owner = get_connect_integration_user()
	prev_user = frappe.session.user
	try:
		frappe.set_user(owner)
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
				frappe.db.set_value(
					"Astra Connect Event", event.name, "owner", owner, update_modified=False
				)
			frappe.db.commit()
		except Exception as exc:
			frappe.db.rollback()
			if not _is_duplicate_key(exc):
				raise
			existing = frappe.db.get_value(
				"Astra Connect Event",
				{"event_id": event_id},
				["name", "status"],
				as_dict=True,
			)
			# Never rewrite another request's row — duplicate is terminal for this POST.
			return _json_response(
				{
					"status": "duplicate",
					"event_id": event_id,
					"name": existing.name if existing else None,
					"previous_status": existing.status if existing else None,
				},
				status_code=200,
			)

		_enqueue_processing(event.name, event_id)
		return _json_response(
			{
				"status": "accepted",
				"event_id": event_id,
				"name": event.name,
			},
			status_code=202,
		)
	finally:
		frappe.set_user(prev_user)


@frappe.whitelist()
def retry_event(event_id: str) -> dict[str, Any]:
	"""Admin-only re-enqueue of a Failed / Received Astra Connect Event."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Managers can retry Connect events"), frappe.PermissionError)

	row = frappe.db.get_value(
		"Astra Connect Event", {"event_id": event_id}, ["name", "status"], as_dict=True
	)
	if not row:
		frappe.throw(_("Event not found: {0}").format(event_id), frappe.DoesNotExistError)
	if row.status not in ("Failed", "Received"):
		frappe.throw(_("Only failed or received events can be retried"))

	# Reset to Received so the worker's claim UPDATE can take it.
	frappe.db.sql(
		"""
		UPDATE `tabAstra Connect Event`
		SET status = 'Received', error = '', modified = %s, modified_by = %s
		WHERE name = %s AND status IN ('Failed', 'Received')
		""",
		(now_datetime(), frappe.session.user, row.name),
	)
	frappe.db.commit()
	_enqueue_processing(row.name, event_id)
	return _json_response(
		{"status": "accepted", "event_id": event_id, "name": row.name},
		status_code=202,
	)


def process_inbox_event(event_name: str) -> dict[str, Any] | None:
	"""Background worker: claim one inbox row, upsert CRM docs, mark Processed/Failed.

	Claim is committed first so attempts stick. Data writes retry on deadlock /
	duplicate-key with a full rollback of the data transaction (claim stays
	Processing). Failed only after MAX_WORKER_ATTEMPTS; Failed stays redeliverable
	via retry_event (or a new delivery id).
	"""
	if not _claim_event(event_name):
		status = frappe.db.get_value("Astra Connect Event", event_name, "status")
		return {"status": "skipped", "event_status": status}
	frappe.db.commit()

	last_exc: BaseException | None = None
	for attempt in range(MAX_WORKER_ATTEMPTS):
		try:
			return _process_claimed_event(event_name)
		except ProcessingError as exc:
			frappe.db.rollback()
			_mark_event_status(event_name, "Failed", error=str(exc))
			frappe.db.commit()
			return {"status": "failed", "error": str(exc)}
		except Exception as exc:
			last_exc = exc
			frappe.db.rollback()
			if not _is_retryable_db(exc) or attempt >= MAX_WORKER_ATTEMPTS - 1:
				_mark_event_status(event_name, "Failed", error=frappe.get_traceback())
				frappe.db.commit()
				frappe.log_error(title="Astra Connect inbox worker failed")
				return {"status": "failed", "error": _("Internal processing error")}
			time.sleep(0.05 * (attempt + 1))

	if last_exc:
		_mark_event_status(event_name, "Failed", error=frappe.get_traceback())
		frappe.db.commit()
		raise last_exc
	return None


def _process_claimed_event(event_name: str) -> dict[str, Any]:
	event = frappe.get_doc("Astra Connect Event", event_name)
	owner = get_connect_integration_user()
	prev = frappe.session.user
	try:
		frappe.set_user(owner)
		result = process_event(event)
	finally:
		frappe.set_user(prev)

	frappe.db.commit()
	_mark_event_status(event_name, "Processed", clear_error=True)
	frappe.db.commit()
	return {"status": "processed", "result": result}


def _claim_event(event_name: str) -> bool:
	"""Conditional claim: only one worker proceeds (rowcount == 1)."""
	now = now_datetime()
	user = get_connect_integration_user()
	frappe.db.sql(
		"""
		UPDATE `tabAstra Connect Event`
		SET status = 'Processing',
			attempts = IFNULL(attempts, 0) + 1,
			error = '',
			modified = %s,
			modified_by = %s
		WHERE name = %s AND status IN ('Received', 'Failed')
		""",
		(now, user, event_name),
	)
	return int(frappe.db.sql("SELECT ROW_COUNT()")[0][0] or 0) == 1


def _mark_event_status(
	event_name: str,
	status: str,
	*,
	error: str | None = None,
	clear_error: bool = False,
) -> None:
	now = now_datetime()
	user = get_connect_integration_user()
	if status == "Processed":
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET status = 'Processed',
				error = '',
				processed_at = %s,
				modified = %s,
				modified_by = %s
			WHERE name = %s AND status = 'Processing'
			""",
			(now, now, user, event_name),
		)
	elif status == "Failed":
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET status = 'Failed',
				error = %s,
				modified = %s,
				modified_by = %s
			WHERE name = %s AND status IN ('Processing', 'Received', 'Failed')
			""",
			(error or "", now, user, event_name),
		)
	elif clear_error:
		frappe.db.set_value("Astra Connect Event", event_name, "error", "")
