<script>
  import { onDestroy, onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { fetchHubById, fetchHubs, updateHub } from "$lib/api/hubs";
  import { adminLogStore } from "$lib/stores/admin-log";
  import { toastStore } from "$lib/stores/toast";
  import { confirmAndRun, confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";

  let hubs = [];
  let activeHub = null;
  let activeView = "list";
  let tier = "Business";
  let billingCycle = "monthly";
  let hubStatus = "active";
  let addDaysAmount = 30;
  let subtractDaysAmount = 5;
  let formDirty = false;
  let formHubId = "";
  let subscriptionStartDate = "";
  let loading = false;
  let saving = false;
  let actionLoading = false;
  let message = "";
  let hubSearch = "";
  let tierFilter = "all";
  let statusFilter = "all";
  let pollHandle = null;

  function tierFromHubType(hubType) {
    const normalized = String(hubType ?? "").toLowerCase();
    return normalized === "individual" ? "Individual" : "Business";
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString();
  }

  function toIsoDate(value) {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "";
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function addMonths(baseDate, months) {
    const d = new Date(baseDate);
    d.setMonth(d.getMonth() + months);
    return d;
  }

  function computeSubscriptionEndDate(startDate, cycle) {
    if (!startDate) return "";
    const start = new Date(startDate);
    if (Number.isNaN(start.getTime())) return "";
    let end = new Date(start);
    if (cycle === "quarterly") {
      end = addMonths(start, 3);
    } else if (cycle === "yearly") {
      end = addMonths(start, 12);
    } else {
      end.setDate(end.getDate() + 30);
    }
    return toIsoDate(end);
  }

  function syncFormFromHub(hub) {
    if (!hub) return;
    formHubId = String(hub.id);
    tier = tierFromHubType(hub.type);
    billingCycle = hub.billingCycle ?? "monthly";
    hubStatus = hub.status ?? "active";
    subscriptionStartDate = toIsoDate(hub.subscriptionStartDate) || toIsoDate(new Date());
    formDirty = false;
  }

  function updateHubInRegister(updatedHub) {
    hubs = hubs.map((hub) => (String(hub.id) === String(updatedHub.id) ? updatedHub : hub));
    if (String(activeHub?.id ?? "") === String(updatedHub.id)) {
      activeHub = updatedHub;
    }
  }

  async function loadHubs() {
    loading = true;
    message = "";
    try {
      hubs = await fetchHubs();
      if (activeHub?.id) {
        const matchingHub = hubs.find((hub) => String(hub.id) === String(activeHub.id));
        if (matchingHub) {
          activeHub = matchingHub;
        }
      }
    } catch (error) {
      console.error("Failed to load hubs", error);
      message = "Unable to load hubs for billing management.";
    } finally {
      loading = false;
    }
  }

  async function refreshActiveHub() {
    if (!activeHub?.id) return;
    try {
      const refreshed = await fetchHubById(activeHub.id);
      updateHubInRegister(refreshed);
      if (!formDirty) {
        syncFormFromHub(refreshed);
      }
    } catch (error) {
      console.error("Failed to refresh active billing hub", error);
    }
  }

  async function openBillingProfile(hub, view = "profile") {
    if (!hub?.id) return;
    loading = true;
    message = "";
    try {
      const detailedHub = await fetchHubById(hub.id);
      activeHub = detailedHub;
      syncFormFromHub(detailedHub);
      activeView = view;
    } catch (error) {
      console.error("Failed to open billing profile", error);
      message = "Unable to open the selected billing profile right now.";
    } finally {
      loading = false;
    }
  }

  function returnToRegister() {
    activeView = "list";
    activeHub = null;
    formHubId = "";
    formDirty = false;
    message = "";
  }

  function matchesHubFilters(hub) {
    const q = hubSearch.trim().toLowerCase();
    const matchesSearch = q
      ? `${hub.name} ${hub.code} ${hub.city ?? ""} ${hub.country ?? ""}`.toLowerCase().includes(q)
      : true;
    const matchesTier = tierFilter === "all" ? true : tierFromHubType(hub.type).toLowerCase() === tierFilter;
    const matchesStatus = statusFilter === "all" ? true : String(hub.status ?? "").toLowerCase() === statusFilter;
    return matchesSearch && matchesTier && matchesStatus;
  }

  $: filteredHubs = (hubs ?? []).filter(matchesHubFilters);
  $: if (activeHub && formHubId !== String(activeHub.id)) {
    syncFormFromHub(activeHub);
  }
  $: computedSubscriptionEndDate = computeSubscriptionEndDate(subscriptionStartDate, billingCycle);
  $: if (activeHub && formHubId === String(activeHub.id)) {
    formDirty =
      billingCycle !== (activeHub.billingCycle ?? "monthly") ||
      hubStatus !== (activeHub.status ?? "active") ||
      subscriptionStartDate !== (toIsoDate(activeHub.subscriptionStartDate) || toIsoDate(new Date())) ||
      computedSubscriptionEndDate !== (toIsoDate(activeHub.subscriptionEndDate) || "");
  }

  async function saveBillingProfile() {
    if (!activeHub) return;
    if (!formDirty) {
      message = "There are no billing changes to save.";
      return;
    }
    if (!(await confirmSave({ title: "Save billing changes", message: "Save these billing changes?" }))) {
      return;
    }

    saving = true;
    message = "";
    const previousBillingCycle = activeHub.billingCycle ?? "monthly";
    const previousTier = tierFromHubType(activeHub.type);
    const previousStatus = activeHub.status ?? "active";
    const requestedStatus = String(hubStatus ?? "").toLowerCase();

    try {
      await updateHub(activeHub.id, {
        type: activeHub.type,
        billingCycle,
        tier,
        status: hubStatus,
        subscriptionStartDate: subscriptionStartDate || null,
        subscriptionEndDate: computedSubscriptionEndDate || null,
      });
      const refreshed = await fetchHubById(activeHub.id);
      updateHubInRegister(refreshed);
      syncFormFromHub(refreshed);
      message = `Billing profile updated. Status: ${refreshed.status ?? "—"}; cycle: ${refreshed.billingCycle ?? "monthly"}.`;
      if (String(refreshed.status ?? "").toLowerCase() !== requestedStatus) {
        message = `Changes saved, but the status remained ${String(refreshed.status ?? "provisioning").toLowerCase()}.`;
      }
      toastStore.push({
        title: "Billing updated",
        message: `Billing profile updated. Status: ${refreshed.status ?? "—"}; cycle: ${refreshed.billingCycle ?? "monthly"}.`,
        tone: "success",
      });
      const changes = [];
      if (previousTier !== tier) changes.push(`tier ${previousTier} -> ${tier}`);
      if (previousBillingCycle !== billingCycle) changes.push(`cycle ${previousBillingCycle} -> ${billingCycle}`);
      if (previousStatus !== hubStatus) changes.push(`status ${previousStatus} -> ${hubStatus}`);
      adminLogStore.append({
        action: "billing-profile-update",
        scope: "billing",
        details: `Billing updated for ${activeHub.name} (${activeHub.code}): ${changes.length ? changes.join(", ") : "no field changes"}`,
      });
    } catch (error) {
      console.error("Failed to save billing profile", error);
      message = "Unable to save the billing profile.";
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function renewSubscription() {
    if (!activeHub) return;
    await confirmAndRun(
      {
        title: "Renew subscription",
        description: "Billing",
        message: "Renew this subscription now?",
        confirmLabel: "Renew subscription",
      },
      async () => {
        actionLoading = true;
        message = "";
        try {
          const latestHub = await fetchHubById(activeHub.id);
          updateHubInRegister(latestHub);
          const start = new Date();
          let end = new Date(start);
          if (billingCycle === "quarterly") {
            end = addMonths(start, 3);
          } else if (billingCycle === "yearly") {
            end = addMonths(start, 12);
          } else {
            end.setDate(end.getDate() + 30);
          }
          await updateHub(activeHub.id, {
            type: latestHub.type,
            billingCycle,
            status: "active",
            subscriptionStartDate: toIsoDate(start),
            subscriptionEndDate: toIsoDate(end),
          });
          const refreshed = await fetchHubById(activeHub.id);
          updateHubInRegister(refreshed);
          syncFormFromHub(refreshed);
          message = `Subscription renewed successfully. New expiry: ${formatDate(refreshed.subscriptionEndDate)}.`;
          toastStore.push({
            title: "Subscription renewed",
            message: `${refreshed.name} is now active until ${formatDate(refreshed.subscriptionEndDate)}.`,
            tone: "success",
          });
          adminLogStore.append({
            action: "billing-renew",
            scope: "billing",
            details: `Renewed ${refreshed.name} (${refreshed.code}) on ${billingCycle} cycle until ${refreshed.subscriptionEndDate ?? "n/a"}`,
          });
        } catch (error) {
          console.error("Failed to renew subscription", error);
          message = "Unable to renew the subscription.";
        } finally {
          actionLoading = false;
        }
      },
    );
  }

  async function addSubscriptionDays() {
    if (!activeHub) return;
    const delta = Number(addDaysAmount);
    if (!Number.isFinite(delta) || delta <= 0) {
      message = "Days to add must be greater than zero.";
      return;
    }
    await confirmAndRun(
      {
        title: "Add subscription days",
        description: "Billing",
        message: `Add ${delta} day(s) to this subscription?`,
        confirmLabel: "Add days",
      },
      async () => {
        actionLoading = true;
        message = "";
        try {
          const latestHub = await fetchHubById(activeHub.id);
          updateHubInRegister(latestHub);
          const start = latestHub.subscriptionStartDate ? new Date(latestHub.subscriptionStartDate) : new Date();
          const currentEnd = latestHub.subscriptionEndDate ? new Date(latestHub.subscriptionEndDate) : new Date();
          const nextEnd = new Date(currentEnd);
          nextEnd.setDate(nextEnd.getDate() + delta);
          await updateHub(activeHub.id, {
            type: latestHub.type,
            billingCycle,
            status: hubStatus,
            subscriptionStartDate: toIsoDate(start),
            subscriptionEndDate: toIsoDate(nextEnd),
          });
          const refreshed = await fetchHubById(activeHub.id);
          updateHubInRegister(refreshed);
          syncFormFromHub(refreshed);
          message = `Added ${delta} day(s). New expiry: ${formatDate(refreshed.subscriptionEndDate)}.`;
          toastStore.push({
            title: "Days added",
            message: `${delta} day(s) added for ${refreshed.name}.`,
            tone: "success",
          });
          adminLogStore.append({
            action: "billing-add-days",
            scope: "billing",
            details: `Added ${delta} day(s) for ${refreshed.name} (${refreshed.code}); expiry now ${refreshed.subscriptionEndDate ?? "n/a"}`,
          });
        } catch (error) {
          console.error("Failed to add subscription days", error);
          message = "Unable to add subscription days.";
        } finally {
          actionLoading = false;
        }
      },
    );
  }

  async function subtractSubscriptionDays() {
    if (!activeHub) return;
    const delta = Number(subtractDaysAmount);
    if (!Number.isFinite(delta) || delta <= 0) {
      message = "Days to subtract must be greater than zero.";
      return;
    }
    await confirmAndRun(
      {
        title: "Subtract subscription days",
        description: "Billing",
        message: `Subtract ${delta} day(s) from this subscription?`,
        confirmLabel: "Subtract days",
        tone: "destructive",
      },
      async () => {
        actionLoading = true;
        message = "";
        try {
          const latestHub = await fetchHubById(activeHub.id);
          updateHubInRegister(latestHub);
          const start = latestHub.subscriptionStartDate ? new Date(latestHub.subscriptionStartDate) : new Date();
          const currentEnd = latestHub.subscriptionEndDate ? new Date(latestHub.subscriptionEndDate) : new Date();
          const nextEnd = new Date(currentEnd);
          nextEnd.setDate(nextEnd.getDate() - delta);
          if (nextEnd < start) {
            message = "You cannot reduce the subscription below its start date.";
            actionLoading = false;
            return;
          }
          await updateHub(activeHub.id, {
            type: latestHub.type,
            billingCycle,
            status: hubStatus,
            subscriptionStartDate: toIsoDate(start),
            subscriptionEndDate: toIsoDate(nextEnd),
          });
          const refreshed = await fetchHubById(activeHub.id);
          updateHubInRegister(refreshed);
          syncFormFromHub(refreshed);
          message = `Subtracted ${delta} day(s). New expiry: ${formatDate(refreshed.subscriptionEndDate)}.`;
          toastStore.push({
            title: "Days subtracted",
            message: `${delta} day(s) removed for ${refreshed.name}.`,
            tone: "success",
          });
          adminLogStore.append({
            action: "billing-subtract-days",
            scope: "billing",
            details: `Subtracted ${delta} day(s) for ${refreshed.name} (${refreshed.code}); expiry now ${refreshed.subscriptionEndDate ?? "n/a"}`,
          });
        } catch (error) {
          console.error("Failed to subtract subscription days", error);
          message = "Unable to subtract subscription days.";
        } finally {
          actionLoading = false;
        }
      },
    );
  }

  onMount(() => {
    void loadHubs();
    pollHandle = setInterval(() => {
      if (activeView !== "list" && activeHub?.id) {
        void refreshActiveHub();
      }
    }, 10000);
  });

  onDestroy(() => {
    if (pollHandle) clearInterval(pollHandle);
  });
</script>

<section class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Operations</p>
      <h2 class="omni-page-title">Billing</h2>
    </div>
  </header>

  {#if activeView === "list"}
    <div class="omni-panel border-0 p-5 shadow-none">
      <div class="omni-toolbar-strip mb-4">
        <input
          class="omni-input min-w-[16rem] flex-1"
          type="search"
          placeholder="Search by hub name, code, or city"
          bind:value={hubSearch}
        />
        <select class="omni-select min-w-[10rem]" bind:value={tierFilter}>
          <option value="all">All tiers</option>
          <option value="individual">Individual</option>
          <option value="business">Business</option>
        </select>
        <select class="omni-select min-w-[10rem]" bind:value={statusFilter}>
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="provisioning">Provisioning</option>
          <option value="suspended">Suspended</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      <div class="omni-table-shell max-h-[620px] overflow-auto">
        {#if loading}
          <div class="omni-loading-state">
            <span class="omni-spinner" aria-hidden="true"></span>
            <p>Loading billing register…</p>
          </div>
        {:else if filteredHubs.length === 0}
          <div class="omni-empty-state">
            <p class="font-medium text-foreground">No hubs match the current filters.</p>
            <p>Try a different search term or clear one of the active filters.</p>
          </div>
        {:else}
          <table class="omni-table">
            <thead class="sticky top-0 z-10">
              <tr>
                <th>Hub</th>
                <th>Code</th>
                <th>Tier</th>
                <th>Cycle</th>
                <th class="text-right">Days left</th>
                <th>Status</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredHubs as hub (hub.id)}
                <tr>
                  <td class="font-medium">{hub.name}</td>
                  <td class="font-mono text-xs">{hub.code}</td>
                  <td>{tierFromHubType(hub.type)}</td>
                  <td class="capitalize">{hub.billingCycle ?? "monthly"}</td>
                  <td class="text-right">{hub.subscriptionDaysLeft ?? "—"}</td>
                  <td class="capitalize">{hub.status ?? "provisioning"}</td>
                  <td class="text-right">
                    <Button size="sm" variant="outline" onclick={() => openBillingProfile(hub, "profile")}>Open</Button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    </div>
  {:else if activeHub}
    <div class="space-y-5">
      <div class="flex flex-wrap items-start justify-between gap-3 rounded-3xl border border-white/70 bg-white/75 px-5 py-5 shadow-sm dark:border-white/10 dark:bg-slate-950/55">
        <div>
          <p class="omni-kicker">Billing profile</p>
          <h3 class="text-2xl font-semibold tracking-tight">{activeHub.name}</h3>
          <p class="text-sm text-muted-foreground">Hub code {activeHub.code}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button size="sm" variant={activeView === "profile" ? "default" : "outline"} onclick={() => (activeView = "profile")}>Profile</Button>
          <Button size="sm" variant={activeView === "renewals" ? "default" : "outline"} onclick={() => (activeView = "renewals")}>Renewals</Button>
          <Button size="sm" variant={activeView === "state" ? "default" : "outline"} onclick={() => (activeView = "state")}>State</Button>
          <Button size="sm" variant="outline" onclick={returnToRegister}>Back</Button>
        </div>
      </div>

      {#if activeView === "profile"}
        <div class="omni-panel border-0 p-5 shadow-none">
          <div class="grid gap-4 lg:grid-cols-2">
            <div class="omni-field">
              <label for="billing-plan">Billing plan</label>
              <input id="billing-plan" class="omni-input bg-muted/35" value={tierFromHubType(activeHub.type)} readonly />
            </div>
            <div class="omni-field">
              <label for="billing-cycle">Billing cycle</label>
              <select id="billing-cycle" class="omni-select" bind:value={billingCycle}>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div class="omni-field">
              <label for="billing-start-date">Subscription start date</label>
              <input id="billing-start-date" class="omni-input" type="date" bind:value={subscriptionStartDate} />
            </div>
            <div class="omni-field">
              <label for="billing-end-date">Subscription expiry date</label>
              <input id="billing-end-date" class="omni-input bg-muted/35" type="date" value={computedSubscriptionEndDate} readonly />
            </div>
            <div class="omni-field lg:col-span-2">
              <label for="billing-status">Subscription status</label>
              <select id="billing-status" class="omni-select" bind:value={hubStatus}>
                <option value="active">Active</option>
                <option value="provisioning">Provisioning</option>
                <option value="suspended">Suspended</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap items-center gap-3">
            <Button size="sm" onclick={saveBillingProfile} disabled={saving || loading}>
              {saving ? "Saving…" : "Save changes"}
            </Button>
            {#if formDirty}
              <p class="text-sm text-cyan-700 dark:text-cyan-300">Unsaved billing changes</p>
            {/if}
          </div>

          <div class="mt-6 grid gap-3 sm:grid-cols-3">
            <div class="rounded-2xl border border-white/70 bg-white/70 px-4 py-4 dark:border-white/10 dark:bg-slate-950/45">
              <p class="text-xs uppercase tracking-[0.18em] text-muted-foreground">Started</p>
              <p class="mt-2 text-lg font-semibold">{formatDate(activeHub.subscriptionStartDate)}</p>
            </div>
            <div class="rounded-2xl border border-white/70 bg-white/70 px-4 py-4 dark:border-white/10 dark:bg-slate-950/45">
              <p class="text-xs uppercase tracking-[0.18em] text-muted-foreground">Expires</p>
              <p class="mt-2 text-lg font-semibold">{formatDate(activeHub.subscriptionEndDate)}</p>
            </div>
            <div class="rounded-2xl border border-white/70 bg-white/70 px-4 py-4 dark:border-white/10 dark:bg-slate-950/45">
              <p class="text-xs uppercase tracking-[0.18em] text-muted-foreground">Days left</p>
              <p class="mt-2 text-lg font-semibold">{activeHub.subscriptionDaysLeft ?? "—"}</p>
            </div>
          </div>
        </div>
      {/if}

      {#if activeView === "renewals"}
        <div class="omni-panel border-0 p-5 shadow-none space-y-4">
          <div class="rounded-2xl border border-white/70 bg-white/70 p-4 dark:border-white/10 dark:bg-slate-950/45">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="text-sm font-semibold">Renew subscription</p>
                <p class="text-sm text-muted-foreground">Monthly adds 30 days, quarterly adds 3 months, yearly adds 12 months from today.</p>
              </div>
              <Button size="sm" onclick={renewSubscription} disabled={actionLoading || loading}>
                {actionLoading ? "Renewing…" : "Renew subscription"}
              </Button>
            </div>
          </div>

          <div class="rounded-2xl border border-white/70 bg-white/70 p-4 dark:border-white/10 dark:bg-slate-950/45">
            <div class="flex flex-wrap items-end gap-3">
              <div class="min-w-[10rem] flex-1">
                <label for="add-days" class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Add days</label>
                <input id="add-days" class="omni-input mt-2" type="number" min="1" bind:value={addDaysAmount} />
              </div>
              <Button size="sm" variant="outline" onclick={addSubscriptionDays} disabled={actionLoading || loading}>
                {actionLoading ? "Applying…" : "Add days"}
              </Button>
            </div>
          </div>

          <div class="rounded-2xl border border-white/70 bg-white/70 p-4 dark:border-white/10 dark:bg-slate-950/45">
            <div class="flex flex-wrap items-end gap-3">
              <div class="min-w-[10rem] flex-1">
                <label for="subtract-days" class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Subtract days</label>
                <input id="subtract-days" class="omni-input mt-2" type="number" min="1" bind:value={subtractDaysAmount} />
              </div>
              <Button size="sm" variant="outline" onclick={subtractSubscriptionDays} disabled={actionLoading || loading}>
                {actionLoading ? "Applying…" : "Subtract days"}
              </Button>
            </div>
          </div>
        </div>
      {/if}

      {#if activeView === "state"}
        <div class="omni-panel border-0 p-5 shadow-none space-y-3 text-sm text-muted-foreground">
          <div class="flex items-center justify-between gap-3 rounded-2xl border border-white/70 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/45">
            <span>Hub type</span>
            <span class="font-medium capitalize text-foreground">{activeHub.type ?? "business"}</span>
          </div>
          <div class="flex items-center justify-between gap-3 rounded-2xl border border-white/70 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/45">
            <span>Billing cycle</span>
            <span class="font-medium capitalize text-foreground">{activeHub.billingCycle ?? "monthly"}</span>
          </div>
          <div class="flex items-center justify-between gap-3 rounded-2xl border border-white/70 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/45">
            <span>Subscription status</span>
            <span class="font-medium capitalize text-foreground">{activeHub.status ?? "provisioning"}</span>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if message}
    <div class="rounded-xl border border-slate-200/80 bg-white/85 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/55 dark:text-slate-200">{message}</div>
  {/if}
</section>
