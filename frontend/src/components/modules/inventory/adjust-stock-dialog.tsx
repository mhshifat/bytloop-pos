"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PackagePlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { adjustStock } from "@/lib/api/catalog";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

type AdjustStockDialogProps = {
  readonly productId: string;
  readonly productName: string;
  readonly currentQuantity: number;
};

export function AdjustStockDialog({
  productId,
  productName,
  currentQuantity,
}: AdjustStockDialogProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [delta, setDelta] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () => adjustStock({ productId, delta }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["inventory", "levels"] });
      setOpen(false);
      setDelta(0);
      setServerError(null);
      toast.success("Stock adjusted.");
    },
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="outline" size="icon-sm" aria-label="Adjust stock">
          <PackagePlus size={14} />
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Adjust stock</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            {productName} · currently {currentQuantity} on hand
          </Dialog.Description>

          <div className="mt-4 space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="delta">Delta (positive to receive, negative to remove)</Label>
              <Input
                id="delta"
                type="number"
                value={delta}
                onChange={(e) => setDelta(Number(e.target.value))}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                New quantity will be {currentQuantity + delta}.
              </p>
            </div>
            {serverError ? <InlineError error={serverError} /> : null}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending || delta === 0}
              >
                {mutation.isPending ? "Saving…" : "Apply adjustment"}
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
