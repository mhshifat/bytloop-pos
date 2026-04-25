"use client";

import { AuroraWaves, GradientOrbs, GridParticles } from "@/components/shared/backgrounds";

/**
 * Ambient background aligned with the public marketing + guest auth pages.
 * Fixed behind the sidebar and main content (pointer-events: none).
 */
export function AppShellBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <GradientOrbs className="opacity-35" />
      <GridParticles />
      <AuroraWaves className="opacity-35" />
    </div>
  );
}
