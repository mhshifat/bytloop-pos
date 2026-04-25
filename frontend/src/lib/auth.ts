/**
 * Auth helpers for Server Components and middleware.
 *
 * Token strategy (docs/PLAN.md §11):
 *  - Access token: short-lived JWT, in-memory on the client (Zustand)
 *  - Refresh token: long-lived, httpOnly secure cookie, rotated on use
 *
 * This module is the SSOT for reading the authenticated user from the
 * server-side context. Route-group layouts call `getCurrentUser()` and
 * `redirect()` as appropriate.
 */

import { cookies } from "next/headers";
import { cache } from "react";

import type { Permission, Role } from "@/lib/rbac";
import { hasPermission } from "@/lib/rbac";

export type CurrentUser = {
  readonly id: string;
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly emailVerified: boolean;
  readonly roles: readonly Role[];
  readonly tenantId: string;
};

const REFRESH_COOKIE = "bytloop_refresh";
const API_BASE = process.env.API_SERVER_BASE_URL ?? "http://localhost:8000";

/**
 * Cached per-request — multiple layouts asking for the current user in a single
 * render only hit the backend once.
 */
export const getCurrentUser = cache(async (): Promise<CurrentUser | null> => {
  const cookieStore = await cookies();
  const refresh = cookieStore.get(REFRESH_COOKIE);
  if (!refresh) return null;

  try {
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { Cookie: `${REFRESH_COOKIE}=${refresh.value}` },
      cache: "no-store",
    });
    if (!refreshRes.ok) return null;
    const tokens: unknown = await refreshRes.json();
    if (typeof tokens !== "object" || tokens === null || !("accessToken" in tokens)) {
      return null;
    }
    const accessToken = (tokens as { accessToken: string }).accessToken;
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data: unknown = await res.json();
    if (!isCurrentUser(data)) return null;
    return data;
  } catch {
    return null;
  }
});

function isCurrentUser(value: unknown): value is CurrentUser {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.email === "string" &&
    typeof candidate.emailVerified === "boolean" &&
    Array.isArray(candidate.roles)
  );
}

export function userHasPermission(
  user: CurrentUser | null,
  required: Permission
): boolean {
  return user ? hasPermission(user.roles, required) : false;
}
