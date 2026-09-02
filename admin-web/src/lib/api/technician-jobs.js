import apiClient from "$lib/api/http";

function normalizeJob(raw = {}) {
  return {
    id: raw.id ?? null,
    hubId: raw.hub_id ?? null,
    hubCode: raw.hub_code ?? "",
    hubName: raw.hub_name ?? "",
    hardwareId: raw.hardware_id ?? null,
    hardwareImei: raw.hardware_imei ?? "",
    hardwareModel: raw.hardware_model ?? "",
    vehicleId: raw.vehicle_id ?? null,
    assignedTechnicianId: raw.assigned_technician_id ?? null,
    assignedTechnicianName: raw.assigned_technician_name ?? "",
    assignedTechnicianEmail: raw.assigned_technician_email ?? "",
    requestedById: raw.requested_by_id ?? null,
    requestedByName: raw.requested_by_name ?? "",
    status: raw.status ?? "pending",
    priority: raw.priority ?? "normal",
    scheduledFor: raw.scheduled_for ?? null,
    startedAt: raw.started_at ?? null,
    acceptedAt: raw.accepted_at ?? null,
    completedAt: raw.completed_at ?? null,
    cancelledAt: raw.cancelled_at ?? null,
    declinedAt: raw.declined_at ?? null,
    installedAt: raw.installed_at ?? null,
    installationLocation: raw.installation_location ?? "",
    installationLatitude: raw.installation_latitude ?? null,
    installationLongitude: raw.installation_longitude ?? null,
    assetLabel: raw.asset_label ?? "",
    assetRegistration: raw.asset_registration ?? "",
    notes: raw.notes ?? "",
    completionNotes: raw.completion_notes ?? "",
    declineReason: raw.decline_reason ?? "",
    assignmentReference: raw.assignment_reference ?? "",
    createdAt: raw.created_at ?? null,
    updatedAt: raw.updated_at ?? null,
  };
}

export async function fetchTechnicianJobs(params = {}) {
  const { data } = await apiClient.get("/technician-jobs", { params });
  const items = Array.isArray(data?.items) ? data.items.map(normalizeJob) : [];
  const meta = data?.meta ?? { page: 1, per_page: items.length, total: items.length };
  return { items, meta };
}

export async function fetchTechnicians() {
  const { data } = await apiClient.get("/users/technicians");
  return Array.isArray(data)
    ? data.map((item) => ({
        id: item.id ?? null,
        name: item.name ?? "",
        email: item.email ?? "",
        role: item.role ?? "technician",
      }))
    : [];
}

export async function createTechnicianJob(payload = {}) {
  const requestBody = {
    hub_id: payload.hubId,
    hardware_id: payload.hardwareId ? Number(payload.hardwareId) : undefined,
    vehicle_id: payload.vehicleId ?? undefined,
    assigned_technician_id: payload.assignedTechnicianId ?? undefined,
    priority: payload.priority ?? "normal",
    scheduled_for: payload.scheduledFor ?? undefined,
    installed_at: payload.installedAt ?? undefined,
    installation_location: payload.installationLocation ?? undefined,
    installation_latitude: payload.installationLatitude ?? undefined,
    installation_longitude: payload.installationLongitude ?? undefined,
    asset_label: payload.assetLabel ?? undefined,
    asset_registration: payload.assetRegistration ?? undefined,
    notes: payload.notes ?? undefined,
  };
  const { data } = await apiClient.post("/technician-jobs", requestBody);
  return normalizeJob(data ?? requestBody);
}

export async function updateTechnicianJob(jobId, payload = {}) {
  if (!jobId) {
    throw new Error("jobId is required");
  }
  const requestBody = {
    status: payload.status ?? undefined,
    assigned_technician_id: payload.assignedTechnicianId ?? undefined,
    priority: payload.priority ?? undefined,
    scheduled_for: payload.scheduledFor ?? undefined,
    installed_at: payload.installedAt ?? undefined,
    installation_location: payload.installationLocation ?? undefined,
    installation_latitude: payload.installationLatitude ?? undefined,
    installation_longitude: payload.installationLongitude ?? undefined,
    asset_label: payload.assetLabel ?? undefined,
    asset_registration: payload.assetRegistration ?? undefined,
    notes: payload.notes ?? undefined,
    completion_notes: payload.completionNotes ?? undefined,
    decline_reason: payload.declineReason ?? undefined,
  };
  const { data } = await apiClient.patch(`/technician-jobs/${jobId}`, requestBody);
  return normalizeJob(data ?? { id: jobId, ...requestBody });
}
