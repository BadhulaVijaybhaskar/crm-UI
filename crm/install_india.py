# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""India defaults (CRM-15): territories, templates, assignment rule, org tax fields."""

from __future__ import annotations

import re

import frappe
from frappe import _

INDIAN_STATES = [
	"Andhra Pradesh",
	"Arunachal Pradesh",
	"Assam",
	"Bihar",
	"Chhattisgarh",
	"Goa",
	"Gujarat",
	"Haryana",
	"Himachal Pradesh",
	"Jharkhand",
	"Karnataka",
	"Kerala",
	"Madhya Pradesh",
	"Maharashtra",
	"Manipur",
	"Meghalaya",
	"Mizoram",
	"Nagaland",
	"Odisha",
	"Punjab",
	"Rajasthan",
	"Sikkim",
	"Tamil Nadu",
	"Telangana",
	"Tripura",
	"Uttar Pradesh",
	"Uttarakhand",
	"West Bengal",
	"Andaman and Nicobar Islands",
	"Chandigarh",
	"Dadra and Nagar Haveli and Daman and Diu",
	"Delhi",
	"Jammu and Kashmir",
	"Ladakh",
	"Lakshadweep",
	"Puducherry",
]

# GSTIN: 2 digit state + 10 char PAN + entity + Z + check char
_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")


def ensure_india_defaults():
	"""Idempotent seed called from after_install / after_migrate.

	Each step is isolated so a single LinkValidationError cannot abort migrate.
	"""
	for step in (
		ensure_system_country_india,
		ensure_fcrm_currency_inr,
		ensure_organization_tax_fields,
		ensure_indian_state_territories,
		ensure_starter_email_templates,
		ensure_starter_whatsapp_templates,
		ensure_lead_round_robin_rule,
	):
		try:
			step()
		except Exception:
			frappe.log_error(title=f"Astra India defaults: {step.__name__}")


def ensure_system_country_india():
	"""Drive +91 E.164 parsing via System Settings country → IN region."""
	if not frappe.db.exists("DocType", "System Settings"):
		return
	if not frappe.db.get_single_value("System Settings", "country"):
		frappe.db.set_single_value("System Settings", "country", "India")
	# Keep timezone/currency aligned if scrubbing already ran
	frappe.db.set_single_value("System Settings", "time_zone", "Asia/Kolkata")
	frappe.db.set_single_value("System Settings", "currency", "INR")
	frappe.db.set_single_value("System Settings", "number_format", "#,##,###.##")
	frappe.db.set_default("country", "India")
	frappe.db.set_default("currency", "INR")
	frappe.db.set_default("number_format", "#,##,###.##")


def ensure_fcrm_currency_inr():
	if frappe.db.exists("DocType", "FCRM Settings"):
		current = frappe.db.get_single_value("FCRM Settings", "currency")
		if not current or current == "USD":
			frappe.db.set_single_value("FCRM Settings", "currency", "INR")


def ensure_organization_tax_fields():
	"""GSTIN / PAN / State on CRM Organization (custom fields so meta sync is safe)."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"CRM Organization": [
				{
					"fieldname": "tax_section",
					"fieldtype": "Section Break",
					"label": "Tax details",
					"insert_after": "address",
				},
				{
					"fieldname": "gstin",
					"fieldtype": "Data",
					"label": "GSTIN",
					"insert_after": "tax_section",
					"length": 15,
				},
				{
					"fieldname": "pan",
					"fieldtype": "Data",
					"label": "PAN",
					"insert_after": "gstin",
					"length": 10,
				},
				{
					"fieldname": "column_break_tax",
					"fieldtype": "Column Break",
					"insert_after": "pan",
				},
				{
					"fieldname": "india_state",
					"fieldtype": "Select",
					"label": "State",
					"options": "\n".join([""] + INDIAN_STATES),
					"insert_after": "column_break_tax",
				},
			]
		},
		ignore_validate=True,
		update=True,
	)


def validate_organization_tax_fields(doc, method=None):
	gstin = (getattr(doc, "gstin", None) or "").strip().upper()
	pan = (getattr(doc, "pan", None) or "").strip().upper()
	if gstin:
		doc.gstin = gstin
		if not _GSTIN_RE.match(gstin):
			frappe.throw(_("GSTIN must be a valid 15-character GST identification number"))
		# PAN embedded in GSTIN positions 3–12
		embedded = gstin[2:12]
		if pan and pan != embedded:
			frappe.throw(_("PAN must match the PAN embedded in GSTIN"))
		if not pan:
			doc.pan = embedded
	if pan:
		doc.pan = pan
		if not _PAN_RE.match(pan):
			frappe.throw(_("PAN must be a valid 10-character Permanent Account Number"))


def ensure_indian_state_territories():
	if not frappe.db.exists("DocType", "CRM Territory"):
		return
	# Group parent
	parent_name = "India"
	if not frappe.db.exists("CRM Territory", parent_name):
		frappe.get_doc(
			{
				"doctype": "CRM Territory",
				"territory_name": parent_name,
				"is_group": 1,
			}
		).insert(ignore_permissions=True)

	for state in INDIAN_STATES:
		if frappe.db.exists("CRM Territory", state):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Territory",
				"territory_name": state,
				"parent_crm_territory": parent_name,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)


def ensure_starter_email_templates():
	if not frappe.db.exists("DocType", "Email Template"):
		return
	templates = [
		{
			"name": "Astra Lead Intro",
			"subject": "Following up — {{ doc.first_name or doc.lead_name }}",
			"response": (
				"<p>Hi {{ doc.first_name or 'there' }},</p>"
				"<p>Thanks for your interest. Happy to share how Astra CRM can help your team.</p>"
				"<p>Best regards</p>"
			),
		},
		{
			"name": "Astra Meeting Request",
			"subject": "Quick call this week?",
			"response": (
				"<p>Hi {{ doc.first_name or 'there' }},</p>"
				"<p>Would you have 20 minutes this week for a short call?</p>"
				"<p>Thanks</p>"
			),
		},
	]
	for t in templates:
		if frappe.db.exists("Email Template", t["name"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": t["name"],
				"subject": t["subject"],
				"response": t["response"],
				"enabled": 1,
				"use_html": 1,
			}
		)
		# Optional CRM custom fields
		if frappe.get_meta("Email Template").has_field("enabled"):
			doc.enabled = 1
		doc.insert(ignore_permissions=True)


def ensure_starter_whatsapp_templates():
	# WhatsApp templates live in different doctypes depending on the WA app.
	# CRM Global Settings.dt is a Link to DocType — never seed a fake dt value
	# (that LinkValidationError breaks migrate). Persist starters as a default.
	payload = [
		{
			"name": "lead_intro",
			"label": "Lead intro",
			"body": "Hi {{first_name}}, thanks for reaching out. This is {{agent_name}} from Astra.",
		},
		{
			"name": "meeting_nudge",
			"label": "Meeting nudge",
			"body": "Hi {{first_name}}, just checking if a quick call this week still works for you?",
		},
	]
	try:
		frappe.db.set_default("india_whatsapp_starters", frappe.as_json(payload))
	except Exception:
		frappe.log_error(title="Astra India WhatsApp starters default")

	# Prefer native WhatsApp Message Template when present
	for doctype in ("WhatsApp Templates", "WA Template", "WhatsApp Message Template"):
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		for row in payload:
			filters = {"template_name": row["name"]} if meta.has_field("template_name") else {"name": row["label"]}
			if frappe.db.exists(doctype, filters):
				continue
			doc = frappe.new_doc(doctype)
			if meta.has_field("template_name"):
				doc.template_name = row["name"]
			# WA Template.validate calls normalize_string(template_label) — never leave None.
			if meta.has_field("template_label"):
				doc.template_label = row["label"]
			if meta.has_field("label"):
				doc.label = row["label"]
			if meta.has_field("template"):
				doc.template = row["body"]
			if meta.has_field("message"):
				doc.message = row["body"]
			if meta.has_field("status"):
				doc.status = "Pending"
			try:
				doc.insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(title="Astra India WhatsApp template seed")
		break


_ALL_WEEKDAYS = (
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
)


def ensure_lead_round_robin_rule():
	"""Create a disabled round-robin Assignment Rule for CRM Lead."""
	if not frappe.db.exists("DocType", "Assignment Rule"):
		return
	name = "Astra Lead Round Robin"
	if frappe.db.exists("Assignment Rule", name):
		# Backfill assignment_days on older seeds that omitted the child table.
		existing = frappe.get_doc("Assignment Rule", name)
		if not existing.get("assignment_days"):
			for day in _ALL_WEEKDAYS:
				existing.append("assignment_days", {"day": day})
			try:
				existing.save(ignore_permissions=True)
			except Exception:
				frappe.log_error(title="Astra India assignment rule days backfill")
		return
	doc = frappe.get_doc(
		{
			"doctype": "Assignment Rule",
			"name": name,
			"document_type": "CRM Lead",
			"rule": "Round Robin",
			"priority": 1,
			"disabled": 1,
			"description": "Round-robin new leads across Sales Users (disabled by default)",
			"assign_condition": 'doc.status == "New"',
			"assignment_days": [{"day": day} for day in _ALL_WEEKDAYS],
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except Exception:
		# Older sites may require users before insert — leave disabled stub via db
		frappe.log_error(title="Astra India assignment rule seed")
