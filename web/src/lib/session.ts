import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const sessionCookieName = process.env.RELAYOPS_SESSION_COOKIE ?? "relayops_session";

export async function requireSession() {
  const cookieStore = await cookies();
  if (!cookieStore.get(sessionCookieName)?.value) {
    redirect("/signin");
  }
}

export async function redirectIfSignedIn(target: string = "/") {
  const cookieStore = await cookies();
  if (cookieStore.get(sessionCookieName)?.value) {
    redirect(target);
  }
}
