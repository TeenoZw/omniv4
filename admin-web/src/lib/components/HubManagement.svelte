<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { sessionStore } from "$lib/stores/session";
  import {
    bulkDeleteHubs,
    decodeAssetVin,
    fetchHubAssetDetail,
    fetchHubAssets,
    fetchHubById,
    fetchHubsPage,
    fetchRecycleBinHubs,
    purgeHubFromRecycleBin,
    restoreHubFromRecycleBin,
    updateHub,
    updateHubAsset,
  } from "$lib/api/hubs";
  import type { Hub, HubAsset, HubAssetDetail } from "$lib/types/hub";
  import HubMultiStepForm from "$lib/components/hub-management/HubMultiStepForm.svelte";
  import { Button } from "$lib/components/ui/button";
  import { RefreshCw, Shield, Sparkles, Crown, Filter, Pencil, ArrowLeft } from "lucide-svelte";
  import { hubChangeLogStore, type HubChangeLogEntry } from "$lib/stores/hub-change-log";
  import { workspaceNavStore } from "$lib/stores/workspace-nav";
  import { confirmAndRun, confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";

  type Session = {
    token: string | null;
    refreshToken: string | null;
    user: { name?: string | null; email?: string | null } | null;
    roles: string[];
    hubs: Hub[];
    currentHubId: string | null;
    currentHub: Hub | null;
    expiresAt: number | null;
    forceLogoutCountdown: boolean;
  } | null;

  let hubs: Hub[] = [];
  let selectedHubId: string | null = null;
  let selectedHub: Hub | null = null;
  let isLoading = false;
  let detailLoading = false;
  let errorMessage: string | null = null;
  let session: Session = null;
  let isProvisioning = false;
  let searchTerm = "";
  let tierFilter: "all" | "Individual" | "Business" = "all";
  let statusFilter: "all" | "active" | "provisioning" | "suspended" | "inactive" = "all";
  let sortKey: "name" | "plan" | "devices" = "name";
  let pageSize = 12;
  let currentPage = 1;
  let totalHubs = 0;
  let filterDebounce: ReturnType<typeof setTimeout> | null = null;
  let hubDetailView: "overview" | "assets" = "overview";
  let assetSearch = "";
  let assetStatusFilter = "all";
  let assetPage = 1;
  let assetPerPage = 10;
  let assetTotal = 0;
  let assetFilterDebounce: ReturnType<typeof setTimeout> | null = null;
  let lastAssetFilterSignature = "";
  let selectedHubAssets: HubAsset[] = [];
  let selectedAssetId: string | null = null;
  let selectedAssetDetail: HubAssetDetail | null = null;
  let assetsLoading = false;
  let assetDetailLoading = false;
  let assetSaving = false;
  let assetVinDecoding = false;
  let assetVinFeedback = "";
  let isEditingHub = false;
  let isSavingEdit = false;
  let isDeletingHubs = false;
  let selectedHubIds = new Set<string>();
  let statusMessage: { type: "success" | "error"; text: string } | null = null;
  let showRecycleBin = false;
  let recycleLoading = false;
  let recycleError: string | null = null;
  let recycleItems: Array<{
    id: string;
    name: string;
    code: string;
    deleted_at?: string | null;
    recycle_bin_expires_at?: string | null;
    days_until_purge?: number | null;
  }> = [];
  let recycleActionHubId: string | null = null;
  let editForm = {
    name: "",
    tier: "",
    billingCycle: "monthly",
    paymentMethod: "manual_invoice",
    status: "active",
    primaryContact: { name: "", email: "", phone: "" },
    billingContact: { name: "", email: "", phone: "" },
    notes: "",
    timezone: "",
    country: "",
    city: "",
    address: "",
    goLiveDate: "",
    type: "",
    currency: "",
  };

  let assetEditForm = {
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
  const assetTypeOptions = ["trailer", "truck", "bus", "sedan", "hatchback", "tractor", "excavator", "other"];

  const tierMeta = {
    Individual: {
      icon: Shield,
      badgeClass: "border-slate-300 bg-slate-100 text-slate-800",
    },
    Business: {
      icon: Crown,
      badgeClass: "border-amber-300 bg-amber-50 text-amber-900",
    },
  };
  type TierKey = keyof typeof tierMeta;

  function normalizePlanValue(value?: string | null) {
    if (!value) return "";
    const normalized = value.toString().trim();
    if (!normalized) return "";
    const lowered = normalized.toLowerCase();
    if (["basic", "free", "individual"].includes(lowered)) return "Individual";
    if (["pro", "enterprise", "business"].includes(lowered)) return "Business";
    return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
  }

  function tierMetaLookup(tier?: string | null) {
    const normalized = normalizePlanValue(tier);
    if (!normalized) return null;
    return tierMeta[normalized as TierKey] ?? null;
  }

  const releaseSession = sessionStore.subscribe((value) => {
    session = value;
  });
  const dispatch = createEventDispatcher<{
    gotoInventory: { deviceSearch: string };
  }>();
  const releaseWorkspaceNav = workspaceNavStore.subscribe((state) => {
    if (state?.hubFocusId && state.hubFocusId !== selectedHubId) {
      void openHubDetail(state.hubFocusId);
    }
  });

  onMount(() => {
    void loadHubs();
  });

  onDestroy(() => {
    releaseSession();
    releaseWorkspaceNav();
    if (filterDebounce) {
      clearTimeout(filterDebounce);
      filterDebounce = null;
    }
    if (assetFilterDebounce) {
      clearTimeout(assetFilterDebounce);
      assetFilterDebounce = null;
    }
  });

  function deriveActor() {
    return session?.user?.name ?? session?.user?.email ?? "Unknown operator";
  }

  function formatDateTime(value?: string | null) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  function simLabel(sim?: { iccid?: string | null; msisdn?: string | null; carrier?: string | null; roamingEnabled?: boolean | null } | null) {
    if (!sim) return "No SIM linked";
    return [sim.iccid, sim.msisdn, sim.carrier, sim.roamingEnabled ? "Roaming" : null].filter(Boolean).join(" · ");
  }

  function latestAssetActivity(detail?: HubAssetDetail | null) {
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
      hub: {
        id: selectedAssetDetail.hubId,
        code: selectedAssetDetail.hubCode,
        name: selectedAssetDetail.hubName,
      },
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

  function appendHubLog(action: HubChangeLogEntry["action"], hub: Hub, details: string) {
    hubChangeLogStore.append({
      id: globalThis.crypto?.randomUUID?.() ?? `hub-log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      actor: deriveActor(),
      action,
      hubId: hub.id,
      summary: `${hub.name} (${hub.code})`,
      details,
    });
  }

  async function loadHubs() {
    isLoading = true;
    errorMessage = null;
    selectedHub = null;
    selectedHubId = null;
    try {
      const sortMap: Record<string, string> = {
        name: "name_asc",
        plan: "name_asc",
        devices: "devices_desc",
      };
      const response = await fetchHubsPage({
        page: currentPage,
        limit: pageSize,
        search: searchTerm.trim() || undefined,
        tier: tierFilter === "all" ? undefined : tierFilter.toLowerCase(),
        status: statusFilter === "all" ? undefined : statusFilter,
        sort: sortMap[sortKey] ?? "name_asc",
      });
      hubs = response.items;
      totalHubs = Number(response.meta?.total ?? hubs.length);
      const nextSelected = new Set<string>();
      for (const hub of hubs) {
        if (selectedHubIds.has(hub.id)) {
          nextSelected.add(hub.id);
        }
      }
      selectedHubIds = nextSelected;
    } catch (error) {
      console.error("Unable to load hubs", error);
      errorMessage = "Failed to load hubs. Please retry.";
      totalHubs = 0;
    } finally {
      isLoading = false;
    }
  }

  async function loadRecycleBin() {
    recycleLoading = true;
    recycleError = null;
    try {
      recycleItems = await fetchRecycleBinHubs();
    } catch (error) {
      console.error("Unable to load recycle bin hubs", error);
      recycleError = "Unable to load the recycle bin.";
    } finally {
      recycleLoading = false;
    }
  }

  async function toggleRecycleBin() {
    showRecycleBin = !showRecycleBin;
    if (showRecycleBin) {
      await loadRecycleBin();
    }
  }

  function queueHubReload(resetPage = false) {
    if (resetPage) {
      currentPage = 1;
    }
    if (filterDebounce) {
      clearTimeout(filterDebounce);
      filterDebounce = null;
    }
    filterDebounce = setTimeout(() => {
      void loadHubs();
    }, 250);
  }

  function toggleHubSelection(hubId: string, checked: boolean) {
    const next = new Set(selectedHubIds);
    if (checked) next.add(hubId);
    else next.delete(hubId);
    selectedHubIds = next;
  }

  function toggleSelectAllOnPage(checked: boolean) {
    const next = new Set(selectedHubIds);
    for (const hub of pagedHubs) {
      if (checked) next.add(hub.id);
      else next.delete(hub.id);
    }
    selectedHubIds = next;
  }

  async function deleteSelectedHubs() {
    const ids = Array.from(selectedHubIds);
    if (!ids.length || isDeletingHubs) return;
    await confirmAndRun(
      {
        title: "Delete selected hubs",
        description: "Recycle bin",
        message: `Delete ${ids.length} selected hub(s)? This will move them to the recycle bin.`,
        confirmLabel: "Delete hubs",
        tone: "destructive",
      },
      async () => {
        isDeletingHubs = true;
        statusMessage = null;
        try {
          const result = await bulkDeleteHubs(ids);
          if (!result.deleted) {
            statusMessage = {
              type: "error",
              text: result.notFound?.length
                ? `No hubs deleted. Missing: ${result.notFound.join(", ")}`
                : "No hubs were deleted.",
            };
            return;
          }
          const deletedSet = new Set(result.deletedIds ?? ids);
          hubs = hubs.filter((hub) => !deletedSet.has(hub.id) && !ids.includes(hub.id));
          totalHubs = Math.max(0, Number(totalHubs || 0) - result.deleted);
          selectedHubIds = new Set<string>();
          if (selectedHubId && ids.includes(selectedHubId)) {
            closeDetail();
          }
          await loadHubs();
          if (showRecycleBin) {
            await loadRecycleBin();
          }
          statusMessage = {
            type: "success",
            text: result.notFound?.length
              ? `Deleted ${result.deleted} hub(s). Missing: ${result.notFound.join(", ")}`
              : `Deleted ${result.deleted} hub(s).`,
          };
        } catch (error) {
          console.error("Failed to delete hubs", error);
          statusMessage = {
            type: "error",
            text: "Unable to delete the selected hubs.",
          };
        } finally {
          isDeletingHubs = false;
        }
      },
    );
  }

  async function restoreDeletedHub(hubId: string) {
    if (!hubId || recycleActionHubId) return;
    await confirmAndRun(
      {
        title: "Restore hub",
        description: "Recycle bin",
        message: "Restore this hub from the recycle bin?",
        confirmLabel: "Restore hub",
      },
      async () => {
        recycleActionHubId = hubId;
        statusMessage = null;
        try {
          await restoreHubFromRecycleBin(hubId);
          await Promise.all([loadHubs(), loadRecycleBin()]);
          statusMessage = { type: "success", text: "Hub restored from recycle bin." };
          toastStore.push({ title: "Hub restored", message: "The hub is available again.", tone: "success" });
        } catch (error) {
          console.error("Failed to restore hub", error);
          statusMessage = { type: "error", text: "Unable to restore the hub." };
        } finally {
          recycleActionHubId = null;
        }
      },
    );
  }

  async function purgeDeletedHub(hubId: string, hubName: string) {
    if (!hubId || recycleActionHubId) return;
    await confirmAndRun(
      {
        title: "Permanently delete hub",
        description: "Recycle bin",
        message: `Permanently delete ${hubName}? This cannot be undone.`,
        confirmLabel: "Delete permanently",
        tone: "destructive",
      },
      async () => {
        recycleActionHubId = hubId;
        statusMessage = null;
        try {
          await purgeHubFromRecycleBin(hubId);
          await Promise.all([loadHubs(), loadRecycleBin()]);
          statusMessage = { type: "success", text: "Hub permanently deleted." };
          toastStore.push({ title: "Hub deleted", message: `${hubName} was permanently removed.`, tone: "success" });
        } catch (error) {
          console.error("Failed to permanently delete hub", error);
          statusMessage = { type: "error", text: "Unable to permanently delete the hub." };
        } finally {
          recycleActionHubId = null;
        }
      },
    );
  }

  async function loadSelectedHubAssets(forceAssetId: string | null = null) {
    if (!selectedHubId) return;
    assetsLoading = true;
    try {
      const response = await fetchHubAssets(selectedHubId, {
        page: assetPage,
        limit: assetPerPage,
        search: assetSearch.trim() || undefined,
        status: assetStatusFilter === "all" ? undefined : assetStatusFilter,
      });
      selectedHubAssets = response.items;
      assetTotal = Number(response.meta?.total ?? response.items.length);

      const nextAssetId =
        forceAssetId ??
        (selectedAssetId && response.items.some((asset) => asset.id === selectedAssetId)
          ? selectedAssetId
          : response.items[0]?.id ?? null);

      selectedAssetId = nextAssetId;
      if (nextAssetId) {
        await openAssetDetail(nextAssetId);
      } else {
        selectedAssetDetail = null;
      hydrateAssetEditForm(null);
    hydrateAssetEditForm(null);
        hydrateAssetEditForm(null);
      }
    } catch (error) {
      console.error("Failed to load hub assets", error);
      selectedHubAssets = [];
      assetTotal = 0;
      selectedAssetDetail = null;
      statusMessage = { type: "error", text: "Unable to load hub assets." };
    } finally {
      assetsLoading = false;
    }
  }

  async function openHubDetail(hubId: string) {
    selectedHubId = hubId;
    detailLoading = true;
    isEditingHub = false;
    hubDetailView = "overview";
    assetSearch = "";
    assetStatusFilter = "all";
    assetPage = 1;
    assetPerPage = 10;
    assetTotal = 0;
    selectedAssetId = null;
    selectedAssetDetail = null;
    statusMessage = null;
    try {
      const hub = await fetchHubById(hubId);
      selectedHub = hub;
      await loadSelectedHubAssets();
      if (selectedHub) {
        seedEditForm(selectedHub);
      }
    } catch (error) {
      console.error("Failed to load hub detail", error);
      selectedHubAssets = [];
    } finally {
      detailLoading = false;
    }
  }

  function closeDetail() {
    selectedHubId = null;
    selectedHub = null;
    hubDetailView = "overview";
    assetSearch = "";
    assetStatusFilter = "all";
    selectedHubAssets = [];
    selectedAssetId = null;
    selectedAssetDetail = null;
    isEditingHub = false;
    statusMessage = null;
  }

  async function openAssetDetail(assetId: string) {
    if (!selectedHubId || !assetId) return;
    selectedAssetId = assetId;
    assetDetailLoading = true;
    try {
      selectedAssetDetail = await fetchHubAssetDetail(selectedHubId, assetId);
      hydrateAssetEditForm(selectedAssetDetail);
    } catch (error) {
      console.error("Failed to load asset detail", error);
      selectedAssetDetail = null;
      statusMessage = { type: "error", text: "Unable to load asset details." };
    } finally {
      assetDetailLoading = false;
    }
  }

  function openDeviceInInventory(deviceSearch: string | null | undefined) {
    if (!deviceSearch) return;
    dispatch("gotoInventory", { deviceSearch });
  }

  function handleHubCreated(event: CustomEvent<{ hub: Hub }>) {
    const { hub } = event.detail;
    hubs = [hub, ...hubs.filter((existing) => existing.id !== hub.id)];
    selectedHubId = hub.id;
    selectedHub = hub;
    isProvisioning = false;
    appendHubLog(
      "create",
      hub,
      `Registered hub at ${hub.city || hub.country} · Plan ${hub.tier} · ${hub.billingCycle} via ${hub.paymentMethod}`
    );
    queueHubReload(true);
  }


  function hydrateAssetEditForm(asset: HubAssetDetail | null) {
    assetEditForm = {
      assetType: asset?.assetType ?? "",
      assetTypeOther: asset?.assetTypeOther ?? "",
      assetName: asset?.assetName ?? "",
      registration: asset?.registration ?? "",
      vin: asset?.vin ?? "",
      make: asset?.make ?? "",
      model: asset?.model ?? "",
      year: asset?.year ?? "",
      color: asset?.color ?? "",
      engineCapacity: asset?.engineCapacity ?? "",
      co2Emissions: asset?.co2Emissions ?? "",
      fuelType: asset?.fuelType ?? "",
      notes: asset?.notes ?? "",
    };
    assetVinFeedback = "";
  }

  function isVirtualAsset(assetId?: string | null) {
    return `${assetId ?? ""}`.startsWith("virtual:");
  }

  function shouldShowVehicleFields(assetType?: string | null) {
    return ["truck", "bus", "sedan", "hatchback", "tractor", "trailer"].includes((assetType ?? "").toLowerCase());
  }

  function applyDecodedAssetData(decoded: Record<string, string | null | undefined>) {
    assetEditForm = {
      ...assetEditForm,
      vin: decoded.normalized_vin || assetEditForm.vin,
      make: decoded.make || assetEditForm.make,
      model: decoded.model || assetEditForm.model,
      year: decoded.year || assetEditForm.year,
      fuelType: decoded.fuel_type || assetEditForm.fuelType,
      engineCapacity: decoded.engine_capacity || assetEditForm.engineCapacity,
      assetType:
        assetEditForm.assetType && assetEditForm.assetType !== "other"
          ? assetEditForm.assetType
          : decoded.suggested_asset_type || assetEditForm.assetType,
    };
  }

  function trackingChip(asset: { trackingState?: string | null; assignedDeviceCount?: number } | null) {
    if (`${asset?.trackingState ?? ""}`.toLowerCase() === "tracked") {
      return { label: "Tracked", className: "border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200" };
    }
    if (isVirtualAsset(selectedAssetDetail?.id)) {
      return { label: "Assignment only", className: "border-slate-300 bg-slate-100 text-slate-800 dark:border-white/10 dark:bg-white/5 dark:text-slate-200" };
    }
    if ((asset?.assignedDeviceCount ?? 0) > 0) {
      return { label: "Pending sync", className: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" };
    }
    return { label: "Pending device", className: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" };
  }

  function seedEditForm(hub: Hub) {
    editForm = {
      name: hub.name,
      tier: hub.tier,
      billingCycle: hub.billingCycle,
      paymentMethod: hub.paymentMethod,
      status: hub.status,
      primaryContact: { ...hub.primaryContact, phone: hub.primaryContact?.phone ?? "" },
      billingContact: { ...hub.billingContact, phone: hub.billingContact?.phone ?? "" },
      notes: hub.notes ?? "",
      timezone: hub.timezone ?? "",
      country: hub.country ?? "",
      city: hub.city ?? "",
      address: hub.address ?? "",
      goLiveDate: hub.goLiveDate ?? "",
      type: hub.type ?? "",
      currency: hub.currency ?? "",
    };
  }

  async function saveAssetChanges() {
    if (!selectedHubId || !selectedAssetDetail || isVirtualAsset(selectedAssetDetail.id)) return;
    await confirmAndRun(
      {
        title: "Save asset details",
        description: "Administrative asset maintenance",
        message: `Save updates for ${selectedAssetDetail.assetName ?? selectedAssetDetail.label ?? "this asset"}?`,
        confirmLabel: "Save asset",
      },
      async () => {
        assetSaving = true;
        statusMessage = null;
        try {
          const updated = await updateHubAsset(selectedHubId, selectedAssetDetail.id, {
            assetType: assetEditForm.assetType,
            assetTypeOther: assetEditForm.assetType === "other" ? assetEditForm.assetTypeOther : "",
            assetName: assetEditForm.assetName,
            registration: assetEditForm.registration,
            vin: assetEditForm.vin,
            make: assetEditForm.make,
            model: assetEditForm.model,
            year: assetEditForm.year,
            color: assetEditForm.color,
            engineCapacity: assetEditForm.engineCapacity,
            co2Emissions: assetEditForm.co2Emissions,
            fuelType: assetEditForm.fuelType,
            notes: assetEditForm.notes,
          });
          selectedAssetDetail = updated;
          hydrateAssetEditForm(updated);
          await loadSelectedHubAssets(updated.id);
          statusMessage = { type: "success", text: "Open saved." };
          toastStore.push({ title: "Asset saved", message: `${updated.assetName ?? updated.label ?? "Asset"} updated successfully.`, tone: "success" });
        } catch (error) {
          console.error("Failed to save asset", error);
          const err = error as { response?: { data?: { detail?: string } }; message?: string };
          statusMessage = { type: "error", text: err?.response?.data?.detail ?? err?.message ?? "Unable to save asset details." };
        } finally {
          assetSaving = false;
          resetFocusAfterSave();
        }
      },
    );
  }

  async function decodeSelectedAssetVin() {
    if (!assetEditForm.vin?.trim()) {
      statusMessage = { type: "error", text: "Enter a VIN before requesting vehicle metadata." };
      return;
    }
    assetVinDecoding = true;
    assetVinFeedback = "";
    try {
      const response = await decodeAssetVin(assetEditForm.vin);
      applyDecodedAssetData((response as { decoded?: Record<string, string | null | undefined> })?.decoded ?? {});
      assetVinFeedback = (response as { warnings?: string[] })?.warnings?.[0] ?? "VIN metadata loaded.";
      toastStore.push({ title: "VIN decoded", message: "Vehicle metadata applied to the selected asset.", tone: "success" });
    } catch (error) {
      console.error("Failed to decode VIN", error);
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      statusMessage = { type: "error", text: err?.response?.data?.detail ?? err?.message ?? "Unable to decode this VIN." };
    } finally {
      assetVinDecoding = false;
    }
  }

  async function saveHubChanges() {
    if (!selectedHub) return;
    if (!(await confirmSave({ title: "Save hub profile", message: "Save these hub profile changes?" }))) {
      return;
    }
    isSavingEdit = true;
    statusMessage = null;
    try {
      const payload = {
        ...selectedHub,
        name: editForm.name,
        tier: editForm.tier,
        billingCycle: editForm.billingCycle,
        paymentMethod: editForm.paymentMethod,
        status: editForm.status,
        primaryContact: { ...editForm.primaryContact },
        billingContact: { ...editForm.billingContact },
        currency: editForm.currency,
        notes: editForm.notes,
        timezone: editForm.timezone,
        country: editForm.country,
        city: editForm.city,
        address: editForm.address,
        goLiveDate: editForm.goLiveDate,
        type: editForm.type,
      };
      const hub = await updateHub(selectedHub.id, payload);
      // Re-fetch to ensure we reflect persisted values (server may coerce/normalize fields)
      const refreshed = await fetchHubById(selectedHub.id);
      hubs = hubs.map((existing) => (existing.id === hub.id ? hub : existing));
      selectedHub = refreshed;
      seedEditForm(refreshed);
      appendHubLog("update", hub, `Edited hub profile · ${hub.tier} · ${hub.billingCycle}`);
      statusMessage = { type: "success", text: "Hub profile saved." };
      toastStore.push({ title: "Hub saved", message: `${hub.name} was updated successfully.`, tone: "success" });
      isEditingHub = false;
    } catch (error) {
      console.error("Failed to save hub edits", error);
      const err = error as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      const detail = err?.response?.data?.detail ?? err?.message ?? "";
      statusMessage = {
        type: "error",
        text: detail ? `Unable to save hub changes: ${detail}` : "Unable to save hub changes.",
      };
    } finally {
      isSavingEdit = false;
      resetFocusAfterSave();
    }
  }

  $: totalPages = Math.max(1, Math.ceil(totalHubs / pageSize));
  $: currentPage = Math.min(currentPage, totalPages);
  $: pagedHubs = hubs;
  $: activeHubCount = hubs.filter((hub) => (hub.status ?? "").toLowerCase() === "active").length;
  $: provisioningHubCount = hubs.filter((hub) => (hub.status ?? "").toLowerCase() === "provisioning").length;
  $: suspendedHubCount = hubs.filter((hub) => (hub.status ?? "").toLowerCase() === "suspended").length;
  $: assetStatusOptions = Array.from(
    new Set(
      selectedHubAssets
        .map((asset) => (asset.status ?? "").toString().toLowerCase())
        .filter(Boolean),
    ),
  ).sort();
  $: selectedAssetDevices = selectedAssetDetail?.devices ?? [];
  $: assetTotalPages = Math.max(1, Math.ceil(assetTotal / assetPerPage));
  $: assetPage = Math.min(assetPage, assetTotalPages);
  $: assetFilterSignature = `${selectedHubId}|${assetSearch}|${assetStatusFilter}|${assetPerPage}`;
  $: if (assetFilterSignature !== lastAssetFilterSignature) {
    lastAssetFilterSignature = assetFilterSignature;
    if (assetPage !== 1) {
      assetPage = 1;
    }
  }
  $: assetFilterTrigger = `${selectedHubId}|${hubDetailView}|${assetSearch}|${assetStatusFilter}|${assetPage}|${assetPerPage}`;
  $: if (selectedHubId && hubDetailView === "assets" && assetFilterTrigger) {
    if (assetFilterDebounce) {
      clearTimeout(assetFilterDebounce);
      assetFilterDebounce = null;
    }
    assetFilterDebounce = setTimeout(() => {
      void loadSelectedHubAssets();
    }, 220);
  }
  $: selectedCount = selectedHubIds.size;
  $: allPageSelected = pagedHubs.length > 0 && pagedHubs.every((hub) => selectedHubIds.has(hub.id));
  $: isProfilePage = Boolean(selectedHub);
  $: filterTrigger = `${searchTerm}|${tierFilter}|${statusFilter}|${sortKey}|${pageSize}`;
  $: if (filterTrigger) {
    queueHubReload(true);
  }
</script>

<section class="space-y-6">
  <header class="omni-page-header">
    <div class="omni-page-header-copy">
      <p class="omni-kicker">Operations</p>
      <h2 class="omni-page-title">Hubs</h2>
    </div>
  </header>

  {#if isProvisioning}
    <section class="space-y-4">
      <div class="omni-child-header">
        <div class="space-y-1">
          <p class="omni-kicker">Provisioning</p>
          <h3 class="text-xl font-semibold">Add new hub</h3>
        </div>
        <Button variant="outline" size="sm" onclick={() => (isProvisioning = false)}>
          Back to hub list
        </Button>
      </div>

      <HubMultiStepForm on:created={handleHubCreated} />
    </section>
  {:else}
    <section class="omni-panel border-0 shadow-none p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-xl font-semibold">Hub register</h3>
        </div>
        <div class="flex items-center gap-2">
          <Button
            variant="destructive"
            size="sm"
            onclick={deleteSelectedHubs}
            disabled={!selectedCount || isDeletingHubs}
          >
            {isDeletingHubs ? "Deleting..." : `Delete selected (${selectedCount})`}
          </Button>
          <Button variant="outline" size="sm" onclick={() => loadHubs()} disabled={isLoading}>
            <RefreshCw class={isLoading ? "mr-2 h-4 w-4 animate-spin" : "mr-2 h-4 w-4"} />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onclick={toggleRecycleBin} disabled={recycleLoading}>
            {showRecycleBin ? "Hide recycle bin" : "Recycle bin"}
          </Button>
          <Button size="sm" onclick={() => (isProvisioning = true)}>
            Add new hub
          </Button>
        </div>
      </div>

      <div class="omni-toolbar-strip mt-5">
        <div class="omni-toolbar-field flex min-w-[15rem] items-center gap-2">
          <svg class="w-4 h-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input
            class="w-full bg-transparent text-sm outline-none"
            type="search"
            placeholder="Search hubs"
            bind:value={searchTerm}
          />
        </div>
        <div class="omni-toolbar-field-compact flex items-center gap-2">
          <Filter class="w-4 h-4 text-muted-foreground" />
          <select class="w-full text-sm bg-transparent outline-none" bind:value={tierFilter}>
            <option value="all">All plans</option>
            <option value="Individual">Individual</option>
            <option value="Business">Business</option>
          </select>
        </div>
        <div class="omni-toolbar-field-compact flex items-center gap-2">
          <span class="text-xs tracking-wide uppercase text-muted-foreground">Status</span>
          <select class="w-full text-sm bg-transparent outline-none" bind:value={statusFilter}>
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="provisioning">Provisioning</option>
            <option value="suspended">Suspended</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div class="omni-toolbar-field-compact flex items-center gap-2">
          <span class="text-xs tracking-wide uppercase text-muted-foreground">Sort</span>
          <select class="w-full text-sm bg-transparent outline-none" bind:value={sortKey}>
            <option value="name">Name A→Z</option>
            <option value="plan">Plan</option>
            <option value="devices">Devices (desc)</option>
          </select>
        </div>
        <div class="omni-toolbar-field-compact flex items-center gap-2">
          <span class="text-xs tracking-wide uppercase text-muted-foreground">Page size</span>
          <select class="w-full text-sm bg-transparent outline-none" bind:value={pageSize}>
            <option value={12}>12</option>
            <option value={24}>24</option>
            <option value={48}>48</option>
          </select>
        </div>
        <div class="ml-auto flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span class="omni-inline-stat">Total hubs: {totalHubs}</span>
          <span class="omni-inline-stat">Active: {activeHubCount}</span>
          <span class="omni-inline-stat">Provisioning: {provisioningHubCount}</span>
          <span class="omni-inline-stat">Suspended: {suspendedHubCount}</span>
        </div>
      </div>

      {#if showRecycleBin}
        <div class="mt-4 rounded-[1.35rem] border border-white/70 bg-white/60 p-4 dark:border-white/10 dark:bg-slate-950/35">
          <div class="mb-3 flex items-center justify-between gap-2">
            <p class="text-sm font-semibold">Recycle bin</p>
            <Button variant="outline" size="sm" onclick={loadRecycleBin} disabled={recycleLoading}>
              {recycleLoading ? "Refreshing…" : "Refresh bin"}
            </Button>
          </div>
          {#if recycleError}
            <p class="rounded-md border border-destructive/60 bg-destructive/10 px-3 py-2 text-sm text-destructive">{recycleError}</p>
          {:else if recycleItems.length === 0}
            <p class="text-sm text-muted-foreground">Recycle bin is empty.</p>
          {:else}
            <div class="omni-table-shell overflow-auto">
              <table class="omni-table">
                <thead>
                  <tr>
                    <th>Hub</th>
                    <th>Code</th>
                    <th>Deleted At</th>
                    <th>Purge In</th>
                    <th class="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {#each recycleItems as item (item.id)}
                    <tr>
                      <td class="font-medium">{item.name}</td>
                      <td class="font-mono text-xs">{item.code}</td>
                      <td>{formatDateTime(item.deleted_at)}</td>
                      <td>{item.days_until_purge ?? "—"} day(s)</td>
                      <td>
                        <div class="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onclick={() => restoreDeletedHub(item.id)}
                            disabled={recycleActionHubId === item.id}
                          >
                            Restore
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onclick={() => purgeDeletedHub(item.id, item.name)}
                            disabled={recycleActionHubId === item.id}
                          >
                            Permanent delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </div>
      {/if}

      {#if errorMessage}
        <div class="p-3 mt-4 text-sm border rounded-md border-destructive/60 bg-destructive/10 text-destructive">
          {errorMessage}
        </div>
      {/if}

      <div class={`${isProfilePage ? "mt-6" : "omni-page-grid mt-6"}`}>
        {#if !isProfilePage}
        <div class="omni-list-stage">
          {#if isLoading}
          <div class="omni-loading-state mt-6">
            <span class="omni-loading-spinner" aria-hidden="true"></span>
            <span>Loading hub register…</span>
          </div>
        {:else if pagedHubs.length === 0}
          <p class="p-4 mt-6 text-sm border border-dashed rounded-lg border-border/60 bg-muted/40 text-muted-foreground">
            No hubs have been provisioned yet. Use Add new hub to create your first hub profile.
          </p>
        {:else}
            <div class="omni-table-shell mt-6 overflow-x-auto">
              <table class="omni-table min-w-full">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        checked={allPageSelected}
                        onchange={(event) =>
                          toggleSelectAllOnPage((event.currentTarget as HTMLInputElement).checked)}
                      />
                    </th>
                    <th>Hub</th>
                    <th>Code</th>
                    <th>Plan</th>
                    <th>Status</th>
                    <th class="text-right">Assets</th>
                    <th class="text-right">Devices</th>
                    <th class="text-right">Users</th>
                    <th>Location</th>
                    <th class="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {#each pagedHubs as hub}
                    <tr
                      class={selectedHubId === hub.id ? "omni-row-active" : ""}
                    >
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedHubIds.has(hub.id)}
                          onclick={(event) => event.stopPropagation()}
                          onchange={(event) =>
                            toggleHubSelection(hub.id, (event.currentTarget as HTMLInputElement).checked)}
                        />
                      </td>
                      <td class="font-semibold">{hub.name}</td>
                      <td class="font-mono text-xs">{hub.code}</td>
                      <td>{hub.tier}</td>
                      <td class="capitalize">{hub.status}</td>
                      <td class="text-right">{hub.vehicleCount ?? 0}</td>
                      <td class="text-right">{hub.deviceCount}</td>
                      <td class="text-right">{hub.users?.length ?? 0}</td>
                      <td>{[hub.city, hub.country].filter(Boolean).join(", ") || "—"}</td>
                      <td class="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onclick={() => openHubDetail(hub.id)}
                        >
                          Open
                        </Button>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <p>
              Showing {(currentPage - 1) * pageSize + 1}–
              {Math.min(currentPage * pageSize, totalHubs)} of {totalHubs}
            </p>
            <div class="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                onclick={() => {
                  currentPage = Math.max(1, currentPage - 1);
                  void loadHubs();
                }}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <span>Page {currentPage} / {totalPages}</span>
              <Button
                size="sm"
                variant="outline"
                onclick={() => {
                  currentPage = Math.min(totalPages, currentPage + 1);
                  void loadHubs();
                }}
                disabled={currentPage >= totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        {/if}
        </div>
        {/if}

        <div class={isProfilePage ? "" : "omni-inspector-stage"}>
          {#if selectedHub}
          {@const selectedHubMeta = tierMetaLookup(selectedHub.tier)}
          <section class="space-y-5">
            <div class="omni-workspace-hero">
              <div class="absolute -right-16 top-0 h-40 w-40 rounded-full bg-cyan-400/10 blur-3xl"></div>
              <div class="relative space-y-5">
                <div class="flex flex-wrap items-center gap-3">
                  <button
                    class="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/75 px-3 py-1.5 text-xs text-slate-600 transition hover:border-slate-300 hover:bg-white dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
                    type="button"
                    onclick={closeDetail}
                  >
                    <ArrowLeft class="h-3.5 w-3.5" />
                    Back
                  </button>
                  <span class="marketing-pill">Hub profile</span>
                </div>

                <div class="flex flex-wrap items-start gap-4">
                  <div class="space-y-1">
                    <h4 class="text-3xl font-semibold leading-tight text-slate-950 dark:text-white">{selectedHub.name}</h4>
                    <p class="text-sm text-slate-600 dark:text-slate-300">{selectedHub.code} · {selectedHub.country} · TZ {selectedHub.timezone}</p>
                  </div>
                  <div class="ml-auto flex flex-wrap items-center gap-2">
                    {#if selectedHubMeta}
                      <span class={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-wide ${selectedHubMeta.badgeClass}`}>
                        <svelte:component this={selectedHubMeta.icon} class="h-4 w-4" />
                        {selectedHub.tier}
                      </span>
                    {:else}
                      <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs uppercase tracking-wide">{selectedHub.tier}</span>
                    {/if}
                    <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs uppercase tracking-wide capitalize text-slate-600 dark:text-slate-300">
                      {selectedHub.status}
                    </span>
                    <Button size="sm" variant="outline" onclick={() => (isEditingHub = true)}>
                      <Pencil class="mr-2 h-4 w-4" />
                      Edit hub
                    </Button>
                  </div>
                </div>

                <div class="omni-tab-rail">
                  <button
                    type="button"
                    class={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                      hubDetailView === "overview"
                        ? "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-200"
                        : "text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-white/[0.04]"
                    }`}
                    onclick={() => (hubDetailView = "overview")}
                  >
                    Overview
                  </button>
                  <button
                    type="button"
                    class={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                      hubDetailView === "assets"
                        ? "bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-200"
                        : "text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-white/[0.04]"
                    }`}
                    onclick={() => (hubDetailView = "assets")}
                  >
                    Assets ({selectedHubAssets.length || selectedHub.vehicleCount || 0})
                  </button>
                </div>

                {#if hubDetailView === "overview"}
                  <p class="max-w-4xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {selectedHub.name} runs as a {selectedHub.type || "hub"} in {selectedHub.city || "an unspecified city"}, {selectedHub.country}. It operates on
                    {selectedHub.billingCycle} billing with {selectedHub.paymentMethod}. Devices online: {selectedHub.deviceCount}. Vehicles linked:
                    {selectedHub.vehicleCount}. Primary contact is {selectedHub.primaryContact?.name || "not assigned"} ({selectedHub.primaryContact?.email || "no email"}).
                  </p>

                  <div class="grid gap-3 md:grid-cols-3">
                    <div class="omni-stat-card">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Footprint</p>
                      <p class="mt-1 text-lg font-semibold text-slate-950 dark:text-white">{selectedHub.city || "—"}, {selectedHub.country}</p>
                      <p class="text-xs text-muted-foreground">{selectedHub.address || "Address pending"}</p>
                    </div>
                    <div class="omni-stat-card">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Ops envelope</p>
                      <p class="mt-1 text-lg font-semibold text-slate-950 dark:text-white">{selectedHub.deviceCount} devices · {selectedHub.vehicleCount} vehicles</p>
                      <p class="text-xs text-muted-foreground">Status {selectedHub.status} · Go-live {selectedHub.goLiveDate || "TBD"}</p>
                    </div>
                    <div class="omni-stat-card">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Billing</p>
                      <p class="mt-1 text-lg font-semibold text-slate-950 dark:text-white">{selectedHub.billingCycle}</p>
                      <p class="text-xs text-muted-foreground">{selectedHub.paymentMethod} · {selectedHub.currency}</p>
                    </div>
                  </div>

                  <div class="grid gap-3 md:grid-cols-2">
                    <div class="omni-panel border-0 shadow-none p-4">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Contacts</p>
                      <div class="mt-3 space-y-3 text-sm">
                        <div>
                          <p class="text-xs uppercase tracking-wide text-muted-foreground">Primary</p>
                          <p class="font-semibold text-slate-950 dark:text-white">{selectedHub.primaryContact?.name || "—"}</p>
                          <p class="text-muted-foreground">{selectedHub.primaryContact?.email || "No email"}</p>
                          <p class="text-muted-foreground">{selectedHub.primaryContact?.phone || "No phone"}</p>
                        </div>
                        <div class="border-t border-border/60 pt-3">
                          <p class="text-xs uppercase tracking-wide text-muted-foreground">Billing</p>
                          <p class="font-semibold text-slate-950 dark:text-white">{selectedHub.billingContact?.name || "—"}</p>
                          <p class="text-muted-foreground">{selectedHub.billingContact?.email || "No email"}</p>
                          <p class="text-muted-foreground">{selectedHub.billingContact?.phone || "No phone"}</p>
                        </div>
                      </div>
                    </div>
                    <div class="omni-panel border-0 shadow-none p-4">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Subscription</p>
                      <div class="mt-3 space-y-1 text-sm">
                        <p>Plan: <span class="font-semibold text-slate-950 dark:text-white">{selectedHub.tier}</span></p>
                        <p>Billing: <span class="font-semibold text-slate-950 dark:text-white">{selectedHub.billingCycle}</span></p>
                        <p>Payment: <span class="font-semibold capitalize text-slate-950 dark:text-white">{selectedHub.paymentMethod}</span></p>
                        <p>Timezone: <span class="font-semibold text-slate-950 dark:text-white">{selectedHub.timezone || "UTC"}</span></p>
                      </div>
                    </div>
                  </div>

                  {#if selectedHub.users && selectedHub.users.length > 0}
                    <div class="omni-panel border-0 shadow-none p-4">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Operators</p>
                      <div class="mt-3 grid gap-2 md:grid-cols-2">
                        {#each selectedHub.users as user (user.id)}
                          <div class="rounded-[1rem] border border-white/70 bg-white/70 p-3 text-sm dark:border-white/10 dark:bg-white/[0.03]">
                            <p class="font-semibold text-slate-950 dark:text-white">{user.name}</p>
                            <p class="text-muted-foreground">{user.email}</p>
                            <p class="text-xs uppercase tracking-wide text-muted-foreground">{user.role}</p>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}

                  {#if selectedHub.notes}
                    <div class="omni-panel border-0 shadow-none p-4">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Notes</p>
                      <p class="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{selectedHub.notes}</p>
                    </div>
                  {/if}
                {:else}
                  <div class="grid gap-4 xl:grid-cols-[1.25fr,0.95fr]">
                    <div class="omni-panel border-0 shadow-none p-4">
                      <div class="rounded-[1.25rem] border border-white/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300">
                        <p class="text-xs uppercase tracking-[0.28em] text-muted-foreground">Asset creation policy</p>
                        <p class="mt-2 leading-relaxed">
                          Asset capture and hardware assignment are completed by technicians through job cards only. Admin can review captured assets here, while the assigned technician performs field onboarding and device pairing.
                        </p>
                      </div>

                      <div class="mt-4 flex flex-wrap items-center gap-3">
                        <input
                          class="min-w-[16rem] flex-1 rounded-full border border-border/70 bg-background/80 px-4 py-2.5 text-sm shadow-sm"
                          type="search"
                          placeholder="Search by registration, VIN, or make"
                          bind:value={assetSearch}
                        />
                        <select
                          class="rounded-full border border-border/70 bg-background/80 px-4 py-2.5 text-sm shadow-sm"
                          bind:value={assetStatusFilter}
                        >
                          <option value="all">All statuses</option>
                          {#each assetStatusOptions as status}
                            <option value={status}>{status}</option>
                          {/each}
                        </select>
                        <div class="rounded-full border border-border/70 bg-background/75 px-3 py-1 text-xs text-muted-foreground">
                          Showing {selectedHubAssets.length} of {assetTotal}
                        </div>
                      </div>

                      {#if assetsLoading}
                        <div class="omni-loading-state mt-3">
                          <span class="omni-loading-spinner" aria-hidden="true"></span>
                          <span>Loading assets...</span>
                        </div>
                      {:else if selectedHubAssets.length > 0}
                        <div class="omni-table-shell mt-3 max-h-[26rem] overflow-auto">
                          <table class="omni-table min-w-full text-xs">
                            <thead class="sticky top-0 z-10">
                              <tr>
                                <th>Registration</th>
                                <th>Asset</th>
                                <th>Tracking</th>
                                <th>Devices</th>
                                <th>Last assignment</th>
                                <th class="text-right">Action</th>
                              </tr>
                            </thead>
                            <tbody>
                              {#each selectedHubAssets as asset (asset.id)}
                                <tr class={`${selectedAssetId === asset.id ? "bg-cyan-50 dark:bg-cyan-500/10" : ""}`}>
                                  <td class="font-medium">{asset.registration ?? "—"}</td>
                                  <td>
                                    <div class="font-medium">{asset.assetName ?? asset.label ?? "—"}</div>
                                    <div class="text-[11px] text-muted-foreground">
                                      {(asset.assetType ?? "asset").replaceAll("_", " ")}
                                      {#if asset.make || asset.model}
                                        · {[asset.make, asset.model].filter(Boolean).join(" ")}
                                      {/if}
                                    </div>
                                  </td>
                                  <td><span class={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${trackingChip(asset).className}`}>{trackingChip(asset).label}</span></td>
                                  <td>{asset.assignedDeviceCount}</td>
                                  <td>{asset.lastAssignmentAt ? new Date(asset.lastAssignmentAt).toLocaleString() : "—"}</td>
                                  <td class="text-right">
                                    <Button size="sm" variant="outline" onclick={() => openAssetDetail(asset.id)}>
                                      Open
                                    </Button>
                                  </td>
                                </tr>
                              {/each}
                            </tbody>
                          </table>
                        </div>
                        <div class="mt-3 flex items-center justify-between gap-3 text-xs text-muted-foreground">
                          <div>Page {assetPage} of {assetTotalPages}</div>
                          <div class="flex items-center gap-2">
                            <select class="rounded-full border border-border/70 bg-background/80 px-3 py-1.5 text-xs shadow-sm" bind:value={assetPerPage}>
                              <option value={10}>10 / page</option>
                              <option value={20}>20 / page</option>
                              <option value={50}>50 / page</option>
                            </select>
                            <Button size="sm" variant="outline" onclick={() => (assetPage = Math.max(1, assetPage - 1))} disabled={assetPage <= 1}>
                              Previous
                            </Button>
                            <Button size="sm" variant="outline" onclick={() => (assetPage = Math.min(assetTotalPages, assetPage + 1))} disabled={assetPage >= assetTotalPages}>
                              Next
                            </Button>
                          </div>
                        </div>
                      {:else}
                        <div class="omni-empty-state mt-3 py-8">No assets match the current filters for this hub.</div>
                      {/if}
                    </div>

                    <div class="omni-panel border-0 shadow-none p-4">
                      {#if assetDetailLoading}
                        <div class="omni-loading-state">
                          <span class="omni-loading-spinner" aria-hidden="true"></span>
                          <span>Loading asset details...</span>
                        </div>
                      {:else if selectedAssetDetail}
                        <div class="space-y-4">
                          <div class="flex flex-wrap items-start justify-between gap-3">
                            <div class="space-y-1">
                              <p class="text-xs uppercase tracking-[0.28em] text-muted-foreground">Asset 360</p>
                              <h5 class="text-xl font-semibold text-slate-950 dark:text-white">{selectedAssetDetail.assetName ?? selectedAssetDetail.registration ?? "Unregistered asset"}</h5>
                              <p class="text-sm text-muted-foreground">
                                {(selectedAssetDetail.assetType ?? "asset").replaceAll("_", " ")}
                                {#if selectedAssetDetail.assetTypeOther}
                                  · {selectedAssetDetail.assetTypeOther}
                                {/if}
                                {#if selectedAssetDetail.registration}
                                  · {selectedAssetDetail.registration}
                                {/if}
                                {#if selectedAssetDetail.make || selectedAssetDetail.model}
                                  · {[selectedAssetDetail.make, selectedAssetDetail.model].filter(Boolean).join(" ")}
                                {/if}
                                {#if selectedAssetDetail.year}
                                  · {selectedAssetDetail.year}
                                {/if}
                                {#if selectedAssetDetail.hubCode}
                                  · {selectedAssetDetail.hubCode}
                                {/if}
                              </p>
                            </div>
                            <div class="flex flex-wrap items-center gap-2">
                              <Button size="sm" variant="outline" onclick={exportAssetSnapshot}>Export Asset 360</Button>
                              <Button size="sm" variant="outline" onclick={() => globalThis.print?.()}>Print view</Button>
                            </div>
                          </div>

                          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                            <div class="omni-stat-card p-3 text-xs shadow-none">
                              <p class="uppercase tracking-wide text-muted-foreground">Tracking</p>
                              <span class={`mt-2 inline-flex rounded-full border px-2 py-0.5 text-[11px] font-semibold ${trackingChip(selectedAssetDetail).className}`}>{trackingChip(selectedAssetDetail).label}</span>
                            </div>
                            <div class="omni-stat-card p-3 text-xs shadow-none">
                              <p class="uppercase tracking-wide text-muted-foreground">Registration</p>
                              <p class="mt-1 text-sm font-semibold text-slate-950 dark:text-white">{selectedAssetDetail.registration ?? "—"}</p>
                            </div>
                            <div class="omni-stat-card p-3 text-xs shadow-none">
                              <p class="uppercase tracking-wide text-muted-foreground">VIN</p>
                              <p class="mt-1 text-sm font-semibold text-slate-950 dark:text-white">{selectedAssetDetail.vin ?? "—"}</p>
                            </div>
                            <div class="omni-stat-card p-3 text-xs shadow-none">
                              <p class="uppercase tracking-wide text-muted-foreground">Managed SIMs</p>
                              <p class="mt-1 text-sm font-semibold text-slate-950 dark:text-white">{selectedAssetDevices.filter((device) => device.sim).length}</p>
                            </div>
                          </div>

                          <div class="grid gap-3 sm:grid-cols-2">
                            <label class="text-xs text-slate-600 dark:text-slate-300">
                              <span class="uppercase tracking-wide text-muted-foreground">Asset type</span>
                              <select class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.assetType} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding}>
                                {#each assetTypeOptions as assetType}
                                  <option value={assetType}>{assetType}</option>
                                {/each}
                              </select>
                            </label>
                            <label class="text-xs text-slate-600 dark:text-slate-300">
                              <span class="uppercase tracking-wide text-muted-foreground">Asset name</span>
                              <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.assetName} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                            </label>
                            {#if assetEditForm.assetType === "other"}
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Specify type</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.assetTypeOther} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                            {/if}
                            <label class="text-xs text-slate-600 dark:text-slate-300">
                              <span class="uppercase tracking-wide text-muted-foreground">Registration</span>
                              <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.registration} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                            </label>
                            <div class="text-xs text-slate-600 dark:text-slate-300">
                              <span class="uppercase tracking-wide text-muted-foreground">VIN</span>
                              <div class="mt-1 flex gap-2">
                                <input class="min-w-0 flex-1 rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.vin} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                                <Button size="sm" variant="outline" onclick={decodeSelectedAssetVin} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding || !assetEditForm.vin.trim()}>
                                  {assetVinDecoding ? "Decoding..." : "Decode VIN"}
                                </Button>
                              </div>
                              {#if assetVinFeedback}
                                <p class="mt-1 text-[11px] text-muted-foreground">{assetVinFeedback}</p>
                              {/if}
                            </div>
                            <label class="text-xs text-slate-600 dark:text-slate-300">
                              <span class="uppercase tracking-wide text-muted-foreground">Fuel type</span>
                              <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.fuelType} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                            </label>
                            {#if shouldShowVehicleFields(assetEditForm.assetType)}
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Make</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.make} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Model</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.model} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Year</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.year} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Color</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.color} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">Engine capacity</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.engineCapacity} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                              <label class="text-xs text-slate-600 dark:text-slate-300">
                                <span class="uppercase tracking-wide text-muted-foreground">CO2 emissions</span>
                                <input class="mt-1 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" bind:value={assetEditForm.co2Emissions} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving || assetVinDecoding} />
                              </label>
                            {/if}
                          </div>

                          <div class="rounded-[1.2rem] border border-white/70 bg-white/65 p-3 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300">
                            <p class="uppercase tracking-wide text-muted-foreground">Notes</p>
                            <textarea class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2 text-sm" rows="3" bind:value={assetEditForm.notes} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving}></textarea>
                          </div>

                          <div class="flex flex-wrap items-center gap-2">
                            <Button size="sm" onclick={saveAssetChanges} disabled={isVirtualAsset(selectedAssetDetail.id) || assetSaving}>
                              {assetSaving ? "Saving..." : "Save asset details"}
                            </Button>
                            {#if isVirtualAsset(selectedAssetDetail.id)}
                              <p class="text-xs text-slate-400">Assignment only records can be viewed here, but they cannot be edited until a formal asset record exists.</p>
                            {/if}
                          </div>

                          <div class="space-y-2">
                            <div class="flex items-center justify-between gap-2">
                              <p class="text-xs uppercase tracking-[0.28em] text-muted-foreground">Assigned devices</p>
                              <span class="text-xs text-muted-foreground">{selectedAssetDevices.length} active</span>
                            </div>
                            {#if selectedAssetDevices.length > 0}
                              <div class="max-h-[20rem] space-y-2 overflow-auto pr-1">
                                {#each selectedAssetDevices as device (device.assignmentId ?? device.imei)}
                                  <details class="rounded-[1.1rem] border border-white/70 bg-white/65 p-3 dark:border-white/10 dark:bg-white/[0.03]">
                                    <summary class="flex cursor-pointer list-none items-center justify-between gap-3 text-sm text-slate-950 dark:text-white">
                                      <div>
                                        <p class="font-mono text-xs">{device.imei}</p>
                                        <p class="text-xs text-muted-foreground">{device.model ?? device.hardwareType ?? "Unspecified hardware"}</p>
                                      </div>
                                      <button
                                        type="button"
                                        class="text-xs font-medium text-cyan-700 dark:text-cyan-300"
                                        onclick={(event) => {
                                          event.preventDefault();
                                          event.stopPropagation();
                                          openDeviceInInventory(device.imei ?? `${device.hardwareId ?? ""}`);
                                        }}
                                      >
                                        Open in inventory
                                      </button>
                                    </summary>
                                    <div class="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                                      <p>Status: <span class="font-medium uppercase text-slate-950 dark:text-white">{device.status ?? "—"}</span></p>
                                      <p>Asset tag: <span class="font-medium text-slate-950 dark:text-white">{device.assetRegistration ?? device.assetLabel ?? "—"}</span></p>
                                      <p>Technician: <span class="font-medium text-slate-950 dark:text-white">{device.technician ?? "—"}</span></p>
                                      <p>Location: <span class="font-medium text-slate-950 dark:text-white">{device.installationLocation ?? "—"}</span></p>
                                      <p>Assigned: <span class="font-medium text-slate-950 dark:text-white">{device.assignedAt ? new Date(device.assignedAt).toLocaleString() : "—"}</span></p>
                                      <p>Installed: <span class="font-medium text-slate-950 dark:text-white">{device.installedAt ? new Date(device.installedAt).toLocaleString() : "—"}</span></p>
                                    </div>
                                    <div class="mt-3 grid gap-3 lg:grid-cols-2">
                                      <div class="rounded-[1rem] border border-white/70 bg-white/55 p-3 dark:border-white/10 dark:bg-white/[0.03]">
                                        <p class="text-[11px] uppercase tracking-[0.25em] text-muted-foreground">Hardware profile</p>
                                        <div class="mt-2 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                                          <p>IMEI: <span class="font-medium text-slate-950 dark:text-white">{device.imei ?? "—"}</span></p>
                                          <p>Serial: <span class="font-medium text-slate-950 dark:text-white">{device.serialNumber ?? "—"}</span></p>
                                          <p>Manufacturer: <span class="font-medium text-slate-950 dark:text-white">{device.manufacturer ?? "—"}</span></p>
                                          <p>Model: <span class="font-medium text-slate-950 dark:text-white">{device.model ?? "—"}</span></p>
                                          <p>Hardware type: <span class="font-medium text-slate-950 dark:text-white">{device.hardwareType ?? "—"}</span></p>
                                          <p>Firmware: <span class="font-medium text-slate-950 dark:text-white">{device.firmwareVersion ?? "—"}</span></p>
                                        </div>
                                      </div>
                                      <div class="rounded-[1rem] border border-white/70 bg-white/55 p-3 dark:border-white/10 dark:bg-white/[0.03]">
                                        <p class="text-[11px] uppercase tracking-[0.25em] text-muted-foreground">Managed SIM</p>
                                        {#if device.sim}
                                          <div class="mt-2 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                                            <p>ICCID: <span class="font-medium text-slate-950 dark:text-white">{device.sim.iccid ?? "—"}</span></p>
                                            <p>SIM number: <span class="font-medium text-slate-950 dark:text-white">{device.sim.msisdn ?? "—"}</span></p>
                                            <p>Carrier: <span class="font-medium text-slate-950 dark:text-white">{device.sim.carrier ?? "—"}</span></p>
                                            <p>Status: <span class="font-medium text-slate-950 dark:text-white">{device.sim.status ?? "assigned"}</span></p>
                                          </div>
                                          <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                                            {#if device.sim.roamingEnabled}
                                              <span class="rounded-full border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-cyan-700 dark:text-cyan-300">Roaming enabled</span>
                                            {/if}
                                          </div>
                                        {:else}
                                          <p class="mt-2 text-xs text-muted-foreground">No managed SIM linked to this device.</p>
                                        {/if}
                                      </div>
                                    </div>
                                    {#if device.assignmentHistory?.length}
                                      <div class="mt-3 rounded-[1rem] border border-white/70 bg-white/55 p-3 dark:border-white/10 dark:bg-white/[0.03]">
                                        <p class="text-[11px] uppercase tracking-[0.25em] text-muted-foreground">Assignment history</p>
                                        <div class="mt-2 max-h-40 overflow-auto">
                                          <table class="omni-table min-w-full text-[11px]">
                                            <thead class="text-muted-foreground">
                                              <tr>
                                                <th>Assigned</th>
                                                <th>Target</th>
                                                <th>SIM</th>
                                                <th>Technician</th>
                                                <th>Reason</th>
                                                <th>Removed</th>
                                              </tr>
                                            </thead>
                                            <tbody>
                                              {#each device.assignmentHistory as history (history.id)}
                                                <tr>
                                                  <td>{history.assignedAt ? new Date(history.assignedAt).toLocaleString() : "—"}</td>
                                                  <td>{history.assetRegistration ?? history.assetLabel ?? history.vehicleLabel ?? history.hubName ?? history.target ?? "—"}</td>
                                                  <td>{history.simIccid ?? "—"}{history.simRoamingEnabled ? " · Roaming" : ""}</td>
                                                  <td>{history.technician ?? "—"}</td>
                                                  <td>{history.notes ?? "—"}</td>
                                                  <td>{history.unassignedAt ? new Date(history.unassignedAt).toLocaleString() : history.isActive ? "Active" : "—"}</td>
                                                </tr>
                                              {/each}
                                            </tbody>
                                          </table>
                                        </div>
                                      </div>
                                    {/if}
                                  </details>
                                {/each}
                              </div>
                            {:else}
                              <p class="text-xs text-muted-foreground">No active devices are currently assigned to this asset.</p>
                            {/if}
                          </div>

                          <div class="rounded-[1.2rem] border border-white/70 bg-white/65 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                            <div class="flex items-center justify-between gap-2">
                              <p class="text-xs uppercase tracking-[0.28em] text-muted-foreground">Latest activity</p>
                              <span class="text-xs text-muted-foreground">{latestAssetActivity(selectedAssetDetail).length} recent event(s)</span>
                            </div>
                            {#if latestAssetActivity(selectedAssetDetail).length}
                              <div class="mt-3 space-y-2">
                                {#each latestAssetActivity(selectedAssetDetail) as entry (entry.id)}
                                  <div class="rounded-2xl border border-border/60 bg-background/70 px-3 py-2 text-xs text-muted-foreground">
                                    <div class="flex flex-wrap items-center justify-between gap-2">
                                      <div class="font-mono text-[11px] text-slate-950 dark:text-white">{entry.imei}</div>
                                      <span class="rounded-full border border-border/70 px-2 py-0.5 text-[10px] uppercase tracking-wide">{entry.status}</span>
                                    </div>
                                    <p class="mt-1">
                                      {entry.target} · {entry.technician}
                                    </p>
                                    <p class="mt-1 text-[11px]">{entry.note}</p>
                                    <p class="mt-1 text-[11px]">{formatDateTime(entry.when)}</p>
                                  </div>
                                {/each}
                              </div>
                            {:else}
                              <p class="mt-3 text-xs text-muted-foreground">No device or SIM events have been recorded for this asset yet.</p>
                            {/if}
                          </div>
                        </div>
                      {:else}
                        <div class="omni-empty-state py-10">
                          Select an asset to inspect its assigned devices.
                        </div>
                      {/if}
                    </div>
                  </div>
                {/if}

              </div>
            </div>

            {#if isEditingHub}
              <section class="omni-panel border-0 shadow-none">
                <div class="flex flex-wrap items-center gap-3 px-4 py-3 border-b">
                  <div>
                    <p class="marketing-pill">Edit profile</p>
                    <h5 class="mt-2 text-lg font-semibold">Hub details</h5>
                  </div>
                  <div class="flex items-center gap-2 ml-auto">
                    <Button variant="ghost" size="sm" onclick={() => (isEditingHub = false)}>
                      Cancel
                    </Button>
                    <Button size="sm" onclick={saveHubChanges} disabled={isSavingEdit}>
                      {isSavingEdit ? "Saving..." : "Save changes"}
                    </Button>
                  </div>
                </div>

                {#if statusMessage}
                  <div
                    class={`mx-4 mt-3 rounded-md border px-3 py-2 text-sm ${
                      statusMessage.type === "success"
                        ? "border-emerald-500/60 bg-emerald-50 text-emerald-800"
                        : "border-destructive/60 bg-destructive/10 text-destructive"
                    }`}
                  >
                    {statusMessage.text}
                  </div>
                {/if}

                <div class="grid gap-4 px-4 py-4 md:grid-cols-2">
                  <label class="text-sm">
                    Name
                    <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.name} />
                  </label>
                  <label class="text-sm">
                    Plan
                    <select class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.tier}>
                      <option value="Individual">Individual</option>
                      <option value="Business">Business</option>
                    </select>
                  </label>
                  <label class="text-sm">
                    Status
                    <select class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.status}>
                      <option value="active">Active</option>
                      <option value="provisioning">Provisioning</option>
                      <option value="suspended">Suspended</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </label>
                  <label class="text-sm">
                    Billing cycle
                    <select class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.billingCycle}>
                      <option value="monthly">Monthly</option>
                    </select>
                  </label>
                  <label class="text-sm">
                    Payment method
                    <select class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.paymentMethod}>
                      <option value="manual_invoice">Manual invoice</option>
                      <option value="card_on_file">Card on file</option>
                      <option value="bank_transfer">Wire / EFT</option>
                    </select>
                  </label>
                  <label class="text-sm">
                    Currency
                    <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" bind:value={editForm.currency} />
                  </label>
                  <div class="rounded-[1.2rem] border border-white/70 bg-white/65 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                    <p class="text-xs uppercase tracking-wide text-muted-foreground">Primary contact</p>
                    <div class="mt-3 space-y-2">
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Name" bind:value={editForm.primaryContact.name} />
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" type="email" placeholder="Email" bind:value={editForm.primaryContact.email} />
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Phone" bind:value={editForm.primaryContact.phone} />
                    </div>
                  </div>
                  <div class="rounded-[1.2rem] border border-white/70 bg-white/65 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                    <p class="text-xs uppercase tracking-wide text-muted-foreground">Billing contact</p>
                    <div class="mt-3 space-y-2">
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Name" bind:value={editForm.billingContact.name} />
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" type="email" placeholder="Email" bind:value={editForm.billingContact.email} />
                      <input class="w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Phone" bind:value={editForm.billingContact.phone} />
                    </div>
                  </div>
                  <div class="grid grid-cols-1 gap-4 md:col-span-2 md:grid-cols-3">
                    <label class="text-sm">
                      City
                      <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="City" bind:value={editForm.city} />
                    </label>
                    <label class="text-sm">
                      Country
                      <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Country" bind:value={editForm.country} />
                    </label>
                    <label class="text-sm">
                      Timezone
                      <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Timezone" bind:value={editForm.timezone} />
                    </label>
                  </div>
                  <label class="text-sm md:col-span-2">
                    Address
                    <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Street address" bind:value={editForm.address} />
                  </label>
                  <label class="text-sm">
                    Go-live date
                    <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" type="date" bind:value={editForm.goLiveDate} />
                  </label>
                  <label class="text-sm">
                    Type
                    <input class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" placeholder="Type" bind:value={editForm.type} />
                  </label>
                  <label class="text-sm md:col-span-2">
                    Notes
                    <textarea class="mt-2 w-full rounded-xl border border-border/70 bg-background/80 px-3 py-2" rows="4" bind:value={editForm.notes}></textarea>
                  </label>
                </div>
              </section>
            {/if}
          </section>
          {:else}
            <div class="omni-empty-state">
              Select a hub from the register to open the full hub view, edit its details, and inspect its assets.
            </div>
          {/if}
        </div>
      </div>
    </section>
  {/if}
</section>
