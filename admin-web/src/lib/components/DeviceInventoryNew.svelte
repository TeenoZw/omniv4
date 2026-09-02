<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { sessionStore } from "$lib/stores/session";
  import {
    fetchDeviceInventory,
    HARDWARE_STATUS_META,
    updateDevice as updateDeviceApi,
    deleteDevice as deleteDeviceApi,
    assignDevice as assignDeviceApi,
    recallDevice as recallDeviceApi,
    reassignDevice as reassignDeviceApi,
  } from "$lib/api/devices";
  import { fetchHubAssetOptions } from "$lib/api/hubs";
  import SimpleInventoryTable from "./device-inventory/simple-table.svelte";
  import type { Device } from "./device-inventory/columns";
  import { Button } from "$lib/components/ui/button/index.js";
  import { confirmAndRun, confirmSave, resetFocusAfterSave } from "$lib/utils/confirm-save";
  import { toastStore } from "$lib/stores/toast";
  import { RefreshCw } from "lucide-svelte";
  import { changeLogStore } from "$lib/stores/change-log";
  import type { ChangeLogEntry } from "$lib/stores/change-log";
  import { workspaceNavStore } from "$lib/stores/workspace-nav";
  export let mode: "inventory" | "assignment" = "inventory";

  type SessionUser = { email?: string | null; name?: string | null } | null;
  type Session = {
    currentHubId?: string | null;
    currentHub?: { id: string; name?: string | null; code?: string | null } | null;
    hubs?: Array<{ id: string; name?: string | null; code?: string | null }>;
    roles?: Array<string | null | undefined>;
    user?: SessionUser;
    expiresAt?: number | null;
  } | null;

  type Feedback = {
    kind: "success" | "error";
    text: string;
  };

  type SortOption = "imei-asc" | "imei-desc" | "status" | "purchase-desc" | "purchase-asc";

  const DEFAULT_EDIT_DRAFT = {
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

  const SORT_OPTIONS: Array<{ value: SortOption; label: string }> = [
    { value: "imei-asc", label: "IMEI A → Z" },
    { value: "imei-desc", label: "IMEI Z → A" },
    { value: "status", label: "Status (workflow order)" },
    { value: "purchase-desc", label: "Purchase date (newest)" },
    { value: "purchase-asc", label: "Purchase date (oldest)" },
  ];
  const ASSET_TYPE_OPTIONS = [
    "vehicle",
    "trailer",
    "equipment",
    "generator",
    "tank",
    "other",
  ];
  const ASSET_PROFILE_BEGIN = "[asset-profile]";
  const ASSET_PROFILE_END = "[/asset-profile]";
  const STATUS_SORT_INDEX = HARDWARE_STATUS_META.reduce<Record<string, number>>((acc, item, index) => {
    acc[item.id] = index;
    return acc;
  }, {});

  function formatDateForInput(value: string | null | undefined) {
    if (!value) {
      return "";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "";
    }
    return date.toISOString().slice(0, 10);
  }

  function formatDateDisplay(value: string | null | undefined) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleDateString();
  }

  function formatDateTimeDisplay(value: string | null | undefined) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  }

  function formatFreeText(value: string | null | undefined) {
    if (!value) {
      return "—";
    }
    const trimmed = value.trim();
    return trimmed.length ? trimmed : "—";
  }

  function normalizeTextInput(value: string | null | undefined) {
    if (value === undefined || value === null) {
      return null;
    }
    const trimmed = value.trim();
    return trimmed.length ? trimmed : null;
  }

  function formatAssetTypeLabel(value: string | null | undefined) {
    if (!value) return "Unspecified";
    const normalized = value.trim().replace(/[_-]+/g, " ");
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
  }

  function isUuidLike(value: string | null | undefined) {
    if (!value) return false;
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
  }

  function toApiErrorMessage(error: unknown, fallback: string) {
    const detail =
      (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
    if (typeof detail === "string" && detail.trim().length > 0) {
      return detail;
    }
    return fallback;
  }

  function parseAssetProfile(notes: string | null | undefined) {
    const raw = notes ?? "";
    const begin = raw.indexOf(ASSET_PROFILE_BEGIN);
    const end = raw.indexOf(ASSET_PROFILE_END);
    const profile = {
      assetType: "",
      assetName: "",
      vehicleMake: "",
      vehicleModel: "",
      vehicleYear: "",
      engineCapacity: "",
      vin: "",
      freeNotes: raw,
    };
    if (begin === -1 || end === -1 || end <= begin) {
      return profile;
    }
    const block = raw.slice(begin + ASSET_PROFILE_BEGIN.length, end).trim();
    const freeNotes = `${raw.slice(0, begin)}${raw.slice(end + ASSET_PROFILE_END.length)}`.trim();
    for (const line of block.split("\n")) {
      const [rawKey, ...rawRest] = line.split(":");
      const key = rawKey?.trim();
      const value = rawRest.join(":").trim();
      if (!key || !value) continue;
      if (key === "type") profile.assetType = value;
      if (key === "name") profile.assetName = value;
      if (key === "make") profile.vehicleMake = value;
      if (key === "model") profile.vehicleModel = value;
      if (key === "year") profile.vehicleYear = value;
      if (key === "engine_capacity") profile.engineCapacity = value;
      if (key === "vin") profile.vin = value;
    }
    profile.freeNotes = freeNotes;
    return profile;
  }

  function purchaseDateToIso(value: string | null | undefined) {
    if (!value) {
      return null;
    }
    const date = new Date(`${value}T00:00:00Z`);
    if (Number.isNaN(date.getTime())) {
      return null;
    }
    return date.toISOString();
  }

  function localDateTimeToIso(value: string | null | undefined) {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return date.toISOString();
  }

  function toNumericOrNull(value: string | null | undefined) {
    if (!value) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function compareStrings(a: string | null | undefined, b: string | null | undefined) {
    return (a ?? "").localeCompare(b ?? "", undefined, { numeric: true, sensitivity: "base" });
  }

  function getStatusIndex(status: string | null | undefined) {
    if (!status) {
      return Number.MAX_SAFE_INTEGER;
    }
    return STATUS_SORT_INDEX[status] ?? Number.MAX_SAFE_INTEGER;
  }

  function parseTimestamp(value: string | null | undefined) {
    if (!value) {
      return null;
    }
    const time = new Date(value).getTime();
    return Number.isNaN(time) ? null : time;
  }

  function applySort(list: Device[], sortKey: SortOption = sortOption) {
    const next = [...list];
    next.sort((a, b) => {
      switch (sortKey) {
        case "imei-desc":
          return compareStrings(b.imei, a.imei);
        case "status": {
          const diff = getStatusIndex(a.status) - getStatusIndex(b.status);
          return diff === 0 ? compareStrings(a.imei, b.imei) : diff;
        }
        case "purchase-desc": {
          const left = parseTimestamp(a.purchaseDate);
          const right = parseTimestamp(b.purchaseDate);
          if (left === right) {
            return compareStrings(a.imei, b.imei);
          }
          if (left === null) {
            return 1;
          }
          if (right === null) {
            return -1;
          }
          return right - left;
        }
        case "purchase-asc": {
          const left = parseTimestamp(a.purchaseDate);
          const right = parseTimestamp(b.purchaseDate);
          if (left === right) {
            return compareStrings(a.imei, b.imei);
          }
          if (left === null) {
            return 1;
          }
          if (right === null) {
            return -1;
          }
          return left - right;
        }
        case "imei-asc":
        default:
          return compareStrings(a.imei, b.imei);
      }
    });
    return next;
  }

  let session: Session = null;
  let devices: Device[] = [];
  let isLoading = false;
  let errorMessage: string | null = null;
  let unsubscribe: (() => void) | null = null;
  let inventoryInspectorWindow: "home" | "overview" | "history" = "home";
  let assignmentInspectorWindow: "home" | "install" | "recall" | "replace" | "history" = "home";
  let releaseWorkspaceNav: (() => void) | null = null;
  let lastWorkspaceIssuedAt = 0;
  let loadToken = 0;

  let actionFeedback: Feedback | null = null;
  let editingDeviceId: string | null = null;
  let pendingDeleteId: string | null = null;
  let savingDeviceId: string | null = null;
  let deletingDeviceId: string | null = null;
  let editDraft = { ...DEFAULT_EDIT_DRAFT };
  let selectedDeviceIds: string[] = [];
  let isBulkDeleting = false;
  let searchDraft = "";
  let searchTerm = "";
  let statusFilter: string = "all";
  let simFilter: string = "all";
  let sortOption: SortOption = "imei-asc";
  let currentPage = 1;
  let perPage = 25;
  let totalItems = 0;
  let searchDebounce: ReturnType<typeof setTimeout> | null = null;
  let deviceHubFilter = "__all__";
  let assigningDeviceId: string | null = null;
  let reassigningDeviceId: string | null = null;
  let recallingDeviceId: string | null = null;
  let loadedAssetHubId = "";
  let availableAssetOptions: Array<{
    id: string;
    assetName: string | null;
    assetType: string | null;
    registration: string | null;
    make: string | null;
    model: string | null;
    year: string | null;
    engineCapacity: string | null;
    vin: string | null;
  }> = [];
  let loadingAssetOptions = false;
  let assignmentForm = {
    hubId: "",
    assignmentMode: "existing",
    targetAssetId: "",
    assetType: "vehicle",
    assetName: "",
    vehicleMake: "",
    vehicleModel: "",
    vehicleYear: "",
    engineCapacity: "",
    vin: "",
    technician: "",
    installedAt: "",
    installationLocation: "",
    installationLatitude: "",
    installationLongitude: "",
    assetRegistration: "",
    reassignmentReason: "",
    notes: "",
  };
  let recallForm = {
    status: "in_stock",
    reason: "",
    notes: "",
  };
  let replacementForm = {
    replacementHardwareId: "",
    targetAssetId: "",
    assetType: "",
    assetName: "",
    vehicleMake: "",
    vehicleModel: "",
    vehicleYear: "",
    engineCapacity: "",
    vin: "",
    technician: "",
    installedAt: "",
    installationLocation: "",
    installationLatitude: "",
    installationLongitude: "",
    assetRegistration: "",
    faultyReason: "",
    notes: "",
  };
  let seededForDeviceId: string | null = null;
  $: isInventoryMode = mode === "inventory";
  $: isAssignmentMode = mode === "assignment";
  $: normalizedRoles = (session?.roles ?? []).map((role) => `${role ?? ""}`.toLowerCase());
  $: isOmniAdmin = normalizedRoles.includes("admin");
  $: canMutateInventory = isInventoryMode && isOmniAdmin;
  $: canUseAssignmentOverrides = isAssignmentMode && isOmniAdmin;
  $: canSelectRows = isAssignmentMode || canMutateInventory;
  $: pageTitle = isAssignmentMode ? "Device Assignment" : "Device Register";
  $: pageDescription = isAssignmentMode
    ? "Assign and replace devices with full installation traceability."
    : "Review all managed devices, their deployment context, and the SIM state attached to each unit.";
  $: totalDevices = totalItems;
  $: availableDeviceHubs = session?.hubs ?? [];

  $: selectionCount = selectedDeviceIds.length;
  $: primarySelectedDeviceId = selectionCount === 1 ? selectedDeviceIds[0] : null;
  $: primarySelectedDevice = primarySelectedDeviceId
    ? devices.find((device) => device.id === primarySelectedDeviceId)
    : null;
  $: inventoryInspectorWindow = primarySelectedDevice ? inventoryInspectorWindow : "home";
  $: assignmentInspectorWindow = primarySelectedDevice ? assignmentInspectorWindow : "home";
  $: canEditSelection = selectionCount === 1;
  $: editActionDisabled =
    !canEditSelection ||
    !primarySelectedDeviceId ||
    (editingDeviceId !== null && editingDeviceId !== primarySelectedDeviceId);
  $: hasActiveFilters = Boolean(searchTerm) || statusFilter !== "all" || simFilter !== "all";
  $: canResetFilters = hasActiveFilters || Boolean(searchDraft);
  $: availableReplacementDevices = devices.filter(
    (device) =>
      device.status === "in_stock" &&
      !device.assignment &&
      (!primarySelectedDevice || device.id !== primarySelectedDevice.id),
  );
  $: availableHubOptions = session?.hubs ?? [];
  $: selectedAssignmentAsset =
    assignmentForm.targetAssetId
      ? availableAssetOptions.find((asset) => asset.id === assignmentForm.targetAssetId) ?? null
      : null;
  $: selectedReplacementAsset =
    replacementForm.targetAssetId
      ? availableAssetOptions.find((asset) => asset.id === replacementForm.targetAssetId) ?? null
      : null;
  $: if (primarySelectedDevice && seededForDeviceId !== primarySelectedDevice.id) {
    seedAssignmentForms(primarySelectedDevice);
    seededForDeviceId = primarySelectedDevice.id;
  }
  $: if (!primarySelectedDevice && seededForDeviceId !== null) {
    seededForDeviceId = null;
  }
  $: if (isAssignmentMode && assignmentForm.hubId && assignmentForm.hubId !== loadedAssetHubId) {
    void loadHubAssetOptions(assignmentForm.hubId);
  } else if (isAssignmentMode && !assignmentForm.hubId && availableAssetOptions.length) {
    availableAssetOptions = [];
    loadedAssetHubId = "";
  }
  $: if (!canSelectRows && selectedDeviceIds.length) {
    selectedDeviceIds = [];
  }

  onDestroy(() => {
    releaseWorkspaceNav?.();
    clearSearchTimer();
  });

  $: if (session) {
    const preferredHub = session.currentHubId ?? "__all__";
    if (isOmniAdmin) {
      if (!deviceHubFilter || !availableDeviceHubs.some((hub) => hub.id === deviceHubFilter)) {
        deviceHubFilter = "__all__";
      }
    } else if (deviceHubFilter !== preferredHub) {
      deviceHubFilter = preferredHub;
    }
  }

  async function loadDevices() {
    if (!session) {
      devices = [];
      selectedDeviceIds = [];
      errorMessage = null;
      return;
    }

    const hubHeader =
      isOmniAdmin
        ? deviceHubFilter === "__all__"
          ? null
          : deviceHubFilter
        : session.currentHubId ?? session.hubs?.[0]?.id ?? null;
    const token = ++loadToken;
    isLoading = true;
    errorMessage = null;

    try {
      const query: Record<string, string> = {};
      if (statusFilter !== "all") {
        query.status = statusFilter;
      }
      if (simFilter !== "all") {
        query.simFilter = simFilter;
      }
      if (searchTerm) {
        query.search = searchTerm;
      }
      query.page = String(currentPage);
      query.limit = String(perPage);
      const result = await fetchDeviceInventory({
        ...query,
        hubHeader,
      });
      if (token !== loadToken) {
        return;
      }
      const fetchedDevices = (result?.items ?? []) as Device[];
      const sortedDevices = applySort(fetchedDevices);
      devices = sortedDevices;
      totalItems = Number(result?.meta?.total ?? sortedDevices.length);
      selectedDeviceIds = selectedDeviceIds.filter((id) => sortedDevices.some((device) => device.id === id));
    } catch (error) {
      console.error("Error loading devices:", error);
      if (token === loadToken) {
        const status =
          typeof error === "object" && error !== null && "response" in error
            ? (error as { response?: { status?: number } }).response?.status
            : undefined;
        const isUnauthorized = status === 401;
        errorMessage = isUnauthorized
          ? "Session expired. Redirecting to login."
          : "Failed to load devices";
        devices = [];
        totalItems = 0;
        selectedDeviceIds = [];
        if (isUnauthorized) {
          sessionStore.forceExpiryCountdown();
        }
      }
    } finally {
      if (token === loadToken) {
        isLoading = false;
      }
    }

  }

  function handleRefresh() {
    void loadDevices();
  }

  function clearSearchTimer() {
    if (searchDebounce) {
      clearTimeout(searchDebounce);
      searchDebounce = null;
    }
  }

  function scheduleSearch(value: string) {
    clearSearchTimer();
    searchDebounce = setTimeout(() => {
      searchTerm = value.trim();
      void loadDevices();
    }, 400);
  }

  function handleSearchInput(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    searchDraft = value;
    currentPage = 1;
    scheduleSearch(value);
  }

  function handleSearchKey(event: KeyboardEvent) {
    if (event.key !== "Enter") {
      return;
    }
    clearSearchTimer();
    currentPage = 1;
    searchTerm = searchDraft.trim();
    void loadDevices();
  }

  function handleStatusFilterChange(event: Event) {
    statusFilter = (event.target as HTMLSelectElement).value;
    currentPage = 1;
    void loadDevices();
  }

  function handleHubFilterChange(event: Event) {
    deviceHubFilter = (event.target as HTMLSelectElement).value;
    currentPage = 1;
    void loadDevices();
  }

  function handleSortChange(event: Event) {
    const value = (event.target as HTMLSelectElement).value as SortOption;
    sortOption = value;
    devices = applySort(devices, value);
  }

  function handleSimFilterChange(event: Event) {
    simFilter = (event.target as HTMLSelectElement).value;
    currentPage = 1;
    void loadDevices();
  }

  function resetFilters() {
    searchDraft = "";
    searchTerm = "";
    statusFilter = "all";
    simFilter = "all";
    if (isOmniAdmin) {
      deviceHubFilter = "__all__";
    }
    currentPage = 1;
    clearSearchTimer();
    void loadDevices();
  }

  function handlePageChange(event: CustomEvent<{ page: number }>) {
    const nextPage = event.detail.page;
    if (!nextPage || nextPage === currentPage) {
      return;
    }
    currentPage = nextPage;
    void loadDevices();
  }

  function setFeedback(kind: Feedback["kind"], text: string) {
    actionFeedback = { kind, text };
    if (kind === "success") {
      setTimeout(() => {
        actionFeedback = null;
      }, 4000);
    }
  }

  function deriveActor() {
    return session?.user?.name ?? session?.user?.email ?? "Unknown operator";
  }

  function formatStatusLabel(value: string | null | undefined) {
    if (!value) {
      return "Unspecified";
    }
    return HARDWARE_STATUS_META.find((item) => item.id === value)?.label ?? value;
  }

  function formatDeviceLocation(device: Device) {
    return device.assignment?.hubName ?? session?.currentHub?.name ?? "Unassigned";
  }

  function formatAssignedAsset(device: Device) {
    return device.assignment?.assetLabel ?? device.assignment?.assetRegistration ?? device.assignment?.target ?? "Not assigned";
  }

  function formatSimSummary(device: Device) {
    if (!device.sim) return "No managed SIM linked";
    return [device.sim.iccid, device.sim.msisdn, device.sim.carrier].filter(Boolean).join(" · ");
  }

  function inspectDevice(deviceId: string) {
    selectedDeviceIds = [deviceId];
    inventoryInspectorWindow = "home";
    assignmentInspectorWindow = "home";
    if (editingDeviceId && editingDeviceId !== deviceId) {
      cancelEdit();
    }
    if (pendingDeleteId && pendingDeleteId !== deviceId) {
      cancelDelete();
    }
  }

  function buildChangeDetails(before: Device, after: Device) {
    const comparisons = [
      {
        label: "Status",
        before: before.status,
        after: after.status,
        formatter: (value: string | null | undefined) => formatStatusLabel(value ?? ""),
      },
      { label: "Firmware", before: before.firmwareVersion, after: after.firmwareVersion },
      { label: "Hardware type", before: before.hardwareType, after: after.hardwareType },
      { label: "Model", before: before.model, after: after.model },
      { label: "Manufacturer", before: before.manufacturer, after: after.manufacturer },
      { label: "Serial #", before: before.serialNumber, after: after.serialNumber },
      {
        label: "Purchase date",
        before: before.purchaseDate,
        after: after.purchaseDate,
        formatter: formatDateDisplay,
      },
      {
        label: "Notes",
        before: before.notes,
        after: after.notes,
        formatter: (value: string | null | undefined) =>
          value && value.trim().length ? value.trim() : "—",
      },
    ];

    const messages = comparisons
      .map(({ label, before: beforeValue, after: afterValue, formatter }) => {
        const left = `${beforeValue ?? ""}`;
        const right = `${afterValue ?? ""}`;
        if (left === right) {
          return null;
        }
        const format = formatter ?? formatFreeText;
        return `${label} ${format(beforeValue)} → ${format(afterValue)}`;
      })
      .filter((entry): entry is string => Boolean(entry));

    return messages.length ? messages.join(" · ") : "Fields saved without detectable changes.";
  }

  function recordChange(entry: Pick<ChangeLogEntry, "action" | "summary" | "details" | "deviceIds">) {
    const logEntry: ChangeLogEntry = {
      id: globalThis.crypto?.randomUUID?.() ?? `log-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      timestamp: new Date().toISOString(),
      actor: deriveActor(),
      ...entry,
    };
    changeLogStore.addEntry(logEntry);
  }

  function beginEditing(device: Device) {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can edit hardware details.");
      return;
    }
    editingDeviceId = device.id;
    updateSelectedIds((set) => {
      set.add(device.id);
    });
    editDraft = {
      imei: device.imei ?? "",
      status: device.status ?? "in_stock",
      firmwareVersion: device.firmwareVersion ?? "",
      hardwareType: device.hardwareType ?? "",
      model: device.model ?? "",
      manufacturer: device.manufacturer ?? "",
      serialNumber: device.serialNumber ?? "",
      purchaseDate: formatDateForInput(device.purchaseDate ?? null),
      notes: device.notes ?? "",
    };
  }

  async function loadHubAssetOptions(hubId: string) {
    if (!hubId) {
      availableAssetOptions = [];
      loadedAssetHubId = "";
      return;
    }
    loadingAssetOptions = true;
    try {
      const response = await fetchHubAssetOptions(hubId, { page: 1, limit: 100 });
      availableAssetOptions = (response?.items ?? [])
        .filter((asset) => isUuidLike(asset.id))
        .map((asset) => ({
        id: asset.id,
        assetName: asset.assetName ?? asset.label ?? "",
        assetType: asset.assetType ?? "other",
        registration: asset.registration ?? "",
        make: asset.make ?? "",
        model: asset.model ?? "",
        year: asset.year ?? "",
        engineCapacity: asset.engineCapacity ?? "",
        vin: asset.vin ?? "",
      }));
      loadedAssetHubId = hubId;
    } catch (error) {
      console.error("Failed to load hub assets", error);
      availableAssetOptions = [];
      loadedAssetHubId = "";
      setFeedback("error", "Unable to load hub assets for reassignment.");
    } finally {
      loadingAssetOptions = false;
    }
  }

  function applyAssetSelectionToAssignment(assetId: string) {
    const selectedAsset = availableAssetOptions.find((asset) => asset.id === assetId);
    if (!selectedAsset) {
      assignmentForm = {
        ...assignmentForm,
        assignmentMode: "existing",
        targetAssetId: "",
      };
      return;
    }
    assignmentForm = {
      ...assignmentForm,
      assignmentMode: "existing",
      targetAssetId: assetId,
      assetType: selectedAsset?.assetType || assignmentForm.assetType,
      assetName: selectedAsset?.assetName || assignmentForm.assetName,
      vehicleMake: selectedAsset?.make || assignmentForm.vehicleMake,
      vehicleModel: selectedAsset?.model || assignmentForm.vehicleModel,
      vehicleYear: selectedAsset?.year || assignmentForm.vehicleYear,
      engineCapacity: selectedAsset?.engineCapacity || assignmentForm.engineCapacity,
      vin: selectedAsset?.vin || assignmentForm.vin,
      assetRegistration: selectedAsset?.registration || assignmentForm.assetRegistration,
    };
  }

  function applyAssetSelectionToReplacement(assetId: string) {
    const selectedAsset = availableAssetOptions.find((asset) => asset.id === assetId);
    replacementForm = {
      ...replacementForm,
      targetAssetId: assetId,
      assetType: selectedAsset?.assetType || replacementForm.assetType,
      assetName: selectedAsset?.assetName || replacementForm.assetName,
      vehicleMake: selectedAsset?.make || replacementForm.vehicleMake,
      vehicleModel: selectedAsset?.model || replacementForm.vehicleModel,
      vehicleYear: selectedAsset?.year || replacementForm.vehicleYear,
      engineCapacity: selectedAsset?.engineCapacity || replacementForm.engineCapacity,
      vin: selectedAsset?.vin || replacementForm.vin,
      assetRegistration: selectedAsset?.registration || replacementForm.assetRegistration,
    };
  }

  function seedAssignmentForms(device: Device) {
    const currentHubId = session?.currentHubId ?? session?.hubs?.[0]?.id ?? "";
    const parsedProfile = parseAssetProfile(device.assignment?.notes ?? "");
    assignmentForm = {
      hubId: device.assignment?.hubId ?? currentHubId,
      assignmentMode: device.assignment?.vehicleId ? "existing" : "new",
      targetAssetId: device.assignment?.vehicleId ?? "",
      assetType: parsedProfile.assetType || "vehicle",
      assetName: parsedProfile.assetName || device.assignment?.assetLabel || "",
      vehicleMake: parsedProfile.vehicleMake || "",
      vehicleModel: parsedProfile.vehicleModel || "",
      vehicleYear: parsedProfile.vehicleYear || "",
      engineCapacity: parsedProfile.engineCapacity || "",
      vin: parsedProfile.vin || "",
      technician: device.assignment?.technician ?? "",
      installedAt: "",
      installationLocation: device.assignment?.installationLocation ?? "",
      installationLatitude:
        device.assignment?.installationLatitude !== null &&
        device.assignment?.installationLatitude !== undefined
          ? String(device.assignment.installationLatitude)
          : "",
      installationLongitude:
        device.assignment?.installationLongitude !== null &&
        device.assignment?.installationLongitude !== undefined
          ? String(device.assignment.installationLongitude)
          : "",
      assetRegistration: device.assignment?.assetRegistration ?? "",
      reassignmentReason: "",
      notes: parsedProfile.freeNotes ?? "",
    };
    recallForm = {
      status: "in_stock",
      reason: "",
      notes: "",
    };
    replacementForm = {
      replacementHardwareId: "",
      targetAssetId: device.assignment?.vehicleId ?? "",
      assetType: parsedProfile.assetType || "",
      assetName: parsedProfile.assetName || device.assignment?.assetLabel || "",
      vehicleMake: parsedProfile.vehicleMake || "",
      vehicleModel: parsedProfile.vehicleModel || "",
      vehicleYear: parsedProfile.vehicleYear || "",
      engineCapacity: parsedProfile.engineCapacity || "",
      vin: parsedProfile.vin || "",
      technician: device.assignment?.technician ?? "",
      installedAt: "",
      installationLocation: device.assignment?.installationLocation ?? "",
      installationLatitude:
        device.assignment?.installationLatitude !== null &&
        device.assignment?.installationLatitude !== undefined
          ? String(device.assignment.installationLatitude)
          : "",
      installationLongitude:
        device.assignment?.installationLongitude !== null &&
        device.assignment?.installationLongitude !== undefined
          ? String(device.assignment.installationLongitude)
          : "",
      assetRegistration: device.assignment?.assetRegistration ?? "",
      faultyReason: "",
      notes: parsedProfile.freeNotes ?? "",
    };
  }


  function cancelEdit() {
    editingDeviceId = null;
    editDraft = { ...DEFAULT_EDIT_DRAFT };
  }

  function handleDraftChange(
    event: CustomEvent<{
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
    }>,
  ) {
    const { field, value } = event.detail;
    editDraft = { ...editDraft, [field]: value };
  }

  async function saveEdit(event: CustomEvent<{ deviceId: string }>) {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can edit hardware details.");
      return;
    }
    const { deviceId } = event.detail;
    const original = devices.find((device) => device.id === deviceId);
    if (!original) {
      setFeedback("error", "Device could not be found.");
      return;
    }
    savingDeviceId = deviceId;
    try {
      const payload = {
        imei: editDraft.imei?.trim() || undefined,
        status: editDraft.status,
        firmware_version: normalizeTextInput(editDraft.firmwareVersion),
        hardware_type: normalizeTextInput(editDraft.hardwareType),
        model: normalizeTextInput(editDraft.model),
        manufacturer: normalizeTextInput(editDraft.manufacturer),
        serial_number: normalizeTextInput(editDraft.serialNumber),
        purchase_date: purchaseDateToIso(editDraft.purchaseDate),
        notes: normalizeTextInput(editDraft.notes),
      };
      const updated = (await updateDeviceApi(deviceId, payload)) as Device | undefined;
      if (updated) {
        const updatedDevices = devices.map((device) => (device.id === updated.id ? updated : device));
        devices = applySort(updatedDevices);
        recordChange({
          action: "update",
          summary: `Updated ${updated.imei ?? updated.id}`,
          details: buildChangeDetails(original, updated),
          deviceIds: [deviceId],
        });
        setFeedback("success", "Device updated successfully.");
        toastStore.push({ title: "Device updated", message: `${updated.imei ?? updated.id} saved successfully.`, tone: "success" });
      }
      editingDeviceId = null;
      editDraft = { ...DEFAULT_EDIT_DRAFT };
    } catch (error) {
      console.error("Failed to update device", error);
      setFeedback("error", "Unable to save device changes.");
    } finally {
      savingDeviceId = null;
    }
  }

  function cancelDelete() {
    pendingDeleteId = null;
    deletingDeviceId = null;
  }

  async function confirmDelete(event: CustomEvent<{ deviceId: string }>) {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can delete hardware.");
      return;
    }
    const { deviceId } = event.detail;
    const target = devices.find((device) => device.id === deviceId);
    if (!target) {
      setFeedback("error", "Device could not be found.");
      return;
    }
    deletingDeviceId = deviceId;
    try {
      await deleteDeviceApi(deviceId);
      const remainingDevices = devices.filter((device) => device.id !== deviceId);
      devices = applySort(remainingDevices);
      selectedDeviceIds = selectedDeviceIds.filter((id) => id !== deviceId);
      recordChange({
        action: "delete",
        summary: `Deleted ${target.imei ?? target.id}`,
        details: `Removed from ${session?.currentHub?.name ?? "inventory"}. Operation recorded for audit.`,
        deviceIds: [deviceId],
      });
      setFeedback("success", "Device removed from inventory.");
      toastStore.push({ title: "Device deleted", message: `${target.imei ?? target.id} was removed from inventory.`, tone: "success" });
    } catch (error) {
      console.error("Failed to delete device", error);
      setFeedback("error", "Unable to delete device.");
    } finally {
      deletingDeviceId = null;
      pendingDeleteId = null;
    }
  }

  function updateSelectedIds(mutator: (set: Set<string>) => void) {
    const next = new Set(selectedDeviceIds);
    mutator(next);
    selectedDeviceIds = Array.from(next);
  }

  function handleSelectToggle(event: CustomEvent<{ deviceId: string; selected: boolean }>) {
    if (!canSelectRows) return;
    const { deviceId, selected } = event.detail;
    updateSelectedIds((set) => {
      if (selected) {
        set.add(deviceId);
      } else {
        set.delete(deviceId);
      }
    });
    if (!selected) {
      if (editingDeviceId === deviceId) {
        cancelEdit();
      }
      if (pendingDeleteId === deviceId) {
        cancelDelete();
      }
    }
  }

  function handleSelectAll(event: CustomEvent<{ deviceIds: string[]; selected: boolean }>) {
    if (!canSelectRows) return;
    const { deviceIds, selected } = event.detail;
    updateSelectedIds((set) => {
      if (selected) {
        deviceIds.forEach((id) => set.add(id));
      } else {
        deviceIds.forEach((id) => set.delete(id));
      }
    });
    if (!selected) {
      if (editingDeviceId && !selectedDeviceIds.includes(editingDeviceId)) {
        cancelEdit();
      }
      if (pendingDeleteId && !selectedDeviceIds.includes(pendingDeleteId)) {
        cancelDelete();
      }
    }
  }

  function clearSelection() {
    selectedDeviceIds = [];
    cancelEdit();
    cancelDelete();
  }

  function editSelectedDevice() {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can edit hardware details.");
      return;
    }
    if (!canEditSelection || !primarySelectedDevice) {
      setFeedback("error", "Select a single device to edit.");
      return;
    }
    beginEditing(primarySelectedDevice);
  }

  async function performBulkDelete(deviceIds: string[]) {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can delete hardware.");
      return;
    }
    if (!deviceIds.length) {
      return;
    }

    isBulkDeleting = true;
    const successes: string[] = [];
    const failures: string[] = [];

    for (const deviceId of deviceIds) {
      try {
        await deleteDeviceApi(deviceId);
        successes.push(deviceId);
      } catch (error) {
        console.error(`Failed deleting device ${deviceId}`, error);
        failures.push(deviceId);
      }
    }

    if (successes.length) {
      const remainingDevices = devices.filter((device) => !successes.includes(device.id));
      devices = applySort(remainingDevices);
      selectedDeviceIds = selectedDeviceIds.filter((id) => !successes.includes(id));
      recordChange({
        action: successes.length === 1 ? "delete" : "bulk-delete",
        summary: `Deleted ${successes.length} device${successes.length === 1 ? "" : "s"}`,
        details: failures.length
          ? `${failures.length} device${failures.length === 1 ? "" : "s"} failed`
          : `Removed from ${session?.currentHub?.name ?? "inventory"}`,
        deviceIds: successes,
      });
      setFeedback(
        failures.length ? "error" : "success",
        failures.length
          ? `${failures.length} device${failures.length === 1 ? "" : "s"} failed to delete.`
          : `${successes.length} device${successes.length === 1 ? "" : "s"} deleted.`,
      );
    } else if (failures.length) {
      setFeedback("error", "Unable to delete the selected devices.");
    }

    isBulkDeleting = false;
  }

  async function deleteSelectedDevices() {
    if (!canMutateInventory) {
      setFeedback("error", "Only admins can delete hardware.");
      return;
    }
    if (selectionCount === 0) {
      setFeedback("error", "Select at least one device.");
      return;
    }

    if (selectionCount === 1 && primarySelectedDevice) {
      pendingDeleteId = primarySelectedDevice.id;
      return;
    }

    await confirmAndRun(
      {
        title: "Delete devices",
        description: "Inventory",
        message: `Delete ${selectionCount} selected device${selectionCount === 1 ? "" : "s"}?`,
        confirmLabel: "Delete devices",
        tone: "destructive",
      },
      async () => {
        await performBulkDelete([...selectedDeviceIds]);
      },
    );
  }

  async function assignSelectedDevice() {
    if (!canUseAssignmentOverrides) {
      setFeedback("error", "Only admins can run manual assignment overrides.");
      return;
    }
    if (!primarySelectedDevice) {
      setFeedback("error", "Select one device to assign.");
      return;
    }
    if (!assignmentForm.hubId) {
      setFeedback("error", "Select a hub for assignment.");
      return;
    }
    if (assignmentForm.assignmentMode === "existing") {
      if (!assignmentForm.targetAssetId) {
        setFeedback("error", "Select an existing asset to continue.");
        return;
      }
    } else if (!assignmentForm.assetType.trim() || !assignmentForm.assetName.trim()) {
      setFeedback("error", "Asset type and asset name are required.");
      return;
    }
    const movingAssignedDevice = Boolean(
      primarySelectedDevice.assignment &&
      (
        primarySelectedDevice.assignment?.hubId !== assignmentForm.hubId ||
        (assignmentForm.targetAssetId
          ? primarySelectedDevice.assignment?.vehicleId !== assignmentForm.targetAssetId
          : primarySelectedDevice.assignment?.assetRegistration !== assignmentForm.assetRegistration ||
            primarySelectedDevice.assignment?.assetLabel !== assignmentForm.assetName)
      ),
    );
    if (movingAssignedDevice && !assignmentForm.reassignmentReason.trim()) {
      setFeedback("error", "A reassignment reason is required when moving hardware to another asset.");
      return;
    }
    await confirmAndRun(
      {
        title: movingAssignedDevice ? "Reassign device" : "Save assignment",
        description: "Inventory",
        message: movingAssignedDevice ? "Move this device to the selected asset?" : "Save this device assignment?",
        confirmLabel: movingAssignedDevice ? "Reassign device" : "Save assignment",
      },
      async () => {
        assigningDeviceId = primarySelectedDevice.id;
        try {
          const updated = (await assignDeviceApi(primarySelectedDevice.id, {
            hubId: assignmentForm.hubId,
            vehicleId: assignmentForm.assignmentMode === "existing" ? assignmentForm.targetAssetId || undefined : undefined,
            assetType: assignmentForm.assetType,
            assetName: assignmentForm.assetName,
            vehicleMake: assignmentForm.vehicleMake || undefined,
            vehicleModel: assignmentForm.vehicleModel || undefined,
            vehicleYear: assignmentForm.vehicleYear || undefined,
            engineCapacity: assignmentForm.engineCapacity || undefined,
            vin: assignmentForm.vin || undefined,
            technician: assignmentForm.technician || undefined,
            installedAt: localDateTimeToIso(assignmentForm.installedAt),
            installationLocation: assignmentForm.installationLocation || undefined,
            installationLatitude: toNumericOrNull(assignmentForm.installationLatitude),
            installationLongitude: toNumericOrNull(assignmentForm.installationLongitude),
            assetRegistration: assignmentForm.assetRegistration || undefined,
            reassignmentReason: assignmentForm.reassignmentReason || undefined,
            notes: assignmentForm.notes || undefined,
          })) as Device | undefined;

          if (updated) {
            devices = applySort(devices.map((device) => (device.id === updated.id ? updated : device)));
            recordChange({
              action: "update",
              summary: `${movingAssignedDevice ? "Reassigned" : "Assigned"} ${updated.imei ?? updated.id}`,
              details: `${movingAssignedDevice ? "Moved to" : "Assigned to"} ${updated.assignment?.hubName ?? "hub"} · asset ${updated.assignment?.assetRegistration ?? updated.assignment?.assetLabel ?? "unlabelled"}`,
              deviceIds: [updated.id],
            });
            setFeedback("success", movingAssignedDevice ? "Hardware reassigned successfully." : "Hardware assigned successfully.");
            toastStore.push({
              title: movingAssignedDevice ? "Hardware reassigned" : "Hardware assigned",
              message: `${updated.imei ?? updated.id} was ${movingAssignedDevice ? "moved" : "assigned"} successfully.`,
              tone: "success",
            });
          }
        } catch (error) {
          console.error("Failed to assign device", error);
          setFeedback("error", toApiErrorMessage(error, "Failed to assign hardware."));
        } finally {
          assigningDeviceId = null;
        }
      },
    );
  }

  async function recallSelectedDevice() {
    if (!canUseAssignmentOverrides) {
      setFeedback("error", "Only admins can recall hardware from inventory overrides.");
      return;
    }
    if (!primarySelectedDevice?.assignment) {
      setFeedback("error", "Select an assigned device to recall.");
      return;
    }
    if (!recallForm.reason.trim()) {
      setFeedback("error", "A recall reason is required.");
      return;
    }

    await confirmAndRun(
      {
        title: "Recall device",
        description: "Inventory",
        message: `Recall this hardware back into inventory as ${recallForm.status.replaceAll("_", " ")}?`,
        confirmLabel: "Recall device",
        tone: recallForm.status === "in_stock" ? "default" : "destructive",
      },
      async () => {
        recallingDeviceId = primarySelectedDevice.id;
        try {
          const updated = (await recallDeviceApi(primarySelectedDevice.id, {
            status: recallForm.status,
            reason: recallForm.reason,
            notes: recallForm.notes || undefined,
          })) as Device | undefined;

          if (updated) {
            devices = applySort(devices.map((device) => (device.id === updated.id ? updated : device)));
            recordChange({
              action: "update",
              summary: `Recalled ${updated.imei ?? updated.id}`,
              details: `Returned to inventory as ${recallForm.status.replaceAll("_", " ")}`,
              deviceIds: [updated.id],
            });
            setFeedback("success", "Hardware recalled into inventory.");
            toastStore.push({
              title: "Hardware recalled",
              message: `${updated.imei ?? updated.id} returned to inventory as ${recallForm.status.replaceAll("_", " ")}.`,
              tone: "success",
            });
          }
        } catch (error) {
          console.error("Failed to recall device", error);
          setFeedback("error", "Failed to recall hardware into inventory.");
        } finally {
          recallingDeviceId = null;
        }
      },
    );
  }

  async function replaceSelectedDevice() {
    if (!canUseAssignmentOverrides) {
      setFeedback("error", "Only admins can run replacement overrides.");
      return;
    }
    if (!primarySelectedDevice) {
      setFeedback("error", "Select one faulty device to replace.");
      return;
    }
    if (!replacementForm.replacementHardwareId) {
      setFeedback("error", "Choose a replacement hardware unit.");
      return;
    }
    if (!replacementForm.faultyReason.trim()) {
      setFeedback("error", "Fault reason is required for recall.");
      return;
    }
    if (!replacementForm.assetType.trim() || !replacementForm.assetName.trim()) {
      setFeedback("error", "Asset type and asset name are required for replacement.");
      return;
    }

    reassigningDeviceId = primarySelectedDevice.id;
    try {
      const replacement = (await reassignDeviceApi(primarySelectedDevice.id, {
        replacementHardwareId: Number(replacementForm.replacementHardwareId),
        assetType: replacementForm.assetType,
        assetName: replacementForm.assetName,
        vehicleMake: replacementForm.vehicleMake || undefined,
        vehicleModel: replacementForm.vehicleModel || undefined,
        vehicleYear: replacementForm.vehicleYear || undefined,
        engineCapacity: replacementForm.engineCapacity || undefined,
        vin: replacementForm.vin || undefined,
        technician: replacementForm.technician || undefined,
        installedAt: localDateTimeToIso(replacementForm.installedAt),
        installationLocation: replacementForm.installationLocation || undefined,
        installationLatitude: toNumericOrNull(replacementForm.installationLatitude),
        installationLongitude: toNumericOrNull(replacementForm.installationLongitude),
        assetRegistration: replacementForm.assetRegistration || undefined,
        faultyReason: replacementForm.faultyReason,
        notes: replacementForm.notes || undefined,
      })) as Device | undefined;

      if (replacement) {
        await loadDevices();
        selectedDeviceIds = [replacement.id];
        recordChange({
          action: "update",
          summary: `Reassigned replacement ${replacement.imei ?? replacement.id}`,
          details: `Replaced faulty hardware on asset ${replacement.assignment?.assetRegistration ?? replacement.assignment?.assetLabel ?? "unlabelled"}`,
          deviceIds: [primarySelectedDevice.id, replacement.id],
        });
        setFeedback("success", "Replacement completed. Faulty hardware returned to inventory as faulty.");
        toastStore.push({
          title: "Replacement completed",
          message: `${replacement.imei ?? replacement.id} is now the active assigned device.`,
          tone: "success",
        });
      }
    } catch (error) {
      console.error("Failed to replace device", error);
      setFeedback("error", "Failed to complete replacement workflow.");
    } finally {
      reassigningDeviceId = null;
    }
  }

  onMount(() => {
    unsubscribe = sessionStore.subscribe((value) => {
      const hubChanged = session?.currentHubId !== value?.currentHubId;
      session = value;

      if (session && (hubChanged || devices.length === 0)) {
        void loadDevices();
      }
    });

    releaseWorkspaceNav = workspaceNavStore.subscribe((state) => {
      if (!state?.issuedAt || state.issuedAt === lastWorkspaceIssuedAt) {
        return;
      }
      if (state.deviceSearch) {
        lastWorkspaceIssuedAt = state.issuedAt;
        searchDraft = state.deviceSearch;
        searchTerm = state.deviceSearch;
        statusFilter = "all";
        simFilter = "all";
        currentPage = 1;
        workspaceNavStore.clearDeviceFocus();
        void loadDevices();
      }
    });

    return () => {
      unsubscribe?.();
      releaseWorkspaceNav?.();
    };
  });
</script>

<section class="space-y-6">
  <section class="flex flex-wrap items-center justify-between gap-3 rounded-[1.2rem] border border-white/70 bg-white/70 px-4 py-3 shadow-sm backdrop-blur dark:border-white/10 dark:bg-slate-950/45">
    <div>
      <p class="text-[11px] uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Registry · Devices</p>
      <h2 class="mt-1 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{pageTitle}</h2>
    </div>
    <Button onclick={handleRefresh} variant="outline" disabled={isLoading}>
      <RefreshCw class={isLoading ? "mr-2 size-4 animate-spin" : "mr-2 size-4"} />
      Refresh
    </Button>
  </section>

  {#if errorMessage}
    <div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
      <p class="text-sm text-destructive">{errorMessage}</p>
    </div>
  {/if}

  {#if actionFeedback}
    <div
      class={`rounded-lg border p-3 text-sm ${
        actionFeedback.kind === "success"
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-destructive/60 bg-destructive/10 text-destructive"
      }`}
    >
      {actionFeedback.text}
    </div>
  {/if}

  {#if isInventoryMode && !canMutateInventory}
    <div class="rounded-lg border border-border/70 bg-muted/30 p-3 text-sm text-muted-foreground">
      Inventory is read-only for technician accounts.
    </div>
  {/if}

  <section class="omni-panel border-0 shadow-none px-5 py-4">
    <div class="omni-toolbar-strip">
      <label class="omni-toolbar-field flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Search devices</span>
        <input
          class="omni-input mt-1 min-w-[16rem]"
          type="search"
          placeholder="IMEI, serial, model, hub"
          value={searchDraft}
          oninput={handleSearchInput}
          onkeydown={handleSearchKey}
        />
      </label>

      <label class="omni-toolbar-field-compact flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Filter status</span>
        <select
          class="omni-select mt-1 min-w-[11rem]"
          value={statusFilter}
          onchange={handleStatusFilterChange}
        >
          <option value="all">All statuses</option>
          {#each HARDWARE_STATUS_META as statusMeta}
            <option value={statusMeta.id}>{statusMeta.label}</option>
          {/each}
        </select>
      </label>

      {#if isOmniAdmin}
        <label class="omni-toolbar-field-compact flex flex-col text-sm font-medium text-foreground">
          <span class="text-xs uppercase tracking-wide text-muted-foreground">Hub</span>
          <select
            class="omni-select mt-1 min-w-[12rem]"
            value={deviceHubFilter}
            onchange={handleHubFilterChange}
          >
            <option value="__all__">All devices</option>
            {#each availableDeviceHubs as hub (hub.id)}
              <option value={hub.id}>{hub.name ?? hub.id}</option>
            {/each}
          </select>
        </label>
      {/if}

      <label class="omni-toolbar-field-compact flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Sort by</span>
        <select
          class="omni-select mt-1 min-w-[11rem]"
          value={sortOption}
          onchange={handleSortChange}
        >
          {#each SORT_OPTIONS as option (option.value)}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>

      <label class="omni-toolbar-field-compact flex flex-col text-sm font-medium text-foreground">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">SIM state</span>
        <select
          class="omni-select mt-1 min-w-[12rem]"
          value={simFilter}
          onchange={handleSimFilterChange}
        >
          <option value="all">All SIM states</option>
          <option value="with_sim">With SIM</option>
          <option value="without_sim">Without SIM</option>
          <option value="roaming">Roaming enabled</option>
          <option value="attention">Needs SIM attention</option>
        </select>
      </label>

      <div class="flex flex-col justify-end text-sm">
        <span class="text-xs uppercase tracking-wide text-muted-foreground">Actions</span>
        <div class="mt-1 flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onclick={resetFilters} disabled={!canResetFilters}>
            Reset filters
          </Button>
          <Button variant="ghost" size="sm" onclick={handleRefresh} disabled={isLoading}>
            Refresh
          </Button>
        </div>
      </div>

      <div class="ml-auto flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1">
          Visible devices: {devices.length}
        </span>
        <span class="rounded-full border border-border/70 bg-background/75 px-3 py-1">
          Total inventory: {totalDevices}
        </span>
      </div>
    </div>
  </section>

  {#if selectionCount > 0 && (isAssignmentMode || canMutateInventory)}
    <div class="sticky top-4 z-20">
      <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-background/95 px-4 py-3 shadow-sm backdrop-blur supports-[backdrop-filter]:backdrop-blur-md">
        <div>
          <p class="text-sm font-semibold">
            {selectionCount} device{selectionCount === 1 ? "" : "s"} selected
          </p>
          {#if isInventoryMode}
            <p class="text-xs text-muted-foreground">
              Edit supports single selection. Delete accepts single or multiple rows.
            </p>
          {:else}
            <p class="text-xs text-muted-foreground">
              Use selection to open installation workflow for this hardware.
            </p>
          {/if}
        </div>
        {#if isInventoryMode && canMutateInventory}
          <div class="flex flex-wrap items-center gap-2">
            <Button variant="ghost" size="sm" onclick={clearSelection}>
              Cancel
            </Button>
            <Button
              size="sm"
              onclick={editSelectedDevice}
              disabled={editActionDisabled}
            >
              Edit
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onclick={deleteSelectedDevices}
              disabled={isBulkDeleting}
            >
              {isBulkDeleting ? "Deleting…" : "Delete"}
            </Button>
          </div>
        {:else if isAssignmentMode}
          <Button variant="ghost" size="sm" onclick={clearSelection}>
            Clear selection
          </Button>
        {/if}
      </div>
    </div>
  {/if}

  <div class="omni-page-grid">
    <div class="omni-list-stage">
      <SimpleInventoryTable
        {devices}
        isLoading={isLoading}
        {currentPage}
        totalPages={Math.max(1, Math.ceil(totalItems / perPage))}
        totalItems={totalItems}
        perPage={perPage}
        {editingDeviceId}
        {pendingDeleteId}
        {selectedDeviceIds}
        {savingDeviceId}
        {deletingDeviceId}
        editDraft={editDraft}
        enableSelection={canSelectRows}
        allowInventoryActions={canMutateInventory}
        on:cancelEdit={cancelEdit}
        on:editDraftChange={handleDraftChange}
        on:saveEdit={saveEdit}
        on:cancelDelete={cancelDelete}
        on:confirmDelete={confirmDelete}
        on:toggleSelect={handleSelectToggle}
        on:toggleSelectAll={handleSelectAll}
        on:changePage={handlePageChange}
        on:inspectDevice={(event) => inspectDevice(event.detail.deviceId)}
      />
    </div>

    <div class="omni-inspector-stage">
  {#if !isAssignmentMode && primarySelectedDevice}
    <section class="omni-panel space-y-4 border-0 shadow-none">
      {#if inventoryInspectorWindow === "home"}
      <div class="grid gap-3">
        <button type="button" class="omni-action-card text-left" onclick={() => (inventoryInspectorWindow = "overview")}>
          <span class="omni-kicker">Overview</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open device profile</span>
          <span class="mt-1 block text-sm text-muted-foreground">Review the selected device on a dedicated page.</span>
        </button>
        <button type="button" class="omni-action-card text-left" onclick={() => (inventoryInspectorWindow = "history")}>
          <span class="omni-kicker">History</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open assignment history</span>
          <span class="mt-1 block text-sm text-muted-foreground">Keep deployment history separate from the main profile page.</span>
        </button>
      </div>
      {/if}

      {#if inventoryInspectorWindow === "overview"}
      <div class="omni-detail-section">
        <div class="flex items-center justify-between gap-2">
          <div>
            <p class="font-semibold text-foreground">Device profile</p>
            <p class="text-xs text-muted-foreground">Review the main properties without leaving the register.</p>
          </div>
          <div class="flex gap-2">
          {#if canMutateInventory}
            <div class="flex gap-2">
              <Button size="sm" variant="outline" onclick={editSelectedDevice} disabled={editActionDisabled}>Edit</Button>
              <Button size="sm" variant="destructive" onclick={deleteSelectedDevices} disabled={isBulkDeleting}>
                {isBulkDeleting ? "Deleting…" : "Delete"}
              </Button>
            </div>
          {/if}
            <Button size="sm" variant="outline" onclick={() => (inventoryInspectorWindow = "home")}>Back</Button>
          </div>
        </div>
        <div class="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
          <p>Serial: <span class="font-medium text-foreground">{primarySelectedDevice.serialNumber ?? "—"}</span></p>
          <p>Firmware: <span class="font-medium text-foreground">{primarySelectedDevice.firmwareVersion ?? "—"}</span></p>
          <p>Purchase date: <span class="font-medium text-foreground">{formatDateDisplay(primarySelectedDevice.purchaseDate)}</span></p>
          <p>SIM state: <span class="font-medium text-foreground">{primarySelectedDevice.sim?.status ?? "No SIM linked"}</span></p>
        </div>
        <div class="mt-4 rounded-2xl border border-white/50 bg-white/70 p-3 text-sm text-muted-foreground dark:border-white/10 dark:bg-slate-950/45">
          {primarySelectedDevice.notes?.trim() || "No device notes have been recorded yet."}
        </div>
      </div>
      {/if}

      {#if inventoryInspectorWindow === "history"}
      <div class="omni-detail-section">
        <div class="flex items-center justify-between gap-2">
          <div>
            <p class="font-semibold text-foreground">Assignment history</p>
            <p class="text-xs text-muted-foreground">Track where this device has been deployed and when it changed state.</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-muted-foreground">{primarySelectedDevice.assignmentHistory?.length ?? 0} events</span>
            <Button size="sm" variant="outline" onclick={() => (inventoryInspectorWindow = "home")}>Back</Button>
          </div>
        </div>
        {#if primarySelectedDevice.assignmentHistory && primarySelectedDevice.assignmentHistory.length > 0}
          <div class="mt-3 space-y-3">
            {#each primarySelectedDevice.assignmentHistory as item (item.id)}
              <div class="rounded-xl border border-white/50 bg-background/70 p-3 text-xs text-muted-foreground dark:border-white/10 dark:bg-slate-900/60">
                <div class="flex items-center justify-between gap-2">
                  <p class="font-semibold text-foreground">{item.assetRegistration ?? item.assetLabel ?? item.target ?? "Deployment event"}</p>
                  <span class={`rounded-full px-2 py-1 ${item.isActive ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : "bg-muted text-muted-foreground"}`}>{item.isActive ? "Active" : "Closed"}</span>
                </div>
                <div class="mt-2 grid gap-1 sm:grid-cols-2">
                  <p>Hub: <span class="font-medium text-foreground">{item.hubName ?? "—"}</span></p>
                  <p>Technician: <span class="font-medium text-foreground">{item.technician ?? "—"}</span></p>
                  <p>Assigned: <span class="font-medium text-foreground">{formatDateTimeDisplay(item.assignedAt)}</span></p>
                  <p>Installed: <span class="font-medium text-foreground">{formatDateTimeDisplay(item.installedAt)}</span></p>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="mt-3 text-sm text-muted-foreground">No assignment history recorded yet.</p>
        {/if}
      </div>
      {/if}
    </section>
  {:else if isAssignmentMode && canUseAssignmentOverrides && primarySelectedDevice}
    <section class="omni-panel space-y-4 border-0 shadow-none">
      <p class="text-xs text-muted-foreground">
        Selected: {primarySelectedDevice.imei}
        {#if parseAssetProfile(primarySelectedDevice.assignment?.notes ?? "").assetType}
          · Type: {formatAssetTypeLabel(parseAssetProfile(primarySelectedDevice.assignment?.notes ?? "").assetType)}
        {/if}
        {#if parseAssetProfile(primarySelectedDevice.assignment?.notes ?? "").assetName}
          · Asset: {parseAssetProfile(primarySelectedDevice.assignment?.notes ?? "").assetName}
        {:else if primarySelectedDevice.assignment?.assetRegistration}
          · Asset: {primarySelectedDevice.assignment.assetRegistration}
        {/if}
        {#if primarySelectedDevice.assignment?.hubName}
          · Hub: {primarySelectedDevice.assignment.hubName}
        {/if}
      </p>

      {#if assignmentInspectorWindow === "home"}
      <div class="grid gap-3">
        <button
          type="button"
          class="omni-action-card text-left border-cyan-400/40 bg-cyan-500/5 dark:border-cyan-400/30 dark:bg-cyan-400/10"
          onclick={() => (assignmentInspectorWindow = "install")}
        >
          <span class="omni-kicker">Install</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open installation page</span>
          <span class="mt-1 block text-sm text-muted-foreground">Assign hardware to an asset. This is the primary assignment workflow.</span>
        </button>
        <button type="button" class="omni-action-card text-left" onclick={() => (assignmentInspectorWindow = "recall")}>
          <span class="omni-kicker">Recall</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open recall page</span>
          <span class="mt-1 block text-sm text-muted-foreground">Handle returns on their own page.</span>
        </button>
        <button type="button" class="omni-action-card text-left" onclick={() => (assignmentInspectorWindow = "replace")}>
          <span class="omni-kicker">Replace</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open replacement page</span>
          <span class="mt-1 block text-sm text-muted-foreground">Work through replacement details without mixing them into recall or install.</span>
        </button>
        <button type="button" class="omni-action-card text-left" onclick={() => (assignmentInspectorWindow = "history")}>
          <span class="omni-kicker">History</span>
          <span class="mt-2 block text-base font-semibold text-foreground">Open assignment history</span>
          <span class="mt-1 block text-sm text-muted-foreground">Review device movement separately from action forms.</span>
        </button>
      </div>
      {/if}

      {#if assignmentInspectorWindow === "install"}
      <div class="grid gap-4 lg:grid-cols-1">
        <div class="rounded-md border border-border/70 p-4 space-y-3">
          <div class="flex items-center justify-between gap-2">
            <div>
              <p class="text-xs uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">Active workflow</p>
              <h4 class="font-medium">Assign / Update Installation</h4>
            </div>
            <Button size="sm" variant="outline" onclick={() => (assignmentInspectorWindow = "home")}>Back</Button>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm">
              Hub
              <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.hubId}>
                <option value="">Select hub</option>
                {#each availableHubOptions as hub (hub.id)}
                  <option value={hub.id}>{hub.name ?? hub.code} ({hub.code})</option>
                {/each}
              </select>
            </label>
            <label class="text-sm">
              Assignment mode
              <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.assignmentMode}>
                <option value="existing">Assign to existing asset</option>
                <option value="new">Create and assign new asset</option>
              </select>
            </label>
            <label class="text-sm">
              Existing asset
              <select
                class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                bind:value={assignmentForm.targetAssetId}
                onchange={(event) => applyAssetSelectionToAssignment(event.currentTarget.value)}
                disabled={loadingAssetOptions || !assignmentForm.hubId || assignmentForm.assignmentMode !== "existing"}
              >
                <option value="">Create or type manually</option>
                {#each availableAssetOptions as asset (asset.id)}
                  <option value={asset.id}>
                    {asset.assetName || "Unnamed asset"}{asset.registration ? ` · ${asset.registration}` : ""}
                  </option>
                {/each}
              </select>
            </label>
            <label class="text-sm">
              Asset type *
              <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.assetType} disabled={assignmentForm.assignmentMode === "existing"}>
                {#each ASSET_TYPE_OPTIONS as option}
                  <option value={option}>{formatAssetTypeLabel(option)}</option>
                {/each}
              </select>
            </label>
            <label class="text-sm">
              Asset name *
              <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.assetName} placeholder="e.g. Truck 12" disabled={assignmentForm.assignmentMode === "existing"} />
            </label>
            <label class="text-sm">
              Technician
              <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.technician} />
            </label>
            <label class="text-sm">
              Install date/time
              <input type="datetime-local" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.installedAt} />
            </label>
            <label class="text-sm">
              Location
              <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.installationLocation} />
            </label>
            <label class="text-sm">
              Latitude
              <input type="number" step="0.0000001" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.installationLatitude} />
            </label>
            <label class="text-sm">
              Longitude
              <input type="number" step="0.0000001" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.installationLongitude} />
            </label>
            <label class="text-sm">
              Asset registration
              <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.assetRegistration} placeholder="e.g. ABL-2345" disabled={assignmentForm.assignmentMode === "existing"} />
            </label>
            {#if primarySelectedDevice.assignment}
              <label class="text-sm md:col-span-2">
                Reassignment reason *
                <input
                  class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                  bind:value={assignmentForm.reassignmentReason}
                  placeholder="Why is this hardware being moved?"
                />
              </label>
            {/if}
            {#if assignmentForm.assetType === "vehicle"}
              <label class="text-sm">
                Make
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.vehicleMake} placeholder="e.g. Toyota" disabled={assignmentForm.assignmentMode === "existing"} />
              </label>
              <label class="text-sm">
                Model
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.vehicleModel} placeholder="e.g. Hilux" disabled={assignmentForm.assignmentMode === "existing"} />
              </label>
              <label class="text-sm">
                Year
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.vehicleYear} placeholder="e.g. 2022" disabled={assignmentForm.assignmentMode === "existing"} />
              </label>
              <label class="text-sm">
                Engine capacity
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.engineCapacity} placeholder="e.g. 2.8L" disabled={assignmentForm.assignmentMode === "existing"} />
              </label>
              <label class="text-sm md:col-span-2">
                VIN
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.vin} disabled={assignmentForm.assignmentMode === "existing"} />
              </label>
            {/if}
          </div>
          <label class="text-sm block">
            Notes
            <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={assignmentForm.notes}></textarea>
          </label>
          <Button
            size="sm"
            onclick={assignSelectedDevice}
            disabled={assigningDeviceId === primarySelectedDevice.id}
          >
            {assigningDeviceId === primarySelectedDevice.id ? "Saving..." : primarySelectedDevice.assignment ? "Reassign device" : "Save assignment"}
          </Button>
        </div>
      </div>
      {/if}

      {#if assignmentInspectorWindow === "recall"}
      <div class="grid gap-4 lg:grid-cols-1">
        <div class="rounded-md border border-border/70 p-4 space-y-3">
          <div class="flex items-center justify-between gap-2">
            <h4 class="font-medium">Recall to inventory</h4>
            <Button size="sm" variant="outline" onclick={() => (assignmentInspectorWindow = "home")}>Back</Button>
          </div>
          <p class="text-xs text-muted-foreground">
            Return the selected hardware to inventory and flag why it was recalled.
          </p>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm block">
              Return status
              <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={recallForm.status}>
                <option value="in_stock">In stock</option>
                <option value="maintenance">Maintenance</option>
                <option value="faulty">Faulty</option>
                <option value="retired">Retired</option>
              </select>
            </label>
            <label class="text-sm block md:col-span-2">
              Recall reason *
              <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={recallForm.reason}></textarea>
            </label>
            <label class="text-sm block md:col-span-2">
              Inventory notes
              <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={recallForm.notes}></textarea>
            </label>
          </div>
          <Button
            variant="outline"
            size="sm"
            onclick={recallSelectedDevice}
            disabled={recallingDeviceId === primarySelectedDevice.id || !primarySelectedDevice.assignment}
          >
            {recallingDeviceId === primarySelectedDevice.id ? "Recalling..." : "Recall to inventory"}
          </Button>
        </div>
      </div>
      {/if}

      {#if assignmentInspectorWindow === "replace"}
      <div class="grid gap-4 lg:grid-cols-1">
        <div class="rounded-md border border-border/70 p-4 space-y-3">
          <div class="flex items-center justify-between gap-2">
            <h4 class="font-medium">Recall & Replacement</h4>
            <Button size="sm" variant="outline" onclick={() => (assignmentInspectorWindow = "home")}>Back</Button>
          </div>
          <p class="text-xs text-muted-foreground">
            Use when installed hardware is faulty. Faulty hardware is returned to inventory with faulty status.
          </p>
          <label class="text-sm block">
            Replacement hardware
            <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.replacementHardwareId}>
              <option value="">Select in-stock hardware</option>
              {#each availableReplacementDevices as option (option.id)}
                <option value={option.id}>{option.imei} · {option.model ?? "Tracker"} · {option.hardwareType ?? "N/A"}</option>
              {/each}
            </select>
          </label>
          <label class="text-sm block">
            Target asset
            <select
              class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              bind:value={replacementForm.targetAssetId}
              onchange={(event) => applyAssetSelectionToReplacement(event.currentTarget.value)}
              disabled={loadingAssetOptions}
            >
              <option value="">Use current asset</option>
              {#each availableAssetOptions as asset (asset.id)}
                <option value={asset.id}>
                  {asset.assetName || "Unnamed asset"}{asset.registration ? ` · ${asset.registration}` : ""}
                </option>
              {/each}
            </select>
          </label>
          <label class="text-sm block">
            Asset type *
            <select class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.assetType}>
              <option value="">Select asset type</option>
              {#each ASSET_TYPE_OPTIONS as option}
                <option value={option}>{formatAssetTypeLabel(option)}</option>
              {/each}
            </select>
          </label>
          <label class="text-sm block">
            Asset name *
            <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.assetName} placeholder="e.g. Truck 12" />
          </label>
          <label class="text-sm block">
            Asset registration
            <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.assetRegistration} />
          </label>
          {#if replacementForm.assetType === "vehicle"}
            <div class="grid gap-3 md:grid-cols-2">
              <label class="text-sm block">
                Make
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.vehicleMake} />
              </label>
              <label class="text-sm block">
                Model
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.vehicleModel} />
              </label>
              <label class="text-sm block">
                Year
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.vehicleYear} />
              </label>
              <label class="text-sm block">
                Engine capacity
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.engineCapacity} />
              </label>
              <label class="text-sm block md:col-span-2">
                VIN
                <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.vin} />
              </label>
            </div>
          {/if}
          <label class="text-sm block">
            Fault reason *
            <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.faultyReason}></textarea>
          </label>
          <label class="text-sm block">
            Technician
            <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.technician} />
          </label>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="text-sm block">
              Install date/time
              <input type="datetime-local" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.installedAt} />
            </label>
            <label class="text-sm block">
              Location
              <input class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.installationLocation} />
            </label>
          </div>
          <label class="text-sm block">
            Replacement notes
            <textarea rows="2" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" bind:value={replacementForm.notes}></textarea>
          </label>
          <Button
            variant="destructive"
            size="sm"
            onclick={replaceSelectedDevice}
            disabled={reassigningDeviceId === primarySelectedDevice.id || !primarySelectedDevice.assignment}
          >
            {reassigningDeviceId === primarySelectedDevice.id ? "Replacing..." : "Replace faulty hardware"}
          </Button>
        </div>
      </div>
      {/if}

      {#if assignmentInspectorWindow === "history"}
      <div class="rounded-md border border-border/70 p-4 space-y-3">
        <div class="flex items-center justify-between gap-2">
          <h4 class="font-medium">Installation history</h4>
          <div class="flex items-center gap-2">
            <span class="text-xs text-muted-foreground">
              {primarySelectedDevice.assignmentHistory?.length ?? 0} event{(primarySelectedDevice.assignmentHistory?.length ?? 0) === 1 ? "" : "s"}
            </span>
            <Button size="sm" variant="outline" onclick={() => (assignmentInspectorWindow = "home")}>Back</Button>
          </div>
        </div>
        {#if primarySelectedDevice.assignmentHistory && primarySelectedDevice.assignmentHistory.length > 0}
          <ul class="space-y-3">
            {#each primarySelectedDevice.assignmentHistory as item (item.id)}
              <li class="rounded-md border border-border/60 bg-background/60 p-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <p class="text-sm font-semibold">
                    {item.assetRegistration ?? item.assetLabel ?? "Unlabelled asset"}
                    {#if item.hubName}
                      · {item.hubName}
                    {/if}
                  </p>
                  <span class={`rounded-full px-2 py-0.5 text-[11px] font-medium ${item.isActive ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : "bg-muted text-muted-foreground"}`}>
                    {item.isActive ? "Active" : "Closed"}
                  </span>
                </div>
                <div class="mt-2 grid gap-1 text-xs text-muted-foreground md:grid-cols-2">
                  <p>Assigned: {formatDateTimeDisplay(item.assignedAt)}</p>
                  <p>Installed: {formatDateTimeDisplay(item.installedAt)}</p>
                  <p>Unassigned: {formatDateTimeDisplay(item.unassignedAt)}</p>
                  <p>Technician: {formatFreeText(item.technician)}</p>
                  <p>Target: {formatFreeText(item.target)}</p>
                  <p>Vehicle: {formatFreeText(item.vehiclePlate)}</p>
                  <p>Location: {formatFreeText(item.installationLocation)}</p>
                  <p>
                    SIM: {formatFreeText(
                      item.simIccid
                        ? `${item.simIccid}${item.simCarrier ? ` · ${item.simCarrier}` : ""}${item.simRoamingEnabled ? " · Roaming" : ""}`
                        : null,
                    )}
                  </p>
                  <p>Notes: {formatFreeText(item.notes)}</p>
                </div>
              </li>
            {/each}
          </ul>
        {:else}
          <p class="text-sm text-muted-foreground">
            No assignment history for this hardware yet.
          </p>
        {/if}
      </div>
      {/if}
    </section>
  {:else if isAssignmentMode}
    <div class="omni-empty-state py-10">
      Select a device from the register to begin assignment, recall, or replacement.
    </div>
  {:else}
    <div class="omni-panel border-0 shadow-none p-5">
      <p class="omni-kicker">Device profile</p>
      <h3 class="mt-2 text-lg font-semibold">Register actions stay in context</h3>
      <p class="mt-2 text-sm text-muted-foreground">
        Use the table to search, sort, edit, or remove devices. Selecting rows unlocks the relevant actions without pushing extra content below the register.
      </p>
    </div>
  {/if}
    </div>
  </div>

</section>
