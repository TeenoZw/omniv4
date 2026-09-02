import { writable } from "svelte/store";

export type ToastTone = "default" | "success" | "error";

export type ToastEntry = {
  id: string;
  title: string;
  message: string;
  tone: ToastTone;
};

const { subscribe, update } = writable<ToastEntry[]>([]);

function remove(id: string) {
  update((items) => items.filter((item) => item.id !== id));
}

function push({
  title,
  message,
  tone = "default",
  duration = 3500,
}: {
  title: string;
  message: string;
  tone?: ToastTone;
  duration?: number;
}) {
  const id = globalThis.crypto?.randomUUID?.() ?? `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const entry: ToastEntry = { id, title, message, tone };
  update((items) => [...items, entry]);
  if (typeof window !== "undefined") {
    window.setTimeout(() => remove(id), duration);
  }
  return id;
}

export const toastStore = {
  subscribe,
  push,
  remove,
};
