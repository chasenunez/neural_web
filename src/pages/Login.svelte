<script lang="ts">
  import { authStore, userStore, setStatus } from '$lib/stores';
  import { navigate } from '$lib/router';
  import * as gh from '$lib/github';
  import * as dropbox from '$lib/dropbox';

  let name = $state($userStore || '');
  let pasteMode = $state(false);
  let pat = $state('');

  let deviceCode: gh.DeviceCodeResponse | undefined = $state();
  let polling = $state(false);
  let pollAbort: AbortController | undefined;

  async function startDeviceFlow() {
    try {
      const code = await gh.startDeviceFlow();
      deviceCode = code;
      polling = true;
      pollAbort = new AbortController();
      const token = await gh.pollForToken(code.device_code, code.interval, pollAbort.signal);
      const user = await gh.getUser(token);
      authStore.update((a) => ({ ...a, githubToken: token, githubLogin: user.login }));
      polling = false;
      deviceCode = undefined;
      setStatus('info', `Signed in to GitHub as ${user.login}.`);
      tryAdvance();
    } catch (e) {
      polling = false;
      deviceCode = undefined;
      setStatus('warn', 'GitHub device-flow sign-in failed: ' + (e as Error).message +
        ' — try the token-paste option below.');
    }
  }

  function cancelDeviceFlow() {
    pollAbort?.abort();
    polling = false;
    deviceCode = undefined;
  }

  async function signInWithPat() {
    try {
      const user = await gh.getUser(pat);
      authStore.update((a) => ({ ...a, githubToken: pat, githubLogin: user.login }));
      pat = '';
      setStatus('info', `Signed in to GitHub as ${user.login}.`);
      tryAdvance();
    } catch (e) {
      setStatus('warn', 'That token didn\'t work: ' + (e as Error).message);
    }
  }

  async function connectDropbox() {
    const redirect = window.location.origin + window.location.pathname;
    const url = await dropbox.startAuth(redirect);
    window.location.href = url;
  }

  function tryAdvance() {
    userStore.set(name.trim());
    if (name.trim() && $authStore.githubToken) navigate('home');
  }
</script>

<h1>Welcome</h1>
<p class="muted">Sign in once to begin adding to the family vault.</p>

<!-- Step 1: name -->
<div class="field">
  <label for="name">Your name</label>
  <input id="name" type="text" bind:value={name} placeholder="The name your family knows you by" />
  <span class="hint">Used to attribute commits in the vault history.</span>
</div>

<!-- Step 2: GitHub -->
<div class="field">
  <!-- svelte-ignore a11y_label_has_associated_control -->
  <label>GitHub</label>
  {#if $authStore.githubToken}
    <p class="muted">Signed in as <strong>{$authStore.githubLogin}</strong>.</p>
  {:else if polling && deviceCode}
    <div class="banner">
      <p>
        Open <a href={deviceCode.verification_uri} target="_blank" rel="noopener">{deviceCode.verification_uri}</a>
        and enter this code:
      </p>
      <p style="font-size:1.8rem; letter-spacing:0.2em; text-align:center; font-family:monospace;">
        {deviceCode.user_code}
      </p>
      <p class="muted">Polling for authorization…</p>
    </div>
    <button class="ghost" onclick={cancelDeviceFlow}>Cancel</button>
  {:else}
    <button onclick={startDeviceFlow}>Sign in with GitHub</button>
    <button class="ghost" onclick={() => (pasteMode = !pasteMode)}>
      {pasteMode ? 'Hide token field' : 'Paste a token instead'}
    </button>
    {#if pasteMode}
      <p class="hint">
        Paste a Personal Access Token with <code>repo</code> scope for the vault repo.
        Use this if the Device Flow gets blocked by your browser.
      </p>
      <input type="password" bind:value={pat} placeholder="github_pat_…" />
      <button onclick={signInWithPat} disabled={!pat.trim()}>Use this token</button>
    {/if}
  {/if}
</div>

<!-- Step 3: Dropbox (optional) -->
<div class="field">
  <!-- svelte-ignore a11y_label_has_associated_control -->
  <label>Dropbox (for the photo prompt flow)</label>
  {#if $authStore.dropboxToken}
    <p class="muted">Connected.</p>
  {:else}
    <button class="ghost" onclick={connectDropbox}>Connect Dropbox</button>
    <span class="hint">Optional. Skip if you only want freeform writing or fill-blanks.</span>
  {/if}
</div>

<button class="full" disabled={!name.trim() || !$authStore.githubToken} onclick={tryAdvance}>
  Enter
</button>
