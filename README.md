# Family Vault

A shared, git-backed vault for **episodic memories** — the specific moments
your family has lived through. Each memory is captured with the same 5W
context the brain itself uses to encode an episode (who, what, where,
when, why), and every person and place mentioned becomes its own linked
markdown file. The vault grows into a **neural web** of cross-linked notes:
pull on Grandma's page and every memory she's part of comes with it.

The app prompts users with one of three flows each visit:

1. **Write a memory in your own words** — who / what / where / when / why + story
2. **Let a photo prompt a memory** — random pick from your personal photo folder, same form below it
3. **Help fill in blank entries** — pages auto-created from earlier memories that need details

Every entry the parser finds (a new person in "who", a new place in "where")
becomes a stub markdown file, which can be filled in later through flow 3. The
vault stays useful when you open it in Obsidian, with `[[Wikilinks]]` and
Dataview-friendly YAML frontmatter.

### A note on entering data

Every form field shows an inline hint about what it expects:

- **Single name fields** (e.g. *Partner*, *Lives in*) — one name only
- **List fields** (e.g. *Parents*, *Friends*, *Past Addresses*) — separate
  multiple names with commas, e.g. `Mary Smith, John Smith`
- **Dates** — `YYYY-MM-DD`
- **Google Maps link** — paste a full URL; coordinates will be filled in
  for you

You don't have to fill every field. Empty fields show up in the
*"Help fill in blank entries"* page next session so anyone in the family
can chip away at them over time.

## Two repos: code vs. vault

There are **two separate git repos**:

| Repo | What lives in it | Visibility |
| --- | --- | --- |
| **This repo** (`neural_web`) | The app code | Public |
| **Your vault repo** (you create) | Memories, people, places, photos | **private** |

The vault repo holds photos, names, and stories. It must be a
**private GitHub repository**. The app never writes anything personal into the
code repo — the code repo and the vault are separate trees on disk.

## First-time setup

### 1. Create a private vault repo

On GitHub, create a new **private** repository.
Leave it empty — no README, no `.gitignore`. The app will populate it on first run.

### 2. Install the app

Clone the repo and run the installer. It creates a Python virtual
environment, installs dependencies, copies a starter `config.yaml`, and
drops a launcher on your Desktop.

```bash
git clone https://github.com/your-org/neural_web.git
cd neural_web
./install.sh
```

After it finishes you'll have:

- a working `.venv/` (don't commit it — it's gitignored)
- `config.yaml` ready to edit
- **"Family Vault"** on your Desktop, with a custom icon

The installer is safe to re-run. It updates dependencies, regenerates the
Desktop launcher (useful if you move the repo), and leaves an existing
`config.yaml` untouched.

> **Windows:** `install.sh` is a bash script. Run it under WSL or Git Bash.
> Alternatively, do the steps manually: `python -m venv .venv`,
> `.venv\Scripts\pip install -r requirements.txt`,
> `copy config.example.yaml config.yaml`,
> `.venv\Scripts\python -m familyvault.bin.create_launcher`.

### 3. Configure it

Open `config.yaml` and set `git_remote` to the private repo URL from step 1.
Adjust `photos_source` to point at your personal photo folder. Optionally
add yourself to the `users:` list so commits get a real email address.

`config.yaml` is in `.gitignore` and **must never be committed**. It
contains the path to your private vault and the local photo source — both
personal.

### 4. Make sure git auth is set up

The app shells out to `git` for clone/pull/push. Use whatever auth you
already use for that GitHub account:

- **SSH** (recommended): `ssh -T git@github.com` should succeed before running the app
- **HTTPS**: `git config --global credential.helper osxkeychain` (macOS) so pushes don't prompt

The app does **not** manage credentials or tokens. If `git push` works for
you from the command line, it'll work for the app.

### 5. Run it

Double-click **Family Vault** on your Desktop. The first launch:

- Starts the local Streamlit server in the background
- Opens your default browser to the app
- Clones the vault repo into `./vault/` on the very first run

To quit, right-click the Family Vault icon in the Dock → Quit. Closing the
browser tab alone leaves the server running so the next launch is instant.

Prefer the terminal? `./.venv/bin/streamlit run app.py` still works.

## Adding family members

Each person:

1. Clones this code repo
2. Runs `./install.sh`
3. Edits `config.yaml` with the same `git_remote` (the private vault URL)
4. Makes sure their GitHub account has read+write access to the vault repo
5. Double-clicks "Family Vault" on their Desktop, logs in with their own name

Conflicts are handled by `git pull --rebase --autostash` on save. With ≈10
users mostly editing different memories, conflicts are rare; when they
happen the app surfaces them and you resolve in the vault directory like
any normal git repo.

## Security & privacy notes

**The vault repo must be private.** It will contain photos of your family,
addresses, birth dates, relationships. There is no way to make a public repo
"safe enough" for this data.

**No data leaves your machine except via git push** to the remote you
configured. The app makes no other network calls. No telemetry, no analytics,
no cloud LLM — every operation is local and inspectable.

**Photos live inside the vault repo.** When you select a photo via flow 2, the
file is copied from your `photos_source` into `vault/Photos/` and committed.
This means the photo's bytes go to GitHub. If you don't want that, don't use
flow 2, or point `photos_source` at a folder that doesn't contain anything
sensitive. For larger vaults consider enabling
[Git LFS](https://git-lfs.com/) on the vault repo.

**`config.yaml` is gitignored** in this code repo so you can't accidentally
commit your remote URL or local paths. Check `git status` before committing
anything to this repo.

**Login is identification, not authentication.** Anyone with the app and a
copy of `config.yaml` can write as the same user. The login name becomes the git
commit author so you can see who wrote what, but it is not an access control.
Access control lives at the GitHub repo permissions layer — only invite
trusted collaborators to the vault repo.

**Commit author email** defaults to `<name-slug>@familyvault.local` when not
configured per-user in `config.yaml`. This is fake by design (the app cannot
prove ownership of a real email). Set a real email in `users:` if you want
GitHub to attribute the commit to a real account.

**No secrets in the code repo.** Don't put API keys, tokens, or anything
sensitive in this repo. If you fork it, double-check `.gitignore`.

## Vault layout

After the first memory is saved, the vault looks like:

```
vault/
├── People/
│   ├── Mom.md
│   ├── Dad.md
│   └── Grandma.md
├── Places/
│   └── Riverside Elementary.md
├── Memories/
│   └── 2026-06-04 The first day of school.md
├── Photos/
│   └── 2026-06-04_a3f7b2.jpg
└── Templates/
```

Open this folder as an Obsidian vault for graph view, search, and editing.

Each file starts with YAML frontmatter (the structured fields from the brief —
Name, Lives in, Birthdate, Parents, Siblings…) followed by a markdown body.
Cross-references use Obsidian-style `[[Wikilinks]]`.

## Development

Run the full test suite:

```bash
.venv/bin/python -m pytest tests/ -v
```

The suite is split into focused unit modules (`test_frontmatter`,
`test_parsing`, `test_vault`, `test_templates`, `test_photos`,
`test_config`, `test_memory_builder`, `test_gitops`) plus two integration
suites:

- `test_e2e_flow.py` — exercises every flow at the data layer in a single
  end-to-end scenario (freeform → photo → fill-blanks)
- `test_ui_smoke.py` — drives `app.py` through Streamlit's headless
  `AppTest` harness so the page-routing and form-submission paths are
  exercised without a real browser

To run the app pointed at a throwaway local vault (no git sync), set
`git_remote: null` in `config.yaml` and either double-click the Desktop
launcher or run `./.venv/bin/streamlit run app.py`.

To regenerate the Desktop launcher after moving the repo:

```bash
./.venv/bin/python -m familyvault.bin.create_launcher
```

(`install.sh` calls this automatically as its last step.)

## License

Copyright (c) 2026 Chase Núñez. Released under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
See [LICENSE](LICENSE) for the full text.

In short:

- **You may** use, modify, and share this software for any **noncommercial**
  purpose — personal projects, family use, education, research, hobby work,
  or by a nonprofit or government organization.
- **You may not** use it for commercial purposes (selling it, building a
  paid product on top of it, running it inside a for-profit company's
  workflow, etc.) without a separate written license.

If you'd like to use this commercially, get in touch.
