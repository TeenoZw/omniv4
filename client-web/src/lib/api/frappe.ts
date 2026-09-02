export const FRAPPE_API_BASE = import.meta.env.VITE_API_URL || "http://development.localhost:8000/api/method";

export type FrappeCallOptions = {
  params?: Record<string, string | number | boolean | null | undefined>;
  method?: "GET" | "POST";
  body?: Record<string, unknown>;
};

function buildUrl(methodPath: string, params: FrappeCallOptions["params"] = {}) {
  const normalizedBase = FRAPPE_API_BASE.replace(/\/$/, "");
  const normalizedPath = methodPath.replace(/^\//, "");
  const url = new URL(`${normalizedBase}/${normalizedPath}`);

  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

async function readError(response: Response) {
  try {
    const payload = await response.json();
    const rawMessage =
      payload?._server_messages ??
      payload?.exception ??
      payload?.exc_type ??
      payload?.message?.error?.message ??
      payload?.message ??
      `Request failed (${response.status})`;
    return typeof rawMessage === "string" ? rawMessage : JSON.stringify(rawMessage);
  } catch {
    return `Request failed (${response.status})`;
  }
}

export async function frappeCall<T>(methodPath: string, options: FrappeCallOptions = {}): Promise<T> {
  const method = options.method ?? (options.body ? "POST" : "GET");
  const response = await fetch(buildUrl(methodPath, options.params), {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const payload = await response.json();
  return (payload?.message ?? payload) as T;
}

export async function frappeLogin(username: string, password: string) {
  const response = await fetch(buildUrl("login"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ usr: username, pwd: password }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json();
}
