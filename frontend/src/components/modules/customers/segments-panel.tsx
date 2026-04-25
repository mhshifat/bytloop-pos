"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { listSegments, listSegmentMembers, recomputeSegments } from "@/lib/api/segments";
import { isApiError } from "@/lib/api/error";

export function SegmentsPanel() {
  const [segmentId, setSegmentId] = useState<string | null>(null);

  const segQ = useQuery({ queryKey: ["segments"], queryFn: () => listSegments() });

  const recompute = useMutation({
    mutationFn: () => recomputeSegments(),
    onSuccess: async (r) => {
      toast.success(`Recomputed: ${r.segmentsCreated} segments, ${r.membershipsWritten} memberships.`);
      await segQ.refetch();
    },
  });

  const membersQ = useQuery({
    queryKey: ["segments", segmentId, "members"],
    queryFn: () => listSegmentMembers(segmentId!),
    enabled: Boolean(segmentId),
  });

  const selected = useMemo(
    () => segQ.data?.find((s) => s.id === segmentId) ?? null,
    [segQ.data, segmentId],
  );

  return (
    <div className="grid gap-4 md:grid-cols-[320px_1fr]">
      <div className="rounded-lg border border-border bg-surface p-4">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold">Segments</p>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={recompute.isPending}
            onClick={() => recompute.mutate()}
          >
            <RefreshCw size={14} aria-hidden="true" /> {recompute.isPending ? "Recomputing…" : "Recompute"}
          </Button>
        </div>
        {segQ.error && isApiError(segQ.error) ? <InlineError error={segQ.error} className="mt-3" /> : null}
        <div className="mt-3 space-y-2">
          {(segQ.data ?? []).map((s) => (
            <Button
              key={s.id}
              type="button"
              variant={s.id === segmentId ? "default" : "outline"}
              className="w-full justify-start"
              onClick={() => setSegmentId(s.id)}
            >
              {s.name}
            </Button>
          ))}
          {segQ.data && segQ.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No segments yet. Click Recompute.</p>
          ) : null}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold">{selected ? selected.name : "Select a segment"}</p>
            <p className="text-xs text-muted-foreground">
              {selected ? `Kind: ${selected.kind}` : "Pick a segment to preview members."}
            </p>
          </div>
          {membersQ.data && membersQ.data.length > 0 ? (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                const header = ["customerId", "score", "refreshedAt"];
                const rows = membersQ.data.map((m) => [m.customerId, String(m.score), m.refreshedAt]);
                const esc = (s: string) => `"${s.replaceAll('"', '""')}"`;
                const csv = [header.map(esc).join(","), ...rows.map((r) => r.map(esc).join(","))].join("\n");
                const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `segment-${selected?.name ?? "export"}.csv`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <Download size={14} aria-hidden="true" /> Export CSV
            </Button>
          ) : null}
        </div>

        {membersQ.isLoading ? (
          <p className="mt-4 text-sm text-muted-foreground">Loading…</p>
        ) : membersQ.error && isApiError(membersQ.error) ? (
          <InlineError error={membersQ.error} className="mt-4" />
        ) : membersQ.data ? (
          <div className="mt-4 space-y-2 text-sm">
            <p className="text-muted-foreground">Members: {membersQ.data.length}</p>
            <ul className="divide-y divide-border rounded-md border border-border">
              {membersQ.data.slice(0, 50).map((m) => (
                <li key={m.customerId} className="flex items-center justify-between px-3 py-2">
                  <span className="font-mono text-xs text-muted-foreground">{m.customerId.slice(0, 8)}…</span>
                  <span className="tabular-nums">{m.score.toFixed(1)}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">No data.</p>
        )}
      </div>
    </div>
  );
}

