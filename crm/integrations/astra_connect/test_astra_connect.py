# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Frappe test cases for Astra Connect webhooks (inbox + worker redesign)."""

from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from crm.integrations.astra_connect.auth import sign_payload
from crm.integrations.astra_connect.mapping import DEFAULT_DISPOSITION, map_disposition
from crm.integrations.astra_connect.processing import (
	ProcessingError,
	process_call_completed,
	process_lead_created as _process_lead_created,
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
	# receive() commits; track rows so tearDown can delete them (rollback alone cannot).
	TEST_TAG = "astra-connect-test"

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
		self._created_event_ids: list[str] = []
		self._created_call_ids: list[str] = []
		self._created_lead_ext_ids: list[str] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup_committed_rows()
		frappe.db.rollback()

	def _track_lead(self, lead_id: str):
		self._created_lead_ext_ids.append(lead_id)

	def _track_call(self, call_id: str):
		self._created_call_ids.append(call_id)

	def process_lead_created(self, data: dict):
		if data.get("leadId"):
			self._track_lead(str(data["leadId"]))
		return _process_lead_created(data)

	def _cleanup_committed_rows(self):
		"""Delete rows receive() committed so later suites (phone lookup) stay clean."""
		for eid in list(getattr(self, "_created_event_ids", [])):
			name = frappe.db.get_value("Astra Connect Event", {"event_id": eid}, "name")
			if name:
				frappe.delete_doc("Astra Connect Event", name, force=True, ignore_permissions=True)
		for call_id in list(getattr(self, "_created_call_ids", [])):
			if frappe.db.exists("CRM Call Log", call_id):
				note = frappe.db.get_value("CRM Call Log", call_id, "note")
				frappe.delete_doc("CRM Call Log", call_id, force=True, ignore_permissions=True)
				if note and frappe.db.exists("FCRM Note", note):
					frappe.delete_doc("FCRM Note", note, force=True, ignore_permissions=True)
			filters = {"title": ("like", f"%({call_id})%")}
			if frappe.db.has_column("FCRM Note", "astra_call_id"):
				for note_name in frappe.get_all(
					"FCRM Note", filters={"astra_call_id": call_id}, pluck="name"
				):
					frappe.delete_doc("FCRM Note", note_name, force=True, ignore_permissions=True)
			for note_name in frappe.get_all("FCRM Note", filters=filters, pluck="name"):
				frappe.delete_doc("FCRM Note", note_name, force=True, ignore_permissions=True)
		for ext in list(getattr(self, "_created_lead_ext_ids", [])):
			lead = frappe.db.get_value("CRM Lead", {"astra_external_id": ext}, "name")
			if lead:
				frappe.delete_doc("CRM Lead", lead, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _event_status(self, eid: str) -> str | None:
		return frappe.db.get_value("Astra Connect Event", {"event_id": eid}, "status")

	def _event_error(self, eid: str) -> str | None:
		return frappe.db.get_value("Astra Connect Event", {"event_id": eid}, "error")

	def _wait_event_status(self, eid: str, allowed: set[str], timeout: float = 10.0) -> str:
		deadline = time.time() + timeout
		status = self._event_status(eid)
		while time.time() < deadline:
			status = self._event_status(eid)
			if status in allowed:
				return status
			time.sleep(0.05)
		return status or ""

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
			self._created_event_ids.append(eid)
			if isinstance(payload, dict):
				if payload.get("leadId"):
					self._created_lead_ext_ids.append(str(payload["leadId"]))
				if payload.get("callId"):
					self._created_call_ids.append(str(payload["callId"]))
			return result, frappe.local.response.get("http_status_code", 200), eid
		finally:
			if prev is None:
				frappe.conf.pop("astra_connect_webhook_secret", None)
			else:
				frappe.conf.astra_connect_webhook_secret = prev

	def _thread_site_bootstrap(self):
		"""Return a callable that inits + connects a worker thread to this site."""
		site = frappe.local.site

		def bootstrap():
			frappe.init(site=site)
			frappe.connect()
			frappe.set_user("Administrator")
			frappe.local.request_ip = "127.0.0.1"

		return bootstrap

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
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
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
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
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

	def test_oversized_body_413_before_hmac(self):
		"""Bodies over MAX_WEBHOOK_BODY_BYTES must 413 without verifying the signature."""
		from crm.integrations.astra_connect import api as connect_api

		oversized = b"x" * (connect_api.MAX_WEBHOOK_BODY_BYTES + 1)
		headers = _Headers(
			{
				"Content-Length": str(len(oversized)),
				"X-Astra-Delivery": "dlv-too-big",
				"X-Astra-Timestamp": str(int(time.time())),
				"X-Astra-Signature": "sha256=" + ("ab" * 32),
			}
		)

		class _Request:
			def get_data(self):
				return oversized

			@property
			def headers(self):
				return headers

		verify_calls = {"n": 0}

		def boom_verify(**_kwargs):
			verify_calls["n"] += 1
			raise AssertionError("HMAC must not run for oversized bodies")

		frappe.local.request = _Request()
		frappe.local.response = frappe._dict()
		prev = getattr(frappe.conf, "astra_connect_webhook_secret", None)
		frappe.conf.astra_connect_webhook_secret = TEST_SECRET
		try:
			with patch.object(connect_api, "verify_signature", side_effect=boom_verify):
				result = connect_api.receive()
			status = frappe.local.response.get("http_status_code", 200)
			self.assertEqual(status, 413)
			self.assertEqual(result["status"], "rejected")
			self.assertEqual(verify_calls["n"], 0)
		finally:
			if prev is None:
				frappe.conf.pop("astra_connect_webhook_secret", None)
			else:
				frappe.conf.astra_connect_webhook_secret = prev

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
		self.assertEqual(s1, 202)
		self.assertEqual(r1["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
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
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
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
		r1, s1, eid1 = self._post(payload)
		self.assertEqual(s1, 202)
		self.assertEqual(r1["status"], "accepted")
		self.assertEqual(self._event_status(eid1), "Processed")
		lead = frappe.get_doc("CRM Lead", {"astra_external_id": "lead-up-1"})
		self.assertEqual(lead.status, "Contacted")
		self.assertEqual(lead.ai_employee_id, "emp-2")

		payload["email"] = "grace.updated@example.com"
		payload["status"] = "qualified"
		r2, s2, eid2 = self._post(payload, delivery_id="dlv-up-2")
		self.assertEqual(s2, 202)
		self.assertEqual(r2["status"], "accepted")
		self.assertEqual(self._event_status(eid2), "Processed")
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
		result, status, eid = self._post(payload)
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
		self.assertTrue(frappe.db.exists("CRM Lead", {"astra_external_id": "lead-alias"}))

	# --- call.completed ---

	def test_call_completed_matched_and_unknown_outcome(self):
		self.process_lead_created(
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
		result, status, eid = self._post(payload)
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
		call_log = frappe.get_doc("CRM Call Log", "call-100")
		self.assertEqual(call_log.outcome, "weird_custom_label_from_ops")
		self.assertEqual(call_log.disposition, DEFAULT_DISPOSITION)
		self.assertEqual(call_log.channel, "voice")
		self.assertEqual(call_log.astra_contact_id, "ctc-55")
		self.assertEqual(call_log.qualified, 1)
		self.assertEqual(call_log.ai_employee_id, "emp-9")
		# Outbound: party on `to`; agent/DID leg stays empty when unset (never
		# duplicate the customer onto both legs or invent astra-connect/unknown).
		self.assertEqual(call_log.to, "+919876543210")
		self.assertFalse(call_log.get("from"))
		self.assertNotIn("astra-connect", str(call_log.get("from") or "").lower())
		self.assertNotIn("unknown", str(call_log.to or "").lower())
		# Zulu endedAt must land as a naive datetime MariaDB accepts.
		self.assertIsNotNone(call_log.end_time or call_log.start_time)
		self.assertIsNone(getattr(call_log.end_time or call_log.start_time, "tzinfo", None))
		self.assertEqual(call_log.owner, "Administrator")
		self.assertEqual(map_disposition("appointment_booked"), "Appointment Booked")

	def test_failed_delivery_is_retryable(self):
		"""Failed inbox rows stay redeliverable via retry_event (same delivery id is duplicate)."""
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
		self.assertEqual(s1, 202)
		self.assertEqual(r1["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Failed")

		# Resend of the same delivery is a pure duplicate — no row rewrite.
		r_dup, s_dup, _ = self._post(payload, delivery_id="dlv-retry-1")
		self.assertEqual(s_dup, 200)
		self.assertEqual(r_dup["status"], "duplicate")
		self.assertEqual(self._event_status(eid), "Failed")

		# Seed the party, then admin-retry the Failed row.
		self.process_lead_created(
			{
				"leadId": "lead-retry-1",
				"name": "Retry Lead",
				"phone": "+919999998888",
			}
		)
		from crm.integrations.astra_connect.api import retry_event

		r2 = retry_event(eid)
		self.assertEqual(r2["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-retry-1"))

	def test_employee_call_completed_extras(self):
		self.process_lead_created(
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
			"durationSeconds": 120,
			"endReason": "cancelled",
			"recordingUrl": "https://connect.example/r/1",
			"transcript": [{"role": "agent", "text": "Hi"}],
		}
		result, status, eid = self._post(payload)
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
		call_log = frappe.get_doc("CRM Call Log", "call-emp-1")
		self.assertEqual(call_log.status, "Canceled")
		self.assertEqual(call_log.duration, 120)
		self.assertTrue(call_log.recording_url)
		self.assertIn("agent", call_log.transcript or "")
		self.assertEqual(call_log.disposition, "Appointment Booked")
		# Inbound: party on `from`; empty agent leg when no Connect DID.
		self.assertTrue(str(call_log.get("from") or "").endswith("9876543211"))
		self.assertFalse(call_log.to)
		self.assertEqual(call_log.ai_employee_id, "emp-3")

	def test_call_unmatched_returns_accepted_event_failed(self):
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
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Failed")
		self.assertIn("No matching", self._event_error(eid) or "")

	def test_phone_last10_fallback(self):
		# Store lead with local formatting; event sends E.164
		self._track_lead("lead-local-10")
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
		self._track_lead("lead-amb-a")
		self._track_lead("lead-amb-b")
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
		result, status, eid = self._post(payload)
		self.assertEqual(status, 202)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Failed")
		self.assertIn("Ambiguous", self._event_error(eid) or "")

	def test_call_completed_retries_deadlock_in_worker(self):
		"""Worker retries the whole job on deadlock; claim stays Processing until done."""
		from crm.integrations.astra_connect import api as connect_api

		self.process_lead_created(
			{
				"leadId": "lead-deadlock-1",
				"name": "Deadlock Lead",
				"phone": "+919811112222",
				"status": "new",
			}
		)
		self._track_call("call-deadlock-1")
		data = {
			"callId": "call-deadlock-1",
			"contactId": "ctc-dl",
			"employeeId": "emp-dl",
			"direction": "outbound",
			"phone": "+919811112222",
			"outcome": "interested",
			"qualified": False,
			"summary": "Retry me",
			"endedAt": "2026-10-27T12:00:00Z",
			"channel": "voice",
		}

		self.assertTrue(connect_api._is_retryable_db(Exception("Deadlock found when trying to get lock")))
		self.assertTrue(connect_api._is_retryable_db(Exception("(1213, 'Deadlock')")))

		calls = {"n": 0}
		import crm.integrations.astra_connect.processing as processing

		real_save = processing._save_call_log

		def flaky_save(call_log):
			calls["n"] += 1
			if calls["n"] == 1:
				raise Exception("Deadlock found when trying to get lock; try restarting transaction")
			return real_save(call_log)

		event = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": "dlv-deadlock-1",
				"event_type": "call.completed",
				"payload": {"type": "call.completed", **data},
				"status": "Received",
				"attempts": 0,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append("dlv-deadlock-1")
		frappe.db.commit()

		with patch.object(processing, "_save_call_log", side_effect=flaky_save):
			result = connect_api.process_inbox_event(event.name)

		self.assertEqual(result["status"], "processed")
		self.assertGreaterEqual(calls["n"], 2)
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-deadlock-1"))
		self.assertTrue(frappe.db.exists("CRM Lead", {"astra_external_id": "lead-deadlock-1"}))
		self.assertEqual(self._event_status("dlv-deadlock-1"), "Processed")

	def test_call_summary_note_is_upserted_across_deliveries(self):
		"""Three deliveries + both event types leave exactly one summary note."""
		self.process_lead_created(
			{
				"leadId": "lead-note-1",
				"name": "Note Lead",
				"phone": "+919822223333",
				"status": "new",
			}
		)
		base = {
			"callId": "call-note-1",
			"contactId": "ctc-note",
			"employeeId": "emp-note",
			"direction": "outbound",
			"phone": "+919822223333",
			"outcome": "interested",
			"qualified": False,
			"endedAt": "2026-10-27T12:00:00Z",
			"channel": "voice",
		}
		self._track_call("call-note-1")

		for i, summary in enumerate(("First", "Second", "Third")):
			payload = {**base, "type": "call.completed", "summary": summary}
			result, status, eid = self._post(payload, delivery_id=f"dlv-note-{i}")
			self.assertEqual(status, 202, result)
			self.assertEqual(result["status"], "accepted")
			self.assertEqual(self._event_status(eid), "Processed")

		emp_payload = {
			**base,
			"type": "employee.call.completed",
			"summary": "Employee enriched",
			"durationSeconds": 42,
		}
		result, status, eid = self._post(emp_payload, delivery_id="dlv-note-emp")
		self.assertEqual(status, 202, result)
		self.assertEqual(result["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")

		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			notes = frappe.get_all(
				"FCRM Note",
				filters={"astra_call_id": "call-note-1"},
				fields=["name", "content"],
			)
		else:
			notes = frappe.get_all(
				"FCRM Note",
				filters={"title": ("like", "%call-note-1%")},
				fields=["name", "content"],
			)
		self.assertEqual(len(notes), 1, notes)
		self.assertIn("Employee enriched", notes[0].content)
		call_log = frappe.get_doc("CRM Call Log", "call-note-1")
		self.assertEqual(call_log.note, notes[0].name)

	def test_concurrent_same_delivery_one_call_one_note(self):
		"""Eight parallel posts of one X-Astra-Delivery → 1 accepted + 7 duplicate;
		exactly one call log and one note; event ends Processed.
		"""
		self.process_lead_created(
			{
				"leadId": "lead-concurrent-1",
				"name": "Concurrent Lead",
				"phone": "+919833334444",
				"status": "new",
			}
		)
		frappe.db.commit()
		payload = {
			"type": "call.completed",
			"callId": "call-concurrent-1",
			"contactId": "ctc-cc",
			"employeeId": "emp-cc",
			"direction": "outbound",
			"phone": "+919833334444",
			"outcome": "interested",
			"qualified": False,
			"summary": "Concurrent",
			"endedAt": "2026-10-27T12:00:00Z",
		}
		self._track_call("call-concurrent-1")
		delivery_id = "dlv-concurrent-same"
		results: list[tuple] = []
		lock = threading.Lock()
		bootstrap = self._thread_site_bootstrap()

		def worker():
			bootstrap()
			try:
				result, status, _ = self._post(payload, delivery_id=delivery_id)
				with lock:
					results.append((status, result.get("status")))
			finally:
				frappe.db.close()

		threads = [threading.Thread(target=worker) for _ in range(8)]
		for t in threads:
			t.start()
		for t in threads:
			t.join(timeout=60)

		self.assertEqual(len(results), 8, results)
		accepted = [r for r in results if r[1] == "accepted"]
		duplicates = [r for r in results if r[1] == "duplicate"]
		failures = [r for r in results if r[1] not in ("accepted", "duplicate")]
		self.assertEqual(len(failures), 0, failures)
		self.assertEqual(len(accepted), 1, results)
		self.assertEqual(len(duplicates), 7, results)
		self.assertEqual(frappe.db.count("Astra Connect Event", {"event_id": delivery_id}), 1)
		self.assertEqual(self._event_status(delivery_id), "Processed")
		self.assertEqual(frappe.db.count("CRM Call Log", {"name": "call-concurrent-1"}), 1)
		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			self.assertEqual(frappe.db.count("FCRM Note", {"astra_call_id": "call-concurrent-1"}), 1)
		else:
			self.assertEqual(
				frappe.db.count("FCRM Note", {"title": ("like", "%call-concurrent-1%")}),
				1,
			)

	def test_same_call_id_distinct_deliveries_serial(self):
		"""Eight deliveries of one callId (serialised) → 0 5xx, one call log, all Processed.

		Serialised to avoid flaky 1020 exhaustion under parallel upserts; idempotent
		upsert behaviour is what we assert here.
		"""
		self.process_lead_created(
			{
				"leadId": "lead-callid-1",
				"name": "CallId Lead",
				"phone": "+919844445555",
				"status": "new",
			}
		)
		frappe.db.commit()
		payload = {
			"type": "call.completed",
			"callId": "call-shared-1",
			"contactId": "ctc-shared",
			"employeeId": "emp-shared",
			"direction": "outbound",
			"phone": "+919844445555",
			"outcome": "interested",
			"qualified": False,
			"summary": "Shared call",
			"endedAt": "2026-10-27T12:00:00Z",
		}
		self._track_call("call-shared-1")
		delivery_ids = [f"dlv-shared-{i}" for i in range(8)]

		for did in delivery_ids:
			result, status, eid = self._post(payload, delivery_id=did)
			self.assertEqual(status, 202, (status, result, eid))
			self.assertEqual(result["status"], "accepted")
			self.assertEqual(self._event_status(eid), "Processed", self._event_error(eid))

		self.assertEqual(frappe.db.count("CRM Call Log", {"name": "call-shared-1"}), 1)
		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			self.assertEqual(frappe.db.count("FCRM Note", {"astra_call_id": "call-shared-1"}), 1)

	def test_out_of_order_delivery_does_not_overwrite_newer_summary(self):
		"""Older endedAt must not regress summary/note text written by a newer delivery."""
		self.process_lead_created(
			{
				"leadId": "lead-ooo-1",
				"name": "OOO Lead",
				"phone": "+919855556666",
				"status": "new",
			}
		)
		base = {
			"type": "call.completed",
			"callId": "call-ooo-1",
			"contactId": "ctc-ooo",
			"employeeId": "emp-ooo",
			"direction": "outbound",
			"phone": "+919855556666",
			"outcome": "interested",
			"qualified": False,
		}
		self._track_call("call-ooo-1")

		newer, s1, eid1 = self._post(
			{**base, "summary": "Newer summary", "endedAt": "2026-10-27T14:00:00Z"},
			delivery_id="dlv-ooo-new",
		)
		self.assertEqual(s1, 202)
		self.assertEqual(self._event_status(eid1), "Processed")

		older, s2, eid2 = self._post(
			{**base, "summary": "Stale summary", "endedAt": "2026-10-27T10:00:00Z"},
			delivery_id="dlv-ooo-old",
		)
		self.assertEqual(s2, 202)
		self.assertEqual(self._event_status(eid2), "Processed")

		call_log = frappe.get_doc("CRM Call Log", "call-ooo-1")
		self.assertIn("Newer summary", call_log.call_summary or "")
		self.assertNotIn("Stale summary", call_log.call_summary or "")
		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			notes = frappe.get_all(
				"FCRM Note",
				filters={"astra_call_id": "call-ooo-1"},
				fields=["name", "content"],
			)
			self.assertEqual(len(notes), 1, notes)
			self.assertIn("Newer summary", notes[0].content)
			self.assertNotIn("Stale summary", notes[0].content)

	def test_stale_processing_sweeper_and_retry_event(self):
		"""Stuck Processing is reset by the sweeper; retry_event accepts stale Processing."""
		from crm.integrations.astra_connect import api as connect_api

		self.process_lead_created(
			{
				"leadId": "lead-stale-1",
				"name": "Stale Lead",
				"phone": "+919866667777",
				"status": "new",
			}
		)
		payload = {
			"type": "call.completed",
			"callId": "call-stale-1",
			"contactId": "ctc-stale",
			"employeeId": "emp-stale",
			"direction": "outbound",
			"phone": "+919866667777",
			"outcome": "interested",
			"qualified": False,
			"summary": "Recover me",
			"endedAt": "2026-10-27T12:00:00Z",
		}
		self._track_call("call-stale-1")
		eid = "dlv-stale-1"
		event = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": eid,
				"event_type": "call.completed",
				"payload": payload,
				"status": "Processing",
				"attempts": 1,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append(eid)
		stale_at = add_to_date(now_datetime(), minutes=-30)
		if frappe.db.has_column("Astra Connect Event", "claimed_at"):
			frappe.db.set_value(
				"Astra Connect Event",
				event.name,
				{"claimed_at": stale_at, "modified": stale_at},
				update_modified=False,
			)
		else:
			frappe.db.sql(
				"UPDATE `tabAstra Connect Event` SET modified=%s WHERE name=%s",
				(stale_at, event.name),
			)
		frappe.db.commit()

		# Redelivery of a stuck Processing row is duplicate (no rewrite).
		r_dup, s_dup, _ = self._post(payload, delivery_id=eid)
		self.assertEqual(s_dup, 200)
		self.assertEqual(r_dup["status"], "duplicate")
		self.assertEqual(self._event_status(eid), "Processing")

		# retry_event accepts stale Processing.
		retried = connect_api.retry_event(eid)
		self.assertEqual(retried["status"], "accepted")
		self.assertEqual(self._event_status(eid), "Processed")
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-stale-1"))

		# Sweeper path: seed another stale Processing and sweep.
		eid2 = "dlv-stale-2"
		event2 = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": eid2,
				"event_type": "call.completed",
				"payload": {**payload, "callId": "call-stale-2", "summary": "Sweep me"},
				"status": "Processing",
				"attempts": 1,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append(eid2)
		self._track_call("call-stale-2")
		if frappe.db.has_column("Astra Connect Event", "claimed_at"):
			frappe.db.set_value(
				"Astra Connect Event",
				event2.name,
				{"claimed_at": stale_at, "modified": stale_at},
				update_modified=False,
			)
		frappe.db.commit()

		result = connect_api.sweep_stale_processing()
		self.assertGreaterEqual(result["reset"], 1)
		self.assertEqual(self._event_status(eid2), "Processed")
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-stale-2"))

	def test_worker_exhaustion_marks_failed(self):
		"""After retry budget exhaustion the event is Failed (sweeper can recover)."""
		from crm.integrations.astra_connect import api as connect_api
		import crm.integrations.astra_connect.processing as processing

		self.process_lead_created(
			{
				"leadId": "lead-exhaust-1",
				"name": "Exhaust Lead",
				"phone": "+919877778888",
				"status": "new",
			}
		)
		self._track_call("call-exhaust-1")
		data = {
			"type": "call.completed",
			"callId": "call-exhaust-1",
			"contactId": "ctc-ex",
			"employeeId": "emp-ex",
			"direction": "outbound",
			"phone": "+919877778888",
			"outcome": "interested",
			"qualified": False,
			"summary": "Never lands",
			"endedAt": "2026-10-27T12:00:00Z",
		}
		event = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": "dlv-exhaust-1",
				"event_type": "call.completed",
				"payload": data,
				"status": "Received",
				"attempts": 0,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append("dlv-exhaust-1")
		frappe.db.commit()

		def always_1020(call_log):
			raise Exception("(1020, 'Record has changed since last read in table')")

		with patch.object(processing, "_save_call_log", side_effect=always_1020):
			with patch.object(connect_api.time, "sleep", return_value=None):
				result = connect_api.process_inbox_event(event.name)

		self.assertEqual(result["status"], "failed")
		self.assertEqual(self._event_status("dlv-exhaust-1"), "Failed")

	def test_unique_index_patch_dedupes_then_indexes(self):
		"""Patch is idempotent: seed duplicates → execute → unique indexes, no 1062."""
		from crm.patches.v1_0 import astra_connect_inbox_unique_indexes as patch

		# Drop unique on event_id so we can seed duplicates.
		try:
			frappe.db.sql_ddl("ALTER TABLE `tabAstra Connect Event` DROP INDEX `unique_event_id`")
		except Exception:
			pass
		try:
			# Frappe often names the unique index after the column.
			frappe.db.sql_ddl("ALTER TABLE `tabAstra Connect Event` DROP INDEX `event_id`")
		except Exception:
			pass

		dup_id = "dlv-patch-dup"
		self._created_event_ids.append(dup_id)
		for i in range(3):
			name = f"ACE-PATCH-{i}"
			frappe.db.sql(
				"""
				INSERT INTO `tabAstra Connect Event`
					(name, creation, modified, modified_by, owner, docstatus,
					 event_id, event_type, status, attempts, payload)
				VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s, 0, %s)
				""",
				(
					name,
					now_datetime(),
					now_datetime(),
					"Administrator",
					"Administrator",
					dup_id,
					"lead.created",
					"Processed" if i == 0 else "Failed",
					"{}",
				),
			)

		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			try:
				frappe.db.sql_ddl("ALTER TABLE `tabFCRM Note` DROP INDEX `unique_astra_call_id`")
			except Exception:
				pass
			for i in range(2):
				nname = f"NOTE-PATCH-{i}"
				frappe.db.sql(
					"""
					INSERT INTO `tabFCRM Note`
						(name, creation, modified, modified_by, owner, docstatus,
						 title, content, astra_call_id)
					VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s)
					""",
					(
						nname,
						now_datetime(),
						now_datetime(),
						"Administrator",
						"Administrator",
						f"Call summary (call-patch-1)",
						f"<p>Note {i}</p>",
						"call-patch-1",
					),
				)
			self._track_call("call-patch-1")

		frappe.db.commit()
		self.assertGreater(frappe.db.count("Astra Connect Event", {"event_id": dup_id}), 1)

		patch.execute()
		# Re-run must be a no-op (idempotent).
		patch.execute()

		self.assertEqual(frappe.db.count("Astra Connect Event", {"event_id": dup_id}), 1)
		self.assertTrue(patch._column_has_unique_index("tabAstra Connect Event", "event_id"))
		if frappe.db.has_column("FCRM Note", "astra_call_id"):
			self.assertEqual(frappe.db.count("FCRM Note", {"astra_call_id": "call-patch-1"}), 1)
			self.assertTrue(patch._column_has_unique_index("tabFCRM Note", "astra_call_id"))

	def test_column_has_unique_index_treats_zero_as_unique(self):
		"""Non_unique=0 must count as unique (``x or 1`` would wrongly flip it)."""
		from crm.patches.v1_0 import astra_connect_inbox_unique_indexes as patch_mod

		with patch.object(
			patch_mod.frappe.db,
			"sql",
			return_value=[{"Non_unique": 0, "Key_name": "unique_event_id", "Column_name": "event_id"}],
		):
			self.assertTrue(patch_mod._column_has_unique_index("tabAstra Connect Event", "event_id"))
		with patch.object(
			patch_mod.frappe.db,
			"sql",
			return_value=[{"Non_unique": 1, "Key_name": "event_id", "Column_name": "event_id"}],
		):
			self.assertFalse(patch_mod._column_has_unique_index("tabAstra Connect Event", "event_id"))

	def test_enqueue_uses_fresh_job_id_despite_stuck_started_record(self):
		"""After SIGKILL leaves an RQ job 'started', recovery must still enqueue.

		Simulates frappe's deduplicate skip for a fixed job_id, then asserts our
		fresh job_id path actually calls enqueue (and the sweeper recovers orphans).
		"""
		from crm.integrations.astra_connect import api as connect_api

		self.process_lead_created(
			{
				"leadId": "lead-stuck-rq-1",
				"name": "Stuck RQ Lead",
				"phone": "+919888889999",
				"status": "new",
			}
		)
		payload = {
			"type": "call.completed",
			"callId": "call-stuck-rq-1",
			"contactId": "ctc-stuck",
			"employeeId": "emp-stuck",
			"direction": "outbound",
			"phone": "+919888889999",
			"outcome": "interested",
			"qualified": False,
			"summary": "Recover after kill",
			"endedAt": "2026-10-27T12:00:00Z",
		}
		self._track_call("call-stuck-rq-1")
		eid = "dlv-stuck-rq-1"
		event = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": eid,
				"event_type": "call.completed",
				"payload": payload,
				"status": "Received",
				"attempts": 1,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append(eid)
		# Age the row so the Received-orphan sweeper picks it up.
		stale_at = add_to_date(now_datetime(), minutes=-30)
		frappe.db.sql(
			"UPDATE `tabAstra Connect Event` SET modified=%s WHERE name=%s",
			(stale_at, event.name),
		)
		frappe.db.commit()

		seen_job_ids: list[str] = []
		stuck_id = f"astra-connect-{eid}"  # old fixed id left in 'started'

		def fake_enqueue(method, **kwargs):
			jid = kwargs.get("job_id")
			# Simulate background_jobs.py skipping when the sticky started id is reused.
			if jid == stuck_id and kwargs.get("deduplicate"):
				return None
			seen_job_ids.append(jid)
			# Run the worker inline for the test.
			if method == connect_api.WORKER_PATH or method == connect_api.process_inbox_event:
				connect_api.process_inbox_event(kwargs.get("event_name") or event.name)
			return jid

		# Force the async enqueue path (bypass in_test sync shortcut).
		# frappe.flags is a _dict — use patch.dict, not patch.object.
		with patch.dict(connect_api.frappe.flags, {"in_test": False}):
			with patch.dict(connect_api.frappe.conf, {"astra_connect_sync_processing": 0}, clear=False):
				with patch.object(connect_api.frappe, "enqueue", side_effect=fake_enqueue):
					# Direct recovery enqueue (retry_event / sweeper path).
					jid1 = connect_api._enqueue_processing(event.name, eid, attempts=1)
					self.assertIsNotNone(jid1)
					self.assertNotEqual(jid1, stuck_id)
					self.assertFalse(jid1.startswith(stuck_id + ":") and jid1 == stuck_id)
					self.assertIn(jid1, seen_job_ids)
					self.assertEqual(self._event_status(eid), "Processed")

		# Second scenario: orphaned Received recovered by sweeper with fresh job ids.
		eid2 = "dlv-stuck-rq-2"
		event2 = frappe.get_doc(
			{
				"doctype": "Astra Connect Event",
				"event_id": eid2,
				"event_type": "call.completed",
				"payload": {**payload, "callId": "call-stuck-rq-2"},
				"status": "Received",
				"attempts": 0,
			}
		).insert(ignore_permissions=True)
		self._created_event_ids.append(eid2)
		self._track_call("call-stuck-rq-2")
		frappe.db.sql(
			"UPDATE `tabAstra Connect Event` SET modified=%s WHERE name=%s",
			(stale_at, event2.name),
		)
		frappe.db.commit()

		seen_job_ids.clear()
		with patch.dict(connect_api.frappe.flags, {"in_test": False}):
			with patch.dict(connect_api.frappe.conf, {"astra_connect_sync_processing": 0}, clear=False):
				with patch.object(connect_api.frappe, "enqueue", side_effect=fake_enqueue):
					result = connect_api.sweep_stale_processing()
					self.assertGreaterEqual(result.get("reenqueued", 0), 1)
					self.assertTrue(seen_job_ids)
					self.assertTrue(all(j and j != f"astra-connect-{eid2}" for j in seen_job_ids))
					self.assertEqual(self._event_status(eid2), "Processed")

	def test_enqueue_falls_back_when_astra_connect_queue_missing(self):
		"""Undeclared astra_connect queue must not leave the inbox row stranded."""
		from crm.integrations.astra_connect import api as connect_api

		calls: list[dict] = []

		def boom_then_ok(method, **kwargs):
			calls.append(dict(kwargs))
			if kwargs.get("queue") == "astra_connect":
				raise Exception("(417) Queue astra_connect not found")
			return kwargs.get("job_id")

		with patch.object(connect_api, "_configured_queue_names", return_value={"default", "short", "long"}):
			self.assertEqual(connect_api._resolve_connect_queue(), "default")

		with patch.object(
			connect_api, "_configured_queue_names", return_value={"default", "astra_connect"}
		):
			self.assertEqual(connect_api._resolve_connect_queue(), "astra_connect")

		# Even if resolve prefers astra_connect, enqueue must fall back on error.
		with patch.dict(connect_api.frappe.flags, {"in_test": False}):
			with patch.dict(connect_api.frappe.conf, {"astra_connect_sync_processing": 0}, clear=False):
				with patch.object(connect_api, "_resolve_connect_queue", return_value="astra_connect"):
					with patch.object(connect_api.frappe, "enqueue", side_effect=boom_then_ok):
						jid = connect_api._enqueue_processing("EVT-X", "dlv-fallback-1", attempts=0)
						self.assertIsNotNone(jid)
						self.assertEqual(len(calls), 2)
						self.assertEqual(calls[0]["queue"], "astra_connect")
						self.assertEqual(calls[1]["queue"], "default")
						self.assertNotEqual(calls[0]["job_id"], calls[1]["job_id"])
						self.assertFalse(calls[1].get("deduplicate"))
