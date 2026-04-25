"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
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
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type SellUnit, upsertWeighable } from "@/lib/api/grocery";

const UNIT_LABELS: Record<SellUnit, string> = {
  each: "Each",
  kg: "Per kilogram",
  g: "Per gram",
  lb: "Per pound",
};

type WeighableFormProps = {
  readonly productId: string;
};

export function WeighableForm({ productId }: WeighableFormProps) {
  const queryClient = useQueryClient();
  const [unit, setUnit] = useState<SellUnit>("kg");
  const [price, setPrice] = useState(0);
  const [tare, setTare] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      upsertWeighable({
        productId,
        sellUnit: unit,
        pricePerUnitCents: price,
        tareGrams: tare,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["grocery", "weighable", productId] });
      setServerError(null);
      toast.success("Weighable pricing saved.");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="grid gap-3 md:grid-cols-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="weighable-unit">Sell by</Label>
        <Select value={unit} onValueChange={(v) => setUnit(v as SellUnit)}>
          <SelectTrigger id="weighable-unit">
            <SelectValue>{UNIT_LABELS[unit]}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(UNIT_LABELS) as SellUnit[]).map((u) => (
              <SelectItem key={u} value={u}>
                {UNIT_LABELS[u]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="weighable-price">Price per unit (cents)</Label>
        <Input
          id="weighable-price"
          type="number"
          min={0}
          value={price}
          onChange={(e) => setPrice(Number(e.target.value))}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="weighable-tare">Tare (grams)</Label>
        <Input
          id="weighable-tare"
          type="number"
          min={0}
          value={tare}
          onChange={(e) => setTare(Number(e.target.value))}
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" disabled={mutation.isPending}>
          Save weighable
        </Button>
      </div>
      {serverError ? (
        <div className="md:col-span-4">
          <InlineError error={serverError} />
        </div>
      ) : null}
    </form>
  );
}
