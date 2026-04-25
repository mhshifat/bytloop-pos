"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, RotateCcw, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/shared/ui/badge";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listAll, type QueuedMutation, remove, revive } from "@/lib/offline/queue";

export function OfflineQueueInspector() {
  const [items, setItems] = useState<QueuedMutation[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const all = await listAll();
      all.sort((a, b) => a.enqueuedAt - b.enqueuedAt);
      setItems(all);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(refresh, 10_000);
    return () => window.clearInterval(id);
  }, [refresh]);

  const onRetry = async (id: string): Promise<void> => {
    await revive(id);
    toast.success("Requeued — will retry on next sync.");
    await refresh();
  };

  const onDiscard = async (id: string): Promise<void> => {
    if (!window.confirm("Discard this mutation? The sale will be lost unless already recorded another way.")) {
      return;
    }
    await remove(id);
    toast.success("Discarded.");
    await refresh();
  };

  if (loading && items.length === 0) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Queue is empty"
        description="No offline mutations pending or dead-lettered."
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={() => void refresh()}>
          <RefreshCw size={12} /> Refresh
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Path</TableHead>
            <TableHead>Enqueued</TableHead>
            <TableHead className="text-right">Attempts</TableHead>
            <TableHead>Last error</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                {item.deadLettered ? (
                  <Badge variant="outline" className="border-red-500/50 text-red-400">
                    Dead-letter
                  </Badge>
                ) : item.nextRetryAt > Date.now() ? (
                  <Badge
                    variant="outline"
                    className="border-amber-500/50 text-amber-400"
                  >
                    Backing off
                  </Badge>
                ) : (
                  <Badge variant="outline">Pending</Badge>
                )}
              </TableCell>
              <TableCell className="font-mono text-xs">
                {item.method} {item.path}
              </TableCell>
              <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                {new Date(item.enqueuedAt).toLocaleString()}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {item.attempts}
              </TableCell>
              <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                {item.lastError ?? "—"}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-1">
                  <Button
                    variant="outline"
                    size="icon-sm"
                    aria-label="Retry"
                    onClick={() => void onRetry(item.id)}
                  >
                    <RotateCcw size={12} />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon-sm"
                    aria-label="Discard"
                    onClick={() => void onDiscard(item.id)}
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
