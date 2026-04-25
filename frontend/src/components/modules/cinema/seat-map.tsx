"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { cn } from "@/lib/utils/cn";
import { holdSeat, listSeats, releaseSeat, type Seat, sellSeat } from "@/lib/api/cinema";
import { isApiError } from "@/lib/api/error";
import { seatStatusLabel } from "@/lib/enums/seat-status";

type SeatMapProps = {
  readonly showId: string;
};

/**
 * Generate or reuse a per-browser session identifier so holds can be
 * converted / released later from the same tab. Deliberately not tied to
 * the logged-in user — a single cashier may juggle multiple browser
 * windows, each building its own cart.
 */
function getSessionHoldId(): string {
  if (typeof window === "undefined") return "server";
  const KEY = "cinema-hold-id";
  let id = window.sessionStorage.getItem(KEY);
  if (!id) {
    id = `s-${Math.random().toString(36).slice(2, 10)}`;
    window.sessionStorage.setItem(KEY, id);
  }
  return id;
}

export function SeatMap({ showId }: SeatMapProps) {
  const queryClient = useQueryClient();
  const heldBy = useMemo(() => getSessionHoldId(), []);

  const { data, isLoading, error } = useQuery({
    queryKey: ["cinema", "seats", showId],
    queryFn: () => listSeats(showId),
    // Poll so other tabs' holds appear without manual refresh; the backend
    // also auto-expires lapsed holds on list.
    refetchInterval: 15_000,
  });

  const hold = useMutation({
    mutationFn: (seatId: string) => holdSeat(seatId, { heldBy }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cinema", "seats", showId] }),
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  const release = useMutation({
    mutationFn: (seatId: string) => releaseSeat(seatId, heldBy),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cinema", "seats", showId] }),
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  const sell = useMutation({
    mutationFn: (seatId: string) => sellSeat(seatId, { heldBy }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cinema", "seats", showId] }),
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.length === 0) {
    return <EmptyState title="No seats configured" description="Add seats when creating the show." />;
  }

  const rows = groupByRow(data);

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-white/5 p-6">
        <div className="mx-auto mb-6 w-3/4 rounded-full border-b-4 border-border text-center text-xs uppercase tracking-widest text-muted-foreground">
          Screen
        </div>
        <div className="space-y-2">
          {rows.map(([row, seats]) => (
            <div key={row} className="flex items-center justify-center gap-1">
              <span className="mr-3 w-6 text-center font-mono text-xs text-muted-foreground">
                {row}
              </span>
              {seats.map((seat) => (
                <button
                  key={seat.id}
                  type="button"
                  onClick={(e) => {
                    if (seat.status === "sold") return;
                    if (seat.status === "available") {
                      hold.mutate(seat.id);
                    } else if (seat.status === "held") {
                      // Shift-click releases a hold; plain click converts to sold.
                      if (e.shiftKey) release.mutate(seat.id);
                      else sell.mutate(seat.id);
                    }
                  }}
                  title={`${seat.label} · ${seatStatusLabel(seat.status)}${
                    seat.status === "held" ? " (click: sell, shift-click: release)" : ""
                  }`}
                  className={cn(
                    "h-9 w-9 rounded-md border border-border text-[11px] font-mono transition-colors",
                    seat.status === "available" && "border-border bg-surface hover:bg-white/10",
                    seat.status === "held" && "border-amber-500/50 bg-amber-500/10 text-amber-200 hover:bg-amber-500/20",
                    seat.status === "sold" && "cursor-not-allowed border-red-500/40 bg-red-500/20 text-red-200 opacity-70",
                  )}
                  disabled={seat.status === "sold"}
                >
                  {seat.label.replace(/^[A-Z]+/, "")}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex justify-center gap-4 text-xs text-muted-foreground">
        <LegendSwatch label="Available" className="border-border bg-surface" />
        <LegendSwatch label="Held" className="border-amber-500/50 bg-amber-500/10" />
        <LegendSwatch label="Sold" className="border-red-500/40 bg-red-500/20" />
      </div>
    </div>
  );
}

function groupByRow(seats: readonly Seat[]): [string, Seat[]][] {
  const groups = new Map<string, Seat[]>();
  for (const seat of seats) {
    const row = seat.label.match(/^[A-Z]+/)?.[0] ?? seat.label;
    const bucket = groups.get(row) ?? [];
    bucket.push(seat);
    groups.set(row, bucket);
  }
  return Array.from(groups.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([row, items]): [string, Seat[]] => [row, items.sort((a, b) => a.label.localeCompare(b.label))]);
}

function LegendSwatch({
  label,
  className,
}: {
  readonly label: string;
  readonly className: string;
}) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("inline-block h-3 w-3 rounded border", className)} />
      {label}
    </span>
  );
}
