# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Frappe test cases for Astra Connect webhooks aligned with Connect-today payloads."""

from __future__ import annotations

import json
import time

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.integrations.astra_connect.auth import sign_payload
from crm.integrations.astra_connect.mapping import DEFAULT_DISPOSITION, map_disposition
from crm.integrations.astra_connect.processing import (
	ProcessingError,
	process_lead_created,
	resolve_party_by_phone,
)


TEST_SECRET = "astra-connect-test-secret-site-a"
OTHER_SITE_SECRET = "astra-connect-test-secret-site-b"


class _Headers(dict):
	def get(self, key, default=None):
		for k, v in self.items():
			if k.lower() == key.lower():
				return v
		return default


class TestAstraConnectWebhooks(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("DocType", "Astra Connect Event"):
			frappe.throw("Astra Connect Event DocType missing — run migrate first")

	def setUp(self):
		frappe.set_user("Administrator")
		# @rate_limit(ip_based=True) requires a request IP; tests have no WSGI environ.
		frappe.local.request_ip = "127.0.0.1"
		settings = frappe.get_single("Astra Connect Settings")
		settings.enabled = 1
		settings.connect_base_url = "https://connect.example.test"
		settings.default_lead_owner = "Administrator"
		settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def _post(
		self,
		payload: dict,
		*,
		secret: str = TEST_SECRET,
		timestamp: int | None = None,
		delivery_id: str | None = None,
		sig_style: str = "sha256",
		bad_sig: bool = False,
		omit_delivery: bool = False,
		use_event_id_fallback: bool = False,
	):
		body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
		ts = int(timestamp if timestamp is not None else time.time())
		eid = delivery_id or frappe.generate_hash(length=12)
		hex_sig = sign_payload(secret, ts, body)
		if bad_sig:
			hex_sig = "0" * 64

		headers = _Headers()
		if not omit_delivery:
			if use_event_id_fallback:
				headers["X-Astra-Event-Id"] = eid
			else:
				headers["X-Astra-Delivery"] = eid

		if sig_style == "tv1":
			headers["X-Astra-Signature"] = f"t={ts},v1={hex_sig}"
		else:
			headers["X-Astra-Timestamp"] = str(ts)
			headers["X-Astra-Signature"] = f"sha256={hex_sig}"

		class _Request:
			def get_data(self):
				return body.encode("utf-8")

			@property
			def headers(self):
				return headers

		frappe.local.request = _Request()
		frappe.local.response = frappe._dict()
		prev = getattr(frappe.conf, "astra_connect_webhook_secret", None)
		frappe.conf.astra_connect_webhook_secret = secret
		try:
			from crm.integrations.astra_connect.api import receive

			result = receive()
			return result, frappe.local.response.get("http_status_code", 200), eid
		finally:
			if prev is None:
				frappe.conf.pop("astra_connect_webhook_secret", None)
			else:
				frappe.conf.astra_connect_webhook_secret = prev

	# --- signature formats ---

	def test_signature_sha256_style(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-sig-a",
			"name": "Sig A",
			"phone": "+919876543201",
			"status": "new",
			"source": "test",
			"employeeId": "emp-1",
		}
		result, status, eid = self._post(payload, sig_style="sha256")
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		self.assertTrue(frappe.db.exists("Astra Connect Event", {"event_id": eid}))

	def test_signature_tv1_style(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-sig-b",
			"name": "Sig B",
			"phone": "+919876543202",
			"status": "assigned",
			"source": "test",
			"employeeId": "emp-1",
		}
		result, status, eid = self._post(payload, sig_style="tv1")
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		lead = frappe.get_doc("CRM Lead", {"astra_external_id": "lead-sig-b"})
		self.assertEqual(lead.status, "Nurture")

	def test_bad_signature_401(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-bad",
			"name": "Bad",
			"phone": "+919876543203",
		}
		result, status, _ = self._post(payload, bad_sig=True)
		self.assertEqual(status, 401)
		self.assertEqual(result["status"], "rejected")

	def test_stale_timestamp_401(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-stale",
			"name": "Stale",
			"phone": "+919876543204",
		}
		result, status, _ = self._post(payload, timestamp=int(time.time()) - 301)
		self.assertEqual(status, 401)
		self.assertEqual(result["status"], "rejected")

	def test_secret_from_another_site_refused(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-other",
			"name": "Other",
			"phone": "+919876543205",
		}
		# Sign with site B while this site expects site A
		body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
		ts = int(time.time())
		eid = "dlv-other-site"
		hex_sig = sign_payload(OTHER_SITE_SECRET, ts, body)
		headers = _Headers(
			{
				"X-Astra-Delivery": eid,
				"X-Astra-Timestamp": str(ts),
				"X-Astra-Signature": f"sha256={hex_sig}",
			}
		)

		class _Request:
			def get_data(self):
				return body.encode("utf-8")

			@property
			def headers(self):
				return headers

		frappe.local.request = _Request()
		frappe.local.response = frappe._dict()
		frappe.conf.astra_connect_webhook_secret = TEST_SECRET
		from crm.integrations.astra_connect.api import receive

		result = receive()
		status = frappe.local.response.get("http_status_code", 200)
		self.assertEqual(status, 401)
		self.assertEqual(result["status"], "rejected")

	def test_malformed_json_400(self):
		ts = int(time.time())
		body = "{not-json"
		hex_sig = sign_payload(TEST_SECRET, ts, body)
		headers = _Headers(
			{
				"X-Astra-Delivery": "dlv-bad-json",
				"X-Astra-Timestamp": str(ts),
				"X-Astra-Signature": f"sha256={hex_sig}",
			}
		)

		class _Request:
			def get_data(self):
				return body.encode("utf-8")

			@property
			def headers(self):
				return headers

		frappe.local.request = _Request()
		frappe.local.response = frappe._dict()
		frappe.conf.astra_connect_webhook_secret = TEST_SECRET
		from crm.integrations.astra_connect.api import receive

		result = receive()
		status = frappe.local.response.get("http_status_code", 200)
		self.assertEqual(status, 400)
		self.assertEqual(result["status"], "rejected")

	# --- dedupe ---

	def test_dedupe_on_delivery_id(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-dup",
			"name": "Dup",
			"phone": "+919876543206",
			"status": "new",
		}
		r1, s1, eid = self._post(payload, delivery_id="dlv-dup-1")
		self.assertEqual(s1, 200)
		self.assertEqual(r1["status"], "processed")
		count = frappe.db.count("CRM Lead", {"astra_external_id": "lead-dup"})
		r2, s2, _ = self._post(payload, delivery_id="dlv-dup-1")
		self.assertEqual(s2, 200)
		self.assertEqual(r2["status"], "duplicate")
		self.assertEqual(frappe.db.count("CRM Lead", {"astra_external_id": "lead-dup"}), count)

	def test_event_id_fallback_header(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-fallback",
			"name": "Fallback",
			"phone": "+919876543207",
		}
		result, status, eid = self._post(payload, use_event_id_fallback=True)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		self.assertTrue(frappe.db.exists("Astra Connect Event", {"event_id": eid}))

	# --- lead.created ---

	def test_lead_created_and_update(self):
		payload = {
			"type": "lead.created",
			"leadId": "lead-up-1",
			"name": "Grace Hopper",
			"phone": "+919876543208",
			"email": "grace@example.com",
			"status": "calling",
			"source": "connect",
			"employeeId": "emp-2",
		}
		r1, s1, _ = self._post(payload)
		self.assertEqual(s1, 200)
		self.assertEqual(r1["result"]["action"], "created")
		lead = frappe.get_doc("CRM Lead", {"astra_external_id": "lead-up-1"})
		self.assertEqual(lead.status, "Contacted")
		self.assertEqual(lead.ai_employee_id, "emp-2")

		payload["email"] = "grace.updated@example.com"
		payload["status"] = "qualified"
		r2, s2, _ = self._post(payload, delivery_id="dlv-up-2")
		self.assertEqual(s2, 200)
		self.assertEqual(r2["result"]["action"], "updated")
		lead.reload()
		self.assertEqual(lead.email, "grace.updated@example.com")
		self.assertEqual(lead.status, "Qualified")

	def test_lead_upsert_alias(self):
		payload = {
			"type": "lead.upsert",
			"leadId": "lead-alias",
			"name": "Alias Lead",
			"phone": "+919876543209",
			"status": "new",
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		self.assertTrue(frappe.db.exists("CRM Lead", {"astra_external_id": "lead-alias"}))

	# --- call.completed ---

	def test_call_completed_matched_and_unknown_outcome(self):
		process_lead_created(
			{
				"leadId": "lead-call-1",
				"name": "Call Lead",
				"phone": "+919876543210",
				"status": "new",
			}
		)
		# Real Connect payload shape (flat camelCase + ISO Z timestamp).
		payload = {
			"type": "call.completed",
			"callId": "call-100",
			"contactId": "ctc-55",
			"employeeId": "emp-9",
			"direction": "outbound",
			"phone": "+919876543210",
			"outcome": "weird_custom_label_from_ops",
			"qualified": True,
			"summary": "Booked interest",
			"fields": {"note": "x"},
			"endedAt": "2026-10-27T10:05:00Z",
			"channel": "voice",
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		call_log = frappe.get_doc("CRM Call Log", "call-100")
		self.assertEqual(call_log.outcome, "weird_custom_label_from_ops")
		self.assertEqual(call_log.disposition, DEFAULT_DISPOSITION)
		self.assertEqual(call_log.channel, "voice")
		self.assertEqual(call_log.astra_contact_id, "ctc-55")
		self.assertEqual(call_log.qualified, 1)
		# Phone fields must stay E.164 — never "astra-connect" / "unknown".
		self.assertTrue(str(call_log.get("from") or "").startswith("+"))
		self.assertTrue(str(call_log.to or "").startswith("+"))
		self.assertNotIn("astra-connect", str(call_log.get("from") or "").lower())
		self.assertNotIn("unknown", str(call_log.to or "").lower())
		# Zulu endedAt must land as a naive datetime MariaDB accepts.
		self.assertIsNotNone(call_log.end_time or call_log.start_time)
		self.assertIsNone(getattr(call_log.end_time or call_log.start_time, "tzinfo", None))
		self.assertEqual(call_log.owner, "Administrator")
		self.assertEqual(map_disposition("appointment_booked"), "Appointment Booked")

	def test_failed_delivery_is_retryable(self):
		"""A 5xx / Failed event with the same X-Astra-Delivery must reprocess."""
		payload = {
			"type": "call.completed",
			"callId": "call-retry-1",
			"contactId": "ctc-retry",
			"employeeId": "emp-1",
			"direction": "outbound",
			"phone": "+919999998888",
			"outcome": "no_answer",
			"qualified": False,
			"summary": "No match yet",
			"endedAt": "2026-10-27T11:00:00Z",
		}
		r1, s1, eid = self._post(payload, delivery_id="dlv-retry-1")
		self.assertEqual(s1, 200)
		self.assertEqual(r1["status"], "failed")
		# Seed the party, then replay the same delivery id.
		process_lead_created(
			{
				"leadId": "lead-retry-1",
				"name": "Retry Lead",
				"phone": "+919999998888",
			}
		)
		r2, s2, _ = self._post(payload, delivery_id="dlv-retry-1")
		self.assertEqual(s2, 200)
		self.assertEqual(r2["status"], "processed")
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-retry-1"))

	def test_employee_call_completed_extras(self):
		process_lead_created(
			{
				"leadId": "lead-emp-call",
				"name": "Emp Call",
				"phone": "+919876543211",
			}
		)
		payload = {
			"type": "employee.call.completed",
			"callId": "call-emp-1",
			"contactId": "ctc-1",
			"employeeId": "emp-3",
			"direction": "inbound",
			"phone": "9876543211",
			"outcome": "appointment_booked",
			"qualified": False,
			"summary": "Done",
			"endedAt": "2026-10-27T10:05:00Z",
			"startedAt": "2026-10-27T10:03:00Z",
			"durationSec": 120,
			"endReason": "cancelled",
			"recordingUrl": "https://connect.example/r/1",
			"transcript": [{"role": "agent", "text": "Hi"}],
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		call_log = frappe.get_doc("CRM Call Log", "call-emp-1")
		self.assertEqual(call_log.status, "Canceled")
		self.assertEqual(call_log.duration, 120)
		self.assertTrue(call_log.recording_url)
		self.assertIn("agent", call_log.transcript or "")
		self.assertEqual(call_log.disposition, "Appointment Booked")

	def test_call_unmatched_returns_200_failed(self):
		payload = {
			"type": "call.completed",
			"callId": "call-orphan",
			"contactId": "ctc-x",
			"employeeId": "emp-1",
			"direction": "outbound",
			"phone": "+919999999999",
			"outcome": "no_answer",
			"qualified": False,
			"summary": "No match",
			"endedAt": "2026-10-27T11:00:00Z",
		}
		result, status, eid = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "failed")
		event = frappe.get_doc("Astra Connect Event", {"event_id": eid})
		self.assertEqual(event.status, "Failed")
		self.assertIn("No matching", event.error)

	def test_phone_last10_fallback(self):
		# Store lead with local formatting; event sends E.164
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Local",
				"mobile_no": "9876543212",
				"astra_external_id": "lead-local-10",
			}
		).insert(ignore_permissions=True)
		match = resolve_party_by_phone("+919876543212")
		self.assertIsNotNone(match)
		self.assertEqual(match["name"], lead.name)

	def test_ambiguous_phone_match_fails(self):
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "A",
				"mobile_no": "+919876543213",
				"astra_external_id": "lead-amb-a",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "B",
				"mobile_no": "+919876543213",
				"astra_external_id": "lead-amb-b",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(ProcessingError) as ctx:
			resolve_party_by_phone("+919876543213")
		self.assertIn("Ambiguous", str(ctx.exception))

		payload = {
			"type": "call.completed",
			"callId": "call-amb",
			"contactId": "ctc-amb",
			"employeeId": "emp-1",
			"direction": "outbound",
			"phone": "+919876543213",
			"outcome": "interested",
			"qualified": False,
			"summary": "Ambiguous",
			"endedAt": "2026-10-27T11:00:00Z",
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "failed")
		self.assertIn("Ambiguous", result["error"])
