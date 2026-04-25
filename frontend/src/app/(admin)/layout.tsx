/**
 * (admin) route-group layout — authenticated + verified + admin permission.
 *
 *  - No user → /login?next=<path>
 *  - Unverified → /activate-pending
 *  - Authed but not permitted → /403
 *
 * Uses the same shell as `(auth)` (sidebar, theme, top bar) so admin pages
 * like Settings match the rest of the app.
 */

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthenticatedAppShell } from "@/components/shared/layout/authenticated-app-shell";
import { getCurrentUser, userHasPermission } from "@/lib/auth";
import { Permission } from "@/lib/rbac";

/** Admin UI is not intended for public indexing; pages may still set `buildMetadata` for titles. */
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default async function AdminLayout({ children }: { readonly children: ReactNode }) {
  const user = await getCurrentUser();
  const headerList = await headers();
  const pathname = headerList.get("x-pathname") ?? "";

  if (!user) {
    redirect(`/login?next=${encodeURIComponent(pathname || "/")}`);
  }
  if (!user.emailVerified) {
    redirect("/activate-pending");
  }
  if (!userHasPermission(user, Permission.ADMIN_ACCESS)) {
    redirect("/403");
  }

  return <AuthenticatedAppShell user={user}>{children}</AuthenticatedAppShell>;
}
