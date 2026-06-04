<script lang="ts">
  import { onMount } from 'svelte';
  import { route, initRouter, navigate } from '$lib/router';
  import { authStore, userStore, statusStore } from '$lib/stores';
  import { tryGetConfig } from '$lib/config';
  import * as dropbox from '$lib/dropbox';

  import Login from './pages/Login.svelte';
  import Home from './pages/Home.svelte';
  import Freeform from './pages/Freeform.svelte';
  import Photo from './pages/Photo.svelte';
  import FillBlanks from './pages/FillBlanks.svelte';

  const { config, error } = tryGetConfig();

  onMount(async () => {
    initRouter();

    // Handle Dropbox OAuth redirect (?code=…)
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) {
      try {
        const token = await dropbox.finishAuth(code);
        authStore.update((a) => ({
          ...a,
          dropboxToken: token.access_token,
          dropboxExpiresAt: token.expires_at,
          dropboxRefreshToken: token.refresh_token,
        }));
        // Strip the ?code= from the URL so we don't reprocess on refresh
        const clean = window.location.pathname + window.location.hash;
        window.history.replaceState({}, '', clean);
        statusStore.set({ kind: 'info', text: 'Dropbox connected.' });
        navigate('login');
      } catch (e) {
        statusStore.set({ kind: 'warn', text: 'Dropbox sign-in failed: ' + (e as Error).message });
      }
    }
  });

  // Routing: if there's no GitHub token, force login.
  $: if ($authStore.githubToken && $userStore && $route.page === 'login') {
    navigate('home');
  }
  $: if ((!$authStore.githubToken || !$userStore) && $route.page !== 'login') {
    navigate('login');
  }
</script>

<main>
  {#if error}
    <div class="banner warn">
      <strong>Configuration missing.</strong>
      {error.message}
    </div>
  {:else if $statusStore}
    <div class="banner" class:warn={$statusStore.kind === 'warn'}>
      {$statusStore.text}
    </div>
  {/if}

  {#if !config}
    <p class="muted">Waiting for configuration. See README for setup.</p>
  {:else if $route.page === 'login'}
    <Login />
  {:else if $route.page === 'home'}
    <Home />
  {:else if $route.page === 'freeform'}
    <Freeform />
  {:else if $route.page === 'photo'}
    <Photo />
  {:else if $route.page === 'fill_blanks' || $route.page === 'fill_edit'}
    <FillBlanks />
  {/if}
</main>
