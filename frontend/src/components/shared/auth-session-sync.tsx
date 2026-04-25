"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { refresh } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

/**
 * On hard refresh, the in-memory access token is empty but the httpOnly
 * refresh cookie is still set. We exchange it once and invalidate queries
 * so apiFetch (Bearer) succeeds for the rest of the session.
 */
export function AuthSessionSync() {
  const queryClient = useQueryClient();
  const ran = useRef(false);
  useEffect(() => {
    if (ran.current) return;
    ran.current = true;
    if (useAuthStore.getState().accessToken) return;
    void (async () => {
      try {
        const t = await refresh();
        useAuthStore.getState().setAccessToken(t.accessToken);
        await queryClient.invalidateQueries();
      } catch {
        // Not logged in — public / guest pages still work
      }
    })();
  }, [queryClient]);

  return null;
}
