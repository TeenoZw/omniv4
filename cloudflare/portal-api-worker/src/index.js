const UPSTREAM_ORIGIN = "https://admin-v4.omnilogistics.co.zw";
const PORTAL_ORIGINS = new Set([
  "https://portal-v4.omnilogistics.co.zw",
  "https://portal.omnilogistics.co.zw",
]);

function isAllowedPath(pathname) {
  return pathname.startsWith("/api/") || pathname.startsWith("/files/") || pathname.startsWith("/private/files/");
}

export default {
  async fetch(request) {
    const incomingUrl = new URL(request.url);
    if (!isAllowedPath(incomingUrl.pathname)) {
      return new Response("Not found", { status: 404 });
    }

    const origin = request.headers.get("Origin");
    if (origin && !PORTAL_ORIGINS.has(origin)) {
      return new Response("Origin not allowed", { status: 403 });
    }

    const upstreamUrl = new URL(incomingUrl.pathname + incomingUrl.search, UPSTREAM_ORIGIN);
    const upstreamHeaders = new Headers(request.headers);
    upstreamHeaders.set("X-Forwarded-Host", incomingUrl.host);
    upstreamHeaders.set("X-Omni-Surface", "customer-portal");

    const upstreamResponse = await fetch(
      new Request(upstreamUrl, {
        method: request.method,
        headers: upstreamHeaders,
        body: request.body,
        redirect: "manual",
      }),
    );

    const responseHeaders = new Headers(upstreamResponse.headers);
    responseHeaders.set("Cache-Control", "private, no-store");
    const location = responseHeaders.get("Location");
    if (location) {
      responseHeaders.set("Location", location.replace(UPSTREAM_ORIGIN, incomingUrl.origin));
    }

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  },
};
