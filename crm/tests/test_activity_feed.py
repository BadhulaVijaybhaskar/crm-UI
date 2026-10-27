# Copyright (c) 2026, Astra and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.activities import get_activity_feed, get_my_day, get_stage_change_activities
from crm.tests import load_crm_user_test_records
from crm.tests.test_search_sqlite import SALES_USER, make_lead


class TestActivityFeed(IntegrationTestCase):
	"""CRM-08: global feed + My day + stage_change timeline rows."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()
		cls.lead = make_lead(SALES_USER)

	def setUp(self):
		frappe.set_user(SALES_USER)
		self.addCleanup(frappe.set_user, "Administrator")

	def test_activity_feed_returns_paged_payload(self):
		result = get_activity_feed(limit=10, start=0)
		self.assertIn("items", result)
		self.assertIn("has_more", result)
		self.assertIsInstance(result["items"], list)

	def test_my_day_returns_agenda_buckets(self):
		result = get_my_day()
		self.assertIn("tasks", result)
		self.assertIn("calls", result)
		self.assertIn("meetings", result)
		self.assertIn("date", result)

	def test_stage_change_helper_skips_open_rows(self):
		# No closed moves yet — should be an empty list, not an error
		rows = get_stage_change_activities("CRM Lead", self.lead, is_lead=True)
		self.assertIsInstance(rows, list)
		self.assertTrue(all(r.get("activity_type") == "stage_change" for r in rows))
		self.assertTrue(all(r.get("data", {}).get("to") for r in rows))
