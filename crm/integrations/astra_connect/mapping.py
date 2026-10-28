"""Small mapping tables between Connect payloads and CRM values."""

from __future__ import annotations

# Connect lead.status → CRM Lead Status name. Fallback used when unknown / missing.
LEAD_STATUS_MAP = {
	"new": "New",
	"assigned": "Nurture",
	"calling": "Contacted",
	"called": "Contacted",
	"failed": "Unqualified",
	"qualified": "Qualified",
	"closed": "Converted",
}
DEFAULT_LEAD_STATUS = "New"

# Known Connect outcome strings → CRM disposition label. Unknown → default.
# Outcome itself is always stored as free text (never hard-validated).
OUTCOME_DISPOSITION_MAP = {
	"appointment_booked": "Appointment Booked",
	"interested": "Interested",
	"not_interested": "Not Interested",
	"callback": "Callback",
	"no_answer": "No Answer",
	"voicemail": "Voicemail",
	"wrong_number": "Wrong Number",
	"do_not_call": "Do Not Call",
	"qualified": "Qualified",
	"unqualified": "Unqualified",
}
DEFAULT_DISPOSITION = "Other"

OUTCOME_MAX_LEN = 64


def map_lead_status(connect_status: str | None) -> str:
	key = (connect_status or "").strip().lower()
	return LEAD_STATUS_MAP.get(key, DEFAULT_LEAD_STATUS)


def store_outcome(raw: str | None) -> str:
	"""Return outcome free text truncated to OUTCOME_MAX_LEN (never reject)."""
	text = (raw or "").strip()
	if len(text) > OUTCOME_MAX_LEN:
		return text[:OUTCOME_MAX_LEN]
	return text


def map_disposition(outcome: str | None) -> str:
	key = (outcome or "").strip().lower()
	return OUTCOME_DISPOSITION_MAP.get(key, DEFAULT_DISPOSITION)
