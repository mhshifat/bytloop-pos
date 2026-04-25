import { SkeletonCard } from "@/components/shared/skeleton-card";

export default function RootLoading() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-2xl items-center justify-center p-6">
      <div className="w-full max-w-md">
        <SkeletonCard lines={4} />
      </div>
    </div>
  );
}
