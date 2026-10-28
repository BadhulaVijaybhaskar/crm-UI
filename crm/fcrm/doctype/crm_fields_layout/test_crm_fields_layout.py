# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import (
	get_fields_layout,
	get_sidepanel_sections,
	save_fields_layout,
)


class TestCRMFieldsLayout(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _save_layout(self, doctype, type, layout):
		if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
			doc = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
		else:
			doc = frappe.new_doc("CRM Fields Layout")
			doc.dt = doctype
			doc.type = type
		doc.layout = json.dumps(layout)
		doc.save()

	def test_sidepanel_drops_unresolved_fieldnames(self):
		"""A fieldname that no longer exists on the doctype (e.g. a deleted custom
		field) must not be passed through as a bare string."""
		self._save_layout(
			"CRM Lead",
			"Side Panel",
			[
				{
					"label": "Details",
					"name": "details_section",
					"columns": [{"name": "column_1", "fields": ["first_name", "custom_deleted_field"]}],
				}
			],
		)

		sections = get_sidepanel_sections("CRM Lead")
		fields = sections[0]["columns"][0]["fields"]

		self.assertEqual([f["fieldname"] for f in fields], ["first_name"])
		self.assertTrue(all(isinstance(f, dict) for f in fields))

	def test_fields_layout_drops_unresolved_fieldnames(self):
		self._save_layout(
			"CRM Lead",
			"Quick Entry",
			[
				{
					"name": "first_tab",
					"sections": [
						{
							"name": "section_1",
							"columns": [
								{
									"name": "column_1",
									"fields": ["first_name", "custom_deleted_field", "email"],
								}
							],
						}
					],
				}
			],
		)

		tabs = get_fields_layout("CRM Lead", "Quick Entry")
		fields = tabs[0]["sections"][0]["columns"][0]["fields"]

		self.assertEqual([f["fieldname"] for f in fields], ["first_name", "email"])
		self.assertTrue(all(isinstance(f, dict) for f in fields))

	def _user(self, email, first_name, role):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles(role)
		return email

	def _layout_value(self, layout_type):
		return frappe.db.get_value(
			"CRM Fields Layout", {"dt": "CRM Lead", "type": layout_type}, "layout"
		)

	def test_sales_user_cannot_save_fields_layout(self):
		email = self._user("layout-sales@hier.test", "Layout Sales", "Sales User")
		before = self._layout_value("Data Fields")
		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			save_fields_layout("CRM Lead", "Data Fields", "[]")
		frappe.set_user("Administrator")
		self.assertEqual(before, self._layout_value("Data Fields"))

	def test_sales_manager_cannot_save_fields_layout(self):
		email = self._user(
			"layout-manager@hier.test", "Layout Manager", "Sales Manager"
		)
		before = self._layout_value("Data Fields")
		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			save_fields_layout("CRM Lead", "Data Fields", "[]")
		frappe.set_user("Administrator")
		self.assertEqual(before, self._layout_value("Data Fields"))

	def test_system_manager_can_save_fields_layout(self):
		email = self._user("layout-admin@hier.test", "Layout Admin", "System Manager")
		layout = '[{"name":"perm_tab"}]'
		frappe.set_user(email)
		saved = save_fields_layout("CRM Lead", "Grid Row", layout)
		self.assertEqual(saved, layout)
		self.assertEqual(
			frappe.db.get_value(
				"CRM Fields Layout", {"dt": "CRM Lead", "type": "Grid Row"}, "layout"
			),
			layout,
		)

	def test_administrator_can_save_fields_layout(self):
		layout = '[{"name":"admin_tab"}]'
		frappe.set_user("Administrator")
		saved = save_fields_layout("CRM Lead", "Required Fields", layout)
		self.assertEqual(saved, layout)
		self.assertEqual(
			frappe.db.get_value(
				"CRM Fields Layout", {"dt": "CRM Lead", "type": "Required Fields"}, "layout"
			),
			layout,
		)
