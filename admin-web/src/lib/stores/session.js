import { writable } from "svelte/store";
import { registerAuthHooks, setSessionHeaders } from "$lib/api/http";

const STORAGE_KEY = "omni-admin-session";
const DEFAULT_SESSION_DURATION_MS = 1000 * 60 * 15; // 15 minutes

function parseExpiry(candidate) {
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

const emptySession = {
  token: null,
  refreshToken: null,
  user: null,
  roles: [],
  hubs: [],
  currentHubId: null,
  currentHub: null,
  expiresAt: null,
  forceLogoutCountdown: false,
};

function isAdminRole(value) {
  return (value ?? "").toString().trim().toLowerCase() === "admin";
}

function defaultHubIdForRoles(hubs = [], roles = [], explicitHubId) {
  if (Object.prototype.hasOwnProperty.call({ explicitHubId }, "explicitHubId") && explicitHubId !== undefined) {
    return explicitHubId;
  }
  return roles.some(isAdminRole) ? null : hubs[0]?.id ?? null;
}

function loadSession() {
  if (typeof localStorage === "undefined") {
    return { ...emptySession };
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { ...emptySession };
    }
    const parsed = JSON.parse(raw);
    const hubs = parsed?.hubs ?? [];
    const hasStoredHubId = Object.prototype.hasOwnProperty.call(parsed ?? {}, "currentHubId");
    const currentHubId = hasStoredHubId
      ? parsed?.currentHubId
      : defaultHubIdForRoles(hubs, parsed?.roles ?? []);
    const hasToken = Boolean(parsed?.token);
    const storedExpiry = parseExpiry(parsed?.expiresAt ?? parsed?.expires_at);
    const expiresAt = hasToken ? storedExpiry ?? nextExpiryTimestamp() : null;
    return {
      ...emptySession,
      ...parsed,
      roles: parsed?.roles ?? [],
      hubs,
      currentHubId,
      currentHub: hubs.find((hub) => hub.id === currentHubId) ?? null,
      expiresAt,
      forceLogoutCountdown: Boolean(parsed?.forceLogoutCountdown) && hasToken,
    };
  } catch (error) {
    console.warn("Failed to parse stored session", error);
    return { ...emptySession };
  }
}

function persistSession(value) {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}

function normalizeSession(payload = {}) {
  const hubs = payload.hubs ?? [];
  const hasExplicitHubId = Object.prototype.hasOwnProperty.call(payload, "currentHubId");
  const upstreamHub = payload.default_hub_id ?? payload.hub_id ?? payload.hubId;
  const derivedHub = hasExplicitHubId
    ? payload.currentHubId
    : defaultHubIdForRoles(hubs, payload.roles ?? [], upstreamHub);
  const expiresCandidate =
    payload.expiresAt ??
    payload.expires_at ??
    (typeof payload.expires_in === "number"
      ? Date.now() + payload.expires_in * 1000
      : undefined) ??
    (typeof payload.expiresIn === "number"
      ? Date.now() + payload.expiresIn * 1000
      : undefined);
  const expiresAt = payload.token ?? payload.access_token
    ? parseExpiry(expiresCandidate) ?? nextExpiryTimestamp()
    : null;

  return {
    token: payload.token ?? payload.access_token ?? null,
    refreshToken: payload.refreshToken ?? payload.refresh_token ?? null,
    user: payload.user ?? null,
    roles: payload.roles ?? [],
    hubs,
    currentHubId: derivedHub,
    currentHub: hubs.find((hub) => hub.id === derivedHub) ?? null,
    expiresAt,
    forceLogoutCountdown: false,
  };
}

function createSessionStore() {
  const store = writable(loadSession());
  let snapshot = loadSession();

  store.subscribe((value) => {
    snapshot = value;
    persistSession(value);
    setSessionHeaders({ token: value.token, hubId: value.currentHubId });
  });

  return {
    subscribe: store.subscribe,
    login(sessionPayload) {
      store.set(normalizeSession(sessionPayload));
    },
    logout() {
      store.set({ ...emptySession });
      setSessionHeaders({ token: null, hubId: null });
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(STORAGE_KEY);
      }
    },
    getSession() {
      return snapshot;
    },
    mergeAuth(payload = {}) {
      store.update((current) => {
        if (!current?.token) {
          return current;
        }
        const expiresAt = payload.expiresIn
          ? Date.now() + payload.expiresIn * 1000
          : payload.expiresAt
            ? parseExpiry(payload.expiresAt)
            : nextExpiryTimestamp();
        return {
          ...current,
          token: payload.token ?? current.token,
          refreshToken: payload.refreshToken ?? current.refreshToken,
          expiresAt: expiresAt ?? nextExpiryTimestamp(),
          forceLogoutCountdown: false,
        };
      });
    },
    selectHub(hubId) {
      store.update((current) => {
        const normalizedHubId = hubId || null;
        const nextHub = current.hubs.find((hub) => hub.id === normalizedHubId) ?? null;
        return {
          ...current,
          currentHubId: normalizedHubId,
          currentHub: nextHub,
        };
      });
      setSessionHeaders({ hubId: hubId || null });
    },
    extendSession(durationMs = DEFAULT_SESSION_DURATION_MS) {
      store.update((current) => {
        if (!current?.token) {
          return current;
        }
        return {
          ...current,
          expiresAt: nextExpiryTimestamp(durationMs),
          forceLogoutCountdown: false,
        };
      });
    },
    forceExpiryCountdown(durationMs = 10000) {
      store.update((current) => {
        if (!current?.token) {
          return current;
        }
        return {
          ...current,
          expiresAt: Date.now() + Math.max(3000, durationMs),
          forceLogoutCountdown: true,
        };
      });
    },
  };
}

export const sessionStore = createSessionStore();

registerAuthHooks({
  getSession: () => sessionStore.getSession(),
  saveSession: (payload) => sessionStore.mergeAuth(payload),
  clearSession: () => sessionStore.logout(),
});
