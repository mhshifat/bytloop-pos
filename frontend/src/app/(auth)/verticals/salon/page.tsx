"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { AppointmentCreateForm } from "@/components/modules/salon/appointment-create-form";
import { ServicesEditor } from "@/components/modules/salon/services-editor";
import { EmptyState } from "@/components/shared/empty-state";
import { EntityLabel } from "@/components/shared/entity-label";
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
  type AppointmentStatus,
  checkInAppointment,
  listAppointments,
} from "@/lib/api/salon";
import { useCartStore } from "@/lib/stores/cart-store";

const STATUS_LABELS: Record<AppointmentStatus, string> = {
  booked: "Booked",
  checked_in: "Checked in",
  completed: "Completed",
  no_show: "No show",
  cancelled: "Cancelled",
};

export default function SalonPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const addLine = useCartStore((s) => s.addLine);
  const { data, isLoading, error } = useQuery({
    queryKey: ["salon", "appointments"],
    queryFn: () => listAppointments(7),
  });

  const checkIn = useMutation({
    mutationFn: (appointmentId: string) => checkInAppointment(appointmentId),
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["salon", "appointments"] });
      if (result.productId) {
        addLine(
          {
            productId: result.productId,
            name: result.appointment.serviceName,
            unitPriceCents: 0,
            currency: "USD",
          },
          1,
        );
        toast.success("Checked in — service added to cart.");
        router.push("/pos");
      } else {
        toast.success("Checked in.");
      }
    },
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Salon</h1>
        <p className="text-sm text-muted-foreground">
          Service catalog, bookings, and check-in → POS cart.
        </p>
      </header>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Services</h2>
        <ServicesEditor />
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-medium">Next 7 days</h2>
        <AppointmentCreateForm />

        {isLoading ? (
          <SkeletonCard />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No appointments in the next 7 days" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Stylist</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>
                    <EntityLabel id={a.customerId} entity="customer" />
                  </TableCell>
                  <TableCell>{a.serviceName}</TableCell>
                  <TableCell>
                    <EntityLabel id={a.staffId} entity="user" fallback="Unassigned" />
                  </TableCell>
                  <TableCell>
                    <EnumBadge value={a.status} getLabel={(s) => STATUS_LABELS[s]} />
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-xs">
                    {new Date(a.startsAt).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {a.status === "booked" ? (
                      <Button
                        size="sm"
                        onClick={() => checkIn.mutate(a.id)}
                        disabled={checkIn.isPending}
                      >
                        Check in
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </section>
  );
}
