<script lang="ts">
  import { createEventDispatcher } from "svelte";

  type Column = {
    key: string;
    label: string;
    align?: "left" | "right";
    render?: (entry: Record<string, unknown>) => string;
  };

  export let panelTitle = "terminal-log";
  export let panelCountLabel = "events";
  export let entries: Array<Record<string, unknown>> = [];
  export let columns: Column[] = [];
  export let tone: "cyan" | "emerald" | "amber" = "cyan";
  export let maxHeight = "18rem";
  export let emptyText = "No entries recorded.";
  export let selectable = false;
  export let selectedEntryId: string | null = null;

  const toneClasses = {
    cyan: {
      panel: "border-cyan-500/30 bg-[#060b14]",
      header: "text-cyan-300/80",
      frame: "border-cyan-500/20 bg-black/40",
      thead: "bg-[#071121] text-cyan-300/80",
      row: "border-cyan-500/15",
      cellMuted: "text-cyan-200/80",
      cellStrong: "text-cyan-100/90",
    },
    emerald: {
      panel: "border-emerald-500/30 bg-[#070e0b]",
      header: "text-emerald-300/80",
      frame: "border-emerald-500/20 bg-black/40",
      thead: "bg-[#0a1511] text-emerald-300/80",
      row: "border-emerald-500/15",
      cellMuted: "text-emerald-200/80",
      cellStrong: "text-emerald-100/90",
    },
    amber: {
      panel: "border-amber-400/30 bg-[#17120a]",
      header: "text-amber-200/80",
      frame: "border-amber-400/20 bg-black/40",
      thead: "bg-[#1d150b] text-amber-200/80",
      row: "border-amber-400/15",
      cellMuted: "text-amber-200/80",
      cellStrong: "text-amber-100/90",
    },
  } as const;
  const dispatch = createEventDispatcher<{ select: { entry: Record<string, unknown> } }>();

  $: palette = toneClasses[tone];

  function entryId(entry: Record<string, unknown>, idx: number): string {
    const raw = entry.id ?? idx;
    return raw === null || raw === undefined ? String(idx) : String(raw);
  }

  function getValue(entry: Record<string, unknown>, column: Column): string {
    if (typeof column.render === "function") {
      return column.render(entry);
    }
    const raw = entry[column.key];
    return raw === null || raw === undefined ? "" : String(raw);
  }

  function getCellClasses(entry: Record<string, unknown>, column: Column): string {
    const value = getValue(entry, column);
    const classes: string[] = [];
    if (column.key === "date" || column.key === "time") {
      classes.push(palette.cellMuted);
    }
    if (column.key === "change") {
      classes.push("font-semibold text-emerald-200");
    }
    if (column.key === "details" && value) {
      classes.push("whitespace-pre-wrap leading-relaxed");
      if (value.includes("->") || value.includes("expiry now") || value.includes("Added")) {
        classes.push("rounded-sm bg-amber-500/10 px-2 py-1 text-amber-100");
      }
    }
    if (column.key === "user_email") {
      classes.push("font-semibold text-cyan-200");
    }
    return classes.join(" ");
  }

  function selectEntry(entry: Record<string, unknown>) {
    if (!selectable) return;
    dispatch("select", { entry });
  }
</script>

<div class={`mx-auto w-full max-w-[980px] rounded-xl border p-3 ${palette.panel}`}>
  <div class={`mb-2 flex items-center justify-between text-[11px] font-mono uppercase tracking-[0.18em] ${palette.header}`}>
    <span>{panelTitle}</span>
    <span>{entries.length} {panelCountLabel}</span>
  </div>

  {#if entries.length === 0}
    <div class={`rounded-md border p-3 text-xs font-mono ${palette.frame} ${palette.cellMuted}`}>
      {emptyText}
    </div>
  {:else}
    <div class={`overflow-y-auto rounded-md border ${palette.frame}`} style={`max-height: ${maxHeight};`}>
      <table class={`min-w-full text-xs font-mono ${palette.cellStrong}`}>
        <thead class={`sticky top-0 text-[11px] uppercase tracking-[0.14em] ${palette.thead}`}>
          <tr>
            {#each columns as column}
              <th class={`px-3 py-2 ${column.align === "right" ? "text-right" : "text-left"}`}>{column.label}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each entries as entry, idx (`${entry.id ?? idx}`)}
            <tr
              class={`border-t ${palette.row} ${selectable ? "cursor-pointer transition-colors" : ""} ${selectable && selectedEntryId === entryId(entry, idx) ? "bg-white/10" : ""}`}
              on:click={() => selectEntry(entry)}
            >
              {#each columns as column}
                <td class={`px-3 py-2 ${column.align === "right" ? "text-right" : "text-left"} ${getCellClasses(entry, column)}`}>
                  {getValue(entry, column)}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
