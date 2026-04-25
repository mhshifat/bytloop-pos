"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { Badge } from "@/components/shared/ui/badge";
import { getAiReportsStatus } from "@/lib/api/ai-reports";

export function AiStatusBadge() {
  const { data, isLoading } = useQuery({
    queryKey: ["ai", "reports", "status"],
    queryFn: () => getAiReportsStatus(),
    retry: false,
  });

  if (isLoading) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        <Sparkles aria-hidden="true" />
        AI status…
      </Badge>
    );
  }

  if (!data) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        <Sparkles aria-hidden="true" />
        AI status unavailable
      </Badge>
    );
  }

  const groqLabel = data.enabled ? "Groq: on" : "Groq: off";
  const groqClass = data.enabled
    ? "border-emerald-500/50 text-emerald-400"
    : "border-amber-500/50 text-amber-400";

  const prophetLabel = data.prophetAvailable ? "Prophet: on" : "Prophet: off";
  const prophetClass = data.prophetAvailable
    ? "border-emerald-500/50 text-emerald-400"
    : "border-amber-500/50 text-amber-400";

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="outline" className={groqClass}>
        <Sparkles aria-hidden="true" />
        {groqLabel}
      </Badge>
      <Badge variant="outline" className={prophetClass}>
        {prophetLabel}
      </Badge>
    </div>
  );
}

