# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from typing import ClassVar

import frappe
from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from frappe.search.sqlite_search import SQLiteSearch

PARENT_DOCTYPES = ["CRM Lead", "CRM Deal"]
QUOTE_SELECTORS = "blockquote, .gmail_quote, .yahoo_quoted"

# Past this many readable records the IN (...) pre-filter gets too large, so hits are
# permission-checked after the search instead.
PREFILTER_LIMIT = 500


class CRMSearch(SQLiteSearch):
	INDEX_NAME = "crm_search.db"

	INDEX_SCHEMA: ClassVar = {
		"metadata_fields": ["parent", "author"],
	}

	# Record doctypes need an explicit content mapping — SQLiteSearch requires
	# the column, and Lead/Deal/Contact/Org have no HTML content field.
	INDEXABLE_DOCTYPES: ClassVar = {
		"CRM Lead": {
			"fields": [
				"name",
				{"title": "lead_name"},
				{"content": "lead_name"},
				"first_name",
				"last_name",
				"email",
				"mobile_no",
				"organization",
				"status",
				"modified",
				{"author": "lead_owner"},
			],
		},
		"CRM Deal": {
			"fields": [
				"name",
				{"title": "organization"},
				{"content": "organization"},
				"email",
				"mobile_no",
				"status",
				"modified",
				{"author": "deal_owner"},
			],
		},
		"Contact": {
			"fields": [
				"name",
				{"title": "full_name"},
				{"content": "full_name"},
				"first_name",
				"last_name",
				"email_id",
				"mobile_no",
				"company_name",
				"modified",
				{"author": "owner"},
			],
		},
		"CRM Organization": {
			"fields": [
				"name",
				{"title": "organization_name"},
				{"content": "organization_name"},
				"website",
				"industry",
				"territory",
				"modified",
				{"author": "owner"},
			],
		},
		"Comment": {
			"fields": [
				"name",
				"content",
				"modified",
				"comment_type",
				"reference_doctype",
				"reference_name",
				{"author": "comment_email"},
			],
			"filters": {
				"comment_type": "Comment",
				"reference_doctype": ("in", PARENT_DOCTYPES),
			},
		},
		"FCRM Note": {
			"fields": [
				"name",
				"title",
				"content",
				"modified",
				"reference_doctype",
				"reference_docname",
				{"author": "owner"},
			],
			"filters": {"reference_doctype": ("in", PARENT_DOCTYPES)},
		},
		"Communication": {
			"fields": [
				"name",
				{"title": "subject"},
				"content",
				"modified",
				"communication_type",
				"communication_medium",
				"reference_doctype",
				"reference_name",
				{"author": "sender"},
			],
			"filters": {
				"communication_type": "Communication",
				"communication_medium": "Email",
				"reference_doctype": ("in", PARENT_DOCTYPES),
			},
		},
	}

	# search() can return before get_search_filters() runs, so it needs a resting value.
	is_post_filter_required = False

	def get_search_filters(self) -> dict:
		parents = self.get_readable_parents()
		self.is_post_filter_required = parents is None
		return {} if parents is None else {"parent": parents}

	def get_readable_parents(self) -> list[str] | None:
		"""Return `parent` keys the user can read, or None when there are too many to pre-filter."""
		leads = frappe.get_list("CRM Lead", pluck="name", limit=PREFILTER_LIMIT + 1)
		deals = frappe.get_list("CRM Deal", pluck="name", limit=PREFILTER_LIMIT + 1)
		contacts = frappe.get_list("Contact", pluck="name", limit=PREFILTER_LIMIT + 1)
		orgs = frappe.get_list("CRM Organization", pluck="name", limit=PREFILTER_LIMIT + 1)
		if any(
			len(rows) > PREFILTER_LIMIT for rows in (leads, deals, contacts, orgs)
		):
			return None

		return (
			[parent_key("CRM Lead", name) for name in leads]
			+ [parent_key("CRM Deal", name) for name in deals]
			+ [parent_key("Contact", name) for name in contacts]
			+ [parent_key("CRM Organization", name) for name in orgs]
		)

	def prepare_document(self, doc):
		# The index queue loads documents by name, so the configured filters are not applied there.
		config = self.doc_configs.get(doc.doctype)
		if not config:
			return None
		filters = config.get("filters") or {}
		if filters and not matches_filters(doc, filters):
			return None

		document = super().prepare_document(doc)
		if not document:
			return None

		if doc.doctype in ("CRM Lead", "CRM Deal", "Contact", "CRM Organization"):
			document["parent"] = parent_key(doc.doctype, doc.name)
			# Always populate content — empty title fields still indexed by name/email/phone.
			document["content"] = self._record_content(doc) or document.get("content") or doc.name
			if not document.get("title"):
				document["title"] = document["content"].split()[0] if document["content"] else doc.name
		else:
			reference_name = doc.reference_docname if doc.doctype == "FCRM Note" else doc.reference_name
			document["parent"] = parent_key(doc.reference_doctype, reference_name)

		# Index only the new text of an email, so a phrase matches the email that said it
		# and not every later reply that quotes it.
		if doc.doctype == "Communication":
			document["content"] = self._process_content(strip_quoted_reply(doc.content))
		# Schema requires content — never leave it None (migrate / lead insert crash).
		if not document.get("content"):
			document["content"] = document.get("title") or doc.name or ""
		return document

	def _record_content(self, doc) -> str:
		fields = {
			"CRM Lead": ("lead_name", "first_name", "last_name", "email", "mobile_no", "organization", "status"),
			"CRM Deal": ("organization", "email", "mobile_no", "status"),
			"Contact": ("full_name", "first_name", "last_name", "email_id", "mobile_no", "company_name"),
			"CRM Organization": ("organization_name", "website", "industry", "territory"),
		}.get(doc.doctype, ())
		parts = []
		for field in fields:
			value = doc.get(field)
			if value not in (None, ""):
				parts.append(str(value))
		return " ".join(parts).strip()

	def add_to_queue(self, *args, **kwargs):
		"""Compatibility shim — older frappe SQLiteSearch used this name; tests patch it."""
		parent = getattr(SQLiteSearch, "add_to_queue", None)
		if callable(parent):
			return parent(self, *args, **kwargs)
		# Fall through to direct index when the parent API is absent.
		doctype = kwargs.get("doctype") or (args[0] if args else None)
		docname = kwargs.get("docname") or (args[1] if len(args) > 1 else None)
		if doctype and docname:
			return self.index_doc(doctype, docname)

	def index_doc(self, doctype, docname):
		try:
			super().index_doc(doctype, docname)
		except Exception:
			frappe.log_error(title=f"CRM search: failed to index {doctype} {docname}")

	def remove_doc(self, doctype, docname):
		try:
			super().remove_doc(doctype, docname)
		except Exception:
			frappe.log_error(title=f"CRM search: failed to remove {doctype} {docname}")


def parent_key(doctype: str, name: str) -> str:
	return f"{doctype}:{name}"


def strip_quoted_reply(html: str) -> str:
	soup = BeautifulSoup(html, "html.parser")
	for quote in soup.select(QUOTE_SELECTORS):
		quote.decompose()
	return EmailReplyParser.parse_reply(soup.get_text("\n"))


def matches_filters(doc, filters: dict) -> bool:
	for field, value in filters.items():
		actual = doc.get(field)
		if isinstance(value, tuple):
			if actual not in value[1]:
				return False
		elif actual != value:
			return False
	return True
