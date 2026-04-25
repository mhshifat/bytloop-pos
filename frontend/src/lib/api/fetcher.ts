/**
 * Thin fetch wrapper — used by hand-written callers that need a raw Response.
 *
 * Generated `openapi-ts` hooks use their own fetcher; this is the escape hatch
 * (e.g., Server Component fetches before the client is generated).
 */

import { type ApiError, networkApiError, toApiError } from "./error";
import { useAuthStore } from "@/lib/stores/auth-store";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type FetcherOptions = RequestInit & {
  readonly json?: unknown;
};

export async function apiFetch<T>(path: string, opts: FetcherOptions = {}): Promise<T> {
  const { json, headers, ...rest } = opts;
  const accessToken = useAuthStore.getState().accessToken;
  const init: RequestInit = {
    ...rest,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
    ...(json !== undefined ? { body: JSON.stringify(json) } : {}),
  };

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    throw networkApiError();
  }

  if (!response.ok) {
    const apiError: ApiError = await toApiError(response);
    throw apiError;
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
