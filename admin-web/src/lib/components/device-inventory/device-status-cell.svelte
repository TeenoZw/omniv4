<script lang="ts">
  export let status = "in_stock";

  const STATUS_CLASSES: Record<string, string> = {
    in_stock: "bg-slate-500/10 text-slate-700 border-slate-400/30 dark:text-slate-200",
    assigned: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20 dark:text-emerald-300",
    maintenance: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    faulty: "bg-rose-500/10 text-rose-500 border-rose-500/20",
    retired: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
  };

  const STATUS_LABELS: Record<string, string> = {
    in_stock: "In Stock",
    assigned: "Deployed",
    maintenance: "Maintenance",
    faulty: "Faulty",
    retired: "Retired",
  };

  $: normalizedStatus = status === "active" ? "assigned" : status;
  $: statusClass = STATUS_CLASSES[normalizedStatus] ?? STATUS_CLASSES.in_stock;
  $: statusLabel = STATUS_LABELS[normalizedStatus] ?? normalizedStatus;
</script>

<span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold {statusClass}">
  {statusLabel}
</span>
