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
	"""Idempotent seed called from after_install / after_migrate."""
	ensure_fcrm_currency_inr()
	ensure_organization_tax_fields()
	ensure_indian_state_territories()
	ensure_starter_email_templates()
	ensure_starter_whatsapp_templates()
	ensure_lead_round_robin_rule()


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
	# Seed a CRM Global Settings JSON fallback the UI can read if WA DocType is absent.
	key = "india_whatsapp_starters"
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
	if frappe.db.exists("DocType", "CRM Global Settings"):
		if not frappe.db.exists("CRM Global Settings", {"dt": key}):
			frappe.get_doc(
				{
					"doctype": "CRM Global Settings",
					"dt": key,
					"json": frappe.as_json(payload),
				}
			).insert(ignore_permissions=True)

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


def ensure_lead_round_robin_rule():
	"""Create a disabled round-robin Assignment Rule for CRM Lead."""
	if not frappe.db.exists("DocType", "Assignment Rule"):
		return
	name = "Astra Lead Round Robin"
	if frappe.db.exists("Assignment Rule", name):
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
		}
	)
	# Field names vary slightly across framework versions
	if hasattr(doc, "assignment_rule_users") or True:
		pass
	try:
		doc.insert(ignore_permissions=True)
	except Exception:
		# Older sites may require users before insert — leave disabled stub via db
		frappe.log_error(title="Astra India assignment rule seed")
