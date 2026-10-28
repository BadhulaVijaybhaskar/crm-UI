# Copyright (c) 2026, Astra and contributors
# See license.txt

"""Read-only Conversations view over existing CRM call / email / note / WhatsApp activity.

Does not send WhatsApp or email — replies open Astra Connect (Message with AI).
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, strip_html

from crm.api.whatsapp import is_whatsapp_installed
from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log


CHANNEL_CALL = "call"
CHANNEL_EMAIL = "email"
CHANNEL_NOTE = "note"
CHANNEL_WHATSAPP = "whatsapp"


def _record_key(doctype: str, name: str) -> str:
	return f"{doctype}::{name}"


def _title_for(doctype: str, name: str) -> dict:
	if doctype == "CRM Lead":
		row = frappe.db.get_value(
			"CRM Lead",
			name,
			["lead_name", "organization", "email", "mobile_no", "status", "lead_owner", "job_title"],
			as_dict=True,
		)
		if not row:
			return {"title": name, "subtitle": _("Lead")}
		return {
			"title": row.lead_name or name,
			"subtitle": " · ".join(p for p in [row.job_title, row.organization or _("Lead")] if p),
			"organization": row.organization,
			"email": row.email,
			"mobile_no": row.mobile_no,
			"status": row.status,
			"owner": row.lead_owner,
			"route": {"name": "Lead", "params": {"leadId": name}},
		}
	if doctype == "CRM Deal":
		row = frappe.db.get_value(
			"CRM Deal",
			name,
			[
				"organization",
				"lead_name",
				"email",
				"mobile_no",
				"status",
				"deal_owner",
				"deal_value",
				"expected_deal_value",
				"next_step",
				"job_title",
			],
			as_dict=True,
		)
		if not row:
			return {"title": name, "subtitle": _("Deal")}
		return {
			"title": row.lead_name or row.organization or name,
			"subtitle": " · ".join(p for p in [row.job_title, row.organization or _("Deal")] if p),
			"organization": row.organization,
			"email": row.email,
			"mobile_no": row.mobile_no,
			"status": row.status,
			"owner": row.deal_owner,
			"value": row.expected_deal_value or row.deal_value,
			"next_step": row.next_step,
			"route": {"name": "Deal", "params": {"dealId": name}},
		}
	if doctype == "Contact":
		row = frappe.db.get_value(
			"Contact",
			name,
			["full_name", "email_id", "mobile_no", "company_name"],
			as_dict=True,
		)
		if not row:
			return {"title": name, "subtitle": _("Contact")}
		return {
			"title": row.full_name or name,
			"subtitle": row.company_name or _("Contact"),
			"organization": row.company_name,
			"email": row.email_id,
			"mobile_no": row.mobile_no,
			"route": {"name": "Contact", "params": {"contactId": name}},
		}
	return {"title": name, "subtitle": doctype}


def _preview(text: str | None, limit: int = 120) -> str:
	if not text:
		return ""
	clean = strip_html(str(text)).strip().replace("\n", " ")
	return clean[:limit]


def _collect_events(limit_per_channel: int = 80) -> list[dict]:
	events: list[dict] = []

	# Calls
	from crm.api.activities import _call_log_list_fields

	fields = _call_log_list_fields()
	calls = frappe.get_list(
		"CRM Call Log",
		filters={"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"])},
		fields=fields,
		order_by="creation desc",
		limit_page_length=limit_per_channel,
	)
	for call in calls:
		if not call.get("reference_doctype") or not call.get("reference_docname"):
			continue
		parsed = parse_call_log(dict(call))
		events.append(
			{
				"channel": CHANNEL_CALL,
				"name": parsed.get("name") or call.name,
				"creation": parsed.get("creation") or call.get("creation"),
				"reference_doctype": call.reference_doctype,
				"reference_docname": call.reference_docname,
				"preview": _preview(
					parsed.get("outcome")
					or parsed.get("call_summary")
					or f"{parsed.get('type') or call.get('type') or ''} · {parsed.get('status') or call.get('status') or ''}"
				),
				"data": parsed,
			}
		)

	# Emails
	comms = frappe.get_list(
		"Communication",
		filters={
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
			"communication_medium": "Email",
		},
		fields=[
			"name",
			"subject",
			"content",
			"creation",
			"owner",
			"sender",
			"sender_full_name",
			"recipients",
			"reference_doctype",
			"reference_name",
			"communication_date",
		],
		order_by="creation desc",
		limit_page_length=limit_per_channel,
	)
	for c in comms:
		events.append(
			{
				"channel": CHANNEL_EMAIL,
				"name": c.name,
				"creation": c.communication_date or c.creation,
				"reference_doctype": c.reference_doctype,
				"reference_docname": c.reference_name,
				"preview": _preview(c.subject or c.content),
				"data": {
					"subject": c.subject,
					"content": c.content,
					"sender": c.sender,
					"sender_full_name": c.sender_full_name,
					"recipients": c.recipients,
					"owner": c.owner,
				},
			}
		)

	# Notes
	notes = frappe.get_list(
		"FCRM Note",
		filters={"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"])},
		fields=["name", "title", "content", "creation", "owner", "reference_doctype", "reference_docname"],
		order_by="creation desc",
		limit_page_length=limit_per_channel,
	)
	for n in notes:
		events.append(
			{
				"channel": CHANNEL_NOTE,
				"name": n.name,
				"creation": n.creation,
				"reference_doctype": n.reference_doctype,
				"reference_docname": n.reference_docname,
				"preview": _preview(n.title or n.content),
				"data": {"title": n.title, "content": n.content, "owner": n.owner},
			}
		)

	# WhatsApp (only when the WhatsApp app is installed)
	if is_whatsapp_installed() and frappe.db.exists("DocType", "WA Message"):
		try:
			messages = frappe.get_list(
				"WA Message",
				filters={"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"])},
				fields=[
					"name",
					"message",
					"creation",
					"timestamp",
					"direction",
					"status",
					"owner",
					"reference_doctype",
					"reference_docname",
				],
				order_by="creation desc",
				limit_page_length=limit_per_channel,
			)
		except frappe.PermissionError:
			messages = []
		for m in messages:
			events.append(
				{
					"channel": CHANNEL_WHATSAPP,
					"name": m.name,
					"creation": m.timestamp or m.creation,
					"reference_doctype": m.reference_doctype,
					"reference_docname": m.reference_docname,
					"preview": _preview(m.message),
					"data": {
						"message": m.message,
						"direction": m.direction,
						"status": m.status,
						"owner": m.owner,
					},
				}
			)

	return events


@frappe.whitelist()
def get_conversations(channel: str | None = None, search: str | None = None, limit: int = 40) -> dict:
	"""People/record threads built from existing CRM activity. Read-only."""
	limit = min(cint(limit) or 40, 100)
	channel = (channel or "all").strip().lower()
	search = (search or "").strip().lower()

	events = _collect_events()
	if channel and channel != "all":
		events = [e for e in events if e["channel"] == channel]

	threads: dict[str, dict] = {}
	counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

	for event in events:
		doctype = event.get("reference_doctype")
		name = event.get("reference_docname")
		if not doctype or not name:
			continue
		if not frappe.has_permission(doctype, "read", name):
			continue
		key = _record_key(doctype, name)
		counts[key][event["channel"]] += 1
		existing = threads.get(key)
		if not existing:
			meta = _title_for(doctype, name)
			threads[key] = {
				"id": key,
				"reference_doctype": doctype,
				"reference_docname": name,
				"title": meta.get("title") or name,
				"subtitle": meta.get("subtitle") or "",
				"organization": meta.get("organization"),
				"email": meta.get("email"),
				"mobile_no": meta.get("mobile_no"),
				"status": meta.get("status"),
				"owner": meta.get("owner"),
				"value": meta.get("value"),
				"next_step": meta.get("next_step"),
				"route": meta.get("route"),
				"latest_preview": event.get("preview") or "",
				"latest_at": event.get("creation"),
				"latest_channel": event.get("channel"),
				"channels": {event["channel"]},
			}
		else:
			existing["channels"].add(event["channel"])
			# events are newest-first; keep first as latest
			pass

	items = []
	for key, thread in threads.items():
		if search:
			hay = " ".join(
				[
					thread.get("title") or "",
					thread.get("subtitle") or "",
					thread.get("organization") or "",
					thread.get("latest_preview") or "",
				]
			).lower()
			if search not in hay:
				continue
		thread_channels = sorted(thread.pop("channels"))
		items.append(
			{
				**thread,
				"channels": thread_channels,
				"channel_counts": dict(counts[key]),
			}
		)

	items.sort(key=lambda t: t.get("latest_at") or "", reverse=True)
	items = items[:limit]

	available_channels = [CHANNEL_CALL, CHANNEL_EMAIL, CHANNEL_NOTE]
	if is_whatsapp_installed():
		available_channels.append(CHANNEL_WHATSAPP)

	return {
		"items": items,
		"available_channels": available_channels,
		"whatsapp_available": is_whatsapp_installed(),
	}


@frappe.whitelist()
def get_conversation_thread(reference_doctype: str, reference_docname: str, limit: int = 100) -> dict:
	"""Full read-only timeline for one record, newest first then reversed for display."""
	doctype = (reference_doctype or "").strip()
	name = (reference_docname or "").strip()
	if not doctype or not name:
		frappe.throw(_("Record is required"))
	if not frappe.has_permission(doctype, "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	limit = min(cint(limit) or 100, 200)
	events = [
		e
		for e in _collect_events(limit_per_channel=limit)
		if e.get("reference_doctype") == doctype and e.get("reference_docname") == name
	]
	events.sort(key=lambda e: e.get("creation") or "")

	meta = _title_for(doctype, name)
	channel_counts: dict[str, int] = defaultdict(int)
	for e in events:
		channel_counts[e["channel"]] += 1

	# Next open task on this record (for the side panel)
	next_task = None
	tasks = frappe.get_list(
		"CRM Task",
		filters={
			"reference_doctype": doctype,
			"reference_docname": name,
			"status": ("in", ["Backlog", "Todo", "In Progress"]),
		},
		fields=["name", "title", "due_date", "status", "priority"],
		order_by="due_date asc",
		limit_page_length=1,
	)
	if tasks:
		next_task = tasks[0]

	return {
		"reference_doctype": doctype,
		"reference_docname": name,
		"meta": meta,
		"events": events,
		"channel_counts": dict(channel_counts),
		"next_task": next_task,
		"read_only": True,
	}
