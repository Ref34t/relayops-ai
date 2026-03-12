import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const sessionCookieName = process.env.RELAYOPS_SESSION_COOKIE ?? "relayops_session";
const backendBaseUrl = process.env.RELAYOPS_BACKEND_URL ?? "http://127.0.0.1:8022";

async function hasValidSession() {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(sessionCookieName);
  if (!sessionCookie?.value) {
    return false;
  }

  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");

  let response: Response;
  try {
    response = await fetch(`${backendBaseUrl}/api/account`, {
      headers: cookieHeader ? { cookie: cookieHeader } : undefined,
      cache: "no-store",
    });
  } catch {
    return false;
  }

  if (!response.ok) {
    return false;
  }

  const payload = (await response.json()) as { auth_mode?: string };
  return payload.auth_mode === "session";
}

export async function requireSession() {
  if (!(await hasValidSession())) {
    redirect("/signin");
  }
}

export async function redirectIfSignedIn(target: string = "/") {
  if (await hasValidSession()) {
    redirect(target);
  }
}
