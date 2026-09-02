import { writable } from "svelte/store";

type ConfirmDialogState = {
  open: boolean;
  message: string;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel: string;
  tone: "default" | "destructive";
  pending: boolean;
};

const initialState: ConfirmDialogState = {
  open: false,
  message: "",
  title: "Confirm action",
  description: "",
  confirmLabel: "Confirm",
  cancelLabel: "Cancel",
  tone: "default",
  pending: false,
};

const { subscribe, set, update } = writable<ConfirmDialogState>(initialState);

let resolver: ((value: boolean) => void) | null = null;

function settle(value: boolean) {
  if (resolver) {
    resolver(value);
    resolver = null;
  }
}

export const confirmDialogStore = {
  subscribe,
  open({
    title = "Confirm action",
    description = "",
    message,
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    tone = "default",
  }: {
    title?: string;
    description?: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    tone?: "default" | "destructive";
  }) {
    if (resolver) {
      settle(false);
    }
    update(() => ({
      open: true,
      title,
      description,
      message,
      confirmLabel,
      cancelLabel,
      tone,
      pending: false,
    }));
    return new Promise<boolean>((resolve) => {
      resolver = resolve;
    });
  },
  confirm() {
    settle(true);
  },
  cancel() {
    if (resolver) {
      resolver(false);
      resolver = null;
    }
    set(initialState);
  },
  close() {
    resolver = null;
    set(initialState);
  },
  setPending(pending: boolean) {
    update((state) => ({ ...state, pending }));
  },
  cancelAndClose() {
    settle(false);
    set(initialState);
  },
};
