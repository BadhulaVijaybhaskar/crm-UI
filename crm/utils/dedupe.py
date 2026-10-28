# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Duplicate-match helpers for create warnings and CSV import."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str | None) -> str:
	if not email:
		return ""
	return str(email).strip().lower()


def is_valid_email(email: str | None) -> bool:
	return bool(email and _EMAIL_RE.match(email.strip()))


def company_domain_from_website(website: str | None) -> str:
	"""Extract a registrable-ish host from a website / email domain for matching."""
	if not website:
		return ""
	raw = str(website).strip().lower()
	if not raw:
		return ""
	if "@" in raw and "://" not in raw and not raw.startswith("www."):
		# treat as email → domain part
		return raw.rsplit("@", 1)[-1]
	if "://" not in raw:
		raw = "https://" + raw
	try:
		host = urlparse(raw).hostname or ""
	except ValueError:
		return ""
	host = host.removeprefix("www.")
	return host


def dedupe_keys_from_values(
	*,
	email: str | None = None,
	phone_e164: str | None = None,
	website: str | None = None,
) -> dict[str, str]:
	"""Return the non-empty match keys present on a draft record."""
	keys: dict[str, str] = {}
	em = normalize_email(email)
	if em:
		keys["email"] = em
	if phone_e164:
		keys["phone"] = phone_e164
	domain = company_domain_from_website(website)
	if domain:
		keys["company_domain"] = domain
	return keys


def rank_match(matched_on: list[str]) -> int:
	"""Higher is stronger — email+phone beats domain-only."""
	score = 0
	if "email" in matched_on:
		score += 4
	if "phone" in matched_on:
		score += 4
	if "company_domain" in matched_on:
		score += 1
	return score


def merge_match_row(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
	"""Combine two match hits for the same document name."""
	if not existing:
		return incoming
	matched = list(dict.fromkeys([*(existing.get("matched_on") or []), *(incoming.get("matched_on") or [])]))
	merged = {**existing, **incoming, "matched_on": matched}
	merged["score"] = rank_match(matched)
	return merged
