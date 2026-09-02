// @ts-check
import apiClient from "$lib/api/http";

/** @typedef {import("$lib/types/hub").Hub} Hub */
/** @typedef {import("$lib/types/hub").HubUser} HubUser */
/** @typedef {import("$lib/types/hub").HubAsset} HubAsset */
/** @typedef {import("$lib/types/hub").HubAssetDetail} HubAssetDetail */

/**
 * Normalize hub payloads from the API or fallbacks into a consistent shape.
 * @param {Record<string, any>} raw
 * @returns {Hub}
 */
function normalizeHub(raw = {}) {
  const typeValue = (raw.hub_type ?? raw.type ?? raw.category ?? "company").toLowerCase();
  const primaryContact = raw.primary_contact ?? {};
  const billingContact = raw.billing_contact ?? {};
  const normalizePlanLabel = (value) => {
    const fallback = typeValue === "individual" ? "Individual" : "Business";
    const normalized = (value ?? fallback).toString().trim();
    if (!normalized) {
      return fallback;
    }
    const lowered = normalized.toLowerCase();
    if (["basic", "free", "individual"].includes(lowered)) {
      return "Individual";
    }
    if (["pro", "enterprise", "business"].includes(lowered)) {
      return "Business";
    }
    return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
  };
  const normalizedUsers = Array.isArray(raw.users)
    ? raw.users.map((user, index) => ({
        id: user.id ?? `hub-user-${index}`,
        name: user.name ?? user.full_name ?? "Unnamed user",
        email: user.email ?? "",
        role: user.role ?? user.permission ?? "Viewer",
      }))
    : [];
  const normalizedDevices = Array.isArray(raw.devices)
    ? raw.devices.map((device, index) => ({
        assignmentId: device.assignment_id ?? device.assignmentId ?? null,
        hardwareId: device.hardware_id ?? device.hardwareId ?? null,
        imei: device.imei ?? `unknown-${index}`,
        model: device.model ?? null,
        hardwareType: device.hardware_type ?? device.hardwareType ?? null,
        status: device.status ?? null,
        assetLabel: device.asset_label ?? device.assetLabel ?? null,
        assetRegistration: device.asset_registration ?? device.assetRegistration ?? null,
        installationLocation: device.installation_location ?? device.installationLocation ?? null,
        technician: device.technician ?? null,
        assignedAt: device.assigned_at ?? device.assignedAt ?? null,
        installedAt: device.installed_at ?? device.installedAt ?? null,
        vehicleId: device.vehicle_id ?? device.vehicleId ?? null,
        vehicleLabel: device.vehicle_label ?? device.vehicleLabel ?? null,
      }))
    : [];

  /** @type {Hub} */
  const normalized = {
    id:
      raw.id ??
      raw.hub_id ??
      raw.code ??
      raw.slug ??
      globalThis.crypto?.randomUUID?.() ??
      `hub-${Date.now()}`,
    name: raw.name ?? raw.hub_name ?? "Unnamed hub",
    code: raw.code ?? raw.reference ?? raw.hub_code ?? raw.id ?? "HUB-0000",
    type: typeValue === "individual" ? "individual" : "company",
    tier: normalizePlanLabel(raw.subscription_tier ?? raw.tier),
    paymentMethod: raw.payment_method ?? "manual_invoice",
    billingCycle: raw.billing_cycle ?? "monthly",
    status: raw.status ?? "active",
    timezone: raw.timezone ?? "UTC",
    country: raw.country ?? raw.region ?? "Unknown",
    city: raw.city ?? raw.locality ?? "",
    address: raw.address ?? raw.address_line ?? "",
    goLiveDate: raw.go_live_date ?? raw.live_at ?? null,
    deviceCount: raw.device_count ?? raw.devices ?? 0,
    vehicleCount: raw.vehicle_count ?? raw.vehicles ?? 0,
    primaryContact: {
      name: raw.primary_contact_name ?? raw.contact_name ?? primaryContact.name ?? "",
      email: raw.primary_contact_email ?? raw.contact_email ?? primaryContact.email ?? "",
      phone: raw.primary_contact_phone ?? raw.contact_phone ?? primaryContact.phone ?? "",
    },
    billingContact: {
      name: raw.billing_contact_name ?? billingContact.name ?? "",
      email: raw.billing_contact_email ?? billingContact.email ?? "",
      phone: raw.billing_contact_phone ?? billingContact.phone ?? "",
    },
    notes: raw.notes ?? "",
    currency: raw.currency ?? "",
    subscriptionDaysLeft:
      raw.subscription_days_left ??
      raw.subscriptionDaysLeft ??
      raw.days_left ??
      raw.daysLeft ??
      null,
    subscriptionStartDate:
      raw.subscription_start_date ??
      raw.subscriptionStartDate ??
      raw.start_date ??
      raw.startDate ??
      null,
    subscriptionEndDate:
      raw.subscription_end_date ??
      raw.subscriptionEndDate ??
      raw.end_date ??
      raw.endDate ??
      null,
    users: normalizedUsers,
    devices: normalizedDevices,
  };

  return normalized;
}

function normalizeHubDevice(raw = {}, index = 0) {
  return {
    assignmentId: raw.assignment_id ?? raw.assignmentId ?? null,
    hardwareId: raw.hardware_id ?? raw.hardwareId ?? null,
    imei: raw.imei ?? `unknown-${index}`,
    serialNumber: raw.serial_number ?? raw.serialNumber ?? null,
    model: raw.model ?? null,
    hardwareType: raw.hardware_type ?? raw.hardwareType ?? null,
    manufacturer: raw.manufacturer ?? null,
    firmwareVersion: raw.firmware_version ?? raw.firmwareVersion ?? null,
    status: raw.status ?? null,
    assetLabel: raw.asset_label ?? raw.assetLabel ?? null,
    assetRegistration: raw.asset_registration ?? raw.assetRegistration ?? null,
    installationLocation: raw.installation_location ?? raw.installationLocation ?? null,
    technician: raw.technician ?? null,
    assignedAt: raw.assigned_at ?? raw.assignedAt ?? null,
    installedAt: raw.installed_at ?? raw.installedAt ?? null,
    vehicleId: raw.vehicle_id ?? raw.vehicleId ?? null,
    vehicleLabel: raw.vehicle_label ?? raw.vehicleLabel ?? null,
    sim: raw.sim
      ? {
          id: raw.sim.id ?? null,
          iccid: raw.sim.iccid ?? null,
          msisdn: raw.sim.msisdn ?? null,
          carrier: raw.sim.carrier ?? null,
          roamingEnabled: Boolean(raw.sim.roaming_enabled ?? raw.sim.roamingEnabled),
          status: raw.sim.status ?? null,
        }
      : null,
    assignmentHistory: Array.isArray(raw.assignment_history ?? raw.assignmentHistory)
      ? (raw.assignment_history ?? raw.assignmentHistory).map((entry) => ({
          id: entry.id ?? null,
          target: entry.target ?? null,
          hubId: entry.hub_id ?? entry.hubId ?? null,
          hubName: entry.hub_name ?? entry.hubName ?? null,
          vehicleId: entry.vehicle_id ?? entry.vehicleId ?? null,
          vehicleLabel: entry.vehicle_label ?? entry.vehicleLabel ?? null,
          technician: entry.technician ?? null,
          assignedAt: entry.assigned_at ?? entry.assignedAt ?? null,
          installedAt: entry.installed_at ?? entry.installedAt ?? null,
          unassignedAt: entry.unassigned_at ?? entry.unassignedAt ?? null,
          installationLocation: entry.installation_location ?? entry.installationLocation ?? null,
          installationLatitude: entry.installation_latitude ?? entry.installationLatitude ?? null,
          installationLongitude: entry.installation_longitude ?? entry.installationLongitude ?? null,
          assetLabel: entry.asset_label ?? entry.assetLabel ?? null,
          assetRegistration: entry.asset_registration ?? entry.assetRegistration ?? null,
          notes: entry.notes ?? null,
          isActive: Boolean(entry.is_active ?? entry.isActive),
          simId: entry.sim_id ?? entry.simId ?? null,
          simIccid: entry.sim_iccid ?? entry.simIccid ?? null,
          simMsisdn: entry.sim_msisdn ?? entry.simMsisdn ?? null,
          simCarrier: entry.sim_carrier ?? entry.simCarrier ?? null,
          simRoamingEnabled: Boolean(entry.sim_roaming_enabled ?? entry.simRoamingEnabled),
        }))
      : [],
  };
}

/**
 * @param {Record<string, any>} raw
 * @returns {HubAsset}
 */
function normalizeHubAsset(raw = {}) {
  return {
    id: raw.id ?? crypto?.randomUUID?.() ?? `asset-${Date.now()}`,
    assetType: raw.asset_type ?? raw.assetType ?? null,
    assetName: raw.asset_name ?? raw.assetName ?? null,
    assetTypeOther: raw.asset_type_other ?? raw.assetTypeOther ?? null,
    registration: raw.registration ?? raw.license_plate ?? null,
    label: raw.label ?? null,
    vin: raw.vin ?? null,
    make: raw.make ?? null,
    model: raw.model ?? null,
    year: raw.year ?? null,
    color: raw.color ?? null,
    engineCapacity: raw.engine_capacity ?? raw.engineCapacity ?? null,
    co2Emissions: raw.co2_emissions ?? raw.co2Emissions ?? null,
    fuelType: raw.fuel_type ?? raw.fuelType ?? null,
    status: raw.status ?? null,
    notes: raw.notes ?? null,
    trackingState: raw.tracking_state ?? raw.trackingState ?? null,
    sourceJobId: raw.source_job_id ?? raw.sourceJobId ?? null,
    assignedDeviceCount: Number(raw.assigned_device_count ?? raw.assignedDeviceCount ?? 0),
    lastAssignmentAt: raw.last_assignment_at ?? raw.lastAssignmentAt ?? null,
  };
}

/**
 * @param {Record<string, any>} raw
 * @returns {HubAssetDetail}
 */
function normalizeHubAssetDetail(raw = {}) {
  return {
    ...normalizeHubAsset(raw),
    hubId: raw.hub_id ?? raw.hubId ?? "",
    hubCode: raw.hub_code ?? raw.hubCode ?? "",
    hubName: raw.hub_name ?? raw.hubName ?? "",
    devices: Array.isArray(raw.devices) ? raw.devices.map(normalizeHubDevice) : [],
  };
}

/**
 * Fetch hubs list.
 * @param {Record<string, any>} params
 * @returns {Promise<Hub[]>}
 */
export async function fetchHubs(params = {}) {
  const hasExplicitPage = Object.prototype.hasOwnProperty.call(params, "page");
  const pageSize = Number(params.limit ?? 200);

  if (hasExplicitPage) {
    const { data } = await apiClient.get("/hubs", { params });
    const hubs = Array.isArray(data?.data)
      ? data.data.map(normalizeHub)
      : Array.isArray(data)
        ? data.map(normalizeHub)
        : [];
    return hubs;
  }

  let page = 1;
  let total = null;
  const results = [];

  while (total === null || results.length < total) {
    const { data } = await apiClient.get("/hubs", {
      params: {
        ...params,
        page,
        limit: pageSize,
      },
    });
    const pageItems = Array.isArray(data?.data)
      ? data.data.map(normalizeHub)
      : Array.isArray(data)
        ? data.map(normalizeHub)
        : [];

    results.push(...pageItems);
    total = Number(data?.meta?.total ?? results.length);

    if (!pageItems.length || pageItems.length < pageSize) {
      break;
    }
    page += 1;
  }

  return results;
}

/**
 * Fetch a single hubs page with server-side filters/sort.
 * @param {Record<string, any>} params
 * @returns {Promise<{items: Hub[]; meta: {page: number; per_page: number; total: number}}>}
 */
export async function fetchHubsPage(params = {}) {
  const { data } = await apiClient.get("/hubs", { params });
  const items = Array.isArray(data?.data)
    ? data.data.map(normalizeHub)
    : Array.isArray(data)
      ? data.map(normalizeHub)
      : [];
  return {
    items,
    meta: {
      page: Number(data?.meta?.page ?? params.page ?? 1),
      per_page: Number(data?.meta?.per_page ?? params.limit ?? items.length),
      total: Number(data?.meta?.total ?? items.length),
    },
  };
}

/**
 * Fetch a single hub.
 * @param {string} hubId
 * @returns {Promise<Hub>}
 */
export async function fetchHubById(hubId) {
  if (!hubId) {
    throw new Error("Hub ID is required");
  }
  const { data } = await apiClient.get(`/hubs/${hubId}`);
  const payload = data?.data ?? data;
  return normalizeHub(payload ?? { id: hubId });
}

/**
 * Fetch assets for a single hub.
 * @param {string} hubId
 * @param {Record<string, any>} params
 * @returns {Promise<{items: HubAsset[], meta: {page: number, perPage: number, total: number}}>}
 */
export async function fetchHubAssets(hubId, params = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required");
  }
  const normalizedParams = {
    ...params,
    limit:
      typeof params?.limit === "number"
        ? Math.min(Math.max(params.limit, 1), 100)
        : params?.limit,
  };
  const { data } = await apiClient.get(`/hubs/${hubId}/assets`, { params: normalizedParams });
  const payload = Array.isArray(data?.data?.items)
    ? data.data.items
    : Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data?.data)
        ? data.data
        : Array.isArray(data)
          ? data
          : [];
  return {
    items: payload.map(normalizeHubAsset),
    meta: {
      page: Number(data?.meta?.page ?? params?.page ?? 1),
      perPage: Number(data?.meta?.per_page ?? normalizedParams.limit ?? payload.length),
      total: Number(data?.meta?.total ?? payload.length),
    },
  };
}

/**
 * Fetch lightweight asset options for assignment workflows.
 * @param {string} hubId
 * @param {Record<string, any>} params
 * @returns {Promise<{items: HubAsset[], meta: {page: number, perPage: number, total: number}}>}
 */
export async function fetchHubAssetOptions(hubId, params = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required");
  }
  const normalizedParams = {
    ...params,
    limit:
      typeof params?.limit === "number"
        ? Math.min(Math.max(params.limit, 1), 100)
        : params?.limit,
  };
  const { data } = await apiClient.get(`/hubs/${hubId}/assets/options`, { params: normalizedParams });
  const payload = Array.isArray(data?.data?.items)
    ? data.data.items
    : Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data?.data)
        ? data.data
        : Array.isArray(data)
          ? data
          : [];
  return {
    items: payload.map(normalizeHubAsset),
    meta: {
      page: Number(data?.meta?.page ?? params?.page ?? 1),
      perPage: Number(data?.meta?.per_page ?? normalizedParams.limit ?? payload.length),
      total: Number(data?.meta?.total ?? payload.length),
    },
  };
}

export async function createHubAsset(hubId, payload = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required");
  }
  const requestBody = {
    asset_type: payload.assetType,
    asset_name: payload.assetName,
    asset_type_other: payload.assetTypeOther ?? undefined,
    registration: payload.registration ?? undefined,
    vin: payload.vin ?? undefined,
    make: payload.make ?? undefined,
    model: payload.model ?? undefined,
    year: payload.year ?? undefined,
    color: payload.color ?? undefined,
    engine_capacity: payload.engineCapacity ?? undefined,
    co2_emissions: payload.co2Emissions ?? undefined,
    fuel_type: payload.fuelType ?? undefined,
    notes: payload.notes ?? undefined,
    source_job_id: payload.sourceJobId ?? undefined,
    hardware_ids: Array.isArray(payload.hardwareIds) ? payload.hardwareIds.map(Number) : [],
    hardware_assignments: Array.isArray(payload.hardwareAssignments)
      ? payload.hardwareAssignments
          .map((item) => ({
            hardware_id: Number(item?.hardwareId),
            sim_id: item?.simId ? Number(item.simId) : undefined,
          }))
          .filter((item) => Number.isFinite(item.hardware_id))
      : [],
  };
  const { data } = await apiClient.post(`/hubs/${hubId}/assets`, requestBody);
  return normalizeHubAssetDetail(data?.data ?? data ?? requestBody);
}

/**
 * Fetch one asset with its assigned devices.
 * @param {string} hubId
 * @param {string} assetId
 * @returns {Promise<HubAssetDetail>}
 */
export async function fetchHubAssetDetail(hubId, assetId) {
  if (!hubId || !assetId) {
    throw new Error("Hub ID and asset ID are required");
  }
  const { data } = await apiClient.get(`/hubs/${hubId}/assets/${assetId}`);
  return normalizeHubAssetDetail(data?.data ?? data ?? {});
}

export async function updateHubAsset(hubId, assetId, payload = {}) {
  if (!hubId || !assetId) {
    throw new Error("Hub ID and asset ID are required");
  }
  const normalizeEmpty = (value) => {
    if (value === undefined || value === null) return undefined;
    if (typeof value === "string" && value.trim() === "") return undefined;
    return value;
  };
  const requestBody = {
    asset_type: normalizeEmpty(payload.assetType),
    asset_name: normalizeEmpty(payload.assetName),
    asset_type_other: normalizeEmpty(payload.assetTypeOther),
    registration: normalizeEmpty(payload.registration),
    vin: normalizeEmpty(payload.vin),
    make: normalizeEmpty(payload.make),
    model: normalizeEmpty(payload.model),
    year: normalizeEmpty(payload.year),
    color: normalizeEmpty(payload.color),
    engine_capacity: normalizeEmpty(payload.engineCapacity),
    co2_emissions: normalizeEmpty(payload.co2Emissions),
    fuel_type: normalizeEmpty(payload.fuelType),
    notes: normalizeEmpty(payload.notes),
  };
  const { data } = await apiClient.patch(`/hubs/${hubId}/assets/${assetId}`, requestBody);
  return normalizeHubAssetDetail(data?.data ?? data ?? {});
}

export async function decodeAssetVin(vin) {
  const normalizedVin = `${vin ?? ""}`.trim().toUpperCase();
  if (!normalizedVin) {
    throw new Error("VIN is required");
  }
  const { data } = await apiClient.post("/hubs/vin/decode", { vin: normalizedVin });
  return data?.data ?? data ?? null;
}

/**
 * Create a new hub.
 * @param {Partial<Hub>} payload
 * @returns {Promise<Hub>}
 */
export async function createHub(payload) {
  const requestBody = {
    name: payload.name,
    code: payload.code,
    type: payload.type,
    tier: payload.tier,
    currency: payload.currency,
    payment_method: payload.paymentMethod,
    billing_cycle: payload.billingCycle,
    primary_contact_name: payload.primaryContact?.name,
    primary_contact_email: payload.primaryContact?.email,
    primary_contact_phone: payload.primaryContact?.phone,
    billing_contact_name: payload.billingContact?.name,
    billing_contact_email: payload.billingContact?.email,
    billing_contact_phone: payload.billingContact?.phone,
    timezone: payload.timezone,
    country: payload.country,
    city: payload.city,
    address_line: payload.address,
    go_live_date: payload.goLiveDate,
    notes: payload.notes,
    users: payload.users ?? [],
  };

  const { data } = await apiClient.post("/hubs", requestBody);
  const payloadData = data?.data ?? data;
  return normalizeHub(payloadData ?? requestBody);
}

/**
 * Update an existing hub.
 * @param {string} hubId
 * @param {Partial<Hub>} payload
 * @returns {Promise<Hub>}
 */
export async function updateHub(hubId, payload = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required to update");
  }
  const normalizeEmpty = (value) => {
    if (value === undefined || value === null) return undefined;
    if (typeof value === "string" && value.trim() === "") return undefined;
    return value;
  };
  const requestBody = {
    name: normalizeEmpty(payload.name),
    type: normalizeEmpty(payload.type),
    tier: normalizeEmpty(payload.tier),
    currency: normalizeEmpty(payload.currency),
    payment_method: normalizeEmpty(payload.paymentMethod),
    billing_cycle: normalizeEmpty(payload.billingCycle),
    primary_contact_name: normalizeEmpty(payload.primaryContact?.name),
    primary_contact_email: normalizeEmpty(payload.primaryContact?.email),
    primary_contact_phone: normalizeEmpty(payload.primaryContact?.phone),
    billing_contact_name: normalizeEmpty(payload.billingContact?.name),
    billing_contact_email: normalizeEmpty(payload.billingContact?.email),
    billing_contact_phone: normalizeEmpty(payload.billingContact?.phone),
    timezone: normalizeEmpty(payload.timezone),
    country: normalizeEmpty(payload.country),
    city: normalizeEmpty(payload.city),
    address_line: normalizeEmpty(payload.address),
    go_live_date: normalizeEmpty(payload.goLiveDate),
    notes: payload.notes,
    status: payload.status,
    days_left:
      payload.subscriptionDaysLeft === null || payload.subscriptionDaysLeft === undefined
        ? undefined
        : Number(payload.subscriptionDaysLeft),
    subscription_start_date: normalizeEmpty(payload.subscriptionStartDate),
    subscription_end_date: normalizeEmpty(payload.subscriptionEndDate),
  };
  const { data } = await apiClient.patch(`/hubs/${hubId}`, requestBody);
  const payloadData = data?.data ?? data;
  return normalizeHub(payloadData ?? { ...payload, id: hubId });
}

/**
 * Invite a new user to a hub.
 * @param {string} hubId
 * @param {Partial<HubUser>} payload
 * @returns {Promise<HubUser>}
 */
export async function createHubUser(hubId, payload = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required for user creation");
  }
  const requestBody = {
    name: payload.name,
    email: payload.email,
    role: payload.role,
    password: payload.password,
  };
  const { data } = await apiClient.post(`/hubs/${hubId}/users`, requestBody);
  const userData = data?.data ?? data ?? requestBody;
  return {
    id: userData.id ?? globalThis.crypto?.randomUUID?.() ?? `hub-user-${Date.now()}`,
    name: userData.name ?? requestBody.name,
    email: userData.email ?? requestBody.email,
    role: userData.role ?? requestBody.role,
  };
}

/**
 * Update an existing user in a hub.
 * @param {string} hubId
 * @param {string} userId
 * @param {Partial<HubUser> & {password?: string}} payload
 * @returns {Promise<HubUser>}
 */
export async function updateHubUser(hubId, userId, payload = {}) {
  if (!hubId) {
    throw new Error("Hub ID is required for user update");
  }
  if (!userId) {
    throw new Error("User ID is required for user update");
  }
  const requestBody = {
    name: payload.name,
    email: payload.email,
    role: payload.role,
    password: payload.password || undefined,
  };
  const { data } = await apiClient.patch(`/hubs/${hubId}/users/${userId}`, requestBody);
  const userData = data?.data ?? data ?? requestBody;
  return {
    id: userData.id ?? userId,
    name: userData.name ?? requestBody.name ?? "",
    email: userData.email ?? requestBody.email ?? "",
    role: userData.role ?? requestBody.role ?? "client",
  };
}

/**
 * Delete a single hub.
 * @param {string} hubId
 * @returns {Promise<void>}
 */
export async function deleteHub(hubId) {
  if (!hubId) {
    throw new Error("Hub ID is required to delete");
  }
  await apiClient.delete(`/hubs/${hubId}`);
}

/**
 * Delete multiple hubs.
 * @param {string[]} hubIds
 * @returns {Promise<{deleted:number;requested:number;deletedIds:string[];notFound:string[]}>}
 */
export async function bulkDeleteHubs(hubIds = []) {
  const validIds = hubIds.filter(Boolean);
  if (!validIds.length) {
    return { deleted: 0, requested: 0, deletedIds: [], notFound: [] };
  }
  const { data } = await apiClient.post("/hubs/bulk-delete", { hub_ids: validIds });
  return {
    deleted: Number(data?.deleted ?? 0),
    requested: Number(data?.requested ?? validIds.length),
    deletedIds: Array.isArray(data?.deleted_ids) ? data.deleted_ids : [],
    notFound: Array.isArray(data?.not_found) ? data.not_found : [],
  };
}

/**
 * List hubs currently in recycle bin.
 * @returns {Promise<Array<{id:string;name:string;code:string;deleted_at?:string|null;recycle_bin_expires_at?:string|null;days_until_purge?:number|null}>>}
 */
export async function fetchRecycleBinHubs() {
  const { data } = await apiClient.get("/hubs/recycle-bin/items");
  return Array.isArray(data?.items) ? data.items : [];
}

/**
 * Restore a hub from recycle bin.
 * @param {string} hubId
 * @returns {Promise<Hub>}
 */
export async function restoreHubFromRecycleBin(hubId) {
  if (!hubId) {
    throw new Error("Hub ID is required to restore");
  }
  const { data } = await apiClient.post(`/hubs/${hubId}/restore`);
  const payloadData = data?.data ?? data;
  return normalizeHub(payloadData ?? { id: hubId });
}

/**
 * Permanently delete a hub from recycle bin.
 * @param {string} hubId
 * @returns {Promise<void>}
 */
export async function purgeHubFromRecycleBin(hubId) {
  if (!hubId) {
    throw new Error("Hub ID is required to purge");
  }
  await apiClient.delete(`/hubs/${hubId}/purge`);
}
