#!/usr/bin/env python3
"""Write catalog.json: all templates from apps/ in one file.

Dahlia (0.4 and later) downloads only this file. Run after every change in
apps/; tools/check.py fails when catalog.json is out of date.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMAT = 1


def bundle() -> str:
    apps = {f.stem: f.read_text(encoding="utf-8") for f in sorted((ROOT / "apps").glob("*.yaml"))}
    return json.dumps({"format": FORMAT, "apps": apps}, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"


def main() -> int:
    (ROOT / "catalog.json").write_text(bundle(), encoding="utf-8")
    print(f"catalog.json: {len(list((ROOT / 'apps').glob('*.yaml')))} templates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
