import unittest

import registry
import versions


class Versions(unittest.TestCase):
    def test_same_shape_only(self):
        tags = ["1.2.4", "1.3.0", "1.3.0-rc1", "1.10.0", "2.0.0", "1", "1.3", "latest"]
        self.assertEqual(versions.newest("1.2.3", tags), "1.10.0")
        self.assertEqual(versions.newest("1.2.3", tags, "major"), "2.0.0")
        self.assertEqual(versions.newest("1.2.3", tags, "patch"), "1.2.4")
        self.assertIsNone(versions.newest("1.2.3", tags, "hold"))
        self.assertIsNone(versions.newest("2.0.0", tags))

    def test_suffix_and_prefix(self):
        tags = ["17.6-alpine", "17.7-alpine", "17.7", "18.0-alpine", "v17.9-alpine"]
        self.assertEqual(versions.newest("17.6-alpine", tags), "17.7-alpine")
        self.assertEqual(versions.newest("v1.2.0", ["v1.3.0", "1.4.0"]), "v1.3.0")

    def test_calver_crosses_years(self):
        self.assertEqual(versions.newest("2025.10.1", ["2025.11.0", "2026.1.0"]), "2026.1.0")
        self.assertEqual(versions.newest("250707", ["251001", "1"]), "251001")

    def test_commit_hash(self):
        tags = ["2024.10.22-7ca5933", "2024.5.13-a0bc346", "2025.1.2-0abc12f"]
        self.assertEqual(versions.newest("2024.5.13-a0bc346", tags), "2025.1.2-0abc12f")
        self.assertEqual(versions.shape("1.2.3-4e8b05daf"), "#.#.#-@")

    def test_pinned(self):
        for tag in ("1.2", "v1.10.3", "17.6-alpine", "250707", "version-6.4.2", "version-2026-07-14c"):
            self.assertTrue(versions.pinned(tag), tag)
        for tag in ("1", "stable", "latest", "v2", "nightly"):
            self.assertFalse(versions.pinned(tag), tag)


class Images(unittest.TestCase):
    def test_split(self):
        self.assertEqual(registry.split_image("postgres:17.6"), ("docker.io", "library/postgres", "17.6"))
        self.assertEqual(registry.split_image("traefik/whoami:v1"), ("docker.io", "traefik/whoami", "v1"))
        self.assertEqual(registry.split_image("ghcr.io/a/b:1.0"), ("ghcr.io", "a/b", "1.0"))
        self.assertEqual(registry.split_image("localhost:5000/x:1"), ("localhost:5000", "x", "1"))


if __name__ == "__main__":
    unittest.main()
