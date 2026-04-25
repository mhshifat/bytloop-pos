import type { Metadata } from "next";
import Link from "next/link";

import { SignupForm } from "@/components/modules/identity/signup-form";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Create account",
  path: "/signup",
  noindex: true,
});

export default function SignupPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Get started</p>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">
          Create your account
        </h1>
        <p className="text-sm leading-relaxed text-zinc-300">Start taking orders in minutes.</p>
      </header>
      <SignupForm />
      <p className="text-center text-sm text-zinc-400">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-zinc-200 underline-offset-2 transition hover:text-primary hover:underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
