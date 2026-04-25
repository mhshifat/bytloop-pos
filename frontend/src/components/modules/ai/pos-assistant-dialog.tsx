"use client";

import { useMutation } from "@tanstack/react-query";
import { Bot, Send } from "lucide-react";
import { useMemo, useState } from "react";

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
import { Input } from "@/components/shared/ui/input";
import { assistantChat } from "@/lib/api/ai-assistant";
import { isApiError } from "@/lib/api/error";

type ChatMsg = {
  readonly role: "user" | "assistant";
  readonly content: string;
};

function renderToolResult(tool: string | null, toolResult: Record<string, unknown> | null): string | null {
  if (!tool || !toolResult) return null;
  if (tool === "search_products") {
    const items = toolResult.items as Array<any> | undefined;
    if (!items?.length) return "No matches.";
    return items
      .slice(0, 6)
      .map((p) => `- ${String(p.name)} (${String(p.sku)})`)
      .join("\n");
  }
  if (tool === "list_top_products") {
    const items = toolResult.items as Array<any> | undefined;
    if (!items?.length) return "No data.";
    return items
      .slice(0, 6)
      .map((p) => `- ${String(p.name)} (${String(p.unitsSold ?? "")} sold)`)
      .join("\n");
  }
  if (tool === "check_discount_code") {
    const code = String((toolResult as any).code ?? "");
    const valid = Boolean((toolResult as any).valid);
    return valid ? `Code ${code} looks valid.` : `Code ${code} not found.`;
  }
  return null;
}

export function PosAssistantDialog() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);

  const mutation = useMutation({
    mutationFn: (message: string) => assistantChat({ message }),
    onSuccess: (res, message) => {
      const toolText = renderToolResult(res.tool, res.toolResult);
      setMessages((m) => [
        ...m,
        { role: "user", content: message },
        { role: "assistant", content: toolText ? `${res.reply}\n\n${toolText}` : res.reply },
      ]);
      setInput("");
    },
  });

  const last = useMemo(() => messages[messages.length - 1], [messages]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm">
          <Bot size={14} aria-hidden="true" /> Assistant
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>POS assistant</DialogTitle>
        </DialogHeader>
        <div className="max-h-[52vh] overflow-auto rounded-md border border-border bg-background p-3 text-sm">
          {messages.length === 0 ? (
            <p className="text-muted-foreground">
              Try: “find vegan options”, “check discount code SAVE10”, “what’s our best-selling coffee?”
            </p>
          ) : (
            <div className="space-y-3">
              {messages.map((m, i) => (
                <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                  <div
                    className={
                      m.role === "user"
                        ? "ml-auto inline-block max-w-[90%] rounded-md bg-primary px-3 py-2 text-primary-foreground"
                        : "inline-block max-w-[90%] whitespace-pre-wrap rounded-md bg-muted px-3 py-2 text-foreground"
                    }
                  >
                    {m.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {mutation.error && isApiError(mutation.error) ? <InlineError error={mutation.error} /> : null}
        <DialogFooter className="sm:justify-between">
          <p className="hidden text-xs text-muted-foreground sm:block">
            {last?.role === "assistant" ? "Tip: be specific (product name, code, time window)." : " "}
          </p>
          <div className="flex w-full gap-2 sm:w-auto">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask…"
              disabled={mutation.isPending}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const msg = input.trim();
                  if (!msg) return;
                  mutation.mutate(msg);
                }
              }}
              className="w-full sm:w-80"
            />
            <Button
              type="button"
              disabled={mutation.isPending}
              onClick={() => {
                const msg = input.trim();
                if (!msg) return;
                mutation.mutate(msg);
              }}
            >
              <Send size={14} aria-hidden="true" /> Send
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

