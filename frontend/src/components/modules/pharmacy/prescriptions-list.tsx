"use client";

import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "@/components/shared/empty-state";
import { EntityLabel } from "@/components/shared/entity-label";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listPrescriptions } from "@/lib/api/pharmacy";

export function PrescriptionsList() {
  const { data, isLoading } = useQuery({
    queryKey: ["pharmacy", "prescriptions"],
    queryFn: () => listPrescriptions(),
  });

  if (isLoading) return <SkeletonCard />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No prescriptions on file"
        description="Controlled-substance dispense will require one of these."
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Rx #</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Doctor</TableHead>
          <TableHead>License</TableHead>
          <TableHead>Issued</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((rx) => (
          <TableRow key={rx.id}>
            <TableCell className="font-mono text-xs">{rx.prescriptionNo}</TableCell>
            <TableCell>
              <EntityLabel id={rx.customerId} entity="customer" fallback="Walk-in" />
            </TableCell>
            <TableCell>{rx.doctorName}</TableCell>
            <TableCell className="font-mono text-xs">
              {rx.doctorLicense ?? "—"}
            </TableCell>
            <TableCell className="whitespace-nowrap text-xs">
              {new Date(rx.issuedOn).toLocaleDateString()}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
