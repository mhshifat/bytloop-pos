"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { CategoryPicker } from "@/components/shared/category-picker";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Checkbox } from "@/components/shared/ui/checkbox";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import { createProduct } from "@/lib/api/catalog";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type ProductCreateForm, productCreateSchema } from "@/schemas/catalog";

export function ProductCreateForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ProductCreateForm>({
    resolver: zodResolver(productCreateSchema),
    defaultValues: {
      currency: "BDT",
      isActive: true,
      trackInventory: true,
      priceCents: 0,
    },
  });

  const mutation = useMutation({
    mutationFn: (input: ProductCreateForm) => createProduct(input),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      router.push("/products");
    },
  });

  return (
    <form
      onSubmit={handleSubmit((v) => {
        setServerError(null);
        mutation.mutate(v);
      })}
      className="grid gap-4 md:grid-cols-2"
      noValidate
    >
      <div className="space-y-1.5">
        <Label htmlFor="sku">SKU</Label>
        <Input id="sku" {...register("sku")} />
        <FieldErrorText error={errors.sku} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="barcode">Barcode (optional)</Label>
        <Input id="barcode" {...register("barcode")} />
        <FieldErrorText error={errors.barcode} />
      </div>

      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="name">Name</Label>
        <Input id="name" {...register("name")} />
        <FieldErrorText error={errors.name} />
      </div>

      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="description">Description</Label>
        <Textarea id="description" rows={3} {...register("description")} />
        <FieldErrorText error={errors.description} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="priceCents">Price (cents)</Label>
        <Input id="priceCents" type="number" min={0} {...register("priceCents")} />
        <FieldErrorText error={errors.priceCents} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="currency">Currency</Label>
        <Input id="currency" maxLength={3} {...register("currency")} />
        <FieldErrorText error={errors.currency} />
      </div>

      <Controller
        control={control}
        name="categoryId"
        render={({ field }) => (
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="categoryId">Category</Label>
            <CategoryPicker
              id="categoryId"
              value={field.value ?? null}
              onChange={field.onChange}
            />
          </div>
        )}
      />

      <Controller
        control={control}
        name="isActive"
        render={({ field }) => (
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              id="isActive"
              checked={field.value}
              onCheckedChange={(v) => field.onChange(Boolean(v))}
            />
            Active (visible in POS)
          </label>
        )}
      />

      <Controller
        control={control}
        name="trackInventory"
        render={({ field }) => (
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              id="trackInventory"
              checked={field.value}
              onCheckedChange={(v) => field.onChange(Boolean(v))}
            />
            Track inventory
          </label>
        )}
      />

      {serverError ? (
        <div className="md:col-span-2">
          <InlineError error={serverError} />
        </div>
      ) : null}

      <div className="md:col-span-2">
        <Button type="submit" disabled={isSubmitting || mutation.isPending} size="lg">
          {mutation.isPending ? "Creating…" : "Create product"}
        </Button>
      </div>
    </form>
  );
}
