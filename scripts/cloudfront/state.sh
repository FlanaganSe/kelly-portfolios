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
# Reading the origin: there isn't one to read. The distribution's single origin is a
# placeholder that answers nothing, because SST's design decides the origin per request
# inside a viewer-request function (`cf.updateRequestOrigin`). So the bucket the site is
# served from is read back out of the published function's own source, which is the only
# place it is true. `scripts/cloudfront/dump.sh` prints the whole arrangement.
#
# `ready` is what the deploy gates on, and it wants all three:
#   `function_is_ours`  the attached function is `directory-index.js` and not the one
#       SST installed, which looks every path up in a five-key store and rewrites a miss
#       to `/index.html` — the home page, with a 200, for every wrong URL.
#   `bucket`            a bucket domain could be read out of that function.
#   `honest_404`        403 and 404 from the origin become `/404.html` with a 404.
set -euo pipefail

domain="${SITE_DOMAIN:?SITE_DOMAIN is not set}"
ours="kellyportfolios-directory-index"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

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

# The bucket is a literal in our function and a variable in SST's, so this reads back
# as empty for anything but the function this repository publishes.
bucket_domain=""
if [ "$attached_name" = "$ours" ]; then
  if aws cloudfront get-function --name "$ours" --stage LIVE "$work/live.js" >/dev/null 2>&1; then
    bucket_domain=$(grep -oE '[a-z0-9][a-z0-9.-]*\.s3[.-][a-z0-9.-]*amazonaws\.com' "$work/live.js" | head -1 || true)
  fi
fi

state=$(jq -c \
  --arg selected_by "$selected_by" \
  --arg attached "$attached" \
  --arg attached_name "$attached_name" \
  --arg ours "$ours" \
  --arg bucket_domain "$bucket_domain" '
  (.CustomErrorResponses.Items // []) as $errors
  | {
      distribution_id:   .Id,
      selected_by:       $selected_by,
      cloudfront_domain: .DomainName,
      aliases:           (.Aliases.Items // []),
      placeholder_origin: (.Origins.Items // [] | map(.DomainName)),
      attached_function: $attached_name,
      function_is_ours:  ($attached_name == $ours and $attached_name != ""),
      bucket_domain:     $bucket_domain,
      bucket:            ($bucket_domain | sub("\\.s3[.-][a-z0-9-]*\\.?amazonaws\\.com$"; "")),
      honest_404:        ([403, 404] | all(. as $code | $errors | any(
                            .ErrorCode == $code and .ResponsePagePath == "/404.html" and .ResponseCode == "404"))),
      spa_fallback:      ($errors | map(select(.ResponsePagePath == "/index.html")) | length > 0),
      error_responses:   $errors
    }
  | .ready = (.function_is_ours and .bucket != "" and .honest_404)
' <<<"$distribution")

printf '%s\n' "$state"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  for key in distribution_id bucket bucket_domain attached_function function_is_ours honest_404 ready; do
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
      "| Viewer-request function | `\(if .attached_function == "" then "—" else .attached_function end)` |",
      "| Bucket it serves from | `\(if .bucket == "" then "—" else .bucket end)` |",
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
