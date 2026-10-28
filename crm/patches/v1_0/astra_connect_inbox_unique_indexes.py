"""Dedupe Connect inbox / note rows, then ensure unique indexes for the redesign.

Indexes:
  - ``tabAstra Connect Event.event_id`` (delivery id) — unique
  - ``tabFCRM Note.astra_call_id`` — unique (NULLs allowed for non-Connect notes)
  - CRM Call Log.id / name already unique via autoname field:id

Safe to re-run.
"""

from __future__ import annotations

import frappe


def execute():
	_dedupe_connect_events()
	_ensure_unique_index("tabAstra Connect Event", "event_id", "unique_event_id")

	_backfill_and_dedupe_notes()
	if frappe.db.has_column("FCRM Note", "astra_call_id"):
		_ensure_unique_index("tabFCRM Note", "astra_call_id", "unique_astra_call_id")

	_ensure_call_log_id_unique()


def _table_exists(table: str) -> bool:
	return bool(frappe.db.sql("SHOW TABLES LIKE %s", (table,)))


def _dedupe_connect_events() -> None:
	if not _table_exists("tabAstra Connect Event"):
		return
	if not frappe.db.has_column("Astra Connect Event", "event_id"):
		return

	dupes = frappe.db.sql(
		"""
		SELECT event_id, COUNT(*) AS n
		FROM `tabAstra Connect Event`
		WHERE event_id IS NOT NULL AND event_id != ''
		GROUP BY event_id
		HAVING n > 1
		"""
	)
	for event_id, _n in dupes:
		rows = frappe.db.sql(
			"""
			SELECT name, status, modified
			FROM `tabAstra Connect Event`
			WHERE event_id = %s
			ORDER BY
				CASE status
					WHEN 'Processed' THEN 0
					WHEN 'Processing' THEN 1
					WHEN 'Received' THEN 2
					WHEN 'Failed' THEN 3
					ELSE 4
				END,
				modified DESC
			""",
			(event_id,),
			as_dict=True,
		)
		for row in rows[1:]:
			frappe.delete_doc("Astra Connect Event", row.name, force=True, ignore_permissions=True)


def _backfill_and_dedupe_notes() -> None:
	if not _table_exists("tabFCRM Note"):
		return
	if not frappe.db.has_column("FCRM Note", "astra_call_id"):
		return

	# Backfill from CRM Call Log.note → call log name/id.
	if _table_exists("tabCRM Call Log") and frappe.db.has_column("CRM Call Log", "note"):
		frappe.db.sql(
			"""
			UPDATE `tabFCRM Note` n
			INNER JOIN `tabCRM Call Log` c ON c.note = n.name
			SET n.astra_call_id = c.name
			WHERE (n.astra_call_id IS NULL OR n.astra_call_id = '')
			  AND c.name IS NOT NULL AND c.name != ''
			"""
		)

	# Title pattern used by Connect: "Call summary (<callId>)"
	frappe.db.sql(
		"""
		UPDATE `tabFCRM Note`
		SET astra_call_id = TRIM(BOTH ')' FROM SUBSTRING_INDEX(title, '(', -1))
		WHERE (astra_call_id IS NULL OR astra_call_id = '')
		  AND title LIKE '%%(%%)'
		  AND title LIKE 'Call summary (%%'
		"""
	)

	dupes = frappe.db.sql(
		"""
		SELECT astra_call_id, COUNT(*) AS n
		FROM `tabFCRM Note`
		WHERE astra_call_id IS NOT NULL AND astra_call_id != ''
		GROUP BY astra_call_id
		HAVING n > 1
		"""
	)
	for call_id, _n in dupes:
		rows = frappe.get_all(
			"FCRM Note",
			filters={"astra_call_id": call_id},
			fields=["name", "modified"],
			order_by="modified desc",
		)
		keep = rows[0].name
		for row in rows[1:]:
			if _table_exists("tabCRM Call Log"):
				frappe.db.sql(
					"""
					UPDATE `tabCRM Call Log`
					SET note = %s
					WHERE note = %s
					""",
					(keep, row.name),
				)
			frappe.delete_doc("FCRM Note", row.name, force=True, ignore_permissions=True)


def _ensure_call_log_id_unique() -> None:
	if not _table_exists("tabCRM Call Log"):
		return
	if not frappe.db.has_column("CRM Call Log", "id"):
		return
	_ensure_unique_index("tabCRM Call Log", "id", "unique_id")


def _ensure_unique_index(table: str, column: str, index_name: str) -> None:
	if not _table_exists(table):
		return

	indexes = frappe.db.sql(
		f"SHOW INDEX FROM `{table}` WHERE Column_name = %s",
		(column,),
		as_dict=True,
	)
	for idx in indexes or []:
		if int(idx.get("Non_unique", 1) or 1) == 0:
			return

	try:
		frappe.db.sql_ddl(f"ALTER TABLE `{table}` DROP INDEX `{index_name}`")
	except Exception:
		pass
	try:
		frappe.db.sql_ddl(f"ALTER TABLE `{table}` ADD UNIQUE INDEX `{index_name}` (`{column}`)")
	except Exception as exc:
		frappe.log_error(
			title=f"Astra Connect unique index {table}.{column}",
			message=str(exc),
		)
