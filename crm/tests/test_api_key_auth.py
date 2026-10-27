# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""End-to-end auth for CRM API keys (auth_hooks)."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.api_key_auth import validate
from crm.fcrm.doctype.crm_api_key.crm_api_key import create_api_key, hash_api_key
from crm.tests import load_crm_user_test_records

SALES_USER = "crm.user1@example.com"


class TestApiKeyAuth(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		load_crm_user_test_records()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM API Key")
		self.addCleanup(frappe.set_user, "Administrator")

	def _create_key(self, user=SALES_USER):
		return create_api_key("e2e-auth", user=user)

	def _run_validate_as_guest(self, *, authorization=None, x_api_key=None):
		frappe.set_user("Guest")

		def _header(name, default=None):
			key = (name or "").lower()
			if key == "authorization":
				return authorization
			if key == "x-api-key":
				return x_api_key
			return default

		with patch("frappe.get_request_header", side_effect=_header):
			validate()

	def test_bearer_header_authenticates_as_key_user(self):
		created = self._create_key()
		raw = created["api_key"]
		self.assertTrue(raw.startswith("crm_"))
		self.assertEqual(
			frappe.db.get_value("CRM API Key", created["name"], "key_hash"),
			hash_api_key(raw),
		)

		self._run_validate_as_guest(authorization=f"Bearer {raw}")
		self.assertEqual(frappe.session.user, SALES_USER)

	def test_token_header_authenticates(self):
		created = self._create_key()
		self._run_validate_as_guest(authorization=f"token {created['api_key']}")
		self.assertEqual(frappe.session.user, SALES_USER)

	def test_token_key_secret_style_is_not_handled_here(self):
		"""Colon form is owned by Frappe User API keys (before auth_hooks).

		Our hook must not claim it — leave Guest so Frappe's validator is the
		source of truth (401 for CRM keys at the HTTP layer).
		"""
		created = self._create_key()
		self._run_validate_as_guest(authorization=f"token api:{created['api_key']}")
		self.assertEqual(frappe.session.user, "Guest")

	def test_x_api_key_header_authenticates(self):
		created = self._create_key()
		self._run_validate_as_guest(x_api_key=created["api_key"])
		self.assertEqual(frappe.session.user, SALES_USER)

	def test_invalid_key_raises_authentication_error(self):
		self._create_key()
		with self.assertRaises(frappe.AuthenticationError):
			self._run_validate_as_guest(authorization="Bearer crm_not_a_real_key_value_xxxxxx")

	def test_disabled_key_is_rejected(self):
		created = self._create_key()
		frappe.db.set_value("CRM API Key", created["name"], "disabled", 1)
		with self.assertRaises(frappe.AuthenticationError):
			self._run_validate_as_guest(authorization=f"Bearer {created['api_key']}")

	def test_set_user_preserves_form_dict_args(self):
		"""frappe.set_user clears form_dict — auth must restore method arguments."""
		created = self._create_key()
		frappe.set_user("Guest")
		frappe.local.form_dict = frappe._dict({"label": "from-request", "user": SALES_USER})

		def _header(name, default=None):
			if (name or "").lower() == "authorization":
				return f"Bearer {created['api_key']}"
			return default

		with patch("frappe.get_request_header", side_effect=_header):
			validate()

		self.assertEqual(frappe.session.user, SALES_USER)
		self.assertEqual(frappe.local.form_dict.get("label"), "from-request")
		self.assertEqual(frappe.local.form_dict.get("user"), SALES_USER)

	def test_method_call_with_args_via_key(self):
		"""Simulate /api/method with params after key auth (no missing-arg 500)."""
		created = self._create_key(user="Administrator")
		frappe.set_user("Guest")
		frappe.local.form_dict = frappe._dict({"label": "param-key-test"})

		def _header(name, default=None):
			if (name or "").lower() == "authorization":
				return f"Bearer {created['api_key']}"
			return default

		with patch("frappe.get_request_header", side_effect=_header):
			validate()

		self.assertEqual(frappe.session.user, "Administrator")
		# Call a whitelist that requires an argument sourced from form_dict.
		from crm.fcrm.doctype.crm_api_key.crm_api_key import create_api_key as create_key_fn

		label = frappe.local.form_dict.get("label")
		self.assertEqual(label, "param-key-test")
		res = create_key_fn(label=label)
		self.assertTrue(res["api_key"].startswith("crm_"))
		self.assertEqual(
			frappe.db.get_value("CRM API Key", res["name"], "label"),
			"param-key-test",
		)

	def test_whitelisted_method_via_key_session(self):
		"""After auth_hook, session user is the key owner for subsequent work."""
		created = self._create_key()
		self._run_validate_as_guest(authorization=f"Bearer {created['api_key']}")
		self.assertEqual(frappe.session.user, SALES_USER)
		self.assertNotEqual(frappe.session.user, "Guest")
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "ApiKeyAuth", "status": "New"}
		).insert(ignore_permissions=True)
		self.assertEqual(lead.owner, SALES_USER)
