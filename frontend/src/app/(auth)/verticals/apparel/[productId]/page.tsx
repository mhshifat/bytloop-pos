import type { Metadata } from "next";

import { VariantMatrixEditor } from "@/components/modules/apparel/variant-matrix-editor";
import { VariantsList } from "@/components/modules/apparel/variants-list";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Variant matrix",
  path: "/verticals/apparel",
  noindex: true,
});

type PageProps = {
  readonly params: Promise<{ readonly productId: string }>;
};

export default async function ApparelMatrixPage({ params }: PageProps) {
  const { productId } = await params;
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Variants</h1>
        <p className="text-sm text-muted-foreground">
          Generate size × color SKUs, scan a barcode into each, and track stock
          per variant.
        </p>
      </header>
      <VariantMatrixEditor productId={productId} />
      <VariantsList productId={productId} />
    </section>
  );
}
