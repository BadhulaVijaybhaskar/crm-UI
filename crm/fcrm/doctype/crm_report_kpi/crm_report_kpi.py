# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.reports.formula import FormulaError, validate_formula
from crm.api.reports.whitelist import (
	assert_aggregation,
	assert_allowed_doctype,
	assert_date_field,
	assert_numeric_field,
)


class CRMReportKPI(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		if not self.title:
			frappe.throw(_("Title is required"))

		if not self.owner_user:
			self.owner_user = frappe.session.user

		roles = frappe.get_roles(frappe.session.user)
		is_manager = "System Manager" in roles or "Sales Manager" in roles
		if self.owner_user != frappe.session.user and not is_manager:
			frappe.throw(_("You can only create KPIs for yourself"))

		if self.visibility == "Everyone" and not is_manager:
			frappe.throw(_("Only managers can share KPIs with everyone"))

		self._validate_filters_json()
		if self.kpi_type == "Simple":
			self._validate_simple()
		else:
			self._validate_calculated()

	def _validate_filters_json(self):
		raw = self.filters_json or "[]"
		try:
			parsed = json.loads(raw) if isinstance(raw, str) else raw
		except (TypeError, json.JSONDecodeError):
			frappe.throw(_("Filters must be valid JSON"))
		self.filters_json = json.dumps(parsed)

	def _validate_simple(self):
		doctype = assert_allowed_doctype(self.source_doctype)
		agg = assert_aggregation(self.aggregation)
		assert_numeric_field(doctype, self.aggregate_field, agg)
		assert_date_field(doctype, self.date_field)

	def _validate_calculated(self):
		raw = self.formula_inputs or "{}"
		try:
			inputs = json.loads(raw) if isinstance(raw, str) else raw
		except (TypeError, json.JSONDecodeError):
			frappe.throw(_("Formula inputs must be valid JSON"))
		if not isinstance(inputs, dict):
			frappe.throw(_("Formula inputs must be an object"))
		for key, cfg in inputs.items():
			if not isinstance(cfg, dict):
				frappe.throw(_("Each formula input must be an object"))
			doctype = assert_allowed_doctype(cfg.get("doctype") or cfg.get("source_doctype"))
			agg = assert_aggregation(cfg.get("aggregation", "count"))
			assert_numeric_field(doctype, cfg.get("field") or cfg.get("aggregate_field"), agg)
		self.formula_inputs = json.dumps(inputs)
		try:
			validate_formula(self.formula or "", allowed_refs=set(inputs.keys()))
		except FormulaError as e:
			frappe.throw(_("Invalid formula: {0}").format(str(e)))


def get_permission_query_conditions(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	roles = frappe.get_roles(user)
	escaped_user = frappe.db.escape(user)
	role_list = ", ".join(frappe.db.escape(r) for r in roles) or "''"
	return (
		f"(`tabCRM Report KPI`.`owner_user` = {escaped_user}"
		f" OR `tabCRM Report KPI`.`visibility` = 'Everyone'"
		f" OR (`tabCRM Report KPI`.`visibility` = 'Role'"
		f" AND `tabCRM Report KPI`.`shared_role` IN ({role_list})))"
	)


def has_permission(doc, ptype, user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	roles = frappe.get_roles(user)
	is_manager = "Sales Manager" in roles

	if doc.owner_user == user:
		return True
	if doc.visibility == "Everyone":
		if ptype in ("read", "select", "export", "print", "email", "report"):
			return True
		return is_manager
	if doc.visibility == "Role" and doc.shared_role in roles:
		if ptype in ("read", "select", "export", "print", "email", "report"):
			return True
		return is_manager
	return False
