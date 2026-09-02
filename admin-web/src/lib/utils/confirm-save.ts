import { confirmDialogStore } from "$lib/stores/confirm-dialog";

function blurActiveElement() {
  if (typeof document === "undefined") return;
  const activeElement = document.activeElement;
  if (activeElement instanceof HTMLElement) {
    activeElement.blur();
  }
}

type ConfirmSaveOptions = {
  title?: string;
  description?: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "destructive";
};

export async function confirmSave(options: string | ConfirmSaveOptions = "Save these changes?"): Promise<boolean> {
  const config =
    typeof options === "string"
      ? {
          title: "Confirm changes",
          description: "",
          message: options,
          confirmLabel: "Yes, continue",
          cancelLabel: "Cancel",
          tone: "default" as const,
        }
      : {
          title: options.title ?? "Confirm action",
          description: options.description ?? "",
          message: options.message ?? "Save these changes?",
          confirmLabel: options.confirmLabel ?? "Yes, continue",
          cancelLabel: options.cancelLabel ?? "Cancel",
          tone: options.tone ?? "default",
        };
  blurActiveElement();
  if (typeof window !== "undefined") {
    const confirmed = await confirmDialogStore.open(config);
    if (!confirmed) {
      confirmDialogStore.close();
      return false;
    }
  }
  confirmDialogStore.close();
  blurActiveElement();
  return true;
}

export async function confirmAndRun(
  options: string | ConfirmSaveOptions,
  action: () => Promise<void> | void,
): Promise<boolean> {
  const config =
    typeof options === "string"
      ? { title: "Confirm action", description: "", message: options, confirmLabel: "Yes, continue", cancelLabel: "Cancel", tone: "default" as const }
      : {
          title: options.title ?? "Confirm action",
          description: options.description ?? "",
          message: options.message ?? "Proceed with this action?",
          confirmLabel: options.confirmLabel ?? "Yes, continue",
          cancelLabel: options.cancelLabel ?? "Cancel",
          tone: options.tone ?? "default",
        };
  blurActiveElement();
  if (typeof window === "undefined") {
    await action();
    resetFocusAfterSave();
    return true;
  }
  const confirmed = await confirmDialogStore.open(config);
  if (!confirmed) {
    confirmDialogStore.close();
    return false;
  }
  confirmDialogStore.setPending(true);
  try {
    await action();
    return true;
  } finally {
    confirmDialogStore.setPending(false);
    confirmDialogStore.close();
    resetFocusAfterSave();
  }
}

export function resetFocusAfterSave() {
  blurActiveElement();
}
