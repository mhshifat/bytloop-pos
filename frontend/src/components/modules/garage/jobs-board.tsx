"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/shared/empty-state";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card } from "@/components/shared/ui/card";
import { isApiError } from "@/lib/api/error";
import { listJobs, type JobCardStatus, updateJobStatus } from "@/lib/api/garage";

import { JobLinesDialog } from "./job-lines-dialog";

const STATUS_LABELS: Record<JobCardStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  completed: "Completed",
  delivered: "Delivered",
};

const NEXT: Record<JobCardStatus, JobCardStatus | null> = {
  open: "in_progress",
  in_progress: "completed",
  completed: "delivered",
  delivered: null,
};

function jobStatusLabel(s: JobCardStatus): string {
  return STATUS_LABELS[s];
}

export function JobsBoard() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["garage", "jobs"],
    queryFn: () => listJobs(),
  });

  const mutation = useMutation({
    mutationFn: (args: { readonly id: string; readonly status: JobCardStatus }) =>
      updateJobStatus(args.id, args.status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["garage", "jobs"] }),
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.length === 0) {
    return <EmptyState title="No open jobs" description="Jobs show here as they open." />;
  }

  return (
    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {data.map((job) => {
        const next = NEXT[job.status];
        return (
          <Card key={job.id} className="space-y-3 p-4">
            <header className="flex items-center justify-between">
              <span className="font-mono text-xs">{job.id.slice(0, 8)}</span>
              <EnumBadge value={job.status} getLabel={jobStatusLabel} />
            </header>
            <p className="text-sm">{job.description || "No description"}</p>
            <div className="flex items-center gap-2">
              <JobLinesDialog jobId={job.id} />
              {next ? (
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => mutation.mutate({ id: job.id, status: next })}
                >
                  Advance to {STATUS_LABELS[next]}
                </Button>
              ) : null}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
