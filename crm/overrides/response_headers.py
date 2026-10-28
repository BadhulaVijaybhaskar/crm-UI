"""Strip vendor-identifying response headers and apply security headers.

App always emits nosniff + Referrer-Policy for the bare backend (:8831).
The in-repo nginx snippet (docker/nginx/security_headers.conf) must NOT
re-add those — use proxy_hide_header / omit add_header so values stay single.
"""

from __future__ import annotations

import re

import frappe

# Headers we remove when present on the response. CSRF tokens travel as cookies /
# boot data, not as a required response header for the SPA.
_HEADERS_TO_STRIP = (
	"Server",
	"X-Powered-By",
	"X-Page-Name",
	"X-Frappe-Site-Name",
	"X-Frappe-Version",
	"X-Frappe-App-Version",
	"X-Frappe-Request-Id",
)

# Framework base.html leaves these in every guest HTML page.
_HTML_VENDOR_COMMENT = re.compile(
	r"<!--\s*Built on Frappe\.[^>]*-->",
	re.IGNORECASE,
)
_HTML_GENERATOR_META = re.compile(
	r"""<meta\s+name=["']generator["']\s+content=["'][^"']*frappe[^"']*["']\s*/?>""",
	re.IGNORECASE,
)

# Enforcing CSP. unsafe-inline + unsafe-eval on script-src are required by Frappe
# desk: boot injects inline <script> blocks and several desk/form helpers still
# use new Function / eval. style-src unsafe-inline is required for desk + the
# Vue SPA (frappe-ui injects critical CSS). Do not remove those without a
# nonce/hash migration of desk templates.
_CSP_BASE = (
	"default-src 'self'; "
	"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
	"style-src 'self' 'unsafe-inline'; "
	"img-src 'self' data: blob:; "
	"font-src 'self' data:; "
	"media-src 'self' blob:; "
	"object-src 'none'; "
	"base-uri 'self'; "
	"form-action 'self'; "
	"frame-ancestors 'self'"
)


def _socketio_connect_sources() -> list[str]:
	"""Extra connect-src origins when socketio_port is explicitly configured."""
	extras: list[str] = []
	try:
		port = frappe.conf.get("socketio_port")
		if port in (None, "", 0, "0"):
			return extras
		port = str(port).strip()
		request = getattr(frappe.local, "request", None)
		host = None
		if request is not None:
			fwd = (request.headers.get("X-Forwarded-Host") or "").split(",")[0].strip()
			raw = fwd or (request.headers.get("Host") or "") or getattr(request, "host", "") or ""
			host = str(raw).split(":")[0].strip() or None
		if not host:
			return extras
		for scheme in ("http", "https", "ws", "wss"):
			extras.append(f"{scheme}://{host}:{port}")
	except Exception:
		return []
	return extras


def _build_csp() -> str:
	connect = ["'self'", "ws:", "wss:", *_socketio_connect_sources()]
	# de-dupe, preserve order
	seen: set[str] = set()
	connect_parts = []
	for c in connect:
		if c not in seen:
			seen.add(c)
			connect_parts.append(c)
	return f"{_CSP_BASE}; connect-src {' '.join(connect_parts)}"


def _app_security_headers() -> dict[str, str]:
	return {
		"Content-Security-Policy": _build_csp(),
		"X-Frame-Options": "SAMEORIGIN",
		"X-Content-Type-Options": "nosniff",
		"Referrer-Policy": "strict-origin-when-cross-origin",
		# camera blocked; microphone allowed for Connect/Twilio call UI; no geolocation
		"Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
	}


def _request_is_https() -> bool:
	"""True when the original client request was HTTPS (direct or via proxy)."""
	try:
		request = getattr(frappe.local, "request", None)
		if request is None:
			return False
		# Werkzeug / proxy headers
		fwd = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
		if fwd:
			return fwd == "https"
		url = getattr(request, "url", None) or ""
		if str(url).lower().startswith("https:"):
			return True
		environ = getattr(request, "environ", None) or {}
		return str(environ.get("wsgi.url_scheme", "")).lower() == "https"
	except Exception:
		return False


def after_request(response):
	"""Frappe after_request hook: drop vendor-leaking headers and set security headers."""
	try:
		headers = response.headers
	except Exception:
		return response

	for name in _HEADERS_TO_STRIP:
		if name in headers:
			del headers[name]

	for name in list(headers.keys()):
		if name.lower().startswith("x-frappe"):
			del headers[name]

	# Drop legacy report-only CSP if an older deploy left it on the response.
	if "Content-Security-Policy-Report-Only" in headers:
		del headers["Content-Security-Policy-Report-Only"]

	for name, value in _app_security_headers().items():
		headers[name] = value

	if _request_is_https():
		headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
	elif "Strict-Transport-Security" in headers:
		# Never advertise HSTS over cleartext / mis-forwarded HTTP.
		del headers["Strict-Transport-Security"]

	# .webmanifest under /assets is served by nginx — set the type there
	# (see docs/nginx-security-headers.md). Python after_request cannot fix it.

	try:
		content_type = (headers.get("Content-Type") or "").lower()
	except Exception:
		content_type = ""

	if "text/html" in content_type:
		_scrub_html_body(response)

	return response


def _scrub_html_body(response) -> None:
	try:
		data = response.get_data(as_text=True)
	except Exception:
		return
	if not data or ("Built on Frappe" not in data and "generator" not in data.lower()):
		return
	cleaned = _HTML_VENDOR_COMMENT.sub("", data)
	cleaned = _HTML_GENERATOR_META.sub("", cleaned)
	if cleaned != data:
		response.set_data(cleaned)
		# Content-Length may be stale after rewrite
		if "Content-Length" in response.headers:
			response.headers["Content-Length"] = str(len(cleaned.encode("utf-8")))
