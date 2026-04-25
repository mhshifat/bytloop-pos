import type { Metadata } from "next";
import Link from "next/link";

import { LoginForm } from "@/components/modules/identity/login-form";
import { OAuthButtons } from "@/components/modules/identity/oauth-buttons";
import { Separator } from "@/components/shared/ui/separator";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Sign in",
  path: "/login",
  noindex: true,
});

export default function LoginPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Account</p>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">Welcome back</h1>
        <p className="text-sm leading-relaxed text-zinc-300">Sign in to your workspace.</p>
      </header>

      <OAuthButtons />
      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <Separator className="flex-1 bg-zinc-600" /> <span className="shrink-0">or</span>{" "}
        <Separator className="flex-1 bg-zinc-600" />
      </div>

      <LoginForm />

      <div className="flex flex-col justify-between gap-3 text-sm sm:flex-row sm:items-center">
        <Link
          href="/forgot-password"
          className="text-zinc-400 underline-offset-2 transition hover:text-primary hover:underline"
        >
          Forgot password?
        </Link>
        <Link
          href="/signup"
          className="font-medium text-zinc-200 underline-offset-2 transition hover:text-primary hover:underline"
        >
          Create account
        </Link>
      </div>
    </div>
  );
}
