"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { forgotPassword } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type ForgotPasswordInput, forgotPasswordSchema } from "@/schemas/auth";

export function ForgotPasswordForm() {
  const [serverError, setServerError] = useState<ApiError | null>(null);
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordInput>({ resolver: zodResolver(forgotPasswordSchema) });

  const mutation = useMutation({
    mutationFn: (input: ForgotPasswordInput) => forgotPassword(input.email),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: () => setSent(true),
  });

  if (sent) {
    return (
      <div
        className="rounded-xl border border-emerald-500/40 bg-emerald-950/50 p-4 text-sm leading-relaxed text-emerald-100"
        role="status"
      >
        If an account with that email exists, we&apos;ve sent a password reset link. Please check
        your inbox.
      </div>
    );
  }

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
        <Label htmlFor="email" className="text-sm font-medium text-zinc-200">
          Email
        </Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="you@company.com"
          className="auth-input"
          {...register("email")}
        />
        <FieldErrorText error={errors.email} />
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
        {mutation.isPending ? "Sending…" : "Send reset link"}
      </Button>
    </form>
  );
}
