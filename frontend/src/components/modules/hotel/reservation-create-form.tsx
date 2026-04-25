"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { reserve, listRooms } from "@/lib/api/hotel";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

export function ReservationCreateForm() {
  const queryClient = useQueryClient();
  const [roomId, setRoomId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: rooms } = useQuery({
    queryKey: ["hotel", "rooms"],
    queryFn: () => listRooms(),
  });

  const mutation = useMutation({
    mutationFn: () => reserve({ roomId, customerId, checkIn, checkOut }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hotel"] });
      setRoomId("");
      setCustomerId("");
      setCheckIn("");
      setCheckOut("");
      setServerError(null);
      toast.success("Reservation created.");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-5"
    >
      <div className="space-y-1.5">
        <Label htmlFor="reservation-room">Room</Label>
        <Select value={roomId} onValueChange={setRoomId}>
          <SelectTrigger id="reservation-room">
            <SelectValue placeholder="Select room" />
          </SelectTrigger>
          <SelectContent>
            {rooms?.map((r) => (
              <SelectItem key={r.id} value={r.id}>
                Room {r.number}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="reservation-customer">Customer ID</Label>
        <Input
          id="reservation-customer"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="UUID from /customers"
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="reservation-in">Check-in</Label>
        <Input
          id="reservation-in"
          type="date"
          value={checkIn}
          onChange={(e) => setCheckIn(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="reservation-out">Check-out</Label>
        <Input
          id="reservation-out"
          type="date"
          value={checkOut}
          onChange={(e) => setCheckOut(e.target.value)}
          required
        />
      </div>
      {serverError ? (
        <div className="md:col-span-5">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-5">
        <Button
          type="submit"
          disabled={mutation.isPending || !roomId || !customerId || !checkIn || !checkOut}
        >
          Reserve
        </Button>
      </div>
    </form>
  );
}
