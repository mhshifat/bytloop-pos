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
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { listAssets, reserveAsset } from "@/lib/api/rental";

export function ContractCreateForm() {
  const queryClient = useQueryClient();
  const [assetId, setAssetId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [depositCents, setDepositCents] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: assets } = useQuery({
    queryKey: ["rental", "assets"],
    queryFn: () => listAssets(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      reserveAsset({
        assetId,
        customerId,
        startsAt: new Date(startsAt).toISOString(),
        endsAt: new Date(endsAt).toISOString(),
        depositCents,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["rental"] });
      setAssetId("");
      setCustomerId("");
      setStartsAt("");
      setEndsAt("");
      setDepositCents(0);
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
        <Label htmlFor="contract-asset">Asset</Label>
        <Select value={assetId} onValueChange={setAssetId}>
          <SelectTrigger id="contract-asset">
            <SelectValue placeholder="Pick asset" />
          </SelectTrigger>
          <SelectContent>
            {assets?.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.code} — {a.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="contract-customer">Customer ID</Label>
        <Input
          id="contract-customer"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-start">Starts</Label>
        <Input
          id="contract-start"
          type="datetime-local"
          value={startsAt}
          onChange={(e) => setStartsAt(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-end">Ends</Label>
        <Input
          id="contract-end"
          type="datetime-local"
          value={endsAt}
          onChange={(e) => setEndsAt(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-deposit">Deposit (cents)</Label>
        <Input
          id="contract-deposit"
          type="number"
          min={0}
          value={depositCents}
          onChange={(e) => setDepositCents(Number(e.target.value))}
        />
      </div>
      {serverError ? (
        <div className="md:col-span-5">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-5">
        <Button type="submit" disabled={mutation.isPending}>
          Reserve asset
        </Button>
      </div>
    </form>
  );
}
