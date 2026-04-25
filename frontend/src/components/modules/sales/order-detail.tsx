"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Printer, Repeat, RotateCcw, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { useCartStore } from "@/lib/stores/cart-store";

import { EntityLabel } from "@/components/shared/entity-label";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { isApiError } from "@/lib/api/error";
import { getOrder, refundOrder, voidOrder } from "@/lib/api/sales";
import { orderStatusLabel, orderTypeLabel } from "@/lib/enums/order-status";
import { formatMoney } from "@/lib/utils/money";

type OrderDetailProps = {
  readonly orderId: string;
};

export function OrderDetail({ orderId }: OrderDetailProps) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const addLine = useCartStore((s) => s.addLine);
  const clearCart = useCartStore((s) => s.clear);
  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", orderId],
    queryFn: () => getOrder(orderId),
  });

  const onReorder = (): void => {
    if (!data) return;
    clearCart();
    for (const item of data.items) {
      addLine(
        {
          productId: item.productId,
          name: item.nameSnapshot,
          unitPriceCents: item.unitPriceCents,
          currency: data.currency,
          verticalData: item.verticalData,
        },
        item.quantity,
      );
    }
    toast.success(`Loaded ${data.items.length} items into a new sale.`);
    router.push("/pos");
  };

  const voidMutation = useMutation({
    mutationFn: () => voidOrder(orderId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Order voided.");
    },
  });

  const refundMutation = useMutation({
    mutationFn: () => refundOrder(orderId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Order refunded.");
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data) return null;

  const canMutate = data.status === "completed";

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="font-mono text-xl">#{data.number}</h1>
          <div className="flex gap-2">
            <EnumBadge value={data.orderType} getLabel={orderTypeLabel} variant="outline" />
            <EnumBadge value={data.status} getLabel={orderStatusLabel} />
          </div>
        </div>
        <div className="flex gap-2">
          {canMutate ? (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  if (window.confirm("Void this order? Stock will be returned.")) {
                    voidMutation.mutate();
                  }
                }}
                disabled={voidMutation.isPending}
              >
                <XCircle size={14} /> Void
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  if (window.confirm("Refund this order? Stock will be returned.")) {
                    refundMutation.mutate();
                  }
                }}
                disabled={refundMutation.isPending}
              >
                <RotateCcw size={14} /> Refund
              </Button>
            </>
          ) : null}
          <Button variant="outline" onClick={onReorder}>
            <Repeat size={14} /> Reorder
          </Button>
          <Button variant="outline" onClick={() => window.print()}>
            <Printer size={14} /> Print
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Items</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">Unit</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Line total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.nameSnapshot}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(item.unitPriceCents, data.currency)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{item.quantity}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(item.lineTotalCents, data.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Totals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5 text-sm">
          {data.customerId ? (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Customer</span>
              <EntityLabel id={data.customerId} entity="customer" />
            </div>
          ) : null}
          <Row label="Subtotal" value={formatMoney(data.subtotalCents, data.currency)} />
          <Row label="Tax" value={formatMoney(data.taxCents, data.currency)} />
          {data.discountCents > 0 ? (
            <Row
              label="Discount"
              value={`-${formatMoney(data.discountCents, data.currency)}`}
            />
          ) : null}
          <Row
            label="Total"
            value={formatMoney(data.totalCents, data.currency)}
            bold
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Method</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.payments.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono text-xs">{p.method}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(p.amountCents, p.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({
  label,
  value,
  bold = false,
}: {
  readonly label: string;
  readonly value: string;
  readonly bold?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className={bold ? "font-semibold" : "text-muted-foreground"}>{label}</span>
      <span className={bold ? "font-semibold tabular-nums" : "tabular-nums"}>{value}</span>
    </div>
  );
}
