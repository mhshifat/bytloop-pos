import { z } from "zod";

export const productCreateSchema = z.object({
  sku: z.string().min(1).max(64),
  barcode: z.string().max(64).optional(),
  name: z.string().min(1).max(255),
  description: z.string().max(2048).optional(),
  categoryId: z.string().uuid().optional().nullable(),
  priceCents: z.coerce.number().int().nonnegative(),
  currency: z.string().length(3).default("BDT"),
  isActive: z.boolean().default(true),
  trackInventory: z.boolean().default(true),
});

export type ProductCreateForm = z.infer<typeof productCreateSchema>;
