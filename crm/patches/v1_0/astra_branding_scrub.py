"""Persist Astra white-label settings: login/email chrome, workspace rename, labels."""

from crm.overrides.branding import (
	apply_doctype_label_overrides,
	relabel_crm_workspace,
	scrub_site_branding,
)


def execute():
	scrub_site_branding()
	relabel_crm_workspace()
	apply_doctype_label_overrides()
