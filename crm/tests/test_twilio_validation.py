# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.twilio.api import validate_twilio_request
from crm.integrations.twilio.utils import get_twilio_webhook_url


class TestTwilioRequestValidation(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _twilio_stub(self):
		twilio = MagicMock()
		twilio.account_sid = "ACxxxxxxxx"
		twilio.application_sid = "APxxxxxxxx"
		return twilio

	def test_webhook_url_uses_forwarded_https(self):
		"""Behind nginx, request.url is http://host; Twilio signed the public https URL."""
		frappe.local.request = MagicMock()
		frappe.local.request.url = "http://crm.internal/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.path = "/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.full_path = "/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.headers = {
			"X-Forwarded-Proto": "https",
			"X-Forwarded-Host": "crm.example.com",
			"Host": "crm.internal",
		}
		self.assertEqual(
			get_twilio_webhook_url(),
			"https://crm.example.com/api/method/crm.integrations.twilio.api.voice",
		)

	@patch("crm.integrations.twilio.api.get_decrypted_password", return_value="auth_token_secret")
	@patch("crm.integrations.twilio.api.RequestValidator")
	@patch("crm.integrations.twilio.api.Twilio.connect")
	def test_missing_signature_is_rejected(self, connect, validator_cls, _password):
		connect.return_value = self._twilio_stub()
		frappe.local.request = MagicMock()
		frappe.local.request.headers = {}
		frappe.local.request.url = "https://example.com/api/method/crm.integrations.twilio.api.voice"

		with self.assertRaises(frappe.PermissionError):
			validate_twilio_request({"AccountSid": "ACxxxxxxxx"})
		validator_cls.assert_not_called()

	@patch("crm.integrations.twilio.api.get_decrypted_password", return_value="auth_token_secret")
	@patch("crm.integrations.twilio.api.RequestValidator")
	@patch("crm.integrations.twilio.api.Twilio.connect")
	def test_invalid_signature_is_rejected(self, connect, validator_cls, _password):
		connect.return_value = self._twilio_stub()
		validator_cls.return_value.validate.return_value = False
		frappe.local.request = MagicMock()
		frappe.local.request.headers = {"X-Twilio-Signature": "bad-sig"}
		frappe.local.request.url = "https://example.com/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.path = "/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.full_path = "/api/method/crm.integrations.twilio.api.voice"

		with self.assertRaises(frappe.PermissionError):
			validate_twilio_request({"AccountSid": "ACxxxxxxxx", "CallSid": "CAxxx"})

		validator_cls.assert_called_once_with("auth_token_secret")
		validator_cls.return_value.validate.assert_called_once()

	@patch("crm.integrations.twilio.api.get_decrypted_password", return_value="auth_token_secret")
	@patch("crm.integrations.twilio.api.RequestValidator")
	@patch("crm.integrations.twilio.api.Twilio.connect")
	def test_valid_signature_passes(self, connect, validator_cls, _password):
		connect.return_value = self._twilio_stub()
		validator_cls.return_value.validate.return_value = True
		frappe.local.request = MagicMock()
		frappe.local.request.headers = {
			"X-Twilio-Signature": "good-sig",
			"X-Forwarded-Proto": "https",
			"X-Forwarded-Host": "crm.example.com",
		}
		frappe.local.request.url = "http://crm.internal/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.path = "/api/method/crm.integrations.twilio.api.voice"
		frappe.local.request.full_path = "/api/method/crm.integrations.twilio.api.voice"

		result = validate_twilio_request({"AccountSid": "ACxxxxxxxx", "CallSid": "CAxxx"})
		self.assertIs(result, connect.return_value)
		# validate(url, params, signature) — url must be the public https URL
		url_arg = validator_cls.return_value.validate.call_args[0][0]
		self.assertEqual(url_arg, "https://crm.example.com/api/method/crm.integrations.twilio.api.voice")
