# Pixel-parity harness (TEST ONLY)

Compares the **production Vite build** (served statically) to:

1. **Source HTML** (`p-*.html` from the Figma capture) re-rendered in Chrome
2. **Figma PNG**

using Playwright + pixelmatch. Fixtures, the frozen clock, and mocks live only
under `frontend/tests/parity/` — they are never imported by `src/`.

## Pass bar (per screen × theme)

| Mode | Metric | Bar |
|---|---|---|
| **(a)** | real difference vs **unedited** source HTML, only on pixels where HTML **agrees** with the PNG | **0%** |
| **(b)** | real difference vs Figma PNG | **≤ 0.75%** |

**Refs are read-only.** Never edit `p-*.html` or the Figma PNGs to close a diff.
Where HTML layout (positions, sizes, text wrap) disagrees with the PNG, the **PNG
is the approved design** — match the PNG. HTML/PNG disagreement pixels are
excluded from pass (a).

**floor %** (reported) = source HTML in Chrome vs the Figma PNG (informational
MCP/layout drift, often ≈ 0.75%).

When `shellRegions` are set (Leads 04 shell), percentages use that crop
(nav 240×960 + app bar 1200×52). Otherwise full-page (after masks).

## Run

```bash
cd frontend
yarn build
yarn parity 04-leads-list
# Settings:
yarn parity 21-settings-stages
yarn parity 22-settings-users
yarn parity 23-settings-fields
```

Source HTML must exist at `/tmp/crm-figma-src/figma-crm/` (from
`uploads/crm-figma-src.tgz`). Do not invent or patch those files.

Artifacts land in `/opt/cursor/artifacts/parity/`:

| File | Contents |
|---|---|
| `<screen>-<theme>-vs-html.png` | triplet: built \| source HTML \| diff |
| `<screen>-<theme>-vs-png.png` | triplet: built \| Figma PNG \| diff |
| `<screen>-report.json` / `.md` | report table below |

### Report columns

| Column | Meaning |
|---|---|
| `screen` | Screen id from `config.js` |
| `theme` | `light` or `dark` |
| `real vs HTML %` | Vue vs unedited HTML (reported) |
| `real vs PNG %` | Vue vs Figma PNG |
| `floor %` | HTML in Chrome vs PNG (informational) |
| `pass` | (a) HTML-agree == 0 **and** (b) vs PNG ≤ 0.75% |
| `masked` | Mask names applied (Example data only) |
| `remaining` | What still fails |

## How a screen agent adds a new screen

1. Drop Figma PNGs into `tests/parity/figma/` as `<id>-light.png` and `<id>-dark.png`
   (or rely on `/tmp/crm-figma-v1-all/` fallback). **Do not edit PNGs.**
2. Point `sourceHtml` at the matching **unedited** `p-*.html` under
   `/tmp/crm-figma-src/figma-crm/`.
3. Add an entry to `config.js` → `SCREENS`:
   - `route` — in-app path under `/crm/…`
   - `viewport` — PNG size (`1440×960` desktop, `390×844` mobile)
   - `deviceScaleFactor: 1`
   - `masks` — **only** the design-only “Example data” tag (selector or fallback box)
   - `shellRegions` — optional; shell crop for chrome-owned diffs
   - `fixture` — folder name under `fixtures/`
4. Create `fixtures/<id>/` JSON that mirrors the Figma copy exactly
   (names, counts, statuses, dates). Wire any extra API shapes in `lib/mocks.js`
   if the catch-all is not enough.
5. Clock is global (`PARITY_CLOCK` in `config.js`) — keep it aligned with the
   design’s “now” (relative dates like “today” / “yesterday”).
6. Run `yarn parity <id>`, restyle Vue until **vs PNG ≤ 0.75%** and **vs HTML
   (agreement) = 0%**. Never patch the HTML or PNG references.

## Ownership

| Region | Owner |
|---|---|
| Nav, app bar, page header chrome, shared `components/astra/*` | Shell agent |
| List / board / record / settings page body | Screen agent for that surface |
| Login | Login agent |
