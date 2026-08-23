# Deploying the site

The build runs in CI and produces a static bundle. Nothing between here and a live
`kellyportfolios.com` needs an AWS credential, a Cloudflare account or a secret in the
repository. It does need four actions in a browser that only the domain's owner can take,
and they are listed below in the order they must happen.

`as of 2026-08-23`.

## What is live now, and what replaces it

`kellyportfolios.com` is served by CloudFront in front of an S3 bucket. That bundle was
last written on 2025-10-10 and cannot be rebuilt from a clone: `sst.config.ts` imports
`./infra/*` and deploys handlers from `functions/`, and neither directory has ever been
committed in any ref. So the deployment currently in production is unreproducible, and
replacing it costs nothing that presently works.

The replacement is GitHub Pages, driven by
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml). The comment at the top
of that file records why Pages rather than Cloudflare; the short version is that Route 53
has no CNAME flattening, so a third-party host reaches the apex only through fixed A
records, and Cloudflare Pages publishes none.

## Step 1. Turn Pages on

In the repository, `Settings`, then `Pages`, then `Build and deployment`, then `Source`, choose
`GitHub Actions`. Do not choose "Deploy from a branch"; the workflow uploads an artifact
and that source setting would ignore it.

Nothing else on that screen matters yet. Leave the custom domain blank until step 3.

## Step 2. Let the workflow run once

Push to `main`, or run `Actions`, then `Deploy`, then `Run workflow`. The first run creates the
`github-pages` environment and publishes to `https://flanaganse.github.io/kelly-portfolios/`.

Open that URL and confirm the page renders before touching DNS. If the CSS is missing, the
`site` value in `astro.config.mjs` and the repository subpath disagree; that resolves
itself at step 3, when the site moves to the apex and the subpath disappears.

## Step 3. Claim the custom domain

`Settings`, then `Pages`, then `Custom domain`, enter `kellyportfolios.com`, and save. GitHub will
report that the DNS check is pending, which is expected until step 4 finishes.

`public/CNAME` already contains `kellyportfolios.com` and is copied into every build, so
the domain survives each deployment. Do not delete it.

## Step 4. The Route 53 records

In the Route 53 hosted zone for `kellyportfolios.com`:

Delete the existing apex `A` ALIAS record pointing at the CloudFront distribution. Note
the distribution's domain name first, so the old deployment can be restored if needed.

Create an `A` record for the apex, TTL 300, with these four values:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

Create an `AAAA` record for the apex, TTL 300, with these four values:

```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

Create a `CNAME` record for `www.kellyportfolios.com`, TTL 300, value
`flanaganse.github.io.`, and the trailing dot matters. `www` does not resolve today; adding it
means a reader who types it lands on the site instead of a DNS error, and GitHub redirects
it to the apex on its own.

Those addresses are GitHub's published set for apex domains. Confirm them against
[GitHub's current documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
before creating the records; they change rarely, and a stale list here would be silent.

## Step 5. Force HTTPS

Return to `Settings`, then `Pages`. Once the DNS check passes, tick `Enforce HTTPS`. The
certificate is issued by Let's Encrypt and usually appears within an hour of the records
propagating. The tick box stays greyed out until then.

## Verifying

```sh
dig +short kellyportfolios.com A
dig +short www.kellyportfolios.com CNAME
curl -sI https://kellyportfolios.com | head -20
```

The apex should answer with the four `185.199.x.153` addresses, and the response headers
should carry `server: GitHub.com` rather than `server: AmazonS3`.

## Rolling back

The CloudFront distribution and its S3 bucket are untouched by any of this. Restoring the
old site means recreating the apex ALIAS record that step 4 deleted. Nothing else changes,
and the GitHub Pages deployment can be left running in parallel at its `github.io` address.

## Building it yourself

```sh
pnpm install
pnpm build      # astro build, then pagefind indexes dist/
pnpm preview    # serves dist/ on http://localhost:4321
```

`pnpm build:legacy` still builds the old client-routed application into `dist-legacy/`.
It is kept as a reference while pages are ported and is not deployed anywhere.
