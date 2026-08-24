#!/usr/bin/env bash
#
# Everything about the distribution, printed. Read-only.
#
# The site is served by an SST design that no committed code describes: one
# `placeholder.sst.dev` origin and a CloudFront Function that decides, per request,
# which origin and which key answer it. What that function does is therefore the whole
# behaviour of the site, and it exists nowhere but in CloudFront. This prints it, along
# with the distribution configuration, any key-value store the function reads, and the
# buckets in the account.
#
#   SITE_DOMAIN=kellyportfolios.com scripts/cloudfront/dump.sh
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
state=$(GITHUB_OUTPUT="" GITHUB_STEP_SUMMARY="" "$here/state.sh" 2>/dev/null)
id=$(jq -r .distribution_id <<<"$state")

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

echo "=== distribution $id"
aws cloudfront get-distribution-config --id "$id" > "$work/config.json"
jq .DistributionConfig "$work/config.json"

echo
echo "=== functions and Lambda@Edge on every behaviour"
arns=$(jq -r '
  .DistributionConfig
  | [.DefaultCacheBehavior] + (.CacheBehaviors.Items // [])
  | map((.FunctionAssociations.Items // []) + (.LambdaFunctionAssociations.Items // []))
  | flatten | map(.FunctionARN // .LambdaFunctionARN) | unique | .[]
' "$work/config.json")

for arn in $arns; do
  name=${arn##*/}
  echo "--- $arn"
  case "$arn" in
    *:function/*)
      aws cloudfront describe-function --name "$name" --stage LIVE --output json | jq '.FunctionSummary.FunctionConfig'
      aws cloudfront get-function --name "$name" --stage LIVE "$work/$name.js" >/dev/null
      cat "$work/$name.js"
      kvs=$(aws cloudfront describe-function --name "$name" --stage LIVE \
        --query 'FunctionSummary.FunctionConfig.KeyValueStoreAssociations.Items[0].KeyValueStoreARN' \
        --output text 2>/dev/null || true)
      if [ -n "$kvs" ] && [ "$kvs" != "None" ]; then
        echo "--- key-value store $kvs"
        aws cloudfront-keyvaluestore list-keys --kvs-arn "$kvs" --output json || true
      fi
      ;;
    *) echo "(Lambda@Edge; code lives in the function's own region)" ;;
  esac
done

echo
echo "=== buckets in the account"
aws s3 ls || true
