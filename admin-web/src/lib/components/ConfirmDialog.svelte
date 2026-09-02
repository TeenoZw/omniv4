<script lang="ts">
  import { onDestroy, tick } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { confirmDialogStore } from "$lib/stores/confirm-dialog";
  import { AlertTriangle, Save, ShieldAlert } from "lucide-svelte";

  let state = {
    open: false,
    title: "Confirm action",
    description: "",
    message: "",
    confirmLabel: "Confirm",
    cancelLabel: "Cancel",
    tone: "default" as "default" | "destructive",
    pending: false,
  };

  let confirmButton: HTMLButtonElement | null = null;
  let dialogCard: HTMLDivElement | null = null;

  const unsubscribe = confirmDialogStore.subscribe(async (value) => {
    state = value;
    if (state.open) {
      await tick();
      confirmButton?.focus();
    }
  });

  onDestroy(unsubscribe);

  function handleConfirm() {
    confirmDialogStore.confirm();
  }

  function handleCancel() {
    if (state.pending) return;
    confirmDialogStore.cancel();
  }

  function handleKeydown(event: KeyboardEvent) {
    if (!state.open) return;
    if (event.key === "Escape") {
      event.preventDefault();
      handleCancel();
      return;
    }
    if (event.key === "Tab" && dialogCard) {
      const focusable = Array.from(
        dialogCard.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((node) => !node.hasAttribute("disabled"));
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }
  $: Icon = state.tone === "destructive" ? ShieldAlert : Save;
</script>

<svelte:window on:keydown={handleKeydown} />

{#if state.open}
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
    <div
      bind:this={dialogCard}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      class="w-full max-w-md rounded-2xl border border-slate-200 bg-background shadow-2xl"
    >
      <div class="border-b px-6 py-4">
        <div class="flex items-start gap-3">
          <div class={`mt-0.5 rounded-2xl p-2 ${state.tone === "destructive" ? "bg-destructive/10 text-destructive" : "bg-primary/10 text-primary"}`}>
            <Icon class="h-5 w-5" />
          </div>
          <div class="space-y-1">
            <h2 id="confirm-dialog-title" class="text-lg font-semibold">{state.title}</h2>
            {#if state.description}
              <p class="text-xs uppercase tracking-wide text-muted-foreground">{state.description}</p>
            {/if}
          </div>
        </div>
      </div>
      <div class="px-6 py-5">
        <p id="confirm-dialog-message" class="text-sm text-muted-foreground">{state.message}</p>
      </div>
      <div class="flex items-center justify-end gap-2 border-t px-6 py-4">
        <Button variant="outline" onclick={handleCancel} disabled={state.pending}>{state.cancelLabel}</Button>
        <Button bind:ref={confirmButton} variant={state.tone === "destructive" ? "destructive" : "default"} onclick={handleConfirm} disabled={state.pending}>
          {state.pending ? "Processing..." : state.confirmLabel}
        </Button>
      </div>
    </div>
  </div>
{/if}
