# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Notes page: pinned / recent split, search, and side-panel detail."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, strip_html

from crm.api.work_queue import _record_label, _reference_title

NOTE_FIELDS = [
	"name",
	"title",
	"content",
	"reference_doctype",
	"reference_docname",
	"owner",
	"creation",
	"modified",
	"pinned",
	"pinned_by",
	"pinned_on",
]


def _time_label(value) -> str:
	if not value:
		return ""
	moment = get_datetime(value)
	days = (now_datetime().date() - moment.date()).days
	if days == 0:
		return _("Today")
	if days == 1:
		return _("Yesterday")
	return moment.strftime("%d %b")


def _full_name(user: str | None) -> str:
	if not user:
		return ""
	return frappe.db.get_value("User", user, "full_name") or user


def _shape(note) -> dict:
	title = _reference_title(note.reference_doctype, note.reference_docname)
	text = " ".join(strip_html(note.content or "").split())
	return {
		"name": note.name,
		"title": note.title or text[:60],
		"preview": text[:160],
		"content": note.content,
		"reference_doctype": note.reference_doctype,
		"reference_docname": note.reference_docname,
		"reference_title": title,
		"record_label": _record_label(note.reference_doctype, title),
		"owner": note.owner,
		"owner_name": _full_name(note.owner),
		"creation": note.creation,
		"modified": note.modified,
		"time_label": _time_label(note.creation),
		"pinned": 1 if note.pinned else 0,
		"pinned_by": _full_name(note.pinned_by).split(" ")[0] if note.pinned_by else None,
		"pinned_on": note.pinned_on,
	}


@frappe.whitelist()
def get_notes(
	search: str | None = None,
	linked_doctype: str | None = None,
	author: str | None = None,
) -> dict:
	filters: dict = {}
	if linked_doctype:
		filters["reference_doctype"] = linked_doctype
	if author:
		filters["owner"] = author
	or_filters = None
	if search:
		like = f"%{search.strip()}%"
		or_filters = {"title": ("like", like), "content": ("like", like)}

	rows = frappe.get_list(
		"FCRM Note",
		filters=filters,
		or_filters=or_filters,
		fields=NOTE_FIELDS,
		order_by="modified desc",
		limit_page_length=100,
	)
	items = [_shape(r) for r in rows]
	pinned = [i for i in items if i["pinned"]]
	recent = [i for i in items if not i["pinned"]]
	sections = []
	if pinned:
		sections.append({"id": "pinned", "label": _("Pinned"), "items": pinned})
	if recent:
		sections.append({"id": "recent", "label": _("Recent"), "items": recent})
	return {"sections": sections, "total": len(items)}


@frappe.whitelist()
def get_note(name: str) -> dict | None:
	if not name or not frappe.has_permission("FCRM Note", "read", name):
		return None
	note = frappe.get_doc("FCRM Note", name)
	data = _shape(note)
	if note.reference_doctype and note.reference_docname:
		linked = data["reference_title"]
		extra = None
		if note.reference_doctype == "CRM Deal":
			extra = frappe.db.get_value("CRM Deal", note.reference_docname, "status")
		elif note.reference_doctype == "CRM Lead":
			extra = frappe.db.get_value("CRM Lead", note.reference_docname, "organization")
		data["linked_title"] = " · ".join(p for p in [linked, extra] if p and p != linked)
		data["linked_title"] = data["linked_title"] or linked
	return data
