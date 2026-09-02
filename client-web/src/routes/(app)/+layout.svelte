<script lang="ts">
  import { browser } from "$app/environment";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import AppHeader from "$lib/components/layout/AppHeader.svelte";
  import AppSidebar from "$lib/components/layout/AppSidebar.svelte";
  import SessionExpiryWatcher from "$lib/components/SessionExpiryWatcher.svelte";
  import { getSession, sessionStore } from "$lib/api/session";

  let hasCheckedSession = false;

  $: session = $sessionStore;
  $: if (browser && hasCheckedSession && !session?.token) {
    void goto("/login");
  }

  onMount(async () => {
    if (!getSession()) {
      await goto("/login");
      return;
    }
    hasCheckedSession = true;
  });
</script>

<div class="omni-shell-bg min-h-screen text-foreground">
  <div class="pointer-events-none fixed inset-0 -z-10">
    <div class="omni-grid-overlay absolute inset-0 opacity-60"></div>
  </div>
  <SessionExpiryWatcher warningWindowMs={60000} />
  <div class="flex min-h-screen">
    <AppSidebar />
    <div class="flex min-h-screen flex-1 flex-col">
      <AppHeader />
      <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <div class="mx-auto w-full max-w-[1480px]">
          <slot />
        </div>
      </main>
    </div>
  </div>
</div>
