"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
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
import { listPlans, upsertPlan } from "@/lib/api/gym";
import { useCurrency } from "@/lib/hooks/use-currency";

export function PlansEditor() {
  const { formatMoney } = useCurrency();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["gym", "plans"],
    queryFn: () => listPlans(),
  });

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [duration, setDuration] = useState(30);
  const [price, setPrice] = useState(0);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const save = useMutation({
    mutationFn: () =>
      upsertPlan({
        code: code.toLowerCase(),
        name,
        durationDays: duration,
        priceCents: price,
        isActive: true,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["gym", "plans"] });
      toast.success("Plan saved.");
      setCode("");
      setName("");
      setDuration(30);
      setPrice(0);
      setServerError(null);
    },
  });

  return (
    <div className="space-y-4">
      <form
        className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-5"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="space-y-1.5">
          <Label htmlFor="plan-code">Code</Label>
          <Input
            id="plan-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="monthly"
            required
          />
        </div>
        <div className="space-y-1.5 md:col-span-2">
          <Label htmlFor="plan-name">Name</Label>
          <Input
            id="plan-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Monthly membership"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="plan-duration">Duration (days)</Label>
          <Input
            id="plan-duration"
            type="number"
            min={1}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="plan-price">Price (cents)</Label>
          <Input
            id="plan-price"
            type="number"
            min={0}
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
          />
        </div>
        <div className="md:col-span-5">
          <Button type="submit" disabled={save.isPending || !code || !name}>
            {save.isPending ? "Saving…" : "Save plan"}
          </Button>
        </div>
        {serverError ? (
          <div className="md:col-span-5">
            <InlineError error={serverError} />
          </div>
        ) : null}
      </form>

      {isLoading ? (
        <SkeletonCard />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No plans yet" description="Add a plan above." />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead className="text-right">Duration</TableHead>
              <TableHead className="text-right">Price</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-mono text-xs">{p.code}</TableCell>
                <TableCell>{p.name}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {p.durationDays} d
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(p.priceCents)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
