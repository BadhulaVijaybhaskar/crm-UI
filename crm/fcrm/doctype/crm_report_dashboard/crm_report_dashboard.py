# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class CRMReportDashboard(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		if not self.title:
			frappe.throw(_("Title is required"))
		self._validate_layout()
		self._validate_ownership()
		if cint(self.is_default):
			self._clear_other_defaults()

	def _validate_layout(self):
		raw = self.layout or "[]"
		try:
			layout = json.loads(raw) if isinstance(raw, str) else raw
		except (TypeError, json.JSONDecodeError):
			frappe.throw(_("Layout must be valid JSON"))
		if not isinstance(layout, list):
			frappe.throw(_("Layout must be a JSON array"))
		self.layout = json.dumps(layout)

	def _validate_ownership(self):
		user = frappe.session.user
		roles = frappe.get_roles(user)
		is_manager = "System Manager" in roles or "Sales Manager" in roles

		if self.is_new():
			if self.dashboard_type == "Personal":
				self.owner_user = self.owner_user or user
				if self.owner_user != user and not is_manager:
					frappe.throw(_("You can only create personal dashboards for yourself"))
				self.shared_role = None
			elif self.dashboard_type == "Team":
				if not is_manager:
					frappe.throw(_("Only managers can create team dashboards"))
				if not self.shared_role:
					self.shared_role = "Sales User"
				self.owner_user = None
			return

		if not is_manager:
			if self.dashboard_type != "Personal" or self.owner_user != user:
				frappe.throw(_("Not permitted"), frappe.PermissionError)

	def _clear_other_defaults(self):
		filters = {"is_default": 1, "name": ["!=", self.name or ""]}
		if self.dashboard_type == "Personal":
			filters["owner_user"] = self.owner_user or frappe.session.user
			filters["dashboard_type"] = "Personal"
		else:
			filters["dashboard_type"] = "Team"
			if self.shared_role:
				filters["shared_role"] = self.shared_role
		for name in frappe.get_all("CRM Report Dashboard", filters=filters, pluck="name"):
			frappe.db.set_value("CRM Report Dashboard", name, "is_default", 0)


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	roles = frappe.get_roles(user)
	escaped_user = frappe.db.escape(user)
	role_list = ", ".join(frappe.db.escape(r) for r in roles) or "''"
	# Personal owned by user OR team dashboards shared to one of the user's roles
	return (
		f"(`tabCRM Report Dashboard`.`dashboard_type` = 'Personal'"
		f" AND `tabCRM Report Dashboard`.`owner_user` = {escaped_user})"
		f" OR (`tabCRM Report Dashboard`.`dashboard_type` = 'Team'"
		f" AND `tabCRM Report Dashboard`.`shared_role` IN ({role_list}))"
	)


def has_permission(doc, ptype, user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	roles = frappe.get_roles(user)
	is_manager = "Sales Manager" in roles

	if doc.dashboard_type == "Personal":
		if doc.owner_user == user:
			return True
		return False

	# Team
	if doc.shared_role and doc.shared_role in roles:
		if ptype in ("read", "select", "export", "print", "email", "report"):
			return True
		return is_manager
	return False


def default_sales_overview_layout() -> str:
	"""Starter layout matching the reports builder design."""
	tiles = [
		{
			"id": "open_pipeline",
			"type": "kpi",
			"title": "Open pipeline",
			"layout": {"x": 0, "y": 0, "w": 3, "h": 1, "i": "open_pipeline"},
			"config": {
				"kpi_type": "simple",
				"doctype": "CRM Deal",
				"aggregation": "sum",
				"field": "deal_value",
				"date_field": "creation",
				"filters": [],
				"format": "currency",
			},
		},
		{
			"id": "won_quarter",
			"type": "kpi",
			"title": "Won this quarter",
			"layout": {"x": 3, "y": 0, "w": 3, "h": 1, "i": "won_quarter"},
			"config": {
				"kpi_type": "simple",
				"doctype": "CRM Deal",
				"aggregation": "sum",
				"field": "deal_value",
				"date_field": "closed_date",
				"filters": [],
				"format": "currency",
			},
		},
		{
			"id": "pipeline_by_stage",
			"type": "bar",
			"title": "Pipeline by stage",
			"layout": {"x": 0, "y": 1, "w": 8, "h": 3, "i": "pipeline_by_stage"},
			"config": {
				"doctype": "CRM Deal",
				"aggregation": "sum",
				"field": "deal_value",
				"group_by": "status",
				"date_field": "creation",
				"stacked": False,
			},
		},
		{
			"id": "won_by_month",
			"type": "line",
			"title": "Won value by month",
			"layout": {"x": 8, "y": 1, "w": 4, "h": 3, "i": "won_by_month"},
			"config": {
				"doctype": "CRM Deal",
				"aggregation": "sum",
				"field": "deal_value",
				"group_by": "closed_date",
				"date_bucket": "month",
				"date_field": "closed_date",
			},
		},
	]
	return json.dumps(tiles)


def ensure_default_dashboards(user: str | None = None):
	"""Create a personal Sales overview for the user if they have none."""
	user = user or frappe.session.user
	existing = frappe.get_all(
		"CRM Report Dashboard",
		filters={"dashboard_type": "Personal", "owner_user": user},
		limit=1,
	)
	if existing:
		return
	doc = frappe.get_doc(
		{
			"doctype": "CRM Report Dashboard",
			"title": "Sales overview",
			"dashboard_type": "Personal",
			"owner_user": user,
			"is_default": 1,
			"layout": default_sales_overview_layout(),
		}
	)
	doc.insert(ignore_permissions=True)
