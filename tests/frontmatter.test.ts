import { describe, expect, it } from 'vitest';
import { parse, render } from '../src/lib/frontmatter';

describe('frontmatter', () => {
  it('round-trips simple data', () => {
    const doc = { frontmatter: { title: 'Hello', tags: ['a', 'b'] }, body: 'Body.\n' };
    const parsed = parse(render(doc));
    expect(parsed.frontmatter.title).toBe('Hello');
    expect(parsed.frontmatter.tags).toEqual(['a', 'b']);
    expect(parsed.body.trim()).toBe('Body.');
  });

  it('handles missing frontmatter', () => {
    const parsed = parse('# heading\n');
    expect(parsed.frontmatter).toEqual({});
    expect(parsed.body).toContain('# heading');
  });

  it('handles empty frontmatter block', () => {
    const parsed = parse('---\n---\n\nBody\n');
    expect(parsed.frontmatter).toEqual({});
    expect(parsed.body.trim()).toBe('Body');
  });

  it('preserves unicode', () => {
    const doc = { frontmatter: { name: 'Café Olé' }, body: 'São Paulo' };
    const parsed = parse(render(doc));
    expect(parsed.frontmatter.name).toBe('Café Olé');
  });

  it('preserves field order', () => {
    const doc = { frontmatter: { z: 1, a: 2, m: 3 }, body: '' };
    const out = render(doc);
    const zi = out.indexOf('z:');
    const ai = out.indexOf('a:');
    const mi = out.indexOf('m:');
    expect(zi).toBeLessThan(ai);
    expect(ai).toBeLessThan(mi);
  });

  it('falls back gracefully on malformed YAML', () => {
    const text = '---\nthis is: not: valid: yaml: at: all\n---\nBody\n';
    const parsed = parse(text);
    expect(parsed.body).toContain('Body');
  });
});
