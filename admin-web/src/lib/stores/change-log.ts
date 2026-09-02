import { writable } from "svelte/store";

export type ChangeLogEntry = {
  id: string;
  timestamp: string;
  actor: string;
  action: "update" | "delete" | "bulk-update" | "bulk-delete";
  summary: string;
  details: string;
  deviceIds: string[];
};

const STORAGE_KEY = "omni-admin-change-log";
const MAX_ENTRIES = 200;

function readFromStorage(): ChangeLogEntry[] {
  if (typeof localStorage === "undefined") {
    return [];
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((entry) => typeof entry?.id === "string");
  } catch (error) {
    console.warn("Failed to parse stored change log", error);
    return [];
  }
}

function persist(entries: ChangeLogEntry[]) {
  if (typeof localStorage === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch (error) {
    console.warn("Failed to persist change log", error);
  }
}

const { subscribe, set, update } = writable<ChangeLogEntry[]>(readFromStorage());

export const changeLogStore = {
  subscribe,
  addEntry(entry: ChangeLogEntry) {
    update((current) => {
      const next = [entry, ...current].slice(0, MAX_ENTRIES);
      persist(next);
      return next;
    });
  },
  replace(entries: ChangeLogEntry[]) {
    const normalized = entries.slice(0, MAX_ENTRIES);
    set(normalized);
    persist(normalized);
  },
  clear() {
    set([]);
    persist([]);
  },
  hydrate() {
    const latest = readFromStorage();
    set(latest);
  },
};
