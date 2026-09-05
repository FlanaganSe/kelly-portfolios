#!/usr/bin/env node
// Screenshot every page of the built site at a desktop and a mobile width.
//
//   pnpm shots [--dark] [--full]
//
// Builds, lists every `dist/**/index.html` that is a page rather than a redirect stub,
// serves `dist/` from a small in-process static server on a spare port, and runs
// `scripts/screenshot.mjs` over the list. The PNGs land in `shots/` (gitignored).
// Needs a browser once: `pnpm exec playwright install chromium`.
//
// The server is here rather than `astro preview` because Astro 7 runs preview as a
// managed background daemon when it detects an agent environment, ignores `--port`
// if one is already up, and refuses `--ignore-lock` in that case. Twenty lines of
// `node:http` have none of those opinions.

import { spawn, spawnSync } from "node:child_process";
import { createReadStream, existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = join(root, "dist");
const outDir = join(root, "shots");
const flags = process.argv.slice(2).filter((a) => a.startsWith("--"));

const built = spawnSync("pnpm", ["build"], { cwd: root, stdio: "inherit" });
if (built.status !== 0) process.exit(built.status ?? 1);

function pages(dir, found = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) pages(path, found);
    else if (name === "index.html") found.push(path);
  }
  return found;
}

// A redirect stub is a page whose only content is a meta refresh; nobody looks at those.
const routes = pages(dist)
  .filter((file) => !readFileSync(file, "utf8").includes('http-equiv="refresh"'))
  .map((file) => `${file.slice(dist.length, -"index.html".length)}`)
  .sort();

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".wasm": "application/wasm",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".xml": "application/xml",
  ".txt": "text/plain",
  ".pf_meta": "application/octet-stream",
  ".pf_index": "application/octet-stream",
  ".pf_fragment": "application/octet-stream",
};

const server = createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url ?? "/", "http://x").pathname);
  const candidates = pathname.endsWith("/") ? [`${pathname}index.html`] : [pathname, `${pathname}/index.html`];
  const hit = candidates
    .map((c) => join(dist, c))
    .find((f) => f.startsWith(dist) && existsSync(f) && statSync(f).isFile());
  if (!hit) {
    res.writeHead(404, { "content-type": "text/html; charset=utf-8" });
    createReadStream(join(dist, "404.html"))
      .on("error", () => res.end())
      .pipe(res);
    return;
  }
  res.writeHead(200, { "content-type": types[extname(hit)] ?? "application/octet-stream" });
  createReadStream(hit).pipe(res);
});

await new Promise((ready) => server.listen(0, "127.0.0.1", ready));
const { port } = server.address();

// Spawned asynchronously: the server above lives in this process, and a synchronous
// spawn would block the event loop it answers from.
const shot = spawn(
  process.execPath,
  [join(root, "scripts/screenshot.mjs"), `http://127.0.0.1:${port}`, outDir, routes.join(","), ...flags],
  { cwd: root, stdio: "inherit" }
);
const status = await new Promise((done) => shot.on("exit", (code) => done(code ?? 1)));
server.close();
process.exit(status);
