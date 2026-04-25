"use client";

import { useQuery } from "@tanstack/react-query";

import { getTenant } from "@/lib/api/tenant";
import { useUtmCapture } from "@/lib/hooks/use-utm-capture";

/**
 * Headless client component that fires UTM capture from anywhere in the
 * authenticated tree. Mount once near the root — subsequent navigations
 * inside the SPA re-check the URL but dedupe-storage prevents double posts.
 */
export function UtmCapture() {
  const { data } = useQuery({
    queryKey: ["tenant", "for-utm"],
    queryFn: () => getTenant(),
    staleTime: 60 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
  useUtmCapture({ tenantSlug: data?.slug ?? null });
  return null;
}
