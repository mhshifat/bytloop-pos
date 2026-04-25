"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeftRight } from "lucide-react";
import { useMemo, useState } from "react";
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
import { transferStock } from "@/lib/api/catalog";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { listLocations } from "@/lib/api/locations";

type TransferStockDialogProps = {
  readonly productId: string;
  readonly productName: string;
  readonly sourceLocationId: string;
  readonly currentQuantity: number;
};

export function TransferStockDialog({
  productId,
  productName,
  sourceLocationId,
  currentQuantity,
}: TransferStockDialogProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [destinationLocationId, setDestinationLocationId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: locations } = useQuery({
    queryKey: ["locations"],
    queryFn: () => listLocations(),
    enabled: open,
  });

  const destinations = useMemo(
    () => (locations ?? []).filter((l) => l.id !== sourceLocationId),
    [locations, sourceLocationId],
  );

  const canSubmit =
    Boolean(destinationLocationId) &&
    quantity > 0 &&
    quantity <= currentQuantity;

  const mutation = useMutation({
    mutationFn: () =>
      transferStock({
        productId,
        sourceLocationId,
        destinationLocationId,
        quantity,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["inventory", "levels"] });
      setOpen(false);
      setDestinationLocationId("");
      setQuantity(1);
      setServerError(null);
      toast.success("Stock transferred.");
    },
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button
          variant="outline"
          size="icon-sm"
          aria-label="Transfer stock"
          disabled={currentQuantity <= 0}
        >
          <ArrowLeftRight size={14} />
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Transfer stock</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            {productName} · {currentQuantity} available at source
          </Dialog.Description>

          <div className="mt-4 space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="transfer-destination">Destination location</Label>
              <Select
                value={destinationLocationId}
                onValueChange={setDestinationLocationId}
              >
                <SelectTrigger id="transfer-destination">
                  <SelectValue
                    placeholder={
                      destinations.length === 0
                        ? "No other locations available"
                        : "Pick a destination"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {destinations.map((l) => (
                    <SelectItem key={l.id} value={l.id}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="transfer-quantity">Quantity</Label>
              <Input
                id="transfer-quantity"
                type="number"
                min={1}
                max={currentQuantity}
                value={quantity}
                onChange={(e) =>
                  setQuantity(
                    Math.max(1, Math.min(currentQuantity, Number(e.target.value))),
                  )
                }
                autoFocus
              />
            </div>

            {serverError ? <InlineError error={serverError} /> : null}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => mutation.mutate()}
                disabled={!canSubmit || mutation.isPending}
              >
                {mutation.isPending ? "Transferring…" : "Transfer"}
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
