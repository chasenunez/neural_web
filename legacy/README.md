# Legacy: Streamlit version

This is the original local Streamlit implementation of the Family Vault.
It was superseded by the browser-based version at the repo root (Svelte +
TypeScript, deployed via GitHub Pages).

It is preserved here for two reasons:

1. **Reference.** The data model and module boundaries are the same in
   the new version; this is the readable Python source for any logic the
   TS port has to match (especially `frontmatter.py`, `templates.py`,
   `parsing.py`, `memory_builder.py`).
2. **Local fallback.** If you want a fully offline, single-machine vault
   without GitHub Pages or Dropbox, the Streamlit version still works.

## Running the Streamlit version

```bash
cd legacy
python3 -m venv .venv          # if .venv isn't present
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

See the original setup notes in this folder's `install.sh` for the full
walk-through, including how it generated a macOS `.app` launcher.

## What changed in the new version

| Concern | Streamlit version (here) | Browser version (repo root) |
| --- | --- | --- |
| Runtime | Local Python | Static site on GitHub Pages |
| Vault I/O | Direct filesystem + `git` CLI | GitHub REST API |
| Photos | Local folder, random pick | Dropbox shared folder, random pick |
| Auth | Git auth on the machine | GitHub Device Flow + Dropbox OAuth |
| Install | `./install.sh`, Desktop launcher | Just open the URL |

The data layer (markdown + YAML frontmatter + Obsidian wikilinks) is
unchanged: the new app reads and writes the exact same files in the same
folders, so an existing vault populated by the Streamlit version is
immediately usable by the browser version.
