"use client";

import { useMutation } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState } from "react";

import { CloudinaryUploader } from "@/components/shared/cloudinary-uploader";
import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import type { ShelfAuditResponse } from "@/lib/api/ai-inventory";
import { shelfLabelAudit } from "@/lib/api/ai-inventory";
import { isApiError } from "@/lib/api/error";

function toCsv(res: ShelfAuditResponse): string {
  const header = ["skuOrName", "labelPriceCents", "posPriceCents", "currency", "productId", "productSku", "productName"];
  const rows = res.mismatches.map((m) => [
    m.skuOrName,
    String(m.labelPriceCents),
    m.posPriceCents == null ? "" : String(m.posPriceCents),
    m.currency,
    m.productId ?? "",
    m.productSku ?? "",
    m.productName ?? "",
  ]);
  const esc = (s: string) => `"${s.replaceAll('"', '""')}"`;
  return [header.map(esc).join(","), ...rows.map((r) => r.map((c) => esc(String(c ?? ""))).join(","))].join("\n");
}

export function ShelfAuditPanel() {
  const [result, setResult] = useState<ShelfAuditResponse | null>(null);

  const mutation = useMutation({
    mutationFn: (asset: { readonly publicId: string; readonly url: string }) =>
      shelfLabelAudit({ asset }),
    onSuccess: (res) => setResult(res),
  });

  return (
    <div className="space-y-4 rounded-lg border border-border bg-surface p-4">
      <CloudinaryUploader
        purpose="shelf_audit"
        label={mutation.isPending ? "Auditing…" : "Upload shelf photo"}
        onUploaded={(asset) => mutation.mutate({ publicId: asset.publicId, url: asset.secureUrl })}
      />

      {mutation.error && isApiError(mutation.error) ? <InlineError error={mutation.error} /> : null}

      {result ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium">
              Mismatches: <span className="font-semibold">{result.mismatches.length}</span>
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                const csv = toCsv(result);
                const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "shelf-label-audit.csv";
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <Download size={14} aria-hidden="true" /> Export CSV
            </Button>
          </div>

          <div className="overflow-auto rounded-md border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-left">
                <tr>
                  <th className="px-3 py-2">Label</th>
                  <th className="px-3 py-2">Label price</th>
                  <th className="px-3 py-2">POS price</th>
                  <th className="px-3 py-2">Matched product</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {result.mismatches.map((m, i) => (
                  <tr key={`${m.skuOrName}-${i}`}>
                    <td className="px-3 py-2">{m.skuOrName}</td>
                    <td className="px-3 py-2 tabular-nums">
                      {m.currency} {(m.labelPriceCents / 100).toFixed(2)}
                    </td>
                    <td className="px-3 py-2 tabular-nums">
                      {m.posPriceCents == null ? "—" : `${m.currency} ${(m.posPriceCents / 100).toFixed(2)}`}
                    </td>
                    <td className="px-3 py-2">
                      {m.productName ? (
                        <span className="text-muted-foreground">
                          {m.productName} {m.productSku ? `(${m.productSku})` : ""}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">No match</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}

