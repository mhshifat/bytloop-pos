"use client";

import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useState } from "react";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { askReporting, type NLAnswer } from "@/lib/api/ai-reports";
import { isApiError } from "@/lib/api/error";

type HistoryEntry = {
  readonly id: string;
  readonly answer: NLAnswer;
};

export function AskReportingPanel() {
  const [question, setQuestion] = useState<string>("");
  const [history, setHistory] = useState<readonly HistoryEntry[]>([]);

  const ask = useMutation({
    mutationFn: (q: string) => askReporting(q),
    onSuccess: (data) => {
      setHistory((prev) => [
        { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, answer: data },
        ...prev,
      ]);
      setQuestion("");
    },
  });

  const submit = (): void => {
    const trimmed = question.trim();
    if (!trimmed || ask.isPending) return;
    ask.mutate(trimmed);
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-primary" aria-hidden="true" />
        <p className="text-sm font-medium">Ask your data</p>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="flex items-center gap-2"
      >
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder='e.g. "What were our top products last month?"'
          className="flex-1"
          disabled={ask.isPending}
          autoFocus
        />
        <Button type="submit" disabled={ask.isPending || !question.trim()}>
          {ask.isPending ? "Asking…" : "Ask"}
        </Button>
        {history.length > 0 ? (
          <Button
            type="button"
            variant="ghost"
            onClick={() => setHistory([])}
            disabled={ask.isPending}
          >
            Clear
          </Button>
        ) : null}
      </form>

      {ask.error && isApiError(ask.error) ? (
        <InlineError error={ask.error} />
      ) : null}

      <div className="flex-1 space-y-4 overflow-y-auto pr-1">
        {history.length === 0 && !ask.isPending ? (
          <p className="text-sm text-muted-foreground">
            Ask anything about your orders, customers, or products — the AI will
            answer in plain English, with the data behind it.
          </p>
        ) : null}
        {history.map((entry) => (
          <AnswerBlock key={entry.id} answer={entry.answer} />
        ))}
      </div>
    </div>
  );
}

function AnswerBlock({ answer }: { readonly answer: NLAnswer }) {
  const [showSql, setShowSql] = useState<boolean>(false);
  const rows = answer.rows;
  const columns = rows.length > 0 ? Object.keys(rows[0] as object) : [];

  return (
    <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Q
        </p>
        <p className="text-sm font-medium">{answer.question}</p>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          A
        </p>
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {answer.answer}
        </p>
      </div>
      {rows.length > 0 ? (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((c) => (
                  <TableHead key={c}>{c}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, i) => (
                <TableRow key={i}>
                  {columns.map((c) => (
                    <TableCell key={c} className="tabular-nums">
                      {formatCell((row as Record<string, unknown>)[c])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}
      {answer.sql ? (
        <div>
          <Button
            type="button"
            variant="ghost"
            size="xs"
            onClick={() => setShowSql((v) => !v)}
          >
            {showSql ? "Hide SQL" : "See SQL"}
          </Button>
          {showSql ? (
            <pre className="mt-2 overflow-x-auto rounded-md border border-border bg-muted/30 p-3 text-xs">
              {answer.sql}
            </pre>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}
