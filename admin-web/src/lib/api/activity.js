import apiClient from "$lib/api/http";

export async function fetchAdminActivity(limit = 50) {
  const { data } = await apiClient.get("/admin/activity", { params: { limit } });
  return Array.isArray(data?.items) ? data.items : [];
}

export async function fetchAdminActivityIntegrity(limit = 500) {
  const { data } = await apiClient.get("/admin/activity/integrity", { params: { limit } });
  return data ?? {};
}
