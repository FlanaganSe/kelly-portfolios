#!/usr/bin/env bash
#
# Makes the distribution serve a directory-format static build.
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh           # prints the diff
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/repair.sh --apply   # writes it
#
# Two changes on the distribution `scripts/cloudfront/state.sh` finds:
#
#   1. `directory-index.js` replaces the viewer-request function SST installed. That
#      function is the whole routing behaviour of the site — it picks the origin per
#      request — so it is tested against CloudFront's own harness before it is published
#      and again before it is attached. `scripts/cloudfront/dump.sh` prints the one being
#      replaced.
#
#   2. 403 and 404 from the origin become `/404.html` with a status of 404. The build
#      emits that page. Both codes, because the bucket is read through an origin access
#      control whose policy grants `GetObject` and not `ListBucket`, so a missing key
#      comes back as 403.
#
# Both are idempotent. Nothing here touches the bucket, the certificate, the aliases, or
# any DNS record. SST's function and its key-value store are left in place, unattached
# and unread, because nothing that can deploy them exists any more and deleting them
# gains nothing.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
apply=false
if [ "${1:-}" = "--apply" ]; then apply=true; fi

name="kellyportfolios-directory-index"
comment="Directory indexes, one trailing-slash form, and the bucket origin"

state=$(GITHUB_OUTPUT="" GITHUB_STEP_SUMMARY="" SITE_DOMAIN="${SITE_DOMAIN:?SITE_DOMAIN is not set}" "$here/state.sh" 2>/dev/null)
id=$(jq -r .distribution_id <<<"$state")
echo "distribution $id, viewer-request function $(jq -r '.attached_function // "none"' <<<"$state")"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# ---------------------------------------------------------------------------
# The function, and the proof that it does what it says before anything points at it.
# ---------------------------------------------------------------------------
etag=$(aws cloudfront describe-function --name "$name" --query ETag --output text 2>/dev/null || true)
if [ -z "$etag" ] || [ "$etag" = "None" ]; then
  action="create"
else
  action="update"
fi
echo "function $name: will $action"

if $apply; then
  if [ "$action" = "create" ]; then
    etag=$(aws cloudfront create-function --name "$name" \
      --function-config "Comment=$comment,Runtime=cloudfront-js-2.0" \
      --function-code "fileb://$here/directory-index.js" --query ETag --output text)
  else
    etag=$(aws cloudfront update-function --name "$name" --if-match "$etag" \
      --function-config "Comment=$comment,Runtime=cloudfront-js-2.0" \
      --function-code "fileb://$here/directory-index.js" --query ETag --output text)
  fi

  event() {
    jq -n --arg uri "$1" '{
      version: "1.0",
      context: {eventType: "viewer-request"},
      viewer: {ip: "203.0.113.1"},
      request: {method: "GET", uri: $uri, headers: {host: {value: "kellyportfolios.com"}},
                cookies: {}, querystring: {}}
    }'
  }

  # `expect <uri> uri <expected>` or `expect <uri> status <expected>`.
  expect() {
    event "$1" > "$work/event.json"
    local out
    out=$(aws cloudfront test-function --name "$name" --if-match "$etag" --stage DEVELOPMENT \
      --event-object "fileb://$work/event.json" --output json)
    local error
    error=$(jq -r '.TestResult.FunctionErrorMessage // ""' <<<"$out")
    if [ -n "$error" ]; then
      echo "::error::$name failed on $1: $error" >&2
      jq -r '.TestResult.FunctionExecutionLogs[]?' <<<"$out" >&2
      exit 1
    fi
    local got
    case "$2" in
      uri)    got=$(jq -r '.TestResult.FunctionOutput | fromjson | .request.uri' <<<"$out") ;;
      status) got=$(jq -r '.TestResult.FunctionOutput | fromjson | .response.statusCode | tostring' <<<"$out") ;;
    esac
    printf '  %-28s %-6s %s\n' "$1" "$2" "$got"
    if [ "$got" != "$3" ]; then
      echo "::error::$1 gave $2 $got, wanted $3. Not publishing." >&2
      exit 1
    fi
  }

  echo "testing $name against CloudFront's harness before publishing it"
  expect "/"                     uri    "/index.html"
  expect "/start/"               uri    "/start/index.html"
  expect "/research/decisions/0004-no-sleeve-promoted/" uri "/research/decisions/0004-no-sleeve-promoted/index.html"
  expect "/start"                status "301"
  expect "/robots.txt"           uri    "/robots.txt"
  expect "/_astro/page.CH4nk3d.js" uri  "/_astro/page.CH4nk3d.js"

  aws cloudfront publish-function --name "$name" --if-match "$etag" >/dev/null
  echo "function $name: published"
fi

arn=$(aws cloudfront describe-function --name "$name" \
  --query FunctionSummary.FunctionMetadata.FunctionARN --output text 2>/dev/null || true)
if [ -z "$arn" ] || [ "$arn" = "None" ]; then arn="<the ARN of $name, once created>"; fi

# ---------------------------------------------------------------------------
# The distribution.
# ---------------------------------------------------------------------------
aws cloudfront get-distribution-config --id "$id" > "$work/wrapper.json"
config_etag=$(jq -r .ETag "$work/wrapper.json")
jq .DistributionConfig "$work/wrapper.json" > "$work/current.json"

jq --arg arn "$arn" '
  .DefaultCacheBehavior.FunctionAssociations = (
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
