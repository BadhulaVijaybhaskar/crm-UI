# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

"""Login page controller — re-exports framework get_context and injects Astra logo.

crm/www/login.html extends the framework login template; without this module the
Jinja ``{{ logo }}`` (and related) variables are not populated and render literally.
"""

from __future__ import annotations

from frappe.www.login import get_context as _frappe_get_context

from crm.overrides.branding import ASTRA_APP_NAME, ASTRA_LOGO, ASTRA_SPLASH


def get_context(context=None):
	ctx = _frappe_get_context(context)
	# Framework returns the context dict (or mutates the passed-in one).
	if ctx is None:
		ctx = context or {}
	ctx["logo"] = ASTRA_LOGO
	ctx["app_logo"] = ASTRA_LOGO
	ctx["splash_image"] = ctx.get("splash_image") or ASTRA_SPLASH
	ctx["app_name"] = ASTRA_APP_NAME
	ctx["brand_html"] = ASTRA_APP_NAME
	return ctx
