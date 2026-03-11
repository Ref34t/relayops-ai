"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, KeyRound, ShieldCheck } from "lucide-react";

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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(179,255,108,0.16),transparent_24%),linear-gradient(180deg,#08110c_0%,#111d16_48%,#f4efe7_48%,#f7f4ee_100%)] px-4 py-6 text-stone-950 md:px-6">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-7xl gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2.2rem] border border-white/12 bg-[#0b1510]/95 p-8 text-white shadow-[0_40px_120px_rgba(0,0,0,0.25)]">
          <div className="flex flex-wrap items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.24em] text-lime-200/85">
            <span className="rounded-full bg-lime-300/15 px-3 py-1">RelayOps</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">Workspace access</span>
          </div>
          <h1 className="mt-8 max-w-3xl font-[family-name:var(--font-display)] text-6xl leading-[0.92] tracking-[-0.05em] md:text-7xl">
            Sign in to review workflows, summaries, and connected systems.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-white/68">
            RelayOps helps teams turn messy operational requests into structured workflows with clear execution visibility.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <FeatureCard title="Protected workspace" text="Session-based access for dashboard and settings." icon={<ShieldCheck className="size-4" />} />
            <FeatureCard title="Fast review path" text="Use the seeded account for immediate access." icon={<ArrowRight className="size-4" />} />
            <FeatureCard title="Shared visibility" text="Review workflow runs, sync outcomes, and provider status in one place." icon={<KeyRound className="size-4" />} />
          </div>
          <div className="mt-10 flex flex-wrap items-center gap-3 text-sm text-white/58">
            <span>Demo workspace:</span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-white">{demoCredentials.email}</span>
          </div>
        </section>

        <section className="grid gap-5 rounded-[2.2rem] border border-stone-200 bg-white/88 p-6 shadow-[0_30px_90px_rgba(0,0,0,0.14)] backdrop-blur">
          <AuthPanel
            title="Sign in"
            description="Use the seeded workspace or sign in with an existing account."
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
            description="Create a new workspace to test the platform with a separate account."
            status={registerStatus}
            actionLabel="Create workspace"
            onSubmit={register}
            fields={[
              { name: "name", label: "Workspace name", placeholder: "Northstar Ops", autoComplete: "organization" },
              { name: "email", label: "Email", placeholder: "ops@northstar.ai", autoComplete: "email" },
              { name: "password", label: "Password", placeholder: "Use 12+ characters", type: "password", autoComplete: "new-password" },
            ]}
          />

          <div className="rounded-[1.5rem] border border-stone-200 bg-[#faf7f1] p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Routing</p>
            <p className="mt-3 text-sm leading-6 text-stone-700">
              After authentication, RelayOps sends you to <span className="font-mono">/dashboard</span>. Settings remains protected behind the same session.
            </p>
            <div className="mt-4">
              <Link href="/dashboard" className="text-sm font-semibold text-emerald-700 underline-offset-4 hover:underline">
                Dashboard route
              </Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function FeatureCard({ title, text, icon }: { title: string; text: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-lime-200/85">
        {icon}
        {title}
      </div>
      <p className="mt-3 text-sm leading-6 text-white/62">{text}</p>
    </div>
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
      className="rounded-[1.7rem] border border-stone-200 bg-white p-5"
      action={async (formData) => {
        await onSubmit(formData);
      }}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">{title}</p>
      <p className="mt-2 text-sm leading-6 text-stone-700">{description}</p>
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
