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
# Two things here are not the obvious thing, and both were learned the hard way.
#
# Finding the distribution: not `Origins.Items[0]`, which is `placeholder.sst.dev` and
# would have the deploy sync a whole site into a bucket of that name, and not the first
# distribution whose aliases mention the domain either. Route 53's alias record names
# the distribution that answers a request, so the domain is followed. The alias match
# survives only as a fallback for a key without Route 53 permission.
#
# Reading the origin: until `repair.sh` ran there was nothing to read. SST's design left
# the distribution one origin, `placeholder.sst.dev`, which answers nothing, and picked
# the bucket per request inside the viewer-request function. `scripts/cloudfront/dump.sh`
# prints that arrangement; `docs/deploying.md` explains why it had to go.
#
# `ready` is what the deploy gates on, and it wants all three:
#   `origin_is_site`    the behaviour serving the site points at the bucket in
#       `site.env`, so the deploy uploads to the place the reader is served from.
#   `function_is_ours`  the attached function is `directory-index.js` and not the one
#       SST installed, which looks every path up in a five-key store and rewrites a miss
#       to `/index.html` — the home page, with a 200, for every wrong URL.
#   `honest_404`        403 and 404 from the origin become `/404.html` with a 404.
set -euo pipefail

domain="${SITE_DOMAIN:?SITE_DOMAIN is not set}"
ours="kellyportfolios-directory-index"
# shellcheck source=/dev/null
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/site.env"

distributions=$(aws cloudfront list-distributions --query 'DistributionList.Items' --output json)

# Every distribution this key can see, one line each. Cheap, and the first thing worth
# knowing when the answer below is surprising.
{
  echo "distributions visible to this key:"
  jq -r '.[] | "  \(.Id)  \(if .Enabled then "enabled " else "disabled" end)  \(.DomainName)  aliases=\((.Aliases.Items // []) | join(","))"' <<<"$distributions"
} >&2

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
distribution=$(jq -c --arg target "$target" '[.[] | select(.DomainName == $target)] | first // empty' <<<"$distributions")
if [ -z "$distribution" ]; then
  selected_by="alias"
  distribution=$(jq -c --arg domain "$domain" \
    '[.[] | select((.Aliases.Items // []) | index($domain))] | first // empty' <<<"$distributions")
fi

if [ -z "$distribution" ]; then
  echo "::error::Nothing this key can see serves ${domain}: no Route 53 alias target matched and no distribution lists it." >&2
  exit 1
fi

attached=$(jq -r '
  (.DefaultCacheBehavior.FunctionAssociations.Items // [])
  | map(select(.EventType == "viewer-request")) | first | .FunctionARN // ""
' <<<"$distribution")
attached_name="${attached##*/}"

state=$(jq -c \
  --arg selected_by "$selected_by" \
  --arg attached_name "$attached_name" \
  --arg ours "$ours" \
  --arg site "$SITE_BUCKET_DOMAIN" '
  (.CustomErrorResponses.Items // []) as $errors
  | .DefaultCacheBehavior.TargetOriginId as $target
  | ((.Origins.Items // []) | map(select(.Id == $target)) | first | .DomainName // "") as $host
  | {
      distribution_id:   .Id,
      selected_by:       $selected_by,
      cloudfront_domain: .DomainName,
      aliases:           (.Aliases.Items // []),
      origins:           ((.Origins.Items // []) | map(.DomainName)),
      origin_domain:     $host,
      origin_is_site:    ($host == $site),
      bucket:            (if $host == $site
                          then ($host | sub("\\.s3[.-][a-z0-9-]*\\.?amazonaws\\.com$"; ""))
                          else "" end),
      attached_function: $attached_name,
      function_is_ours:  ($attached_name == $ours and $attached_name != ""),
      honest_404:        ([403, 404] | all(. as $code | $errors | any(
                            .ErrorCode == $code and .ResponsePagePath == "/404.html" and .ResponseCode == "404"))),
      spa_fallback:      ($errors | map(select(.ResponsePagePath == "/index.html")) | length > 0),
      error_responses:   $errors
    }
  | .ready = (.origin_is_site and .function_is_ours and .honest_404)
' <<<"$distribution")

printf '%s\n' "$state"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  for key in distribution_id bucket origin_domain origin_is_site attached_function function_is_ours honest_404 ready; do
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
      "| Origin | `\(if .origin_domain == "" then "—" else .origin_domain end)`\(if .origin_is_site then "" else " — **not the bucket in site.env**" end) |",
      "| Viewer-request function | `\(if .attached_function == "" then "—" else .attached_function end)` |",
      "| A miss answers 404 | **\(.honest_404)** |",
      "| Ready to publish | **\(.ready)** |"
    ' <<<"$state"
    echo ""
    if [ "$(jq -r .ready <<<"$state")" != "true" ]; then
      echo "> Not publishable as configured. Run the **Configure distribution** workflow,"
      echo "> or read \`docs/deploying.md\`."
    fi
  } >> "$GITHUB_STEP_SUMMARY"
fi
