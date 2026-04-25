"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Controller, useForm, useWatch } from "react-hook-form";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { FieldErrorText } from "@/components/shared/ui/field-error";
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
import { createDiscount, listDiscounts } from "@/lib/api/discounts";
import { isApiError } from "@/lib/api/error";
import { discountCreateSchema, type DiscountCreateInput } from "@/schemas/admin";

export function DiscountsSection() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["discounts"],
    queryFn: () => listDiscounts(),
  });

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DiscountCreateInput>({
    resolver: zodResolver(discountCreateSchema),
    defaultValues: { kind: "percent" },
  });

  const kind = useWatch({ control, name: "kind" });

  const mutation = useMutation({
    mutationFn: (input: DiscountCreateInput) => createDiscount(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["discounts"] });
      reset({ kind: "percent" });
      toast.success("Discount created.");
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Discounts</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          onSubmit={handleSubmit((v) => mutation.mutate(v))}
          className="grid gap-3 md:grid-cols-5"
          noValidate
        >
          <div className="space-y-1.5">
            <Label htmlFor="discount-code">Code</Label>
            <Input id="discount-code" placeholder="WELCOME10" {...register("code")} />
            <FieldErrorText error={errors.code} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="discount-name">Name</Label>
            <Input id="discount-name" {...register("name")} />
            <FieldErrorText error={errors.name} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="discount-kind">Kind</Label>
            <Controller
              control={control}
              name="kind"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="discount-kind">
                    <SelectValue>{field.value === "percent" ? "Percent" : "Fixed"}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percent">Percent</SelectItem>
                    <SelectItem value="fixed">Fixed amount</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          {kind === "percent" ? (
            <div className="space-y-1.5">
              <Label htmlFor="discount-percent">Percent (0–1)</Label>
              <Input id="discount-percent" placeholder="0.10" {...register("percent")} />
              <FieldErrorText error={errors.percent} />
            </div>
          ) : (
            <div className="space-y-1.5">
              <Label htmlFor="discount-amount">Amount (cents)</Label>
              <Input
                id="discount-amount"
                type="number"
                min={0}
                {...register("amountCents")}
              />
              <FieldErrorText error={errors.amountCents} />
            </div>
          )}
          <div className="flex items-end">
            <Button type="submit" disabled={isSubmitting || mutation.isPending}>
              Add discount
            </Button>
          </div>
        </form>

        {isLoading ? (
          <SkeletonCard />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No discounts yet" description="Add your first above." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead className="text-right">Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-mono text-xs">{d.code}</TableCell>
                  <TableCell>{d.name}</TableCell>
                  <TableCell>{d.kind === "percent" ? "Percent" : "Fixed"}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {d.kind === "percent" && d.percent
                      ? `${(Number(d.percent) * 100).toFixed(2)}%`
                      : d.amountCents
                        ? `${d.currency} ${(d.amountCents / 100).toFixed(2)}`
                        : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
