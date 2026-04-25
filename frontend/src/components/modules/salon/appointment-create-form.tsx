"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { bookAppointment } from "@/lib/api/salon";

export function AppointmentCreateForm() {
  const queryClient = useQueryClient();
  const [customerId, setCustomerId] = useState("");
  const [service, setService] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      bookAppointment({
        customerId,
        serviceName: service,
        startsAt: new Date(startsAt).toISOString(),
        endsAt: new Date(endsAt).toISOString(),
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["salon", "appointments"] });
      setCustomerId("");
      setService("");
      setStartsAt("");
      setEndsAt("");
      setServerError(null);
      toast.success("Appointment booked.");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-4"
    >
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="appt-customer">Customer ID</Label>
        <Input
          id="appt-customer"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="UUID from /customers"
          required
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="appt-service">Service</Label>
        <Input
          id="appt-service"
          value={service}
          onChange={(e) => setService(e.target.value)}
          placeholder="Haircut"
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="appt-start">Starts</Label>
        <Input
          id="appt-start"
          type="datetime-local"
          value={startsAt}
          onChange={(e) => setStartsAt(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="appt-end">Ends</Label>
        <Input
          id="appt-end"
          type="datetime-local"
          value={endsAt}
          onChange={(e) => setEndsAt(e.target.value)}
          required
        />
      </div>
      {serverError ? (
        <div className="md:col-span-4">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-4">
        <Button type="submit" disabled={mutation.isPending}>
          Book appointment
        </Button>
      </div>
    </form>
  );
}
