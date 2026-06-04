# Family Vault

A calm, git-backed memory vault for a small group (≈10 family members). Memories
are markdown files in an Obsidian-compatible structure; people and places are
their own linked files, so the vault grows into a knowledge graph of who-was-where-when.

The app prompts you with one of three flows each visit:

1. **Write a memory in your own words** — who / what / where / when / why + story
2. **Let a photo prompt a memory** — random pick from your personal photo folder, same form below it
3. **Help fill in blank entries** — pages auto-created from earlier memories that need details

Every entry the parser finds (a new person in "who", a new place in "where")
becomes a stub markdown file, which can be filled in later through flow 3. The
vault stays useful when you open it in Obsidian, with `[[Wikilinks]]` and
Dataview-friendly YAML frontmatter.

## Two repos: code vs. vault

This is critical. There are **two separate git repos**:

| Repo | What lives in it | Visibility |
| --- | --- | --- |
| **This repo** (`neural_web`) | The app code | Public is fine |
| **Your vault repo** (you create) | Memories, people, places, photos | **MUST be private** |

The vault repo holds your family's photos, names, and stories. It must be a
**private GitHub repository**. The app never writes anything personal into the
code repo — the code repo and the vault are separate trees on disk.

## First-time setup

### 1. Create a private vault repo

On GitHub, create a new **private** repository (e.g. `your-family-vault`).
Leave it empty — no README, no `.gitignore`. The app will populate it on first run.

### 2. Install the app

```bash
git clone https://github.com/your-org/neural_web.git
cd neural_web
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configure it

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
vault_path: ./vault                                   # local checkout of the vault
git_remote: git@github.com:you/your-family-vault.git  # the private repo from step 1
photos_source: ~/Pictures                             # your personal photo folder
users:
  - name: Mom
    email: mom@example.com
```

`config.yaml` is in `.gitignore` and **must never be committed**. It contains
the path to your private vault and the local photo source — both personal.

### 4. Make sure git auth is set up

The app shells out to `git` for clone/pull/push. Use whatever auth you already
use for that GitHub account:

- **SSH** (recommended): `ssh -T git@github.com` should succeed before running the app
- **HTTPS**: `git config --global credential.helper osxkeychain` (macOS) so pushes don't prompt

The app does **not** manage credentials or tokens. If `git push` works for you
from the command line, it'll work for the app.

### 5. Run it

```bash
.venv/bin/streamlit run app.py
```

It opens in your browser. On first launch it clones the vault repo into
`./vault/`. After that, every launch pulls and every save pushes, attributed
to whatever name you typed at the login screen.

## Adding family members

Each person:

1. Clones this code repo
2. Runs the same install steps
3. Edits `config.yaml` with the same `git_remote` (the private vault URL)
4. Makes sure their GitHub account has read+write access to the vault repo
5. Runs the app, logs in with their own name

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
copy of `config.yaml` can write as "Mom". The login name becomes the git
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

Tests are split into unit suites per module plus two integration tests:
`test_e2e_flow.py` exercises every flow at the data layer, and
`test_ui_smoke.py` drives `app.py` through Streamlit's headless test harness.

To run the app pointed at a throwaway test vault:

```bash
# Edit config.yaml to set git_remote: null and vault_path to a local dir
.venv/bin/streamlit run app.py
```

## What this app deliberately does not do

- **No fuzzy noun matching.** "Mary" and "Mary Smith" produce two files. Merging
  is a future feature; for now the fill-blanks page lets you see and clean up.
- **No NLP on the story body.** Only the explicit who/where fields produce
  linked files.
- **No conflict UI.** If `git pull` fails with a merge conflict, the app
  surfaces the error and you resolve in the vault repo with normal git tools.
- **No authentication.** Login is just identification for commit attribution.
  The trust boundary is the GitHub repo's collaborator list.
