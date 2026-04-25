"use client";

import { useMutation } from "@tanstack/react-query";
import { Mic } from "lucide-react";
import { useState } from "react";
import type { UseFormSetValue } from "react-hook-form";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/shared/ui/dialog";
import { Textarea } from "@/components/shared/ui/textarea";
import { isApiError } from "@/lib/api/error";
import { voiceProductDraft } from "@/lib/api/voice-product";
import type { ProductCreateForm } from "@/schemas/catalog";

type Props = {
  readonly setValue: UseFormSetValue<ProductCreateForm>;
};

export function TranscriptProductDraftDialog({ setValue }: Props) {
  const [open, setOpen] = useState(false);
  const [transcript, setTranscript] = useState("");

  const mutation = useMutation({
    mutationFn: () => voiceProductDraft({ transcript }),
    onSuccess: (draft) => {
      setValue("name", draft.name, { shouldDirty: true });
      if (draft.sku) setValue("sku", draft.sku, { shouldDirty: true });
      if (draft.barcode) setValue("barcode", draft.barcode, { shouldDirty: true });
      if (draft.description) setValue("description", draft.description, { shouldDirty: true });
      setValue("priceCents", draft.priceCents, { shouldDirty: true });
      setValue("currency", draft.currency, { shouldDirty: true });
      // categoryName is returned for now; we don't auto-map it client-side in v1.
      toast.success("Draft applied. Review fields and create the product.");
      setOpen(false);
      setTranscript("");
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline">
          <Mic size={14} aria-hidden="true" /> Paste transcript
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Paste transcript</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          Paste what you said (or what a drive-thru mic captured). We’ll extract product fields and
          prefill the form.
        </p>
        <Textarea
          rows={6}
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder='e.g. "Create a new product: medium latte, 500 taka, under beverages. SKU LATTE-MED"'
          disabled={mutation.isPending}
        />
        {mutation.error && isApiError(mutation.error) ? (
          <InlineError error={mutation.error} />
        ) : null}
        <DialogFooter>
          <Button
            type="button"
            onClick={() => {
              const t = transcript.trim();
              if (!t) {
                toast.error("Paste a transcript first.");
                return;
              }
              mutation.mutate();
            }}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Extracting…" : "Extract draft"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

