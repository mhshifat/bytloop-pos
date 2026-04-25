/**
 * (public) route-group layout — anyone can access.
 * No auth gate applied here.
 */

import type { ReactNode } from "react";

export default function PublicLayout({ children }: { readonly children: ReactNode }) {
  return <>{children}</>;
}
