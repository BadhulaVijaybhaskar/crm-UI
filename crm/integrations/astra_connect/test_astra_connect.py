# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Frappe test cases for Astra Connect webhooks (CRM-04)."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.integrations.astra_connect.auth import sign_payload
from crm.integrations.astra_connect.processing import process_call_outcome, process_lead_upsert


TEST_SECRET = "astra-connect-test-secret-site-a"
OTHER_SITE_SECRET = "astra-connect-test-secret-site-b"


class TestAstraConnectWebhooks(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("DocType", "Astra Connect Event"):
			frappe.throw("Astra Connect Event DocType missing — run migrate first")

	def setUp(self):
		frappe.set_user("Administrator")
		# Ensure settings exist
		if not frappe.db.exists("DocType", "Astra Connect Settings"):
			frappe.throw("Astra Connect Settings DocType missing — run migrate first")
		settings = frappe.get_single("Astra Connect Settings")
		settings.enabled = 1
		settings.connect_base_url = "https://connect.example.test"
		settings.default_lead_owner = "Administrator"
		settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def _post(self, payload: dict, *, secret: str = TEST_SECRET, timestamp: int | None = None, event_id: str | None = None, bad_sig: bool = False):
		body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
		ts = int(timestamp if timestamp is not None else time.time())
		eid = event_id or payload.get("event_id") or frappe.generate_hash(length=12)
		sig = sign_payload(secret, ts, body)
		if bad_sig:
			sig = "0" * 64

		class _Headers(dict):
			def get(self, key, default=None):
				for k, v in self.items():
					if k.lower() == key.lower():
						return v
				return default

		headers = _Headers(
			{
				"X-Astra-Event-Id": eid,
				"X-Astra-Timestamp": str(ts),
				"X-Astra-Signature": sig,
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
		with patch("frappe.conf.get", side_effect=lambda k, default=None: secret if k == "astra_connect_webhook_secret" else frappe.conf.get(k, default)):
			# Prefer direct conf override
			prev = frappe.conf.get("astra_connect_webhook_secret")
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

	def test_good_signature_lead_upsert_create(self):
		payload = {
			"type": "lead.upsert",
			"data": {
				"external_id": "ext-lead-1",
				"name": "Ada Lovelace",
				"phone": "+14155550100",
				"email": "ada@example.com",
				"company": "Analytical Engines",
				"source": "Astra Connect",
				"ai_employee_id": "ai-emp-1",
				"campaign_id": "camp-1",
			},
		}
		result, status, eid = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		lead = frappe.get_doc("CRM Lead", {"astra_external_id": "ext-lead-1"})
		self.assertEqual(lead.email, "ada@example.com")
		self.assertEqual(lead.ai_employee_id, "ai-emp-1")
		self.assertTrue(frappe.db.exists("Astra Connect Event", {"event_id": eid, "status": "Processed"}))

	def test_lead_upsert_update(self):
		process_lead_upsert(
			{
				"external_id": "ext-lead-2",
				"name": "Grace Hopper",
				"phone": "+14155550101",
				"email": "grace@example.com",
			}
		)
		payload = {
			"type": "lead.upsert",
			"data": {
				"external_id": "ext-lead-2",
				"name": "Grace Hopper",
				"phone": "+14155550101",
				"email": "grace.updated@example.com",
				"ai_employee_id": "ai-emp-2",
			},
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		self.assertEqual(result["result"]["action"], "updated")
		lead = frappe.get_doc("CRM Lead", {"astra_external_id": "ext-lead-2"})
		self.assertEqual(lead.email, "grace.updated@example.com")
		self.assertEqual(lead.ai_employee_id, "ai-emp-2")

	def test_bad_signature(self):
		payload = {"type": "lead.upsert", "data": {"external_id": "x", "name": "X", "phone": "+14155550999"}}
		result, status, _ = self._post(payload, bad_sig=True)
		self.assertEqual(status, 401)
		self.assertEqual(result["status"], "rejected")
		self.assertFalse(frappe.db.exists("Astra Connect Event", {"event_id": result.get("event_id")}))

	def test_stale_timestamp(self):
		payload = {"type": "lead.upsert", "data": {"external_id": "stale", "name": "S", "phone": "+14155550998"}}
		result, status, _ = self._post(payload, timestamp=int(time.time()) - 301)
		self.assertEqual(status, 401)
		self.assertEqual(result["status"], "rejected")

	def test_duplicate_event_id(self):
		payload = {
			"type": "lead.upsert",
			"data": {
				"external_id": "ext-dup",
				"name": "Dup Lead",
				"phone": "+14155550102",
			},
		}
		r1, s1, eid = self._post(payload, event_id="evt-dup-1")
		self.assertEqual(s1, 200)
		self.assertEqual(r1["status"], "processed")
		count_before = frappe.db.count("CRM Lead", {"astra_external_id": "ext-dup"})
		r2, s2, _ = self._post(payload, event_id="evt-dup-1")
		self.assertEqual(s2, 200)
		self.assertEqual(r2["status"], "duplicate")
		self.assertEqual(frappe.db.count("CRM Lead", {"astra_external_id": "ext-dup"}), count_before)

	def test_call_outcome_matched(self):
		lead = process_lead_upsert(
			{
				"external_id": "ext-call-lead",
				"name": "Call Lead",
				"phone": "+14155550103",
				"email": "call@example.com",
			}
		)
		payload = {
			"type": "call.outcome",
			"data": {
				"call_id": "call-100",
				"lead_external_id": "ext-call-lead",
				"phone": "+14155550103",
				"direction": "outbound",
				"started_at": "2026-10-27 10:00:00",
				"duration_s": 95,
				"status": "completed",
				"disposition": "interested",
				"summary": "Prospect asked for a demo.",
				"ai_employee_id": "ai-emp-9",
				"next_action": {"title": "Send demo invite", "due_at": "2026-10-28 15:00:00"},
			},
		}
		result, status, _ = self._post(payload)
		self.assertEqual(status, 200)
		self.assertEqual(result["status"], "processed")
		call_log = frappe.get_doc("CRM Call Log", "call-100")
		self.assertEqual(call_log.telephony_medium, "Astra Connect")
		self.assertEqual(call_log.disposition, "interested")
		self.assertEqual(call_log.reference_docname, lead["name"])
		self.assertTrue(call_log.note)
		self.assertTrue(result["result"].get("task"))
		self.assertEqual(
			frappe.db.get_value("CRM Lead", lead["name"], "ai_employee_id"),
			"ai-emp-9",
		)

	def test_call_outcome_unmatched(self):
		payload = {
			"type": "call.outcome",
			"data": {
				"call_id": "call-orphan",
				"phone": "+14155550900",
				"direction": "inbound",
				"started_at": "2026-10-27 11:00:00",
				"duration_s": 10,
				"status": "completed",
				"summary": "No match",
			},
		}
		result, status, eid = self._post(payload)
		self.assertEqual(status, 422)
		self.assertEqual(result["status"], "failed")
		event = frappe.get_doc("Astra Connect Event", {"event_id": eid})
		self.assertEqual(event.status, "Failed")
		self.assertIn("No matching", event.error)
		self.assertFalse(frappe.db.exists("CRM Call Log", "call-orphan"))

	def test_secret_from_another_site_refused(self):
		payload = {
			"type": "lead.upsert",
			"data": {"external_id": "other-site", "name": "Other", "phone": "+14155550104"},
		}
		# Sign with site B secret while this site expects site A
		body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
		ts = int(time.time())
		eid = "evt-other-site"
		sig = sign_payload(OTHER_SITE_SECRET, ts, body)

		class _Headers(dict):
			def get(self, key, default=None):
				for k, v in self.items():
					if k.lower() == key.lower():
						return v
				return default

		headers = _Headers(
			{
				"X-Astra-Event-Id": eid,
				"X-Astra-Timestamp": str(ts),
				"X-Astra-Signature": sig,
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

	def test_disabled_without_secret(self):
		payload = {"type": "lead.upsert", "data": {"external_id": "z", "name": "Z", "phone": "+14155550105"}}
		body = json.dumps(payload)
		ts = int(time.time())

		class _Headers(dict):
			def get(self, key, default=None):
				for k, v in self.items():
					if k.lower() == key.lower():
						return v
				return default

		class _Request:
			def get_data(self):
				return body.encode("utf-8")

			@property
			def headers(self):
				return _Headers(
					{
						"X-Astra-Event-Id": "evt-disabled",
						"X-Astra-Timestamp": str(ts),
						"X-Astra-Signature": sign_payload("x", ts, body),
					}
				)

		frappe.local.request = _Request()
		frappe.local.response = frappe._dict()
		frappe.conf.pop("astra_connect_webhook_secret", None)
		if hasattr(frappe.conf, "astra_connect_webhook_secret"):
			delattr(frappe.conf, "astra_connect_webhook_secret")
		from crm.integrations.astra_connect.api import receive

		result = receive()
		status = frappe.local.response.get("http_status_code", 200)
		self.assertEqual(status, 503)
		self.assertEqual(result["status"], "disabled")

	def test_retry_failed_event(self):
		# Create unmatched failed event, then create the lead and retry
		payload = {
			"type": "call.outcome",
			"data": {
				"call_id": "call-retry-1",
				"lead_external_id": "ext-retry-lead",
				"phone": "+14155550106",
				"direction": "outbound",
				"started_at": "2026-10-27 12:00:00",
				"duration_s": 30,
				"status": "completed",
				"summary": "Retry me",
			},
		}
		result, status, eid = self._post(payload)
		self.assertEqual(status, 422)
		process_lead_upsert(
			{
				"external_id": "ext-retry-lead",
				"name": "Retry Lead",
				"phone": "+14155550106",
			}
		)
		from crm.integrations.astra_connect.api import retry_event

		retried = retry_event(eid)
		self.assertEqual(retried["status"], "processed")
		self.assertTrue(frappe.db.exists("CRM Call Log", "call-retry-1"))
