"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { generateMatrix } from "@/lib/api/apparel";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

type VariantMatrixEditorProps = {
  readonly productId: string;
};

function parseCsv(input: string): string[] {
  return Array.from(
    new Set(
      input
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
    ),
  );
}

export function VariantMatrixEditor({ productId }: VariantMatrixEditorProps) {
  const queryClient = useQueryClient();
  const [sizesInput, setSizesInput] = useState("S, M, L, XL");
  const [colorsInput, setColorsInput] = useState("BLACK, WHITE");
  const [skuPrefix, setSkuPrefix] = useState("SKU");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const sizes = parseCsv(sizesInput);
  const colors = parseCsv(colorsInput);

  const mutation = useMutation({
    mutationFn: () =>
      generateMatrix({ productId, sizes, colors, skuPrefix: skuPrefix.toUpperCase() }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async (rows) => {
      setServerError(null);
      toast.success(`Created ${rows.length} variants.`);
      await queryClient.invalidateQueries({ queryKey: ["apparel", "variants", productId] });
    },
  });

  return (
    <div className="space-y-4 rounded-lg border border-border bg-surface p-4">
      <header>
        <h3 className="text-base font-medium">Generate size × color matrix</h3>
        <p className="text-sm text-muted-foreground">
          We&apos;ll create one SKU per combination.
        </p>
      </header>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="matrix-sizes">Sizes (comma-separated)</Label>
          <Input
            id="matrix-sizes"
            value={sizesInput}
            onChange={(e) => setSizesInput(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="matrix-colors">Colors (comma-separated)</Label>
          <Input
            id="matrix-colors"
            value={colorsInput}
            onChange={(e) => setColorsInput(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="matrix-prefix">SKU prefix</Label>
          <Input
            id="matrix-prefix"
            value={skuPrefix}
            onChange={(e) => setSkuPrefix(e.target.value)}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Will create {sizes.length * colors.length} variants.
      </p>

      {serverError ? <InlineError error={serverError} /> : null}

      <Button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || sizes.length === 0 || colors.length === 0}
      >
        {mutation.isPending ? "Generating…" : "Generate variants"}
      </Button>
    </div>
  );
}
