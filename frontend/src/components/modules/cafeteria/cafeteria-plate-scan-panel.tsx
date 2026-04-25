"use client";

import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { CloudinaryUploader } from "@/components/shared/cloudinary-uploader";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { plateScan, type PlateScanResponse } from "@/lib/api/ai-cafeteria";
import { isApiError } from "@/lib/api/error";
import { useCartStore } from "@/lib/stores/cart-store";

export function CafeteriaPlateScanPanel() {
  const addLine = useCartStore((s) => s.addLine);
  const [res, setRes] = useState<PlateScanResponse | null>(null);

  const mut = useMutation({
    mutationFn: (asset: { readonly publicId: string; readonly url: string }) =>
      plateScan({ asset, maxItems: 5 }),
    onSuccess: (r) => setRes(r),
  });

  const canApply = useMemo(() => Boolean(res?.lines?.length), [res]);

  return (
    <div className="space-y-4 rounded-lg border border-border bg-surface p-4">
      <CloudinaryUploader
        purpose="cafeteria"
        label={mut.isPending ? "Scanning…" : "Upload tray photo"}
        onUploaded={(asset) => mut.mutate({ publicId: asset.publicId, url: asset.secureUrl })}
      />

      {mut.error && isApiError(mut.error) ? <InlineError error={mut.error} /> : null}

      {res ? (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Tags: <span className="text-foreground">{res.tags.join(", ")}</span>
          </p>
          <div className="rounded-md border border-border bg-background p-3">
            <p className="text-sm font-medium">Suggested items</p>
            {res.lines.length === 0 ? (
              <p className="mt-1 text-sm text-muted-foreground">No suggestions.</p>
            ) : (
              <ul className="mt-2 space-y-2 text-sm">
                {res.lines.map((l) => (
                  <li key={l.productId} className="flex items-center justify-between gap-2">
                    <span>{l.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {l.currency} {(l.unitPriceCents / 100).toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              disabled={!canApply}
              onClick={() => {
                if (!res) return;
                for (const l of res.lines) {
                  addLine({
                    productId: l.productId,
                    name: l.name,
                    unitPriceCents: l.unitPriceCents,
                    currency: l.currency,
                  }, l.quantity);
                }
                toast.success("Suggested items added to cart. Review and charge.");
              }}
            >
              Apply to cart
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

