"use client";

import { useQuery } from "@tanstack/react-query";

import { ReservationCreateForm } from "@/components/modules/hotel/reservation-create-form";
import { ReservationsList } from "@/components/modules/hotel/reservations-list";
import { RoomCreateForm } from "@/components/modules/hotel/room-create-form";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Card } from "@/components/shared/ui/card";
import { isApiError } from "@/lib/api/error";
import { listRooms } from "@/lib/api/hotel";
import { useCurrency } from "@/lib/hooks/use-currency";

export default function HotelPage() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["hotel", "rooms"],
    queryFn: () => listRooms(),
  });

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Hotel</h1>
        <p className="text-sm text-muted-foreground">Rooms &amp; reservations.</p>
      </header>

      <RoomCreateForm />
      <ReservationCreateForm />
      <ReservationsList />

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No rooms configured" />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {data.map((room) => (
            <Card key={room.id} className="flex flex-col gap-2 p-4">
              <p className="text-sm font-medium">Room {room.number}</p>
              <p className="text-xs text-muted-foreground">{room.category}</p>
              <p className="text-base font-semibold tabular-nums">
                {formatMoney(room.nightlyRateCents)}
                <span className="text-xs font-normal text-muted-foreground">/night</span>
              </p>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
