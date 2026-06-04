<script lang="ts">
  import { navigate } from '$lib/router';
  import { userStore, signOut, photoPickStore } from '$lib/stores';

  function logout() {
    signOut();
    navigate('login');
  }

  function gotoPhoto() {
    photoPickStore.set(undefined);
    navigate('photo');
  }
</script>

<h1>Hello, {$userStore}</h1>
<p class="muted">How would you like to add to the vault today?</p>

<button class="full" onclick={() => navigate('freeform')}>
  Write a memory in your own words
</button>
<button class="full" onclick={gotoPhoto}>
  Let a photo prompt a memory
</button>
<button class="full" onclick={() => navigate('fill_blanks')}>
  Help fill in blank entries
</button>

<div style="height:2rem;"></div>
<button class="ghost" onclick={logout}>Sign out</button>
