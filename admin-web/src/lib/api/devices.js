import apiClient from "$lib/api/http";

export const HARDWARE_STATUS_META = [
  {
    id: "in_stock",
    label: "In Stock",
    description: "Ready in warehouse awaiting assignment",
  },
  {
    id: "assigned",
    label: "Deployed",
    description: "Allocated to a hub or asset and no longer available in stock",
  },
  {
    id: "maintenance",
    label: "Maintenance",
    description: "Escalated for diagnostics or firmware work",
  },
  {
    id: "faulty",
    label: "Faulty",
    description: "Failed validation and awaiting resolution",
  },
  {
    id: "retired",
    label: "Retired",
    description: "Permanently removed from service",
  },
];

const STATUS_LOOKUP = HARDWARE_STATUS_META.reduce((acc, item) => {
  acc[item.id] = item.label;
  return acc;
}, {});

const STATUS_ORDER = HARDWARE_STATUS_META.map((item) => item.id);

function generateLocalId() {
  if (typeof globalThis !== "undefined" && globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `hw-${Math.random().toString(36).slice(2, 11)}`;
}

function createStatusSeed() {
  return STATUS_ORDER.reduce((acc, status) => {
    acc[status] = 0;
    return acc;
  }, {});
}

function normalizeStatus(value) {
  if (!value) {
    return "in_stock";
  }
  const candidate = value.toString().trim().toLowerCase();
  if (candidate === "active") {
    return "assigned";
  }
  if (STATUS_ORDER.includes(candidate)) {
    return candidate;
  }
  switch (candidate) {
    case "available":
    case "warehouse":
      return "in_stock";
    case "paired":
    case "installed":
    case "deployed":
      return "assigned";
    case "diagnostic":
      return "maintenance";
    default:
      return "in_stock";
  }
}

function normalizeAssignment(raw = null) {
  if (!raw) {
    return null;
  }

  const vehicleId = raw.vehicle_id ?? raw.vehicleId ?? raw.vehicle ?? null;
  const vehiclePlate =
    raw.vehicle_plate ??
    raw.vehiclePlate ??
    raw.vehicle_label ??
    raw.vehicleLabel ??
    raw.vehicle_name ??
    raw.vehicleName ??
    null;

  return {
    vehicleId,
    vehiclePlate,
    hubId: raw.hub_id ?? raw.hubId ?? null,
    hubName: raw.hub_name ?? raw.hubName ?? null,
    technician: raw.technician ?? raw.assigned_by_name ?? raw.assignedBy ?? null,
    assignedAt: raw.assigned_at ?? raw.started_at ?? raw.updated_at ?? null,
    installedAt: raw.installed_at ?? null,
    installationLocation: raw.installation_location ?? null,
    installationLatitude: raw.installation_latitude ?? null,
    installationLongitude: raw.installation_longitude ?? null,
    assetLabel: raw.asset_label ?? null,
    assetRegistration: raw.asset_registration ?? null,
    notes: raw.notes ?? null,
    simId: raw.sim_id ?? raw.simId ?? null,
    simIccid: raw.sim_iccid ?? raw.simIccid ?? null,
    simMsisdn: raw.sim_msisdn ?? raw.simMsisdn ?? null,
    simCarrier: raw.sim_carrier ?? raw.simCarrier ?? null,
    simRoamingEnabled:
      raw.sim_roaming_enabled ?? raw.simRoamingEnabled ?? null,
  };
}

function normalizeAssignmentHistory(raw = []) {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.map((entry) => {
    const vehicleId = entry.vehicle_id ?? entry.vehicleId ?? null;
    const vehiclePlate =
      entry.vehicle_plate ??
      entry.vehiclePlate ??
      entry.vehicle_label ??
      entry.vehicleLabel ??
      entry.vehicle_name ??
      entry.vehicleName ??
      null;
    return {
      id: entry.id ?? null,
      target: entry.target ?? null,
      hubId: entry.hub_id ?? entry.hubId ?? null,
      hubName: entry.hub_name ?? entry.hubName ?? null,
      vehicleId,
      vehiclePlate,
      technician: entry.technician ?? entry.assigned_by_name ?? entry.assignedBy ?? null,
      assignedAt: entry.assigned_at ?? null,
      installedAt: entry.installed_at ?? null,
      unassignedAt: entry.unassigned_at ?? null,
      installationLocation: entry.installation_location ?? null,
      installationLatitude: entry.installation_latitude ?? null,
      installationLongitude: entry.installation_longitude ?? null,
      assetLabel: entry.asset_label ?? null,
      assetRegistration: entry.asset_registration ?? null,
      notes: entry.notes ?? null,
      isActive: Boolean(entry.is_active),
      simId: entry.sim_id ?? entry.simId ?? null,
      simIccid: entry.sim_iccid ?? entry.simIccid ?? null,
      simMsisdn: entry.sim_msisdn ?? entry.simMsisdn ?? null,
      simCarrier: entry.sim_carrier ?? entry.simCarrier ?? null,
      simRoamingEnabled:
        entry.sim_roaming_enabled ?? entry.simRoamingEnabled ?? null,
    };
  });
}

function normalizeSimAssignment(raw = null) {
  if (!raw) {
    return null;
  }
  return {
    target: raw.target ?? null,
    hardwareId: raw.hardware_id ?? raw.hardwareId ?? null,
    hardwareImei: raw.hardware_imei ?? raw.hardwareImei ?? null,
    hubId: raw.hub_id ?? raw.hubId ?? null,
    hubName: raw.hub_name ?? raw.hubName ?? null,
    vehicleId: raw.vehicle_id ?? raw.vehicleId ?? null,
    vehicleLabel: raw.vehicle_label ?? raw.vehicleLabel ?? null,
    assignedAt: raw.assigned_at ?? raw.assignedAt ?? null,
    technician: raw.technician ?? null,
    notes: raw.notes ?? null,
  };
}

function normalizeSimHistory(raw = []) {
  if (!Array.isArray(raw)) return [];
  return raw.map((entry) => ({
    id: entry.id ?? null,
    target: entry.target ?? null,
    hardwareId: entry.hardware_id ?? entry.hardwareId ?? null,
    hardwareImei: entry.hardware_imei ?? entry.hardwareImei ?? null,
    hubId: entry.hub_id ?? entry.hubId ?? null,
    hubName: entry.hub_name ?? entry.hubName ?? null,
    vehicleId: entry.vehicle_id ?? entry.vehicleId ?? null,
    vehicleLabel: entry.vehicle_label ?? entry.vehicleLabel ?? null,
    technician: entry.technician ?? null,
    assignedAt: entry.assigned_at ?? entry.assignedAt ?? null,
    unassignedAt: entry.unassigned_at ?? entry.unassignedAt ?? null,
    notes: entry.notes ?? null,
    isActive: Boolean(entry.is_active ?? entry.isActive),
  }));
}

function normalizeSim(raw = {}) {
  return {
    id: raw.id ?? null,
    iccid: raw.iccid ?? "",
    msisdn: raw.msisdn ?? null,
    carrier: raw.carrier ?? "Econet",
    imsi: raw.imsi ?? raw.apn ?? null,
    roamingEnabled: Boolean(raw.roaming_enabled ?? raw.roamingEnabled),
    roamingRegions: raw.roaming_regions ?? raw.roamingRegions ?? null,
    status: raw.status ?? "in_stock",
    notes: raw.notes ?? null,
    createdAt: raw.created_at ?? raw.createdAt ?? null,
    updatedAt: raw.updated_at ?? raw.updatedAt ?? null,
    assignment: normalizeSimAssignment(raw.assignment ?? null),
    assignmentHistory: normalizeSimHistory(raw.assignment_history ?? raw.assignmentHistory ?? []),
  };
}

function normalizePairing(raw = null) {
  if (!raw) {
    return null;
  }
  return {
    status: raw.status ?? "pending",
    requestedBy: raw.requested_by_name ?? raw.requested_by ?? raw.requestedBy ?? null,
    approvedBy: raw.approved_by_name ?? raw.approved_by ?? raw.approvedBy ?? null,
    approvedAt: raw.approved_at ?? raw.updated_at ?? null,
  };
}

function normalizeDevice(raw = {}) {
  const status = normalizeStatus(raw.status ?? raw.lifecycle_status ?? raw.hardware_status);
  const assignment = normalizeAssignment(raw.assignment ?? raw.current_assignment ?? raw.latest_assignment);
  const assignmentHistory = normalizeAssignmentHistory(
    raw.assignment_history ?? raw.assignmentHistory ?? raw.assignments ?? [],
  );

  return {
    id: raw.id ?? raw.hardware_id ?? raw.imei ?? generateLocalId(),
    imei: raw.imei ?? raw.hardware_identifier ?? "Unknown IMEI",
    serialNumber: raw.serial_number ?? raw.serialNumber ?? raw.serial ?? null,
    hardwareType: raw.hardware_type ?? raw.type ?? null,
    model: raw.model ?? raw.variant ?? null,
    manufacturer: raw.manufacturer ?? raw.vendor ?? "Omni Devices",
    firmwareVersion: raw.firmware_version ?? raw.firmware ?? null,
    status,
    assignment,
    assignmentHistory,
    lastSeen: raw.last_seen ?? raw.last_seen_at ?? raw.telemetry_last_seen ?? raw.updated_at ?? null,
    notes: raw.notes ?? "",
    purchaseDate: raw.purchase_date ?? raw.purchased_at ?? null,
    description: raw.description ?? null,
    sim: raw.sim ? normalizeSim(raw.sim) : null,
    pairing: normalizePairing(raw.pairing ?? raw.latest_pairing ?? raw.device_pairing),
  };
}

function sanitizeQuery(params = {}) {
  const query = { ...params };
  if (query.status === "all") {
    delete query.status;
  }
  if (!query.search) {
    delete query.search;
  }
  if (!query.hubId && query.hub_id) {
    query.hubId = query.hub_id;
  }
  if (!query.hubId) {
    delete query.hubId;
  }
  return query;
}

function buildSummary(allItems, visibleCount) {
  const base = createStatusSeed();
  for (const item of allItems) {
    const key = STATUS_ORDER.includes(item.status) ? item.status : "in_stock";
    base[key] = (base[key] ?? 0) + 1;
  }

  return {
    total: allItems.length,
    visible: typeof visibleCount === "number" ? visibleCount : allItems.length,
    updatedAt: new Date().toISOString(),
    byStatus: base,
    distribution: STATUS_ORDER.map((status) => ({
      id: status,
      label: STATUS_LOOKUP[status],
      count: base[status] ?? 0,
    })),
  };
}

function normalizeSummary(summaryCandidate, allItems, visibleCount) {
  if (!summaryCandidate) {
    return buildSummary(allItems, visibleCount);
  }
  const seed = buildSummary(allItems, visibleCount);
  const counts = {
    ...seed.byStatus,
    ...(summaryCandidate.byStatus ?? summaryCandidate.status_counts ?? {}),
  };
  if (counts.active) {
    counts.assigned = (counts.assigned ?? 0) + counts.active;
    delete counts.active;
  }

  return {
    total: summaryCandidate.total ?? seed.total,
    visible: visibleCount ?? seed.visible,
    updatedAt:
      summaryCandidate.updatedAt ??
      summaryCandidate.updated_at ??
      summaryCandidate.generated_at ??
      seed.updatedAt,
    byStatus: STATUS_ORDER.reduce((acc, status) => {
      acc[status] = counts[status] ?? 0;
      return acc;
    }, {}),
    distribution: seed.distribution.map((entry) => ({
      ...entry,
      count: counts[entry.id] ?? entry.count,
    })),
  };
}

function normalizePurchaseDate(value) {
  if (!value) return undefined;
  const candidate = String(value).trim();
  if (!candidate) return undefined;

  // HTML date input emits YYYY-MM-DD; API expects a datetime.
  if (/^\d{4}-\d{2}-\d{2}$/.test(candidate)) {
    return `${candidate}T00:00:00Z`;
  }
  return candidate;
}

export async function fetchDeviceInventory(params = {}) {
  const { hubHeader = undefined, ...rest } = params ?? {};
  const query = sanitizeQuery(rest);
  const requestConfig = { params: query };

  if (hubHeader === null) {
    requestConfig.headers = { "X-Hub-ID": undefined };
  } else if (hubHeader) {
    requestConfig.headers = { "X-Hub-ID": hubHeader };
  }

  const response = await apiClient.get("/devices", requestConfig);
  const payload = response?.data ?? {};
  const rawItems = Array.isArray(payload?.data?.items)
    ? payload.data.items
    : Array.isArray(payload?.data)
      ? payload.data
      : Array.isArray(payload?.items)
        ? payload.items
        : Array.isArray(payload?.results)
          ? payload.results
          : [];
  const normalizedItems = rawItems.map((item) => normalizeDevice(item));
  const summary = normalizeSummary(payload.summary, normalizedItems, normalizedItems.length);

  return {
    items: normalizedItems,
    summary,
    meta: payload.meta ?? {
      total: normalizedItems.length,
      page: payload.page ?? 1,
      perPage: payload.per_page ?? normalizedItems.length,
    },
  };
}

export async function updateDevice(hardwareId, payload = {}) {
  if (!hardwareId) {
    throw new Error("hardwareId is required to update a device");
  }
  const response = await apiClient.patch(`/devices/${hardwareId}`, payload);
  const rawDevice = response?.data?.data;
  return rawDevice ? normalizeDevice(rawDevice) : null;
}

export async function deleteDevice(hardwareId) {
  if (!hardwareId) {
    throw new Error("hardwareId is required to delete a device");
  }
  await apiClient.delete(`/devices/${hardwareId}`);
  return true;
}

export function getStatusLabel(status) {
  return STATUS_LOOKUP[status] ?? STATUS_LOOKUP[normalizeStatus(status)] ?? status;
}

export async function updateDeviceStatus(deviceId, payload) {
  if (!deviceId) {
    throw new Error("deviceId is required to update hardware status");
  }
  const requestBody = {
    status: payload.status,
    notes: payload.notes ?? undefined,
  };
  const { data } = await apiClient.patch(`/devices/${deviceId}/status`, requestBody);
  const rawDevice = data?.data ?? data;
  return normalizeDevice(rawDevice);
}

export async function assignDevice(deviceId, payload = {}) {
  if (!deviceId) {
    throw new Error("deviceId is required for assignment");
  }

  const requestBody = {
    hub_id: payload.hubId ?? payload.hub_id ?? undefined,
    vehicle_id: payload.vehicleId ?? payload.vehicle_id ?? undefined,
    source_job_id: payload.sourceJobId ?? payload.source_job_id ?? undefined,
    asset_type: payload.assetType ?? payload.asset_type ?? undefined,
    asset_name: payload.assetName ?? payload.asset_name ?? undefined,
    vehicle_make: payload.vehicleMake ?? payload.vehicle_make ?? undefined,
    vehicle_model: payload.vehicleModel ?? payload.vehicle_model ?? undefined,
    vehicle_year: payload.vehicleYear ?? payload.vehicle_year ?? undefined,
    engine_capacity: payload.engineCapacity ?? payload.engine_capacity ?? undefined,
    vin: payload.vin ?? undefined,
    technician: payload.technician ?? undefined,
    installed_at: payload.installedAt ?? payload.installed_at ?? undefined,
    installation_location: payload.installationLocation ?? payload.installation_location ?? undefined,
    installation_latitude: payload.installationLatitude ?? payload.installation_latitude ?? undefined,
    installation_longitude: payload.installationLongitude ?? payload.installation_longitude ?? undefined,
    asset_label: payload.assetLabel ?? payload.asset_label ?? undefined,
    asset_registration: payload.assetRegistration ?? payload.asset_registration ?? undefined,
    reassignment_reason: payload.reassignmentReason ?? payload.reassignment_reason ?? undefined,
    sim_id: payload.simId ?? payload.sim_id ?? undefined,
    notes: payload.notes ?? undefined,
  };

  const { data } = await apiClient.post(`/devices/${deviceId}/assign`, requestBody);
  const rawDevice = data?.data ?? data;
  return normalizeDevice(rawDevice);
}

export async function fetchSimInventory(params = {}) {
  const response = await apiClient.get("/devices/sims", { params: sanitizeQuery(params) });
  const payload = response?.data ?? {};
  const rawItems = Array.isArray(payload?.data?.items)
    ? payload.data.items
    : Array.isArray(payload?.data)
      ? payload.data
      : [];
  const items = rawItems.map((item) => normalizeSim(item));
  return {
    items,
    summary: payload.summary ?? null,
    meta: payload.meta ?? {
      total: items.length,
      page: 1,
      perPage: items.length,
    },
  };
}

export async function intakeSim(payload = {}) {
  const body = {
    iccid: payload.iccid,
    msisdn: payload.msisdn ?? undefined,
    carrier: payload.carrier ?? "Econet",
    imsi: payload.imsi ?? undefined,
    roaming_enabled: payload.roamingEnabled ?? payload.roaming_enabled ?? false,
    roaming_regions: payload.roamingRegions ?? payload.roaming_regions ?? undefined,
    notes: payload.notes ?? undefined,
  };
  const response = await apiClient.post("/devices/sims", body);
  return normalizeSim(response?.data?.data ?? response?.data);
}

export async function updateSim(simId, payload = {}) {
  const response = await apiClient.patch(`/devices/sims/${simId}`, {
    msisdn: payload.msisdn ?? undefined,
    carrier: payload.carrier ?? undefined,
    imsi: payload.imsi ?? undefined,
    roaming_enabled: payload.roamingEnabled ?? payload.roaming_enabled ?? undefined,
    roaming_regions: payload.roamingRegions ?? payload.roaming_regions ?? undefined,
    status: payload.status ?? undefined,
    notes: payload.notes ?? undefined,
  });
  return normalizeSim(response?.data?.data ?? response?.data);
}

export async function assignSim(simId, payload = {}) {
  const response = await apiClient.post(`/devices/sims/${simId}/assign`, {
    hardware_id: payload.hardwareId ?? payload.hardware_id,
    hub_id: payload.hubId ?? payload.hub_id ?? undefined,
    vehicle_id: payload.vehicleId ?? payload.vehicle_id ?? undefined,
    source_job_id: payload.sourceJobId ?? payload.source_job_id ?? undefined,
    notes: payload.notes ?? undefined,
  });
  return normalizeSim(response?.data?.data ?? response?.data);
}

export async function recallSim(simId, payload = {}) {
  const response = await apiClient.post(`/devices/sims/${simId}/recall`, {
    status: payload.status ?? "in_stock",
    reason: payload.reason,
    source_job_id: payload.sourceJobId ?? payload.source_job_id ?? undefined,
    notes: payload.notes ?? undefined,
  });
  return normalizeSim(response?.data?.data ?? response?.data);
}

export async function deleteSim(simId) {
  await apiClient.delete(`/devices/sims/${simId}`);
}

export async function reassignDevice(faultyDeviceId, payload = {}) {
  if (!faultyDeviceId) {
    throw new Error("faultyDeviceId is required for reassignment");
  }
  if (!payload.replacementHardwareId && !payload.replacement_hardware_id) {
    throw new Error("replacementHardwareId is required for reassignment");
  }

  const requestBody = {
    replacement_hardware_id: payload.replacementHardwareId ?? payload.replacement_hardware_id,
    asset_type: payload.assetType ?? payload.asset_type ?? undefined,
    asset_name: payload.assetName ?? payload.asset_name ?? undefined,
    vehicle_make: payload.vehicleMake ?? payload.vehicle_make ?? undefined,
    vehicle_model: payload.vehicleModel ?? payload.vehicle_model ?? undefined,
    vehicle_year: payload.vehicleYear ?? payload.vehicle_year ?? undefined,
    engine_capacity: payload.engineCapacity ?? payload.engine_capacity ?? undefined,
    vin: payload.vin ?? undefined,
    technician: payload.technician ?? undefined,
    installed_at: payload.installedAt ?? payload.installed_at ?? undefined,
    installation_location: payload.installationLocation ?? payload.installation_location ?? undefined,
    installation_latitude: payload.installationLatitude ?? payload.installation_latitude ?? undefined,
    installation_longitude: payload.installationLongitude ?? payload.installation_longitude ?? undefined,
    asset_label: payload.assetLabel ?? payload.asset_label ?? undefined,
    asset_registration: payload.assetRegistration ?? payload.asset_registration ?? undefined,
    faulty_reason: payload.faultyReason ?? payload.faulty_reason ?? undefined,
    notes: payload.notes ?? undefined,
  };

  const { data } = await apiClient.post(`/devices/${faultyDeviceId}/reassign`, requestBody);
  const rawDevice = data?.data ?? data;
  return normalizeDevice(rawDevice);
}

export async function recallDevice(deviceId, payload = {}) {
  if (!deviceId) {
    throw new Error("deviceId is required for recall");
  }

  const requestBody = {
    status: payload.status ?? "in_stock",
    reason: payload.reason ?? undefined,
    source_job_id: payload.sourceJobId ?? payload.source_job_id ?? undefined,
    notes: payload.notes ?? undefined,
  };

  const { data } = await apiClient.post(`/devices/${deviceId}/recall`, requestBody);
  const rawDevice = data?.data ?? data;
  return normalizeDevice(rawDevice);
}

export async function intakeHardware(payload = {}, options = {}) {
  if (!payload.imei) {
    throw new Error("IMEI is required for hardware intake");
  }

  const body = {
    imei: payload.imei,
    hardware_type: payload.hardwareType ?? payload.hardware_type ?? undefined,
    model: payload.model ?? undefined,
    manufacturer: payload.manufacturer ?? undefined,
    firmware_version: payload.firmwareVersion ?? payload.firmware_version ?? undefined,
    serial_number: payload.serialNumber ?? payload.serial_number ?? undefined,
    notes: payload.notes ?? undefined,
    purchase_date: normalizePurchaseDate(payload.purchaseDate ?? payload.purchase_date),
  };

  const headers = {};

  const candidateToken = typeof options.token === "string" ? options.token.trim() : "";
  if (candidateToken) {
    headers.Authorization = candidateToken.startsWith("Bearer ") ? candidateToken : `Bearer ${candidateToken}`;
  }

  const candidateHubId = typeof options.hubId === "string" ? options.hubId.trim() : "";
  if (candidateHubId) {
    headers["X-Hub-ID"] = candidateHubId;
  }

  const config = Object.keys(headers).length > 0 ? { headers } : undefined;

  const { data } = await apiClient.post("/devices", body, config);
  const rawDevice = data?.data ?? data;
  return normalizeDevice(rawDevice);
}
