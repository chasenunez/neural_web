// Hash-based router. Works on GitHub Pages without server config.
// Params ride along as a query string: #/fill_edit?type=Person&name=Alex

import { writable } from 'svelte/store';

export type PageName =
  | 'login'
  | 'home'
  | 'freeform'
  | 'photo'
  | 'fill_blanks'
  | 'fill_edit';

export interface Route {
  page: PageName;
  params: Record<string, string>;
}

const DEFAULT: Route = { page: 'login', params: {} };

export const route = writable<Route>(DEFAULT);

function parse(hash: string): Route {
  const raw = hash.replace(/^#\/?/, '');
  if (!raw) return DEFAULT;
  const [pageRaw, query = ''] = raw.split('?');
  const params: Record<string, string> = {};
  if (query) {
    for (const pair of query.split('&')) {
      const [k, v = ''] = pair.split('=');
      if (k) params[decodeURIComponent(k)] = decodeURIComponent(v);
    }
  }
  const page = (pageRaw || 'login') as PageName;
  return { page, params };
}

function serialize(r: Route): string {
  const qs = Object.entries(r.params)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&');
  return `#/${r.page}${qs ? `?${qs}` : ''}`;
}

export function navigate(page: PageName, params: Record<string, string> = {}): void {
  const next: Route = { page, params };
  window.location.hash = serialize(next);
  route.set(next);
}

export function initRouter(): void {
  const apply = () => route.set(parse(window.location.hash));
  window.addEventListener('hashchange', apply);
  apply();
}
