/**
 * Schemas for each type of markdown record in the vault.
 *
 * Each Template lists its fields in display importance order (most important
 * first, least important last). Field.kind controls how the value is rendered
 * in the UI and stored in YAML frontmatter.
 *
 * Same shape as the Python `templates.py` from the Streamlit version so a
 * vault populated by either app reads identically.
 */

export type Kind =
  | 'text'      // single-line string
  | 'longtext'  // multi-line string
  | 'date'      // ISO date YYYY-MM-DD
  | 'url'       // a URL string
  | 'link'      // single [[wikilink]]
  | 'links'     // list of [[wikilinks]]
  | 'number';   // numeric

export interface Field {
  key: string;            // YAML key
  label: string;          // displayed label
  kind: Kind;
  targetType?: TypeName;  // for link/links: which Template type
  hint?: string;          // optional explicit hint; falls back to kind default
}

export type TypeName = 'Person' | 'Place' | 'Memory';

export interface Template {
  type: TypeName;
  folder: string;         // vault subfolder, e.g. "People"
  fields: readonly Field[];
}

const DEFAULT_HINTS: Record<Kind, string> = {
  text: '',
  longtext: '',
  date: 'YYYY-MM-DD',
  url: 'Paste a full URL',
  link: 'One name',
  links: 'Separate multiple names with commas',
  number: 'A number',
};

export function hintFor(field: Field): string {
  return field.hint ?? DEFAULT_HINTS[field.kind];
}

export const PERSON: Template = {
  type: 'Person',
  folder: 'People',
  fields: [
    { key: 'name', label: 'Name', kind: 'text', hint: 'First and last, e.g. Mary Smith' },
    { key: 'lives_in', label: 'Lives in', kind: 'link', targetType: 'Place', hint: 'A city, town, or specific place' },
    { key: 'birthdate', label: 'Birthdate', kind: 'date' },
    { key: 'birthplace', label: 'Birthplace', kind: 'link', targetType: 'Place' },
    { key: 'parents', label: 'Parents', kind: 'links', targetType: 'Person', hint: 'Two names, separated by a comma' },
    { key: 'siblings', label: 'Siblings', kind: 'links', targetType: 'Person' },
    { key: 'partner', label: 'Partner', kind: 'link', targetType: 'Person' },
    { key: 'children', label: 'Children', kind: 'links', targetType: 'Person' },
    { key: 'core_memories', label: 'Core Memories', kind: 'links', targetType: 'Memory', hint: 'Reference existing memories by title' },
    { key: 'paternal_grandparents', label: 'Paternal Grandparents', kind: 'links', targetType: 'Person', hint: 'Two names, separated by a comma' },
    { key: 'maternal_grandparents', label: 'Maternal Grandparents', kind: 'links', targetType: 'Person', hint: 'Two names, separated by a comma' },
    { key: 'extended_family', label: 'Extended Family', kind: 'links', targetType: 'Person', hint: 'Aunts, uncles, cousins — comma-separated' },
    { key: 'occupation', label: 'Occupation', kind: 'text' },
    { key: 'degrees', label: 'Degrees', kind: 'longtext', hint: 'One per line, e.g. BA English — Boston U — 2004' },
    { key: 'past_addresses', label: 'Past Addresses', kind: 'links', targetType: 'Place', hint: 'Cities or places they\'ve lived' },
    { key: 'friends', label: 'Friends', kind: 'links', targetType: 'Person' },
    { key: 'employers', label: 'Employers', kind: 'longtext', hint: 'One per line, e.g. Acme Corp — 2010 to 2015' },
  ],
};

export const PLACE: Template = {
  type: 'Place',
  folder: 'Places',
  fields: [
    { key: 'name', label: 'Name', kind: 'text', hint: 'What you\'d call this place in conversation' },
    { key: 'maps_link', label: 'Google Maps link', kind: 'url', hint: 'Paste a Google Maps URL' },
    { key: 'latitude', label: 'Latitude', kind: 'number', hint: 'Decimal degrees, e.g. 42.3601' },
    { key: 'longitude', label: 'Longitude', kind: 'number', hint: 'Decimal degrees, e.g. -71.0589' },
    { key: 'address', label: 'Address', kind: 'text' },
    { key: 'notes', label: 'Notes', kind: 'longtext' },
  ],
};

export const MEMORY: Template = {
  type: 'Memory',
  folder: 'Memories',
  fields: [
    { key: 'title', label: 'Title (what)', kind: 'text', hint: 'A short title for this memory' },
    { key: 'when', label: 'When', kind: 'date' },
    { key: 'who', label: 'Who', kind: 'links', targetType: 'Person', hint: 'People present — separate multiple with commas' },
    { key: 'where', label: 'Where', kind: 'links', targetType: 'Place', hint: 'Places involved — separate multiple with commas' },
    { key: 'why', label: 'Why', kind: 'longtext', hint: 'Why does this moment matter?' },
    { key: 'photo', label: 'Photo', kind: 'text' },
    { key: 'story', label: 'Story', kind: 'longtext', hint: 'Tell it in your own words' },
  ],
};

export const TEMPLATES: readonly Template[] = [PERSON, PLACE, MEMORY];

export function byType(type: TypeName | string): Template {
  const lower = type.toLowerCase();
  const found = TEMPLATES.find((t) => t.type.toLowerCase() === lower);
  if (!found) throw new Error(`Unknown template type: ${type}`);
  return found;
}

export function blankValue(kind: Kind): unknown {
  return kind === 'links' ? [] : '';
}

export function emptyFrontmatter(template: Template): Record<string, unknown> {
  const out: Record<string, unknown> = { type: template.type.toLowerCase() };
  for (const f of template.fields) out[f.key] = blankValue(f.kind);
  return out;
}

export function findField(template: Template, key: string): Field | undefined {
  return template.fields.find((f) => f.key === key);
}
