"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

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
import { isApiError } from "@/lib/api/error";
import { optimizeRoute, suggestStaffSchedule, tableTurnForecast } from "@/lib/api/ai-ops";

export function OpsInsightsPanel() {
  const schedQ = useQuery({ queryKey: ["ai", "ops", "schedule"], queryFn: () => suggestStaffSchedule() });
  const tableQ = useQuery({ queryKey: ["ai", "ops", "table-turn"], queryFn: () => tableTurnForecast() });

  const [routeDay, setRouteDay] = useState(() => new Date().toISOString().slice(0, 10));
  const routeQ = useQuery({
    queryKey: ["ai", "ops", "route", routeDay],
    queryFn: () => optimizeRoute(routeDay),
    enabled: Boolean(routeDay),
  });

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Staff schedule (suggested)</h2>
        {schedQ.error && isApiError(schedQ.error) ? <InlineError error={schedQ.error} className="mt-3" /> : null}
        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Day</TableHead>
              <TableHead>Shift</TableHead>
              <TableHead>Role</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(schedQ.data?.shifts ?? []).map((s, i) => (
              <TableRow key={i}>
                <TableCell>{s.day}</TableCell>
                <TableCell className="tabular-nums">
                  {s.startHour}:00–{s.endHour}:00
                </TableCell>
                <TableCell>{s.roleHint}</TableCell>
              </TableRow>
            ))}
            {schedQ.data && schedQ.data.shifts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-sm text-muted-foreground">
                  Not enough order history yet.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Delivery route optimizer</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <div className="space-y-1.5">
            <Label>Day</Label>
            <Input type="date" value={routeDay} onChange={(e) => setRouteDay(e.target.value)} />
          </div>
          <Button type="button" variant="outline" onClick={() => routeQ.refetch()}>
            Refresh
          </Button>
        </div>
        {routeQ.error && isApiError(routeQ.error) ? <InlineError error={routeQ.error} className="mt-3" /> : null}
        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>#</TableHead>
              <TableHead>City</TableHead>
              <TableHead>Postal</TableHead>
              <TableHead>Address</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(routeQ.data?.stops ?? []).map((s: any, idx: number) => (
              <TableRow key={s.deliveryId ?? idx}>
                <TableCell className="tabular-nums">{idx + 1}</TableCell>
                <TableCell>{s.city}</TableCell>
                <TableCell className="font-mono text-xs">{s.postalCode}</TableCell>
                <TableCell>{s.addressLine1}</TableCell>
              </TableRow>
            ))}
            {routeQ.data && routeQ.data.stops.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-sm text-muted-foreground">
                  No scheduled deliveries for that day.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Restaurant table-turn forecast</h2>
        {tableQ.error && isApiError(tableQ.error) ? <InlineError error={tableQ.error} className="mt-3" /> : null}
        <p className="mt-2 text-sm text-muted-foreground">
          Assumed avg dining minutes: {tableQ.data?.assumedMinutes ?? "—"}
        </p>
        <Table className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Table</TableHead>
              <TableHead>Predicted free at</TableHead>
              <TableHead className="text-right">Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(tableQ.data?.items ?? []).map((t: any) => (
              <TableRow key={t.tableId}>
                <TableCell>{t.label}</TableCell>
                <TableCell className="font-mono text-xs">{t.predictedFreeAt}</TableCell>
                <TableCell className="text-right tabular-nums">{t.confidence}</TableCell>
              </TableRow>
            ))}
            {tableQ.data && tableQ.data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-sm text-muted-foreground">
                  No occupied tables right now.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
        <p className="mt-3 text-xs text-muted-foreground">
          QSR prep-time and stylist matching APIs are available; we can wire them into the QSR and Salon screens next.
        </p>
      </div>

      <div className="text-xs text-muted-foreground">
        Tip: you can link this into your workflows from <Link className="underline" href="/ai-insights">AI insights</Link>.
      </div>
    </div>
  );
}

