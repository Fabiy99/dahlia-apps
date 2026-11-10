#!/usr/bin/env python3
"""Look for newer image versions and write them into the templates.

For every image in apps/*.yaml the registry's tag list is read and the
newest tag of the same shape is taken (see versions.py). By default only
versions with the same major number are applied; tools/bump.json can set
"major", "patch" or "hold" per image (registry/name without tag). Newer
major versions that were not applied are listed in the report, so they can
be checked and applied by hand.

Usage: tools/bump.py [--report report.md] [--only <id>...]
Rewrites the changed templates and catalog.json; exit code 0 also when
nothing changed.
"""

import argparse
import json
import sys
from pathlib import Path

import build
import registry
import versions
import yaml

ROOT = Path(__file__).resolve().parent.parent


def images_of(text: str) -> list[str]:
    data = yaml.safe_load(text)
    return [s["image"] for s in (data.get("services") or {}).values()] or [data["image"]]


def repo_key(image: str) -> str:
    return image.split("@")[0].rsplit(":", 1)[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", help="write a Markdown report of the changes here")
    p.add_argument("--only", nargs="*", help="only these app ids")
    args = p.parse_args()

    policies = json.loads((ROOT / "tools/bump.json").read_text()).get("policy", {})
    tag_cache: dict[str, list[str]] = {}
    applied, majors, errors = [], [], []

    for f in sorted((ROOT / "apps").glob("*.yaml")):
        if args.only and f.stem not in args.only:
            continue
        text = f.read_text(encoding="utf-8")
        new_text = text
        for image in dict.fromkeys(images_of(text)):
            if "@" in image:
                continue
            key = repo_key(image)
            tag = image.rsplit(":", 1)[1]
            try:
                if key not in tag_cache:
                    tag_cache[key] = registry.tags(image)
            except registry.RegistryError as e:
                errors.append(f"{f.stem}: {e}")
                continue
            tags = tag_cache[key]
            policy = policies.get(key, "minor")
            best = versions.newest(tag, tags, policy)
            if best:
                new = f"{key}:{best}"
                if not registry.exists(new):
                    errors.append(f"{f.stem}: {new} is listed but has no manifest")
                    continue
                new_text = new_text.replace(f"image: {image}\n", f"image: {new}\n")
                applied.append((f.stem, image, new))
                tag = best
            top = versions.newest(tag, tags, "major")
            if top and policy != "hold":
                majors.append((f.stem, f"{key}:{tag}", f"{key}:{top}"))
        if new_text != text:
            f.write_text(new_text, encoding="utf-8")

    if applied:
        build.main()
    lines = []
    if applied:
        lines += ["### Neue Versionen / New versions", "", "| App | alt / old | neu / new |",
                  "| --- | --- | --- |"]
        lines += [f"| {a} | `{o}` | `{n}` |" for a, o, n in applied]
        lines.append("")
    if majors:
        lines += ["### Neue Hauptversionen, nicht übernommen / New major versions, not applied",
                  "", "| App | aktuell / current | verfügbar / available |", "| --- | --- | --- |"]
        lines += [f"| {a} | `{o}` | `{n}` |" for a, o, n in majors]
        lines.append("")
    if errors:
        lines += ["### Fehler / Errors", ""] + [f"- {e}" for e in errors] + [""]
    report = "\n".join(lines) or "Keine neuen Versionen. / No new versions.\n"
    print(report)
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    print(f"{len(applied)} images updated, {len(majors)} major versions held, {len(errors)} errors",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
