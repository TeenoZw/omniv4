import { browser } from "$app/environment";
import { writable } from "svelte/store";

export const AUTH_TOKEN_KEY = "omni.auth.token";
export const REFRESH_TOKEN_KEY = "omni.auth.refreshToken";
export const HUB_ID_KEY = "omni.auth.hubId";
export const HUB_CODE_KEY = "omni.auth.hubCode";
export const HUB_NAME_KEY = "omni.auth.hubName";
export const HUBS_KEY = "omni.auth.hubs";
export const ROLES_KEY = "omni.auth.roles";
export const USER_EMAIL_KEY = "omni.auth.userEmail";
export const TOKEN_EXPIRES_AT_KEY = "omni.auth.expiresAt";

export type SessionHub = {
  id: string;
  code: string;
  name: string;
  role?: string;
  subscription_tier?: string;
  status?: string;
};

export type SessionState = {
  token: string;
  refreshToken?: string;
  hubId: string;
  hubCode: string;
  hubName?: string;
  hubs: SessionHub[];
  roles: string[];
  userEmail?: string;
  expiresAt?: string;
  forceLogoutCountdown?: boolean;
};

type PersistOptions = {
  persistent?: boolean;
};

const DEFAULT_SESSION_DURATION_MS = 1000 * 60 * 15;

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeStorage(storage: Storage, state: SessionState) {
  storage.setItem(AUTH_TOKEN_KEY, state.token);
  if (state.refreshToken) {
    storage.setItem(REFRESH_TOKEN_KEY, state.refreshToken);
  }
  storage.setItem(HUB_ID_KEY, state.hubId);
  storage.setItem(HUB_CODE_KEY, state.hubCode);
  if (state.hubName) {
    storage.setItem(HUB_NAME_KEY, state.hubName);
  }
  storage.setItem(HUBS_KEY, JSON.stringify(state.hubs ?? []));
  storage.setItem(ROLES_KEY, JSON.stringify(state.roles ?? []));
  if (state.userEmail) {
    storage.setItem(USER_EMAIL_KEY, state.userEmail);
  }
  if (state.expiresAt) {
    storage.setItem(TOKEN_EXPIRES_AT_KEY, state.expiresAt);
  }
}

function parseExpiry(candidate: string | number | undefined | null): number | null {
  if (typeof candidate === "number" && Number.isFinite(candidate)) {
    return candidate;
  }
  if (typeof candidate === "string") {
    const parsed = Date.parse(candidate);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return null;
}

function nextExpiryTimestamp(durationMs = DEFAULT_SESSION_DURATION_MS) {
  return Date.now() + durationMs;
}

function nextExpiryIso(durationMs = DEFAULT_SESSION_DURATION_MS) {
  return new Date(nextExpiryTimestamp(durationMs)).toISOString();
}

function readFromStorage(storage: Storage): SessionState | null {
  const token = storage.getItem(AUTH_TOKEN_KEY);
  const hubId = storage.getItem(HUB_ID_KEY);
  const hubCode = storage.getItem(HUB_CODE_KEY);
  if (!token || !hubId || !hubCode) {
    return null;
  }

  const hubs = safeParse<SessionHub[]>(storage.getItem(HUBS_KEY), []);
  const roles = safeParse<string[]>(storage.getItem(ROLES_KEY), []);
  const hubNameFromStorage = storage.getItem(HUB_NAME_KEY) ?? undefined;
  const selectedHub = hubs.find((hub) => hub.id === hubId);
  const parsedExpiry = parseExpiry(storage.getItem(TOKEN_EXPIRES_AT_KEY));

  return {
    token,
    refreshToken: storage.getItem(REFRESH_TOKEN_KEY) ?? undefined,
    hubId,
    hubCode,
    hubName: selectedHub?.name ?? hubNameFromStorage,
    hubs,
    roles,
    userEmail: storage.getItem(USER_EMAIL_KEY) ?? undefined,
    expiresAt: parsedExpiry ? new Date(parsedExpiry).toISOString() : nextExpiryIso(),
    forceLogoutCountdown: false,
  };
}

export function getSession(): SessionState | null {
  if (!browser) return null;
  return readFromStorage(localStorage) ?? readFromStorage(sessionStorage);
}

export const sessionStore = writable<SessionState | null>(getSession());

function refreshStore() {
  sessionStore.set(getSession());
}

export function persistSession(state: SessionState, options: PersistOptions = {}) {
  if (!browser) return;
  const persistent = options.persistent ?? true;
  clearSession();
  writeStorage(persistent ? localStorage : sessionStorage, {
    ...state,
    forceLogoutCountdown: false,
    expiresAt: state.expiresAt ?? nextExpiryIso(),
  });
  refreshStore();
}

export function clearSession() {
  if (!browser) return;
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(AUTH_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
    storage.removeItem(HUB_ID_KEY);
    storage.removeItem(HUB_CODE_KEY);
    storage.removeItem(HUB_NAME_KEY);
    storage.removeItem(HUBS_KEY);
    storage.removeItem(ROLES_KEY);
    storage.removeItem(USER_EMAIL_KEY);
    storage.removeItem(TOKEN_EXPIRES_AT_KEY);
  }
  refreshStore();
}

export function switchHub(hubId: string) {
  if (!browser || !hubId) return;

  for (const storage of [localStorage, sessionStorage]) {
    const session = readFromStorage(storage);
    if (!session) continue;

    const selectedHub = session.hubs.find((hub) => hub.id === hubId);
    if (!selectedHub) continue;

    storage.setItem(HUB_ID_KEY, selectedHub.id);
    storage.setItem(HUB_CODE_KEY, selectedHub.code);
    storage.setItem(HUB_NAME_KEY, selectedHub.name);
    break;
  }

  refreshStore();
}

function isPersistentSession(current: SessionState | null) {
  if (!browser || !current?.token) return true;
  return localStorage.getItem(AUTH_TOKEN_KEY) === current.token;
}

export function extendSession(durationMs = DEFAULT_SESSION_DURATION_MS) {
  if (!browser) return;
  const current = getSession();
  if (!current?.token) return;
  persistSession(
    {
      ...current,
      expiresAt: nextExpiryIso(durationMs),
      forceLogoutCountdown: false,
    },
    { persistent: isPersistentSession(current) },
  );
}

export function forceExpiryCountdown(durationMs = 10000) {
  if (!browser) return;
  const current = getSession();
  if (!current?.token) return;
  persistSession(
    {
      ...current,
      expiresAt: nextExpiryIso(Math.max(3000, durationMs)),
      forceLogoutCountdown: true,
    },
    { persistent: isPersistentSession(current) },
  );
}

export function getAuthHeaders(additional: Record<string, string> = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...additional,
  };

  const session = getSession();
  if (session?.token) {
    headers.Authorization = `Bearer ${session.token}`;
  }
  if (session?.hubId) {
    headers["X-Hub-ID"] = session.hubId;
  }

  return headers;
}
