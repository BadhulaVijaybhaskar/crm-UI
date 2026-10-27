# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMOutboundWebhook(Document):
	pass


@frappe.whitelist()
def list_outbound_webhooks():
	frappe.only_for("System Manager")
	return frappe.get_all(
		"CRM Outbound Webhook",
		fields=["name", "title", "enabled", "endpoint_url", "events", "modified"],
		order_by="modified desc",
	)
