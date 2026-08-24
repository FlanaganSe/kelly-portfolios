import cf from "cloudfront";

// Serves the static build, and picks the origin it is served from.
//
// The distribution has one origin, `placeholder.sst.dev`, which answers nothing. SST's
// design puts the routing in this function instead: it calls `cf.updateRequestOrigin`
// per request, so the origin is decided here and the distribution's own origin list is
// a formality. The function it installed looked every path up in a CloudFront
// key-value store, one key per file in the bucket, and rewrote anything it could not
// find to `/index.html` — which is why every wrong URL used to answer with the home
// page and a 200. That store held five keys. This build has several hundred files, and
// keeping a key-value store in step with them on every deploy is a moving part with no
// purpose: `<route>/index.html` is derivable from the URL.
//
// So: resolve the directory index, redirect the slashless form rather than serving a
// second copy of the page at it, and let a genuine miss miss. The distribution's custom
// error responses turn S3's 403 into `/404.html` with a 404.
//
// Runtime is `cloudfront-js-2.0`. `scripts/cloudfront/repair.sh` publishes it, tests it
// against the live CloudFront test harness, and attaches it on viewer request.

// Where the site is. `scripts/cloudfront/state.sh` reads this back out of the published
// function so the deploy syncs into the bucket the function actually serves from,
// rather than into one the repository merely believes in.
const BUCKET = "portfolio-op-production-portfoliooptimizerassetsbucket-okwwseht.s3.us-east-1.amazonaws.com";

function handler(event) {
  const request = event.request;
  const uri = request.uri;

  if (uri.endsWith("/")) {
    request.uri = `${uri}index.html`;
  } else {
    // A last segment with no dot in it is a page, not a file: `/start` -> `/start/`.
    const last = uri.slice(uri.lastIndexOf("/") + 1);
    if (!last.includes(".")) {
      return {
        statusCode: 301,
        statusDescription: "Moved Permanently",
        headers: { location: { value: `${uri}/${queryString(request.querystring)}` } },
      };
    }
  }

  // S3 has no use for these and they are not part of the signature. SST's function
  // dropped them too.
  delete request.headers.cookie;
  delete request.cookies;

  cf.updateRequestOrigin({
    domainName: BUCKET,
    originAccessControlConfig: {
      enabled: true,
      signingBehavior: "always",
      signingProtocol: "sigv4",
      originType: "s3",
    },
  });

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
