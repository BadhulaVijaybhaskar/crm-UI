# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""CSV helpers shared by export and import — keep free of frappe imports for unit tests."""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Iterable

# Excel / Sheets treat leading = + - @ as formulas. Prefix with a single quote.
_FORMULA_PREFIX = re.compile(r"^[=+\-@]")


def guard_csv_cell(value: Any) -> str:
	"""Return a string safe to write into a CSV cell (formula-injection guarded)."""
	if value is None:
		return ""
	if isinstance(value, bool):
		text = "1" if value else "0"
	elif isinstance(value, (int, float)):
		text = str(value)
	else:
		text = str(value)

	# Preserve newlines as spaces for single-line CSV consumers; keep other text.
	text = text.replace("\r\n", "\n").replace("\r", "\n")
	if _FORMULA_PREFIX.match(text):
		return "'" + text
	return text


def rows_to_csv(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
	"""Build a UTF-8 CSV string with a BOM so Excel opens UTF-8 correctly."""
	buf = io.StringIO()
	writer = csv.writer(buf, lineterminator="\n")
	header_list = [guard_csv_cell(h) for h in headers]
	writer.writerow(header_list)
	for row in rows:
		writer.writerow([guard_csv_cell(cell) for cell in row])
	return "\ufeff" + buf.getvalue()
