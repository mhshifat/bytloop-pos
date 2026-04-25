"use client";

import { useQuery } from "@tanstack/react-query";

import { ShowCreateForm } from "@/components/modules/cinema/show-create-form";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Card } from "@/components/shared/ui/card";
import { isApiError } from "@/lib/api/error";
import { listShows } from "@/lib/api/cinema";
import { useCurrency } from "@/lib/hooks/use-currency";

export default function CinemaPage() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["cinema", "shows"],
    queryFn: () => listShows(),
  });

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Cinema</h1>
        <p className="text-sm text-muted-foreground">Upcoming shows.</p>
      </header>

      <ShowCreateForm />

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No upcoming shows" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.map((show) => (
            <Card
              key={show.id}
              className="flex cursor-pointer flex-col gap-2 p-4 hover:border-primary/60"
              onClick={() => {
                window.location.href = `/verticals/cinema/${show.id}`;
              }}
            >
              <p className="text-base font-medium">{show.title}</p>
              <p className="text-xs text-muted-foreground">Screen {show.screen}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(show.startsAt).toLocaleString()}
              </p>
              <p className="text-sm font-semibold tabular-nums">
                {formatMoney(show.ticketPriceCents)}
              </p>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
