/**
 * POS-session state beyond the cart — selected customer and applied
 * discount code. Session-scoped (clears on sessionStorage reset).
 */

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

type PosState = {
  readonly customerId: string | null;
  readonly customerLabel: string | null;
  readonly discountCode: string | null;
  readonly setCustomer: (id: string | null, label: string | null) => void;
  readonly setDiscount: (code: string | null) => void;
  readonly reset: () => void;
};

export const usePosStore = create<PosState>()(
  persist(
    (set) => ({
      customerId: null,
      customerLabel: null,
      discountCode: null,
      setCustomer: (id, label) => set({ customerId: id, customerLabel: label }),
      setDiscount: (code) => set({ discountCode: code }),
      reset: () => set({ customerId: null, customerLabel: null, discountCode: null }),
    }),
    {
      name: "bytloop:pos-session",
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);
