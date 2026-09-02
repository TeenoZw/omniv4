import apiClient from "$lib/api/http";

function normalizeVehicle(raw = {}) {
  const labelCandidate =
    raw.label ??
    raw.display_label ??
    raw.license_plate ??
    raw.licensePlate ??
    raw.vin ??
    `${raw.make ?? "Omni"} ${raw.model ?? "Vehicle"}`;

  return {
    id: raw.id ?? raw.vehicle_id ?? null,
    label: labelCandidate,
    licensePlate: raw.license_plate ?? raw.licensePlate ?? labelCandidate,
    vin: raw.vin ?? null,
    make: raw.make ?? null,
    model: raw.model ?? null,
    status: raw.status ?? raw.vehicle_status ?? "active",
    hubId: raw.hub_id ?? raw.hubId ?? null,
    hubName: raw.hub_name ?? raw.hubName ?? null,
  };
}

export async function fetchHubVehicles(params = {}) {
  const response = await apiClient.get("/vehicles", { params });
  const payload = response?.data ?? {};
  const rawVehicles = Array.isArray(payload.vehicles)
    ? payload.vehicles
    : Array.isArray(payload.data)
      ? payload.data
      : [];

  return {
    total: payload.total ?? rawVehicles.length,
    vehicles: rawVehicles.map((vehicle) => normalizeVehicle(vehicle)),
  };
}

export { normalizeVehicle };
