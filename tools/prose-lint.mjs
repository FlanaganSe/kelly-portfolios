#!/usr/bin/env node
// Enforce the house voice on reader-facing prose.
//
//   node tools/prose-lint.mjs <file|dir> [...]
//   node tools/prose-lint.mjs --quiet src/content   # exit code only
//
// Pattern rules live in tools/prose-rules.txt, extracted verbatim from section I of
// the voice guide so the linter and the guide cannot drift apart. Density rules are
// section I's scriptable checks and live here because they need a parsed document.
//
// A pattern hit is an error. A density warning is a warning: these measure habits,
// and a single page may legitimately sit outside a band.
//
// Prose reaches a reader through `src/content/` as well as through a page: a figure's
// note is printed under its number and a data module's `reason` or `gloss` is printed
// verbatim. So this reads `.yaml` records and `.ts` modules too, and in both it reads
// the prose fields rather than the whole file. What it deliberately does not read: a
// test file, which quotes the copy it asserts on; an address, meaning `docPath`,
// `anchor`, `id`, `ticker` and their kind; and a measurement, meaning `value`, `unit`,
// `interval` and `period`, which are the fact as its source printed it.

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, extname, basename } from 'node:path'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import * as yaml from 'js-yaml'

const here = dirname(fileURLToPath(import.meta.url))
const TEXT_EXT = new Set(['.md', '.mdx', '.ts', '.tsx', '.astro', '.html', '.yaml', '.yml'])

/**
 * The keys of a YAML record whose value is reader-facing prose.
 *
 * A figure record is mostly data. `value`, `unit`, `interval`, `period`, `status` and
 * `asOf` are the fact as its source printed it and are not the linter's business — a
 * unit reading "percent of simulated thirty-year paths" is a measurement, not writing.
 * What a reader meets as sentences is the caption above the number, the note beneath it
 * and the citation's link text, so those are what this checks. Everything else in the
 * record, `source.docPath` and `source.anchor` included, is a path or a slug and would
 * report a heading called `3-what-makes-a-sleeve-worth-adding` as writing.
 */
const YAML_PROSE_KEYS = new Set(['label', 'note', 'caption', 'summary', 'why', 'gloss', 'caution', 'blurb'])

/** Every prose-bearing string in a parsed YAML document, in document order. */
function yamlProse(node, key = null, out = []) {
  if (typeof node === 'string') {
    if (key !== null && YAML_PROSE_KEYS.has(key)) out.push(node)
    return out
  }
  if (Array.isArray(node)) {
    for (const item of node) yamlProse(item, key, out)
    return out
  }
  if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) yamlProse(v, k, out)
  }
  return out
}

/** PCRE `\x{...}` is not JS. Rewrite to `\u{...}` and flag the pattern as unicode. */
function compile(source) {
  const unicode = /\\x\{/.test(source)
  const body = unicode ? source.replaceAll('\\x{', '\\u{') : source
  let flags = 'g'
  // Inline (?i) / (?m) / (?im) prefixes, which JS does not support.
  const inline = body.match(/^\((\?[ims]+)\)/)
  let rest = body
  if (inline) {
    if (inline[1].includes('i')) flags += 'i'
    if (inline[1].includes('m')) flags += 'm'
    rest = body.slice(inline[0].length)
  }
  if (unicode) flags += 'u'
  return new RegExp(rest, flags)
}

function loadRules() {
  const lines = readFileSync(join(here, 'prose-rules.txt'), 'utf8').split('\n')
  const rules = []
  let section = 'general'
  for (const line of lines) {
    const t = line.trim()
    if (!t) continue
    if (t.startsWith('#')) {
      section = t.replace(/^#\s*/, '')
      continue
    }
    try {
      rules.push({ section, source: t, re: compile(t) })
    } catch (err) {
      console.error(`skipping unparseable rule: ${t} (${err.message})`)
    }
  }
  return rules
}

/**
 * Strip the parts of a source file that are not reader-facing prose: code fences,
 * inline code, URLs, import lines, HTML/JSX attributes, and markdown link targets.
 * Without this the linter fires on identifiers and hrefs rather than on writing.
 */
function proseOf(text, ext) {
  let s = text
  // A YAML record is data with prose in a few named fields. Pull those out first and let
  // the generic strips below run over them, so a note quoting `AVUV` in backticks is
  // treated the same way it would be in Markdown.
  if (ext === '.yaml' || ext === '.yml') {
    let doc
    try {
      doc = yaml.load(s)
    } catch (err) {
      console.error(`skipping unparseable YAML: ${err.message}`)
      return ''
    }
    s = yamlProse(doc).join('\n\n')
  }
  // An .astro file opens with a `---` fenced script, and .md/.mdx open with YAML
  // frontmatter. Both fences are syntax rather than the Markdown horizontal rule the
  // typography rule hunts, and neither body is reader-facing prose.
  if (ext === '.astro' || ext === '.md' || ext === '.mdx')
    s = s.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '')
  s = s.replace(/```[\s\S]*?```/g, '')
  s = s.replace(/`[^`\n]*`/g, '')
  s = s.replace(/^\s*(import|export)\s.*$/gm, '')
  s = s.replace(/\]\([^)]*\)/g, ']')
  // `\S+` would swallow the quote and comma that close `href: "https://…htm",`, and the
  // literal scan below pairs quotes naively: one unbalanced quote inverts the pairing for
  // the rest of the file, so raw source lints as prose and real prose goes unread. Stop at
  // the delimiter instead.
  s = s.replace(/https?:\/\/[^\s"'`]+/g, '')
  if (ext === '.ts' || ext === '.tsx' || ext === '.astro') {
    s = s.replace(/^\s*\/\/.*$/gm, '')
    s = s.replace(/\/\*[\s\S]*?\*\//g, '')
    s = s.replace(/\b(class|className|href|src|id|key|slug|path|docPath)=(["'])[^"']*\2/g, '')
    // The same fields again in their object-literal spelling. A data module addresses a
    // research file by path and a heading by slug, so `docPath: "docs/research/
    // marginal-sleeve-value.md"` and `anchor: "3-what-makes-a-sleeve-worth-adding"` are
    // addresses. Reporting them as jargon would push the fix onto the corpus's filenames
    // rather than onto the writing, which is the wrong file to edit.
    s = s.replace(/\b(?:href|src|id|key|slug|path|docPath|anchor|ticker|factor|route|file|category)\s*:\s*(["'])[^"'\n]*\1/g, '')
    // And the measurement fields, for the reason {@link YAML_PROSE_KEYS} gives: a value
    // reading "8,563 → 2,105 → 44" is a count at three stages of a screen, not an arrow
    // used as punctuation.
    s = s.replace(/\b(?:value|unit|interval|period)\s*:\s*(["'])[^"'\n]*\1/g, '')
    // A string union is an identifier that happens to be spelled with quotes. `type
    // ShelfCategory = … | "capital-efficient"` is the same kind of address as an `id`,
    // and the words a reader actually sees for it live in the page's own label map.
    s = s.replace(/\btype\s+\w+(?:<[^>]*>)?\s*=[\s\S]*?;/g, '')
    // The `export type X =` line is already gone by here, so a union broken over several
    // lines survives as bare `| "member"` continuations. Those are members too.
    s = s.replace(/^\s*\|\s*(["'])[^"'\n]*\1\s*;?\s*$/gm, '')
  }

  // A `.ts` data module is mostly identifiers. Its reader-facing copy is always inside a
  // string, so lint the strings and nothing else — otherwise a field named `loadings`
  // reports as jargon sixty-four times and buries the four sentences that really say it.
  if (ext === '.ts' || ext === '.tsx') {
    const literals = s.match(/(["'`])(?:\\.|(?!\1)[^\\])*\1/g) ?? []
    s = literals.map((l) => l.slice(1, -1)).join('\n')
  }
  return s
}

function sentences(prose) {
  return prose
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?])\s+(?=[A-Z"'“])/)
    .map((x) => x.trim())
    .filter((x) => x.split(/\s+/).length > 1)
}

function density(prose) {
  const words = prose.split(/\s+/).filter(Boolean)
  const n = words.length
  if (n < 120) return []
  const per = (count, unit) => (count / n) * unit
  const out = []
  const warn = (msg) => out.push(msg)

  const emDash = (prose.match(/\s—\s/g) ?? []).length
  if (per(emDash, 1000) > 5) warn(`em dashes ${per(emDash, 1000).toFixed(1)}/1k words (fail above 5)`)
  else if (per(emDash, 1000) > 2) warn(`em dashes ${per(emDash, 1000).toFixed(1)}/1k words (warn above 2)`)

  const lens = sentences(prose).map((s) => s.split(/\s+/).length)
  if (lens.length > 8) {
    const mean = lens.reduce((a, b) => a + b, 0) / lens.length
    const sd = Math.sqrt(lens.reduce((a, b) => a + (b - mean) ** 2, 0) / lens.length)
    if (sd < 8) warn(`sentence-length variety low: sd ${sd.toFixed(1)} words, mean ${mean.toFixed(1)} (want sd >= 8)`)
  }

  const bold = (prose.match(/\*\*[^*]+\*\*/g) ?? []).length
  if (per(bold, 100) > 1) warn(`bold runs ${per(bold, 100).toFixed(1)}/100 words (want <= 1)`)

  // Two rules lived here once: a minimum digit count and a minimum count of distinct
  // proper nouns, both per 500 words. They were meant to stop the prose going abstract.
  // What they actually did was reward stuffing a number and a fund name into every
  // paragraph, which is most of why the old pages read the way they did. A paragraph
  // that needs no number should be allowed to have none.

  const bland = (prose.match(/\b(is|are|was|were)\b/gi) ?? []).length
  const puffed = (prose.match(/\b(serves as|stands as|represents|features)\b/gi) ?? []).length
  if (puffed > 0 && bland / puffed < 3) warn(`"serves as"/"represents" family outweighs plain "is" (${bland}:${puffed}, want >= 3:1)`)

  const participles = (prose.match(/,\s\w+ing\b/g) ?? []).length
  if (per(participles, 1000) > 3) warn(`comma-offset "-ing" tails ${per(participles, 1000).toFixed(1)}/1k words (want <= 3)`)

  // A performance figure with nothing to compare it against.
  const naked = sentences(prose).filter(
    (s) =>
      /\d+(\.\d+)?\s*(pp\/yr|bp|%|percentage points?|points? a year)/i.test(s) &&
      /\b(better|beat|ahead|adds?|gains?|improve|outperform|extra|more)\b/i.test(s) &&
      !/\b(against|compared with|compared to|versus|vs\.?|relative to|better than|than|benchmark|index|control)\b/i.test(s),
  )
  for (const s of naked) warn(`figure with no stated comparison: "${s.slice(0, 90)}…"`)

  return out
}

/** A test file quotes the copy it asserts on. Linting it would report the same sentence twice. */
const isTest = (file) => /\.(test|spec)\.[jt]sx?$/.test(basename(file))

function walk(target, acc = []) {
  const st = statSync(target)
  if (st.isFile()) {
    if (TEXT_EXT.has(extname(target)) && !isTest(target)) acc.push(target)
    return acc
  }
  for (const entry of readdirSync(target)) {
    if (entry === 'node_modules' || entry.startsWith('.')) continue
    walk(join(target, entry), acc)
  }
  return acc
}

const args = process.argv.slice(2)
const quiet = args.includes('--quiet')
const targets = args.filter((a) => !a.startsWith('--'))
if (targets.length === 0) {
  console.error('usage: node tools/prose-lint.mjs <file|dir> [...] [--quiet]')
  process.exit(2)
}

const rules = loadRules()
const files = targets.flatMap((t) => walk(t))
let errors = 0
let warnings = 0

for (const file of files) {
  const raw = readFileSync(file, 'utf8')
  const prose = proseOf(raw, extname(file))
  const hits = []

  for (const rule of rules) {
    rule.re.lastIndex = 0
    for (const m of prose.matchAll(rule.re)) {
      const before = prose.slice(0, m.index)
      const line = before.split('\n').length
      hits.push({ line, text: m[0].trim().slice(0, 70), section: rule.section })
    }
  }

  const dens = density(prose)
  errors += hits.length
  warnings += dens.length

  if (!quiet && (hits.length || dens.length)) {
    console.log(`\n${file}`)
    for (const h of hits) console.log(`  error  [${h.section}] ${JSON.stringify(h.text)}`)
    for (const d of dens) console.log(`  warn   ${d}`)
  }
}

const summary = `${files.length} files · ${errors} errors · ${warnings} warnings`
if (errors) {
  console.log(`\n${summary}`)
  process.exit(1)
}
console.log(`\n${summary}`)
