"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listPurchaseOrders } from "@/lib/api/procurement";
import { isApiError } from "@/lib/api/error";
import { purchaseOrderStatusLabel } from "@/lib/enums/purchase-order-status";
import { formatMoney } from "@/lib/utils/money";

export function PurchaseOrdersList() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["purchase-orders", { page }],
    queryFn: () => listPurchaseOrders({ page, pageSize: 25 }),
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No purchase orders yet"
        description="Create a PO to order stock from a supplier."
      />
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Number</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Total</TableHead>
            <TableHead className="text-right">Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((po) => (
            <TableRow
              key={po.id}
              className="cursor-pointer hover:bg-white/5"
              onClick={() => {
                window.location.href = `/purchase-orders/${po.id}`;
              }}
            >
              <TableCell className="font-mono text-xs">{po.number}</TableCell>
              <TableCell>
                <EnumBadge value={po.status} getLabel={purchaseOrderStatusLabel} />
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatMoney(po.totalCents, po.currency)}
              </TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">
                {new Date(po.createdAt).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
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
