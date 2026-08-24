# Deploying the site

The build runs in CI and publishes into the S3 bucket that already sits behind
`kellyportfolios.com`. **No DNS record changes.** `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` are already repository secrets, so there is nothing to create.

`as of 2026-08-24`.

## What is live now

`kellyportfolios.com` is served by CloudFront in front of an S3 bucket. That bundle was
written on 2025-10-10 and cannot be rebuilt from a clone: `sst.config.ts` imports
`./infra/*` and deploys handlers from `functions/`, and neither directory has ever been
committed in any ref. The workflow that ran it, `deploy-prod.yaml`, has been deleted
because it could only ever fail.

What replaces it is [`deploy.yml`](../.github/workflows/deploy.yml), which builds the
static bundle and syncs it into the same bucket. Because the distribution and the DNS
records are untouched, there is no cutover and no propagation window.

## The distribution has to be reconfigured once

SST built that distribution for a single-page client, and it is configured for one. Three
things follow from that, and all three fail quietly rather than loudly, which is worse.
The first was found by a deploy that failed on 2026-08-24; the other two are visible in
`sst.config.ts` and in the responses the live site gives.

**`placeholder.sst.dev` sits first in the origin list.** It is not the origin serving the
site — the default cache behaviour targets the bucket — but a deploy that reads
`Origins.Items[0]`, as the first version of this workflow did, derives the bucket name
`placeholder.sst.dev` and syncs an entire site into a bucket that does not exist.
[`scripts/cloudfront/state.sh`](../scripts/cloudfront/state.sh) now reads the origin that
the default cache behaviour targets, which is the one that answers a request.

**The origin is a REST origin** (`bucket.s3.region.amazonaws.com`), not the S3 website
endpoint. The REST API resolves keys, not directories, and CloudFront's default root
object applies to `/` and to no other directory, so `/start/` — the key `start/` — misses.
Every page except the home page would 404.

**`errorPage: "index.html"`** in `sst.config.ts` is a custom error response mapping 403
and 404 to `/index.html` with a status of 200. The old client needed it: its routes were
real paths and a refresh had to reach the app. Against a directory-format build it answers
every wrong URL with the *home page* and a success status, so a typo looks like a working
page and a crawler indexes a copy of the home page under each one. Today
`https://kellyportfolios.com/no-such-page/` returns 200 with the home page's ETag.

`publish` refuses to upload while the last two hold, rather than half-publishing.

### Fixing it

`Actions` → `Configure distribution` → `Run workflow`. Leave **apply** unticked for a dry
run: it writes nothing and prints the diff it would apply. Then run it again with **apply**
ticked. It takes a few minutes, most of that waiting for the distribution to deploy.

It makes two changes, both idempotent, neither touching the bucket, the certificate, the
aliases, or any DNS record:

1. Publishes [`directory-index.js`](../scripts/cloudfront/directory-index.js) as a
   CloudFront Function and attaches it to the default cache behaviour on viewer request.
   `/start/` becomes the key `start/index.html`, and `/start` redirects to `/start/` so
   there is one URL form rather than two copies of a page. Skipped if the origin is ever
   moved to a website endpoint, which resolves directory indexes on its own.
2. Replaces the error responses that map 403 and 404 to `/index.html` with ones that serve
   `/404.html` — the build emits it — with a status of 404. Both codes, because a REST
   origin behind an origin access control answers a missing key with 403: the bucket
   policy grants `GetObject` and not `ListBucket`.

The alternative to the function is to enable static website hosting on the bucket and
point the origin at the website endpoint. It resolves directory indexes and the slashless
redirect itself, but it is HTTP-only and needs a public bucket, which is a worse trade
than eighteen lines of JavaScript.

**Order matters, slightly.** Configure first, then deploy. In between — a few minutes —
the old single-page client is still in the bucket and its deep links have lost the
fallback that made them work, so they answer 404 until the new build lands. The home page
is unaffected. Deploying first instead would leave every URL answering with the *new* home
page and a 200, which is the worse of the two windows.

The IAM user needs `cloudfront:GetDistributionConfig`, `UpdateDistribution`,
`CreateFunction`, `UpdateFunction`, `DescribeFunction` and `PublishFunction`. If it does
not have them the workflow says so and changes nothing.

## Publish

Once `Configure distribution` reports **Ready to publish: true**, either push to `main`,
or run `Deploy` with **dry run** unticked.

The sync runs in two passes on purpose. Fingerprinted assets go first with a one-year
immutable cache; HTML, the sitemap and the search index go second with
`must-revalidate`, so a reader never receives a new document that references an asset
which has not landed. Then the whole distribution is invalidated and the job waits for it
to complete before checking eighteen live URLs, one from each family that has its own
route generator, plus a URL that cannot exist.

## Reading the state without changing it

The `discover` job on `Deploy` reports the distribution, the origin actually serving the
site, every origin on it, the error responses, and whether the thing is publishable. It
changes nothing. With credentials in the environment it also runs locally:

```sh
SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/state.sh | jq .
```

## Verifying

```sh
curl -sI https://kellyportfolios.com/ | head -5
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/stacking/
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/no-such-page/   # must be 404
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/stacking        # must be 301
```

## The trailing slash

The build emits one URL form: `trailingSlash: "always"` with directory format, so every
page is written as `<route>/index.html` and every internal link carries the slash. The
setting does not redirect — on a static build it governs the dev server only, and the host
decides whether `/start` is a redirect to `/start/` or a second copy of the page. Two
indexed URLs for one document is the failure being avoided, and the CloudFront Function
above is what prevents it: it redirects the slashless form rather than serving it.

## Rolling back

The bucket is versioned only if it was configured that way, so the reliable rollback is to
check out the previous commit and re-run the workflow. The distribution, its settings and
every DNS record are untouched by any deploy, so nothing outside the bucket needs undoing.

## Building it yourself

```sh
pnpm install
pnpm build      # astro build, then pagefind indexes dist/
pnpm preview    # serves dist/ on http://localhost:4321
```

`pnpm build:legacy` still builds the old client-routed application into `dist-legacy/`.
It is kept as a reference while pages are ported and is deployed nowhere.
