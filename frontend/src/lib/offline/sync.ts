/**
 * Coordinates offline mutation replay.
 *
 * When the browser reports `online`, drains the IndexedDB queue by replaying
 * each mutation through `apiFetch`. ULID-based idempotency keys let the
 * backend dedupe if the client previously succeeded but didn't receive ack.
 *
 * Classifies errors so poison messages (4xx validation) dead-letter quickly
 * instead of consuming retries forever. 5xx and network failures stay in
 * the queue and back off until the next online window.
 */

import { apiFetch, type FetcherOptions } from "@/lib/api/fetcher";
import { isApiError } from "@/lib/api/error";

import { drain, type FlushResult, type QueuedMutation, watchNetwork } from "./queue";

/** Periodically retry while online — backoff'd items need a clock tick to drain. */
const IDLE_RETRY_MS = 30_000;

function classify(error: unknown): FlushResult {
  if (isApiError(error)) {
    // 0 = network, 408 = timeout, 429 = rate-limit, 5xx = server — retryable.
    // 4xx validation / forbidden / not-found = poison, dead-letter now.
    const status = error.status;
    const permanent =
      status >= 400 && status < 500 && status !== 408 && status !== 429;
    return { ok: false, permanent, error: error.message };
  }
  // Unknown error — treat as transient; worst case we hit MAX_ATTEMPTS.
  return {
    ok: false,
    permanent: false,
    error: error instanceof Error ? error.message : String(error),
  };
}

export function startOfflineSync(): () => void {
  const flush = async (m: QueuedMutation): Promise<FlushResult> => {
    const options: FetcherOptions = {
      method: m.method,
      json: m.body,
      headers: { "Idempotency-Key": m.id },
    };
    try {
      await apiFetch<unknown>(m.path, options);
      return { ok: true };
    } catch (err) {
      return classify(err);
    }
  };

  // Drain on boot in case mutations were left from a previous session.
  void drain(flush);

  const stopOnline = watchNetwork(() => {
    void drain(flush);
  });

  const interval = window.setInterval(() => {
    if (navigator.onLine === false) return;
    void drain(flush);
  }, IDLE_RETRY_MS);

  return () => {
    stopOnline();
    window.clearInterval(interval);
  };
}
