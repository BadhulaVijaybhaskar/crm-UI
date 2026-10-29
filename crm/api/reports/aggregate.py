# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Permission-aware aggregation for reports.

Every query goes through frappe.get_list so record-level permission hooks apply.
Never uses raw SQL that skips permissions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate

from crm.api.reports.whitelist import (
	DATE_FIELDS,
	assert_aggregation,
	assert_allowed_doctype,
	assert_date_bucket,
	assert_date_field,
	assert_dimension_field,
	assert_numeric_field,
)


def run_aggregate(
	*,
	doctype: str,
	aggregation: str = "count",
	field: str | None = None,
	filters: list | dict | None = None,
	date_field: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
) -> float:
	"""Aggregate values the current user is allowed to read."""
	doctype = assert_allowed_doctype(doctype)
	aggregation = assert_aggregation(aggregation)
	field = assert_numeric_field(doctype, field, aggregation)
	date_field = assert_date_field(doctype, date_field)

	list_filters = _normalize_filters(filters)
	if date_field and from_date and to_date:
		list_filters.append([doctype, date_field, "Between", [from_date, to_date]])

	if aggregation == "count":
		rows = frappe.get_list(
			doctype,
			filters=list_filters,
			fields=["name"],
			limit_page_length=0,
			ignore_permissions=False,
		)
		return float(len(rows))

	rows = frappe.get_list(
		doctype,
		filters=list_filters,
		fields=[field],
		limit_page_length=0,
		ignore_permissions=False,
	)
	values = [_as_number(r.get(field)) for r in rows]
	values = [v for v in values if v is not None]
	if not values:
		return 0.0
	if aggregation == "sum":
		return float(sum(values))
	if aggregation == "avg":
		return float(sum(values) / len(values))
	if aggregation == "min":
		return float(min(values))
	if aggregation == "max":
		return float(max(values))
	raise ValueError(f"Unsupported aggregation: {aggregation}")


def run_grouped(
	*,
	doctype: str,
	aggregation: str = "count",
	field: str | None = None,
	group_by: str,
	filters: list | dict | None = None,
	date_field: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	date_bucket: str | None = None,
	secondary_group: str | None = None,
) -> list[dict[str, Any]]:
	"""Group-by aggregate with the current user's permissions."""
	doctype = assert_allowed_doctype(doctype)
	aggregation = assert_aggregation(aggregation)
	field = assert_numeric_field(doctype, field, aggregation)
	group_by = assert_dimension_field(doctype, group_by)
	date_field = assert_date_field(doctype, date_field)
	date_bucket = assert_date_bucket(date_bucket)
	if secondary_group:
		secondary_group = assert_dimension_field(doctype, secondary_group)

	list_filters = _normalize_filters(filters)
	if date_field and from_date and to_date:
		list_filters.append([doctype, date_field, "Between", [from_date, to_date]])

	select_fields = [group_by]
	if secondary_group and secondary_group not in select_fields:
		select_fields.append(secondary_group)
	value_field = field if aggregation != "count" else None
	if value_field and value_field not in select_fields:
		select_fields.append(value_field)

	rows = frappe.get_list(
		doctype,
		filters=list_filters,
		fields=select_fields,
		limit_page_length=0,
		ignore_permissions=False,
	)

	date_dims = set(DATE_FIELDS.get(doctype, ()))
	buckets: dict[tuple, list[float | None]] = defaultdict(list)
	for row in rows:
		key_parts = []
		raw = row.get(group_by)
		if date_bucket and (group_by in date_dims or _is_dateish(raw)):
			key_parts.append(_bucket_label(raw, date_bucket) if raw else _("Unset"))
		else:
			key_parts.append(raw if raw not in (None, "") else _("Unset"))
		if secondary_group:
			sec = row.get(secondary_group)
			key_parts.append(sec if sec not in (None, "") else _("Unset"))
		val = _as_number(row.get(value_field)) if value_field else 1.0
		buckets[tuple(key_parts)].append(val)

	out = []
	for key, vals in buckets.items():
		nums = [v for v in vals if v is not None]
		if aggregation == "count":
			result = float(len(vals))
		elif not nums:
			result = 0.0
		elif aggregation == "sum":
			result = float(sum(nums))
		elif aggregation == "avg":
			result = float(sum(nums) / len(nums))
		elif aggregation == "min":
			result = float(min(nums))
		elif aggregation == "max":
			result = float(max(nums))
		else:
			result = 0.0

		item = {"group": key[0], "value": result}
		if secondary_group:
			item["series"] = key[1] if len(key) > 1 else None
		out.append(item)

	out.sort(key=lambda r: (str(r.get("group") or ""), str(r.get("series") or "")))
	return out


def run_funnel(
	*,
	doctype: str,
	milestones: list[dict],
	filters: list | dict | None = None,
	date_field: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict[str, Any]]:
	"""Funnel counts. Each milestone is {label, field, value} or {label, filters}."""
	doctype = assert_allowed_doctype(doctype)
	date_field = assert_date_field(doctype, date_field)
	base = _normalize_filters(filters)
	if date_field and from_date and to_date:
		base.append([doctype, date_field, "Between", [from_date, to_date]])

	out = []
	for step in milestones or []:
		step_filters = list(base)
		if step.get("filters"):
			step_filters.extend(_normalize_filters(step["filters"]))
		elif step.get("field") and "value" in step:
			assert_dimension_field(doctype, step["field"])
			step_filters.append([doctype, step["field"], "=", step["value"]])
		rows = frappe.get_list(
			doctype,
			filters=step_filters,
			fields=["name"],
			limit_page_length=0,
			ignore_permissions=False,
		)
		out.append({"label": step.get("label") or step.get("value") or "", "value": len(rows)})
	return out


def _normalize_filters(filters: list | dict | None) -> list:
	if not filters:
		return []
	if isinstance(filters, dict):
		return [[k, "=", v] for k, v in filters.items()]
	if isinstance(filters, list):
		return list(filters)
	raise ValueError("Invalid filters")


def _as_number(value) -> float | None:
	if value is None or value == "":
		return None
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def _is_dateish(value) -> bool:
	return isinstance(value, (date, datetime)) or (
		isinstance(value, str) and len(value) >= 8 and value[4:5] == "-"
	)


def _bucket_label(value, bucket: str) -> str:
	d = getdate(value)
	if bucket == "day":
		return d.isoformat()
	if bucket == "week":
		iso = d.isocalendar()
		return f"{iso.year}-W{iso.week:02d}"
	if bucket == "month":
		return f"{d.year}-{d.month:02d}"
	if bucket == "quarter":
		q = (d.month - 1) // 3 + 1
		return f"{d.year}-Q{q}"
	if bucket == "year":
		return str(d.year)
	return d.isoformat()

