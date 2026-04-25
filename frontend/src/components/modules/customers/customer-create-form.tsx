"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import { createCustomer } from "@/lib/api/customers";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type CustomerCreateForm, customerCreateSchema } from "@/schemas/customers";

export function CustomerCreateForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CustomerCreateForm>({
    resolver: zodResolver(customerCreateSchema),
  });

  const mutation = useMutation({
    mutationFn: (input: CustomerCreateForm) =>
      createCustomer({
        firstName: input.firstName,
        lastName: input.lastName || undefined,
        email: input.email || undefined,
        phone: input.phone || undefined,
        notes: input.notes || undefined,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["customers"] });
      router.push("/customers");
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
        <Label htmlFor="firstName">First name</Label>
        <Input id="firstName" autoComplete="given-name" {...register("firstName")} />
        <FieldErrorText error={errors.firstName} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="lastName">Last name</Label>
        <Input id="lastName" autoComplete="family-name" {...register("lastName")} />
        <FieldErrorText error={errors.lastName} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        <FieldErrorText error={errors.email} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="phone">Phone</Label>
        <Input id="phone" type="tel" autoComplete="tel" {...register("phone")} />
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

      <div className="md:col-span-2">
        <Button type="submit" disabled={isSubmitting || mutation.isPending} size="lg">
          {mutation.isPending ? "Creating…" : "Create customer"}
        </Button>
      </div>
    </form>
  );
}
