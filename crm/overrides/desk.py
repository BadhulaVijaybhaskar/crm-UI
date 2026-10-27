# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Desk (/app) redirects for sales roles — they use Astra CRM, not Desk."""

from __future__ import annotations

import frappe


_DESK_ROLES = frozenset({"System Manager", "Administrator"})


def redirect_sales_users_from_desk() -> None:
	"""Send non-desk users who hit /app to /crm instead of a permission modal."""
	try:
		path = (frappe.request.path or "").rstrip("/") or "/"
	except Exception:
		return

	if not path.startswith("/app"):
		return
	if frappe.session.user in (None, "Guest"):
		return

	roles = set(frappe.get_roles())
	if roles & _DESK_ROLES:
		return

	frappe.local.flags.redirect_location = "/crm"
	raise frappe.Redirect
