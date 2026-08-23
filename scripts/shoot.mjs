// Screenshot a list of routes at several widths. Usage:
//   node scripts/shoot.mjs [baseUrl] [outDir] [route,route,...] [theme]
//
// `theme` covers the three states the palette actually has, because "dark" is two
// different code paths: the media query and the stored override.
//   system-light (default) · system-dark · dark · light
// The last two stamp `pe-theme` in localStorage, which is what the pre-paint script
// in the page head reads, and pin the opposite system preference so the override is
// the thing being tested.
import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'

const base = process.argv[2] ?? 'http://localhost:5199'
const outDir = process.argv[3] ?? '.claude/scratch/shots'
const routes = (process.argv[4] ?? '/').split(',')
const theme = process.argv[5] ?? 'system-light'

const THEMES = {
  'system-light': { colorScheme: 'light', stored: null },
  'system-dark': { colorScheme: 'dark', stored: null },
  dark: { colorScheme: 'light', stored: 'dark' },
  light: { colorScheme: 'dark', stored: 'light' },
}
const themeConfig = THEMES[theme]
if (!themeConfig) {
  console.error(`unknown theme "${theme}". Use one of: ${Object.keys(THEMES).join(', ')}`)
  process.exit(2)
}
const suffix = theme === 'system-light' ? '' : `.${theme}`
const widths = [
  ['mobile', 390, 844],
  ['desktop', 1440, 900],
]

await mkdir(outDir, { recursive: true })
const browser = await chromium.launch()
const errors = []

for (const [label, width, height] of widths) {
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 2,
    colorScheme: themeConfig.colorScheme,
  })
  if (themeConfig.stored) {
    await context.addInitScript((value) => {
      try {
        localStorage.setItem('pe-theme', value)
      } catch {}
    }, themeConfig.stored)
  }
  const page = await context.newPage()
  page.on('console', (m) => m.type() === 'error' && errors.push(`${label} ${page.url()} :: ${m.text()}`))
  page.on('pageerror', (e) => errors.push(`${label} ${page.url()} :: ${e.message}`))
  for (const route of routes) {
    const name = route.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home'
    const res = await page.goto(base + route, { waitUntil: 'networkidle' })
    await page.screenshot({ path: `${outDir}/${name}${suffix}.${label}.png`, fullPage: true })
    console.log(`${res?.status()} ${route} @${label}`)
  }
  await context.close()
}

await browser.close()
if (errors.length) {
  console.log('\nCONSOLE ERRORS:')
  for (const e of errors) console.log('  ' + e)
} else {
  console.log('\nno console errors')
}
