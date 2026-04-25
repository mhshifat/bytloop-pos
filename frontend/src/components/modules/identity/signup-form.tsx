"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Checkbox } from "@/components/shared/ui/checkbox";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { signup } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { type SignupInput, signupSchema } from "@/schemas/auth";

export function SignupForm() {
  const router = useRouter();
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: { acceptTerms: false },
  });

  const mutation = useMutation({
    mutationFn: (input: SignupInput) => signup(input),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: (_, input) => {
      router.push(`/activate-pending?email=${encodeURIComponent(input.email)}`);
    },
  });

  return (
    <form
      onSubmit={handleSubmit((values) => {
        setServerError(null);
        mutation.mutate(values);
      })}
      className="flex flex-col gap-4"
      noValidate
    >
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="firstName" className="text-sm font-medium text-zinc-200">
            First name
          </Label>
          <Input
            id="firstName"
            autoComplete="given-name"
            placeholder="Alex"
            className="auth-input"
            {...register("firstName")}
          />
          <FieldErrorText error={errors.firstName} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="lastName" className="text-sm font-medium text-zinc-200">
            Last name
          </Label>
          <Input
            id="lastName"
            autoComplete="family-name"
            placeholder="Rahman"
            className="auth-input"
            {...register("lastName")}
          />
          <FieldErrorText error={errors.lastName} />
        </div>
      </div>

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

      <div className="space-y-1.5">
        <Label htmlFor="password" className="text-sm font-medium text-zinc-200">
          Password
        </Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          className="auth-input"
          {...register("password")}
        />
        <FieldErrorText error={errors.password} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword" className="text-sm font-medium text-zinc-200">
          Confirm password
        </Label>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          placeholder="Repeat your password"
          className="auth-input"
          {...register("confirmPassword")}
        />
        <FieldErrorText error={errors.confirmPassword} />
      </div>

      <Controller
        control={control}
        name="acceptTerms"
        render={({ field }) => (
          <label className="flex items-start gap-2 text-sm text-zinc-300">
            <Checkbox
              id="acceptTerms"
              checked={field.value}
              onCheckedChange={(v) => field.onChange(Boolean(v))}
              className="mt-0.5"
            />
            <span>
              I agree to the{" "}
              <a href="/privacy" className="font-medium text-primary underline-offset-2 hover:underline">
                Privacy Policy
              </a>{" "}
              and{" "}
              <a href="/terms" className="font-medium text-primary underline-offset-2 hover:underline">
                Terms of Service
              </a>
              .
            </span>
          </label>
        )}
      />
      <FieldErrorText error={errors.acceptTerms} />

      {serverError ? (
        <InlineError error={serverError} className="border-red-500/40 bg-red-950/50" />
      ) : null}

      <Button
        type="submit"
        disabled={isSubmitting || mutation.isPending}
        size="lg"
        className="w-full font-semibold shadow-lg shadow-primary/30"
      >
        {mutation.isPending ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
}
