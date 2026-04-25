"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
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
import { CloudinaryUploader } from "@/components/shared/cloudinary-uploader";
import { listProducts } from "@/lib/api/catalog";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { invoiceOcrToDraft } from "@/lib/api/ai-procurement";
import { createPurchaseOrder, listSuppliers } from "@/lib/api/procurement";

type Line = {
  readonly id: string;
  readonly productId: string;
  readonly quantityOrdered: number;
  readonly unitCostCents: number;
};

function newLineId(): string {
  return Math.random().toString(36).slice(2);
}

export function PoCreateForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [supplierId, setSupplierId] = useState("");
  const [currency, setCurrency] = useState("BDT");
  const [lines, setLines] = useState<Line[]>([
    { id: newLineId(), productId: "", quantityOrdered: 1, unitCostCents: 0 },
  ]);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: suppliers } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => listSuppliers(),
  });

  const { data: products } = useQuery({
    queryKey: ["products", "po-picker"],
    queryFn: () => listProducts({ pageSize: 100 }),
  });

  const updateLine = (id: string, patch: Partial<Line>): void => {
    setLines((prev) => prev.map((l) => (l.id === id ? { ...l, ...patch } : l)));
  };

  const total = lines.reduce(
    (sum, l) => sum + l.quantityOrdered * l.unitCostCents,
    0,
  );

  const canSubmit = Boolean(
    supplierId &&
      lines.length > 0 &&
      lines.every((l) => l.productId && l.quantityOrdered > 0 && l.unitCostCents >= 0),
  );

  const mutation = useMutation({
    mutationFn: () =>
      createPurchaseOrder({
        supplierId,
        currency: currency.toUpperCase(),
        items: lines.map((l) => ({
          productId: l.productId,
          quantityOrdered: l.quantityOrdered,
          unitCostCents: l.unitCostCents,
        })),
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async (po) => {
      await queryClient.invalidateQueries({ queryKey: ["purchase-orders"] });
      toast.success(`Purchase order ${po.number} created.`);
      router.push(`/purchase-orders/${po.id}`);
    },
  });

  const ocrMutation = useMutation({
    mutationFn: (asset: { readonly publicId: string; readonly url: string }) =>
      invoiceOcrToDraft({ asset, currency }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: (draft) => {
      if (draft.currency) setCurrency(draft.currency);
      if (draft.supplierId) setSupplierId(draft.supplierId);
      if (draft.lines?.length) {
        setLines(
          draft.lines.map((l) => ({
            id: newLineId(),
            productId: l.productId ?? "",
            quantityOrdered: l.quantity,
            unitCostCents: l.unitCostCents,
          })),
        );
      }
      toast.success("Draft extracted from invoice. Review and create the purchase order.");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="space-y-4"
    >
      <div className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-3">
        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="po-supplier">Supplier</Label>
          <Select value={supplierId} onValueChange={setSupplierId}>
            <SelectTrigger id="po-supplier">
              <SelectValue placeholder="Pick supplier" />
            </SelectTrigger>
            <SelectContent>
              {suppliers?.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="po-currency">Currency</Label>
          <Input
            id="po-currency"
            maxLength={3}
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
          />
        </div>
        <div className="md:col-span-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium">Invoice OCR (optional)</p>
            <span className="text-xs text-muted-foreground">Upload supplier invoice photo to prefill lines</span>
          </div>
          <div className="mt-2">
            <CloudinaryUploader
              purpose="invoice_ocr"
              label={ocrMutation.isPending ? "Extracting…" : "Upload invoice photo"}
              onUploaded={(asset) => {
                ocrMutation.mutate({ publicId: asset.publicId, url: asset.secureUrl });
              }}
            />
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm font-medium">Lines</p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() =>
              setLines((prev) => [
                ...prev,
                { id: newLineId(), productId: "", quantityOrdered: 1, unitCostCents: 0 },
              ])
            }
          >
            <Plus size={14} /> Add line
          </Button>
        </div>
        <div className="space-y-2">
          {lines.map((line, idx) => (
            <div key={line.id} className="grid gap-2 md:grid-cols-[2fr_1fr_1fr_auto]">
              <Select
                value={line.productId}
                onValueChange={(v) => updateLine(line.id, { productId: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder={`Line ${idx + 1} product`} />
                </SelectTrigger>
                <SelectContent>
                  {products?.items.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} — {p.sku}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                type="number"
                min={1}
                value={line.quantityOrdered}
                onChange={(e) =>
                  updateLine(line.id, {
                    quantityOrdered: Math.max(1, Number(e.target.value)),
                  })
                }
                aria-label="Quantity"
              />
              <Input
                type="number"
                min={0}
                value={line.unitCostCents}
                onChange={(e) =>
                  updateLine(line.id, { unitCostCents: Number(e.target.value) })
                }
                aria-label="Unit cost (cents)"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Remove line"
                disabled={lines.length === 1}
                onClick={() =>
                  setLines((prev) => prev.filter((l) => l.id !== line.id))
                }
              >
                <Trash2 size={14} />
              </Button>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-between border-t border-border pt-3 text-sm">
          <span className="text-muted-foreground">Total</span>
          <span className="font-semibold tabular-nums">
            {currency.toUpperCase()} {(total / 100).toFixed(2)}
          </span>
        </div>
      </div>

      {serverError ? <InlineError error={serverError} /> : null}

      <div className="flex justify-end">
        <Button type="submit" disabled={!canSubmit || mutation.isPending} size="lg">
          {mutation.isPending ? "Creating…" : "Create purchase order"}
        </Button>
      </div>
    </form>
  );
}
