<script>
  import { onDestroy, onMount } from "svelte";
  import { Download, Eye, RefreshCw, Trash2, Upload } from "lucide-svelte";

  import { Button } from "$lib/components/ui/button";
  import {
    createSecurityIncident,
    deleteComplianceAttachment,
    downloadComplianceAttachment,
    exportSecurityIncidentPack,
    exportSecurityIncidentPdf,
    exportSecurityIncidentsCsv,
    fetchComplianceAttachmentBlob,
    fetchSecurityIncidentDetail,
    fetchSecurityIncidents,
    updateSecurityIncident,
    uploadSecurityIncidentAttachment,
  } from "$lib/api/compliance";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  const INCIDENT_TYPE_OPTIONS = [
    { value: "unauthorised_access", label: "Unauthorised access" },
    { value: "data_breach", label: "Data breach" },
    { value: "device_loss", label: "Device loss" },
    { value: "credential_compromise", label: "Credential compromise" },
    { value: "service_outage", label: "Service outage" },
    { value: "operator_issue", label: "Operator issue" },
    { value: "other", label: "Other" },
  ];

  const STATUS_OPTIONS = [
    { value: "open", label: "Open" },
    { value: "contained", label: "Contained" },
    { value: "investigating", label: "Investigating" },
    { value: "notified", label: "Notified" },
    { value: "closed", label: "Closed" },
  ];

  const SEVERITY_OPTIONS = [
    { value: "low", label: "Low" },
    { value: "medium", label: "Medium" },
    { value: "high", label: "High" },
    { value: "critical", label: "Critical" },
  ];

  const SORT_OPTIONS = [
    { value: "updated_desc", label: "Recently updated" },
    { value: "detected_desc", label: "Detected time" },
    { value: "severity_desc", label: "Severity" },
  ];

  let incidents = [];
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
  let severityFilter = "all";
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
    void loadIncidents();
  });

  onDestroy(() => {
    clearPreview();
  });

  function createEmptyForm() {
    return {
      incident_type: "unauthorised_access",
      status: "open",
      severity: "medium",
      reported_by: "",
      systems_affected: "",
      information_affected: "",
      summary: "",
      containment_action: "",
      impact_assessment: "",
      owner: "",
      information_officer_notified: false,
      regulator_notification_required: false,
      data_subject_notification_required: false,
      regulator_notified_at: "",
      data_subjects_notified_at: "",
      detected_at: "",
      closed_at: "",
      lessons_learned: "",
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

  function loadFormFromIncident(item) {
    return {
      incident_type: item.incident_type ?? "unauthorised_access",
      status: item.status ?? "open",
      severity: item.severity ?? "medium",
      reported_by: item.reported_by ?? "",
      systems_affected: item.systems_affected ?? "",
      information_affected: item.information_affected ?? "",
      summary: item.summary ?? "",
      containment_action: item.containment_action ?? "",
      impact_assessment: item.impact_assessment ?? "",
      owner: item.owner ?? "",
      information_officer_notified: Boolean(item.information_officer_notified),
      regulator_notification_required: Boolean(item.regulator_notification_required),
      data_subject_notification_required: Boolean(item.data_subject_notification_required),
      regulator_notified_at: toInputDateTime(item.regulator_notified_at),
      data_subjects_notified_at: toInputDateTime(item.data_subjects_notified_at),
      detected_at: toInputDateTime(item.detected_at),
      closed_at: toInputDateTime(item.closed_at),
      lessons_learned: item.lessons_learned ?? "",
      notes: item.notes ?? "",
    };
  }

  function normalizePayload(source) {
    return {
      incident_type: source.incident_type,
      status: source.status,
      severity: source.severity,
      reported_by: source.reported_by.trim() || null,
      systems_affected: source.systems_affected.trim() || null,
      information_affected: source.information_affected.trim() || null,
      summary: source.summary.trim(),
      containment_action: source.containment_action.trim() || null,
      impact_assessment: source.impact_assessment.trim() || null,
      owner: source.owner.trim() || null,
      information_officer_notified: Boolean(source.information_officer_notified),
      regulator_notification_required: Boolean(source.regulator_notification_required),
      data_subject_notification_required: Boolean(source.data_subject_notification_required),
      regulator_notified_at: fromInputDateTime(source.regulator_notified_at),
      data_subjects_notified_at: fromInputDateTime(source.data_subjects_notified_at),
      detected_at: fromInputDateTime(source.detected_at),
      closed_at: fromInputDateTime(source.closed_at),
      lessons_learned: source.lessons_learned.trim() || null,
      notes: source.notes.trim() || null,
    };
  }

  function validateForm() {
    if (!form.summary.trim()) return "An incident summary is required.";
    return "";
  }

  async function loadIncidents() {
    loading = true;
    errorMessage = "";
    statusMessage = null;
    try {
      const response = await fetchSecurityIncidents({
        search: searchTerm,
        status: statusFilter,
        severity: severityFilter,
        incidentType: typeFilter,
        page: meta.page ?? 1,
        limit: meta.per_page ?? 20,
      });
      incidents = response?.data?.items ?? [];
      summary = response?.summary ?? summary;
      meta = response?.meta ?? meta;

      if (selectedId && !incidents.some((item) => item.id === selectedId)) {
        selectedId = null;
        selected = null;
        form = createEmptyForm();
        clearAttachmentDraft();
      }
    } catch (error) {
      console.error("Failed to load security incidents", error);
      errorMessage = "Unable to load security incidents.";
    } finally {
      loading = false;
    }
  }

  async function loadIncidentDetail(incidentId) {
    detailLoading = true;
    try {
      const detail = await fetchSecurityIncidentDetail(incidentId);
      selected = detail;
      selectedId = detail.id;
      form = loadFormFromIncident(detail);
      clearAttachmentDraft();
      if (previewAttachmentId && !detail.attachments?.some((attachment) => attachment.id === previewAttachmentId)) {
        clearPreview();
      }
    } catch (error) {
      console.error("Failed to load incident detail", error);
      statusMessage = { type: "error", text: "Unable to load the full incident profile right now." };
    } finally {
      detailLoading = false;
    }
  }

  function openIncident(item) {
    selectedId = item.id;
    selected = item;
    statusMessage = null;
    void loadIncidentDetail(item.id);
  }

  function startNewIncident() {
    selectedId = null;
    selected = null;
    form = createEmptyForm();
    statusMessage = null;
    clearAttachmentDraft();
    clearPreview();
  }

  function severityWeight(value) {
    return { critical: 4, high: 3, medium: 2, low: 1 }[value] ?? 0;
  }

  function incidentNeedsNotification(item) {
    return Boolean(item?.regulator_notification_required) || Boolean(item?.data_subject_notification_required);
  }

  function incidentAlertLabel(item) {
    if (item?.severity === "critical") return "Critical";
    if (incidentNeedsNotification(item)) return "Notify";
    return "Standard";
  }

  function incidentAlertClass(item) {
    if (item?.severity === "critical") {
      return "border-red-300 bg-red-100 text-red-700 dark:border-red-400/30 dark:bg-red-500/10 dark:text-red-200";
    }
    if (incidentNeedsNotification(item)) {
      return "border-amber-300 bg-amber-100 text-amber-700 dark:border-amber-400/30 dark:bg-amber-500/10 dark:text-amber-200";
    }
    return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
  }

  function incidentRowClass(item) {
    const classes = [];
    if (selectedId === item.id) classes.push("omni-row-active");
    if (item?.severity === "critical") classes.push("omni-row-critical");
    else if (incidentNeedsNotification(item)) classes.push("omni-row-attention");
    return classes.join(" ");
  }

  function sortedIncidents() {
    const rows = [...incidents];
    if (sortMode === "detected_desc") {
      rows.sort((left, right) => {
        const leftValue = left.detected_at ? new Date(left.detected_at).getTime() : 0;
        const rightValue = right.detected_at ? new Date(right.detected_at).getTime() : 0;
        return rightValue - leftValue;
      });
      return rows;
    }
    if (sortMode === "severity_desc") {
      rows.sort((left, right) => severityWeight(right.severity) - severityWeight(left.severity));
      return rows;
    }
    rows.sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime());
    return rows;
  }

  async function exportCsv() {
    try {
      await exportSecurityIncidentsCsv({
        search: searchTerm,
        status: statusFilter,
        severity: severityFilter,
        incident_type: typeFilter,
      });
    } catch (error) {
      console.error("Failed to export incident register", error);
      statusMessage = { type: "error", text: "Unable to export the incident register right now." };
    }
  }

  async function saveIncident() {
    const validationMessage = validateForm();
    if (validationMessage) {
      statusMessage = { type: "error", text: validationMessage };
      return;
    }

    const isEditing = Boolean(selectedId);
    const confirmed = await confirmSave({
      title: isEditing ? "Save incident changes" : "Log security incident",
      message: isEditing ? "Save these security incident changes?" : "Log this security incident?",
    });
    if (!confirmed) return;

    saving = true;
    statusMessage = null;
    try {
      const payload = normalizePayload(form);
      let persisted;
      if (isEditing) {
        persisted = await updateSecurityIncident(selectedId, payload);
      } else {
        persisted = await createSecurityIncident(payload);
      }
      await loadIncidents();
      if (persisted?.id) {
        await loadIncidentDetail(persisted.id);
      }
      toastStore.push({
        title: isEditing ? "Incident updated" : "Incident logged",
        message: isEditing
          ? `${persisted.reference_no} is now ${persisted.status}.`
          : `${persisted.reference_no} has been added to the incident register.`,
        tone: "success",
      });
      statusMessage = {
        type: "success",
        text: isEditing ? "Security incident updated." : "Security incident logged.",
      };
    } catch (error) {
      console.error("Failed to save security incident", error);
      statusMessage = { type: "error", text: "Unable to save this incident right now." };
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function uploadAttachment() {
    if (!selectedId) {
      statusMessage = { type: "error", text: "Open an incident before adding evidence." };
      return;
    }
    if (!attachmentFile) {
      statusMessage = { type: "error", text: "Choose a file to upload first." };
      return;
    }

    uploadSaving = true;
    statusMessage = null;
    try {
      await uploadSecurityIncidentAttachment(selectedId, {
        file: attachmentFile,
        title: attachmentTitle,
        description: attachmentDescription,
      });
      await loadIncidentDetail(selectedId);
      await loadIncidents();
      clearAttachmentDraft();
      toastStore.push({
        title: "Evidence uploaded",
        message: "The attachment is now part of the incident record.",
        tone: "success",
      });
    } catch (error) {
      console.error("Failed to upload incident evidence", error);
      statusMessage = { type: "error", text: "Unable to upload this evidence file right now." };
    } finally {
      uploadSaving = false;
    }
  }

  async function removeAttachment(attachment) {
    const confirmed = await confirmSave({
      title: "Remove evidence file",
      message: `Remove ${attachment.original_filename} from this incident?`,
      confirmLabel: "Remove",
      tone: "destructive",
    });
    if (!confirmed) return;

    try {
      await deleteComplianceAttachment(attachment.id);
      await loadIncidentDetail(selectedId);
      await loadIncidents();
      if (attachment.id === previewAttachmentId) {
        clearPreview();
      }
      toastStore.push({ title: "Evidence removed", message: attachment.original_filename, tone: "success" });
    } catch (error) {
      console.error("Failed to remove incident evidence", error);
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
      await exportSecurityIncidentPdf(selectedId);
    } catch (error) {
      console.error("Failed to export incident PDF", error);
      statusMessage = { type: "error", text: "Unable to export the incident PDF right now." };
    }
  }

  async function exportSelectedPack() {
    if (!selectedId) return;
    try {
      await exportSecurityIncidentPack(selectedId);
    } catch (error) {
      console.error("Failed to export incident pack", error);
      statusMessage = { type: "error", text: "Unable to export the incident evidence pack right now." };
    }
  }

  function changePage(direction) {
    const nextPage = (meta.page ?? 1) + direction;
    const maxPage = Math.max(1, Math.ceil((meta.total ?? 0) / (meta.per_page ?? 20)));
    meta = { ...meta, page: Math.max(1, Math.min(maxPage, nextPage)) };
    void loadIncidents();
  }
</script>

<div class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Governance</p>
      <h2 class="omni-page-title">Security Incidents</h2>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="outline" size="sm" onclick={startNewIncident}>New incident</Button>
      <Button variant="outline" size="sm" onclick={exportCsv} disabled={incidents.length === 0}>Export CSV</Button>
      <Button variant="outline" size="sm" onclick={loadIncidents} disabled={loading}>
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
            placeholder="Search reference, summary, or owner"
            bind:value={searchTerm}
            on:change={loadIncidents}
          />
          <select class="omni-select min-w-[12rem]" bind:value={statusFilter} on:change={loadIncidents}>
            <option value="all">All statuses</option>
            {#each STATUS_OPTIONS as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
          <select class="omni-select min-w-[12rem]" bind:value={severityFilter} on:change={loadIncidents}>
            <option value="all">All severities</option>
            {#each SEVERITY_OPTIONS as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
          <select class="omni-select min-w-[12rem]" bind:value={typeFilter} on:change={loadIncidents}>
            <option value="all">All incident types</option>
            {#each INCIDENT_TYPE_OPTIONS as option}
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
            <span>Loading security incidents…</span>
          </div>
        {:else}
          <div class="mt-4 omni-table-shell">
            <table class="omni-table text-sm">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Owner</th>
                  <th>Evidence</th>
                  <th class="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {#if sortedIncidents().length === 0}
                  <tr>
                    <td colspan="7" class="py-8 text-center text-muted-foreground">No security incidents match this filter.</td>
                  </tr>
                {:else}
                  {#each sortedIncidents() as item}
                    <tr class={incidentRowClass(item)}>
                      <td class="font-medium text-slate-900 dark:text-white">{item.reference_no}</td>
                      <td>{item.incident_type.replaceAll("_", " ")}</td>
                      <td>{item.severity}</td>
                      <td>
                        <div class="flex flex-col gap-1">
                          <span>{item.status}</span>
                          <span class={`inline-flex w-fit rounded-full border px-2 py-0.5 text-[11px] font-medium ${incidentAlertClass(item)}`}>
                            {incidentAlertLabel(item)}
                          </span>
                        </div>
                      </td>
                      <td>{item.owner || "—"}</td>
                      <td>{item.attachment_count ?? 0}</td>
                      <td class="text-right">
                        <Button variant="outline" size="sm" onclick={() => openIncident(item)}>Open</Button>
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
                {selected ? "Incident profile" : "New incident"}
              </p>
              <h3 class="mt-2 text-2xl font-semibold">
                {selected ? selected.reference_no : "Log security incident"}
              </h3>
              <p class="text-sm text-muted-foreground">
                {selected
                  ? `${selected.incident_type.replaceAll("_", " ")} · ${selected.severity} severity`
                  : "Capture compromises, outages, breaches, and notification decisions in one governed register."}
              </p>
              {#if selected}
                <div class="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <span class={`inline-flex rounded-full border px-2.5 py-1 font-medium ${incidentAlertClass(selected)}`}>
                    {incidentAlertLabel(selected)}
                  </span>
                  <span class="rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
                    Updated {formatDateTime(selected.updated_at)}
                  </span>
                </div>
              {/if}
            </div>
            <div class="flex items-center gap-2">
              {#if selected}
                <Button variant="outline" size="sm" onclick={exportSelectedPdf}>PDF</Button>
                <Button variant="outline" size="sm" onclick={exportSelectedPack}>Pack</Button>
              {/if}
              <Button variant="outline" size="sm" onclick={startNewIncident}>Reset</Button>
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
              <span>Loading incident profile…</span>
            </div>
          {/if}

          <div class="omni-detail-section">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="omni-field">
                <label for="incident-type">Incident type</label>
                <select id="incident-type" class="omni-select" bind:value={form.incident_type}>
                  {#each INCIDENT_TYPE_OPTIONS as option}
                    <option value={option.value}>{option.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="incident-status">Status</label>
                <select id="incident-status" class="omni-select" bind:value={form.status}>
                  {#each STATUS_OPTIONS as option}
                    <option value={option.value}>{option.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="incident-severity">Severity</label>
                <select id="incident-severity" class="omni-select" bind:value={form.severity}>
                  {#each SEVERITY_OPTIONS as option}
                    <option value={option.value}>{option.label}</option>
                  {/each}
                </select>
              </div>
              <div class="omni-field">
                <label for="incident-owner">Owner</label>
                <input id="incident-owner" class="omni-input" bind:value={form.owner} placeholder="Incident owner" />
              </div>
              <div class="omni-field">
                <label for="incident-reported-by">Reported by</label>
                <input id="incident-reported-by" class="omni-input" bind:value={form.reported_by} placeholder="Reporter or source" />
              </div>
              <div class="omni-field">
                <label for="incident-detected-at">Detected at</label>
                <input id="incident-detected-at" class="omni-input" type="datetime-local" bind:value={form.detected_at} />
              </div>
            </div>

            <div class="mt-4 grid gap-4">
              <div class="omni-field">
                <label for="incident-summary">Summary</label>
                <textarea id="incident-summary" class="omni-textarea" bind:value={form.summary} placeholder="Describe what happened and the initial impact."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-systems-affected">Systems affected</label>
                <textarea id="incident-systems-affected" class="omni-textarea" bind:value={form.systems_affected} placeholder="Apps, services, devices, or environments."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-information-affected">Information affected</label>
                <textarea id="incident-information-affected" class="omni-textarea" bind:value={form.information_affected} placeholder="Personal information types, categories, or records impacted."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-containment-action">Containment action</label>
                <textarea id="incident-containment-action" class="omni-textarea" bind:value={form.containment_action} placeholder="Immediate containment or mitigation steps."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-impact-assessment">Impact assessment</label>
                <textarea id="incident-impact-assessment" class="omni-textarea" bind:value={form.impact_assessment} placeholder="Operational, legal, and data subject impact."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-lessons-learned">Lessons learned</label>
                <textarea id="incident-lessons-learned" class="omni-textarea" bind:value={form.lessons_learned} placeholder="Root cause follow-up and corrective actions."></textarea>
              </div>
              <div class="omni-field">
                <label for="incident-notes">Notes</label>
                <textarea id="incident-notes" class="omni-textarea" bind:value={form.notes} placeholder="Additional regulator, operator, or internal notes."></textarea>
              </div>
            </div>

            <div class="mt-4 grid gap-4 md:grid-cols-2">
              <div class="omni-field">
                <label for="incident-regulator-notified-at">Regulator notified at</label>
                <input id="incident-regulator-notified-at" class="omni-input" type="datetime-local" bind:value={form.regulator_notified_at} />
              </div>
              <div class="omni-field">
                <label for="incident-data-subjects-notified-at">Data subjects notified at</label>
                <input id="incident-data-subjects-notified-at" class="omni-input" type="datetime-local" bind:value={form.data_subjects_notified_at} />
              </div>
              <div class="omni-field">
                <label for="incident-closed-at">Closed at</label>
                <input id="incident-closed-at" class="omni-input" type="datetime-local" bind:value={form.closed_at} />
              </div>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-3">
              <label class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                <input type="checkbox" class="h-4 w-4 rounded border-border" bind:checked={form.information_officer_notified} />
                Information Officer notified
              </label>
              <label class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                <input type="checkbox" class="h-4 w-4 rounded border-border" bind:checked={form.regulator_notification_required} />
                Regulator notification required
              </label>
              <label class="flex items-center gap-3 text-sm text-slate-700 dark:text-slate-200">
                <input type="checkbox" class="h-4 w-4 rounded border-border" bind:checked={form.data_subject_notification_required} />
                Data subject notification required
              </label>
            </div>
          </div>

          {#if selected}
            <div class="omni-detail-section">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Evidence attachments</p>
                  <p class="mt-2 text-sm text-muted-foreground">Attach incident reports, screenshots, legal notices, or investigation artefacts.</p>
                </div>
                <span class="omni-inline-stat">{selected.attachments?.length ?? 0} files</span>
              </div>

              <div class="mt-4 grid gap-4 md:grid-cols-[1.2fr,1fr,auto]">
                <div class="omni-field">
                  <label for="incident-attachment-file">Evidence file</label>
                  <input
                    id="incident-attachment-file"
                    class="omni-input"
                    type="file"
                    on:change={(event) => {
                      attachmentFile = event.currentTarget.files?.[0] ?? null;
                    }}
                  />
                </div>
                <div class="omni-field">
                  <label for="incident-attachment-title">Title</label>
                  <input id="incident-attachment-title" class="omni-input" bind:value={attachmentTitle} placeholder="Incident report, notice…" />
                </div>
                <div class="omni-field">
                  <label for="incident-attachment-description">Description</label>
                  <input id="incident-attachment-description" class="omni-input" bind:value={attachmentDescription} placeholder="Optional note" />
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
            <Button size="sm" onclick={saveIncident} disabled={saving}>
              {saving ? "Saving…" : selected ? "Save changes" : "Log incident"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
