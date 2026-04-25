/**
 * Best-effort parse of one line of text from a retail scale.
 * Returns mass in **grams** or `null` if no confident match.
 * Many devices send: "   0.255 kg  ", "ST,GS,0.500,kg", "0.5 lb", "1250" (1.25 kg).
 */
export function parseScaleLineToGrams(line: string): number | null {
  const t = line.replace(/\0/g, "").trim();
  if (t.length === 0) return null;

  const low = t.toLowerCase();

  // "1.25 kg" / "1,25 kg" (EU decimal comma)
  const kg = /([\d.,]+)\s*kg\b/i.exec(low);
  if (kg) {
    const n = parseNum(kg[1] ?? "");
    if (n != null && n > 0 && n < 1000) {
      return Math.round(n * 1000);
    }
  }

  // "500 g" / "500.5 g" — avoid matching "kg"
  const g = /([\d.,]+)\s*g\b(?!a)/i.exec(low);
  if (g) {
    const n = parseNum(g[1] ?? "");
    if (n != null && n > 0 && n < 1_000_000) {
      return Math.round(n);
    }
  }

  // pounds → grams (rare in BD but common in US)
  const lb = /([\d.,]+)\s*(?:lb|lbs|#)\b/i.exec(low);
  if (lb) {
    const n = parseNum(lb[1] ?? "");
    if (n != null && n > 0) {
      return Math.round(n * 453.592);
    }
  }

  // CSV-style: look for a numeric field before "kg" token in chunks
  const parts = t.split(/[,;|\t]+/).map((s) => s.trim());
  for (const p of parts) {
    const m = /([\d.,]+)/.exec(p);
    if (m) {
      const n = parseNum(m[1] ?? "");
      if (n == null) continue;
      if (/kg/i.test(p) && n < 1000) return Math.round(n * 1000);
    }
  }

  // Isolated number: treat as **grams** if 1..999999, else as kg if 0.001..99.999
  const only = /^([+-]?[\d.,]+)\s*$/i.exec(t);
  if (only) {
    const n = parseNum(only[1] ?? "");
    if (n == null) return null;
    if (n >= 1 && n <= 999_999) return Math.round(n);
    if (n > 0 && n < 100) return Math.round(n * 1000);
  }

  return null;
}

function parseNum(s: string): number | null {
  const t = s.replace(/,/g, ".");
  const m = t.match(/-?[\d.]+/);
  if (!m) return null;
  const n = Number(m[0]);
  return Number.isFinite(n) ? n : null;
}
