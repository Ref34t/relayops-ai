import Link from "next/link";
import { ArrowRight, Bot, Cable, Radar, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(190,242,100,0.18),transparent_22%),linear-gradient(180deg,#09120d_0%,#101b15_36%,#f3efe7_36%,#f7f4ee_100%)] px-4 py-6 text-stone-950 md:px-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="overflow-hidden rounded-[2.4rem] border border-white/12 bg-[#0b1510]/95 text-white shadow-[0_40px_140px_rgba(0,0,0,0.24)]">
          <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="p-8 md:p-10">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-lime-200/85">
                <span className="rounded-full bg-lime-300/15 px-3 py-1">RelayOps</span>
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Operations automation</span>
              </div>
              <h1 className="mt-8 max-w-4xl font-[family-name:var(--font-display)] text-6xl leading-[0.92] tracking-[-0.05em] md:text-8xl">
                Turn messy operational requests into structured workflows.
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-white/70 md:text-lg">
                RelayOps ingests requests from CRM, Slack, forms, or APIs, normalizes the data, generates AI-assisted summaries, and tracks execution across connected systems.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/signin">
                  <Button className="h-12 rounded-full px-6 text-sm">
                    Sign in
                    <ArrowRight className="size-4" />
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button variant="outline" className="h-12 rounded-full border-white/15 bg-white/5 px-6 text-sm text-white hover:bg-white/10">
                    Open dashboard
                  </Button>
                </Link>
              </div>
            </div>
            <div className="grid gap-4 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-8 md:p-10">
              <LandingMetric icon={<Bot className="size-4" />} title="AI brief generation" text="Summaries, risk signals, and recommended next actions for every run." />
              <LandingMetric icon={<Cable className="size-4" />} title="Connected systems" text="Coordinate execution across CRM, communications, finance, and internal tools." />
              <LandingMetric icon={<Radar className="size-4" />} title="Run visibility" text="Track execution health, sync outcomes, and audit activity in one place." />
              <LandingMetric icon={<ShieldCheck className="size-4" />} title="Secure access" text="Protected workspace sessions for dashboard and integration settings." />
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <ValueCard title="Ingest" text="Capture inbound operational requests from connected tools and normalize the data." />
          <ValueCard title="Orchestrate" text="Score urgency, route actions, and generate a clear workflow summary." />
          <ValueCard title="Synchronize" text="Push structured updates into downstream systems with visible execution status." />
        </section>
      </div>
    </main>
  );
}

function LandingMetric({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-[1.6rem] border border-white/10 bg-black/15 p-5">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-lime-200/80">
        {icon}
        {title}
      </div>
      <p className="mt-3 text-sm leading-6 text-white/66">{text}</p>
    </div>
  );
}

function ValueCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-[1.8rem] border border-stone-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">{title}</p>
      <p className="mt-4 text-sm leading-7 text-stone-700">{text}</p>
    </div>
  );
}
