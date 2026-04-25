/**
 * API error normalization.
 *
 * Converts any non-2xx response or network failure into a typed `ApiError`
 * with a correlation ID the user can copy. See docs/PLAN.md §12.
 */

import { ulid } from "ulid";

export type ApiError = {
  readonly correlationId: string;
  readonly code: string;
  readonly message: string;
  readonly details: unknown;
  readonly status: number;
};

const GENERIC_MESSAGE = "Something went wrong. Please try again.";
const NETWORK_MESSAGE = "We couldn't reach the server. Check your connection and try again.";

export function isApiError(value: unknown): value is ApiError {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.correlationId === "string" &&
    typeof candidate.code === "string" &&
    typeof candidate.message === "string" &&
    typeof candidate.status === "number"
  );
}

export async function toApiError(response: Response): Promise<ApiError> {
  const headerCid = response.headers.get("X-Correlation-Id") ?? "";
  let body: unknown = null;
  try {
    body = await response.clone().json();
  } catch {
    // Body wasn't JSON — fall through and fabricate the envelope.
  }
  const envelope = extractEnvelope(body);
  return {
    correlationId: envelope.correlationId || headerCid || `client_${ulid()}`,
    code: envelope.code || "internal_error",
    message: envelope.message || GENERIC_MESSAGE,
    details: envelope.details,
    status: response.status,
  };
}

export function networkApiError(): ApiError {
  return {
    correlationId: `client_${ulid()}`,
    code: "network_error",
    message: NETWORK_MESSAGE,
    details: null,
    status: 0,
  };
}

function extractEnvelope(body: unknown): {
  correlationId?: string;
  code?: string;
  message?: string;
  details?: unknown;
} {
  if (typeof body !== "object" || body === null) return {};
  const outer = body as Record<string, unknown>;
  const err = outer.error;
  if (typeof err !== "object" || err === null) return {};
  const e = err as Record<string, unknown>;
  const pick = (v: unknown): string | undefined => (typeof v === "string" ? v : undefined);
  return {
    correlationId: pick(e.correlationId) ?? pick(e.correlation_id),
    code: pick(e.code),
    message: pick(e.message),
    details: e.details ?? null,
  };
}
