import { browser } from "$app/environment";
import { AUTH_TOKEN_KEY, clearSession, getSession, persistSession } from "$lib/api/session";
import { refreshSession } from "$lib/api/auth";

export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

let refreshPromise: Promise<{ access_token: string; refresh_token?: string; expires_in?: number }> | null = null;

async function ensureRefreshedToken() {
  const session = getSession();
  if (!session?.refreshToken) {
    clearSession();
    throw new Error("Session expired");
  }
  if (!refreshPromise) {
    refreshPromise = refreshSession(session.refreshToken).finally(() => {
      refreshPromise = null;
    });
  }
  const refreshed = await refreshPromise;
  const expiresAt = refreshed.expires_in
    ? new Date(Date.now() + refreshed.expires_in * 1000).toISOString()
    : undefined;
  const wasPersistent =
    typeof localStorage !== "undefined" && localStorage.getItem(AUTH_TOKEN_KEY) === session.token;
  persistSession(
    {
      ...session,
      token: refreshed.access_token,
      refreshToken: refreshed.refresh_token ?? session.refreshToken,
      expiresAt,
    },
    { persistent: wasPersistent },
  );
  return refreshed.access_token;
}

function withAuthHeaders(headers: HeadersInit = {}): HeadersInit {
  const session = getSession();
  const enriched = new Headers(headers);
  if (!enriched.has("Content-Type")) {
    enriched.set("Content-Type", "application/json");
  }
  if (session?.token) {
    enriched.set("Authorization", `Bearer ${session.token}`);
  }
  if (session?.hubId) {
    enriched.set("X-Hub-ID", session.hubId);
  }
  return enriched;
}

export async function apiFetch(input: string, init: RequestInit = {}, allowRetry = true) {
  const url = input.startsWith("http") ? input : `${API_BASE}${input.startsWith("/") ? "" : "/"}${input}`;
  const response = await fetch(url, {
    ...init,
    headers: withAuthHeaders(init.headers ?? {}),
  });

  if (response.status !== 401 || !allowRetry || !browser) {
    return response;
  }

  try {
    const token = await ensureRefreshedToken();
    const retryHeaders = new Headers(withAuthHeaders(init.headers ?? {}));
    retryHeaders.set("Authorization", `Bearer ${token}`);
    return fetch(url, {
      ...init,
      headers: retryHeaders,
    });
  } catch (error) {
    clearSession();
    return response;
  }
}
