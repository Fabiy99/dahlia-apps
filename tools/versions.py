"""Version logic for image tags.

A tag's shape is the tag with every digit run replaced by '#' and every
commit hash by '@': 1.23.16 and 1.24.0 share the shape '#.#.#', 1.24.0-rc1
does not. Only tags of the same shape count as newer versions, so
pre-releases, architecture tags and floating tags (1, 1.23, stable) are
never picked.
"""

import re

DIGITS = re.compile(r"\d+")
# Commit hashes in tags (2024.10.22-7ca5933): not a version number.
HASH = re.compile(r"(?<![0-9A-Za-z])(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{7,40}(?![0-9A-Za-z])")


def shape(tag: str) -> str:
    return DIGITS.sub("#", HASH.sub("@", tag))


def numbers(tag: str) -> tuple[int, ...]:
    return tuple(int(n) for n in DIGITS.findall(HASH.sub("@", tag)))


def is_calver(tag: str) -> bool:
    """2025.10.1, 250707: the first number is a year or a date."""
    nums = numbers(tag)
    return bool(nums) and nums[0] >= 2000


def pinned(tag: str) -> bool:
    """A tag that names one release: at least major.minor, or a date."""
    return bool(re.search(r"\d+\.\d+", tag) or re.search(r"\d{6,}", tag))


def newest(current: str, candidates: list[str], policy: str = "minor") -> str | None:
    """The newest candidate above current that the policy allows, or None.

    policy: "major" anything newer, "minor" same first number (default),
    "patch" same first two numbers, "hold" never.
    """
    if policy == "hold":
        return None
    cur = numbers(current)
    best, best_n = None, cur
    keep = {"major": 0, "minor": 1, "patch": 2}[policy]
    if policy == "minor" and is_calver(current):
        keep = 0
    for tag in candidates:
        if shape(tag) != shape(current):
            continue
        n = numbers(tag)
        if n[:keep] != cur[:keep]:
            continue
        if n > best_n:
            best, best_n = tag, n
    return best
