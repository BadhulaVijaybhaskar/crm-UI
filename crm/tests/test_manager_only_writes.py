# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase


class TestManagerOnlyWrites(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _sales_user(self, email="mgr-gate-sales@hier.test"):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Sales",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.get_doc("User", email).add_roles("Sales User")
		return email

	def test_reset_erpnext_form_script_requires_system_manager(self):
		sales = self._sales_user()
		settings = frappe.get_single("ERPNext CRM Settings")
		frappe.set_user(sales)
		with self.assertRaises(frappe.PermissionError):
			settings.reset_erpnext_form_script()

	def test_run_product_sync_requires_system_manager(self):
		sales = self._sales_user()
		settings = frappe.get_single("ERPNext CRM Settings")
		frappe.set_user(sales)
		with self.assertRaises(frappe.PermissionError):
			settings.run_product_sync()

	def test_fetch_facebook_pages_requires_manager(self):
		from crm.lead_syncing.doctype.lead_sync_source.facebook import (
			fetch_and_store_pages_from_facebook,
		)

		sales = self._sales_user()
		frappe.set_user(sales)
		with self.assertRaises(frappe.PermissionError):
			fetch_and_store_pages_from_facebook("token")
