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
]

const browser = await chromium.launch()
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
      const file = path.join(out, `astra-${pageName}-${theme}-${vp.name}-MOCKED.png`)
      await page.screenshot({ path: file, fullPage: true })
      console.log('wrote', file)
      await context.close()
    }
  }
}
await browser.close()
console.log('done')
