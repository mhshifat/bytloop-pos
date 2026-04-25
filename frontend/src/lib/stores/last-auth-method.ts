/**
 * Track the last successful authentication method (per browser).
 * Drives the "Last used" badge on the login page. See docs/PLAN.md §11.
 */

export const AuthMethod = {
  EMAIL: "email",
  GOOGLE: "google",
  GITHUB: "github",
} as const;

export type AuthMethod = (typeof AuthMethod)[keyof typeof AuthMethod];

const KEY = "bytloop:last_auth_method";

export function getLastAuthMethod(): AuthMethod | null {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(KEY);
  return value === AuthMethod.EMAIL ||
    value === AuthMethod.GOOGLE ||
    value === AuthMethod.GITHUB
    ? value
    : null;
}

export function setLastAuthMethod(method: AuthMethod): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, method);
}

export function clearLastAuthMethod(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(KEY);
}
