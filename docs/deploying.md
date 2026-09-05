# Deploying the site

The build runs in CI and publishes into the S3 bucket that already sits behind
`kellyportfolios.com`. **No DNS record changes.** `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` are already repository secrets, so there is nothing to create.

`as of 2026-08-24`.

## What is live now

`kellyportfolios.com` is served by CloudFront in front of an S3 bucket. SST created both
on 2025-10-10, from an `sst.config.ts` that imported `./infra/*` and `functions/`, and
neither directory was ever committed in any ref. The config, the `sst` and `@pulumi/aws`
packages, and the `deploy-prod.yaml` workflow that ran it have all been removed: none of
them could run from a clone. Nothing declarative describes the distribution now; if it is
ever deleted, the recovery path is this document and the console.

What replaces it is [`deploy.yml`](../.github/workflows/deploy.yml), which builds the
static bundle and syncs it into the same bucket. Because the distribution and the DNS
records are untouched, there is no cutover and no propagation window.

## How the site is actually served

Worth knowing before changing anything, because none of it is in this repository and two
plausible readings of the distribution are both wrong.

There is one distribution, `E2UXACC7VKS53Z`, and Route 53 points the domain at it. Until
2026-08-24 it had a single origin, `placeholder.sst.dev`, which answers nothing, and no
custom error responses. That was not broken. SST's design decides the origin *per
request*, inside a viewer-request CloudFront Function that calls `cf.updateRequestOrigin`,
so the function was the entire routing behaviour of the site and the origin list was a
formality. [`scripts/cloudfront/dump.sh`](../scripts/cloudfront/dump.sh) prints the whole
arrangement — the distribution, the function's source, the key-value store it reads, the
bucket policy, and the buckets in the account.

The function SST installed resolves a path by looking it up in a CloudFront key-value
store holding one key per file in the bucket, and rewrites anything it cannot find to
`/index.html`. The store held five keys, which was the whole of the old client-routed
bundle. Two consequences:

- **Every wrong URL answered with the home page and a 200**, so a typo looked like a
  working page and a crawler would index a copy of the home page under each one.
- **A file that is not in the store is not served**, so `aws s3 sync` alone would have
  published a site that still answered every URL with the old home page. Keeping a
  key-value store in step with several hundred built files on every deploy is a moving
  part with no purpose: `<route>/index.html` is derivable from the URL.

A third consequence only shows up once you try to fix the second. A custom error response
is fetched with the cache behaviour's **own** origin — the viewer-request function does not
run for it — so with only a placeholder origin a miss came back 502 rather than
`/404.html`. That is why the repair gives the distribution a real S3 origin instead of
leaving the choice to the function.

Two more traps, both of which cost a failed deploy:

- `Origins.Items[0]` was `placeholder.sst.dev`. A deploy that derives the bucket from it —
  the first version of this workflow did — syncs an entire site into a bucket of that name.
- The bucket was named nowhere in the distribution, only inside the function. It now has
  one canonical home, [`scripts/cloudfront/site.env`](../scripts/cloudfront/site.env), and
  the deploy refuses to upload unless the distribution serves from exactly that bucket.

Finding the distribution has its own trap: the first one whose aliases mention the domain
is not necessarily the one serving it. Route 53's alias record is followed instead, and the
alias match survives only as a fallback for a key without Route 53 permission.

## Reconfiguring it, once

`Actions` → `Configure distribution` → `Run workflow`. Leave **apply** unticked for a dry
run: it prints the state, the function being replaced, the bucket policy, and the diff it
would apply, and writes nothing. Then run it again with **apply** ticked. It takes a few
minutes, most of that waiting for the distribution to deploy.

Three changes, all idempotent, none of them touching the bucket's contents, its policy,
the certificate, the aliases, or any DNS record:

1. **A real origin.** The bucket becomes an actual origin, read through a new origin
   access control named `kellyportfolios-site`, and the default behaviour points at it.
   The bucket policy already allows `cloudfront.amazonaws.com` to `GetObject` without
   naming a distribution, so nothing about the policy has to change. The placeholder
   origin is removed once nothing references it.
2. **Honest misses.** 403 and 404 from that origin become `/404.html` with a status of
   404. The build emits that page. Both codes, because the policy grants `GetObject` and
   not `ListBucket`, so a missing key is a 403.
3. **[`directory-index.js`](../scripts/cloudfront/directory-index.js) replaces SST's
   function.** It derives `<route>/index.html` from the URL and redirects `/start` to
   `/start/` so one document has one URL rather than two. Because a function is the whole
   behaviour of the site, `repair.sh` runs it against CloudFront's own `test-function`
   harness — seven paths, including the redirect, a hashed asset and a query string — and
   refuses to publish it if any answer is wrong. That harness is what caught `for...of`
   being absent from the `cloudfront-js-2.0` runtime.

The order inside the run matters: the distribution is fixed first and the function's code
is published last, because the function that is attached at the start may be the one
choosing the origin, and publishing new code under it first would take the site down for
the minutes the distribution takes to deploy.

SST's function and its key-value store are left in place, unattached and unread. Nothing
that could deploy them exists any more, and deleting them gains nothing.

**Order between the two workflows matters too.** Configure first, then deploy. In between
— a few minutes — the old bundle is still in the bucket and has lost the fallback that made
its deep links work, so they answer 404 until the new build lands. The home page is
unaffected. Deploying first instead would leave every URL answering with the *new* home
page and a 200, which is the worse of the two windows.

The IAM user needs `cloudfront:GetDistributionConfig`, `UpdateDistribution`,
`CreateOriginAccessControl`, `ListOriginAccessControls`, `CreateFunction`,
`UpdateFunction`, `DescribeFunction`, `GetFunction`, `TestFunction` and `PublishFunction`,
plus `route53:ListHostedZonesByName` and `ListResourceRecordSets` for the lookup above. If
it does not have them the workflow says so and changes nothing.

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

## `www` does not resolve

`as of 2026-08-24`. The distribution lists `www.kellyportfolios.com` as an alias and the
certificate covers it, but **Route 53 holds no record for it**, so the name fails to
resolve rather than redirecting. Nothing in either workflow checks `www`, which is why it
survived the repair above unnoticed.

The fix is one record in the hosted zone: an A record for `www` aliased to the same
distribution, or a redirect to the apex. The IAM user the workflows use has
`ListResourceRecordSets` but not `ChangeResourceRecordSets`, so this cannot be automated
with the current key and has to be done in the console.

## Verifying

```sh
curl -sI https://kellyportfolios.com/ | head -5
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/strategies/
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/no-such-page/   # must be 404
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/stacking        # must be 301
```

## The trailing slash

The build emits one URL form: `trailingSlash: "always"` with directory format, so every
page is written as `<route>/index.html` and every internal link carries the slash. The
setting does not redirect — on a static build it governs the dev server only, and the host
decides whether `/evidence` is a redirect to `/evidence/` or a second copy of the page. Two
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
