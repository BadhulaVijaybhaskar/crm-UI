"""Map Frappe login lockouts to HTTP 429 instead of an unhandled 500.

``LoginAttemptTracker`` / ``get_login_attempt_tracker`` raise
``frappe.SecurityException`` when consecutive failures exceed System Settings.
That exception historically has no ``http_status_code``, so the framework
responds with 500. Attaching 429 matches ``TooManyRequestsError`` semantics.
"""

from __future__ import annotations


def ensure_lockout_returns_429() -> None:
	"""Idempotent: set SecurityException.http_status_code = 429."""
	import frappe

	exc = getattr(frappe, "SecurityException", None)
	if exc is None:
		return
	if getattr(exc, "http_status_code", None) != 429:
		exc.http_status_code = 429


# Apply at import so login requests never race the first before_request.
ensure_lockout_returns_429()
