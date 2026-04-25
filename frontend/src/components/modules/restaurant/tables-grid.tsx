"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { EnumBadge } from "@/components/shared/enum-display";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card } from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { createTable, listTables } from "@/lib/api/tables";
import { isApiError } from "@/lib/api/error";
import { tableStatusLabel } from "@/lib/enums/table-status";

export function TablesGrid() {
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [label, setLabel] = useState("");
  const [seats, setSeats] = useState(4);

  const { data, isLoading, error } = useQuery({
    queryKey: ["restaurant", "tables"],
    queryFn: () => listTables(),
  });

  const mutation = useMutation({
    mutationFn: () => createTable({ code, label: label || code, seats }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["restaurant", "tables"] });
      setCode("");
      setLabel("");
      setSeats(4);
      toast.success("Table added.");
    },
  });

  return (
    <div className="space-y-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="table-code">Code</Label>
          <Input
            id="table-code"
            placeholder="T-01"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="table-label">Label</Label>
          <Input
            id="table-label"
            placeholder="Window table"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="table-seats">Seats</Label>
          <Input
            id="table-seats"
            type="number"
            min={1}
            max={40}
            value={seats}
            onChange={(e) => setSeats(Number(e.target.value))}
          />
        </div>
        <div className="flex items-end">
          <Button type="submit" disabled={mutation.isPending || !code}>
            Add table
          </Button>
        </div>
      </form>

      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <SkeletonCard /> <SkeletonCard /> <SkeletonCard />
        </div>
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState
          title="No tables yet"
          description="Add tables to enable dine-in orders and KOT fires."
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {data.map((t) => (
            <Card key={t.id} className="flex flex-col gap-2 p-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-muted-foreground">{t.code}</span>
                <EnumBadge value={t.status} getLabel={tableStatusLabel} />
              </div>
              <p className="text-base font-medium">{t.label}</p>
              <p className="text-xs text-muted-foreground">{t.seats} seats</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
