"""HMAC signature verification for Astra Connect webhooks."""

from __future__ import annotations

import hashlib
import hmac
import re
import time

import frappe
from frappe import _

MAX_SKEW_SECONDS = 300
HEADER_DELIVERY = "X-Astra-Delivery"
HEADER_EVENT_ID = "X-Astra-Event-Id"
HEADER_TIMESTAMP = "X-Astra-Timestamp"
HEADER_SIGNATURE = "X-Astra-Signature"

# t=<ts>,v1=<hex>  (timestamp may be quoted or bare)
_TV1_RE = re.compile(
	r"(?:^|,)\s*t=(?P<ts>[0-9]+)\s*,\s*v1=(?P<sig>[0-9a-fA-F]+)\s*(?:,|$)",
	re.IGNORECASE,
)


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
	"""Return hex HMAC-SHA256(secret, ``ts + '.' + rawBody``)."""
	digest = hmac.new(
		secret.encode("utf-8"),
		build_signing_payload(timestamp, raw_body),
		hashlib.sha256,
	)
	return digest.hexdigest()


def parse_signature_header(
	signature: str | None,
	timestamp_header: str | None = None,
) -> tuple[int, str]:
	"""Return (unix_ts, hex_digest) from either signature style.

	Supported:
	- ``sha256=<hex>`` with ``X-Astra-Timestamp``
	- ``t=<ts>,v1=<hex>`` (timestamp inside the signature header)
	"""
	if not signature:
		raise WebhookAuthError(_("Missing webhook signature headers"))

	raw = str(signature).strip()
	lower = raw.lower()

	# Style A: sha256=<hex> (+ X-Astra-Timestamp)
	if lower.startswith("sha256="):
		if not timestamp_header:
			raise WebhookAuthError(_("Missing X-Astra-Timestamp for sha256 signature"))
		try:
			ts = int(str(timestamp_header).strip())
		except (TypeError, ValueError) as exc:
			raise WebhookAuthError(_("Invalid webhook timestamp")) from exc
		hex_digest = raw.split("=", 1)[1].strip()
		if not hex_digest or not re.fullmatch(r"[0-9a-fA-F]+", hex_digest):
			raise WebhookAuthError(_("Invalid webhook signature"))
		return ts, hex_digest

	# Style B: t=<ts>,v1=<hex>
	m = _TV1_RE.search(raw)
	if m:
		return int(m.group("ts")), m.group("sig")

	raise WebhookAuthError(_("Unrecognized webhook signature format"))


def verify_signature(
	*,
	secret: str,
	timestamp: str | None,
	signature: str | None,
	raw_body: str | bytes,
	now: int | None = None,
) -> int:
	"""Verify signature; return the timestamp used. Raises WebhookAuthError on failure.

	Uses hmac.compare_digest for constant-time comparison. Rejects timestamps more
	than MAX_SKEW_SECONDS off.
	"""
	ts, provided = parse_signature_header(signature, timestamp)
	current = int(now if now is not None else time.time())
	if abs(current - ts) > MAX_SKEW_SECONDS:
		raise WebhookAuthError(_("Webhook timestamp is outside the allowed window"))

	expected = sign_payload(secret, ts, raw_body)
	if not hmac.compare_digest(expected.lower(), provided.lower()):
		raise WebhookAuthError(_("Invalid webhook signature"))
	return ts


def read_request_headers() -> dict[str, str | None]:
	headers = frappe.request.headers if frappe.request else {}
	# Prefer X-Astra-Delivery for dedupe (Replay reuses it); Event-Id is fallback.
	delivery = headers.get(HEADER_DELIVERY)
	event_id = headers.get(HEADER_EVENT_ID)
	return {
		"delivery_id": delivery,
		"event_id": (delivery or event_id),
		"timestamp": headers.get(HEADER_TIMESTAMP),
		"signature": headers.get(HEADER_SIGNATURE),
	}
