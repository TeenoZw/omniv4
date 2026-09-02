import { writable } from "svelte/store";

export type HubChangeLogEntry = {
  id: string;
  timestamp: string;
  actor: string;
  action: "create" | "update" | "user-create" | "subscription";
  hubId: string;
  summary: string;
  details: string;
};

const STORAGE_KEY = "omni-hub-change-log";
const MAX_ENTRIES = 200;

function safeParse(value: string | null) {
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.warn("Failed to parse hub log", error);
    return [];
  }
}

function readFromStorage(): HubChangeLogEntry[] {
  if (typeof localStorage === "undefined") {
    return [];
  }
  return safeParse(localStorage.getItem(STORAGE_KEY));
}

function persist(entries: HubChangeLogEntry[]) {
  if (typeof localStorage === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch (error) {
    console.warn("Unable to persist hub change log", error);
  }
}

const { subscribe, update, set } = writable<HubChangeLogEntry[]>(readFromStorage());

export const hubChangeLogStore = {
  subscribe,
  append(entry: HubChangeLogEntry) {
    update((current) => {
      const next = [entry, ...current].slice(0, MAX_ENTRIES);
      persist(next);
      return next;
    });
  },
  hydrate() {
    set(readFromStorage());
  },
  clear() {
    set([]);
    persist([]);
  },
};
