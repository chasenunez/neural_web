/**
 * Parse 5W free-text into normalized noun lists.
 *
 * Identical semantics to Python `parsing.py`: split on commas, semicolons,
 * `and`, ampersands, or slashes; trim; dedupe case-insensitively while
 * preserving the first-seen casing.
 */

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
