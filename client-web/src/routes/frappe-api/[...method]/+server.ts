import type { RequestHandler } from "./$types";

const FRAPPE_ORIGIN = "https://admin-v4.omnilogistics.co.zw";

function responseCookies(headers: Headers) {
  const cloudflareHeaders = headers as Headers & {
    getAll?: (name: string) => string[];
    getSetCookie?: () => string[];
  };
  if (typeof cloudflareHeaders.getAll === "function") {
    const cookies = cloudflareHeaders.getAll("Set-Cookie");
    if (cookies.length) return cookies;
  }
  if (typeof cloudflareHeaders.getSetCookie === "function") {
    const cookies = cloudflareHeaders.getSetCookie();
    if (cookies.length) return cookies;
  }

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

function applyPortalCookie(
  cookieHeader: string,
  cookies: Parameters<RequestHandler>[0]["cookies"],
) {
  const parts = cookieHeader.split(";").map((part) => part.trim());
  const [nameValue, ...attributes] = parts;
  const separator = nameValue.indexOf("=");
  if (separator < 1) return;

  const name = nameValue.slice(0, separator);
  const value = nameValue.slice(separator + 1);
  const options: Parameters<typeof cookies.set>[2] = {
    path: "/",
    secure: true,
    sameSite: "lax",
  };

  for (const attribute of attributes) {
    const [rawName, ...rawValue] = attribute.split("=");
    const attributeName = rawName.toLowerCase();
    const attributeValue = rawValue.join("=");

    if (attributeName === "httponly") options.httpOnly = true;
    if (attributeName === "secure") options.secure = true;
    if (attributeName === "path" && attributeValue) options.path = attributeValue;
    if (attributeName === "max-age" && Number.isFinite(Number(attributeValue))) {
      options.maxAge = Number(attributeValue);
    }
    if (attributeName === "expires" && attributeValue) {
      const expires = new Date(attributeValue);
      if (!Number.isNaN(expires.getTime())) options.expires = expires;
    }
    if (attributeName === "samesite") {
      const sameSite = attributeValue.toLowerCase();
      if (["lax", "strict", "none"].includes(sameSite)) {
        options.sameSite = sameSite as "lax" | "strict" | "none";
      }
    }
  }

  cookies.set(name, value, options);
}

const proxy: RequestHandler = async ({ request, params, url, cookies }) => {
  const methodPath = params.method || "";
  const upstreamUrl = new URL(`/api/method/${methodPath}${url.search}`, FRAPPE_ORIGIN);
  const headers = new Headers(request.headers);
  headers.delete("host");
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
      applyPortalCookie(portalCookie(cookie), cookies);
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
