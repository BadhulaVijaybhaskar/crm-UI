# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.caching import request_cache

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
	# Standard Contact has no contact_owner; document owner is the ownership signal.
	"Contact": "owner",
}


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


def _permission_query_conditions(user: str | None, doctype: str):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return ""

	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	# Sales Manager outside the tree retains the default ie sees everything
	if "Sales Manager" in roles and not in_tree:
		return ""

	owner_field = _OWNER_FIELD[doctype]
	DT = frappe.qb.DocType(doctype)
	Todo = frappe.qb.DocType("ToDo").as_("_todo")

	if in_tree:
		# Owner is the user themselves or any member of their subtree
		q1 = (DT[owner_field] == user) | DT[owner_field].isin(_team_mem_query(user))
		q_doc_owner = (DT.owner == user) | DT.owner.isin(_team_mem_query(user))
		# Assigned to the user or any member of their subtree by ToDo
		q2 = DT.name.isin(
			frappe.qb.from_(Todo)
			.select(Todo.reference_name)
			.where(
				(Todo.reference_type == doctype)
				& (Todo.status != "Cancelled")
				& ((Todo.allocated_to == user) | (Todo.allocated_to.isin(_team_mem_query(user))))
			)
		)
		if owner_field == "owner":
			return q1 | q2
		return q1 | q_doc_owner | q2

	# Sales User default: own records (owner field and/or lead_owner/deal_owner)
	# and records directly assigned to them. Including document owner covers
	# API/CSV creates that left the dedicated owner field blank.
	q1 = DT[owner_field] == user
	q_doc_owner = DT.owner == user
	q2 = DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where((Todo.reference_type == doctype) & (Todo.status != "Cancelled") & (Todo.allocated_to == user))
	)
	if owner_field == "owner":
		return q1 | q2
	return q1 | q_doc_owner | q2


def get_lead_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Lead")
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def get_deal_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "CRM Deal")
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def get_contact_permission_query_conditions(user=None):
	cond = _permission_query_conditions(user, "Contact")
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def _has_permission(doc, ptype, user, doctype: str) -> bool | None:
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True

	if ptype == "create" or not doc.name:
		return True

	in_tree = hierarchy_enabled() and _in_hierarchy(user)
	if "Sales Manager" in roles and not in_tree:
		return True

	conditions = _permission_query_conditions(user, doctype)
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(conditions).limit(1).run()
	)


def has_lead_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Deal")


def has_contact_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "Contact")


# --------------------------------------------------------------------------- #
# Child docs (Call Log / Note / Task) — inherit access from parent Lead/Deal/
# Contact. Managers/admins keep team-wide (or unrestricted) visibility.
# --------------------------------------------------------------------------- #

_CHILD_REF_PARENTS = ("CRM Lead", "CRM Deal", "Contact")


def _is_unrestricted_user(user: str) -> bool:
	if user == "Administrator":
		return True
	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True
	in_tree = hierarchy_enabled() and _in_hierarchy(user)
	# Sales Manager outside the tree sees everything (same as parent doctypes).
	if "Sales Manager" in roles and not in_tree:
		return True
	return False


def _accessible_parent_names(user: str, parent_doctype: str):
	"""Subquery of parent names ``user`` may read under hierarchy rules."""
	Parent = frappe.qb.DocType(parent_doctype)
	pcond = _permission_query_conditions(user, parent_doctype)
	if pcond:
		return frappe.qb.from_(Parent).select(Parent.name).where(pcond)
	return frappe.qb.from_(Parent).select(Parent.name)


def _child_permission_query_conditions(user: str | None, doctype: str):
	"""Scope Call Log / Note / Task rows to parents the user can read (+ own/assignee)."""
	if not user:
		user = frappe.session.user

	if _is_unrestricted_user(user):
		return ""

	DT = frappe.qb.DocType(doctype)
	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	own = DT.owner == user
	if in_tree:
		own = own | DT.owner.isin(_team_mem_query(user))

	parent_access = None
	for parent_doctype in _CHILD_REF_PARENTS:
		accessible = _accessible_parent_names(user, parent_doctype)
		q = (DT.reference_doctype == parent_doctype) & DT.reference_docname.isin(accessible)
		parent_access = q if parent_access is None else (parent_access | q)

	combined = own | parent_access

	if doctype == "CRM Task":
		assigned = DT.assigned_to == user
		if in_tree:
			assigned = assigned | DT.assigned_to.isin(_team_mem_query(user))
		combined = combined | assigned

	if doctype == "CRM Call Log":
		on_call = (DT.caller == user) | (DT.receiver == user)
		if in_tree:
			on_call = (
				on_call
				| DT.caller.isin(_team_mem_query(user))
				| DT.receiver.isin(_team_mem_query(user))
			)
		combined = combined | on_call

		# Calls may link a Lead/Deal only via Dynamic Link (no reference_* set).
		Link = frappe.qb.DocType("Dynamic Link")
		for parent_doctype in ("CRM Lead", "CRM Deal"):
			accessible = _accessible_parent_names(user, parent_doctype)
			via_link = DT.name.isin(
				frappe.qb.from_(Link)
				.select(Link.parent)
				.where(
					(Link.parenttype == doctype)
					& (Link.link_doctype == parent_doctype)
					& Link.link_name.isin(accessible)
				)
			)
			combined = combined | via_link

	return combined


def _cond_sql(cond) -> str:
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""


def get_call_log_permission_query_conditions(user=None):
	return _cond_sql(_child_permission_query_conditions(user, "CRM Call Log"))


def get_note_permission_query_conditions(user=None):
	return _cond_sql(_child_permission_query_conditions(user, "FCRM Note"))


def get_task_permission_query_conditions(user=None):
	return _cond_sql(_child_permission_query_conditions(user, "CRM Task"))


def _has_child_permission(doc, ptype, user, doctype: str) -> bool | None:
	if not user:
		user = frappe.session.user

	if _is_unrestricted_user(user):
		return True

	if ptype == "create" or not doc.name:
		return True

	conditions = _child_permission_query_conditions(user, doctype)
	if not conditions:
		return True
	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(conditions).limit(1).run()
	)


def has_call_log_permission(doc, ptype, user):
	return _has_child_permission(doc, ptype, user, "CRM Call Log")


def has_note_permission(doc, ptype, user):
	return _has_child_permission(doc, ptype, user, "FCRM Note")


def has_task_permission(doc, ptype, user):
	return _has_child_permission(doc, ptype, user, "CRM Task")


def _fallback_integration_owner() -> str | None:
	"""Owner for Guest/webhook creates when no Assignment Rule assignee exists."""
	try:
		configured = frappe.db.get_single_value("Astra Connect Settings", "default_lead_owner")
		if configured and frappe.db.exists("User", configured):
			return configured
	except Exception:
		pass
	if frappe.db.exists("User", "Administrator"):
		return "Administrator"
	return None


def apply_default_record_owner(doc, method=None):
	"""Set lead_owner/deal_owner only when still empty, without preempting Assignment Rule.

	- Prefer an open ToDo assignee (round-robin / availability).
	- Never call assign_agent here — that creates a ToDo and skips Assignment Rule.
	- Logged-in creates with no rule fall back to the creator (session user).
	- Guest/webhook creates fall back to configured default_lead_owner / Administrator.
	"""
	owner_field = _OWNER_FIELD.get(doc.doctype)
	if not owner_field or owner_field == "owner":
		return
	if doc.get(owner_field):
		return

	assignees = []
	try:
		assignees = list(doc.get_assigned_users() or [])
	except Exception:
		assignees = []
	if assignees:
		doc.db_set(owner_field, assignees[0], update_modified=False)
		return

	user = frappe.session.user
	if user not in (None, "", "Guest"):
		# No Assignment Rule assignee — record belongs to its creator.
		doc.db_set(owner_field, user, update_modified=False)
		return

	fallback = _fallback_integration_owner()
	if not fallback:
		return
	doc.db_set(owner_field, fallback, update_modified=False)
	try:
		frappe.db.set_value(doc.doctype, doc.name, "owner", fallback, update_modified=False)
	except Exception:
		pass


def _in_hierarchy(user: str) -> bool:
	return bool(frappe.db.exists("CRM Sales Hierarchy", {"user": user}))


def _team_mem_query(user: str):
	Mgr = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmgr")
	Member = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmem")
	return (
		frappe.qb.from_(Mgr)
		.join(Member)
		.on((Member.lft >= Mgr.lft) & (Member.lft <= Mgr.rgt))
		.select(Member.user)
		.where(Mgr.user == user)
	)
