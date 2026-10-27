// Copyright (c) 2026, Astra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Astra Connect Event", {
	refresh(frm) {
		if (frm.doc.status === "Failed" && !frm.is_new()) {
			frm.add_custom_button(__("Retry"), () => {
				frappe.call({
					method: "crm.integrations.astra_connect.api.retry_event",
					args: { event_id: frm.doc.event_id },
					freeze: true,
					callback(r) {
						if (!r.exc) {
							frm.reload_doc()
						}
					},
				})
			})
		}
	},
})
