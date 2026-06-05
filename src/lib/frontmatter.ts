// Read/write Obsidian-style YAML frontmatter. Tolerant of missing or
// malformed frontmatter; preserves key order on render.

import yaml from 'js-yaml';

const DELIM = '---';

export interface Document {
  frontmatter: Record<string, unknown>;
  body: string;
}

export function parse(text: string): Document {
  const lines = text.split(/\r?\n/);
  if (lines.length === 0 || lines[0].trim() !== DELIM) {
    return { frontmatter: {}, body: text };
  }
  const end = lines.indexOf(DELIM, 1);
  if (end === -1) {
    return { frontmatter: {}, body: text };
  }
  const fmText = lines.slice(1, end).join('\n');
  let body = lines.slice(end + 1).join('\n').replace(/^\n+/, '');

  let fm: Record<string, unknown> = {};
  try {
    const loaded = yaml.load(fmText);
    if (loaded && typeof loaded === 'object' && !Array.isArray(loaded)) {
      fm = loaded as Record<string, unknown>;
    }
  } catch {
    body = `<!-- frontmatter could not be parsed -->\n${fmText}\n\n${body}`;
  }
  return { frontmatter: fm, body };
}

export function render(doc: Document): string {
  const fmText = yaml.dump(doc.frontmatter, {
    sortKeys: false,
    lineWidth: -1,
    quotingType: '"',
  }).replace(/\n$/, '');
  const body = doc.body.trim() ? doc.body.replace(/\s+$/, '') + '\n' : '';
  return `${DELIM}\n${fmText}\n${DELIM}\n\n${body}`;
}
