import type { FieldError } from "react-hook-form";

type FieldErrorProps = {
  readonly error: FieldError | undefined;
  readonly id?: string;
};

export function FieldErrorText({ error, id }: FieldErrorProps) {
  if (!error?.message) return null;
  return (
    <p id={id} role="alert" className="mt-1 text-xs text-red-400">
      {error.message}
    </p>
  );
}
