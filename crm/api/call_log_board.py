# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Call logs page: tabs, filtered table, footer stats and side-panel detail."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime

from crm.api.work_queue import _record_label, _reference_title

MISSED_STATUSES = ["No Answer", "Busy", "Failed", "Canceled"]
CALL_FIELDS = [
	"name",
	"type",
	"channel",
	"status",
	"duration",
	"outcome",
	"disposition",
	"start_time",
	"creation",
	"caller",
	"receiver",
	"`from`",
	"`to`",
	"qualified",
	"call_summary",
	"recording_url",
	"telephony_medium",
	"reference_doctype",
	"reference_docname",
]


def _tab_filters(tab: str, user: str, days: int | None, logged_by: str | None) -> dict:
	filters: dict = {}
	if days:
		filters["creation"] = (">=", add_days(now_datetime(), -days))
	tab = (tab or "all").strip().lower()
	if tab == "mine":
		filters["caller"] = logged_by or user
	elif tab == "missed":
		filters["status"] = ("in", MISSED_STATUSES)
	elif tab == "qualified":
		filters["qualified"] = 1
	if logged_by and tab != "mine":
		filters["caller"] = logged_by
	return filters


def _count(tab: str, user: str, days: int | None, logged_by: str | None) -> int:
	return len(
		frappe.get_list(
			"CRM Call Log", filters=_tab_filters(tab, user, days, logged_by), fields=["name"], limit_page_length=0
		)
	)


def _duration_label(seconds) -> str:
	seconds = int(seconds or 0)
	if not seconds:
		return "—"
	minutes, secs = divmod(seconds, 60)
	return f"{minutes} m {secs:02d} s"


def _started_label(value) -> str:
	if not value:
		return ""
	moment = get_datetime(value)
	days = (now_datetime().date() - moment.date()).days
	clock = moment.strftime("%H:%M")
	if days == 0:
		return f"{_('Today')} {clock}"
	if days == 1:
		return f"{_('Yesterday')} {clock}"
	return f"{moment.strftime('%d %b')} {clock}"


def _contact_name(doctype: str | None, name: str | None) -> str:
	if not doctype or not name:
		return ""
	if doctype == "CRM Lead":
		return frappe.db.get_value("CRM Lead", name, "lead_name") or name
	if doctype == "CRM Deal":
		contact = frappe.db.get_value("CRM Contacts", {"parent": name, "is_primary": 1}, "contact")
		if contact:
			return frappe.db.get_value("Contact", contact, "full_name") or contact
		return frappe.db.get_value("CRM Deal", name, "lead_name") or ""
	return _reference_title(doctype, name)


def _type_label(call) -> str:
	direction = _("Incoming") if call.type == "Incoming" else _("Outgoing")
	medium = _("WhatsApp") if call.channel == "whatsapp" else _("Voice")
	return f"{direction} · {medium}"


def _shape(call) -> dict:
	title = _reference_title(call.reference_doctype, call.reference_docname)
	record_label = _record_label(call.reference_doctype, title)
	status = call.status or ""
	return {
		"name": call.name,
		"contact_name": _contact_name(call.reference_doctype, call.reference_docname) or call.get("to") or call.get("from"),
		"record_label": record_label,
		"reference_doctype": call.reference_doctype,
		"reference_docname": call.reference_docname,
		"type": call.type,
		"channel": call.channel or "voice",
		"status": status,
		"duration": call.duration,
		"duration_label": _duration_label(call.duration),
		"outcome": call.outcome or "",
		"disposition": call.disposition or "—",
		"start_time": call.start_time,
		"creation": call.creation,
		"started_label": _started_label(call.start_time or call.creation),
		"caller": call.caller,
		"receiver": call.receiver,
		"to": call.get("to"),
		"qualified": 1 if call.qualified else 0,
		"logged_by": call.telephony_medium or _("Manual"),
		"type_label": _type_label(call),
		"linked_label": record_label,
		"summary": call.call_summary,
		"has_recording": 1 if call.recording_url else 0,
		"started_detail": f"{_started_label(call.start_time or call.creation)} · {_duration_label(call.duration)}",
	}


@frappe.whitelist()
def get_call_logs(
	tab: str | None = None,
	days: int | None = 30,
	logged_by: str | None = None,
	limit: int = 10,
) -> dict:
	"""tab: all | mine | missed | qualified."""
	user = frappe.session.user
	days = int(days) if days else None
	tab = (tab or "all").strip().lower()
	filters = _tab_filters(tab, user, days, logged_by)

	total = _count(tab, user, days, logged_by)
	rows = frappe.get_list(
		"CRM Call Log",
		filters=filters,
		fields=CALL_FIELDS,
		order_by="start_time desc, creation desc",
		limit_page_length=int(limit),
	)
	all_in_range = frappe.get_list(
		"CRM Call Log", filters=_tab_filters("all", user, days, None), fields=["duration", "qualified"], limit_page_length=0
	)
	answered = [c.duration for c in all_in_range if c.duration]
	avg = int(sum(answered) / len(answered)) if answered else 0

	return {
		"tab": tab,
		"tabs": {
			"all": _count("all", user, days, None),
			"mine": _count("mine", user, days, None),
			"missed": _count("missed", user, days, None),
			"qualified": _count("qualified", user, days, None),
		},
		"rows": [_shape(r) for r in rows],
		"footer": {
			"shown": len(rows),
			"total": total,
			"range": _("last {0} days").format(days) if days else _("all time"),
			"avg_duration": _duration_label(avg),
			"qualified": sum(1 for c in all_in_range if c.qualified),
		},
	}


@frappe.whitelist()
def get_call_log_detail(name: str) -> dict | None:
	if not name or not frappe.has_permission("CRM Call Log", "read", name):
		return None
	call = frappe.get_doc("CRM Call Log", name)
	return _shape(call)
