// Split a free-text "who" or "where" field into individual names.
// Separators: commas, semicolons, "and", ampersands, slashes.
// Dedupes case-insensitively but keeps the first-seen casing.

const SPLIT = /\s*(?:,|;|\band\b|&|\/)\s*/i;

export function splitNouns(text: string): string[] {
  if (!text || !text.trim()) return [];
  const parts = text.split(SPLIT).map((p) => p.trim()).filter(Boolean);
  const seen = new Map<string, string>();
  for (const p of parts) {
    const key = p.toLowerCase();
    if (!seen.has(key)) seen.set(key, p);
  }
  return [...seen.values()];
}
