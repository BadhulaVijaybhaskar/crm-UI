# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import update_quick_filters


class TestQuickFiltersPermission(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_sales_user_cannot_update_global_quick_filters(self):
		email = "qf-sales@hier.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "QF Sales",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.get_doc("User", email).add_roles("Sales User")

		before = frappe.db.get_value(
			"CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"}, "json"
		)

		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			update_quick_filters(
				json.dumps(["status", "deal_owner", "hacked_filter"]),
				json.dumps(["status", "deal_owner"]),
				"CRM Deal",
			)

		frappe.set_user("Administrator")
		after = frappe.db.get_value(
			"CRM Global Settings", {"dt": "CRM Deal", "type": "Quick Filters"}, "json"
		)
		self.assertEqual(before, after)
