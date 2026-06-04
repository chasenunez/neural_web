<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '$lib/router';
  import { authStore, photoPickStore, setStatus } from '$lib/stores';
  import * as gh from '$lib/github';
  import * as dropbox from '$lib/dropbox';
  import * as memory from '$lib/memory';
  import { getConfig } from '$lib/config';
  import { hintFor, MEMORY } from '$lib/templates';
  import { todayIso } from '$lib/vault';

  function hint(key: string): string {
    const f = MEMORY.fields.find((x) => x.key === key);
    return f ? hintFor(f) : '';
  }

  let title = $state('');
  let when = $state(todayIso());
  let who = $state('');
  let where = $state('');
  let why = $state('');
  let story = $state('');
  let saving = $state(false);
  let loadingPhoto = $state(false);
  let lastError = $state<string | undefined>();

  let photoBytes: Uint8Array | undefined;
  let photoExt = '.jpg';

  onMount(() => {
    if (!$photoPickStore) pickPhoto();
  });

  async function pickPhoto() {
    if (!$authStore.dropboxToken) {
      lastError = 'Dropbox is not connected. Go back to the sign-in page to connect.';
      return;
    }
    loadingPhoto = true;
    lastError = undefined;
    try {
      const { dropboxPhotosPath } = getConfig();
      const files = await dropbox.listImages($authStore.dropboxToken, dropboxPhotosPath);
      if (files.length === 0) {
        lastError = `No images in Dropbox folder "${dropboxPhotosPath}".`;
        loadingPhoto = false;
        return;
      }
      const pick = dropbox.pickRandom(files)!;
      const bytes = await dropbox.downloadFile($authStore.dropboxToken, pick.path);
      const dataUrl = dropbox.bytesToDataUrl(bytes, pick.name);
      photoPickStore.set({ path: pick.path, dataUrl, bytes: bytes.length });
      photoBytes = bytes;
      photoExt = '.' + (pick.name.split('.').pop() || 'jpg').toLowerCase();
    } catch (e) {
      lastError = (e as Error).message;
    } finally {
      loadingPhoto = false;
    }
  }

  async function save() {
    if (!title.trim()) {
      setStatus('warn', 'Please give the memory a short title.');
      return;
    }
    saving = true;
    try {
      const user = await gh.getUser($authStore.githubToken!);
      const result = await memory.saveMemory($authStore.githubToken!, user, {
        title, when, who, where, why, story,
        photoBytes, photoExt,
      });
      setStatus('info', `Saved — ${result.memoryPath.split('/').pop()}`);
      photoPickStore.set(undefined);
      navigate('home');
    } catch (e) {
      setStatus('warn', 'Save failed: ' + (e as Error).message);
    } finally {
      saving = false;
    }
  }
</script>

<h1>A moment from your photos</h1>

{#if loadingPhoto}
  <p class="muted">Finding a photo…</p>
{:else if lastError}
  <div class="banner warn">{lastError}</div>
{:else if $photoPickStore}
  <img class="photo" src={$photoPickStore.dataUrl} alt={$photoPickStore.path} />
  <p class="hint">{$photoPickStore.path.split('/').pop()}</p>
{/if}

<div class="field">
  <label for="title">What</label>
  <input id="title" type="text" bind:value={title} placeholder={hint('title')} />
</div>

<div class="field">
  <label for="when">When</label>
  <input id="when" type="date" bind:value={when} />
</div>

<div class="field">
  <label for="who">Who</label>
  <input id="who" type="text" bind:value={who} placeholder={hint('who')} />
  <span class="hint">{hint('who')}</span>
</div>

<div class="field">
  <label for="where">Where</label>
  <input id="where" type="text" bind:value={where} placeholder={hint('where')} />
  <span class="hint">{hint('where')}</span>
</div>

<div class="field">
  <label for="why">Why</label>
  <textarea id="why" bind:value={why} placeholder={hint('why')}></textarea>
</div>

<div class="field">
  <label for="story">Story</label>
  <textarea id="story" bind:value={story} rows="8" placeholder={hint('story')}></textarea>
</div>

<button onclick={save} disabled={saving || !$photoPickStore}>{saving ? 'Saving…' : 'Save memory'}</button>
<button class="ghost" onclick={() => { photoPickStore.set(undefined); pickPhoto(); }} disabled={loadingPhoto}>Try a different photo</button>
<button class="ghost" onclick={() => navigate('home')}>← Back</button>
