# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Reports dashboard builder API.

Whitelisted endpoints for saved dashboards, KPIs, and chart aggregates.
All aggregates run through frappe.get_list with the caller's permissions.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, get_first_day, get_last_day, getdate, nowdate

from crm.api.reports.aggregate import run_aggregate, run_funnel, run_grouped
from crm.api.reports.formula import FormulaError, evaluate_formula
from crm.api.reports.whitelist import (
	assert_chart_type,
	get_field_options,
	get_module_options,
)
from crm.fcrm.doctype.crm_report_dashboard.crm_report_dashboard import (
	ensure_default_dashboards,
)
from crm.utils import sales_user_only


def _parse_json(value, default):
	if value is None or value == "":
		return deepcopy(default)
	if isinstance(value, (dict, list)):
		return value
	return json.loads(value)


def _period_bounds(period: str | None = None, from_date: str | None = None, to_date: str | None = None):
	if from_date and to_date:
		return str(getdate(from_date)), str(getdate(to_date))
	period = (period or "this_quarter").lower()
	today = getdate(nowdate())
	if period in ("this_quarter", "quarter"):
		q = (today.month - 1) // 3
		start = today.replace(month=q * 3 + 1, day=1)
		end_month = q * 3 + 3
		end = get_last_day(today.replace(month=end_month, day=1))
		return str(start), str(end)
	if period in ("this_month", "month"):
		return str(get_first_day(today)), str(today)
	if period in ("this_year", "year"):
		return str(today.replace(month=1, day=1)), str(today)
	if period == "last_30_days":
		return str(add_days(today, -30)), str(today)
	return str(add_days(today, -30)), str(today)


def _previous_period(from_date: str, to_date: str):
	start = getdate(from_date)
	end = getdate(to_date)
	days = (end - start).days + 1
	prev_end = add_to_date(start, days=-1)
	prev_start = add_to_date(prev_end, days=-(days - 1))
	return str(getdate(prev_start)), str(getdate(prev_end))


@frappe.whitelist()
@sales_user_only
def get_builder_meta():
	"""Modules, aggregations, and field whitelists for the builder UI."""
	return {
		"modules": get_module_options(),
		"fields_by_doctype": {dt: get_field_options(dt) for dt in (
			"CRM Lead",
			"CRM Deal",
			"Contact",
			"CRM Organization",
			"CRM Task",
			"CRM Call Log",
		)},
	}


@frappe.whitelist()
@sales_user_only
def get_fields(doctype: str):
	return get_field_options(doctype)


@frappe.whitelist()
@sales_user_only
def list_dashboards():
	ensure_default_dashboards()
	rows = frappe.get_list(
		"CRM Report Dashboard",
		fields=[
			"name",
			"title",
			"dashboard_type",
			"owner_user",
			"shared_role",
			"is_default",
			"modified",
		],
		order_by="is_default desc, modified desc",
		limit_page_length=0,
	)
	mine = [r for r in rows if r.dashboard_type == "Personal"]
	team = [r for r in rows if r.dashboard_type == "Team"]
	return {"personal": mine, "team": team, "all": rows}


@frappe.whitelist()
@sales_user_only
def get_dashboard(
	name: str | None = None,
	period: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	resolve: int | str | None = 1,
):
	ensure_default_dashboards()
	if not name:
		default = frappe.get_list(
			"CRM Report Dashboard",
			filters={"is_default": 1},
			fields=["name"],
			limit=1,
		)
		if not default:
			listed = frappe.get_list("CRM Report Dashboard", fields=["name"], limit=1)
			if not listed:
				frappe.throw(_("No dashboards available"))
			name = listed[0].name
		else:
			name = default[0].name

	doc = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "read", doc=doc, throw=True)

	layout = _parse_json(doc.layout, [])
	from_d, to_d = _period_bounds(period, from_date, to_date)

	if int(resolve or 0):
		for tile in layout:
			try:
				tile["data"] = _resolve_tile(tile, from_d, to_d)
			except Exception as e:
				tile["data"] = None
				tile["error"] = str(e)

	return {
		"name": doc.name,
		"title": doc.title,
		"dashboard_type": doc.dashboard_type,
		"owner_user": doc.owner_user,
		"shared_role": doc.shared_role,
		"is_default": doc.is_default,
		"from_date": from_d,
		"to_date": to_d,
		"layout": layout,
	}


@frappe.whitelist()
@sales_user_only
def create_dashboard(title: str, dashboard_type: str = "Personal", shared_role: str | None = None):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Report Dashboard",
			"title": title,
			"dashboard_type": dashboard_type or "Personal",
			"shared_role": shared_role,
			"owner_user": frappe.session.user if (dashboard_type or "Personal") == "Personal" else None,
			"layout": "[]",
		}
	)
	doc.insert()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
@sales_user_only
def rename_dashboard(name: str, title: str):
	doc = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "write", doc=doc, throw=True)
	doc.title = title
	doc.save()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
@sales_user_only
def duplicate_dashboard(name: str, title: str | None = None):
	src = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "read", doc=src, throw=True)
	doc = frappe.copy_doc(src)
	doc.title = title or _("{0} (copy)").format(src.title)
	doc.is_default = 0
	if doc.dashboard_type == "Personal":
		doc.owner_user = frappe.session.user
	doc.insert()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
@sales_user_only
def delete_dashboard(name: str):
	doc = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "delete", doc=doc, throw=True)
	frappe.delete_doc("CRM Report Dashboard", name)
	return {"ok": True}


@frappe.whitelist()
@sales_user_only
def set_default_dashboard(name: str):
	doc = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "write", doc=doc, throw=True)
	doc.is_default = 1
	doc.save()
	return {"name": doc.name, "is_default": 1}


@frappe.whitelist()
@sales_user_only
def save_dashboard_layout(name: str, layout: str | list):
	doc = frappe.get_doc("CRM Report Dashboard", name)
	frappe.has_permission("CRM Report Dashboard", "write", doc=doc, throw=True)
	parsed = _parse_json(layout, [])
	# Strip resolved runtime data before persisting
	clean = []
	for tile in parsed:
		item = {k: v for k, v in tile.items() if k not in ("data", "error")}
		clean.append(item)
	doc.layout = json.dumps(clean)
	doc.save()
	return {"name": doc.name, "layout": clean}


@frappe.whitelist()
@sales_user_only
def evaluate_kpi(
	config: str | dict | None = None,
	kpi_name: str | None = None,
	period: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
):
	"""Evaluate a KPI config or saved CRM Report KPI with the caller's permissions."""
	from_d, to_d = _period_bounds(period, from_date, to_date)
	if kpi_name:
		doc = frappe.get_doc("CRM Report KPI", kpi_name)
		frappe.has_permission("CRM Report KPI", "read", doc=doc, throw=True)
		cfg = _kpi_doc_to_config(doc)
	else:
		cfg = _parse_json(config, {})
	return _evaluate_kpi_config(cfg, from_d, to_d)


@frappe.whitelist()
@sales_user_only
def evaluate_chart(
	config: str | dict,
	period: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
):
	from_d, to_d = _period_bounds(period, from_date, to_date)
	cfg = _parse_json(config, {})
	return _evaluate_chart_config(cfg, from_d, to_d)


@frappe.whitelist()
@sales_user_only
def save_kpi(kpi: str | dict):
	data = _parse_json(kpi, {})
	name = data.pop("name", None)
	if name and frappe.db.exists("CRM Report KPI", name):
		doc = frappe.get_doc("CRM Report KPI", name)
		frappe.has_permission("CRM Report KPI", "write", doc=doc, throw=True)
		doc.update(data)
		doc.save()
	else:
		data["doctype"] = "CRM Report KPI"
		doc = frappe.get_doc(data)
		doc.insert()
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
@sales_user_only
def list_kpis():
	return frappe.get_list(
		"CRM Report KPI",
		fields=["name", "title", "kpi_type", "visibility", "format", "modified"],
		order_by="modified desc",
		limit_page_length=0,
	)


@frappe.whitelist()
@sales_user_only
def validate_kpi_formula(formula: str, refs: str | list | None = None):
	from crm.api.reports.formula import validate_formula

	allowed = set(_parse_json(refs, []))
	try:
		validate_formula(formula, allowed_refs=allowed or None)
		return {"ok": True}
	except FormulaError as e:
		return {"ok": False, "error": str(e)}


def _kpi_doc_to_config(doc) -> dict:
	return {
		"title": doc.title,
		"kpi_type": (doc.kpi_type or "Simple").lower(),
		"doctype": doc.source_doctype,
		"aggregation": doc.aggregation,
		"field": doc.aggregate_field,
		"date_field": doc.date_field,
		"filters": _parse_json(doc.filters_json, []),
		"formula": doc.formula,
		"formula_inputs": _parse_json(doc.formula_inputs, {}),
		"format": doc.format,
		"compare_with": doc.compare_with,
	}


def _evaluate_kpi_config(cfg: dict, from_d: str, to_d: str) -> dict[str, Any]:
	kpi_type = (cfg.get("kpi_type") or "simple").lower()
	compare = (cfg.get("compare_with") or "none").lower()
	prev_from, prev_to = _previous_period(from_d, to_d)

	if kpi_type == "calculated":
		inputs = cfg.get("formula_inputs") or {}
		values = {}
		breakdown = {}
		for key, input_cfg in inputs.items():
			val = _simple_aggregate(input_cfg, from_d, to_d)
			values[key] = val
			breakdown[key] = val
		try:
			result = evaluate_formula(cfg.get("formula") or "", values)
		except FormulaError as e:
			frappe.throw(_(str(e)))
		prev_result = None
		if compare == "previous_period":
			prev_values = {
				k: _simple_aggregate(input_cfg, prev_from, prev_to) for k, input_cfg in inputs.items()
			}
			try:
				prev_result = evaluate_formula(cfg.get("formula") or "", prev_values)
			except FormulaError:
				prev_result = None
		return _kpi_payload(cfg, result, prev_result, breakdown=breakdown)

	value = _simple_aggregate(cfg, from_d, to_d)
	prev_value = _simple_aggregate(cfg, prev_from, prev_to) if compare == "previous_period" else None
	return _kpi_payload(cfg, value, prev_value)


def _simple_aggregate(cfg: dict, from_d: str, to_d: str) -> float:
	return run_aggregate(
		doctype=cfg.get("doctype") or cfg.get("source_doctype"),
		aggregation=cfg.get("aggregation", "count"),
		field=cfg.get("field") or cfg.get("aggregate_field"),
		filters=cfg.get("filters") or _parse_json(cfg.get("filters_json"), []),
		date_field=cfg.get("date_field"),
		from_date=from_d,
		to_date=to_d,
	)


def _kpi_payload(cfg, value, previous=None, breakdown=None):
	delta = None
	delta_pct = None
	if previous is not None and previous != 0:
		delta = value - previous
		delta_pct = (delta / abs(previous)) * 100
	elif previous == 0 and value:
		delta = value
		delta_pct = 100.0
	return {
		"title": cfg.get("title"),
		"value": value,
		"previous": previous,
		"delta": delta,
		"delta_pct": delta_pct,
		"format": cfg.get("format") or "number",
		"breakdown": breakdown,
		"formula": cfg.get("formula"),
		"kpi_type": (cfg.get("kpi_type") or "simple").lower(),
	}


def _evaluate_chart_config(cfg: dict, from_d: str, to_d: str) -> dict[str, Any]:
	chart_type = assert_chart_type(cfg.get("chart_type") or cfg.get("type") or "bar")
	title = cfg.get("title") or ""

	if chart_type == "funnel":
		steps = run_funnel(
			doctype=cfg.get("doctype") or "CRM Deal",
			milestones=cfg.get("milestones") or [],
			filters=cfg.get("filters"),
			date_field=cfg.get("date_field"),
			from_date=from_d,
			to_date=to_d,
		)
		return {
			"type": "funnel",
			"title": title,
			"data": steps,
			"summary": _funnel_summary(steps),
		}

	if chart_type == "table":
		doctype = cfg.get("doctype")
		fields = cfg.get("columns") or ["name"]
		rows = frappe.get_list(
			doctype,
			filters=cfg.get("filters") or [],
			fields=fields,
			order_by=cfg.get("order_by") or "modified desc",
			limit_page_length=int(cfg.get("limit") or 10),
			ignore_permissions=False,
		)
		return {"type": "table", "title": title, "columns": fields, "rows": rows}

	grouped = run_grouped(
		doctype=cfg.get("doctype"),
		aggregation=cfg.get("aggregation", "count"),
		field=cfg.get("field"),
		group_by=cfg.get("group_by") or cfg.get("x_axis"),
		filters=cfg.get("filters"),
		date_field=cfg.get("date_field"),
		from_date=from_d,
		to_date=to_d,
		date_bucket=cfg.get("date_bucket"),
		secondary_group=cfg.get("series_by") or cfg.get("group_by_secondary"),
	)

	if chart_type == "donut":
		return {
			"type": "donut_chart",
			"title": title,
			"data": [{"label": r["group"], "value": r["value"]} for r in grouped],
			"categoryColumn": "label",
			"valueColumn": "value",
			"colors": cfg.get("colors"),
		}

	# bar / line — possibly stacked series
	if any(r.get("series") for r in grouped):
		categories = []
		series_names = []
		seen_cat = set()
		seen_series = set()
		for r in grouped:
			if r["group"] not in seen_cat:
				seen_cat.add(r["group"])
				categories.append(r["group"])
			s = r.get("series") or "value"
			if s not in seen_series:
				seen_series.add(s)
				series_names.append(s)
		matrix = {c: {s: 0 for s in series_names} for c in categories}
		for r in grouped:
			matrix[r["group"]][r.get("series") or "value"] = r["value"]
		data = [{"label": c, **matrix[c]} for c in categories]
		series = [
			{"name": s, "type": "bar" if chart_type == "bar" else "line", "stackName": "total" if cfg.get("stacked") else None}
			for s in series_names
		]
	else:
		data = [{"label": r["group"], "value": r["value"]} for r in grouped]
		series = [{"name": "value", "type": "bar" if chart_type == "bar" else "line"}]

	return {
		"type": "axis_chart",
		"title": title,
		"data": data,
		"xAxis": {"key": "label", "type": "category"},
		"series": series,
		"stacked": bool(cfg.get("stacked")),
		"colors": cfg.get("colors"),
		"chart_kind": chart_type,
	}


def _funnel_summary(steps: list[dict]) -> dict:
	if not steps:
		return {}
	first = steps[0]["value"] or 0
	last = steps[-1]["value"] or 0
	rate = (last / first * 100) if first else 0
	return {"first": first, "last": last, "conversion_pct": rate}


def _resolve_tile(tile: dict, from_d: str, to_d: str):
	ttype = (tile.get("type") or "").lower()
	cfg = dict(tile.get("config") or {})
	cfg.setdefault("title", tile.get("title"))
	if ttype == "kpi":
		return _evaluate_kpi_config(cfg, from_d, to_d)
	if ttype in ("bar", "line", "donut", "pie", "funnel", "table"):
		cfg["chart_type"] = "donut" if ttype == "pie" else ttype
		return _evaluate_chart_config(cfg, from_d, to_d)
	return None
