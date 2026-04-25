"use client";

import { useId, type SVGProps } from "react";

import { cn } from "@/lib/utils/cn";

const defaultTitle = "Bytloop POS";

type BytloopLogoMarkProps = SVGProps<SVGSVGElement> & {
  readonly "aria-label"?: string;
  readonly title?: string;
};

/**
 * Wordmark-free logomark: stacked isometric “planes” looped by a ribbon — suggests
 * platform layers, continuous flow, and Point-of-Sale without a literal letter tile.
 */
export function BytloopLogoMark({
  className,
  title = defaultTitle,
  "aria-label": ariaLabel = defaultTitle,
  "aria-hidden": ariaHidden,
  ...props
}: BytloopLogoMarkProps) {
  const uid = useId().replace(/:/g, "");
  const gBg = `blpm-bg-${uid}`;
  const gRib = `blpm-rib-${uid}`;
  const fGlow = `blpm-glow-${uid}`;

  return (
    <svg
      viewBox="0 0 32 32"
      role="img"
      aria-label={ariaHidden ? undefined : ariaLabel}
      aria-hidden={ariaHidden}
      className={cn("shrink-0 select-none", className)}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <defs>
        <linearGradient id={gBg} x1="4" y1="4" x2="30" y2="28" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#7c3aed" />
          <stop offset="45%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient id={gRib} x1="6" y1="22" x2="24" y2="8" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#f8fafc" stopOpacity="0.98" />
          <stop offset="100%" stopColor="#c7d2fe" stopOpacity="0.95" />
        </linearGradient>
        <filter id={fGlow} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="0.45" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <rect width="32" height="32" rx="8" fill={`url(#${gBg})`} />
      {/* Stacked isometric “planes” — platform layers */}
      <g filter={`url(#${fGlow})`} opacity="0.98">
        <path
          fill="rgba(255,255,255,0.1)"
          d="M7 12.4 L16 7.6 L25 12.4 L16 17.1 Z"
        />
        <path
          fill="rgba(255,255,255,0.2)"
          d="M7 16.1 L16 11.2 L25 16.1 L16 20.8 Z"
        />
        <path
          fill="rgba(255,255,255,0.3)"
          d="M7 19.7 L16 15 L25 19.7 L16 24.3 Z"
        />
      </g>
      {/* “Byte loop” — arcing flow over the stack; cyan point = “point of sale / signal” */}
      <path
        fill="none"
        stroke={`url(#${gRib})`}
        strokeWidth="1.85"
        strokeLinecap="round"
        d="M6.2 22.2 Q 16 5.8 25.8 22.2"
      />
      <circle cx="24.2" cy="8.2" r="1.2" fill="#a5f3fc" />
    </svg>
  );
}

type BytloopLogoLockupProps = {
  readonly className?: string;
  readonly nameClassName?: string;
  readonly showName?: boolean;
  readonly name?: string;
  readonly size?: "sm" | "md" | "lg";
};

const sizeToMark: Record<NonNullable<BytloopLogoLockupProps["size"]>, string> = {
  sm: "h-6 w-6",
  md: "h-8 w-8",
  lg: "h-9 w-9",
};

/**
 * Mark + “Bytloop POS” for headers that need the full lockup.
 */
export function BytloopLogoLockup({
  className,
  nameClassName,
  showName = true,
  name = "Bytloop POS",
  size = "md",
}: BytloopLogoLockupProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <BytloopLogoMark className={sizeToMark[size]} />
      {showName ? <span className={cn("font-semibold tracking-tight", nameClassName)}>{name}</span> : null}
    </span>
  );
}
