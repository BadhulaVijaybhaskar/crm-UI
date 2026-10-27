# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.twilio.api import validate_twilio_request


class TestTwilioRequestValidation(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _twilio_stub(self):
		twilio = MagicMock()
		twilio.account_sid = "ACxxxxxxxx"
		twilio.application_sid = "APxxxxxxxx"
		return twilio

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
		frappe.local.request.headers = {"X-Twilio-Signature": "good-sig"}
		frappe.local.request.url = "https://example.com/api/method/crm.integrations.twilio.api.voice"

		result = validate_twilio_request({"AccountSid": "ACxxxxxxxx", "CallSid": "CAxxx"})
		self.assertIs(result, connect.return_value)
