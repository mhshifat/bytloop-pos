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
import { addAsset } from "@/lib/api/rental";

export function AssetCreateForm() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [label, setLabel] = useState("");
  const [hourly, setHourly] = useState(0);
  const [daily, setDaily] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      addAsset({
        code,
        label,
        hourlyRateCents: hourly,
        dailyRateCents: daily,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["rental", "assets"] });
      setCode("");
      setLabel("");
      setHourly(0);
      setDaily(0);
      setServerError(null);
      toast.success("Asset added.");
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
        <Label htmlFor="asset-code">Code</Label>
        <Input
          id="asset-code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="asset-label">Label</Label>
        <Input
          id="asset-label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="asset-hourly">Hourly (cents)</Label>
        <Input
          id="asset-hourly"
          type="number"
          min={0}
          value={hourly}
          onChange={(e) => setHourly(Number(e.target.value))}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="asset-daily">Daily (cents)</Label>
        <Input
          id="asset-daily"
          type="number"
          min={0}
          value={daily}
          onChange={(e) => setDaily(Number(e.target.value))}
        />
      </div>
      {serverError ? (
        <div className="md:col-span-5">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-5">
        <Button type="submit" disabled={mutation.isPending || !code || !label}>
          Add asset
        </Button>
      </div>
    </form>
  );
}
