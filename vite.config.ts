import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'node:path';

// VITE_BASE_PATH is set by the GitHub Actions deploy workflow to the
// `/${REPO_NAME}/` subpath that Pages serves from. Defaults to '/' for
// local development.
const base = process.env.VITE_BASE_PATH || '/';

export default defineConfig({
  base,
  plugins: [svelte()],
  resolve: {
    alias: {
      $lib: path.resolve('./src/lib'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/**/*.test.ts'],
  },
});
