import { cn } from "@/lib/utils/cn";

/**
 * Subtle SVG grid with a radial mask — great for auth/marketing hero.
 * Static (no motion); pairs well with GradientOrbs on top.
 */
export function GridParticles({ className }: { readonly className?: string }) {
  return (
    <svg
      aria-hidden="true"
      role="presentation"
      className={cn(
        "pointer-events-none absolute inset-0 h-full w-full text-primary/20",
        className,
      )}
    >
      <defs>
        <pattern id="grid-dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="1" fill="currentColor" />
        </pattern>
        <radialGradient id="grid-mask" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="white" stopOpacity="1" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </radialGradient>
        <mask id="grid-fade">
          <rect width="100%" height="100%" fill="url(#grid-mask)" />
        </mask>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid-dots)" mask="url(#grid-fade)" />
    </svg>
  );
}
