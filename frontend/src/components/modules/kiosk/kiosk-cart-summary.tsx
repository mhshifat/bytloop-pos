"use client";

import { useRouter } from "next/navigation";
import { Minus, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/shared/ui/button";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

export function KioskCartSummary() {
  const router = useRouter();
  const lines = useCartStore((s) => s.lines);
  const total = useCartStore((s) => s.totalCents());
  const setQuantity = useCartStore((s) => s.setQuantity);
  const removeLine = useCartStore((s) => s.removeLine);
  const clear = useCartStore((s) => s.clear);

  const currency = lines[0]?.currency ?? "USD";

  return (
    <div className="flex h-full flex-col">
      <h2 className="mb-3 text-xl font-semibold tracking-tight">Your order</h2>
      {lines.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Tap a menu item to start.
        </p>
      ) : (
        <ul className="flex-1 space-y-3 overflow-y-auto pr-1">
          {lines.map((line) => (
            <li
              key={line.lineId}
              className="flex items-center justify-between gap-3 border-b border-border pb-3 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{line.name}</p>
                <p className="text-xs text-muted-foreground tabular-nums">
                  {formatMoney(line.unitPriceCents, line.currency)}
                </p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  size="icon-sm"
                  variant="outline"
                  aria-label="Decrement"
                  onClick={() => setQuantity(line.lineId, line.quantity - 1)}
                >
                  <Minus size={14} />
                </Button>
                <span className="w-8 text-center tabular-nums">{line.quantity}</span>
                <Button
                  size="icon-sm"
                  variant="outline"
                  aria-label="Increment"
                  onClick={() => setQuantity(line.lineId, line.quantity + 1)}
                >
                  <Plus size={14} />
                </Button>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Remove"
                  onClick={() => removeLine(line.lineId)}
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 space-y-3 border-t border-border pt-4">
        <div className="flex items-center justify-between text-lg font-semibold">
          <span>Total</span>
          <span className="tabular-nums">{formatMoney(total, currency)}</span>
        </div>
        <Button
          size="lg"
          className="h-14 w-full text-base"
          disabled={lines.length === 0}
          onClick={() => router.push("/kiosk/checkout")}
        >
          Pay now
        </Button>
        {lines.length > 0 ? (
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => {
              if (window.confirm("Clear the whole order?")) {
                clear();
              }
            }}
          >
            Start over
          </Button>
        ) : null}
      </div>
    </div>
  );
}
