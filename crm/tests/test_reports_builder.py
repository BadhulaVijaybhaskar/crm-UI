# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Integration tests for the reports builder: permissions + aggregates."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import make_test_records
from frappe.utils import get_first_day, get_last_day, nowdate

from crm.api.reports import evaluate_kpi, list_dashboards
from crm.api.reports.aggregate import run_aggregate
from crm.api.reports.formula import FormulaError, evaluate_formula


class TestReportsBuilder(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.from_date = get_first_day(nowdate())
		cls.to_date = get_last_day(nowdate())
		cls.manager = "crm.manager@example.com"
		cls.user1 = "crm.user1@example.com"
		cls.user2 = "crm.user2@example.com"

		if frappe.db.exists("DocType", "FCRM Settings"):
			frappe.db.set_single_value("FCRM Settings", "currency", "USD")

		make_test_records("CRM Lead Status")
		make_test_records("CRM Deal Status")
		make_test_records("CRM Lead Source")
		make_test_records("CRM Organization")
		make_test_records("CRM Lead")
		make_test_records("CRM Deal")

		cls._ensure_users()

	@classmethod
	def _ensure_users(cls):
		for email, roles in (
			(cls.user1, ["Sales User"]),
			(cls.user2, ["Sales User"]),
			(cls.manager, ["Sales Manager", "Sales User"]),
		):
			if not frappe.db.exists("User", email):
				user = frappe.get_doc(
					{
						"doctype": "User",
						"email": email,
						"first_name": email.split("@")[0],
						"send_welcome_email": 0,
					}
				)
				user.insert(ignore_permissions=True)
			else:
				user = frappe.get_doc("User", email)
			for role in roles:
				user.add_roles(role)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_formula_injection_still_blocked_in_package(self):
		with self.assertRaises(FormulaError):
			evaluate_formula("__import__('os').system('id')", {})
		with self.assertRaises(FormulaError):
			evaluate_formula("{a}; import os", {"a": 1})

	def test_sales_user_kpi_excludes_others_deals(self):
		"""Sales User A must not see Sales User B's deal values in a sum KPI."""
		# Create two deals owned by different sales users
		status = frappe.db.get_value("CRM Deal Status", {"type": "Open"}, "name") or frappe.db.get_value(
			"CRM Deal Status", {}, "name"
		)
		org = frappe.db.get_value("CRM Organization", {}, "name")

		deal_a = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org,
				"status": status,
				"deal_owner": self.user1,
				"deal_value": 1000,
				"exchange_rate": 1,
				"currency": "USD",
			}
		).insert(ignore_permissions=True)

		deal_b = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org,
				"status": status,
				"deal_owner": self.user2,
				"deal_value": 5000,
				"exchange_rate": 1,
				"currency": "USD",
			}
		).insert(ignore_permissions=True)

		self.addCleanup(lambda: frappe.delete_doc("CRM Deal", deal_a.name, force=True, ignore_permissions=True))
		self.addCleanup(lambda: frappe.delete_doc("CRM Deal", deal_b.name, force=True, ignore_permissions=True))
		frappe.db.commit()

		frappe.set_user(self.user1)
		mine = run_aggregate(
			doctype="CRM Deal",
			aggregation="sum",
			field="deal_value",
			filters=[["CRM Deal", "name", "in", [deal_a.name, deal_b.name]]],
		)
		# user1 can only read their own deal → 1000, not 6000
		self.assertEqual(mine, 1000.0)

		frappe.set_user(self.user2)
		theirs = run_aggregate(
			doctype="CRM Deal",
			aggregation="sum",
			field="deal_value",
			filters=[["CRM Deal", "name", "in", [deal_a.name, deal_b.name]]],
		)
		self.assertEqual(theirs, 5000.0)

	def test_evaluate_kpi_respects_session_user(self):
		status = frappe.db.get_value("CRM Deal Status", {"type": "Open"}, "name") or frappe.db.get_value(
			"CRM Deal Status", {}, "name"
		)
		org = frappe.db.get_value("CRM Organization", {}, "name")
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org,
				"status": status,
				"deal_owner": self.user1,
				"deal_value": 2500,
				"exchange_rate": 1,
				"currency": "USD",
			}
		).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("CRM Deal", deal.name, force=True, ignore_permissions=True))
		frappe.db.commit()

		cfg = {
			"title": "My pipeline",
			"kpi_type": "simple",
			"doctype": "CRM Deal",
			"aggregation": "sum",
			"field": "deal_value",
			"filters": [["CRM Deal", "name", "=", deal.name]],
			"compare_with": "none",
		}

		frappe.set_user(self.user1)
		ok = evaluate_kpi(config=cfg)
		self.assertEqual(ok["value"], 2500.0)

		frappe.set_user(self.user2)
		blocked = evaluate_kpi(config=cfg)
		self.assertEqual(blocked["value"], 0.0)

	def test_personal_dashboard_crud_isolation(self):
		frappe.set_user(self.user1)
		doc = frappe.get_doc(
			{
				"doctype": "CRM Report Dashboard",
				"title": f"User1 Board {frappe.generate_hash(length=6)}",
				"dashboard_type": "Personal",
				"owner_user": self.user1,
				"layout": "[]",
			}
		).insert()

		frappe.set_user(self.user2)
		visible = frappe.get_list(
			"CRM Report Dashboard",
			filters={"name": doc.name},
			pluck="name",
		)
		self.assertEqual(visible, [])

		frappe.set_user(self.user1)
		listed = list_dashboards()
		self.assertTrue(any(d["name"] == doc.name for d in listed["personal"]))
		frappe.delete_doc("CRM Report Dashboard", doc.name)

	def test_reject_unwhitelisted_doctype(self):
		frappe.set_user(self.manager)
		with self.assertRaises(Exception):
			run_aggregate(doctype="User", aggregation="count")
