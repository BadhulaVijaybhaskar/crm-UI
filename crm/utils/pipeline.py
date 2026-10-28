"""Lead/Deal pipeline helpers — Kanban columns from CRM Lead/Deal Status."""

from __future__ import annotations

import frappe

STATUS_DOCTYPE = {
	"CRM Lead": "CRM Lead Status",
	"CRM Deal": "CRM Deal Status",
}


def get_status_pipeline_columns(parent_doctype: str | None = None, status_doctype: str | None = None) -> list[dict]:
	"""Return Kanban column dicts ordered by status ``position``, with colour.

	Reuses CRM Lead Status / CRM Deal Status (site-configurable stages).
	"""
	status_dt = status_doctype
	if not status_dt and parent_doctype:
		status_dt = STATUS_DOCTYPE.get(parent_doctype)
	if not status_dt:
		return []

	meta = frappe.get_meta(status_dt)
	fields = ["name"]
	has_position = meta.has_field("position")
	has_color = meta.has_field("color")
	if has_position:
		fields.append("position")
	if has_color:
		fields.append("color")

	order_by = "position asc" if has_position else "modified asc"
	rows = frappe.get_all(status_dt, fields=fields, order_by=order_by)
	columns = []
	for row in rows:
		col = {"name": row.name}
		if has_color and row.get("color"):
			col["color"] = row.color
		columns.append(col)
	return columns
