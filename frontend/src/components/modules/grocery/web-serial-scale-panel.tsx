"use client";

import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { useQuery } from "@tanstack/react-query";
import { getTenant } from "@/lib/api/tenant";
import { useSerialScale } from "@/lib/hooks/use-serial-scale";
import { isWebSerialScaleEnabled } from "@/lib/pos/web-serial-flags";

/**
 * Dev / pilot UI to verify USB scale text + parsing (Chrome, HTTPS or localhost).
 * Enable with `NEXT_PUBLIC_EXPERIMENTAL_WEB_SERIAL_SCALE=true` or
 * `tenant.config.posWebSerialScale === true`.
 */
export function WebSerialScalePanel() {
  const { data: tenant } = useQuery({ queryKey: ["tenant"], queryFn: () => getTenant() });
  const [baud, setBaud] = useState("9600");
  const scale = useSerialScale(Math.max(300, Math.min(921600, Number(baud) || 9600)));
  const enabled = isWebSerialScaleEnabled(tenant?.config);

  if (!enabled) {
    return (
      <div className="rounded-lg border border-border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
        <p className="font-medium text-foreground">USB Web Serial (experimental)</p>
        <p className="mt-1 text-xs">
          Set <code className="text-[11px]">NEXT_PUBLIC_EXPERIMENTAL_WEB_SERIAL_SCALE=true</code>{" "}
          in <code className="text-[11px]">.env</code>, or add{" "}
          <code className="text-[11px]">posWebSerialScale: true</code> to tenant <code>config</code>{" "}
          to test with Chrome or Edge.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
      <header>
        <h3 className="text-base font-medium">USB scale (Web Serial)</h3>
        <p className="text-sm text-muted-foreground">
          Chromium only, secure context. Pick your scale when asked; try baud{" "}
          <strong>9600</strong> (common) or 2400. Parsed weight appears as grams.
        </p>
      </header>
      <div className="flex flex-wrap items-end gap-2">
        <div className="space-y-1.5">
          <Label htmlFor="baud">Baud</Label>
          <Input
            id="baud"
            className="w-28"
            value={baud}
            onChange={(e) => setBaud(e.target.value)}
            inputMode="numeric"
          />
        </div>
        {scale.status === "open" ? (
          <Button type="button" variant="outline" onClick={() => void scale.disconnect()}>
            Disconnect
          </Button>
        ) : (
          <Button
            type="button"
            onClick={() => void scale.connect()}
            disabled={!scale.isSupported || scale.status === "connecting"}
          >
            {scale.status === "connecting" ? "Connecting…" : "Request port & connect"}
          </Button>
        )}
      </div>
      {!scale.isSupported ? (
        <p className="text-sm text-amber-600/90 dark:text-amber-200/80">
          Web Serial is not available. Use Google Chrome or Microsoft Edge.
        </p>
      ) : null}
      {scale.error ? <p className="text-sm text-destructive">{scale.error}</p> : null}
      <div className="rounded border border-border p-2 font-mono text-xs text-muted-foreground min-h-12">
        {scale.lastLine ? <p className="break-all">{scale.lastLine}</p> : <p>— raw line —</p>}
        {scale.lastGrams != null ? (
          <p className="mt-1 text-foreground">Parsed: {scale.lastGrams} g</p>
        ) : null}
        {scale.status === "open" && scale.lastGrams == null && scale.lastLine ? (
          <p className="text-[11px]">Could not parse grams — adjust format in scale-line-parser or baud.</p>
        ) : null}
      </div>
    </div>
  );
}
