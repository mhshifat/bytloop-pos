"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils/cn";

/** Large mesh + arc SVGs for the hero — motion respects reduced motion via framer if we add useReducedMotion later */
export function MarketingHeroPatterns({ className }: { readonly className?: string }) {
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden>
      <svg
        className="absolute -left-[20%] top-0 h-[min(90dvh,800px)] w-[min(140%,1200px)] text-primary/20"
        viewBox="0 0 800 600"
        fill="none"
      >
        <defs>
          <linearGradient id="mkt-mesh1" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.5" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
        <motion.g
          animate={{ x: [0, 12, 0], y: [0, -8, 0] }}
          transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
        >
          <path
            d="M0 420 Q200 300 400 400 T800 360 L800 600 L0 600 Z"
            fill="url(#mkt-mesh1)"
            opacity="0.35"
          />
        </motion.g>
        {[0, 1, 2, 3, 4].map((i) => (
          <line
            key={i}
            x1={80 + i * 140}
            y1="40"
            x2={200 + i * 80}
            y2="520"
            stroke="currentColor"
            strokeWidth="0.5"
            opacity="0.2"
          />
        ))}
      </svg>
      <svg
        className="absolute -right-[10%] bottom-0 h-[50dvh] w-[80%] text-cyan-400/15"
        viewBox="0 0 400 300"
        fill="none"
      >
        <motion.path
          d="M0 200 Q100 100 200 200 T400 120 L400 300 L0 300 Z"
          fill="currentColor"
          animate={{ d: [
            "M0 200 Q100 100 200 200 T400 120 L400 300 L0 300 Z",
            "M0 210 Q100 120 200 190 T400 130 L400 300 L0 300 Z",
            "M0 200 Q100 100 200 200 T400 120 L400 300 L0 300 Z",
          ] }}
          transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
        />
      </svg>
    </div>
  );
}
