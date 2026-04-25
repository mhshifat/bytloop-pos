"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils/cn";

type GradientOrbsProps = {
  readonly className?: string;
};

/**
 * Decorative drifting gradient orbs. Purely visual — `aria-hidden`.
 * Motion is suppressed when `prefers-reduced-motion` is set (see globals.css).
 */
export function GradientOrbs({ className }: GradientOrbsProps) {
  return (
    <div
      aria-hidden="true"
      role="presentation"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <motion.div
        className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-500/25 blur-3xl"
        animate={{ x: [0, 40, 0], y: [0, 30, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -bottom-32 -right-32 h-[28rem] w-[28rem] rounded-full bg-fuchsia-500/20 blur-3xl"
        animate={{ x: [0, -30, 0], y: [0, -20, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute left-1/3 top-1/2 h-80 w-80 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-400/15 blur-3xl"
        animate={{ x: [-20, 20, -20], y: [20, -20, 20] }}
        transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
