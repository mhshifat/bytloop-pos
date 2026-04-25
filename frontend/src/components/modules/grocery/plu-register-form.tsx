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
import { registerPlu } from "@/lib/api/grocery";

export function PluRegisterForm() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [productId, setProductId] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () => registerPlu({ code, productId }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["grocery"] });
      setCode("");
      setProductId("");
      setServerError(null);
      toast.success("PLU code registered.");
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
        <Label htmlFor="plu-code">PLU (3–8 digits)</Label>
        <Input
          id="plu-code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="4011"
          required
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="plu-product">Product ID</Label>
        <Input
          id="plu-product"
          value={productId}
          onChange={(e) => setProductId(e.target.value)}
          placeholder="UUID from /products"
          required
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" disabled={mutation.isPending || !code || !productId}>
          Register PLU
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
