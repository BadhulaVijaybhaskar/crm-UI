"""Clear the retired +910000000000 Connect agent placeholder from settings and call logs."""

from __future__ import annotations

import frappe

PLACEHOLDER = "+910000000000"


def execute():
	if frappe.db.exists("DocType", "Astra Connect Settings"):
		try:
			current = frappe.db.get_single_value("Astra Connect Settings", "connect_agent_number")
		except Exception:
			current = None
		if current and str(current).strip() == PLACEHOLDER:
			frappe.db.set_single_value("Astra Connect Settings", "connect_agent_number", None)

	if not frappe.db.exists("DocType", "CRM Call Log"):
		return

	for field in ("from", "to"):
		frappe.db.sql(
			f"""
			UPDATE `tabCRM Call Log`
			SET `{field}` = NULL
			WHERE `{field}` = %s
			""",
			(PLACEHOLDER,),
		)
