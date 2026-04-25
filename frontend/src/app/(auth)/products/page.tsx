import type { Metadata } from "next";
import Link from "next/link";
import { Plus } from "lucide-react";

import { ProductsList } from "@/components/modules/catalog/products-list";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Products",
  path: "/products",
  noindex: true,
});

export default function ProductsPage() {
  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Products</h1>
          <p className="text-sm text-muted-foreground">Manage your catalog.</p>
        </div>
        <Button asChild>
          <Link href="/products/new" className="flex items-center gap-2">
            <Plus size={14} /> New product
          </Link>
        </Button>
      </header>
      <ProductsList />
    </section>
  );
}
