"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { addRoom } from "@/lib/api/hotel";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

export function RoomCreateForm() {
  const queryClient = useQueryClient();
  const [number, setNumber] = useState("");
  const [category, setCategory] = useState("standard");
  const [rate, setRate] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () => addRoom({ number, category, nightlyRateCents: rate }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hotel", "rooms"] });
      setNumber("");
      setCategory("standard");
      setRate(0);
      setServerError(null);
      toast.success("Room added.");
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
      <div className="space-y-1.5">
        <Label htmlFor="room-number">Number</Label>
        <Input
          id="room-number"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="room-category">Category</Label>
        <Input
          id="room-category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="room-rate">Nightly rate (cents)</Label>
        <Input
          id="room-rate"
          type="number"
          min={0}
          value={rate}
          onChange={(e) => setRate(Number(e.target.value))}
          required
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" disabled={mutation.isPending || !number}>
          Add room
        </Button>
      </div>
      {serverError ? (
        <div className="md:col-span-4">
          <InlineError error={serverError} />
        </div>
      ) : null}
    </form>
  );
}
