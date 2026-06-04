"""Create a platform-appropriate Family Vault launcher on the user's Desktop.

Run via ``python -m familyvault.bin.create_launcher``. Called from ``install.sh``
as the last step so a non-technical family member only has to:

  1. clone the repo
  2. run ``./install.sh``
  3. double-click "Family Vault" on the Desktop

On macOS a real .app bundle is produced (with a generated custom icon) so the
Dock and Finder treat it like any other app. Linux and Windows get equivalent
launchers (.desktop file and .bat respectively) since the bundle format
doesn't exist there.
"""

from __future__ import annotations

import math
import plistlib
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# Project root = two levels up from this file (.../familyvault/bin/create_launcher.py).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DESKTOP = Path.home() / "Desktop"
DEFAULT_PORT = 8765


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> int:
    DESKTOP.mkdir(parents=True, exist_ok=True)

    if sys.platform == "darwin":
        path = _create_macos_app()
    elif sys.platform.startswith("linux"):
        path = _create_linux_desktop()
    elif sys.platform.startswith("win"):
        path = _create_windows_launcher()
    else:
        print(f"Unsupported platform: {sys.platform}. No launcher created.")
        return 1

    print(f"Launcher created: {path}")
    return 0


# ── macOS ───────────────────────────────────────────────────────────────────


_MACOS_LAUNCHER_SCRIPT = r"""#!/bin/bash
set -e
INSTALL_DIR="{install_dir}"
PORT={port}

cd "$INSTALL_DIR"

# If the server is already running, just open the browser.
if curl -fsS "http://localhost:$PORT/_stcore/health" >/dev/null 2>&1; then
    open "http://localhost:$PORT"
    exit 0
fi

# Start Streamlit in the background.
.venv/bin/streamlit run app.py \
    --server.port "$PORT" \
    --server.headless true \
    --browser.gatherUsageStats false &
STREAMLIT_PID=$!

# When the .app process is killed (e.g. via Dock → Quit), shut Streamlit down too.
trap 'kill $STREAMLIT_PID 2>/dev/null || true; exit 0' EXIT INT TERM

# Wait up to 30 seconds for the server to be ready.
for _ in $(seq 1 60); do
    if curl -fsS "http://localhost:$PORT/_stcore/health" >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

open "http://localhost:$PORT"

# Keep the .app alive while Streamlit runs so Dock → Quit can kill it cleanly.
wait $STREAMLIT_PID
"""


def _create_macos_app() -> Path:
    app_dir = DESKTOP / "Family Vault.app"
    if app_dir.exists():
        shutil.rmtree(app_dir)

    contents = app_dir / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    # Info.plist
    plist = {
        "CFBundleName": "Family Vault",
        "CFBundleDisplayName": "Family Vault",
        "CFBundleExecutable": "familyvault",
        "CFBundleIdentifier": "com.familyvault.app",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "CFBundleIconFile": "AppIcon",
        "CFBundlePackageType": "APPL",
        "LSMinimumSystemVersion": "10.13",
        "NSHighResolutionCapable": True,
    }
    with (contents / "Info.plist").open("wb") as f:
        plistlib.dump(plist, f)

    # Executable
    launcher = macos / "familyvault"
    launcher.write_text(
        _MACOS_LAUNCHER_SCRIPT.format(install_dir=PROJECT_ROOT, port=DEFAULT_PORT)
    )
    _make_executable(launcher)

    # Icon
    try:
        _generate_macos_icns(resources / "AppIcon.icns")
    except Exception as e:
        # Icon is cosmetic — failing to generate it shouldn't break the install.
        print(f"  (skipping icon: {e})")

    return app_dir


def _generate_macos_icns(out_path: Path) -> None:
    """Build an .icns from a generated PNG iconset using macOS's iconutil."""
    iconset = out_path.parent / "AppIcon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()

    sizes = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    for name, size in sizes:
        _draw_icon(size).save(iconset / name)

    try:
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(out_path)],
            check=True,
            capture_output=True,
        )
    finally:
        shutil.rmtree(iconset, ignore_errors=True)


def _draw_icon(size: int):
    """Generate a calm, app-matching icon: sage rounded square with three
    connected circles representing the neural web of memories."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    sage = (143, 166, 142, 255)
    cream = (250, 247, 242, 255)

    pad = max(1, size // 16)
    corner = max(2, size // 5)
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=corner,
        fill=sage,
    )

    cx, cy = size // 2, size // 2
    orbit = max(2, size // 5)
    node_r = max(2, size // 14)
    line_w = max(1, size // 60)

    points = []
    for i in range(3):
        angle = math.pi / 2 + i * 2 * math.pi / 3
        px = cx + int(orbit * math.cos(angle))
        py = cy - int(orbit * math.sin(angle))
        points.append((px, py))

    for i in range(3):
        draw.line([points[i], points[(i + 1) % 3]], fill=cream, width=line_w)

    for px, py in points:
        draw.ellipse([px - node_r, py - node_r, px + node_r, py + node_r], fill=cream)

    return img


# ── Linux ───────────────────────────────────────────────────────────────────


_LINUX_DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=Family Vault
Comment=A shared episodic memory vault
Exec=bash -c 'cd "{install_dir}" && .venv/bin/streamlit run app.py --server.port {port} --server.headless true & sleep 2 && xdg-open http://localhost:{port}'
Terminal=false
Categories=Office;
"""


def _create_linux_desktop() -> Path:
    out = DESKTOP / "Family Vault.desktop"
    out.write_text(
        _LINUX_DESKTOP_ENTRY.format(install_dir=PROJECT_ROOT, port=DEFAULT_PORT)
    )
    _make_executable(out)
    return out


# ── Windows ─────────────────────────────────────────────────────────────────


_WINDOWS_BAT = """@echo off
cd /d "{install_dir}"
start "" .venv\\Scripts\\streamlit.exe run app.py --server.port {port} --server.headless true
timeout /t 3 /nobreak >nul
start "" http://localhost:{port}
"""


def _create_windows_launcher() -> Path:
    out = DESKTOP / "Family Vault.bat"
    out.write_text(
        _WINDOWS_BAT.format(install_dir=str(PROJECT_ROOT), port=DEFAULT_PORT)
    )
    return out


# ── Shared ──────────────────────────────────────────────────────────────────


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    raise SystemExit(main())
