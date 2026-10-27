# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Authenticate CRM API keys via Frappe auth_hooks.

Accepted schemes (raw key shown once at creation, hashed at rest):

* ``Authorization: Bearer <api_key>``
* ``Authorization: token <api_key>``
* ``Authorization: token <api_key>:<ignored>`` (Frappe-style token header)
* ``X-API-Key: <api_key>``
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

	frappe.set_user(row.user)
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
			# Frappe uses key:secret; CRM keys are a single opaque token. Accept either.
			if ":" in token:
				key, _, secret = token.partition(":")
				# Prefer the secret segment when both look non-empty (key:secret),
				# otherwise the whole token / left side.
				candidate = (secret or key).strip()
				# Also accept key-only forms and full "crm_…" keys on either side.
				if key.strip().startswith("crm_"):
					return key.strip()
				if candidate.startswith("crm_"):
					return candidate
				return candidate or None
			return token or None

	header_key = (frappe.get_request_header("X-API-Key", "") or "").strip()
	return header_key or None
