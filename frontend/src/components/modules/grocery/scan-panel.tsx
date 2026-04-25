"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { EntityLabel } from "@/components/shared/entity-label";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { scanInput, type ScanResult } from "@/lib/api/grocery";
import { useCurrency } from "@/lib/hooks/use-currency";

export function ScanPanel() {
  const { formatMoney } = useCurrency();
  const [code, setCode] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const scan = useMutation({
    mutationFn: (input: string) => scanInput(input),
    onError: (err) => {
      setResult(null);
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: (data) => {
      setServerError(null);
      setResult(data);
    },
  });

  return (
    <form
      className="space-y-4 rounded-lg border border-border bg-surface p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (code.trim()) scan.mutate(code.trim());
      }}
    >
      <header>
        <h3 className="text-base font-medium">Register scan</h3>
        <p className="text-sm text-muted-foreground">
          Try a 4-digit PLU (e.g. produce code <code>4011</code>) or a
          price-embedded EAN-13 from a deli scale (starts with <code>2</code>).
        </p>
      </header>
      <div className="flex items-end gap-2">
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="scan-input">Input</Label>
          <Input
            id="scan-input"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="4011 or 2004011012500"
            autoFocus
          />
        </div>
        <Button type="submit" disabled={scan.isPending || code.trim().length === 0}>
          {scan.isPending ? "Scanning…" : "Scan"}
        </Button>
      </div>

      {serverError ? <InlineError error={serverError} /> : null}

      {result ? (
        <div className="rounded-md border border-border p-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Product</span>
            <EntityLabel id={result.productId} entity="product" />
          </div>
          <div className="mt-1 flex justify-between">
            <span className="text-muted-foreground">Line total</span>
            <span className="font-semibold tabular-nums">
              {result.lineTotalCents !== null
                ? formatMoney(result.lineTotalCents)
                : "Use configured price"}
            </span>
          </div>
        </div>
      ) : null}
    </form>
  );
}
