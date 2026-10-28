# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
from pathlib import Path

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

	def test_shipped_status_permissions_are_read_only_for_sales_user(self):
		root = Path(__file__).resolve().parents[1]
		for folder in ("crm_lead_status", "crm_deal_status"):
			data = json.loads((root / "fcrm" / "doctype" / folder / f"{folder}.json").read_text())
			perm = next(row for row in data["permissions"] if row["role"] == "Sales User")
			self.assertEqual(perm.get("read"), 1)
			self.assertFalse(perm.get("create"))
			self.assertFalse(perm.get("write"))
			self.assertFalse(perm.get("delete"))
			options = next(field["options"] for field in data["fields"] if field["fieldname"] == "color")
			for key in ("c1", "c6", "success", "danger", "warning", "teal", "blue", "gray", "green"):
				self.assertIn(key, options.split("\n"))

	def test_manager_can_rename_retype_and_set_probability(self):
		manager = self._user("stage-manager3@hier.test", "Stage Manager3", "Sales Manager")
		frappe.set_user(manager)
		created = save_pipeline_stages(
			"CRM Deal",
			[
				{
					"label": "ZZ Alpha",
					"type": "Open",
					"color": "green",
					"position": 970,
					"probability": 15,
				},
				{
					"label": "ZZ Beta",
					"type": "Open",
					"color": "c4",
					"position": 980,
					"probability": 20,
				},
			],
		)
		alpha = next(row for row in created if row["label"] == "ZZ Alpha")
		self.assertEqual(alpha["color"], "success")
		self.assertEqual(float(alpha["probability"]), 15.0)

		frappe.set_user("Administrator")
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"status": "ZZ Alpha",
				"expected_deal_value": 100,
				"expected_closure_date": "2026-12-31",
			}
		)
		deal.insert(ignore_permissions=True, ignore_mandatory=True)

		frappe.set_user(manager)
		saved = save_pipeline_stages(
			"CRM Deal",
			[
				{
					"name": "ZZ Alpha",
					"label": "ZZ Alpha Renamed",
					"type": "Ongoing",
					"color": "c2",
					"position": 975,
					"probability": 55,
				},
				{
					"name": "ZZ Beta",
					"label": "ZZ Beta",
					"type": "On Hold",
					"color": "warning",
					"position": 960,
					"probability": 5,
				},
			],
		)
		renamed = next(row for row in saved if row["label"] == "ZZ Alpha Renamed")
		held = next(row for row in saved if row["label"] == "ZZ Beta")
		self.assertEqual(renamed["name"], "ZZ Alpha Renamed")
		self.assertEqual(renamed["type"], "Ongoing")
		self.assertEqual(renamed["color"], "c2")
		self.assertEqual(float(renamed["probability"]), 55.0)
		self.assertEqual(held["type"], "On Hold")
		self.assertEqual(held["position"], 960)
		self.assertLess(
			[row["name"] for row in saved].index("ZZ Beta"),
			[row["name"] for row in saved].index("ZZ Alpha Renamed"),
		)
		columns = [column["name"] for column in get_status_pipeline_columns("CRM Deal")]
		self.assertLess(columns.index("ZZ Beta"), columns.index("ZZ Alpha Renamed"))
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "status"), "ZZ Alpha Renamed")
		self.assertFalse(frappe.db.exists("CRM Deal Status", "ZZ Alpha"))

	def test_kanban_keeps_column_flags_when_stages_move(self):
		manager = self._user("stage-manager4@hier.test", "Stage Manager4", "Sales Manager")
		frappe.set_user(manager)
		save_pipeline_stages(
			"CRM Deal",
			[
				{"label": "ZZ Lane A", "type": "Open", "color": "c1", "position": 940, "probability": 10},
				{"label": "ZZ Lane B", "type": "Open", "color": "c3", "position": 950, "probability": 10},
			],
		)
		frappe.set_user("Administrator")
		view = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"label": "ZZ Pipeline Kanban",
				"dt": "CRM Deal",
				"type": "kanban",
				"user": "Administrator",
				"column_field": "status",
				"kanban_columns": json.dumps(
					[
						{"name": "ZZ Lane B", "delete": True, "page_length": 40, "color": "gray"},
						{"name": "ZZ Lane A", "delete": False, "page_length": 15},
						{"name": "Not A Stage", "delete": True},
					]
				),
			}
		).insert(ignore_permissions=True)

		frappe.set_user(manager)
		save_pipeline_stages(
			"CRM Deal",
			[
				{"name": "ZZ Lane A", "label": "ZZ Lane A", "type": "Open", "color": "c5", "position": 930, "probability": 10},
				{"name": "ZZ Lane B", "label": "ZZ Lane B", "type": "Won", "color": "success", "position": 990, "probability": 100},
			],
		)
		stored = json.loads(frappe.db.get_value("CRM View Settings", view.name, "kanban_columns"))
		names = [column["name"] for column in stored]
		self.assertEqual(names, [column["name"] for column in get_status_pipeline_columns("CRM Deal")])
		self.assertLess(names.index("ZZ Lane A"), names.index("ZZ Lane B"))
		lane_b = next(column for column in stored if column["name"] == "ZZ Lane B")
		self.assertTrue(lane_b["delete"])
		self.assertEqual(lane_b["page_length"], 40)
		self.assertEqual(lane_b["color"], "success")
		lane_a = next(column for column in stored if column["name"] == "ZZ Lane A")
		self.assertFalse(lane_a["delete"])
		self.assertEqual(lane_a["page_length"], 15)
		self.assertNotIn("Not A Stage", names)

	def test_delete_in_use_deal_moves_deals_then_removes_stage(self):
		manager = self._user("stage-manager5@hier.test", "Stage Manager5", "Sales Manager")
		frappe.set_user(manager)
		save_pipeline_stages(
			"CRM Deal",
			[
				{"label": "ZZ Used Deal", "type": "Open", "color": "c2", "position": 910, "probability": 10},
				{"label": "ZZ Spare Deal", "type": "Open", "color": "c3", "position": 920, "probability": 10},
			],
		)
		frappe.set_user("Administrator")
		deal = frappe.get_doc({"doctype": "CRM Deal", "status": "ZZ Used Deal"})
		deal.insert(ignore_permissions=True, ignore_mandatory=True)
		frappe.set_user(manager)
		listed = get_pipeline_stages("CRM Deal")
		used = next(row for row in listed if row["name"] == "ZZ Used Deal")
		self.assertGreaterEqual(used["in_use"], 1)
		with self.assertRaises(frappe.ValidationError):
			delete_pipeline_stage("CRM Deal", "ZZ Used Deal")
		self.assertTrue(frappe.db.exists("CRM Deal Status", "ZZ Used Deal"))
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "status"), "ZZ Used Deal")

		delete_pipeline_stage("CRM Deal", "ZZ Used Deal", remap_to="ZZ Spare Deal")
		self.assertEqual(frappe.db.get_value("CRM Deal", deal.name, "status"), "ZZ Spare Deal")
		self.assertFalse(frappe.db.exists("CRM Deal Status", "ZZ Used Deal"))

	def test_cannot_delete_the_last_stage(self):
		frappe.set_user("Administrator")
		names = frappe.get_all("CRM Lead Status", pluck="name")
		if not names:
			self.skipTest("No lead statuses")
		keeper = names[0]
		frappe.db.set_value("CRM Lead", {"status": ("!=", keeper)}, "status", keeper)
		frappe.db.delete("CRM Lead Status", {"name": ("!=", keeper)})
		self.assertEqual(frappe.db.count("CRM Lead Status"), 1)

		manager = self._user("stage-manager6@hier.test", "Stage Manager6", "Sales Manager")
		frappe.set_user(manager)
		with self.assertRaises(frappe.ValidationError):
			delete_pipeline_stage("CRM Lead", keeper)
		self.assertTrue(frappe.db.exists("CRM Lead Status", keeper))

	def test_invalid_colour_is_rejected(self):
		manager = self._user("stage-manager7@hier.test", "Stage Manager7", "Sales Manager")
		frappe.set_user(manager)
		before = frappe.db.count("CRM Deal Status")
		with self.assertRaises(frappe.ValidationError):
			save_pipeline_stages(
				"CRM Deal",
				[{"label": "ZZ Bad Colour", "type": "Open", "color": "magenta", "position": 1}],
			)
		self.assertEqual(frappe.db.count("CRM Deal Status"), before)
		self.assertFalse(frappe.db.exists("CRM Deal Status", "ZZ Bad Colour"))

	def test_patch_clears_sales_user_write(self):
		from crm.patches.v1_0.restrict_status_and_layout_write import execute

		name = frappe.db.get_value(
			"DocPerm", {"parent": "CRM Lead Status", "role": "Sales User", "permlevel": 0}
		)
		if not name:
			self.skipTest("DocPerm row missing")
		frappe.db.set_value("DocPerm", name, {"create": 1, "write": 1, "delete": 1})
		custom = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": "CRM Deal Status",
				"role": "Sales User",
				"permlevel": 0,
				"read": 1,
				"write": 1,
				"create": 1,
				"delete": 1,
			}
		).insert(ignore_permissions=True)

		execute()

		self.assertEqual(frappe.db.get_value("DocPerm", name, "write"), 0)
		self.assertEqual(frappe.db.get_value("DocPerm", name, "create"), 0)
		self.assertEqual(frappe.db.get_value("DocPerm", name, "delete"), 0)
		self.assertEqual(frappe.db.get_value("DocPerm", name, "read"), 1)
		self.assertEqual(frappe.db.get_value("Custom DocPerm", custom.name, "write"), 0)
		self.assertEqual(frappe.db.get_value("Custom DocPerm", custom.name, "read"), 1)
