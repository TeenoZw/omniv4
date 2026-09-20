import type { RequestHandler } from "./$types";

const FRAPPE_ORIGIN = "https://admin-v4.omnilogistics.co.zw";

function responseCookies(headers: Headers) {
  const cloudflareHeaders = headers as Headers & {
    getAll?: (name: string) => string[];
    getSetCookie?: () => string[];
  };
  if (typeof cloudflareHeaders.getAll === "function") return cloudflareHeaders.getAll("Set-Cookie");
  if (typeof cloudflareHeaders.getSetCookie === "function") return cloudflareHeaders.getSetCookie();

  const combined = headers.get("Set-Cookie");
  if (!combined) return [];
  return combined.split(/,(?=\s*[^;,=\s]+=[^;,]*)/g);
}

function portalCookie(cookie: string) {
  let value = cookie.replace(/;\s*Domain=[^;]+/gi, "");
  if (!/;\s*Path=/i.test(value)) value += "; Path=/";
  if (!/;\s*Secure/i.test(value)) value += "; Secure";
  if (!/;\s*SameSite=/i.test(value)) value += "; SameSite=Lax";
  return value;
}

const proxy: RequestHandler = async ({ request, params, url, fetch }) => {
  const methodPath = params.method || "";
  const upstreamUrl = new URL(`/api/method/${methodPath}${url.search}`, FRAPPE_ORIGIN);
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.set("X-Forwarded-Host", url.host);
  headers.set("X-Omni-Surface", "customer-portal");

  const upstream = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    redirect: "manual",
  });

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.set("Cache-Control", "private, no-store");
  const cookies = responseCookies(upstream.headers);
  if (cookies.length) {
    responseHeaders.delete("Set-Cookie");
    for (const cookie of cookies) responseHeaders.append("Set-Cookie", portalCookie(cookie));
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
