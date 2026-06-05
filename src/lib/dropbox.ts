// Dropbox client for the shared photo pool. OAuth 2 with PKCE (no
// client secret). Tokens persist in authStore.

import { getConfig } from './config';

const AUTH_BASE = 'https://www.dropbox.com/oauth2/authorize';
const TOKEN_URL = 'https://api.dropboxapi.com/oauth2/token';
const API_BASE = 'https://api.dropboxapi.com/2';
const CONTENT_BASE = 'https://content.dropboxapi.com/2';
const PKCE_VERIFIER_KEY = 'familyvault.dropbox.pkce_verifier';
const REDIRECT_KEY = 'familyvault.dropbox.redirect_state';

const IMAGE_EXTS = new Set(['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif']);

export interface DropboxFile {
  path: string;
  name: string;
  size: number;
  id: string;
}

export class DropboxError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

// ── PKCE auth ───────────────────────────────────────────────────────────────

export async function startAuth(redirectUri: string): Promise<string> {
  const verifier = randomString(64);
  const challenge = await sha256Base64Url(verifier);
  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);
  sessionStorage.setItem(REDIRECT_KEY, redirectUri);

  const { dropboxAppKey } = getConfig();
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: dropboxAppKey,
    redirect_uri: redirectUri,
    code_challenge: challenge,
    code_challenge_method: 'S256',
    token_access_type: 'offline',
  });
  return `${AUTH_BASE}?${params.toString()}`;
}

export interface DropboxToken {
  access_token: string;
  refresh_token?: string;
  expires_at: number;       // epoch ms
}

export async function finishAuth(code: string): Promise<DropboxToken> {
  const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);
  const redirectUri = sessionStorage.getItem(REDIRECT_KEY);
  if (!verifier || !redirectUri) throw new DropboxError(0, 'PKCE state missing — auth flow was interrupted.');
  sessionStorage.removeItem(PKCE_VERIFIER_KEY);
  sessionStorage.removeItem(REDIRECT_KEY);

  const { dropboxAppKey } = getConfig();
  const body = new URLSearchParams({
    code,
    grant_type: 'authorization_code',
    client_id: dropboxAppKey,
    code_verifier: verifier,
    redirect_uri: redirectUri,
  });
  const resp = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!resp.ok) throw new DropboxError(resp.status, await resp.text());
  const data = await resp.json();
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + (data.expires_in ?? 14400) * 1000,
  };
}

export async function refresh(refreshToken: string): Promise<DropboxToken> {
  const { dropboxAppKey } = getConfig();
  const body = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
    client_id: dropboxAppKey,
  });
  const resp = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!resp.ok) throw new DropboxError(resp.status, await resp.text());
  const data = await resp.json();
  return {
    access_token: data.access_token,
    refresh_token: refreshToken,
    expires_at: Date.now() + (data.expires_in ?? 14400) * 1000,
  };
}

// ── API ─────────────────────────────────────────────────────────────────────

function rpcHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}

export async function listImages(token: string, folderPath: string): Promise<DropboxFile[]> {
  const out: DropboxFile[] = [];
  let cursor: string | undefined;
  do {
    const url = `${API_BASE}/files/${cursor ? 'list_folder/continue' : 'list_folder'}`;
    const body = cursor
      ? { cursor }
      : { path: folderPath === '/' ? '' : folderPath, recursive: true, include_non_downloadable_files: false };
    const resp = await fetch(url, {
      method: 'POST',
      headers: rpcHeaders(token),
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new DropboxError(resp.status, await resp.text());
    const data = await resp.json();
    for (const entry of data.entries ?? []) {
      if (entry['.tag'] !== 'file') continue;
      const name: string = entry.name;
      const lower = '.' + name.split('.').pop()!.toLowerCase();
      if (!IMAGE_EXTS.has(lower)) continue;
      out.push({ path: entry.path_lower ?? entry.path_display, name, size: entry.size, id: entry.id });
    }
    cursor = data.has_more ? data.cursor : undefined;
  } while (cursor);
  return out;
}

export async function downloadFile(token: string, path: string): Promise<Uint8Array> {
  const resp = await fetch(`${CONTENT_BASE}/files/download`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Dropbox-API-Arg': JSON.stringify({ path }),
    },
  });
  if (!resp.ok) throw new DropboxError(resp.status, await resp.text());
  const buf = await resp.arrayBuffer();
  return new Uint8Array(buf);
}

// ── PKCE helpers ────────────────────────────────────────────────────────────

function randomString(byteLen: number): string {
  const a = new Uint8Array(byteLen);
  crypto.getRandomValues(a);
  return base64Url(a);
}

async function sha256Base64Url(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return base64Url(new Uint8Array(hash));
}

function base64Url(bytes: Uint8Array): string {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function pickRandom<T>(items: readonly T[]): T | undefined {
  if (items.length === 0) return undefined;
  return items[Math.floor(Math.random() * items.length)];
}

export function bytesToDataUrl(bytes: Uint8Array, filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? 'jpg';
  const mime = ext === 'png' ? 'image/png'
    : ext === 'gif' ? 'image/gif'
    : ext === 'webp' ? 'image/webp'
    : 'image/jpeg';
  // For HEIC/HEIF we still claim jpeg — most browsers won't render HEIC natively;
  // upstream callers convert via canvas when needed.
  let bin = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return `data:${mime};base64,${btoa(bin)}`;
}
