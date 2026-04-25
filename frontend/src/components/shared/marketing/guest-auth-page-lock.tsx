"use client";

import { useLayoutEffect } from "react";

const ATTR = "data-guest-auth";

/**
 * Prevents a useless window-level scrollbar on auth screens (subpixel dvh, flex, etc.)
 * by clamping the document. The form area inside GuestAuthShell still scrolls when needed.
 */
export function GuestAuthPageLock() {
  useLayoutEffect(() => {
    document.documentElement.setAttribute(ATTR, "true");
    return () => {
      document.documentElement.removeAttribute(ATTR);
    };
  }, []);

  return null;
}
