// Resolves a URL to a key in a directory-format static build.
//
// S3 resolves keys, not directories: `/start/` is the key `start/`, which does not
// exist, and CloudFront's default root object applies to `/` and to no other directory.
// So `<route>/index.html` is derived here, from the URL.
//
// It replaces the function SST installed, which looked every path up in a CloudFront
// key-value store — one key per file, and the store held five — and rewrote anything it
// could not find to `/index.html`. That is why every wrong URL used to answer with the
// home page and a 200. Keeping such a store in step with several hundred built files on
// every deploy is a moving part with no purpose, and a genuine miss is now allowed to
// miss: the distribution turns S3's 403 into `/404.html` with a 404.
//
// The build emits one URL form (`trailingSlash: "always"` with directory format), so the
// slashless form is redirected rather than served as a second copy of the page.
//
// Runtime is `cloudfront-js-2.0`, which is ES5.1 with parts of ES6 — `const`, template
// literals and `endsWith` are in, `for...of` is not. `repair.sh` runs this against
// CloudFront's own test harness before publishing it, which is how that was established.
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
  const keys = Object.keys(parsed);
  const parts = [];
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const parameter = parsed[key];
    if (parameter.multiValue) {
      for (let j = 0; j < parameter.multiValue.length; j++) {
        const each = parameter.multiValue[j];
        parts.push(each.value === "" ? key : `${key}=${each.value}`);
      }
    } else {
      parts.push(parameter.value === "" ? key : `${key}=${parameter.value}`);
    }
  }
  return parts.length === 0 ? "" : `?${parts.join("&")}`;
}
