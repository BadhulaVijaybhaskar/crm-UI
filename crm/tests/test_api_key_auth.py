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

	def test_token_key_secret_style_accepts_crm_key(self):
		created = self._create_key()
		# Frappe-style "token key:secret" — our opaque key on either side.
		self._run_validate_as_guest(authorization=f"token api:{created['api_key']}")
		self.assertEqual(frappe.session.user, SALES_USER)

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

	def test_whitelisted_method_via_key_session(self):
		"""After auth_hook, session user is the key owner for subsequent work."""
		created = self._create_key()
		self._run_validate_as_guest(authorization=f"Bearer {created['api_key']}")
		self.assertEqual(frappe.session.user, SALES_USER)
		self.assertNotEqual(frappe.session.user, "Guest")
		# Creating a lead as the authenticated key user must stamp the owner.
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "ApiKeyAuth", "status": "New"}
		).insert(ignore_permissions=True)
		self.assertEqual(lead.owner, SALES_USER)
