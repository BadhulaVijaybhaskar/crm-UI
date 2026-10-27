# Copyright (c) 2026, Astra and contributors
# For license information, please see license.txt
"""Background CSV import for CRM Lead / Contact with email / E.164 phone dedupe."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils.file_manager import get_file

from crm.utils import normalize_phone
from crm.utils.dedupe import normalize_email
from crm.utils.csv_safe import rows_to_csv

IMPORTABLE = {
	"CRM Lead": {
		"email_field": "email",
		"phone_fields": ("mobile_no", "phone"),
		"required": ("first_name",),
	},
	"Contact": {
		"email_field": "email_id",
		"phone_fields": ("mobile_no", "phone"),
		"required": ("first_name",),
	},
}

ON_DUPLICATE = ("skip", "update", "create")


@frappe.whitelist()
def start_csv_import(
	doctype: str,
	file_url: str,
	field_map: str | dict | None = None,
	on_duplicate: str = "skip",
	dedupe_by: str | list | None = None,
):
	"""Enqueue a CRM CSV import. Returns a job id the UI can poll via get_import_result."""
	if doctype not in IMPORTABLE:
		frappe.throw(_("CSV import is not available for {0}").format(doctype))
	frappe.has_permission(doctype, "create", throw=True)

	on_duplicate = (on_duplicate or "skip").lower()
	if on_duplicate not in ON_DUPLICATE:
		frappe.throw(_("Invalid on_duplicate option"))

	mapping = _parse_json(field_map, {}) or {}
	keys = _parse_json(dedupe_by, ["email", "phone"]) or ["email", "phone"]
	keys = [k for k in keys if k in ("email", "phone")]

	job_id = f"crm-csv-import-{frappe.generate_hash(length=10)}"
	frappe.enqueue(
		"crm.api.csv_import.run_csv_import",
		queue="long",
		timeout=60 * 30,
		job_id=job_id,
		doctype=doctype,
		file_url=file_url,
		field_map=mapping,
		on_duplicate=on_duplicate,
		dedupe_by=keys,
		user=frappe.session.user,
		job_id_arg=job_id,
		now=bool(getattr(frappe.flags, "in_test", False)),
	)
	# Persist a result stub so the UI can poll before the worker finishes.
	frappe.cache().set_value(
		_result_key(job_id),
		{"status": "queued", "job_id": job_id, "doctype": doctype},
	)
	return {"job_id": job_id}


@frappe.whitelist()
def get_import_result(job_id: str):
	"""Poll status / counts / downloadable error CSV for a started import."""
	if not job_id:
		frappe.throw(_("job_id is required"))
	data = frappe.cache().get_value(_result_key(job_id))
	if not data:
		return {"status": "unknown", "job_id": job_id}
	return data


@frappe.whitelist()
def download_import_errors(job_id: str):
	"""Download the row-error report produced by a finished import."""
	data = frappe.cache().get_value(_result_key(job_id)) or {}
	errors = data.get("errors") or []
	if not errors:
		frappe.throw(_("No error report for this import"))
	headers = ["row", "error", "email", "phone", "first_name", "last_name"]
	rows = [[e.get(h, "") for h in headers] for e in errors]
	from crm.api.csv_io import _file_response

	_file_response(f"import_errors_{job_id}.csv", rows_to_csv(headers, rows))


def run_csv_import(
	doctype: str,
	file_url: str,
	field_map: dict | None = None,
	on_duplicate: str = "skip",
	dedupe_by: list | None = None,
	user: str | None = None,
	job_id_arg: str | None = None,
):
	"""Worker entry — import rows with skip / update / create-new on email or phone match."""
	job_id = job_id_arg or (
		getattr(frappe.local, "job", None) and getattr(frappe.local.job, "id", None)
	)
	if user and user != frappe.session.user:
		frappe.set_user(user)

	key = _result_key(job_id or "unknown")
	frappe.cache().set_value(
		key,
		{"status": "running", "job_id": job_id, "doctype": doctype},
	)

	cfg = IMPORTABLE[doctype]
	field_map = field_map or {}
	dedupe_by = dedupe_by or ["email", "phone"]

	try:
		_filename, content = get_file(file_url)
		text = content.decode("utf-8-sig") if isinstance(content, (bytes, bytearray)) else str(content)
		reader = csv.DictReader(io.StringIO(text))
		if not reader.fieldnames:
			raise frappe.ValidationError(_("CSV has no header row"))

		created = updated = skipped = 0
		errors: list[dict[str, Any]] = []

		for idx, raw in enumerate(reader, start=2):  # row 1 = header
			try:
				doc_values = _map_row(raw, field_map, cfg)
				_validate_required(doc_values, cfg)
				existing = _find_existing(doctype, doc_values, cfg, dedupe_by)
				if existing:
					if on_duplicate == "skip":
						skipped += 1
						continue
					if on_duplicate == "update":
						_update_doc(doctype, existing, doc_values)
						updated += 1
						continue
					# create — fall through with a fresh insert
				doc = frappe.get_doc({"doctype": doctype, **doc_values})
				doc.flags.ignore_mandatory = False
				doc.insert(ignore_permissions=False)
				created += 1
			except Exception as exc:
				errors.append(
					{
						"row": idx,
						"error": frappe.get_traceback() if frappe.conf.developer_mode else str(exc),
						"email": raw.get(field_map.get("email") or cfg["email_field"] or "", ""),
						"phone": raw.get(
							field_map.get("mobile_no") or (cfg["phone_fields"][0] if cfg["phone_fields"] else ""),
							"",
						),
						"first_name": raw.get(field_map.get("first_name") or "first_name", ""),
						"last_name": raw.get(field_map.get("last_name") or "last_name", ""),
					}
				)

		result = {
			"status": "done",
			"job_id": job_id,
			"doctype": doctype,
			"created": created,
			"updated": updated,
			"skipped": skipped,
			"error_count": len(errors),
			"errors": errors[:500],
		}
		frappe.cache().set_value(key, result)
		frappe.db.commit()
		return result
	except Exception as exc:
		frappe.cache().set_value(
			key,
			{"status": "failed", "job_id": job_id, "doctype": doctype, "error": str(exc)},
		)
		frappe.db.rollback()
		raise


def _map_row(raw: dict, field_map: dict, cfg: dict) -> dict:
	"""Map CSV columns → DocType fields. field_map values are CSV header names."""
	values: dict[str, Any] = {}
	headers = {k.strip(): v for k, v in raw.items() if k is not None}
	candidates = set(_all_fields(cfg))
	for docfield in candidates:
		csv_key = field_map.get(docfield) or docfield
		if csv_key in headers and headers[csv_key] not in (None, ""):
			val = headers[csv_key]
			values[docfield] = val.strip() if isinstance(val, str) else val
	for header, val in headers.items():
		if header in candidates and header not in values and val not in (None, ""):
			values[header] = val.strip() if isinstance(val, str) else val
	return values


def _all_fields(cfg: dict) -> list[str]:
	fields = ["first_name", "last_name", "organization", "company_name", "status", "source", "designation"]
	if cfg.get("email_field"):
		fields.append(cfg["email_field"])
	fields.extend(cfg.get("phone_fields") or ())
	return list(dict.fromkeys(fields))


def _validate_required(values: dict, cfg: dict):
	for f in cfg.get("required") or ():
		if not values.get(f):
			frappe.throw(_("{0} is required").format(f))


def _find_existing(doctype: str, values: dict, cfg: dict, dedupe_by: list) -> str | None:
	email_f = cfg.get("email_field")
	if "email" in dedupe_by and email_f and values.get(email_f):
		name = frappe.db.get_value(doctype, {email_f: normalize_email(values[email_f])}, "name")
		if not name:
			# try case-insensitive via get_all
			rows = frappe.get_all(doctype, filters={email_f: values[email_f]}, pluck="name", limit=1)
			name = rows[0] if rows else None
		if name:
			return name

	if "phone" in dedupe_by:
		for field in cfg.get("phone_fields") or ():
			raw = values.get(field)
			if not raw:
				continue
			e164 = normalize_phone(raw)
			if not e164:
				continue
			# Exact match first
			name = frappe.db.get_value(doctype, {field: raw}, "name") or frappe.db.get_value(
				doctype, {field: e164}, "name"
			)
			if name:
				return name
			digits = "".join(ch for ch in e164 if ch.isdigit())[-10:]
			if digits:
				for row in frappe.get_all(doctype, filters={field: ["like", f"%{digits}"]}, fields=["name", field], limit=20):
					if normalize_phone(row.get(field)) == e164:
						return row["name"]
	return None


def _update_doc(doctype: str, name: str, values: dict):
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("write")
	for k, v in values.items():
		if k != "name" and v not in (None, ""):
			doc.set(k, v)
	doc.save()


def _result_key(job_id: str) -> str:
	return f"crm:csv_import:{job_id}"


def _parse_json(value, default):
	if value is None or value == "":
		return default
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value)
	except (TypeError, ValueError):
		return default
