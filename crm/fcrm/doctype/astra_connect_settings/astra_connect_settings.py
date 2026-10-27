# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AstraConnectSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		connect_base_url: DF.Data | None
		default_lead_owner: DF.Link | None
		enabled: DF.Check
	# end: auto-generated types

	def validate(self):
		if self.connect_base_url:
			self.connect_base_url = self.connect_base_url.rstrip("/")


def get_connect_base_url() -> str:
	"""Public Connect base URL for deep-links (never includes secrets)."""
	url = frappe.db.get_single_value("Astra Connect Settings", "connect_base_url")
	if url:
		return str(url).rstrip("/")
	return (frappe.conf.get("astra_connect_url") or "https://connect.astraconnect.io").rstrip("/")


def is_connect_enabled() -> bool:
	return bool(frappe.db.get_single_value("Astra Connect Settings", "enabled"))
