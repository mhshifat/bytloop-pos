/**
 * Money formatting — the only place in the UI that turns minor-unit integers
 * into human-visible currency strings. Always pair cents with the currency
 * they were priced in (order.currency, product.currency, …) rather than
 * globally reinterpreting with the active tenant currency — mixing those
 * two is the subtle bug that burned us last time.
 *
 * Locale intentionally pinned to the browser locale so numbers group as
 * the user expects; symbols come from the ISO code so we get ৳ / $ / €
 * without per-currency conditionals.
 */

export type FormatMoneyOptions = {
  readonly locale?: string;
  readonly showSymbol?: boolean;
};

export function formatMoney(
  cents: number,
  currency: string,
  opts: FormatMoneyOptions = {},
): string {
  const { locale, showSymbol = true } = opts;
  const amount = cents / 100;
  const code = currency?.toUpperCase() || "USD";

  if (!showSymbol) {
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: code,
      currencyDisplay: "narrowSymbol",
    }).format(amount);
  } catch {
    return `${code} ${amount.toFixed(2)}`;
  }
}
