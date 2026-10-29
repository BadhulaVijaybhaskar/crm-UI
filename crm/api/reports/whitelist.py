# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Whitelisted doctypes and fields for the reports builder.

Only these modules/fields are offered in the UI and accepted by the API.
"""

from __future__ import annotations

from frappe import _

# Public module label → DocType
REPORT_MODULES = {
	"CRM Lead": {"label": "Lead", "owner_field": "lead_owner"},
	"CRM Deal": {"label": "Deal", "owner_field": "deal_owner"},
	"Contact": {"label": "Contact", "owner_field": "owner"},
	"CRM Organization": {"label": "Organization", "owner_field": "owner"},
	"CRM Task": {"label": "Task", "owner_field": "assigned_to"},
	"CRM Call Log": {"label": "Call log", "owner_field": "owner"},
}

AGGREGATIONS = ("count", "sum", "avg", "min", "max")

CHART_TYPES = ("bar", "line", "donut", "funnel", "table")

DATE_BUCKETS = ("day", "week", "month", "quarter", "year")

# Numeric fields eligible for sum/avg/min/max (count always allowed)
NUMERIC_FIELDS = {
	"CRM Lead": ("annual_revenue", "lead_score", "total", "net_total"),
	"CRM Deal": (
		"deal_value",
		"expected_deal_value",
		"annual_revenue",
		"probability",
		"total",
		"net_total",
		"exchange_rate",
	),
	"Contact": (),
	"CRM Organization": ("annual_revenue", "exchange_rate"),
	"CRM Task": (),
	"CRM Call Log": ("duration",),
}

# Group-by / filter dimensions
DIMENSION_FIELDS = {
	"CRM Lead": ("status", "source", "lead_owner", "territory", "industry", "organization"),
	"CRM Deal": (
		"status",
		"source",
		"deal_owner",
		"territory",
		"industry",
		"organization",
	),
	"Contact": ("company_name", "gender", "status", "owner"),
	"CRM Organization": ("industry", "territory", "organization_name"),
	"CRM Task": ("status", "priority", "assigned_to"),
	"CRM Call Log": ("status", "type", "caller", "receiver"),
}

# Date fields usable for range filters / time buckets
DATE_FIELDS = {
	"CRM Lead": ("creation", "modified", "first_responded_on", "last_responded_on"),
	"CRM Deal": (
		"creation",
		"modified",
		"expected_closure_date",
		"closed_date",
		"first_responded_on",
		"last_responded_on",
	),
	"Contact": ("creation", "modified"),
	"CRM Organization": ("creation", "modified"),
	"CRM Task": ("creation", "modified", "start_date", "due_date"),
	"CRM Call Log": ("creation", "modified", "start_time", "end_time"),
}


def assert_allowed_doctype(doctype: str) -> str:
	if doctype not in REPORT_MODULES:
		raise ValueError(f"Doctype not allowed for reports: {doctype}")
	return doctype


def assert_aggregation(aggregation: str) -> str:
	agg = (aggregation or "count").lower()
	if agg not in AGGREGATIONS:
		raise ValueError(f"Aggregation not allowed: {aggregation}")
	return agg


def assert_numeric_field(doctype: str, field: str | None, aggregation: str) -> str | None:
	if aggregation == "count":
		return field or "name"
	if not field:
		raise ValueError("Field is required for this aggregation")
	allowed = NUMERIC_FIELDS.get(doctype, ())
	if field not in allowed:
		raise ValueError(f"Field not allowed for aggregation: {field}")
	return field


def assert_dimension_field(doctype: str, field: str) -> str:
	allowed = DIMENSION_FIELDS.get(doctype, ()) + DATE_FIELDS.get(doctype, ())
	if field not in allowed and field != "name":
		raise ValueError(f"Field not allowed for grouping: {field}")
	return field


def assert_date_field(doctype: str, field: str | None) -> str | None:
	if not field:
		return None
	if field not in DATE_FIELDS.get(doctype, ()):
		raise ValueError(f"Date field not allowed: {field}")
	return field


def assert_chart_type(chart_type: str) -> str:
	ct = (chart_type or "").lower()
	if ct == "pie":
		ct = "donut"
	if ct not in CHART_TYPES:
		raise ValueError(f"Chart type not allowed: {chart_type}")
	return ct


def assert_date_bucket(bucket: str | None) -> str | None:
	if not bucket:
		return None
	b = bucket.lower()
	if b not in DATE_BUCKETS:
		raise ValueError(f"Date bucket not allowed: {bucket}")
	return b


def get_module_options():
	return [
		{"label": _(meta["label"]), "value": dt}
		for dt, meta in REPORT_MODULES.items()
	]


def get_field_options(doctype: str):
	assert_allowed_doctype(doctype)
	return {
		"numeric": [{"label": _(f), "value": f} for f in NUMERIC_FIELDS.get(doctype, ())],
		"dimensions": [
			{"label": _(f), "value": f} for f in DIMENSION_FIELDS.get(doctype, ())
		],
		"dates": [{"label": _(f), "value": f} for f in DATE_FIELDS.get(doctype, ())],
		"aggregations": [{"label": _(a.title()), "value": a} for a in AGGREGATIONS],
		"chart_types": [{"label": _(c.title()), "value": c} for c in CHART_TYPES],
		"date_buckets": [{"label": _(b.title()), "value": b} for b in DATE_BUCKETS],
	}
