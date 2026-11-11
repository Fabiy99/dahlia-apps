import tempfile
import unittest
from pathlib import Path

import app_icons


class Icons(unittest.TestCase):
    def check(self, name, data):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / name
            f.write_bytes(data)
            return app_icons.check(f)

    def test_clean_svg(self):
        svg = (b'<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g"/></defs>'
               b'<path fill="url(#g)" d="M0 0h1"/><use href="#g"/></svg>')
        self.assertIsNone(self.check("a.svg", svg))

    def test_svg_rejects_active_content(self):
        for bad in (b"<svg><script>alert(1)</script></svg>", b'<svg onload="x()"></svg>',
                    b'<svg><image href="https://example.com/a.png"/></svg>',
                    b'<svg><style>a{fill:url(https://x/y)}</style></svg>',
                    b"<svg><foreignObject/></svg>"):
            self.assertIsNotNone(self.check("a.svg", bad), bad)

    def test_png(self):
        self.assertIsNone(self.check("a.png", app_icons.PNG_MAGIC + b"rest"))
        self.assertEqual(self.check("a.png", b"<svg/>"), "not a PNG file")
        self.assertIsNotNone(self.check("a.png", app_icons.PNG_MAGIC + b"x" * app_icons.MAX_SIZE))
        self.assertEqual(self.check("a.gif", b"GIF89a"), "only .svg and .png")


if __name__ == "__main__":
    unittest.main()
