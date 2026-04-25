"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { CategoryPicker } from "@/components/shared/category-picker";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Checkbox } from "@/components/shared/ui/checkbox";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import { deleteProduct, getProduct, updateProduct } from "@/lib/api/catalog";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type ProductCreateForm, productCreateSchema } from "@/schemas/catalog";

type ProductEditFormProps = {
  readonly productId: string;
};

export function ProductEditForm({ productId }: ProductEditFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["products", productId],
    queryFn: () => getProduct(productId),
  });

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProductCreateForm>({
    resolver: zodResolver(productCreateSchema),
  });

  useEffect(() => {
    if (!data) return;
    reset({
      sku: data.sku,
      barcode: data.barcode ?? undefined,
      name: data.name,
      description: data.description ?? undefined,
      categoryId: data.categoryId ?? null,
      priceCents: data.priceCents,
      currency: data.currency,
      isActive: data.isActive,
      trackInventory: data.trackInventory,
    });
  }, [data, reset]);

  const saveMutation = useMutation({
    mutationFn: (input: ProductCreateForm) =>
      updateProduct(productId, {
        barcode: input.barcode,
        name: input.name,
        description: input.description,
        categoryId: input.categoryId ?? null,
        priceCents: input.priceCents,
        currency: input.currency,
        isActive: input.isActive,
        trackInventory: input.trackInventory,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["products", productId] });
      toast.success("Product saved.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteProduct(productId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Product deleted.");
      router.push("/products");
    },
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data) return null;

  return (
    <form
      onSubmit={handleSubmit((v) => {
        setServerError(null);
        saveMutation.mutate(v);
      })}
      className="grid gap-4 md:grid-cols-2"
      noValidate
    >
      <div className="space-y-1.5">
        <Label htmlFor="sku">SKU</Label>
        <Input id="sku" {...register("sku")} readOnly disabled />
        <p className="text-xs text-muted-foreground">SKU is immutable once created.</p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="barcode">Barcode</Label>
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
            Active
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

      <div className="flex items-center gap-3 md:col-span-2">
        <Button type="submit" disabled={isSubmitting || saveMutation.isPending || !isDirty} size="lg">
          {saveMutation.isPending ? "Saving…" : "Save changes"}
        </Button>
        <Button
          type="button"
          variant="destructive"
          disabled={deleteMutation.isPending}
          onClick={() => {
            if (window.confirm("Delete this product? This cannot be undone.")) {
              deleteMutation.mutate();
            }
          }}
        >
          <Trash2 size={14} aria-hidden="true" /> Delete
        </Button>
      </div>
    </form>
  );
}
