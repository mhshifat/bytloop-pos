"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock3, DollarSign, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { closeShift, currentShift, openShift } from "@/lib/api/shifts";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { useCurrency } from "@/lib/hooks/use-currency";

export function ShiftIndicator() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: shift, isLoading } = useQuery({
    queryKey: ["shifts", "current"],
    queryFn: () => currentShift(),
    // Poll every 30s so another device closing the shift is reflected here.
    refetchInterval: 30_000,
  });

  const openMutation = useMutation({
    mutationFn: () => openShift(amount),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["shifts"] });
      setOpen(false);
      setAmount(0);
      setServerError(null);
      toast.success("Shift opened.");
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closeShift(amount),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["shifts"] });
      setOpen(false);
      setAmount(0);
      setServerError(null);
      const variance = result.varianceCents ?? 0;
      if (variance === 0) {
        toast.success("Shift closed. Drawer balanced.");
      } else if (variance > 0) {
        toast.success(`Shift closed. Over by ${formatMoney(variance)}.`);
      } else {
        toast.warning(`Shift closed. Short by ${formatMoney(Math.abs(variance))}.`);
      }
    },
  });

  if (isLoading) return null;

  const active = shift !== null && shift !== undefined;

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-1 text-xs hover:bg-white/5"
        >
          {active ? (
            <>
              <Clock3 size={12} aria-hidden="true" />
              <span>Shift open</span>
              <span className="text-muted-foreground">
                · {formatMoney(shift.openingFloatCents)}
              </span>
            </>
          ) : (
            <>
              <LockKeyhole size={12} aria-hidden="true" />
              <span>No shift</span>
            </>
          )}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">
            {active ? "Close shift" : "Open shift"}
          </Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            {active
              ? "Count the cash in the drawer and enter the total to close."
              : "Enter the cash float you're starting with."}
          </Dialog.Description>

          <div className="mt-4 space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="shift-amount">
                {active ? "Counted cash (cents)" : "Opening float (cents)"}
              </Label>
              <Input
                id="shift-amount"
                type="number"
                min={0}
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                {formatMoney(amount)}
              </p>
            </div>

            {serverError ? <InlineError error={serverError} /> : null}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() =>
                  active ? closeMutation.mutate() : openMutation.mutate()
                }
                disabled={openMutation.isPending || closeMutation.isPending}
              >
                <DollarSign size={14} />
                {active ? "Close shift" : "Open shift"}
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
