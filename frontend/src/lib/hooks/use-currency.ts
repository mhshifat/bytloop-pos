"use client";

import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";

import { getTenant } from "@/lib/api/tenant";
import { formatMoney as formatMoneyUtil, type FormatMoneyOptions } from "@/lib/utils/money";

/**
 * Tenant-aware currency access. Fetches the active tenant once per session via
 * React Query and exposes a formatter that defaults to the tenant's resolved
 * currency while still respecting explicit per-record currencies (orders,
 * products) — mix them deliberately, don't let the default rewrite a real
 * currency the data carries.
 */
export function useCurrency(): {
  readonly currency: string;
  readonly isLoading: boolean;
  readonly formatMoney: (cents: number, currency?: string, opts?: FormatMoneyOptions) => string;
} {
  const { data, isLoading } = useQuery({
    queryKey: ["tenant", "currency"],
    queryFn: () => getTenant(),
    staleTime: 10 * 60 * 1000,
  });

  const fallback = "USD";
  const currency = data?.defaultCurrency ?? fallback;

  const formatMoney = useCallback(
    (cents: number, override?: string, opts?: FormatMoneyOptions): string =>
      formatMoneyUtil(cents, override ?? currency, opts),
    [currency],
  );

  return { currency, isLoading, formatMoney };
}
