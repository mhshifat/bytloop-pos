import { SkeletonCard } from "@/components/shared/skeleton-card";

export default function AuthLoading() {
  return (
    <div className="space-y-4">
      <SkeletonCard />
      <SkeletonCard />
    </div>
  );
}
