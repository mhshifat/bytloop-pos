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
import { createSupplier, listSuppliers } from "@/lib/api/procurement";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

export function SuppliersSection() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => listSuppliers(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      createSupplier({
        name,
        email: email || null,
        phone: phone || null,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setName("");
      setEmail("");
      setPhone("");
      setServerError(null);
      toast.success("Supplier added.");
    },
  });

  return (
    <div className="space-y-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="supplier-name">Name</Label>
          <Input
            id="supplier-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-email">Email</Label>
          <Input
            id="supplier-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="supplier-phone">Phone</Label>
          <Input
            id="supplier-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>
        <div className="flex items-end">
          <Button type="submit" disabled={mutation.isPending || !name}>
            Add supplier
          </Button>
        </div>
      </form>

      {serverError ? <InlineError error={serverError} /> : null}

      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No suppliers yet" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((s) => (
              <TableRow key={s.id}>
                <TableCell>{s.name}</TableCell>
                <TableCell>{s.email ?? "—"}</TableCell>
                <TableCell>{s.phone ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
