"use client";

import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/shared/ui/skeleton";
import { listStaff } from "@/lib/api/auth";
import { getCustomer } from "@/lib/api/customers";
import { getProduct } from "@/lib/api/catalog";

/**
 * Resolve an ID to a human label via React Query. Prevents leaking UUIDs into
 * the UI (docs/PLAN.md §13) — never renders the raw id.
 *
 * Cached across mount/unmount via the shared QueryClient so repeated usage
 * on the same page only fetches once per entity.
 */

type EntityKind = "customer" | "product" | "user";

type EntityLabelProps = {
  readonly id: string | null | undefined;
  readonly entity: EntityKind;
  readonly fallback?: string;
};

export function EntityLabel({ id, entity, fallback = "—" }: EntityLabelProps) {
  const { data, isLoading, isError } = useQuery({
    // Note: user lookups share one cache key across rows — React Query
    // dedupes so repeated EntityLabel mounts only hit /auth/staff once.
    queryKey: entity === "user" ? ["staff"] : [entity, id],
    queryFn: async () => {
      if (!id) return null;
      if (entity === "customer") {
        const c = await getCustomer(id);
        return `${c.firstName} ${c.lastName}`.trim() || c.email || c.phone || fallback;
      }
      if (entity === "product") {
        const p = await getProduct(id);
        return p.name;
      }
      if (entity === "user") {
        return await listStaff();
      }
      return fallback;
    },
    enabled: Boolean(id),
    staleTime: 5 * 60 * 1000,
  });

  if (!id) return <span className="text-muted-foreground">{fallback}</span>;
  if (isLoading) return <Skeleton className="inline-block h-4 w-24 align-middle" />;
  if (isError || !data) return <span className="text-muted-foreground">{fallback}</span>;

  if (entity === "user") {
    const staff = (data as Awaited<ReturnType<typeof listStaff>>) ?? [];
    const match = staff.find((m) => m.id === id);
    if (!match) return <span className="text-muted-foreground">{fallback}</span>;
    const name = `${match.firstName} ${match.lastName}`.trim();
    return <span>{name || match.email}</span>;
  }

  return <span>{String(data)}</span>;
}
