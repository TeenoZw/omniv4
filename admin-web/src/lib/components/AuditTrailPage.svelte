<script>
  import { onDestroy, onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import TerminalLogPanel from "$lib/components/TerminalLogPanel.svelte";
  import { fetchAdminActivity, fetchAdminActivityIntegrity } from "$lib/api/activity";
  import { downloadComplianceAttachment, fetchComplianceAttachmentBlob } from "$lib/api/compliance";

  let entries = [];
  let loading = false;
  let errorMessage = "";
  let moduleFilter = "all";
  let actorFilter = "";
  let searchFilter = "";
  let fromDate = "";
  let toDate = "";
  let integrity = null;
  let integrityLoading = false;
  let integrityError = "";
  let selectedEntryId = null;
  let previewUrl = "";
  let previewName = "";
  let previewMimeType = "";

  function parseAuditTimestamp(value) {
    if (!value) return null;
    const normalized = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`;
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  $: moduleOptions = Array.from(new Set(entries.map((entry) => entry.module).filter(Boolean))).sort();
  $: normalizedActor = actorFilter.trim().toLowerCase();
  $: normalizedSearch = searchFilter.trim().toLowerCase();
  $: fromDateTime = fromDate ? new Date(`${fromDate}T00:00:00`).getTime() : null;
  $: toDateTime = toDate ? new Date(`${toDate}T23:59:59.999`).getTime() : null;
  $: filteredEntries = entries.filter((entry) => {
    const moduleMatch = moduleFilter === "all" || entry.module === moduleFilter;
    const actor = String(entry.user ?? entry.user_email ?? "").toLowerCase();
    const actorMatch = !normalizedActor || actor.includes(normalizedActor);
    const detailsText = String(entry.details_message ?? entry.details ?? "");
    const metaText = entry.details_meta ? JSON.stringify(entry.details_meta) : "";
    const haystack = `${entry.change ?? ""} ${detailsText} ${metaText} ${entry.target_type ?? ""} ${entry.target_id ?? ""}`.toLowerCase();
    const searchMatch = !normalizedSearch || haystack.includes(normalizedSearch);
    const parsedTimestamp = parseAuditTimestamp(entry.timestamp);
    const ts = parsedTimestamp ? parsedTimestamp.getTime() : null;
    const fromMatch = fromDateTime === null || (ts !== null && ts >= fromDateTime);
    const toMatch = toDateTime === null || (ts !== null && ts <= toDateTime);
    return moduleMatch && actorMatch && searchMatch && fromMatch && toMatch;
  });
  $: integrityValid = integrity ? (integrity.valid ?? integrity.ok ?? false) : false;
  $: {
    if (!filteredEntries.length) {
      selectedEntryId = null;
    } else if (!filteredEntries.some((entry) => String(entry.id) === String(selectedEntryId))) {
      selectedEntryId = String(filteredEntries[0].id);
    }
  }
  $: selectedEntry = filteredEntries.find((entry) => String(entry.id) === String(selectedEntryId)) ?? null;
  $: if (previewUrl && (!selectedEntry || !attachmentMeta(selectedEntry))) {
    clearPreview();
  }

  function formatDate(value) {
    const date = parseAuditTimestamp(value);
    if (!date) return "—";
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function formatTime(value) {
    const date = parseAuditTimestamp(value);
    if (!date) return "—";
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function clearPreview() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    previewUrl = "";
    previewName = "";
    previewMimeType = "";
  }

  onDestroy(() => {
    clearPreview();
  });

  function detailsMessage(entry) {
    return entry?.details_message ?? entry?.details ?? "—";
  }

  function attachmentMeta(entry) {
    return entry?.details_meta?.attachment_id ? entry.details_meta : null;
  }

  function canPreviewEntryAttachment(entry) {
    const mime = attachmentMeta(entry)?.attachment_mime ?? "";
    return Boolean(mime.startsWith("image/") || mime === "application/pdf" || mime.startsWith("text/"));
  }

  async function previewEntryAttachment(entry) {
    const meta = attachmentMeta(entry);
    if (!meta?.attachment_id) return;
    try {
      const blob = await fetchComplianceAttachmentBlob(meta.attachment_id);
      clearPreview();
      previewUrl = URL.createObjectURL(blob);
      previewName = meta.attachment_name || meta.attachment_title || `Attachment ${meta.attachment_id}`;
      previewMimeType = meta.attachment_mime || blob.type || "application/octet-stream";
    } catch (error) {
      console.error("Unable to preview compliance evidence", error);
    }
  }

  async function downloadEntryAttachment(entry) {
    const meta = attachmentMeta(entry);
    if (!meta?.attachment_id) return;
    await downloadComplianceAttachment(meta.attachment_id, meta.attachment_name || `compliance-attachment-${meta.attachment_id}`);
  }

  async function loadActivity() {
    try {
      loading = true;
      errorMessage = "";
      entries = await fetchAdminActivity(300);
    } catch (error) {
      console.error("Unable to load audit activity", error);
      errorMessage = "Unable to load audit records.";
    } finally {
      loading = false;
    }
  }

  async function verifyIntegrity() {
    try {
      integrityLoading = true;
      integrityError = "";
      integrity = await fetchAdminActivityIntegrity(1000);
    } catch (error) {
      console.error("Unable to verify audit integrity", error);
      integrityError = "Integrity verification failed.";
    } finally {
      integrityLoading = false;
    }
  }

  onMount(() => {
    void loadActivity();
    void verifyIntegrity();
  });

  function csvCell(value) {
    const raw = String(value ?? "");
    const escaped = raw.replaceAll('"', '""');
    return `"${escaped}"`;
  }

  function exportCsv() {
    if (!filteredEntries.length) return;
    const headers = ["timestamp", "module", "change", "details", "user", "user_email", "target_type", "target_id"];
    const rows = filteredEntries.map((entry) =>
      [
        entry.timestamp ?? "",
        entry.module ?? "",
        entry.change ?? "",
        entry.details ?? "",
        entry.user ?? "",
        entry.user_email ?? "",
        entry.target_type ?? "",
        entry.target_id ?? "",
      ]
        .map(csvCell)
        .join(","),
    );
    const csv = [headers.map(csvCell).join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().slice(0, 19).replaceAll(":", "-");
    const link = document.createElement("a");
    link.href = url;
    link.download = `omni-audit-${stamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
</script>

<section class="space-y-4">
  <div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/[0.03]">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.2em] text-cyan-700 dark:text-cyan-300/80">Audit</p>
        <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Immutable audit trail</h3>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" onclick={exportCsv} disabled={!filteredEntries.length}>
          Export CSV
        </Button>
        <Button variant="outline" size="sm" onclick={loadActivity} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh records"}
        </Button>
        <Button variant="outline" size="sm" onclick={verifyIntegrity} disabled={integrityLoading}>
          {integrityLoading ? "Verifying…" : "Verify integrity"}
        </Button>
      </div>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-3 text-xs">
      {#if integrityError}
        <span class="rounded-full border border-red-300 bg-red-100 px-3 py-1 text-red-700 dark:border-red-400/40 dark:bg-red-500/15 dark:text-red-200">{integrityError}</span>
      {:else if integrity}
        <span class="rounded-full border px-3 py-1 {integrityValid ? 'border-emerald-300 bg-emerald-100 text-emerald-700 dark:border-emerald-400/40 dark:bg-emerald-500/15 dark:text-emerald-200' : 'border-red-300 bg-red-100 text-red-700 dark:border-red-400/40 dark:bg-red-500/15 dark:text-red-200'}">
          Chain {integrityValid ? "valid" : "invalid"}
        </span>
        <span class="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-slate-700 dark:border-white/20 dark:bg-white/10 dark:text-white/80">
          Checked {integrity.checked ?? 0} entries
        </span>
      {/if}
      <span class="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-slate-700 dark:border-white/20 dark:bg-white/10 dark:text-white/80">
        Showing {filteredEntries.length} of {entries.length}
      </span>
    </div>
  </div>

  <div class="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-5 dark:border-white/10 dark:bg-white/[0.03]">
    <label class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-white/60">
      Module
      <select class="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-white/10 dark:text-white" value={moduleFilter} on:change={(event) => (moduleFilter = event.target.value)}>
        <option value="all">All modules</option>
        {#each moduleOptions as moduleName (moduleName)}
          <option value={moduleName}>{moduleName}</option>
        {/each}
      </select>
    </label>
    <label class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-white/60">
      User
      <input
        class="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-white/10 dark:text-white"
        type="search"
        value={actorFilter}
        placeholder="Filter by user or email"
        on:input={(event) => (actorFilter = event.target.value)}
      />
    </label>
    <label class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-white/60">
      Search
      <input
        class="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-white/10 dark:text-white"
        type="search"
        value={searchFilter}
        placeholder="Search change, detail, or target"
        on:input={(event) => (searchFilter = event.target.value)}
      />
    </label>
    <label class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-white/60">
      From
      <input
        class="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-white/10 dark:text-white"
        type="date"
        value={fromDate}
        on:input={(event) => (fromDate = event.target.value)}
      />
    </label>
    <label class="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-white/60">
      To
      <input
        class="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-white/20 dark:bg-white/10 dark:text-white"
        type="date"
        value={toDate}
        on:input={(event) => (toDate = event.target.value)}
      />
    </label>
  </div>

  {#if errorMessage}
    <p class="rounded-xl border border-red-300 bg-red-100 px-3 py-3 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-500/15 dark:text-red-200">
      {errorMessage}
    </p>
  {:else}
    <div class="omni-page-grid">
      <div class="omni-list-stage">
        {#if loading && entries.length === 0}
          <div class="omni-loading-state">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading audit records…</span>
          </div>
        {:else if filteredEntries.length === 0}
          <p class="rounded-xl border border-slate-300 bg-slate-100 px-3 py-3 text-sm text-slate-700 dark:border-white/15 dark:bg-white/5 dark:text-white/70">
            No audit records match the current filters.
          </p>
        {:else}
          <TerminalLogPanel
            panelTitle="omni-admin-audit"
            panelCountLabel="entries"
            tone="cyan"
            maxHeight="34rem"
            entries={filteredEntries}
            selectable={true}
            selectedEntryId={selectedEntryId}
            on:select={(event) => (selectedEntryId = String(event.detail.entry?.id ?? ""))}
            columns={[
              { key: "date", label: "Date", render: (entry) => formatDate(String(entry.timestamp ?? "")) },
              { key: "time", label: "Time", render: (entry) => formatTime(String(entry.timestamp ?? "")) },
              { key: "module", label: "Module", render: (entry) => String(entry.module ?? "") },
              { key: "change", label: "Change", render: (entry) => String(entry.change ?? "") },
              { key: "details", label: "What changed", render: (entry) => detailsMessage(entry) },
              { key: "user_email", label: "Changed by (email)", render: (entry) => String(entry.user_email ?? entry.user ?? "") },
            ]}
          />
        {/if}
      </div>

      <div class="omni-inspector-stage">
        <div class="omni-panel border-0 p-5 shadow-none">
          {#if selectedEntry}
            <div class="space-y-4 omni-animate-fade">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">Audit entry</p>
                  <h3 class="mt-2 text-xl font-semibold text-slate-900 dark:text-white">{selectedEntry.change}</h3>
                  <p class="mt-1 text-sm text-muted-foreground">{detailsMessage(selectedEntry)}</p>
                </div>
                <span class="omni-inline-stat">#{selectedEntry.sequence_no}</span>
              </div>

              <div class="omni-detail-section">
                <div class="grid gap-3 md:grid-cols-2">
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Module</p>
                    <p class="mt-1 text-sm text-slate-700 dark:text-slate-200">{selectedEntry.module}</p>
                  </div>
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Changed by</p>
                    <p class="mt-1 text-sm text-slate-700 dark:text-slate-200">{selectedEntry.user_email ?? selectedEntry.user ?? "system"}</p>
                  </div>
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Date</p>
                    <p class="mt-1 text-sm text-slate-700 dark:text-slate-200">{formatDate(selectedEntry.timestamp)} {formatTime(selectedEntry.timestamp)}</p>
                  </div>
                  <div>
                    <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Target</p>
                    <p class="mt-1 text-sm text-slate-700 dark:text-slate-200">{selectedEntry.target_type || "—"} {selectedEntry.target_id ? `· ${selectedEntry.target_id}` : ""}</p>
                  </div>
                </div>
              </div>

              {#if selectedEntry.details_meta}
                <div class="omni-detail-section">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Evidence context</p>
                      <p class="mt-1 text-sm text-muted-foreground">
                        {selectedEntry.details_meta.reference_no || "Compliance record"}
                        {#if selectedEntry.details_meta.attachment_name}
                          · {selectedEntry.details_meta.attachment_name}
                        {/if}
                      </p>
                    </div>
                    {#if attachmentMeta(selectedEntry)}
                      <div class="flex items-center gap-2">
                        {#if canPreviewEntryAttachment(selectedEntry)}
                          <Button variant="outline" size="sm" onclick={() => previewEntryAttachment(selectedEntry)}>Preview evidence</Button>
                        {/if}
                        <Button variant="outline" size="sm" onclick={() => downloadEntryAttachment(selectedEntry)}>Download evidence</Button>
                      </div>
                    {/if}
                  </div>

                  <div class="mt-4 grid gap-3 md:grid-cols-2 text-sm text-slate-700 dark:text-slate-200">
                    {#each Object.entries(selectedEntry.details_meta) as [key, value]}
                      <div>
                        <p class="text-xs uppercase tracking-[0.18em] text-slate-500">{key.replaceAll("_", " ")}</p>
                        <p class="mt-1 break-words">{String(value)}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              {#if previewUrl}
                <div class="omni-detail-section">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Evidence preview</p>
                      <p class="mt-1 text-sm font-medium text-slate-900 dark:text-white">{previewName}</p>
                    </div>
                    <Button variant="outline" size="sm" onclick={clearPreview}>Close preview</Button>
                  </div>

                  <div class="mt-4 overflow-hidden rounded-xl border border-slate-200/70 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/80">
                    {#if previewMimeType.startsWith("image/")}
                      <img src={previewUrl} alt={previewName} class="max-h-[28rem] w-full object-contain" />
                    {:else}
                      <iframe src={previewUrl} title={previewName} class="h-[28rem] w-full bg-white dark:bg-slate-950"></iframe>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {:else}
            <div class="omni-inline-state">Select an audit entry to inspect its details and any linked evidence.</div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</section>
