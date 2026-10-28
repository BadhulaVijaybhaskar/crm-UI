# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Lightweight sidebar counts — one permission-respecting request for the shell."""

from __future__ import annotations

import frappe
from frappe import _


OPEN_TASK_STATUSES = ("Backlog", "Todo", "In Progress")


def _open_status_names(status_doctype: str) -> list[str]:
	"""CRM Lead/Deal Status rows whose type is Open (not Won/Lost/Converted…)."""
	return frappe.get_all(
		status_doctype,
		filters={"type": "Open"},
		pluck="name",
	)


def _permitted_count(doctype: str, filters: dict) -> int | None:
	"""Count docs matching filters under the session user's read permissions.

	Uses ``frappe.get_list`` (not ``db.count``) so permission query conditions
	from org hierarchy / assignment rules apply. Returns ``None`` when the
	doctype is unreadable so the UI omits the badge instead of showing 0.
	"""
	if not frappe.has_permission(doctype, "read"):
		return None
	rows = frappe.get_list(
		doctype,
		filters=filters,
		pluck="name",
		limit_page_length=100000,
		ignore_permissions=False,
	)
	return len(rows or [])


def _count_my_open(doctype: str, *, owner_field: str, status_doctype: str) -> int | None:
	open_statuses = _open_status_names(status_doctype)
	if not open_statuses:
		# Status master missing — still readable, report zero rather than omit.
		if not frappe.has_permission(doctype, "read"):
			return None
		return 0
	return _permitted_count(
		doctype,
		{
			owner_field: frappe.session.user,
			"status": ["in", open_statuses],
		},
	)


def _count_my_open_tasks() -> int | None:
	return _permitted_count(
		"CRM Task",
		{
			"assigned_to": frappe.session.user,
			"status": ["in", list(OPEN_TASK_STATUSES)],
		},
	)


def _work_queue_count() -> int | None:
	"""Optional — only when the Work Queue API has shipped on this site."""
	try:
		fn = frappe.get_attr("crm.api.work_queue.get_work_queue_count")
	except Exception:
		return None
	try:
		value = fn()
	except Exception:
		frappe.log_error(title=_("Work queue count failed"))
		return None
	if value is None:
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


@frappe.whitelist()
def get_nav_counts() -> dict:
	"""Return real sidebar counts for the current user.

	Keys present only when the count is known and permission allows the doctype.
	Never invent numbers — omit a key rather than fake it.
	"""
	out: dict[str, int] = {}

	leads = _count_my_open(
		"CRM Lead", owner_field="lead_owner", status_doctype="CRM Lead Status"
	)
	if leads is not None:
		out["leads"] = leads

	deals = _count_my_open(
		"CRM Deal", owner_field="deal_owner", status_doctype="CRM Deal Status"
	)
	if deals is not None:
		out["deals"] = deals

	tasks = _count_my_open_tasks()
	if tasks is not None:
		out["tasks"] = tasks

	work_queue = _work_queue_count()
	if work_queue is not None:
		out["work_queue"] = work_queue

	return out
