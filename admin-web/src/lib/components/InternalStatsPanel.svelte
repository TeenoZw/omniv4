<script>
  import { onDestroy, onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { fetchAdminStats } from "$lib/api/stats";

  let stats = null;
  let loading = false;
  let pollHandle = null;
  let selectedMetric = "users";

  async function loadStats() {
    loading = true;
    try {
      stats = await fetchAdminStats();
    } finally {
      loading = false;
    }
  }

  function startPolling() {
    pollHandle = setInterval(() => {
      void loadStats();
    }, 15000);
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

  $: metricCards = [
    { key: "users", label: "Landing: Active users", value: stats?.totals?.users ?? 0 },
    { key: "devices", label: "Landing: Active assets", value: stats?.totals?.devices ?? 0 },
    { key: "hubs", label: "Managed hubs", value: stats?.totals?.hubs ?? 0 },
    { key: "subscriptions", label: "Active subscriptions", value: stats?.totals?.activeSubscriptions ?? 0 },
  ];

  $: selectedMetricTitle =
    metricCards.find((metric) => metric.key === selectedMetric)?.label ?? "Details";
</script>

<section class="space-y-4">
  <header class="flex items-center justify-between">
    <div>
      <p class="text-sm font-medium text-primary">Internal Analytics</p>
      <h2 class="text-2xl font-bold">Realtime stats counters</h2>
    </div>
    <Button size="sm" variant="outline" onclick={loadStats} disabled={loading}>
      {loading ? "Refreshing..." : "Refresh counters"}
    </Button>
  </header>

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    {#each metricCards as metric (metric.key)}
      <button
        type="button"
        class={`rounded-xl border bg-card p-4 text-left transition ${selectedMetric === metric.key ? "border-primary" : "hover:border-primary/60"}`}
        onclick={() => (selectedMetric = metric.key)}
      >
        <p class="text-xs uppercase tracking-wide text-muted-foreground">{metric.label}</p>
        <p class="mt-2 text-2xl font-bold">{metric.value}</p>
      </button>
    {/each}
  </div>

  <div class="rounded-xl border bg-card p-4">
    <h3 class="text-sm font-semibold">{selectedMetricTitle}</h3>
    {#if loading && !stats}
      <div class="omni-loading-state mt-3">
        <span class="omni-loading-spinner" aria-hidden="true"></span>
        <span>Loading statistics…</span>
      </div>
    {:else if !stats}
      <p class="mt-3 text-sm text-muted-foreground">No data.</p>
    {:else if selectedMetric === "hubs"}
      <div class="mt-3 max-h-64 overflow-auto rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-3 py-2 text-left">Hub</th>
              <th class="px-3 py-2 text-left">Code</th>
              <th class="px-3 py-2 text-left">Tier</th>
              <th class="px-3 py-2 text-right">Devices</th>
              <th class="px-3 py-2 text-right">Users</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.hierarchy ?? [] as hub (hub.id)}
              <tr class="border-t">
                <td class="px-3 py-2">{hub.name}</td>
                <td class="px-3 py-2 font-mono text-xs">{hub.code}</td>
                <td class="px-3 py-2">{hub.tier}</td>
                <td class="px-3 py-2 text-right">{hub.deviceCount ?? 0}</td>
                <td class="px-3 py-2 text-right">{hub.users?.length ?? 0}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else if selectedMetric === "devices"}
      <div class="mt-3 max-h-64 overflow-auto rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-3 py-2 text-left">Status</th>
              <th class="px-3 py-2 text-right">Count</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.deviceStatus ?? [] as item (item.id)}
              <tr class="border-t">
                <td class="px-3 py-2">{item.id}</td>
                <td class="px-3 py-2 text-right">{item.count}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else if selectedMetric === "users"}
      <div class="mt-3 max-h-64 overflow-auto rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-3 py-2 text-left">Hub</th>
              <th class="px-3 py-2 text-right">Users</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.hierarchy ?? [] as hub (hub.id)}
              <tr class="border-t">
                <td class="px-3 py-2">{hub.name}</td>
                <td class="px-3 py-2 text-right">{hub.users?.length ?? 0}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="mt-3 max-h-64 overflow-auto rounded-lg border">
        <table class="w-full text-sm">
          <thead class="bg-muted/40 text-xs uppercase text-muted-foreground">
            <tr>
              <th class="px-3 py-2 text-left">Hub</th>
              <th class="px-3 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.hierarchy ?? [] as hub (hub.id)}
              <tr class="border-t">
                <td class="px-3 py-2">{hub.name}</td>
                <td class="px-3 py-2 capitalize">{hub.status ?? "unknown"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>

</section>
