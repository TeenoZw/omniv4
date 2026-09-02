import apiClient from "$lib/api/http";

/**
 * @typedef {Object} LoginPayload
 * @property {string} email
 * @property {string} password
 * @property {string=} hubCode
 */

/**
 * @typedef {Object} LoginResponse
 * @property {string} access_token
 * @property {string} refresh_token
 * @property {{ id: string; name: string; email: string; avatar_url?: string }} user
 * @property {Array<{ id: string; name: string; role: string }>} hubs
 * @property {Array<string>} roles
 * @property {string=} default_hub_id
 */

/**
 * @param {LoginPayload} payload
 * @returns {Promise<LoginResponse>}
 */
export async function login(payload) {
  const requestBody = {
    email: payload.email,
    password: payload.password,
  };

  if (payload.hubCode) {
    requestBody.hub_code = payload.hubCode;
  }

  const { data } = await apiClient.post("/users/login", requestBody);

  const userName = data.user_name ?? payload?.email?.split("@")?.[0] ?? "Omni Admin";
  const normalizedUser = {
    id: data.user_id ?? payload.email,
    email: payload.email,
    name: userName,
  };

  const normalizePlan = (value) => {
    const normalized = (value ?? "").toString().trim();
    if (!normalized) return "Individual";
    const lowered = normalized.toLowerCase();
    if (["basic", "free", "individual"].includes(lowered)) return "Individual";
    if (["pro", "enterprise", "business"].includes(lowered)) return "Business";
    return normalized.charAt(0).toUpperCase() + normalized.slice(1).toLowerCase();
  };

  const preferredTier = normalizePlan(data.subscription_tier ?? data.tier ?? data.plan ?? "Individual");

  const normalizeHub = (hubCandidate) => {
    if (!hubCandidate) {
      return null;
    }

    const tierValue =
      hubCandidate.subscription_tier ??
      hubCandidate.tier ??
      hubCandidate.plan ??
      preferredTier;

    return {
      id: hubCandidate.id ?? hubCandidate.hub_id ?? hubCandidate.code ?? hubCandidate.slug ?? null,
      name: hubCandidate.name ?? hubCandidate.label ?? hubCandidate.hub_name ?? "Primary Hub",
      role: hubCandidate.role ?? hubCandidate.permission ?? "viewer",
      tier: normalizePlan(tierValue),
    };
  };

  const hubs = Array.isArray(data.hubs)
    ? data.hubs.map(normalizeHub).filter(Boolean)
    : data.hub_id
      ? [
          normalizeHub({
            id: data.hub_id,
            name: data.hub_name ?? data.hub_code ?? "Primary Hub",
            role: data.hub_role ?? "admin",
            tier: preferredTier,
          }),
        ].filter(Boolean)
      : [];

  const derivedHubId = data.current_hub_id ?? data.hub_id ?? hubs[0]?.id ?? null;

  return {
    ...data,
    token: data.access_token,
    user: normalizedUser,
    hubs,
    currentHubId: derivedHubId,
    roles: data.roles ?? ["admin"],
  };
}

export async function logout(refreshToken = null) {
  try {
    const response = await apiClient.post("/auth/logout", {
      refresh_token: refreshToken,
    });
    return response.data;
  } catch (error) {
    if (error?.response?.status === 404) {
      return { skipped: true };
    }
    throw error;
  }
}

export async function refresh(refreshToken) {
  const response = await apiClient.post("/auth/refresh", {
    refresh_token: refreshToken,
  });
  return response.data;
}
