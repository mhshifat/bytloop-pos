import { z } from "zod";

export const customerCreateSchema = z
  .object({
    firstName: z.string().min(1).max(80),
    lastName: z.string().max(80).optional(),
    email: z.string().email().optional().or(z.literal("")),
    phone: z.string().max(32).optional(),
    notes: z.string().max(2048).optional(),
  })
  .refine(
    (d) => Boolean(d.email) || Boolean(d.phone),
    { path: ["email"], message: "Provide at least an email or phone." },
  );

export type CustomerCreateForm = z.infer<typeof customerCreateSchema>;
