# Deploying the site

The build runs in CI and publishes into the S3 bucket that already sits behind
`kellyportfolios.com`. **No DNS record changes.** `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` are already repository secrets, so there is nothing to create.

`as of 2026-08-23`.

## What is live now

`kellyportfolios.com` is served by CloudFront in front of an S3 bucket. That bundle was
written on 2025-10-10 and cannot be rebuilt from a clone: `sst.config.ts` imports
`./infra/*` and deploys handlers from `functions/`, and neither directory has ever been
committed in any ref. The workflow that ran it, `deploy-prod.yaml`, has been deleted
because it could only ever fail.

What replaces it is [`deploy.yml`](../.github/workflows/deploy.yml), which builds the
static bundle and syncs it into the same bucket. Because the distribution and the DNS
records are untouched, there is no cutover and no propagation window.

## Run the discovery job first

The previous site was a single-page application, and two of its likely CloudFront
settings would break this build **quietly**. Find out before publishing:

`Actions` → `Deploy` → `Run workflow`, leave **dry run** ticked, run it.

It changes nothing. It prints the distribution id, the bucket, the origin type, and any
custom error responses into the run summary.

### If it reports `Resolves directory indexes: false`

The distribution uses a REST origin (`bucket.s3.amazonaws.com`) rather than the website
endpoint (`bucket.s3-website-us-east-1.amazonaws.com`). A REST origin serves the default
root object at `/` and nothing at any other directory, so every page except the home page
would 404. The `publish` job refuses to run in this state rather than half-publishing.

Two ways out, either is fine:

- **Point the origin at the website endpoint.** Enable static website hosting on the
  bucket with `index.html` as the index document, then change the distribution's origin
  domain to the website endpoint. Note that a website endpoint is HTTP-only, so the
  origin protocol policy has to be `http-only`.
- **Attach a CloudFront Function** on viewer request:

  ```js
  function handler(event) {
    var request = event.request;
    if (request.uri.endsWith('/')) request.uri += 'index.html';
    else if (!request.uri.includes('.')) request.uri += '/index.html';
    return request;
  }
  ```

### If it reports a custom error response mapping 404 or 403 to `/index.html`

That is the single-page-application fallback, and it must be removed. Against this build
it serves the **home page** for every URL that does not exist, with a 200 status. A typo
looks like a working page, and search engines index a copy of the home page under every
wrong URL. Delete the error response in the distribution's Error Pages tab.

The final step of the deploy checks for exactly this by requesting a URL that cannot
exist and failing if it returns 200.

## Publish

Once discovery is clean, either push to `main`, or run the workflow again with **dry run
unticked**.

The sync runs in two passes on purpose. Fingerprinted assets go first with a one-year
immutable cache; HTML, the sitemap and the search index go second with
`must-revalidate`, so a reader never receives a new document that references an asset
which has not landed. Then the whole distribution is invalidated and the job waits for it
to complete before checking six live URLs.

## Verifying

```sh
curl -sI https://kellyportfolios.com/ | head -5
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/stacking/
curl -so /dev/null -w '%{http_code}\n' https://kellyportfolios.com/no-such-page/   # must be 404
```

## The trailing slash

The build emits one URL form: `trailingSlash: "always"` with directory format, so every
page is written as `<route>/index.html` and every internal link carries the slash. The
setting does not redirect — on a static build it governs the dev server only, and the host
decides whether `/start` is a redirect to `/start/` or a second copy of the page. Two
indexed URLs for one document is the failure being avoided. An S3 website endpoint issues
the redirect on its own; a CloudFront Function can do it if the origin changes.

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
