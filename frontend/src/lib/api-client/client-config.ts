/**
 * Runtime config for the generated `openapi-ts` fetch client.
 *
 * The generated client imports this module to configure its base URL and
 * credential behavior. We set `credentials: "include"` so the httpOnly
 * refresh cookie accompanies every request (docs/PLAN.md §11).
 */

import type { CreateClientConfig } from "@hey-api/client-fetch";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  credentials: "include",
});
