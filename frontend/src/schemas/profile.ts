import { z } from "zod";

import { PASSWORD_MIN_LENGTH } from "./auth";

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, "Required."),
    newPassword: z
      .string()
      .min(PASSWORD_MIN_LENGTH, `At least ${PASSWORD_MIN_LENGTH} characters.`),
    confirmNewPassword: z.string(),
  })
  .refine((d) => d.newPassword === d.confirmNewPassword, {
    path: ["confirmNewPassword"],
    message: "Passwords do not match.",
  });

export type ChangePasswordForm = z.infer<typeof changePasswordSchema>;
