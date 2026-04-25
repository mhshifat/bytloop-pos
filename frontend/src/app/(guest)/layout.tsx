/**
 * (guest) route-group layout — only for users who are NOT signed in.
 *
 * If the user is authenticated, they are redirected to /dashboard. Middleware
 * already performs a cookie-level bounce; this is the server-side authoritative
 * check (re-validated against /auth/me).
 */

import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { GuestAuthPageLock } from "@/components/shared/marketing/guest-auth-page-lock";
import { GuestAuthShell } from "@/components/shared/marketing/guest-auth-shell";
import { getCurrentUser } from "@/lib/auth";

export default async function GuestLayout({ children }: { readonly children: ReactNode }) {
  const user = await getCurrentUser();
  if (user) redirect("/dashboard");
  return (
    <>
      <GuestAuthPageLock />
      <GuestAuthShell>{children}</GuestAuthShell>
    </>
  );
}
