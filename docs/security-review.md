# CRM security review (CRM-12)
_Generated 2026-10-27. Whitelisted methods under `crm/`._

## Legend
| Status | Meaning |
|---|---|
| pass | Permission or signature check present; guests rate-limited where required |
| session | Login required (no `allow_guest`); relies on DocType / role perms |
| fixed | Addressed in this CRM-12 pass |
| guest-no-rate | Guest endpoint without rate_limit — review |

## Cross-cutting controls
- **Security headers**: `crm.overrides.response_headers.after_request` sets enforcing CSP (`frame-ancestors 'self'`; `unsafe-inline`/`unsafe-eval` retained for Frappe desk), `X-Frame-Options: SAMEORIGIN`, `Permissions-Policy`, and HSTS only on HTTPS. Edge nginx owns `nosniff` + `Referrer-Policy` (see `docs/nginx-security-headers.md`). `*.map` blocked at nginx and scrubbed from `sites/assets`.
- **Webhook site binding**: `astra_connect_webhook_secret` is read from `frappe.conf` (per-site). Frappe resolves the site from the Host header before the method runs, so a secret cannot authorize writes on another site.
- **Sanitisation**: `crm.utils.sanitize` strips scripts from HTML notes/comments and plain-text webhook strings. Applied on `FCRM Note.validate`, `crm.api.comment.add_comment`, and Astra Connect `receive`.
- **Nginx**: see `docs/nginx-security-headers.md` (snippet only — not applied by this change).

## Whitelist inventory
| Module | Method | Access | Status | Rate limit | Explicit perm/auth |
|---|---|---|---|---|---|
| `crm/api/__init__.py` | `accept_invitation` | guest | pass | yes | yes |
| `crm/api/__init__.py` | `delete_attachment` | auth | pass | no | yes |
| `crm/api/__init__.py` | `get_file_uploader_defaults` | auth | session | no | no |
| `crm/api/__init__.py` | `get_translations` | guest | fixed | yes | yes |
| `crm/api/__init__.py` | `get_unsubscribed_emails` | auth | pass | no | yes |
| `crm/api/__init__.py` | `get_user_signature` | auth | pass | yes | yes |
| `crm/api/__init__.py` | `invite_by_email` | auth | pass | no | yes |
| `crm/api/activities.py` | `get_activities` | auth | pass | no | yes |
| `crm/api/activities.py` | `get_activity_feed` | auth | pass | no | yes |
| `crm/api/activities.py` | `get_my_day` | auth | pass | no | yes |
| `crm/api/assignment_rule.py` | `duplicate_assignment_rule` | auth | session | no | no |
| `crm/api/assignment_rule.py` | `get_assignment_rules_list` | auth | session | no | no |
| `crm/api/auth.py` | `oauth_providers` | guest | fixed | yes | no |
| `crm/api/command_palette.py` | `search` | auth | pass | no | yes |
| `crm/api/comment.py` | `add_comment` | auth | fixed | no | yes |
| `crm/api/contact.py` | `create_new` | auth | pass | no | yes |
| `crm/api/contact.py` | `get_linked_deals` | auth | pass | no | yes |
| `crm/api/contact.py` | `search_emails` | auth | session | no | no |
| `crm/api/contact.py` | `set_as_primary` | auth | pass | no | yes |
| `crm/api/csv_import.py` | `download_import_errors` | auth | pass | no | yes |
| `crm/api/csv_import.py` | `get_import_result` | auth | pass | no | yes |
| `crm/api/csv_import.py` | `start_csv_import` | auth | pass | no | yes |
| `crm/api/csv_io.py` | `download_template` | auth | pass | no | yes |
| `crm/api/csv_io.py` | `export_csv` | auth | pass | no | yes |
| `crm/api/dashboard.py` | `get_chart` | auth | pass | no | yes |
| `crm/api/dashboard.py` | `get_chart_options` | auth | session | no | no |
| `crm/api/dashboard.py` | `get_dashboard` | auth | pass | no | yes |
| `crm/api/dashboard.py` | `reset_to_default` | auth | pass | no | yes |
| `crm/api/dedupe.py` | `find_duplicates` | auth | pass | no | yes |
| `crm/api/doc.py` | `add_seen` | auth | pass | no | yes |
| `crm/api/doc.py` | `delete_bulk_docs` | auth | session | no | no |
| `crm/api/doc.py` | `get_assigned_users` | auth | pass | no | yes |
| `crm/api/doc.py` | `get_data` | auth | pass | no | yes |
| `crm/api/doc.py` | `get_fields` | auth | pass | no | yes |
| `crm/api/doc.py` | `get_filterable_fields` | auth | session | no | no |
| `crm/api/doc.py` | `get_group_by_fields` | auth | session | no | no |
| `crm/api/doc.py` | `get_linked_docs_of_document` | auth | pass | no | yes |
| `crm/api/doc.py` | `get_quick_filters` | auth | session | no | no |
| `crm/api/doc.py` | `remove_assignments` | auth | pass | no | yes |
| `crm/api/doc.py` | `remove_linked_doc_reference` | auth | pass | no | yes |
| `crm/api/doc.py` | `sort_options` | auth | session | no | no |
| `crm/api/doc.py` | `update_quick_filters` | auth | session | no | no |
| `crm/api/exchange_rate.py` | `get_exchange_rate` | auth | session | no | no |
| `crm/api/form.py` | `delete_form` | auth | session | no | no |
| `crm/api/form.py` | `get_form_config` | auth | session | no | no |
| `crm/api/form.py` | `get_form_fields` | auth | session | no | no |
| `crm/api/form.py` | `get_hidden_seed` | auth | session | no | no |
| `crm/api/form.py` | `grant_guest_link_access` | auth | session | no | no |
| `crm/api/form.py` | `link_field_guest_access` | auth | session | no | no |
| `crm/api/form.py` | `list_forms` | auth | session | no | no |
| `crm/api/form.py` | `save_form` | auth | session | no | no |
| `crm/api/form.py` | `set_published` | auth | session | no | no |
| `crm/api/form.py` | `test_submit_form` | auth | session | no | no |
| `crm/api/live_demo.py` | `login` | guest | fixed | yes | yes |
| `crm/api/notifications.py` | `get_notifications` | auth | pass | no | yes |
| `crm/api/notifications.py` | `get_unread_count` | auth | pass | no | yes |
| `crm/api/notifications.py` | `mark_as_read` | auth | pass | no | yes |
| `crm/api/onboarding.py` | `get_first_deal` | auth | session | no | no |
| `crm/api/onboarding.py` | `get_first_lead` | auth | session | no | no |
| `crm/api/session.py` | `get_organizations` | auth | session | no | no |
| `crm/api/session.py` | `get_user_info` | auth | session | no | no |
| `crm/api/session.py` | `get_users` | auth | pass | no | yes |
| `crm/api/settings.py` | `create_email_account` | auth | session | no | no |
| `crm/api/user.py` | `add_existing_users` | auth | pass | no | yes |
| `crm/api/user.py` | `change_password` | auth | pass | yes | yes |
| `crm/api/user.py` | `remove_crm_roles_from_user` | auth | pass | no | yes |
| `crm/api/user.py` | `update_user_role` | auth | pass | no | yes |
| `crm/api/views.py` | `get_views` | auth | pass | no | yes |
| `crm/api/whatsapp.py` | `get_account_usage` | auth | session | no | no |
| `crm/api/whatsapp.py` | `is_whatsapp_enabled` | auth | session | no | no |
| `crm/api/whatsapp.py` | `is_whatsapp_installed` | auth | session | no | no |
| `crm/demo/api.py` | `clear_demo_data` | auth | pass | no | yes |
| `crm/demo/api.py` | `get_demo_state` | auth | session | no | no |
| `crm/domain_enrichment/api.py` | `enrich` | auth | pass | yes | yes |
| `crm/domain_enrichment/api.py` | `get_enriched_fields` | auth | pass | no | yes |
| `crm/domain_enrichment/api.py` | `get_status` | auth | pass | no | yes |
| `crm/domain_enrichment/api.py` | `retry` | auth | pass | yes | yes |
| `crm/domain_enrichment/api.py` | `undo` | auth | pass | yes | yes |
| `crm/fcrm/doctype/crm_call_log/crm_call_log.py` | `create_lead_from_call_log` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_call_log/crm_call_log.py` | `get_call_log` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_deal/api.py` | `get_deal_contacts` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `add_contact` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `create_deal` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `remove_contact` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` | `set_primary_contact` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py` | `get_fields_layout` | auth | session | no | no |
| `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py` | `get_sidepanel_sections` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py` | `save_fields_layout` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_lead/crm_lead.py` | `convert_to_deal` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_products/crm_products.py` | `get_product_rate_details` | auth | session | no | no |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `create` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `create_or_update_standard_view` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `delete` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `fetch_and_update_kanban_columns` | auth | session | no | no |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `pin` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `public` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `set_as_default` | auth | pass | no | yes |
| `crm/fcrm/doctype/crm_view_settings/crm_view_settings.py` | `update` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `can_create_quotations` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `can_view_quotations` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `check_customer_for_quotation` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `dismiss_sync_issue` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_crm_form_script` | auth | session | no | no |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_customer_link` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_deal_quotations` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_open_sync_issues` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_product_sync_status` | auth | pass | no | yes |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `get_quotation_url` | auth | session | no | no |
| `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py` | `prefill_quotation_items` | auth | session | no | no |
| `crm/fcrm/doctype/fcrm_note/fcrm_note.py` | `set_pinned` | auth | pass | no | yes |
| `crm/integrations/api.py` | `add_note_to_call_log` | auth | pass | no | yes |
| `crm/integrations/api.py` | `add_task_to_call_log` | auth | pass | no | yes |
| `crm/integrations/api.py` | `get_contact_by_phone_number` | auth | pass | no | yes |
| `crm/integrations/api.py` | `get_contact_lead_or_deal_from_number` | auth | pass | no | yes |
| `crm/integrations/api.py` | `get_recording_url` | auth | pass | no | yes |
| `crm/integrations/api.py` | `is_call_integration_enabled` | auth | pass | no | yes |
| `crm/integrations/api.py` | `set_default_calling_medium` | auth | pass | no | yes |
| `crm/integrations/astra_connect/api.py` | `receive` | guest | fixed | yes | yes |
| `crm/integrations/astra_connect/api.py` | `retry_event` | auth | pass | no | yes |
| `crm/integrations/exotel/handler.py` | `handle_request` | guest | guest-no-rate | no | yes |
| `crm/integrations/exotel/handler.py` | `is_integration_enabled` | auth | session | no | no |
| `crm/integrations/exotel/handler.py` | `make_a_call` | auth | pass | no | yes |
| `crm/integrations/twilio/api.py` | `generate_access_token` | auth | pass | no | yes |
| `crm/integrations/twilio/api.py` | `is_enabled` | auth | pass | no | yes |
| `crm/integrations/twilio/api.py` | `update_call_status_info` | guest | guest-ok | no | no |
| `crm/integrations/twilio/api.py` | `update_recording_info` | guest | guest-ok | no | no |
| `crm/lead_syncing/doctype/lead_sync_source/facebook.py` | `fetch_and_store_pages_from_facebook` | auth | session | no | no |
| `crm/lead_syncing/doctype/lead_sync_source/facebook.py` | `get_pages_with_forms` | auth | session | no | no |
| `crm/www/crm.py` | `get_context_for_dev` | guest | guest-no-rate | no | yes |
