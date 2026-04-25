"use client";

import { motion } from "framer-motion";
import { ArrowRight, Check, Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/shared/ui/button";
import { cn } from "@/lib/utils/cn";

import { MarketingHeroPatterns } from "./marketing-hero-patterns";
import { MarketingPosShowcase } from "./marketing-pos-showcase";

const fade = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

const checks = [
  "One workspace: catalog, customers, staff, and lanes",
  "Dozens of business types—switch without reinstalling",
  "Built for shaky networks and real shift reporting",
] as const;

const stats = [
  { v: "Real-time", l: "Sales + inventory signals" },
  { v: "One stack", l: "Front lane to back office" },
  { v: "Global-ready", l: "Built for BD & intl. markets" },
] as const;

export function PublicLandingHero({ className }: { readonly className?: string }) {
  return (
    <div
      className={cn("relative z-10 overflow-hidden pb-16 pt-6 sm:pb-24 sm:pt-8 lg:pb-28", className)}
    >
      <MarketingHeroPatterns />
      <div className="relative mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-10 xl:gap-16">
          <div className="min-w-0 text-left">
            <motion.a
              href="#product"
              onClick={(e) => {
                e.preventDefault();
                document.getElementById("product")?.scrollIntoView({ behavior: "smooth" });
                window.history.pushState(null, "", "#product");
              }}
              className="mkt-eyebrow group inline-flex items-center gap-2 rounded-full border border-primary/30 bg-zinc-900/80 px-3 py-1.5 text-sm font-medium text-zinc-100 shadow-[0_0_0_1px_rgba(129,140,248,0.15)] backdrop-blur"
              variants={fade}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.4 }}
            >
              <span className="text-primary" aria-hidden>
                <Sparkles className="size-4" />
              </span>
              Explore the product
              <ArrowRight className="size-3.5 transition group-hover:translate-x-0.5" aria-hidden />
            </motion.a>

            <motion.h1
              className="mt-6 text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl lg:leading-[1.08]"
              style={{ textShadow: "0 0 40px rgba(0,0,0,0.4)" }}
              variants={fade}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.5, delay: 0.05 }}
            >
              <span className="text-zinc-50">Run the floor with</span>{" "}
              <span className="bg-linear-to-r from-violet-300 via-primary to-cyan-300 bg-clip-text text-transparent">
                one POS
              </span>{" "}
              <span className="text-zinc-50">that matches how you sell.</span>
            </motion.h1>

            <motion.p
              className="mt-5 max-w-xl text-pretty text-lg leading-relaxed text-zinc-300 sm:text-xl"
              variants={fade}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              Sell faster at the register, keep stock honest, and run the business from one product—
              from neighborhood retail and busy cafés to pharmacies, hotels, and specialty verticals.{" "}
              <span className="text-zinc-200">No feature buffet you will never open.</span>
            </motion.p>

            <motion.ul
              className="mt-6 space-y-2.5"
              aria-label="Key benefits"
              variants={fade}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.5, delay: 0.12 }}
            >
              {checks.map((c) => (
                <li key={c} className="flex items-center gap-2.5 text-sm text-zinc-200">
                  <span
                    className="grid size-5 shrink-0 place-items-center rounded-full bg-primary/20 text-primary"
                    aria-hidden
                  >
                    <Check className="size-3.5" strokeWidth={2.5} />
                  </span>
                  {c}
                </li>
              ))}
            </motion.ul>

            <motion.div
              className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center"
              variants={fade}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.5, delay: 0.15 }}
            >
              <Button
                asChild
                size="lg"
                className="h-12 min-w-44 text-base font-semibold shadow-lg shadow-primary/30"
              >
                <Link href="/signup">Start for free</Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 min-w-44 border-zinc-500/80 bg-zinc-900/50 text-zinc-100 hover:border-primary/50 hover:bg-zinc-800/50"
              >
                <Link href="/login">Sign in</Link>
              </Button>
            </motion.div>
            <motion.p
              className="mt-3 text-sm text-zinc-400"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.35 }}
            >
              <Link href="#get-started" className="text-zinc-300 underline-offset-2 hover:underline">
                Book a walkthrough
              </Link>{" "}
              · No credit card to explore the console.
            </motion.p>

            <dl className="mt-10 grid max-w-lg grid-cols-1 gap-4 sm:grid-cols-3">
              {stats.map((s, i) => (
                <motion.div
                  key={s.v}
                  className="rounded-xl border border-zinc-600/50 bg-zinc-900/60 px-3 py-3"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                >
                  <dt className="text-sm font-semibold text-zinc-50">{s.v}</dt>
                  <dd className="mt-0.5 text-xs leading-snug text-zinc-400">{s.l}</dd>
                </motion.div>
              ))}
            </dl>
          </div>

          <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
            <div className="lg:pl-4">
              <MarketingPosShowcase />
            </div>
            <p className="mt-3 text-center text-xs text-zinc-500 sm:text-left">
              Illustration — your catalog, tax rules, and lanes appear here in the live app.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
