#!/usr/bin/env node
// Crawl every built page in `dist/` and report internal hrefs that resolve to nothing.
//
//   node scripts/check-links.mjs [distDir]
//
// `trailingSlash` is `always` and the build format is `directory`, so every page is
// `dist/<route>/index.html` and every internal link should carry its slash. A link
// missing the slash is reported separately: it resolves on most hosts, by way of a
// redirect the reader pays for, and the build emits no such URL of its own.
//
// Only internal links are followed. An external URL is somebody else's uptime, and a
// crawler that hit GitHub 89 times per run would be rate-limited rather than useful.

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'

const dist = resolve(process.argv[2] ?? 'dist')

function walk(dir, found = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) walk(path, found)
    else found.push(path)
  }
  return found
}

const all = walk(dist)
// Every file the build emitted, not only its pages: a favicon, a manifest and a
// stylesheet are all linked from every page and all of them have to exist.
const emitted = new Set(all.map((f) => f.slice(dist.length).replaceAll('\\', '/')))
const files = all.filter((f) => f.endsWith('.html'))

/** Anchor ids on each built page, so a `#fragment` can be checked as well as the path. */
const idsFor = new Map()
function idsOf(htmlPath) {
  let ids = idsFor.get(htmlPath)
  if (!ids) {
    ids = new Set()
    const html = readFileSync(htmlPath, 'utf8')
    for (const m of html.matchAll(/\sid="([^"]+)"/g)) ids.add(m[1])
    for (const m of html.matchAll(/\sname="([^"]+)"/g)) ids.add(m[1])
    idsFor.set(htmlPath, ids)
  }
  return ids
}

const decode = (s) => s.replace(/&#x26;|&#38;|&amp;/gi, '&')

let checked = 0
const dead = []
const noSlash = []
const deadFragment = []

for (const file of files) {
  const from = file.slice(dist.length)
  const html = readFileSync(file, 'utf8')
  for (const match of html.matchAll(/href="([^"]*)"/g)) {
    const href = decode(match[1])
    if (href === '' || /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(href)) continue
    checked += 1

    const [rawPath, ...rest] = href.split('#')
    const fragment = rest.join('#')

    // A bare fragment points at the page it was written on.
    let targetFile = file
    if (rawPath !== '') {
      const path = rawPath.startsWith('/') ? rawPath : new URL(rawPath, `http://x${from}`).pathname
      const candidates = path.endsWith('/') ? [`${path}index.html`] : [path, `${path}/index.html`]
      const hit = candidates.find((c) => emitted.has(c))
      if (!hit) {
        dead.push(`${from} -> ${href}`)
        continue
      }
      if (!path.endsWith('/') && !path.includes('.')) noSlash.push(`${from} -> ${href}`)
      targetFile = join(dist, hit)
    }

    if (fragment && !idsOf(targetFile).has(fragment)) deadFragment.push(`${from} -> ${href}`)
  }
}

const report = (label, list) => {
  if (list.length === 0) return
  console.log(`\n${label} (${list.length}):`)
  for (const line of list.slice(0, 40)) console.log(`  ${line}`)
  if (list.length > 40) console.log(`  … and ${list.length - 40} more`)
}

report('internal links with no file behind them', dead)
report('internal links to a fragment that is not on the page', deadFragment)
report('internal links missing their trailing slash', noSlash)

console.log(`\n${files.length} pages · ${checked} internal links · ${dead.length} dead · ${deadFragment.length} dead fragments · ${noSlash.length} missing a slash`)
process.exit(dead.length + deadFragment.length > 0 ? 1 : 0)
