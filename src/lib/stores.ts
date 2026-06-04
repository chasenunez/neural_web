/**
 * Persistent + ephemeral stores for the app.
 *
 *   authStore       — GitHub + Dropbox tokens, persisted to localStorage
 *   userStore       — the family member's chosen display name (login.svelte sets this)
 *   photoPickStore  — caches a random photo selection across reruns of the photo page
 */

import { writable, type Writable } from 'svelte/store';

const STORAGE_KEY = 'familyvault.auth.v1';
const USER_KEY = 'familyvault.user.v1';

export interface AuthState {
  githubToken?: string;
  githubLogin?: string;
  dropboxToken?: string;
  dropboxExpiresAt?: number;       // epoch ms
  dropboxRefreshToken?: string;
}

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function persisted<T>(key: string, initial: T): Writable<T> {
  const store = writable<T>(loadJson(key, initial));
  store.subscribe((value) => {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* quota / disabled */ }
  });
  return store;
}

export const authStore = persisted<AuthState>(STORAGE_KEY, {});
export const userStore = persisted<string>(USER_KEY, '');

// Ephemeral session state — held in memory only.
export interface PhotoPick {
  path: string;       // Dropbox path
  dataUrl: string;    // base64 data URL ready to <img>
  bytes: number;
}

export const photoPickStore = writable<PhotoPick | undefined>(undefined);

// Toast-style status banner shown across pages.
export interface Status {
  kind: 'info' | 'warn';
  text: string;
}
export const statusStore = writable<Status | undefined>(undefined);

export function setStatus(kind: Status['kind'], text: string): void {
  statusStore.set({ kind, text });
}
export function clearStatus(): void {
  statusStore.set(undefined);
}

export function signOut(): void {
  authStore.set({});
  userStore.set('');
  photoPickStore.set(undefined);
  statusStore.set(undefined);
}
