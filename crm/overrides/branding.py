"""White-label website / email chrome so framework defaults do not surface upstream names."""

from __future__ import annotations


def update_website_context(context: dict) -> None:
	context["brand_html"] = "Astra CRM"
	context["footer_address"] = ""
	context["copyright"] = ""
	# Common login / website footer keys across framework versions
	context["powered_by"] = ""
	context["footer_powered"] = ""
	if not context.get("splash_image"):
		context["splash_image"] = "/assets/crm/images/astra-crm-logo.png"


def scrub_site_branding() -> None:
	"""Clear System / Website Settings fields that inject upstream names into emails and login."""
	import frappe

	try:
		if frappe.db.has_column("System Settings", "email_footer_address"):
			frappe.db.set_single_value("System Settings", "email_footer_address", "")
	except Exception:
		frappe.log_error(title="Astra branding: System Settings email footer")

	try:
		if not frappe.db.exists("DocType", "Website Settings"):
			return
		ws = frappe.get_single("Website Settings")
		changed = False
		for field, value in (
			("app_name", "Astra CRM"),
			("title_prefix", "Astra CRM"),
			("copyright", ""),
			("footer_powered", ""),
			("footer_address", ""),
		):
			if hasattr(ws, field) and ws.get(field) != value:
				ws.set(field, value)
				changed = True
		if hasattr(ws, "splash_image") and not ws.splash_image:
			ws.splash_image = "/assets/crm/images/astra-crm-logo.png"
			changed = True
		if changed:
			ws.flags.ignore_permissions = True
			ws.save()
	except Exception:
		frappe.log_error(title="Astra branding: Website Settings")
