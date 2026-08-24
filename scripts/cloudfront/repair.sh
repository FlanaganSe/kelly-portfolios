#!/usr/bin/env bash
#
# Makes the distribution serve a directory-format static build.
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh           # prints the diff
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh --apply   # writes it
#
# Three changes, all idempotent:
#
#   1. A real origin. SST's design left the distribution with one origin,
#      `placeholder.sst.dev`, which answers nothing, and picked the bucket per request
#      inside the viewer-request function instead. That works for a page and not for a
#      custom error response: CloudFront fetches the error page with the cache
#      behaviour's own origin, the function never runs for it, and a miss came back 502
#      rather than 404. So the bucket becomes an actual origin, read through an origin
#      access control, and the behaviour points at it.
#
#   2. 403 and 404 from that origin become `/404.html` with a status of 404. Both codes:
#      the bucket policy grants `GetObject` and not `ListBucket`, so a missing key is a
#      403.
#
#   3. `directory-index.js` replaces the function SST installed, which resolved paths
#      through a five-key store and rewrote a miss to `/index.html`.
#
# Order matters and is the reason this is not two scripts. The function that is attached
# right now may be the one that picks the origin; publishing new code under it before the
# distribution has an origin of its own would take the site down for the minutes the
# distribution takes to deploy. So the distribution is fixed first, and the code is
# published after.
#
# Nothing here touches the bucket's contents, its policy, the certificate, the aliases, or
# any DNS record. SST's function and its key-value store are left in place, unattached and
# unread; nothing that could deploy them exists any more and deleting them gains nothing.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
. "$here/site.env"

apply=false
if [ "${1:-}" = "--apply" ]; then apply=true; fi

name="kellyportfolios-directory-index"
oac="kellyportfolios-site"
# The shorthand form of --function-config splits on commas, so this must not contain one.
config='{"Comment":"Directory indexes for a static build","Runtime":"cloudfront-js-2.0"}'

state=$(GITHUB_OUTPUT="" GITHUB_STEP_SUMMARY="" SITE_DOMAIN="${SITE_DOMAIN:?SITE_DOMAIN is not set}" "$here/state.sh" 2>/dev/null)
id=$(jq -r .distribution_id <<<"$state")
echo "distribution $id, viewer-request function $(jq -r 'if .attached_function == "" then "none" else .attached_function end' <<<"$state")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# `expect <uri> uri|status|location <expected> [querystring-json]`, against the DEVELOPMENT
# stage of the function, before anything can be pointed at it.
test_function() {
  local etag="$1"
  event() {
    local qs="${2:-}"
    if [ -z "$qs" ]; then qs="{}"; fi
    jq -n --arg uri "$1" --argjson qs "$qs" '{
      version: "1.0",
      context: {eventType: "viewer-request"},
      viewer: {ip: "203.0.113.1"},
      request: {method: "GET", uri: $uri, headers: {host: {value: "kellyportfolios.com"}},
                cookies: {}, querystring: $qs}
    }'
  }
  expect() {
    event "$1" "${4:-}" > "$work/event.json"
    local out error got
    out=$(aws cloudfront test-function --name "$name" --if-match "$etag" --stage DEVELOPMENT \
      --event-object "fileb://$work/event.json" --output json)
    error=$(jq -r '.TestResult.FunctionErrorMessage // ""' <<<"$out")
    if [ -n "$error" ]; then
      echo "::error::$name failed on $1: $error" >&2
      jq -r '.TestResult.FunctionExecutionLogs[]?' <<<"$out" >&2
      exit 1
    fi
    case "$2" in
      uri)      got=$(jq -r '.TestResult.FunctionOutput | fromjson | .request.uri' <<<"$out") ;;
      status)   got=$(jq -r '.TestResult.FunctionOutput | fromjson | .response.statusCode | tostring' <<<"$out") ;;
      location) got=$(jq -r '.TestResult.FunctionOutput | fromjson | .response.headers.location.value' <<<"$out") ;;
    esac
    printf '  %-44s %-8s %s\n' "$1" "$2" "$got"
    if [ "$got" != "$3" ]; then
      echo "::error::$1 gave $2 $got, wanted $3. Not publishing." >&2
      exit 1
    fi
  }

  echo "testing $name against CloudFront's harness"
  expect "/"                                            uri      "/index.html"
  expect "/start/"                                      uri      "/start/index.html"
  expect "/research/decisions/0004-no-sleeve-promoted/"  uri      "/research/decisions/0004-no-sleeve-promoted/index.html"
  expect "/start"                                       status   "301"
  expect "/robots.txt"                                  uri      "/robots.txt"
  expect "/_astro/page.CH4nk3d.js"                      uri      "/_astro/page.CH4nk3d.js"
  # The only case that reaches the query-string rebuild.
  expect "/tools/how-long"                              location "/tools/how-long/?years=20" '{"years":{"value":"20"}}'
}

# ---------------------------------------------------------------------------
# The function has to exist before the distribution can name it, but its code is
# published at the end.
# ---------------------------------------------------------------------------
etag=$(aws cloudfront describe-function --name "$name" --query ETag --output text 2>/dev/null || true)
existed=true
if [ -z "$etag" ] || [ "$etag" = "None" ]; then
  existed=false
  echo "function $name: does not exist, will create"
  if $apply; then
    etag=$(aws cloudfront create-function --name "$name" --function-config "$config" \
      --function-code "fileb://$here/directory-index.js" --query ETag --output text)
    test_function "$etag"
    aws cloudfront publish-function --name "$name" --if-match "$etag" >/dev/null
    echo "function $name: published"
  fi
fi

arn=$(aws cloudfront describe-function --name "$name" \
  --query FunctionSummary.FunctionMetadata.FunctionARN --output text 2>/dev/null || true)
if [ -z "$arn" ] || [ "$arn" = "None" ]; then arn="<the ARN of $name, once created>"; fi

# ---------------------------------------------------------------------------
# The origin access control, and then the distribution.
# ---------------------------------------------------------------------------
oac_id=$(aws cloudfront list-origin-access-controls \
  --query "OriginAccessControlList.Items[?Name=='${oac}'].Id | [0]" --output text 2>/dev/null || true)
if [ -z "$oac_id" ] || [ "$oac_id" = "None" ]; then
  echo "origin access control $oac: does not exist, will create"
  if $apply; then
    oac_id=$(aws cloudfront create-origin-access-control --origin-access-control-config \
      "{\"Name\":\"$oac\",\"Description\":\"Signs the bucket reads for the site\",\"SigningProtocol\":\"sigv4\",\"SigningBehavior\":\"always\",\"OriginAccessControlOriginType\":\"s3\"}" \
      --query OriginAccessControl.Id --output text)
  else
    oac_id="<the id of $oac, once created>"
  fi
fi

aws cloudfront get-distribution-config --id "$id" > "$work/wrapper.json"
config_etag=$(jq -r .ETag "$work/wrapper.json")
jq .DistributionConfig "$work/wrapper.json" > "$work/current.json"

jq --arg arn "$arn" --arg oac "$oac_id" --arg bucket "$SITE_BUCKET_DOMAIN" '
  # One origin, the bucket, read through the access control. The placeholder goes: it is
  # referenced by nothing once the behaviour points at the bucket, and an inert origin in
  # a hand-edited configuration is a thing for the next reader to have to work out.
  .Origins = {
    Quantity: 1,
    Items: [{
      Id: "site",
      DomainName: $bucket,
      OriginPath: "",
      CustomHeaders: {Quantity: 0},
      S3OriginConfig: {OriginAccessIdentity: ""},
      OriginAccessControlId: $oac,
      ConnectionAttempts: 3,
      ConnectionTimeout: 10,
      OriginShield: {Enabled: false}
    }]
  }
  | .DefaultCacheBehavior.TargetOriginId = "site"
  | .DefaultCacheBehavior.FunctionAssociations = (
      (((.DefaultCacheBehavior.FunctionAssociations.Items // [])
        | map(select(.EventType != "viewer-request")))
       + [{FunctionARN: $arn, EventType: "viewer-request"}]) as $items
      | {Quantity: ($items | length), Items: $items})
  | .CustomErrorResponses = {
      Quantity: 2,
      Items: [
        {ErrorCode: 403, ResponsePagePath: "/404.html", ResponseCode: "404", ErrorCachingMinTTL: 10},
        {ErrorCode: 404, ResponsePagePath: "/404.html", ResponseCode: "404", ErrorCachingMinTTL: 10}
      ]
    }
' "$work/current.json" > "$work/next.json"

echo
if diff -u <(jq -S . "$work/current.json") <(jq -S . "$work/next.json") > "$work/diff"; then
  echo "the distribution already says what it should"
else
  sed -n '3,$p' "$work/diff"
  echo
  if $apply; then
    aws cloudfront update-distribution --id "$id" --if-match "$config_etag" \
      --distribution-config "file://$work/next.json" >/dev/null
    echo "written. Waiting for the distribution to deploy, which takes a few minutes."
    aws cloudfront wait distribution-deployed --id "$id"
    echo "deployed."
  fi
fi

if ! $apply; then
  echo "dry run. Re-run with --apply to write it."
  exit 0
fi

# ---------------------------------------------------------------------------
# And now the code, safely, because the distribution no longer depends on what it says.
# ---------------------------------------------------------------------------
if $existed; then
  etag=$(aws cloudfront describe-function --name "$name" --query ETag --output text)
  etag=$(aws cloudfront update-function --name "$name" --if-match "$etag" --function-config "$config" \
    --function-code "fileb://$here/directory-index.js" --query ETag --output text)
  test_function "$etag"
  aws cloudfront publish-function --name "$name" --if-match "$etag" >/dev/null
  echo "function $name: published"
fi
