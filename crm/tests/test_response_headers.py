# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Unit tests for crm.overrides.response_headers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from crm.overrides import response_headers as rh


class _Hdr(dict):
	"""Case-preserving header bag with ``in`` / ``del`` like Werkzeug."""

	def __contains__(self, key):
		return dict.__contains__(self, key)

	def keys(self):
		return dict.keys(self)


class TestResponseHeaders(UnitTestCase):
	def _response(self, *, https=False, content_type="application/json"):
		resp = MagicMock()
		resp.headers = _Hdr()
		resp.headers["Content-Type"] = content_type
		resp.headers["Server"] = "nginx"
		resp.headers["X-Frappe-Version"] = "15"
		resp.headers["Content-Security-Policy-Report-Only"] = "old"
		resp.get_data.return_value = ""
		request = MagicMock()
		request.headers = {"X-Forwarded-Proto": "https" if https else "http"}
		request.url = "https://crm.example/api" if https else "http://crm.example/api"
		request.environ = {"wsgi.url_scheme": "https" if https else "http"}
		return resp, request

	def test_enforcing_csp_and_frame_permissions(self):
		resp, request = self._response(https=False)
		with patch.object(frappe.local, "request", request):
			rh.after_request(resp)

		self.assertIn("Content-Security-Policy", resp.headers)
		self.assertNotIn("Content-Security-Policy-Report-Only", resp.headers)
		csp = resp.headers["Content-Security-Policy"]
		self.assertIn("frame-ancestors 'self'", csp)
		self.assertIn("object-src 'none'", csp)
		# Desk still needs these; documented in module docstring.
		self.assertIn("'unsafe-inline'", csp)
		self.assertIn("'unsafe-eval'", csp)
		self.assertEqual(resp.headers["X-Frame-Options"], "SAMEORIGIN")
		self.assertIn("camera=()", resp.headers["Permissions-Policy"])
		self.assertIn("microphone=(self)", resp.headers["Permissions-Policy"])
		self.assertIn("geolocation=()", resp.headers["Permissions-Policy"])
		# Edge owns nosniff / Referrer-Policy — app must not duplicate them.
		self.assertNotIn("X-Content-Type-Options", resp.headers)
		self.assertNotIn("Referrer-Policy", resp.headers)
		self.assertNotIn("Server", resp.headers)
		self.assertNotIn("X-Frappe-Version", resp.headers)

	def test_hsts_only_on_https(self):
		resp_http, req_http = self._response(https=False)
		with patch.object(frappe.local, "request", req_http):
			rh.after_request(resp_http)
		self.assertNotIn("Strict-Transport-Security", resp_http.headers)

		resp_https, req_https = self._response(https=True)
		with patch.object(frappe.local, "request", req_https):
			rh.after_request(resp_https)
		self.assertEqual(
			resp_https.headers["Strict-Transport-Security"],
			"max-age=31536000; includeSubDomains",
		)


class TestLoginLockoutStatus(UnitTestCase):
	def test_security_exception_maps_to_429(self):
		from crm.overrides.login_lockout import ensure_lockout_returns_429

		ensure_lockout_returns_429()
		self.assertEqual(frappe.SecurityException.http_status_code, 429)


class TestAssetsScrub(UnitTestCase):
	def test_strip_sourcemaps_removes_map_files(self):
		import tempfile
		from pathlib import Path

		from crm.overrides.assets_scrub import strip_sourcemaps

		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			(root / "app.js").write_text("ok")
			(root / "app.js.map").write_text('{"version":3}')
			nested = root / "chunk"
			nested.mkdir()
			(nested / "x.js.map").write_text("{}")
			removed = strip_sourcemaps(extra_roots=[root])
			self.assertGreaterEqual(removed, 2)
			self.assertTrue((root / "app.js").exists())
			self.assertFalse((root / "app.js.map").exists())
			self.assertFalse((nested / "x.js.map").exists())
