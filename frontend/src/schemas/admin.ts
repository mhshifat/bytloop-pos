import { z } from "zod";

export const taxRuleCreateSchema = z.object({
  code: z.string().min(1).max(32),
  name: z.string().min(1).max(128),
  rate: z
    .string()
    .regex(/^0?(\.\d+)?$|^1(\.0+)?$/, "Enter a rate between 0 and 1 (e.g. 0.15)"),
  isInclusive: z.boolean(),
});

export type TaxRuleCreateInput = z.infer<typeof taxRuleCreateSchema>;

export const discountCreateSchema = z
  .object({
    code: z.string().min(1).max(32),
    name: z.string().min(1).max(128),
    kind: z.enum(["percent", "fixed"]),
    percent: z.string().optional(),
    amountCents: z.coerce.number().int().nonnegative().optional(),
  })
  .refine(
    (d) => d.kind !== "percent" || (d.percent !== undefined && d.percent !== ""),
    { path: ["percent"], message: "Percent is required for percent discounts." },
  )
  .refine(
    (d) => d.kind !== "fixed" || (d.amountCents !== undefined && d.amountCents > 0),
    { path: ["amountCents"], message: "Amount is required for fixed discounts." },
  );

export type DiscountCreateInput = z.infer<typeof discountCreateSchema>;
