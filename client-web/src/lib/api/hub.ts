import { getAuthHeaders } from "$lib/api/session";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export type HubSummaryResponse = {
  hub: {
    id: string;
    name: string;
    code: string;
    type: string;
    tier: string;
    timezone?: string | null;
    location?: {
      country?: string | null;
      city?: string | null;
      address?: string | null;
    };
  };
  subscription: {
    status: string;
    tier: string;
    start_date?: string | null;
    end_date?: string | null;
    days_left?: number | null;
    billing_cycle?: string | null;
  };
  metrics: {
    active_users: number;
    assets: number;
    active_devices: number;
    vehicles: number;
  };
  viewer: {
    role: string;
    features: string[];
  };
};

export type HubAssetDevice = {
  assignment_id?: number | null;
  hardware_id?: number | null;
  imei: string;
  serial_number?: string | null;
  model?: string | null;
  hardware_type?: string | null;
  manufacturer?: string | null;
  firmware_version?: string | null;
  status?: string | null;
  asset_label?: string | null;
  asset_registration?: string | null;
  installation_location?: string | null;
  technician?: string | null;
  assigned_at?: string | null;
  installed_at?: string | null;
  vehicle_id?: string | null;
  vehicle_label?: string | null;
  sim?: {
    id?: number | null;
    iccid?: string | null;
    msisdn?: string | null;
    carrier?: string | null;
    roaming_enabled?: boolean | null;
    status?: string | null;
  } | null;
  assignment_history?: Array<{
    id: number;
    target?: string | null;
    hub_id?: string | null;
    hub_name?: string | null;
    vehicle_id?: string | null;
    vehicle_label?: string | null;
    technician?: string | null;
    assigned_at?: string | null;
    installed_at?: string | null;
    unassigned_at?: string | null;
    installation_location?: string | null;
    installation_latitude?: number | null;
    installation_longitude?: number | null;
    asset_label?: string | null;
    asset_registration?: string | null;
    notes?: string | null;
    is_active?: boolean;
    sim_id?: number | null;
    sim_iccid?: string | null;
    sim_msisdn?: string | null;
    sim_carrier?: string | null;
    sim_roaming_enabled?: boolean | null;
  }>;
};

export type HubAsset = {
  id: string;
  asset_type?: string | null;
  asset_name?: string | null;
  asset_type_other?: string | null;
  registration?: string | null;
  label?: string | null;
  vin?: string | null;
  make?: string | null;
  model?: string | null;
  year?: string | null;
  color?: string | null;
  engine_capacity?: string | null;
  co2_emissions?: string | null;
  fuel_type?: string | null;
  status?: string | null;
  notes?: string | null;
  tracking_state?: string | null;
  source_job_id?: string | null;
  assigned_device_count: number;
  last_assignment_at?: string | null;
};

export type HubAssetDetail = HubAsset & {
  hub_id: string;
  hub_code: string;
  hub_name: string;
  devices: HubAssetDevice[];
};

export type HubAssetListResponse = {
  data: {
    items: HubAsset[];
  };
  meta: {
    page: number;
    per_page: number;
    total: number;
  };
};

export async function fetchCurrentHubSummary(): Promise<HubSummaryResponse> {
  const response = await fetch(`${API_BASE}/hubs/current/summary`, {
    method: "GET",
    headers: getAuthHeaders(),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Unable to load hub summary";
    try {
      const errorPayload = await response.json();
      if (typeof errorPayload?.detail === "string") {
        detail = errorPayload.detail;
      }
    } catch {
      // no-op
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchCurrentHubAssets(params: {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
} = {}): Promise<HubAssetListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.limit) query.set("limit", String(params.limit));
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  const url = `${API_BASE}/hubs/current/assets${query.size ? `?${query.toString()}` : ""}`;
  const response = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Unable to load hub assets";
    try {
      const errorPayload = await response.json();
      if (typeof errorPayload?.detail === "string") {
        detail = errorPayload.detail;
      }
    } catch {
      // no-op
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchCurrentHubAssetDetail(assetId: string): Promise<HubAssetDetail> {
  const response = await fetch(`${API_BASE}/hubs/current/assets/${assetId}`, {
    method: "GET",
    headers: getAuthHeaders(),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Unable to load asset details";
    try {
      const errorPayload = await response.json();
      if (typeof errorPayload?.detail === "string") {
        detail = errorPayload.detail;
      }
    } catch {
      // no-op
    }
    throw new Error(detail);
  }

  return response.json();
}
