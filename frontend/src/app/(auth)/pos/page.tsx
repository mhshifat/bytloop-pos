import type { Metadata } from "next";

import { PosTerminal } from "@/components/modules/pos/pos-terminal";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "POS terminal",
  path: "/pos",
  noindex: true,
});

export default function PosPage() {
  return <PosTerminal />;
}
