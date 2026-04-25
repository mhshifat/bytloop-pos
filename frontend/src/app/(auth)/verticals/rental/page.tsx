"use client";

import { useQuery } from "@tanstack/react-query";

import { AssetCreateForm } from "@/components/modules/rental/asset-create-form";
import { ContractCreateForm } from "@/components/modules/rental/contract-create-form";
import { ContractsList } from "@/components/modules/rental/contracts-list";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { isApiError } from "@/lib/api/error";
import { listAssets } from "@/lib/api/rental";
import { useCurrency } from "@/lib/hooks/use-currency";

export default function RentalPage() {
  const { formatMoney } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ["rental", "assets"],
    queryFn: () => listAssets(),
  });

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Rental</h1>
        <p className="text-sm text-muted-foreground">Assets &amp; contracts.</p>
      </header>

      <AssetCreateForm />
      <ContractCreateForm />
      <ContractsList />

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No rental assets yet" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Asset</TableHead>
              <TableHead className="text-right">Hourly</TableHead>
              <TableHead className="text-right">Daily</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((a) => (
              <TableRow key={a.id}>
                <TableCell className="font-mono text-xs">{a.code}</TableCell>
                <TableCell>{a.label}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(a.hourlyRateCents)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(a.dailyRateCents)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  );
}
