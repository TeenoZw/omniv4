<script>
  import { onDestroy, onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { fetchAdminStats } from "$lib/api/stats";

  let stats = null;
  let loading = false;
  let errorMessage = "";
  let expandedHubId = null;
  let pollHandle = null;

  const statCards = [
    { key: "hubs", label: "Hubs" },
    { key: "devices", label: "Devices" },
    { key: "users", label: "Users" },
    { key: "activeSubscriptions", label: "Active subscriptions" },
    { key: "pendingEnquiries", label: "Pending enquiries" },
  ];

  const simCards = [
    { key: "sims", label: "Managed SIMs" },
    { key: "assignedSims", label: "Assigned SIMs" },
    { key: "roamingEnabledSims", label: "Roaming enabled" },
    { key: "attentionSims", label: "Attention required" },
  ];

  async function loadStats() {
    loading = true;
    errorMessage = "";
    try {
      stats = await fetchAdminStats();
    } catch (error) {
      console.error("Unable to load admin stats", error);
      errorMessage = "Unable to load dashboard data.";
    } finally {
      loading = false;
    }
  }

  function toggleHub(hubId) {
    expandedHubId = expandedHubId === hubId ? null : hubId;
  }

  function startPolling() {
    pollHandle = setInterval(() => {
      void loadStats();
    }, 30000);
  }

  function prettyStatus(value) {
    return (value ?? "unknown").replaceAll("_", " ");
  }

  onMount(() => {
    void loadStats();
    startPolling();
  });

  onDestroy(() => {
    if (pollHandle) {
      clearInterval(pollHandle);
    }
  });
</script>

<section class="space-y-6">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Operations</p>
      <h2 class="omni-page-title">Dashboard</h2>
    </div>
    <Button variant="outline" size="sm" onclick={loadStats} disabled={loading}>
      {#if loading}Refreshing…{:else}Refresh{/if}
    </Button>
  </header>

  {#if errorMessage}
    <div class="rounded-[1.35rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
      {errorMessage}
    </div>
  {/if}

  {#if loading && !stats}
    <div class="omni-loading-state">
      <span class="omni-loading-spinner" aria-hidden="true"></span>
      <span>Loading dashboard data…</span>
    </div>
  {/if}

  <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    {#each statCards as item}
      <div class="omni-stat-card">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{item.label}</p>
        <p class="mt-2 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {stats?.totals?.[item.key] ?? 0}
        </p>
      </div>
    {/each}
  </section>

  <section class="omni-panel border-0 shadow-none">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">Connectivity</p>
        <h3 class="mt-1 text-xl font-semibold text-slate-950 dark:text-white">Managed SIM health</h3>
      </div>
      <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
        Econet fleet visibility
      </span>
    </div>
    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {#each simCards as item}
        <div class="omni-stat-card">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{item.label}</p>
          <p class="mt-2 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {stats?.totals?.[item.key] ?? 0}
          </p>
        </div>
      {/each}
    </div>
  </section>

  <div class="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
    <section class="omni-panel border-0 shadow-none">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">Hub structure</p>
          <h3 class="mt-1 text-xl font-semibold text-slate-950 dark:text-white">Hub hierarchy</h3>
        </div>
        <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
          {stats?.hierarchy?.length ?? 0} hubs
        </span>
      </div>

      <div class="space-y-3">
        {#if !stats?.hierarchy?.length}
          <div class="omni-empty-state">No hubs are currently available.</div>
        {:else}
          {#each stats.hierarchy as hub (hub.id)}
            <div class="rounded-[1.4rem] border border-white/70 bg-white/60 dark:border-white/10 dark:bg-slate-950/35">
              <button
                type="button"
                class="flex w-full items-center justify-between gap-3 px-4 py-4 text-left"
                on:click={() => toggleHub(hub.id)}
              >
                <div class="min-w-0">
                  <p class="font-semibold text-slate-950 dark:text-white">{hub.name}</p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {hub.code} · {hub.tier} · {prettyStatus(hub.status)}
                  </p>
                </div>
                <div class="grid min-w-[8rem] grid-cols-2 gap-2 text-right text-xs text-slate-500 dark:text-slate-400">
                  <div>
                    <p class="font-semibold text-slate-900 dark:text-white">{hub.users.length}</p>
                    <p>Users</p>
                  </div>
                  <div>
                    <p class="font-semibold text-slate-900 dark:text-white">{hub.deviceCount}</p>
                    <p>Devices</p>
                  </div>
                </div>
              </button>

              {#if expandedHubId === hub.id}
                <div class="grid gap-4 border-t border-white/70 px-4 py-4 dark:border-white/10 md:grid-cols-2">
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Users</p>
                    <ul class="mt-3 space-y-2">
                      {#if !hub.users.length}
                        <li class="text-sm text-muted-foreground">No users are currently assigned.</li>
                      {:else}
                        {#each hub.users as user (user.id)}
                          <li class="rounded-[1rem] border border-white/70 bg-white/70 px-3 py-3 text-sm dark:border-white/10 dark:bg-white/[0.03]">
                            <p class="font-medium text-slate-950 dark:text-white">{user.name}</p>
                            <p class="text-xs text-muted-foreground">{user.email} · {user.role}</p>
                          </li>
                        {/each}
                      {/if}
                    </ul>
                  </div>
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Devices</p>
                    <ul class="mt-3 space-y-2">
                      {#if !hub.devices.length}
                        <li class="text-sm text-muted-foreground">No devices are currently assigned.</li>
                      {:else}
                        {#each hub.devices.slice(0, 8) as device (device.id)}
                          <li class="rounded-[1rem] border border-white/70 bg-white/70 px-3 py-3 text-sm dark:border-white/10 dark:bg-white/[0.03]">
                            <p class="font-medium text-slate-950 dark:text-white">{device.imei}</p>
                            <p class="text-xs text-muted-foreground">{device.model ?? "Tracker"} · {prettyStatus(device.status)}</p>
                          </li>
                        {/each}
                      {/if}
                    </ul>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>
    </section>

    <section class="omni-panel border-0 shadow-none">
      <div class="mb-4">
        <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">Priority checks</p>
        <h3 class="mt-1 text-xl font-semibold text-slate-950 dark:text-white">Current focus</h3>
      </div>

      <div class="space-y-3">
        <div class="rounded-[1.25rem] border border-white/70 bg-white/70 px-4 py-4 dark:border-white/10 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Billing attention</p>
          <p class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{stats?.totals?.activeSubscriptions ?? 0}</p>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">Hubs currently marked active and billing-ready.</p>
        </div>
        <div class="rounded-[1.25rem] border border-white/70 bg-white/70 px-4 py-4 dark:border-white/10 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Enquiry load</p>
          <p class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{stats?.totals?.pendingEnquiries ?? 0}</p>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">Enquiries waiting for follow-up or commercial conversion.</p>
        </div>
      </div>
    </section>
  </div>
</section>
