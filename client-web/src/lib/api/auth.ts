const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export type LoginPayload = {
  email: string;
  password: string;
  hubCode: string;
};

export type LoginHub = {
  id: string;
  code: string;
  name: string;
  role?: string;
  subscription_tier?: string;
  status?: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type: string;
  roles?: string[];
  hubs?: LoginHub[];
  current_hub_id?: string;
  hub_id?: string;
  hub_code?: string;
  hub_name?: string;
};

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/users/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      hub_code: payload.hubCode.trim().toUpperCase(),
    }),
  });

  if (response.ok) {
    return response.json();
  }

  let message = "Unable to sign in";
  try {
    const errorBody = await response.json();
    if (typeof errorBody?.detail === "string") {
      message = errorBody.detail;
    }
  } catch (error) {
    // Ignore JSON parsing errors and fall back to default message.
  }
  throw new Error(message);
}

export async function refreshSession(refreshToken: string) {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    throw new Error("Unable to refresh session");
  }
  return response.json();
}

export async function logout(refreshToken?: string) {
  await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken ?? null }),
  });
}
