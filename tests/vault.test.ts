import { describe, expect, it } from 'vitest';
import {
  normalizeName, displayToWikilink, wikilinksToDisplays,
  pathFor, memoryPath, isBlank, todayIso, folderFor,
} from '../src/lib/vault';

describe('normalizeName', () => {
  it('title-cases multi-word names', () => {
    expect(normalizeName('mary smith')).toBe('Mary Smith');
  });

  it('strips apostrophes', () => {
    expect(normalizeName("grandma's house")).toBe('Grandmas House');
    expect(normalizeName('grandma’s house')).toBe('Grandmas House');
  });

  it('collapses whitespace', () => {
    expect(normalizeName('  Mary    Smith  ')).toBe('Mary Smith');
  });

  it('strips unsafe filename chars', () => {
    expect(normalizeName('Mary/Smith?')).toBe('Marysmith');
  });
});

describe('wikilinks', () => {
  it('displayToWikilink wraps + normalizes', () => {
    expect(displayToWikilink('mary smith')).toBe('[[Mary Smith]]');
  });

  it('wikilinksToDisplays unwraps and filters', () => {
    expect(wikilinksToDisplays(['[[Mary]]', '[[John]]', ''])).toEqual(['Mary', 'John']);
  });
});

describe('paths', () => {
  it('pathFor combines folder + normalized name + .md', () => {
    expect(pathFor('Person', 'mary smith')).toBe('People/Mary Smith.md');
    expect(pathFor('Place', 'the park')).toBe('Places/The Park.md');
  });

  it('memoryPath prepends ISO date', () => {
    expect(memoryPath('First Lesson', '2026-06-04')).toBe('Memories/2026-06-04 First Lesson.md');
  });

  it('memoryPath falls back to Untitled', () => {
    expect(memoryPath('', '2026-06-04')).toBe('Memories/2026-06-04 Untitled.md');
  });

  it('folderFor returns the type\'s folder', () => {
    expect(folderFor('Person')).toBe('People');
    expect(folderFor('Place')).toBe('Places');
    expect(folderFor('Memory')).toBe('Memories');
  });
});

describe('isBlank', () => {
  it('recognises blanks across types', () => {
    expect(isBlank(undefined)).toBe(true);
    expect(isBlank(null)).toBe(true);
    expect(isBlank('')).toBe(true);
    expect(isBlank('  ')).toBe(true);
    expect(isBlank([])).toBe(true);
    expect(isBlank({})).toBe(true);
  });

  it('non-blanks read non-blank', () => {
    expect(isBlank('x')).toBe(false);
    expect(isBlank(['a'])).toBe(false);
    expect(isBlank(0)).toBe(false);  // numeric zero is a real value
  });
});

describe('todayIso', () => {
  it('returns YYYY-MM-DD', () => {
    expect(todayIso()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
