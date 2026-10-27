# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_view_settings.crm_view_settings import (
	create,
	create_or_update_standard_view,
	fetch_and_update_kanban_columns,
	get_permission_query_conditions,
	has_permission,
	set_as_default,
	update,
)

GROUPING = {"fields": ["status"], "aggregates": [{"function": "count"}], "showTotals": True}


def stored_grouping(name):
	value = frappe.db.get_value("CRM View Settings", name, "group_by_settings")
	return json.loads(value) if value else None


class TestCRMViewSettings(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM View Settings", {"user": "Administrator"})

	def tearDown(self):
		frappe.db.rollback()

	def make_view(self, label, doctype, is_default=0):
		return frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"name": label,
				"label": label,
				"dt": doctype,
				"type": "list",
				"user": "Administrator",
				"is_default": is_default,
			}
		).insert()

	def test_name_only_call_clears_previous_default_of_same_doctype(self):
		old = self.make_view("Old Leads", "CRM Lead", is_default=1)
		new = self.make_view("New Leads", "CRM Lead")

		set_as_default(name=new.name)

		self.assertEqual(frappe.db.get_value("CRM View Settings", new.name, "is_default"), 1)
		self.assertEqual(frappe.db.get_value("CRM View Settings", old.name, "is_default"), 0)

	def test_name_only_call_keeps_default_of_other_doctype(self):
		deals = self.make_view("My Deals", "CRM Deal", is_default=1)
		leads = self.make_view("My Leads", "CRM Lead")

		set_as_default(name=leads.name)

		self.assertEqual(frappe.db.get_value("CRM View Settings", deals.name, "is_default"), 1)

	def test_saving_standard_view_keeps_it_default(self):
		set_as_default(type="kanban", doctype="CRM Lead")
		kanban = create_or_update_standard_view({"type": "kanban", "doctype": "CRM Lead"})

		self.assertEqual(frappe.db.get_value("CRM View Settings", kanban.name, "is_default"), 1)

	def test_saving_another_standard_view_keeps_chosen_default(self):
		set_as_default(type="kanban", doctype="CRM Lead")
		kanban = create_or_update_standard_view({"type": "kanban", "doctype": "CRM Lead"})
		list_view = create_or_update_standard_view({"type": "list", "doctype": "CRM Lead"})

		self.assertEqual(frappe.db.get_value("CRM View Settings", kanban.name, "is_default"), 1)
		self.assertEqual(frappe.db.get_value("CRM View Settings", list_view.name, "is_default"), 0)

	def test_standard_view_saves_and_clears_grouping(self):
		view = {"type": "list", "doctype": "CRM Lead", "group_by_settings": GROUPING}
		grouped = create_or_update_standard_view(view)
		self.assertEqual(stored_grouping(grouped.name), GROUPING)

		cleared = create_or_update_standard_view({**view, "group_by_settings": None})
		self.assertEqual(cleared.name, grouped.name)
		self.assertIsNone(stored_grouping(cleared.name))

	def test_saved_view_create_and_update_store_grouping(self):
		view = {
			"label": "Grouped Leads",
			"type": "list",
			"doctype": "CRM Lead",
			"group_by_settings": GROUPING,
		}
		doc = create(view)
		self.assertEqual(stored_grouping(doc.name), GROUPING)

		# the view dialog sends the stored JSON text back when editing
		update({**view, "name": doc.name, "group_by_settings": json.dumps(GROUPING)})
		self.assertEqual(stored_grouping(doc.name), GROUPING)

		update({**view, "name": doc.name, "group_by_settings": None})
		self.assertIsNone(stored_grouping(doc.name))

	def test_sales_user_cannot_update_foreign_kanban_columns(self):
		"""fetch_and_update_kanban_columns must use owner check, not DocType write."""
		admin_view = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"name": "Admin Kanban",
				"label": "Admin Kanban",
				"dt": "CRM Lead",
				"type": "kanban",
				"user": "Administrator",
				"column_field": "status",
				"kanban_columns": "[]",
			}
		).insert()
		sales = ensure_sales_user("view-sales@hier.test")

		frappe.set_user(sales)
		try:
			with self.assertRaises(frappe.PermissionError):
				fetch_and_update_kanban_columns(admin_view.name)
		finally:
			frappe.set_user("Administrator")

	def test_sales_user_cannot_set_foreign_view_as_default(self):
		admin_view = self.make_view("Admin Private Leads", "CRM Lead")
		sales = ensure_sales_user("view-sales@hier.test")

		frappe.set_user(sales)
		try:
			with self.assertRaises(frappe.PermissionError):
				set_as_default(name=admin_view.name)
			self.assertEqual(frappe.db.get_value("CRM View Settings", admin_view.name, "is_default"), 0)
		finally:
			frappe.set_user("Administrator")

	def test_sales_user_cannot_read_or_rename_foreign_private_view(self):
		admin_view = self.make_view("Admin Secret View", "CRM Lead")
		sales = ensure_sales_user("view-sales@hier.test")

		self.assertFalse(has_permission(admin_view, "read", sales))
		self.assertFalse(has_permission(admin_view, "write", sales))
		cond = get_permission_query_conditions(sales)
		self.assertIn("`tabCRM View Settings`.`user`", cond)
		self.assertIn("public", cond)

		frappe.set_user(sales)
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("CRM View Settings", admin_view.name)
		finally:
			frappe.set_user("Administrator")

	def test_sales_user_can_read_public_and_own_views(self):
		own = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"name": "Sales Own View",
				"label": "Sales Own View",
				"dt": "CRM Lead",
				"type": "list",
				"user": "view-sales@hier.test",
			}
		).insert(ignore_permissions=True)
		public = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"name": "Public Leads",
				"label": "Public Leads",
				"dt": "CRM Lead",
				"type": "list",
				"user": "Administrator",
				"public": 1,
			}
		).insert()
		sales = ensure_sales_user("view-sales@hier.test")

		self.assertTrue(has_permission(own, "read", sales))
		self.assertTrue(has_permission(own, "write", sales))
		self.assertTrue(has_permission(public, "read", sales))
		self.assertFalse(has_permission(public, "write", sales))


def ensure_sales_user(email):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user.add_roles("Sales User")
	return email
