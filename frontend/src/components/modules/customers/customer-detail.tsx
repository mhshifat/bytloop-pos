"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import type { CustomerUpdateInput } from "@/lib/api/customers";
import { getCustomer, updateCustomer } from "@/lib/api/customers";
import { apiFetch } from "@/lib/api/fetcher";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type CustomerCreateForm, customerCreateSchema } from "@/schemas/customers";

type CustomerDetailProps = {
  readonly customerId: string;
};

export function CustomerDetail({ customerId }: CustomerDetailProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["customers", customerId],
    queryFn: () => getCustomer(customerId),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<CustomerCreateForm>({ resolver: zodResolver(customerCreateSchema) });

  useEffect(() => {
    if (!data) return;
    reset({
      firstName: data.firstName,
      lastName: data.lastName || undefined,
      email: data.email ?? undefined,
      phone: data.phone ?? undefined,
      notes: data.notes ?? undefined,
    });
  }, [data, reset]);

  const saveMutation = useMutation({
    mutationFn: (v: CustomerCreateForm) => {
      const payload: CustomerUpdateInput = {
        firstName: v.firstName,
        lastName: v.lastName || "",
        email: v.email || null,
        phone: v.phone || null,
        notes: v.notes || null,
      };
      return updateCustomer(customerId, payload);
    },
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["customers"] });
      await queryClient.invalidateQueries({ queryKey: ["customers", customerId] });
      toast.success("Customer updated.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiFetch<void>(`/customers/${customerId}`, { method: "DELETE" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["customers"] });
      toast.success("Customer deleted.");
      router.push("/customers");
    },
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((v) => {
              setServerError(null);
              saveMutation.mutate(v);
            })}
            className="grid gap-4 md:grid-cols-2"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="firstName">First name</Label>
              <Input id="firstName" {...register("firstName")} />
              <FieldErrorText error={errors.firstName} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="lastName">Last name</Label>
              <Input id="lastName" {...register("lastName")} />
              <FieldErrorText error={errors.lastName} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              <FieldErrorText error={errors.email} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" type="tel" {...register("phone")} />
              <FieldErrorText error={errors.phone} />
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" rows={3} {...register("notes")} />
              <FieldErrorText error={errors.notes} />
            </div>

            {serverError ? (
              <div className="md:col-span-2">
                <InlineError error={serverError} />
              </div>
            ) : null}

            <div className="flex items-center gap-3 md:col-span-2">
              <Button
                type="submit"
                disabled={isSubmitting || saveMutation.isPending || !isDirty}
              >
                {saveMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={deleteMutation.isPending}
                onClick={() => {
                  if (window.confirm("Delete this customer?")) {
                    deleteMutation.mutate();
                  }
                }}
              >
                <Trash2 size={14} /> Delete
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
