const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export type PublicStats = {
  active_users: number;
  active_assets: number;
  provinces_served: number;
  total_hubs: number;
};

export async function fetchPublicStats(): Promise<PublicStats> {
  const response = await fetch(`${API_BASE}/admin/stats/public`);
  if (!response.ok) {
    throw new Error(`Failed to fetch public stats (${response.status})`);
  }
  const payload = await response.json();
  const metrics = payload?.metrics ?? {};
  return {
    active_users: Number(metrics.active_users) || 0,
    active_assets: Number(metrics.active_assets) || 0,
    provinces_served: Number(metrics.provinces_served) || 0,
    total_hubs: Number(metrics.total_hubs) || 0,
  };
}
