#!/usr/bin/env bash
#
# What is actually in front of the domain, and can it serve this build?
#
# Prints one JSON object on stdout and an inventory of every distribution the key can
# see on stderr. Inside Actions it also writes the fields to $GITHUB_OUTPUT and a table
# to $GITHUB_STEP_SUMMARY. Reads nothing but the API and changes nothing at all:
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/state.sh | jq .
#
# Finding the right distribution is most of the job, and two obvious ways to do it are
# both wrong. `Origins.Items[0]` is `placeholder.sst.dev`, an SST leftover that sorts
# ahead of the bucket; a deploy that trusts it derives the bucket name
# `placeholder.sst.dev` and syncs an entire site into nowhere. The first distribution
# whose aliases mention the domain is `E2UXACC7VKS53Z`, which has that one placeholder
# origin and serves nothing. So the domain is followed instead: Route 53's alias record
# names the CloudFront distribution that answers a request, and that is the one read.
# The alias match is kept only as a fallback for a key without Route 53 permission.
#
# The field that decides a deploy is `ready`. Three things can make it false, and each
# fails quietly rather than loudly:
#
#   `origin_kind: foreign`  The behaviour serving the site points at something that is
#       not a bucket.
#   `rewrites_directories: false`  A REST origin with nothing rewriting the URI serves
#       `/` and misses on every other page.
#   `spa_fallback: true`  A custom error response mapping 403 or 404 to `/index.html`
#       answers every wrong URL with the home page and a 200.
#
# `scripts/cloudfront/repair.sh` fixes the last two. `docs/deploying.md` is the long
# version.
set -euo pipefail

domain="${SITE_DOMAIN:?SITE_DOMAIN is not set}"

distributions=$(aws cloudfront list-distributions --query 'DistributionList.Items' --output json)

# Every distribution this key can see, one line each. Cheap, and the first thing worth
# knowing when the answer below is surprising.
{
  echo "distributions visible to this key:"
  jq -r '.[] | "  \(.Id)  \(if .Enabled then "enabled " else "disabled" end)  \(.DomainName)  aliases=\((.Aliases.Items // []) | join(","))  default-origin=\(.DefaultCacheBehavior.TargetOriginId as $t | (.Origins.Items // [] | map(select(.Id == $t)) | first | .DomainName // "?"))"' <<<"$distributions"
} >&2

# Route 53 is the authority on which of them answers for the domain.
target=""
zone=$(aws route53 list-hosted-zones-by-name --dns-name "$domain" \
  --query "HostedZones[?Name=='${domain}.'].Id | [0]" --output text 2>/dev/null || true)
if [ -n "$zone" ] && [ "$zone" != "None" ]; then
  target=$(aws route53 list-resource-record-sets --hosted-zone-id "$zone" \
    --query "ResourceRecordSets[?Name=='${domain}.' && (Type=='A' || Type=='AAAA')].AliasTarget.DNSName | [0]" \
    --output text 2>/dev/null || true)
  [ "$target" = "None" ] && target=""
  target="${target%.}"
  echo "route 53 says ${domain} is an alias for ${target:-<nothing this key can read>}" >&2
else
  echo "route 53: no hosted zone for ${domain} that this key can read; falling back to aliases" >&2
fi

selected_by="route53"
distribution=$(jq -c --arg target "$target" '
  [.[] | select(.DomainName == $target)] | first // empty
' <<<"$distributions")

if [ -z "$distribution" ]; then
  selected_by="alias"
  # Prefer a candidate that could actually serve the site over one that could not.
  distribution=$(jq -c --arg domain "$domain" '
    [.[] | select((.Aliases.Items // []) | index($domain))]
    | (map(select(.DefaultCacheBehavior.TargetOriginId as $t
        | (.Origins.Items // [] | map(select(.Id == $t)) | first | .DomainName // "")
        | test("\\.s3[.-]"))) | first)
      // first
      // empty
  ' <<<"$distributions")
fi

if [ -z "$distribution" ]; then
  echo "::error::Nothing this key can see serves ${domain}: no Route 53 alias target matched and no distribution lists it." >&2
  exit 1
fi

state=$(jq -c --arg selected_by "$selected_by" '
  .DefaultCacheBehavior.TargetOriginId as $target
  | (.Origins.Items // [] | map(select(.Id == $target)) | first) as $origin
  | ($origin.DomainName // "") as $host
  # Website endpoint first: it also matches the REST pattern if tested the other way.
  | (if   ($host | test("\\.s3-website[.-]"))                     then "website"
     elif ($host | test("\\.s3[.-][a-z0-9.-]*amazonaws\\.com$"))  then "rest"
     else "foreign" end) as $kind
  | ((.DefaultCacheBehavior.FunctionAssociations.Items // [])
     | map(select(.EventType == "viewer-request"))) as $viewer
  | (.CustomErrorResponses.Items // []) as $errors
  | {
      distribution_id:      .Id,
      selected_by:          $selected_by,
      cloudfront_domain:    .DomainName,
      aliases:              (.Aliases.Items // []),
      origin_id:            $target,
      origin_domain:        $host,
      origin_kind:          $kind,
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
      "| Distribution | `\(.distribution_id)` (\(.cloudfront_domain), found by \(.selected_by)) |",
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
