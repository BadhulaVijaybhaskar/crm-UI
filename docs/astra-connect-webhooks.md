# Astra Connect Webhooks (DRAFT)

> **Status: DRAFT** — CRM-side receiver contract aligned with what Connect sends today.
> Do not treat this as a frozen public API until this notice is removed.

## Endpoint

```
POST /api/method/crm.integrations.astra_connect.api.receive
```

- Guest-accessible (signed).
- Content-Type: `application/json`
- Disabled when site config key `astra_connect_webhook_secret` is missing (HTTP **503**, retryable).

## Headers

| Header | Role |
|---|---|
| `X-Astra-Delivery` | **Primary** delivery / dedupe id (Replay reuses it) |
| `X-Astra-Event-Id` | Fallback if Delivery is absent |
| `X-Astra-Timestamp` | Unix seconds — required for `sha256=` signatures |
| `X-Astra-Signature` | See signature formats below |

## Signature formats (both accepted)

Both are HMAC-SHA256 over `` ts + '.' + rawBody ``, ±**300s** skew, constant-time compare (`hmac.compare_digest`).

### A — `sha256=<hex>` + timestamp header (proposed preferred)

```
X-Astra-Timestamp: 1730000000
X-Astra-Signature: sha256=<hex>
```

### B — `t=<ts>,v1=<hex>` (Connect today)

```
X-Astra-Signature: t=1730000000,v1=<hex>
```

Timestamp lives inside the signature header; `X-Astra-Timestamp` is optional for this style.

## HTTP status codes

| Code | When | Connect outbox |
|---|---|---|
| **202 accepted** | Inbox row inserted; worker will process | Stop (final — inbox is durable) |
| **200 duplicate** | Same `X-Astra-Delivery` already stored (incl. Failed) | Stop (final) |
| **400** | Malformed JSON / missing delivery id or type | Stop (final) |
| **401** | Bad signature or stale timestamp | Stop (final) |
| **5xx / 429** | Transient server errors only | Retry |
| **503** | Webhook secret not configured | Retry |

`receive()` only verifies HMAC and inserts the inbox row. Business failures land on the **Astra Connect Event** as `Failed` after the worker runs. Redelivering a Failed delivery returns **duplicate**; recover via `retry_event` or the stale-Processing sweeper.

## Site configuration

```json
{
  "astra_connect_webhook_secret": "<per-site shared secret>"
}
```

Desk Single **Astra Connect Settings**: `enabled`, `connect_base_url` (public deep-links only), `default_lead_owner`.  
The signing secret is **never** exposed to the frontend.

## Events (flat camelCase)

Aliases kept for the earlier CRM-04 draft: `lead.upsert` → `lead.created`, `call.outcome` → `call.completed`.

### `lead.created`

Upserts **CRM Lead** keyed on `leadId` → `astra_external_id`.

```json
{
  "type": "lead.created",
  "leadId": "lead_123",
  "name": "Ada Lovelace",
  "phone": "+14155550100",
  "email": "ada@example.com",
  "status": "new",
  "source": "campaign_a",
  "employeeId": "emp_9",
  "createdAt": "2026-10-27T10:00:00Z",
  "channel": "voice"
}
```

`status` ∈ `new|assigned|calling|called|failed|qualified|closed` → CRM Lead Status via a small mapping table (fallback **New**).

| Connect | CRM Lead Status |
|---|---|
| new | New |
| assigned | Nurture |
| calling / called | Contacted |
| failed | Unqualified |
| qualified | Qualified |
| closed | Converted |
| *(other)* | New |

### `call.completed`

Creates/updates **CRM Call Log** (`telephony_medium` = `Astra Connect`). Matching is by **phone** (E.164 with default region **IN**, then last-10 digits). `contactId` is Connect’s id — not a CRM leadId. More than one match → Failed with a clear error.

```json
{
  "type": "call.completed",
  "callId": "call_100",
  "contactId": "ctc_55",
  "employeeId": "emp_9",
  "direction": "outbound",
  "phone": "+919876543210",
  "outcome": "appointment_booked",
  "qualified": true,
  "summary": "Booked a demo for Friday.",
  "fields": { "slot": "2026-10-31T11:00:00Z" },
  "endedAt": "2026-10-27T10:05:00Z",
  "channel": "voice"
}
```

- `outcome` is **free text**, at most 64 chars. Stored as-is (never hard-validated). Known values map to a disposition; anything else → disposition **Other**.
- `qualified` is a bool (also nudges Lead status to Qualified when linked).
- Optional `nextAction` / `nextActionAt` create a **CRM Task** when present (not sent by Connect yet).
- Optional `channel` ∈ `voice|whatsapp` is stored on the Call Log. Channel toggles are **not** in the payload beyond this field.

### `employee.call.completed`

Same as `call.completed`, plus:

```json
{
  "type": "employee.call.completed",
  "callId": "call_100",
  "contactId": "ctc_55",
  "employeeId": "emp_9",
  "direction": "outbound",
  "phone": "9876543210",
  "outcome": "custom_label_from_ops",
  "qualified": false,
  "summary": "Left a voicemail.",
  "fields": {},
  "endedAt": "2026-10-27T10:05:00Z",
  "startedAt": "2026-10-27T10:03:00Z",
  "durationSec": 95,
  "endReason": "completed",
  "recordingUrl": "https://connect.example/r/100",
  "transcript": [{ "role": "agent", "text": "Hello" }]
}
```

`endReason` accepts both `canceled` (one L) and `cancelled` (two Ls).

## Connect today vs proposed

| Topic | Connect today | Proposed (needs Vijay’s OK) |
|---|---|---|
| Call party key | `contactId` + `phone` | Also send `leadId` on `call.completed` so CRM can key by `astra_external_id` without phone ambiguity |
| Signature style | `t=<ts>,v1=<hex>` | Prefer `sha256=<hex>` + `X-Astra-Timestamp` (CRM already accepts both) |
| Event names | `lead.created`, `call.completed`, `employee.call.completed` | — |
| Payload shape | Flat camelCase | — |

## Signing samples

### Python — `sha256=` style

```python
import hashlib, hmac, json, time, urllib.request

SECRET = "your-site-secret"
url = "https://crm.example/api/method/crm.integrations.astra_connect.api.receive"
payload = {
    "type": "lead.created",
    "leadId": "lead_123",
    "name": "Ada Lovelace",
    "phone": "+14155550100",
    "email": "ada@example.com",
    "status": "new",
    "source": "campaign_a",
    "employeeId": "emp_9",
}
body = json.dumps(payload, separators=(",", ":"))
ts = str(int(time.time()))
sig = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
req = urllib.request.Request(
    url,
    data=body.encode(),
    headers={
        "Content-Type": "application/json",
        "X-Astra-Delivery": "dlv_demo_1",
        "X-Astra-Timestamp": ts,
        "X-Astra-Signature": f"sha256={sig}",
    },
    method="POST",
)
print(urllib.request.urlopen(req).read().decode())
```

### curl — `t=,v1=` style

```bash
SECRET='your-site-secret'
BODY='{"type":"call.completed","callId":"call_100","contactId":"ctc_55","employeeId":"emp_9","direction":"outbound","phone":"+919876543210","outcome":"appointment_booked","qualified":true,"summary":"Booked","endedAt":"2026-10-27T10:05:00Z"}'
TS=$(date +%s)
SIG=$(printf '%s' "${TS}.${BODY}" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -sS -X POST \
  'https://crm.example/api/method/crm.integrations.astra_connect.api.receive' \
  -H 'Content-Type: application/json' \
  -H "X-Astra-Delivery: dlv_demo_2" \
  -H "X-Astra-Signature: t=${TS},v1=${SIG}" \
  --data-binary "${BODY}"
```

## Audit log

Every accepted delivery is stored as **Astra Connect Event** (`event_id` = Delivery id, `type`, `payload`, `status`, `error`, `attempts`, `claimed_at`, `processed_at`, `source_timestamp`). System Managers can retry Failed / Received / stale Processing rows via `POST crm.integrations.astra_connect.api.retry_event`.

## Background worker (required on deploy)

Connect prefers the RQ queue **`astra_connect`**. Declare it in `common_site_config.json` (or site config) so `frappe.enqueue` accepts it:

```json
{
  "workers": {
    "astra_connect": { "timeout": 300 }
  }
}
```

Then run a worker that listens to it:

```bash
bench worker --queue astra_connect
# or alongside other queues:
bench worker --queue astra_connect,short,default
```

If `astra_connect` is **not** configured, CRM falls back to the **`default`** queue automatically (so inbox rows are not stranded after `receive()` commits). Prefer declaring the dedicated queue in production.

The scheduler must be running (`bench schedule` / supervisor). Every **2 minutes** `sweep_stale_processing`:

1. Resets stale **`Processing`** rows (older than **N minutes**, default **5**) back to **`Received`** and re-enqueues them with a **fresh RQ job_id** (so a SIGKILL-left `started` job cannot block recovery).
2. Re-enqueues orphaned **`Received`** rows older than N minutes (failed enqueue / undeclared queue / skipped dedupe).

N is configurable on **Astra Connect Settings** → Stale Processing Minutes, or site_config `astra_connect_stale_processing_minutes`.

## Out-of-order deliveries

Call summary text on **CRM Call Log** / **FCRM Note** is guarded by `astra_source_ts` (payload `occurredAt` / `endedAt`, else the signed request timestamp). An older delivery does not overwrite a newer summary.
