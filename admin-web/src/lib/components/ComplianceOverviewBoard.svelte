<script>
  import { onMount } from "svelte";
  import { AlertTriangle, FolderOpenDot, RefreshCw, ShieldCheck, Siren, TimerReset } from "lucide-svelte";

  import { Button } from "$lib/components/ui/button";
  import { fetchComplianceOverview } from "$lib/api/compliance";

  let loading = false;
  let errorMessage = "";
  let overview = null;

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }

  async function loadOverview() {
    loading = true;
    errorMessage = "";
    try {
      overview = await fetchComplianceOverview();
    } catch (error) {
      console.error("Failed to load compliance overview", error);
      errorMessage = "Unable to load the compliance overview.";
    } finally {
      loading = false;
    }
  }

  function openModule(section) {
    window.dispatchEvent(new CustomEvent("omni-admin-navigate", { detail: { section } }));
  }

  onMount(() => {
    void loadOverview();
  });
</script>

<div class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Governance</p>
      <h2 class="omni-page-title">Compliance Overview</h2>
    </div>
    <div class="flex flex-wrap items-center justify-end gap-2">
      <span class="omni-inline-stat">
        Last updated {overview?.generated_at ? formatDateTime(overview.generated_at) : "—"}
      </span>
      <Button variant="outline" size="sm" onclick={() => openModule("data-requests")}>Open requests</Button>
      <Button variant="outline" size="sm" onclick={() => openModule("security-incidents")}>Open incidents</Button>
      <Button variant="outline" size="sm" onclick={loadOverview} disabled={loading}>
        <RefreshCw class="h-4 w-4" />
        Refresh
      </Button>
    </div>
  </header>

  {#if errorMessage}
    <div class="omni-inline-state">{errorMessage}</div>
  {/if}

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <article class="omni-stat-card">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Open requests</p>
          <p class="mt-2 text-3xl font-semibold">{overview?.requests?.open ?? 0}</p>
        </div>
        <FolderOpenDot class="h-5 w-5 text-cyan-500" />
      </div>
      <p class="mt-3 text-sm text-muted-foreground">{overview?.requests?.total ?? 0} total requests in register</p>
    </article>

    <article class="omni-stat-card">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Overdue requests</p>
          <p class="mt-2 text-3xl font-semibold">{overview?.requests?.overdue ?? 0}</p>
        </div>
        <TimerReset class="h-5 w-5 text-amber-500" />
      </div>
      <p class="mt-3 text-sm text-muted-foreground">Requests that need action before the regulator timeline slips.</p>
    </article>

    <article class="omni-stat-card">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Open incidents</p>
          <p class="mt-2 text-3xl font-semibold">{overview?.incidents?.open ?? 0}</p>
        </div>
        <ShieldCheck class="h-5 w-5 text-rose-500" />
      </div>
      <p class="mt-3 text-sm text-muted-foreground">{overview?.incidents?.critical_open ?? 0} critical incidents still open.</p>
    </article>

    <article class="omni-stat-card">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Notifications required</p>
          <p class="mt-2 text-3xl font-semibold">{overview?.incidents?.notification_required ?? 0}</p>
        </div>
        <Siren class="h-5 w-5 text-fuchsia-500" />
      </div>
      <p class="mt-3 text-sm text-muted-foreground">Incidents flagged for regulator or data-subject notification.</p>
    </article>
  </div>

  <div class="omni-page-grid">
    <div class="omni-list-stage">
      <section class="omni-panel border-0 p-5 shadow-none">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Recent requests</p>
            <h3 class="mt-2 text-lg font-semibold">Data request activity</h3>
          </div>
          <div class="omni-inline-stat">Evidence files: {overview?.requests?.attachments ?? 0}</div>
        </div>

        {#if loading && !overview}
          <div class="omni-loading-state mt-4">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading recent requests…</span>
          </div>
        {:else}
          <div class="mt-4 omni-table-shell">
            <table class="omni-table text-sm">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Requester</th>
                  <th>Status</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {#if overview?.recent_requests?.length}
                  {#each overview.recent_requests as item}
                    <tr>
                      <td class="font-medium text-slate-900 dark:text-white">{item.reference_no}</td>
                      <td>{item.title}</td>
                      <td>{item.status.replaceAll("_", " ")}</td>
                      <td>{formatDateTime(item.updated_at)}</td>
                    </tr>
                  {/each}
                {:else}
                  <tr>
                    <td colspan="4" class="py-8 text-center text-muted-foreground">No data subject requests logged yet.</td>
                  </tr>
                {/if}
              </tbody>
            </table>
          </div>
        {/if}
      </section>
    </div>

    <div class="omni-inspector-stage">
      <section class="omni-panel border-0 p-5 shadow-none">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Recent incidents</p>
          <h3 class="mt-2 text-lg font-semibold">Security incident activity</h3>
          <p class="mt-2 text-sm text-muted-foreground">Keep an eye on open incidents, evidence coverage, and notification-ready cases.</p>
        </div>

        {#if loading && !overview}
          <div class="omni-loading-state mt-4">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading incident activity…</span>
          </div>
        {:else}
          <div class="mt-4 space-y-3">
            {#if overview?.recent_incidents?.length}
              {#each overview.recent_incidents as item}
                <article class="omni-detail-section">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-semibold text-slate-900 dark:text-white">{item.reference_no}</p>
                      <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.title}</p>
                    </div>
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] text-slate-600 dark:bg-slate-800 dark:text-slate-200">
                      {item.status.replaceAll("_", " ")}
                    </span>
                  </div>
                  <div class="mt-3 flex items-center justify-between gap-3 text-xs text-muted-foreground">
                    <span>Updated {formatDateTime(item.updated_at)}</span>
                    <AlertTriangle class="h-4 w-4 text-amber-500" />
                  </div>
                </article>
              {/each}
            {:else}
              <div class="omni-inline-state mt-4">No incidents logged yet.</div>
            {/if}
          </div>
        {/if}
      </section>
    </div>
  </div>
</div>
