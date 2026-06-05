// Save a new note, fill in a stub. All vault writes funnel through here.

import * as gh from './github';
import * as fm from './frontmatter';
import { splitNouns } from './parsing';
import {
  byType, emptyFrontmatter, findField, type Field, type TypeName,
} from './templates';
import {
  displayToWikilink, isBlank, memoryPath, normalizeName, pathFor, todayIso,
} from './vault';

export interface MemoryInput {
  title: string;
  when: string;        // ISO date string; blank → today
  who: string;
  where: string;
  why: string;
  story: string;
  // Optional photo bytes to upload into vault/Photos/ before saving the memory
  photoBytes?: Uint8Array;
  photoExt?: string;   // e.g. ".jpg"
}

export interface SaveResult {
  memoryPath: string;
  createdPaths: string[];
  updatedPaths: string[];
}

function photoId(): string {
  const a = new Uint8Array(3);
  crypto.getRandomValues(a);
  return [...a].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function saveMemory(
  token: string,
  user: gh.GitHubUser,
  input: MemoryInput,
): Promise<SaveResult> {
  const created: string[] = [];
  const updated: string[] = [];
  const when = (input.when || '').trim() || todayIso();

  // 1. Upload photo if provided.
  let photoFilename = '';
  if (input.photoBytes && input.photoBytes.byteLength > 0) {
    const ext = (input.photoExt || '.jpg').toLowerCase();
    photoFilename = `${when}_${photoId()}${ext}`;
    const photoPath = `Photos/${photoFilename}`;
    await gh.writeBinary(token, photoPath, input.photoBytes,
      `Add photo for "${input.title.trim() || 'memory'}"`, user);
    created.push(photoPath);
  }

  // 2. Create stub files for new people and places.
  const peopleNames = splitNouns(input.who);
  const placeNames = splitNouns(input.where);

  for (const name of peopleNames) {
    const [path, didCreate] = await ensureStub(token, user, 'Person', name);
    (didCreate ? created : updated).push(path);
  }
  for (const name of placeNames) {
    const [path, didCreate] = await ensureStub(token, user, 'Place', name);
    (didCreate ? created : updated).push(path);
  }

  // 3. Write the memory file itself.
  const path = memoryPath(input.title.trim() || 'Untitled', when);
  const tmpl = byType('Memory');
  const frontmatterObj: Record<string, unknown> = emptyFrontmatter(tmpl);
  frontmatterObj.title = input.title.trim();
  frontmatterObj.when = when;
  frontmatterObj.who = peopleNames.map(displayToWikilink);
  frontmatterObj.where = placeNames.map(displayToWikilink);
  frontmatterObj.why = input.why.trim();
  frontmatterObj.photo = photoFilename;
  frontmatterObj.story = input.story.trim();

  const bodyLines: string[] = [];
  if (photoFilename) {
    bodyLines.push(`![[${photoFilename}]]`, '');
  }
  if (input.story.trim()) {
    bodyLines.push(input.story.trim());
  }
  const doc: fm.Document = { frontmatter: frontmatterObj, body: bodyLines.join('\n') };
  await gh.writeFile(token, path, fm.render(doc),
    `Add memory: ${input.title.trim() || 'Untitled'}`, user);
  created.push(path);

  return { memoryPath: path, createdPaths: created, updatedPaths: updated };
}

async function ensureStub(
  token: string,
  user: gh.GitHubUser,
  type: TypeName,
  displayName: string,
): Promise<[string, boolean]> {
  const path = pathFor(type, displayName);
  const existing = await gh.readFile(token, path);
  if (existing) return [path, false];

  const tmpl = byType(type);
  const fmData = emptyFrontmatter(tmpl);
  fmData.name = normalizeName(displayName);
  const doc: fm.Document = { frontmatter: fmData, body: '' };
  await gh.writeFile(token, path, fm.render(doc),
    `Create ${type} stub: ${normalizeName(displayName)}`, user);
  return [path, true];
}

// ── Fill-blanks flow ────────────────────────────────────────────────────────

export interface RecordEdit {
  type: TypeName;
  path: string;
  inputs: Record<string, string>;   // field.key → raw string from the form
}

export async function saveRecord(
  token: string,
  user: gh.GitHubUser,
  edit: RecordEdit,
): Promise<SaveResult> {
  const tmpl = byType(edit.type);
  const existing = await gh.readFile(token, edit.path);
  const doc = existing ? fm.parse(existing.text) : { frontmatter: emptyFrontmatter(tmpl), body: '' };

  const created: string[] = [];
  const updated: string[] = [];

  for (const [key, raw] of Object.entries(edit.inputs)) {
    const field = findField(tmpl, key);
    if (!field) continue;
    const [value, names] = coerce(field, raw);
    if (value !== undefined) doc.frontmatter[key] = value;
    if (field.targetType && names.length) {
      for (const n of names) {
        const [stubPath, didCreate] = await ensureStub(token, user, field.targetType, n);
        (didCreate ? created : updated).push(stubPath);
      }
    }
  }

  await gh.writeFile(token, edit.path, fm.render(doc),
    `Update ${edit.type}: ${edit.path}`, user, existing?.sha);
  updated.push(edit.path);

  return { memoryPath: edit.path, createdPaths: created, updatedPaths: updated };
}

function coerce(field: Field, raw: string): [unknown, string[]] {
  const trimmed = (raw ?? '').trim();
  switch (field.kind) {
    case 'link':
      if (!trimmed) return ['', []];
      return [displayToWikilink(trimmed), [trimmed]];
    case 'links': {
      const names = splitNouns(trimmed);
      return [names.map(displayToWikilink), names];
    }
    case 'number': {
      if (!trimmed) return ['', []];
      const n = Number(trimmed);
      return [Number.isFinite(n) ? n : trimmed, []];
    }
    default:
      return [trimmed, []];
  }
}

// ── Incomplete listing for fill-blanks ──────────────────────────────────────

export async function listIncomplete(
  token: string,
  type: TypeName,
): Promise<{ path: string; name: string }[]> {
  const tmpl = byType(type);
  const files = await gh.listDir(token, tmpl.folder);
  const out: { path: string; name: string }[] = [];
  for (const f of files) {
    if (!f.path.endsWith('.md')) continue;
    const content = await gh.readFile(token, f.path);
    if (!content) continue;
    const { frontmatter } = fm.parse(content.text);
    const incomplete = tmpl.fields.some((field) => isBlank(frontmatter[field.key]));
    if (incomplete) {
      const stem = f.path.split('/').pop()!.replace(/\.md$/, '');
      out.push({ path: f.path, name: stem });
    }
  }
  return out;
}
