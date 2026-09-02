<script>
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { adminLogStore } from "$lib/stores/admin-log";
  import TerminalLogPanel from "$lib/components/TerminalLogPanel.svelte";

  let entries = [];
  const release = adminLogStore.subscribe((value) => {
    entries = value;
  });

  function clearLogs() {
    adminLogStore.clear();
  }

  function formatTimestamp(value) {
    if (!value) return "Unknown";
    const normalized = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`;
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? "Unknown" : date.toLocaleString();
  }

  onMount(() => {
    adminLogStore.hydrate();
    return () => release();
  });
</script>

<section class="space-y-6">
  <header class="flex flex-wrap items-center justify-between gap-3">
    <div>
      <p class="text-sm font-medium text-primary">Immutable Logs</p>
      <h2 class="text-3xl font-bold tracking-tight">Admin audit trail (90-day retention)</h2>
      <p class="text-sm text-muted-foreground">
        Immutable local record of critical admin actions retained for 90 days.
      </p>
    </div>
    <Button variant="outline" size="sm" onclick={clearLogs}>Clear log view</Button>
  </header>

  <TerminalLogPanel
    panelTitle="admin-immutable-log"
    panelCountLabel="entries"
    tone="cyan"
    maxHeight="20rem"
    entries={entries}
    emptyText="No admin log entries recorded yet."
    columns={[
      { key: "scope", label: "Scope", render: (entry) => `${entry.scope ?? ""} · ${entry.action ?? ""}` },
      { key: "timestamp", label: "Timestamp", render: (entry) => formatTimestamp(String(entry.timestamp ?? "")) },
      { key: "details", label: "Details", render: (entry) => String(entry.details ?? "") },
      { key: "actor", label: "Actor", render: (entry) => String(entry.actor ?? "") },
    ]}
  />
</section>
