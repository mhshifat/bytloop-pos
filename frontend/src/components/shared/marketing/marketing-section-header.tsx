type SectionHeaderProps = {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly align?: "center" | "left";
};

export function SectionHeader({
  eyebrow,
  title,
  description,
  align = "center",
}: SectionHeaderProps) {
  return (
    <div
      className={align === "left" ? "max-w-2xl text-left" : "mx-auto max-w-3xl text-center"}
    >
      <p className="mkt-eyebrow text-sm font-semibold uppercase tracking-[0.2em] text-primary">
        {eyebrow}
      </p>
      <h2 className="mt-3 text-3xl font-bold tracking-tight text-zinc-50 sm:text-4xl md:text-5xl">
        {title}
      </h2>
      <p className="mt-4 text-pretty text-base leading-relaxed text-zinc-300 sm:text-lg">
        {description}
      </p>
    </div>
  );
}
