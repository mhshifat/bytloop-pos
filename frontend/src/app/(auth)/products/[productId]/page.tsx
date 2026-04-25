import type { Metadata } from "next";
import Link from "next/link";

import { VariantsList } from "@/components/modules/apparel/variants-list";
import { ProductEditForm } from "@/components/modules/catalog/product-edit-form";
import { WeighableForm } from "@/components/modules/grocery/weighable-form";
import { JewelryAttributesForm } from "@/components/modules/jewelry/attributes-form";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Edit product",
  path: "/products",
  noindex: true,
});

type PageProps = {
  readonly params: Promise<{ readonly productId: string }>;
};

export default async function ProductDetailPage({ params }: PageProps) {
  const { productId } = await params;
  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/products">← Back to products</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Edit product</h1>
        <p className="text-sm text-muted-foreground">
          Update fields, then save. Changes are logged in the audit trail.
        </p>
      </header>
      <ProductEditForm productId={productId} />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Apparel variants</CardTitle>
        </CardHeader>
        <CardContent>
          <VariantsList productId={productId} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Grocery — weighable pricing</CardTitle>
        </CardHeader>
        <CardContent>
          <WeighableForm productId={productId} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Jewelry attributes</CardTitle>
        </CardHeader>
        <CardContent>
          <JewelryAttributesForm productId={productId} />
        </CardContent>
      </Card>
    </section>
  );
}
