#!/usr/bin/env python3
"""Write catalog.json: all templates from apps/ in one file, plus the icons.

Dahlia (0.4 and later) downloads this file. "icons" maps an app id to its
file in icons/ and the file's SHA-256; Dahlia (0.8 and later) downloads an
icon only when the hash changed, older versions ignore the key. Run after
every change in apps/ or icons/; tools/check.py fails when catalog.json is
out of date.
"""

import hashlib
import json
import sys
from pathlib import Path

import app_icons

ROOT = Path(__file__).resolve().parent.parent
FORMAT = 1


def bundle() -> str:
    apps = {f.stem: f.read_text(encoding="utf-8") for f in sorted((ROOT / "apps").glob("*.yaml"))}
    found = {}
    for app_id in apps:
        f = app_icons.icon_file(app_id)
        if f:
            found[app_id] = {"file": f"icons/{f.name}",
                             "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
    return json.dumps({"format": FORMAT, "apps": apps, "icons": found}, ensure_ascii=False,
                      indent=1, sort_keys=True) + "\n"


def main() -> int:
    (ROOT / "catalog.json").write_text(bundle(), encoding="utf-8")
    print(f"catalog.json: {len(list((ROOT / 'apps').glob('*.yaml')))} templates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
