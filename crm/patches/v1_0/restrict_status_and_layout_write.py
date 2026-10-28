import frappe


def execute():
	"""Sales User read-only on statuses; Sales Manager read-only on fields layout."""
	_set_role_perms(
		"CRM Lead Status",
		"Sales User",
		{"read": 1, "export": 1, "print": 1, "email": 1, "report": 1, "share": 1},
	)
	_set_role_perms(
		"CRM Deal Status",
		"Sales User",
		{"read": 1, "export": 1, "print": 1, "email": 1, "report": 1, "share": 1},
	)
	_set_role_perms(
		"CRM Fields Layout",
		"Sales Manager",
		{"read": 1, "export": 1, "print": 1, "email": 1, "report": 1, "share": 1},
	)


def _set_role_perms(doctype: str, role: str, flags: dict):
	if not frappe.db.exists("DocType", doctype):
		return
	values = {
		"create": 0,
		"write": 0,
		"delete": 0,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		**flags,
	}
	# Custom DocPerm replaces DocPerm for the whole DocType, so a site that
	# customized permissions keeps Sales User write unless this row is updated too.
	for perm_doctype in ("DocPerm", "Custom DocPerm"):
		name = frappe.db.get_value(perm_doctype, {"parent": doctype, "role": role, "permlevel": 0})
		if name:
			frappe.db.set_value(perm_doctype, name, values)
		elif perm_doctype == "DocPerm":
			doc = frappe.get_doc("DocType", doctype)
			doc.append("permissions", {"role": role, "permlevel": 0, **values})
			doc.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)
