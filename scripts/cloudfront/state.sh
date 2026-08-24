#!/usr/bin/env bash
#
# What is actually in front of the domain, and can it serve this build?
#
# Prints one JSON object on stdout. Inside Actions it also writes those fields to
# $GITHUB_OUTPUT and a table to $GITHUB_STEP_SUMMARY. Reads nothing but the API and
# changes nothing at all, so it is safe to run at any time:
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/state.sh | jq .
#
# The field that decides a deploy is `ready`. Three separate things can make it false,
# and all three are quiet failures rather than loud ones, which is why the state is
# computed here instead of being assumed:
#
#   `origin_kind: foreign`  The behaviour serving the site points at something that is
#       not a bucket. SST leaves `placeholder.sst.dev` in the origin list, and it sorts
#       ahead of the real bucket, so a deploy that reads `Origins.Items[0]` derives the
#       bucket name `placeholder.sst.dev` and syncs a whole site into nowhere. This
#       reads the origin that `DefaultCacheBehavior` targets, which is the one that
#       answers a request.
#
#   `rewrites_directories: false`  A REST origin with nothing rewriting the URI serves
#       `/` and 404s every other page.
#
#   `spa_fallback: true`  A custom error response mapping 403 or 404 to `/index.html`
#       is the single-page-application fallback the old site needed. Against this build
#       it answers every wrong URL with the home page and a 200, so a typo looks like a
#       working page and a crawler indexes a copy of the home page under each one.
#
# `scripts/cloudfront/repair.sh` fixes the second and the third. `docs/deploying.md`
# explains the first.
set -euo pipefail

domain="${SITE_DOMAIN:?SITE_DOMAIN is not set}"

distribution=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?contains(Aliases.Items || \`[]\`, '${domain}')] | [0]" \
  --output json)

if [ -z "$distribution" ] || [ "$distribution" = "null" ]; then
  echo "::error::No CloudFront distribution lists ${domain} as an alias." >&2
  echo "Distributions this key can see:" >&2
  aws cloudfront list-distributions \
    --query "DistributionList.Items[].{Id:Id,Aliases:Aliases.Items,Origin:Origins.Items[0].DomainName}" \
    --output table >&2 || true
  exit 1
fi

state=$(jq -c '
  .DefaultCacheBehavior.TargetOriginId as $target
  | (.Origins.Items // [] | map(select(.Id == $target)) | first) as $origin
  | ($origin.DomainName // "") as $host
  # Website endpoint first: it also matches the REST pattern if tested the other way.
  | (if   ($host | test("\\.s3-website[.-]"))            then "website"
     elif ($host | test("\\.s3[.-][a-z0-9.-]*amazonaws\\.com$")) then "rest"
     else "foreign" end) as $kind
  | ((.DefaultCacheBehavior.FunctionAssociations.Items // [])
     | map(select(.EventType == "viewer-request"))) as $viewer
  | (.CustomErrorResponses.Items // []) as $errors
  | {
      distribution_id:      .Id,
      origin_id:            $target,
      origin_domain:        $host,
      origin_kind:          $kind,
      origin_protocol:      ($origin.CustomOriginConfig.OriginProtocolPolicy // "s3"),
      bucket:               (if $kind == "foreign" then ""
                             else ($host
                                   | sub("\\.s3-website[.-][a-z0-9-]+\\.amazonaws\\.com$"; "")
                                   | sub("\\.s3[.-][a-z0-9-]*\\.?amazonaws\\.com$"; "")) end),
      all_origins:          (.Origins.Items // [] | map({id: .Id, domain: .DomainName})),
      viewer_functions:     ($viewer | map(.FunctionARN)),
      rewrites_directories: ($kind == "website" or ($viewer | length) > 0),
      spa_fallback:         ($errors | map(select(.ResponsePagePath == "/index.html")) | length > 0),
      error_responses:      $errors,
      default_root_object:  (.DefaultRootObject // "")
    }
  | .ready = (.origin_kind != "foreign" and .rewrites_directories and (.spa_fallback | not))
' <<<"$distribution")

printf '%s\n' "$state"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  for key in distribution_id bucket origin_domain origin_kind rewrites_directories spa_fallback ready; do
    printf '%s=%s\n' "$key" "$(jq -r --arg k "$key" '.[$k]' <<<"$state")" >> "$GITHUB_OUTPUT"
  done
fi

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "### ${STATE_HEADING:-What is behind ${domain}}"
    echo ""
    jq -r '
      "| | |", "|---|---|",
      "| Distribution | `\(.distribution_id)` |",
      "| Origin serving the site | `\(.origin_domain)` (\(.origin_kind)) |",
      "| Bucket | `\(if .bucket == "" then "—" else .bucket end)` |",
      "| Resolves directory indexes | **\(.rewrites_directories)** |",
      "| Single-page-app fallback | **\(.spa_fallback)** |",
      "| Ready to publish | **\(.ready)** |",
      "",
      "Every origin on the distribution:",
      "",
      (.all_origins[] | "- `\(.domain)`  _(\(.id))_"),
      "",
      (if .error_responses == [] then "No custom error responses."
       else "Custom error responses:\n\n```json\n" + (.error_responses | tojson) + "\n```" end)
    ' <<<"$state"
    echo ""
    if [ "$(jq -r .ready <<<"$state")" != "true" ]; then
      echo "> Not publishable as configured. Run the **Configure distribution** workflow,"
      echo "> or read \`docs/deploying.md\`."
    fi
  } >> "$GITHUB_STEP_SUMMARY"
fi
