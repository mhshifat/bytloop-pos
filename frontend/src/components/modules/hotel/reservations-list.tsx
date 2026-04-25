"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { EntityLabel } from "@/components/shared/entity-label";
import { EmptyState } from "@/components/shared/empty-state";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { isApiError } from "@/lib/api/error";
import {
  hotelCheckIn,
  hotelCheckOut,
  listReservations,
  type ReservationStatus,
} from "@/lib/api/hotel";

import { FolioDialog } from "./folio-dialog";

const STATUS_LABELS: Record<ReservationStatus, string> = {
  booked: "Booked",
  checked_in: "Checked in",
  checked_out: "Checked out",
  cancelled: "Cancelled",
};

export function ReservationsList() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["hotel", "reservations"],
    queryFn: () => listReservations(),
  });

  const checkIn = useMutation({
    mutationFn: (id: string) => hotelCheckIn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hotel", "reservations"] });
      toast.success("Guest checked in.");
    },
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  const checkOut = useMutation({
    mutationFn: (id: string) => hotelCheckOut(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hotel", "reservations"] });
      toast.success("Guest checked out.");
    },
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.length === 0) return <EmptyState title="No reservations yet" />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Check-in</TableHead>
          <TableHead>Check-out</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((r) => (
          <TableRow key={r.id}>
            <TableCell>
              <EntityLabel id={r.customerId} entity="customer" />
            </TableCell>
            <TableCell>
              <EnumBadge value={r.status} getLabel={(s) => STATUS_LABELS[s]} />
            </TableCell>
            <TableCell>{r.checkIn}</TableCell>
            <TableCell>{r.checkOut}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <FolioDialog reservationId={r.id} />
                {r.status === "booked" ? (
                  <Button
                    size="sm"
                    onClick={() => checkIn.mutate(r.id)}
                    disabled={checkIn.isPending}
                  >
                    Check in
                  </Button>
                ) : null}
                {r.status === "checked_in" ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => checkOut.mutate(r.id)}
                    disabled={checkOut.isPending}
                  >
                    Check out
                  </Button>
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
