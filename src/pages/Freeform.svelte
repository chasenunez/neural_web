<script lang="ts">
  import { navigate } from '$lib/router';
  import { authStore, setStatus } from '$lib/stores';
  import * as gh from '$lib/github';
  import * as memory from '$lib/memory';
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
      });
      setStatus('info', `Saved — ${result.memoryPath.split('/').pop()}`);
      navigate('home');
    } catch (e) {
      setStatus('warn', 'Save failed: ' + (e as Error).message);
    } finally {
      saving = false;
    }
  }
</script>

<h1>Write a memory</h1>
<p class="muted">Tell the story as completely or briefly as you like.</p>

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
  <textarea id="story" bind:value={story} rows="10" placeholder={hint('story')}></textarea>
</div>

<button onclick={save} disabled={saving}>{saving ? 'Saving…' : 'Save memory'}</button>
<button class="ghost" onclick={() => navigate('home')}>← Back</button>
