"""White-label website / email chrome so framework defaults do not surface upstream names."""

from __future__ import annotations

ASTRA_APP_NAME = "Astra CRM"
ASTRA_SPLASH = "/assets/crm/images/astra-crm-logo.png"
ASTRA_LOGO = "/assets/crm/images/astra-crm-logo.png"


def update_website_context(context: dict) -> None:
	"""Force brand context on every website/login render (no CSS-only hiding)."""
	context["brand_html"] = ASTRA_APP_NAME
	context["app_name"] = ASTRA_APP_NAME
	context["footer_address"] = ""
	context["copyright"] = ""
	# Non-empty so templates/includes/footer/footer_info.html skips the
	# framework's footer_powered.html include path; CRM also ships an empty
	# footer_powered.html override and a footer_info.html without that column.
	context["footer_powered"] = " "
	context["powered_by"] = ""
	context["splash_image"] = context.get("splash_image") or ASTRA_SPLASH
	# Login page: do not reveal the website footer (JS would otherwise .show() it).
	context["show_footer_on_login"] = 0


def scrub_site_branding() -> None:
	"""Persist Website / System Settings so login HTML and emails stay white-labelled."""
	import frappe

	_scrub_system_settings()
	_scrub_website_settings()
	frappe.clear_cache()


def _set_if_present(doc, field: str, value) -> bool:
	if not hasattr(doc, field):
		return False
	if doc.get(field) == value:
		return False
	doc.set(field, value)
	return True


def _scrub_system_settings() -> None:
	import frappe

	try:
		if not frappe.db.exists("DocType", "System Settings"):
			return
		ss = frappe.get_single("System Settings")
		changed = False
		changed |= _set_if_present(ss, "app_name", ASTRA_APP_NAME)
		changed |= _set_if_present(ss, "email_footer_address", "")
		# Turns off the framework "Sent via …" / default_mail_footer block in emails.
		changed |= _set_if_present(ss, "disable_standard_email_footer", 1)
		if hasattr(ss, "hide_footer_in_auto_email_reports"):
			changed |= _set_if_present(ss, "hide_footer_in_auto_email_reports", 1)
		if changed:
			ss.flags.ignore_permissions = True
			ss.save()
		# email_body.get_footer reads these via frappe.db.get_default
		frappe.db.set_default("email_footer_address", "")
		frappe.db.set_default("disable_standard_email_footer", "1")
	except Exception:
		frappe.log_error(title="Astra branding: System Settings")


def _scrub_website_settings() -> None:
	import frappe

	try:
		if not frappe.db.exists("DocType", "Website Settings"):
			return
		ws = frappe.get_single("Website Settings")
		changed = False
		for field, value in (
			("app_name", ASTRA_APP_NAME),
			("title_prefix", ASTRA_APP_NAME),
			("brand_html", ASTRA_APP_NAME),
			("copyright", ""),
			("footer_powered", " "),
			("address", ""),
			("show_footer_on_login", 0),
		):
			changed |= _set_if_present(ws, field, value)
		if hasattr(ws, "splash_image") and not ws.splash_image:
			ws.splash_image = ASTRA_SPLASH
			changed = True
		if hasattr(ws, "app_logo") and not ws.app_logo:
			ws.app_logo = ASTRA_LOGO
			changed = True
		if hasattr(ws, "favicon") and not ws.favicon:
			ws.favicon = "/assets/crm/images/favicon-32.png"
			changed = True
		if changed:
			ws.flags.ignore_permissions = True
			ws.save()
	except Exception:
		frappe.log_error(title="Astra branding: Website Settings")


def apply_doctype_label_overrides() -> None:
	"""Neutralize user-visible DocType / field labels without renaming internals."""
	import frappe

	field_labels = [
		# (doctype, fieldname, new label)
		("ERPNext CRM Settings", "section_break_oubd", "ERP Site APIs"),
		("ERPNext CRM Settings", "erpnext_site_url", "ERP Site URL"),
		("ERPNext CRM Settings", "erpnext_company", "Company on ERP site"),
		("ERPNext CRM Settings", "is_erpnext_in_different_site", "Is ERP installed on a different site?"),
	]
	for doctype, fieldname, label in field_labels:
		if not frappe.db.exists("DocType", doctype):
			continue
		if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			# Section breaks may lack DocField rows on some versions; still try.
			pass
		_ensure_property_setter(doctype, fieldname, "label", label, "Data")

	# DocType titles shown via __(doctype) — seed English translations.
	translations = {
		"ERPNext CRM Settings": "ERP Settings",
		"FCRM Settings": "CRM Settings",
		"FCRM Note": "Note",
	}
	for source, translated in translations.items():
		_ensure_translation(source, translated)


def _ensure_property_setter(doctype: str, fieldname: str, prop: str, value: str, property_type: str) -> None:
	import frappe
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	name = f"{doctype}-{fieldname}-{prop}"
	existing = frappe.db.exists("Property Setter", {"name": name})
	if existing:
		current = frappe.db.get_value("Property Setter", existing, "value")
		if current != value:
			frappe.db.set_value("Property Setter", existing, "value", value)
		return
	# Also match by filters in case naming differs
	filters = {"doc_type": doctype, "field_name": fieldname, "property": prop}
	if frappe.db.exists("Property Setter", filters):
		frappe.db.set_value("Property Setter", filters, "value", value)
		return
	make_property_setter(doctype, fieldname, prop, value, property_type, validate_fields_for_doctype=False)


def _ensure_translation(source: str, translated: str, language: str = "en") -> None:
	import frappe

	filters = {"language": language, "source_text": source}
	if frappe.db.exists("Translation", filters):
		name = frappe.db.exists("Translation", filters)
		if frappe.db.get_value("Translation", name, "translated_text") != translated:
			frappe.db.set_value("Translation", name, "translated_text", translated)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Translation",
			"language": language,
			"source_text": source,
			"translated_text": translated,
		}
	)
	doc.insert(ignore_permissions=True)


def relabel_crm_workspace() -> None:
	"""Set Workspace label/title to Astra CRM without changing the document name or route.

	If a prior scrub renamed the Workspace document itself, restore the original
	document name so internal identifiers stay stable.
	"""
	import frappe
	from frappe.model.rename_doc import rename_doc

	doc_name = "Frappe CRM"
	visible = ASTRA_APP_NAME
	if not frappe.db.exists("DocType", "Workspace"):
		return

	# Undo an earlier document rename if it happened.
	if frappe.db.exists("Workspace", visible) and not frappe.db.exists("Workspace", doc_name):
		rename_doc("Workspace", visible, doc_name, force=True, merge=False)

	if not frappe.db.exists("Workspace", doc_name):
		return

	ws = frappe.get_doc("Workspace", doc_name)
	changed = False
	if getattr(ws, "title", None) != visible:
		ws.title = visible
		changed = True
	if getattr(ws, "label", None) != visible:
		ws.label = visible
		changed = True
	if changed:
		ws.flags.ignore_permissions = True
		ws.save()


# Back-compat alias for older patch imports
rename_crm_workspace = relabel_crm_workspace
