/**
 * pixelmatch diffs + 1px-neighbour tolerance (threshold 0.1) for "real difference".
 */
import fs from 'node:fs'
import path from 'node:path'
import { PNG } from 'pngjs'
import pixelmatch from 'pixelmatch'

function loadPng(filePath) {
  const buf = fs.readFileSync(filePath)
  return PNG.sync.read(buf)
}

function ensureSize(img, width, height) {
  if (img.width === width && img.height === height) return img
  const out = new PNG({ width, height })
  // fill with black, blit top-left
  for (let y = 0; y < Math.min(height, img.height); y++) {
    for (let x = 0; x < Math.min(width, img.width); x++) {
      const si = (img.width * y + x) << 2
      const di = (width * y + x) << 2
      out.data[di] = img.data[si]
      out.data[di + 1] = img.data[si + 1]
      out.data[di + 2] = img.data[si + 2]
      out.data[di + 3] = img.data[si + 3]
    }
  }
  return out
}

function applyMasks(img, masks) {
  const out = PNG.sync.read(PNG.sync.write(img))
  for (const m of masks || []) {
    const x0 = Math.max(0, Math.floor(m.x))
    const y0 = Math.max(0, Math.floor(m.y))
    const x1 = Math.min(img.width, Math.ceil(m.x + m.width))
    const y1 = Math.min(img.height, Math.ceil(m.y + m.height))
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const i = (img.width * y + x) << 2
        // Magenta mask fill so it matches on both sides when applied to both
        out.data[i] = 255
        out.data[i + 1] = 0
        out.data[i + 2] = 255
        out.data[i + 3] = 255
      }
    }
  }
  return out
}

function crop(img, region) {
  const { x, y, width, height } = region
  const out = new PNG({ width, height })
  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
      const sx = x + col
      const sy = y + row
      if (sx < 0 || sy < 0 || sx >= img.width || sy >= img.height) continue
      const si = (img.width * sy + sx) << 2
      const di = (width * row + col) << 2
      out.data[di] = img.data[si]
      out.data[di + 1] = img.data[si + 1]
      out.data[di + 2] = img.data[si + 2]
      out.data[di + 3] = img.data[si + 3]
    }
  }
  return out
}

function colorDist(a, b, i, j) {
  const dr = a[i] - b[j]
  const dg = a[i + 1] - b[j + 1]
  const db = a[i + 2] - b[j + 2]
  return Math.sqrt(dr * dr + dg * dg + db * db) / 441.67 // ~max rgb dist
}

/**
 * Real-difference: a pixel counts only if it fails pixelmatch threshold AND
 * no neighbour within 1px in the reference is similar (tolerance for AA/layout jitter).
 */
function realDifferenceCount(built, figma, width, height, threshold = 0.1) {
  let count = 0
  const diffMap = new Uint8Array(width * height)
  // First pass: raw per-pixel fail at threshold
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (width * y + x) << 2
      if (colorDist(built.data, figma.data, i, i) > threshold) {
        diffMap[width * y + x] = 1
      }
    }
  }
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!diffMap[width * y + x]) continue
      const bi = (width * y + x) << 2
      let near = false
      for (let dy = -1; dy <= 1 && !near; dy++) {
        for (let dx = -1; dx <= 1 && !near; dx++) {
          const nx = x + dx
          const ny = y + dy
          if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue
          const fi = (width * ny + nx) << 2
          if (colorDist(built.data, figma.data, bi, fi) <= threshold) near = true
        }
      }
      if (!near) count++
    }
  }
  return count
}

function stitchTriplet(built, figma, diff) {
  const w = built.width
  const h = built.height
  const gap = 8
  const out = new PNG({ width: w * 3 + gap * 2, height: h })
  const panels = [built, figma, diff]
  panels.forEach((img, idx) => {
    const ox = idx * (w + gap)
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const si = (w * y + x) << 2
        const di = (out.width * y + (ox + x)) << 2
        out.data[di] = img.data[si]
        out.data[di + 1] = img.data[si + 1]
        out.data[di + 2] = img.data[si + 2]
        out.data[di + 3] = img.data[si + 3]
      }
    }
  })
  return out
}

export function compareImages({
  builtPath,
  figmaPath,
  outTripletPath,
  masks = [],
  shellRegions = [],
}) {
  let built = loadPng(builtPath)
  let figma = loadPng(figmaPath)
  const width = figma.width
  const height = figma.height
  built = ensureSize(built, width, height)

  const builtM = applyMasks(built, masks)
  const figmaM = applyMasks(figma, masks)

  const diff = new PNG({ width, height })
  const mismatch = pixelmatch(builtM.data, figmaM.data, diff.data, width, height, {
    threshold: 0.1,
    includeAA: true,
  })
  const total = width * height
  const rawPct = (mismatch / total) * 100
  const real = realDifferenceCount(builtM, figmaM, width, height, 0.1)
  const realPct = (real / total) * 100

  fs.mkdirSync(path.dirname(outTripletPath), { recursive: true })
  const triplet = stitchTriplet(builtM, figmaM, diff)
  fs.writeFileSync(outTripletPath, PNG.sync.write(triplet))

  // Also write individual panels next to triplet
  const base = outTripletPath.replace(/\.png$/, '')
  fs.writeFileSync(`${base}-built.png`, PNG.sync.write(builtM))
  fs.writeFileSync(`${base}-figma.png`, PNG.sync.write(figmaM))
  fs.writeFileSync(`${base}-diff.png`, PNG.sync.write(diff))

  const shell = []
  for (const region of shellRegions) {
    const b = crop(built, region)
    const f = crop(figma, region)
    const d = new PNG({ width: region.width, height: region.height })
    const m = pixelmatch(b.data, f.data, d.data, region.width, region.height, {
      threshold: 0.1,
      includeAA: true,
    })
    const t = region.width * region.height
    const r = realDifferenceCount(b, f, region.width, region.height, 0.1)
    shell.push({
      name: region.name,
      rawPct: (m / t) * 100,
      realPct: (r / t) * 100,
      mismatch: m,
      real: r,
      total: t,
    })
  }

  // Combined shell metric (union of regions)
  let shellReal = 0
  let shellTotal = 0
  let shellRaw = 0
  for (const s of shell) {
    shellReal += s.real
    shellRaw += s.mismatch
    shellTotal += s.total
  }

  return {
    width,
    height,
    mismatch,
    rawPct,
    real,
    realPct,
    masks: masks.map((m) => m.name || 'mask'),
    shell,
    shellRawPct: shellTotal ? (shellRaw / shellTotal) * 100 : 0,
    shellRealPct: shellTotal ? (shellReal / shellTotal) * 100 : 0,
    tripletPath: outTripletPath,
  }
}

/**
 * Real-difference % of built vs HTML, counted only on pixels where HTML agrees
 * with the Figma PNG (1px / 0.1). PNG wins layout disputes — HTML-only pixels
 * are excluded from pass (a). Returns percent of the full frame.
 */
export function agreementRealPercent(
  builtPath,
  htmlPath,
  pngPath,
  masks = [],
  threshold = 0.1,
) {
  let built = loadPng(builtPath)
  let html = loadPng(htmlPath)
  let png = loadPng(pngPath)
  const width = png.width
  const height = png.height
  built = ensureSize(built, width, height)
  html = ensureSize(html, width, height)

  const builtM = applyMasks(built, masks)
  const htmlM = applyMasks(html, masks)
  const pngM = applyMasks(png, masks)

  let agree = 0
  let disagree = 0
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (width * y + x) << 2
      // HTML ≡ PNG? (exact or 1px neighbour)
      let htmlMatchesPng = colorDist(htmlM.data, pngM.data, i, i) <= threshold
      if (!htmlMatchesPng) {
        outer: for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (!dx && !dy) continue
            const nx = x + dx
            const ny = y + dy
            if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue
            const ni = (width * ny + nx) << 2
            if (colorDist(htmlM.data, pngM.data, i, ni) <= threshold) {
              htmlMatchesPng = true
              break outer
            }
          }
        }
      }
      if (!htmlMatchesPng) continue
      agree++
      // Built must match HTML on agreement pixels
      let builtMatches = colorDist(builtM.data, htmlM.data, i, i) <= threshold
      if (!builtMatches) {
        outer2: for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (!dx && !dy) continue
            const nx = x + dx
            const ny = y + dy
            if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue
            const ni = (width * ny + nx) << 2
            if (colorDist(builtM.data, htmlM.data, i, ni) <= threshold) {
              builtMatches = true
              break outer2
            }
          }
        }
      }
      if (!builtMatches) disagree++
    }
  }
  const total = width * height
  return {
    agree,
    disagree,
    /** Mismatches on agreement pixels as % of full frame (pass (a) → 0). */
    realPct: total ? (disagree / total) * 100 : 0,
    /** Mismatches as % of agreement pixels only. */
    agreePct: agree ? (disagree / agree) * 100 : 0,
  }
}

/** Shell-only real % (nav + app bar), same 1px / 0.1 rule as full-page real %. */
export function shellRealPercent(builtPath, figmaPath, shellRegions = []) {
  const built = loadPng(builtPath)
  const figma = loadPng(figmaPath)
  const width = figma.width
  const height = figma.height
  const builtSized = ensureSize(built, width, height)
  let shellReal = 0
  let shellTotal = 0
  for (const region of shellRegions) {
    const b = crop(builtSized, region)
    const f = crop(figma, region)
    const r = realDifferenceCount(b, f, region.width, region.height, 0.1)
    shellReal += r
    shellTotal += region.width * region.height
  }
  return shellTotal ? (shellReal / shellTotal) * 100 : 0
}
