"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCannabisPotencyPriceMatch,
  getGymChurnNudges,
  getHotelUpsell,
  getMenuEngineering,
  getRentalDamageRisk,
  getRestaurantWaitTime,
} from "@/lib/api/ai-vertical";
import { Button } from "@/components/shared/ui/button";

function JsonCard(props: { readonly title: string; readonly data: unknown; readonly isLoading?: boolean; readonly error?: unknown }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-sm font-medium">{props.title}</p>
      {props.isLoading ? (
        <p className="mt-2 text-sm text-muted-foreground">Loading…</p>
      ) : props.error ? (
        <p className="mt-2 text-sm text-destructive">Failed to load.</p>
      ) : (
        <pre className="mt-3 max-h-88 overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(props.data, null, 2)}</pre>
      )}
    </div>
  );
}

export function VerticalInsightsPanel() {
  const menu = useQuery({
    queryKey: ["ai-vertical", "menu-engineering"],
    queryFn: () => getMenuEngineering({ days: 60 }),
  });
  const waitTime = useQuery({
    queryKey: ["ai-vertical", "restaurant-wait-time"],
    queryFn: () => getRestaurantWaitTime({}),
  });
  const cannabis = useQuery({
    queryKey: ["ai-vertical", "cannabis-match"],
    queryFn: () => getCannabisPotencyPriceMatch({ desiredThcPct: 18, desiredCbdPct: 0, limit: 5 }),
  });
  const hotel = useQuery({
    queryKey: ["ai-vertical", "hotel-upsell"],
    queryFn: () => getHotelUpsell({ limit: 25 }),
  });
  const rental = useQuery({
    queryKey: ["ai-vertical", "rental-risk"],
    queryFn: () => getRentalDamageRisk({ limit: 50 }),
  });
  const gym = useQuery({
    queryKey: ["ai-vertical", "gym-churn"],
    queryFn: () => getGymChurnNudges({ days: 14, limit: 50 }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            void menu.refetch();
            void waitTime.refetch();
            void cannabis.refetch();
            void hotel.refetch();
            void rental.refetch();
            void gym.refetch();
          }}
        >
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <JsonCard title="Menu engineering (60d)" data={menu.data} isLoading={menu.isLoading} error={menu.error} />
        <JsonCard title="Restaurant wait-time ETA" data={waitTime.data} isLoading={waitTime.isLoading} error={waitTime.error} />
        <JsonCard title="Cannabis potency-to-price match" data={cannabis.data} isLoading={cannabis.isLoading} error={cannabis.error} />
        <JsonCard title="Hotel upsell prediction" data={hotel.data} isLoading={hotel.isLoading} error={hotel.error} />
        <JsonCard title="Rental damage risk scoring" data={rental.data} isLoading={rental.isLoading} error={rental.error} />
        <JsonCard title="Gym churn-prevention nudges" data={gym.data} isLoading={gym.isLoading} error={gym.error} />
      </div>
    </div>
  );
}

