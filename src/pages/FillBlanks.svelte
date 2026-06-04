<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate, route } from '$lib/router';
  import { authStore, setStatus } from '$lib/stores';
  import * as gh from '$lib/github';
  import * as memory from '$lib/memory';
  import * as fm from '$lib/frontmatter';
  import { byType, hintFor, type TypeName } from '$lib/templates';
  import { wikilinksToDisplays } from '$lib/vault';

  let loading = $state(false);
  let incompletePeople: { path: string; name: string }[] = $state([]);
  let incompletePlaces: { path: string; name: string }[] = $state([]);

  let editingType: TypeName | undefined = $state();
  let editingPath: string | undefined = $state();
  let inputs: Record<string, string> = $state({});
  let saving = $state(false);

  onMount(() => refresh());

  async function refresh() {
    loading = true;
    try {
      const [people, places] = await Promise.all([
        memory.listIncomplete($authStore.githubToken!, 'Person'),
        memory.listIncomplete($authStore.githubToken!, 'Place'),
      ]);
      incompletePeople = people;
      incompletePlaces = places;
    } catch (e) {
      setStatus('warn', 'Could not list incomplete files: ' + (e as Error).message);
    } finally {
      loading = false;
    }
  }

  async function openEditor(type: TypeName, path: string) {
    editingType = type;
    editingPath = path;
    inputs = {};
    try {
      const file = await gh.readFile($authStore.githubToken!, path);
      if (!file) return;
      const doc = fm.parse(file.text);
      const tmpl = byType(type);
      for (const field of tmpl.fields) {
        inputs[field.key] = toEditableString(doc.frontmatter[field.key]);
      }
    } catch (e) {
      setStatus('warn', 'Could not load the file: ' + (e as Error).message);
    }
  }

  function toEditableString(value: unknown): string {
    if (value == null) return '';
    if (Array.isArray(value)) return wikilinksToDisplays(value).join(', ');
    if (typeof value === 'string') {
      const s = value.trim();
      return s.startsWith('[[') && s.endsWith(']]') ? s.slice(2, -2) : s;
    }
    return String(value);
  }

  async function save() {
    if (!editingType || !editingPath) return;
    saving = true;
    try {
      const user = await gh.getUser($authStore.githubToken!);
      await memory.saveRecord($authStore.githubToken!, user, {
        type: editingType, path: editingPath, inputs,
      });
      setStatus('info', `Saved ${editingPath.split('/').pop()}`);
      editingType = undefined;
      editingPath = undefined;
      await refresh();
    } catch (e) {
      setStatus('warn', 'Save failed: ' + (e as Error).message);
    } finally {
      saving = false;
    }
  }

  let tmpl = $derived(editingType ? byType(editingType) : undefined);
</script>

{#if editingType && editingPath && tmpl}
  <h1>{editingPath.split('/').pop()?.replace(/\.md$/, '')}</h1>
  <p class="muted">{editingType} · fill anything you remember</p>

  {#each tmpl.fields as field (field.key)}
    <div class="field">
      <label for={field.key}>{field.label}</label>
      {#if field.kind === 'longtext'}
        <textarea id={field.key} bind:value={inputs[field.key]} placeholder={hintFor(field)}></textarea>
      {:else}
        <input id={field.key} type="text" bind:value={inputs[field.key]} placeholder={hintFor(field)} />
      {/if}
      {#if hintFor(field)}<span class="hint">{hintFor(field)}</span>{/if}
    </div>
  {/each}

  <button onclick={save} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
  <button class="ghost" onclick={() => { editingType = undefined; editingPath = undefined; }}>← Back to list</button>
{:else}
  <h1>Help fill in blank entries</h1>
  <p class="muted">These entries were created automatically from earlier memories.</p>

  {#if loading}
    <p class="muted">Loading…</p>
  {:else if incompletePeople.length === 0 && incompletePlaces.length === 0}
    <div class="banner">Every entry is complete. Nothing to do here right now.</div>
  {:else}
    {#if incompletePeople.length}
      <h2>People</h2>
      {#each incompletePeople as f (f.path)}
        <button class="full" onclick={() => openEditor('Person', f.path)}>{f.name}</button>
      {/each}
    {/if}
    {#if incompletePlaces.length}
      <h2>Places</h2>
      {#each incompletePlaces as f (f.path)}
        <button class="full" onclick={() => openEditor('Place', f.path)}>{f.name}</button>
      {/each}
    {/if}
  {/if}

  <div style="height:1rem;"></div>
  <button class="ghost" onclick={() => navigate('home')}>← Back</button>
{/if}
