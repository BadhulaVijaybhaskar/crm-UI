# Astra Connect Webhooks (DRAFT)

> **Status: DRAFT** — contract for CRM-04 inbound events from Astra Connect into Astra CRM.
> Do not treat this as a frozen public API until this notice is removed.

## Endpoint

```
POST /api/method/crm.integrations.astra_connect.api.receive
```

- Guest-accessible (signed).
- Content-Type: `application/json`
- Disabled when site config key `astra_connect_webhook_secret` is missing (HTTP 503).

## Headers

| Header | Description |
|---|---|
| `X-Astra-Event-Id` | Unique event id (idempotency key) |
| `X-Astra-Timestamp` | Unix seconds (UTC) |
| `X-Astra-Signature` | Hex HMAC-SHA256 of `` `${timestamp}.${raw_body}` `` using the site secret |

Reject (HTTP 401) when the signature is wrong, or the timestamp is more than **300 seconds** off. Signature comparison is constant-time (`hmac.compare_digest`).

## Site configuration

```json
{
  "astra_connect_webhook_secret": "<per-site shared secret>"
}
```

Optional Desk settings (Single DocType **Astra Connect Settings**):

- `enabled`
- `connect_base_url` — used for sidebar / Call with AI / Message with AI entry points (public; no credentials)
- `default_lead_owner`

The webhook signing secret is **never** exposed to the frontend.

## Events

### `lead.upsert`

Creates or updates a **CRM Lead** by `astra_external_id`, else by phone.

```json
{
  "type": "lead.upsert",
  "data": {
    "external_id": "lead_123",
    "name": "Ada Lovelace",
    "phone": "+14155550100",
    "email": "ada@example.com",
    "company": "Analytical Engines",
    "source": "Astra Connect",
    "ai_employee_id": "emp_9",
    "campaign_id": "camp_1"
  }
}
```

### `call.outcome`

Creates a **CRM Call Log** (`telephony_medium` = `Astra Connect`) with disposition, summary, AI employee, optional transcript/recording URLs. Links to the matching Lead / Deal / Contact (phone first, then email). Adds an **FCRM Note** for the summary and a **CRM Task** when `next_action` is present. Unmatched outcomes are stored as **Failed** on **Astra Connect Event** and can be retried by a System Manager via `crm.integrations.astra_connect.api.retry_event`.

```json
{
  "type": "call.outcome",
  "data": {
    "call_id": "call_100",
    "lead_external_id": "lead_123",
    "phone": "+14155550100",
    "direction": "outbound",
    "started_at": "2026-10-27T10:00:00Z",
    "duration_s": 95,
    "status": "completed",
    "disposition": "interested",
    "summary": "Prospect asked for a demo.",
    "transcript_url": "https://connect.example/t/100",
    "recording_url": "https://connect.example/r/100",
    "ai_employee_id": "emp_9",
    "next_action": {
      "title": "Send demo invite",
      "due_at": "2026-10-28T15:00:00Z"
    }
  }
}
```

## Idempotency

A repeated `X-Astra-Event-Id` returns HTTP 200 with `"status": "duplicate"` and creates no new CRM records.

## Responses

| status | HTTP | Meaning |
|---|---|---|
| `processed` | 200 | Event applied |
| `duplicate` | 200 | Event id already seen |
| `failed` | 422 | Business processing failed (retryable) |
| `rejected` | 401 / 400 | Auth or payload rejected |
| `disabled` | 503 | Secret not configured |

## Signing example (Python)

```python
import hashlib, hmac, json, time, urllib.request

SECRET = "your-site-secret"
url = "https://crm.example/api/method/crm.integrations.astra_connect.api.receive"
payload = {
    "type": "lead.upsert",
    "data": {
        "external_id": "lead_123",
        "name": "Ada Lovelace",
        "phone": "+14155550100",
        "email": "ada@example.com",
    },
}
body = json.dumps(payload, separators=(",", ":"))
ts = str(int(time.time()))
sig = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
req = urllib.request.Request(
    url,
    data=body.encode(),
    headers={
        "Content-Type": "application/json",
        "X-Astra-Event-Id": "evt_demo_1",
        "X-Astra-Timestamp": ts,
        "X-Astra-Signature": sig,
    },
    method="POST",
)
print(urllib.request.urlopen(req).read().decode())
```

## Signing example (curl)

```bash
SECRET='your-site-secret'
BODY='{"type":"lead.upsert","data":{"external_id":"lead_123","name":"Ada Lovelace","phone":"+14155550100"}}'
TS=$(date +%s)
SIG=$(printf '%s' "${TS}.${BODY}" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')
EVENT_ID="evt_demo_1"

curl -sS -X POST \
  'https://crm.example/api/method/crm.integrations.astra_connect.api.receive' \
  -H 'Content-Type: application/json' \
  -H "X-Astra-Event-Id: ${EVENT_ID}" \
  -H "X-Astra-Timestamp: ${TS}" \
  -H "X-Astra-Signature: ${SIG}" \
  --data-binary "${BODY}"
```

## Audit log

Every accepted delivery is stored as **Astra Connect Event** (`event_id`, `type`, `payload`, `status`, `error`, `attempts`, `processed_at`).
