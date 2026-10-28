"""Whitelisted Astra Connect webhook endpoints.

Design (inbox + worker):
  receive()  — verify HMAC, INSERT durable inbox row (unique event_id), commit,
               enqueue worker, return 2xx accepted. Duplicate key → 200 duplicate
               with no other writes.
  worker     — claim via conditional UPDATE, upsert call log / note under unique
               indexes, commit data, then conditional status UPDATE. No GET_LOCK,
               no savepoints, never rewrite another request's inbox row.
  sweeper    — DB row is source of truth: reclaim stale Processing and orphaned
               Received rows; always re-enqueue with a fresh job_id (RQ job
               records must not block recovery).
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, get_datetime, now_datetime

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

MAX_WORKER_ATTEMPTS = 8
CONNECT_QUEUE = "astra_connect"
FALLBACK_QUEUE = "default"
WORKER_PATH = "crm.integrations.astra_connect.api.process_inbox_event"
DEFAULT_STALE_MINUTES = 5
# Reject oversized bodies before HMAC work (DoS / CPU on signature verify).
MAX_WEBHOOK_BODY_BYTES = 256 * 1024


def _webhook_body_too_large() -> bool:
	"""True when Content-Length exceeds the webhook body cap (before reading body)."""
	try:
		request = frappe.request
		cl = request.headers.get("Content-Length") if request is not None else None
		if cl is None or cl == "":
			return False
		return int(cl) > MAX_WEBHOOK_BODY_BYTES
	except (TypeError, ValueError, AttributeError):
		return False


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


def _logger():
	return frappe.logger("astra_connect")


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


def _stale_processing_minutes() -> int:
	conf = frappe.conf.get("astra_connect_stale_processing_minutes")
	if conf is not None and str(conf).strip() != "":
		try:
			return max(1, int(conf))
		except (TypeError, ValueError):
			pass
	try:
		configured = frappe.db.get_single_value("Astra Connect Settings", "stale_processing_minutes")
		if configured is not None:
			return max(1, int(configured))
	except Exception:
		pass
	return DEFAULT_STALE_MINUTES


def _extract_source_timestamp(payload: dict, signed_ts) -> Any:
	"""Prefer payload occurredAt/endedAt/createdAt; else signed request timestamp."""
	from datetime import datetime

	for key in (
		"occurredAt",
		"occurred_at",
		"endedAt",
		"ended_at",
		"createdAt",
		"created_at",
		"startedAt",
		"started_at",
	):
		raw = payload.get(key)
		if raw in (None, ""):
			continue
		dt = get_datetime(raw)
		if dt is not None:
			tzinfo = getattr(dt, "tzinfo", None)
			return dt.replace(tzinfo=None) if tzinfo is not None else dt
	if signed_ts in (None, ""):
		return None
	try:
		return datetime.utcfromtimestamp(int(signed_ts))
	except Exception:
		try:
			dt = get_datetime(signed_ts)
			if dt is not None:
				tzinfo = getattr(dt, "tzinfo", None)
				return dt.replace(tzinfo=None) if tzinfo is not None else dt
		except Exception:
			return None
		return None


def _configured_queue_names() -> set[str]:
	"""Queue names known to this site (workers.* / get_queues_timeout)."""
	names: set[str] = {"default", "short", "long"}
	workers = frappe.conf.get("workers")
	if isinstance(workers, dict):
		names.update(str(k) for k in workers.keys())
	try:
		from frappe.utils.background_jobs import get_queues_timeout

		names.update(str(k) for k in (get_queues_timeout() or {}).keys())
	except Exception:
		pass
	return names


def _resolve_connect_queue() -> str:
	"""Prefer ``astra_connect`` when configured; otherwise fall back to default."""
	if CONNECT_QUEUE in _configured_queue_names():
		return CONNECT_QUEUE
	return FALLBACK_QUEUE


def _fresh_job_id(event_id: str, attempts: int | None = None) -> str:
	"""Unique RQ job id per enqueue attempt — never blocked by a stuck 'started' record."""
	attempt = int(attempts or 0)
	nonce = frappe.generate_hash(length=10)
	return f"astra-connect-{event_id}:{attempt}:{nonce}"


def _enqueue_processing(event_name: str, event_id: str, *, attempts: int | None = None) -> str | None:
	"""Enqueue (or run sync in tests). Always uses a fresh job_id; never deduplicate.

	The DB inbox row + conditional claim UPDATE are the source of truth. A stale RQ
	job left in ``started`` after SIGKILL must not prevent recovery.
	"""
	if attempts is None:
		try:
			attempts = int(
				frappe.db.get_value("Astra Connect Event", event_name, "attempts") or 0
			)
		except Exception:
			attempts = 0

	if getattr(frappe.flags, "in_test", False) or frappe.conf.get("astra_connect_sync_processing"):
		process_inbox_event(event_name)
		return None

	job_id = _fresh_job_id(event_id, attempts)
	queue = _resolve_connect_queue()
	kwargs = dict(
		event_name=event_name,
		queue=queue,
		timeout=300,
		job_id=job_id,
		deduplicate=False,
		enqueue_after_commit=True,
	)
	try:
		frappe.enqueue(WORKER_PATH, **kwargs)
		return job_id
	except Exception as exc:
		# Undeclared custom queue (or transient RQ error) — fall back to default.
		if queue != FALLBACK_QUEUE:
			_logger().warning(
				f"Astra Connect enqueue on '{queue}' failed ({exc}); falling back to '{FALLBACK_QUEUE}'"
			)
			kwargs["queue"] = FALLBACK_QUEUE
			kwargs["job_id"] = _fresh_job_id(event_id, attempts)
			frappe.enqueue(WORKER_PATH, **kwargs)
			return kwargs["job_id"]
		raise


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=120, seconds=60, ip_based=True)
def receive() -> dict[str, Any]:
	"""Inbound Astra Connect webhook — durable inbox insert only, then enqueue.

	Headers:
	  X-Astra-Delivery (dedupe; Replay reuses it) — fallback X-Astra-Event-Id
	  X-Astra-Signature: ``sha256=<hex>`` (+ X-Astra-Timestamp) or ``t=<ts>,v1=<hex>``

	Status codes:
	  200/202 accepted (inbox durable; worker will process)
	  200 duplicate (unique delivery already stored — including Failed redelivery)
	  400 malformed payload (final)
	  401 bad signature or stale timestamp (final)
	  413 body too large (final; checked before HMAC)
	  503 webhook disabled
	"""
	try:
		secret = require_webhook_secret()
	except WebhookDisabledError as exc:
		return _json_response({"status": "disabled", "error": str(exc)}, status_code=503)

	# Cap body size before reading / HMAC — Content-Length when present, else len(body).
	if _webhook_body_too_large():
		return _json_response(
			{"status": "rejected", "error": _("Payload too large")},
			status_code=413,
		)

	raw_body = frappe.request.get_data() or b""
	if len(raw_body) > MAX_WEBHOOK_BODY_BYTES:
		return _json_response(
			{"status": "rejected", "error": _("Payload too large")},
			status_code=413,
		)

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

	source_timestamp = _extract_source_timestamp(payload, headers.get("timestamp"))
	owner = get_connect_integration_user()
	prev_user = frappe.session.user
	try:
		frappe.set_user(owner)
		try:
			doc = {
				"doctype": "Astra Connect Event",
				"event_id": event_id,
				"event_type": event_type,
				"payload": payload,
				"status": "Received",
				"attempts": 0,
				"owner": owner,
			}
			if source_timestamp is not None and frappe.db.has_column(
				"Astra Connect Event", "source_timestamp"
			):
				doc["source_timestamp"] = source_timestamp
			event = frappe.get_doc(doc)
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
			# Never rewrite another request's row — Failed redelivery is also duplicate;
			# sweeper / retry_event own recovery.
			return _json_response(
				{
					"status": "duplicate",
					"event_id": event_id,
					"name": existing.name if existing else None,
					"previous_status": existing.status if existing else None,
				},
				status_code=200,
			)

		_enqueue_processing(event.name, event_id, attempts=0)
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


@frappe.whitelist(methods=["POST"])
def retry_event(event_id: str) -> dict[str, Any]:
	"""Admin-only re-enqueue of Failed / Received / stale Processing events."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Managers can retry Connect events"), frappe.PermissionError)

	fields = ["name", "status", "attempts"]
	if frappe.db.has_column("Astra Connect Event", "claimed_at"):
		fields.append("claimed_at")
	row = frappe.db.get_value(
		"Astra Connect Event", {"event_id": event_id}, fields, as_dict=True
	)
	if not row:
		frappe.throw(_("Event not found: {0}").format(event_id), frappe.DoesNotExistError)

	stale = row.status == "Processing" and _is_stale_processing(row)
	if row.status not in ("Failed", "Received") and not stale:
		frappe.throw(_("Only failed, received, or stale processing events can be retried"))

	minutes = _stale_processing_minutes()
	cutoff = add_to_date(now_datetime(), minutes=-minutes)
	now = now_datetime()
	user = frappe.session.user
	has_claimed = frappe.db.has_column("Astra Connect Event", "claimed_at")

	# Conditional UPDATE — do not clobber a fresh in-flight Processing claim.
	if has_claimed:
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET status = 'Received', error = '', claimed_at = NULL,
				modified = %s, modified_by = %s
			WHERE name = %s
			  AND (
				status IN ('Failed', 'Received')
				OR (
					status = 'Processing'
					AND (claimed_at IS NULL OR claimed_at <= %s)
				)
			  )
			""",
			(now, user, row.name, cutoff),
		)
	else:
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET status = 'Received', error = '',
				modified = %s, modified_by = %s
			WHERE name = %s
			  AND (
				status IN ('Failed', 'Received')
				OR (status = 'Processing' AND modified <= %s)
			  )
			""",
			(now, user, row.name, cutoff),
		)

	changed = int(frappe.db.sql("SELECT ROW_COUNT()")[0][0] or 0)
	frappe.db.commit()
	if changed == 0:
		# Raced a live worker — do not enqueue a duplicate claim.
		fresh = frappe.db.get_value(
			"Astra Connect Event", row.name, ["status", "attempts"], as_dict=True
		)
		return _json_response(
			{
				"status": "skipped",
				"event_id": event_id,
				"name": row.name,
				"event_status": fresh.status if fresh else None,
			},
			status_code=200,
		)

	attempts = int((row.attempts or 0))
	_enqueue_processing(row.name, event_id, attempts=attempts)
	return _json_response(
		{"status": "accepted", "event_id": event_id, "name": row.name},
		status_code=202,
	)


def _is_stale_processing(row) -> bool:
	minutes = _stale_processing_minutes()
	claimed_at = row.get("claimed_at") if hasattr(row, "get") else getattr(row, "claimed_at", None)
	if not claimed_at:
		return True
	cutoff = add_to_date(now_datetime(), minutes=-minutes)
	return get_datetime(claimed_at) <= get_datetime(cutoff)


def sweep_stale_processing() -> dict[str, Any]:
	"""Recover orphaned inbox rows: stale Processing + aged Received without a live job.

	DB rows are the source of truth. Always re-enqueues with a fresh job_id so a
	stuck RQ ``started`` record cannot block recovery. Scheduled every 2 minutes.
	"""
	if not frappe.db.exists("DocType", "Astra Connect Event"):
		return {"reset": 0, "reenqueued": 0}

	minutes = _stale_processing_minutes()
	cutoff = add_to_date(now_datetime(), minutes=-minutes)
	has_claimed = frappe.db.has_column("Astra Connect Event", "claimed_at")
	user = get_connect_integration_user()
	now = now_datetime()

	# 1) Stale Processing → Received (conditional), then enqueue.
	if has_claimed:
		processing_rows = frappe.db.sql(
			"""
			SELECT name, event_id, attempts, claimed_at, modified
			FROM `tabAstra Connect Event`
			WHERE status = 'Processing'
			  AND (claimed_at IS NULL OR claimed_at <= %s)
			""",
			(cutoff,),
			as_dict=True,
		)
	else:
		processing_rows = frappe.db.sql(
			"""
			SELECT name, event_id, attempts, modified
			FROM `tabAstra Connect Event`
			WHERE status = 'Processing' AND modified <= %s
			""",
			(cutoff,),
			as_dict=True,
		)

	reset = 0
	reenqueued = 0
	for row in processing_rows:
		if has_claimed:
			frappe.db.sql(
				"""
				UPDATE `tabAstra Connect Event`
				SET status = 'Received',
					error = %s,
					claimed_at = NULL,
					modified = %s,
					modified_by = %s
				WHERE name = %s AND status = 'Processing'
				  AND (claimed_at IS NULL OR claimed_at <= %s)
				""",
				(
					_("Reset by Connect sweeper after stale Processing"),
					now,
					user,
					row.name,
					cutoff,
				),
			)
		else:
			frappe.db.sql(
				"""
				UPDATE `tabAstra Connect Event`
				SET status = 'Received',
					error = %s,
					modified = %s,
					modified_by = %s
				WHERE name = %s AND status = 'Processing' AND modified <= %s
				""",
				(
					_("Reset by Connect sweeper after stale Processing"),
					now,
					user,
					row.name,
					cutoff,
				),
			)
		if int(frappe.db.sql("SELECT ROW_COUNT()")[0][0] or 0) != 1:
			continue
		frappe.db.commit()
		_enqueue_processing(row.name, row.event_id, attempts=int(row.attempts or 0))
		reset += 1
		reenqueued += 1

	# 2) Orphaned Received (enqueue never ran / undeclared queue / skipped RQ job).
	received_rows = frappe.db.sql(
		"""
		SELECT name, event_id, attempts, modified
		FROM `tabAstra Connect Event`
		WHERE status = 'Received' AND modified <= %s
		""",
		(cutoff,),
		as_dict=True,
	)
	for row in received_rows:
		# Touch modified so we do not tight-loop the same row every sweep if enqueue
		# keeps failing hard; still uses a fresh job_id each time.
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET error = %s, modified = %s, modified_by = %s
			WHERE name = %s AND status = 'Received'
			""",
			(
				_("Re-enqueued by Connect sweeper (orphaned Received)"),
				now_datetime(),
				user,
				row.name,
			),
		)
		if int(frappe.db.sql("SELECT ROW_COUNT()")[0][0] or 0) != 1:
			continue
		frappe.db.commit()
		_enqueue_processing(row.name, row.event_id, attempts=int(row.attempts or 0))
		reenqueued += 1

	return {"reset": reset, "reenqueued": reenqueued, "stale_minutes": minutes}


def process_inbox_event(event_name: str) -> dict[str, Any] | None:
	"""Background worker: claim one inbox row, upsert CRM docs, mark Processed/Failed.

	Claim is committed first so attempts / claimed_at stick. Data writes retry on
	deadlock / duplicate-key / 1020 with exponential backoff + jitter. After
	MAX_WORKER_ATTEMPTS the row becomes Failed so the sweeper / retry_event can
	recover it — never silently lost.
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
			retryable = _is_retryable_db(exc)
			if retryable:
				_logger().debug(
					f"Astra Connect retryable DB error on {event_name} "
					f"attempt={attempt + 1}/{MAX_WORKER_ATTEMPTS}: {exc}"
				)
			if not retryable or attempt >= MAX_WORKER_ATTEMPTS - 1:
				_mark_event_status(event_name, "Failed", error=frappe.get_traceback())
				frappe.db.commit()
				frappe.log_error(title="Astra Connect inbox worker failed")
				return {"status": "failed", "error": _("Internal processing error")}
			# Exponential backoff with jitter — keep 1020 / deadlock noise out of Error Log.
			delay = (0.05 * (2**attempt)) + random.uniform(0, 0.08)
			time.sleep(delay)

	if last_exc:
		_mark_event_status(event_name, "Failed", error=frappe.get_traceback())
		frappe.db.commit()
		frappe.log_error(title="Astra Connect inbox worker failed")
		return {"status": "failed", "error": _("Internal processing error")}
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
	"""Conditional claim: only one worker proceeds (rowcount == 1). Sets claimed_at."""
	now = now_datetime()
	user = get_connect_integration_user()
	has_claimed = frappe.db.has_column("Astra Connect Event", "claimed_at")
	if has_claimed:
		frappe.db.sql(
			"""
			UPDATE `tabAstra Connect Event`
			SET status = 'Processing',
				attempts = IFNULL(attempts, 0) + 1,
				claimed_at = %s,
				error = '',
				modified = %s,
				modified_by = %s
			WHERE name = %s AND status IN ('Received', 'Failed')
			""",
			(now, now, user, event_name),
		)
	else:
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
