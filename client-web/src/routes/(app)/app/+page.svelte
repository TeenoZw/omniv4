<script lang="ts">
  import { onDestroy } from "svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { buttonVariants } from "$lib/components/ui/button";
  import { cn } from "$lib/utils.js";
  import {
    fetchCurrentHubAssetDetail,
    fetchCurrentHubAssets,
    fetchCurrentHubSummary,
    type HubAsset,
    type HubAssetDetail,
    type HubSummaryResponse,
  } from "$lib/api/hub";
  import { sessionStore } from "$lib/api/session";

  const supportEmail = "support@omnilogistics.co.zw";

  let summary: HubSummaryResponse | null = null;
  let summaryLoading = true;
  let summaryRefreshing = false;
  let errorMessage = "";
  let lastHubId: string | null = null;
  let lastAssetsHubId: string | null = null;
  let pollHandle: ReturnType<typeof setInterval> | null = null;
  let assets: HubAsset[] = [];
  let assetsLoading = false;
  let assetsRefreshing = false;
  let assetsError = "";
  let assetSearch = "";
  let assetPage = 1;
  let assetPerPage = 10;
  let assetTotal = 0;
  let assetSearchDebounce: ReturnType<typeof setTimeout> | null = null;
  let lastAssetFilterSignature = "";
  let selectedAssetId: string | null = null;
  let selectedAssetDetail: HubAssetDetail | null = null;
  let assetDetailLoading = false;

  $: session = $sessionStore;
  $: currentHubId = session?.hubId ?? null;

  async function loadHubSummary(hubId: string, force = false) {
    if (!hubId || (!force && hubId === lastHubId)) return;
    const isHubSwitch = hubId !== lastHubId;
    lastHubId = hubId;
    if (!summary || isHubSwitch) {
      summaryLoading = true;
    } else if (force) {
      summaryRefreshing = true;
    }
    if (!summary) {
      errorMessage = "";
    }
    try {
      summary = await fetchCurrentHubSummary();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to load your dashboard summary.";
    } finally {
      summaryLoading = false;
      summaryRefreshing = false;
    }
  }

  async function loadHubAssets(hubId: string, force = false) {
    if (!hubId || (!force && hubId === lastAssetsHubId && !assetSearch && assetPage === 1 && assetPerPage === 10)) return;
    const isHubSwitch = hubId !== lastAssetsHubId;
    lastAssetsHubId = hubId;
    if (!assets.length || isHubSwitch) {
      assetsLoading = true;
    } else if (force) {
      assetsRefreshing = true;
    }
    if (!assets.length) {
      assetsError = "";
    }
    try {
      const response = await fetchCurrentHubAssets({
        page: assetPage,
        limit: assetPerPage,
        search: assetSearch.trim() || undefined,
      });
      assets = response.data.items;
      assetTotal = Number(response.meta?.total ?? response.data.items.length);
      const nextAssetId =
        selectedAssetId && response.data.items.some((asset) => asset.id === selectedAssetId)
          ? selectedAssetId
          : response.data.items[0]?.id ?? null;
      selectedAssetId = nextAssetId;
      if (nextAssetId) {
        const silentRefresh = Boolean(
          force &&
          !isHubSwitch &&
          selectedAssetId === nextAssetId &&
          selectedAssetDetail,
        );
        await openAssetDetail(nextAssetId, { silent: silentRefresh });
      } else {
        selectedAssetDetail = null;
      }
    } catch (error) {
      if (!assets.length || isHubSwitch) {
        assets = [];
        assetTotal = 0;
      }
      assetsError = error instanceof Error ? error.message : "Unable to load assets.";
      if (!selectedAssetDetail || isHubSwitch) {
        selectedAssetDetail = null;
      }
    } finally {
      assetsLoading = false;
      assetsRefreshing = false;
    }
  }

  async function openAssetDetail(assetId: string, options: { silent?: boolean } = {}) {
    if (!assetId) return;
    selectedAssetId = assetId;
    const silent = options.silent ?? false;
    if (!silent || !selectedAssetDetail) {
      assetDetailLoading = true;
    }
    try {
      selectedAssetDetail = await fetchCurrentHubAssetDetail(assetId);
    } catch (error) {
      if (!silent) {
        selectedAssetDetail = null;
      }
      assetsError = error instanceof Error ? error.message : "Unable to load asset details.";
    } finally {
      assetDetailLoading = false;
    }
  }

  function formatDaysLeft(days?: number | null) {
    if (days === null || days === undefined) return "No fixed expiry";
    if (days < 0) return `Expired ${Math.abs(days)} day(s) ago`;
    return `${days} day(s) remaining`;
  }

  function assetTrackingChip(asset?: { tracking_state?: string | null; assigned_device_count?: number } | HubAssetDetail | null) {
    const trackingState = `${asset?.tracking_state ?? ""}`.toLowerCase();
    if (trackingState === "tracked") {
      return { label: "Tracked", className: "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200" };
    }
    if (`${(asset as any)?.id ?? ""}`.startsWith("virtual:")) {
      return { label: "Assignment only", className: "border-slate-300 bg-slate-100 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200" };
    }
    if ((asset?.assigned_device_count ?? 0) > 0) {
      return { label: "Pending sync", className: "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" };
    }
    return { label: "Pending device", className: "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" };
  }

  function formatDateTime(value?: string | null) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  function simLabel(sim?: { iccid?: string | null; msisdn?: string | null; carrier?: string | null; roaming_enabled?: boolean | null } | null) {
    if (!sim) return "No SIM linked";
    return [sim.iccid, sim.msisdn, sim.carrier, sim.roaming_enabled ? "Roaming" : null].filter(Boolean).join(" · ");
  }

  function latestAssetActivity(detail?: HubAssetDetail | null) {
    if (!detail?.devices?.length) return [];
    return detail.devices
      .flatMap((device) =>
        (device.assignment_history ?? []).map((entry) => ({
          id: `${device.imei}-${entry.id ?? entry.assigned_at ?? Math.random()}`,
          imei: device.imei,
          when: entry.unassigned_at ?? entry.installed_at ?? entry.assigned_at ?? null,
          target: entry.asset_registration ?? entry.asset_label ?? entry.vehicle_label ?? entry.hub_name ?? entry.target ?? "Unknown target",
          technician: entry.technician ?? "—",
          note: entry.notes ?? "No notes recorded",
          status: entry.unassigned_at ? "Closed" : entry.is_active ? "Active" : "Recorded",
        })),
      )
      .sort((a, b) => new Date(b.when ?? 0).getTime() - new Date(a.when ?? 0).getTime())
      .slice(0, 6);
  }

  function exportAssetSnapshot() {
    if (!selectedAssetDetail) return;
    const payload = {
      exportedAt: new Date().toISOString(),
      asset: selectedAssetDetail,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${(selectedAssetDetail.asset_name ?? selectedAssetDetail.registration ?? "asset").replace(/\s+/g, "-").toLowerCase()}-360.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  $: if (currentHubId) {
    void loadHubSummary(currentHubId);
    void loadHubAssets(currentHubId, true);
  }

  $: if (currentHubId && !pollHandle) {
    pollHandle = setInterval(() => {
      void loadHubSummary(currentHubId, true);
      void loadHubAssets(currentHubId, true);
    }, 10000);
  }

  $: if (!currentHubId && pollHandle) {
    clearInterval(pollHandle);
    pollHandle = null;
  }

  onDestroy(() => {
    if (pollHandle) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
    if (assetSearchDebounce) {
      clearTimeout(assetSearchDebounce);
      assetSearchDebounce = null;
    }
  });

  $: metricCards = summary
    ? [
        { label: "Active assets", value: summary.metrics.assets },
        { label: "Active devices", value: summary.metrics.active_devices },
        { label: "Active users", value: summary.metrics.active_users },
      ]
    : [];
  $: assetTotalPages = Math.max(1, Math.ceil(assetTotal / assetPerPage));
  $: assetPage = Math.min(assetPage, assetTotalPages);
  $: assetFilterSignature = `${currentHubId}|${assetSearch}|${assetPerPage}`;
  $: if (assetFilterSignature !== lastAssetFilterSignature) {
    lastAssetFilterSignature = assetFilterSignature;
    if (assetPage !== 1) {
      assetPage = 1;
    }
  }
  $: assetTrigger = `${currentHubId}|${assetSearch}|${assetPage}|${assetPerPage}`;
  $: if (currentHubId && assetTrigger) {
    if (assetSearchDebounce) {
      clearTimeout(assetSearchDebounce);
      assetSearchDebounce = null;
    }
    assetSearchDebounce = setTimeout(() => {
      void loadHubAssets(currentHubId, true);
    }, 220);
  }
</script>

<section class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Hub</p>
      <h1 class="omni-page-title">{summary?.hub.name ?? session?.hubName ?? "Omni Logistics"}</h1>
      <p class="omni-page-subtitle">
        {summary?.hub.code ?? session?.hubCode ?? "-"}
        {#if summary?.hub.type}
          · <span class="capitalize">{summary.hub.type}</span>
        {/if}
        {#if summary?.viewer.role}
          · {summary.viewer.role}
        {/if}
      </p>
    </div>
  </header>

  {#if errorMessage}
    <p class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</p>
  {/if}

  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    {#if summaryLoading && !summary}
      {#each Array.from({ length: 4 }) as _, index (index)}
        <div class="omni-stat-card h-24 animate-pulse"></div>
      {/each}
    {:else}
      {#each metricCards as metric (metric.label)}
        <div class="omni-stat-card border-0 shadow-none">
          <div class="pt-1">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">{metric.label}</p>
            <div class="mt-2 flex items-center gap-2">
              <p class="text-3xl font-semibold">{metric.value}</p>
              {#if summaryRefreshing}
                <span class="inline-flex h-2.5 w-2.5 animate-spin rounded-full border-2 border-primary/25 border-t-primary" aria-hidden="true"></span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <div class="grid gap-6 lg:grid-cols-3">
    <section class="omni-panel lg:col-span-2 border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Subscription</p>
        <h2 class="mt-2 text-2xl font-semibold">Subscription overview</h2>
      </div>
      <div class="grid gap-4 px-6 py-5 sm:grid-cols-2">
        <div class="space-y-2 text-sm">
          <p>Status: <span class="font-medium capitalize">{summary?.subscription.status ?? "provisioning"}</span></p>
          <p>Plan: <span class="font-medium">{summary?.subscription.tier ?? summary?.hub.tier ?? "Unknown"}</span></p>
          <p>Billing cycle: <span class="font-medium capitalize">{summary?.subscription.billing_cycle ?? "monthly"}</span></p>
          <p>Subscription start: <span class="font-medium">{summary?.subscription.start_date ? new Date(summary.subscription.start_date).toLocaleDateString() : "—"}</span></p>
          <p>Subscription expiry: <span class="font-medium">{summary?.subscription.end_date ? new Date(summary.subscription.end_date).toLocaleDateString() : "—"}</span></p>
          <p>Days remaining: <span class="font-medium">{formatDaysLeft(summary?.subscription.days_left)}</span></p>
        </div>
        <div class="space-y-2 text-sm text-muted-foreground">
          <p>Location: {summary?.hub.location?.city ?? "-"}{summary?.hub.location?.country ? `, ${summary.hub.location.country}` : ""}</p>
          <p>Timezone: {summary?.hub.timezone ?? "UTC"}</p>
          <div class="flex flex-wrap gap-2 pt-2">
            <Badge variant="secondary">Hub code: {summary?.hub.code ?? session?.hubCode}</Badge>
            <Badge variant="secondary">Role: {summary?.viewer.role ?? "client"}</Badge>
          </div>
        </div>
      </div>
    </section>

    <section class="omni-panel border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Permissions</p>
        <h2 class="mt-2 text-2xl font-semibold">Access permissions</h2>
      </div>
      <div class="space-y-2 px-6 py-5">
        {#if summary?.viewer.features?.length}
          {#each summary.viewer.features as feature (feature)}
            <Badge variant="outline" class="mr-2 mb-2">{feature}</Badge>
          {/each}
        {:else}
          <p class="text-sm text-muted-foreground">No additional permissions listed.</p>
        {/if}
      </div>
    </section>
  </div>

  <div class="grid gap-6 lg:grid-cols-2">
    <section class="omni-panel border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Tracking</p>
        <h2 class="mt-2 text-2xl font-semibold">Tracking access</h2>
      </div>
      <div class="space-y-4 px-6 py-5">
        <a href="/tracking" target="_blank" rel="noreferrer" class={cn(buttonVariants({ size: "sm" }))}>
          Open tracking portal
        </a>
      </div>
    </section>

    <section class="omni-panel border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Support</p>
        <h2 class="mt-2 text-2xl font-semibold">Support and technical assistance</h2>
      </div>
      <div class="space-y-3 px-6 py-5 text-sm text-muted-foreground">
        <p class="font-medium text-foreground">{supportEmail}</p>
      </div>
    </section>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.2fr,0.9fr]">
    <section class="omni-panel border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Assets</p>
        <h2 class="mt-2 text-2xl font-semibold">Assets</h2>
      </div>
      <div class="space-y-4 px-6 py-5">
        <div class="omni-toolbar">
          <input
            class="omni-input min-w-[16rem] flex-1 rounded-full py-2.5"
            type="search"
            placeholder="Search by registration, VIN, make, or model"
            bind:value={assetSearch}
          />
          <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
            {assetTotal} assets
          </span>
          {#if assetsRefreshing}
            <span class="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
              <span class="inline-flex h-2.5 w-2.5 animate-spin rounded-full border-2 border-primary/25 border-t-primary" aria-hidden="true"></span>
              Refreshing
            </span>
          {/if}
        </div>

        {#if assetsError}
          <p class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{assetsError}</p>
        {/if}

        {#if assetsLoading && !assets.length}
          <div class="omni-inline-state">Loading assets…</div>
        {:else if assets.length > 0}
          <div class="omni-table-shell">
            <table class="omni-table">
              <thead>
                <tr>
                  <th>Registration</th>
                  <th>Asset</th>
                  <th>Devices</th>
                  <th>Status</th>
                  <th class="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {#each assets as asset (asset.id)}
                  <tr class={`${selectedAssetId === asset.id ? "omni-row-active" : ""}`}>
                    <td class="font-medium">{asset.registration ?? "—"}</td>
                    <td>
                      <div class="font-medium">{asset.asset_name ?? asset.label ?? "—"}</div>
                      <div class="text-xs text-muted-foreground">
                        {(asset.asset_type ?? "asset").replaceAll("_", " ")}
                        {#if asset.make || asset.model}
                          · {[asset.make, asset.model].filter(Boolean).join(" ")}
                        {/if}
                      </div>
                    </td>
                    <td>{asset.assigned_device_count}</td>
                    <td><span class={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${assetTrackingChip(asset).className}`}>{assetTrackingChip(asset).label}</span></td>
                    <td class="text-right">
                      <button
                        type="button"
                        class={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                        on:click={() => openAssetDetail(asset.id)}
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <div class="flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <div>Page {assetPage} of {assetTotalPages}</div>
            <div class="flex items-center gap-2">
              <select
                class="omni-select rounded-full px-3 py-1.5 text-xs"
                bind:value={assetPerPage}
              >
                <option value={10}>10 per page</option>
                <option value={20}>20 per page</option>
                <option value={50}>50 per page</option>
              </select>
              <button
                type="button"
                class={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                on:click={() => (assetPage = Math.max(1, assetPage - 1))}
                disabled={assetPage <= 1}
              >
                Previous
              </button>
              <button
                type="button"
                class={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                on:click={() => (assetPage = Math.min(assetTotalPages, assetPage + 1))}
                disabled={assetPage >= assetTotalPages}
              >
                Next
              </button>
            </div>
          </div>
        {:else}
          <div class="omni-inline-state">No assets are currently linked to this hub.</div>
        {/if}
      </div>
    </section>

    <section class="omni-panel border-0 shadow-none">
      <div class="border-b border-white/60 px-6 py-5 dark:border-slate-800">
        <p class="omni-kicker">Asset 360</p>
        <h2 class="mt-2 text-2xl font-semibold">Asset 360</h2>
      </div>
      <div class="px-6 py-5">
        {#if assetDetailLoading}
          <div class="omni-inline-state">Loading asset details…</div>
        {:else if selectedAssetDetail}
          <div class="space-y-4 omni-animate-fade">
            <div>
              <p class="text-2xl font-semibold">{selectedAssetDetail.asset_name ?? selectedAssetDetail.registration ?? "Unregistered asset"}</p>
              <p class="text-sm text-muted-foreground">
                {(selectedAssetDetail.asset_type ?? "asset").replaceAll("_", " ")}
                {#if selectedAssetDetail.asset_type_other}
                  · {selectedAssetDetail.asset_type_other}
                {/if}
                {#if selectedAssetDetail.registration}
                  · {selectedAssetDetail.registration}
                {/if}
                {#if selectedAssetDetail.make || selectedAssetDetail.model}
                  · {[selectedAssetDetail.make, selectedAssetDetail.model].filter(Boolean).join(" ")}
                {/if}
                {#if selectedAssetDetail.year}
                  · {selectedAssetDetail.year}
                {/if}
                {#if selectedAssetDetail.vin}
                  · VIN {selectedAssetDetail.vin}
                {/if}
              </p>
            </div>

            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                on:click={exportAssetSnapshot}
              >
                Export Asset 360
              </button>
              <button
                type="button"
                class={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                on:click={() => globalThis.print?.()}
              >
                Print view
              </button>
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
              <div class="omni-stat-card p-3 text-sm shadow-none">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Tracking</p>
                <span class={`mt-1 inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${assetTrackingChip(selectedAssetDetail).className}`}>{assetTrackingChip(selectedAssetDetail).label}</span>
              </div>
              <div class="omni-stat-card p-3 text-sm shadow-none">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Assigned devices</p>
                <p class="mt-1 font-medium">{selectedAssetDetail.devices.length}</p>
              </div>
            </div>

            <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div class="omni-soft-panel text-sm">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Registration</p>
                <p class="mt-1 font-medium text-foreground">{selectedAssetDetail.registration ?? "Not recorded"}</p>
              </div>
              <div class="omni-soft-panel text-sm">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">VIN</p>
                <p class="mt-1 font-medium text-foreground">{selectedAssetDetail.vin ?? "Not recorded"}</p>
              </div>
              <div class="omni-soft-panel text-sm">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Fuel type</p>
                <p class="mt-1 font-medium text-foreground">{selectedAssetDetail.fuel_type ?? "Not recorded"}</p>
              </div>
              <div class="omni-soft-panel text-sm">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Managed SIMs</p>
                <p class="mt-1 font-medium text-foreground">{selectedAssetDetail.devices.filter((device) => device.sim).length}</p>
              </div>
            </div>

            {#if selectedAssetDetail.notes}
              <div class="omni-soft-panel text-sm">
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Notes</p>
                <p class="mt-1">{selectedAssetDetail.notes}</p>
              </div>
            {/if}

            <div class="omni-soft-panel text-sm">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-wide text-muted-foreground">Latest activity</p>
                  <p class="mt-1 font-medium text-foreground">Recent device and SIM changes</p>
                </div>
                <span class="text-xs text-muted-foreground">{latestAssetActivity(selectedAssetDetail).length} event{latestAssetActivity(selectedAssetDetail).length === 1 ? "" : "s"}</span>
              </div>
              {#if latestAssetActivity(selectedAssetDetail).length}
                <div class="mt-3 space-y-2">
                  {#each latestAssetActivity(selectedAssetDetail) as event (event.id)}
                    <div class="rounded-2xl border border-border/70 bg-background/70 px-3 py-3 text-xs text-muted-foreground">
                      <div class="flex flex-wrap items-center justify-between gap-2">
                        <p class="font-medium text-foreground">{event.status} · {event.imei}</p>
                        <p>{formatDateTime(event.when)}</p>
                      </div>
                      <p class="mt-1">Target: <span class="font-medium text-foreground">{event.target}</span> · Technician: <span class="font-medium text-foreground">{event.technician}</span></p>
                      <p class="mt-1">{event.note}</p>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="mt-3 text-muted-foreground">No recent activity has been recorded for this asset yet.</p>
              {/if}
            </div>

            <div class="space-y-3">
              <p class="text-xs uppercase tracking-wide text-muted-foreground">Assigned devices</p>
              {#if selectedAssetDetail.devices.length > 0}
                {#each selectedAssetDetail.devices as device (device.assignment_id ?? device.imei)}
                  <details class="omni-soft-panel">
                    <summary class="flex cursor-pointer list-none items-center justify-between gap-3">
                      <div>
                        <p class="font-mono text-xs">{device.imei}</p>
                        <p class="text-sm">{device.model ?? device.hardware_type ?? "Unspecified hardware"}</p>
                      </div>
                      <span class="text-xs text-primary">View device detail</span>
                    </summary>
                    <div class="mt-3 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                      <p>Inventory status: <span class="font-medium text-foreground uppercase">{device.status ?? "—"}</span></p>
                      <p>Assigned asset: <span class="font-medium text-foreground">{device.asset_registration ?? device.asset_label ?? "—"}</span></p>
                      <p>Technician: <span class="font-medium text-foreground">{device.technician ?? "—"}</span></p>
                      <p>Installation location: <span class="font-medium text-foreground">{device.installation_location ?? "—"}</span></p>
                      <p>Assigned on: <span class="font-medium text-foreground">{formatDateTime(device.assigned_at)}</span></p>
                      <p>Installed on: <span class="font-medium text-foreground">{formatDateTime(device.installed_at)}</span></p>
                      <p class="sm:col-span-2">Managed SIM: <span class="font-medium text-foreground">{simLabel(device.sim)}</span></p>
                    </div>
                    <div class="mt-3 grid gap-3 lg:grid-cols-2">
                      <div class="omni-soft-panel text-xs">
                        <p class="text-[11px] uppercase tracking-wide text-muted-foreground">Hardware profile</p>
                        <div class="mt-2 grid gap-2 sm:grid-cols-2">
                          <p>IMEI: <span class="font-medium text-foreground">{device.imei}</span></p>
                          <p>Serial: <span class="font-medium text-foreground">{device.serial_number ?? "—"}</span></p>
                          <p>Manufacturer: <span class="font-medium text-foreground">{device.manufacturer ?? "—"}</span></p>
                          <p>Model: <span class="font-medium text-foreground">{device.model ?? "—"}</span></p>
                          <p>Type: <span class="font-medium text-foreground">{device.hardware_type ?? "—"}</span></p>
                          <p>Firmware: <span class="font-medium text-foreground">{device.firmware_version ?? "—"}</span></p>
                          <p>Status: <span class="font-medium text-foreground">{device.status ?? "—"}</span></p>
                        </div>
                      </div>
                      <div class="omni-soft-panel text-xs">
                        <p class="text-[11px] uppercase tracking-wide text-muted-foreground">SIM profile</p>
                        {#if device.sim}
                          <div class="mt-2 grid gap-2 sm:grid-cols-2">
                            <p>ICCID: <span class="font-medium text-foreground">{device.sim.iccid ?? "—"}</span></p>
                            <p>SIM number: <span class="font-medium text-foreground">{device.sim.msisdn ?? "—"}</span></p>
                            <p>Carrier: <span class="font-medium text-foreground">{device.sim.carrier ?? "Econet"}</span></p>
                            <p>Status: <span class="font-medium text-foreground">{device.sim.status ?? "assigned"}</span></p>
                          </div>
                        {:else}
                          <p class="mt-2">No managed SIM is linked to this tracker.</p>
                        {/if}
                      </div>
                    </div>
                    {#if device.sim}
                      <div class="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span class="rounded-full border border-border/70 bg-background/70 px-2 py-1">{device.sim.status ?? "assigned"}</span>
                        {#if device.sim.roaming_enabled}
                          <span class="rounded-full border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-cyan-700 dark:text-cyan-300">Roaming enabled</span>
                        {/if}
                      </div>
                    {/if}
                    {#if device.assignment_history?.length}
                      <div class="mt-3 rounded-[1.1rem] border border-white/70 bg-white/50 p-3 dark:border-slate-800 dark:bg-slate-950/35">
                        <p class="text-xs uppercase tracking-wide text-muted-foreground">Assignment history</p>
                        <div class="mt-2 max-h-40 overflow-auto">
                          <table class="omni-table text-xs">
                            <thead class="text-muted-foreground">
                              <tr>
                                <th class="px-2 py-1 text-left">Assigned</th>
                                <th class="px-2 py-1 text-left">Target</th>
                                <th class="px-2 py-1 text-left">SIM</th>
                                <th class="px-2 py-1 text-left">Technician</th>
                                <th class="px-2 py-1 text-left">Reason</th>
                                <th class="px-2 py-1 text-left">Removed</th>
                              </tr>
                            </thead>
                            <tbody>
                              {#each device.assignment_history as history (history.id)}
                                <tr class="border-t">
                                  <td class="px-2 py-1">{formatDateTime(history.assigned_at)}</td>
                                  <td class="px-2 py-1">{history.asset_registration ?? history.asset_label ?? history.vehicle_label ?? history.hub_name ?? history.target ?? "—"}</td>
                                  <td class="px-2 py-1">{history.sim_iccid ?? "—"}{history.sim_roaming_enabled ? " · Roaming" : ""}</td>
                                  <td class="px-2 py-1">{history.technician ?? "—"}</td>
                                  <td class="px-2 py-1">{history.notes ?? "—"}</td>
                                  <td class="px-2 py-1">{history.unassigned_at ? formatDateTime(history.unassigned_at) : history.is_active ? "Active" : "—"}</td>
                                </tr>
                              {/each}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    {/if}
                  </details>
                {/each}
              {:else}
                <div class="omni-empty-state py-8">No active devices are currently assigned to this asset.</div>
              {/if}
            </div>
          </div>
        {:else}
          <div class="omni-inline-state">Select an asset to review its assigned devices.</div>
        {/if}
      </div>
    </section>
  </div>
</section>
