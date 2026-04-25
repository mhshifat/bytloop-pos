"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Receipt } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { getFolio, postFolioCharge } from "@/lib/api/hotel";
import { useCurrency } from "@/lib/hooks/use-currency";

type FolioDialogProps = {
  readonly reservationId: string;
};

export function FolioDialog({ reservationId }: FolioDialogProps) {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: folio } = useQuery({
    queryKey: ["hotel", "folio", reservationId],
    queryFn: () => getFolio(reservationId),
    enabled: open,
  });

  const post = useMutation({
    mutationFn: () =>
      postFolioCharge(reservationId, { description, amountCents: amount }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["hotel", "folio", reservationId],
      });
      setDescription("");
      setAmount(0);
      setServerError(null);
      toast.success("Charge posted.");
    },
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button size="sm" variant="outline">
          <Receipt size={14} /> Folio
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Folio</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Room total plus posted incidentals.
          </Dialog.Description>

          {folio ? (
            <div className="mt-4 space-y-1.5 rounded-md border border-border p-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Room × {folio.nights} nights</span>
                <span className="tabular-nums">
                  {formatMoney(folio.roomTotalCents)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Incidentals</span>
                <span className="tabular-nums">
                  {formatMoney(folio.incidentalsCents)}
                </span>
              </div>
              <div className="flex justify-between border-t border-border pt-1.5 font-semibold">
                <span>Total</span>
                <span className="tabular-nums">{formatMoney(folio.totalCents)}</span>
              </div>
            </div>
          ) : null}

          <form
            className="mt-4 grid gap-3 md:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              post.mutate();
            }}
          >
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="folio-desc">Description</Label>
              <Input
                id="folio-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Room service, laundry…"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="folio-amt">Amount (cents)</Label>
              <Input
                id="folio-amt"
                type="number"
                min={0}
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
              />
            </div>
            <div className="md:col-span-3">
              <Button
                type="submit"
                disabled={post.isPending || !description || amount <= 0}
              >
                {post.isPending ? "Posting…" : "Post charge"}
              </Button>
            </div>
            {serverError ? (
              <div className="md:col-span-3">
                <InlineError error={serverError} />
              </div>
            ) : null}
          </form>

          {folio && folio.charges.length > 0 ? (
            <div className="mt-4 max-h-56 overflow-y-auto">
              <h4 className="mb-2 text-sm font-medium">Posted charges</h4>
              <ul className="space-y-1.5 text-sm">
                {folio.charges.map((c) => (
                  <li key={c.id} className="flex justify-between">
                    <span>{c.description}</span>
                    <span className="tabular-nums">
                      {formatMoney(c.amountCents)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
