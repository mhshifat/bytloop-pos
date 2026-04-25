"use client";

import { useEffect } from "react";

type Modifier = "ctrl" | "meta" | "shift" | "alt";

type ShortcutDef = {
  readonly key: string;
  readonly modifiers?: readonly Modifier[];
  readonly handler: (event: KeyboardEvent) => void;
  readonly enabled?: boolean;
  readonly allowInInputs?: boolean;
};

function matches(event: KeyboardEvent, def: ShortcutDef): boolean {
  if (event.key.toLowerCase() !== def.key.toLowerCase()) return false;
  const mods = new Set(def.modifiers ?? []);
  if (mods.has("ctrl") !== event.ctrlKey) return false;
  if (mods.has("meta") !== event.metaKey) return false;
  if (mods.has("shift") !== event.shiftKey) return false;
  if (mods.has("alt") !== event.altKey) return false;
  return true;
}

function isTypingContext(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return target.isContentEditable;
}

export function useKeyboardShortcut(defs: readonly ShortcutDef[]): void {
  useEffect(() => {
    const handler = (event: KeyboardEvent): void => {
      for (const def of defs) {
        if (def.enabled === false) continue;
        if (!def.allowInInputs && isTypingContext(event.target)) continue;
        if (!matches(event, def)) continue;
        event.preventDefault();
        def.handler(event);
        return;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [defs]);
}
