# Family Vault

A shared, browser-based vault for **episodic memories** — the specific
moments your family has lived through. Each memory is captured with the
same 5W context the brain uses to encode an episode (who, what, where,
when, why), and every person and place mentioned becomes its own linked
markdown file. The vault grows into a **neural web** of cross-linked
notes.

The app runs entirely in the browser, deployed to GitHub Pages, and
stores everything in a **private GitHub repository** you control. There
is no server — the code repo (this one) can be public, while the vault
repo (the memories themselves) stays private.

## The three flows

1. **Write a memory in your own words** — who / what / where / when / why + story
2. **Let a photo prompt a memory** — a random pick from a shared Dropbox folder, with the same form
3. **Help fill in blank entries** — pages auto-created from earlier memories that need details

Every entry the parser finds (a new person in "who", a new place in
"where") becomes a stub markdown file, which any family member can fill
in later through flow 3. The vault stays Obsidian-compatible:
`[[Wikilinks]]` and Dataview-friendly YAML frontmatter.

## What lives where

| Repo / Service | What's in it | Visibility |
| --- | --- | --- |
| **This code repo** | The app source (Svelte + TypeScript) | Public (must be, for free GitHub Pages) |
| **Your vault repo** | All memories, people, places, photos as markdown + images | **Private** |
| **Your Dropbox folder** | The shared photo pool the "photo prompt" flow draws from | Shared between family members |

## Initial setup

The vault owner does these steps once. Family members later just visit
the URL and sign in.

> **You'll need:** a GitHub account, a Dropbox account, and 15-20 minutes.
> At the end, you'll have a deployed URL like
> `https://<your-username>.github.io/<repo-name>/` that you can share
> with family members.

### 1. Create a private vault repo on GitHub

This is where memories will be stored — separate from the code.

[github.com/new](https://github.com/new) → name it whatever you like
(e.g. `family-vault`) → **Private** → **Create repository**. Leave it
empty (no README, no .gitignore — the app populates it on first save).
You'll grant access to family members later under
**Settings → Collaborators**.

Note `owner/name` (e.g. `chasenunez/family-vault`) — you'll need it as
the `VITE_VAULT_REPO` secret in the Deployment section.

### 2. Fork this code repo (or push your own copy)

Click **Fork** at the top of this repo's page on GitHub, or push the
contents of this folder to your own new repo.

> **The code repo must be public** for free GitHub Pages. That's fine —
> the code holds no personal data. Only the vault repo (step 1) is
> private.

### 3. Register a GitHub OAuth App

The app uses this to sign family members into GitHub from the browser.

Go to **[github.com/settings/developers](https://github.com/settings/developers)**
→ **OAuth Apps** → **New OAuth App**:

| Field | Value |
| --- | --- |
| Application name | `Family Vault` |
| Homepage URL | `https://<your-username>.github.io/<repo-name>/` |
| Authorization callback URL | same as Homepage URL |
| **Enable Device Flow** | ✅ **Check this box** (essential — without it sign-in won't work) |

Click **Register application**.

On the next page, copy the **Client ID** (something like `Iv1.abc123…`)
to a temporary safe place. You'll paste it as a repo secret in the
Deployment section.

> You do **not** need to generate a client secret. Device Flow doesn't
> use one — that's why it's safe for a static site.

### 4. Register a Dropbox App

The app uses this only for the "let a photo prompt a memory" flow.

Go to **[dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)**
→ **Create app**:

| Field | Value |
| --- | --- |
| API | **Scoped access** |
| Type of access | **App folder** (recommended — auto-creates an "Apps/Family Vault" folder in each member's Dropbox), or **Full Dropbox** if you want to share an existing folder |
| Name | `Family Vault` |

After clicking **Create app**:

1. In the **Settings** tab:
   - Copy the **App key** to a temporary safe place.
   - Under **Redirect URIs**, add `https://<your-username>.github.io/<repo-name>/` and click **Add**.

2. In the **Permissions** tab:
   - Enable `files.content.read` and `files.metadata.read`.
   - Click **Submit** at the bottom.

Now create the folder that will hold the photo pool:

- **App folder mode:** Dropbox auto-creates `Apps/Family Vault/` the
  first time a family member authorizes. Each member sees it in their
  own Dropbox; share it as a normal Dropbox shared folder if you want
  everyone seeing the same photos.
- **Full Dropbox mode:** create a folder anywhere (e.g.
  `/Family Vault Photos`), then share it with family members.

Note the folder path you'll use — you'll need it as
`VITE_DROPBOX_PHOTOS_PATH` in the Deployment section.

## Deploying to GitHub Pages

Now wire up the secrets, turn on Pages, and push.

### 1. Enable Pages

On the code repo:

1. Click **Settings** in the repo's top navigation.
2. Click **Pages** in the left sidebar.
3. Under **Build and deployment** → **Source**, select **GitHub Actions**.

That's it. No file needs to be edited — the included
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) handles
the build and publish.

### 2. Add the secrets and variable

Still on the code repo:

1. Click **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** three times and add:

| Secret name | Value |
| --- | --- |
| `VITE_GITHUB_CLIENT_ID` | The Client ID from step 3 of Initial setup |
| `VITE_VAULT_REPO` | `owner/repo` of the **vault** repo, e.g. `chasenunez/family-vault` |
| `VITE_DROPBOX_APP_KEY` | The App key from step 4 of Initial setup |

3. Then switch to the **Variables** tab (same page) and click **New repository variable**:

| Variable name | Value |
| --- | --- |
| `VITE_DROPBOX_PHOTOS_PATH` | Dropbox folder path, e.g. `/Family Vault Photos` (or empty for the App folder root) |

> Secrets are encrypted and never visible after creation. Variables
> aren't — that's fine for `VITE_DROPBOX_PHOTOS_PATH` since the path
> isn't sensitive.

### 3. Trigger the first deploy

A deploy runs automatically every time something is pushed to `main`.
To trigger the first one without code changes, you have two options:

**Option A — run the workflow manually:**

1. Click **Actions** in the top nav.
2. Click **Deploy to GitHub Pages** in the left list.
3. Click the **Run workflow** dropdown → **Run workflow**.

**Option B — push any change:**

```bash
git commit --allow-empty -m "Trigger first deploy"
git push
```

### 4. Verify the deploy

Watch progress under the **Actions** tab. A successful run takes
30-60 seconds and looks like:

- ✅ **build** — installs dependencies + runs `npm run build`
- ✅ **deploy** — uploads the build to GitHub Pages

Then visit your site URL:

```
https://<your-username>.github.io/<repo-name>/
```

> Your username here is whichever account (or organization) **owns the
> code repo**. The repo name is whatever you named the fork in step 2.
> The trailing slash matters.

If you see the **Welcome** page with a "Sign in with GitHub" button —
deploy worked. From here on, every push to `main` redeploys
automatically; no further action needed.

### Updating the app

When you (or anyone) push commits to `main`, the workflow runs again
and updates the live site. Family members see the change on next page
load. No manual step required.

To preview changes locally first:

```bash
cp .env.example .env.local      # fill with your dev values
npm install
npm run dev                      # http://localhost:5173
```

### Troubleshooting

| Symptom | Most likely cause |
| --- | --- |
| **Actions tab is empty, no workflow ran** | Pages source isn't set to **GitHub Actions** yet. Go back to *Deployment step 1*. |
| **Workflow ran but failed at the `build` step** | A `VITE_*` secret is missing or misspelled. The build logs in the Actions tab will name it. Re-check *step 2*. |
| **Workflow succeeded, but the URL shows 404** | Pages can take ~1 minute to propagate after the first deploy. Wait, then hard-refresh. If still 404, confirm the URL has a trailing slash and matches the case of your username/repo. |
| **Page loads but shows "Configuration missing"** | The build deployed without the secrets. Open the deployed page's view-source — if you see `VITE_GITHUB_CLIENT_ID=` literally, the secret wasn't injected. Re-add it under **Settings → Secrets** (not Variables) and re-run the workflow. |
| **Sign in with GitHub does nothing / spins forever** | Some browsers block the Device Flow endpoint due to CORS. Click **"Paste a token instead"** on the login page and use a PAT instead. (See [Authentication detail](#authentication-detail) below.) |
| **Dropbox redirect lands on a Dropbox error page** | The Redirect URI in the Dropbox app settings doesn't match your Pages URL exactly. Open Dropbox app settings and confirm the URI matches your Pages URL, including the trailing slash. |
| **"Could not display [photo].heic"** | iPhone HEIC photos aren't natively renderable in browsers. Either re-upload as JPEG, or limit the Dropbox folder to JPEG/PNG/WebP. |

## Inviting family members

For each person:

1. Vault owner: invite them on the **vault** repo's **Collaborators**
   page (they need at least Write access).
2. They visit the deployed URL.
3. **Sign in to GitHub** — they'll see a 6-character code; they open
   `github.com/login/device` in another tab, paste the code, click
   Authorize. The app picks up the token automatically.
4. **(Optional) Connect Dropbox** — only needed for the photo-prompt
   flow. Click "Connect Dropbox", authorize on the redirect, come back.
5. Pick a display name. Click Enter.

Tokens live in the browser's localStorage. They stay signed in across
visits on that device until they sign out.

## Authentication detail

The app uses GitHub's **Device Flow** by default — no client secret,
no manual token paste. If a particular browser blocks the Device Flow
endpoint (a known CORS issue with some configurations), each user can
fall back to **pasting a Personal Access Token** on the login page:

1. Go to
   [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
   → **Generate new token** → **Fine-grained personal access token**.
2. Scope it to **just the vault repo** with **Contents = Read and
   write**.
3. Paste the token into the "Paste a token instead" field on the
   sign-in page.

## Local development

Requires Node 20+.

```bash
git clone <this repo>
cd neural_web
cp .env.example .env.local      # fill in your dev values
npm install
npm run dev                      # opens http://localhost:5173
```

```bash
npm test                         # vitest unit suite
npm run build                    # production build → ./dist
npm run preview                  # serve the built bundle
npm run check                    # svelte + TS type-check
```

## Project layout

```
src/
├── App.svelte                  Root component, dispatches to pages
├── main.ts                     Mount point
├── styles.css                  Calm theme (cream / sage / serif)
├── lib/
│   ├── config.ts               VITE_* env vars, validated at runtime
│   ├── templates.ts            Schemas: Person / Place / Memory
│   ├── frontmatter.ts          YAML frontmatter read/write
│   ├── parsing.ts              5W → noun-list splitter
│   ├── vault.ts                Path math + slug rules
│   ├── github.ts               REST client + Device Flow + PAT
│   ├── dropbox.ts              OAuth (PKCE) + Files API
│   ├── memory.ts               Save / fill-blanks orchestration
│   ├── router.ts               Hash router
│   └── stores.ts               Auth + session state
└── pages/
    ├── Login.svelte
    ├── Home.svelte
    ├── Freeform.svelte
    ├── Photo.svelte
    └── FillBlanks.svelte

.github/workflows/deploy.yml    Build + deploy to Pages on push to main
legacy/                          The original Streamlit version (preserved)
```

## Vault layout

After the first memory is saved, the vault repo looks like:

```
People/
  Mom.md
  Dad.md
Places/
  Riverside Elementary.md
Memories/
  2026-06-04 The first day of school.md
Photos/
  2026-06-04_a3f7b2.jpg
Templates/
```

Open the vault repo (cloned locally) as an Obsidian vault for graph
view, search, and direct editing.

Each file starts with YAML frontmatter (Name, Lives in, Birthdate,
Parents, Siblings…) followed by a markdown body. Cross-references use
Obsidian-style `[[Wikilinks]]`.

## Security & privacy

- **The vault repo must be private.** It holds family photos, names,
  birth dates, addresses, relationships.
- **Tokens live in the browser's localStorage.** That's safe for a
  static app with no user-provided HTML (no XSS surface). Signing out
  clears them.
- **The OAuth Client IDs are public**, as designed. Device Flow doesn't
  use a client secret. PKCE handles the Dropbox auth without one either.
- **No telemetry, no analytics.** Every operation is a direct call from
  your browser to GitHub or Dropbox.
- **Bigger vaults get slower.** Each fill-blanks load fetches every file
  in the type's folder to inspect its frontmatter. At ~500+ records you
  may want to add caching; the desktop version (in `legacy/`) avoids
  this since it reads from disk.

## What this app deliberately does not do

- **No fuzzy noun matching.** "Mary" and "Mary Smith" produce two files.
  Use the fill-blanks page to clean up.
- **No NLP on the story body.** Only the explicit who/where fields
  produce linked files.
- **No conflict UI.** Concurrent edits to the same file by two family
  members will surface as a GitHub API 409 — refresh and re-save.
- **No authentication beyond GitHub's.** Anyone with collaborator
  access can write to the vault. Trust is at the GitHub repo level.

## License

Copyright (c) 2026 Chase Núñez. Released under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
See [LICENSE](LICENSE) for the full text.

In short:

- **You may** use, modify, and share this software for any
  **noncommercial** purpose.
- **You may not** use it for commercial purposes without a separate
  written license.

## Legacy

The original Python/Streamlit implementation lives in
[`legacy/`](legacy/). It still works as a fully local, offline-capable
vault — useful as reference or for one-machine personal use.
