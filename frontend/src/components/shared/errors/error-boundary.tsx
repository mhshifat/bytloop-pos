"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { ulid } from "ulid";

import { CopyIdButton } from "./copy-id-button";

type State = {
  readonly correlationId: string | null;
};

type Props = {
  readonly children: ReactNode;
  readonly fallback?: (props: { correlationId: string; reset: () => void }) => ReactNode;
};

/**
 * React error boundary with a client-generated correlation ID. The ID is
 * logged to the console so a developer can grep for it in telemetry.
 *
 * Use Next.js `error.tsx` files for route-level boundaries; use this component
 * around third-party widgets or isolated interactive regions.
 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { correlationId: null };

  static getDerivedStateFromError(): State {
    return { correlationId: `client_${ulid()}` };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught", {
      correlationId: this.state.correlationId,
      error,
      info,
    });
  }

  private readonly reset = (): void => {
    this.setState({ correlationId: null });
  };

  override render(): ReactNode {
    const { correlationId } = this.state;
    if (!correlationId) return this.props.children;
    if (this.props.fallback) return this.props.fallback({ correlationId, reset: this.reset });

    return (
      <div
        role="alert"
        className="m-4 flex flex-col items-start gap-3 rounded-lg border border-red-500/30 bg-red-500/5 p-6"
      >
        <h2 className="text-lg font-semibold">Something went wrong</h2>
        <p className="text-sm text-[var(--color-muted)]">
          An unexpected error interrupted this section. You can copy the ID and
          share it with support to speed up the fix.
        </p>
        <CopyIdButton correlationId={correlationId} />
        <button
          type="button"
          onClick={this.reset}
          className="mt-2 rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm"
        >
          Try again
        </button>
      </div>
    );
  }
}
