#!/usr/bin/env python3
"""Derive every website icon from the one canonical ClipForge app icon.

The master is ``branding/clipforge-app-icon.webp``: an exact copy of
``branding/clipforge-app-icon.webp`` in the main ClipForge repository
(branch ``cloud/unified-app-branding``, commit 4dfb882), which is the icon
submitted as the app icon in the TikTok Developer Portal. Its SHA-256 is pinned
below so a different file can never slip in.

Every output is a plain Lanczos resize of the master (no redrawing, cropping or
recolouring). The Open Graph image places the unchanged icon on a black canvas;
the master's own corners are pure black, so the padding is seamless.

    python3 scripts/generate_icons.py           # regenerate after replacing the master
    python3 scripts/generate_icons.py --check   # fail if a committed icon is stale

The outputs are committed, so GitHub Pages needs no build step.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "branding" / "clipforge-app-icon.webp"
MASTER_SHA256 = "1b6115bd57cde23635c11a0a907859034865e455425a28a3b37ead6a578c2f11"
ICONS = ROOT / "assets" / "icons"

PNG_OUTPUTS = {
    ICONS / "favicon-16x16.png": 16,
    ICONS / "favicon-32x32.png": 32,
    ICONS / "favicon-48x48.png": 48,
    ICONS / "apple-touch-icon.png": 180,
    ICONS / "icon-192.png": 192,  # web app manifest, header logo
    ICONS / "icon-512.png": 512,  # web app manifest, home page
}
FAVICON = ROOT / "favicon.ico"
FAVICON_SIZES = [(16, 16), (32, 32), (48, 48)]
OG_IMAGE = ROOT / "assets" / "og-image.png"
OG_SIZE = (1200, 630)


def load_master() -> Image.Image:
    data = MASTER.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != MASTER_SHA256:
        raise SystemExit(f"{MASTER.relative_to(ROOT)} is not the canonical ClipForge icon (sha256 {digest})")
    image = Image.open(io.BytesIO(data))
    if image.width != image.height:
        raise SystemExit(f"{MASTER} must be square, got {image.width}x{image.height}")
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
    return image.convert("RGBA" if has_alpha else "RGB")


def resized(master: Image.Image, size: int) -> Image.Image:
    return master.resize((size, size), Image.Resampling.LANCZOS)


def png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render(master: Image.Image) -> dict[Path, bytes]:
    out = {path: png_bytes(resized(master, size)) for path, size in PNG_OUTPUTS.items()}

    # ICO frames are stored as PNG and must be 32-bit RGBA (decoders reject RGB).
    buf = io.BytesIO()
    resized(master, 256).convert("RGBA").save(buf, format="ICO", sizes=FAVICON_SIZES)
    out[FAVICON] = buf.getvalue()

    width, height = OG_SIZE
    canvas = Image.new("RGB", OG_SIZE, (0, 0, 0))
    canvas.paste(resized(master, height).convert("RGB"), ((width - height) // 2, 0))
    out[OG_IMAGE] = png_bytes(canvas)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a committed icon differs from the master")
    args = parser.parse_args()

    outputs = render(load_master())
    stale = [path for path, data in outputs.items() if not path.exists() or path.read_bytes() != data]
    if args.check:
        for path in stale:
            print(f"stale or missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(outputs[path])
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
