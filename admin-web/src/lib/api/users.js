import apiClient from "$lib/api/http";

function mapUser(user) {
  return {
    id: user.id,
    name: user.name ?? "",
    email: user.email ?? "",
    role: (user.role ?? "client").toString().toLowerCase(),
    isActive: Boolean(user.is_active ?? user.isActive ?? true),
  };
}

export async function fetchUsers() {
  const { data } = await apiClient.get("/users");
  const payload = Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : [];
  return payload.map(mapUser);
}

export async function createSystemUser(payload) {
  const { data } = await apiClient.post("/users/register", payload);
  return mapUser(data);
}

export async function updateSystemUser(userId, payload) {
  const { data } = await apiClient.patch(`/users/${userId}`, payload);
  return mapUser(data);
}

export async function deactivateSystemUser(userId) {
  await apiClient.delete(`/users/${userId}`);
}
