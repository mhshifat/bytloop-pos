"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { CloudinaryUploader } from "@/components/shared/cloudinary-uploader";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { Textarea } from "@/components/shared/ui/textarea";
import { createPlanogram, listPlanograms, scanPlanogram, type PlanogramScanResult } from "@/lib/api/ai-planograms";
import { isApiError } from "@/lib/api/error";

export function PlanogramsPanel() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [locationName, setLocationName] = useState("");
  const [skusText, setSkusText] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<PlanogramScanResult | null>(null);

  const { data: planograms } = useQuery({
    queryKey: ["planograms"],
    queryFn: () => listPlanograms(),
  });

  const selected = useMemo(
    () => planograms?.find((p) => p.id === selectedId) ?? null,
    [planograms, selectedId],
  );

  const createMut = useMutation({
    mutationFn: () =>
      createPlanogram({
        name,
        locationName,
        expectedSkus: skusText
          .split(/\r?\n/)
          .map((s) => s.trim())
          .filter(Boolean),
      }),
    onSuccess: async (p) => {
      await qc.invalidateQueries({ queryKey: ["planograms"] });
      setSelectedId(p.id);
      setName("");
      setLocationName("");
      setSkusText("");
    },
  });

  const scanMut = useMutation({
    mutationFn: (asset: { readonly publicId: string; readonly url: string }) =>
      scanPlanogram({ asset, planogramId: selectedId }),
    onSuccess: (res) => setScanResult(res),
  });

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Create planogram</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="pl-name">Name</Label>
            <Input id="pl-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="pl-loc">Location (optional)</Label>
            <Input id="pl-loc" value={locationName} onChange={(e) => setLocationName(e.target.value)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="pl-skus">Expected SKUs (one per line)</Label>
            <Textarea id="pl-skus" rows={6} value={skusText} onChange={(e) => setSkusText(e.target.value)} />
          </div>
        </div>
        {createMut.error && isApiError(createMut.error) ? <InlineError error={createMut.error} className="mt-3" /> : null}
        <div className="mt-3 flex justify-end">
          <Button
            type="button"
            disabled={createMut.isPending || name.trim().length === 0 || skusText.trim().length === 0}
            onClick={() => createMut.mutate()}
          >
            {createMut.isPending ? "Creating…" : "Create planogram"}
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-4">
        <h2 className="text-sm font-semibold">Scan shelf photo</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Pick a planogram (optional), then upload a shelf photo to detect missing/unexpected SKUs.
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {(planograms ?? []).map((p) => (
            <Button
              key={p.id}
              type="button"
              size="sm"
              variant={p.id === selectedId ? "default" : "outline"}
              onClick={() => setSelectedId(p.id)}
            >
              {p.name}
            </Button>
          ))}
          {selectedId ? (
            <Button type="button" size="sm" variant="ghost" onClick={() => setSelectedId(null)}>
              Clear selection
            </Button>
          ) : null}
        </div>

        <div className="mt-3">
          <CloudinaryUploader
            purpose="planogram"
            label={scanMut.isPending ? "Scanning…" : "Upload shelf photo"}
            onUploaded={(asset) => scanMut.mutate({ publicId: asset.publicId, url: asset.secureUrl })}
          />
        </div>

        {scanMut.error && isApiError(scanMut.error) ? <InlineError error={scanMut.error} className="mt-3" /> : null}

        {scanResult ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <ResultCard title="Missing SKUs" items={scanResult.missingSkus} />
            <ResultCard title="Unexpected SKUs" items={scanResult.unexpectedSkus} />
          </div>
        ) : null}

        {selected ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Selected planogram: <span className="text-foreground">{selected.name}</span>{" "}
            {selected.locationName ? `(${selected.locationName})` : ""}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ResultCard({ title, items }: { readonly title: string; readonly items: readonly string[] }) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <p className="text-sm font-medium">{title}</p>
      {items.length === 0 ? (
        <p className="mt-1 text-sm text-muted-foreground">None.</p>
      ) : (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {items.slice(0, 30).map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

