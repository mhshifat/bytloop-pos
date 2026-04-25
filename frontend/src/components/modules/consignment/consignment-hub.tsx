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
import {
  addItem,
  createConsignor,
  createPayout,
  type ConsignmentItem,
  type ConsignmentItemStatus,
  listConsignors,
  listItems,
  listPayouts,
  returnItem,
} from "@/lib/api/consignment";
import { listProducts } from "@/lib/api/catalog";
import { useCurrency } from "@/lib/hooks/use-currency";

const STATUSES: readonly ConsignmentItemStatus[] = ["listed", "sold", "returned"];

export function ConsignmentHub() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [itemFilter, setItemFilter] = useState<ConsignmentItemStatus | "all">("all");
  const [consignorFilter, setConsignorFilter] = useState<string>("all");
  const [serverError, setServerError] = useState<ApiError | null>(null);
  const [payoutError, setPayoutError] = useState<ApiError | null>(null);

  const { data: consignors, isLoading: cLoading } = useQuery({
    queryKey: ["consignment", "consignors"],
    queryFn: () => listConsignors(),
  });
  const { data: items, isLoading: iLoading } = useQuery({
    queryKey: [
      "consignment",
      "items",
      consignorFilter,
      itemFilter,
    ],
    queryFn: () =>
      listItems({
        consignorId: consignorFilter === "all" ? undefined : consignorFilter,
        status: itemFilter === "all" ? undefined : itemFilter,
      }),
  });
  const [payoutConsignor, setPayoutConsignor] = useState<string | null>(null);
  const { data: payoutHistory } = useQuery({
    queryKey: ["consignment", "payouts", payoutConsignor],
    queryFn: () => (payoutConsignor ? listPayouts(payoutConsignor) : Promise.resolve([])),
    enabled: payoutConsignor != null,
  });

  const [newName, setNewName] = useState("");
  const [newPayoutRate, setNewPayoutRate] = useState("50");
  const [addConsignorId, setAddConsignorId] = useState("");
  const [addProductId, setAddProductId] = useState("");
  const [addListPrice, setAddListPrice] = useState("");
  const [productSearch, setProductSearch] = useState("");
  const { data: productSearchResults } = useQuery({
    queryKey: ["products", "search", productSearch],
    queryFn: () => listProducts({ search: productSearch, pageSize: 15 }),
    enabled: productSearch.trim().length >= 2,
  });
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutNote, setPayoutNote] = useState("");

  const createC = useMutation({
    mutationFn: () =>
      createConsignor({
        name: newName,
        payoutRatePct: Math.min(100, Math.max(0, Number(newPayoutRate) || 50)),
      }),
    onSuccess: () => {
      setNewName("");
      setServerError(null);
      void queryClient.invalidateQueries({ queryKey: ["consignment"] });
      toast.success("Consignor added.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });
  const addCItem = useMutation({
    mutationFn: () =>
      addItem({
        consignorId: addConsignorId,
        productId: addProductId,
        listedPriceCents: Math.max(0, Math.round((Number(addListPrice) || 0) * 100)),
      }),
    onSuccess: () => {
      setAddListPrice("");
      setServerError(null);
      void queryClient.invalidateQueries({ queryKey: ["consignment", "items"] });
      toast.success("Item listed.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });
  const returnM = useMutation({
    mutationFn: (id: string) => returnItem(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["consignment", "items"] });
      toast.success("Item returned to consignor.");
    },
    onError: (e) => {
      if (isApiError(e)) setServerError(e);
    },
  });
  const payoutM = useMutation({
    mutationFn: () => {
      if (!payoutConsignor) throw new Error("Select consignor");
      return createPayout(payoutConsignor, {
        amountCents: Math.max(0, Math.round((Number(payoutAmount) || 0) * 100)),
        note: payoutNote.trim() || null,
      });
    },
    onSuccess: () => {
      setPayoutAmount("");
      setPayoutNote("");
      setPayoutError(null);
      void queryClient.invalidateQueries({ queryKey: ["consignment"] });
      toast.success("Payout recorded.");
    },
    onError: (e) => {
      if (isApiError(e)) setPayoutError(e);
    },
  });

  const cMap = new Map(consignors?.map((x) => [x.id, x]) ?? []);
  return (
    <div className="space-y-8">
      {serverError ? <InlineError error={serverError} /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold">Add consignor</h2>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              createC.mutate();
            }}
          >
            <div className="space-y-1.5">
              <Label htmlFor="c-name">Name</Label>
              <Input
                id="c-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
                placeholder="Jane Consignor"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-pct">Payout % (of sale)</Label>
              <Input
                id="c-pct"
                type="number"
                min={0}
                max={100}
                value={newPayoutRate}
                onChange={(e) => setNewPayoutRate(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={createC.isPending || !newName.trim()}>
              {createC.isPending ? "Saving…" : "Create consignor"}
            </Button>
          </form>
        </div>
        <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
          <h2 className="text-sm font-semibold">Payouts</h2>
          <p className="text-xs text-muted-foreground">
            May require the “Manage settings” permission. Choose a consignor to view
            history and record a payout in cents.
          </p>
          {payoutError ? <InlineError error={payoutError} /> : null}
          <div className="space-y-2">
            <Label>Consignor</Label>
            <Select
              value={payoutConsignor ?? "none"}
              onValueChange={(v) => setPayoutConsignor(v === "none" ? null : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select…" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">—</SelectItem>
                {(consignors ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} · {formatMoney(c.balanceCents)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {payoutConsignor && payoutHistory ? (
            <ul className="max-h-32 overflow-y-auto text-xs text-muted-foreground">
              {payoutHistory.length === 0 ? (
                <li>No payouts yet.</li>
              ) : (
                payoutHistory.map((p) => (
                  <li key={p.id}>
                    {p.createdAt.slice(0, 10)} — {formatMoney(p.amountCents)} · bal{" "}
                    {formatMoney(p.balanceAfterCents)}
                    {p.note ? ` — ${p.note}` : null}
                  </li>
                ))
              )}
            </ul>
          ) : null}
          {payoutConsignor ? (
            <form
              className="space-y-2"
              onSubmit={(e) => {
                e.preventDefault();
                payoutM.mutate();
              }}
            >
              <div className="flex gap-2">
                <div className="flex-1 space-y-1">
                  <Label htmlFor="p-amt">Amount (major units)</Label>
                  <Input
                    id="p-amt"
                    type="number"
                    step="0.01"
                    min={0}
                    value={payoutAmount}
                    onChange={(e) => setPayoutAmount(e.target.value)}
                  />
                </div>
              </div>
              <Input
                placeholder="Note (optional)"
                value={payoutNote}
                onChange={(e) => setPayoutNote(e.target.value)}
              />
              <Button type="submit" size="sm" disabled={payoutM.isPending}>
                Record payout
              </Button>
            </form>
          ) : null}
        </div>
      </div>

      <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">List consigned item</h2>
        <form
          className="grid gap-3 md:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            addCItem.mutate();
          }}
        >
          <div className="space-y-1.5">
            <Label>Consignor</Label>
            <Select
              value={addConsignorId || "none"}
              onValueChange={(v) => setAddConsignorId(v === "none" ? "" : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select…" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">—</SelectItem>
                {(consignors ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Listed price (major units)</Label>
            <Input
              type="number"
              min={0}
              step="0.01"
              value={addListPrice}
              onChange={(e) => setAddListPrice(e.target.value)}
              required
            />
          </div>
          <div className="md:col-span-2 space-y-2">
            <Label>Product</Label>
            <Input
              value={addProductId}
              onChange={(e) => setAddProductId(e.target.value)}
              placeholder="Product UUID"
            />
            <p className="text-xs text-muted-foreground">Or search by name:</p>
            <Input
              value={productSearch}
              onChange={(e) => {
                setProductSearch(e.target.value);
              }}
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
                        setAddProductId(p.id);
                        setProductSearch("");
                      }}
                    >
                      {p.name} · {p.sku}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <div className="md:col-span-2">
            <Button
              type="submit"
              disabled={addCItem.isPending || !addConsignorId || !addProductId}
            >
              {addCItem.isPending ? "Adding…" : "Add to floor"}
            </Button>
          </div>
        </form>
      </div>

      <div className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Consignor</Label>
            <Select
              value={consignorFilter}
              onValueChange={setConsignorFilter}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {(consignors ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Status</Label>
            <Select
              value={itemFilter}
              onValueChange={(v) => setItemFilter(v as ConsignmentItemStatus | "all")}
            >
              <SelectTrigger className="w-[160px]">
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
        {iLoading || cLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Consignor</TableHead>
                  <TableHead className="text-right">Listed</TableHead>
                  <TableHead className="w-[100px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(items ?? []).map((r: ConsignmentItem) => (
                  <TableRow key={r.id}>
                    <TableCell className="text-xs font-mono">{r.status}</TableCell>
                    <TableCell className="text-xs font-mono">{r.productId.slice(0, 8)}…</TableCell>
                    <TableCell>
                      {cMap.get(r.consignorId)?.name ?? "—"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(r.listedPriceCents)}
                    </TableCell>
                    <TableCell>
                      {r.status === "listed" ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (window.confirm("Return this item?")) {
                              returnM.mutate(r.id);
                            }
                          }}
                        >
                          Return
                        </Button>
                      ) : null}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        {(items ?? []).length === 0 && !iLoading ? (
          <p className="text-sm text-muted-foreground">No items match the filters.</p>
        ) : null}
      </div>
    </div>
  );
}
