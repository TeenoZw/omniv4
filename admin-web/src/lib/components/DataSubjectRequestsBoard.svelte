<script>
  import { onDestroy, onMount } from "svelte";
  import { Download, Eye, RefreshCw, Trash2, Upload } from "lucide-svelte";

  import { Button } from "$lib/components/ui/button";
  import {
    createDataSubjectRequest,
    deleteComplianceAttachment,
    downloadComplianceAttachment,
    exportDataSubjectRequestPack,
    exportDataSubjectRequestPdf,
    exportDataSubjectRequestsCsv,
    fetchComplianceAttachmentBlob,
    fetchDataSubjectRequestDetail,
    fetchDataSubjectRequests,
    updateDataSubjectRequest,
    uploadDataSubjectRequestAttachment,
  } from "$lib/api/compliance";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  const REQUEST_TYPE_OPTIONS = [
    { value: "access", label: "Access" },
    { value: "correction", label: "Correction" },
    { value: "deletion", label: "Deletion" },
    { value: "objection", label: "Objection" },
    { value: "portability", label: "Portability" },
    { value: "complaint", label: "Complaint" },
    { value: "marketing_objection", label: "Marketing objection" },
    { value: "other", label: "Other" },
  ];

  const STATUS_OPTIONS = [
    { value: "new", label: "New" },
    { value: "in_review", label: "In review" },
    { value: "awaiting_identity", label: "Awaiting identity" },
    { value: "approved", label: "Approved" },
    { value: "rejected", label: "Rejected" },
    { value: "fulfilled", label: "Fulfilled" },
    { value: "closed", label: "Closed" },
  ];

  const CHANNEL_OPTIONS = ["email", "portal", "phone", "walk-in", "regulator", "other"];
  const SORT_OPTIONS = [
    { value: "updated_desc", label: "Recently updated" },
    { value: "due_asc", label: "Due date" },
    { value: "requester_asc", label: "Requester" },
  ];

  let requests = [];
  let summary = { total: 0, visible: 0, updated_at: null, status_counts: {} };
  let meta = { page: 1, per_page: 20, total: 0 };
  let loading = false;
  let saving = false;
  let detailLoading = false;
  let uploadSaving = false;
  let errorMessage = "";
  let statusMessage = null;
  let searchTerm = "";
  let statusFilter = "all";
  let typeFilter = "all";
  let sortMode = "updated_desc";
  let selectedId = null;
  let selected = null;
  let form = createEmptyForm();
  let attachmentFile = null;
  let attachmentTitle = "";
  let attachmentDescription = "";
  let previewAttachmentId = null;
  let previewAttachmentName = "";
  let previewUrl = "";
  let previewMimeType = "";

  onMount(() => {
    void loadRequests();
  });

  onDestroy(() => {
    clearPreview();
  });

  function createEmptyForm() {
    return {
      request_type: "access",
      status: "new",
      requester_name: "",
      data_subject_name: "",
      requester_email: "",
      requester_phone: "",
      channel: "email",
      identity_verified: false,
      summary: "",
      assigned_owner: "",
      due_date: "",
      decision: "",
      responded_at: "",
      closed_at: "",
      legal_basis: "",
      notes: "",
    };
  }

  function clearAttachmentDraft() {
    attachmentFile = null;
    attachmentTitle = "";
    attachmentDescription = "";
  }

  function clearPreview() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    previewAttachmentId = null;
    previewAttachmentName = "";
    previewUrl = "";
    previewMimeType = "";
  }

  function toInputDateTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  function fromInputDateTime(value) {
    return value ? new Date(value).toISOString() : null;
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }

  function formatBytes(value) {
    if (!value) return "0 B";
    if (value < 1024) return `${value} B`;
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }

  function requestIsOpen(item) {
    return ["new", "in_review", "awaiting_identity", "approved"].includes(item?.status ?? "");
  }

  function isRequestOverdue(item) {
    if (!item?.due_date || !requestIsOpen(item)) return false;
    const dueTime = new Date(item.due_date).getTime();
    return !Number.isNaN(dueTime) && dueTime < Date.now();
  }

  function dueStateLabel(item) {
    if (!item?.due_date) return "No SLA";
    if (!requestIsOpen(item)) return "Closed";
    return isRequestOverdue(item) ? "Overdue" : "On track";
  }

  function dueStateClass(item) {
    if (!item?.due_date) return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
    if (!requestIsOpen(item)) return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
    return isRequestOverdue(item)
      ? "border-red-300 bg-red-100 text-red-700 dark:border-red-400/30 dark:bg-red-500/10 dark:text-red-200"
      : "border-emerald-300 bg-emerald-100 text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-500/10 dark:text-emerald-200";
  }

  function requestRowClass(item) {
    const classes = [];
    if (selectedId === item.id) classes.push("omni-row-active");
    if (isRequestOverdue(item)) classes.push("omni-row-overdue");
    return classes.join(" ");
  }

  function canPreviewAttachment(attachment) {
    const mime = attachment?.mime_type ?? "";
    return mime.startsWith("image/") || mime === "application/pdf" || mime.startsWith("text/");
  }

  async function previewAttachment(attachment) {
    if (!canPreviewAttachment(attachment)) {
      statusMessage = { type: "error", text: "This file type is not previewable in the browser. Please download it instead." };
      return;
    }

    try {
      const blob = await fetchComplianceAttachmentBlob(attachment.id);
      clearPreview();
      previewUrl = URL.createObjectURL(blob);
      previewAttachmentId = attachment.id;
      previewAttachmentName = attachment.title || attachment.original_filename;
      previewMimeType = attachment.mime_type || blob.type || "application/octet-stream";
    } catch (error) {
      console.error("Failed to preview attachment", error);
      statusMessage = { type: "error", text: "Unable to preview that attachment right now." };
    }
  }

  function loadFormFromRequest(item) {
    return {
      request_type: item.request_type ?? "access",
      status: item.status ?? "new",
      requester_name: item.requester_name ?? "",
      data_subject_name: item.data_subject_name ?? "",
      requester_email: item.requester_email ?? "",
      requester_phone: item.requester_phone ?? "",
      channel: item.channel ?? "email",
      identity_verified: Boolean(item.identity_verified),
      summary: item.summary ?? "",
      assigned_owner: item.assigned_owner ?? "",
      due_date: toInputDateTime(item.due_date),
      decision: item.decision ?? "",
      responded_at: toInputDateTime(item.responded_at),
      closed_at: toInputDateTime(item.closed_at),
      legal_basis: item.legal_basis ?? "",
      notes: item.notes ?? "",
    };
  }

  function normalizePayload(source) {
    return {
      request_type: source.request_type,
      status: source.status,
      requester_name: source.requester_name.trim(),
      data_subject_name: source.data_subject_name.trim() || null,
      requester_email: source.requester_email.trim() || null,
      requester_phone: source.requester_phone.trim() || null,
      channel: source.channel.trim() || null,
      identity_verified: Boolean(source.identity_verified),
      summary: source.summary.trim(),
      assigned_owner: source.assigned_owner.trim() || null,
      due_date: fromInputDateTime(source.due_date),
      decision: source.decision.trim() || null,
      responded_at: fromInputDateTime(source.responded_at),
      closed_at: fromInputDateTime(source.closed_at),
      legal_basis: source.legal_basis.trim() || null,
      notes: source.notes.trim() || null,
    };
  }

  function validateForm() {
    if (!form.requester_name.trim()) return "Requester name is required.";
    if (!form.summary.trim()) return "A request summary is required.";
    return "";
  }

  async function loadRequests() {
    loading = true;
    errorMessage = "";
    statusMessage = null;
    try {
      const response = await fetchDataSubjectRequests({
        search: searchTerm,
        status: statusFilter,
        requestType: typeFilter,
        page: meta.page ?? 1,
        limit: meta.per_page ?? 20,
      });
      requests = response?.data?.items ?? [];
      summary = response?.summary ?? summary;
      meta = response?.meta ?? meta;

      if (selectedId && !requests.some((item) => item.id === selectedId)) {
        selectedId = null;
        selected = null;
        form = createEmptyForm();
        clearAttachmentDraft();
      }
    } catch (error) {
      console.error("Failed to load data subject requests", error);
      errorMessage = "Unable to load data subject requests.";
    } finally {
      loading = false;
    }
  }

  async function loadRequestDetail(requestId) {
    detailLoading = true;
    try {
      const detail = await fetchDataSubjectRequestDetail(requestId);
      selected = detail;
      selectedId = detail.id;
      form = loadFormFromRequest(detail);
      clearAttachmentDraft();
      if (previewAttachmentId && !detail.attachments?.some((attachment) => attachment.id === previewAttachmentId)) {
        clearPreview();
      }
    } catch (error) {
      console.error("Failed to load request detail", error);
      statusMessage = { type: "error", text: "Unable to load the full request profile right now." };
    } finally {
      detailLoading = false;
    }
  }

  function openRequest(item) {
    selectedId = item.id;
    selected = item;
    statusMessage = null;
    void loadRequestDetail(item.id);
  }

  function startNewRequest() {
    selectedId = null;
    selected = null;
    form = createEmptyForm();
    statusMessage = null;
    clearAttachmentDraft();
    clearPreview();
  }

  function sortedRequests() {
    const rows = [...requests];
    if (sortMode === "due_asc") {
      rows.sort((left, right) => {
        const leftValue = left.due_date ? new Date(left.due_date).getTime() : Number.POSITIVE_INFINITY;
        const rightValue = right.due_date ? new Date(right.due_date).getTime() : Number.POSITIVE_INFINITY;
        return leftValue - rightValue;
      });
      return rows;
    }
    if (sortMode === "requester_asc") {
      rows.sort((left, right) => left.requester_name.localeCompare(right.requester_name));
      return rows;
    }
    rows.sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime());
    return rows;
  }

  async function exportCsv() {
    try {
      await exportDataSubjectRequestsCsv({
        search: searchTerm,
        status: statusFilter,
        request_type: typeFilter,
      });
    } catch (error) {
      console.error("Failed to export request register", error);
      statusMessage = { type: "error", text: "Unable to export the data request register right now." };
    }
  }

  async function saveRequest() {
    const validationMessage = validateForm();
    if (validationMessage) {
      statusMessage = { type: "error", text: validationMessage };
      return;
    }

    const isEditing = Boolean(selectedId);
    const confirmed = await confirmSave({
      title: isEditing ? "Save request changes" : "Add data request",
      message: isEditing ? "Save these data subject request changes?" : "Add this new data subject request?",
    });
    if (!confirmed) return;

    saving = true;
    statusMessage = null;
    try {
      const payload = normalizePayload(form);
      let persisted;
      if (isEditing) {
        persisted = await updateDataSubjectRequest(selectedId, payload);
      } else {
        persisted = await createDataSubjectRequest(payload);
      }
      await loadRequests();
      if (persisted?.id) {
        await loadRequestDetail(persisted.id);
      }
      toastStore.push({
        title: isEditing ? "Request updated" : "Request added",
        message: isEditing
          ? `${persisted.reference_no} is now ${persisted.status.replaceAll("_", " ")}.`
          : `${persisted.reference_no} is now in the register.`,
        tone: "success",
      });
      statusMessage = {
        type: "success",
        text: isEditing ? "Data subject request updated." : "Data subject request added.",
      };
    } catch (error) {
      console.error("Failed to save data subject request", error);
      statusMessage = { type: "error", text: "Unable to save this request right now." };
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function uploadAttachment() {
    if (!selectedId) {
      statusMessage = { type: "error", text: "Open a request before adding evidence." };
      return;
    }
    if (!attachmentFile) {
      statusMessage = { type: "error", text: "Choose a file to upload first." };
      return;
    }

    uploadSaving = true;
    statusMessage = null;
    try {
      await uploadDataSubjectRequestAttachment(selectedId, {
        file: attachmentFile,
        title: attachmentTitle,
        description: attachmentDescription,
      });
      await loadRequestDetail(selectedId);
      await loadRequests();
      clearAttachmentDraft();
      toastStore.push({
        title: "Evidence uploaded",
        message: "The attachment is now part of the request record.",
        tone: "success",
      });
    } catch (error) {
      console.error("Failed to upload request evidence", error);
      statusMessage = { type: "error", text: "Unable to upload this evidence file right now." };
    } finally {
      uploadSaving = false;
    }
  }

  async function removeAttachment(attachment) {
    const confirmed = await confirmSave({
      title: "Remove evidence file",
      message: `Remove ${attachment.original_filename} from this request?`,
      confirmLabel: "Remove",
      tone: "destructive",
    });
    if (!confirmed) return;

    try {
      await deleteComplianceAttachment(attachment.id);
      await loadRequestDetail(selectedId);
      await loadRequests();
      if (attachment.id === previewAttachmentId) {
        clearPreview();
      }
      toastStore.push({ title: "Evidence removed", message: attachment.original_filename, tone: "success" });
    } catch (error) {
      console.error("Failed to remove request evidence", error);
      statusMessage = { type: "error", text: "Unable to remove this attachment right now." };
    }
  }

  async function openAttachment(attachment) {
    try {
      await downloadComplianceAttachment(attachment.id, attachment.original_filename);
    } catch (error) {
      console.error("Failed to download attachment", error);
      statusMessage = { type: "error", text: "Unable to download that attachment right now." };
    }
  }

  async function exportSelectedPdf() {
    if (!selectedId) return;
    try {
      await exportDataSubjectRequestPdf(selectedId);
    } catch (error) {
      console.error("Failed to export request PDF", error);
      statusMessage = { type: "error", text: "Unable to export the request PDF right now." };
    }
  }

  async function exportSelectedPack() {
    if (!selectedId) return;
    try {
      await exportDataSubjectRequestPack(selectedId);
    } catch (error) {
      console.error("Failed to export request pack", error);
      statusMessage = { type: "error", text: "Unable to export the evidence pack right now." };
    }
  }

  function changePage(direction) {
    const nextPage = (meta.page ?? 1) + direction;
    const maxPage = Math.max(1, Math.ceil((meta.total ?? 0) / (meta.per_page ?? 20)));
    meta = { ...meta, page: Math.max(1, Math.min(maxPage, nextPage)) };
    void loadRequests();
  }
</script>

<div class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Governance</p>
      <h2 class="omni-page-title">Data Requests</h2>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="outline" size="sm" onclick={startNewRequest}>New request</Button>
      <Button variant="outline" size="sm" onclick={exportCsv} disabled={requests.length === 0}>Export CSV</Button>
      <Button variant="outline" size="sm" onclick={loadRequests} disabled={loading}>
        <RefreshCw class="h-4 w-4" />
        Refresh
      </Button>
    </div>
  </header>

  <div class="omni-page-grid">
    <div class="omni-list-stage">
      <div class="omni-panel border-0 p-5 shadow-none">
        <div class="omni-toolbar-strip">
          <input
            class="omni-input min-w-[16rem] flex-1"
            type="search"
            placeholder="Search reference, requester, or summary"
            bind:value={searchTerm}
            on:change={loadRequests}
          />
          <select class="omni-select min-w-[12rem]" bind:value={statusFilter} on:change={loadRequests}>
            <option value="all">All statuses</option>
            {#each STATUS_OPTIONS as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
          <select class="omni-select min-w-[12rem]" bind:value={typeFilter} on:change={loadRequests}>
            <option value="all">All request types</option>
            {#each REQUEST_TYPE_OPTIONS as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
          <select class="omni-select min-w-[12rem]" bind:value={sortMode}>
            {#each SORT_OPTIONS as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span class="omni-inline-stat">Visible: {summary.visible}</span>
          <span class="omni-inline-stat">Total: {summary.total}</span>
          <span class="omni-inline-stat">Updated: {formatDateTime(summary.updated_at)}</span>
        </div>

        {#if errorMessage}
          <div class="omni-inline-state mt-4">{errorMessage}</div>
        {:else if loading}
          <div class="omni-loading-state mt-4">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading data requests…</span>
          </div>
        {:else}
          <div class="mt-4 omni-table-shell">
            <table class="omni-table text-sm">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Type</th>
                  <th>Requester</th>
                  <th>Status</th>
                  <th>Due</th>
                  <th>Evidence</th>
                  <th class="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {#if sortedRequests().length === 0}
                  <tr>
                    <td colspan="7" class="py-8 text-center text-muted-foreground">No data subject requests match this filter.</td>
                  </tr>
                {:else}
                  {#each sortedRequests() as item}
                    <tr class={requestRowClass(item)}>
                      <td class="font-medium text-slate-900 dark:text-white">{item.reference_no}</td>
                      <td>{item.request_type.replaceAll("_", " ")}</td>
                      <td>{item.requester_name}</td>
                      <td>{item.status.replaceAll("_", " ")}</td>
                      <td>
                        <div class="flex flex-col gap-1">
                          <span>{formatDateTime(item.due_date)}</span>
                          <span class={`inline-flex w-fit rounded-full border px-2 py-0.5 text-[11px] font-medium ${dueStateClass(item)}`}>
                            {dueStateLabel(item)}
                          </span>
                        </div>
                      </td>
                      <td>{item.attachment_count ?? 0}</td>
                      <td class="text-right">
                        <Button variant="outline" size="sm" onclick={() => openRequest(item)}>Open</Button>
                      </td>
                    </tr>
                  {/each}
                {/if}
              </tbody>
            </table>
          </div>
        {/if}

        {#if meta.total > meta.per_page}
          <div class="mt-4 flex items-center justify-between gap-3 text-sm text-muted-foreground">
            <span>
              Page {meta.page} of {Math.max(1, Math.ceil((meta.total ?? 0) / (meta.per_page ?? 20)))}
            </span>
            <div class="flex items-center gap-2">
              <Button variant="outline" size="sm" onclick={() => changePage(-1)} disabled={(meta.page ?? 1) <= 1}>Previous</Button>
              <Button
                variant="outline"
                size="sm"
                onclick={() => changePage(1)}
                disabled={(meta.page ?? 1) >= Math.max(1, Math.ceil((meta.total ?? 0) / (meta.per_page ?? 20)))}
              >
                Next
              </Button>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <div class="omni-inspector-stage">
      <div class="omni-panel border-0 p-6 shadow-none">
        <div class="space-y-5 omni-animate-fade">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-slate-500 dark:text-cyan-300/70">
                {selected ? "Request profile" : "New request"}
              </p>
              <h3 class="mt-2 text-2xl font-semibold">
                {selected ? selected.reference_no : "Add data subject request"}
              </h3>
              <p class="text-sm text-muted-foreground">
                {selected
                  ? `${selected.request_type.replaceAll("_", " ")} · ${selected.requester_name}`
                  : "Capture formal access, correction, deletion, or objection requests."}
              </p>
              {#if selected}
                <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <span class={`inline-flex rounded-full border px-2.5 py-1 font-medium ${dueStateClass(selected)}`}>
                    {dueStateLabel(selected)}
                  </span>
                  {#if selected.due_date}
                    <span class="rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
                      Due {formatDateTime(selected.due_date)}
                    </span>
                  {/if}
                </div>
              {/if}
            </div>
            <div class="flex items-center gap-2">
              {#if selected}
                <Button variant="outline" size="sm" onclick={exportSelectedPdf}>PDF</Button>
                <Button variant="outline" size="sm" onclick={exportSelectedPack}>Pack</Button>
              {/if}
              <Button variant="outline" size="sm" onclick={startNewRequest}>Reset</Button>
            </div>
          </div>

          {#if statusMessage}
            <div class={statusMessage.type === "success" ? "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700" : "rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"}>
              {statusMessage.text}
            </div>
          {/if}

          {#if detailLoading}
            <div class="omni-loading-state">
              <span class="omni-loading-spinner" aria-hidden="true"></span>
              <span>Loading request profile…</span>
            </div>
          {/if}

          <div class="omni-detail-section">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="omni-field">
                <label for="dsr-request-type">Request type</label>
                <select id="dsr-request-type" class="omni-select" bind:value={form.request_type}>
                  {#each REQUEST_TYPE_OPTIONS as option}
                    <option value={option.value}>{option.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="dsr-status">Status</label>
                <select id="dsr-status" class="omni-select" bind:value={form.status}>
                  {#each STATUS_OPTIONS as option}
                    <option value={option.value}>{option.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="dsr-requester-name">Requester name</label>
                <input id="dsr-requester-name" class="omni-input" bind:value={form.requester_name} placeholder="Full name or authorised agent" />
              </div>
              <div class="omni-field">
                <label for="dsr-data-subject-name">Data subject name</label>
                <input id="dsr-data-subject-name" class="omni-input" bind:value={form.data_subject_name} placeholder="If different from requester" />
              </div>
              <div class="omni-field">
                <label for="dsr-requester-email">Requester email</label>
                <input id="dsr-requester-email" class="omni-input" type="email" bind:value={form.requester_email} placeholder="name@example.com" />
              </div>
              <div class="omni-field">
                <label for="dsr-requester-phone">Requester phone</label>
                <input id="dsr-requester-phone" class="omni-input" bind:value={form.requester_phone} placeholder="+27..." />
              </div>
              <div class="omni-field">
                <label for="dsr-channel">Channel</label>
                <select id="dsr-channel" class="omni-select" bind:value={form.channel}>
                  {#each CHANNEL_OPTIONS as option}
                    <option value={option}>{option}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="dsr-assigned-owner">Assigned owner</label>
                <input id="dsr-assigned-owner" class="omni-input" bind:value={form.assigned_owner} placeholder="Compliance owner" />
              </div>
              <div class="omni-field">
                <label for="dsr-due-date">Due date</label>
                <input id="dsr-due-date" class="omni-input" type="datetime-local" bind:value={form.due_date} />
              </div>
              <div class="omni-field">
                <label for="dsr-responded-at">Responded at</label>
                <input id="dsr-responded-at" class="omni-input" type="datetime-local" bind:value={form.responded_at} />
              </div>
              <div class="omni-field">
                <label for="dsr-closed-at">Closed at</label>
                <input id="dsr-closed-at" class="omni-input" type="datetime-local" bind:value={form.closed_at} />
              </div>
              <div class="omni-field">
                <label for="dsr-legal-basis">Legal basis</label>
                <input id="dsr-legal-basis" class="omni-input" bind:value={form.legal_basis} placeholder="POPIA / PAIA basis" />
              </div>
            </div>

            <label class="mt-4 flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
              <input type="checkbox" class="h-4 w-4 rounded border-border" bind:checked={form.identity_verified} />
              Identity or authority verified
            </label>

            <div class="mt-4 grid gap-4">
              <div class="omni-field">
                <label for="dsr-summary">Summary</label>
                <textarea id="dsr-summary" class="omni-textarea" bind:value={form.summary} placeholder="Describe the request and what information is being sought."></textarea>
              </div>
              <div class="omni-field">
                <label for="dsr-decision">Decision</label>
                <textarea id="dsr-decision" class="omni-textarea" bind:value={form.decision} placeholder="Record approval, rejection, or response decision."></textarea>
              </div>
              <div class="omni-field">
                <label for="dsr-notes">Notes</label>
                <textarea id="dsr-notes" class="omni-textarea" bind:value={form.notes} placeholder="Internal handling notes, identity evidence, or communications."></textarea>
              </div>
            </div>
          </div>

          {#if selected}
            <div class="omni-detail-section">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Evidence attachments</p>
                  <p class="mt-2 text-sm text-muted-foreground">Attach supporting forms, identity proofs, or response evidence.</p>
                </div>
                <span class="omni-inline-stat">{selected.attachments?.length ?? 0} files</span>
              </div>

              <div class="mt-4 grid gap-4 md:grid-cols-[1.2fr,1fr,auto]">
                <div class="omni-field">
                  <label for="dsr-attachment-file">Evidence file</label>
                  <input
                    id="dsr-attachment-file"
                    class="omni-input"
                    type="file"
                    on:change={(event) => {
                      attachmentFile = event.currentTarget.files?.[0] ?? null;
                    }}
                  />
                </div>
                <div class="omni-field">
                  <label for="dsr-attachment-title">Title</label>
                  <input id="dsr-attachment-title" class="omni-input" bind:value={attachmentTitle} placeholder="Identity copy, response letter…" />
                </div>
                <div class="omni-field">
                  <label for="dsr-attachment-description">Description</label>
                  <input id="dsr-attachment-description" class="omni-input" bind:value={attachmentDescription} placeholder="Optional note" />
                </div>
              </div>

              <div class="mt-4 flex items-center justify-end gap-2">
                <Button variant="outline" size="sm" onclick={clearAttachmentDraft}>Clear</Button>
                <Button size="sm" onclick={uploadAttachment} disabled={uploadSaving || !attachmentFile}>
                  <Upload class="mr-2 h-4 w-4" />
                  {uploadSaving ? "Uploading…" : "Upload evidence"}
                </Button>
              </div>

              <div class="mt-4 space-y-3">
                {#if selected.attachments?.length}
                  {#each selected.attachments as attachment}
                    <article class="rounded-2xl border border-slate-200/70 bg-white/80 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/60">
                      <div class="flex items-start justify-between gap-3">
                        <div>
                          <p class="font-medium text-slate-900 dark:text-white">{attachment.title || attachment.original_filename}</p>
                          <p class="mt-1 text-sm text-muted-foreground">
                            {attachment.original_filename} · {formatBytes(attachment.size_bytes)} · {formatDateTime(attachment.created_at)}
                          </p>
                          {#if attachment.description}
                            <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{attachment.description}</p>
                          {/if}
                        </div>
                        <div class="flex items-center gap-2">
                          {#if canPreviewAttachment(attachment)}
                            <Button variant="outline" size="icon" onclick={() => previewAttachment(attachment)} aria-label="Preview attachment">
                              <Eye class="h-4 w-4" />
                            </Button>
                          {/if}
                          <Button variant="outline" size="icon" onclick={() => openAttachment(attachment)} aria-label="Download attachment">
                            <Download class="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="icon" onclick={() => removeAttachment(attachment)} aria-label="Remove attachment">
                            <Trash2 class="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </article>
                  {/each}
                {:else}
                  <div class="omni-inline-state">No evidence files attached yet.</div>
                {/if}
              </div>

              {#if previewUrl}
                <div class="mt-4 rounded-2xl border border-slate-200/70 bg-white/90 p-4 dark:border-slate-800 dark:bg-slate-950/70">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Attachment preview</p>
                      <p class="mt-1 text-sm font-medium text-slate-900 dark:text-white">{previewAttachmentName}</p>
                    </div>
                    <Button variant="outline" size="sm" onclick={clearPreview}>Close preview</Button>
                  </div>

                  <div class="mt-4 overflow-hidden rounded-xl border border-slate-200/70 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/80">
                    {#if previewMimeType.startsWith("image/")}
                      <img src={previewUrl} alt={previewAttachmentName} class="max-h-[28rem] w-full object-contain" />
                    {:else}
                      <iframe src={previewUrl} title={previewAttachmentName} class="h-[28rem] w-full bg-white dark:bg-slate-950"></iframe>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>

            <div class="omni-detail-section text-sm text-muted-foreground">
              <div class="grid gap-3 md:grid-cols-2">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Created</p>
                  <p class="mt-1 text-slate-700 dark:text-slate-200">{formatDateTime(selected.created_at)}</p>
                </div>
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Updated</p>
                  <p class="mt-1 text-slate-700 dark:text-slate-200">{formatDateTime(selected.updated_at)}</p>
                </div>
              </div>
            </div>
          {/if}

          <div class="flex flex-wrap items-center justify-end gap-2">
            <Button size="sm" onclick={saveRequest} disabled={saving}>
              {saving ? "Saving…" : selected ? "Save changes" : "Add request"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
