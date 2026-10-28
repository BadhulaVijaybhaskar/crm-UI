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
		# frappe.local may not define request until a WSGI hit — create=True.
		with patch.object(frappe.local, "request", request, create=True):
			rh.after_request(resp)

		self.assertIn("Content-Security-Policy", resp.headers)
		self.assertNotIn("Content-Security-Policy-Report-Only", resp.headers)
		csp = resp.headers["Content-Security-Policy"]
		self.assertIn("frame-ancestors 'self'", csp)
		self.assertIn("object-src 'none'", csp)
		self.assertIn("connect-src", csp)
		self.assertIn("'self'", csp)
		# Desk still needs these; documented in module docstring.
		self.assertIn("'unsafe-inline'", csp)
		self.assertIn("'unsafe-eval'", csp)
		self.assertEqual(resp.headers["X-Frame-Options"], "SAMEORIGIN")
		self.assertIn("camera=()", resp.headers["Permissions-Policy"])
		self.assertIn("microphone=(self)", resp.headers["Permissions-Policy"])
		self.assertIn("geolocation=()", resp.headers["Permissions-Policy"])
		# Bare backend always emits these (nginx snippet must not duplicate).
		self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
		self.assertEqual(resp.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
		self.assertNotIn("Server", resp.headers)
		self.assertNotIn("X-Frappe-Version", resp.headers)

	def test_hsts_only_on_https(self):
		resp_http, req_http = self._response(https=False)
		with patch.object(frappe.local, "request", req_http, create=True):
			rh.after_request(resp_http)
		self.assertNotIn("Strict-Transport-Security", resp_http.headers)

		resp_https, req_https = self._response(https=True)
		with patch.object(frappe.local, "request", req_https, create=True):
			rh.after_request(resp_https)
		self.assertEqual(
			resp_https.headers["Strict-Transport-Security"],
			"max-age=31536000; includeSubDomains",
		)

	def test_csp_includes_configured_socketio_origin(self):
		resp, request = self._response(https=False)
		request.headers = {
			"X-Forwarded-Proto": "http",
			"Host": "crm.example:8831",
		}
		with patch.object(frappe.local, "request", request, create=True):
			with patch.dict(
				frappe.conf, {"socketio_port": 9000, "astra_socketio_direct": 1}, clear=False
			):
				rh.after_request(resp)
		csp = resp.headers["Content-Security-Policy"]
		self.assertIn("http://crm.example:9000", csp)
		self.assertIn("ws://crm.example:9000", csp)

	def test_csp_omits_socketio_port_without_direct_opt_in(self):
		resp, request = self._response(https=False)
		request.headers = {"X-Forwarded-Proto": "http", "Host": "crm.example:8831"}
		with patch.object(frappe.local, "request", request, create=True):
			with patch.dict(
				frappe.conf, {"socketio_port": 9000, "astra_socketio_direct": 0}, clear=False
			):
				rh.after_request(resp)
		csp = resp.headers["Content-Security-Policy"]
		self.assertNotIn(":9000", csp)


class TestLoginLockoutStatus(UnitTestCase):
	def test_security_exception_maps_to_429(self):
		from crm.overrides.login_lockout import ensure_lockout_returns_429

		ensure_lockout_returns_429()
		self.assertEqual(frappe.SecurityException.http_status_code, 429)


class TestAssetsScrub(UnitTestCase):
	def test_strip_sourcemaps_removes_map_files(self):
		import os
		import tempfile
		from pathlib import Path

		from crm.overrides.assets_scrub import strip_sourcemaps

		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			real = root / "real"
			real.mkdir()
			(real / "app.js").write_text("ok")
			(real / "app.js.map").write_text('{"version":3}')
			# Symlink tree like sites/assets/frappe -> apps/frappe/.../dist
			link = root / "assets"
			link.mkdir()
			os.symlink(real, link / "frappe", target_is_directory=True)
			removed = strip_sourcemaps(extra_roots=[link])
			self.assertGreaterEqual(removed, 1)
			self.assertTrue((real / "app.js").exists())
			self.assertFalse((real / "app.js.map").exists())
