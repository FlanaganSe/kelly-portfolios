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

## How the site is actually served

Worth knowing before changing anything, because none of it is in this repository and two
plausible readings of the distribution are both wrong.

There is one distribution, `E2UXACC7VKS53Z`, and Route 53 points the domain at it. It has
a single origin, `placeholder.sst.dev`, which answers nothing, and — until 2026-08-24 —
no custom error responses at all. That is not a broken distribution. SST's design decides
the origin *per request*, inside a viewer-request CloudFront Function that calls
`cf.updateRequestOrigin`, so the function is the entire routing behaviour of the site and
the origin list is a formality. [`scripts/cloudfront/dump.sh`](../scripts/cloudfront/dump.sh)
prints the whole arrangement — the distribution, the function's source, the key-value
store it reads, and the buckets in the account.

The function SST installed resolves a path by looking it up in a CloudFront key-value
store holding one key per file in the bucket, and rewrites anything it cannot find to
`/index.html`. The store holds five keys, which was the whole of the old client-routed
bundle. Two consequences:

- **Every wrong URL answers with the home page and a 200.** Today
  `https://kellyportfolios.com/no-such-page/` returns the home page's own ETag. Against a
  build of thirty-odd pages that means a typo looks like a working page and a crawler
  indexes a copy of the home page under each one.
- **A file that is not in the store is not served**, so `aws s3 sync` alone would publish a
  site that still answers every URL with the old home page. Keeping a key-value store in
  step with several hundred built files on every deploy is a moving part with no purpose:
  `<route>/index.html` is derivable from the URL.

Two traps follow from the same design, and both cost a failed deploy on 2026-08-24:

- `Origins.Items[0]` is `placeholder.sst.dev`. A deploy that derives the bucket from it —
  the first version of this workflow did — syncs an entire site into a bucket of that name.
- The bucket is named nowhere in the distribution. It is a literal inside the function, and
  that is where [`state.sh`](../scripts/cloudfront/state.sh) reads it back from, so the
  deploy syncs into the bucket the function actually serves from rather than one the
  repository merely believes in.

Finding the distribution has its own trap: the first one whose aliases mention the domain
is not necessarily the one serving it. Route 53's alias record is followed instead, and the
alias match survives only as a fallback for a key without Route 53 permission.

## Reconfiguring it, once

`Actions` → `Configure distribution` → `Run workflow`. Leave **apply** unticked for a dry
run: it prints the state, the function being replaced, and the diff it would apply, and
writes nothing. Then run it again with **apply** ticked. It takes a few minutes, most of
that waiting for the distribution to deploy.

Two changes, both idempotent, neither touching the bucket, the certificate, the aliases, or
any DNS record:

1. [`directory-index.js`](../scripts/cloudfront/directory-index.js) replaces SST's
   function. It derives `<route>/index.html` from the URL, redirects `/start` to `/start/`
   so one document has one URL rather than two, and points the request at the bucket with
   the same signed origin-access-control configuration SST used. Because that function is
   the whole behaviour of the site, `repair.sh` runs it against CloudFront's own
   `test-function` harness — six paths, including the redirect and a hashed asset — and
   refuses to publish it if any answer is wrong.
2. 403 and 404 from the origin become `/404.html` with a status of 404. The build emits
   that page. Both codes, because the bucket is read through an origin access control whose
   policy grants `GetObject` and not `ListBucket`, so a missing key comes back as 403.

SST's function and its key-value store are left in place, unattached and unread. Nothing
that could deploy them exists any more, and deleting them gains nothing.

**Order matters, slightly.** Configure first, then deploy. In between — a few minutes — the
old single-page client is still in the bucket and has lost the fallback that made its deep
links work, so they answer 404 until the new build lands. The home page is unaffected.
Deploying first instead would leave every URL answering with the *new* home page and a 200,
which is the worse of the two windows.

The IAM user needs `cloudfront:GetDistributionConfig`, `UpdateDistribution`,
`CreateFunction`, `UpdateFunction`, `DescribeFunction`, `GetFunction`, `TestFunction` and
`PublishFunction`, and `route53:ListHostedZonesByName` and `ListResourceRecordSets` for the
lookup above. If it does not have them the workflow says so and changes nothing.

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

The `discover` job on `Deploy` reports which distribution serves the domain and how it was
found, which function is attached, which bucket that function serves from, whether a miss
answers 404, and whether the thing is publishable. It changes nothing. With credentials in
the environment both scripts also run locally:

```sh
SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/state.sh | jq .
SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/dump.sh
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
