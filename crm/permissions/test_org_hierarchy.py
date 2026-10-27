# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import rebuild_tree

from crm.api.activities import get_activities
from crm.api.activities import get_activity_feed
from crm.permissions.org_hierarchy import (
	get_call_log_permission_query_conditions,
	get_contact_permission_query_conditions,
	get_deal_permission_query_conditions,
	get_lead_permission_query_conditions,
	get_note_permission_query_conditions,
	get_task_permission_query_conditions,
	has_call_log_permission,
	has_contact_permission,
	has_deal_permission,
	has_lead_permission,
	has_note_permission,
	has_task_permission,
	hierarchy_enabled,
)


class TestOrgHierarchy(IntegrationTestCase):
	"""
	Hierarchy structure used in tests:
	  manager@hier.test  (root)
	  ├── rep1@hier.test
	  └── rep2@hier.test
	  outsider@hier.test  (not in the hierarchy)
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create test users
		make_user("manager@hier.test", roles=["Sales Manager"])
		make_user("rep1@hier.test", roles=["Sales User"])
		make_user("rep2@hier.test", roles=["Sales User"])
		make_user("outsider@hier.test", roles=["Sales User"])

		# Build hierarchy
		mgr = make_hierarchy_node("manager@hier.test", is_group=1)
		make_hierarchy_node("rep1@hier.test", reports_to=mgr.name)
		make_hierarchy_node("rep2@hier.test", reports_to=mgr.name)
		rebuild_tree("CRM Sales Hierarchy")

		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 1
		settings.save(ignore_permissions=True)

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()

	def setUp(self):
		frappe.db.savepoint("test_org_hierarchy")

	def tearDown(self):
		frappe.db.rollback(save_point="test_org_hierarchy")

	# ------------------------------------------------------------------
	# hierarchy_enabled
	# ------------------------------------------------------------------

	def test_hierarchy_is_enabled(self):
		self.assertTrue(hierarchy_enabled())

	# ------------------------------------------------------------------
	# Lead permissions -- owner-based
	# ------------------------------------------------------------------

	def test_owner_can_read_own_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "rep1@hier.test"))

	def test_manager_can_read_direct_report_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	def test_manager_can_read_any_report_lead(self):
		lead = make_lead("rep2@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	def test_sibling_cannot_read_peer_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertFalse(has_lead_permission(lead, "read", "rep2@hier.test"))

	def test_outsider_cannot_read_team_lead(self):
		lead = make_lead("rep1@hier.test")
		self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_administrator_always_has_permission(self):
		lead = make_lead("rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "Administrator"))

	def test_sales_user_can_create_lead(self):
		new_lead = frappe.get_doc({"doctype": "CRM Lead", "lead_owner": "rep1@hier.test"})
		self.assertTrue(has_lead_permission(new_lead, "create", "rep1@hier.test"))

	# ------------------------------------------------------------------
	# Lead permissions -- ToDo-based
	# ------------------------------------------------------------------

	def test_direct_assignee_can_read_lead(self):
		lead = make_lead("rep1@hier.test")
		assign_todo("CRM Lead", lead.name, "outsider@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_cancelled_todo_does_not_grant_access(self):
		lead = make_lead("rep1@hier.test")
		assign_todo("CRM Lead", lead.name, "outsider@hier.test", status="Cancelled")
		self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))

	def test_manager_can_read_lead_assigned_to_report(self):
		lead = make_lead("outsider@hier.test")
		assign_todo("CRM Lead", lead.name, "rep1@hier.test")
		self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))

	# ------------------------------------------------------------------
	# Deal permissions
	# ------------------------------------------------------------------

	def test_manager_can_read_report_deal(self):
		deal = make_deal("rep2@hier.test")
		self.assertTrue(has_deal_permission(deal, "read", "manager@hier.test"))

	def test_peer_cannot_read_sibling_deal(self):
		deal = make_deal("rep2@hier.test")
		self.assertFalse(has_deal_permission(deal, "read", "rep1@hier.test"))

	def test_owner_can_write_and_delete_own_deal(self):
		deal = make_deal("rep1@hier.test")
		self.assertTrue(has_deal_permission(deal, "write", "rep1@hier.test"))
		self.assertTrue(has_deal_permission(deal, "delete", "rep1@hier.test"))

	def test_peer_cannot_write_or_delete_sibling_deal(self):
		deal = make_deal("rep1@hier.test")
		self.assertFalse(has_deal_permission(deal, "write", "rep2@hier.test"))
		self.assertFalse(has_deal_permission(deal, "delete", "rep2@hier.test"))

	# ------------------------------------------------------------------
	# Contact permissions -- owner + assignment + hierarchy
	# ------------------------------------------------------------------

	def test_owner_can_read_own_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertTrue(has_contact_permission(contact, "read", "rep1@hier.test"))

	def test_manager_can_read_direct_report_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertTrue(has_contact_permission(contact, "read", "manager@hier.test"))

	def test_sibling_cannot_read_peer_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertFalse(has_contact_permission(contact, "read", "rep2@hier.test"))

	def test_outsider_cannot_read_team_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertFalse(has_contact_permission(contact, "read", "outsider@hier.test"))

	def test_direct_assignee_can_read_contact(self):
		contact = make_contact("rep1@hier.test")
		assign_todo("Contact", contact.name, "outsider@hier.test")
		self.assertTrue(has_contact_permission(contact, "read", "outsider@hier.test"))

	def test_manager_can_read_contact_assigned_to_report(self):
		contact = make_contact("outsider@hier.test")
		assign_todo("Contact", contact.name, "rep1@hier.test")
		self.assertTrue(has_contact_permission(contact, "read", "manager@hier.test"))

	def test_owner_can_write_and_delete_own_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertTrue(has_contact_permission(contact, "write", "rep1@hier.test"))
		self.assertTrue(has_contact_permission(contact, "delete", "rep1@hier.test"))

	def test_peer_cannot_write_or_delete_sibling_contact(self):
		contact = make_contact("rep1@hier.test")
		self.assertFalse(has_contact_permission(contact, "write", "rep2@hier.test"))
		self.assertFalse(has_contact_permission(contact, "delete", "rep2@hier.test"))

	def test_sales_user_can_create_contact(self):
		new_contact = frappe.get_doc({"doctype": "Contact", "first_name": "New"})
		self.assertTrue(has_contact_permission(new_contact, "create", "rep1@hier.test"))

	def test_contact_query_conditions_non_empty_for_sales_user(self):
		self.assertTrue(get_contact_permission_query_conditions("rep1@hier.test"))

	def test_contact_query_conditions_empty_for_administrator(self):
		self.assertFalse(get_contact_permission_query_conditions("Administrator"))

	# ------------------------------------------------------------------
	# API surface: get_list / get / set_value refuse out-of-scope records
	# ------------------------------------------------------------------

	def test_api_list_hides_out_of_scope_lead(self):
		own = make_lead("rep1@hier.test")
		other = make_lead("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			names = {d.name for d in frappe.client.get_list("CRM Lead", fields=["name"], limit_page_length=50)}
		finally:
			frappe.set_user("Administrator")
		self.assertIn(own.name, names)
		self.assertNotIn(other.name, names)

	def test_api_get_refuses_out_of_scope_lead(self):
		lead = make_lead("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.client.get(doctype="CRM Lead", name=lead.name)
		finally:
			frappe.set_user("Administrator")

	def test_api_set_value_refuses_out_of_scope_lead(self):
		lead = make_lead("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.client.set_value("CRM Lead", lead.name, "first_name", "Nope")
		finally:
			frappe.set_user("Administrator")

	def test_api_list_hides_out_of_scope_deal(self):
		own = make_deal("rep1@hier.test")
		other = make_deal("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			names = {d.name for d in frappe.client.get_list("CRM Deal", fields=["name"], limit_page_length=50)}
		finally:
			frappe.set_user("Administrator")
		self.assertIn(own.name, names)
		self.assertNotIn(other.name, names)

	def test_api_get_refuses_out_of_scope_deal(self):
		deal = make_deal("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.client.get(doctype="CRM Deal", name=deal.name)
		finally:
			frappe.set_user("Administrator")

	def test_api_list_hides_out_of_scope_contact(self):
		own = make_contact("rep1@hier.test")
		other = make_contact("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			names = {d.name for d in frappe.client.get_list("Contact", fields=["name"], limit_page_length=50)}
		finally:
			frappe.set_user("Administrator")
		self.assertIn(own.name, names)
		self.assertNotIn(other.name, names)

	def test_api_get_refuses_out_of_scope_contact(self):
		contact = make_contact("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.client.get(doctype="Contact", name=contact.name)
		finally:
			frappe.set_user("Administrator")

	def test_api_set_value_refuses_out_of_scope_contact(self):
		contact = make_contact("rep2@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.client.set_value("Contact", contact.name, "first_name", "Nope")
		finally:
			frappe.set_user("Administrator")

	def test_api_manager_lists_team_contacts(self):
		rep_contact = make_contact("rep1@hier.test")
		outsider_contact = make_contact("outsider@hier.test")
		frappe.set_user("manager@hier.test")
		try:
			names = {d.name for d in frappe.client.get_list("Contact", fields=["name"], limit_page_length=50)}
		finally:
			frappe.set_user("Administrator")
		self.assertIn(rep_contact.name, names)
		self.assertNotIn(outsider_contact.name, names)

	def test_api_admin_lists_all_leads(self):
		a = make_lead("rep1@hier.test")
		b = make_lead("outsider@hier.test")
		# Administrator session (default) — no filter
		names = {d.name for d in frappe.client.get_list("CRM Lead", fields=["name"], limit_page_length=50)}
		self.assertIn(a.name, names)
		self.assertIn(b.name, names)

	# ------------------------------------------------------------------
	# Deal activities
	# ------------------------------------------------------------------

	def test_deal_activities_skip_lead_the_user_cannot_read(self):
		lead = make_lead("rep2@hier.test")
		deal = make_deal("rep1@hier.test")
		frappe.db.set_value("CRM Deal", deal.name, "lead", lead.name)

		frappe.set_user("rep1@hier.test")
		try:
			activities, calls, notes, tasks, attachments = get_activities(deal.name)
		finally:
			frappe.set_user("Administrator")

		# the deal's own timeline loads instead of the lead check failing the call
		self.assertTrue(any(a["activity_type"] == "creation" for a in activities))

		# the lead's history stays hidden
		self.assertEqual(calls, [])
		self.assertEqual(notes, [])
		self.assertEqual(tasks, [])
		self.assertEqual(attachments, [])

	# ------------------------------------------------------------------
	# Permission query conditions
	# ------------------------------------------------------------------

	def test_query_conditions_empty_for_administrator(self):
		self.assertFalse(get_lead_permission_query_conditions("Administrator"))

	def test_query_conditions_non_empty_for_regular_user(self):
		self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))

	def test_report_with_child_table_field_does_not_raise(self):
		make_lead("rep1@hier.test")
		self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))
		frappe.set_user("rep1@hier.test")
		try:
			frappe.get_list(
				"CRM Lead",
				fields=["name", "`tabCRM Products`.`amount`"],
				limit_page_length=5,
			)
		finally:
			frappe.set_user("Administrator")

	# ------------------------------------------------------------------
	# Hierarchy disabled
	# ------------------------------------------------------------------

	def test_hierarchy_disabled_sales_user_still_restricted_to_own(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			lead = make_lead("rep1@hier.test")
			contact = make_contact("rep1@hier.test")
			# Sales User default: cannot read another user's records even when feature is off
			self.assertFalse(has_lead_permission(lead, "read", "outsider@hier.test"))
			self.assertFalse(has_contact_permission(contact, "read", "outsider@hier.test"))
			# Sales Manager default: sees everything when feature is off
			self.assertTrue(has_lead_permission(lead, "read", "manager@hier.test"))
			self.assertTrue(has_contact_permission(contact, "read", "manager@hier.test"))
		finally:
			settings.enable_sales_hierarchy = 1
			settings.save(ignore_permissions=True)

	def test_query_conditions_when_hierarchy_disabled(self):
		settings = frappe.get_single("FCRM Settings")
		settings.enable_sales_hierarchy = 0
		settings.save(ignore_permissions=True)
		try:
			# Sales User still gets a filter (own + assigned)
			self.assertTrue(get_lead_permission_query_conditions("rep1@hier.test"))
			self.assertTrue(get_contact_permission_query_conditions("rep1@hier.test"))
			self.assertTrue(get_deal_permission_query_conditions("rep1@hier.test"))
			# Sales Manager has no filter (sees everything)
			self.assertFalse(get_lead_permission_query_conditions("manager@hier.test"))
			self.assertFalse(get_contact_permission_query_conditions("manager@hier.test"))
			self.assertFalse(get_deal_permission_query_conditions("manager@hier.test"))
		finally:
			settings.enable_sales_hierarchy = 1
			settings.save(ignore_permissions=True)

	# ------------------------------------------------------------------
	# Child docs (Call Log / Note / Task) inherit parent Lead access
	# ------------------------------------------------------------------

	def test_sales_user_cannot_list_other_owners_child_docs(self):
		"""Sales User must not see Call Log / Note / Task on leads they cannot read."""
		other_lead = make_lead("rep1@hier.test")
		call = make_call_log(other_lead.name, owner="rep1@hier.test")
		note = make_note(other_lead.name, owner="rep1@hier.test")
		task = make_task(other_lead.name, owner="rep1@hier.test", assigned_to="rep1@hier.test")

		self.assertFalse(has_call_log_permission(call, "read", "outsider@hier.test"))
		self.assertFalse(has_note_permission(note, "read", "outsider@hier.test"))
		self.assertFalse(has_task_permission(task, "read", "outsider@hier.test"))

		frappe.set_user("outsider@hier.test")
		try:
			self.assertNotIn(call.name, frappe.get_list("CRM Call Log", pluck="name", limit_page_length=500))
			self.assertNotIn(note.name, frappe.get_list("FCRM Note", pluck="name", limit_page_length=500))
			self.assertNotIn(task.name, frappe.get_list("CRM Task", pluck="name", limit_page_length=500))
			# REST-style client.get_list uses the same permission_query_conditions.
			from frappe.client import get_list as client_get_list

			self.assertNotIn(
				call.name,
				[r["name"] for r in client_get_list("CRM Call Log", fields=["name"], limit_page_length=500)],
			)
			self.assertNotIn(
				note.name,
				[r["name"] for r in client_get_list("FCRM Note", fields=["name"], limit_page_length=500)],
			)
			self.assertNotIn(
				task.name,
				[r["name"] for r in client_get_list("CRM Task", fields=["name"], limit_page_length=500)],
			)
		finally:
			frappe.set_user("Administrator")

	def test_sales_user_sees_child_docs_on_own_lead(self):
		lead = make_lead("rep1@hier.test")
		call = make_call_log(lead.name, owner="Administrator")  # Connect-style foreign owner
		note = make_note(lead.name, owner="Administrator")
		task = make_task(lead.name, owner="Administrator", assigned_to="rep1@hier.test")

		self.assertTrue(has_call_log_permission(call, "read", "rep1@hier.test"))
		self.assertTrue(has_note_permission(note, "read", "rep1@hier.test"))
		self.assertTrue(has_task_permission(task, "read", "rep1@hier.test"))

		frappe.set_user("rep1@hier.test")
		try:
			self.assertIn(call.name, frappe.get_list("CRM Call Log", pluck="name", limit_page_length=500))
			self.assertIn(note.name, frappe.get_list("FCRM Note", pluck="name", limit_page_length=500))
			self.assertIn(task.name, frappe.get_list("CRM Task", pluck="name", limit_page_length=500))
		finally:
			frappe.set_user("Administrator")

	def test_manager_sees_team_child_docs(self):
		lead = make_lead("rep1@hier.test")
		call = make_call_log(lead.name, owner="rep1@hier.test")
		note = make_note(lead.name, owner="rep1@hier.test")
		task = make_task(lead.name, owner="rep1@hier.test", assigned_to="rep1@hier.test")

		self.assertTrue(has_call_log_permission(call, "read", "manager@hier.test"))
		self.assertTrue(has_note_permission(note, "read", "manager@hier.test"))
		self.assertTrue(has_task_permission(task, "read", "manager@hier.test"))

		frappe.set_user("manager@hier.test")
		try:
			self.assertIn(call.name, frappe.get_list("CRM Call Log", pluck="name", limit_page_length=500))
			self.assertIn(note.name, frappe.get_list("FCRM Note", pluck="name", limit_page_length=500))
			self.assertIn(task.name, frappe.get_list("CRM Task", pluck="name", limit_page_length=500))
		finally:
			frappe.set_user("Administrator")

	def test_activity_feed_ignores_owner_arg_for_sales_user(self):
		"""Sales User cannot pull another owner's notes/calls via owner= on the feed."""
		other_lead = make_lead("rep1@hier.test")
		call = make_call_log(other_lead.name, owner="rep1@hier.test")
		note = make_note(other_lead.name, owner="rep1@hier.test")

		frappe.set_user("outsider@hier.test")
		try:
			for owner_arg in (None, "rep1@hier.test", "Administrator"):
				feed = get_activity_feed(owner=owner_arg, limit=100, start=0)
				names = {i["name"] for i in feed["items"]}
				self.assertNotIn(call.name, names)
				self.assertNotIn(note.name, names)
		finally:
			frappe.set_user("Administrator")

	def test_child_query_conditions_empty_for_administrator(self):
		self.assertFalse(get_call_log_permission_query_conditions("Administrator"))
		self.assertFalse(get_note_permission_query_conditions("Administrator"))
		self.assertFalse(get_task_permission_query_conditions("Administrator"))
		self.assertTrue(get_call_log_permission_query_conditions("rep1@hier.test"))

	def test_create_child_on_unreadable_parent_is_refused(self):
		"""Sales User must not create Note/Call Log on a parent they cannot read."""
		other_lead = make_lead("rep1@hier.test")
		frappe.set_user("outsider@hier.test")
		try:
			note = frappe.get_doc(
				{
					"doctype": "FCRM Note",
					"title": "Should fail",
					"content": "<p>x</p>",
					"reference_doctype": "CRM Lead",
					"reference_docname": other_lead.name,
				}
			)
			self.assertFalse(has_note_permission(note, "create", "outsider@hier.test"))
			with self.assertRaises(frappe.PermissionError):
				note.insert()

			call = frappe.get_doc(
				{
					"doctype": "CRM Call Log",
					"id": frappe.generate_hash(length=12),
					"type": "Outgoing",
					"status": "Completed",
					"from": "+911111111111",
					"to": "+912222222222",
					"reference_doctype": "CRM Lead",
					"reference_docname": other_lead.name,
				}
			)
			call.flags.ignore_mandatory = True
			self.assertFalse(has_call_log_permission(call, "create", "outsider@hier.test"))
			with self.assertRaises(frappe.PermissionError):
				call.insert()
		finally:
			frappe.set_user("Administrator")

	def test_create_child_on_own_lead_is_allowed(self):
		lead = make_lead("rep1@hier.test")
		frappe.set_user("rep1@hier.test")
		try:
			note = frappe.get_doc(
				{
					"doctype": "FCRM Note",
					"title": f"Own-{frappe.generate_hash(length=6)}",
					"content": "<p>ok</p>",
					"reference_doctype": "CRM Lead",
					"reference_docname": lead.name,
				}
			)
			self.assertTrue(has_note_permission(note, "create", "rep1@hier.test"))
			note.insert()
			self.assertTrue(frappe.db.exists("FCRM Note", note.name))

			call = frappe.get_doc(
				{
					"doctype": "CRM Call Log",
					"id": frappe.generate_hash(length=12),
					"type": "Outgoing",
					"status": "Completed",
					"from": "+911111111111",
					"to": "+912222222222",
					"reference_doctype": "CRM Lead",
					"reference_docname": lead.name,
				}
			)
			call.flags.ignore_mandatory = True
			self.assertTrue(has_call_log_permission(call, "create", "rep1@hier.test"))
			call.insert()
			self.assertTrue(frappe.db.exists("CRM Call Log", call.name))
		finally:
			frappe.set_user("Administrator")

	def test_reparent_child_to_unreadable_parent_is_refused(self):
		"""Owning a note does not allow moving its reference onto an unreadable parent."""
		own_lead = make_lead("rep1@hier.test")
		other_lead = make_lead("outsider@hier.test")
		note = make_note(own_lead.name, owner="rep1@hier.test")

		frappe.set_user("rep1@hier.test")
		try:
			note.reference_docname = other_lead.name
			self.assertFalse(has_note_permission(note, "write", "rep1@hier.test"))
			with self.assertRaises(frappe.PermissionError):
				note.save()
		finally:
			frappe.set_user("Administrator")


def make_call_log(lead_name, owner):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Call Log",
			"id": frappe.generate_hash(length=12),
			"type": "Outgoing",
			"status": "Completed",
			"from": "+911111111111",
			"to": "+912222222222",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_name,
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	frappe.db.set_value("CRM Call Log", doc.name, "owner", owner, update_modified=False)
	doc.reload()
	return doc


def make_note(lead_name, owner):
	doc = frappe.get_doc(
		{
			"doctype": "FCRM Note",
			"title": f"Note-{frappe.generate_hash(length=6)}",
			"content": "<p>secret summary</p>",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_name,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("FCRM Note", doc.name, "owner", owner, update_modified=False)
	doc.reload()
	return doc


def make_task(lead_name, owner, assigned_to=None):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Task",
			"title": f"Task-{frappe.generate_hash(length=6)}",
			"status": "Todo",
			"priority": "Medium",
			"reference_doctype": "CRM Lead",
			"reference_docname": lead_name,
			"assigned_to": assigned_to or owner,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("CRM Task", doc.name, "owner", owner, update_modified=False)
	doc.reload()
	return doc


def make_user(email, roles=None):
	if frappe.db.exists("User", email):
		return frappe.get_doc("User", email)
	u = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	for role in roles or []:
		u.add_roles(role)
	return u


def make_hierarchy_node(user, reports_to=None, is_group=0):
	existing = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, "name")
	if existing:
		return frappe.get_doc("CRM Sales Hierarchy", existing)
	return frappe.get_doc(
		{
			"doctype": "CRM Sales Hierarchy",
			"user": user,
			"reports_to": reports_to,
			"is_group": is_group,
		}
	).insert(ignore_permissions=True)


def make_lead(owner_email):
	doc = frappe.get_doc({"doctype": "CRM Lead", "lead_owner": owner_email, "first_name": "Test"})
	doc.flags.ignore_mandatory = True
	return doc.insert(ignore_permissions=True)


def make_deal(owner_email):
	doc = frappe.get_doc({"doctype": "CRM Deal", "deal_owner": owner_email, "organization": "Test Org"})
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	return doc.insert(ignore_permissions=True)


def make_contact(owner_email):
	doc = frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": f"Test-{frappe.generate_hash(length=5)}",
			"email_ids": [{"email_id": f"{frappe.generate_hash(length=6)}@hier.test", "is_primary": 1}],
		}
	)
	doc.insert(ignore_permissions=True)
	# Ownership for Contact is the document owner field (no contact_owner).
	frappe.db.set_value("Contact", doc.name, "owner", owner_email, update_modified=False)
	doc.reload()
	return doc


def assign_todo(doctype, docname, allocated_to, status="Open"):
	return frappe.get_doc(
		{
			"doctype": "ToDo",
			"reference_type": doctype,
			"reference_name": docname,
			"allocated_to": allocated_to,
			"status": status,
			"description": f"Test assignment to {allocated_to}",
		}
	).insert(ignore_permissions=True)
