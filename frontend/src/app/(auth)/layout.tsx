/**
 * (auth) route-group layout — authenticated + verified users only.
 *
 *  - No user → /login?next=<path>
 *  - Unverified user → /activate-pending (except when already there)
 */

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthenticatedAppShell } from "@/components/shared/layout/authenticated-app-shell";
import { getCurrentUser } from "@/lib/auth";

/**
 * App shell routes are not for public search indexing. Client-only pages without
 * per-route `metadata` would otherwise inherit the root `robots: index` only.
 * Pages that export `buildMetadata({...})` still control title/canonical per URL.
 */
export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default async function AuthLayout({ children }: { readonly children: ReactNode }) {
  const user = await getCurrentUser();
  const headerList = await headers();
  const pathname = headerList.get("x-pathname") ?? "";

  if (!user) {
    redirect(`/login?next=${encodeURIComponent(pathname || "/dashboard")}`);
  }
  if (!user.emailVerified && !pathname.startsWith("/activate-pending")) {
    redirect("/activate-pending");
  }

  // Unverified users still on activate-pending render without the sidebar.
  if (!user.emailVerified) {
    return <>{children}</>;
  }

  return <AuthenticatedAppShell user={user}>{children}</AuthenticatedAppShell>;
}
