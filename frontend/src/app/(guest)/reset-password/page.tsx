import type { Metadata } from "next";
import Link from "next/link";

import { ResetPasswordForm } from "@/components/modules/identity/reset-password-form";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Reset password",
  path: "/reset-password",
  noindex: true,
});

type ResetPasswordPageProps = {
  readonly searchParams: Promise<{ readonly token?: string }>;
};

export default async function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const { token } = await searchParams;

  return (
    <div className="flex flex-col gap-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Account</p>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-50 sm:text-3xl">Reset password</h1>
        <p className="text-sm leading-relaxed text-zinc-300">Choose a new password for your account.</p>
      </header>
      {token ? (
        <ResetPasswordForm token={token} />
      ) : (
        <p
          className="rounded-xl border border-amber-500/40 bg-amber-950/40 p-4 text-sm leading-relaxed text-amber-100"
          role="alert"
        >
          Missing reset token. Use the link from your email, or{" "}
          <Link
            href="/forgot-password"
            className="font-medium text-amber-200 underline-offset-2 hover:underline"
          >
            request a new reset
          </Link>
          .
        </p>
      )}
    </div>
  );
}
