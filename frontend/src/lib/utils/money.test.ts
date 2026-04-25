import { describe, expect, it } from "vitest";

import { formatMoney } from "./money";

describe("formatMoney", () => {
  it("formats cents as the given currency", () => {
    // Intl formatting varies slightly across Node locales; check the parts
    // that are stable (digits + grouping + decimals).
    const result = formatMoney(123_45, "USD", { locale: "en-US" });
    expect(result).toContain("123.45");
  });

  it("falls back when an unknown currency is provided", () => {
    const result = formatMoney(1000, "ZZZ", { locale: "en-US" });
    expect(result).toMatch(/10\.00/);
  });

  it("respects showSymbol=false", () => {
    const result = formatMoney(9999, "USD", { locale: "en-US", showSymbol: false });
    expect(result).toBe("99.99");
  });

  it("uppercases lowercase currency codes", () => {
    const result = formatMoney(500, "usd", { locale: "en-US" });
    expect(result).toContain("5.00");
  });

  it("handles zero cents", () => {
    expect(formatMoney(0, "USD", { locale: "en-US" })).toContain("0.00");
  });

  it("handles negative cents (refunds)", () => {
    const result = formatMoney(-1500, "USD", { locale: "en-US" });
    expect(result).toContain("15.00");
    expect(result).toContain("-");
  });
});
