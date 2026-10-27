"""Strip vendor-identifying response headers that the CRM app can control."""

from __future__ import annotations

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


def after_request(response):
	"""Frappe after_request hook: drop vendor-leaking headers from the response."""
	try:
		headers = response.headers
	except Exception:
		return response

	# Exact names
	for name in _HEADERS_TO_STRIP:
		if name in headers:
			del headers[name]

	# Any remaining X-Frappe-* response headers
	for name in list(headers.keys()):
		if name.lower().startswith("x-frappe"):
			del headers[name]

	return response
