# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pipeline stage editor for Lead and Deal statuses."""

from __future__ import annotations

import json
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import cint, flt, parse_json

from crm.utils.pipeline import get_status_pipeline_columns

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

# Same legacy names as the settings editor. Astra keys win when a name is both.
LEGACY_COLOUR_TO_ASTRA = {
	"black": "c6",
	"gray": "c6",
	"grey": "c6",
	"green": "success",
	"red": "danger",
	"pink": "danger",
	"orange": "c5",
	"amber": "warning",
	"yellow": "c5",
	"cyan": "c1",
	"violet": "c2",
	"purple": "c1",
}


@dataclass(frozen=True)
class _StageInput:
	name: str | None
	label: str
	stage_type: str
	color: str
	position: int
	probability: float | None


def _require_manager():
	frappe.only_for(["System Manager", "Sales Manager"], True)


def _status_doctype(parent_doctype: str) -> str:
	status_dt = STATUS_DOCTYPE.get((parent_doctype or "").strip())
	if not status_dt:
		frappe.throw(_("Unsupported doctype: {0}").format(parent_doctype), frappe.ValidationError)
	return status_dt


def _label_field(status_dt: str) -> str:
	return STATUS_LABEL_FIELD[status_dt]


def _parse_stages(stages):
	if isinstance(stages, str):
		try:
			stages = json.loads(stages or "[]")
		except json.JSONDecodeError:
			frappe.throw(_("Stages must be a list"), frappe.ValidationError)
	if not isinstance(stages, list):
		frappe.throw(_("Stages must be a list"), frappe.ValidationError)
	return stages


def _normalize_color(color: str | None) -> str:
	text = ("" if color is None else str(color)).strip()
	if not text:
		return "c6"
	if text in ASTRA_STAGE_COLOURS:
		return text
	mapped = LEGACY_COLOUR_TO_ASTRA.get(text)
	if mapped:
		return mapped
	frappe.throw(_("Invalid colour: {0}").format(text), frappe.ValidationError)


def _normalize_type(stage_type: str | None) -> str:
	stage_type = (stage_type or "Open").strip()
	if stage_type not in STAGE_TYPES:
		frappe.throw(_("Invalid stage type: {0}").format(stage_type), frappe.ValidationError)
	return stage_type


def _position(raw, index: int) -> int:
	if raw.get("position") in (None, ""):
		return index + 1
	return cint(raw.position)


def _probability(raw) -> float | None:
	if "probability" not in raw or raw.get("probability") in (None, ""):
		return None
	return flt(raw.probability)


def _stage_inputs(stages, existing_names: set[str]) -> list[_StageInput]:
	parsed: list[_StageInput] = []
	seen_labels: set[str] = set()
	seen_names: set[str] = set()
	for index, raw in enumerate(stages):
		if not isinstance(raw, dict):
			frappe.throw(_("Each stage must be an object"), frappe.ValidationError)
		raw = frappe._dict(raw)
		label = (raw.label or raw.name or "").strip()
		if not label:
			frappe.throw(_("Stage name is required"), frappe.ValidationError)
		if len(label) > 140:
			frappe.throw(_("Stage name {0} is too long").format(label), frappe.ValidationError)
		if label in seen_labels:
			frappe.throw(_("Duplicate stage name: {0}").format(label), frappe.ValidationError)
		seen_labels.add(label)
		name = (str(raw.name).strip() if raw.name else "") or None
		if name:
			if name in seen_names:
				frappe.throw(_("Stage {0} is listed more than once").format(name), frappe.ValidationError)
			seen_names.add(name)
		parsed.append(
			_StageInput(
				name=name,
				label=label,
				stage_type=_normalize_type(raw.type),
				color=_normalize_color(raw.color),
				position=_position(raw, index),
				probability=_probability(raw),
			)
		)

	vacated = {stage.name for stage in parsed if stage.name in existing_names and stage.name != stage.label}
	for stage in parsed:
		if stage.label in existing_names and stage.label != stage.name and stage.label not in vacated:
			frappe.throw(_("Stage {0} already exists").format(stage.label), frappe.ValidationError)
	return parsed


def _rename_stages(status_dt: str, plans: list[tuple[str, str]]) -> dict[str, str]:
	pending = [(old, new) for old, new in plans if old != new]
	done: dict[str, str] = {}
	guard = len(pending) + 1
	while pending and guard:
		guard -= 1
		blocked: list[tuple[str, str]] = []
		moved = False
		for old, new in pending:
			if frappe.db.exists(status_dt, new):
				blocked.append((old, new))
				continue
			frappe.rename_doc(status_dt, old, new, force=True, show_alert=False)
			done[old] = new
			moved = True
		if blocked and not moved:
			frappe.throw(_("Stage {0} already exists").format(blocked[0][1]), frappe.ValidationError)
		pending = blocked
	return done


def _apply_stages(status_dt: str, stages: list[_StageInput]) -> dict[str, str]:
	label_field = _label_field(status_dt)
	has_probability = frappe.get_meta(status_dt).has_field("probability")
	existing_names = set(frappe.get_all(status_dt, pluck="name"))
	plans: list[tuple[str, str]] = []
	for stage in stages:
		if not (stage.name and stage.name in existing_names):
			continue
		doc = frappe.get_doc(status_dt, stage.name)
		doc.type = stage.stage_type
		doc.color = stage.color
		doc.position = stage.position
		if has_probability and stage.probability is not None:
			doc.probability = stage.probability
		if stage.label == doc.name:
			doc.set(label_field, stage.label)
		doc.save()
		if stage.label != doc.name:
			plans.append((doc.name, stage.label))

	renames = _rename_stages(status_dt, plans)

	for stage in stages:
		if stage.name and stage.name in existing_names:
			continue
		doc = frappe.new_doc(status_dt)
		doc.set(label_field, stage.label)
		doc.type = stage.stage_type
		doc.color = stage.color
		doc.position = stage.position
		if has_probability and stage.probability is not None:
			doc.probability = stage.probability
		doc.insert()
	return renames


def _move_renamed_columns(by_name: dict[str, dict], renames: dict[str, str]) -> None:
	pending = {old: new for old, new in renames.items() if old and old != new}
	guard = len(pending) + 1
	while pending and guard:
		guard -= 1
		moved = False
		for old, new in list(pending.items()):
			if old not in by_name:
				pending.pop(old)
				moved = True
				continue
			if new in by_name and new in pending:
				continue
			column = by_name.pop(old)
			column["name"] = new
			by_name[new] = column
			pending.pop(old)
			moved = True
		if not moved:
			break


def _merge_kanban_columns(existing, ordered, renames: dict[str, str]) -> list[dict]:
	by_name: dict[str, dict] = {}
	for column in existing or []:
		if isinstance(column, dict) and column.get("name"):
			by_name[str(column["name"])] = dict(column)
	_move_renamed_columns(by_name, renames)
	merged = []
	for column in ordered:
		name = column.get("name")
		if not name:
			continue
		base = dict(by_name.get(name, {}))
		base["name"] = name
		if column.get("color"):
			base["color"] = column["color"]
		merged.append(base)
	return merged


def _sync_kanban_columns(parent_doctype: str, renames: dict[str, str] | None = None) -> None:
	# validate() blocks a manager from saving another user's view.
	# Column names are text in a Code field, so rename_doc does not move them.
	ordered = get_status_pipeline_columns(parent_doctype)
	view_names = frappe.get_all(
		"CRM View Settings",
		filters={"dt": parent_doctype, "type": "kanban", "column_field": "status"},
		pluck="name",
	)
	for name in view_names:
		raw = frappe.db.get_value("CRM View Settings", name, "kanban_columns")
		existing = parse_json(raw) if raw else []
		if not isinstance(existing, list):
			existing = []
		merged = _merge_kanban_columns(existing, ordered, renames or {})
		frappe.db.set_value("CRM View Settings", name, "kanban_columns", json.dumps(merged))


def _deal_settings_hold(stage: str) -> bool:
	if not frappe.get_meta("ERPNext CRM Settings").has_field("deal_status"):
		return False
	return frappe.db.get_single_value("ERPNext CRM Settings", "deal_status") == stage


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
	out = []
	for row in rows:
		item = {
			"name": row.name,
			"label": row.get(label_field) or row.name,
			"type": row.type or "Open",
			"color": row.color or "c6",
			"position": cint(row.position),
			"in_use": frappe.db.count(parent_doctype, {"status": row.name}),
		}
		if has_probability:
			item["probability"] = flt(row.probability)
		out.append(item)
	return out


@frappe.whitelist()
def save_pipeline_stages(parent_doctype: str, stages=None):
	_require_manager()
	status_dt = _status_doctype(parent_doctype)
	stages = _parse_stages(stages)
	if not stages:
		frappe.throw(_("At least one stage is required"), frappe.ValidationError)

	existing_names = set(frappe.get_all(status_dt, pluck="name"))
	parsed = _stage_inputs(stages, existing_names)
	renames = _apply_stages(status_dt, parsed)
	_sync_kanban_columns(parent_doctype, renames)
	return get_pipeline_stages(parent_doctype)


@frappe.whitelist()
def delete_pipeline_stage(parent_doctype: str, stage: str, remap_to: str | None = None):
	_require_manager()
	status_dt = _status_doctype(parent_doctype)
	stage = (stage or "").strip()
	if isinstance(remap_to, str):
		remap_to = remap_to.strip() or None
	if not stage or not frappe.db.exists(status_dt, stage):
		frappe.throw(_("Stage not found"), frappe.DoesNotExistError)

	if frappe.db.count(status_dt) <= 1:
		frappe.throw(_("Cannot delete the last stage"), frappe.ValidationError)

	if remap_to == stage:
		frappe.throw(_("Cannot map a stage onto itself"), frappe.ValidationError)
	if remap_to and not frappe.db.exists(status_dt, remap_to):
		frappe.throw(_("Target stage not found"), frappe.DoesNotExistError)

	in_use = frappe.db.count(parent_doctype, {"status": stage})
	settings_hold = parent_doctype == "CRM Deal" and _deal_settings_hold(stage)
	if in_use and not remap_to:
		frappe.throw(
			_("{0} is in use by {1} record(s). Choose another stage to map them to first.").format(
				stage, in_use
			),
			frappe.ValidationError,
		)
	if settings_hold and not remap_to:
		frappe.throw(
			_("{0} is the ERPNext deal status. Choose another stage to map it to first.").format(stage),
			frappe.ValidationError,
		)
	if remap_to and settings_hold:
		frappe.db.set_single_value("ERPNext CRM Settings", "deal_status", remap_to)
	if remap_to and in_use:
		# A full document save would reject a Lost row that has no lost reason.
		frappe.db.set_value(parent_doctype, {"status": stage}, "status", remap_to, update_modified=False)

	frappe.delete_doc(status_dt, stage)
	_sync_kanban_columns(parent_doctype)
	return {"deleted": stage, "remapped_to": remap_to, "remapped_count": in_use}
