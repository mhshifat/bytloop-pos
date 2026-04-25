"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PackageCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { EntityLabel } from "@/components/shared/entity-label";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { getPurchaseOrder, receivePurchaseOrder } from "@/lib/api/procurement";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { purchaseOrderStatusLabel } from "@/lib/enums/purchase-order-status";
import { formatMoney } from "@/lib/utils/money";

type ReceiveFormProps = {
  readonly purchaseOrderId: string;
};

export function ReceiveForm({ purchaseOrderId }: ReceiveFormProps) {
  const queryClient = useQueryClient();
  const [received, setReceived] = useState<Record<string, number>>({});
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["purchase-orders", purchaseOrderId],
    queryFn: () => getPurchaseOrder(purchaseOrderId),
  });

  const outstanding = useMemo(() => {
    return (data?.items ?? []).map((item) => ({
      ...item,
      remaining: item.quantityOrdered - item.quantityReceived,
    }));
  }, [data]);

  const anyReceived = Object.values(received).some((q) => q > 0);

  const mutation = useMutation({
    mutationFn: () =>
      receivePurchaseOrder(purchaseOrderId, {
        items: Object.entries(received)
          .filter(([, q]) => q > 0)
          .map(([purchaseOrderItemId, quantity]) => ({ purchaseOrderItemId, quantity })),
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
      setReceived({});
      setServerError(null);
      toast.success("Stock received and inventory updated.");
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data) return null;

  const allReceived = outstanding.every((o) => o.remaining === 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4">
        <div>
          <p className="font-mono text-sm">{data.number}</p>
          <p className="text-xs text-muted-foreground">
            Supplier: <EntityLabel id={data.supplierId} entity="customer" fallback="—" />
          </p>
        </div>
        <div className="flex items-center gap-3">
          <EnumBadge value={data.status} getLabel={purchaseOrderStatusLabel} />
          <span className="font-semibold tabular-nums">
            {formatMoney(data.totalCents, data.currency)}
          </span>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Product</TableHead>
            <TableHead className="text-right">Ordered</TableHead>
            <TableHead className="text-right">Received</TableHead>
            <TableHead className="text-right">Remaining</TableHead>
            <TableHead className="text-right">Receive now</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {outstanding.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                <EntityLabel id={item.productId} entity="product" />
              </TableCell>
              <TableCell className="text-right tabular-nums">{item.quantityOrdered}</TableCell>
              <TableCell className="text-right tabular-nums text-muted-foreground">
                {item.quantityReceived}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {item.remaining}
              </TableCell>
              <TableCell className="text-right">
                <Input
                  type="number"
                  min={0}
                  max={item.remaining}
                  value={received[item.id] ?? 0}
                  onChange={(e) =>
                    setReceived((prev) => ({
                      ...prev,
                      [item.id]: Math.min(item.remaining, Math.max(0, Number(e.target.value))),
                    }))
                  }
                  disabled={item.remaining === 0}
                  className="w-24 text-right tabular-nums"
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {serverError ? <InlineError error={serverError} /> : null}

      <div className="flex justify-end">
        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !anyReceived || allReceived}
        >
          <PackageCheck size={14} /> Receive marked quantities
        </Button>
      </div>
    </div>
  );
}
