"use client";

import { useQuery } from "@tanstack/react-query";

import { translateText } from "@/lib/api/translate";

export function useTranslatedText(sourceText: string | null | undefined, targetLocale: string) {
  const text = (sourceText ?? "").trim();
  const locale = (targetLocale || "en").toLowerCase();

  return useQuery({
    queryKey: ["ai", "translate", { text, locale }],
    queryFn: async () => {
      if (!text) return "";
      if (locale === "en" || locale.startsWith("en-")) return text;
      const res = await translateText({ sourceText: text, targetLocale: locale });
      return res.translatedText;
    },
    enabled: Boolean(text),
    staleTime: 1000 * 60 * 60 * 24 * 30,
  });
}

