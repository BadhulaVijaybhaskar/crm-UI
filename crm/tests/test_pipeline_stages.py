# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.pipeline_stages import (
	delete_pipeline_stage,
	get_pipeline_stages,
	save_pipeline_stages,
)
from crm.utils.pipeline import get_status_pipeline_columns


class TestPipelineStages(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

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
		frappe.get_doc("User", email).add_roles(role)
		return email

	def test_sales_user_cannot_get_or_save_stages(self):
		sales = self._user("stage-sales@hier.test", "Stage Sales", "Sales User")
		frappe.set_user(sales)
		with self.assertRaises(frappe.PermissionError):
			get_pipeline_stages("CRM Deal")
		with self.assertRaises(frappe.PermissionError):
			save_pipeline_stages("CRM Deal", [])
		with self.assertRaises(frappe.PermissionError):
			delete_pipeline_stage("CRM Deal", "Qualification")

	def test_manager_can_reorder_and_recolour(self):
		manager = self._user("stage-manager@hier.test", "Stage Manager", "Sales Manager")
		frappe.set_user("Administrator")
		before = get_pipeline_stages("CRM Deal")
		self.assertTrue(before)
		payload = []
		for index, row in enumerate(reversed(before)):
			payload.append(
				{
					"name": row["name"],
					"label": row["label"],
					"type": row["type"],
					"color": "c1" if index == 0 else row["color"],
					"position": index + 1,
					"probability": row.get("probability", 0),
				}
			)
		frappe.set_user(manager)
		saved = save_pipeline_stages("CRM Deal", payload)
		self.assertEqual([s["name"] for s in saved], [p["name"] for p in payload])
		self.assertEqual(saved[0]["color"], "c1")
		cols = get_status_pipeline_columns("CRM Deal")
		self.assertEqual([c["name"] for c in cols], [p["name"] for p in payload])

	def test_delete_in_use_requires_remap(self):
		frappe.set_user("Administrator")
		stages = get_pipeline_stages("CRM Lead")
		self.assertGreaterEqual(len(stages), 2)
		source = stages[0]["name"]
		target = stages[1]["name"]
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "StageRemap",
				"status": source,
			}
		).insert(ignore_permissions=True)

		manager = self._user("stage-manager2@hier.test", "Stage Manager2", "Sales Manager")
		frappe.set_user(manager)
		with self.assertRaises(frappe.ValidationError):
			delete_pipeline_stage("CRM Lead", source)

		delete_pipeline_stage("CRM Lead", source, remap_to=target)
		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "status"), target)
		self.assertFalse(frappe.db.exists("CRM Lead Status", source))
