import { SignInShell } from "@/components/signin-shell";
import { redirectIfSignedIn } from "@/lib/session";

export default async function SignInPage() {
  await redirectIfSignedIn("/dashboard");
  return <SignInShell />;
}
