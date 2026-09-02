<script lang="ts">
  import { createEventDispatcher, onDestroy } from "svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import { changeLogStore, type ChangeLogEntry } from "$lib/stores/change-log";
  import TerminalLogPanel from "$lib/components/TerminalLogPanel.svelte";

  const dispatch = createEventDispatcher<{ close: void }>();

  let entries: ChangeLogEntry[] = [];
  const release = changeLogStore.subscribe((value) => {
    entries = value;
  });

  onDestroy(() => {
    release();
  });

  function formatTimestamp(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  }

  function handleClose() {
    dispatch("close");
  }
</script>

<section class="space-y-6">
  <div class="flex flex-wrap items-center justify-between gap-3">
    <div>
      <p class="text-sm font-medium text-primary">Inventory audit trail</p>
      <h2 class="text-3xl font-bold tracking-tight">Full change log</h2>
      <p class="text-sm text-muted-foreground">
        Review every device update or removal captured on this workstation. Entries persist locally even after logging out.
      </p>
    </div>
    <div class="flex flex-col items-end gap-2 text-sm text-muted-foreground">
      <span>Total entries: <strong class="text-foreground">{entries.length}</strong></span>
      <Button variant="outline" size="sm" onclick={handleClose}>
        Back to inventory
      </Button>
    </div>
  </div>

  {#if entries.length === 0}
    <div class="rounded-lg border border-dashed border-border/70 bg-muted/30 p-6 text-sm text-muted-foreground">
      No changes logged yet. Head to the inventory table to start editing devices and the audit trail will populate automatically.
    </div>
  {:else}
    <TerminalLogPanel
      panelTitle="inventory-audit-terminal"
      panelCountLabel="entries"
      tone="emerald"
      maxHeight="34rem"
      entries={entries}
      columns={[
        { key: "action", label: "Action", render: (entry) => String(entry.action ?? "") },
        { key: "timestamp", label: "Timestamp", render: (entry) => formatTimestamp(String(entry.timestamp ?? "")) },
        { key: "summary", label: "Summary", render: (entry) => String(entry.summary ?? "") },
        { key: "details", label: "Details", render: (entry) => String(entry.details ?? "") },
        { key: "actor", label: "User", render: (entry) => String(entry.actor ?? "") },
      ]}
    />
  {/if}
</section>
