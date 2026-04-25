"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { resetPassword } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type ResetPasswordInput, resetPasswordSchema } from "@/schemas/auth";

type ResetPasswordFormProps = {
  readonly token: string;
};

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const router = useRouter();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordInput>({ resolver: zodResolver(resetPasswordSchema) });

  const mutation = useMutation({
    mutationFn: (input: ResetPasswordInput) => resetPassword(token, input.newPassword),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: () => router.push("/login"),
  });

  return (
    <form
      onSubmit={handleSubmit((v) => {
        setServerError(null);
        mutation.mutate(v);
      })}
      className="flex flex-col gap-4"
      noValidate
    >
      <div className="space-y-1.5">
        <Label htmlFor="newPassword" className="text-sm font-medium text-zinc-200">
          New password
        </Label>
        <Input
          id="newPassword"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          className="auth-input"
          {...register("newPassword")}
        />
        <FieldErrorText error={errors.newPassword} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword" className="text-sm font-medium text-zinc-200">
          Confirm new password
        </Label>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          placeholder="Repeat new password"
          className="auth-input"
          {...register("confirmPassword")}
        />
        <FieldErrorText error={errors.confirmPassword} />
      </div>

      {serverError ? (
        <InlineError error={serverError} className="border-red-500/40 bg-red-950/50" />
      ) : null}

      <Button
        type="submit"
        disabled={isSubmitting || mutation.isPending}
        size="lg"
        className="w-full font-semibold shadow-lg shadow-primary/30"
      >
        {mutation.isPending ? "Updating…" : "Reset password"}
      </Button>
    </form>
  );
}
