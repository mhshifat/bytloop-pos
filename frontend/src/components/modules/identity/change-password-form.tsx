"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { changePassword } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type ChangePasswordForm, changePasswordSchema } from "@/schemas/profile";

export function ChangePasswordFormComponent() {
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordForm>({ resolver: zodResolver(changePasswordSchema) });

  const mutation = useMutation({
    mutationFn: (v: ChangePasswordForm) =>
      changePassword({ currentPassword: v.currentPassword, newPassword: v.newPassword }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: () => {
      reset();
      toast.success("Password updated.");
    },
  });

  return (
    <form
      onSubmit={handleSubmit((v) => {
        setServerError(null);
        mutation.mutate(v);
      })}
      className="max-w-md space-y-4"
      noValidate
    >
      <div className="space-y-1.5">
        <Label htmlFor="currentPassword">Current password</Label>
        <Input
          id="currentPassword"
          type="password"
          autoComplete="current-password"
          {...register("currentPassword")}
        />
        <FieldErrorText error={errors.currentPassword} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="newPassword">New password</Label>
        <Input
          id="newPassword"
          type="password"
          autoComplete="new-password"
          {...register("newPassword")}
        />
        <FieldErrorText error={errors.newPassword} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmNewPassword">Confirm new password</Label>
        <Input
          id="confirmNewPassword"
          type="password"
          autoComplete="new-password"
          {...register("confirmNewPassword")}
        />
        <FieldErrorText error={errors.confirmNewPassword} />
      </div>

      {serverError ? <InlineError error={serverError} /> : null}

      <Button type="submit" disabled={isSubmitting || mutation.isPending}>
        {mutation.isPending ? "Updating…" : "Update password"}
      </Button>
    </form>
  );
}
