# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json

import frappe
from frappe import _
from frappe.model.document import Document, get_controller
from frappe.utils import cint, parse_json


def _is_view_manager(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	roles = frappe.get_roles(user)
	return "System Manager" in roles or "Sales Manager" in roles


def _is_system_manager(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


class CRMViewSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		column_field: DF.Data | None
		columns: DF.Code | None
		dt: DF.Link | None
		filters: DF.Code | None
		group_by_field: DF.Data | None
		group_by_settings: DF.Code | None
		icon: DF.Data | None
		is_default: DF.Check
		is_standard: DF.Check
		kanban_columns: DF.Code | None
		kanban_fields: DF.Code | None
		label: DF.Data | None
		load_default_columns: DF.Check
		name: DF.Int | None
		order_by: DF.Code | None
		pinned: DF.Check
		public: DF.Check
		route_name: DF.Data | None
		rows: DF.Code | None
		title_field: DF.Data | None
		type: DF.Literal["list", "group_by", "kanban"]
		user: DF.Link | None
	# end: auto-generated types

	def validate(self):
		"""Close REST create/write holes Sales User had via unrestricted DocType write.

		Non-managers always own their row. Public / shared (user-empty) standard views
		are manager-only — matching `public()`. Personal is_standard copies for the
		session user remain allowed so list/kanban defaults still work.
		Only System Manager may create/assign a view owned by another user.
		"""
		session = frappe.session.user
		if not _is_view_manager(session):
			self.user = session
			if cint(self.public):
				frappe.throw(_("Not permitted to make views public"), frappe.PermissionError)
			if cint(self.is_standard) and self.user != session:
				frappe.throw(_("Not permitted to create standard views"), frappe.PermissionError)

		# Sales Manager (and below) cannot create a view for someone else.
		if self.user and self.user != session and not _is_system_manager(session):
			frappe.throw(_("Not permitted to create views for another user"), frappe.PermissionError)

		# Default flag for someone else's private view
		if cint(self.is_default) and self.user and self.user != session and not _is_system_manager(session):
			frappe.throw(_("Not permitted to set another user's view as default"), frappe.PermissionError)

		# Shared/system standard (no user) — managers only
		if cint(self.is_standard) and not self.user and not _is_view_manager(session):
			frappe.throw(_("Not permitted to create standard views"), frappe.PermissionError)


@frappe.whitelist()
def create(view: dict):
	view = frappe._dict(view)

	view.filters = parse_json(view.filters) or {}
	view.columns = parse_json(view.columns or "[]")
	view.rows = parse_json(view.rows or "[]")
	view.kanban_columns = parse_json(view.kanban_columns or "[]")
	view.kanban_fields = parse_json(view.kanban_fields or "[]")

	default_rows = sync_default_rows(view.doctype)
	view.rows = view.rows + default_rows if default_rows else view.rows
	view.rows = remove_duplicates(view.rows)

	if not view.kanban_columns and view.type == "kanban":
		view.kanban_columns = sync_default_columns(view)
	elif not view.columns:
		view.columns = sync_default_columns(view)

	doc = frappe.new_doc("CRM View Settings")
	doc.name = view.label
	doc.label = view.label
	doc.type = view.type or "list"
	doc.icon = view.icon
	doc.dt = view.doctype
	doc.user = frappe.session.user
	doc.route_name = view.route_name or get_route_name(view.doctype)
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(view.filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.group_by_settings = dump_group_by_settings(view.group_by_settings)
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(view.kanban_columns)
	doc.kanban_fields = json.dumps(view.kanban_fields)
	doc.columns = json.dumps(view.columns)
	doc.rows = json.dumps(view.rows)
	doc.insert()
	return doc


@frappe.whitelist()
def update(view: dict):
	view = frappe._dict(view)

	filters = parse_json(view.filters or {})
	columns = parse_json(view.columns or [])
	rows = parse_json(view.rows or [])
	kanban_columns = parse_json(view.kanban_columns or [])
	kanban_fields = parse_json(view.kanban_fields or [])

	default_rows = sync_default_rows(view.doctype)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	doc = frappe.get_doc("CRM View Settings", view.name)
	check_permission(doc)

	doc.label = view.label
	doc.type = view.type or "list"
	doc.icon = view.icon
	doc.route_name = view.route_name or get_route_name(view.doctype)
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.group_by_settings = dump_group_by_settings(view.group_by_settings)
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(kanban_columns)
	doc.kanban_fields = json.dumps(kanban_fields)
	doc.columns = json.dumps(columns)
	doc.rows = json.dumps(rows)
	doc.save()
	return doc


@frappe.whitelist()
def delete(name: str | int):
	if frappe.db.exists("CRM View Settings", name):
		doc = frappe.get_doc("CRM View Settings", name)
		check_permission(doc)
		frappe.delete_doc("CRM View Settings", name)


@frappe.whitelist()
def public(name: str | int, value: bool | int):
	if frappe.session.user != "Administrator" and "Sales Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("CRM View Settings", name)
	if doc.pinned:
		doc.pinned = False
	doc.public = bool(value)
	doc.user = "" if value else frappe.session.user
	doc.save()


@frappe.whitelist()
def pin(name: str | int, value: bool | int):
	doc = frappe.get_doc("CRM View Settings", name)
	check_permission(doc)
	doc.pinned = bool(value)
	doc.save()


def check_permission(doc):
	"""Administrator and System Manager can edit any view.
	If view is public, Sales Manager can edit.
	If view is private, only the view owner can edit."""
	if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
		pass
	elif doc.public and "Sales Manager" in frappe.get_roles():
		pass
	elif doc.user and doc.user == frappe.session.user:
		pass
	else:
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _can_read_view(doc, user: str) -> bool:
	"""Own views, public views, and system-created standards (shared defaults).

	Decision: standard views are shared defaults, so reading is OK when they are
	system-created (`user` empty). Another user's personal is_standard copy is not
	readable — those are per-user defaults, not shared.
	"""
	if doc.user == user or cint(doc.public):
		return True
	if cint(doc.is_standard) and not doc.user:
		return True
	return False


def get_permission_query_conditions(user=None):
	"""Non-managers only list own + public + system-created (user-empty) standards."""
	if not user:
		user = frappe.session.user

	if _is_system_manager(user):
		return ""

	escaped_user = frappe.db.escape(user)
	return (
		f"(`tabCRM View Settings`.`user` = {escaped_user}"
		f" OR `tabCRM View Settings`.`public` = 1"
		f" OR (`tabCRM View Settings`.`is_standard` = 1"
		f" AND IFNULL(`tabCRM View Settings`.`user`, '') = ''))"
	)


def has_permission(doc, ptype, user):
	"""Restrict REST/doc access: System Managers unrestricted; others use owner rules.

	Create is allowed at the DocType level; `validate` forces ownership and blocks
	public/shared-standard forges for non-managers.
	"""
	if not user:
		user = frappe.session.user

	if _is_system_manager(user):
		return True

	if ptype in ("read", "select", "export", "print", "email", "report", "share"):
		return _can_read_view(doc, user)

	if ptype == "create":
		return True

	# write / delete / etc. — same owner rules as check_permission
	if cint(doc.public) and "Sales Manager" in frappe.get_roles(user):
		return True
	if doc.user and doc.user == user:
		return True
	return False


def remove_duplicates(l):
	return list(dict.fromkeys(l))


def sync_default_rows(doctype, type="list"):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows


def sync_default_columns(view):
	doctype = view.dt or view.doctype
	list = get_controller(doctype)
	columns = []

	if view.type == "kanban" and view.column_field:
		field_meta = frappe.get_meta(doctype).get_field(view.column_field)
		if field_meta.fieldtype == "Link":
			from crm.utils.pipeline import get_status_pipeline_columns

			if view.column_field == "status" and doctype in ("CRM Lead", "CRM Deal"):
				columns = get_status_pipeline_columns(doctype)
			else:
				columns = frappe.get_all(
					field_meta.options,
					fields=["name"],
					order_by="modified asc",
				)
		elif field_meta.fieldtype == "Select":
			columns = [{"name": option} for option in field_meta.options.split("\n")]
	elif hasattr(list, "default_list_data"):
		columns = list.default_list_data().get("columns")

	return columns


@frappe.whitelist()
def set_as_default(name: str | int | None = None, type: str | None = None, doctype: str | None = None):
	if name:
		doc = frappe.get_doc("CRM View Settings", name)
		check_permission(doc)
		frappe.db.set_value("CRM View Settings", name, "is_default", 1)
		doctype = doctype or doc.dt
	else:
		doc = create_or_update_standard_view({"type": type, "doctype": doctype, "is_default": 1})
		name = doc.name

	# remove default from other views of same user and same doctype
	frappe.db.set_value(
		"CRM View Settings",
		{"name": ("!=", name), "user": frappe.session.user, "is_default": 1, "dt": doctype},
		"is_default",
		0,
	)


def dump_group_by_settings(value):
	"""Store the grouping as JSON text, from the list's object or a saved view's stored text."""
	return json.dumps(parse_json(value)) if value else None


@frappe.whitelist()
def create_or_update_standard_view(view: dict):
	view = frappe._dict(view)

	filters = parse_json(view.filters) or {}
	columns = parse_json(view.columns or "[]")
	rows = parse_json(view.rows or "[]")
	kanban_columns = parse_json(view.kanban_columns or "[]")
	kanban_fields = parse_json(view.kanban_fields or "[]")
	view.column_field = view.column_field or "status"

	default_rows = sync_default_rows(view.doctype, view.type)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	if not kanban_columns and view.type == "kanban":
		kanban_columns = sync_default_columns(view)
	elif not columns:
		columns = sync_default_columns(view)

	doc = frappe.db.exists(
		"CRM View Settings",
		{"dt": view.doctype, "type": view.type or "list", "is_standard": True, "user": frappe.session.user},
	)
	if doc:
		doc = frappe.get_doc("CRM View Settings", doc)
		doc.label = view.label
		doc.type = view.type or "list"
		doc.route_name = view.route_name or get_route_name(view.doctype)
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by or "modified desc"
		doc.group_by_field = view.group_by_field or "owner"
		doc.group_by_settings = dump_group_by_settings(view.group_by_settings)
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		# Only set_as_default changes the default; routine view saves leave it as is
		if view.is_default:
			doc.is_default = 1
		doc.save()
	else:
		doc = frappe.new_doc("CRM View Settings")

		label = "List"
		if view.type == "group_by":
			label = "Group By"
		elif view.type == "kanban":
			label = "Kanban"

		doc.name = view.label or label
		doc.label = view.label or label
		doc.type = view.type or "list"
		doc.dt = view.doctype
		doc.user = frappe.session.user
		doc.route_name = view.route_name or get_route_name(view.doctype)
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by or "modified desc"
		doc.group_by_field = view.group_by_field or "owner"
		doc.group_by_settings = dump_group_by_settings(view.group_by_settings)
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.is_standard = True
		doc.is_default = view.is_default or False
		doc.insert()

	return doc


@frappe.whitelist()
def fetch_and_update_kanban_columns(name: str | int):
	doc = frappe.get_doc("CRM View Settings", name)
	# Owner/public-manager check — DocType write alone is unrestricted for Sales User.
	check_permission(doc)
	if doc.type != "kanban":
		return

	new_columns = sync_default_columns(doc)
	existing_columns = parse_json(doc.kanban_columns or "[]")
	existing_column_names = [column.get("name") for column in existing_columns]
	for column in new_columns:
		if column.get("name") not in existing_column_names:
			existing_columns.append({"name": column.get("name"), "delete": True})

	doc.kanban_columns = json.dumps(existing_columns)
	doc.save()
	return doc.kanban_columns


def clear_old_versions(days=14):
	from frappe.utils import add_days, now_datetime

	frappe.db.delete(
		"Version",
		{
			"ref_doctype": "CRM View Settings",
			"creation": ("<", add_days(now_datetime(), -days)),
		},
	)


def get_route_name(doctype):
	# Example: "CRM Lead" -> "Leads"
	if doctype.startswith("CRM "):
		doctype = doctype[4:]

	if doctype[-1] != "s":
		doctype += "s"

	return doctype
