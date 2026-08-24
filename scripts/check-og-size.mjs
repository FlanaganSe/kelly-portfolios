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

// Recursive, because a card's file name is its page's path: the tools sit at
// dist/og/tools/, and the fifty rendered corpus documents at dist/og/research/. A
// flat readdir here saw eighteen of sixty-four and reported all clear on the rest.
async function cards(root) {
  const found = []
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const path = join(root, entry.name)
    if (entry.isDirectory()) found.push(...(await cards(path)))
    else if (/\.(png|jpe?g|webp)$/i.test(entry.name)) found.push(path)
  }
  return found
}

let images
try {
  images = await cards(dir)
} catch {
  console.error(`no social cards found at ${dir}; did the build run?`)
  process.exit(1)
}

if (images.length === 0) {
  console.error(`no social cards found at ${dir}; did the build run?`)
  process.exit(1)
}

const oversized = []
for (const name of images) {
  const { size } = await stat(name)
  if (size > MAX_BYTES) oversized.push([name, size])
}

if (oversized.length > 0) {
  console.error(`social cards over the ${MAX_BYTES.toLocaleString()}-byte Bluesky cap:`)
  for (const [name, size] of oversized) console.error(`  ${name}  ${size.toLocaleString()} bytes`)
  process.exit(1)
}

console.log(`${images.length} social card(s), all under the ${MAX_BYTES.toLocaleString()}-byte cap`)
