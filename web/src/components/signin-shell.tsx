"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, LockKeyhole, ShieldCheck, Workflow } from "lucide-react";

import { Button } from "@/components/ui/button";
import { API_KEY_STORAGE, relayFetch } from "@/lib/relayops";

const demoCredentials = {
  email: "demo@relayops.app",
  password: "relayops-demo-pass",
};

export function SignInShell() {
  const router = useRouter();
  const [loginStatus, setLoginStatus] = useState("");
  const [registerStatus, setRegisterStatus] = useState("");

  async function signIn(formData: FormData) {
    setLoginStatus("Signing in...");
    const response = await relayFetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: String(formData.get("email") ?? ""),
        password: String(formData.get("password") ?? ""),
      }),
    });

    if (!response.ok) {
      setLoginStatus("Sign-in failed. Check your credentials and try again.");
      return;
    }

    window.localStorage.removeItem(API_KEY_STORAGE);
    setLoginStatus("Signed in. Redirecting...");
    router.replace("/dashboard");
    router.refresh();
  }

  async function register(formData: FormData) {
    setRegisterStatus("Creating workspace...");
    const response = await relayFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: String(formData.get("name") ?? ""),
        email: String(formData.get("email") ?? ""),
        password: String(formData.get("password") ?? ""),
      }),
    });

    if (!response.ok) {
      setRegisterStatus(response.status === 409 ? "That workspace email already exists." : "Workspace creation failed.");
      return;
    }

    window.localStorage.removeItem(API_KEY_STORAGE);
    setRegisterStatus("Workspace created. Redirecting...");
    router.replace("/dashboard");
    router.refresh();
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(179,255,108,0.18),transparent_22%),linear-gradient(180deg,#08110c_0%,#101b15_46%,#f3eadc_46%,#f7f4ed_100%)] px-4 py-6 md:px-6">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-[1460px] gap-6 lg:grid-cols-[1fr_0.96fr]">
        <section className="relay-noise relative overflow-hidden rounded-[2.6rem] border border-white/10 bg-[#0a1610] px-7 py-8 text-white shadow-[0_40px_140px_rgba(0,0,0,0.26)] md:px-10 md:py-10">
          <div className="relative z-10">
            <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-lime-200/85">
              <span className="rounded-full border border-lime-300/20 bg-lime-300/10 px-3 py-1">RelayOps</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Workspace access</span>
            </div>

            <h1 className="mt-10 max-w-4xl font-[family-name:var(--font-display)] text-6xl leading-[0.92] tracking-[-0.05em] md:text-7xl">
              Sign in to review workflows, summaries, and connected systems.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-8 text-white/68">
              RelayOps helps teams turn messy operational requests into structured workflows with clear execution
              visibility.
            </p>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              <SignalCard icon={<ShieldCheck className="size-4" />} title="Protected access" text="Dashboard and settings remain behind a workspace session." />
              <SignalCard icon={<Workflow className="size-4" />} title="Workflow visibility" text="Review activity, summaries, and connected system status after sign-in." />
              <SignalCard icon={<LockKeyhole className="size-4" />} title="Fast entry" text="Use the seeded account or create a separate workspace locally." />
            </div>

            <div className="mt-10 rounded-[1.8rem] border border-white/10 bg-white/6 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">Demo workspace</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 font-mono text-sm text-white">
                  {demoCredentials.email}
                </span>
                <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 font-mono text-sm text-white">
                  {demoCredentials.password}
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 rounded-[2.6rem] border border-stone-200 bg-white/88 p-6 shadow-[0_30px_90px_rgba(0,0,0,0.12)] backdrop-blur md:p-7">
          <AuthPanel
            title="Sign in"
            description="Use the seeded workspace or an existing account."
            status={loginStatus}
            actionLabel="Enter dashboard"
            onSubmit={signIn}
            fields={[
              { name: "email", label: "Email", defaultValue: demoCredentials.email, autoComplete: "email" },
              {
                name: "password",
                label: "Password",
                defaultValue: demoCredentials.password,
                type: "password",
                autoComplete: "current-password",
              },
            ]}
          />

          <AuthPanel
            title="Create workspace"
            description="Create a separate workspace for a fresh local account."
            status={registerStatus}
            actionLabel="Create workspace"
            onSubmit={register}
            fields={[
              { name: "name", label: "Workspace name", placeholder: "Northstar Ops", autoComplete: "organization" },
              { name: "email", label: "Email", placeholder: "ops@northstar.ai", autoComplete: "email" },
              { name: "password", label: "Password", placeholder: "Use 12+ characters", type: "password", autoComplete: "new-password" },
            ]}
          />

          <div className="rounded-[1.7rem] border border-stone-200 bg-[#faf6ef] p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">Routing</p>
                <p className="mt-2 text-sm leading-7 text-stone-700">
                  Successful sign-in routes directly to <span className="font-mono">/dashboard</span>.
                </p>
              </div>
              <Link href="/">
                <Button variant="outline" className="h-10 rounded-full px-4 text-sm">
                  Back to landing
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function SignalCard({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <article className="rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-lime-200/80">
        {icon}
        {title}
      </div>
      <p className="mt-3 text-sm leading-7 text-white/62">{text}</p>
    </article>
  );
}

function AuthPanel({
  title,
  description,
  status,
  actionLabel,
  fields,
  onSubmit,
}: {
  title: string;
  description: string;
  status: string;
  actionLabel: string;
  fields: {
    name: string;
    label: string;
    defaultValue?: string;
    placeholder?: string;
    type?: string;
    autoComplete?: string;
  }[];
  onSubmit: (formData: FormData) => Promise<void>;
}) {
  return (
    <form
      className="rounded-[1.9rem] border border-stone-200 bg-white p-5"
      action={async (formData) => {
        await onSubmit(formData);
      }}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">{title}</p>
      <p className="mt-2 text-sm leading-7 text-stone-700">{description}</p>
      <div className="mt-5 grid gap-3">
        {fields.map((field) => (
          <label key={field.name} className="grid gap-2 text-sm font-medium text-stone-700">
            {field.label}
            <input
              name={field.name}
              type={field.type ?? "text"}
              defaultValue={field.defaultValue}
              placeholder={field.placeholder}
              autoComplete={field.autoComplete}
              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none"
            />
          </label>
        ))}
      </div>
      <div className="mt-5 flex items-center justify-between gap-3">
        <Button type="submit" className="h-11 rounded-full px-5 text-sm">
          {actionLabel}
        </Button>
        {status ? <p className="text-right text-sm text-emerald-700">{status}</p> : null}
      </div>
    </form>
  );
}
