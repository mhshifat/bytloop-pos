"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Input } from "@/components/shared/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listProductsAllPages } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";
import {
  type KdsStation,
  listStationRoutes,
  upsertStationRoute,
} from "@/lib/api/restaurant";

const STATION_LABELS: Record<KdsStation, string> = {
  kitchen: "Kitchen",
  bar: "Bar",
  dessert: "Dessert",
  expo: "Expo",
};

const STATIONS: readonly KdsStation[] = ["kitchen", "bar", "dessert", "expo"];

export function StationRoutesEditor() {
  const queryClient = useQueryClient();
  const { data: products, isLoading: productsLoading, error } = useQuery({
    queryKey: ["products", "for-routes"],
    queryFn: () => listProductsAllPages(),
  });
  const { data: routes } = useQuery({
    queryKey: ["restaurant", "routes"],
    queryFn: () => listStationRoutes(),
  });

  const routeByProduct = useMemo(() => {
    const map = new Map<string, { station: KdsStation; course: number }>();
    for (const r of routes ?? []) {
      map.set(r.productId, { station: r.station, course: r.course });
    }
    return map;
  }, [routes]);

  const save = useMutation({
    mutationFn: (input: { productId: string; station: KdsStation; course: number }) =>
      upsertStationRoute(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["restaurant", "routes"] });
      toast.success("Route saved.");
    },
  });

  if (productsLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!products || products.items.length === 0) {
    return (
      <EmptyState
        title="No products"
        description="Create products first, then map each one to a station."
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>SKU</TableHead>
          <TableHead>Station</TableHead>
          <TableHead className="w-28">Course</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {products.items.map((p) => {
          const current = routeByProduct.get(p.id);
          const station = current?.station ?? "kitchen";
          const course = current?.course ?? 1;
          return (
            <TableRow key={p.id}>
              <TableCell>{p.name}</TableCell>
              <TableCell className="font-mono text-xs">{p.sku}</TableCell>
              <TableCell>
                <Select
                  value={station}
                  onValueChange={(v) =>
                    save.mutate({
                      productId: p.id,
                      station: v as KdsStation,
                      course,
                    })
                  }
                >
                  <SelectTrigger className="w-36">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATIONS.map((s) => (
                      <SelectItem key={s} value={s}>
                        {STATION_LABELS[s]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  min={1}
                  max={9}
                  defaultValue={course}
                  onBlur={(e) => {
                    const next = Math.max(1, Math.min(9, Number(e.target.value)));
                    if (next !== course) {
                      save.mutate({ productId: p.id, station, course: next });
                    }
                  }}
                />
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
