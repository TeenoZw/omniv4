import { redirect } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { applyPortalSessionCookie, FRAPPE_ORIGIN, responseCookies } from "$lib/server/frappe-session";

export const POST: RequestHandler = async ({ request, cookies }) => {
  const form = await request.formData();
  const usr = String(form.get("usr") || "").trim();
  const pwd = String(form.get("pwd") || "");
  if (!usr || !pwd) redirect(303, "/portal?login_error=missing");

  const upstream = await fetch(`${FRAPPE_ORIGIN}/api/method/login`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ usr, pwd }),
    redirect: "manual",
  });

  let authenticated = false;
  for (const cookie of responseCookies(upstream.headers)) {
    authenticated = applyPortalSessionCookie(cookie, cookies) || authenticated;
  }
  if (!upstream.ok || !authenticated) redirect(303, "/portal?login_error=invalid");

  redirect(303, "/portal");
};
