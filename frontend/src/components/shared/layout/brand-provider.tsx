"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";

import { getBrand, type TenantBrand } from "@/lib/api/tenant";

/**
 * Applies tenant brand tokens as CSS custom properties on :root so every
 * component honors them without prop drilling. Falls back gracefully when
 * the tenant hasn't configured a brand — existing shadcn tokens stay in
 * effect.
 *
 * Mounted inside the authenticated layout only; the guest/public shell
 * stays on the default theme.
 */
export function BrandProvider({ children }: { readonly children: ReactNode }) {
  const { data } = useQuery({
    queryKey: ["tenant", "brand"],
    queryFn: () => getBrand(),
    // Brand rarely changes — long stale time, no refetch on focus.
    staleTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (!data) return;
    applyBrand(data);
    return () => resetBrand();
  }, [data]);

  return <>{children}</>;
}

function applyBrand(brand: TenantBrand): void {
  const root = document.documentElement;
  if (brand.primaryColor) {
    root.style.setProperty("--brand-primary", brand.primaryColor);
    root.style.setProperty("--color-primary", brand.primaryColor);
  }
  if (brand.accentColor) {
    root.style.setProperty("--brand-accent", brand.accentColor);
    root.style.setProperty("--color-accent", brand.accentColor);
  }
}

function resetBrand(): void {
  const root = document.documentElement;
  root.style.removeProperty("--brand-primary");
  root.style.removeProperty("--brand-accent");
  // Don't touch shadcn's --color-primary / --color-accent on unmount —
  // the default theme handles them via CSS, no inline override needed.
}
