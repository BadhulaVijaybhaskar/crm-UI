# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime

STATUS_DOCTYPE_BY_PARENT = {
	"CRM Lead": "CRM Lead Status",
	"CRM Deal": "CRM Deal Status",
}


class CRMStatusChangeLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		duration: DF.Duration | None
		from_date: DF.Datetime | None
		from_type: DF.Data | None
		last_status_change_log: DF.Link | None
		log_owner: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		to: DF.Data | None
		to_date: DF.Datetime | None
		to_type: DF.Data | None
	# end: auto-generated types

	pass


def get_duration(from_date, to_date):
	if not isinstance(from_date, datetime):
		from_date = get_datetime(from_date)
	if not isinstance(to_date, datetime):
		to_date = get_datetime(to_date)
	duration = to_date - from_date
	return duration.total_seconds()


def _status_doctype_for(doc) -> str:
	return STATUS_DOCTYPE_BY_PARENT.get(doc.doctype, "CRM Deal Status")


def _status_type(status_doctype: str, status: str | None) -> str:
	if not status:
		return ""
	return frappe.db.get_value(status_doctype, status, "type") or ""


def add_status_change_log(doc):
	"""Append stage history when ``status`` changes on CRM Lead / CRM Deal.

	Records from/to, owner, timestamps, and duration spent in the previous stage.
	Uses the correct status DocType for Lead vs Deal type lookups.
	"""
	status_dt = _status_doctype_for(doc)
	to_status_type = _status_type(status_dt, doc.status)

	if not doc.is_new():
		previous_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
		previous_status_type = _status_type(status_dt, previous_status)
		if not doc.status_change_log and previous_status:
			now_minus_one_minute = add_to_date(datetime.now(), minutes=-1)
			doc.append(
				"status_change_log",
				{
					"from": previous_status,
					"from_type": previous_status_type or "",
					"to": "",
					"to_type": "",
					"from_date": now_minus_one_minute,
					"to_date": "",
					"log_owner": frappe.session.user,
				},
			)
		last_status_change = doc.status_change_log[-1]
		last_status_change.to = doc.status
		last_status_change.to_type = to_status_type or ""
		last_status_change.to_date = datetime.now()
		last_status_change.log_owner = frappe.session.user
		last_status_change.duration = get_duration(last_status_change.from_date, last_status_change.to_date)

	doc.append(
		"status_change_log",
		{
			"from": doc.status,
			"from_type": to_status_type or "",
			"to": "",
			"to_type": "",
			"from_date": datetime.now(),
			"to_date": "",
			"log_owner": frappe.session.user,
		},
	)


def set_status_with_history(doctype: str, name: str, status: str, *, ignore_permissions: bool = False):
	"""Update status via Document.save so stage history and validate hooks run.

	Prefer this over ``frappe.db.set_value`` for API/webhook status writes.
	"""
	doc = frappe.get_doc(doctype, name)
	if doc.status == status:
		return doc
	doc.status = status
	doc.flags.ignore_permissions = ignore_permissions
	doc.save(ignore_permissions=ignore_permissions)
	return doc
