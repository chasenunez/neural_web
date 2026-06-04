import { describe, expect, it } from 'vitest';
import { splitNouns } from '../src/lib/parsing';

describe('splitNouns', () => {
  it('returns empty for blank input', () => {
    expect(splitNouns('')).toEqual([]);
    expect(splitNouns('   ')).toEqual([]);
  });

  it('handles a single name', () => {
    expect(splitNouns('Mary')).toEqual(['Mary']);
  });

  it('splits on commas', () => {
    expect(splitNouns('Mary, John, Sue')).toEqual(['Mary', 'John', 'Sue']);
  });

  it('splits on "and"', () => {
    expect(splitNouns('Mom and Dad')).toEqual(['Mom', 'Dad']);
  });

  it('splits on ampersand', () => {
    expect(splitNouns('Mary & John')).toEqual(['Mary', 'John']);
  });

  it('splits on semicolon', () => {
    expect(splitNouns('Mary; John')).toEqual(['Mary', 'John']);
  });

  it('handles mixed separators', () => {
    expect(splitNouns('Mary, John and Sue & Tim')).toEqual(['Mary', 'John', 'Sue', 'Tim']);
  });

  it('dedupes case-insensitively', () => {
    expect(splitNouns('Mary, mary, MARY')).toEqual(['Mary']);
  });

  it('preserves the first-seen casing', () => {
    expect(splitNouns('mary smith, Mary Smith')).toEqual(['mary smith']);
  });

  it('strips whitespace', () => {
    expect(splitNouns('  Mary  ,   John  ')).toEqual(['Mary', 'John']);
  });
});
