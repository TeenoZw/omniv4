<script>
  import { createEventDispatcher } from "svelte";
  import { sessionStore } from "$lib/stores/session";

  const dispatch = createEventDispatcher();

  $: session = $sessionStore;
  $: user = session?.user ?? {};
  $: hubs = session?.hubs ?? [];
  $: managedHubCount = hubs.length;
  $: roleLabel = (session?.roles ?? []).join(", ") || "Omni Admin";

  function handleLogout() {
    dispatch("logout");
  }

</script>

<div class="border-t border-white/5 bg-black/70 text-white">
  <div class="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 text-sm lg:flex-row lg:items-center lg:justify-between">
    <div class="flex items-center gap-3">
      <div class="flex h-12 w-12 items-center justify-center rounded-full bg-primary/30 text-base font-semibold text-white">
        {user?.name ? user.name.slice(0, 2).toUpperCase() : "AD"}
      </div>
      <div>
        <p class="text-sm font-semibold">{user?.name ?? "Admin User"}</p>
        <p class="text-xs text-white/60">{user?.email ?? "ops@omni.dev"}</p>
        <p class="text-xs text-white/60">Roles: {roleLabel}</p>
      </div>
    </div>

    <div class="flex flex-col gap-3 text-xs uppercase tracking-[0.4em] text-white/60 sm:flex-row sm:items-center">
      <div class="flex flex-col gap-1 text-left normal-case tracking-normal text-white/70">
        <span class="text-[0.65rem] uppercase tracking-[0.5em] text-white/50">Managed hubs</span>
        <span class="text-base font-semibold normal-case tracking-normal text-white">{managedHubCount}</span>
      </div>
      <div class="rounded-full border border-white/20 px-4 py-1 text-[0.65rem] uppercase tracking-[0.4em] text-white/80">
        Omni Logistics Platform
      </div>
    </div>

    <div class="flex flex-wrap gap-3 text-sm text-white/80">
      <button
        class="rounded-2xl border border-red-500/50 px-4 py-2 text-xs uppercase tracking-widest text-red-200 hover:bg-red-500/10"
        type="button"
        on:click={handleLogout}
      >
        Logout
      </button>
    </div>
  </div>
</div>
