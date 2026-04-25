"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PackageCheck } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { processReturn, type ReturnSummary } from "@/lib/api/rental";
import { useCurrency } from "@/lib/hooks/use-currency";

type ReturnDialogProps = {
  readonly contractId: string;
};

export function ReturnDialog({ contractId }: ReturnDialogProps) {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [damageFee, setDamageFee] = useState(0);
  const [damageNotes, setDamageNotes] = useState("");
  const [summary, setSummary] = useState<ReturnSummary | null>(null);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      processReturn(contractId, {
        damageFeeCents: damageFee,
        damageNotes: damageNotes || null,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: (result) => {
      setSummary(result);
      setServerError(null);
      toast.success("Return processed.");
      queryClient.invalidateQueries({ queryKey: ["rental", "contracts"] });
    },
  });

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) {
          setDamageFee(0);
          setDamageNotes("");
          setSummary(null);
          setServerError(null);
        }
      }}
    >
      <Dialog.Trigger asChild>
        <Button size="sm" variant="outline">
          <PackageCheck size={14} /> Process return
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Process return</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Late fees computed automatically from the asset&apos;s own rates.
          </Dialog.Description>

          {summary ? (
            <div className="mt-4 space-y-1.5 rounded-md border border-border p-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Base rental</span>
                <span className="tabular-nums">
                  {formatMoney(summary.baseRentalCents)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Late fee</span>
                <span className="tabular-nums">
                  {formatMoney(summary.lateFeeCents)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Damage fee</span>
                <span className="tabular-nums">
                  {formatMoney(summary.damageFeeCents)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Deposit refund</span>
                <span className="tabular-nums">
                  {formatMoney(summary.depositRefundCents)}
                </span>
              </div>
              <div className="flex justify-between border-t border-border pt-1.5 font-semibold">
                <span>Net due</span>
                <span className="tabular-nums">
                  {formatMoney(summary.netDueCents)}
                </span>
              </div>
            </div>
          ) : (
            <form
              className="mt-4 space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                mutation.mutate();
              }}
            >
              <div className="space-y-1.5">
                <Label htmlFor="damage-fee">Damage fee (cents)</Label>
                <Input
                  id="damage-fee"
                  type="number"
                  min={0}
                  value={damageFee}
                  onChange={(e) => setDamageFee(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="damage-notes">Damage notes</Label>
                <Input
                  id="damage-notes"
                  value={damageNotes}
                  onChange={(e) => setDamageNotes(e.target.value)}
                  placeholder="Scratches on rear panel…"
                />
              </div>
              {serverError ? <InlineError error={serverError} /> : null}
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "Processing…" : "Process return"}
                </Button>
              </div>
            </form>
          )}

          {summary ? (
            <div className="mt-4 flex justify-end">
              <Button onClick={() => setOpen(false)}>Done</Button>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
