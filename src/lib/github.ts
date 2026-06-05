// GitHub REST client. Auth via Device Flow or pasted PAT.
// One commit per write via the Contents API.

import { getConfig } from './config';

const GITHUB_API = 'https://api.github.com';
const DEVICE_CODE_URL = 'https://github.com/login/device/code';
const ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token';
const DEVICE_FLOW_SCOPE = 'repo';

export interface DeviceCodeResponse {
  device_code: string;
  user_code: string;
  verification_uri: string;
  expires_in: number;
  interval: number;
}

export interface GitHubUser {
  login: string;
  name?: string;
  email?: string;
  avatar_url?: string;
}

export class GitHubError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

// ── Device Flow auth ───────────────────────────────────────────────────────

export async function startDeviceFlow(): Promise<DeviceCodeResponse> {
  const { githubClientId } = getConfig();
  const resp = await fetch(DEVICE_CODE_URL, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: githubClientId, scope: DEVICE_FLOW_SCOPE }),
  });
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  return await resp.json();
}

// Poll the token endpoint until the user authorizes. Honors slow_down,
// gives up after 15 minutes regardless.
export async function pollForToken(
  deviceCode: string,
  initialIntervalSec: number,
  abort: AbortSignal,
): Promise<string> {
  const { githubClientId } = getConfig();
  let interval = initialIntervalSec * 1000;
  const deadline = Date.now() + 15 * 60 * 1000; // 15 min absolute cap

  while (Date.now() < deadline) {
    if (abort.aborted) throw new GitHubError(0, 'cancelled');
    await new Promise((r) => setTimeout(r, interval));

    const resp = await fetch(ACCESS_TOKEN_URL, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_id: githubClientId,
        device_code: deviceCode,
        grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
      }),
    });
    if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
    const data = await resp.json();
    if (data.access_token) return data.access_token as string;
    if (data.error === 'authorization_pending') continue;
    if (data.error === 'slow_down') { interval += 5000; continue; }
    if (data.error === 'expired_token' || data.error === 'access_denied') {
      throw new GitHubError(0, data.error);
    }
    throw new GitHubError(0, data.error_description || data.error || 'unknown error');
  }
  throw new GitHubError(0, 'timeout');
}

// ── REST API ───────────────────────────────────────────────────────────────

function authHeaders(token: string): HeadersInit {
  return {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    Authorization: `Bearer ${token}`,
  };
}

export async function getUser(token: string): Promise<GitHubUser> {
  const resp = await fetch(`${GITHUB_API}/user`, { headers: authHeaders(token) });
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  return await resp.json();
}

export interface FileMeta {
  path: string;
  sha: string;
  size: number;
}

export interface FileContent extends FileMeta {
  text: string;
}

export async function listDir(token: string, path: string): Promise<FileMeta[]> {
  const { vaultRepo } = getConfig();
  const url = `${GITHUB_API}/repos/${vaultRepo}/contents/${encodeURIComponent(path)}`;
  const resp = await fetch(url, { headers: authHeaders(token) });
  if (resp.status === 404) return [];
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  const data = await resp.json();
  if (!Array.isArray(data)) return [];
  return data
    .filter((entry: { type: string }) => entry.type === 'file')
    .map((entry: { path: string; sha: string; size: number }) => ({
      path: entry.path, sha: entry.sha, size: entry.size,
    }));
}

export async function readFile(token: string, path: string): Promise<FileContent | null> {
  const { vaultRepo } = getConfig();
  const url = `${GITHUB_API}/repos/${vaultRepo}/contents/${encodePath(path)}`;
  const resp = await fetch(url, { headers: authHeaders(token) });
  if (resp.status === 404) return null;
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  const data = await resp.json();
  const text = decodeBase64Utf8((data.content as string).replace(/\n/g, ''));
  return { path: data.path, sha: data.sha, size: data.size, text };
}

export async function writeFile(
  token: string,
  path: string,
  content: string,
  message: string,
  user: GitHubUser,
  sha?: string,
): Promise<{ sha: string }> {
  const { vaultRepo } = getConfig();
  const url = `${GITHUB_API}/repos/${vaultRepo}/contents/${encodePath(path)}`;
  const body: Record<string, unknown> = {
    message,
    content: encodeBase64Utf8(content),
    committer: { name: user.name || user.login, email: user.email || `${user.login}@users.noreply.github.com` },
    author: { name: user.name || user.login, email: user.email || `${user.login}@users.noreply.github.com` },
  };
  if (sha) body.sha = sha;
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  const data = await resp.json();
  return { sha: data.content.sha as string };
}

export async function writeBinary(
  token: string,
  path: string,
  bytes: Uint8Array,
  message: string,
  user: GitHubUser,
  sha?: string,
): Promise<{ sha: string }> {
  const { vaultRepo } = getConfig();
  const url = `${GITHUB_API}/repos/${vaultRepo}/contents/${encodePath(path)}`;
  const body: Record<string, unknown> = {
    message,
    content: bytesToBase64(bytes),
    committer: { name: user.name || user.login, email: user.email || `${user.login}@users.noreply.github.com` },
    author: { name: user.name || user.login, email: user.email || `${user.login}@users.noreply.github.com` },
  };
  if (sha) body.sha = sha;
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new GitHubError(resp.status, await resp.text());
  const data = await resp.json();
  return { sha: data.content.sha as string };
}

// ── Encoding helpers ───────────────────────────────────────────────────────

function encodePath(path: string): string {
  return path.split('/').map(encodeURIComponent).join('/');
}

function encodeBase64Utf8(text: string): string {
  const bytes = new TextEncoder().encode(text);
  return bytesToBase64(bytes);
}

function decodeBase64Utf8(b64: string): string {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

function bytesToBase64(bytes: Uint8Array): string {
  let bin = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(bin);
}

export const _internal = { encodeBase64Utf8, decodeBase64Utf8, bytesToBase64, encodePath };
