#!/usr/bin/env python3
"""Check the catalog: every template against the parser Dahlia itself uses
(dahlia_agent.apps from dahlia-linux), the catalog's own rules, and that
catalog.json matches apps/.

Catalog rules on top of the parser: schema 2 (3 only with gpu), German and English texts,
pinned tags (major.minor or a date), web and LAN ports unique across the
catalog, every image in block style ("image: ..." on its own line, which
tools/bump.py relies on). Icons in icons/ belong to an app and pass
app_icons.check().

Usage: tools/check.py --linux <path to a dahlia-linux checkout> [--images]
--images also checks in the registries that each image exists.
"""

import argparse
import sys
from pathlib import Path

import app_icons
import build
import registry
import versions

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--linux", required=True, help="path to a dahlia-linux checkout")
    p.add_argument("--images", action="store_true", help="check that the images exist")
    args = p.parse_args()

    sys.path.insert(0, str(Path(args.linux) / "packages/dahlia-agent/usr/lib/python3/dist-packages"))
    from dahlia_agent.apps import AppError, parse_template

    errors = []
    templates = []
    for f in sorted((ROOT / "apps").glob("*.yaml")):
        text = f.read_text(encoding="utf-8")
        try:
            t = parse_template(text, f.stem)
        except AppError as e:
            errors.append(f"apps/{f.name}: {e}")
            continue
        where = f"apps/{f.name}"
        # Schema 3 only where needed: older Dahlia versions skip those templates.
        if t.schema != (3 if t.gpu else 2):
            errors.append(f"{where}: use schema {3 if t.gpu else 2}")
        for key in ("description", "notes"):
            texts = getattr(t, key)
            if key == "description" or texts:
                for lang in ("de", "en"):
                    if not texts.get(lang):
                        errors.append(f"{where}: {key}.{lang} is missing")
        for s in t.services.values():
            tag = s.image.split("@")[0].rsplit(":", 1)[1]
            if not versions.pinned(tag):
                errors.append(f"{where}: {s.image} is not a pinned version")
            if f"image: {s.image}\n" not in text:
                errors.append(f"{where}: write 'image: {s.image}' on its own line")
        templates.append(t)

    ports = {}
    for t in templates:
        used = [(t.public_port, "web")] if t.public_port else []
        used += [(lp.host, lp.protocol) for lp in t.lan_ports]
        for port, kind in used:
            # The web port is TCP behind nginx; a LAN TCP port on the same number clashes.
            key = (port, "tcp" if kind == "web" else kind)
            other = ports.get(key)
            if other and other != t.id:
                errors.append(f"port {port}/{key[1]} is used by {other} and {t.id}")
            ports[key] = t.id

    ids = {t.id for t in templates}
    for f in sorted(app_icons.ICONS.iterdir()) if app_icons.ICONS.is_dir() else []:
        if f.stem not in ids:
            errors.append(f"icons/{f.name}: no app with this id")
        elif f.suffix == ".png" and (app_icons.ICONS / f"{f.stem}.svg").exists():
            errors.append(f"icons/{f.name}: there is an SVG too, keep one")
        elif problem := app_icons.check(f):
            errors.append(f"icons/{f.name}: {problem}")

    if (ROOT / "catalog.json").read_text(encoding="utf-8") != build.bundle():
        errors.append("catalog.json is out of date, run tools/build.py")
    if (ROOT / "index.json").exists():
        errors.append("index.json is not used any more, Dahlia reads catalog.json")

    if args.images:
        seen = set()
        for t in templates:
            for s in t.services.values():
                if s.image in seen:
                    continue
                seen.add(s.image)
                try:
                    ok = registry.exists(s.image)
                except registry.RegistryError as e:
                    errors.append(f"{t.id}: {e}")
                    continue
                if ok:
                    print(f"ok {s.image}")
                else:
                    errors.append(f"{t.id}: image {s.image} not found")

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    print(f"{len(templates)} templates checked, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
