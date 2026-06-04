/**
 * Vault path helpers and slug rules.
 *
 * The vault is a GitHub repository whose root contains People/, Places/,
 * Memories/, Photos/, and Templates/ folders (plain markdown + images).
 * This module only does path math — actual I/O lives in `github.ts`.
 */

import { byType, type TypeName } from './templates';

const BAD_FILE_CHARS = /[\\/:*?"<>|]/g;
const MULTI_SPACE = /\s+/g;

/**
 * Turn a free-form display name into a stable filename stem.
 *
 * - Strip surrounding whitespace
 * - Collapse internal whitespace
 * - Remove characters illegal on common filesystems
 * - Strip apostrophes (so "Grandma's House" → "Grandmas House")
 * - Title-case (so "mary smith" and "Mary Smith" collide)
 */
export function normalizeName(name: string): string {
  let s = name.trim();
  s = s.replace(/['’]/g, '');
  s = s.replace(BAD_FILE_CHARS, '');
  s = s.replace(MULTI_SPACE, ' ');
  if (!s) return s;
  return s
    .split(' ')
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(' ');
}

export function displayToWikilink(display: string): string {
  return `[[${normalizeName(display)}]]`;
}

export function wikilinksToDisplays(values: readonly unknown[]): string[] {
  const out: string[] = [];
  for (const v of values) {
    if (typeof v !== 'string') continue;
    let s = v.trim();
    if (s.startsWith('[[') && s.endsWith(']]')) s = s.slice(2, -2);
    if (s) out.push(s);
  }
  return out;
}

export function folderFor(type: TypeName): string {
  return byType(type).folder;
}

export function pathFor(type: TypeName, displayName: string): string {
  return `${folderFor(type)}/${normalizeName(displayName)}.md`;
}

export function memoryPath(title: string, dateIso: string): string {
  const safe = normalizeName(title) || 'Untitled';
  return `Memories/${dateIso} ${safe}.md`;
}

export function isBlank(value: unknown): boolean {
  if (value == null) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value as object).length === 0;
  return false;
}

export function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
