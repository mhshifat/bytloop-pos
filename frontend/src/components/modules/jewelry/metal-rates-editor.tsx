"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
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
import { listRates, upsertRate } from "@/lib/api/jewelry";
import { useCurrency } from "@/lib/hooks/use-currency";

const METALS = ["gold", "silver", "platinum"] as const;
const KARATS = [24, 22, 18, 14, 10] as const;

export function MetalRatesEditor() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["jewelry", "rates"],
    queryFn: () => listRates(),
  });

  const [metal, setMetal] = useState<(typeof METALS)[number]>("gold");
  const [karat, setKarat] = useState<number>(22);
  const [rate, setRate] = useState<number>(0);
  const [effectiveOn, setEffectiveOn] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const save = useMutation({
    mutationFn: () =>
      upsertRate({
        metal,
        karat,
        ratePerGramCents: rate,
        effectiveOn,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jewelry", "rates"] });
      toast.success("Rate set for today.");
      setServerError(null);
    },
  });

  return (
    <div className="space-y-4">
      <form
        className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-5"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="space-y-1.5">
          <Label htmlFor="rate-metal">Metal</Label>
          <Select
            value={metal}
            onValueChange={(v) => setMetal(v as (typeof METALS)[number])}
          >
            <SelectTrigger id="rate-metal">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {METALS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="rate-karat">Karat</Label>
          <Select value={String(karat)} onValueChange={(v) => setKarat(Number(v))}>
            <SelectTrigger id="rate-karat">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {KARATS.map((k) => (
                <SelectItem key={k} value={String(k)}>
                  {k}K
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="rate-cents">Rate per gram (cents)</Label>
          <Input
            id="rate-cents"
            type="number"
            min={0}
            value={rate}
            onChange={(e) => setRate(Number(e.target.value))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="rate-date">Effective on</Label>
          <Input
            id="rate-date"
            type="date"
            value={effectiveOn}
            onChange={(e) => setEffectiveOn(e.target.value)}
          />
        </div>
        <div className="flex items-end">
          <Button type="submit" disabled={save.isPending || rate <= 0}>
            {save.isPending ? "Saving…" : "Save rate"}
          </Button>
        </div>
        {serverError ? (
          <div className="md:col-span-5">
            <InlineError error={serverError} />
          </div>
        ) : null}
      </form>

      <h3 className="text-base font-medium">Current rates</h3>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="No rates yet"
          description="Set today's rate above to start quoting jewelry prices."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Metal</TableHead>
              <TableHead>Karat</TableHead>
              <TableHead className="text-right">Rate / gram</TableHead>
              <TableHead>Effective on</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="capitalize">{r.metal}</TableCell>
                <TableCell>{r.karat}K</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(r.ratePerGramCents)}
                </TableCell>
                <TableCell>{new Date(r.effectiveOn).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
