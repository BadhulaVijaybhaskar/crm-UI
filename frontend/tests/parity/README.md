# Pixel-parity harness (TEST ONLY)

Compares the **production Vite build** (served statically) to:

1. **Source HTML** (`p-*.html` from the Figma capture) re-rendered in Chrome — mode **(a)**
2. **Figma PNG** — mode **(b)**

using Playwright + pixelmatch. Fixtures, the frozen clock, and mocks live only
under `frontend/tests/parity/` — they are never imported by `src/`.

## READ-ONLY references

**Never edit** `p-*.html` or the Figma PNGs to make a diff pass. Where capture
HTML disagrees with its PNG on layout (positions, sizes, text wrap), the **PNG
is the approved design** — match the Vue UI to the PNG. Mode (a) scores Vue vs
HTML only on pixels where that HTML already agrees with the PNG.

## Pass bar (per screen × theme)

| Mode | Metric | Bar |
|---|---|---|
| **(a)** | real difference (1px / 0.1) vs unedited source HTML, on HTML∩PNG agreement pixels | **0%** |
| **(b)** | real difference vs Figma PNG | **≤ 0.75%** |

**floor %** (HTML-in-Chrome vs PNG) is reported for context only.

## Run

```bash
cd frontend
yarn build
yarn parity 02-home
yarn parity all
```

Artifacts land in `/opt/cursor/artifacts/parity/`:

| File | Contents |
|---|---|
| `<screen>-<theme>.png` | triplet: built \| Figma PNG \| diff |
| `<screen>-<theme>-vs-html.png` | triplet: built \| source HTML \| diff |
| `<screen>-report.json` / `.md` | report table below |

### Report columns

| Column | Meaning |
|---|---|
| `screen` | Screen id from `config.js` |
| `theme` | `light` or `dark` |
| `real vs HTML %` | Mode (a) — must be **0** on agreement pixels |
| `real vs PNG %` | Mode (b) — must be **≤ 0.75%** |
| `floor %` | HTML-in-Chrome vs Figma PNG (informational) |
| `pass` | `PASS` only when (a) and (b) both hold |
| `masked` | Example data tag (+ html↔png disagree px count for scoring a) |
| `remaining` | Excess over the pass bar |

## How a screen agent adds a new screen

1. Drop Figma PNGs into `tests/parity/figma/` as `<id>-light.png` and `<id>-dark.png`
   (or rely on `/tmp/crm-figma-v1-all/` fallback). **Do not edit the PNGs.**
2. Point `sourceHtml` at the matching **unedited** `p-*.html` under
   `/tmp/crm-figma-src/figma-crm/` (from `crm-figma-src.tgz`). **Do not edit the HTML.**
3. Add an entry to `config.js` → `SCREENS`:
   - `route` — in-app path under `/crm/…`
   - `viewport` — PNG size (`1440×960` desktop, `390×844` mobile)
   - `deviceScaleFactor: 1`
   - `sourceHtml` / `figma` — light + dark file names
   - `masks` — **only** the design-only “Example data” tag
   - `fixture` — folder name under `fixtures/`
4. Create `fixtures/<id>/` JSON that mirrors the Figma copy exactly.
   Wire extra API shapes in `lib/mocks.js` if needed. Fixtures are test-only.
5. Align `clock` with the design’s “now”.
6. Run `yarn parity <id>`. Fix **Vue UI** until PNG ≤ 0.75% and HTML agreement
   set is 0%. Never put fixtures or clock overrides in production code.

## Ownership

| Region | Owner |
|---|---|
| Nav, app bar, page header chrome, shared `components/astra/*` | Shell agent |
| List / board / record page body | Screen agent for that doctype |
| Login | Login agent |
| Home, Work queue, Conversations, Tasks, Notes, Call logs, m1 | Activity agent |
