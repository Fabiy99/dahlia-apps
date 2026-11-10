#!/usr/bin/env python3
"""Check the catalog: index.json against apps/, every template against the
parser Dahlia itself uses (dahlia_agent.apps from dahlia-linux), and the
catalog's own rules (German and English description).

Usage: tools/check.py --linux <path to a dahlia-linux checkout> [--images]
--images also checks with `docker manifest inspect` that each image exists.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--linux", required=True, help="path to a dahlia-linux checkout")
    p.add_argument("--images", action="store_true", help="check that the images exist")
    args = p.parse_args()

    sys.path.insert(0, str(Path(args.linux) / "packages/dahlia-agent/usr/lib/python3/dist-packages"))
    from dahlia_agent.apps import AppError, parse_template

    errors = []
    index = json.loads((ROOT / "index.json").read_text())
    ids = index.get("apps", [])
    files = sorted(f.stem for f in (ROOT / "apps").glob("*.yaml"))
    if ids != sorted(ids):
        errors.append("index.json: keep the apps sorted")
    if len(set(ids)) != len(ids):
        errors.append("index.json: duplicate ids")
    for missing in sorted(set(ids) - set(files)):
        errors.append(f"index.json lists {missing}, but apps/{missing}.yaml is missing")
    for extra in sorted(set(files) - set(ids)):
        errors.append(f"apps/{extra}.yaml is not listed in index.json")

    templates = []
    for app_id in files:
        try:
            t = parse_template((ROOT / "apps" / f"{app_id}.yaml").read_text(), app_id)
        except AppError as e:
            errors.append(f"apps/{app_id}.yaml: {e}")
            continue
        for lang in ("de", "en"):
            if not t.description.get(lang):
                errors.append(f"apps/{app_id}.yaml: description.{lang} is missing")
        templates.append(t)

    ports = {}
    for t in templates:
        for port in [t.public_port] + [lp.host for lp in t.lan_ports]:
            if port is None:
                continue
            key = port
            other = ports.get(key)
            if other and other != t.id:
                errors.append(f"port {port} is used by {other} and {t.id}")
            ports[key] = t.id

    if args.images:
        for t in templates:
            proc = subprocess.run(["docker", "manifest", "inspect", t.image],
                                  capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                errors.append(f"{t.id}: image {t.image} not found")
            else:
                print(f"ok {t.image}")

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    print(f"{len(templates)} templates checked, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
