import { DashboardShell } from "@/components/dashboard-shell";
import { getDashboardInitialState } from "@/lib/server-relayops";
import { requireSession } from "@/lib/session";

export default async function DashboardPage() {
  await requireSession();
  const initialState = await getDashboardInitialState();
  return <DashboardShell initialState={initialState} />;
}
