#!/bin/sh
# PostToolUse(Edit|Write): apply Biome to the file just written, so formatting and
# safe lint fixes never reach `pnpm biome check` at handoff.
#
# Node parses the hook payload because jq is not guaranteed to be installed, and
# the Biome binary is resolved from node_modules because hooks run in a
# non-login shell where pnpm may not be on PATH.
set -e

root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
biome="$root/node_modules/.bin/biome"
[ -x "$biome" ] || exit 0

file=$(node -e '
let raw = "";
process.stdin.on("data", (c) => { raw += c; });
process.stdin.on("end", () => {
  try {
    process.stdout.write(JSON.parse(raw)?.tool_input?.file_path ?? "");
  } catch {
    process.stdout.write("");
  }
});
')

case "$file" in
  *.ts | *.tsx | *.js | *.jsx | *.json | *.jsonc) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

# Never fail the turn over formatting; `pnpm biome check` remains the real gate.
"$biome" check --write --no-errors-on-unmatched "$file" >/dev/null 2>&1 || true
exit 0
