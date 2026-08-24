import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const root = process.cwd();
const read = (file: string) => readFileSync(path.join(root, file), "utf8");

/**
 * A direct load of `/portfolios/candidate` has to return the app, not the host's 404.
 *
 * The mechanism is one line long, which is exactly how it gets deleted by accident: a
 * `404.html` copy of the entry document, for hosts that serve their error document for an
 * unknown key.
 *
 * This guards the client-routed app only, which `build:legacy` now produces and which is
 * deployed nowhere. The Astro build writes a real `index.html` per route, so no unknown key
 * is ever a known page, and the same fallback against it would answer every wrong URL with
 * the home page and a 200. `sst.config.ts` still asks CloudFront for exactly that, with
 * `errorPage: "index.html"`; it cannot run — `./infra/*` has never been committed — and
 * `scripts/cloudfront/repair.sh` is what undoes it on the live distribution.
 */
describe("single-page routing survives a refresh", () => {
  it("copies the entry document to 404.html as part of the legacy build", () => {
    const scripts = JSON.parse(read("package.json")).scripts;
    expect(scripts["build:legacy"]).toContain("spa-fallback");
    expect(read("scripts/spa-fallback.mjs")).toContain("404.html");
  });
});

/**
 * The viewer-request function decides what every URL on the site means and which origin
 * answers it — the distribution's own origin is a placeholder that serves nothing — and it
 * runs somewhere no test can reach. So it is exercised here as the bytes that get
 * published, and again by `repair.sh` against CloudFront's own harness before anything
 * points at it.
 */
describe("the CloudFront function serves a directory-format build", () => {
  type QueryValue = { value: string; multiValue?: { value: string }[] };
  type Request = { uri: string; querystring: Record<string, QueryValue>; headers: Record<string, unknown> };
  type Redirect = { statusCode: number; headers: { location: { value: string } } };
  type Handler = (event: { request: Request }) => Request | Redirect;
  type Origin = { domainName: string; originAccessControlConfig: { enabled: boolean; originType: string } };

  const source = read("scripts/cloudfront/directory-index.js");
  const origins: Origin[] = [];
  // The `cloudfront` module is only importable inside CloudFront, so it arrives as an
  // argument instead; nothing else about the source is changed.
  const build = new Function("cf", `${source.replace(/^import[^\n]*\n/m, "")}\nreturn handler;`);
  const handler = build({ updateRequestOrigin: (origin: Origin) => origins.push(origin) }) as Handler;

  const request = (uri: string, querystring: Record<string, QueryValue> = {}) => {
    origins.length = 0;
    return handler({ request: { uri, querystring, headers: {} } });
  };

  it("resolves a directory to its index document", () => {
    expect(request("/")).toMatchObject({ uri: "/index.html" });
    expect(request("/start/")).toMatchObject({ uri: "/start/index.html" });
    expect(request("/research/decisions/0004-no-sleeve-promoted/")).toMatchObject({
      uri: "/research/decisions/0004-no-sleeve-promoted/index.html",
    });
  });

  it("redirects the slashless form rather than serving a second copy of the page", () => {
    expect(request("/start")).toEqual({
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { location: { value: "/start/" } },
    });
    expect(origins).toEqual([]);
  });

  it("keeps the query string across that redirect", () => {
    expect(request("/tools/how-long", { years: { value: "20" }, print: { value: "" } })).toMatchObject({
      headers: { location: { value: "/tools/how-long/?years=20&print" } },
    });
    expect(request("/funds", { tag: { value: "a", multiValue: [{ value: "a" }, { value: "b" }] } })).toMatchObject({
      headers: { location: { value: "/funds/?tag=a&tag=b" } },
    });
  });

  it("passes a file through untouched", () => {
    expect(request("/robots.txt")).toMatchObject({ uri: "/robots.txt" });
    expect(request("/_astro/page.CH4nk3d.js")).toMatchObject({ uri: "/_astro/page.CH4nk3d.js" });
    expect(request("/og/funds.png")).toMatchObject({ uri: "/og/funds.png" });
  });

  it("points the request at the bucket, signed, on every path that reaches an origin", () => {
    for (const uri of ["/", "/start/", "/robots.txt"]) {
      request(uri);
      expect(origins).toEqual([
        {
          domainName: expect.stringMatching(/^[a-z0-9.-]+\.s3\.[a-z0-9-]+\.amazonaws\.com$/),
          originAccessControlConfig: {
            enabled: true,
            signingBehavior: "always",
            signingProtocol: "sigv4",
            originType: "s3",
          },
        },
      ]);
    }
  });
});

/**
 * The deploy refuses rather than half-publishing, and what it refuses on is easy to
 * loosen by accident, since the distribution it checks is edited by hand.
 */
describe("the deploy will not publish into a distribution configured for the old client", () => {
  it("gates the upload on the discovered state", () => {
    expect(read(".github/workflows/deploy.yml")).toContain("needs.discover.outputs.ready != 'true'");
  });

  it("follows Route 53 to the distribution rather than an alias or an origin list", () => {
    const state = read("scripts/cloudfront/state.sh");
    expect(state).toContain("list-resource-record-sets");
    // And says which of the two it used, because the fallback picks a different answer.
    expect(state).toContain("selected_by");
  });

  it("takes the bucket from the published function, which is the only place it is named", () => {
    expect(read("scripts/cloudfront/state.sh")).toContain('get-function --name "$ours" --stage LIVE');
  });

  it("serves the built 404 page with a 404, not the home page with a 200", () => {
    const repair = read("scripts/cloudfront/repair.sh");
    expect(repair).toContain('ResponsePagePath: "/404.html", ResponseCode: "404"');
    expect(repair).not.toContain('ResponsePagePath: "/index.html"');
  });

  it("tests the function against CloudFront before publishing it", () => {
    const repair = read("scripts/cloudfront/repair.sh");
    expect(repair).toContain("test-function");
    expect(repair.indexOf("test-function")).toBeLessThan(repair.indexOf("publish-function"));
  });
});
