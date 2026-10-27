import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.query_builder import JoinType, Order
from frappe.translate import get_translated_doctypes
from frappe.utils import cint, get_datetime, getdate, now_datetime, today

from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log
from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_permlevel_access


@frappe.whitelist()
def get_activities(name: str, doctype: str | None = None):
	"""Return the unified timeline for a Lead, Deal, or Contact.

	Includes field changes, emails, comments, calls (with Astra Connect outcome /
	summary / qualified when present), notes, tasks, attachments, and stage
	changes. Contact timelines also gather activity from linked leads and deals.
	"""
	doctype = (doctype or "").strip() or None
	if doctype == "Contact" or (not doctype and frappe.db.exists("Contact", name)):
		if frappe.db.exists("Contact", name):
			return get_contact_activities(name)
	if doctype == "CRM Deal" or (not doctype and frappe.db.exists("CRM Deal", name)):
		if frappe.db.exists("CRM Deal", name):
			return get_deal_activities(name)
	if doctype == "CRM Lead" or (not doctype and frappe.db.exists("CRM Lead", name)):
		if frappe.db.exists("CRM Lead", name):
			return get_lead_activities(name)
	frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_stage_change_activities(doctype: str, name: str, *, is_lead: bool = True) -> list:
	"""Stage history rows from CRM Status Change Log as timeline events."""
	if doctype not in ("CRM Lead", "CRM Deal"):
		return []
	if not frappe.db.exists(doctype, name):
		return []
	rows = frappe.db.get_all(
		"CRM Status Change Log",
		filters={"parenttype": doctype, "parent": name, "parentfield": "status_change_log"},
		fields=["name", "from", "to", "from_date", "to_date", "duration", "log_owner", "creation"],
		order_by="from_date desc",
	)
	activities = []
	for row in rows:
		# Skip the open "current stage" placeholder (no `to`) — show closed moves
		if not row.to:
			continue
		activities.append(
			{
				"name": row.name,
				"activity_type": "stage_change",
				"creation": row.to_date or row.from_date or row.creation,
				"owner": row.log_owner or "",
				"data": {
					"from": row.get("from"),
					"to": row.to,
					"duration": row.duration,
				},
				"is_lead": is_lead,
			}
		)
	return activities


def get_contact_activities(name: str):
	"""Contact timeline: own links + activity from linked leads and deals."""
	if not frappe.has_permission("Contact", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	seen_calls = set()
	seen_notes = set()
	seen_tasks = set()

	def merge(versions, _calls, _notes, _tasks, _attachments):
		nonlocal activities, calls, notes, tasks, attachments
		activities.extend(versions or [])
		for c in _calls or []:
			if c.get("name") in seen_calls:
				continue
			seen_calls.add(c.get("name"))
			calls.append(c)
		for n in _notes or []:
			if n.get("name") in seen_notes:
				continue
			seen_notes.add(n.get("name"))
			notes.append(n)
		for t in _tasks or []:
			if t.get("name") in seen_tasks:
				continue
			seen_tasks.add(t.get("name"))
			tasks.append(t)
		attachments.extend(_attachments or [])

	# Direct links on the Contact
	linked = get_linked_calls(name)
	merge([], linked.get("calls", []), get_linked_notes(name) + linked.get("notes", []), get_linked_tasks(name) + linked.get("tasks", []), get_attachments("Contact", name))
	activities += get_note_activities(notes, is_lead=False)

	# Linked deals via CRM Contacts
	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": name, "parenttype": "CRM Deal"},
		pluck="parent",
		distinct=True,
	)
	for deal in deal_names:
		if not frappe.has_permission("CRM Deal", "read", deal):
			continue
		merge(*get_deal_activities(deal))

	# Linked leads by email / phone
	contact = frappe.db.get_value(
		"Contact", name, ["email_id", "mobile_no", "phone"], as_dict=True
	) or {}
	lead_filters = []
	if contact.get("email_id"):
		lead_filters.append(["email", "=", contact.email_id])
	if contact.get("mobile_no"):
		lead_filters.append(["mobile_no", "=", contact.mobile_no])
	if contact.get("phone"):
		lead_filters.append(["phone", "=", contact.phone])
	if lead_filters:
		leads = frappe.get_all(
			"CRM Lead",
			filters={"converted": 0},
			or_filters=lead_filters,
			pluck="name",
			limit=50,
		)
		for lead in leads:
			if not frappe.has_permission("CRM Lead", "read", lead):
				continue
			merge(*get_lead_activities(lead))

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	activities = group_note_activities(activities)
	return activities, calls, notes, tasks, attachments


def get_deal_activities(name: str):
	if not frappe.has_permission("CRM Deal", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Deal", name)
	docinfo = frappe.response["docinfo"]
	deal_fields = get_readable_fields("CRM Deal")
	avoid_fields = [
		"lead",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Deal", name, ["creation", "owner", "lead"])[0]
	lead = doc[2]

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	creation_text = _("created this deal")

	if lead:
		creation_text = _("converted the lead to this deal")
		# a user can have access to the deal but not the lead it came from, so
		# skip the lead's history instead of failing the whole timeline
		if frappe.has_permission("CRM Lead", "read", lead):
			activities, calls, notes, tasks, attachments = get_lead_activities(lead)
			activities = ungroup_note_activities(activities)

	activities.append(
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": creation_text,
			"is_lead": False,
		}
	)

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = deal_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": False,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": False,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"name": communication.name,
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": False,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": False,
		}
		activities.append(activity)

	linked_calls = get_linked_calls(name)
	calls = calls + linked_calls.get("calls", [])
	# the lead's note events already came with its activities, so only add the deal's own
	lead_notes = {n.get("name") for n in notes}
	deal_notes = [
		n for n in get_linked_notes(name) + linked_calls.get("notes", []) if n.get("name") not in lead_notes
	]
	notes = notes + deal_notes
	tasks = tasks + get_linked_tasks(name) + linked_calls.get("tasks", [])
	attachments = attachments + get_attachments("CRM Deal", name)
	activities += get_note_activities(deal_notes, is_lead=False)
	activities += get_stage_change_activities("CRM Deal", name, is_lead=False)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	activities = group_note_activities(activities)

	return activities, calls, notes, tasks, attachments


def get_lead_activities(name: str):
	if not frappe.has_permission("CRM Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_fields = get_readable_fields("CRM Lead")
	avoid_fields = [
		"converted",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Lead", name, ["creation", "owner"])[0]
	activities = [
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": _("created this lead"),
			"is_lead": True,
		}
	]

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = lead_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": True,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": True,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activity = {
			"activity_type": "communication",
			"name": communication.name,
			"communication_type": communication.communication_type,
			"communication_date": communication.communication_date or communication.creation,
			"creation": communication.creation,
			"data": {
				"subject": communication.subject,
				"content": communication.content,
				"sender_full_name": communication.sender_full_name,
				"sender": communication.sender,
				"recipients": communication.recipients,
				"cc": communication.cc,
				"bcc": communication.bcc,
				"attachments": get_attachments("Communication", communication.name),
				"read_by_recipient": communication.read_by_recipient,
				"delivery_status": communication.delivery_status,
			},
			"is_lead": True,
		}
		activities.append(activity)

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": True,
		}
		activities.append(activity)

	linked_calls = get_linked_calls(name)
	calls = linked_calls.get("calls", [])
	notes = get_linked_notes(name) + linked_calls.get("notes", [])
	tasks = get_linked_tasks(name) + linked_calls.get("tasks", [])
	attachments = get_attachments("CRM Lead", name)
	activities += get_note_activities(notes, is_lead=True)
	activities += get_stage_change_activities("CRM Lead", name, is_lead=True)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)
	activities = group_note_activities(activities)

	return activities, calls, notes, tasks, attachments


def get_readable_fields(doctype: str):
	"""Map of fieldname to label & options, skipping fields the user cannot read.

	Permlevel restrictions already hide these fields on the form layout, so the
	activity timeline has to hide them too instead of leaking their values.
	"""
	allowed_permlevels = get_permlevel_access("read", doctype)

	return {
		field.fieldname: {"label": field.label, "options": field.options}
		for field in frappe.get_meta(doctype).fields
		if field.permlevel == 0 or field.permlevel in allowed_permlevels
	}


def get_attachments(doctype: str, name: str):
	return (
		frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": name},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		)
		or []
	)


def handle_multiple_versions(versions: list):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version:
				grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version:
				grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities


def group_note_activities(activities: list):
	"""Fold back-to-back note entries by the same person into one, like field changes."""
	grouped = []
	for activity in activities:
		previous = grouped[-1] if grouped else None
		if (
			activity["activity_type"] == "note"
			and previous
			and previous["activity_type"] == "note"
			and previous["owner"] == activity["owner"]
		):
			previous.setdefault("other_notes", []).append(activity)
		else:
			grouped.append(activity)
	return grouped


def ungroup_note_activities(activities: list):
	"""Undo `group_note_activities` so the lead's notes can regroup with the deal's."""
	ungrouped = []
	for activity in activities:
		ungrouped.append(activity)
		ungrouped.extend(activity.pop("other_notes", []))
	return ungrouped


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
	return version


_CALL_LOG_FIELDS = [
	"name",
	"caller",
	"receiver",
	"from",
	"to",
	"duration",
	"start_time",
	"end_time",
	"status",
	"type",
	"recording_url",
	"creation",
	"note",
	"reference_doctype",
	"reference_docname",
	"telephony_medium",
	"outcome",
	"disposition",
	"call_summary",
	"qualified",
	"channel",
	"ai_employee_id",
]


def get_linked_calls(name: str):
	# Only request fields that exist (older sites may not have Astra Connect columns yet)
	meta = frappe.get_meta("CRM Call Log")
	fields = [f for f in _CALL_LOG_FIELDS if meta.has_field(f) or f == "name"]
	calls = frappe.db.get_all(
		"CRM Call Log",
		filters={"reference_docname": name},
		fields=fields,
	)

	linked_calls = frappe.db.get_all(
		"Dynamic Link", filters={"link_name": name, "parenttype": "CRM Call Log"}, pluck="parent"
	)

	notes = []
	tasks = []

	if linked_calls:
		CallLog = frappe.qb.DocType("CRM Call Log")
		Link = frappe.qb.DocType("Dynamic Link")
		query = (
			frappe.qb.from_(CallLog)
			.select(
				CallLog.name,
				CallLog.caller,
				CallLog.receiver,
				CallLog["from"],
				CallLog.to,
				CallLog.duration,
				CallLog.start_time,
				CallLog.end_time,
				CallLog.status,
				CallLog.type,
				CallLog.recording_url,
				CallLog.creation,
				CallLog.note,
				CallLog.ai_employee_id,
				CallLog.reference_doctype,
				CallLog.reference_docname,
				Link.link_doctype,
				Link.link_name,
			)
			.join(Link, JoinType.inner)
			.on(Link.parent == CallLog.name)
			.where(CallLog.name.isin(linked_calls))
		)
		_calls = query.run(as_dict=True)

		for call in _calls:
			if call.get("link_doctype") == "FCRM Note":
				notes.append(call.link_name)
			elif call.get("link_doctype") == "CRM Task":
				tasks.append(call.link_name)

		_calls = [call for call in _calls if call.get("link_doctype") not in ["FCRM Note", "CRM Task"]]
		if _calls:
			calls = calls + _calls

	if notes:
		notes = frappe.db.get_all(
			"FCRM Note",
			filters={"name": ("in", notes)},
			fields=[
				"name",
				"title",
				"content",
				"pinned",
				"pinned_by",
				"pinned_on",
				"owner",
				"modified",
				"creation",
			],
		)

	if tasks:
		tasks = frappe.db.get_all(
			"CRM Task",
			filters={"name": ("in", tasks)},
			fields=[
				"name",
				"title",
				"description",
				"assigned_to",
				"due_date",
				"priority",
				"status",
				"modified",
			],
		)

	calls = [parse_call_log(call) for call in calls] if calls else []

	return {"calls": calls, "notes": notes, "tasks": tasks}


def get_linked_notes(name: str):
	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"reference_docname": name},
		fields=[
			"name",
			"title",
			"content",
			"pinned",
			"pinned_by",
			"pinned_on",
			"owner",
			"modified",
			"creation",
		],
	)
	return notes or []


def get_note_activities(notes: list, is_lead: bool):
	"""Timeline entries for notes being added, pinned and unpinned."""
	notes = [n for n in notes if n.get("name")]
	if not notes:
		return []

	titles = {n.get("name"): n.get("title") for n in notes}
	activities = [
		{
			"name": note.get("name"),
			"activity_type": "note",
			"creation": note.get("creation"),
			"owner": note.get("owner"),
			"data": {"action": "added", "note": note.get("name"), "title": note.get("title")},
			"is_lead": is_lead,
		}
		for note in notes
	]

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "FCRM Note", "docname": ["in", list(titles)], "data": ["like", '%"pinned"%']},
		fields=["name", "docname", "owner", "creation", "data"],
	)
	for version in versions:
		changed = json.loads(version.data).get("changed", [])
		pinned = next((c[2] for c in changed if c[0] == "pinned"), None)
		if pinned is None:
			continue
		activities.append(
			{
				"name": version.name,
				"activity_type": "note",
				"creation": version.creation,
				"owner": version.owner,
				"data": {
					"action": "pinned" if int(pinned) else "unpinned",
					"note": version.docname,
					"title": titles.get(version.docname),
				},
				"is_lead": is_lead,
			}
		)
	return activities


def get_linked_tasks(name: str):
	tasks = frappe.db.get_all(
		"CRM Task",
		filters={"reference_docname": name},
		fields=[
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"priority",
			"status",
			"modified",
			"creation",
		],
	)
	return tasks or []


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()


@frappe.whitelist()
def get_activity_feed(
	activity_type: str | None = None,
	owner: str | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	limit: int = 50,
	start: int = 0,
):
	"""Global activity feed across Leads, Deals and Contacts the user can read.

	Reuses Call Log / Communication / Comment / Note / Task / stage-change sources
	from the per-record timeline. Paged and filterable by type, owner and date.
	"""
	limit = min(cint(limit) or 50, 100)
	start = max(cint(start) or 0, 0)
	user = frappe.session.user
	items: list[dict] = []

	type_filter = (activity_type or "").strip().lower() or None
	owner_filter = (owner or "").strip() or None

	def in_range(ts) -> bool:
		if not ts:
			return False
		d = get_datetime(ts).date() if not isinstance(ts, str) else getdate(ts)
		if from_date and d < getdate(from_date):
			return False
		if to_date and d > getdate(to_date):
			return False
		return True

	# Calls
	if not type_filter or type_filter in ("calls", "all", "incoming_call", "outgoing_call"):
		call_filters: dict = {}
		if owner_filter:
			call_filters["owner"] = owner_filter
		meta = frappe.get_meta("CRM Call Log")
		fields = [f for f in _CALL_LOG_FIELDS if meta.has_field(f) or f == "name"]
		calls = frappe.get_list(
			"CRM Call Log",
			filters=call_filters or None,
			fields=fields,
			order_by="creation desc",
			limit_page_length=limit + start,
		)
		for call in calls:
			if not in_range(call.get("creation")):
				continue
			parsed = parse_call_log(dict(call))
			items.append(
				{
					"name": parsed.get("name"),
					"activity_type": parsed.get("activity_type") or "outgoing_call",
					"creation": parsed.get("creation"),
					"owner": parsed.get("owner") or call.get("owner") or "",
					"reference_doctype": parsed.get("reference_doctype"),
					"reference_docname": parsed.get("reference_docname"),
					"data": {
						"outcome": parsed.get("outcome"),
						"call_summary": parsed.get("call_summary"),
						"qualified": parsed.get("qualified"),
						"status": parsed.get("status"),
						"type": parsed.get("type"),
					},
				}
			)

	# Emails (Communication)
	if not type_filter or type_filter in ("emails", "all", "communication"):
		comm_filters = {
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
			"communication_medium": "Email",
		}
		if owner_filter:
			comm_filters["owner"] = owner_filter
		comms = frappe.get_list(
			"Communication",
			filters=comm_filters,
			fields=["name", "subject", "creation", "owner", "reference_doctype", "reference_name", "sender"],
			order_by="creation desc",
			limit_page_length=limit + start,
		)
		for c in comms:
			if not in_range(c.creation):
				continue
			items.append(
				{
					"name": c.name,
					"activity_type": "communication",
					"creation": c.creation,
					"owner": c.owner,
					"reference_doctype": c.reference_doctype,
					"reference_docname": c.reference_name,
					"data": {"subject": c.subject, "sender": c.sender},
				}
			)

	# Comments
	if not type_filter or type_filter in ("comments", "all", "comment"):
		comment_filters = {
			"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"]),
			"comment_type": "Comment",
		}
		if owner_filter:
			comment_filters["owner"] = owner_filter
		comments = frappe.get_list(
			"Comment",
			filters=comment_filters,
			fields=["name", "content", "creation", "owner", "reference_doctype", "reference_name"],
			order_by="creation desc",
			limit_page_length=limit + start,
		)
		for c in comments:
			if not in_range(c.creation):
				continue
			items.append(
				{
					"name": c.name,
					"activity_type": "comment",
					"creation": c.creation,
					"owner": c.owner,
					"reference_doctype": c.reference_doctype,
					"reference_docname": c.reference_name,
					"data": {"content": c.content},
				}
			)

	# Stage changes (closed moves only)
	if not type_filter or type_filter in ("stage", "all", "stage_change"):
		stage_filters = {"to": ("is", "set")}
		if owner_filter:
			stage_filters["log_owner"] = owner_filter
		rows = frappe.get_all(
			"CRM Status Change Log",
			filters=stage_filters,
			fields=["name", "from", "to", "to_date", "from_date", "duration", "log_owner", "parent", "parenttype"],
			order_by="to_date desc",
			limit_page_length=limit + start,
		)
		for row in rows:
			ts = row.to_date or row.from_date
			if not in_range(ts):
				continue
			if row.parenttype not in ("CRM Lead", "CRM Deal"):
				continue
			if not frappe.has_permission(row.parenttype, "read", row.parent):
				continue
			items.append(
				{
					"name": row.name,
					"activity_type": "stage_change",
					"creation": ts,
					"owner": row.log_owner or "",
					"reference_doctype": row.parenttype,
					"reference_docname": row.parent,
					"data": {"from": row.get("from"), "to": row.to, "duration": row.duration},
				}
			)

	# Notes
	if not type_filter or type_filter in ("notes", "all", "note"):
		note_filters = {"reference_doctype": ("in", ["CRM Lead", "CRM Deal", "Contact"])}
		if owner_filter:
			note_filters["owner"] = owner_filter
		notes = frappe.get_list(
			"FCRM Note",
			filters=note_filters,
			fields=["name", "title", "creation", "owner", "reference_doctype", "reference_docname"],
			order_by="creation desc",
			limit_page_length=limit + start,
		)
		for n in notes:
			if not in_range(n.creation):
				continue
			items.append(
				{
					"name": n.name,
					"activity_type": "note",
					"creation": n.creation,
					"owner": n.owner,
					"reference_doctype": n.reference_doctype,
					"reference_docname": n.reference_docname,
					"data": {"title": n.title},
				}
			)

	items.sort(key=lambda x: x.get("creation") or "", reverse=True)
	page = items[start : start + limit]
	return {"items": page, "start": start, "limit": limit, "has_more": len(items) > start + limit}


@frappe.whitelist()
def get_my_day():
	"""Agenda for the signed-in user: overdue/due-today tasks, today's calls, today's meetings."""
	user = frappe.session.user
	today_str = today()
	day_start = get_datetime(f"{today_str} 00:00:00")
	day_end = get_datetime(f"{today_str} 23:59:59")

	tasks = frappe.get_list(
		"CRM Task",
		filters={
			"assigned_to": user,
			"status": ("not in", ["Done", "Canceled", "Cancelled"]),
			"due_date": ("<=", today_str),
		},
		fields=[
			"name",
			"title",
			"status",
			"priority",
			"due_date",
			"reference_doctype",
			"reference_docname",
		],
		order_by="due_date asc",
		limit_page_length=50,
	)
	for t in tasks:
		t["overdue"] = bool(t.due_date and getdate(t.due_date) < getdate(today_str))

	# Calls involving the user today (caller, receiver, or owner)
	CallLog = frappe.qb.DocType("CRM Call Log")
	calls_query = (
		frappe.qb.from_(CallLog)
		.select(
			CallLog.name,
			CallLog.type,
			CallLog.status,
			CallLog.creation,
			CallLog["from"],
			CallLog.to,
			CallLog.reference_doctype,
			CallLog.reference_docname,
		)
		.where(CallLog.creation.between(day_start, day_end))
		.where(
			(CallLog.caller == user) | (CallLog.receiver == user) | (CallLog.owner == user)
		)
		.orderby(CallLog.creation, order=Order.desc)
		.limit(50)
	)
	# Optional Connect columns when present
	meta = frappe.get_meta("CRM Call Log")
	if meta.has_field("outcome"):
		calls_query = calls_query.select(CallLog.outcome)
	if meta.has_field("qualified"):
		calls_query = calls_query.select(CallLog.qualified)
	calls = calls_query.run(as_dict=True)

	meetings = []
	if frappe.db.exists("DocType", "Event"):
		event_names = frappe.get_all(
			"Event Participants",
			filters={"email": user},
			pluck="parent",
		)
		if event_names:
			meetings = frappe.get_list(
				"Event",
				filters={
					"name": ("in", event_names),
					"starts_on": ("between", [day_start, day_end]),
				},
				fields=["name", "subject", "starts_on", "ends_on", "status", "event_type"],
				order_by="starts_on asc",
				limit_page_length=50,
			)

	return {
		"date": today_str,
		"tasks": tasks,
		"calls": calls,
		"meetings": meetings,
		"now": str(now_datetime()),
	}
