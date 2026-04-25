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
import { listClasses } from "@/lib/api/gym";

export function ClassesList() {
  const { data, isLoading } = useQuery({
    queryKey: ["gym", "classes"],
    queryFn: () => listClasses(),
  });

  if (isLoading) return <SkeletonCard />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No upcoming classes"
        description="Schedule one from the backend for now — UI coming soon."
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Class</TableHead>
          <TableHead>Trainer</TableHead>
          <TableHead>Starts</TableHead>
          <TableHead className="text-right">Capacity</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((c) => (
          <TableRow key={c.id}>
            <TableCell>{c.title}</TableCell>
            <TableCell>
              <EntityLabel id={c.trainerId} entity="user" fallback="—" />
            </TableCell>
            <TableCell className="whitespace-nowrap text-xs">
              {new Date(c.startsAt).toLocaleString()}
            </TableCell>
            <TableCell className="text-right tabular-nums">{c.capacity}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
