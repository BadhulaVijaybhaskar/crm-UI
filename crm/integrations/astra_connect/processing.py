"""Process Astra Connect webhook event payloads into CRM documents."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from crm.integrations.astra_connect.mapping import (
	map_disposition,
	map_lead_status,
	store_outcome,
)
from crm.utils import normalize_phone

# Connect today + draft aliases (kept for compatibility with earlier CRM-04 docs).
PRIMARY_EVENTS = ("lead.created", "call.completed", "employee.call.completed")
ALIAS_EVENTS = {
	"lead.upsert": "lead.created",
	"call.outcome": "call.completed",
}
SUPPORTED_EVENTS = PRIMARY_EVENTS + tuple(ALIAS_EVENTS.keys())
TELEPHONY_MEDIUM = "Astra Connect"
# Connect payloads normalize phones with IN as the default region.
CONNECT_PHONE_REGION = "IN"
# Valid E.164 placeholder for the Connect agent leg — never put non-phone strings
# like "astra-connect" / "unknown" into CRM Call Log Phone fields.
# No fake placeholder number — unset Connect line leaves the agent side blank.
DEFAULT_AGENT_NUMBER = None


class ProcessingError(frappe.ValidationError):
	"""Business / data error — acknowledge with 2xx; do not ask Connect to retry."""

	pass


def process_event(event_doc) -> dict[str, Any]:
	"""Dispatch a stored Astra Connect Event. Raises ProcessingError on failure."""
	payload = _as_dict(event_doc.payload)
	raw_type = (event_doc.event_type or payload.get("type") or payload.get("event") or "").strip()
	event_type = ALIAS_EVENTS.get(raw_type, raw_type)
	data = _event_data(payload)

	if event_type == "lead.created":
		return process_lead_created(data)
	if event_type in ("call.completed", "employee.call.completed"):
		return process_call_completed(data, employee_enriched=(event_type == "employee.call.completed"))
	raise ProcessingError(_("Unsupported event type: {0}").format(raw_type or "-"))


def process_lead_created(data: dict) -> dict[str, Any]:
	"""Upsert CRM Lead keyed on leadId → astra_external_id (alias: lead.upsert)."""
	external_id = _first_str(data, "leadId", "lead_id", "external_id")
	phone = _normalize_connect_phone(data.get("phone"))
	email = _first_str(data, "email") or None
	name = _first_str(data, "name")
	source = _first_str(data, "source") or "Astra Connect"
	ai_employee_id = _first_str(data, "employeeId", "employee_id", "ai_employee_id") or None
	connect_status = _first_str(data, "status")
	channel = _normalize_channel(data.get("channel"))

	if not external_id and not phone and not email:
		raise ProcessingError(_("lead.created requires leadId, phone, or email"))

	lead_name = None
	if external_id:
		lead_name = _find_lead_by_external_id(external_id)

	created = False
	if lead_name:
		lead = frappe.get_doc("CRM Lead", lead_name)
	else:
		lead = frappe.new_doc("CRM Lead")
		created = True
		first, last = _split_name(name)
		lead.first_name = first or (name or "Connect Lead")
		if last:
			lead.last_name = last

	if external_id:
		lead.astra_external_id = external_id
	if phone:
		lead.mobile_no = phone
	if email:
		lead.email = email
	if source:
		_ensure_lead_source(source)
		lead.source = source
	if ai_employee_id:
		lead.ai_employee_id = ai_employee_id

	crm_status = map_lead_status(connect_status)
	if frappe.db.exists("CRM Lead Status", crm_status):
		lead.status = crm_status

	owner = get_connect_integration_user()
	if created:
		lead.lead_owner = owner
		lead.owner = owner

	lead.flags.ignore_permissions = True
	if created:
		lead.insert(ignore_permissions=True)
	else:
		lead.save(ignore_permissions=True)

	return {
		"action": "created" if created else "updated",
		"doctype": "CRM Lead",
		"name": lead.name,
		"channel": channel,
		"mapped_status": crm_status,
	}


def process_call_completed(data: dict, *, employee_enriched: bool = False) -> dict[str, Any]:
	"""Create/update CRM Call Log from call.completed / employee.call.completed.

	Matching is by phone (contactId is Connect's id — not a CRM leadId). Ambiguous
	phone matches fail the event with a clear error.

	Deadlock retry wraps the whole unit of work — a mid-flight rollback must not
	leave a half-saved call log that then fails DoesNotExistError on retry.
	"""
	import time as _time

	last_exc = None
	for attempt in range(3):
		try:
			return _process_call_completed_once(data, employee_enriched=employee_enriched)
		except Exception as exc:
			last_exc = exc
			msg = str(exc).lower()
			if "deadlock" not in msg and "1213" not in msg and "lock wait" not in msg:
				raise
			frappe.db.rollback()
			_time.sleep(0.05 * (attempt + 1))
	raise last_exc


def _process_call_completed_once(data: dict, *, employee_enriched: bool = False) -> dict[str, Any]:
	"""Single attempt of call.completed processing (may raise on deadlock)."""
	call_id = _first_str(data, "callId", "call_id")
	if not call_id:
		raise ProcessingError(_("call.completed requires callId"))

	phone = _normalize_connect_phone(data.get("phone"))
	contact_id = _first_str(data, "contactId", "contact_id") or None
	direction = _map_direction(data.get("direction"))
	outcome_raw = store_outcome(_first_str(data, "outcome"))
	disposition = map_disposition(outcome_raw)
	qualified = _as_bool(data.get("qualified"))
	summary = _first_str(data, "summary") or None
	ai_employee_id = _first_str(data, "employeeId", "employee_id", "ai_employee_id") or None
	channel = _normalize_channel(data.get("channel"))
	ended_at = data.get("endedAt") or data.get("ended_at")
	fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}

	# employee.call.completed extras
	started_at = data.get("startedAt") or data.get("started_at")
	duration_s = _as_int(data.get("durationSec") if data.get("durationSec") is not None else data.get("duration_s"))
	end_reason = _first_str(data, "endReason", "end_reason", "status")
	recording_url = _first_str(data, "recordingUrl", "recording_url") or None
	transcript = data.get("transcript")

	# Optional next action (not sent by Connect yet)
	next_action = _first_str(data, "nextAction", "next_action") or None
	next_action_at = data.get("nextActionAt") or data.get("next_action_at")
	# Old draft nested shape
	if not next_action and isinstance(data.get("next_action"), dict):
		nested = data["next_action"]
		next_action = _first_str(nested, "title", "action") or None
		next_action_at = nested.get("due_at") or next_action_at

	match = resolve_party_by_phone(phone)
	if not match:
		raise ProcessingError(
			_("No matching lead or contact for call.completed (phone={0}, contactId={1})").format(
				phone or "-", contact_id or "-"
			)
		)

	status = _map_call_status(end_reason) if end_reason else "Completed"
	from_number, to_number = _call_numbers(direction, phone, data)
	if not from_number or not to_number:
		raise ProcessingError(_("call.completed requires a valid party phone number"))

	if frappe.db.exists("CRM Call Log", call_id):
		call_log = frappe.get_doc("CRM Call Log", call_id)
	else:
		call_log = frappe.new_doc("CRM Call Log")
		call_log.id = call_id

	owner = get_connect_integration_user()
	call_log.owner = owner
	call_log.type = direction
	call_log.status = status
	call_log.telephony_medium = TELEPHONY_MEDIUM
	call_log.medium = channel or TELEPHONY_MEDIUM
	if duration_s:
		call_log.duration = duration_s
	start_dt = _naive_site_datetime(started_at)
	end_dt = _naive_site_datetime(ended_at)
	if start_dt:
		call_log.start_time = start_dt
	elif end_dt and duration_s:
		call_log.end_time = end_dt
		call_log.start_time = add_to_date(end_dt, seconds=-duration_s)
	elif end_dt:
		call_log.end_time = end_dt
		call_log.start_time = end_dt
	else:
		call_log.start_time = call_log.start_time or now_datetime()
	if duration_s and call_log.start_time and not call_log.end_time:
		call_log.end_time = add_to_date(call_log.start_time, seconds=duration_s)
	elif end_dt and not call_log.end_time:
		call_log.end_time = end_dt

	call_log.set("from", from_number)
	call_log.to = to_number
	if recording_url:
		call_log.recording_url = recording_url

	# Store outcome as-is; disposition is the mapped label (default Other).
	call_log.outcome = outcome_raw
	call_log.disposition = disposition
	call_log.qualified = 1 if qualified else 0
	call_log.call_summary = _compose_summary(summary, fields)
	call_log.ai_employee_id = ai_employee_id
	call_log.channel = channel
	call_log.astra_contact_id = contact_id
	if transcript is not None:
		call_log.transcript = _format_transcript(transcript)

	call_log.reference_doctype = match["doctype"]
	call_log.reference_docname = match["name"]

	call_log.flags.ignore_permissions = True
	_save_call_log(call_log)

	call_log.link_with_reference_doc(match["doctype"], match["name"])
	if match.get("contact"):
		call_log.link_with_reference_doc("Contact", match["contact"])

	note_name = None
	if call_log.call_summary:
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": _("Call summary ({0})").format(call_id),
				"content": f"<p>{frappe.utils.escape_html(call_log.call_summary)}</p>",
				"reference_doctype": match["doctype"],
				"reference_docname": match["name"],
				"owner": owner,
			}
		).insert(ignore_permissions=True)
		note_name = note.name
		call_log.note = note.name
		call_log.link_with_reference_doc("FCRM Note", note.name)
		_save_call_log(call_log)

	task_name = None
	if next_action:
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": next_action,
				"description": call_log.call_summary or "",
				"status": "Todo",
				"priority": "Medium",
				"due_date": _naive_site_datetime(next_action_at) if next_action_at else None,
				"reference_doctype": match["doctype"],
				"reference_docname": match["name"],
				"owner": owner,
			}
		).insert(ignore_permissions=True)
		task_name = task.name
		call_log.link_with_reference_doc("CRM Task", task.name)
		_save_call_log(call_log)

	if ai_employee_id and match["doctype"] in ("CRM Lead", "CRM Deal"):
		frappe.db.set_value(match["doctype"], match["name"], "ai_employee_id", ai_employee_id)

	if qualified and match["doctype"] == "CRM Lead" and frappe.db.exists("CRM Lead Status", "Qualified"):
		# Document.save so CRM Status Change Log / validate hooks run
		from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
			set_status_with_history,
		)

		set_status_with_history("CRM Lead", match["name"], "Qualified", ignore_permissions=True)

	return {
		"doctype": "CRM Call Log",
		"name": call_log.name,
		"linked": match,
		"note": note_name,
		"task": task_name,
		"outcome": outcome_raw,
		"disposition": disposition,
		"channel": channel,
		"employee_enriched": employee_enriched,
	}


# Back-compat names used by older tests / callers
process_lead_upsert = process_lead_created
process_call_outcome = process_call_completed


def resolve_party_by_phone(phone: str) -> dict | None:
	"""Match Lead or Contact by full E.164, then last-10 digits. Ambiguous → fail."""
	if not phone:
		return None

	exact = _collect_phone_matches(phone, mode="e164")
	candidates = exact if exact else _collect_phone_matches(phone, mode="last10")

	if not candidates:
		return None
	if len(candidates) > 1:
		labels = ", ".join(f"{c['doctype']} {c['name']}" for c in candidates)
		raise ProcessingError(
			_("Ambiguous phone match for {0}: {1}").format(phone, labels)
		)
	return candidates[0]


def _collect_phone_matches(phone: str, *, mode: str) -> list[dict]:
	digits = "".join(ch for ch in phone if ch.isdigit())
	last10 = digits[-10:] if len(digits) >= 10 else digits
	if not last10:
		return []

	seen: set[tuple[str, str]] = set()
	out: list[dict] = []

	def add(doctype: str, name: str, **extra):
		key = (doctype, name)
		if key in seen:
			return
		seen.add(key)
		out.append({"doctype": doctype, "name": name, **extra})

	# Leads
	rows = frappe.get_all(
		"CRM Lead",
		filters={"converted": 0},
		or_filters=[
			["mobile_no", "like", f"%{last10}%"],
			["phone", "like", f"%{last10}%"],
		],
		fields=["name", "mobile_no", "phone"],
		limit=50,
	)
	for row in rows:
		if _phone_matches(phone, row.mobile_no, mode=mode) or _phone_matches(
			phone, row.phone, mode=mode
		):
			add("CRM Lead", row.name)

	# Contacts (primary mobile + Contact Phone child rows)
	contacts = frappe.get_all(
		"Contact",
		filters={"mobile_no": ("like", f"%{last10}%")},
		fields=["name", "mobile_no"],
		limit=50,
	)
	for row in contacts:
		if _phone_matches(phone, row.mobile_no, mode=mode):
			add("Contact", row.name, contact=row.name)

	phone_rows = frappe.get_all(
		"Contact Phone",
		filters={"phone": ("like", f"%{last10}%"), "parenttype": "Contact"},
		fields=["parent", "phone"],
		limit=50,
	)
	for row in phone_rows:
		if _phone_matches(phone, row.phone, mode=mode):
			add("Contact", row.parent, contact=row.parent)

	return out


def _phone_matches(target_e164: str, candidate: str | None, *, mode: str) -> bool:
	if not candidate:
		return False
	cand = normalize_phone(candidate, region=CONNECT_PHONE_REGION)
	if not cand:
		return False
	if mode == "e164":
		return cand == target_e164
	# last10
	t_digits = "".join(ch for ch in target_e164 if ch.isdigit())
	c_digits = "".join(ch for ch in cand if ch.isdigit())
	if len(t_digits) < 10 or len(c_digits) < 10:
		return t_digits == c_digits and bool(t_digits)
	return t_digits[-10:] == c_digits[-10:]


def _normalize_connect_phone(value) -> str:
	return normalize_phone(value, region=CONNECT_PHONE_REGION) if value else ""


def _find_lead_by_external_id(external_id: str) -> str | None:
	if not external_id or not frappe.db.has_column("CRM Lead", "astra_external_id"):
		return None
	return frappe.db.get_value("CRM Lead", {"astra_external_id": external_id}, "name")


def _split_name(name: str) -> tuple[str, str]:
	parts = (name or "").strip().split(None, 1)
	if not parts:
		return "", ""
	if len(parts) == 1:
		return parts[0], ""
	return parts[0], parts[1]


def _ensure_lead_source(source: str) -> None:
	if not source:
		return
	if frappe.db.exists("CRM Lead Source", source):
		return
	try:
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": source}).insert(
			ignore_permissions=True
		)
	except Exception:
		frappe.log_error(title="Astra Connect lead source ensure failed")


def _map_direction(value: str | None) -> str:
	v = (value or "").strip().lower()
	if v in ("inbound", "incoming", "in"):
		return "Incoming"
	return "Outgoing"


def _map_call_status(value: str | None) -> str:
	"""Accept both canceled (one L) and cancelled (two Ls)."""
	v = (value or "").strip().lower()
	mapping = {
		"completed": "Completed",
		"complete": "Completed",
		"answered": "Completed",
		"failed": "Failed",
		"busy": "Busy",
		"no_answer": "No Answer",
		"no-answer": "No Answer",
		"missed": "No Answer",
		"canceled": "Canceled",
		"cancelled": "Canceled",
		"queued": "Queued",
		"ringing": "Ringing",
		"in_progress": "In Progress",
		"initiated": "Initiated",
	}
	return mapping.get(v, "Completed")


def _save_call_log(call_log):
	"""Insert/save a call log. Deadlocks bubble to process_call_completed's outer retry."""
	if call_log.is_new():
		call_log.insert(ignore_permissions=True)
	else:
		call_log.save(ignore_permissions=True)
	return call_log


def get_connect_integration_user() -> str:
	"""User that owns webhook-created docs (never Guest)."""
	try:
		configured = frappe.db.get_single_value("Astra Connect Settings", "default_lead_owner")
		if configured and frappe.db.exists("User", configured):
			return configured
	except Exception:
		pass
	if frappe.session.user and frappe.session.user not in ("Guest", "Administrator"):
		# Prefer a real signed-in operator when present (manual retries).
		return frappe.session.user
	if frappe.db.exists("User", "Administrator"):
		return "Administrator"
	return frappe.session.user or "Administrator"


def _connect_agent_number() -> str | None:
	try:
		configured = frappe.db.get_single_value("Astra Connect Settings", "connect_agent_number")
		if configured and str(configured).strip():
			return str(configured).strip()
	except Exception:
		pass
	return DEFAULT_AGENT_NUMBER


def _naive_site_datetime(value):
	"""Parse ISO timestamps (incl. trailing Z) to naive datetimes in the site tz.

	MariaDB rejects tz-aware values (Incorrect datetime value). Connect sends
	``endedAt`` like ``2026-10-27T10:05:00Z``.
	"""
	if value in (None, ""):
		return None
	dt = get_datetime(value)
	if dt is None:
		return None
	tzinfo = getattr(dt, "tzinfo", None)
	if tzinfo is None:
		return dt
	try:
		from zoneinfo import ZoneInfo

		from frappe.utils import get_system_timezone

		local = dt.astimezone(ZoneInfo(get_system_timezone()))
		return local.replace(tzinfo=None)
	except Exception:
		return dt.replace(tzinfo=None)


def _agent_number_from_payload(data: dict | None, direction: str) -> str | None:
	"""Prefer an explicit agent/line number from the event over settings."""
	if not data:
		return None
	# Common Connect / employee payload keys for the agent leg.
	candidates = [
		_first_str(data, "agentPhone", "agent_phone", "agentNumber", "agent_number", "linePhone", "line_phone"),
	]
	# Directional from/to when the payload already split the legs.
	if direction == "Incoming":
		candidates.append(_first_str(data, "to", "toNumber", "to_number", "destination"))
	else:
		candidates.append(_first_str(data, "from", "fromNumber", "from_number", "source"))
	for raw in candidates:
		if not raw:
			continue
		normalized = _normalize_connect_phone(raw)
		if normalized:
			return normalized
	return None


def _call_numbers(
	direction: str, phone: str | None, data: dict | None = None
) -> tuple[str | None, str | None]:
	party_phone = (phone or "").strip() or None
	if not party_phone:
		party_phone = _normalize_connect_phone(phone) if phone else None
	if not party_phone:
		return None, None
	agent = _connect_agent_number() or _agent_number_from_payload(data, direction)
	# Required Phone fields on CRM Call Log — never invent a fake MSISDN. When no
	# Connect line / payload agent is available, put the party number on both legs.
	if not agent:
		agent = party_phone
	if direction == "Incoming":
		return party_phone, agent
	return agent, party_phone


def _normalize_channel(value) -> str | None:
	v = (str(value).strip().lower() if value is not None else "")
	if v in ("voice", "whatsapp"):
		return v
	return None


def _compose_summary(summary: str | None, fields: dict) -> str | None:
	parts = []
	if summary:
		parts.append(summary)
	if fields:
		try:
			parts.append(json.dumps(fields, ensure_ascii=False, sort_keys=True))
		except Exception:
			parts.append(str(fields))
	return "\n".join(parts) if parts else None


def _format_transcript(transcript) -> str:
	if isinstance(transcript, str):
		return transcript
	try:
		return json.dumps(transcript, ensure_ascii=False)
	except Exception:
		return str(transcript)


def _event_data(payload: dict) -> dict:
	"""Flat camelCase payloads are the Connect-today shape; nested data is the old draft."""
	if isinstance(payload.get("data"), dict):
		# Merge flat top-level keys under data for mixed senders
		merged = dict(payload)
		merged.update(payload["data"])
		return merged
	return payload


def _first_str(data: dict, *keys: str) -> str:
	for key in keys:
		val = data.get(key)
		if val is None:
			continue
		text = str(val).strip()
		if text:
			return text
	return ""


def _as_bool(value) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	if isinstance(value, str):
		return value.strip().lower() in ("1", "true", "yes", "y")
	return False


def _as_int(value) -> int:
	try:
		return int(value or 0)
	except (TypeError, ValueError):
		return 0


def _as_dict(value) -> dict:
	if value is None:
		return {}
	if isinstance(value, dict):
		return value
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
			return parsed if isinstance(parsed, dict) else {}
		except Exception:
			return {}
	return {}
