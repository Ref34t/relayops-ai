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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(192,255,141,0.16),transparent_24%),linear-gradient(180deg,#09110d_0%,#132019_32%,#f2eadf_32%,#f7f4ec_100%)] px-5 py-6 md:px-8">
      <div className="mx-auto max-w-[1380px] space-y-6">
        <section className="relay-noise relative overflow-hidden rounded-[2.4rem] border border-white/10 bg-[#0c1712] px-7 py-8 text-white shadow-[0_36px_120px_rgba(0,0,0,0.24)] md:px-9">
          <div className="relative z-10 flex flex-wrap items-start justify-between gap-5">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-lime-200/80">Integrations</p>
              <h1 className="mt-4 font-[family-name:var(--font-display)] text-5xl tracking-[-0.05em] text-white md:text-6xl">
                Provider status, diagnostics, and loaded configuration.
              </h1>
              <p className="mt-5 max-w-2xl text-sm leading-8 text-white/68">
                Review provider availability, validate configured integrations, and confirm the runtime values loaded
                by the current workspace.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href="/dashboard">
                <Button variant="outline" className="h-11 rounded-full border-white/15 bg-white/5 px-5 text-sm text-white hover:bg-white/10">
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

        <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="grid gap-4 md:grid-cols-2">
            {items.map((item) => (
              <article key={item.provider} className="rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_18px_50px_rgba(0,0,0,0.06)]">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">{item.provider}</p>
                  <span className="rounded-full border border-stone-200 bg-stone-100 px-3 py-1 text-xs uppercase tracking-[0.18em] text-stone-700">
                    {item.mode}
                  </span>
                </div>
                <p className="mt-4 text-sm leading-7 text-stone-700">{item.detail}</p>
                {item.action ? <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">{item.action}</p> : null}
              </article>
            ))}
          </div>

          <div className="space-y-4 rounded-[2.2rem] border border-white/10 bg-[#0d1712] p-6 text-white shadow-[0_26px_90px_rgba(0,0,0,0.22)]">
            <StatusCard icon={<Orbit className="size-4" />} title="Status" value={status} />
            <StatusCard icon={<Gauge className="size-4" />} title="API endpoint" value={apiBaseUrl() || "Same-origin proxy"} />
            <StatusCard
              icon={<ShieldAlert className="size-4" />}
              title="Behavior"
              value="Unavailable providers remain visible in settings, while workflow execution continues with the providers that are configured."
            />
          </div>
        </section>

        <section className="rounded-[2.2rem] border border-stone-200 bg-white p-6 shadow-[0_22px_80px_rgba(0,0,0,0.08)]">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Runtime configuration</p>
            <h2 className="mt-4 font-[family-name:var(--font-display)] text-4xl tracking-[-0.05em] text-stone-950">
              Loaded credentials and environment values.
            </h2>
            <p className="mt-4 text-sm leading-7 text-stone-700">
              Sensitive values remain masked. This view is intended for operational verification only.
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {runtimeItems.map((item) => (
              <article key={item.env_var} className="rounded-[1.7rem] border border-stone-200 bg-[#fcfbf7] p-5">
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
                <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-stone-400">{item.env_var}</p>
                <p className="mt-3 break-all rounded-[1rem] bg-white px-3 py-3 font-mono text-sm text-stone-800">{item.preview}</p>
                <p className="mt-4 text-xs text-stone-500">{item.source}</p>
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
    <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-5">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/50">
        {icon}
        {title}
      </div>
      <p className="mt-4 text-sm leading-7 text-white/84">{value}</p>
    </div>
  );
}
