#!/usr/bin/env python3
"""Static checks for the ClipForge website before it is deployed to GitHub Pages.

    python3 scripts/verify_site.py

Checks every HTML page for: the shared icon and manifest tags, local
references that resolve to committed files, no root-absolute paths (the site
is served under /clipforge-site/), absolute Open Graph URLs that map to files,
links to the Privacy Policy and Terms of Service, and the icon files' formats
and dimensions. It also scans the site for anything that looks like a secret.
Needs Pillow for the image checks.
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://benedict-bulitz.github.io/clipforge-site/"
BASE_PATH = "/clipforge-site/"

EXPECTED_ICON_LINKS = {
    ("icon", "favicon.ico"),
    ("icon", "assets/icons/favicon-16x16.png"),
    ("icon", "assets/icons/favicon-32x32.png"),
    ("icon", "assets/icons/favicon-48x48.png"),
    ("apple-touch-icon", "assets/icons/apple-touch-icon.png"),
    ("manifest", "site.webmanifest"),
}
PNG_SIZES = {
    "assets/icons/favicon-16x16.png": (16, 16),
    "assets/icons/favicon-32x32.png": (32, 32),
    "assets/icons/favicon-48x48.png": (48, 48),
    "assets/icons/apple-touch-icon.png": (180, 180),
    "assets/icons/icon-192.png": (192, 192),
    "assets/icons/icon-512.png": (512, 512),
    "assets/og-image.png": (1200, 630),
}
ICO_SIZES = {(16, 16), (32, 32), (48, 48)}
SECRET_PATTERNS = [
    re.compile(r"(?i)(client[_-]?secret|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)localhost:\d+|127\.0\.0\.1"),
]


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []
        self.links: list[dict[str, str]] = []
        self.meta: dict[str, str] = {}
        self.base: str | None = None
        self.ids: set[str] = set()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "base":
            self.base = a.get("href")
        if tag == "link":
            self.links.append(a)
            self.refs.append(a.get("href", ""))
        elif tag in ("a",) and "href" in a:
            self.refs.append(a["href"])
        elif tag in ("img", "script", "source") and ("src" in a or "srcset" in a):
            if "src" in a:
                self.refs.append(a["src"])
            for part in a.get("srcset", "").split(","):
                if part.strip():
                    self.refs.append(part.split()[0])
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def local_target(page: Path, ref: str, base: str | None) -> Path | None:
    """The committed file a relative reference points to, or None for external links."""
    url = urlsplit(ref)
    if url.scheme or ref.startswith("//"):
        return None
    path = url.path
    if not path:
        return page
    if base:
        if not path.startswith("/"):
            path = base + path
        if not path.startswith(BASE_PATH):
            raise ValueError(f"{ref} resolves outside {BASE_PATH}")
        return ROOT / path[len(BASE_PATH):]
    if path.startswith("/"):
        raise ValueError(f"root-absolute path {ref} breaks under {BASE_PATH}")
    return (page.parent / path).resolve()


def main() -> int:
    errors: list[str] = []
    pages = sorted(ROOT.glob("*.html"))
    parsed: dict[str, Page] = {}
    for page in pages:
        p = Page()
        p.feed(page.read_text(encoding="utf-8"))
        parsed[page.name] = p
        name = page.name
        if not p.title.strip():
            errors.append(f"{name}: missing <title>")
        icon_links = {(link.get("rel", ""), urlsplit(link.get("href", "")).path) for link in p.links if link.get("rel") in ("icon", "apple-touch-icon", "manifest")}
        if icon_links != EXPECTED_ICON_LINKS:
            errors.append(f"{name}: icon links {sorted(icon_links)} != expected")
        for ref in p.refs:
            if ref.startswith(("mailto:", "tel:")):
                continue
            try:
                target = local_target(page, ref, p.base)
            except ValueError as exc:
                errors.append(f"{name}: {exc}")
                continue
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"{name}: broken reference {ref}")
                continue
            fragment = urldefrag(ref).fragment
            if fragment and target.suffix == ".html":
                other = parsed.get(target.name) or Page()
                if target.name not in parsed:
                    other.feed(target.read_text(encoding="utf-8"))
                if fragment not in other.ids:
                    errors.append(f"{name}: missing anchor #{fragment} in {target.name}")
        if name != "404.html":
            hrefs = {urlsplit(r).path for r in p.refs}
            for required in ("privacy.html", "terms.html"):
                if required not in hrefs:
                    errors.append(f"{name}: no link to {required}")
            if 'class="brand"' not in page.read_text(encoding="utf-8"):
                errors.append(f"{name}: missing header brand")
            for key in ("description", "og:title", "og:description", "og:url", "og:image", "twitter:card"):
                if not p.meta.get(key):
                    errors.append(f"{name}: missing meta {key}")
            for key in ("og:url", "og:image"):
                value = p.meta.get(key, "")
                if not value.startswith(SITE_URL):
                    errors.append(f"{name}: {key} must be an absolute {SITE_URL} URL")
                    continue
                rel = value[len(SITE_URL):] or "index.html"
                if not (ROOT / rel).is_file():
                    errors.append(f"{name}: {key} {value} has no file")
            canonical = [link.get("href") for link in p.links if link.get("rel") == "canonical"]
            expected = SITE_URL + ("" if name == "index.html" else name)
            if canonical != [expected]:
                errors.append(f"{name}: canonical {canonical} != {expected}")

    for rel, size in PNG_SIZES.items():
        with Image.open(ROOT / rel) as im:
            if im.format != "PNG" or im.size != size:
                errors.append(f"{rel}: {im.format} {im.size}, expected PNG {size}")
    with Image.open(ROOT / "favicon.ico") as ico:
        if ico.format != "ICO" or set(ico.info.get("sizes", ())) != ICO_SIZES:
            errors.append(f"favicon.ico: {ico.format} frames {ico.info.get('sizes')}, expected {sorted(ICO_SIZES)}")

    manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
    for icon in manifest.get("icons", []):
        path = ROOT / icon["src"]
        if not path.is_file():
            errors.append(f"site.webmanifest: missing {icon['src']}")
            continue
        with Image.open(path) as im:
            if f"{im.width}x{im.height}" != icon["sizes"]:
                errors.append(f"site.webmanifest: {icon['src']} is {im.size}, declared {icon['sizes']}")
    for key in ("start_url", "scope"):
        if manifest.get(key, "").startswith("/"):
            errors.append(f"site.webmanifest: {key} must be relative for {BASE_PATH}")

    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file() or path.suffix not in (".html", ".css", ".js", ".json", ".webmanifest", ".md", ".txt", ".py"):
            continue
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                errors.append(f"{path.relative_to(ROOT)}: possible secret or private endpoint: {match.group(0)[:40]}")

    for error in errors:
        print(f"FAIL {error}", file=sys.stderr)
    print(f"{len(pages)} pages checked, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
