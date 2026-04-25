import type { Metadata } from "next";

import { AuroraWaves, GradientOrbs, GridParticles } from "@/components/shared/backgrounds";
import { MarketingFaqSection } from "@/components/shared/marketing/marketing-faq-section";
import {
  MarketingCtaSection,
  MarketingFooter,
  MarketingIndustriesSection,
  MarketingProductSection,
  MarketingReliabilitySection,
  MarketingWorkflowSection,
} from "@/components/shared/marketing/marketing-landing-sections";
import {
  MarketingPosTypesSection,
  MarketingSimplicitySection,
} from "@/components/shared/marketing/marketing-solutions-sections";
import { MarketingNav } from "@/components/shared/marketing/marketing-nav";
import { PublicLandingHero } from "@/components/shared/marketing/public-landing-hero";
import { getCurrentUser } from "@/lib/auth";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Bytloop POS — one platform for every kind of sale",
  description:
    "Point-of-sale and operations for retail, restaurants, grocery, pharmacy, hotels, and more. Fast lanes, real inventory, role-based control—start in minutes.",
  path: "/",
});

export default async function LandingPage() {
  const sessionUser = await getCurrentUser();
  const signedIn = sessionUser !== null;

  return (
    <div className="marketing-page relative min-h-dvh bg-background text-zinc-50">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <GradientOrbs className="opacity-50" />
        <GridParticles className="opacity-80" />
        <AuroraWaves className="opacity-60" />
      </div>
      <MarketingNav signedIn={signedIn} />
      <main>
        <section id="hero" className="scroll-mt-16">
          <PublicLandingHero />
        </section>
        <MarketingSimplicitySection />
        <MarketingProductSection />
        <MarketingPosTypesSection />
        <MarketingIndustriesSection />
        <MarketingWorkflowSection />
        <MarketingReliabilitySection />
        <MarketingFaqSection />
        <MarketingCtaSection />
        <MarketingFooter />
      </main>
    </div>
  );
}
