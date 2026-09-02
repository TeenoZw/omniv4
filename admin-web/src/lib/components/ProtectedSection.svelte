<script>
  import { createEventDispatcher } from "svelte";
  import { sessionStore } from "$lib/stores/session";

  export let title = "Sign in required";
  export let ctaLabel = "Open login";

  const dispatch = createEventDispatcher();
  $: session = $sessionStore;
  $: isAuthenticated = Boolean(session?.token);

  function requestLogin() {
    dispatch("requestLogin");
  }
</script>

{#if isAuthenticated}
  <slot />
{:else}
  <div class="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-900 dark:border-white/15 dark:bg-black/30 dark:text-white">
    <p class="text-sm uppercase tracking-[0.4em] text-primary">{title}</p>
    <button
      class="mt-6 inline-flex items-center justify-center rounded-full border border-slate-300 bg-slate-50 px-6 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-100 dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
      type="button"
      on:click={requestLogin}
    >
      {ctaLabel}
    </button>
  </div>
{/if}
