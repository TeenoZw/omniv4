const UPSTREAM_ORIGIN = "https://admin-v4.omnilogistics.co.zw";
const PORTAL_ORIGINS = new Set([
  "https://portal-v4.omnilogistics.co.zw",
  "https://portal.omnilogistics.co.zw",
]);

function isAllowedPath(pathname) {
  return pathname.startsWith("/api/") || pathname.startsWith("/files/") || pathname.startsWith("/private/files/");
}

function applyCors(headers, origin) {
  if (!origin) return;
  headers.set("Access-Control-Allow-Origin", origin);
  headers.set("Access-Control-Allow-Credentials", "true");
  headers.append("Vary", "Origin");
}

function portalCookie(cookie) {
  let value = cookie.replace(/;\s*Domain=[^;]+/gi, "");
  if (!/;\s*Path=/i.test(value)) value += "; Path=/";
  if (!/;\s*Secure/i.test(value)) value += "; Secure";
  if (!/;\s*SameSite=/i.test(value)) value += "; SameSite=Lax";
  return value;
}

function responseCookies(headers) {
  if (typeof headers.getAll === "function") {
    return headers.getAll("Set-Cookie");
  }
  if (typeof headers.getSetCookie === "function") {
    return headers.getSetCookie();
  }

  const combined = headers.get("Set-Cookie");
  if (!combined) return [];

  // Set-Cookie values may contain a comma in Expires, so only split where the
  // next token starts a new cookie name.
  return combined.split(/,(?=\s*[^;,=\s]+=[^;,]*)/g);
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

    if (request.method === "OPTIONS") {
      const headers = new Headers({
        "Access-Control-Allow-Headers": request.headers.get("Access-Control-Request-Headers") || "Content-Type",
        "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
        "Access-Control-Max-Age": "86400",
      });
      applyCors(headers, origin);
      return new Response(null, { status: 204, headers });
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
    applyCors(responseHeaders, origin);

    const setCookies = responseCookies(upstreamResponse.headers);
    if (setCookies.length) {
      responseHeaders.delete("Set-Cookie");
      for (const cookie of setCookies) responseHeaders.append("Set-Cookie", portalCookie(cookie));
    }

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
