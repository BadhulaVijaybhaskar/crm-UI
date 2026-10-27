"""Strip vendor-identifying response headers and HTML chrome the CRM app can control."""

from __future__ import annotations

import re

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

_SECURITY_HEADERS = {
	"X-Content-Type-Options": "nosniff",
	"Referrer-Policy": "strict-origin-when-cross-origin",
	# Report-only CSP — tighten later; do not break desk/login scripts.
	"Content-Security-Policy-Report-Only": (
		"default-src 'self'; "
		"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
		"style-src 'self' 'unsafe-inline'; "
		"img-src 'self' data: blob:; "
		"font-src 'self' data:; "
		"connect-src 'self' ws: wss:; "
		"frame-ancestors 'self'"
	),
}


def after_request(response):
	"""Frappe after_request hook: drop vendor-leaking headers and HTML chrome."""
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

	for name, value in _SECURITY_HEADERS.items():
		if name not in headers:
			headers[name] = value

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
