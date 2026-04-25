"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";

import { AskReportingPanel } from "@/components/modules/ai/ask-reporting-panel";
import { Button } from "@/components/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/shared/ui/dialog";

/**
 * Floating action button that opens the Groq-powered natural-language
 * reporting chat. Mounted once from the authenticated layout so it's
 * reachable from every page in the app.
 */
export function AskFab() {
  const [open, setOpen] = useState<boolean>(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          size="icon-lg"
          className="fixed bottom-6 right-6 z-40 rounded-full shadow-lg"
          aria-label="Ask your data"
        >
          <Sparkles aria-hidden="true" />
        </Button>
      </DialogTrigger>
      <DialogContent className="flex max-h-[80vh] flex-col sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Ask reporting</DialogTitle>
        </DialogHeader>
        <div className="min-h-0 flex-1 overflow-hidden">
          <AskReportingPanel />
        </div>
      </DialogContent>
    </Dialog>
  );
}
