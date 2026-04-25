import type { Metadata } from "next";

import { KioskCheckout } from "@/components/modules/kiosk/kiosk-checkout";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Checkout",
  path: "/kiosk/checkout",
  noindex: true,
});

export default function KioskCheckoutPage() {
  return <KioskCheckout />;
}
