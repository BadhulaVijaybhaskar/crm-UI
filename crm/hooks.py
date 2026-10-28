import frappe

app_name = "crm"
app_title = "Astra CRM"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Astra CRM — sales workspace for Astra Connect teams"
app_email = "shariq@frappe.io"
app_license = "AGPLv3"
app_icon_url = "/assets/crm/images/astra-crm-logo.png"
app_icon_title = "Astra CRM"
app_icon_route = "/crm"
app_logo_url = "/assets/crm/images/astra-crm-logo.png"

# Apps
# ------------------

required_apps = ["whatsapp"]
add_to_apps_screen = [
	{
		"name": "crm",
		"logo": "/assets/crm/images/astra-crm-logo.png",
		"title": "Astra CRM",
		"route": "/crm",
		"has_permission": "crm.api.check_app_permission",
	}
]

# Login / website chrome for Astra branding (card follows light/dark theme)
web_include_css = ["/assets/crm/css/astra-login.css"]
website_context = {
	"splash_image": "/assets/crm/images/astra-crm-logo.png",
	"brand_html": "Astra CRM",
	"app_name": "Astra CRM",
	"footer_address": "",
	"copyright": "",
	# Space (truthy) skips the framework footer_powered.html include; CRM also
	# ships empty/override footer templates so no vendor text is in the HTML.
	"footer_powered": " ",
	"show_footer_on_login": 0,
}

update_website_context = ["crm.overrides.branding.update_website_context"]

get_site_info = "crm.activation.get_site_info"

export_python_type_annotations = True
require_type_annotated_api_methods = True

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/crm/css/crm.css"
# app_include_js = "/assets/crm/js/crm.js"

# include js, css files in header of web template
# web_include_css = "/assets/crm/css/crm.css"
# web_include_js = "/assets/crm/js/crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Quotation": "public/js/erpnext_quotation_prefill.js",
	"Sales Order": "public/js/erpnext_sales_order_customer.js",
	"CRM Lead": "public/js/domain_enrichment.js",
	"CRM Organization": "public/js/domain_enrichment.js",
	"CRM Deal": "public/js/domain_enrichment.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# Sales roles land in Astra CRM, not the Desk /app workspace.
role_home_page = {
	"Sales User": "crm",
	"Sales Manager": "crm",
}

website_route_rules = [
	{"from_route": "/crm/<path:app_path>", "to_route": "crm"},
	{"from_route": "/crm-form/<route>", "to_route": "crm_form"},
]

# Root favicon / PWA manifest — avoid 404 on bare /favicon.ico and /manifest.json
website_redirects = [
	{"source": "/favicon.ico", "target": "/assets/crm/images/favicon-32.png", "redirect_http_status": 301},
	{
		"source": "/manifest.json",
		"target": "/assets/crm/manifest/manifest.webmanifest",
		"redirect_http_status": 301,
	},
]

# before_request redirect for sales users hitting /app (Desk)
before_request = ["crm.overrides.desk.redirect_sales_users_from_desk"]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "crm.utils.jinja_methods",
# "filters": "crm.utils.jinja_filters"
# }

# Setup wizard
# setup_wizard_requires = "assets/crm/js/setup_wizard.js"
# setup_wizard_stages = "crm.setup.setup_wizard.setup_wizard.get_setup_stages"
# setup_wizard_test = "crm.setup.setup_wizard.test_setup_wizard.run_setup_wizard_test"

# Installation
# ------------

before_install = "crm.install.before_install"
after_install = [
	"crm.install.after_install",
	"frappe.search.sqlite_search.build_index_in_background",
]

# Uninstallation
# ------------

before_uninstall = "crm.uninstall.before_uninstall"
# after_uninstall = "crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "crm.utils.before_app_install"
# after_app_install = "crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "crm.utils.before_app_uninstall"
# after_app_uninstall = "crm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"CRM Lead": "crm.permissions.org_hierarchy.get_lead_permission_query_conditions",
	"CRM Deal": "crm.permissions.org_hierarchy.get_deal_permission_query_conditions",
	"Contact": "crm.permissions.org_hierarchy.get_contact_permission_query_conditions",
	"CRM Call Log": "crm.permissions.org_hierarchy.get_call_log_permission_query_conditions",
	"FCRM Note": "crm.permissions.org_hierarchy.get_note_permission_query_conditions",
	"CRM Task": "crm.permissions.org_hierarchy.get_task_permission_query_conditions",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.get_permission_query_conditions",
	"CRM Enrichment Run": "crm.domain_enrichment.doctype.crm_enrichment_run.crm_enrichment_run.get_permission_query_conditions",
	"CRM View Settings": "crm.fcrm.doctype.crm_view_settings.crm_view_settings.get_permission_query_conditions",
}

has_permission = {
	"CRM Lead": "crm.permissions.org_hierarchy.has_lead_permission",
	"CRM Deal": "crm.permissions.org_hierarchy.has_deal_permission",
	"Contact": "crm.permissions.org_hierarchy.has_contact_permission",
	"CRM Call Log": "crm.permissions.org_hierarchy.has_call_log_permission",
	"FCRM Note": "crm.permissions.org_hierarchy.has_note_permission",
	"CRM Task": "crm.permissions.org_hierarchy.has_task_permission",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.has_permission",
	"CRM Enrichment Run": "crm.domain_enrichment.doctype.crm_enrichment_run.crm_enrichment_run.has_permission",
	"CRM View Settings": "crm.fcrm.doctype.crm_view_settings.crm_view_settings.has_permission",
}

# Automation Engine
# ---------------
# CRM relationships, actions and events available to Automation Flows

automation_relationships = ["crm.automation.relationships.CRMRelationshipProvider"]

automation_actions = [
	"crm.automation.actions.AdjustLeadScore",
	"crm.automation.actions.SetLeadTemperature",
	"crm.automation.actions.ConvertLeadToDeal",
	"crm.automation.actions.SendEmailToRecord",
	"crm.automation.actions.SendCRMNotification",
]

# Correlation options are the keys `crm.automation.events` actually emits, offered to the
# builder so waiting on an event never means hand-writing a Jinja expression.
MESSAGE_CORRELATIONS = [
	{"label": "This email thread", "value": "{{ doc.message_id or doc.name }}"},
	{
		"label": "This lead or deal",
		"value": "{{ doc.reference_doctype }}:{{ doc.reference_name }}",
	},
]
RECORD_CORRELATION = [{"label": "This record", "value": "{{ doc.name }}"}]

# `subject` names the record an event is about, so a flow triggers on that record rather than
# on whatever document the emitter held. Either a fixed doctype with the payload key holding
# its name, or the payload keys for a reference that may be a Lead or a Deal.
REFERENCE_SUBJECT = {
	"doctype_key": "reference_doctype",
	"name_key": "reference_name",
	"doctypes": ["CRM Lead", "CRM Deal"],
}
LEAD_SUBJECT = {"doctype": "CRM Lead", "name_key": "lead"}
DEAL_SUBJECT = {"doctype": "CRM Deal", "name_key": "deal"}

automation_events = [
	{
		"crm.prospect_message_sent": {
			"label": "We emailed the prospect",
			"subject": REFERENCE_SUBJECT,
			"correlation_options": MESSAGE_CORRELATIONS,
		},
		"crm.prospect_message_received": {
			"label": "The prospect replied",
			"subject": REFERENCE_SUBJECT,
			"correlation_options": MESSAGE_CORRELATIONS,
		},
		"crm.lead_qualified": {"label": "Lead was qualified", "subject": LEAD_SUBJECT},
		"crm.lead_converted": {
			"label": "Lead became a deal",
			"subject": LEAD_SUBJECT,
			"correlation_options": RECORD_CORRELATION,
		},
		"crm.deal_stage_changed": {
			"label": "Deal changed stage",
			"subject": DEAL_SUBJECT,
			"correlation_options": RECORD_CORRELATION,
		},
		"crm.deal_won": {
			"label": "Deal was won",
			"subject": DEAL_SUBJECT,
			"correlation_options": RECORD_CORRELATION,
		},
		"crm.deal_lost": {
			"label": "Deal was lost",
			"subject": DEAL_SUBJECT,
			"correlation_options": RECORD_CORRELATION,
		},
		"crm.task_overdue": {
			"label": "Task went overdue",
			"subject": REFERENCE_SUBJECT,
			"correlation_options": RECORD_CORRELATION,
		},
	}
]

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Contact": "crm.overrides.contact.CustomContact",
	"Email Template": "crm.overrides.email_template.CustomEmailTemplate",
}

# Mixins stack with other apps' overrides, e.g. Helpdesk's Assignment Rule
extend_doctype_class = {
	"Data Import": ["crm.overrides.data_import.DataImportListView"],
	"Assignment Rule": ["crm.overrides.assignment_rule.CRMAssignmentRule"],
}

# Frappe v15, still supported on main-hotfix, has no extend_doctype_class
if int(frappe.__version__.split(".")[0]) < 16:
	override_doctype_class["Data Import"] = "crm.overrides.data_import.DataImportV15"

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Contact": {
		"validate": ["crm.api.contact.validate"],
		"after_insert": [
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_contact_insert",
		],
		"on_update": [
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_contact_update",
		],
	},
	"CRM Organization": {
		"validate": ["crm.install_india.validate_organization_tax_fields"],
	},
	"Notification Log": {
		"before_insert": ["crm.extends.notification_log.before_insert"],
	},
	"ToDo": {
		"validate": ["crm.api.todo.validate"],
		"after_insert": ["crm.api.todo.after_insert"],
		"on_update": ["crm.api.todo.on_update"],
	},
	"Communication": {
		"after_insert": [
			"crm.utils.on_communication_insert",
			"crm.automation.events.on_communication",
		],
		"on_update": ["crm.utils.on_communication_update"],
	},
	"Comment": {
		"after_insert": ["crm.utils.on_comment_insert"],
		"on_update": ["crm.api.comment.on_update"],
	},
	"WA Message": {
		"validate": ["crm.api.whatsapp.validate"],
		"on_submit": ["crm.api.whatsapp.update_reference_modified"],
		"on_update": [
			"crm.api.whatsapp.notify_agent",
			"crm.automation.events.on_whatsapp_message",
		],
	},
	"CRM Deal": {
		"after_insert": [
			# Do not assign here — only sync owner after Assignment Rule / for Guest.
			"crm.permissions.org_hierarchy.apply_default_record_owner",
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_deal_insert",
		],
		"on_update": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.create_customer_in_erpnext",
			"crm.automation.events.on_deal_update",
			"crm.integrations.astra_connect.outbound.on_deal_update",
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_deal_update",
			# After Frappe Assignment Rule on_update: copy ToDo assignee → deal_owner.
			"crm.permissions.org_hierarchy.apply_default_record_owner",
		],
	},
	"CRM Lead": {
		"after_insert": [
			"crm.permissions.org_hierarchy.apply_default_record_owner",
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_lead_insert",
		],
		"on_update": [
			"crm.automation.events.on_lead_update",
			"crm.integrations.astra_connect.outbound.on_lead_update",
			"crm.fcrm.doctype.crm_outbound_webhook.crm_outbound_webhook.on_lead_update",
			"crm.permissions.org_hierarchy.apply_default_record_owner",
		],
	},
	"Sales Order": {
		"before_validate": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.create_customer_on_sales_order"
		],
	},
	"Quotation": {
		"after_insert": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.notify_deal_quotation_change"
		],
		"on_update": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.notify_deal_quotation_change"
		],
		"on_trash": [
			"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.notify_deal_quotation_change"
		],
	},
	"Item": {
		"after_insert": ["crm.integrations.erpnext.item.after_insert"],
		"on_update": ["crm.integrations.erpnext.item.on_update"],
		"before_rename": ["crm.integrations.erpnext.item.before_rename"],
		"after_rename": ["crm.integrations.erpnext.item.after_rename"],
		"on_trash": ["crm.integrations.erpnext.item.on_trash"],
	},
	"User Permission": {
		"before_validate": ["crm.integrations.erpnext.user_permission.before_validate"],
		"after_insert": ["crm.integrations.erpnext.user_permission.after_insert"],
		"on_update": ["crm.integrations.erpnext.user_permission.on_update"],
		"on_trash": ["crm.integrations.erpnext.user_permission.on_trash"],
	},
	"DocShare": {
		"before_validate": ["crm.integrations.erpnext.doc_share.before_validate"],
		"after_insert": ["crm.integrations.erpnext.doc_share.after_insert"],
		"on_update": ["crm.integrations.erpnext.doc_share.on_update"],
		"on_trash": ["crm.integrations.erpnext.doc_share.on_trash"],
	},
	"User": {
		"before_validate": ["crm.api.live_demo.validate_user"],
		"validate": ["crm.api.availability.validate_user"],
		"on_update": ["crm.api.availability.on_user_update"],
		"validate_reset_password": ["crm.api.live_demo.validate_reset_password"],
	},
}

# The whatsapp app has no role model of its own; this gates its whitelisted
# endpoints on CRM's sales roles.
whatsapp_access_guard = ["crm.api.whatsapp.validate_access"]

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": ["crm.api.event.trigger_offset_event_notifications"],
	"hourly": [
		"crm.api.event.trigger_hourly_event_notifications",
		"crm.automation.events.emit_overdue_tasks",
	],
	"daily": [
		"crm.api.event.trigger_daily_event_notifications",
		"crm.fcrm.doctype.crm_invitation.crm_invitation.expire_invitations",
		"crm.fcrm.doctype.crm_view_settings.crm_view_settings.clear_old_versions",
		"crm.telemetry.capture_feature_state",
	],
	"weekly": ["crm.api.event.trigger_weekly_event_notifications"],
	"daily_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_daily"],
	"hourly_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_hourly"],
	"monthly_long": ["crm.lead_syncing.background_sync.sync_leads_from_sources_monthly"],
	"cron": {
		"*/2 * * * *": [
			"crm.integrations.astra_connect.api.sweep_stale_processing",
		],
		"*/5 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_5_minutes"],
		"*/10 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_10_minutes"],
		"*/15 * * * *": ["crm.lead_syncing.background_sync.sync_leads_from_sources_15_minutes"],
	},
}

# Testing
# -------

before_tests = "crm.tests.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "crm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["Failed Lead Sync Log"]

# Request Events
# ----------------
# before_request = ["crm.utils.before_request"]
after_request = ["crm.overrides.response_headers.after_request"]

# Job Events
# ----------
# before_job = ["crm.utils.before_job"]
# after_job = ["crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

auth_hooks = [
	"crm.api.api_key_auth.validate",
]

on_session_creation = ["crm.api.onboarding.complete_setup_for_fc_site"]

after_migrate = [
	"crm.fcrm.doctype.fcrm_settings.fcrm_settings.after_migrate",
	"crm.api.whatsapp.add_roles",
	"crm.domain_enrichment.install.seed_default_rules_and_mappings",
	"crm.install.add_default_scripts",
	"crm.install.add_web_form_custom_fields",
	"crm.install.ensure_contact_sales_permissions",
	"crm.install_india.ensure_india_defaults",
]

sqlite_search = ["crm.search_sqlite.CRMSearch"]

standard_dropdown_items = [
	{
		"name1": "app_selector",
		"label": "Apps",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "settings",
		"label": "Settings",
		"type": "Route",
		"icon": "settings",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "about",
		"label": "About",
		"type": "Route",
		"icon": "info",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "separator",
		"label": "",
		"type": "Separator",
		"is_standard": 1,
	},
	{
		"name1": "logout",
		"label": "Log out",
		"type": "Route",
		"icon": "log-out",
		"route": "#",
		"is_standard": 1,
	},
]
