# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Tasks page: status-grouped queue, tab counts and side-panel detail."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, today

from crm.api.work_queue import _record_label, _reference_title

OPEN_STATUSES = ["Backlog", "Todo", "In Progress"]
GROUP_ORDER = ["Todo", "In Progress", "Backlog"]
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
TASK_FIELDS = [
	"name",
	"title",
	"status",
	"priority",
	"due_date",
	"assigned_to",
	"description",
	"reference_doctype",
	"reference_docname",
	"creation",
	"modified",
]


def _tab_filters(tab: str, user: str, assigned_to: str | None) -> dict:
	filters: dict = {"status": ("in", OPEN_STATUSES)}
	tab = (tab or "mine").strip().lower()
	if tab == "mine":
		filters["assigned_to"] = assigned_to or user
	elif tab in ("due_today", "overdue"):
		filters["assigned_to"] = assigned_to or user
		if tab == "due_today":
			filters["due_date"] = ("between", [f"{today()} 00:00:00", f"{today()} 23:59:59"])
		else:
			filters["due_date"] = ("<", now_datetime())
	elif assigned_to:
		filters["assigned_to"] = assigned_to
	return filters


def _count(tab: str, user: str, assigned_to: str | None) -> int:
	return len(
		frappe.get_list("CRM Task", filters=_tab_filters(tab, user, assigned_to), fields=["name"], limit_page_length=0)
	)


def _due_label(due_date, status: str) -> tuple[str, bool]:
	"""Human due text and whether it is overdue. Midnight means date-only."""
	if not due_date:
		return "—", False
	due = get_datetime(due_date)
	now = now_datetime()
	has_time = bool(due.hour or due.minute)
	overdue = status in OPEN_STATUSES and due < now
	if due.date() == now.date():
		clock = due.strftime("%H:%M")
		if overdue:
			return (f"{clock} · {_('overdue')}" if has_time else _("Overdue")), True
		return (f"{_('Today')} {clock}" if has_time else _("Today")), False
	label = due.strftime("%d %b")
	return (f"{label} · {_('overdue')}" if overdue else label), overdue


def _shape(task) -> dict:
	title = _reference_title(task.reference_doctype, task.reference_docname)
	label, overdue = _due_label(task.due_date, task.status)
	return {
		"name": task.name,
		"title": task.title,
		"status": task.status,
		"priority": task.priority,
		"due_date": task.due_date,
		"due_label": label,
		"overdue": overdue,
		"assigned_to": task.assigned_to,
		"assigned_name": frappe.db.get_value("User", task.assigned_to, "full_name") if task.assigned_to else None,
		"reference_doctype": task.reference_doctype,
		"reference_docname": task.reference_docname,
		"record_label": _record_label(task.reference_doctype, title),
		"reference_title": title,
		"description": task.description,
		"creation": task.creation,
		"modified": task.modified,
	}


@frappe.whitelist()
def get_task_board(tab: str | None = None, priority: str | None = None, assigned_to: str | None = None) -> dict:
	"""tab: mine | due_today | overdue | team. priority: High | Medium | Low (optional)."""
	user = frappe.session.user
	tab = (tab or "mine").strip().lower()
	filters = _tab_filters(tab, user, assigned_to)
	if priority:
		filters["priority"] = priority

	tasks = frappe.get_list(
		"CRM Task", filters=filters, fields=TASK_FIELDS, order_by="due_date asc, modified desc", limit_page_length=200
	)

	groups = []
	for status in GROUP_ORDER:
		items = [_shape(t) for t in tasks if t.status == status]
		if items:
			groups.append({"id": status, "label": status, "count": len(items), "items": items})

	scope = {"assigned_to": assigned_to or user} if tab != "team" else {}
	done_filters = {"status": "Done", **scope}
	canceled_filters = {"status": "Canceled", **scope}
	return {
		"tab": tab,
		"tabs": {
			"mine": _count("mine", user, assigned_to),
			"due_today": _count("due_today", user, assigned_to),
			"overdue": _count("overdue", user, assigned_to),
			"team": _count("team", user, None),
		},
		"groups": groups,
		"done": {
			"count": len(frappe.get_list("CRM Task", filters=done_filters, fields=["name"], limit_page_length=0)),
			"canceled": len(frappe.get_list("CRM Task", filters=canceled_filters, fields=["name"], limit_page_length=0)),
		},
		"updated_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_task_detail(name: str) -> dict | None:
	if not name or not frappe.has_permission("CRM Task", "read", name):
		return None
	task = frappe.get_doc("CRM Task", name)
	data = _shape(task)
	ref_kind = {"CRM Lead": _("Lead"), "CRM Deal": _("Deal"), "Contact": _("Contact")}.get(task.reference_doctype)
	if task.reference_doctype and task.reference_docname:
		parts = [ref_kind or task.reference_doctype, data["reference_title"]]
		if task.reference_doctype == "CRM Lead":
			org = frappe.db.get_value("CRM Lead", task.reference_docname, "organization")
			if org:
				parts.append(org)
		data["linked_label"] = " · ".join(p for p in parts if p)
	data["source_label"] = _(
		"Created {0}"
	).format(get_datetime(task.creation).strftime("%d %b"))
	return data
