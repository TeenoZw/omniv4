import { writable } from "svelte/store";

const STORAGE_KEY = "omni-admin-immutable-log";
const RETENTION_MS = 90 * 24 * 60 * 60 * 1000;

function nowIso() {
  return new Date().toISOString();
}

function parseTime(iso) {
  const value = Date.parse(iso ?? "");
  return Number.isNaN(value) ? 0 : value;
}

function prune(entries) {
  const cutoff = Date.now() - RETENTION_MS;
  return entries.filter((entry) => parseTime(entry.timestamp) >= cutoff);
}

function read() {
  if (typeof localStorage === "undefined") {
    return [];
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) {
      return [];
    }
    return prune(parsed);
  } catch (error) {
    console.warn("Unable to parse immutable admin logs", error);
    return [];
  }
}

function persist(entries) {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prune(entries)));
}

const { subscribe, set, update } = writable(read());

export const adminLogStore = {
  subscribe,
  append(entry) {
    update((current) => {
      const next = prune([
        {
          id: entry.id ?? globalThis.crypto?.randomUUID?.() ?? `log-${Date.now()}`,
          timestamp: entry.timestamp ?? nowIso(),
          actor: entry.actor ?? "system",
          action: entry.action ?? "update",
          scope: entry.scope ?? "admin",
          details: entry.details ?? "",
        },
        ...current,
      ]);
      persist(next);
      return next;
    });
  },
  hydrate() {
    const latest = read();
    set(latest);
    persist(latest);
  },
  clear() {
    set([]);
    persist([]);
  },
};
