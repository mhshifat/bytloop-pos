import { Skeleton } from "@/components/shared/ui/skeleton";
import { cn } from "@/lib/utils/cn";

type SkeletonCardProps = {
  readonly className?: string;
  readonly lines?: number;
};

/**
 * Generic skeleton matching our card layout. Concrete features can build
 * feature-specific skeletons that mirror the final shape more closely.
 */
export function SkeletonCard({ className, lines = 3 }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4",
        className,
      )}
    >
      <Skeleton className="h-5 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}
