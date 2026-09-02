<script>
  import { sessionStore } from "$lib/stores/session";

  const statusTokens = [
    { label: "Online", tone: "text-emerald-300", badge: "bg-emerald-500/15" },
    { label: "Syncing", tone: "text-amber-200", badge: "bg-amber-500/15" },
    { label: "Maintenance", tone: "text-sky-200", badge: "bg-sky-500/15" },
  ];

  $: session = $sessionStore;
  $: hubs = session?.hubs ?? [];
  $: activeHubId = session?.currentHubId;

  function deriveStatus(index) {
    return statusTokens[index % statusTokens.length];
  }
</script>

<div class="rounded-3xl border border-white/10 bg-black/40 p-6 text-white">
  <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.5em] text-primary">Hub Overview</p>
      <h2 class="mt-2 text-2xl font-semibold">Provisioned Sites</h2>
      <p class="text-sm text-white/70">Context pulled from the authenticated session payload.</p>
    </div>
    <div class="text-right">
      <p class="text-3xl font-semibold">{hubs.length}</p>
      <p class="text-xs uppercase tracking-widest text-white/60">Linked hubs</p>
    </div>
  </div>

  {#if hubs.length === 0}
    <div class="mt-8 rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-white/70">
      No hubs assigned to this account yet. Invite a deployment engineer to grant access.
    </div>
  {:else}
    <div class="mt-6 grid gap-4 md:grid-cols-2">
      {#each hubs as hub, index (hub.id)}
        {#if hub}
          {@const status = deriveStatus(index)}
          <article class="rounded-2xl border border-white/10 bg-black/30 p-5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-semibold">{hub.name}</p>
                <p class="text-xs text-white/60">{hub.id}</p>
              </div>
              {#if hub.role}
                <span class="rounded-full border border-white/20 px-3 py-1 text-xs text-white/70">{hub.role}</span>
              {/if}
            </div>
            <div class="mt-4 flex items-center justify-between text-sm text-white/80">
              <div class="flex items-center gap-2">
                {#if hub.id === activeHubId}
                  <span class="inline-flex h-2 w-2 rounded-full bg-emerald-400"></span>
                  <span>Active context</span>
                {:else}
                  <span class="inline-flex h-2 w-2 rounded-full bg-white/30"></span>
                  <span>Available</span>
                {/if}
              </div>
              <span class={`rounded-full ${status.badge} px-3 py-1 text-xs ${status.tone}`}>
                {status.label}
              </span>
            </div>
          </article>
        {/if}
      {/each}
    </div>
  {/if}
</div>
