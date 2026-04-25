"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { FieldErrorText } from "@/components/shared/ui/field-error";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { login } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { useAuthStore } from "@/lib/stores/auth-store";
import { AuthMethod, setLastAuthMethod } from "@/lib/stores/last-auth-method";
import { type LoginInput, loginSchema } from "@/schemas/auth";

import { LastUsedBadge } from "./last-used-badge";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [serverError, setServerError] = useState<ApiError | null>(null);
  const setAccessToken = useAuthStore((s) => s.setAccessToken);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  const mutation = useMutation({
    mutationFn: (input: LoginInput) => login(input),
    onError: (err) => {
      if (isApiError(err)) {
        setServerError(err);
        // Redirect unverified accounts to the activate-pending flow.
        if (err.code === "email_not_verified") {
          router.push("/activate-pending");
        }
      }
    },
    onSuccess: (tokens) => {
      setAccessToken(tokens.accessToken);
      setLastAuthMethod(AuthMethod.EMAIL);
      const next = searchParams.get("next") ?? "/dashboard";
      router.push(next);
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
      <div className="space-y-1.5">
        <Label htmlFor="email" className="flex items-center text-sm font-medium text-zinc-200">
          Email
          <LastUsedBadge method={AuthMethod.EMAIL} />
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
          autoComplete="current-password"
          placeholder="••••••••"
          className="auth-input"
          {...register("password")}
        />
        <FieldErrorText error={errors.password} />
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
        {mutation.isPending ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
