import { chromium } from 'playwright'
import path from 'path'
import fs from 'fs'

const out = '/opt/cursor/artifacts/astra-batch1-screenshots'
fs.mkdirSync(out, { recursive: true })

const pages = ['myday', 'workqueue', 'conversations']
const themes = ['light', 'dark']
const viewports = [
  { name: '1440', width: 1440, height: 900 },
  { name: '390', width: 390, height: 844 },
  { name: '360', width: 360, height: 800 },
]

const browser = await chromium.launch()
let overflowFailures = 0

for (const theme of themes) {
  for (const pageName of pages) {
    for (const vp of viewports) {
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        colorScheme: theme === 'dark' ? 'dark' : 'light',
      })
      const page = await context.newPage()
      const url = `http://127.0.0.1:8080/astra-preview.html?page=${pageName}&theme=${theme}`
      await page.goto(url, { waitUntil: 'networkidle' })
      await page.waitForTimeout(400)

      // No horizontal scroll at narrow widths (My day was overflowing at 390).
      if (
        pageName === 'myday' &&
        (vp.width === 390 || vp.width === 360)
      ) {
        const metrics = await page.evaluate(() => {
          const doc = document.documentElement
          const body = document.body
          const root = document.querySelector('.astra-bento') || body
          return {
            clientWidth: doc.clientWidth,
            scrollWidth: Math.max(
              doc.scrollWidth,
              body.scrollWidth,
              root.scrollWidth,
            ),
          }
        })
        if (metrics.scrollWidth > metrics.clientWidth + 1) {
          overflowFailures += 1
          console.error(
            `OVERFLOW ${pageName} ${theme} ${vp.name}: scrollWidth=${metrics.scrollWidth} clientWidth=${metrics.clientWidth}`,
          )
        } else {
          console.log(
            `ok no-h-scroll ${pageName} ${theme} ${vp.name} (${metrics.scrollWidth}/${metrics.clientWidth})`,
          )
        }
      }

      // Keep published shot matrix at 1440 + 390 (360 is assert-only).
      if (vp.name !== '360') {
        const file = path.join(
          out,
          `astra-${pageName}-${theme}-${vp.name}-MOCKED.png`,
        )
        await page.screenshot({ path: file, fullPage: true })
        console.log('wrote', file)
      }
      await context.close()
    }
  }
}
await browser.close()
if (overflowFailures) {
  console.error(`failed: ${overflowFailures} horizontal overflow check(s)`)
  process.exit(1)
}
console.log('done')
