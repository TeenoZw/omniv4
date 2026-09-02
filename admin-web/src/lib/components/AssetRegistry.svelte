<script>
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { decodeAssetVin, fetchHubs, fetchHubAssets, fetchHubAssetDetail, updateHubAsset } from "$lib/api/hubs";
  import { toastStore } from "$lib/stores/toast";
  import { confirmAndRun } from "$lib/utils/confirm-save";
  import { ArrowLeft } from "lucide-svelte";

  const ALL_HUBS_OPTION = "__all_assets__";
  let hubs = [];
  let selectedHubId = ALL_HUBS_OPTION;
  let selectedAssetId = null;
  let selectedAssetDetail = null;
  let assets = [];
  let hubsLoading = false;
  let assetsLoading = false;
  let detailLoading = false;
  let saving = false;
  let decodingVin = false;
  let vinDecodeFeedback = "";
  let statusMessage = "";
  let statusKind = "info";
  let assetSearch = "";
  let statusFilter = "all";
  let simFilter = "all";
  let page = 1;
  let perPage = 12;
  let total = 0;
  let editForm = createEditForm();
  let lastHubId = "";
  const assetTypeOptions = ["trailer", "truck", "bus", "sedan", "hatchback", "tractor", "excavator", "other"];

  function createEditForm() {
    return {
      assetType: "",
      assetTypeOther: "",
      assetName: "",
      registration: "",
      vin: "",
      make: "",
      model: "",
      year: "",
      color: "",
      engineCapacity: "",
      co2Emissions: "",
      fuelType: "",
      notes: "",
    };
  }

  function setStatus(kind, message) {
    statusKind = kind;
    statusMessage = message;
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  function simLabel(sim) {
    if (!sim) return "No SIM linked";
    return [sim.iccid, sim.msisdn, sim.carrier, sim.roamingEnabled ? "Roaming" : null].filter(Boolean).join(" · ");
  }

  function latestAssetActivity(detail) {
    if (!detail?.devices?.length) return [];
    return detail.devices
      .flatMap((device) =>
        (device.assignmentHistory ?? []).map((entry) => ({
          id: `${device.imei}-${entry.id ?? entry.assignedAt ?? Math.random()}`,
          imei: device.imei,
          when: entry.unassignedAt ?? entry.installedAt ?? entry.assignedAt ?? null,
          target: entry.assetRegistration ?? entry.assetLabel ?? entry.vehicleLabel ?? entry.hubName ?? entry.target ?? "Unknown target",
          technician: entry.technician ?? "—",
          note: entry.notes ?? "No notes recorded",
          status: entry.unassignedAt ? "Closed" : entry.isActive ? "Active" : "Recorded",
        })),
      )
      .sort((a, b) => new Date(b.when ?? 0).getTime() - new Date(a.when ?? 0).getTime())
      .slice(0, 6);
  }

  function exportAssetSnapshot() {
    if (!selectedAssetDetail) return;
    const payload = {
      exportedAt: new Date().toISOString(),
      asset: selectedAssetDetail,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${(selectedAssetDetail.assetName ?? selectedAssetDetail.registration ?? "asset").replace(/\s+/g, "-").toLowerCase()}-360.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function trackingBadgeClass(trackingState) {
    if (trackingState === "tracked") {
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-200";
    }
    if (trackingState === "assignment_only") {
      return "bg-slate-200 text-slate-700 dark:bg-white/10 dark:text-slate-200";
    }
    return "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200";
  }

  function trackingLabel(trackingState) {
    if (trackingState === "tracked") return "Tracked";
    if (trackingState === "assignment_only") return "Assignment only";
    return "Pending device";
  }

  function isVirtualAsset(assetId) {
    return `${assetId ?? ""}`.startsWith("virtual:");
  }

  function shouldShowVehicleFields(assetType) {
    return ["truck", "bus", "sedan", "hatchback", "tractor", "trailer"].includes((assetType || "").toLowerCase());
  }

  function hydrateEditForm(detail) {
    editForm = {
      assetType: detail?.assetType ?? "",
      assetTypeOther: detail?.assetTypeOther ?? "",
      assetName: detail?.assetName ?? "",
      registration: detail?.registration ?? "",
      vin: detail?.vin ?? "",
      make: detail?.make ?? "",
      model: detail?.model ?? "",
      year: detail?.year ?? "",
      color: detail?.color ?? "",
      engineCapacity: detail?.engineCapacity ?? "",
      co2Emissions: detail?.co2Emissions ?? "",
      fuelType: detail?.fuelType ?? "",
      notes: detail?.notes ?? "",
    };
    vinDecodeFeedback = "";
  }

  function currentAssetHubId(asset = null) {
    return asset?.hubId ?? selectedAssetDetail?.hubId ?? (selectedHubId === ALL_HUBS_OPTION ? "" : selectedHubId);
  }

  function applyVinDecodedData(decoded) {
    if (!decoded) return;
    editForm = {
      ...editForm,
      vin: decoded.normalized_vin || editForm.vin,
      make: decoded.make || editForm.make,
      model: decoded.model || editForm.model,
      year: decoded.year || editForm.year,
      fuelType: decoded.fuel_type || editForm.fuelType,
      engineCapacity: decoded.engine_capacity || editForm.engineCapacity,
      assetType:
        editForm.assetType && editForm.assetType !== "other"
          ? editForm.assetType
          : decoded.suggested_asset_type || editForm.assetType,
    };
  }

  async function loadHubs() {
    hubsLoading = true;
    try {
      hubs = await fetchHubs({ limit: 200 });
      if (!selectedHubId) {
        selectedHubId = ALL_HUBS_OPTION;
      } else if (selectedHubId !== ALL_HUBS_OPTION && !hubs.some((hub) => hub.id === selectedHubId) && hubs.length > 0) {
        selectedHubId = hubs[0].id;
      }
    } catch (error) {
      console.error("Failed to load hubs for asset registry", error);
      setStatus("error", "Unable to load hubs for the asset registry.");
    } finally {
      hubsLoading = false;
    }
  }

  async function loadAssets(force = false) {
    if (!selectedHubId) {
      assets = [];
      total = 0;
      selectedAssetId = null;
      selectedAssetDetail = null;
      hydrateEditForm(null);
      return;
    }
    if (!force && lastHubId === selectedHubId && page === 1 && !assetSearch.trim() && statusFilter === "all" && simFilter === "all") {
      return;
    }
    lastHubId = selectedHubId;
    assetsLoading = true;
    try {
      if (selectedHubId === ALL_HUBS_OPTION) {
        const filters = {
          page: 1,
          limit: 100,
          search: assetSearch.trim() || undefined,
          status: statusFilter === "all" ? undefined : statusFilter,
          simFilter: simFilter === "all" ? undefined : simFilter,
        };
        const responses = await Promise.all(
          hubs.map((hub) =>
            fetchHubAssets(hub.id, filters).then((response) => ({
              hub,
              items: response.items ?? [],
            })),
          ),
        );

        const combined = responses.flatMap(({ hub, items }) =>
          items.map((asset) => ({
            ...asset,
            hubId: hub.id,
            hubName: hub.name,
            hubCode: hub.code,
          })),
        );

        total = combined.length;
        const start = (page - 1) * perPage;
        assets = combined.slice(start, start + perPage);
      } else {
        const response = await fetchHubAssets(selectedHubId, {
          page,
          limit: perPage,
          search: assetSearch.trim() || undefined,
          status: statusFilter === "all" ? undefined : statusFilter,
          simFilter: simFilter === "all" ? undefined : simFilter,
        });
        assets = (response.items ?? []).map((asset) => ({
          ...asset,
          hubId: selectedHubId,
          hubName: selectedHub?.name ?? "",
          hubCode: selectedHub?.code ?? "",
        }));
        total = Number(response.meta?.total ?? assets.length);
      }
      if (selectedAssetId && assets.some((asset) => asset.id === selectedAssetId)) {
        await openAssetDetail(selectedAssetId);
      } else {
        selectedAssetId = null;
        selectedAssetDetail = null;
        hydrateEditForm(null);
      }
    } catch (error) {
      console.error("Failed to load assets", error);
      assets = [];
      total = 0;
      selectedAssetDetail = null;
      hydrateEditForm(null);
      setStatus("error", "Unable to load assets for the selected hub.");
    } finally {
      assetsLoading = false;
    }
  }

  async function openHubDetail(hubId) {
    if (!hubId || hubId === selectedHubId) return;
    selectedHubId = hubId;
    selectedAssetId = null;
    selectedAssetDetail = null;
    page = 1;
    lastHubId = "";
    await loadAssets(true);
  }

  async function openAssetDetail(assetId) {
    const sourceAsset = assets.find((asset) => asset.id === assetId);
    const hubId = sourceAsset?.hubId ?? currentAssetHubId(sourceAsset);
    if (!hubId || !assetId) return;
    selectedAssetId = assetId;
    detailLoading = true;
    try {
      selectedAssetDetail = await fetchHubAssetDetail(hubId, assetId);
      hydrateEditForm(selectedAssetDetail);
    } catch (error) {
      console.error("Failed to load asset detail", error);
      selectedAssetDetail = null;
      hydrateEditForm(null);
      setStatus("error", "Unable to load asset details.");
    } finally {
      detailLoading = false;
    }
  }

  function closeAssetDetail() {
    selectedAssetId = null;
    selectedAssetDetail = null;
    detailLoading = false;
    hydrateEditForm(null);
  }

  async function saveAsset() {
    const hubId = currentAssetHubId(selectedAssetDetail);
    if (!hubId || !selectedAssetDetail || isVirtualAsset(selectedAssetDetail.id)) return;
    await confirmAndRun(
      {
        title: "Save asset details",
        description: "Administrative asset maintenance",
        message: `Save updates for ${selectedAssetDetail.assetName ?? selectedAssetDetail.label ?? "this asset"}?`,
        confirmLabel: "Save asset",
      },
      async () => {
        saving = true;
        try {
          const updated = await updateHubAsset(hubId, selectedAssetDetail.id, {
            assetType: editForm.assetType,
            assetTypeOther: editForm.assetType === "other" ? editForm.assetTypeOther : "",
            assetName: editForm.assetName,
            registration: editForm.registration,
            vin: editForm.vin,
            make: editForm.make,
            model: editForm.model,
            year: editForm.year,
            color: editForm.color,
            engineCapacity: editForm.engineCapacity,
            co2Emissions: editForm.co2Emissions,
            fuelType: editForm.fuelType,
            notes: editForm.notes,
          });
          selectedAssetDetail = updated;
          hydrateEditForm(updated);
          await loadAssets(true);
          toastStore.push({
            title: "Asset updated",
            message: `${updated.assetName ?? updated.label ?? "Asset"} saved successfully.`,
            tone: "success",
          });
          setStatus("success", "Asset details saved.");
        } catch (error) {
          console.error("Failed to update asset", error);
          setStatus("error", error?.response?.data?.detail ?? "Unable to save asset details.");
        } finally {
          saving = false;
        }
      },
    );
  }

  async function runVinDecode() {
    if (!editForm.vin?.trim()) {
      setStatus("error", "Enter a VIN before requesting vehicle metadata.");
      return;
    }
    decodingVin = true;
    vinDecodeFeedback = "";
    try {
      const response = await decodeAssetVin(editForm.vin);
      applyVinDecodedData(response?.decoded);
      vinDecodeFeedback = response?.warnings?.[0] || (response?.success ? "VIN metadata loaded." : "VIN decode returned limited data.");
      if (response?.success) {
        toastStore.push({
          title: "VIN decoded",
          message: "Vehicle metadata was applied to this asset form.",
          tone: "success",
        });
      }
    } catch (error) {
      console.error("Failed to decode VIN", error);
      setStatus("error", error?.response?.data?.detail ?? error?.message ?? "Unable to decode this VIN.");
    } finally {
      decodingVin = false;
    }
  }

  function handleAssetSearchInput(event) {
    assetSearch = event.target.value;
    page = 1;
    void loadAssets(true);
  }

  function handleHubFilterChange(event) {
    selectedHubId = event.target.value;
    selectedAssetId = null;
    selectedAssetDetail = null;
    page = 1;
    lastHubId = "";
    void loadAssets(true);
  }

  function handleStatusChange(event) {
    statusFilter = event.target.value;
    page = 1;
    void loadAssets(true);
  }

  function handleSimFilterChange(event) {
    simFilter = event.target.value;
    page = 1;
    void loadAssets(true);
  }

  function nextPage() {
    const totalPages = Math.max(1, Math.ceil(total / perPage));
    if (page < totalPages) {
      page += 1;
      void loadAssets(true);
    }
  }

  function prevPage() {
    if (page > 1) {
      page -= 1;
      void loadAssets(true);
    }
  }

  $: selectedHub = hubs.find((hub) => hub.id === selectedHubId) ?? null;

  onMount(async () => {
    await loadHubs();
    await loadAssets(true);
  });
</script>

<section class="space-y-6 marketing-reveal">
  {#if statusMessage}
    <div class={`rounded-2xl border px-4 py-3 text-sm ${
      statusKind === "error"
        ? "border-red-300 bg-red-50 text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200"
        : "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
    }`}>
      {statusMessage}
    </div>
  {/if}

  <section class="space-y-5">
    <div class="omni-list-stage">
      <section class="omni-panel p-5">
        <div class="omni-toolbar-strip">
          <label class="omni-toolbar-field-compact omni-field">
            <span>Hub</span>
            <select class="omni-select" bind:value={selectedHubId} onchange={handleHubFilterChange}>
              <option value={ALL_HUBS_OPTION}>All Assets</option>
              {#each hubs as hub}
                <option value={hub.id}>{hub.name} · {hub.code}</option>
              {/each}
            </select>
          </label>
          <label class="omni-toolbar-field omni-field">
            <span>Search assets</span>
            <input
              class="omni-input"
              type="search"
              placeholder="Search by asset name, registration, VIN, make, or model"
              value={assetSearch}
              oninput={handleAssetSearchInput}
            />
          </label>
          <label class="omni-toolbar-field-compact omni-field">
            <span>Tracking</span>
            <select class="omni-select" bind:value={statusFilter} onchange={handleStatusChange}>
              <option value="all">All assets</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="assigned">Assigned</option>
            </select>
          </label>
          <label class="omni-toolbar-field-compact omni-field">
            <span>SIM state</span>
            <select class="omni-select" bind:value={simFilter} onchange={handleSimFilterChange}>
              <option value="all">All SIM states</option>
              <option value="with_sim">With SIM</option>
              <option value="without_sim">Without SIM</option>
              <option value="roaming">Roaming enabled</option>
              <option value="attention">Needs SIM attention</option>
            </select>
          </label>
          <div class="ml-auto flex flex-wrap gap-2">
            <span class="omni-inline-stat">{selectedHubId === ALL_HUBS_OPTION ? "All Assets" : selectedHub ? `${selectedHub.name}` : "No hub selected"}</span>
            <span class="omni-inline-stat">{total} assets</span>
          </div>
        </div>

        <div class="omni-table-shell mt-4">
          <table class="omni-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Hub</th>
                <th>Registration</th>
                <th>Tracking</th>
                <th>Devices</th>
                <th>Last assignment</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#if hubsLoading}
                <tr>
                  <td colspan="7" class="px-3 omni-table-loading">
                    <div class="omni-loading-state">
                      <span class="omni-loading-spinner" aria-hidden="true"></span>
                      <span>Loading hub options…</span>
                    </div>
                  </td>
                </tr>
              {:else if !selectedHubId}
                <tr><td colspan="7" class="px-3 py-6 text-muted-foreground">Select a hub filter to load the asset register.</td></tr>
              {:else if assetsLoading}
                <tr>
                  <td colspan="7" class="px-3 omni-table-loading">
                    <div class="omni-loading-state">
                      <span class="omni-loading-spinner" aria-hidden="true"></span>
                      <span>Loading assets…</span>
                    </div>
                  </td>
                </tr>
              {:else if assets.length === 0}
                <tr><td colspan="7" class="px-3 py-6 text-muted-foreground">No assets match the current hub and filters.</td></tr>
              {:else}
                {#each assets as asset (asset.id)}
                  <tr class={selectedAssetId === asset.id ? "omni-row-active" : ""}>
                    <td>
                      <p class="font-semibold text-foreground">{asset.assetName ?? asset.label ?? "Unlabelled asset"}</p>
                      <p class="text-xs capitalize text-muted-foreground">{asset.assetType ?? "asset"}</p>
                    </td>
                    <td>
                      <p class="font-medium text-foreground">{asset.hubName ?? selectedHub?.name ?? "—"}</p>
                      <p class="text-xs text-muted-foreground">{asset.hubCode ?? selectedHub?.code ?? ""}</p>
                    </td>
                    <td class="text-xs text-muted-foreground">{asset.registration ?? asset.vin ?? "—"}</td>
                    <td>
                      <span class={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${trackingBadgeClass(asset.trackingState)}`}>
                        {trackingLabel(asset.trackingState)}
                      </span>
                    </td>
                    <td>{asset.assignedDeviceCount}</td>
                    <td class="text-xs text-muted-foreground">{formatDateTime(asset.lastAssignmentAt)}</td>
                    <td class="text-right">
                      <Button size="sm" variant="outline" onclick={() => openAssetDetail(asset.id)}>
                        Open
                      </Button>
                    </td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>

        <div class="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <p>Showing {total === 0 ? 0 : (page - 1) * perPage + 1} - {Math.min(page * perPage, total)} of {total}</p>
          <div class="flex gap-2">
            <Button size="sm" variant="outline" onclick={prevPage} disabled={page <= 1 || assetsLoading}>Previous</Button>
            <Button size="sm" variant="outline" onclick={nextPage} disabled={page >= Math.max(1, Math.ceil(total / perPage)) || assetsLoading}>Next</Button>
          </div>
        </div>
      </section>
    </div>

    <div class="omni-inspector-stage">
      <section class="omni-panel p-5">
        {#if detailLoading}
          <div class="omni-loading-state">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading Asset 360…</span>
          </div>
        {:else if selectedAssetDetail}
          <div class="space-y-5 omni-animate-fade">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="omni-kicker">Asset 360</p>
                <h4 class="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">{selectedAssetDetail.assetName ?? selectedAssetDetail.label ?? "Unnamed asset"}</h4>
                <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  {(selectedAssetDetail.assetType ?? "asset").replaceAll("_", " ")}
                  {#if selectedAssetDetail.assetTypeOther}
                    · {selectedAssetDetail.assetTypeOther}
                  {/if}
                  {#if selectedAssetDetail.registration}
                    · {selectedAssetDetail.registration}
                  {/if}
                </p>
              </div>
              <div class="flex flex-wrap gap-2">
                <Button size="sm" variant="outline" onclick={exportAssetSnapshot}>Export Asset 360</Button>
                <Button size="sm" variant="outline" onclick={() => globalThis.print?.()}>Print view</Button>
                <span class={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${trackingBadgeClass(selectedAssetDetail.trackingState)}`}>
                  {trackingLabel(selectedAssetDetail.trackingState)}
                </span>
                {#if isVirtualAsset(selectedAssetDetail.id)}
                  <span class="inline-flex rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-white/10 dark:text-slate-200">Assignment only record</span>
                {/if}
              </div>
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
              <div class="omni-stat-card">
                <p class="text-xs uppercase tracking-[0.18em] text-muted-foreground">Registration</p>
                <p class="mt-2 font-semibold text-foreground">{selectedAssetDetail.registration ?? "Not recorded"}</p>
              </div>
              <div class="omni-stat-card">
                <p class="text-xs uppercase tracking-[0.18em] text-muted-foreground">Managed SIMs</p>
                <p class="mt-2 font-semibold text-foreground">{selectedAssetDetail.devices.filter((device) => device.sim).length}</p>
              </div>
            </div>

            <div class="omni-detail-section">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-semibold">Latest activity</p>
                  <p class="text-xs text-muted-foreground">Recent device and SIM changes recorded against this asset.</p>
                </div>
                <span class="text-xs text-muted-foreground">{latestAssetActivity(selectedAssetDetail).length} event{latestAssetActivity(selectedAssetDetail).length === 1 ? "" : "s"}</span>
              </div>
              {#if latestAssetActivity(selectedAssetDetail).length}
                <div class="mt-3 space-y-2">
                  {#each latestAssetActivity(selectedAssetDetail) as event (event.id)}
                    <div class="rounded-2xl border border-white/50 bg-white/70 px-3 py-3 text-xs text-muted-foreground dark:border-white/10 dark:bg-slate-950/45">
                      <div class="flex flex-wrap items-center justify-between gap-2">
                        <p class="font-medium text-foreground">{event.status} · {event.imei}</p>
                        <p>{formatDateTime(event.when)}</p>
                      </div>
                      <p class="mt-1">Target: <span class="font-medium text-foreground">{event.target}</span> · Technician: <span class="font-medium text-foreground">{event.technician}</span></p>
                      <p class="mt-1">{event.note}</p>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="mt-3 text-sm text-muted-foreground">No recent activity has been recorded for this asset yet.</p>
              {/if}
            </div>

            <div class="omni-detail-section">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p class="font-semibold text-foreground">Asset properties</p>
                  <p class="text-xs text-muted-foreground">Maintain the asset record without leaving the registry context.</p>
                </div>
                {#if isVirtualAsset(selectedAssetDetail.id)}
                  <span class="rounded-full border border-white/70 bg-white/70 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-600 dark:border-white/10 dark:bg-slate-950/45 dark:text-slate-300">View only</span>
                {/if}
              </div>

              <div class="omni-form-grid mt-4">
                <div class="omni-field">
                  <label for="registry-asset-type">Asset type</label>
                  <select id="registry-asset-type" class="omni-select" bind:value={editForm.assetType} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin}>
                    {#each assetTypeOptions as assetType}
                      <option value={assetType}>{assetType}</option>
                    {/each}
                  </select>
                </div>
                <div class="omni-field">
                  <label for="registry-asset-name">Asset name</label>
                  <input id="registry-asset-name" class="omni-input" bind:value={editForm.assetName} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                </div>
                {#if editForm.assetType === "other"}
                  <div class="omni-field">
                    <label for="registry-asset-type-other">Specify asset type</label>
                    <input id="registry-asset-type-other" class="omni-input" bind:value={editForm.assetTypeOther} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                {/if}
                <div class="omni-field">
                  <label for="registry-registration">Registration</label>
                  <input id="registry-registration" class="omni-input" bind:value={editForm.registration} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                </div>
                <div class="omni-field sm:col-span-2">
                  <label for="registry-vin">VIN</label>
                  <div class="flex gap-2">
                    <input id="registry-vin" class="omni-input min-w-0 flex-1" bind:value={editForm.vin} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                    <Button size="sm" variant="outline" onclick={runVinDecode} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin || !editForm.vin?.trim()}>
                      {decodingVin ? "Decoding..." : "Decode VIN"}
                    </Button>
                  </div>
                  {#if vinDecodeFeedback}
                    <p class="mt-1 text-xs text-muted-foreground">{vinDecodeFeedback}</p>
                  {/if}
                </div>
                <div class="omni-field">
                  <label for="registry-fuel-type">Fuel type</label>
                  <input id="registry-fuel-type" class="omni-input" bind:value={editForm.fuelType} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                </div>
                {#if shouldShowVehicleFields(editForm.assetType)}
                  <div class="omni-field">
                    <label for="registry-make">Make</label>
                    <input id="registry-make" class="omni-input" bind:value={editForm.make} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                  <div class="omni-field">
                    <label for="registry-model">Model</label>
                    <input id="registry-model" class="omni-input" bind:value={editForm.model} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                  <div class="omni-field">
                    <label for="registry-year">Year</label>
                    <input id="registry-year" class="omni-input" bind:value={editForm.year} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                  <div class="omni-field">
                    <label for="registry-color">Color</label>
                    <input id="registry-color" class="omni-input" bind:value={editForm.color} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                  <div class="omni-field">
                    <label for="registry-engine-capacity">Engine capacity</label>
                    <input id="registry-engine-capacity" class="omni-input" bind:value={editForm.engineCapacity} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                  <div class="omni-field">
                    <label for="registry-co2">CO2 emissions</label>
                    <input id="registry-co2" class="omni-input" bind:value={editForm.co2Emissions} disabled={isVirtualAsset(selectedAssetDetail.id) || saving || decodingVin} />
                  </div>
                {/if}
              </div>

              <div class="omni-field mt-4">
                <label for="registry-notes">Asset notes</label>
                <textarea id="registry-notes" rows="3" class="omni-textarea" bind:value={editForm.notes} disabled={isVirtualAsset(selectedAssetDetail.id) || saving}></textarea>
              </div>

              <div class="mt-5 flex flex-wrap gap-2">
                <Button size="sm" onclick={saveAsset} disabled={saving || isVirtualAsset(selectedAssetDetail.id)}>
                  {saving ? "Saving…" : "Save asset details"}
                </Button>
                {#if isVirtualAsset(selectedAssetDetail.id)}
                  <p class="text-xs text-muted-foreground">This record exists from assignment history only and cannot be edited until it is captured as a formal asset.</p>
                {/if}
              </div>
            </div>

            <div class="omni-detail-section">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-semibold">Assigned devices</p>
                  <p class="text-xs text-muted-foreground">Each device keeps its hardware profile, current SIM, and deployment context in line.</p>
                </div>
                <span class="text-xs text-muted-foreground">{selectedAssetDetail.devices.length} device{selectedAssetDetail.devices.length === 1 ? "" : "s"}</span>
              </div>
              {#if selectedAssetDetail.devices.length > 0}
                <div class="mt-3 space-y-3">
                  {#each selectedAssetDetail.devices as device (device.assignmentId ?? device.imei)}
                    <div class="rounded-xl border border-white/50 bg-background/70 p-3 dark:border-white/10 dark:bg-slate-900/60">
                      <div class="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p class="font-medium">{device.imei}</p>
                          <p class="text-xs text-muted-foreground">{[device.model, device.hardwareType].filter(Boolean).join(" · ") || "Device assigned"}</p>
                        </div>
                        <span class="text-xs text-muted-foreground">Installed {formatDateTime(device.installedAt ?? device.assignedAt)}</span>
                      </div>
                      <div class="mt-2 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2 xl:grid-cols-3">
                        <p>Technician: <span class="font-medium text-foreground">{device.technician ?? "—"}</span></p>
                        <p>Location: <span class="font-medium text-foreground">{device.installationLocation ?? "—"}</span></p>
                        <p>Status: <span class="font-medium text-foreground">{device.status ?? "—"}</span></p>
                        <p>Managed SIM: <span class="font-medium text-foreground">{simLabel(device.sim)}</span></p>
                      </div>
                      <div class="mt-3 grid gap-3 lg:grid-cols-2">
                        <div class="rounded-2xl border border-white/50 bg-white/70 p-3 text-xs text-muted-foreground dark:border-white/10 dark:bg-slate-950/45">
                          <p class="text-[11px] uppercase tracking-[0.2em]">Device profile</p>
                          <div class="mt-2 grid gap-2 sm:grid-cols-2">
                            <p>IMEI: <span class="font-medium text-foreground">{device.imei}</span></p>
                            <p>Serial: <span class="font-medium text-foreground">{device.serialNumber ?? "—"}</span></p>
                            <p>Manufacturer: <span class="font-medium text-foreground">{device.manufacturer ?? "—"}</span></p>
                            <p>Model: <span class="font-medium text-foreground">{device.model ?? "—"}</span></p>
                            <p>Type: <span class="font-medium text-foreground">{device.hardwareType ?? "—"}</span></p>
                            <p>Firmware: <span class="font-medium text-foreground">{device.firmwareVersion ?? "—"}</span></p>
                            <p>Inventory state: <span class="font-medium text-foreground">{device.status ?? "—"}</span></p>
                          </div>
                        </div>
                        <div class="rounded-2xl border border-white/50 bg-white/70 p-3 text-xs text-muted-foreground dark:border-white/10 dark:bg-slate-950/45">
                          <p class="text-[11px] uppercase tracking-[0.2em]">SIM profile</p>
                          {#if device.sim}
                            <div class="mt-2 grid gap-2 sm:grid-cols-2">
                              <p>ICCID: <span class="font-medium text-foreground">{device.sim.iccid ?? "—"}</span></p>
                              <p>SIM number: <span class="font-medium text-foreground">{device.sim.msisdn ?? "—"}</span></p>
                              <p>Carrier: <span class="font-medium text-foreground">{device.sim.carrier ?? "Econet"}</span></p>
                              <p>Status: <span class="font-medium text-foreground">{device.sim.status ?? "assigned"}</span></p>
                            </div>
                          {:else}
                            <p class="mt-2">No managed SIM is currently linked to this device.</p>
                          {/if}
                        </div>
                      </div>
                      {#if device.sim}
                        <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                          <span class="rounded-full border border-border/70 bg-background/70 px-2 py-1">{device.sim.status ?? "assigned"}</span>
                          {#if device.sim.roamingEnabled}
                            <span class="rounded-full border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-cyan-700 dark:text-cyan-300">Roaming enabled</span>
                          {/if}
                        </div>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="mt-3 text-sm text-muted-foreground">No devices are currently assigned to this asset.</p>
              {/if}
            </div>
          </div>
        {:else if selectedHubId === ALL_HUBS_OPTION}
          <div class="omni-empty-state">Select any asset from the full register to open Asset 360.</div>
        {:else if selectedHub}
          <div class="omni-empty-state">Select an asset from {selectedHub.name} to open Asset 360.</div>
        {:else}
          <div class="omni-empty-state">Pick a hub first, then select an asset to inspect everything in one place.</div>
        {/if}
      </section>
    </div>
  </section>
</section>
