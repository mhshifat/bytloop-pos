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
import { registerVehicle } from "@/lib/api/garage";

export function VehicleCreateForm() {
  const queryClient = useQueryClient();
  const [plate, setPlate] = useState("");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () => registerVehicle({ plate, make, model }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["garage", "vehicles"] });
      setPlate("");
      setMake("");
      setModel("");
      setServerError(null);
      toast.success("Vehicle registered.");
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
        <Label htmlFor="vehicle-plate">Plate</Label>
        <Input
          id="vehicle-plate"
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="vehicle-make">Make</Label>
        <Input
          id="vehicle-make"
          value={make}
          onChange={(e) => setMake(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="vehicle-model">Model</Label>
        <Input
          id="vehicle-model"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          required
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" disabled={mutation.isPending || !plate || !make}>
          Register vehicle
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
