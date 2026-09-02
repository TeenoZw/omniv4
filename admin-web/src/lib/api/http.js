import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    Pragma: "no-cache",
    Expires: "0",
  },
});

let authHooks = {
  getSession: () => null,
  saveSession: () => {},
  clearSession: () => {},
};
let refreshPromise = null;

export function registerAuthHooks(hooks = {}) {
  authHooks = {
    ...authHooks,
    ...hooks,
  };
}

/**
 * Updates the default Authorization and X-Hub-ID headers used by the shared axios instance.
 * @param {{ token?: string | null, hubId?: string | null }} params
 */
export function setSessionHeaders(params = {}) {
  const { token, hubId } = params;

  if (typeof token !== "undefined") {
    if (token) {
      apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common.Authorization;
    }
  }

  if (typeof hubId !== "undefined") {
    if (hubId) {
      apiClient.defaults.headers.common["X-Hub-ID"] = hubId;
    } else {
      delete apiClient.defaults.headers.common["X-Hub-ID"];
    }
  }
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

async function refreshAccessToken(refreshToken, hubId) {
  const response = await axios.post(
    `${API_BASE_URL}/auth/refresh`,
    { refresh_token: refreshToken },
    {
      headers: {
        "Content-Type": "application/json",
        ...(hubId ? { "X-Hub-ID": hubId } : {}),
      },
      timeout: 15000,
    },
  );
  return response.data;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config ?? {};
    const status = error?.response?.status;
    const requestUrl = String(originalRequest?.url ?? "");

    if (status !== 401) {
      return Promise.reject(error);
    }
    if (
      originalRequest?._retry ||
      requestUrl.includes("/users/login") ||
      requestUrl.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    const session = authHooks.getSession?.();
    if (!session?.refreshToken) {
      authHooks.clearSession?.();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken(session.refreshToken, session.currentHubId).finally(() => {
          refreshPromise = null;
        });
      }
      const refreshed = await refreshPromise;
      authHooks.saveSession?.({
        token: refreshed.access_token,
        refreshToken: refreshed.refresh_token ?? session.refreshToken,
        expiresIn: refreshed.expires_in,
      });

      const token = refreshed.access_token;
      originalRequest.headers = {
        ...(originalRequest.headers ?? {}),
        Authorization: `Bearer ${token}`,
      };
      return apiClient.request(originalRequest);
    } catch (refreshError) {
      authHooks.clearSession?.();
      return Promise.reject(refreshError);
    }
  },
);

apiClient.interceptors.request.use((config) => {
  const method = String(config.method ?? "get").toLowerCase();

  if (method === "get") {
    config.params = {
      ...(config.params ?? {}),
      _ts: Date.now(),
    };
  }

  config.headers = {
    ...(config.headers ?? {}),
    "Cache-Control": "no-cache, no-store, must-revalidate",
    Pragma: "no-cache",
    Expires: "0",
  };

  return config;
});

export default apiClient;
