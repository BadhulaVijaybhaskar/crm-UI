# Pixel-parity harness (TEST ONLY)

Compares the **production Vite build** (served statically) to signed-off Figma PNGs
using Playwright + pixelmatch. Fixtures, the frozen clock, and mocks live only
under `frontend/tests/parity/` — they are never imported by `src/`.

## Run

```bash
cd frontend
yarn build
yarn parity 04-leads-list
```

Artifacts land in `/opt/cursor/artifacts/parity/`:

- `<screen>-<theme>.png` — triplet (built | figma PNG | diff)
- `<screen>-<theme>-vs-html.png` — triplet (built | source HTML | diff)
- `<screen>-report.json` / `.md` — real vs HTML %, real vs PNG %, floor %, pass

**Pass bar:**

- **01-login:** real % vs Figma PNG ≤ **0.75%** (both themes). real vs source HTML
  is informational only — `figma-src/` is read-only and may drift from the PNG
  (login HTML↔PNG floor ≈ 2.15%).
- **Other screens:** (a) real vs source HTML ≈ 0; (b) real vs PNG ≤ floor
  (sourceHtml↔PNG, typically ~0.75% MCP noise).

Do not edit `figma-src/` or Figma PNGs to chase a pass — fix Vue/CSS only.

## How a screen agent adds a new screen

1. Drop Figma PNGs into `tests/parity/figma/` as `<id>-light.png` and `<id>-dark.png`
   (or rely on `/tmp/crm-figma-v1-all/` fallback).
2. Add an entry to `config.js` → `SCREENS`:
   - `route` — in-app path under `/crm/…`
   - `viewport` — PNG size (`1440×960` desktop, `390×844` mobile)
   - `deviceScaleFactor: 1`
   - `masks` — **only** the design-only “Example data” tag (selector or fallback box)
   - `shellRegions` — optional; shell crop for chrome-owned diffs
   - `fixture` — folder name under `fixtures/`
3. Create `fixtures/<id>/` JSON that mirrors the Figma copy exactly
   (names, counts, statuses, dates). Wire any extra API shapes in `lib/mocks.js`
   if the catch-all is not enough.
4. Clock is global (`PARITY_CLOCK` in `config.js`) — keep it aligned with the
   design’s “now” (relative dates like “today” / “yesterday”).
5. Run `yarn parity <id>`, fix token/spacing/copy until **real %** is 0 for the
   regions you own. Do not put fixtures or clock overrides in production code.

## Ownership

| Region | Owner |
|---|---|
| Nav, app bar, page header chrome, shared `components/astra/*` | Shell agent |
| List / board / record page body | Screen agent for that doctype |
| Login | Login agent |
