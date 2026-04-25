"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { EntityLabel } from "@/components/shared/entity-label";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
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
import { isApiError } from "@/lib/api/error";
import { listOrders, type OrderSummary } from "@/lib/api/sales";
import { orderStatusLabel, orderTypeLabel } from "@/lib/enums/order-status";
import { formatMoney } from "@/lib/utils/money";

type StatusFilter = OrderSummary["status"] | "all";

export function OrdersList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<StatusFilter>("all");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", { page, status, since, until }],
    queryFn: () =>
      listOrders({
        page,
        pageSize: 25,
        status: status === "all" ? undefined : status,
        since: since ? new Date(since).toISOString() : undefined,
        until: until ? new Date(until).toISOString() : undefined,
      }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-border bg-surface p-3">
        <div className="space-y-1.5">
          <Label htmlFor="orders-status">Status</Label>
          <Select value={status} onValueChange={(v) => setStatus(v as StatusFilter)}>
            <SelectTrigger id="orders-status" className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="voided">Voided</SelectItem>
              <SelectItem value="refunded">Refunded</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="orders-since">From</Label>
          <Input
            id="orders-since"
            type="date"
            value={since}
            onChange={(e) => {
              setSince(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="orders-until">To</Label>
          <Input
            id="orders-until"
            type="date"
            value={until}
            onChange={(e) => {
              setUntil(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title={status === "all" && !since && !until ? "No orders yet" : "No matches"}
          description="Try clearing the filters."
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Number</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead className="text-right">Total</TableHead>
            <TableHead className="text-right">Opened</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((order) => (
            <TableRow
              key={order.id}
              className="cursor-pointer hover:bg-white/5"
              onClick={() => {
                window.location.href = `/orders/${order.id}`;
              }}
            >
              <TableCell className="font-mono text-xs">{order.number}</TableCell>
              <TableCell>
                <EnumBadge value={order.orderType} getLabel={orderTypeLabel} variant="outline" />
              </TableCell>
              <TableCell>
                <EnumBadge value={order.status} getLabel={orderStatusLabel} />
              </TableCell>
              <TableCell className="text-sm">
                <EntityLabel id={order.customerId} entity="customer" fallback="—" />
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatMoney(order.totalCents, order.currency)}
              </TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">
                {new Date(order.openedAt).toLocaleString()}
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
        </>
      ) : null}
    </div>
  );
}
