"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils/cn";

/**
 * Aurora-style softly animated SVG waves for hero surfaces.
 */
export function AuroraWaves({ className }: { readonly className?: string }) {
  return (
    <svg
      aria-hidden="true"
      role="presentation"
      viewBox="0 0 1440 600"
      preserveAspectRatio="none"
      className={cn("pointer-events-none absolute inset-0 h-full w-full", className)}
    >
      <defs>
        <linearGradient id="aurora-a" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#a855f7" stopOpacity="0.25" />
        </linearGradient>
        <linearGradient id="aurora-b" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.4" />
        </linearGradient>
      </defs>
      <motion.path
        d="M0 360 Q 360 280 720 360 T 1440 360 L 1440 600 L 0 600 Z"
        fill="url(#aurora-a)"
        animate={{ d: [
          "M0 360 Q 360 280 720 360 T 1440 360 L 1440 600 L 0 600 Z",
          "M0 380 Q 360 320 720 380 T 1440 360 L 1440 600 L 0 600 Z",
          "M0 360 Q 360 280 720 360 T 1440 360 L 1440 600 L 0 600 Z",
        ] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.path
        d="M0 440 Q 360 380 720 440 T 1440 440 L 1440 600 L 0 600 Z"
        fill="url(#aurora-b)"
        animate={{ d: [
          "M0 440 Q 360 380 720 440 T 1440 440 L 1440 600 L 0 600 Z",
          "M0 420 Q 360 460 720 420 T 1440 440 L 1440 600 L 0 600 Z",
          "M0 440 Q 360 380 720 440 T 1440 440 L 1440 600 L 0 600 Z",
        ] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
    </svg>
  );
}
