# Copyright (c) 2026, Astra and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from crm.api.activities import (
	_call_log_list_fields,
	get_activity_feed,
	get_my_day,
	get_stage_change_activities,
)
from crm.tests import load_crm_user_test_records
from crm.tests.test_search_sqlite import OTHER_SALES_USER, SALES_USER, make_lead


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

	def test_call_log_list_fields_keep_creation(self):
		"""Meta.has_field('creation') is False — the feed must still select it."""
		fields = _call_log_list_fields()
		self.assertIn("creation", fields)
		self.assertIn("name", fields)

	def test_calls_feed_includes_creation_for_administrator(self):
		"""P2: without creation in fields, in_range() dropped every call."""
		frappe.set_user("Administrator")
		call = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": frappe.generate_hash(length=12),
				"type": "Outgoing",
				"status": "Completed",
				"from": "+911234567890",
				"to": "+919876543210",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.lead,
			}
		)
		call.flags.ignore_mandatory = True
		call.insert(ignore_permissions=True)
		frappe.db.set_value("CRM Call Log", call.name, "owner", "Administrator", update_modified=False)

		feed = get_activity_feed(activity_type="calls", limit=100, start=0)
		names = {i["name"] for i in feed["items"]}
		self.assertIn(call.name, names)
		row = next(i for i in feed["items"] if i["name"] == call.name)
		self.assertTrue(row.get("creation"))

		# Date-range path also needs creation
		feed_ranged = get_activity_feed(
			activity_type="calls",
			from_date=today(),
			to_date=today(),
			limit=100,
			start=0,
		)
		self.assertIn(call.name, {i["name"] for i in feed_ranged["items"]})

	def test_sales_user_feed_cannot_fetch_other_owners_via_owner_arg(self):
		other_lead = make_lead(OTHER_SALES_USER)
		frappe.set_user("Administrator")
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Other owner note",
				"content": "<p>private</p>",
				"reference_doctype": "CRM Lead",
				"reference_docname": other_lead,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("FCRM Note", note.name, "owner", OTHER_SALES_USER, update_modified=False)

		frappe.set_user(SALES_USER)
		feed = get_activity_feed(owner=OTHER_SALES_USER, activity_type="notes", limit=100, start=0)
		self.assertNotIn(note.name, {i["name"] for i in feed["items"]})
