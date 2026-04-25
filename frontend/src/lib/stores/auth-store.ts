/**
 * In-memory access-token store. See docs/PLAN.md §11 Tokens.
 *
 * We deliberately do NOT persist the access token — it lives in memory only,
 * and is re-fetched via /auth/refresh (httpOnly cookie) on each page load.
 */

import { create } from "zustand";

type AuthState = {
  readonly accessToken: string | null;
  readonly setAccessToken: (token: string | null) => void;
  readonly clear: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  setAccessToken: (token) => set({ accessToken: token }),
  clear: () => set({ accessToken: null }),
}));
