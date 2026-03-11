import { DashboardShell } from "@/components/dashboard-shell";
import { requireSession } from "@/lib/session";

export default async function DashboardPage() {
  await requireSession();
  return <DashboardShell />;
}
