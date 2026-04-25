import type { Metadata } from "next";
import Link from "next/link";

import { ProductCreateForm } from "@/components/modules/catalog/product-create-form";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "New product",
  path: "/products/new",
  noindex: true,
});

export default function NewProductPage() {
  return (
    <section className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">New product</h1>
        <p className="text-sm text-muted-foreground">
          Fill in the basics — you can edit details later.
        </p>
      </header>
      <ProductCreateForm />
      <Button asChild variant="ghost" size="sm">
        <Link href="/products">← Back to products</Link>
      </Button>
    </section>
  );
}
