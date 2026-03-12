import Link from "next/link";
import { ArrowRight, Bot, Cable, Radar, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";

const pillars = [
  {
    title: "Intake",
    text: "Capture inbound requests from CRM, Slack, forms, or internal APIs without forcing teams into a single entry point.",
  },
  {
    title: "Workflow logic",
    text: "Normalize data, score urgency, assign next actions, and generate a concise workflow summary for operators.",
  },
  {
    title: "Execution",
    text: "Track provider activity, sync outcomes, and operational follow-through across connected systems.",
  },
];

const signals = [
  {
    icon: <Bot className="size-4" />,
    title: "AI-assisted summaries",
    text: "Briefs, highlights, and next actions generated from structured workflow context.",
  },
  {
    icon: <Cable className="size-4" />,
    title: "Connected systems",
    text: "CRM, communication, finance, and internal systems coordinated from one layer.",
  },
  {
    icon: <Radar className="size-4" />,
    title: "Execution visibility",
    text: "Live workflow activity, sync outcomes, diagnostics, and health signals.",
  },
  {
    icon: <ShieldCheck className="size-4" />,
    title: "Protected workspace",
    text: "Landing, sign-in, dashboard, and settings with session-based access control.",
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(192,255,141,0.18),transparent_24%),radial-gradient(circle_at_bottom_right,_rgba(9,80,46,0.16),transparent_18%),linear-gradient(180deg,#08110c_0%,#112018_36%,#eee7da_36%,#f7f3ec_100%)] px-4 py-6 md:px-6">
      <div className="mx-auto max-w-[1460px] space-y-6">
        <section className="relay-noise relative overflow-hidden rounded-[2.8rem] border border-white/10 bg-[#0b1711] text-white shadow-[0_40px_160px_rgba(0,0,0,0.28)]">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="relative z-10 px-7 py-8 md:px-10 md:py-10">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-lime-200/85">
                <span className="rounded-full border border-lime-300/20 bg-lime-300/10 px-3 py-1">RelayOps</span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Operations workflow platform</span>
              </div>

              <h1 className="mt-10 max-w-5xl font-[family-name:var(--font-display)] text-6xl leading-[0.9] tracking-[-0.055em] text-white md:text-8xl">
                Turn messy operational requests into structured workflows.
              </h1>

              <p className="mt-7 max-w-3xl text-base leading-8 text-white/70 md:text-lg">
                RelayOps ingests requests from CRM, Slack, forms, or APIs, normalizes the data, generates AI-assisted
                summaries, and tracks execution across connected systems.
              </p>

              <div className="mt-10 flex flex-wrap gap-3">
                <Link href="/signin">
                  <Button className="h-12 rounded-full px-6 text-sm">
                    Sign in
                    <ArrowRight className="size-4" />
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-6 text-sm text-white hover:bg-white/10">
                    Open workspace
                  </Button>
                </Link>
              </div>

              <div className="mt-12 grid gap-4 md:grid-cols-3">
                {pillars.map((pillar) => (
                  <article key={pillar.title} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-lime-200/80">{pillar.title}</p>
                    <p className="mt-3 text-sm leading-7 text-white/64">{pillar.text}</p>
                  </article>
                ))}
              </div>
            </div>

            <div className="relative overflow-hidden border-l border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] px-7 py-8 md:px-10 md:py-10">
              <div className="pointer-events-none absolute inset-x-10 top-10 h-32 rounded-full bg-lime-300/12 blur-3xl" />
              <div className="relative grid gap-5">
                <div className="rounded-[2.2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.11),rgba(255,255,255,0.04))] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)]">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-lime-200/80">Current frame</p>
                      <h2 className="mt-4 max-w-lg text-3xl font-semibold leading-tight tracking-[-0.05em] text-white md:text-[2.2rem]">
                        One operational layer between intake, workflow logic, and execution.
                      </h2>
                    </div>
                    <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/60">
                      Product view
                    </span>
                  </div>

                  <p className="mt-5 max-w-2xl text-sm leading-7 text-white/68">
                    RelayOps receives inbound requests, structures them into consistent workflow records, and keeps
                    execution visible across the systems that operators already use.
                  </p>

                  <div className="mt-6 grid gap-3 sm:grid-cols-3">
                    <FrameMetric label="Sources" value="CRM, Slack, forms, APIs" />
                    <FrameMetric label="Core flow" value="Normalize, summarize, execute" />
                    <FrameMetric label="Outcome" value="Tracked follow-through" />
                  </div>
                </div>

                <div className="grid gap-4">
                {signals.map((signal) => (
                  <article
                    key={signal.title}
                    className="rounded-[1.6rem] border border-white/10 bg-[linear-gradient(180deg,rgba(0,0,0,0.22),rgba(255,255,255,0.03))] p-5 backdrop-blur"
                  >
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-lime-200/80">
                      {signal.icon}
                      {signal.title}
                    </div>
                    <p className="mt-3 text-sm leading-7 text-white/62">{signal.text}</p>
                  </article>
                ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="rounded-[2rem] border border-stone-200 bg-white p-7 shadow-[0_24px_90px_rgba(0,0,0,0.08)]">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Product promise</p>
            <h2 className="mt-4 font-[family-name:var(--font-display)] text-5xl tracking-[-0.05em] text-stone-950">
              Better structure in, clearer execution out.
            </h2>
            <p className="mt-5 text-sm leading-7 text-stone-700">
              RelayOps is not another chat UI. It is a workflow product built around operational requests, structured
              data, AI-assisted summaries, and visible downstream execution.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-3">
            <ValueCard title="Ingest" text="Capture requests from multiple tools without losing context or structure." />
            <ValueCard title="Orchestrate" text="Score urgency, assign actions, and produce workflow-ready summaries." />
            <ValueCard title="Synchronize" text="Keep execution visible across CRM, communication, and finance systems." />
          </div>
        </section>
      </div>
    </main>
  );
}

function ValueCard({ title, text }: { title: string; text: string }) {
  return (
    <article className="rounded-[2rem] border border-stone-200 bg-white px-6 py-7 shadow-[0_24px_80px_rgba(0,0,0,0.08)]">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">{title}</p>
      <p className="mt-4 text-sm leading-7 text-stone-700">{text}</p>
    </article>
  );
}

function FrameMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.3rem] border border-white/10 bg-black/18 px-4 py-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/45">{label}</p>
      <p className="mt-3 text-sm leading-6 text-white/80">{value}</p>
    </div>
  );
}
