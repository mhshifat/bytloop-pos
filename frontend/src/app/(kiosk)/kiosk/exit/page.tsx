import type { Metadata } from "next";

import { KioskExit } from "@/components/modules/kiosk/kiosk-exit";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Staff exit",
  path: "/kiosk/exit",
  noindex: true,
});

export default function KioskExitPage() {
  return <KioskExit />;
}
