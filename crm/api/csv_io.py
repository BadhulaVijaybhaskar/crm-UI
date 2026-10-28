# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""CRM UI CSV export / template download (permission-aware, formula-safe)."""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.utils.csv_safe import rows_to_csv

EXPORTABLE = {
	"CRM Lead": [
		"first_name",
		"last_name",
		"email",
		"mobile_no",
		"organization",
		"status",
		"source",
		"lead_owner",
		"website",
		"territory",
	],
	"Contact": [
		"first_name",
		"last_name",
		"email_id",
		"mobile_no",
		"phone",
		"company_name",
		"designation",
		"status",
	],
	"CRM Deal": [
		"organization",
		"status",
		"deal_owner",
		"probability",
		"annual_revenue",
		"territory",
		"email",
		"mobile_no",
	],
	"CRM Organization": [
		"organization_name",
		"website",
		"industry",
		"territory",
		"annual_revenue",
		"no_of_employees",
	],
}


@frappe.whitelist()
def download_template(doctype: str):
	"""CSV header template for Lead / Contact import in the CRM UI."""
	if doctype not in EXPORTABLE:
		frappe.throw(_("CSV template is not available for {0}").format(doctype))
	frappe.has_permission(doctype, "create", throw=True)
	headers = EXPORTABLE[doctype]
	payload = rows_to_csv(headers, [])
	_file_response(f"{doctype.replace(' ', '_').lower()}_template.csv", payload)


@frappe.whitelist()
def export_csv(
	doctype: str,
	fields: str | list | None = None,
	filters: str | dict | list | None = None,
	order_by: str | None = None,
	limit: int | None = None,
	title: str | None = None,
):
	"""Export list rows as formula-safe CSV. Respects DocType permissions + query conditions."""
	if doctype not in EXPORTABLE:
		frappe.throw(_("CSV export is not available for {0}").format(doctype))
	# Prefer export perm when the role has it; otherwise require read.
	if _has_export_perm(doctype):
		frappe.has_permission(doctype, "export", throw=True)
	else:
		frappe.has_permission(doctype, "read", throw=True)

	fieldnames = _parse_fields(doctype, fields)
	parsed_filters = _parse_json(filters, {})
	parsed_order = order_by or "modified desc"
	page_length = min(int(limit or 10000), 50000)

	rows = frappe.get_list(
		doctype,
		filters=parsed_filters,
		fields=fieldnames,
		order_by=parsed_order,
		limit_page_length=page_length,
	)

	values = [[row.get(f) for f in fieldnames] for row in rows]
	payload = rows_to_csv(fieldnames, values)
	filename = f"{(title or doctype).replace(' ', '_')}.csv"
	_file_response(filename, payload)


def _has_export_perm(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, "export"))
	except Exception:
		return False


def _parse_fields(doctype: str, fields) -> list[str]:
	parsed = _parse_json(fields, None)
	if not parsed:
		return list(EXPORTABLE[doctype])
	if isinstance(parsed, str):
		parsed = [parsed]
	allowed = set(EXPORTABLE[doctype]) | {"name", "owner", "modified", "creation"}
	# Also allow any field the user can read on the meta (list columns).
	meta = frappe.get_meta(doctype)
	for df in meta.fields:
		if df.fieldname:
			allowed.add(df.fieldname)
	out = []
	for f in parsed:
		name = f[1:] if isinstance(f, str) and f.startswith("`") else f
		name = name.strip("`") if isinstance(name, str) else name
		if isinstance(name, str) and name in allowed and name not in out:
			out.append(name)
	return out or list(EXPORTABLE[doctype])


def _parse_json(value, default):
	if value is None or value == "":
		return default
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		return default


def _file_response(filename: str, content: str):
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content.encode("utf-8")
	frappe.local.response.type = "download"
