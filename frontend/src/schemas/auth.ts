import { z } from "zod";

export const PASSWORD_MIN_LENGTH = 8;

const passwordField = z
  .string()
  .min(PASSWORD_MIN_LENGTH, `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`);

export const signupSchema = z
  .object({
    firstName: z.string().min(1, "First name is required.").max(80),
    lastName: z.string().min(1, "Last name is required.").max(80),
    email: z.string().email("Enter a valid email."),
    password: passwordField,
    confirmPassword: z.string(),
    acceptTerms: z.boolean().refine((v) => v, {
      message: "You must accept the Privacy Policy and Terms of Service.",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match.",
  });

export type SignupInput = z.infer<typeof signupSchema>;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email."),
  password: z.string().min(1, "Password is required."),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email."),
});

export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    newPassword: passwordField,
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match.",
  });

export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
