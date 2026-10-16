import type { Cookies } from "@sveltejs/kit";

export const FRAPPE_ORIGIN = "https://admin-v4.omnilogistics.co.zw";
export const PORTAL_SESSION_COOKIE = "omni_portal_sid";

export function responseCookies(headers: Headers) {
  const runtimeHeaders = headers as Headers & {
    getAll?: (name: string) => string[];
    getSetCookie?: () => string[];
  };
  if (typeof runtimeHeaders.getAll === "function") {
    const values = runtimeHeaders.getAll("Set-Cookie");
    if (values.length) return values;
  }
  if (typeof runtimeHeaders.getSetCookie === "function") {
    const values = runtimeHeaders.getSetCookie();
    if (values.length) return values;
  }

  const combined = headers.get("Set-Cookie");
  return combined ? combined.split(/,(?=\s*[^;,=\s]+=[^;,]*)/g) : [];
}

export function applyPortalSessionCookie(cookieHeader: string, cookies: Cookies) {
  const parts = cookieHeader.split(";").map((part) => part.trim());
  const [nameValue, ...attributes] = parts;
  const separator = nameValue.indexOf("=");
  if (separator < 1 || nameValue.slice(0, separator) !== "sid") return false;

  const value = nameValue.slice(separator + 1);
  const options: Parameters<Cookies["set"]>[2] = {
    path: "/",
    secure: true,
    httpOnly: true,
    sameSite: "lax",
  };

  for (const attribute of attributes) {
    const [rawName, ...rawValue] = attribute.split("=");
    const attributeName = rawName.toLowerCase();
    const attributeValue = rawValue.join("=");
    if (attributeName === "max-age" && Number.isFinite(Number(attributeValue))) {
      options.maxAge = Number(attributeValue);
    }
    if (attributeName === "expires" && attributeValue) {
      const expires = new Date(attributeValue);
      if (!Number.isNaN(expires.getTime())) options.expires = expires;
    }
  }

  cookies.set(PORTAL_SESSION_COOKIE, value, options);
  return value !== "Guest" && value !== "";
}

export function upstreamCookieHeader(requestHeaders: Headers, cookies: Cookies) {
  const values = (requestHeaders.get("cookie") || "")
    .split(";")
    .map((cookie) => cookie.trim())
    .filter((cookie) => cookie && !/^(sid|omni_portal_sid)=/i.test(cookie));
  const portalSession = cookies.get(PORTAL_SESSION_COOKIE);
  if (portalSession) values.push(`sid=${portalSession}`);
  return values.join("; ");
}
