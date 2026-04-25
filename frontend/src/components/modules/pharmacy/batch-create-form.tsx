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
import { createBatch } from "@/lib/api/pharmacy";

export function BatchCreateForm() {
  const queryClient = useQueryClient();
  const [productId, setProductId] = useState("");
  const [batchNo, setBatchNo] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      createBatch({ productId, batchNo, expiryDate, quantity }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["pharmacy", "batches"] });
      setProductId("");
      setBatchNo("");
      setExpiryDate("");
      setQuantity(1);
      setServerError(null);
      toast.success("Batch recorded.");
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
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="batch-product">Product ID</Label>
        <Input
          id="batch-product"
          value={productId}
          onChange={(e) => setProductId(e.target.value)}
          placeholder="UUID from /products"
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="batch-no">Batch no</Label>
        <Input
          id="batch-no"
          value={batchNo}
          onChange={(e) => setBatchNo(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="batch-expiry">Expiry</Label>
        <Input
          id="batch-expiry"
          type="date"
          value={expiryDate}
          onChange={(e) => setExpiryDate(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="batch-qty">Quantity</Label>
        <Input
          id="batch-qty"
          type="number"
          min={1}
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          required
        />
      </div>
      {serverError ? (
        <div className="md:col-span-5">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-5">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Record batch"}
        </Button>
      </div>
    </form>
  );
}
