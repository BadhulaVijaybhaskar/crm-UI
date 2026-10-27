# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AstraConnectEvent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attempts: DF.Int
		error: DF.LongText | None
		event_id: DF.Data
		event_type: DF.Data
		payload: DF.JSON | None
		processed_at: DF.Datetime | None
		status: DF.Literal["Received", "Processed", "Failed", "Duplicate"]
	# end: auto-generated types

	pass
