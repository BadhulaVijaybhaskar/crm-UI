# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pipeline stage editor API — list, save, delete-with-remap for Lead/Deal statuses."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt

STATUS_DOCTYPE = {
	"CRM Lead": "CRM Lead Status",
	"CRM Deal": "CRM Deal Status",
}

STATUS_LABEL_FIELD = {
	"CRM Lead Status": "lead_status",
	"CRM Deal Status": "deal_status",
}

STAGE_TYPES = ("Open", "Ongoing", "On Hold", "Won", "Lost")

ASTRA_STAGE_COLOURS = (
	"c1",
	"c2",
	"c3",
	"c4",
	"c5",
	"c6",
	"success",
	"danger",
	"warning",
	"teal",
	"blue",
)

LEGACY_COLOURS = (
	"black",
	"gray",
	"blue",
	"green",
	"red",
	"pink",
	"orange",
	"amber",
	"yellow",
	"cyan",
	"teal",
	"violet",
	"purple",
)

ALLOWED_COLOURS = set(ASTRA_STAGE_COLOURS) | set(LEGACY_COLOURS)


def _require_manager():
	frappe.only_for(["System Manager", "Sales Manager"], True)


def _status_doctype(parent_doctype: str) -> str:
	status_dt = STATUS_DOCTYPE.get(parent_doctype)
	if not status_dt:
		frappe.throw(_("Unsupported doctype: {0}").format(parent_doctype), frappe.ValidationError)
	return status_dt


def _label_field(status_dt: str) -> str:
	return STATUS_LABEL_FIELD[status_dt]


def _parse_stages(stages):
	if isinstance(stages, str):
		stages = json.loads(stages or "[]")
	if not isinstance(stages, list):
		frappe.throw(_("Stages must be a list"), frappe.ValidationError)
	return stages


def _in_use_counts(parent_doctype: str) -> dict[str, int]:
	rows = frappe.get_all(
		parent_doctype,
		fields=["status", "count(name) as cnt"],
		group_by="status",
	)
	return {row.status: cint(row.cnt) for row in rows if row.status}


def _normalize_color(color: str | None) -> str:
	color = (color or "c6").strip()
	if color not in ALLOWED_COLOURS:
		frappe.throw(_("Invalid colour: {0}").format(color), frappe.ValidationError)
	return color


def _normalize_type(stage_type: str | None) -> str:
	stage_type = (stage_type or "Open").strip()
	if stage_type not in STAGE_TYPES:
		frappe.throw(_("Invalid stage type: {0}").format(stage_type), frappe.ValidationError)
	return stage_type


@frappe.whitelist()
def get_pipeline_stages(parent_doctype: str):
	_require_manager()
	status_dt = _status_doctype(parent_doctype)
	label_field = _label_field(status_dt)
	meta = frappe.get_meta(status_dt)
	fields = ["name", label_field, "type", "color", "position"]
	has_probability = meta.has_field("probability")
	if has_probability:
		fields.append("probability")

	rows = frappe.get_all(status_dt, fields=fields, order_by="position asc")
	counts = _in_use_counts(parent_doctype)
	out = []
	for row in rows:
		item = {
			"name": row.name,
			"label": row.get(label_field) or row.name,
			"type": row.type or "Open",
			"color": row.color or "c6",
			"position": cint(row.position),
			"in_use": counts.get(row.name, 0),
		}
		if has_probability:
			item["probability"] = flt(row.probability)
		out.append(item)
	return out


@frappe.whitelist()
def save_pipeline_stages(parent_doctype: str, stages):
	_require_manager()
	status_dt = _status_doctype(parent_doctype)
	label_field = _label_field(status_dt)
	has_probability = frappe.get_meta(status_dt).has_field("probability")
	stages = _parse_stages(stages)
	if not stages:
		frappe.throw(_("At least one stage is required"), frappe.ValidationError)

	existing = {d.name: d for d in frappe.get_all(status_dt, fields=["name"], as_list=False)}
	seen_labels = set()

	for index, raw in enumerate(stages):
		raw = frappe._dict(raw)
		label = (raw.label or raw.name or "").strip()
		if not label:
			frappe.throw(_("Stage name is required"), frappe.ValidationError)
		if label in seen_labels:
			frappe.throw(_("Duplicate stage name: {0}").format(label), frappe.ValidationError)
		seen_labels.add(label)

		stage_type = _normalize_type(raw.type)
		color = _normalize_color(raw.color)
		position = cint(raw.position) or (index + 1)
		name = raw.name

		if name and name in existing:
			if name != label and not frappe.db.exists(status_dt, label):
				frappe.rename_doc(status_dt, name, label, force=True, show_alert=False)
				name = label
			elif name != label and frappe.db.exists(status_dt, label):
				frappe.throw(_("Stage {0} already exists").format(label), frappe.ValidationError)
			doc = frappe.get_doc(status_dt, name)
			doc.type = stage_type
			doc.color = color
			doc.position = position
			if has_probability:
				doc.probability = flt(raw.probability)
			doc.save()
		else:
			if frappe.db.exists(status_dt, label):
				frappe.throw(_("Stage {0} already exists").format(label), frappe.ValidationError)
			doc = frappe.new_doc(status_dt)
			doc.set(label_field, label)
			doc.type = stage_type
			doc.color = color
			doc.position = position
			if has_probability:
				doc.probability = flt(raw.probability)
			doc.insert()

	_sync_kanban_columns(parent_doctype)
	return get_pipeline_stages(parent_doctype)


@frappe.whitelist()
def delete_pipeline_stage(parent_doctype: str, stage: str, remap_to: str | None = None):
	_require_manager()
	status_dt = _status_doctype(parent_doctype)
	if not stage or not frappe.db.exists(status_dt, stage):
		frappe.throw(_("Stage not found"), frappe.DoesNotExistError)

	total = frappe.db.count(status_dt)
	if total <= 1:
		frappe.throw(_("Cannot delete the last stage"), frappe.ValidationError)

	in_use = frappe.db.count(parent_doctype, {"status": stage})
	if in_use:
		if not remap_to:
			frappe.throw(
				_("{0} is in use by {1} record(s). Choose another stage to map them to first.").format(
					stage, in_use
				),
				frappe.ValidationError,
			)
		if remap_to == stage:
			frappe.throw(_("Cannot map a stage onto itself"), frappe.ValidationError)
		if not frappe.db.exists(status_dt, remap_to):
			frappe.throw(_("Target stage not found"), frappe.DoesNotExistError)
		frappe.db.set_value(parent_doctype, {"status": stage}, "status", remap_to, update_modified=False)

	frappe.delete_doc(status_dt, stage)
	_sync_kanban_columns(parent_doctype)
	return {"deleted": stage, "remapped_to": remap_to, "remapped_count": in_use}


def _sync_kanban_columns(parent_doctype: str):
	"""Reorder saved kanban views so the board follows status.position."""
	from frappe.utils import parse_json

	from crm.utils.pipeline import get_status_pipeline_columns

	ordered = get_status_pipeline_columns(parent_doctype)
	ordered_names = [col.get("name") for col in ordered]
	views = frappe.get_all(
		"CRM View Settings",
		filters={"dt": parent_doctype, "type": "kanban", "column_field": "status"},
		pluck="name",
	)
	for name in views:
		doc = frappe.get_doc("CRM View Settings", name)
		existing = parse_json(doc.kanban_columns or "[]") or []
		by_name = {col.get("name"): col for col in existing if col.get("name")}
		merged = []
		for col in ordered:
			prev = by_name.pop(col.get("name"), None)
			if prev:
				prev.update({k: v for k, v in col.items() if v is not None})
				prev.pop("delete", None)
				merged.append(prev)
			else:
				merged.append(dict(col))
		# Keep columns that were manually hidden / leftover under delete flag
		for leftover in by_name.values():
			leftover["delete"] = True
			merged.append(leftover)
		doc.kanban_columns = json.dumps(merged)
		doc.flags.ignore_permissions = True
		doc.save()
		# Preserve name list length for callers that only care about order
		_ = ordered_names
