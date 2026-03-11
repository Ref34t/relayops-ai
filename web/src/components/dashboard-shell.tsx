"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { startTransition, useEffect, useEffectEvent, useState } from "react";
import {
  Activity,
  ArrowRight,
  Bot,
  Cable,
  ChevronRight,
  Database,
  Radar,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  AccountResponse,
  API_KEY_STORAGE,
  HealthResponse,
  IntegrationItem,
  OverviewResponse,
  WorkflowPayload,
  relayFetch,
} from "@/lib/relayops";

type DashboardState = {
  overview: OverviewResponse | null;
  health: HealthResponse | null;
  integrations: IntegrationItem[];
  account: AccountResponse | null;
};

const emptyState: DashboardState = {
  overview: null,
  health: null,
  integrations: [],
  account: null,
};

export function DashboardShell() {
  const router = useRouter();
  const [state, setState] = useState<DashboardState>(emptyState);
  const [loading, setLoading] = useState(true);
  const [workflowStatus, setWorkflowStatus] = useState("");

  async function load() {
    setLoading(true);
    const [accountResponse, overviewResponse, healthResponse, integrationResponse] = await Promise.all([
      relayFetch("/api/account"),
      relayFetch("/api/overview"),
      relayFetch("/api/health"),
      relayFetch("/api/integrations"),
    ]);

    if (!accountResponse.ok || !overviewResponse.ok || !healthResponse.ok || !integrationResponse.ok) {
      setLoading(false);
      return;
    }

    const [account, overview, health, integrations] = await Promise.all([
      accountResponse.json() as Promise<AccountResponse>,
      overviewResponse.json() as Promise<OverviewResponse>,
      healthResponse.json() as Promise<HealthResponse>,
      integrationResponse.json() as Promise<{ items: IntegrationItem[] }>,
    ]);

    setState({
      account,
      overview,
      health,
      integrations: integrations.items,
    });
    setLoading(false);

    if (account.auth_mode !== "session") {
      router.replace("/signin");
      router.refresh();
    }
  }

  const loadEvent = useEffectEvent(async () => {
    await load();
  });

  useEffect(() => {
    startTransition(() => {
      void loadEvent();
    });
  }, []);

  async function logout() {
    await relayFetch("/api/auth/logout", { method: "POST" });
    window.localStorage.removeItem(API_KEY_STORAGE);
    router.replace("/signin");
    router.refresh();
  }

  async function runWorkflow(formData: FormData) {
    setWorkflowStatus("Submitting workflow...");
    const payload: WorkflowPayload = {
      source: String(formData.get("source") ?? "hubspot"),
      company: String(formData.get("company") ?? ""),
      contact_name: String(formData.get("contact_name") ?? ""),
      email: String(formData.get("email") ?? ""),
      requested_systems: String(formData.get("requested_systems") ?? "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      pain_points: String(formData.get("pain_points") ?? "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      monthly_revenue: String(formData.get("monthly_revenue") ?? ""),
      urgency: String(formData.get("urgency") ?? "medium"),
      notes: String(formData.get("notes") ?? ""),
    };

    const response = await relayFetch("/api/workflows/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      setWorkflowStatus(response.status === 429 ? "Too many requests. Try again in a minute." : "Workflow request failed.");
      return;
    }

    setWorkflowStatus("Workflow queued.");
    await load();
  }

  const account = state.account?.account;
  const authMode = state.account?.auth_mode ?? "session";
  const enabledIntegrations = state.integrations.filter((item) => item.enabled).length;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(192,255,141,0.18),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(17,88,54,0.16),_transparent_20%),linear-gradient(180deg,#07110c_0%,#101d17_28%,#efe7da_28%,#f7f3ec_100%)] text-stone-950">
      <div className="mx-auto grid min-h-screen max-w-[1500px] gap-6 px-4 py-5 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-6">
        <aside className="space-y-5 rounded-[2rem] border border-white/12 bg-[#0b1510]/95 p-5 text-white shadow-[0_40px_120px_rgba(0,0,0,0.25)] backdrop-blur lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)] lg:overflow-auto">
          <div className="space-y-4 rounded-[1.6rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.07),rgba(255,255,255,0.03))] p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="rounded-full bg-lime-300/15 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-lime-200">
                RelayOps
              </span>
              <span className="rounded-full bg-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/70">{authMode}</span>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-white/45">Workspace</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em]">{account?.name ?? "Loading workspace..."}</h2>
              <p className="mt-2 text-sm text-white/55">{account?.email ?? "Fetching account context"}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <RailMetric icon={<Activity className="size-4" />} label="Health" value={state.health?.status ?? "healthy"} />
              <RailMetric icon={<Database className="size-4" />} label="Runs" value={`${state.health?.total_runs ?? 0}`} />
              <RailMetric icon={<Cable className="size-4" />} label="Connectors" value={`${enabledIntegrations} enabled`} />
              <RailMetric icon={<Bot className="size-4" />} label="Syncs" value={`${state.health?.sync_targets ?? 0}`} />
            </div>
          </div>

          <div className="space-y-3 rounded-[1.6rem] border border-white/10 bg-black/15 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">Navigation</p>
            <div className="grid gap-2">
              <QuickLink href="#workflow" title="New workflow" description="Create and submit a workflow request." />
              <QuickLink href="#runs" title="Recent activity" description="Review current runs, summaries, and sync results." />
              <QuickLink href="/settings" title="Integrations" description="Check provider status and loaded configuration." />
            </div>
          </div>

          <div className="space-y-4 rounded-[1.6rem] border border-lime-300/20 bg-[linear-gradient(180deg,rgba(190,242,100,0.14),rgba(255,255,255,0.04))] p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-lime-200/90">Workspace</p>
                <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">Session active.</h3>
                <p className="mt-2 text-sm leading-6 text-white/65">
                  Use the dashboard to review workflow intake, execution status, and downstream system activity.
                </p>
              </div>
              <span className="rounded-full border border-lime-300/20 bg-lime-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-lime-100">
                {authMode}
              </span>
            </div>
            <div className="rounded-[1.2rem] border border-white/10 bg-black/15 p-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-white/45">Current workspace</p>
              <p className="mt-2 text-lg font-semibold text-white">{account?.email}</p>
              <p className="mt-1 text-sm text-white/50">{account?.name}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/settings">
                    <Button type="button" variant="secondary" className="h-10 rounded-full px-4 text-sm">
                      Integration settings
                    </Button>
                  </Link>
              <Button
                type="button"
                variant="ghost"
                className="h-10 rounded-full px-4 text-sm text-white hover:bg-white/10"
                onClick={() => void logout()}
              >
                Sign out
              </Button>
            </div>
          </div>
        </aside>

        <section className="space-y-6">
          <header className="overflow-hidden rounded-[2.4rem] border border-white/30 bg-white/88 shadow-[0_40px_120px_rgba(0,0,0,0.14)] backdrop-blur">
            <div className="grid gap-0 lg:grid-cols-[1.3fr_0.7fr]">
              <div className="space-y-6 p-6 md:p-8">
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.26em] text-emerald-900/60">
                  <span className="rounded-full border border-emerald-900/12 bg-emerald-100 px-3 py-1">Dashboard</span>
                  <span className="rounded-full border border-stone-300 bg-stone-100 px-3 py-1">{loading ? "Updating" : "Live"}</span>
                </div>
                <div className="space-y-4">
                  <h1 className="max-w-5xl font-[family-name:var(--font-display)] text-5xl leading-[0.9] tracking-[-0.05em] md:text-7xl">
                    Structured workflows, execution visibility, and connected systems in one workspace.
                  </h1>
                  <p className="max-w-3xl text-base leading-7 text-stone-700 md:text-lg">
                    RelayOps turns inbound requests into structured workflows, AI-assisted summaries, and tracked execution across connected systems.
                  </p>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  {(state.overview?.metrics ?? []).map((metric) => (
                    <div key={metric.label} className="rounded-[1.5rem] border border-stone-200 bg-[#faf7f1] p-4">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-stone-500">{metric.label}</p>
                      <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-stone-950">{metric.value}</p>
                      <p className="mt-2 text-sm leading-6 text-stone-600">{metric.detail}</p>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-3">
                  <a href="#workflow">
                    <Button className="h-11 rounded-full px-5 text-sm">
                      New workflow
                      <ArrowRight className="size-4" />
                    </Button>
                  </a>
                  <Link href="/settings">
                    <Button variant="outline" className="h-11 rounded-full px-5 text-sm">
                      Integration settings
                    </Button>
                  </Link>
                </div>
              </div>

              <div className="relay-noise relative grid gap-3 bg-[#0d1712] p-6 text-white md:p-8">
                <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-lime-200/80">
                    <Radar className="size-4" />
                    Workflow summary
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em]">
                    {state.overview?.recent_runs[0]?.ai_analysis.executive_title ?? "Waiting for workflow context"}
                  </h2>
                  <p className="mt-3 text-sm leading-6 text-white/70">
                    {state.overview?.recent_runs[0]?.summary ??
                      "A concise summary appears here after a workflow is processed."}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <DarkCard
                    icon={<ShieldCheck className="size-4" />}
                    title="Risk posture"
                    value={state.overview?.recent_runs[0]?.ai_analysis.risk_level ?? "stable"}
                  />
                  <DarkCard
                    icon={<Waypoints className="size-4" />}
                    title="Source"
                    value={state.overview?.recent_runs[0]?.source ?? "none"}
                  />
                  <DarkCard
                    icon={<Cable className="size-4" />}
                    title="Providers"
                    value={`${enabledIntegrations} connectors`}
                  />
                  <DarkCard
                    icon={<Database className="size-4" />}
                    title="Completed"
                    value={`${state.health?.completed_runs ?? 0} runs`}
                  />
                </div>
              </div>
            </div>
          </header>

          <section className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
            <div className="space-y-6">
              <section id="workflow" className="rounded-[2.2rem] border border-stone-200 bg-white p-6 shadow-[0_24px_80px_rgba(0,0,0,0.1)]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700/70">New workflow</p>
                    <h2 className="mt-3 font-[family-name:var(--font-display)] text-4xl tracking-[-0.04em]">
                      Create a new workflow request.
                    </h2>
                  </div>
                  <Sparkles className="mt-1 size-5 text-emerald-700" />
                </div>
                <form
                  className="mt-6 grid gap-4 md:grid-cols-2"
                  action={async (formData) => {
                    await runWorkflow(formData);
                  }}
                >
                  <Field name="company" label="Company" defaultValue="Atlas Retail Ops" />
                  <Field name="contact_name" label="Contact" defaultValue="Laila Fathy" />
                  <Field name="email" label="Email" defaultValue="laila@atlasretail.ai" type="email" />
                  <Field name="source" label="Source" defaultValue="hubspot" />
                  <Field name="requested_systems" label="Requested systems" defaultValue="HubSpot, NetSuite, Slack" />
                  <Field name="pain_points" label="Pain points" defaultValue="Manual reporting, slow approvals, missing client visibility" />
                  <Field name="monthly_revenue" label="Revenue band" defaultValue="EUR 90k-140k" />
                  <label className="grid gap-2 text-sm font-medium text-stone-700">
                    Urgency
                    <select
                      name="urgency"
                      defaultValue="medium"
                      className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none"
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </label>
                  <label className="md:col-span-2 grid gap-2 text-sm font-medium text-stone-700">
                    Notes
                    <textarea
                      name="notes"
                      rows={4}
                      defaultValue="Leadership needs a unified operational brief before weekly decision meetings."
                      className="rounded-[1.4rem] border border-stone-200 bg-stone-50 px-4 py-3 outline-none"
                    />
                  </label>
                  <div className="md:col-span-2 flex flex-wrap items-center gap-3">
                    <Button type="submit" className="h-11 rounded-full px-5 text-sm">
                      Submit workflow
                    </Button>
                    {workflowStatus ? <p className="text-sm text-stone-600">{workflowStatus}</p> : null}
                  </div>
                </form>
              </section>

              <section className="rounded-[2.2rem] border border-stone-200 bg-[#f8f4ec] p-6 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Integrations</p>
                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  {state.integrations.map((item) => (
                    <article key={item.provider} className="rounded-[1.4rem] border border-stone-200 bg-white p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">{item.provider}</p>
                        <span
                          className={`rounded-full px-3 py-1 text-xs uppercase tracking-[0.16em] ${
                            item.enabled ? "bg-emerald-100 text-emerald-800" : "bg-stone-200 text-stone-700"
                          }`}
                        >
                          {item.mode}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-stone-700">{item.detail}</p>
                    </article>
                  ))}
                </div>
              </section>
            </div>

            <div id="runs" className="space-y-6">
              <section className="rounded-[2.2rem] border border-stone-200 bg-white p-6 shadow-[0_24px_80px_rgba(0,0,0,0.1)]">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Activity</p>
                    <h2 className="mt-3 font-[family-name:var(--font-display)] text-4xl tracking-[-0.04em]">
                      Recent workflow runs.
                    </h2>
                  </div>
                  <span className="rounded-full border border-stone-200 bg-stone-100 px-4 py-2 text-xs uppercase tracking-[0.18em] text-stone-600">
                    {loading ? "Updating" : `${state.overview?.recent_runs.length ?? 0} visible`}
                  </span>
                </div>
                <div className="mt-6 space-y-4">
                  {(state.overview?.recent_runs ?? []).map((run) => (
                    <article key={run.id} className="rounded-[1.8rem] border border-stone-200 bg-[#fcfbf7] p-5 shadow-[0_12px_30px_rgba(0,0,0,0.04)]">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-stone-500">
                            <span>{run.source}</span>
                            <span className="h-1 w-1 rounded-full bg-stone-300" />
                            <span>{run.status}</span>
                          </div>
                          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-stone-950">{run.normalized.company}</h3>
                          <p className="mt-1 text-sm text-stone-500">{run.normalized.contact_name}</p>
                        </div>
                        <div className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xl font-semibold text-emerald-900">
                          {run.score}
                        </div>
                      </div>
                      <p className="mt-4 text-sm leading-6 text-stone-700">{run.summary}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {run.normalized.requested_systems.map((system) => (
                          <span key={system} className="rounded-full bg-stone-200 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-stone-700">
                            {system}
                          </span>
                        ))}
                      </div>
                      <div className="mt-5 grid gap-4 md:grid-cols-2">
                        <RunList title={`Risk: ${run.ai_analysis.risk_level}`} items={run.ai_analysis.highlights} />
                        <RunList title="Next steps" items={run.ai_analysis.next_steps} />
                        <RunList title="Automation" items={run.ai_analysis.automation_opportunities} />
                        <RunList title="Sync results" items={run.sync_results.map((sync) => `${sync.target}: ${sync.status} in ${sync.latency_ms}ms`)} />
                      </div>
                    </article>
                  ))}
                </div>
              </section>

              <section className="rounded-[2.2rem] border border-stone-200 bg-[#0d1712] p-6 text-white shadow-[0_24px_80px_rgba(0,0,0,0.18)]">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-lime-200/75">Workspace overview</p>
                <h2 className="mt-3 font-[family-name:var(--font-display)] text-4xl tracking-[-0.04em]">
                  Live view of workflow volume, provider status, and recent execution.
                </h2>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-white/70">
                  Monitor intake, recent workflow activity, and provider readiness from one operational workspace.
                </p>
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  <DarkCard icon={<Bot className="size-4" />} title="Access" value="Signed in" />
                  <DarkCard icon={<Cable className="size-4" />} title="Providers" value={`${enabledIntegrations}/3 ready`} />
                  <DarkCard icon={<Activity className="size-4" />} title="Completed" value={`${state.health?.completed_runs ?? 0} runs`} />
                </div>
              </section>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}

function RailMetric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-white/10 bg-black/15 p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-white/45">
        {icon}
        {label}
      </div>
      <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-white">{value}</p>
    </div>
  );
}

function DarkCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="rounded-[1.25rem] border border-white/10 bg-black/20 p-4">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-white/45">
        {icon}
        {title}
      </div>
      <p className="mt-3 text-xl font-semibold tracking-[-0.03em] text-white">{value}</p>
    </div>
  );
}

function QuickLink({ href, title, description }: { href: string; title: string; description: string }) {
  const content = (
    <div className="group rounded-[1.2rem] border border-white/10 bg-black/15 p-3 transition hover:border-lime-300/30 hover:bg-white/8">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-white">{title}</p>
        <ChevronRight className="size-4 text-white/40 transition group-hover:text-lime-200" />
      </div>
      <p className="mt-2 text-sm leading-5 text-white/50">{description}</p>
    </div>
  );

  if (href.startsWith("/")) {
    return <Link href={href}>{content}</Link>;
  }

  return <a href={href}>{content}</a>;
}

function Field(props: { name: string; label: string; defaultValue?: string; placeholder?: string; type?: string }) {
  return (
    <label className="grid gap-2 text-sm font-medium text-stone-700">
      {props.label}
      <input
        name={props.name}
        type={props.type ?? "text"}
        defaultValue={props.defaultValue}
        placeholder={props.placeholder}
        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none"
      />
    </label>
  );
}

function RunList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-[1.2rem] border border-stone-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">{title}</p>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-stone-700">
        {items.slice(0, 3).map((item) => (
          <li key={item} className="border-l-2 border-emerald-300 pl-3">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
