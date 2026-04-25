"use client";

import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { uploadImageToCloudinary, type UploadedAsset, MAX_UPLOAD_BYTES } from "@/lib/uploads/cloudinary";

export function CloudinaryUploader(props: {
  readonly purpose:
    | "invoice_ocr"
    | "id_scan"
    | "shelf_audit"
    | "planogram"
    | "jewelry"
    | "cafeteria";
  readonly onUploaded: (asset: UploadedAsset) => void;
  readonly label?: string;
}) {
  const { purpose, onUploaded, label = "Upload photo" } = props;
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  return (
    <div className="space-y-2">
      <label className="inline-flex">
        <input
          type="file"
          accept="image/*"
          className="sr-only"
          disabled={busy}
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setError(null);
            if (f.size > MAX_UPLOAD_BYTES) {
              setError("File too large (max 95MB).");
              return;
            }
            try {
              setBusy(true);
              const asset = await uploadImageToCloudinary({ purpose, file: f });
              onUploaded(asset);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Upload failed.");
            } finally {
              setBusy(false);
              e.target.value = "";
            }
          }}
        />
        <Button asChild type="button" disabled={busy} variant="outline">
          <span>{busy ? "Uploading…" : label}</span>
        </Button>
      </label>
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}

