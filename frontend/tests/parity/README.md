# Pixel-parity harness (TEST ONLY)

Compares the **production Vite build** (served statically) to:

1. **Source HTML** (`p-*.html` from the Figma capture) re-rendered in Chrome — mode **(a)**
2. **Figma PNG** — mode **(b)**

using Playwright + pixelmatch. Fixtures, the frozen clock, and mocks live only
under `frontend/tests/parity/` — they are never imported by `src/`.

## Pass bar (per screen × theme)

| Mode | Metric | Bar |
|---|---|---|
| **(a)** | real difference (1px neighbour / threshold 0.1) vs source HTML | **0%** |
| **(b)** | real difference vs Figma PNG | **≤ floor %** |

**floor %** = the same crop of the source HTML in Chrome compared with the Figma PNG
(≈ 0.75% for the shell — MCP PNGs are not Chrome pixels).

When `shellRegions` are set (Leads 04 shell), both percentages are the **shell crop**
(nav 240×960 + app bar 1200×52). Otherwise they are full-page (after masks).

## Run

```bash
cd frontend
yarn build
yarn parity 04-leads-list
```

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
| `real vs HTML %` | Mode (a) — must be **0** |
| `real vs PNG %` | Mode (b) — must be **≤ floor %** |
| `floor %` | HTML-in-Chrome vs Figma PNG (same crop) |
| `pass` | `yes` only when (a) and (b) both hold |
| `masked` | Design-only masks applied (e.g. Example data tag) |
| `remaining` | Shell vs HTML left to close, or `—` when (a) is 0 |

## How a screen agent adds a new screen

1. Drop Figma PNGs into `tests/parity/figma/` as `<id>-light.png` and `<id>-dark.png`
   (or rely on `/tmp/crm-figma-v1-all/` fallback).
2. Point `sourceHtml` at the matching `p-*.html` basenames under
   `/tmp/crm-figma-src/figma-crm/` (or `PATHS.figmaSrc`).
3. Add an entry to `config.js` → `SCREENS`:
   - `route` — in-app path under `/crm/…`
   - `viewport` — PNG size (`1440×960` desktop, `390×844` mobile)
   - `deviceScaleFactor: 1`
   - `sourceHtml` / `figma` — light + dark file names
   - `masks` — **only** the design-only “Example data” tag (selector or fallback box)
   - `shellRegions` — optional; shell crop while the shell agent owns chrome
   - `fixture` — folder name under `fixtures/`
4. Create `fixtures/<id>/` JSON that mirrors the Figma copy exactly
   (names, counts, statuses, dates). Wire any extra API shapes in `lib/mocks.js`
   if the catch-all is not enough.
5. Clock is global (`PARITY_CLOCK` in `config.js`) — keep it aligned with the
   design’s “now” (relative dates like “today” / “yesterday”).
6. Run `yarn parity <id>`. Drive **real vs HTML %** to **0** for the regions you
   own; keep **real vs PNG %** ≤ **floor %**. Do not put fixtures or clock
   overrides in production code.

## Ownership

| Region | Owner |
|---|---|
| Nav, app bar, page header chrome, shared `components/astra/*` | Shell agent |
| List / board / record page body | Screen agent for that doctype |
| Login | Login agent |
