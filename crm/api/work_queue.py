# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Work queue — ranked follow-ups and quiet leads for the signed-in user.

Nav badge uses `get_work_queue_count` (permission-aware, short-lived cache).
"""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, getdate, now_datetime, today

WORK_QUEUE_COUNT_TTL = 60
QUIET_DAYS = 7


def _cache_key(user: str) -> str:
	return f"crm:work_queue_count:{user}"


def _invalidate_count(user: str | None = None) -> None:
	user = user or frappe.session.user
	frappe.cache().delete_value(_cache_key(user))


def _open_task_statuses() -> list[str]:
	return ["Backlog", "Todo", "In Progress"]


def _follow_ups(user: str, priorities: list[str] | None = None) -> list[dict]:
	"""Open tasks assigned to the user that are due today or overdue."""
	day_end = get_datetime(f"{today()} 23:59:59")
	filters: dict = {
		"assigned_to": user,
		"status": ("in", _open_task_statuses()),
		"due_date": ("<=", day_end),
	}
	if priorities:
		filters["priority"] = ("in", priorities)

	tasks = frappe.get_list(
		"CRM Task",
		filters=filters,
		fields=[
			"name",
			"title",
			"status",
			"priority",
			"due_date",
			"description",
			"reference_doctype",
			"reference_docname",
			"modified",
		],
		order_by="due_date asc",
		limit_page_length=100,
	)
	now = now_datetime()
	items = []
	for task in tasks:
		due = get_datetime(task.due_date) if task.due_date else None
		late_minutes = None
		due_label = _("Today")
		if due:
			if due.date() < getdate(today()):
				late_minutes = int((now - due).total_seconds() // 60)
				due_label = _("{0} m late").format(late_minutes) if late_minutes < 24 * 60 else _("Overdue")
			elif due.date() == getdate(today()):
				due_label = due.strftime("%H:%M") if due.hour or due.minute else _("Today")

		ref_title = _reference_title(task.reference_doctype, task.reference_docname)
		items.append(
			{
				"id": f"task:{task.name}",
				"kind": "follow_up",
				"task": task.name,
				"title": task.title,
				"priority": task.priority or "Low",
				"status": task.status,
				"due_date": task.due_date,
				"due_label": due_label,
				"late_minutes": late_minutes,
				"description": (task.description or "")[:280],
				"reference_doctype": task.reference_doctype,
				"reference_docname": task.reference_docname,
				"reference_title": ref_title,
				"record_label": _record_label(task.reference_doctype, ref_title),
			}
		)
	return items


def _reference_title(doctype: str | None, name: str | None) -> str:
	if not doctype or not name:
		return ""
	if not frappe.has_permission(doctype, "read", name):
		return name
	if doctype == "CRM Lead":
		return frappe.db.get_value("CRM Lead", name, "lead_name") or name
	if doctype == "CRM Deal":
		return (
			frappe.db.get_value("CRM Deal", name, "organization")
			or frappe.db.get_value("CRM Deal", name, "lead_name")
			or name
		)
	if doctype == "Contact":
		return frappe.db.get_value("Contact", name, "full_name") or name
	return name


def _record_label(doctype: str | None, title: str) -> str:
	if not doctype:
		return title or ""
	kind = {
		"CRM Lead": _("Lead"),
		"CRM Deal": _("Deal"),
		"Contact": _("Contact"),
	}.get(doctype, doctype)
	if title:
		return f"{title} · {kind}"
	return kind


def _recent_activity_refs(cutoff) -> set[tuple[str, str]]:
	"""(doctype, name) pairs touched by call, email or note since cutoff."""
	refs: set[tuple[str, str]] = set()

	calls = frappe.get_list(
		"CRM Call Log",
		filters={
			"creation": (">=", cutoff),
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
		},
		fields=["reference_doctype", "reference_docname"],
		limit_page_length=500,
	)
	for row in calls:
		if row.reference_doctype and row.reference_docname:
			refs.add((row.reference_doctype, row.reference_docname))

	notes = frappe.get_list(
		"FCRM Note",
		filters={
			"creation": (">=", cutoff),
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
		},
		fields=["reference_doctype", "reference_docname"],
		limit_page_length=500,
	)
	for row in notes:
		if row.reference_doctype and row.reference_docname:
			refs.add((row.reference_doctype, row.reference_docname))

	comms = frappe.get_list(
		"Communication",
		filters={
			"creation": (">=", cutoff),
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
			"communication_medium": "Email",
		},
		fields=["reference_doctype", "reference_name"],
		limit_page_length=500,
	)
	for row in comms:
		if row.reference_doctype and row.reference_name:
			refs.add((row.reference_doctype, row.reference_name))

	return refs


def _quiet_leads(user: str) -> list[dict]:
	"""Open leads owned by the user with no call, email or note in QUIET_DAYS+."""
	cutoff = now_datetime() - timedelta(days=QUIET_DAYS)
	leads = frappe.get_list(
		"CRM Lead",
		filters={
			"lead_owner": user,
			"converted": 0,
			"creation": ("<", cutoff),
		},
		fields=[
			"name",
			"lead_name",
			"organization",
			"status",
			"source",
			"lead_temperature",
			"lead_score",
			"mobile_no",
			"email",
			"creation",
			"modified",
			"response_by",
			"sla_status",
		],
		order_by="modified asc",
		limit_page_length=100,
	)
	recent = _recent_activity_refs(cutoff)
	items = []
	now = now_datetime()
	for lead in leads:
		if ("CRM Lead", lead.name) in recent:
			continue
		last_touch = get_datetime(lead.modified) or get_datetime(lead.creation)
		days = max(cint((now - last_touch).total_seconds() // 86400), QUIET_DAYS)
		items.append(
			{
				"id": f"lead:{lead.name}",
				"kind": "quiet_lead",
				"title": _("No recent activity"),
				"priority": "Medium" if (lead.lead_temperature or "") == "Hot" else "Low",
				"due_label": _("No touch in {0} days").format(days),
				"days_quiet": days,
				"description": _("Last update {0}").format(last_touch.strftime("%d %b") if last_touch else ""),
				"reference_doctype": "CRM Lead",
				"reference_docname": lead.name,
				"reference_title": lead.lead_name or lead.name,
				"record_label": _record_label("CRM Lead", lead.organization or lead.lead_name or lead.name),
				"status": lead.status,
				"source": lead.source,
				"lead_temperature": lead.lead_temperature,
				"lead_score": lead.lead_score,
				"mobile_no": lead.mobile_no,
				"email": lead.email,
				"organization": lead.organization,
				"response_by": lead.response_by,
				"sla_status": lead.sla_status,
			}
		)
	return items


def _cleared_today(user: str) -> list[dict]:
	day_start = get_datetime(f"{today()} 00:00:00")
	tasks = frappe.get_list(
		"CRM Task",
		filters={
			"assigned_to": user,
			"status": "Done",
			"modified": (">=", day_start),
		},
		fields=["name", "title", "modified", "reference_doctype", "reference_docname"],
		order_by="modified desc",
		limit_page_length=50,
	)
	return [
		{
			"id": f"cleared:{t.name}",
			"kind": "cleared",
			"task": t.name,
			"title": t.title,
			"modified": t.modified,
			"reference_doctype": t.reference_doctype,
			"reference_docname": t.reference_docname,
		}
		for t in tasks
	]


def _parse_priorities(priority: str | None) -> list[str] | None:
	if not priority:
		return None
	parts = [p.strip() for p in str(priority).split(",") if p.strip()]
	return parts or None


@frappe.whitelist()
def get_work_queue_count() -> dict:
	"""Lightweight badge count for the shell nav. Cached per user for 60s."""
	user = frappe.session.user
	if not user or user == "Guest":
		return {"count": 0, "updated_at": str(now_datetime())}

	cache = frappe.cache()
	key = _cache_key(user)
	cached = cache.get_value(key)
	if isinstance(cached, dict) and "count" in cached:
		return cached

	follow_ups = _follow_ups(user)
	quiet = _quiet_leads(user)
	payload = {
		"count": len(follow_ups) + len(quiet),
		"follow_ups": len(follow_ups),
		"quiet_leads": len(quiet),
		"updated_at": str(now_datetime()),
	}
	cache.set_value(key, payload, expires_in_sec=WORK_QUEUE_COUNT_TTL)
	return payload


@frappe.whitelist()
def get_work_queue(tab: str | None = None, priority: str | None = None) -> dict:
	"""Ranked work queue for the signed-in user.

	tab: all | follow_ups | quiet_leads
	priority: comma-separated High,Medium,Low (applied to follow-ups)
	"""
	user = frappe.session.user
	tab = (tab or "all").strip().lower()
	priorities = _parse_priorities(priority)

	follow_ups = _follow_ups(user, priorities)
	quiet = _quiet_leads(user)
	cleared = _cleared_today(user)

	if tab == "follow_ups":
		sections = [{"id": "follow_ups", "label": _("Follow-ups"), "items": follow_ups}]
	elif tab in ("quiet_leads", "quiet"):
		sections = [{"id": "quiet_leads", "label": _("Quiet leads"), "items": quiet}]
	else:
		sections = [
			{
				"id": "follow_ups",
				"label": _("Follow-ups"),
				"description": _("Tasks and next steps due today or overdue"),
				"items": follow_ups,
			},
			{
				"id": "quiet_leads",
				"label": _("Quiet leads"),
				"description": _("Open leads with no call, email or note in {0}+ days").format(QUIET_DAYS),
				"items": quiet,
			},
		]

	# Drop empty sections so the UI never shows a hollow block
	sections = [s for s in sections if s.get("items")]

	return {
		"tab": tab,
		"sections": sections,
		"counts": {
			"all": len(follow_ups) + len(quiet),
			"follow_ups": len(follow_ups),
			"quiet_leads": len(quiet),
			"cleared_today": len(cleared),
		},
		"cleared_today": cleared,
		"updated_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_work_queue_detail(reference_doctype: str, reference_docname: str) -> dict | None:
	"""Side-panel payload for a selected queue row's linked record."""
	doctype = (reference_doctype or "").strip()
	name = (reference_docname or "").strip()
	if not doctype or not name:
		return None
	if not frappe.has_permission(doctype, "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if doctype == "CRM Lead":
		lead = frappe.db.get_value(
			"CRM Lead",
			name,
			[
				"name",
				"lead_name",
				"organization",
				"status",
				"source",
				"mobile_no",
				"email",
				"lead_score",
				"lead_temperature",
				"response_by",
				"sla_status",
				"lead_owner",
			],
			as_dict=True,
		)
		if not lead:
			return None
		last_call = frappe.get_list(
			"CRM Call Log",
			filters={"reference_doctype": "CRM Lead", "reference_docname": name},
			fields=["name", "start_time", "creation", "outcome", "call_summary", "status", "type"],
			order_by="creation desc",
			limit_page_length=1,
		)
		return {
			"doctype": doctype,
			"name": name,
			"title": lead.lead_name or name,
			"status": lead.status,
			"temperature": lead.lead_temperature,
			"organization": lead.organization,
			"source": lead.source,
			"mobile_no": lead.mobile_no,
			"email": lead.email,
			"lead_score": lead.lead_score,
			"response_by": lead.response_by,
			"sla_status": lead.sla_status,
			"owner": lead.lead_owner,
			"last_call": last_call[0] if last_call else None,
			"route": {"name": "Lead", "params": {"leadId": name}},
		}

	if doctype == "CRM Deal":
		deal = frappe.db.get_value(
			"CRM Deal",
			name,
			[
				"name",
				"organization",
				"lead_name",
				"status",
				"deal_value",
				"expected_deal_value",
				"mobile_no",
				"email",
				"deal_owner",
				"next_step",
			],
			as_dict=True,
		)
		if not deal:
			return None
		return {
			"doctype": doctype,
			"name": name,
			"title": deal.organization or deal.lead_name or name,
			"status": deal.status,
			"organization": deal.organization,
			"mobile_no": deal.mobile_no,
			"email": deal.email,
			"owner": deal.deal_owner,
			"value": deal.expected_deal_value or deal.deal_value,
			"next_step": deal.next_step,
			"route": {"name": "Deal", "params": {"dealId": name}},
		}

	return {
		"doctype": doctype,
		"name": name,
		"title": _reference_title(doctype, name),
	}
