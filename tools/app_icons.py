#!/usr/bin/env python3
"""App icons: icons/<id>.svg or icons/<id>.png, shown in the Dahlia app store.

The icons come from homarr-labs/dashboard-icons (Apache-2.0). Product names
and logos belong to their owners; they identify the app, nothing more.
tools/icons.json maps an app id to the icon name where the two differ.

    tools/app_icons.py --fetch [ID ...]   download missing icons (or the given ones)

PNGs are scaled to 128x128 (needs Pillow, only for --fetch).

check() is used by tools/check.py: size, PNG signature, SVG without scripts,
event handlers or external references. Dahlia shows icons in <img>, where
scripts never run; the check keeps the files clean anyway.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "icons"
MAX_SIZE = 64 * 1024
PNG_PIXELS = 128
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
SVG_FORBIDDEN = re.compile(
    rb"<script|<foreignObject|<iframe|<embed|<object|\son\w+\s*=|javascript:"
    rb"|(?:xlink:)?href\s*=\s*[\"'](?!#|data:image/)|url\(\s*[\"']?(?!#|data:image/)",
    re.IGNORECASE,
)


def icon_file(app_id: str) -> Path | None:
    for ext in ("svg", "png"):
        f = ICONS / f"{app_id}.{ext}"
        if f.is_file():
            return f
    return None


def check(path: Path) -> str | None:
    """None if the icon is fine, else what is wrong."""
    data = path.read_bytes()
    if len(data) > MAX_SIZE:
        return f"larger than {MAX_SIZE} bytes"
    if path.suffix == ".png":
        return None if data.startswith(PNG_MAGIC) else "not a PNG file"
    if path.suffix != ".svg":
        return "only .svg and .png"
    if b"<svg" not in data[:2048]:
        return "not an SVG file"
    m = SVG_FORBIDDEN.search(data)
    return f"SVG contains {m.group(0).decode(errors='replace')!r}" if m else None


def _get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read(4 * 1024 * 1024)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _small_png(data: bytes) -> bytes:
    import io

    from PIL import Image

    img = Image.open(io.BytesIO(data))
    img.thumbnail((PNG_PIXELS, PNG_PIXELS))
    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


def fetch(ids: list[str]) -> int:
    cfg = json.loads((ROOT / "tools/icons.json").read_text())
    ICONS.mkdir(exist_ok=True)
    missing = []
    for app_id in ids:
        name = cfg["names"].get(app_id, app_id)
        for ext in ("svg", "png"):
            data = _get(f"{cfg['source']}{ext}/{name}.{ext}")
            if data is None:
                continue
            target = ICONS / f"{app_id}.{ext}"
            target.write_bytes(_small_png(data) if ext == "png" else data)
            problem = check(target)
            if problem:
                target.unlink()
                print(f"{app_id}: {ext} skipped, {problem}")
                continue
            print(f"{app_id}: {name}.{ext}")
            break
        else:
            missing.append(app_id)
    for app_id in missing:
        print(f"{app_id}: no icon, Dahlia shows the first letter")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fetch", action="store_true", required=True)
    p.add_argument("ids", nargs="*", help="app ids (default: apps without an icon)")
    args = p.parse_args()
    ids = args.ids or [f.stem for f in sorted((ROOT / "apps").glob("*.yaml"))
                       if icon_file(f.stem) is None]
    return fetch(ids)


if __name__ == "__main__":
    sys.exit(main())
