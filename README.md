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

### 4. Set up GitHub authentication

The app automatically pulls from the vault repo when it launches and
pushes after every save. For that to work, your computer needs to talk
to GitHub without prompting you for a password each time.

**Follow the [Git authentication setup](#git-authentication-setup)
section near the bottom of this README before continuing.** It walks
through generating a Personal Access Token on GitHub, storing it in your
OS's secure credential store, and doing a one-time terminal
authentication so the Desktop app works silently afterward.

The app itself does **not** manage credentials. If `git push` works for
you from the terminal, it'll work for the app.

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

## Git authentication setup

The app pulls from the vault repo on every launch and pushes after every
save — silently, with no prompts. To make that work on a fresh computer
you need to give git a Personal Access Token (PAT) once, and it gets
stored in your operating system's secure credential store. Future git
operations use the stored token automatically.

> **A note on the order of steps.** The Desktop launcher runs git in the
> background where it can't show password prompts. **You must complete
> the terminal authentication step (step 5 below) before you double-click
> the Desktop launcher for the first time.** Otherwise git will silently
> hang waiting for input you can't see.

### Before you start

You need three things:

1. **A GitHub account.** Sign up free at
   [github.com/join](https://github.com/join) if you don't have one.

2. **Collaborator access to the vault repo.** The person who created the
   private vault repo (the "vault owner") must invite you as a
   collaborator. They do this on the vault repo on GitHub:
   **Settings → Collaborators → Add people**, then search for your
   GitHub username and send the invite. Accept the invite in your email
   or at [github.com/notifications](https://github.com/notifications)
   before continuing.

3. **Git installed on your computer.** Check with `git --version` in a
   terminal. If it's missing:
   - **macOS** — running `git` once will prompt to install Xcode Command
     Line Tools; accept.
   - **Windows** — install [Git for Windows](https://git-scm.com/download/win).
   - **Linux** — `sudo apt install git` (Debian/Ubuntu) or your distro's
     equivalent.

### Step 1 — Generate a Personal Access Token on GitHub

A Personal Access Token is a long random string that acts like a
password, but is scoped to specific repositories and specific
permissions.

1. Go to **[github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)**.
   (Or: click your profile picture → **Settings** → **Developer
   settings** in the left sidebar → **Personal access tokens** →
   **Fine-grained tokens**.)
2. Click the green **Generate new token** button at the top right.
3. Fill in the form exactly like this:

   | Field | What to enter |
   | --- | --- |
   | **Token name** | Something memorable like `Family Vault on MacBook` |
   | **Expiration** | 1 year (the maximum). Set a calendar reminder to renew it. |
   | **Description** | Optional. e.g. "Used by the Family Vault app to push memories." |
   | **Resource owner** | Your own account (the default) |
   | **Repository access** | Select **Only select repositories**, then click **Select repositories** and pick **just the vault repo**. Do not give it access to anything else. |
   | **Repository permissions → Contents** | Change from "No access" to **Read and write** |
   | **Repository permissions → Metadata** | This auto-changes to **Read-only**. Leave it. |
   | All other permissions | Leave at "No access" |

4. Scroll to the bottom and click **Generate token**.
5. **GitHub now shows your token. Copy it immediately into a temporary
   safe place** (a sticky note app, a password manager — anywhere you can
   read it in 2 minutes). The token starts with `github_pat_` and is
   about 90 characters long.

   **You will not be able to see it again.** If you close the page
   without copying it, you have to delete the token and generate a new
   one.

### Step 2 — Tell git to remember credentials securely

Run **one** of the following in your terminal, matching your operating
system. This is a one-time setup.

**macOS**

```bash
git config --global credential.helper osxkeychain
```

This stores tokens in the macOS Keychain.

**Windows** (using Git for Windows, which is what you installed above)

```bash
git config --global credential.helper manager
```

This stores tokens in the Windows Credential Manager.

**Linux** — install the secret-storage helper, then configure git to use it:

```bash
sudo apt install -y libsecret-1-0 libsecret-1-dev
sudo make --directory=/usr/share/doc/git/contrib/credential/libsecret
git config --global credential.helper /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret
```

(If you don't want to compile the helper, you can fall back to
`git config --global credential.helper "cache --timeout=86400"` for a
24-hour in-memory cache, but you'll have to re-enter the token every
day.)

### Step 3 — Use the HTTPS form of the vault URL in config.yaml

Open `config.yaml` (in this code repo, the one you cloned) and set:

```yaml
git_remote: https://github.com/OWNER/VAULT-REPO.git
```

Replace `OWNER` with the GitHub username/org that owns the vault, and
`VAULT-REPO` with the repo name. **Note `https://` — not `git@`.** SSH
URLs won't use your token.

### Step 4 — Authenticate once in the terminal

This is the step that's easy to skip but essential: you need to trigger
**one** git operation in your terminal so git asks for your username +
token and stores them. The Desktop app can't show password prompts, so
this has to happen here first.

From inside the code repo's folder, run:

```bash
git ls-remote https://github.com/OWNER/VAULT-REPO.git
```

(Use the exact URL you put in `config.yaml`.)

The first time, git will ask:

```
Username for 'https://github.com': <type your GitHub username>
Password for 'https://USERNAME@github.com': <paste your token>
```

Important details:

- **Username** is your GitHub username (not your email).
- **Password** is the PAT from step 1 — *not* your GitHub login
  password. (GitHub stopped accepting account passwords for git
  operations in 2021.)
- When you paste the token, **nothing will appear on screen**. That's
  the terminal hiding your password — it's normal. Just paste and press
  Enter.

If it worked, git prints a list of commit hashes (something like
`abc123…  HEAD`). Your token is now stored in your OS's credential store.

If it asks again or you see "Authentication failed":

- You may have typed the wrong username, or pasted the wrong thing
  into "Password".
- Re-run the command and try again. If it keeps failing, delete the
  stored credential (see "Renewing the token" below) and re-paste.

### Step 5 — You're done

You can now safely delete your temporary copy of the token. Git stored
it in the OS credential store; you'll never need to type it again until
it expires.

Launch the Desktop app and the first memory you save will push
automatically.

### Renewing the token (every ~1 year)

When the token expires, the app will fail to push and show a git error
message in the UI. To fix:

1. Generate a new PAT (repeat Step 1).
2. Delete the old stored credential so git asks for the new one:

   - **macOS:** open **Keychain Access**, search for `github.com`,
     right-click the entry, **Delete**.
   - **Windows:** open **Credential Manager** (search for it in Start),
     **Windows Credentials**, find `git:https://github.com`, click
     **Remove**.
   - **Linux (libsecret):** `secret-tool clear protocol https host github.com`
     (or use a tool like Seahorse to delete it manually).

3. Re-run the `git ls-remote` command from Step 4 and paste the new
   token when prompted.

### Alternative: SSH key instead of a PAT

Prefer SSH? It doesn't expire, and once set up it's invisible. The
trade-off is that the setup is a bit more conceptual (public/private
keys, ssh-agent).

In short:

1. `ssh-keygen -t ed25519 -C "your-github-email@example.com"`
   (accept defaults; no passphrase is fine on a personal machine).
2. On macOS, append to `~/.ssh/config`:
   `Host github.com\n  UseKeychain yes\n  AddKeysToAgent yes\n  IdentityFile ~/.ssh/id_ed25519`
   and run `ssh-add --apple-use-keychain ~/.ssh/id_ed25519`.
   On Linux: `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519`.
3. Copy `~/.ssh/id_ed25519.pub` to your clipboard and add it at
   [github.com/settings/keys](https://github.com/settings/keys) →
   **New SSH key**.
4. Test with `ssh -T git@github.com`.
5. Use the SSH form of the vault URL in `config.yaml`:
   `git_remote: git@github.com:OWNER/VAULT-REPO.git`.

After that, no terminal authentication step is needed — SSH doesn't
prompt — so you can go straight to launching the app.

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
