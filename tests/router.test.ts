/**
 * @vitest-environment jsdom
 */
import { describe, expect, it, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { initRouter, navigate, route } from '../src/lib/router';

describe('router', () => {
  beforeEach(() => {
    window.location.hash = '';
  });

  it('initializes from current hash', () => {
    window.location.hash = '#/freeform';
    initRouter();
    expect(get(route).page).toBe('freeform');
  });

  it('parses params', () => {
    window.location.hash = '#/fill_edit?type=Person&name=Mom';
    initRouter();
    const r = get(route);
    expect(r.page).toBe('fill_edit');
    expect(r.params.type).toBe('Person');
    expect(r.params.name).toBe('Mom');
  });

  it('navigate updates the hash + store', () => {
    initRouter();
    navigate('photo');
    expect(window.location.hash).toBe('#/photo');
    expect(get(route).page).toBe('photo');
  });

  it('navigate with params round-trips', () => {
    initRouter();
    navigate('fill_edit', { type: 'Person', name: 'Mom' });
    expect(get(route).params).toEqual({ type: 'Person', name: 'Mom' });
  });
});
