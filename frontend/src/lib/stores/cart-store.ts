/**
 * POS cart — line-based (supports multiple lines for the same product with
 * different serials, variants, or vertical metadata). Persists to sessionStorage.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type CartLine = {
  readonly lineId: string;
  readonly productId: string;
  readonly name: string;
  readonly unitPriceCents: number;
  readonly currency: string;
  readonly quantity: number;
  /** Per-line excise (liquor); included in line total. */
  readonly exciseCents?: number;
  /** Backend order_items.vertical_data — serial, department, batch id, etc. */
  readonly verticalData?: Record<string, unknown>;
};

type CartState = {
  readonly lines: CartLine[];
  readonly addLine: (line: Omit<CartLine, "lineId" | "quantity">, qty?: number) => void;
  readonly setQuantity: (lineId: string, qty: number) => void;
  readonly updateLine: (lineId: string, patch: Partial<Pick<CartLine, "verticalData" | "exciseCents" | "unitPriceCents">>) => void;
  readonly removeLine: (lineId: string) => void;
  readonly clear: () => void;
  readonly totalCents: () => number;
  readonly subtotalCents: () => number;
  readonly exciseTotalCents: () => number;
};

function mergeKey(verticalData: Record<string, unknown> | undefined): string {
  if (verticalData == null || Object.keys(verticalData).length === 0) return "";
  return JSON.stringify(verticalData, Object.keys(verticalData).sort());
}

function canMerge(a: CartLine, b: Omit<CartLine, "lineId" | "quantity">): boolean {
  if (a.productId !== b.productId) return false;
  return mergeKey(a.verticalData) === mergeKey(b.verticalData) && a.exciseCents === b.exciseCents;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      lines: [],
      addLine: (line, qty = 1) =>
        set((state) => {
          const existing = state.lines.find((l) => canMerge(l, line));
          if (existing) {
            return {
              lines: state.lines.map((l) =>
                l.lineId === existing.lineId ? { ...l, quantity: l.quantity + qty } : l,
              ),
            };
          }
          const lineId =
            typeof crypto !== "undefined" && crypto.randomUUID
              ? crypto.randomUUID()
              : `ln_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
          return {
            lines: [
              ...state.lines,
              {
                ...line,
                lineId,
                quantity: qty,
              },
            ],
          };
        }),
      setQuantity: (lineId, qty) =>
        set((state) => ({
          lines:
            qty <= 0
              ? state.lines.filter((l) => l.lineId !== lineId)
              : state.lines.map((l) => (l.lineId === lineId ? { ...l, quantity: qty } : l)),
        })),
      updateLine: (lineId, patch) =>
        set((state) => ({
          lines: state.lines.map((l) => (l.lineId === lineId ? { ...l, ...patch } : l)),
        })),
      removeLine: (lineId) => set((state) => ({ lines: state.lines.filter((l) => l.lineId !== lineId) })),
      clear: () => set({ lines: [] }),
      subtotalCents: () =>
        get().lines.reduce((sum, l) => sum + l.unitPriceCents * l.quantity, 0),
      exciseTotalCents: () => get().lines.reduce((sum, l) => sum + (l.exciseCents ?? 0), 0),
      totalCents: () => get().subtotalCents() + get().exciseTotalCents(),
    }),
    {
      name: "bytloop:pos-cart",
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);
