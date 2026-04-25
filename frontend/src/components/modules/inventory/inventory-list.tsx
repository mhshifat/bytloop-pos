"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Badge } from "@/components/shared/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listInventoryLevels } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";

import { AdjustStockDialog } from "./adjust-stock-dialog";
import { ReorderPointCell } from "./reorder-point-cell";
import { TransferStockDialog } from "./transfer-stock-dialog";

export function InventoryList() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["inventory", "levels", { page }],
    queryFn: () => listInventoryLevels({ page, pageSize: 50 }),
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No stock movements yet"
        description="Sell products or receive stock to populate inventory."
      />
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SKU</TableHead>
            <TableHead>Product</TableHead>
            <TableHead>Location</TableHead>
            <TableHead className="text-right">On hand</TableHead>
            <TableHead className="text-right">Reorder at</TableHead>
            <TableHead></TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((level) => {
            const lowStock =
              level.reorderPoint > 0 && level.quantity <= level.reorderPoint;
            return (
              <TableRow key={level.id}>
                <TableCell className="font-mono text-xs">{level.sku}</TableCell>
                <TableCell>{level.productName}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {level.locationName}
                </TableCell>
                <TableCell
                  className={`text-right tabular-nums ${lowStock ? "text-amber-400" : ""}`}
                >
                  {level.quantity}
                </TableCell>
                <TableCell className="text-right">
                  <ReorderPointCell
                    productId={level.productId}
                    current={level.reorderPoint}
                  />
                </TableCell>
                <TableCell>
                  {lowStock ? (
                    <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                      <AlertTriangle size={12} aria-hidden="true" />
                      Low
                    </Badge>
                  ) : null}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <TransferStockDialog
                      productId={level.productId}
                      productName={level.productName}
                      sourceLocationId={level.locationId}
                      currentQuantity={level.quantity}
                    />
                    <AdjustStockDialog
                      productId={level.productId}
                      productName={level.productName}
                      currentQuantity={level.quantity}
                    />
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <DataPagination
        page={data.page}
        pageSize={data.pageSize}
        hasMore={data.hasMore}
        onPageChange={setPage}
      />
    </div>
  );
}
