"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { CloudinaryUploader } from "@/components/shared/cloudinary-uploader";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { scanIdForDob } from "@/lib/api/ai-age-restricted";

type AgeVerificationDialogProps = {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
  readonly onConfirm: (isoDob: string) => void;
  readonly minAgeHint?: number;
};

export function AgeVerificationDialog({
  open,
  onOpenChange,
  onConfirm,
  minAgeHint,
}: AgeVerificationDialogProps) {
  const [dob, setDob] = useState("");
  const scan = useMutation({
    mutationFn: (asset: { readonly publicId: string; readonly url: string }) =>
      scanIdForDob({ asset }),
    onSuccess: (res) => setDob(res.customerDob),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-5 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">Verify customer age</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            This sale includes age-restricted items
            {minAgeHint != null ? ` (minimum ${minAgeHint}+).` : "."} Enter the
            customer&apos;s date of birth.
          </Dialog.Description>
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium">Scan ID (optional)</p>
            <CloudinaryUploader
              purpose="id_scan"
              label={scan.isPending ? "Scanning…" : "Upload ID photo"}
              onUploaded={(asset) => scan.mutate({ publicId: asset.publicId, url: asset.secureUrl })}
            />
          </div>
          <div className="mt-4 space-y-2">
            <Label htmlFor="pos-dob">Date of birth</Label>
            <Input
              id="pos-dob"
              type="date"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              disabled={!dob}
              onClick={() => {
                onConfirm(dob);
                onOpenChange(false);
                setDob("");
              }}
            >
              Continue
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
