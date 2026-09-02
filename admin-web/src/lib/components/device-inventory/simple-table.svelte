<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { HARDWARE_STATUS_META } from "$lib/api/devices";
  import { confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import DeviceStatusCell from "./device-status-cell.svelte";
  import type { Device } from "./columns";

  export let devices: Device[] = [];
  export let isLoading = false;
  export let selectedDeviceIds: string[] = [];
  export let editingDeviceId: string | null = null;
  export let pendingDeleteId: string | null = null;
  export let savingDeviceId: string | null = null;
  export let deletingDeviceId: string | null = null;
  export let currentPage = 1;
  export let totalPages = 1;
  export let totalItems = 0;
  export let perPage = 25;
  export let enableSelection = true;
  export let allowInventoryActions = true;
  export let editDraft: {
    imei: string;
    status: string;
    firmwareVersion: string;
    hardwareType: string;
    model: string;
    manufacturer: string;
    serialNumber: string;
    purchaseDate: string;
    notes: string;
  } = {
    imei: "",
    status: "in_stock",
    firmwareVersion: "",
    hardwareType: "",
    model: "",
    manufacturer: "",
    serialNumber: "",
    purchaseDate: "",
    notes: "",
  };

  let pageNumbers: number[] = [];
  let rangeStart = 0;
  let rangeEnd = 0;
  let effectiveTotalPages = 1;
  let selectAllCheckbox: HTMLInputElement | null = null;

  $: effectiveTotalPages = Math.max(1, Number(totalPages || 1));
  $: pageNumbers = Array.from({ length: effectiveTotalPages }, (_, idx) => idx + 1);
  $: visibleSelectedCount = devices.filter((device) => selectedDeviceIds.includes(device.id)).length;
  $: allVisibleSelected = devices.length > 0 && visibleSelectedCount === devices.length;
  $: someVisibleSelected = visibleSelectedCount > 0 && !allVisibleSelected;
  $: rangeStart = totalItems === 0 ? 0 : (currentPage - 1) * perPage + 1;
  $: rangeEnd = Math.min(currentPage * perPage, totalItems);
  $: if (selectAllCheckbox) {
    selectAllCheckbox.indeterminate = someVisibleSelected;
  }

  const dispatch = createEventDispatcher<{
    cancelEdit: Record<string, never>;
    editDraftChange: {
      field:
        | "imei"
        | "status"
        | "firmwareVersion"
        | "hardwareType"
        | "model"
        | "manufacturer"
        | "serialNumber"
        | "purchaseDate"
        | "notes";
      value: string;
    };
    saveEdit: { deviceId: string };
    cancelDelete: Record<string, never>;
    confirmDelete: { deviceId: string };
    toggleSelect: { deviceId: string; selected: boolean };
    toggleSelectAll: { deviceIds: string[]; selected: boolean };
    changePage: { page: number };
    inspectDevice: { deviceId: string };
  }>();

  function formatHardware(device: Device): string {
    const parts = [device.model, device.hardwareType].filter(Boolean);
    return parts.join(" • ") || "Unknown";
  }

  function formatManufacturer(device: Device): string | null {
    return device.manufacturer ?? null;
  }

  function formatFirmware(device: Device): string {
    return device.firmwareVersion ?? "—";
  }

  function formatPurchaseDate(device: Device): string {
    if (!device.purchaseDate) {
      return "—";
    }
    const parsed = new Date(device.purchaseDate);
    if (Number.isNaN(parsed.getTime())) {
      return device.purchaseDate;
    }
    return parsed.toLocaleDateString();
  }

  function formatHub(device: Device): string {
    return device.assignment?.hubName ?? "—";
  }

  function formatAsset(device: Device): string {
    return device.assignment?.assetLabel ?? device.assignment?.assetRegistration ?? device.assignment?.target ?? "—";
  }

  function formatSim(device: Device): string {
    if (!device.sim) {
      return "—";
    }
    return [device.sim.iccid, device.sim.msisdn].filter(Boolean).join(" · ") || "Linked";
  }

  function formatLastActivity(device: Device): string {
    const value = device.assignment?.installedAt ?? device.assignment?.assignedAt ?? device.purchaseDate ?? null;
    if (!value) {
      return "—";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleString();
  }

  function cancelInlineEdit() {
    dispatch("cancelEdit", {});
  }

  function cancelInlineDelete() {
    dispatch("cancelDelete", {});
  }

  function confirmInlineDelete(device: Device) {
    dispatch("confirmDelete", { deviceId: device.id });
  }

  function updateDraft(
    field:
      | "imei"
      | "status"
      | "firmwareVersion"
      | "hardwareType"
      | "model"
      | "manufacturer"
      | "serialNumber"
      | "purchaseDate"
      | "notes",
    value: string,
  ) {
    dispatch("editDraftChange", { field, value });
  }

  async function saveInlineEdit(device: Device) {
    if (!(await confirmSave({ title: "Save device changes", message: "Save these device changes?" }))) {
      return;
    }
    dispatch("saveEdit", { deviceId: device.id });
    resetFocusAfterSave();
  }

  function handleRowSelect(device: Device, event: Event) {
    const target = event.target as HTMLInputElement;
    dispatch("toggleSelect", { deviceId: device.id, selected: target?.checked ?? false });
  }

  function inspectDevice(device: Device) {
    dispatch("inspectDevice", { deviceId: device.id });
  }

  function handleSelectAll(event: Event) {
    const target = event.target as HTMLInputElement;
    dispatch("toggleSelectAll", {
      deviceIds: devices.map((device) => device.id),
      selected: target?.checked ?? false,
    });
  }

  function goToPage(page: number) {
    if (page < 1 || page > effectiveTotalPages || page === currentPage) {
      return;
    }
    dispatch("changePage", { page });
  }

  function previousPage() {
    if (currentPage > 1) {
      dispatch("changePage", { page: currentPage - 1 });
    }
  }

  function nextPage() {
    if (currentPage < effectiveTotalPages) {
      dispatch("changePage", { page: currentPage + 1 });
    }
  }
</script>

<div class="omni-table-shell overflow-x-auto">
  <table class="omni-table">
    <thead>
      <tr>
        <th class="w-12">
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-border/70 text-primary"
            bind:this={selectAllCheckbox}
            checked={allVisibleSelected}
            on:change={handleSelectAll}
            aria-label="Select all visible devices"
            disabled={devices.length === 0 || !enableSelection}
          />
        </th>
        <th>IMEI / Serial</th>
        <th>Device</th>
        <th>Hub</th>
        <th>Asset</th>
        <th>SIM</th>
        <th>Status</th>
        <th>Date purchased</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#if isLoading}
        <tr>
          <td colspan="9" class="px-3 omni-table-loading">
            <div class="omni-loading-state">
              <span class="omni-loading-spinner" aria-hidden="true"></span>
              <span>Loading devices…</span>
            </div>
          </td>
        </tr>
      {:else if devices.length === 0}
        <tr>
          <td colspan="9" class="py-10 text-center text-muted-foreground">
            No devices match the current search and filters.
          </td>
        </tr>
      {:else}
        {#each devices as device (device.id)}
          <tr
            class={`border-t border-border/60 ${
              editingDeviceId === device.id || selectedDeviceIds.includes(device.id) ? "omni-row-active" : ""
            }`}
          >
            <td class="align-top">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-border/70 text-primary"
                checked={selectedDeviceIds.includes(device.id)}
                on:change={(event) => handleRowSelect(device, event)}
                aria-label={`Select device ${device.imei}`}
                disabled={!enableSelection}
              />
            </td>
            <td class="align-top">
              {#if editingDeviceId === device.id}
                <div class="space-y-1">
                  <input
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    type="text"
                    value={editDraft.imei}
                    on:input={(event) =>
                      updateDraft("imei", (event.target as HTMLInputElement).value)}
                    placeholder="IMEI"
                  />
                  <input
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    type="text"
                    value={editDraft.serialNumber}
                    on:input={(event) =>
                      updateDraft("serialNumber", (event.target as HTMLInputElement).value)}
                    placeholder="Serial number"
                  />
                </div>
              {:else}
                <div class="font-semibold tracking-tight">{device.imei}</div>
                {#if device.serialNumber}
                  <div class="text-xs text-muted-foreground">SN: {device.serialNumber}</div>
                {/if}
              {/if}
            </td>
            <td class="align-top">
              {#if editingDeviceId === device.id}
                <div class="space-y-1">
                  <input
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    type="text"
                    value={editDraft.hardwareType}
                    on:input={(event) =>
                      updateDraft("hardwareType", (event.target as HTMLInputElement).value)}
                    placeholder="Hardware type"
                  />
                  <input
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    type="text"
                    value={editDraft.model}
                    on:input={(event) => updateDraft("model", (event.target as HTMLInputElement).value)}
                    placeholder="Model"
                  />
                  <input
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    type="text"
                    value={editDraft.manufacturer}
                    on:input={(event) =>
                      updateDraft("manufacturer", (event.target as HTMLInputElement).value)}
                    placeholder="Manufacturer"
                  />
                </div>
              {:else}
                <button type="button" class="space-y-0.5 text-left" on:click={() => inspectDevice(device)}>
                  <div>{formatHardware(device)}</div>
                  {#if formatManufacturer(device)}
                    <div class="text-xs text-muted-foreground">{formatManufacturer(device)}</div>
                  {/if}
                </button>
              {/if}
            </td>
            <td class="align-top text-sm text-muted-foreground">
              {formatHub(device)}
            </td>
            <td class="align-top text-sm text-muted-foreground">
              {formatAsset(device)}
            </td>
            <td class="align-top text-sm text-muted-foreground">
              {formatSim(device)}
            </td>
            <td class="align-top">
              {#if editingDeviceId === device.id}
                <select
                  class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                  value={editDraft.status}
                  on:change={(event) =>
                    updateDraft("status", (event.target as HTMLSelectElement).value)}
                >
                  {#each HARDWARE_STATUS_META as statusMeta}
                    <option value={statusMeta.id}>{statusMeta.label}</option>
                  {/each}
                </select>
              {:else}
                <DeviceStatusCell status={device.status} />
              {/if}
            </td>
            <td class="align-top">
              {#if editingDeviceId === device.id}
                <div class="space-y-1">
                  <input
                    type="text"
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    value={editDraft.firmwareVersion}
                    on:input={(event) =>
                      updateDraft("firmwareVersion", (event.target as HTMLInputElement).value)}
                    placeholder="Firmware"
                  />
                  <input
                    type="date"
                    class="w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                    value={editDraft.purchaseDate}
                    on:input={(event) =>
                      updateDraft("purchaseDate", (event.target as HTMLInputElement).value)}
                  />
                </div>
              {:else}
                <div class="text-sm text-muted-foreground">{formatPurchaseDate(device)}</div>
              {/if}
            </td>
            <td class="align-top">
              {#if !allowInventoryActions && enableSelection}
                <span class="text-xs text-muted-foreground">Select row from toolbar</span>
              {:else if !allowInventoryActions}
                <span class="text-xs text-muted-foreground">Read-only</span>
              {:else if editingDeviceId === device.id}
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center rounded-md border border-primary bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground disabled:opacity-50"
                    on:click={() => saveInlineEdit(device)}
                    disabled={savingDeviceId === device.id}
                  >
                    {savingDeviceId === device.id ? "Saving…" : "Save"}
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center rounded-md border border-border/80 px-3 py-1 text-xs font-medium"
                    on:click={cancelInlineEdit}
                    disabled={savingDeviceId === device.id}
                  >
                    Cancel
                  </button>
                </div>
              {:else if pendingDeleteId === device.id}
                <div class="space-y-2">
                  <p class="text-xs text-muted-foreground">Remove this device?</p>
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="inline-flex items-center rounded-md border border-destructive bg-destructive px-3 py-1 text-xs font-semibold text-destructive-foreground disabled:opacity-50"
                      on:click={() => confirmInlineDelete(device)}
                      disabled={deletingDeviceId === device.id}
                    >
                      {deletingDeviceId === device.id ? "Deleting…" : "Confirm"}
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center rounded-md border border-border/80 px-3 py-1 text-xs font-medium"
                      on:click={cancelInlineDelete}
                      disabled={deletingDeviceId === device.id}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              {:else if selectedDeviceIds.includes(device.id)}
                <span class="text-xs text-muted-foreground">Use the toolbar or inspector actions</span>
              {:else}
                <button type="button" class="text-xs text-cyan-700 dark:text-cyan-300" on:click={() => inspectDevice(device)}>Inspect</button>
              {/if}
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>

  {#if devices.length > 0}
    <div class="flex flex-col gap-3 border-t border-border/60 p-4 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
      <div>
        Showing
        <span class="font-medium text-foreground">{rangeStart || 0}</span>
        –
        <span class="font-medium text-foreground">{rangeEnd || 0}</span>
        of
        <span class="font-medium text-foreground">{totalItems}</span>
        devices
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center rounded-md border border-border/70 px-3 py-1 text-xs font-medium disabled:opacity-50"
          on:click={previousPage}
          aria-label="Previous page"
          disabled={currentPage === 1}
        >
          Prev
        </button>

        {#each pageNumbers as page}
          <button
            type="button"
            class={`inline-flex items-center rounded-md border px-3 py-1 text-xs font-medium ${
              page === currentPage
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border/70 text-foreground hover:bg-muted"
            }`}
            on:click={() => goToPage(page)}
            aria-current={page === currentPage ? "page" : undefined}
          >
            {page}
          </button>
        {/each}

        <button
          type="button"
          class="inline-flex items-center rounded-md border border-border/70 px-3 py-1 text-xs font-medium disabled:opacity-50"
          on:click={nextPage}
          aria-label="Next page"
          disabled={currentPage === effectiveTotalPages}
        >
          Next
        </button>
      </div>
    </div>
  {/if}
</div>
