<script lang="ts">
  import { onDestroy } from "svelte";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { fetchCurrentHubSummary, type HubSummaryResponse } from "$lib/api/hub";
  import { sessionStore } from "$lib/api/session";

  let summary: HubSummaryResponse | null = null;
  let loading = true;
  let refreshing = false;
  let errorMessage = "";
  let lastHubId: string | null = null;
  let pollHandle: ReturnType<typeof setInterval> | null = null;

  $: session = $sessionStore;
  $: currentHubId = session?.hubId ?? null;

  async function loadSummary(force = false) {
    if (!currentHubId || (!force && lastHubId === currentHubId && summary)) return;
    lastHubId = currentHubId;
    if (!summary) loading = true;
    refreshing = true;
    errorMessage = "";
    try {
      summary = await fetchCurrentHubSummary();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "Unable to load billing details.";
    } finally {
      loading = false;
      refreshing = false;
    }
  }

  function formatDaysLeft(days?: number | null) {
    if (days === null || days === undefined) return "No fixed expiry";
    if (days < 0) return `Expired ${Math.abs(days)} day(s) ago`;
    return `${days} day(s) remaining`;
  }

  function subscriptionAlert(subscription?: HubSummaryResponse["subscription"] | null) {
    if (!subscription) return null;
    const status = String(subscription.status ?? "").toLowerCase();
    const days = subscription.days_left;

    if (["suspended", "inactive", "cancelled"].includes(status)) {
      return {
        tone: "critical",
        message: "Your subscription is inactive. Please contact billing support to restore service.",
      };
    }
    if (typeof days === "number" && days < 0) {
      return {
        tone: "critical",
        message: `Your subscription expired ${Math.abs(days)} day(s) ago. Please renew or contact billing support as soon as possible.`,
      };
    }
    if (typeof days === "number" && days <= 5) {
      return {
        tone: "warning",
        message: "Your subscription is close to expiry. Please settle payment promptly to avoid service interruption.",
      };
    }
    return null;
  }

  function formatDate(value?: string | null) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString();
  }

  function estimatedBaseFee(tier?: string | null) {
    const normalized = (tier ?? "").toLowerCase();
    if (normalized === "business") return "$15 / month";
    return "$10 / month";
  }

  $: billingAlert = subscriptionAlert(summary?.subscription);

  $: if (currentHubId) {
    void loadSummary(false);
  }

  $: if (currentHubId && !pollHandle) {
    pollHandle = setInterval(() => {
      void loadSummary(true);
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
  });
</script>

<section class="space-y-6">
  <div class="flex flex-wrap items-center justify-between gap-3">
    <div>
      <p class="text-xs uppercase tracking-wide text-muted-foreground">Account billing</p>
      <h1 class="text-3xl font-semibold">Billing and subscription</h1>
    </div>
    <Button size="sm" variant="outline" onclick={() => loadSummary(true)} disabled={refreshing}>
      {refreshing ? "Refreshing…" : "Refresh"}
    </Button>
  </div>

  {#if errorMessage}
    <p class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</p>
  {/if}

  {#if !loading && billingAlert}
    <p
      class={`rounded-xl px-4 py-3 text-sm ${
        billingAlert.tone === "critical"
          ? "border border-red-300 bg-red-50 text-red-800"
          : "border border-amber-300 bg-amber-50 text-amber-800"
      }`}
    >
      {billingAlert.message}
    </p>
  {/if}

  <div class="grid gap-6 lg:grid-cols-3">
    <Card class="lg:col-span-2">
      <CardHeader>
        <CardTitle>Subscription overview</CardTitle>
      </CardHeader>
      <CardContent class="grid gap-4 sm:grid-cols-2">
        {#if loading}
          <div class="h-24 animate-pulse rounded-lg bg-muted/50"></div>
          <div class="h-24 animate-pulse rounded-lg bg-muted/50"></div>
        {:else}
          <div class="space-y-2 text-sm">
            <p>Status: <span class="font-medium capitalize">{summary?.subscription.status ?? "—"}</span></p>
            <p>Plan: <span class="font-medium">{summary?.subscription.tier ?? "Unknown"}</span></p>
            <p>Hub type: <span class="font-medium capitalize">{summary?.hub.type ?? "Unknown"}</span></p>
            <p>Billing cycle: <span class="font-medium capitalize">{summary?.subscription.billing_cycle ?? "monthly"}</span></p>
            <p>Days remaining: <span class="font-medium">{formatDaysLeft(summary?.subscription.days_left)}</span></p>
          </div>
          <div class="space-y-2 text-sm">
            <p>Subscription start: <span class="font-medium">{formatDate(summary?.subscription.start_date)}</span></p>
            <p>Subscription expiry: <span class="font-medium">{formatDate(summary?.subscription.end_date)}</span></p>
            <p>Estimated base fee: <span class="font-medium">{estimatedBaseFee(summary?.subscription.tier)}</span></p>
            <p>Hub code: <span class="font-medium">{summary?.hub.code ?? session?.hubCode ?? "—"}</span></p>
          </div>
        {/if}
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Billing snapshot</CardTitle>
      </CardHeader>
      <CardContent class="space-y-3">
        <Badge variant="secondary">Hub: {summary?.hub.name ?? session?.hubName ?? "—"}</Badge>
        <Badge variant="secondary">Status: {summary?.subscription.status ?? "—"}</Badge>
        <Badge variant="secondary">Cycle: {summary?.subscription.billing_cycle ?? "—"}</Badge>
        <Badge variant="secondary">Days remaining: {formatDaysLeft(summary?.subscription.days_left)}</Badge>
        <Badge variant="secondary">Expiry: {formatDate(summary?.subscription.end_date)}</Badge>
      </CardContent>
    </Card>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>Billing support</CardTitle>
    </CardHeader>
    <CardContent class="flex flex-wrap gap-3">
      <a
        class="inline-flex items-center rounded-md border px-3 py-2 text-sm font-medium hover:bg-muted/40"
        href={`mailto:info@omnilogistics.co.zw?subject=${encodeURIComponent(`Billing support - ${summary?.hub.code ?? session?.hubCode ?? "Hub"}`)}`}
      >
        Email billing support
      </a>
      <a
        class="inline-flex items-center rounded-md border px-3 py-2 text-sm font-medium hover:bg-muted/40"
        href={`mailto:info@omnilogistics.co.zw?subject=${encodeURIComponent(`Subscription change request - ${summary?.hub.code ?? session?.hubCode ?? "Hub"}`)}`}
      >
        Request a subscription change
      </a>
    </CardContent>
  </Card>
</section>
