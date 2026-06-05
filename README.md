# Neural Web

A shared graph of nodes — people, places, and the moments that link
them. Each node is a markdown file in a private GitHub repo. The graph
grows whenever anyone in the network adds a note.

The app runs in the browser, deployed from GitHub Pages. There is no
backend. The vault repo (your data) stays private; the code repo (this
one) can be public.

## How it works

Three flows for adding nodes and edges:

1. **Write a note.** Capture an event with who/what/where/when/why and
   a description. Any new name in "who" or "where" becomes its own
   linked node.
2. **Photo prompt.** A random image from a shared Dropbox folder seeds
   the same form.
3. **Fill in blanks.** Nodes created as side-effects of other notes
   start empty. Anyone with access can come back and add detail.

Cross-references use Obsidian-style `[[Wikilinks]]`. The vault opens
cleanly in Obsidian for graph view, search, and direct editing.

## What lives where

| Component | Holds | Visibility |
| --- | --- | --- |
| This code repo | App source (Svelte + TypeScript) | Public |
| Your vault repo | The graph: people, places, events, photos | Private |
| Shared Dropbox folder | The photo pool the "photo prompt" flow draws from | Shared |

## Initial setup

You'll need a GitHub account, a Dropbox account, and about 20 minutes.
At the end you'll have a URL like
`https://<username>.github.io/<repo-name>/` to share with collaborators.

### 1. Create a private vault repo on GitHub

This is where the graph data lives, separate from the code.

[github.com/new](https://github.com/new) → name it whatever you like →
**Private** → **Create repository**. Leave it empty (no README, no
.gitignore — the app populates it on first save).

Note `owner/name`. You'll need it as the `VITE_VAULT_REPO` secret.

### 2. Fork this code repo

Click **Fork** at the top of this repo's page, or push the contents of
this folder to a new repo of your own.

The code repo must be public for free GitHub Pages. The code holds no
personal data; everything personal lives in the private vault repo.

### 3. Register a GitHub OAuth App

The app uses this to authenticate users from the browser.

[github.com/settings/developers](https://github.com/settings/developers)
→ **OAuth Apps** → **New OAuth App**:

| Field | Value |
| --- | --- |
| Application name | Anything (e.g. your project name) |
| Homepage URL | `https://<username>.github.io/<repo-name>/` |
| Authorization callback URL | Same as Homepage URL |
| Enable Device Flow | Yes — check this box |

Register, then copy the **Client ID**. You don't need a client secret;
Device Flow doesn't use one.

### 4. Register a Dropbox App

Only required for the photo-prompt flow.

[dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
→ **Create app**:

| Field | Value |
| --- | --- |
| API | Scoped access |
| Access | App folder (recommended) or Full Dropbox |
| Name | Anything |

After creating:

- In **Settings**: copy the **App key**, and add your Pages URL under
  **Redirect URIs**.
- In **Permissions**: enable `files.content.read` and
  `files.metadata.read`, then click **Submit**.

Create a folder for the photo pool (e.g. `/Shared Photos` or just use
the App folder root). Note the path — you'll need it as
`VITE_DROPBOX_PHOTOS_PATH`.

## Deploying to GitHub Pages

### 1. Enable Pages

Repo **Settings** → **Pages** → **Source** = **GitHub Actions**.

The included [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
handles build and publish. No file needs to be edited.

### 2. Add secrets and a variable

Repo **Settings** → **Secrets and variables** → **Actions**.

Add three secrets:

| Name | Value |
| --- | --- |
| `VITE_GITHUB_CLIENT_ID` | Client ID from Initial setup step 3 |
| `VITE_VAULT_REPO` | `owner/repo` of your private vault repo |
| `VITE_DROPBOX_APP_KEY` | App key from Initial setup step 4 |

And one variable (the **Variables** tab on the same page):

| Name | Value |
| --- | --- |
| `VITE_DROPBOX_PHOTOS_PATH` | Dropbox folder path (or empty for App folder root) |

### 3. Trigger the first deploy

The workflow runs on every push to `main`. To kick off the first run
without code changes:

- **Actions** tab → **Deploy to GitHub Pages** → **Run workflow**.

Or push an empty commit:

```bash
git commit --allow-empty -m "Trigger first deploy"
git push
```

### 4. Verify

Watch the run under **Actions**. A successful build/deploy takes about
30–60 seconds. Then open `https://<username>.github.io/<repo-name>/`
(the trailing slash matters).

If you see the **Welcome** page, you're done. Every push to `main` will
redeploy from now on.

### Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Actions tab is empty, no workflow ran | Pages source isn't set to **GitHub Actions** yet. |
| Workflow failed at the `build` step | A `VITE_*` secret is missing or misspelled. Check the build logs for the exact name. |
| URL returns 404 after a successful deploy | First deploy can take ~1 minute to propagate. Wait and hard-refresh. Confirm the URL has a trailing slash. |
| Page loads but shows "Configuration missing" | Secrets weren't injected into the build. Re-add them under **Settings → Secrets** (not Variables) and re-run. |
| "Sign in with GitHub" spins forever | Browser blocked the Device Flow endpoint. Use **"Paste a token instead"** with a PAT. |
| Dropbox redirect lands on an error page | The Redirect URI in Dropbox app settings doesn't match the Pages URL exactly (case + trailing slash). |
| HEIC photo won't display | Browsers can't render HEIC. Use JPEG/PNG/WebP in the Dropbox folder. |
| Push rejected with "workflow scope" error | Your PAT doesn't have permission to modify workflow files. Either add the `workflow` scope to it, or use SSH for code pushes. |

## Granting access to collaborators

For each person who should be able to read or write:

1. On the **vault** repo: **Settings → Collaborators → Add people**.
   Write access is the minimum.
2. They visit the Pages URL.
3. **Sign in to GitHub.** They'll see a short code; they open
   `github.com/login/device` in a new tab, paste the code, click
   Authorize. The app picks up the token automatically.
4. **(Optional) Connect Dropbox.** Only needed for the photo-prompt
   flow.
5. Pick a display name. Enter.

Tokens live in the browser's localStorage. Users stay signed in across
visits on that device until they sign out.

## Authentication

GitHub Device Flow is the default. No client secret, no token-pasting.
Some browsers block the Device Flow endpoint due to CORS. The login
page exposes a fallback: paste a Personal Access Token instead.

To create one:

1. [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
   → **Generate new token** → **Fine-grained personal access token**.
2. Scope to the vault repo with **Contents = Read and write**.
3. Paste into the "Paste a token instead" field on the sign-in page.

## Local development

Requires Node 20+.

```bash
git clone <this repo>
cd neural_web
cp .env.example .env.local      # fill with your values
npm install
npm run dev                      # http://localhost:5173
```

```bash
npm test                         # unit suite
npm run build                    # production build → ./dist
npm run preview                  # serve the built bundle
npm run check                    # type-check
```

## Project layout

```
src/
├── App.svelte                  Root, dispatches to pages
├── main.ts                     Mount point
├── styles.css                  Theme
├── lib/
│   ├── config.ts               VITE_* env vars
│   ├── templates.ts            Schemas: Person / Place / Memory
│   ├── frontmatter.ts          YAML frontmatter read/write
│   ├── parsing.ts              5W noun splitter
│   ├── vault.ts                Path math, slug rules
│   ├── github.ts               REST + Device Flow + PAT
│   ├── dropbox.ts              OAuth (PKCE) + Files API
│   ├── memory.ts               Save + fill-blanks orchestration
│   ├── router.ts               Hash router
│   └── stores.ts               Auth + session state
└── pages/
    ├── Login.svelte
    ├── Home.svelte
    ├── Freeform.svelte
    ├── Photo.svelte
    └── FillBlanks.svelte

.github/workflows/deploy.yml    Build + publish on push to main
legacy/                          Earlier Streamlit implementation
```

## Vault layout

After the first note is saved, the vault repo looks like:

```
People/
  Mary Smith.md
  Alex Jones.md
Places/
  Riverside Park.md
Memories/
  2026-06-04 Picnic.md
Photos/
  2026-06-04_a3f7b2.jpg
Templates/
```

Each file starts with YAML frontmatter (Name, Lives in, Birthdate,
Parents, Siblings…) followed by a markdown body. Cross-references use
Obsidian-style `[[Wikilinks]]`.

Open the vault repo (cloned locally) as an Obsidian vault for graph
view, search, and direct editing.

## Security & privacy

The vault repo must be private. It contains photos, names, dates,
locations, and relationships.

Tokens live in the browser's localStorage. That's safe for a static app
with no user-provided HTML — there's no XSS surface. Signing out clears
them.

OAuth Client IDs are public by design. Device Flow doesn't use a client
secret; PKCE covers Dropbox auth without one either.

No telemetry, no analytics. Every operation is a direct call from the
browser to GitHub or Dropbox.

Large vaults get slower. Each fill-blanks load fetches every file in
the type's folder to inspect frontmatter. At ~500+ records you'll want
to add caching; the older Streamlit version in `legacy/` avoids this by
reading from disk.

## Limitations

- No fuzzy name matching. "Mary" and "Mary Smith" produce two separate
  nodes. Use fill-blanks to clean up.
- No NLP on the story body. Only the explicit who/where fields become
  linked nodes.
- No conflict UI. Concurrent edits to the same file by two collaborators
  surface as a GitHub API 409. Refresh, re-save.
- No authentication beyond GitHub's. Anyone with collaborator access
  can write. Trust lives at the repo collaborator list.

## License

Copyright (c) 2026 Chase Núñez. Released under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
See [LICENSE](LICENSE).

In short: use, modify, and share for any noncommercial purpose. Get
in touch for commercial licensing.

## Legacy

The earlier Python/Streamlit implementation lives in [`legacy/`](legacy/).
It works as a fully local, offline-capable vault — useful as reference
or for single-machine personal use.
