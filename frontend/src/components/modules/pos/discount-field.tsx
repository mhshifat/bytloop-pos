"use client";

import { useQuery } from "@tanstack/react-query";
import { TicketPercent, X } from "lucide-react";
import { useState } from "react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { listDiscounts } from "@/lib/api/discounts";
import { usePosStore } from "@/lib/stores/pos-store";

const NONE_VALUE = "__none__";

export function DiscountField() {
  const discountCode = usePosStore((s) => s.discountCode);
  const setDiscount = usePosStore((s) => s.setDiscount);
  const [open, setOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["discounts"],
    queryFn: () => listDiscounts(),
    enabled: open || discountCode === null,
  });

  if (discountCode) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-md bg-white/5 px-3 py-2 text-sm">
        <span>
          <span className="text-muted-foreground">Discount:</span>{" "}
          <span className="font-mono">{discountCode}</span>
        </span>
        <button
          type="button"
          onClick={() => setDiscount(null)}
          aria-label="Remove discount"
          className="text-muted-foreground hover:text-foreground"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  const activeCodes = data ?? [];

  if (activeCodes.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">
        <TicketPercent size={12} aria-hidden="true" className="mr-1 inline" />
        No active discounts. Create one in Settings.
      </p>
    );
  }

  return (
    <Select
      value={NONE_VALUE}
      onValueChange={(v) => {
        if (v && v !== NONE_VALUE) setDiscount(v);
      }}
      onOpenChange={setOpen}
    >
      <SelectTrigger className="w-full">
        <div className="flex items-center gap-2 text-muted-foreground">
          <TicketPercent size={14} aria-hidden="true" />
          <SelectValue placeholder="Apply discount" />
        </div>
      </SelectTrigger>
      <SelectContent>
        {activeCodes.map((d) => (
          <SelectItem key={d.id} value={d.code}>
            <span className="font-mono text-xs">{d.code}</span>
            <span className="ml-2 text-muted-foreground">
              {d.kind === "percent" && d.percent
                ? `${(Number(d.percent) * 100).toFixed(0)}% off`
                : d.amountCents
                  ? `${d.currency} ${(d.amountCents / 100).toFixed(2)} off`
                  : d.name}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
