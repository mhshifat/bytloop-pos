"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Checkbox } from "@/components/shared/ui/checkbox";
import { FieldErrorText } from "@/components/shared/ui/field-error";
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
import { createTaxRule, listTaxRules } from "@/lib/api/tax";
import { isApiError } from "@/lib/api/error";
import { taxRuleCreateSchema, type TaxRuleCreateInput } from "@/schemas/admin";

export function TaxRulesSection() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["tax-rules"],
    queryFn: () => listTaxRules(),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TaxRuleCreateInput>({
    resolver: zodResolver(taxRuleCreateSchema),
    defaultValues: { isInclusive: false },
  });

  const mutation = useMutation({
    mutationFn: (input: TaxRuleCreateInput) => createTaxRule(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tax-rules"] });
      reset();
      toast.success("Tax rule created.");
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Tax rules</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          onSubmit={handleSubmit((v) => mutation.mutate(v))}
          className="grid gap-3 md:grid-cols-5"
          noValidate
        >
          <div className="space-y-1.5">
            <Label htmlFor="tax-code">Code</Label>
            <Input id="tax-code" placeholder="VAT15" {...register("code")} />
            <FieldErrorText error={errors.code} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tax-name">Name</Label>
            <Input id="tax-name" placeholder="VAT 15%" {...register("name")} />
            <FieldErrorText error={errors.name} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tax-rate">Rate (0–1)</Label>
            <Input id="tax-rate" placeholder="0.15" {...register("rate")} />
            <FieldErrorText error={errors.rate} />
          </div>
          <div className="flex items-center gap-2 pt-7">
            <Checkbox id="tax-inclusive" {...register("isInclusive")} />
            <Label htmlFor="tax-inclusive">Inclusive</Label>
          </div>
          <div className="flex items-end">
            <Button type="submit" disabled={isSubmitting || mutation.isPending}>
              Add rule
            </Button>
          </div>
        </form>

        {isLoading ? (
          <SkeletonCard />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No tax rules yet" description="Add your first above." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead>Inclusive</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-mono text-xs">{r.code}</TableCell>
                  <TableCell>{r.name}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {(Number(r.rate) * 100).toFixed(2)}%
                  </TableCell>
                  <TableCell>{r.isInclusive ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
