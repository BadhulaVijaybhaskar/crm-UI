"""Process Astra Connect webhook event payloads into CRM documents."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, now_datetime

from crm.integrations.api import find_contact_by_phone_number
from crm.utils import normalize_phone


SUPPORTED_EVENTS = ("lead.upsert", "call.outcome")
TELEPHONY_MEDIUM = "Astra Connect"


class ProcessingError(frappe.ValidationError):
	pass


def process_event(event_doc) -> dict[str, Any]:
	"""Dispatch a stored Astra Connect Event. Raises ProcessingError on failure."""
	payload = _as_dict(event_doc.payload)
	event_type = event_doc.event_type or payload.get("type") or payload.get("event")
	data = payload.get("data") if isinstance(payload.get("data"), dict) else payload

	if event_type == "lead.upsert":
		result = process_lead_upsert(data)
	elif event_type == "call.outcome":
		result = process_call_outcome(data)
	else:
		raise ProcessingError(_("Unsupported event type: {0}").format(event_type))

	return result


def process_lead_upsert(data: dict) -> dict[str, Any]:
	external_id = (data.get("external_id") or "").strip()
	phone = normalize_phone(data.get("phone"))
	email = (data.get("email") or "").strip() or None
	name = (data.get("name") or "").strip()
	company = (data.get("company") or "").strip() or None
	source = (data.get("source") or "Astra Connect").strip()
	ai_employee_id = (data.get("ai_employee_id") or "").strip() or None
	campaign_id = (data.get("campaign_id") or "").strip() or None

	if not external_id and not phone and not email:
		raise ProcessingError(_("lead.upsert requires external_id, phone, or email"))

	lead_name = _find_lead(external_id=external_id, phone=phone, email=email)
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
	if company:
		lead.organization = company
	if source:
		_ensure_lead_source(source)
		lead.source = source
	if ai_employee_id:
		lead.ai_employee_id = ai_employee_id
	if campaign_id and hasattr(lead, "campaign_id"):
		lead.campaign_id = campaign_id

	owner = frappe.db.get_single_value("Astra Connect Settings", "default_lead_owner")
	if created and owner:
		lead.lead_owner = owner

	lead.flags.ignore_permissions = True
	if created:
		lead.insert(ignore_permissions=True)
	else:
		lead.save(ignore_permissions=True)

	return {"action": "created" if created else "updated", "doctype": "CRM Lead", "name": lead.name}


def process_call_outcome(data: dict) -> dict[str, Any]:
	call_id = (data.get("call_id") or "").strip()
	if not call_id:
		raise ProcessingError(_("call.outcome requires call_id"))

	lead_external_id = (data.get("lead_external_id") or data.get("external_id") or "").strip()
	phone = normalize_phone(data.get("phone") or data.get("lead_phone"))
	email = (data.get("email") or "").strip() or None
	direction = _map_direction(data.get("direction"))
	started_at = data.get("started_at")
	duration_s = int(data.get("duration_s") or 0)
	status = _map_call_status(data.get("status"))
	disposition = (data.get("disposition") or "").strip() or None
	summary = (data.get("summary") or "").strip() or None
	transcript_url = (data.get("transcript_url") or "").strip() or None
	recording_url = (data.get("recording_url") or "").strip() or None
	ai_employee_id = (data.get("ai_employee_id") or "").strip() or None
	next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else None

	match = _resolve_party(
		lead_external_id=lead_external_id,
		phone=phone,
		email=email,
	)
	if not match:
		raise ProcessingError(
			_("No matching lead, deal, or contact for call.outcome (external_id={0}, phone={1})").format(
				lead_external_id or "-", phone or "-"
			)
		)

	from_number, to_number = _call_numbers(direction, phone, match)

	if frappe.db.exists("CRM Call Log", call_id):
		call_log = frappe.get_doc("CRM Call Log", call_id)
	else:
		call_log = frappe.new_doc("CRM Call Log")
		call_log.id = call_id

	call_log.type = direction
	call_log.status = status
	call_log.telephony_medium = TELEPHONY_MEDIUM
	call_log.medium = TELEPHONY_MEDIUM
	call_log.duration = duration_s
	call_log.start_time = get_datetime(started_at) if started_at else now_datetime()
	if duration_s:
		call_log.end_time = add_to_date(call_log.start_time, seconds=duration_s)
	call_log.set("from", from_number or "unknown")
	call_log.to = to_number or "unknown"
	if recording_url:
		call_log.recording_url = recording_url
	call_log.disposition = disposition
	call_log.call_summary = summary
	call_log.transcript_url = transcript_url
	call_log.ai_employee_id = ai_employee_id
	call_log.reference_doctype = match["doctype"]
	call_log.reference_docname = match["name"]

	call_log.flags.ignore_permissions = True
	if call_log.is_new():
		call_log.insert(ignore_permissions=True)
	else:
		call_log.save(ignore_permissions=True)

	# Link table
	call_log.link_with_reference_doc(match["doctype"], match["name"])
	if match.get("contact"):
		call_log.link_with_reference_doc("Contact", match["contact"])

	note_name = None
	if summary:
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": _("Call summary ({0})").format(call_id),
				"content": f"<p>{frappe.utils.escape_html(summary)}</p>",
				"reference_doctype": match["doctype"],
				"reference_docname": match["name"],
			}
		).insert(ignore_permissions=True)
		note_name = note.name
		call_log.note = note.name
		call_log.link_with_reference_doc("FCRM Note", note.name)
		call_log.save(ignore_permissions=True)

	task_name = None
	if next_action:
		title = (next_action.get("title") or next_action.get("action") or _("Follow up")).strip()
		due_at = next_action.get("due_at")
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": title,
				"description": next_action.get("description") or summary or "",
				"status": "Todo",
				"priority": next_action.get("priority") or "Medium",
				"due_date": get_datetime(due_at) if due_at else None,
				"reference_doctype": match["doctype"],
				"reference_docname": match["name"],
			}
		).insert(ignore_permissions=True)
		task_name = task.name
		call_log.link_with_reference_doc("CRM Task", task.name)
		call_log.save(ignore_permissions=True)

	# Propagate AI employee onto Lead/Deal when present
	if ai_employee_id and match["doctype"] in ("CRM Lead", "CRM Deal"):
		frappe.db.set_value(match["doctype"], match["name"], "ai_employee_id", ai_employee_id)

	return {
		"doctype": "CRM Call Log",
		"name": call_log.name,
		"linked": match,
		"note": note_name,
		"task": task_name,
	}


def _resolve_party(
	*, lead_external_id: str = "", phone: str = "", email: str | None = None
) -> dict | None:
	"""Prefer lead by external id, then phone match (lead/deal/contact), then email."""
	if lead_external_id and frappe.db.has_column("CRM Lead", "astra_external_id"):
		name = frappe.db.get_value("CRM Lead", {"astra_external_id": lead_external_id}, "name")
		if name:
			return {"doctype": "CRM Lead", "name": name}

	if phone:
		# Prefer Lead, then Deal (via contact), then Contact — phone first as specified
		matches = find_contact_by_phone_number(phone)
		for row in matches:
			if row["doctype"] == "CRM Lead":
				return {"doctype": "CRM Lead", "name": row["docname"]}
		for row in matches:
			if row["doctype"] == "CRM Deal":
				return {
					"doctype": "CRM Deal",
					"name": row["docname"],
					"contact": row.get("contact"),
				}
		for row in matches:
			if row["doctype"] == "Contact":
				return {"doctype": "Contact", "name": row["docname"], "contact": row["docname"]}

		# Direct lead lookup by normalized phone
		lead = _find_lead(phone=phone)
		if lead:
			return {"doctype": "CRM Lead", "name": lead}

	if email:
		lead = frappe.db.get_value("CRM Lead", {"email": email, "converted": 0}, "name")
		if lead:
			return {"doctype": "CRM Lead", "name": lead}
		contact = frappe.db.get_value("Contact", {"email_id": email}, "name")
		if contact:
			deal = frappe.db.get_value("CRM Contacts", {"contact": contact, "is_primary": 1}, "parent")
			if deal:
				return {"doctype": "CRM Deal", "name": deal, "contact": contact}
			return {"doctype": "Contact", "name": contact, "contact": contact}

	return None


def _find_lead(*, external_id: str = "", phone: str = "", email: str | None = None) -> str | None:
	if external_id and frappe.db.has_column("CRM Lead", "astra_external_id"):
		name = frappe.db.get_value("CRM Lead", {"astra_external_id": external_id}, "name")
		if name:
			return name
	if phone:
		for field in ("mobile_no", "phone"):
			# Scan recent candidates with digit overlap via normalize
			digits = "".join(ch for ch in phone if ch.isdigit())
			if not digits:
				continue
			rows = frappe.get_all(
				"CRM Lead",
				filters={"converted": 0, field: ("like", f"%{digits[-10:]}")},
				fields=["name", "mobile_no", "phone"],
				limit=20,
			)
			for row in rows:
				if normalize_phone(row.mobile_no) == phone or normalize_phone(row.phone) == phone:
					return row.name
	if email:
		return frappe.db.get_value("CRM Lead", {"email": email, "converted": 0}, "name")
	return None


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
		# Source may already exist under a different naming scheme — non-fatal
		frappe.log_error(title="Astra Connect lead source ensure failed")


def _map_direction(value: str | None) -> str:
	v = (value or "").strip().lower()
	if v in ("inbound", "incoming", "in"):
		return "Incoming"
	return "Outgoing"


def _map_call_status(value: str | None) -> str:
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


def _call_numbers(direction: str, phone: str, match: dict) -> tuple[str, str]:
	party_phone = phone or "unknown"
	agent = "astra-connect"
	if direction == "Incoming":
		return party_phone, agent
	return agent, party_phone


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
