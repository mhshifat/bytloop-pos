import type { Metadata } from "next";
import Link from "next/link";

import { ForgotPasswordForm } from "@/components/modules/identity/forgot-password-form";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Forgot password",
  path: "/forgot-password",
  noindex: true,
});

export default function ForgotPasswordPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Account</p>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">Forgot password</h1>
        <p className="text-sm leading-relaxed text-zinc-300">
          Enter your email and we&apos;ll send you a reset link.
        </p>
      </header>
      <ForgotPasswordForm />
      <p className="text-center text-sm text-zinc-400">
        <Link
          href="/login"
          className="font-medium text-zinc-200 underline-offset-2 transition hover:text-primary hover:underline"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
