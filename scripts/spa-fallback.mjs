// Copies the built index.html to 404.html.
//
// The client uses real paths, so any static host that serves a bucket's 404 document
// for an unknown key — GitHub Pages, S3 website hosting, most CDNs without an explicit
// error-page rewrite — would return "not found" for `/portfolios/candidate` on a direct
// load or a refresh. A 404.html that is the app makes the router take over instead.
// SST's `errorPage` covers the same case on CloudFront; this covers everywhere else.

import { copyFile } from "node:fs/promises";
import path from "node:path";

const dist = path.resolve(import.meta.dirname, "..", process.argv[2] ?? "dist");
await copyFile(path.join(dist, "index.html"), path.join(dist, "404.html"));
process.stdout.write(`wrote ${path.relative(process.cwd(), path.join(dist, "404.html"))}\n`);
