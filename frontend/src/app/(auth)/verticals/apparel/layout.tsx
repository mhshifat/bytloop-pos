import type { ReactNode } from "react";
import type { Metadata } from "next";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Apparel — variants",
  path: "/verticals/apparel",
  noindex: true,
});

export default function ApparelLayout({ children }: { children: ReactNode }) {
  return children;
}
