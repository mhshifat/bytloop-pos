"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listProducts } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";
import { listLocations } from "@/lib/api/locations";
import { listSuppliers } from "@/lib/api/procurement";
import { listProductSuppliers, upsertProductSupplier } from "@/lib/api/product-suppliers";
import {
  applyReorderRecommendations,
  draftWeeklyPurchaseOrders,
  getReorderRecommendations,
  getSupplierReliability,
} from "@/lib/api/supply-chain";

export function SupplyChainPanel() {
  const [productSearch, setProductSearch] = useState("");
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [locationId, setLocationId] = useState<string>("");

  const productsQ = useQuery({
    queryKey: ["products", { productSearch }],
    queryFn: () => listProducts({ search: productSearch || undefined, page: 1, pageSize: 10 }),
  });
  const suppliersQ = useQuery({ queryKey: ["suppliers"], queryFn: () => listSuppliers() });
  const locationsQ = useQuery({ queryKey: ["locations"], queryFn: () => listLocations() });

  const mappingsQ = useQuery({
    queryKey: ["product-suppliers", selectedProductId],
    queryFn: () => listProductSuppliers({ productId: selectedProductId }),
    enabled: Boolean(selectedProductId),
  });

  const [supplierId, setSupplierId] = useState("");
  const [unitCostCents, setUnitCostCents] = useState(0);
  const [leadTimeDays, setLeadTimeDays] = useState(7);
  const [leadTimeStdDays, setLeadTimeStdDays] = useState(2);
  const [minOrderQty, setMinOrderQty] = useState(1);
  const [packSize, setPackSize] = useState(1);
  const [isPreferred, setIsPreferred] = useState(true);

  const upsert = useMutation({
    mutationFn: () =>
      upsertProductSupplier({
        productId: selectedProductId,
        supplierId,
        isPreferred,
        unitCostCents,
        leadTimeDays,
        leadTimeStdDays,
        minOrderQty,
        packSize,
      }),
    onSuccess: async () => {
      toast.success("Supplier mapping saved.");
      await mappingsQ.refetch();
    },
  });

  const reorderQ = useQuery({
    queryKey: ["ai", "supply-chain", "reorder-points", { locationId }],
    queryFn: () => getReorderRecommendations({ days: 60, limit: 50, locationId: locationId || undefined }),
  });

  const applyReorder = useMutation({
    mutationFn: async () => {
      const items = (reorderQ.data?.items ?? []).map((i) => ({
        productId: i.productId,
        reorderPoint: i.recommendedReorderPoint,
      }));
      const loc = reorderQ.data?.items?.[0]?.locationId;
      if (!loc) return { ok: false, error: "No location found" } as const;
      return applyReorderRecommendations({ locationId: loc, items });
    },
    onSuccess: (r) => {
      if (!r.ok) toast.error(r.error ?? "Failed to apply.");
      else toast.success(`Applied reorder points for ${r.updated} items.`);
    },
  });

  const draftPO = useMutation({
    mutationFn: () => draftWeeklyPurchaseOrders({ days: 60, locationId: locationId || undefined }),
    onSuccess: (r) => {
      const nums = (r.purchaseOrders ?? []).map((p) => p.number).slice(0, 5);
      toast.success(
        r.purchaseOrdersCreated > 0
          ? `Draft POs created: ${r.purchaseOrdersCreated}${nums.length ? ` (${nums.join(", ")}${r.purchaseOrdersCreated > nums.length ? ", …" : ""})` : ""}`
          : "No draft POs created.",
      );
    },
  });

  const reliabilityQ = useQuery({
    queryKey: ["ai", "supply-chain", "suppliers", "reliability"],
    queryFn: () => getSupplierReliability({ days: 180 }),
  });

  const selectedProduct = useMemo(
    () => productsQ.data?.items.find((p) => p.id === selectedProductId) ?? null,
    [productsQ.data, selectedProductId],
  );

  const supplierNameById = useMemo(() => {
    const m = new Map<string, string>();
    (suppliersQ.data ?? []).forEach((s) => m.set(s.id, s.name));
    return m;
  }, [suppliersQ.data]);

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Reorder recommendations</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Uses recent demand + lead time to recommend reorder points.
        </p>
        <div className="mt-3 max-w-sm">
          <Label>Location</Label>
          <select
            className="mt-1 h-9 w-full rounded-md border border-border bg-background px-3 text-sm"
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
          >
            <option value="">Default</option>
            {(locationsQ.data ?? []).map((l) => (
              <option key={l.id} value={l.id}>
                {l.code} · {l.name}
              </option>
            ))}
          </select>
        </div>
        {reorderQ.error && isApiError(reorderQ.error) ? <InlineError error={reorderQ.error} className="mt-3" /> : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <Button type="button" variant="outline" disabled={applyReorder.isPending} onClick={() => applyReorder.mutate()}>
            {applyReorder.isPending ? "Applying…" : "Apply all recommendations"}
          </Button>
          <Button type="button" variant="outline" disabled={draftPO.isPending} onClick={() => draftPO.mutate()}>
            {draftPO.isPending ? "Drafting…" : "Draft weekly POs"}
          </Button>
        </div>
        <div className="mt-3">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>SKU</TableHead>
                <TableHead>Product</TableHead>
                <TableHead className="text-right">On hand</TableHead>
                <TableHead className="text-right">Current ROP</TableHead>
                <TableHead className="text-right">Recommended</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(reorderQ.data?.items ?? []).map((i) => (
                <TableRow key={i.productId}>
                  <TableCell className="font-mono text-xs">{i.sku}</TableCell>
                  <TableCell>{i.name}</TableCell>
                  <TableCell className="text-right tabular-nums">{i.onHand}</TableCell>
                  <TableCell className="text-right tabular-nums text-muted-foreground">
                    {i.currentReorderPoint}
                  </TableCell>
                  <TableCell className="text-right tabular-nums font-semibold">
                    {i.recommendedReorderPoint}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Product → supplier mappings</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Needed for automated PO drafting (preferred supplier, lead time, pack size).
        </p>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="ps-search">Find product</Label>
            <Input
              id="ps-search"
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              placeholder="Search products…"
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {(productsQ.data?.items ?? []).map((p) => (
                <Button
                  key={p.id}
                  type="button"
                  size="sm"
                  variant={p.id === selectedProductId ? "default" : "outline"}
                  onClick={() => setSelectedProductId(p.id)}
                >
                  {p.sku} · {p.name}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Supplier</Label>
            <select
              className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm"
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
            >
              <option value="">Select…</option>
              {(suppliersQ.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label>Unit cost (cents)</Label>
            <Input type="number" min={0} value={unitCostCents} onChange={(e) => setUnitCostCents(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label>Lead time (days)</Label>
            <Input type="number" min={1} value={leadTimeDays} onChange={(e) => setLeadTimeDays(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label>Lead time std (days)</Label>
            <Input type="number" min={0} value={leadTimeStdDays} onChange={(e) => setLeadTimeStdDays(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label>MOQ</Label>
            <Input type="number" min={1} value={minOrderQty} onChange={(e) => setMinOrderQty(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label>Pack size</Label>
            <Input type="number" min={1} value={packSize} onChange={(e) => setPackSize(Number(e.target.value))} />
          </div>
          <div className="flex items-center gap-2 md:col-span-2">
            <input type="checkbox" checked={isPreferred} onChange={(e) => setIsPreferred(e.target.checked)} />
            <Label>Preferred supplier for this product</Label>
          </div>
        </div>

        {upsert.error && isApiError(upsert.error) ? <InlineError error={upsert.error} className="mt-3" /> : null}
        <div className="mt-3 flex justify-end">
          <Button type="button" disabled={!selectedProductId || !supplierId || upsert.isPending} onClick={() => upsert.mutate()}>
            {upsert.isPending ? "Saving…" : "Save mapping"}
          </Button>
        </div>

        <div className="mt-4">
          <p className="text-sm font-medium">
            Current mappings{selectedProduct ? ` for ${selectedProduct.sku}` : ""}
          </p>
          {mappingsQ.error && isApiError(mappingsQ.error) ? <InlineError error={mappingsQ.error} className="mt-2" /> : null}
          <ul className="mt-2 space-y-2 text-sm">
            {(mappingsQ.data ?? []).map((m) => (
              <li key={m.id} className="rounded-md border border-border bg-background p-3">
                <p className="font-medium">
                  {supplierNameById.get(m.supplierId) ?? `Supplier ${m.supplierId.slice(0, 8)}…`}{" "}
                  {m.isPreferred ? "(preferred)" : ""}
                </p>
                <p className="text-xs text-muted-foreground">
                  cost {m.unitCostCents}¢ · lead {m.leadTimeDays}±{m.leadTimeStdDays}d · MOQ {m.minOrderQty} · pack {m.packSize}
                </p>
              </li>
            ))}
            {mappingsQ.data && mappingsQ.data.length === 0 ? (
              <li className="text-muted-foreground">No mappings yet.</li>
            ) : null}
          </ul>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Supplier reliability</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          On-time rate uses PO promise date (or implied promise if missing).
        </p>
        {reliabilityQ.error && isApiError(reliabilityQ.error) ? <InlineError error={reliabilityQ.error} className="mt-3" /> : null}
        <div className="mt-3">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Supplier</TableHead>
                <TableHead className="text-right">On-time</TableHead>
                <TableHead className="text-right">POs</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(reliabilityQ.data?.items ?? []).map((s) => (
                <TableRow key={s.supplierId}>
                  <TableCell>{s.name}</TableCell>
                  <TableCell className="text-right tabular-nums">{(s.onTimeRate * 100).toFixed(0)}%</TableCell>
                  <TableCell className="text-right tabular-nums">{s.poCount}</TableCell>
                </TableRow>
              ))}
              {reliabilityQ.data && reliabilityQ.data.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-sm text-muted-foreground">
                    No received POs yet.
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

