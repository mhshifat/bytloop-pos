"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { applyLoyaltyAutoTune, getLoyaltyAutoTune } from "@/lib/api/loyalty-auto-tune";
import { isApiError } from "@/lib/api/error";

export function LoyaltyAutoTuneSection() {
  const q = useQuery({ queryKey: ["p13n", "loyalty", "auto-tune"], queryFn: () => getLoyaltyAutoTune() });
  const apply = useMutation({
    mutationFn: (punchesRequired: number) => applyLoyaltyAutoTune({ punchesRequired }),
    onSuccess: async (r) => {
      if (!r.ok) toast.error(r.error ?? "Failed to apply.");
      else toast.success(`Applied: punches_required = ${r.punchesRequired} (updated ${r.updated}).`);
      await q.refetch();
    },
  });

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <h2 className="text-sm font-semibold">Auto-tune punches_required</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Uses simple retention heuristics on loyalty card completion rate.
      </p>

      {q.error && isApiError(q.error) ? <InlineError error={q.error} className="mt-3" /> : null}

      {q.data ? (
        <div className="mt-4 space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Total cards</span>
            <span className="tabular-nums">{q.data.totalCards}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Current punches_required</span>
            <span className="tabular-nums">{q.data.currentPunchesRequired}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Recommended</span>
            <span className="tabular-nums font-semibold">{q.data.recommendedPunchesRequired}</span>
          </div>
          <p className="text-xs text-muted-foreground">{q.data.reason}</p>
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              disabled={apply.isPending}
              onClick={() => apply.mutate(q.data.recommendedPunchesRequired)}
            >
              {apply.isPending ? "Applying…" : "Apply recommendation"}
            </Button>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
      )}
    </div>
  );
}

