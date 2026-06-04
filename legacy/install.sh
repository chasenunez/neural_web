#!/usr/bin/env bash
#
# Install Family Vault on this machine.
#
# Creates a virtual environment, installs dependencies, copies the example
# config if there isn't one yet, and places a launcher on the Desktop so the
# app can be double-clicked like any other application.
#
# Safe to re-run: it skips work that's already done and overwrites only the
# Desktop launcher (in case you moved the repo since the last install).

set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "Installing Family Vault in $ROOT"
echo ""

# ── 1. Check Python ─────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    cat <<MSG
ERROR: python3 is not installed.

  macOS : install via https://python.org or 'brew install python'
  Linux : 'sudo apt install python3 python3-venv' or your distro's equivalent
MSG
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "→ Python ${PY_VERSION}"

# ── 2. Virtual environment + deps ───────────────────────────────────────────
if [ ! -d .venv ]; then
    echo "→ Creating virtual environment in .venv"
    python3 -m venv .venv
else
    echo "→ Using existing virtual environment in .venv"
fi

echo "→ Installing dependencies"
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

# ── 3. Local config ─────────────────────────────────────────────────────────
if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "→ Created config.yaml from template."
    echo "  IMPORTANT: edit config.yaml and set 'git_remote' to your private vault repo URL."
else
    echo "→ config.yaml already present (not overwritten)"
fi

# ── 4. Desktop launcher ─────────────────────────────────────────────────────
echo "→ Creating Desktop launcher"
./.venv/bin/python -m familyvault.bin.create_launcher

# ── 5. Done ─────────────────────────────────────────────────────────────────
cat <<MSG

────────────────────────────────────────────────────────────────────
 Install complete.

 Next steps:
   1. Open config.yaml and set 'git_remote' to your private
      GitHub vault repository URL.
   2. Double-click "Family Vault" on your Desktop to launch.

 (If git_remote is left as 'null', the app runs in local-only
 mode — no clone, no push, no pull.)
────────────────────────────────────────────────────────────────────
MSG
