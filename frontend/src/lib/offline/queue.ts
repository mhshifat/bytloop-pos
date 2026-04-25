/**
 * Offline mutation queue (IndexedDB).
 *
 * When the network is unavailable the POS can still take sales. Each
 * mutation is enqueued with a client-generated ULID so the server can
 * de-duplicate on reconnect (docs/PLAN.md §14 Offline POS).
 *
 * Hardening (Phase 5):
 *  - ``attempts`` increments on every failed flush so we can back off.
 *  - Exponential backoff with ``nextRetryAt`` gating — stops hammering
 *    a down backend, lets a flaky tablet drain cleanly when it recovers.
 *  - ``MAX_ATTEMPTS`` dead-letters items that keep failing so one stuck
 *    mutation doesn't block the whole queue behind it.
 */

import { ulid } from "ulid";

const DB_NAME = "bytloop-pos-offline";
const DB_VERSION = 2;
const STORE = "mutations";

/** After this many consecutive failures, mark the item dead-lettered. */
export const MAX_ATTEMPTS = 10;

/** Backoff schedule (seconds), capped at the last entry. */
const BACKOFF_SECONDS: readonly number[] = [2, 5, 15, 30, 60, 120, 300, 600];

export type QueuedMutation = {
  readonly id: string; // ULID, also the idempotency key on the server
  readonly method: "POST" | "PATCH" | "DELETE";
  readonly path: string;
  readonly body: unknown;
  readonly enqueuedAt: number;
  readonly attempts: number;
  readonly nextRetryAt: number; // epoch ms; 0 = try immediately
  readonly deadLettered: boolean;
  readonly lastError: string | null;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" });
      }
      // v1 → v2: existing records don't have the new fields; ``normalize``
      // fills in defaults on read so no migration script is needed.
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => Promise<T>,
): Promise<T> {
  const db = await openDb();
  return new Promise<T>((resolve, reject) => {
    const tx = db.transaction(STORE, mode);
    const store = tx.objectStore(STORE);
    fn(store).then(resolve, reject);
    tx.onerror = () => reject(tx.error);
  });
}

function normalize(raw: unknown): QueuedMutation {
  const r = raw as Partial<QueuedMutation> & { readonly id: string };
  return {
    id: r.id,
    method: r.method ?? "POST",
    path: r.path ?? "",
    body: r.body,
    enqueuedAt: r.enqueuedAt ?? Date.now(),
    attempts: r.attempts ?? 0,
    nextRetryAt: r.nextRetryAt ?? 0,
    deadLettered: r.deadLettered ?? false,
    lastError: r.lastError ?? null,
  };
}

function backoffMs(attempts: number): number {
  const cap = Math.max(0, BACKOFF_SECONDS.length - 1);
  const idx = Math.min(attempts, cap);
  // Jitter ±20% so a fleet of offline tablets doesn't retry in lock-step.
  const base = (BACKOFF_SECONDS[idx] ?? BACKOFF_SECONDS[cap] ?? 600) * 1000;
  const jitter = (Math.random() - 0.5) * 0.4 * base;
  return Math.max(1000, Math.round(base + jitter));
}

export async function enqueue(
  mutation: Omit<
    QueuedMutation,
    "id" | "enqueuedAt" | "attempts" | "nextRetryAt" | "deadLettered" | "lastError"
  >,
): Promise<string> {
  const record: QueuedMutation = {
    id: ulid(),
    enqueuedAt: Date.now(),
    attempts: 0,
    nextRetryAt: 0,
    deadLettered: false,
    lastError: null,
    ...mutation,
  };
  await withStore("readwrite", async (store) => {
    await new Promise<void>((resolve, reject) => {
      const req = store.put(record);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  });
  return record.id;
}

export type FlushResult =
  | { readonly ok: true }
  | { readonly ok: false; readonly permanent: boolean; readonly error: string };

/**
 * Drain eligible items. Items past their ``nextRetryAt`` and not dead-lettered
 * are attempted; on failure we increment attempts and push the next retry out.
 *
 * Returns the number of items successfully flushed.
 */
export async function drain(
  flush: (mutation: QueuedMutation) => Promise<FlushResult>,
): Promise<number> {
  const items = await listAll();
  const now = Date.now();
  let sent = 0;
  for (const item of items) {
    if (item.deadLettered) continue;
    if (item.nextRetryAt > now) continue;
    const result = await flush(item);
    if (result.ok) {
      await remove(item.id);
      sent += 1;
      continue;
    }
    // Non-retryable errors (e.g. 400-class validation) → straight to DLQ
    // so we don't loop forever on a poison message.
    const nextAttempts = item.attempts + 1;
    const shouldDeadLetter =
      result.permanent || nextAttempts >= MAX_ATTEMPTS;
    await update(item.id, {
      attempts: nextAttempts,
      nextRetryAt: shouldDeadLetter ? 0 : now + backoffMs(nextAttempts),
      deadLettered: shouldDeadLetter,
      lastError: result.error,
    });
  }
  return sent;
}

export function listAll(): Promise<QueuedMutation[]> {
  return withStore("readonly", (store) =>
    new Promise<QueuedMutation[]>((resolve, reject) => {
      const req = store.getAll();
      req.onsuccess = () => {
        const rows = (req.result as unknown[]).map(normalize);
        resolve(rows);
      };
      req.onerror = () => reject(req.error);
    }),
  );
}

export async function countPending(): Promise<number> {
  const all = await listAll();
  return all.filter((m) => !m.deadLettered).length;
}

export async function countDeadLettered(): Promise<number> {
  const all = await listAll();
  return all.filter((m) => m.deadLettered).length;
}

export async function remove(id: string): Promise<void> {
  await withStore("readwrite", (store) =>
    new Promise<void>((resolve, reject) => {
      const req = store.delete(id);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    }),
  );
}

async function update(
  id: string,
  patch: Partial<QueuedMutation>,
): Promise<void> {
  await withStore("readwrite", async (store) => {
    const existing = await new Promise<QueuedMutation | null>((resolve, reject) => {
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result ? normalize(req.result) : null);
      req.onerror = () => reject(req.error);
    });
    if (!existing) return;
    const next: QueuedMutation = { ...existing, ...patch };
    await new Promise<void>((resolve, reject) => {
      const req = store.put(next);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  });
}

/**
 * Re-queue a dead-lettered item after the operator has investigated. Resets
 * attempt count and clears the DLQ flag so the next drain picks it up.
 */
export async function revive(id: string): Promise<void> {
  await update(id, {
    attempts: 0,
    nextRetryAt: 0,
    deadLettered: false,
    lastError: null,
  });
}

export function watchNetwork(onOnline: () => void): () => void {
  window.addEventListener("online", onOnline);
  return () => window.removeEventListener("online", onOnline);
}
