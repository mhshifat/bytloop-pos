"use client";

import { Minus, Plus, Tag, Trash2, Cpu } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { isApiError } from "@/lib/api/error";
import { resolveUnitPrice } from "@/lib/api/hardware";
import { type CartLine, useCartStore } from "@/lib/stores/cart-store";
import { VerticalProfile, verticalProfileLabel } from "@/lib/enums/vertical-profile";
import { formatMoney } from "@/lib/utils/money";
import { posCartQuickLinks } from "@/lib/verticals/pos-store-mode";

import { ElectronicsSerialDialog } from "./electronics-serial-dialog";
import { UpsellPanel } from "./upsell-panel";
import { PairingsPanel } from "./pairings-panel";

type CartPanelProps = {
  readonly verticalProfile?: string;
};

export function CartPanel({ verticalProfile = VerticalProfile.RETAIL_GENERAL }: CartPanelProps) {
  const lines = useCartStore((s) => s.lines);
  const setQuantity = useCartStore((s) => s.setQuantity);
  const updateLine = useCartStore((s) => s.updateLine);
  const removeLine = useCartStore((s) => s.removeLine);
  const subtotalCents = useCartStore((s) => s.subtotalCents());
  const exciseCents = useCartStore((s) => s.exciseTotalCents());
  const [elOpen, setElOpen] = useState(false);
  const [elLine, setElLine] = useState<CartLine | null>(null);

  const isHardware = verticalProfile === VerticalProfile.RETAIL_HARDWARE;
  const isElectronics = verticalProfile === VerticalProfile.RETAIL_ELECTRONICS;
  const isLiquor = verticalProfile === VerticalProfile.RETAIL_LIQUOR;
  const isDept = verticalProfile === VerticalProfile.RETAIL_DEPARTMENT;
  const isPharmacy = verticalProfile === VerticalProfile.RETAIL_PHARMACY;

  const adjustHardwareQty = async (line: CartLine, newQty: number): Promise<void> => {
    setQuantity(line.lineId, newQty);
    if (newQty <= 0) return;
    if (!isHardware) return;
    try {
      const r = await resolveUnitPrice({ productId: line.productId, quantity: newQty });
      updateLine(line.lineId, { unitPriceCents: r.unitPriceCents });
    } catch (e) {
      if (isApiError(e)) {
        // leave prior unit price
      }
    }
  };

  const quick = posCartQuickLinks(verticalProfile);

  if (lines.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center text-sm text-muted-foreground">
        <p>Scan a product or tap a tile to start a sale.</p>
        {verticalProfile !== VerticalProfile.RETAIL_GENERAL ? (
          <p className="text-xs">Mode: {verticalProfileLabel(verticalProfile)}</p>
        ) : null}
        {quick.length > 0 ? (
          <div className="flex flex-wrap justify-center gap-2 text-xs text-muted-foreground">
            {quick.map((l) => (
              <Link key={l.href} className="text-primary underline" href={l.href}>
                {l.label}
              </Link>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <>
      {quick.length > 0 ? (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border px-4 py-2 text-[0.7rem] text-muted-foreground">
          <span className="font-medium text-foreground">Verticals</span>
          {quick.map((l) => (
            <Link key={l.href} className="text-primary underline" href={l.href}>
              {l.label}
            </Link>
          ))}
        </div>
      ) : null}
      <ul className="flex flex-1 flex-col divide-y divide-border overflow-y-auto">
        {lines.map((line) => (
          <li key={line.lineId} className="flex items-start gap-3 px-4 py-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium leading-snug">{line.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatMoney(line.unitPriceCents, line.currency)} &times; {line.quantity}
                {isHardware ? (
                  <span className="ml-1 text-amber-600/90 dark:text-amber-300/90">
                    (break pricing at checkout)
                  </span>
                ) : null}
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                {isDept && line.verticalData?.departmentName != null ? (
                  <span className="inline-flex items-center rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    <Tag size={10} className="mr-0.5" />
                    {String(line.verticalData.departmentName)}
                  </span>
                ) : null}
                {line.verticalData?.apparelVariantId != null ? (
                  <span className="text-[10px] text-muted-foreground">
                    {String(line.verticalData.size ?? "")}
                    {line.verticalData.color != null ? ` / ${String(line.verticalData.color)}` : null}
                  </span>
                ) : null}
                {line.verticalData?.serialNo != null || line.verticalData?.electronicsItemId != null ? (
                  <span className="text-[10px] font-mono text-muted-foreground">
                    S/N {String(line.verticalData.serialNo ?? "—")}
                  </span>
                ) : null}
                {line.verticalData?.pharmacyBatchId != null ? (
                  <span className="text-[10px] text-muted-foreground">
                    Batch {String(line.verticalData.pharmacyBatchId).slice(0, 8)}…
                  </span>
                ) : null}
              </div>
              {isPharmacy ? (
                <div className="mt-2 flex max-w-[14rem] items-center gap-2 text-xs">
                  <span className="shrink-0 text-muted-foreground">Batch UUID</span>
                  <Input
                    className="h-8 font-mono text-[10px]"
                    placeholder="optional — for audit"
                    value={String(line.verticalData?.pharmacyBatchId ?? "")}
                    onChange={(e) =>
                      updateLine(line.lineId, {
                        verticalData: {
                          ...line.verticalData,
                          pharmacyBatchId: e.target.value.trim() || undefined,
                        },
                      })
                    }
                  />
                </div>
              ) : null}
              {isElectronics && !line.verticalData?.serialNo && !line.verticalData?.electronicsItemId ? (
                <Button
                  type="button"
                  variant="link"
                  className="mt-1 h-auto p-0 text-xs"
                  onClick={() => {
                    setElLine(line);
                    setElOpen(true);
                  }}
                >
                  <Cpu size={12} className="mr-1" />
                  Set serial
                </Button>
              ) : null}
              {isLiquor ? (
                <div className="mt-2 flex max-w-[12rem] items-center gap-2 text-xs">
                  <span className="shrink-0 text-muted-foreground">Excise ¢</span>
                  <Input
                    type="number"
                    className="h-8"
                    min={0}
                    value={line.exciseCents ?? 0}
                    onChange={(e) =>
                      updateLine(line.lineId, { exciseCents: Math.max(0, Number(e.target.value) || 0) })
                    }
                  />
                </div>
              ) : null}
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <Button
                variant="outline"
                size="icon-sm"
                aria-label="Decrease quantity"
                onClick={() => {
                  if (isHardware) void adjustHardwareQty(line, line.quantity - 1);
                  else setQuantity(line.lineId, line.quantity - 1);
                }}
              >
                <Minus size={12} />
              </Button>
              <span className="w-8 text-center text-sm tabular-nums">{line.quantity}</span>
              <Button
                variant="outline"
                size="icon-sm"
                aria-label="Increase quantity"
                onClick={() => {
                  if (isHardware) void adjustHardwareQty(line, line.quantity + 1);
                  else setQuantity(line.lineId, line.quantity + 1);
                }}
              >
                <Plus size={12} />
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Remove"
                onClick={() => removeLine(line.lineId)}
              >
                <Trash2 size={12} />
              </Button>
            </div>
            <div className="w-24 text-right text-sm font-semibold tabular-nums">
              {formatMoney(
                line.unitPriceCents * line.quantity + (isLiquor ? (line.exciseCents ?? 0) : 0),
                line.currency,
              )}
            </div>
          </li>
        ))}
      </ul>
      <UpsellPanel />
      <PairingsPanel verticalProfile={verticalProfile} />
      {isLiquor && exciseCents > 0 ? (
        <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
          Subtotal {formatMoney(subtotalCents, lines[0]?.currency ?? "BDT")} + excise{" "}
          {formatMoney(exciseCents, lines[0]?.currency ?? "BDT")} (tax at charge)
        </div>
      ) : null}
      <ElectronicsSerialDialog open={elOpen} onOpenChange={setElOpen} line={elLine} />
    </>
  );
}
