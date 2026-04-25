"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChefHat, Clock } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { connectWs } from "@/lib/realtime/ws-client";

type KdsEvent = { readonly id: string; readonly event: string; readonly status?: string };

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card } from "@/components/shared/ui/card";
import { isApiError } from "@/lib/api/error";
import { kdsQueue, type KdsStation, type KotStatus, type KotTicket, updateKotStatus } from "@/lib/api/restaurant";

const STATIONS: readonly { readonly value: KdsStation; readonly label: string }[] = [
  { value: "kitchen", label: "Kitchen" },
  { value: "bar", label: "Bar" },
  { value: "dessert", label: "Dessert" },
  { value: "expo", label: "Expo" },
];

const NEXT_STATUS: Record<KotStatus, KotStatus | null> = {
  new: "preparing",
  preparing: "ready",
  ready: "served",
  served: null,
  cancelled: null,
};

function StatusLabel({ status }: { readonly status: KotStatus }) {
  // Avoid raw enum rendering per docs/PLAN.md §13 — map to friendly label.
  const map: Record<KotStatus, string> = {
    new: "New",
    preparing: "Preparing",
    ready: "Ready",
    served: "Served",
    cancelled: "Cancelled",
  };
  return <span className="text-xs uppercase tracking-wide">{map[status]}</span>;
}

function elapsedLabel(firedAt: string): string {
  const delta = Date.now() - new Date(firedAt).getTime();
  const minutes = Math.floor(delta / 60000);
  if (minutes < 1) return "Just now";
  return `${minutes}m`;
}

export function KdsBoard() {
  const [station, setStation] = useState<KdsStation>("kitchen");
  const queryClient = useQueryClient();

  const { data: me } = useQuery({
    queryKey: ["auth", "me-lite"],
    // Cheap tenant probe via the /config endpoint lookup isn't enough —
    // we need the authed tenant. The dashboard already fetches /auth/me;
    // here we lazy-fetch and cache.
    queryFn: async () => {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/auth/me`,
        { credentials: "include" },
      );
      if (!res.ok) return null;
      return (await res.json()) as { readonly tenantId: string };
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["kds", station],
    queryFn: () => kdsQueue(station),
    // Poll is the fallback; WebSocket invalidates the query on push. Slow
    // interval when WS is connected, faster when it isn't — the ws-client
    // handles reconnect/backoff internally.
    refetchInterval: 30_000,
  });

  useEffect(() => {
    if (!me?.tenantId) return;
    const client = connectWs<KdsEvent>(
      `/ws/restaurant/kds?tenant=${me.tenantId}&station=${station}`,
      () => {
        void queryClient.invalidateQueries({ queryKey: ["kds", station] });
      },
    );
    return () => client.close();
  }, [me?.tenantId, station, queryClient]);

  const mutation = useMutation({
    mutationFn: (args: { readonly id: string; readonly status: KotStatus }) =>
      updateKotStatus(args.id, args.status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kds", station] }),
  });

  const tickets = useMemo(() => data ?? [], [data]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {STATIONS.map((s) => (
          <Button
            key={s.value}
            variant={s.value === station ? "default" : "outline"}
            size="sm"
            onClick={() => setStation(s.value)}
          >
            {s.label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard /> <SkeletonCard /> <SkeletonCard />
        </div>
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : tickets.length === 0 ? (
        <EmptyState
          icon={ChefHat}
          title="No active tickets"
          description="Fired KOTs will appear here in real time."
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tickets.map((ticket) => {
            const next = NEXT_STATUS[ticket.status];
            return <TicketCard key={ticket.id} ticket={ticket} nextStatus={next} onAdvance={mutation.mutate} />;
          })}
        </div>
      )}
    </div>
  );
}

function TicketCard({
  ticket,
  nextStatus,
  onAdvance,
}: {
  readonly ticket: KotTicket;
  readonly nextStatus: KotStatus | null;
  readonly onAdvance: (args: { id: string; status: KotStatus }) => void;
}) {
  return (
    <Card className="flex flex-col gap-3 p-4">
      <header className="flex items-center justify-between text-sm">
        <span className="font-mono font-semibold">#{ticket.number}</span>
        <StatusLabel status={ticket.status} />
      </header>
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <Clock size={12} aria-hidden="true" />
        {elapsedLabel(ticket.firedAt)}
      </div>
      {nextStatus ? (
        <Button
          size="sm"
          className="w-full"
          onClick={() => onAdvance({ id: ticket.id, status: nextStatus })}
        >
          Mark {nextStatus === "preparing" ? "preparing" : nextStatus === "ready" ? "ready" : "served"}
        </Button>
      ) : null}
    </Card>
  );
}
