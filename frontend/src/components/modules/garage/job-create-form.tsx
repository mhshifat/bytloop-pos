"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Label } from "@/components/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { Textarea } from "@/components/shared/ui/textarea";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { listVehicles, openJob } from "@/lib/api/garage";

export function JobCreateForm() {
  const queryClient = useQueryClient();
  const [vehicleId, setVehicleId] = useState("");
  const [description, setDescription] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: vehicles } = useQuery({
    queryKey: ["garage", "vehicles"],
    queryFn: () => listVehicles(),
  });

  const mutation = useMutation({
    mutationFn: () => openJob({ vehicleId, description }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["garage", "jobs"] });
      setVehicleId("");
      setDescription("");
      setServerError(null);
      toast.success("Job opened.");
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
        <Label htmlFor="job-vehicle">Vehicle</Label>
        <Select value={vehicleId} onValueChange={setVehicleId}>
          <SelectTrigger id="job-vehicle">
            <SelectValue placeholder="Pick vehicle" />
          </SelectTrigger>
          <SelectContent>
            {vehicles?.map((v) => (
              <SelectItem key={v.id} value={v.id}>
                {v.plate} — {v.make} {v.model}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5 md:col-span-3">
        <Label htmlFor="job-description">Description</Label>
        <Textarea
          id="job-description"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      {serverError ? (
        <div className="md:col-span-4">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-4">
        <Button type="submit" disabled={mutation.isPending || !vehicleId}>
          Open job
        </Button>
      </div>
    </form>
  );
}
