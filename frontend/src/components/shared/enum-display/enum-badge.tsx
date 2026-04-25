import { Badge } from "@/components/shared/ui/badge";
import { cn } from "@/lib/utils/cn";

type EnumBadgeProps<T extends string> = {
  readonly value: T;
  readonly getLabel: (value: T) => string;
  readonly variant?: "default" | "secondary" | "destructive" | "outline";
  readonly className?: string;
};

/**
 * Typed badge for enum-like values. The raw value is NEVER rendered as text —
 * it's passed to `getLabel()` which returns the translated human string.
 *
 * See docs/PLAN.md §13 Enum display rule.
 */
export function EnumBadge<T extends string>({
  value,
  getLabel,
  variant = "secondary",
  className,
}: EnumBadgeProps<T>) {
  return (
    <Badge
      variant={variant}
      className={cn(className)}
      data-enum={value /* diagnostic hook only, stripped in prod build if needed */}
    >
      {getLabel(value)}
    </Badge>
  );
}
