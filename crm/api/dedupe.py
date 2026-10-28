# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Find likely duplicates when creating Leads, Contacts, or Organizations."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr

from crm.utils import normalize_phone
from crm.utils.dedupe import (
	company_domain_from_website,
	merge_match_row,
	normalize_email,
	rank_match,
)

SUPPORTED = {
	"CRM Lead": {
		"email_field": "email",
		"phone_fields": ("mobile_no", "phone"),
		"website_field": "website",
		"title_fields": ("lead_name", "first_name", "last_name", "email"),
	},
	"Contact": {
		"email_field": "email_id",
		"phone_fields": ("mobile_no", "phone"),
		"website_field": None,
		"title_fields": ("full_name", "first_name", "last_name", "email_id"),
	},
	"CRM Organization": {
		"email_field": None,
		"phone_fields": (),
		"website_field": "website",
		"title_fields": ("organization_name", "website"),
	},
}


@frappe.whitelist()
def find_duplicates(
	doctype: str,
	email: str | None = None,
	phone: str | None = None,
	website: str | None = None,
	exclude: str | None = None,
	limit: int = 10,
):
	"""Return existing records that match email, E.164 phone, or company domain.

	Used by create dialogs to warn before inserting a likely duplicate.
	"""
	if doctype not in SUPPORTED:
		frappe.throw(_("Duplicate check is not supported for {0}").format(doctype))

	frappe.has_permission(doctype, "read", throw=True)

	cfg = SUPPORTED[doctype]
	email_n = normalize_email(email)
	phone_n = normalize_phone(phone) if phone else ""
	domain = company_domain_from_website(website)

	if not (email_n or phone_n or domain):
		return []

	hits: dict[str, dict] = {}

	if email_n and cfg["email_field"]:
		for row in _by_email(doctype, cfg["email_field"], email_n, exclude, limit):
			hits[row["name"]] = merge_match_row(
				hits.get(row["name"]),
				_hit(doctype, row, cfg, ["email"]),
			)

	if phone_n and cfg["phone_fields"]:
		for row in _by_phone(doctype, cfg["phone_fields"], phone_n, exclude, limit):
			hits[row["name"]] = merge_match_row(
				hits.get(row["name"]),
				_hit(doctype, row, cfg, ["phone"]),
			)

	if domain and cfg["website_field"]:
		for row in _by_domain(doctype, cfg["website_field"], domain, exclude, limit):
			hits[row["name"]] = merge_match_row(
				hits.get(row["name"]),
				_hit(doctype, row, cfg, ["company_domain"]),
			)

	results = sorted(hits.values(), key=lambda r: (-r["score"], r["name"]))
	return results[: max(1, min(int(limit or 10), 25))]


def _hit(doctype: str, row: dict, cfg: dict, matched_on: list[str]) -> dict:
	title = _title(row, cfg["title_fields"])
	return {
		"doctype": doctype,
		"name": row["name"],
		"title": title,
		"matched_on": matched_on,
		"score": rank_match(matched_on),
		"email": row.get(cfg["email_field"]) if cfg["email_field"] else None,
		"phone": next((row.get(f) for f in cfg["phone_fields"] if row.get(f)), None),
		"website": row.get(cfg["website_field"]) if cfg["website_field"] else None,
	}


def _title(row: dict, fields: tuple[str, ...]) -> str:
	parts = []
	for f in fields:
		val = row.get(f)
		if val and val not in parts:
			parts.append(cstr(val))
		if len(parts) >= 2:
			break
	return " ".join(parts) if parts else row.get("name") or ""


def _by_email(doctype: str, field: str, email: str, exclude: str | None, limit: int):
	filters = {field: email}
	if exclude:
		filters["name"] = ["!=", exclude]
	return frappe.get_all(
		doctype,
		filters=filters,
		fields=["name", field, *(_extra_fields(doctype))],
		limit_page_length=limit,
	)


def _by_phone(doctype: str, fields: tuple[str, ...], phone_e164: str, exclude: str | None, limit: int):
	"""Match by exact stored value or last-10 digits (common CRM entry variance)."""
	digits = "".join(ch for ch in phone_e164 if ch.isdigit())
	last10 = digits[-10:] if len(digits) >= 10 else digits
	or_filters = []
	for field in fields:
		or_filters.append([doctype, field, "=", phone_e164])
		or_filters.append([doctype, field, "like", f"%{last10}"])
	filters = {}
	if exclude:
		filters["name"] = ["!=", exclude]
	rows = frappe.get_all(
		doctype,
		filters=filters,
		or_filters=or_filters,
		fields=["name", *fields, *(_extra_fields(doctype))],
		limit_page_length=limit * 3,
	)
	# Re-check with normalize_phone so LIKE false positives drop out.
	out = []
	for row in rows:
		for field in fields:
			cand = row.get(field)
			if cand and normalize_phone(cand) == phone_e164:
				out.append(row)
				break
		if len(out) >= limit:
			break
	return out


def _by_domain(doctype: str, field: str, domain: str, exclude: str | None, limit: int):
	filters = {field: ["like", f"%{domain}%"]}
	if exclude:
		filters["name"] = ["!=", exclude]
	rows = frappe.get_all(
		doctype,
		filters=filters,
		fields=["name", field, *(_extra_fields(doctype))],
		limit_page_length=limit * 3,
	)
	return [r for r in rows if company_domain_from_website(r.get(field)) == domain][:limit]


def _extra_fields(doctype: str) -> list[str]:
	cfg = SUPPORTED[doctype]
	fields = list(cfg["title_fields"])
	if cfg["email_field"]:
		fields.append(cfg["email_field"])
	fields.extend(cfg["phone_fields"])
	if cfg["website_field"]:
		fields.append(cfg["website_field"])
	# unique while preserving order
	return list(dict.fromkeys(fields))
