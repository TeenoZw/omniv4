import apiClient from "$lib/api/http";

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export async function fetchAdminStats() {
  const { data } = await apiClient.get("/admin/stats");
  const payload = data ?? {};
  const metrics = payload.metrics ?? {};
  const hierarchy = Array.isArray(payload.hierarchy)
    ? payload.hierarchy.map((hub) => ({
        id: hub.id,
        name: hub.name,
        code: hub.code,
        tier: hub.tier,
        status: hub.status,
        users: hub.users ?? [],
        devices: hub.devices ?? [],
        deviceCount: toNumber(hub.device_count ?? hub.deviceCount),
      }))
    : [];

  return {
    updatedAt: payload.updated_at ?? new Date().toISOString(),
    totals: {
      hubs: toNumber(metrics.hubs),
      devices: toNumber(metrics.devices),
      users: toNumber(metrics.users),
      activeSubscriptions: toNumber(metrics.active_subscriptions),
      pendingEnquiries: toNumber(metrics.pending_enquiries),
      onboardedEnquiries: toNumber(metrics.onboarded_enquiries),
      sims: toNumber(metrics.sims),
      assignedSims: toNumber(metrics.assigned_sims),
      roamingEnabledSims: toNumber(metrics.roaming_enabled_sims),
      attentionSims: toNumber(metrics.attention_sims),
    },
    hierarchy,
    deviceStatus: payload.device_status ?? [],
  };
}
