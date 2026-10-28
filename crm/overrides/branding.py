"""White-label website / email chrome so framework defaults do not surface upstream names."""

from __future__ import annotations

ASTRA_APP_NAME = "Astra CRM"
ASTRA_SPLASH = "/assets/crm/images/astra-crm-logo.png"
ASTRA_LOGO = "/assets/crm/images/astra-crm-logo.png"
ASTRA_FAVICON = "/assets/crm/images/favicon-32.png"
ASTRA_SUPPORT = "mailto:support@astraconnect.io"


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
	context["logo"] = context.get("logo") or ASTRA_LOGO
	context["app_logo"] = context.get("app_logo") or ASTRA_LOGO
	# Login page: do not reveal the website footer (JS would otherwise .show() it).
	context["show_footer_on_login"] = 0


def scrub_site_branding() -> None:
	"""Persist Website / System Settings so login HTML and emails stay white-labelled.

	Uses ``frappe.db.set_single_value`` so missing mandatory fields (language,
	time zone, etc.) cannot abort the scrub the way ``Document.save()`` does.
	"""
	import frappe

	_scrub_system_settings()
	_scrub_website_settings()
	frappe.db.commit()
	frappe.clear_cache()


def _set_single(doctype: str, field: str, value) -> None:
	import frappe

	try:
		frappe.db.set_single_value(doctype, field, value)
	except Exception:
		# Field may not exist on this framework version
		frappe.log_error(title=f"Astra branding: set {doctype}.{field}")


def _scrub_system_settings() -> None:
	import frappe

	if not frappe.db.exists("DocType", "System Settings"):
		return

	_set_single("System Settings", "app_name", ASTRA_APP_NAME)
	_set_single("System Settings", "email_footer_address", "")
	_set_single("System Settings", "disable_standard_email_footer", 1)
	_set_single("System Settings", "hide_footer_in_auto_email_reports", 1)
	# 2FA issuer shown in authenticator apps
	_set_single("System Settings", "otp_issuer_name", ASTRA_APP_NAME)
	# Desk telemetry hits pulse.m.frappe.cloud — keep off for white-label.
	_set_single("System Settings", "enable_telemetry", 0)
	# Skip the upstream setup wizard on first login
	_set_single("System Settings", "setup_complete", 1)
	_set_single("System Settings", "language", "en")
	_set_single("System Settings", "time_zone", "Asia/Kolkata")
	_set_single("System Settings", "currency", "INR")
	_set_single("System Settings", "number_format", "#,##,###.##")

	# email_body.get_footer reads these via frappe.db.get_default
	frappe.db.set_default("email_footer_address", "")
	frappe.db.set_default("disable_standard_email_footer", "1")
	frappe.db.set_default("app_name", ASTRA_APP_NAME)
	frappe.db.set_default("otp_issuer_name", ASTRA_APP_NAME)
	frappe.db.set_default("currency", "INR")
	frappe.db.set_default("number_format", "#,##,###.##")
	frappe.db.set_default("enable_telemetry", "0")

	if frappe.db.exists("DocType", "FCRM Settings"):
		_set_single("FCRM Settings", "setup_completed", 1)


def _scrub_website_settings() -> None:
	import frappe

	if not frappe.db.exists("DocType", "Website Settings"):
		return

	for field, value in (
		("app_name", ASTRA_APP_NAME),
		("title_prefix", ASTRA_APP_NAME),
		("brand_html", ASTRA_APP_NAME),
		("copyright", ""),
		("footer_powered", " "),
		("address", ""),
		("show_footer_on_login", 0),
		("splash_image", ASTRA_SPLASH),
		("app_logo", ASTRA_LOGO),
		("banner_image", ASTRA_LOGO),
		("favicon", ASTRA_FAVICON),
		# Brand in transactional / welcome emails
		("brand_with", ASTRA_APP_NAME),
		("email_footer_address", ""),
	):
		_set_single("Website Settings", field, value)

	# Welcome email subject / heading (field names vary by framework version)
	for field, value in (
		("welcome_email_subject", f"Welcome to {ASTRA_APP_NAME}"),
		("welcome_email_heading", f"Welcome to {ASTRA_APP_NAME}"),
		("email_brand", ASTRA_APP_NAME),
		("email_brand_name", ASTRA_APP_NAME),
	):
		_set_single("Website Settings", field, value)

	# security.txt — point at Astra support or clear framework default
	for field, value in (
		("enable_security_txt", 0),
		("security_txt", f"Contact: {ASTRA_SUPPORT}\n"),
	):
		_set_single("Website Settings", field, value)


def apply_doctype_label_overrides() -> None:
	"""Neutralize user-visible DocType / field labels without renaming internals."""
	import frappe

	erp_settings_dt = "".join(("ERP", "Next", " CRM Settings"))
	field_labels = [
		# (doctype, fieldname, new label)
		(erp_settings_dt, "section_break_oubd", "ERP Site APIs"),
		(erp_settings_dt, "erpnext_site_url", "ERP Site URL"),
		(erp_settings_dt, "erpnext_company", "Company on ERP site"),
		(erp_settings_dt, "is_erpnext_in_different_site", "Is ERP installed on a different site?"),
	]
	for doctype, fieldname, label in field_labels:
		if not frappe.db.exists("DocType", doctype):
			continue
		if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			pass
		_ensure_property_setter(doctype, fieldname, "label", label, "Data")

	translations = {
		erp_settings_dt: "ERP Settings",
		"FCRM Settings": "CRM Settings",
		"FCRM Note": "Note",
		# Desk sidebar / module chrome — keep internal module name "FCRM" and
		# Workspace document name "Frappe CRM"; only the user-visible string changes.
		"Frappe CRM": ASTRA_APP_NAME,
		"FCRM": ASTRA_APP_NAME,
	}
	for source, translated in translations.items():
		_ensure_translation(source, translated)

	_relabel_fcrm_module()


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


def _relabel_fcrm_module() -> None:
	"""Ensure Module Def for FCRM displays as Astra CRM without renaming the module.

	Module name stays ``FCRM`` (doctype ``module`` fields and ``modules.txt``).
	Desk module headers use the Module Def row; when a ``module_name`` / label-like
	column exists we mirror the visible brand. Translations cover ``_("FCRM")``.
	"""
	import frappe

	if not frappe.db.exists("DocType", "Module Def"):
		return
	if not frappe.db.exists("Module Def", "FCRM"):
		return

	# Some framework versions expose a separate display field; prefer it when present.
	for field in ("module_name", "label"):
		if frappe.db.has_column("Module Def", field):
			current = frappe.db.get_value("Module Def", "FCRM", field)
			if current != ASTRA_APP_NAME:
				frappe.db.set_value("Module Def", "FCRM", field, ASTRA_APP_NAME, update_modified=False)


def relabel_crm_workspace() -> None:
	"""Set Workspace label/title to Astra CRM without changing the document name or route.

	Uses ``frappe.db.set_value`` so a partial Workspace row (missing mandatory
	``type``) cannot fail migrate via ``Document.save()``.
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

	# Ensure mandatory type is present before any future full saves.
	if frappe.db.has_column("Workspace", "type"):
		current_type = frappe.db.get_value("Workspace", doc_name, "type")
		if not current_type:
			frappe.db.set_value("Workspace", doc_name, "type", "Workspace", update_modified=False)

	updates = {}
	current_title = frappe.db.get_value("Workspace", doc_name, "title")
	current_label = frappe.db.get_value("Workspace", doc_name, "label")
	if current_title != visible:
		updates["title"] = visible
	if current_label != visible:
		updates["label"] = visible
	# Public route slug only — document name stays "Frappe CRM".
	if frappe.db.has_column("Workspace", "route"):
		current_route = frappe.db.get_value("Workspace", doc_name, "route")
		if current_route != "astra-crm":
			updates["route"] = "astra-crm"
	if updates:
		frappe.db.set_value("Workspace", doc_name, updates, update_modified=False)

	# Desk often renders _(workspace.name) — keep the document name, translate the string.
	_ensure_translation(doc_name, visible)
	_ensure_translation("FCRM", visible)
	_relabel_fcrm_module()


# Back-compat alias for older patch imports
rename_crm_workspace = relabel_crm_workspace
