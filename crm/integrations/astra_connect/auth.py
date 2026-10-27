"""HMAC signature verification for Astra Connect webhooks."""

from __future__ import annotations

import hashlib
import hmac
import time

import frappe
from frappe import _

MAX_SKEW_SECONDS = 300
HEADER_EVENT_ID = "X-Astra-Event-Id"
HEADER_TIMESTAMP = "X-Astra-Timestamp"
HEADER_SIGNATURE = "X-Astra-Signature"


class WebhookAuthError(frappe.AuthenticationError):
	pass


class WebhookDisabledError(frappe.ValidationError):
	pass


def get_webhook_secret() -> str | None:
	"""Per-site signing secret from site_config. Missing means webhooks are disabled."""
	secret = frappe.conf.get("astra_connect_webhook_secret")
	if secret is None or secret == "":
		return None
	return str(secret)


def require_webhook_secret() -> str:
	secret = get_webhook_secret()
	if not secret:
		raise WebhookDisabledError(_("Astra Connect webhooks are not configured on this site"))
	return secret


def build_signing_payload(timestamp: str | int, raw_body: str | bytes) -> bytes:
	if isinstance(raw_body, bytes):
		body = raw_body
	else:
		body = (raw_body or "").encode("utf-8")
	return f"{timestamp}.".encode("utf-8") + body


def sign_payload(secret: str, timestamp: str | int, raw_body: str | bytes) -> str:
	"""Return hex HMAC-SHA256(secret, `${timestamp}.${raw_body}`)."""
	digest = hmac.new(
		secret.encode("utf-8"),
		build_signing_payload(timestamp, raw_body),
		hashlib.sha256,
	)
	return digest.hexdigest()


def verify_signature(
	*,
	secret: str,
	timestamp: str | None,
	signature: str | None,
	raw_body: str | bytes,
	now: int | None = None,
) -> None:
	"""Reject bad signatures or timestamps more than MAX_SKEW_SECONDS off.

	Uses hmac.compare_digest for constant-time comparison.
	"""
	if not timestamp or not signature:
		raise WebhookAuthError(_("Missing webhook signature headers"))

	try:
		ts = int(str(timestamp).strip())
	except (TypeError, ValueError) as exc:
		raise WebhookAuthError(_("Invalid webhook timestamp")) from exc

	current = int(now if now is not None else time.time())
	if abs(current - ts) > MAX_SKEW_SECONDS:
		raise WebhookAuthError(_("Webhook timestamp is outside the allowed window"))

	expected = sign_payload(secret, ts, raw_body)
	provided = str(signature).strip().lower()
	if provided.startswith("sha256="):
		provided = provided[7:]

	if not hmac.compare_digest(expected.lower(), provided):
		raise WebhookAuthError(_("Invalid webhook signature"))


def read_request_headers() -> dict[str, str | None]:
	headers = frappe.request.headers if frappe.request else {}
	# werkzeug headers are case-insensitive
	return {
		"event_id": headers.get(HEADER_EVENT_ID),
		"timestamp": headers.get(HEADER_TIMESTAMP),
		"signature": headers.get(HEADER_SIGNATURE),
	}
