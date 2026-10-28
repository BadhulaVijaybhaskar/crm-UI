import frappe
from frappe.utils import get_url


def get_public_url(path: str | None = None):
	return get_url().split(":8", 1)[0] + path


def get_twilio_webhook_url() -> str:
	"""Absolute URL Twilio signed for this request.

	Behind nginx/TLS, ``frappe.request.url`` is often ``http://host`` without the
	public scheme/port. Prefer X-Forwarded-Proto/Host, then the site ``host_name``
	via ``get_url``, and only then the raw request URL.
	"""
	request = frappe.request
	if not request:
		return ""

	path = request.full_path or request.path or ""
	if path.endswith("?"):
		path = path[:-1]

	headers = request.headers or {}
	proto = headers.get("X-Forwarded-Proto")
	host = headers.get("X-Forwarded-Host") or headers.get("Host")
	if proto and host:
		return f"{proto}://{host}{path}"

	# Configured public base (site host_name / nginx conf)
	base = get_url().rstrip("/")
	if "://" in base:
		return f"{base}{path}"

	return request.url or ""


def merge_dicts(d1: dict, d2: dict):
	"""Merge dicts of dictionaries.
	>>> merge_dicts(
		{'name1': {'age': 20}, 'name2': {'age': 30}},
		{'name1': {'phone': '+xxx'}, 'name2': {'phone': '+yyy'}, 'name3': {'phone': '+zzz'}}
	)
	... {'name1': {'age': 20, 'phone': '+xxx'}, 'name2': {'age': 30, 'phone': '+yyy'}}
	"""
	return {k: {**v, **d2.get(k, {})} for k, v in d1.items()}
