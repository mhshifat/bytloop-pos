"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Keyboard } from "lucide-react";
import { useState } from "react";

import { useKeyboardShortcut } from "@/lib/hooks/use-keyboard-shortcut";

type Shortcut = { readonly keys: string; readonly description: string };

const SHORTCUTS: readonly { readonly scope: string; readonly items: readonly Shortcut[] }[] = [
  {
    scope: "Global",
    items: [{ keys: "?", description: "Show this help" }],
  },
  {
    scope: "POS terminal",
    items: [
      { keys: "F8", description: "Charge current sale" },
      { keys: "F9", description: "Clear current sale" },
      { keys: "/", description: "Focus product search" },
      { keys: "Esc", description: "Clear search" },
      { keys: "Enter (in search)", description: "Auto-add barcode / SKU match" },
    ],
  },
];

export function ShortcutsHelp() {
  const [open, setOpen] = useState(false);

  useKeyboardShortcut([
    { key: "?", modifiers: ["shift"], handler: () => setOpen((v) => !v) },
  ]);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label="Keyboard shortcuts"
          className="hidden h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-white/5 hover:text-foreground md:flex"
        >
          <Keyboard size={14} />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Keyboard shortcuts</Dialog.Title>
          <Dialog.Description className="mt-1 text-xs text-muted-foreground">
            Press <kbd className="font-mono">?</kbd> at any time to toggle this panel.
          </Dialog.Description>
          <div className="mt-4 space-y-4 text-sm">
            {SHORTCUTS.map((group) => (
              <div key={group.scope}>
                <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">
                  {group.scope}
                </p>
                <ul className="space-y-1.5">
                  {group.items.map((item) => (
                    <li
                      key={item.keys}
                      className="flex items-center justify-between"
                    >
                      <span className="text-muted-foreground">{item.description}</span>
                      <kbd className="rounded bg-white/10 px-2 py-0.5 font-mono text-xs">
                        {item.keys}
                      </kbd>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
