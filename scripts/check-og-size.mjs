#!/usr/bin/env node
// Fail the build if a generated social card exceeds Bluesky's thumbnail cap.
//
//   node scripts/check-og-size.mjs [dist/og]
//
// Bluesky's lexicon caps an embedded external thumbnail at exactly 1,000,000 bytes and
// drops the card silently above it. That is the binding limit — Facebook's is 8MB and
// X's is 5MB — and it is the kind of thing nobody notices until a link looks bare in
// somebody else's feed six months later.

import { readdir, stat } from 'node:fs/promises'
import { join } from 'node:path'

const MAX_BYTES = 1_000_000
const dir = process.argv[2] ?? 'dist/og'

let files
try {
  files = await readdir(dir)
} catch {
  console.error(`no social cards found at ${dir}; did the build run?`)
  process.exit(1)
}

const images = files.filter((name) => /\.(png|jpe?g|webp)$/i.test(name))
if (images.length === 0) {
  console.error(`no social cards found at ${dir}; did the build run?`)
  process.exit(1)
}

const oversized = []
for (const name of images) {
  const { size } = await stat(join(dir, name))
  if (size > MAX_BYTES) oversized.push([name, size])
}

if (oversized.length > 0) {
  console.error(`social cards over the ${MAX_BYTES.toLocaleString()}-byte Bluesky cap:`)
  for (const [name, size] of oversized) console.error(`  ${name}  ${size.toLocaleString()} bytes`)
  process.exit(1)
}

console.log(`${images.length} social card(s), all under the ${MAX_BYTES.toLocaleString()}-byte cap`)
