# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
	set_status_with_history,
)
from crm.utils.pipeline import get_status_pipeline_columns


class TestCRMStatusChangeLog(FrappeTestCase):
	"""CRM-07: stage history + pipeline columns from existing Lead/Deal Status."""

	def tearDown(self):
		frappe.db.rollback()

	def test_lead_status_change_uses_lead_status_type(self):
		if not frappe.db.exists("CRM Lead Status", "New"):
			self.skipTest("CRM Lead Status New missing")
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Pipeline",
				"status": "New",
			}
		).insert(ignore_permissions=True)
		# Seed an open log as validate would
		add_status_change_log(lead)
		lead.save(ignore_permissions=True)

		lead.status = "Contacted" if frappe.db.exists("CRM Lead Status", "Contacted") else lead.status
		if lead.has_value_changed("status") or lead.status != "New":
			lead.status = "Contacted" if frappe.db.exists("CRM Lead Status", "Contacted") else "New"
		# Force change through save path
		before = lead.status
		target = "Qualified" if frappe.db.exists("CRM Lead Status", "Qualified") else before
		if target == before:
			self.skipTest("Need a second lead status")
		lead.status = target
		lead.save(ignore_permissions=True)
		lead.reload()
		self.assertTrue(lead.status_change_log)
		# Closed rows should carry Lead Status types when available
		closed = [r for r in lead.status_change_log if r.to]
		self.assertTrue(closed)
		lead_type = frappe.db.get_value("CRM Lead Status", target, "type")
		self.assertEqual(closed[-1].to_type, lead_type or closed[-1].to_type)

	def test_set_status_with_history_logs(self):
		if not frappe.db.exists("CRM Lead Status", "New"):
			self.skipTest("CRM Lead Status New missing")
		if not frappe.db.exists("CRM Lead Status", "Qualified"):
			self.skipTest("CRM Lead Status Qualified missing")
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Hist", "status": "New"}
		).insert(ignore_permissions=True)
		set_status_with_history("CRM Lead", lead.name, "Qualified", ignore_permissions=True)
		lead.reload()
		self.assertEqual(lead.status, "Qualified")
		self.assertTrue(any(r.to == "Qualified" for r in lead.status_change_log))

	def test_pipeline_columns_ordered_by_position(self):
		cols = get_status_pipeline_columns("CRM Lead")
		if not cols:
			self.skipTest("No lead statuses")
		positions = []
		for c in cols:
			pos = frappe.db.get_value("CRM Lead Status", c["name"], "position")
			positions.append(pos or 0)
		self.assertEqual(positions, sorted(positions))
