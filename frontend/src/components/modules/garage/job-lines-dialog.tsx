"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ListPlus, Trash2 } from "lucide-react";
import { useState } from "react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import {
  addJobLine,
  getJobTotals,
  type JobLineKind,
  listJobLines,
  removeJobLine,
} from "@/lib/api/garage";
import { useCurrency } from "@/lib/hooks/use-currency";

type JobLinesDialogProps = {
  readonly jobId: string;
};

export function JobLinesDialog({ jobId }: JobLinesDialogProps) {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<JobLineKind>("labor");
  const [description, setDescription] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [unitCost, setUnitCost] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: lines } = useQuery({
    queryKey: ["garage", "job-lines", jobId],
    queryFn: () => listJobLines(jobId),
    enabled: open,
  });
  const { data: totals } = useQuery({
    queryKey: ["garage", "job-totals", jobId],
    queryFn: () => getJobTotals(jobId),
    enabled: open,
  });

  const add = useMutation({
    mutationFn: () =>
      addJobLine(jobId, { kind, description, quantity, unitCostCents: unitCost }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["garage", "job-lines", jobId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["garage", "job-totals", jobId],
      });
      setDescription("");
      setQuantity(1);
      setUnitCost(0);
      setServerError(null);
      toast.success("Line added.");
    },
  });

  const remove = useMutation({
    mutationFn: (lineId: string) => removeJobLine(jobId, lineId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["garage", "job-lines", jobId],
      });
      await queryClient.invalidateQueries({
        queryKey: ["garage", "job-totals", jobId],
      });
    },
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button size="sm" variant="outline">
          <ListPlus size={14} /> Lines
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Job lines</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Parts sold and labor billed on this job card.
          </Dialog.Description>

          <form
            className="mt-4 grid gap-3 md:grid-cols-5"
            onSubmit={(e) => {
              e.preventDefault();
              add.mutate();
            }}
          >
            <div className="space-y-1.5">
              <Label htmlFor="line-kind">Kind</Label>
              <Select
                value={kind}
                onValueChange={(v) => setKind(v as JobLineKind)}
              >
                <SelectTrigger id="line-kind">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="labor">Labor</SelectItem>
                  <SelectItem value="part">Part</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="line-desc">Description</Label>
              <Input
                id="line-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="line-qty">
                {kind === "labor" ? "Minutes" : "Qty"}
              </Label>
              <Input
                id="line-qty"
                type="number"
                min={1}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="line-unit">Unit cost (cents)</Label>
              <Input
                id="line-unit"
                type="number"
                min={0}
                value={unitCost}
                onChange={(e) => setUnitCost(Number(e.target.value))}
              />
            </div>
            <div className="md:col-span-5">
              <Button
                type="submit"
                disabled={add.isPending || description.trim().length === 0}
              >
                {add.isPending ? "Adding…" : "Add line"}
              </Button>
            </div>
            {serverError ? (
              <div className="md:col-span-5">
                <InlineError error={serverError} />
              </div>
            ) : null}
          </form>

          <div className="mt-4 max-h-80 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Kind</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Unit</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(lines ?? []).map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="capitalize text-xs">{l.kind}</TableCell>
                    <TableCell>{l.description}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {l.quantity}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(l.unitCostCents)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(l.lineTotalCents)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Remove line"
                        onClick={() => remove.mutate(l.id)}
                      >
                        <Trash2 size={12} />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {totals ? (
            <div className="mt-4 flex justify-end gap-6 border-t border-border pt-3 text-sm">
              <span>
                <span className="text-muted-foreground">Parts:</span>{" "}
                <span className="tabular-nums">{formatMoney(totals.partsCents)}</span>
              </span>
              <span>
                <span className="text-muted-foreground">Labor:</span>{" "}
                <span className="tabular-nums">{formatMoney(totals.laborCents)}</span>
              </span>
              <span className="font-semibold">
                Total{" "}
                <span className="tabular-nums">
                  {formatMoney(totals.totalCents)}
                </span>
              </span>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
