import { SettingsShell } from "@/components/settings-shell";
import { requireSession } from "@/lib/session";

export default async function SettingsPage() {
  await requireSession();
  return <SettingsShell />;
}
