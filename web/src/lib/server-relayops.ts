import { cookies } from "next/headers";

import type { AccountResponse, HealthResponse, IntegrationItem, OverviewResponse } from "@/lib/relayops";

const backendBaseUrl = process.env.RELAYOPS_BACKEND_URL ?? "http://127.0.0.1:8022";

export type DashboardInitialState = {
  overview: OverviewResponse | null;
  health: HealthResponse | null;
  integrations: IntegrationItem[];
  account: AccountResponse | null;
};

async function serverRelayFetch(path: string) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");

  return fetch(`${backendBaseUrl}${path}`, {
    headers: cookieHeader ? { cookie: cookieHeader } : undefined,
    cache: "no-store",
  });
}

export async function getDashboardInitialState(): Promise<DashboardInitialState> {
  const [accountResponse, overviewResponse, healthResponse, integrationResponse] = await Promise.all([
    serverRelayFetch("/api/account"),
    serverRelayFetch("/api/overview"),
    serverRelayFetch("/api/health"),
    serverRelayFetch("/api/integrations"),
  ]);

  if (!accountResponse.ok || !overviewResponse.ok || !healthResponse.ok || !integrationResponse.ok) {
    return {
      account: null,
      overview: null,
      health: null,
      integrations: [],
    };
  }

  const [account, overview, health, integrations] = await Promise.all([
    accountResponse.json() as Promise<AccountResponse>,
    overviewResponse.json() as Promise<OverviewResponse>,
    healthResponse.json() as Promise<HealthResponse>,
    integrationResponse.json() as Promise<{ items: IntegrationItem[] }>,
  ]);

  return {
    account,
    overview,
    health,
    integrations: integrations.items,
  };
}
