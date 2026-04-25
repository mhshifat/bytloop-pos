"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils/cn";

/**
 * Abstract “register” visual — suggests the app without a real screenshot.
 */
export function MarketingPosShowcase({ className }: { readonly className?: string }) {
  return (
    <motion.div
      className={cn("relative w-full", className)}
      initial={{ opacity: 0, y: 24, rotateX: 8 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      style={{ transformPerspective: 1200 }}
    >
      <div
        className="absolute -inset-1 rounded-3xl bg-linear-to-br from-primary/25 via-fuchsia-500/15 to-cyan-500/20 blur-2xl"
        aria-hidden
      />
      <div className="relative overflow-hidden rounded-2xl border border-zinc-600/80 bg-zinc-900/90 shadow-2xl shadow-black/50 ring-1 ring-white/10">
        <div className="flex items-center justify-between border-b border-zinc-600/50 bg-zinc-950/80 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-400" aria-hidden />
            <div className="h-2.5 w-2.5 rounded-full bg-amber-400" aria-hidden />
            <div className="h-2.5 w-2.5 rounded-full bg-zinc-500" aria-hidden />
          </div>
          <p className="text-xs font-medium text-zinc-200">Bytloop · Main lane</p>
          <div className="h-2 w-16 rounded bg-zinc-600/50" aria-hidden />
        </div>
        <div className="grid grid-cols-[1.2fr,1fr] gap-0 border-b border-zinc-600/30">
          <div className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">Cart</p>
            <ul className="mt-3 space-y-2.5 text-sm text-zinc-200">
              <li className="flex justify-between gap-2">
                <span>Americano (L)</span>
                <span className="tabular-nums text-zinc-300">৳ 240</span>
              </li>
              <li className="flex justify-between gap-2">
                <span>Chocolate croissant</span>
                <span className="tabular-nums text-zinc-300">৳ 195</span>
              </li>
              <li className="flex justify-between gap-2 text-zinc-500 line-through">
                <span>Member discount</span>
                <span>−৳ 40</span>
              </li>
            </ul>
          </div>
          <div className="border-l border-zinc-600/30 bg-zinc-800/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">Numpad</p>
            <div className="mt-2 grid grid-cols-3 gap-1.5 text-center text-sm font-medium text-zinc-100">
              {["1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "0", "⌫"].map((k) => (
                <span
                  key={k}
                  className="rounded-md border border-zinc-600/40 bg-zinc-800/50 py-2.5"
                >
                  {k}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between bg-primary/90 px-4 py-3 text-primary-foreground">
          <span className="text-sm font-medium">Total</span>
          <span className="text-2xl font-bold tabular-nums">৳ 635</span>
        </div>
        <div className="grid grid-cols-2 gap-2 border-t border-zinc-600/30 bg-zinc-950/60 p-3">
          <div className="rounded-lg border border-zinc-500/30 bg-zinc-800/40 py-2 text-center text-sm font-medium text-zinc-100">
            Card
          </div>
          <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/20 py-2 text-center text-sm font-medium text-emerald-200">
            Cash
          </div>
        </div>
      </div>
      <motion.svg
        className="pointer-events-none absolute -right-4 -top-4 h-24 w-24 text-primary/30 sm:-right-8"
        viewBox="0 0 100 100"
        fill="none"
        aria-hidden
        animate={{ rotate: [0, 6, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      >
        <path
          d="M20 50 Q50 20 80 50 T50 85"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <circle cx="50" cy="50" r="4" fill="currentColor" className="text-cyan-400" />
      </motion.svg>
    </motion.div>
  );
}
