"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
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
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { listProducts } from "@/lib/api/catalog";
import {
  type CustomOrder,
  type CustomOrderStatus,
  listCustomOrders,
  markDelivered,
  markReady,
  startProduction,
  updateCustomOrder,
  quoteOrder,
} from "@/lib/api/furniture";
import { useCurrency } from "@/lib/hooks/use-currency";

const STATUSES: readonly CustomOrderStatus[] = [
  "quoted",
  "in_production",
  "ready",
  "delivered",
  "cancelled",
];

export function FurnitureOrdersHub() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<CustomOrderStatus | "all">("all");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: orders, isLoading } = useQuery({
    queryKey: ["furniture", "custom-orders", statusFilter],
    queryFn: () =>
      listCustomOrders({
        status: statusFilter === "all" ? undefined : statusFilter,
      }),
  });

  const [qProductId, setQProductId] = useState("");
  const [qDescription, setQDescription] = useState("");
  const [qPrice, setQPrice] = useState("");
  const [qDims, setQDims] = useState("");
  const [qMaterial, setQMaterial] = useState("");
  const [qFinish, setQFinish] = useState("");
  const [qReady, setQReady] = useState("");
  const [productSearch, setProductSearch] = useState("");

  const { data: productSearchResults } = useQuery({
    queryKey: ["products", "furniture-search", productSearch],
    queryFn: () => listProducts({ search: productSearch, pageSize: 15 }),
    enabled: productSearch.trim().length >= 2,
  });

  const quoteM = useMutation({
    mutationFn: () =>
      quoteOrder({
        productId: qProductId,
        description: qDescription,
        quotedPriceCents: Math.max(0, Math.round((Number(qPrice) || 0) * 100)),
        dimensionsCm: qDims.trim() || null,
        material: qMaterial.trim() || null,
        finish: qFinish.trim() || null,
        estimatedReadyOn: qReady.trim() || null,
      }),
    onSuccess: () => {
      setQDescription("");
      setQPrice("");
      setQDims("");
      setQMaterial("");
      setQFinish("");
      setQReady("");
      setServerError(null);
      void queryClient.invalidateQueries({ queryKey: ["furniture"] });
      toast.success("Custom order created.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });

  const sp = useMutation({
    mutationFn: (id: string) => startProduction(id, {}),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["furniture"] });
      toast.success("Started production.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });
  const mr = useMutation({
    mutationFn: (id: string) => markReady(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["furniture"] });
      toast.success("Marked ready.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });
  const md = useMutation({
    mutationFn: (id: string) => markDelivered(id, { orderId: null }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["furniture"] });
      toast.success("Marked delivered.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });

  return (
    <div className="space-y-8">
      {serverError ? <InlineError error={serverError} /> : null}

      <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">New quote (custom order)</h2>
        <form
          className="grid gap-3 md:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            quoteM.mutate();
          }}
        >
          <div className="md:col-span-2 space-y-1">
            <Label>Product</Label>
            <Input
              value={qProductId}
              onChange={(e) => setQProductId(e.target.value)}
              placeholder="Product UUID (placeholder or finished good)"
            />
            <p className="text-xs text-muted-foreground">Search to pick:</p>
            <Input
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              placeholder="Type 2+ characters"
            />
            {productSearchResults && productSearchResults.items.length > 0 ? (
              <ul className="max-h-32 overflow-y-auto rounded border border-border p-1 text-sm">
                {productSearchResults.items.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      className="w-full rounded px-2 py-1.5 text-left hover:bg-muted/50"
                      onClick={() => {
                        setQProductId(p.id);
                        setProductSearch("");
                      }}
                    >
                      {p.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <div className="md:col-span-2 space-y-1.5">
            <Label>Description / notes</Label>
            <Input
              value={qDescription}
              onChange={(e) => setQDescription(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label>Quoted price</Label>
            <Input
              type="number"
              min={0}
              step="0.01"
              value={qPrice}
              onChange={(e) => setQPrice(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label>Est. ready (ISO date)</Label>
            <Input
              value={qReady}
              onChange={(e) => setQReady(e.target.value)}
              placeholder="2026-05-01"
            />
          </div>
          <div className="space-y-1.5">
            <Label>Dimensions (cm)</Label>
            <Input value={qDims} onChange={(e) => setQDims(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Material / finish</Label>
            <Input
              value={qMaterial}
              onChange={(e) => setQMaterial(e.target.value)}
              placeholder="Material"
            />
            <Input value={qFinish} onChange={(e) => setQFinish(e.target.value)} placeholder="Finish" />
          </div>
          <div className="md:col-span-2">
            <Button
              type="submit"
              disabled={quoteM.isPending || !qProductId || !qDescription}
            >
              {quoteM.isPending ? "Saving…" : "Create quote"}
            </Button>
          </div>
        </form>
      </div>

      <div className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Status</Label>
            <Select
              value={statusFilter}
              onValueChange={(v) => setStatusFilter(v as CustomOrderStatus | "all")}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Est. ready</TableHead>
                  <TableHead className="text-right">Quote</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(orders ?? []).map((o: CustomOrder) => (
                  <TableRow key={o.id}>
                    <TableCell className="text-xs font-mono whitespace-nowrap">{o.status}</TableCell>
                    <TableCell>
                      <p className="max-w-[200px] truncate text-sm" title={o.description}>
                        {o.description}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {o.material ?? ""} {o.finish ? `· ${o.finish}` : ""}
                      </p>
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {o.estimatedReadyOn ? o.estimatedReadyOn.slice(0, 10) : "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(o.quotedPriceCents)}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {o.status === "quoted" ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => sp.mutate(o.id)}
                          >
                            Build
                          </Button>
                        ) : null}
                        {o.status === "in_production" ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => mr.mutate(o.id)}
                          >
                            Ready
                          </Button>
                        ) : null}
                        {o.status === "ready" ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => md.mutate(o.id)}
                          >
                            Delivered
                          </Button>
                        ) : null}
                        {o.status === "quoted" ? (
                          <FurniturePricePatch
                            order={o}
                            onPatched={() => {
                              void queryClient.invalidateQueries({ queryKey: ["furniture"] });
                            }}
                          />
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        {!isLoading && (orders ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">No custom orders yet.</p>
        ) : null}
      </div>
    </div>
  );
}

function FurniturePricePatch({
  order,
  onPatched,
}: {
  readonly order: CustomOrder;
  onPatched: () => void;
}) {
  const [next, setNext] = useState(
    (order.quotedPriceCents / 100).toFixed(2),
  );
  const m = useMutation({
    mutationFn: () =>
      updateCustomOrder(order.id, {
        quotedPriceCents: Math.max(
          0,
          Math.round((Number(next) || 0) * 100),
        ),
      }),
    onSuccess: () => {
      onPatched();
      toast.success("Price updated.");
    },
  });
  return (
    <div className="flex items-center gap-1 text-xs">
      <Input
        className="h-8 w-20"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        aria-label="Requote price"
      />
      <Button
        type="button"
        size="sm"
        variant="ghost"
        className="h-8"
        onClick={() => m.mutate()}
        disabled={m.isPending}
      >
        Save
      </Button>
    </div>
  );
}
