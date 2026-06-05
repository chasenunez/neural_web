// Build-time config read from Vite env vars. See .env.example.

function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new ConfigError(
      `Missing required env var ${name}. Copy .env.example to .env.local and fill it in, ` +
      `or set it as a GitHub Actions secret for production.`,
    );
  }
  return value;
}

function optional(value: string | undefined, fallback: string): string {
  return value && value.trim() ? value : fallback;
}

const DEFAULT_PHOTOS_PATH = '/Shared Photos';

export class ConfigError extends Error {}

export interface AppConfig {
  githubClientId: string;
  vaultRepo: string;       // "owner/repo"
  dropboxAppKey: string;
  dropboxPhotosPath: string;
}

let cached: AppConfig | undefined;

export function getConfig(): AppConfig {
  if (cached) return cached;
  const env = import.meta.env;
  cached = {
    githubClientId: required('VITE_GITHUB_CLIENT_ID', env.VITE_GITHUB_CLIENT_ID),
    vaultRepo: required('VITE_VAULT_REPO', env.VITE_VAULT_REPO),
    dropboxAppKey: required('VITE_DROPBOX_APP_KEY', env.VITE_DROPBOX_APP_KEY),
    dropboxPhotosPath: optional(env.VITE_DROPBOX_PHOTOS_PATH, DEFAULT_PHOTOS_PATH),
  };
  return cached;
}

export function tryGetConfig(): { config?: AppConfig; error?: ConfigError } {
  try {
    return { config: getConfig() };
  } catch (e) {
    if (e instanceof ConfigError) return { error: e };
    throw e;
  }
}
