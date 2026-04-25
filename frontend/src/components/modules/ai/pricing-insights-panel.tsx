"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
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
import {
  applyDynamicPricing,
  applyHappyHour,
  applyJewelryMetalRate,
  getElasticity,
  suggestBundles,
  suggestDynamicPricing,
  suggestHappyHour,
  suggestJewelryMetalRate,
} from "@/lib/api/ai-pricing";
import { isApiError } from "@/lib/api/error";

export function PricingInsightsPanel() {
  const happyQ = useQuery({ queryKey: ["ai", "pricing", "happy-hour"], queryFn: () => suggestHappyHour({ days: 28 }) });
  const elasQ = useQuery({ queryKey: ["ai", "pricing", "elasticity"], queryFn: () => getElasticity({ days: 180, limit: 30 }) });
  const bundlesQ = useQuery({ queryKey: ["ai", "pricing", "bundles"], queryFn: () => suggestBundles({ days: 90, limit: 10 }) });
  const dynQ = useQuery({ queryKey: ["ai", "pricing", "dynamic"], queryFn: () => suggestDynamicPricing() });

  const [hhCode, setHhCode] = useState("HAPPY10");
  const [hhName, setHhName] = useState("Happy hour 10% off");
  const hhApply = useMutation({
    mutationFn: (s: { startHour: number; endHour: number; percentOff: number }) =>
      applyHappyHour({ code: hhCode, name: hhName, ...s }),
    onSuccess: (r) => {
      if (r.ok) toast.success(`Discount created: ${r.code}`);
    },
  });

  const dynApply = useMutation({
    mutationFn: () => applyDynamicPricing({ hotelDeltaPct: dynQ.data?.hotel.suggestedDeltaPct, rentalDeltaPct: dynQ.data?.rental.suggestedDeltaPct }),
    onSuccess: (r) => toast.success(`Updated rates: ${r.updated}`),
  });

  const [spot, setSpot] = useState(0);
  const [metal, setMetal] = useState("gold");
  const [karat, setKarat] = useState(22);
  const jewelrySuggest = useMutation({
    mutationFn: () => suggestJewelryMetalRate({ metal, karat, spotPerGramCents: spot, markupPct: 0.08 }),
  });
  const jewelryApply = useMutation({
    mutationFn: () => applyJewelryMetalRate({ metal, karat, ratePerGramCents: jewelrySuggest.data?.suggestedRatePerGramCents ?? 0 }),
    onSuccess: () => toast.success("Jewelry metal rate saved."),
  });

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Happy-hour auto-suggest</h2>
        {happyQ.error && isApiError(happyQ.error) ? <InlineError error={happyQ.error} className="mt-3" /> : null}
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Discount code</Label>
            <Input value={hhCode} onChange={(e) => setHhCode(e.target.value.toUpperCase())} />
          </div>
          <div className="space-y-1.5">
            <Label>Name</Label>
            <Input value={hhName} onChange={(e) => setHhName(e.target.value)} />
          </div>
        </div>
        <div className="mt-3 space-y-2 text-sm">
          {(happyQ.data?.suggestions ?? []).map((s, idx) => (
            <div key={idx} className="flex items-center justify-between gap-3 rounded-md border border-border bg-background p-3">
              <div>
                <p className="font-medium">
                  {s.startHour}:00–{s.endHour}:00 · {(s.percentOff * 100).toFixed(0)}% off
                </p>
                <p className="text-xs text-muted-foreground">{s.reason}</p>
              </div>
              <Button type="button" size="sm" variant="outline" disabled={hhApply.isPending} onClick={() => hhApply.mutate(s)}>
                Create discount
              </Button>
            </div>
          ))}
          {happyQ.data && happyQ.data.suggestions.length === 0 ? (
            <p className="text-muted-foreground">Not enough data to suggest a window yet.</p>
          ) : null}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Price elasticity (top movers)</h2>
        {elasQ.error && isApiError(elasQ.error) ? <InlineError error={elasQ.error} className="mt-3" /> : null}
        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Product</TableHead>
              <TableHead className="text-right">Elasticity</TableHead>
              <TableHead className="text-right">Points</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(elasQ.data?.items ?? []).map((r) => (
              <TableRow key={r.productId}>
                <TableCell className="font-mono text-xs">{r.productId.slice(0, 8)}…</TableCell>
                <TableCell className="text-right tabular-nums">{r.elasticity}</TableCell>
                <TableCell className="text-right tabular-nums">{r.points}</TableCell>
              </TableRow>
            ))}
            {elasQ.data && elasQ.data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-sm text-muted-foreground">
                  No elasticity results yet.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Bundle / upsell optimizer</h2>
        {bundlesQ.error && isApiError(bundlesQ.error) ? <InlineError error={bundlesQ.error} className="mt-3" /> : null}
        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Pair</TableHead>
              <TableHead className="text-right">Co-occurrence</TableHead>
              <TableHead className="text-right">Lift</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(bundlesQ.data?.items ?? []).map((b, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">
                  {b.a.slice(0, 8)}… + {b.b.slice(0, 8)}…
                </TableCell>
                <TableCell className="text-right tabular-nums">{b.cooccurrence}</TableCell>
                <TableCell className="text-right tabular-nums">{b.lift}</TableCell>
              </TableRow>
            ))}
            {bundlesQ.data && bundlesQ.data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-sm text-muted-foreground">
                  No bundle suggestions yet.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Dynamic pricing (hotel/cinema/rental)</h2>
        {dynQ.error && isApiError(dynQ.error) ? <InlineError error={dynQ.error} className="mt-3" /> : null}
        {dynQ.data ? (
          <div className="mt-3 space-y-3 text-sm">
            <p>
              Hotel occupancy next 7d: <span className="font-semibold">{(dynQ.data.hotel.occupancyNext7d * 100).toFixed(0)}%</span> · suggested delta{" "}
              <span className="font-semibold">{(dynQ.data.hotel.suggestedDeltaPct * 100).toFixed(0)}%</span>
            </p>
            <p>
              Rental utilization: <span className="font-semibold">{(dynQ.data.rental.utilization * 100).toFixed(0)}%</span> · suggested delta{" "}
              <span className="font-semibold">{(dynQ.data.rental.suggestedDeltaPct * 100).toFixed(0)}%</span>
            </p>
            <Button type="button" variant="outline" disabled={dynApply.isPending} onClick={() => dynApply.mutate()}>
              {dynApply.isPending ? "Applying…" : "Apply hotel+rental deltas"}
            </Button>
            <p className="text-xs text-muted-foreground">
              Cinema show-level apply is supported via API; add a dedicated UI later if you want.
            </p>
          </div>
        ) : null}
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Jewelry daily metal rate suggestion</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label>Metal</Label>
            <Input value={metal} onChange={(e) => setMetal(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Karat</Label>
            <Input type="number" min={1} max={24} value={karat} onChange={(e) => setKarat(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label>Spot per gram (cents)</Label>
            <Input type="number" min={0} value={spot} onChange={(e) => setSpot(Number(e.target.value))} />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button type="button" variant="outline" disabled={jewelrySuggest.isPending} onClick={() => jewelrySuggest.mutate()}>
            {jewelrySuggest.isPending ? "Suggesting…" : "Suggest rate"}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={!jewelrySuggest.data || jewelryApply.isPending}
            onClick={() => jewelryApply.mutate()}
          >
            {jewelryApply.isPending ? "Saving…" : "Apply suggested rate"}
          </Button>
          {jewelrySuggest.data ? (
            <p className="text-sm text-muted-foreground">
              Suggested: <span className="font-semibold">{jewelrySuggest.data.suggestedRatePerGramCents}</span> ¢/g
            </p>
          ) : null}
        </div>
        {jewelrySuggest.error && isApiError(jewelrySuggest.error) ? <InlineError error={jewelrySuggest.error} className="mt-3" /> : null}
      </div>

      <div className="text-xs text-muted-foreground">
        Tip: happy-hour apply creates a Discount row (see <Link className="underline" href="/settings">Settings → Discounts</Link>).
      </div>
    </div>
  );
}

