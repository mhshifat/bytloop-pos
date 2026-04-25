/**
 * Edge middleware — first line of route protection (docs/PLAN.md §11).
 *
 * Enforces route-group rules BEFORE any rendering:
 *   (public) — no gate
 *   (guest)  — authed user → /dashboard
 *   (auth)   — unauthed → /login?next=<path>
 *   (admin)  — unauthed → /login?next=<path>
 *
 * Verification here is a cheap cookie-presence check — real auth is re-checked
 * in each route-group layout (Server Component) which calls the backend's
 * /auth/me. Middleware is intentionally fast and never throws.
 */

import { NextResponse, type NextRequest } from "next/server";

const REFRESH_COOKIE = "bytloop_refresh";

const GUEST_PREFIXES = ["/login", "/signup", "/forgot-password", "/reset-password"];
const AUTH_PREFIXES = [
  "/dashboard",
  "/pos",
  "/products",
  "/orders",
  "/customers",
  "/activate-pending",
];
const ADMIN_PREFIXES = ["/settings", "/staff", "/audit-log"];
// /activate?token=… is intentionally outside every gate.

function matches(path: string, prefixes: readonly string[]): boolean {
  return prefixes.some((p) => path === p || path.startsWith(`${p}/`));
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname, search } = request.nextUrl;
  const isAuthed = Boolean(request.cookies.get(REFRESH_COOKIE));

  if (matches(pathname, GUEST_PREFIXES) && isAuthed) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  if ((matches(pathname, AUTH_PREFIXES) || matches(pathname, ADMIN_PREFIXES)) && !isAuthed) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  const res = NextResponse.next();
  res.headers.set("x-pathname", pathname);
  return res;
}

export const config = {
  // Skip Next internals and static assets.
  matcher: ["/((?!_next/|favicon.ico|robots.txt|sitemap.xml|.*\\..*).*)"],
};
