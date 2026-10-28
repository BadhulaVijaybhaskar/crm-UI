"""Dedupe Connect inbox / note rows, commit, then add unique indexes if missing.

Order matters: never ADD UNIQUE while duplicate values still exist. DocType JSON
does not mark ``FCRM Note.astra_call_id`` unique so schema sync cannot race this
patch; uniqueness lives here.

Safe / idempotent to re-run.
"""

from __future__ import annotations

import frappe


def execute():
	# 1) Events: dedupe → commit → unique index
	_dedupe_connect_events()
	frappe.db.commit()
	_ensure_unique_index("tabAstra Connect Event", "event_id", "unique_event_id")

	# 2) Notes: backfill → dedupe → commit → unique index
	_backfill_note_astra_call_ids()
	_dedupe_notes_by_astra_call_id()
	frappe.db.commit()
	if frappe.db.has_column("FCRM Note", "astra_call_id"):
		_ensure_unique_index("tabFCRM Note", "astra_call_id", "unique_astra_call_id")

	# 3) Call log id (usually already unique via autoname)
	_ensure_call_log_id_unique()
	frappe.db.commit()


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
			frappe.db.sql("DELETE FROM `tabAstra Connect Event` WHERE name = %s", (row.name,))


def _backfill_note_astra_call_ids() -> None:
	if not _table_exists("tabFCRM Note"):
		return
	if not frappe.db.has_column("FCRM Note", "astra_call_id"):
		return

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


def _dedupe_notes_by_astra_call_id() -> None:
	if not _table_exists("tabFCRM Note"):
		return
	if not frappe.db.has_column("FCRM Note", "astra_call_id"):
		return

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
		rows = frappe.db.sql(
			"""
			SELECT name, modified
			FROM `tabFCRM Note`
			WHERE astra_call_id = %s
			ORDER BY modified DESC
			""",
			(call_id,),
			as_dict=True,
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
			frappe.db.sql("DELETE FROM `tabFCRM Note` WHERE name = %s", (row.name,))


def _ensure_call_log_id_unique() -> None:
	if not _table_exists("tabCRM Call Log"):
		return
	if not frappe.db.has_column("CRM Call Log", "id"):
		return
	_ensure_unique_index("tabCRM Call Log", "id", "unique_id")


def _column_has_unique_index(table: str, column: str) -> bool:
	indexes = frappe.db.sql(
		f"SHOW INDEX FROM `{table}` WHERE Column_name = %s",
		(column,),
		as_dict=True,
	)
	for idx in indexes or []:
		# Non_unique is 0 for UNIQUE indexes. Do NOT use ``x or 1`` — that turns 0 into 1.
		try:
			non_unique = int(idx.get("Non_unique"))
		except (TypeError, ValueError):
			non_unique = 1
		if non_unique == 0:
			return True
	return False


def ensure_indexes() -> None:
	"""Idempotent ensure of Connect unique indexes (after_install / after_migrate)."""
	_ensure_unique_index("tabAstra Connect Event", "event_id", "unique_event_id")
	if frappe.db.has_column("FCRM Note", "astra_call_id"):
		# Dedupe first so fresh/partial installs never 1062.
		_dedupe_notes_by_astra_call_id()
		frappe.db.commit()
		_ensure_unique_index("tabFCRM Note", "astra_call_id", "unique_astra_call_id")
	_ensure_call_log_id_unique()
	frappe.db.commit()


def _ensure_unique_index(table: str, column: str, index_name: str) -> None:
	"""Add UNIQUE INDEX only when the column has no unique index yet. Never recreate."""
	if not _table_exists(table):
		return
	if _column_has_unique_index(table, column):
		return

	try:
		frappe.db.sql_ddl(f"ALTER TABLE `{table}` ADD UNIQUE INDEX `{index_name}` (`{column}`)")
	except Exception as exc:
		msg = str(exc).lower()
		# Already exists under another name, or raced — treat as success if unique now.
		if _column_has_unique_index(table, column):
			return
		if "duplicate key name" in msg or "1061" in msg:
			return
		frappe.log_error(
			title=f"Astra Connect unique index {table}.{column}",
			message=str(exc),
		)
		raise
