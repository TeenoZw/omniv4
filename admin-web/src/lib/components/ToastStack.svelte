<script lang="ts">
  import { CheckCircle2, AlertTriangle, Info } from "lucide-svelte";
  import { toastStore, type ToastEntry } from "$lib/stores/toast";

  let items: ToastEntry[] = [];

  const unsubscribe = toastStore.subscribe((value) => {
    items = value;
  });

  const toneClasses = {
    default: "border-slate-200 bg-background text-foreground",
    success: "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100",
    error: "border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100",
  };

  const icons = {
    default: Info,
    success: CheckCircle2,
    error: AlertTriangle,
  };
</script>

<svelte:head />

{#if items.length}
  <div class="pointer-events-none fixed right-4 top-4 z-[110] flex w-full max-w-sm flex-col gap-3">
    {#each items as item (item.id)}
      {@const Icon = icons[item.tone]}
      <div class={`pointer-events-auto rounded-2xl border px-4 py-3 shadow-xl ${toneClasses[item.tone]}`}>
        <div class="flex items-start gap-3">
          <div class="mt-0.5">
            <Icon class="h-5 w-5" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold">{item.title}</p>
            <p class="mt-1 text-sm opacity-90">{item.message}</p>
          </div>
          <button
            type="button"
            class="rounded-md p-1 text-current/70 hover:bg-black/5 dark:hover:bg-white/10"
            on:click={() => toastStore.remove(item.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      </div>
    {/each}
  </div>
{/if}
