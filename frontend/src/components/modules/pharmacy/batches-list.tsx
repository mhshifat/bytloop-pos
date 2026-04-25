"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listBatches, listExpiringBatches } from "@/lib/api/pharmacy";
import { isApiError } from "@/lib/api/error";

export function BatchesList() {
  const [mode, setMode] = useState<"all" | "expiring">("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["pharmacy", "batches", mode],
    queryFn: () => (mode === "expiring" ? listExpiringBatches(30) : listBatches()),
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button
          variant={mode === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("all")}
        >
          All batches
        </Button>
        <Button
          variant={mode === "expiring" ? "default" : "outline"}
          size="sm"
          onClick={() => setMode("expiring")}
        >
          Expiring in 30 days
        </Button>
      </div>

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title={mode === "expiring" ? "Nothing expires soon" : "No batches yet"}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Batch no</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Expiry</TableHead>
              <TableHead className="text-right">Remaining</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((b) => (
              <TableRow key={b.id}>
                <TableCell className="font-mono text-xs">{b.batchNo}</TableCell>
                <TableCell className="font-mono text-xs">
                  {b.productId.slice(0, 8)}…
                </TableCell>
                <TableCell>{b.expiryDate}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {b.quantityRemaining}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
