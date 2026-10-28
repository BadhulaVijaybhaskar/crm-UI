# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

import hashlib
import secrets

import frappe
from frappe.model.document import Document


class CRMAPIKey(Document):
	pass


def hash_api_key(raw: str) -> str:
	return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@frappe.whitelist()
def create_api_key(label: str, user: str | None = None):
	"""Create an API key. Returns the plaintext once; only the hash is stored.

	Authenticate later with ``Authorization: Bearer <key>``, ``Authorization: token <key>``
	(no colon — colon form is Frappe User API keys), or ``X-API-Key: <key>``.
	"""
	frappe.only_for("System Manager")
	user = user or frappe.session.user
	raw = "crm_" + secrets.token_urlsafe(32)
	doc = frappe.get_doc(
		{
			"doctype": "CRM API Key",
			"label": label,
			"user": user,
			"key_prefix": raw[:12],
			"key_hash": hash_api_key(raw),
			"disabled": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "api_key": raw, "key_prefix": doc.key_prefix}


@frappe.whitelist()
def list_api_keys():
	frappe.only_for("System Manager")
	return frappe.get_all(
		"CRM API Key",
		fields=["name", "label", "user", "key_prefix", "last_used", "disabled", "creation"],
		order_by="creation desc",
	)


@frappe.whitelist()
def set_api_key_disabled(name: str, disabled: int):
	frappe.only_for("System Manager")
	frappe.db.set_value("CRM API Key", name, "disabled", int(disabled))
	return {"name": name, "disabled": int(disabled)}
