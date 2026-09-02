<script>
  import { onMount } from "svelte";
  import { Pencil, Link2, Trash2 } from "lucide-svelte";
  import { Button } from "$lib/components/ui/button";
  import { sessionStore } from "$lib/stores/session";
  import {
    assignSim,
    deleteSim,
    fetchDeviceInventory,
    fetchSimInventory,
    intakeSim,
    recallSim,
    updateSim,
  } from "$lib/api/devices";
  import { confirmAndRun, confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  const EMPTY_FORM = {
    iccid: "",
    msisdn: "",
    carrier: "Econet",
    imsi: "",
    roamingEnabled: false,
    roamingRegions: "",
    notes: "",
  };

  let session = null;
  let sims = [];
  let devices = [];
  let selectedSimId = null;
  let selectedSim = null;
  let loading = false;
  let saving = false;
  let search = "";
  let statusFilter = "all";
  let sortKey = "updatedAt";
  let sortDirection = "desc";
  let message = "";
  let messageTone = "info";
  let inspectorWindow = "";
  let intakeForm = { ...EMPTY_FORM };
  let editForm = { ...EMPTY_FORM, status: "in_stock" };
  let assignForm = {
    hardwareId: "",
    notes: "",
  };
  let recallForm = {
    status: "in_stock",
    reason: "",
    notes: "",
  };
  let deleteConfirmation = "";
  let bootstrappedForSession = "";

  $: roles = (session?.roles ?? []).map((role) => `${role}`.toLowerCase());
  $: isAdmin = roles.includes("admin");
  $: sessionBootstrapKey = `${session?.token ?? ""}:${roles.join(",")}`;
  $: availableHardware = devices.filter((device) => {
    if (device.sim) return false;
    return !["faulty", "retired", "maintenance"].includes(`${device.status ?? ""}`.toLowerCase());
  });
  $: selectedSim = sims.find((item) => item.id === selectedSimId) ?? null;
  $: if (!selectedSim && ["edit", "assign", "history", "delete"].includes(inspectorWindow)) {
    inspectorWindow = "";
  }
  $: if (selectedSim) {
    editForm = {
      iccid: selectedSim.iccid ?? "",
      msisdn: selectedSim.msisdn ?? "",
      carrier: selectedSim.carrier ?? "Econet",
      imsi: selectedSim.imsi ?? "",
      roamingEnabled: Boolean(selectedSim.roamingEnabled),
      roamingRegions: selectedSim.roamingRegions ?? "",
      notes: selectedSim.notes ?? "",
      status: selectedSim.status ?? "in_stock",
    };
  }

  function setMessage(text, tone = "info") {
    message = text;
    messageTone = tone;
  }

  function openIntakePage() {
    selectedSimId = null;
    deleteConfirmation = "";
    inspectorWindow = "intake";
  }

  function openEditPage(simId) {
    selectedSimId = simId;
    deleteConfirmation = "";
    inspectorWindow = "edit";
  }

  function openAssignPage(simId) {
    selectedSimId = simId;
    deleteConfirmation = "";
    assignForm = {
      hardwareId: "",
      notes: "",
    };
    inspectorWindow = "assign";
  }

  function openDeletePage(simId) {
    selectedSimId = simId;
    deleteConfirmation = "";
    inspectorWindow = "delete";
  }

  function backToRegister() {
    deleteConfirmation = "";
    inspectorWindow = "";
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  function simStatusClass(status) {
    switch ((status || "").toLowerCase()) {
      case "assigned":
        return "border-cyan-400/40 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300";
      case "faulty":
      case "retired":
        return "border-red-400/40 bg-red-500/10 text-red-700 dark:text-red-300";
      case "suspended":
        return "border-amber-400/40 bg-amber-500/10 text-amber-700 dark:text-amber-300";
      default:
        return "border-emerald-400/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    }
  }

  function simLabel(sim) {
    return `${sim.iccid}${sim.msisdn ? ` · ${sim.msisdn}` : ""}${sim.roamingEnabled ? " · Roaming" : ""}`;
  }

  function hardwareLabel(device) {
    return [
      device.imei,
      device.manufacturer,
      device.model,
      device.assignment?.assetRegistration ?? device.assignment?.assetLabel,
    ]
      .filter(Boolean)
      .join(" · ");
  }

  function sortIndicator(column) {
    if (sortKey !== column) return "";
    return sortDirection === "asc" ? "↑" : "↓";
  }

  function toggleSort(column) {
    if (sortKey === column) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
      return;
    }
    sortKey = column;
    sortDirection = column === "updatedAt" || column === "createdAt" ? "desc" : "asc";
  }

  function sortableValue(sim, column) {
    switch (column) {
      case "iccid":
        return sim.iccid ?? "";
      case "msisdn":
        return sim.msisdn ?? "";
      case "imsi":
        return sim.imsi ?? "";
      case "carrier":
        return sim.carrier ?? "";
      case "roamingEnabled":
        return sim.roamingEnabled ? 1 : 0;
      case "status":
        return sim.status ?? "";
      case "assignment":
        return sim.assignment?.hardwareImei ?? sim.assignment?.vehicleLabel ?? "";
      case "createdAt":
        return sim.createdAt ? new Date(sim.createdAt).getTime() : 0;
      case "updatedAt":
      default:
        return sim.updatedAt ? new Date(sim.updatedAt).getTime() : 0;
    }
  }

  $: sortedSims = [...sims].sort((left, right) => {
    const leftValue = sortableValue(left, sortKey);
    const rightValue = sortableValue(right, sortKey);
    const multiplier = sortDirection === "asc" ? 1 : -1;

    if (typeof leftValue === "number" && typeof rightValue === "number") {
      return (leftValue - rightValue) * multiplier;
    }

    return `${leftValue}`.localeCompare(`${rightValue}`) * multiplier;
  });

  function normalizeSimIdentity(value, field) {
    const trimmed = `${value ?? ""}`.trim();
    if (!trimmed) return "";
    if (field === "msisdn") {
      return trimmed.replace(/[\s().-]+/g, "");
    }
    return trimmed.replace(/\s+/g, "");
  }

  function findSimDuplicate(fields, excludeId = null) {
    const checks = [
      { field: "iccid", label: "ICCID", value: normalizeSimIdentity(fields.iccid, "iccid") },
      { field: "msisdn", label: "SIM number", value: normalizeSimIdentity(fields.msisdn, "msisdn") },
      { field: "imsi", label: "IMSI", value: normalizeSimIdentity(fields.imsi, "imsi") },
    ];

    for (const check of checks) {
      if (!check.value) continue;
      const existing = sims.find((sim) => {
        if (excludeId && sim.id === excludeId) return false;
        const candidate =
          check.field === "iccid"
            ? normalizeSimIdentity(sim.iccid, "iccid")
            : check.field === "msisdn"
              ? normalizeSimIdentity(sim.msisdn, "msisdn")
              : normalizeSimIdentity(sim.imsi, "imsi");
        return candidate && candidate === check.value;
      });
      if (existing) {
        return `${check.label} already exists on SIM ${existing.iccid}.`;
      }
    }

    return "";
  }

  function duplicateForField(fields, field, excludeId = null) {
    const value = normalizeSimIdentity(fields?.[field], field);
    if (!value) return "";

    const existing = sims.find((sim) => {
      if (excludeId && sim.id === excludeId) return false;
      const candidate =
        field === "iccid"
          ? normalizeSimIdentity(sim.iccid, "iccid")
          : field === "msisdn"
            ? normalizeSimIdentity(sim.msisdn, "msisdn")
            : normalizeSimIdentity(sim.imsi, "imsi");
      return candidate && candidate === value;
    });

    if (!existing) return "";

    const fieldLabel = field === "iccid" ? "ICCID" : field === "msisdn" ? "SIM number" : "IMSI";
    return `${fieldLabel} already belongs to SIM ${existing.iccid}.`;
  }

  $: intakeDuplicateWarnings = {
    iccid: duplicateForField(intakeForm, "iccid"),
    msisdn: duplicateForField(intakeForm, "msisdn"),
    imsi: duplicateForField(intakeForm, "imsi"),
  };

  $: editDuplicateWarnings = {
    msisdn: duplicateForField(editForm, "msisdn", selectedSim?.id ?? null),
    imsi: duplicateForField(editForm, "imsi", selectedSim?.id ?? null),
  };

  async function loadSims() {
    loading = true;
    try {
      const result = await fetchSimInventory({
        page: 1,
        limit: 200,
        search: search.trim() || undefined,
        status: statusFilter === "all" ? undefined : statusFilter,
      });
      sims = result?.items ?? [];
      if (selectedSimId && !sims.some((item) => item.id === selectedSimId)) {
        selectedSimId = null;
      }
    } catch (error) {
      console.error("Failed to load SIM inventory", error);
      setMessage("Unable to load SIM inventory.", "error");
      sims = [];
      selectedSimId = null;
    } finally {
      loading = false;
    }
  }

  async function loadDevices() {
    try {
      const result = await fetchDeviceInventory({ page: 1, limit: 200, simFilter: "without_sim" });
      devices = result?.items ?? [];
    } catch (error) {
      console.error("Failed to load tracker inventory", error);
      setMessage("Unable to load tracker inventory for SIM assignment.", "error");
      devices = [];
    }
  }

  async function refreshAll() {
    await Promise.all([loadSims(), loadDevices()]);
  }

  async function handleIntake() {
    if (!intakeForm.iccid.trim()) {
      setMessage("ICCID is required.", "error");
      return;
    }
    const duplicateMessage = findSimDuplicate(intakeForm);
    if (duplicateMessage) {
      setMessage(duplicateMessage, "error");
      return;
    }
    if (!(await confirmSave({ title: "Save SIM", message: "Save this managed SIM into inventory?" }))) {
      return;
    }
    saving = true;
    try {
      await intakeSim({
        iccid: intakeForm.iccid.trim(),
        msisdn: intakeForm.msisdn.trim() || undefined,
        carrier: intakeForm.carrier.trim() || "Econet",
        imsi: intakeForm.imsi.trim() || undefined,
        roamingEnabled: intakeForm.roamingEnabled,
        roamingRegions: intakeForm.roamingRegions.trim() || undefined,
        notes: intakeForm.notes.trim() || undefined,
      });
      toastStore.push({ title: "SIM saved", message: `${intakeForm.iccid.trim()} added to inventory.`, tone: "success" });
      intakeForm = { ...EMPTY_FORM };
      setMessage("SIM saved successfully.", "success");
      await refreshAll();
    } catch (error) {
      console.error("Failed to save SIM", error);
      setMessage(error?.response?.data?.detail ?? "Unable to save SIM inventory.", "error");
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function saveSelectedSim() {
    if (!selectedSim) return;
    const duplicateMessage = findSimDuplicate(editForm, selectedSim.id);
    if (duplicateMessage) {
      setMessage(duplicateMessage, "error");
      return;
    }
    if (!(await confirmSave({ title: "Save SIM details", message: "Save these SIM details?" }))) {
      return;
    }
    saving = true;
    try {
        const updated = await updateSim(selectedSim.id, {
          msisdn: editForm.msisdn.trim() || undefined,
          carrier: editForm.carrier.trim() || "Econet",
          imsi: editForm.imsi.trim() || undefined,
        roamingEnabled: editForm.roamingEnabled,
        roamingRegions: editForm.roamingRegions.trim() || undefined,
        status: editForm.status,
        notes: editForm.notes.trim() || undefined,
      });
      toastStore.push({ title: "SIM updated", message: `${updated.iccid} updated successfully.`, tone: "success" });
      setMessage("SIM details saved.", "success");
      await refreshAll();
      selectedSimId = updated.id;
    } catch (error) {
      console.error("Failed to update SIM", error);
      setMessage(error?.response?.data?.detail ?? "Unable to save SIM details.", "error");
    } finally {
      saving = false;
      resetFocusAfterSave();
    }
  }

  async function assignSelectedSim() {
    if (!selectedSim) return;
    if (!assignForm.hardwareId) {
      setMessage("Select a tracker before assigning the SIM.", "error");
      return;
    }
    await confirmAndRun(
      {
        title: "Assign SIM",
        description: "SIM management",
        message: "Assign this SIM to the selected tracker?",
        confirmLabel: "Assign SIM",
      },
      async () => {
        saving = true;
        try {
          await assignSim(selectedSim.id, {
            hardwareId: Number(assignForm.hardwareId),
            notes: assignForm.notes.trim() || undefined,
          });
          toastStore.push({ title: "SIM assigned", message: `${selectedSim.iccid} linked to the selected tracker.`, tone: "success" });
          setMessage("SIM assigned successfully.", "success");
          assignForm = { hardwareId: "", notes: "" };
          await refreshAll();
        } catch (error) {
          console.error("Failed to assign SIM", error);
          setMessage(error?.response?.data?.detail ?? "Unable to assign this SIM.", "error");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function recallSelectedSim() {
    if (!selectedSim) return;
    if (!recallForm.reason.trim()) {
      setMessage("A recall reason is required.", "error");
      return;
    }
    await confirmAndRun(
      {
        title: "Recall SIM",
        description: "SIM management",
        message: `Recall this SIM as ${recallForm.status.replaceAll("_", " ")}?`,
        confirmLabel: "Recall SIM",
        tone: recallForm.status === "in_stock" ? "default" : "destructive",
      },
      async () => {
        saving = true;
        try {
          await recallSim(selectedSim.id, {
            status: recallForm.status,
            reason: recallForm.reason.trim(),
            notes: recallForm.notes.trim() || undefined,
          });
          toastStore.push({ title: "SIM recalled", message: `${selectedSim.iccid} returned to inventory.`, tone: "success" });
          setMessage("SIM recalled successfully.", "success");
          recallForm = { status: "in_stock", reason: "", notes: "" };
          await refreshAll();
        } catch (error) {
          console.error("Failed to recall SIM", error);
          setMessage(error?.response?.data?.detail ?? "Unable to recall this SIM.", "error");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function deleteSelectedSim() {
    if (!selectedSim) return;
    if (selectedSim.assignment) {
      setMessage("Recall the active assignment before deleting this SIM record.", "error");
      return;
    }
    if (deleteConfirmation.trim() !== selectedSim.iccid) {
      setMessage("Type the full ICCID to confirm deletion.", "error");
      return;
    }

    if (
      !(await confirmSave({
        title: "Delete managed SIM",
        message: `Delete SIM ${selectedSim.iccid} from the registry? This removes its history from the active register.`,
      }))
    ) {
      return;
    }

    saving = true;
    try {
      await deleteSim(selectedSim.id);
      toastStore.push({ title: "SIM deleted", message: `${selectedSim.iccid} was removed from the register.`, tone: "success" });
      setMessage("SIM deleted successfully.", "success");
      selectedSimId = null;
      deleteConfirmation = "";
      inspectorWindow = "";
      await refreshAll();
    } catch (error) {
      console.error("Failed to delete SIM", error);
      setMessage(error?.response?.data?.detail ?? "Unable to delete this SIM.", "error");
    } finally {
      saving = false;
    }
  }

  onMount(() => {
    const unsubscribe = sessionStore.subscribe((value) => {
      session = value;
    });
    return () => unsubscribe();
  });

  $: if (session?.token && sessionBootstrapKey !== bootstrappedForSession) {
    bootstrappedForSession = sessionBootstrapKey;
    void refreshAll();
  }
</script>

<section class="space-y-6 marketing-reveal">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Registry</p>
      <h2 class="omni-page-title">SIMs</h2>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <Button size="sm" onclick={openIntakePage} disabled={!isAdmin}>Add managed SIM</Button>
      <Button variant="outline" size="sm" onclick={refreshAll} disabled={loading || saving}>Refresh</Button>
    </div>
  </header>

  {#if message}
    <div class={`rounded-xl border px-4 py-3 text-sm ${messageTone === "error" ? "border-red-300 bg-red-50 text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200" : "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"}`}>
      {message}
    </div>
  {/if}

  <section class="omni-panel px-5 py-4 border-0 shadow-none">
    <div class="omni-toolbar-strip">
      <label class="omni-toolbar-field flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Search SIMs</span>
        <input class="omni-input mt-1" bind:value={search} placeholder="ICCID, SIM number, carrier" />
      </label>
      <label class="omni-toolbar-field omni-toolbar-field-compact flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Status</span>
        <select class="omni-select mt-1" bind:value={statusFilter}>
          <option value="all">All statuses</option>
          <option value="in_stock">In stock</option>
          <option value="assigned">Assigned</option>
          <option value="suspended">Suspended</option>
          <option value="faulty">Faulty</option>
          <option value="retired">Retired</option>
        </select>
      </label>
      <div class="flex items-end gap-2">
        <Button size="sm" onclick={loadSims} disabled={loading}>Apply</Button>
      </div>
      <div class="ml-auto flex flex-wrap gap-2">
        <span class="omni-inline-stat">{sims.length} visible</span>
        <span class="omni-inline-stat">{sims.filter((sim) => sim.status === "assigned").length} assigned</span>
        <span class="omni-inline-stat">{sims.filter((sim) => sim.roamingEnabled).length} roaming</span>
      </div>
    </div>
  </section>

  {#if !inspectorWindow}
    <section class="omni-panel overflow-hidden p-0">
      <div class="border-b border-white/60 px-4 py-3 dark:border-white/10">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm font-medium text-slate-900 dark:text-white">SIM register</p>
          </div>
          <span class="omni-inline-stat">{sortedSims.length} visible</span>
        </div>
      </div>
      <table class="omni-table">
        <thead>
          <tr>
            <th><button type="button" class="text-left" onclick={() => toggleSort("iccid")}>ICCID {sortIndicator("iccid")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("msisdn")}>SIM number {sortIndicator("msisdn")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("imsi")}>IMSI {sortIndicator("imsi")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("carrier")}>Network {sortIndicator("carrier")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("roamingEnabled")}>Roaming {sortIndicator("roamingEnabled")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("status")}>Status {sortIndicator("status")}</button></th>
            <th><button type="button" class="text-left" onclick={() => toggleSort("updatedAt")}>Updated {sortIndicator("updatedAt")}</button></th>
            <th class="text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {#if loading}
            <tr>
              <td colspan="8" class="px-3 omni-table-loading">
                <div class="omni-loading-state">
                  <span class="omni-loading-spinner" aria-hidden="true"></span>
                  <span>Loading SIM inventory…</span>
                </div>
              </td>
            </tr>
          {:else if sortedSims.length === 0}
            <tr><td colspan="8" class="px-3 py-4 text-muted-foreground">No SIMs match the current filters.</td></tr>
          {:else}
            {#each sortedSims as sim (sim.id)}
              <tr class={selectedSimId === sim.id ? "omni-row-active" : ""}>
                <td>
                  <div class="font-medium">{sim.iccid}</div>
                </td>
                <td>
                  <div>{sim.msisdn ?? "—"}</div>
                </td>
                <td class="text-xs text-muted-foreground">
                  {sim.imsi ?? "—"}
                </td>
                <td>
                  <div>{sim.carrier ?? "Econet"}</div>
                </td>
                <td>
                  <span class={`inline-flex rounded-full border px-2 py-0.5 text-[11px] ${sim.roamingEnabled ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300" : "border-border/70 bg-background/80 text-muted-foreground"}`}>
                    {sim.roamingEnabled ? "Enabled" : "Local"}
                  </span>
                </td>
                <td>
                  <span class={`rounded-full border px-2 py-0.5 text-[11px] ${simStatusClass(sim.status)}`}>
                    {sim.status.replaceAll("_", " ")}
                  </span>
                </td>
                <td class="text-xs text-muted-foreground">{formatDateTime(sim.updatedAt ?? sim.createdAt)}</td>
                <td class="text-right">
                  <div class="inline-flex items-center justify-end gap-1 whitespace-nowrap">
                    <Button size="icon" variant="outline" onclick={() => openEditPage(sim.id)} aria-label={`Edit SIM ${sim.iccid}`}>
                      <Pencil class="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="outline" onclick={() => openAssignPage(sim.id)} aria-label={`Assign SIM ${sim.iccid}`}>
                      <Link2 class="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="destructive" onclick={() => openDeletePage(sim.id)} disabled={!isAdmin} aria-label={`Delete SIM ${sim.iccid}`}>
                      <Trash2 class="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </section>
  {/if}

      {#if inspectorWindow === "intake"}
      <section class="omni-panel p-5">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">Intake</p>
            <h4 class="mt-2 text-lg font-semibold">Add managed SIM</h4>
          </div>
          <Button size="sm" variant="outline" onclick={backToRegister}>Back</Button>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <label class="text-sm">
            ICCID *
            <input class="omni-input mt-1" bind:value={intakeForm.iccid} />
            {#if intakeDuplicateWarnings.iccid}
              <span class="mt-1 block text-xs text-red-600 dark:text-red-300">{intakeDuplicateWarnings.iccid}</span>
            {/if}
          </label>
          <label class="text-sm">
            SIM number
            <input class="omni-input mt-1" bind:value={intakeForm.msisdn} />
            {#if intakeDuplicateWarnings.msisdn}
              <span class="mt-1 block text-xs text-red-600 dark:text-red-300">{intakeDuplicateWarnings.msisdn}</span>
            {/if}
          </label>
          <label class="text-sm">Carrier<input class="omni-input mt-1" bind:value={intakeForm.carrier} /></label>
          <label class="text-sm">
            IMSI
            <input class="omni-input mt-1" bind:value={intakeForm.imsi} />
            {#if intakeDuplicateWarnings.imsi}
              <span class="mt-1 block text-xs text-red-600 dark:text-red-300">{intakeDuplicateWarnings.imsi}</span>
            {/if}
          </label>
          <label class="text-sm md:col-span-2">Roaming regions<input class="omni-input mt-1" bind:value={intakeForm.roamingRegions} placeholder="e.g. SADC, COMESA" /></label>
          <label class="text-sm md:col-span-2 flex items-center gap-2">
            <input type="checkbox" bind:checked={intakeForm.roamingEnabled} />
            Roaming enabled
          </label>
          <label class="text-sm md:col-span-2">Notes<textarea rows="2" class="omni-textarea mt-1" bind:value={intakeForm.notes}></textarea></label>
        </div>
        <div class="mt-4 flex justify-end">
          <Button size="sm" onclick={handleIntake} disabled={saving || !isAdmin}>Add SIM</Button>
        </div>
      </section>
      {/if}

      {#if selectedSim && inspectorWindow === "edit"}
        <section class="omni-panel p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">Edit SIM</p>
              <h4 class="mt-2 text-lg font-semibold">{selectedSim.iccid}</h4>
            </div>
            <div class="flex items-center gap-2">
              <span class={`rounded-full border px-3 py-1 text-xs ${simStatusClass(selectedSim.status)}`}>
                {selectedSim.status.replaceAll("_", " ")}
              </span>
              <Button size="sm" variant="outline" onclick={backToRegister}>Back</Button>
            </div>
          </div>

          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm">
              SIM number
              <input class="omni-input mt-1" bind:value={editForm.msisdn} />
              {#if editDuplicateWarnings.msisdn}
                <span class="mt-1 block text-xs text-red-600 dark:text-red-300">{editDuplicateWarnings.msisdn}</span>
              {/if}
            </label>
            <label class="text-sm">Carrier<input class="omni-input mt-1" bind:value={editForm.carrier} /></label>
            <label class="text-sm">
              IMSI
              <input class="omni-input mt-1" bind:value={editForm.imsi} />
              {#if editDuplicateWarnings.imsi}
                <span class="mt-1 block text-xs text-red-600 dark:text-red-300">{editDuplicateWarnings.imsi}</span>
              {/if}
            </label>
            <label class="text-sm">
              Status
              <select class="omni-select mt-1" bind:value={editForm.status}>
                <option value="in_stock">In stock</option>
                <option value="assigned">Assigned</option>
                <option value="suspended">Suspended</option>
                <option value="faulty">Faulty</option>
                <option value="retired">Retired</option>
              </select>
            </label>
            <label class="text-sm md:col-span-2">Roaming regions<input class="omni-input mt-1" bind:value={editForm.roamingRegions} /></label>
            <label class="text-sm md:col-span-2 flex items-center gap-2">
              <input type="checkbox" bind:checked={editForm.roamingEnabled} />
              Roaming enabled
            </label>
            <label class="text-sm md:col-span-2">Notes<textarea rows="2" class="omni-textarea mt-1" bind:value={editForm.notes}></textarea></label>
          </div>
          <div class="mt-4 flex justify-end">
            <Button size="sm" onclick={saveSelectedSim} disabled={saving || !isAdmin}>Save changes</Button>
          </div>
        </section>
      {/if}

      {#if selectedSim && inspectorWindow === "assign"}
        <section class="omni-panel p-5">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">Assign SIM</p>
              <h4 class="mt-2 text-lg font-semibold">
                {selectedSim.assignment ? "Current tracker link" : "Assign to tracker"}
              </h4>
            </div>
            <Button size="sm" variant="outline" onclick={backToRegister}>Back</Button>
          </div>

          {#if selectedSim.assignment}
            <div class="rounded-xl border border-border/70 bg-background/60 p-4 text-sm">
              <p><span class="font-medium">Tracker:</span> {selectedSim.assignment.hardwareImei ?? "—"}</p>
              <p><span class="font-medium">Asset:</span> {selectedSim.assignment.vehicleLabel ?? "—"}</p>
              <p><span class="font-medium">Hub:</span> {selectedSim.assignment.hubName ?? "—"}</p>
              <p><span class="font-medium">Assigned:</span> {formatDateTime(selectedSim.assignment.assignedAt)}</p>
              <p><span class="font-medium">Notes:</span> {selectedSim.assignment.notes ?? "—"}</p>
            </div>

            <div class="mt-4 grid gap-3 md:grid-cols-2">
              <label class="text-sm">
                Return status
                <select class="omni-select mt-1" bind:value={recallForm.status}>
                  <option value="in_stock">In stock</option>
                  <option value="assigned">Assigned (deployed)</option>
                  <option value="suspended">Suspended</option>
                  <option value="faulty">Faulty</option>
                  <option value="retired">Retired</option>
                </select>
              </label>
              <label class="text-sm md:col-span-2">Recall reason<textarea rows="2" class="omni-textarea mt-1" bind:value={recallForm.reason}></textarea></label>
              <label class="text-sm md:col-span-2">Notes<textarea rows="2" class="omni-textarea mt-1" bind:value={recallForm.notes}></textarea></label>
            </div>
            <div class="mt-4 flex justify-end">
              <Button variant="outline" size="sm" onclick={recallSelectedSim} disabled={saving || !isAdmin}>Recall SIM</Button>
            </div>
          {:else}
            <div class="grid gap-3">
              <div class="space-y-2">
                <div class="flex items-center justify-between gap-3">
                  <p class="text-sm font-medium text-foreground">Available trackers without SIM assignments</p>
                  <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
                    {availableHardware.length} available
                  </span>
                </div>
                {#if availableHardware.length}
                  <div class="omni-table-shell">
                    <table class="omni-table">
                      <thead>
                        <tr>
                          <th class="w-14">Select</th>
                          <th>IMEI</th>
                          <th>Model</th>
                          <th>Status</th>
                          <th>Asset</th>
                        </tr>
                      </thead>
                      <tbody>
                        {#each availableHardware as device (device.id)}
                          <tr class={assignForm.hardwareId === `${device.id}` ? "omni-row-active" : ""}>
                            <td>
                              <input
                                type="radio"
                                name="sim-hardware-selection"
                                value={device.id}
                                checked={assignForm.hardwareId === `${device.id}`}
                                onchange={() => (assignForm.hardwareId = `${device.id}`)}
                                aria-label={`Select tracker ${device.imei}`}
                              />
                            </td>
                            <td class="font-medium">{device.imei}</td>
                            <td>{[device.manufacturer, device.model].filter(Boolean).join(" ") || "—"}</td>
                            <td>
                              <span class="rounded-full border border-border/70 bg-background/80 px-2 py-0.5 text-[11px]">
                                {device.status?.replaceAll("_", " ") ?? "—"}
                              </span>
                            </td>
                            <td>{device.assignment?.assetRegistration ?? device.assignment?.assetLabel ?? "Warehouse / unassigned"}</td>
                          </tr>
                        {/each}
                      </tbody>
                    </table>
                  </div>
                {:else}
                  <div class="rounded-xl border border-border/70 bg-background/60 px-4 py-3 text-sm text-muted-foreground">
                    No trackers without SIM assignments are available right now.
                  </div>
                {/if}
              </div>
              <label class="text-sm">Assignment notes<textarea rows="2" class="omni-textarea mt-1" bind:value={assignForm.notes}></textarea></label>
            </div>
            <div class="mt-4 flex justify-end">
              <Button size="sm" onclick={assignSelectedSim} disabled={saving || !isAdmin}>Assign SIM</Button>
            </div>
          {/if}
        </section>
      {/if}

      {#if selectedSim && inspectorWindow === "delete"}
        <section class="omni-panel p-5">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-red-600 dark:text-red-300/80">Delete SIM</p>
              <h4 class="mt-2 text-lg font-semibold">{selectedSim.iccid}</h4>
              <p class="mt-2 text-sm text-muted-foreground">This is a destructive action. First review the current state, then type the ICCID to confirm deletion.</p>
            </div>
            <Button size="sm" variant="outline" onclick={backToRegister}>Back</Button>
          </div>

          <div class="grid gap-3 md:grid-cols-2">
            <div class="rounded-xl border border-border/70 bg-background/60 p-4 text-sm">
              <p><span class="font-medium">SIM number:</span> {selectedSim.msisdn ?? "—"}</p>
              <p><span class="font-medium">IMSI:</span> {selectedSim.imsi ?? "—"}</p>
              <p><span class="font-medium">Status:</span> {selectedSim.status.replaceAll("_", " ")}</p>
              <p><span class="font-medium">Assignment:</span> {selectedSim.assignment ? simLabel(selectedSim) : "In inventory"}</p>
            </div>
            <div class="rounded-xl border border-dashed border-red-300 bg-red-50/70 p-4 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
              <p class="font-semibold">Delete checklist</p>
              <ul class="mt-2 list-disc space-y-1 pl-5">
                <li>Make sure this SIM is not actively assigned.</li>
                <li>Confirm you are removing the correct managed SIM record.</li>
                <li>Type the full ICCID below to continue.</li>
              </ul>
            </div>
          </div>

          <label class="mt-4 block text-sm font-medium">
            Type <span class="font-semibold">{selectedSim.iccid}</span> to confirm
            <input class="omni-input mt-1" bind:value={deleteConfirmation} placeholder={selectedSim.iccid} />
          </label>

          <div class="mt-4 flex justify-end gap-2">
            <Button size="sm" variant="outline" onclick={backToRegister}>Cancel</Button>
            <Button size="sm" variant="destructive" onclick={deleteSelectedSim} disabled={saving || !isAdmin || deleteConfirmation.trim() !== selectedSim.iccid}>
              Delete SIM
            </Button>
          </div>
        </section>
      {/if}

      {#if selectedSim && inspectorWindow === "history"}
        <section class="omni-panel p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300/80">History</p>
              <h4 class="mt-2 text-lg font-semibold">SIM lifecycle</h4>
            </div>
            <div class="flex items-center gap-2">
              <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs">
                {selectedSim.assignmentHistory?.length ?? 0} event{selectedSim.assignmentHistory?.length === 1 ? "" : "s"}
              </span>
              <Button size="sm" variant="outline" onclick={backToRegister}>Back</Button>
            </div>
          </div>

          {#if selectedSim.assignmentHistory?.length}
            <div class="omni-table-shell">
              <table class="omni-table">
                <thead>
                  <tr>
                    <th>Assigned</th>
                    <th>Tracker</th>
                    <th>Target</th>
                    <th>Technician</th>
                    <th>Reason</th>
                    <th>Removed</th>
                  </tr>
                </thead>
                <tbody>
                  {#each selectedSim.assignmentHistory as history (history.id)}
                    <tr>
                      <td>{formatDateTime(history.assignedAt)}</td>
                      <td>
                        <div class="font-medium">{history.hardwareImei ?? "—"}</div>
                        <div class="text-xs text-muted-foreground">{history.isActive ? "Active" : "Closed"}</div>
                      </td>
                      <td>{history.vehicleLabel ?? history.hubName ?? history.target ?? "—"}</td>
                      <td>{history.technician ?? "—"}</td>
                      <td>{history.notes ?? "—"}</td>
                      <td>{history.unassignedAt ? formatDateTime(history.unassignedAt) : history.isActive ? "Active" : "—"}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else}
            <div class="omni-empty-state py-8">No assignment or recall events have been recorded for this SIM yet.</div>
          {/if}
        </section>
      {/if}
</section>
