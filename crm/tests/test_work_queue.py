# Copyright (c) 2026, Astra and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, today

from crm.api.work_queue import get_work_queue, get_work_queue_count
from crm.tests import load_crm_user_test_records
from crm.tests.test_search_sqlite import SALES_USER, make_lead


class TestWorkQueue(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()

	def setUp(self):
		frappe.set_user(SALES_USER)
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.cache().delete_value(f"crm:work_queue_count:{SALES_USER}")

	def test_work_queue_count_shape_and_cache(self):
		first = get_work_queue_count()
		self.assertIn("count", first)
		self.assertIn("follow_ups", first)
		self.assertIn("quiet_leads", first)
		self.assertIsInstance(first["count"], int)

		second = get_work_queue_count()
		self.assertEqual(first["count"], second["count"])
		self.assertEqual(first["updated_at"], second["updated_at"])

	def test_follow_up_includes_due_task(self):
		lead = make_lead(SALES_USER)
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Call back about pricing",
				"assigned_to": SALES_USER,
				"status": "Todo",
				"priority": "High",
				"due_date": now_datetime(),
				"reference_doctype": "CRM Lead",
				"reference_docname": lead,
			}
		)
		task.insert(ignore_permissions=True)

		queue = get_work_queue(tab="follow_ups", priority="High,Medium,Low")
		ids = {item["task"] for section in queue["sections"] for item in section["items"]}
		self.assertIn(task.name, ids)

	def test_quiet_lead_after_seven_days_without_touch(self):
		lead_name = make_lead(SALES_USER)
		old = add_days(today(), -10)
		frappe.db.set_value(
			"CRM Lead",
			lead_name,
			{"creation": old, "modified": old},
			update_modified=False,
		)

		queue = get_work_queue(tab="quiet_leads")
		docs = {
			item["reference_docname"]
			for section in queue["sections"]
			for item in section["items"]
		}
		self.assertIn(lead_name, docs)
