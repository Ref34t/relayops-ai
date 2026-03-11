export type OverviewMetric = {
  label: string;
  value: string;
  detail: string;
};

export type IntegrationItem = {
  provider: string;
  enabled: boolean;
  mode: string;
  detail: string;
  action?: string | null;
};

export type RuntimeSettingItem = {
  provider: string;
  env_var: string;
  configured: boolean;
  preview: string;
  source: string;
};

export type AccountResponse = {
  account: {
    id: string;
    name: string;
    email: string;
    api_key: string;
  };
  auth_mode: "demo" | "session" | "api_key";
};

export type HealthResponse = {
  status: string;
  total_runs: number;
  completed_runs: number;
  sync_targets: number;
};

export type WorkflowRun = {
  id: string;
  source: string;
  score: number;
  status: string;
  summary: string;
  normalized: {
    company: string;
    contact_name: string;
    monthly_revenue: string;
    urgency: string;
    requested_systems: string[];
  };
  ai_analysis: {
    executive_title: string;
    risk_level: string;
    highlights: string[];
    next_steps: string[];
    automation_opportunities: string[];
  };
  audit_events: { stage: string; detail: string }[];
  sync_results: { target: string; status: string; latency_ms: number }[];
};

export type OverviewResponse = {
  title: string;
  subtitle: string;
  metrics: OverviewMetric[];
  capabilities: string[];
  recent_runs: WorkflowRun[];
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  name: string;
  email: string;
  password: string;
};

export type WorkflowPayload = {
  source: string;
  company: string;
  contact_name: string;
  email: string;
  requested_systems: string[];
  pain_points: string[];
  monthly_revenue: string;
  urgency: string;
  notes: string;
};

export const API_KEY_STORAGE = "relayops_api_key";

export function apiBaseUrl() {
  return process.env.NEXT_PUBLIC_RELAYOPS_API_BASE_URL ?? "";
}

export function authHeaders() {
  if (typeof window === "undefined") {
    return {};
  }

  const apiKey = window.localStorage.getItem(API_KEY_STORAGE);
  return apiKey ? { "X-RelayOps-Api-Key": apiKey } : {};
}

export async function relayFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  Object.entries(authHeaders()).forEach(([key, value]) => {
    if (value) {
      headers.set(key, value);
    }
  });

  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    credentials: "include",
    headers,
    cache: "no-store",
  });

  if (response.status === 401 && typeof window !== "undefined" && window.localStorage.getItem(API_KEY_STORAGE)) {
    window.localStorage.removeItem(API_KEY_STORAGE);
    return fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      credentials: "include",
      headers: init.headers ? new Headers(init.headers) : undefined,
      cache: "no-store",
    });
  }

  return response;
}
