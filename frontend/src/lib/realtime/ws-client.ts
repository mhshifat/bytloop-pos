/**
 * Tiny typed WebSocket client with auto-reconnect + exponential backoff.
 *
 * Used by the KDS board to subscribe to `/ws/restaurant/kds` and trigger
 * React Query invalidations when tickets change. Degrades to the existing
 * polling refetch if WebSocket construction fails (no hard dependency).
 */

type Listener<T> = (message: T) => void;

export type WsClient = {
  readonly close: () => void;
};

const MAX_BACKOFF_MS = 30_000;

export function connectWs<T>(
  path: string,
  onMessage: Listener<T>,
  onOpen?: () => void,
): WsClient {
  if (typeof window === "undefined") {
    return { close: () => undefined };
  }

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const wsBase = apiBase.replace(/^http/i, "ws");
  const url = `${wsBase}${path}`;

  let socket: WebSocket | null = null;
  let backoff = 1000;
  let closed = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  const open = (): void => {
    if (closed) return;
    try {
      socket = new WebSocket(url);
    } catch {
      schedule();
      return;
    }
    socket.addEventListener("open", () => {
      backoff = 1000;
      onOpen?.();
    });
    socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data as string) as T;
        onMessage(parsed);
      } catch {
        // ignore malformed frames
      }
    });
    socket.addEventListener("close", () => {
      if (!closed) schedule();
    });
    socket.addEventListener("error", () => {
      socket?.close();
    });
  };

  const schedule = (): void => {
    if (closed || reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      backoff = Math.min(backoff * 2, MAX_BACKOFF_MS);
      open();
    }, backoff);
  };

  open();

  return {
    close: () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    },
  };
}
