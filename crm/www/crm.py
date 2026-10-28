# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# GNU GPLv3 License. See license.txt

import frappe
from frappe import _, get_installed_apps
from frappe.translate import get_messages_for_boot, get_translated_doctypes
from frappe.utils import cint, get_system_timezone
from frappe.utils.telemetry import capture

no_cache = 1

# Built at runtime so the vendor product string is not in the /crm page source.
_ERP_CRM_SETTINGS_DOCTYPE = "".join(("ERP", "Next", " CRM Settings"))


def _is_fc_site() -> bool:
	"""Optional cloud-host check — never hard-require the vendor billing module."""
	try:
		from frappe.integrations.frappe_providers import frappecloud_billing

		return bool(frappecloud_billing.is_fc_site())
	except Exception:
		return False


def get_context():
	from crm.api import check_app_permission

	# Guests hitting /crm should go to login, not a raw 403 page.
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect

	if not check_app_permission():
		frappe.throw(_("You do not have permission to access Astra CRM"), frappe.PermissionError)

	redirect_to_set_password()

	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	if frappe.session.user != "Guest":
		capture("active_site", "crm")
	return context


def redirect_to_set_password():
	"""Send users who have no password of their own to the set password page.

	The Frappe Cloud site owner arrives on a session handed over by the
	dashboard and never sets a password, so they cannot get back in once it
	expires. Invited users are already routed here by `accept_invitation`; this
	covers everyone else, on the same page.
	"""
	from crm.api.user import needs_password_setup

	if not needs_password_setup():
		return

	user = frappe.get_doc("User", frappe.session.user)
	link = user._reset_password()

	# this is a GET request, which is rolled back unless a commit is requested
	frappe.local.flags.commit = True

	frappe.local.flags.redirect_location = link

	# 302, not the 301 default: v16+ lets the browser cache a permanent redirect,
	# which would keep sending the user to a spent key long after they set a
	# password. Set on the instance — v15's `Redirect` takes no constructor arg.
	redirect = frappe.Redirect()
	redirect.http_status_code = 302
	raise redirect


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	from crm.overrides.branding import ASTRA_APP_NAME

	sysdefaults = frappe.defaults.get_defaults() or {}
	# Boot JSON is user-visible — never ship upstream product names or framework version.
	sysdefaults = dict(sysdefaults)
	sysdefaults["app_name"] = ASTRA_APP_NAME
	sysdefaults["otp_issuer_name"] = ASTRA_APP_NAME

	return frappe._dict(
		{
			"default_route": get_default_route(),
			"site_name": frappe.local.site,
			"socketio_port": frappe.conf.socketio_port,
			"read_only_mode": frappe.flags.read_only,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"setup_complete": cint(frappe.get_system_settings("setup_complete")),
			"sysdefaults": sysdefaults,
			"app_name": ASTRA_APP_NAME,
			"is_demo_site": frappe.conf.get("is_demo_site"),
			"demo_data_created": frappe.db.get_default("crm_demo_data_created") == "1",
			"is_fc_site": _is_fc_site(),
			"translated_doctypes": get_translated_doctypes(),
			"translated_messages": get_messages_for_boot(),
			"timezone": {
				"system": get_system_timezone(),
				"user": frappe.db.get_value("User", frappe.session.user, "time_zone")
				or get_system_timezone(),
			},
			"state_options": get_state_options(),
			"erp_integration_available": _erp_integration_available(),
			**_astra_connect_boot(),
		}
	)


def _astra_connect_boot() -> dict:
	"""Expose Connect UI only when Astra Connect Settings is enabled and has a base URL.

	Without the Settings DocType (or when disabled / URL blank), Connect nav and
	Call/Message with AI stay hidden — no dead links.
	"""
	enabled = False
	url = ""
	try:
		if frappe.db.exists("DocType", "Astra Connect Settings"):
			enabled = bool(cint(frappe.db.get_single_value("Astra Connect Settings", "enabled")))
			url = (
				frappe.db.get_single_value("Astra Connect Settings", "connect_base_url") or ""
			).strip().rstrip("/")
	except Exception:
		enabled = False
		url = ""

	configured = bool(enabled and url)
	return {
		"astra_connect_enabled": configured,
		"astra_connect_url": url if configured else "",
	}


def _erp_integration_available() -> bool:
	"""True when ERPNext is installed locally or ERP CRM Settings is already on."""
	try:
		from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
			_is_erpnext_installed,
		)

		if _is_erpnext_installed():
			return True
		if frappe.db.exists("DocType", _ERP_CRM_SETTINGS_DOCTYPE):
			return bool(cint(frappe.db.get_single_value(_ERP_CRM_SETTINGS_DOCTYPE, "enabled")))
	except Exception:
		return False
	return False


def get_state_options() -> dict[str, list[str]]:
	"""Country -> list of states, so the frontend can render a state dropdown.

	Sourced from India Compliance's own constant when that app is installed, so the
	options stay in sync with the desk. Returns an empty map (state field stays free
	text) on any failure.

	This runs inside ``get_boot``, so it must never raise — a failure here would break
	the whole CRM page load. ``get_installed_apps`` can return `[]` or raise in
	unauthenticated/boot contexts (notably on v15), so the lookup is wrapped defensively.
	"""
	try:
		if "india_compliance" not in get_installed_apps():
			return {}

		from india_compliance.gst_india.constants import INDIAN_STATES

		return {"India": list(INDIAN_STATES)}
	except Exception:
		# Degrade silently to free-text: this runs in boot, so the except branch
		# must not do anything that can itself raise (e.g. logging to a missing dir).
		return {}


def get_default_route():
	return "/crm"
