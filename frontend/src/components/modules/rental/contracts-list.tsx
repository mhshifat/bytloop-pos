"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { EntityLabel } from "@/components/shared/entity-label";
import { EmptyState } from "@/components/shared/empty-state";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { isApiError } from "@/lib/api/error";
import { listContracts, rentalCheckOut, type RentalStatus } from "@/lib/api/rental";
import { useCurrency } from "@/lib/hooks/use-currency";

import { ReturnDialog } from "./return-dialog";

const STATUS_LABELS: Record<RentalStatus, string> = {
  reserved: "Reserved",
  out: "Out",
  returned: "Returned",
  overdue: "Overdue",
};

export function ContractsList() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["rental", "contracts"],
    queryFn: () => listContracts(),
  });

  const checkOut = useMutation({
    mutationFn: (id: string) => rentalCheckOut(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rental", "contracts"] });
      toast.success("Asset checked out.");
    },
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.length === 0) return <EmptyState title="No contracts yet" />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Starts</TableHead>
          <TableHead>Ends</TableHead>
          <TableHead className="text-right">Deposit</TableHead>
          <TableHead className="text-right">Fees</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((c) => (
          <TableRow key={c.id}>
            <TableCell>
              <EntityLabel id={c.customerId} entity="customer" />
            </TableCell>
            <TableCell>
              <EnumBadge value={c.status} getLabel={(s) => STATUS_LABELS[s]} />
            </TableCell>
            <TableCell className="text-xs">
              {new Date(c.startsAt).toLocaleString()}
            </TableCell>
            <TableCell className="text-xs">
              {new Date(c.endsAt).toLocaleString()}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(c.depositCents)}
            </TableCell>
            <TableCell className="text-right tabular-nums text-xs">
              {c.lateFeeCents + c.damageFeeCents > 0
                ? formatMoney(c.lateFeeCents + c.damageFeeCents)
                : "—"}
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                {c.status === "reserved" ? (
                  <Button
                    size="sm"
                    onClick={() => checkOut.mutate(c.id)}
                    disabled={checkOut.isPending}
                  >
                    Check out
                  </Button>
                ) : null}
                {c.status === "out" || c.status === "overdue" ? (
                  <ReturnDialog contractId={c.id} />
                ) : null}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
