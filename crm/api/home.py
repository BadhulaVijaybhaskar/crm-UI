# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Personal Home summary for the Astra CRM dashboard route (Figma 02 / m1).

Only surfaces buckets that have a real data source. Empty sections are omitted
so the UI can hide them instead of showing placeholders.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, today

from crm.api.activities import get_activity_feed, get_my_day


def _period_bounds(period: str) -> tuple[str, str]:
	period = (period or "today").strip().lower()
	end = today()
	if period in ("week", "this_week", "this week"):
		start = frappe.utils.add_days(end, -6)
	else:
		start = end
	return start, end


def _open_leads(user: str) -> dict:
	filters = {"converted": 0, "lead_owner": user}
	total = len(frappe.get_list("CRM Lead", filters=filters, pluck="name", limit_page_length=5000))
	yesterday = frappe.utils.add_days(today(), -1)
	new_since = len(
		frappe.get_list(
			"CRM Lead",
			filters={**filters, "creation": (">=", yesterday)},
			pluck="name",
			limit_page_length=5000,
		)
	)
	by_status: dict[str, int] = defaultdict(int)
	for row in frappe.get_list(
		"CRM Lead",
		filters=filters,
		fields=["status"],
		limit_page_length=5000,
	):
		by_status[row.status or _("Unknown")] += 1
	return {"count": total, "new_since_yesterday": new_since, "by_status": dict(by_status)}


def _open_pipeline(user: str) -> dict:
	Deal = frappe.qb.DocType("CRM Deal")
	Status = frappe.qb.DocType("CRM Deal Status")
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(
			Deal.name,
			Deal.status,
			Deal.deal_value,
			Deal.expected_deal_value,
			Deal.annual_revenue,
			Deal.probability,
			Status.type,
		)
		.where(Status.type.notin(["Won", "Lost"]))
		.where(Deal.deal_owner == user)
	)
	rows = query.run(as_dict=True)
	total_value = 0.0
	weighted = 0.0
	by_status: dict[str, int] = defaultdict(int)
	for row in rows:
		value = flt(row.expected_deal_value or row.deal_value or row.annual_revenue or 0)
		prob = flt(row.probability or 0) / 100.0
		total_value += value
		weighted += value * prob
		by_status[row.status or _("Unknown")] += 1
	return {
		"count": len(rows),
		"value": total_value,
		"weighted_value": weighted,
		"by_status": dict(by_status),
	}


def _closed_this_month(user: str) -> dict:
	month_start = frappe.utils.get_first_day(today())
	Deal = frappe.qb.DocType("CRM Deal")
	Status = frappe.qb.DocType("CRM Deal Status")
	query = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(Deal.status, Status.type)
		.where(Status.type.isin(["Won", "Lost"]))
		.where(Deal.deal_owner == user)
		.where(Deal.modified >= month_start)
	)
	rows = query.run(as_dict=True)
	by_status: dict[str, int] = defaultdict(int)
	won = lost = 0
	for row in rows:
		by_status[row.status or row.type] += 1
		if row.type == "Won":
			won += 1
		elif row.type == "Lost":
			lost += 1
	return {"count": len(rows), "won": won, "lost": lost, "by_status": dict(by_status)}


def _tasks_due(user: str, start: str, end: str) -> dict:
	day_end = get_datetime(f"{end} 23:59:59")
	open_statuses = ["Backlog", "Todo", "In Progress"]
	due = frappe.get_list(
		"CRM Task",
		filters={
			"assigned_to": user,
			"status": ("in", open_statuses),
			"due_date": ("<=", day_end),
		},
		fields=["name", "due_date"],
		limit_page_length=500,
	)
	overdue = 0
	today_d = getdate(today())
	for t in due:
		if t.due_date and getdate(t.due_date) < today_d:
			overdue += 1
	return {"count": len(due), "overdue": overdue}


def _calls_in_period(user: str, start: str, end: str) -> dict:
	day_start = get_datetime(f"{start} 00:00:00")
	day_end = get_datetime(f"{end} 23:59:59")
	CallLog = frappe.qb.DocType("CRM Call Log")
	query = (
		frappe.qb.from_(CallLog)
		.select(CallLog.name, CallLog.status)
		.where(CallLog.creation.between(day_start, day_end))
		.where((CallLog.caller == user) | (CallLog.receiver == user) | (CallLog.owner == user))
	)
	rows = query.run(as_dict=True)
	connected = sum(1 for r in rows if (r.status or "").lower() in ("completed", "connected", "answered"))
	return {"count": len(rows), "connected": connected}


def _response_deadlines(user: str) -> list[dict]:
	"""Leads with an open SLA response_by for the current user."""
	now = now_datetime()
	leads = frappe.get_list(
		"CRM Lead",
		filters={
			"lead_owner": user,
			"converted": 0,
			"response_by": ("is", "set"),
			"sla_status": ("in", ["First Response Due", "Rolling Response Due", "Failed"]),
		},
		fields=[
			"name",
			"lead_name",
			"organization",
			"status",
			"source",
			"response_by",
			"sla_status",
			"mobile_no",
			"lead_temperature",
		],
		order_by="response_by asc",
		limit_page_length=20,
	)
	items = []
	for lead in leads:
		due = get_datetime(lead.response_by)
		if not due:
			continue
		delta_min = int((due - now).total_seconds() // 60)
		if delta_min < 0:
			label = _("overdue {0} min").format(abs(delta_min))
			state = "overdue"
		else:
			label = _("in {0} min").format(delta_min)
			state = "due"
		kind = "Rolling response" if "Rolling" in (lead.sla_status or "") else "First response"
		items.append(
			{
				"name": lead.name,
				"title": lead.lead_name or lead.name,
				"organization": lead.organization,
				"status": lead.status,
				"source": lead.source,
				"sla_status": lead.sla_status,
				"response_by": lead.response_by,
				"label": label,
				"state": state,
				"kind": kind,
				"mobile_no": lead.mobile_no,
				"temperature": lead.lead_temperature,
				"route": {"name": "Lead", "params": {"leadId": lead.name}},
			}
		)
	return items


def _pipeline_groups(leads: dict, deals: dict, closed: dict) -> list[dict]:
	"""Milestone groups for the Home pipeline rail. Omits empty groups."""
	groups = []
	lead_statuses = leads.get("by_status") or {}
	if lead_statuses:
		# Split New/Contacted/Nurture vs Qualified when present
		lead_stage_order = ["New", "Contacted", "Nurture", "Qualified", "Unqualified", "Junk"]
		open_stages = []
		qualified_stages = []
		for status in lead_stage_order:
			count = cint(lead_statuses.get(status))
			if not count:
				continue
			stage = {"name": status, "count": count}
			if status == "Qualified":
				qualified_stages.append(stage)
			elif status in ("Unqualified", "Junk"):
				continue
			else:
				open_stages.append(stage)
		# Any custom statuses not in the known list
		for status, count in lead_statuses.items():
			if status in lead_stage_order:
				continue
			open_stages.append({"name": status, "count": cint(count)})
		if open_stages:
			groups.append(
				{
					"id": "lead",
					"label": _("Lead"),
					"count": sum(s["count"] for s in open_stages),
					"stages": open_stages,
				}
			)
		if qualified_stages:
			groups.append(
				{
					"id": "qualified",
					"label": _("Qualified"),
					"count": sum(s["count"] for s in qualified_stages),
					"stages": qualified_stages,
				}
			)

	deal_statuses = deals.get("by_status") or {}
	if deal_statuses:
		stages = [{"name": s, "count": c} for s, c in deal_statuses.items()]
		groups.append(
			{
				"id": "deal",
				"label": _("Deal"),
				"count": deals.get("count") or sum(s["count"] for s in stages),
				"stages": stages,
				"current": True,
			}
		)

	closed_statuses = closed.get("by_status") or {}
	if closed_statuses:
		groups.append(
			{
				"id": "closed",
				"label": _("Closed"),
				"count": closed.get("count") or 0,
				"stages": [{"name": s, "count": c} for s, c in closed_statuses.items()],
			}
		)
	return groups


def _enrich_today_tasks(my_day: dict) -> list[dict]:
	"""Attach display labels for the Today timeline."""
	items = []
	for task in my_day.get("tasks") or []:
		ref_title = ""
		kind = ""
		if task.get("reference_doctype") == "CRM Lead" and task.get("reference_docname"):
			ref_title = (
				frappe.db.get_value("CRM Lead", task.reference_docname, "lead_name")
				or task.reference_docname
			)
			kind = _("Lead")
		elif task.get("reference_doctype") == "CRM Deal" and task.get("reference_docname"):
			ref_title = (
				frappe.db.get_value("CRM Deal", task.reference_docname, "organization")
				or task.reference_docname
			)
			kind = _("Deal")
		due = get_datetime(task.due_date) if task.get("due_date") else None
		time_label = due.strftime("%H:%M") if due else ""
		badge = _("Overdue") if task.get("overdue") else (_("Due {0}").format(time_label) if time_label else _("Today"))
		items.append(
			{
				**task,
				"time_label": time_label,
				"badge": badge,
				"record_label": f"{ref_title} · {kind}" if ref_title else kind,
			}
		)

	for meeting in my_day.get("meetings") or []:
		starts = get_datetime(meeting.starts_on) if meeting.get("starts_on") else None
		items.append(
			{
				"name": meeting.name,
				"title": meeting.subject,
				"time_label": starts.strftime("%H:%M") if starts else "",
				"badge": _("Meeting"),
				"kind": "meeting",
				"due_date": meeting.starts_on,
				"record_label": "",
			}
		)

	items.sort(key=lambda i: i.get("due_date") or i.get("starts_on") or "")
	return items


@frappe.whitelist()
def get_home_summary(period: str | None = None) -> dict:
	"""Home KPIs + pipeline + today agenda + SLA deadlines + recent activity.

	period: today | week
	"""
	user = frappe.session.user
	period = (period or "today").strip().lower()
	start, end = _period_bounds(period)

	leads = _open_leads(user)
	pipeline = _open_pipeline(user)
	closed = _closed_this_month(user)
	tasks = _tasks_due(user, start, end)
	calls = _calls_in_period(user, start, end)
	my_day = get_my_day()
	deadlines = _response_deadlines(user)
	recent = get_activity_feed(limit=12, start=0)

	kpis = [
		{
			"id": "open_leads",
			"label": _("Open leads"),
			"value": leads["count"],
			"subtitle": _("{0} new since yesterday").format(leads["new_since_yesterday"])
			if leads["new_since_yesterday"]
			else None,
		},
		{
			"id": "open_pipeline",
			"label": _("Open pipeline"),
			"value": pipeline["value"],
			"value_is_currency": True,
			"subtitle": None,
			"deal_count": pipeline["count"],
			"weighted_value": pipeline["weighted_value"],
		},
		{
			"id": "due_today",
			"label": _("Due today") if period == "today" else _("Due this week"),
			"value": tasks["count"],
			"value_suffix": _(" tasks") if tasks["count"] != 1 else _(" task"),
			"subtitle": _("{0} overdue").format(tasks["overdue"]) if tasks["overdue"] else None,
			"subtitle_tone": "danger" if tasks["overdue"] else None,
		},
		{
			"id": "calls_today",
			"label": _("Calls today") if period == "today" else _("Calls this week"),
			"value": calls["count"],
			"subtitle": _("{0} connected · via Astra Connect").format(calls["connected"])
			if calls["count"]
			else None,
		},
	]

	pipeline_groups = _pipeline_groups(leads, pipeline, closed)
	today_items = _enrich_today_tasks(my_day)

	# First-name greeting
	full_name = frappe.db.get_value("User", user, "first_name") or frappe.db.get_value(
		"User", user, "full_name"
	) or user
	hour = now_datetime().hour
	if hour < 12:
		greeting = _("Good morning, {0}").format(full_name)
	elif hour < 17:
		greeting = _("Good afternoon, {0}").format(full_name)
	else:
		greeting = _("Good evening, {0}").format(full_name)

	return {
		"greeting": greeting,
		"date": today(),
		"now": str(now_datetime()),
		"period": period,
		"kpis": kpis,
		"pipeline": pipeline_groups,
		"today": today_items,
		"response_deadlines": deadlines,
		"recent": (recent or {}).get("items") or [],
	}
