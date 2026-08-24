#!/usr/bin/env bash
#
# Makes the distribution able to serve a directory-format static build.
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh           # prints the diff
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh --apply   # writes it
#
# Two changes, both on the distribution `scripts/cloudfront/state.sh` finds:
#
#   1. `directory-index.js` is published and attached to the default cache behaviour on
#      viewer request, so `/start/` reaches the key `start/index.html` and `/start`
#      redirects to `/start/`. Skipped when the origin is an S3 website endpoint, which
#      resolves directory indexes itself.
#
#   2. The custom error responses that map 403 and 404 to `/index.html` with a 200 —
#      SST's `errorPage: "index.html"`, which the old single-page client needed — are
#      replaced by ones that serve `/404.html` with a 404. The build emits that page.
#
# Both are idempotent: running it twice changes nothing the second time. Nothing here
# touches the bucket, the certificate, the aliases, or any DNS record, so a reader
# sees the current site throughout and the only visible effect is that URLs which used
# to answer with the home page start answering honestly.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
apply=false
if [ "${1:-}" = "--apply" ]; then apply=true; fi

name="kellyportfolios-directory-index"
comment="Directory indexes and one trailing-slash form for a static build"

state=$(GITHUB_OUTPUT="" GITHUB_STEP_SUMMARY="" SITE_DOMAIN="${SITE_DOMAIN:?SITE_DOMAIN is not set}" "$here/state.sh")
id=$(jq -r .distribution_id <<<"$state")
kind=$(jq -r .origin_kind <<<"$state")
origin=$(jq -r .origin_domain <<<"$state")

echo "distribution $id, serving from $origin ($kind)"

if [ "$kind" = "foreign" ]; then
  {
    echo "::error::The default cache behaviour points at ${origin}, which is not a bucket."
    echo "Origins on this distribution:"
    jq -r '.all_origins[] | "  \(.domain)  (\(.id))"' <<<"$state"
    echo "Repointing a live behaviour is not a guess worth automating. Pick the bucket"
    echo "origin in the console, or add one, and run this again. See docs/deploying.md."
  } >&2
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# ---------------------------------------------------------------------------
# The function.
# ---------------------------------------------------------------------------
arn=""
if [ "$kind" = "website" ]; then
  echo "website endpoint: it resolves directory indexes itself, no function needed"
else
  etag=$(aws cloudfront describe-function --name "$name" --query ETag --output text 2>/dev/null || true)
  if [ -z "$etag" ] || [ "$etag" = "None" ]; then
    echo "function $name: does not exist, will create"
    if $apply; then
      etag=$(aws cloudfront create-function --name "$name" \
        --function-config "Comment=$comment,Runtime=cloudfront-js-2.0" \
        --function-code "fileb://$here/directory-index.js" \
        --query ETag --output text)
    fi
  else
    echo "function $name: exists, will update to the committed source"
    if $apply; then
      etag=$(aws cloudfront update-function --name "$name" --if-match "$etag" \
        --function-config "Comment=$comment,Runtime=cloudfront-js-2.0" \
        --function-code "fileb://$here/directory-index.js" \
        --query ETag --output text)
    fi
  fi

  if $apply; then
    aws cloudfront publish-function --name "$name" --if-match "$etag" >/dev/null
    arn=$(aws cloudfront describe-function --name "$name" \
      --query FunctionSummary.FunctionMetadata.FunctionARN --output text)
    echo "function $name: published as $arn"
  else
    # An association cannot be previewed against a function that does not exist yet.
    arn=$(aws cloudfront describe-function --name "$name" \
      --query FunctionSummary.FunctionMetadata.FunctionARN --output text 2>/dev/null || true)
    if [ -z "$arn" ] || [ "$arn" = "None" ]; then arn="<the ARN of $name, once created>"; fi
  fi
fi

# ---------------------------------------------------------------------------
# The distribution.
# ---------------------------------------------------------------------------
aws cloudfront get-distribution-config --id "$id" > "$work/wrapper.json"
config_etag=$(jq -r .ETag "$work/wrapper.json")
jq .DistributionConfig "$work/wrapper.json" > "$work/current.json"

jq --arg arn "$arn" --argjson attach "$( [ -n "$arn" ] && echo true || echo false )" '
  .DefaultRootObject = "index.html"
  | (if $attach then
       .DefaultCacheBehavior.FunctionAssociations = (
         (((.DefaultCacheBehavior.FunctionAssociations.Items // [])
           | map(select(.EventType != "viewer-request")))
          + [{FunctionARN: $arn, EventType: "viewer-request"}]) as $items
         | {Quantity: ($items | length), Items: $items})
     else . end)
  # 403 as well as 404: a REST origin behind an origin access control answers a missing
  # key with 403, because the bucket policy grants GetObject and not ListBucket.
  | .CustomErrorResponses = {
      Quantity: 2,
      Items: [
        {ErrorCode: 403, ResponsePagePath: "/404.html", ResponseCode: "404", ErrorCachingMinTTL: 10},
        {ErrorCode: 404, ResponsePagePath: "/404.html", ResponseCode: "404", ErrorCachingMinTTL: 10}
      ]
    }
' "$work/current.json" > "$work/next.json"

echo
if diff -u <(jq -S . "$work/current.json") <(jq -S . "$work/next.json") > "$work/diff" ; then
  echo "the distribution already says what it should; nothing to write"
  exit 0
fi
sed -n '3,$p' "$work/diff"
echo

if ! $apply; then
  echo "dry run. Re-run with --apply to write it."
  exit 0
fi

aws cloudfront update-distribution --id "$id" --if-match "$config_etag" \
  --distribution-config "file://$work/next.json" >/dev/null
echo "written. Waiting for the distribution to deploy, which takes a few minutes."
aws cloudfront wait distribution-deployed --id "$id"
echo "deployed."
