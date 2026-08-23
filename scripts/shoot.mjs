// Screenshot a list of routes at several widths. Usage:
//   node scripts/shoot.mjs [baseUrl] [outDir] [route,route,...]
import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'

const base = process.argv[2] ?? 'http://localhost:5199'
const outDir = process.argv[3] ?? '.claude/scratch/shots'
const routes = (process.argv[4] ?? '/').split(',')
const widths = [
  ['mobile', 390, 844],
  ['desktop', 1440, 900],
]

await mkdir(outDir, { recursive: true })
const browser = await chromium.launch()
const errors = []

for (const [label, width, height] of widths) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 })
  page.on('console', (m) => m.type() === 'error' && errors.push(`${label} ${page.url()} :: ${m.text()}`))
  page.on('pageerror', (e) => errors.push(`${label} ${page.url()} :: ${e.message}`))
  for (const route of routes) {
    const name = route.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home'
    const res = await page.goto(base + route, { waitUntil: 'networkidle' })
    await page.screenshot({ path: `${outDir}/${name}.${label}.png`, fullPage: true })
    console.log(`${res?.status()} ${route} @${label}`)
  }
  await page.close()
}

await browser.close()
if (errors.length) {
  console.log('\nCONSOLE ERRORS:')
  for (const e of errors) console.log('  ' + e)
} else {
  console.log('\nno console errors')
}
