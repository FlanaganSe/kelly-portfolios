// Serves a directory-format static build from a CloudFront REST origin.
//
// S3's REST API resolves keys, not directories. `/start/` is the key `start/`, which
// does not exist, and CloudFront's default root object applies to `/` and to no other
// directory, so without this every page but the home page misses. The S3 *website*
// endpoint resolves `start/index.html` on its own, but it is HTTP-only and needs a
// public bucket, which is a worse trade than eighteen lines of JavaScript.
//
// The build emits one URL form (`trailingSlash: "always"` with directory format), so
// the slashless form is redirected rather than served as a second copy of the page.
// Two indexed URLs for one document is the failure being avoided.
//
// Runtime is `cloudfront-js-2.0`. `scripts/cloudfront/repair.sh` publishes it and
// attaches it to the default cache behaviour on viewer request.
function handler(event) {
  const request = event.request;
  const uri = request.uri;

  if (uri.endsWith("/")) {
    request.uri = `${uri}index.html`;
    return request;
  }

  // A last segment with no dot in it is a page, not a file: `/start` -> `/start/`.
  const last = uri.slice(uri.lastIndexOf("/") + 1);
  if (!last.includes(".")) {
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { location: { value: `${uri}/${queryString(request.querystring)}` } },
    };
  }

  return request;
}

// The query string arrives parsed, so a redirect has to rebuild it or drop it. This
// re-joins the parts exactly as they arrived; it does not encode or decode anything.
function queryString(parsed) {
  const parts = [];
  for (const key of Object.keys(parsed)) {
    const parameter = parsed[key];
    if (parameter.multiValue) {
      for (const each of parameter.multiValue) {
        parts.push(each.value === "" ? key : `${key}=${each.value}`);
      }
    } else {
      parts.push(parameter.value === "" ? key : `${key}=${parameter.value}`);
    }
  }
  return parts.length === 0 ? "" : `?${parts.join("&")}`;
}
