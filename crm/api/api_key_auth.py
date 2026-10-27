# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Authenticate CRM API keys via Frappe auth_hooks.

Accepted schemes (raw key shown once at creation, hashed at rest):

* ``Authorization: Bearer <api_key>``
* ``Authorization: token <api_key>``  (opaque key, no colon)
* ``X-API-Key: <api_key>``

Note: ``Authorization: token <key>:<secret>`` is handled by Frappe's User API
key validator *before* auth_hooks and will 401 for CRM keys. Use Bearer or
X-API-Key (or ``token <key>`` without a colon) instead.
"""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from crm.fcrm.doctype.crm_api_key.crm_api_key import hash_api_key


def validate():
	"""auth_hooks entry — set the session user when a valid CRM API key is present."""
	if frappe.session.user and frappe.session.user not in ("", "Guest"):
		return

	raw = _extract_api_key_from_request()
	if not raw:
		return

	row = frappe.db.get_value(
		"CRM API Key",
		{"key_hash": hash_api_key(raw), "disabled": 0},
		["name", "user"],
		as_dict=True,
	)
	if not row or not row.user:
		# Present but invalid — reject rather than falling through as Guest.
		frappe.throw(
			frappe._("Invalid API key"),
			frappe.AuthenticationError,
		)

	if not frappe.db.exists("User", {"name": row.user, "enabled": 1}):
		frappe.throw(
			frappe._("API key user is disabled"),
			frappe.AuthenticationError,
		)

	# frappe.set_user() clears form_dict (frappe/__init__.py) — preserve request args
	# the same way frappe/auth.py does around set_user during token auth.
	form_dict = getattr(frappe.local, "form_dict", None)
	saved = dict(form_dict) if form_dict is not None else None

	frappe.set_user(row.user)

	if saved is not None:
		frappe.local.form_dict = frappe._dict(saved)

	login_manager = getattr(frappe.local, "login_manager", None)
	if login_manager is not None:
		login_manager.user = row.user
	try:
		frappe.db.set_value(
			"CRM API Key",
			row.name,
			"last_used",
			now_datetime(),
			update_modified=False,
		)
	except Exception:
		pass


def _extract_api_key_from_request() -> str | None:
	authorization = (frappe.get_request_header("Authorization", "") or "").strip()
	if authorization:
		lower = authorization.lower()
		if lower.startswith("bearer "):
			return authorization[7:].strip() or None
		if lower.startswith("token "):
			token = authorization[6:].strip()
			# Colon form is owned by Frappe User API keys (runs before auth_hooks).
			# Only accept opaque CRM keys here (no colon).
			if ":" in token:
				return None
			return token or None

	header_key = (frappe.get_request_header("X-API-Key", "") or "").strip()
	return header_key or None
