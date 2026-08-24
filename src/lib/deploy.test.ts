import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * A direct load of `/portfolios/candidate` has to return the app, not the host's 404.
 *
 * Two mechanisms cover it and both are one line long, which is exactly how they get
 * deleted by accident: a `404.html` copy of the entry document for hosts that serve their
 * error document for an unknown key, and CloudFront's `errorPage` for the intended target.
 *
 * This guards the client-routed app only, which `build:legacy` now produces. The Astro
 * build writes a real `index.html` per route, so no unknown key is ever a known page and
 * the fallback answers a question that build does not ask.
 */
describe("single-page routing survives a refresh", () => {
  const root = process.cwd();

  it("copies the entry document to 404.html as part of the legacy build", () => {
    const scripts = JSON.parse(readFileSync(path.join(root, "package.json"), "utf8")).scripts;
    expect(scripts["build:legacy"]).toContain("spa-fallback");
    expect(readFileSync(path.join(root, "scripts/spa-fallback.mjs"), "utf8")).toContain("404.html");
  });

  it("tells CloudFront to serve the app for an unknown key", () => {
    expect(readFileSync(path.join(root, "sst.config.ts"), "utf8")).toContain('errorPage: "index.html"');
  });
});
