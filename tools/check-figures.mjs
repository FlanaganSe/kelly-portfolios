#!/usr/bin/env node
// Validate figure manifests before they are copied into src/content/figures/.
//
//   node tools/check-figures.mjs <dir-of-*.figures.yaml>
//
// Checks: every id is declared exactly once across all manifests, every status is a
// member of the EvidenceStatus union, values are strings, docPaths resolve, and the
// same id never carries two different facts.

import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { join, basename } from 'node:path'
import * as yaml from 'js-yaml'

const STATUSES = new Set([
  'exploratory', 'source-reproduced', 'independently-reproduced', 'walk-forward-tested',
  'shadow-live', 'production-eligible', 'rejected', 'unresolved',
])

const dir = process.argv[2] ?? '.claude/scratch/copy'
const files = readdirSync(dir).filter((f) => f.endsWith('.figures.yaml'))

const seen = new Map() // id -> [{page, record}]
const problems = []

for (const file of files) {
  const page = basename(file, '.figures.yaml')
  const doc = yaml.load(readFileSync(join(dir, file), 'utf8'))
  const records = Array.isArray(doc) ? doc : (doc?.figures ?? Object.values(doc ?? {}))

  for (const r of records) {
    if (!r?.id) { problems.push(`${page}: a record has no id`); continue }
    if (!STATUSES.has(r.status)) {
      problems.push(`${page}/${r.id}: status "${r.status}" is not an EvidenceStatus`)
    }
    if (typeof r.value !== 'string') {
      problems.push(`${page}/${r.id}: value must be a string, got ${typeof r.value} (${r.value})`)
    }
    if (r.status === 'production-eligible') {
      problems.push(`${page}/${r.id}: nothing here has reached production-eligible`)
    }
    const dp = r.source?.docPath
    if (!dp) problems.push(`${page}/${r.id}: no source.docPath`)
    else if (!existsSync(dp)) problems.push(`${page}/${r.id}: docPath does not exist: ${dp}`)
    if (!r.asOf) problems.push(`${page}/${r.id}: no asOf`)

    if (!seen.has(r.id)) seen.set(r.id, [])
    seen.get(r.id).push({ page, r })
  }
}

// Same id in two manifests: fine only if the fact is identical.
for (const [id, uses] of seen) {
  if (uses.length === 1) continue
  const key = (x) => JSON.stringify([x.value, x.unit ?? null, x.interval ?? null, x.status])
  const distinct = new Set(uses.map((u) => key(u.r)))
  if (distinct.size > 1) {
    problems.push(
      `COLLISION ${id}: declared in ${uses.map((u) => u.page).join(', ')} with different facts:\n` +
        uses.map((u) => `      ${u.page}: value=${JSON.stringify(u.r.value)} unit=${JSON.stringify(u.r.unit ?? null)} interval=${JSON.stringify(u.r.interval ?? null)} status=${u.r.status}`).join('\n'),
    )
  }
}

console.log(`${files.length} manifests · ${seen.size} distinct figure ids`)
if (problems.length) {
  console.log(`\n${problems.length} problems:\n`)
  for (const p of problems) console.log('  ' + p)
  process.exit(1)
}
console.log('all figure records valid')
