import { describe, expect, it } from 'vitest';
import {
  PERSON, PLACE, MEMORY, TEMPLATES, byType,
  blankValue, emptyFrontmatter, findField, hintFor,
} from '../src/lib/templates';

describe('templates', () => {
  it('exposes all three templates', () => {
    expect(TEMPLATES).toHaveLength(3);
    expect(TEMPLATES.map((t) => t.type)).toEqual(['Person', 'Place', 'Memory']);
  });

  it('byType is case-insensitive', () => {
    expect(byType('person')).toBe(PERSON);
    expect(byType('Place')).toBe(PLACE);
    expect(byType('MEMORY')).toBe(MEMORY);
  });

  it('byType throws on unknown type', () => {
    expect(() => byType('Banana')).toThrow();
  });

  it('person fields are in importance order', () => {
    expect(PERSON.fields[0].key).toBe('name');
    expect(PERSON.fields.at(-1)!.key).toBe('employers');
  });

  it('emptyFrontmatter includes every field with the right blank', () => {
    const fm = emptyFrontmatter(PERSON);
    for (const f of PERSON.fields) {
      expect(fm).toHaveProperty(f.key);
    }
    expect(fm.parents).toEqual([]);
    expect(fm.lives_in).toBe('');
    expect(fm.type).toBe('person');
  });

  it('blankValue returns correct shape per kind', () => {
    expect(blankValue('links')).toEqual([]);
    expect(blankValue('text')).toBe('');
    expect(blankValue('date')).toBe('');
  });

  it('findField finds + returns undefined cleanly', () => {
    expect(findField(PERSON, 'name')?.label).toBe('Name');
    expect(findField(PERSON, 'nonexistent')).toBeUndefined();
  });

  it('hintFor prefers explicit hint, falls back to default by kind', () => {
    const grandparents = findField(PERSON, 'paternal_grandparents')!;
    expect(hintFor(grandparents)).toMatch(/two/i);

    const birthdate = findField(PERSON, 'birthdate')!;
    expect(birthdate.hint).toBeUndefined();
    expect(hintFor(birthdate)).toMatch(/YYYY-MM-DD/);
  });
});
