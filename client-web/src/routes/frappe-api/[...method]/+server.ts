import type { RequestHandler } from "./$types";
import {
  applyPortalSessionCookie,
  FRAPPE_ORIGIN,
  responseCookies,
  upstreamCookieHeader,
} from "$lib/server/frappe-session";

const proxy: RequestHandler = async ({ request, params, url, cookies }) => {
  const methodPath = params.method || "";
  const upstreamUrl = new URL(`/api/method/${methodPath}${url.search}`, FRAPPE_ORIGIN);
  const headers = new Headers(request.headers);
  headers.delete("host");
  const cookieHeader = upstreamCookieHeader(headers, cookies);
  if (cookieHeader) headers.set("cookie", cookieHeader);
  else headers.delete("cookie");
  headers.set("X-Forwarded-Host", url.host);
  headers.set("X-Omni-Surface", "customer-portal");

  const upstream = await globalThis.fetch(upstreamUrl, {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    redirect: "manual",
  });

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.set("Cache-Control", "private, no-store");
  const upstreamCookies = responseCookies(upstream.headers);
  if (upstreamCookies.length) {
    responseHeaders.delete("Set-Cookie");
    for (const cookie of upstreamCookies) {
      applyPortalSessionCookie(cookie, cookies);
    }
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
};

export const GET = proxy;
export const HEAD = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
