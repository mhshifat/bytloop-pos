"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Skeleton } from "@/components/shared/ui/skeleton";
import { type CohortCell, getCohortRetention } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";

export function CohortHeatmap() {
  const [monthsBack, setMonthsBack] = useState<number>(12);

  const { data, isLoading, error } = useQuery({
    queryKey: ["ai", "cohort-retention", monthsBack],
    queryFn: () => getCohortRetention(monthsBack),
  });

  const { cohorts, maxOffset, cellMap } = useMemo(() => {
    const cells = data?.cells ?? [];
    const cohortSet = new Set<string>();
    let max = 0;
    const map = new Map<string, CohortCell>();
    for (const c of cells) {
      cohortSet.add(c.cohortMonth);
      if (c.monthsSinceAcquisition > max) max = c.monthsSinceAcquisition;
      map.set(`${c.cohortMonth}|${c.monthsSinceAcquisition}`, c);
    }
    const sorted = Array.from(cohortSet).sort((a, b) => b.localeCompare(a));
    return { cohorts: sorted, maxOffset: max, cellMap: map };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-3 text-sm font-medium text-muted-foreground">
          <span>Cohort retention</span>
          <div className="flex items-end gap-2">
            <Label htmlFor="cohort-months-back" className="text-xs">
              Months back
            </Label>
            <Input
              id="cohort-months-back"
              type="number"
              min={3}
              max={36}
              value={monthsBack}
              onChange={(e) => {
                const n = Number(e.target.value);
                if (Number.isFinite(n)) {
                  setMonthsBack(Math.min(36, Math.max(3, Math.floor(n))));
                }
              }}
              className="h-8 w-24"
            />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : cohorts.length === 0 ? (
          <EmptyState
            title="No cohort data yet"
            description="Cohorts form as customers place their first order."
          />
        ) : (
          <>
            {data?.insight ? (
              <div className="flex items-start gap-2 rounded-md border border-border bg-muted/30 p-3 text-sm">
                <Sparkles
                  size={14}
                  className="mt-0.5 shrink-0 text-primary"
                  aria-hidden="true"
                />
                <p className="text-muted-foreground">{data.insight}</p>
              </div>
            ) : null}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr>
                    <th className="sticky left-0 bg-card px-2 py-1.5 text-left font-medium text-muted-foreground">
                      Cohort
                    </th>
                    {Array.from({ length: maxOffset + 1 }).map((_, i) => (
                      <th
                        key={i}
                        className="px-2 py-1.5 text-center font-medium text-muted-foreground"
                      >
                        M{i}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cohorts.map((cohort) => (
                    <tr key={cohort}>
                      <td className="sticky left-0 bg-card px-2 py-1.5 font-medium tabular-nums">
                        {cohort}
                      </td>
                      {Array.from({ length: maxOffset + 1 }).map((_, i) => {
                        const cell = cellMap.get(`${cohort}|${i}`);
                        return (
                          <td
                            key={i}
                            className="px-1 py-0.5 text-center tabular-nums"
                          >
                            {cell ? (
                              <span
                                className={`block rounded px-2 py-1 ${tintFor(cell.retentionPct)}`}
                                title={`${cell.activeCustomers} active`}
                              >
                                {Math.round(cell.retentionPct)}%
                              </span>
                            ) : (
                              <span className="block px-2 py-1 text-muted-foreground/40">
                                —
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function tintFor(pct: number): string {
  // 0% = red, 50% = amber, 100% = green (via Tailwind opacity on base hues).
  if (pct >= 80) return "bg-emerald-500/70 text-emerald-950";
  if (pct >= 60) return "bg-emerald-500/50 text-emerald-950";
  if (pct >= 40) return "bg-amber-500/50 text-amber-950";
  if (pct >= 20) return "bg-amber-500/30 text-amber-100";
  if (pct > 0) return "bg-red-500/40 text-red-100";
  return "bg-red-500/60 text-red-50";
}
