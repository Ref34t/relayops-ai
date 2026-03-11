"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { startTransition, useEffect, useEffectEvent, useState } from "react";
import { ArrowLeft, Gauge, Orbit, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { IntegrationItem, RuntimeSettingItem, apiBaseUrl, relayFetch } from "@/lib/relayops";

export function SettingsShell() {
  const [items, setItems] = useState<IntegrationItem[]>([]);
  const [runtimeItems, setRuntimeItems] = useState<RuntimeSettingItem[]>([]);
  const [status, setStatus] = useState("Loading integration status...");

  async function load() {
    const [statusResponse, runtimeResponse] = await Promise.all([
      relayFetch("/api/integrations"),
      relayFetch("/api/integrations/runtime"),
    ]);
    if (!statusResponse.ok || !runtimeResponse.ok) {
      setStatus("Could not load integration status.");
      return;
    }
    const [statusData, runtimeData] = await Promise.all([
      statusResponse.json() as Promise<{ items: IntegrationItem[] }>,
      runtimeResponse.json() as Promise<{ items: RuntimeSettingItem[] }>,
    ]);
    setItems(statusData.items);
    setRuntimeItems(runtimeData.items);
    setStatus("Current integration status.");
  }

  const loadEvent = useEffectEvent(async () => {
    await load();
  });

  useEffect(() => {
    startTransition(() => {
      void loadEvent();
    });
  }, []);

  async function runChecks() {
    setStatus("Running diagnostics...");
    const response = await relayFetch("/api/integrations/check", { method: "POST" });
    if (!response.ok) {
      setStatus("Diagnostics failed.");
      return;
    }
    const data = (await response.json()) as { items: IntegrationItem[] };
    setItems(data.items);
    setStatus("Diagnostics complete.");
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(160deg,#f5f1e9_0%,#e7f3e1_48%,#0d1712_48%,#0d1712_100%)] px-5 py-6 text-stone-950 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-[2rem] border border-white/20 bg-white/85 p-6 shadow-[0_30px_90px_rgba(0,0,0,0.14)] backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Integrations</p>
              <h1 className="mt-3 font-[family-name:var(--font-display)] text-5xl tracking-[-0.04em]">Connection status across configured providers.</h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-stone-700">
                Review provider availability, run quick checks, and confirm which credentials are loaded in the current environment.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href="/dashboard">
                <Button variant="outline" className="h-11 rounded-full px-5 text-sm">
                  <ArrowLeft className="size-4" />
                  Dashboard
                </Button>
              </Link>
              <Button className="h-11 rounded-full px-5 text-sm" onClick={() => void runChecks()}>
                Run diagnostics
              </Button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="grid gap-4 md:grid-cols-2">
            {items.map((item) => (
              <article key={item.provider} className="rounded-[1.6rem] border border-stone-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">{item.provider}</p>
                  <span className="rounded-full border border-stone-200 bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.18em] text-stone-700">
                    {item.mode}
                  </span>
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-700">{item.detail}</p>
                {item.action ? <p className="mt-3 text-xs uppercase tracking-[0.16em] text-emerald-700">{item.action}</p> : null}
              </article>
            ))}
          </div>
          <div className="space-y-4 rounded-[1.8rem] border border-white/15 bg-[#0d1712] p-5 text-white shadow-[0_30px_90px_rgba(0,0,0,0.2)]">
            <StatusCard icon={<Orbit className="size-4" />} title="Status" value={status} />
            <StatusCard icon={<Gauge className="size-4" />} title="API endpoint" value={apiBaseUrl() || "Same-origin proxy"} />
            <StatusCard icon={<ShieldAlert className="size-4" />} title="Behavior" value="Providers that are not configured remain visible, but they do not affect workflow execution." />
          </div>
        </section>

        <section className="rounded-[1.8rem] border border-stone-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Runtime configuration</p>
          <h2 className="mt-3 font-[family-name:var(--font-display)] text-4xl tracking-[-0.04em]">Loaded credentials and environment values.</h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-700">
            Sensitive values stay masked. This section exists to confirm what is loaded, not to expose secrets.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {runtimeItems.map((item) => (
              <article key={item.env_var} className="rounded-[1.4rem] border border-stone-200 bg-[#fcfbf7] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-stone-500">{item.provider}</p>
                  <span
                    className={`rounded-full px-3 py-1 text-xs uppercase tracking-[0.16em] ${
                      item.configured ? "bg-emerald-100 text-emerald-800" : "bg-stone-200 text-stone-700"
                    }`}
                  >
                    {item.configured ? "loaded" : "missing"}
                  </span>
                </div>
                <p className="mt-3 text-xs uppercase tracking-[0.16em] text-stone-400">{item.env_var}</p>
                <p className="mt-2 break-all font-mono text-sm text-stone-800">{item.preview}</p>
                <p className="mt-3 text-xs text-stone-500">{item.source}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function StatusCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="rounded-[1.3rem] border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/55">
        {icon}
        {title}
      </div>
      <p className="mt-3 text-sm leading-6 text-white/85">{value}</p>
    </div>
  );
}
