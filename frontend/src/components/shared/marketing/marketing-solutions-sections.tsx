import {
  Apple,
  Building2,
  CheckCircle2,
  Headphones,
  HeartPulse,
  type LucideIcon,
  MapPin,
  Martini,
  Music,
  Scissors,
  Sparkles,
  Stethoscope,
  Store,
  UtensilsCrossed,
} from "lucide-react";

import { SectionHeader } from "./marketing-section-header";

const SIMPLICITY: { title: string; text: string }[] = [
  {
    title: "One workspace",
    text: "Sign in once. Registers, catalog, customers, and staff share the same data—no duplicating products across tools.",
  },
  {
    title: "Set your business type",
    text: "Pick the industry you run (retail, F&B, pharmacy, hotel, and dozens more). The register and flows adapt without a new installation per store format.",
  },
  {
    title: "Power when you need it",
    text: "Kitchen display, batch tracking, custom orders, and room books live in the Verticals you turn on—optional depth, not mandatory complexity.",
  },
  {
    title: "Built for real floors",
    text: "Permissions, voids, discounts, and audit trails that finance and operations can stand behind on day one.",
  },
];

export type PosTypeCard = {
  readonly id: string;
  readonly title: string;
  readonly tagline: string;
  readonly icon: LucideIcon;
  readonly accent: string;
  readonly helps: readonly string[];
};

const POS_TYPES: readonly PosTypeCard[] = [
  {
    id: "retail",
    title: "General & specialty retail",
    tagline: "From one shop to many doors",
    icon: Store,
    accent: "from-violet-500/20 to-transparent",
    helps: [
      "Fast barcode and search-first checkout; promotions and line-level tax without spreadsheet gymnastics.",
      "Apparel, electronics, department flags—matrix SKUs, serials, and category-aware selling where you need them.",
    ],
  },
  {
    id: "fnb",
    title: "Restaurants, cafés & bars",
    tagline: "Service at speed",
    icon: UtensilsCrossed,
    accent: "from-amber-500/20 to-transparent",
    helps: [
      "Table service, kitchen display, and station routing so the right dish hits the right pass.",
      "Holds, modifiers, and a lane UI tuned for the rush—same stack as your back office.",
    ],
  },
  {
    id: "grocery",
    title: "Grocery & fresh",
    tagline: "Weigh, scan, go",
    icon: Apple,
    accent: "from-emerald-500/20 to-transparent",
    helps: [
      "PLU and integrated scale flows for weighted items—less manual keying, fewer price disputes.",
      "Scan rules that match how cashiers actually move at the register.",
    ],
  },
  {
    id: "pharmacy",
    title: "Pharmacy & regulated retail",
    tagline: "Trace what matters",
    icon: Stethoscope,
    accent: "from-cyan-500/20 to-transparent",
    helps: [
      "Line-level attention to batches and compliance-friendly patterns alongside everyday selling.",
      "Dedicate vertical screens to inventory batches and scripts without leaving the Bytloop ecosystem.",
    ],
  },
  {
    id: "hospitality",
    title: "Hotels, rental & venues",
    tagline: "Sell beyond the front desk",
    icon: Building2,
    accent: "from-sky-500/20 to-transparent",
    helps: [
      "Rooms, reservations, and guest-facing add-ons in flows staff can run in seconds.",
      "Cinema, rental counters, and salon retail share the same catalog muscle as your core POS.",
    ],
  },
  {
    id: "specialty",
    title: "Jewelry, furniture, consignment",
    tagline: "High-consideration selling",
    icon: Sparkles,
    accent: "from-fuchsia-500/20 to-transparent",
    helps: [
      "Metal rates, custom build orders, and consignor-aware selling with links from the cart to the right back-office surface.",
      "Furniture and large-ticket flows that don’t pretend every SKU behaves like a candy bar.",
    ],
  },
] as const;

const MORE_VERTICALS: { icon: LucideIcon; label: string; hint: string }[] = [
  { icon: MapPin, label: "Field & on-site", hint: "Services, trade, and mobile sales patterns." },
  { icon: Martini, label: "Clubs & nightlife", hint: "Tabs, speed rings, and bar-forward service." },
  { icon: Scissors, label: "Salon & spa", hint: "Service plus retail in one house." },
  { icon: Music, label: "Events", hint: "Concessions and merch alongside ticketing stacks." },
  { icon: HeartPulse, label: "Health & pet", hint: "Clinical and vet-adjacent retail with room to grow." },
  { icon: Headphones, label: "You name it", hint: "A broad business-type list—if we don’t have a module yet, your mode still shapes the register." },
];

export function MarketingSimplicitySection() {
  return (
    <section
      id="simplicity"
      className="scroll-mt-24 border-t border-zinc-800/60 bg-zinc-950/90 py-16 sm:py-20"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="No hassle"
          title="Complex operations, simple daily use"
          description="You should not need five logins, three spreadsheets, and a weekend training course just to open a lane. Bytloop keeps the power in the product—not in busywork."
        />
        <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SIMPLICITY.map((s) => (
            <li
              key={s.title}
              className="relative overflow-hidden rounded-2xl border border-zinc-600/40 bg-zinc-900/50 p-5 before:pointer-events-none before:absolute before:inset-0 before:bg-linear-to-b before:from-zinc-800/40 before:to-transparent"
            >
              <div className="relative z-10 flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
                <CheckCircle2 className="size-4" aria-hidden />
              </div>
              <h3 className="relative z-10 mt-3 text-base font-semibold text-zinc-50">{s.title}</h3>
              <p className="relative z-10 mt-2 text-sm leading-relaxed text-zinc-400">{s.text}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function MarketingPosTypesSection() {
  return (
    <section
      id="pos-types"
      className="scroll-mt-24 border-t border-zinc-800/50 bg-linear-to-b from-violet-950/20 via-zinc-950 to-zinc-950 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Solutions"
          title="A POS for how you actually sell"
          description="The same product powers different business types. Choose your world—we surface the right controls, copy, and optional vertical apps so you are not force-fit into a one-size-fits-nobody template."
        />

        <ul className="mt-14 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {POS_TYPES.map((c) => (
            <li
              key={c.id}
              className="group relative flex flex-col overflow-hidden rounded-2xl border border-zinc-600/40 bg-zinc-900/60 p-6 shadow-lg shadow-black/30 transition duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-primary/5"
            >
              <div
                className={`pointer-events-none absolute -right-6 -top-6 h-40 w-40 rounded-full bg-linear-to-br ${c.accent} opacity-90 blur-2xl transition group-hover:opacity-100`}
                aria-hidden
              />
              <div className="relative z-10 flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-zinc-500/30 bg-zinc-950/80 text-primary">
                  <c.icon className="size-6" aria-hidden />
                </div>
                <div className="min-w-0">
                  <h3 className="text-lg font-semibold leading-snug text-zinc-50">{c.title}</h3>
                  <p className="mt-0.5 text-sm font-medium text-primary/90">{c.tagline}</p>
                </div>
              </div>
              <ul className="relative z-10 mt-4 space-y-2.5 text-sm leading-relaxed text-zinc-300">
                {c.helps.map((h) => (
                  <li key={h} className="flex gap-2.5">
                    <span
                      className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/80"
                      aria-hidden
                    />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>

        <div className="mt-12 rounded-2xl border border-dashed border-zinc-600/50 bg-zinc-900/40 p-6 sm:p-8">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-zinc-400">
            And many more
          </p>
          <ul className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-4 sm:gap-x-8">
            {MORE_VERTICALS.map((m) => (
              <li key={m.label} className="flex max-w-44 flex-col items-center text-center sm:max-w-52">
                <m.icon
                  className="size-5 text-zinc-500"
                  strokeWidth={1.75}
                  aria-hidden
                />
                <span className="mt-2 text-sm font-medium text-zinc-200">{m.label}</span>
                <span className="mt-0.5 text-xs leading-snug text-zinc-500">{m.hint}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
