"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import { createCampaignTrigger, listCampaignTriggers } from "@/lib/api/campaign-triggers";
import { listSegments } from "@/lib/api/segments";
import { isApiError } from "@/lib/api/error";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";

export function CampaignsPanel() {
  const [segmentId, setSegmentId] = useState<string>("__none__");
  const [threshold, setThreshold] = useState(0.6);
  const [subject, setSubject] = useState("We miss you — come back today");
  const [htmlTemplate, setHtmlTemplate] = useState("<p>Come back and enjoy your next visit.</p>");
  const [discountCode, setDiscountCode] = useState("");
  const [cooldownDays, setCooldownDays] = useState(14);
  const [enabled, setEnabled] = useState(false);

  const segQ = useQuery({ queryKey: ["segments"], queryFn: () => listSegments() });
  const trigQ = useQuery({ queryKey: ["campaign-triggers"], queryFn: () => listCampaignTriggers() });

  const create = useMutation({
    mutationFn: () =>
      createCampaignTrigger({
        segmentId: segmentId === "__none__" ? null : segmentId,
        threshold,
        subject,
        htmlTemplate,
        discountCode: discountCode.trim() ? discountCode.trim() : null,
        cooldownDays,
        enabled,
      }),
    onSuccess: async () => {
      toast.success("Trigger saved.");
      await trigQ.refetch();
    },
  });

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">New churn email trigger</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5 md:col-span-2">
            <Label>Segment (optional)</Label>
            <Select value={segmentId} onValueChange={setSegmentId}>
              <SelectTrigger>
                <SelectValue placeholder="All churn-risk customers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">All churn-risk customers</SelectItem>
                {(segQ.data ?? []).map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="thr">Threshold</Label>
            <Input id="thr" type="number" step="0.05" min={0} max={1} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cool">Cooldown (days)</Label>
            <Input id="cool" type="number" min={1} max={365} value={cooldownDays} onChange={(e) => setCooldownDays(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="subj">Subject</Label>
            <Input id="subj" value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="html">HTML template</Label>
            <Textarea id="html" rows={6} value={htmlTemplate} onChange={(e) => setHtmlTemplate(e.target.value)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="disc">Discount code (optional)</Label>
            <Input id="disc" value={discountCode} onChange={(e) => setDiscountCode(e.target.value)} />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <input id="en" type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            <Label htmlFor="en">Enabled</Label>
          </div>
        </div>
        {create.error && isApiError(create.error) ? <InlineError error={create.error} className="mt-3" /> : null}
        <div className="mt-3 flex justify-end">
          <Button type="button" onClick={() => create.mutate()} disabled={create.isPending}>
            {create.isPending ? "Saving…" : "Save trigger"}
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Existing triggers</h2>
        {trigQ.error && isApiError(trigQ.error) ? <InlineError error={trigQ.error} className="mt-3" /> : null}
        <ul className="mt-3 space-y-2 text-sm">
          {(trigQ.data ?? []).map((t) => (
            <li key={t.id} className="rounded-md border border-border bg-background p-3">
              <div className="flex items-center justify-between">
                <p className="font-medium">{t.subject || "(no subject)"}</p>
                <span className="text-xs text-muted-foreground">{t.enabled ? "enabled" : "disabled"}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                threshold {t.threshold} · cooldown {t.cooldownDays}d
              </p>
            </li>
          ))}
          {trigQ.data && trigQ.data.length === 0 ? (
            <li className="text-muted-foreground">No triggers yet.</li>
          ) : null}
        </ul>
      </div>
    </div>
  );
}

