import base64
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/paper-graph-note/scripts/render.py"
spec = importlib.util.spec_from_file_location("render", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class Tags(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/demo.json").read_text())

    def zotero_data(self):
        self.data["zotero"] = {"library": "personal", "attachment": "DEMO0001"}
        self.data["lanes"][0]["nodes"][0]["source"]["annotation"] = "DEMO0002"
        return self.data

    def test_normal_is_self_contained_and_has_five_lanes(self):
        output = renderer.render(self.data)
        tags = Tags(output).tags
        self.assertEqual(sum(tag == "section" for tag, _ in tags), 5)
        self.assertEqual(sum(tag == "article" for tag, _ in tags), 11)
        self.assertEqual(len(re.findall('class="connection(?: hypothesis)?"', output)), 10)
        self.assertNotIn("zotero://", output)
        self.assertNotRegex(output, r"@@[A-Z_]+@@")
        for tag, attrs in tags:
            self.assertNotIn("src", attrs)
            if tag == "a":
                self.assertTrue(attrs["href"].startswith("#"))
        self.assertIn("noscript", output)
        self.assertIn("prefers-color-scheme: dark", output)

    def test_only_zotero_mode_emits_item_or_annotation_identifiers(self):
        output = renderer.render(self.zotero_data())
        self.assertNotIn("zotero://", output)
        self.assertNotIn("DEMO0001", output)
        self.assertNotIn("DEMO0002", output)
        linked = renderer.render(self.data, zotero=True)
        self.assertIn("zotero://open-pdf/library/items/DEMO0001?page=1&amp;annotation=DEMO0002", linked)
        self.assertEqual(linked.count('class="node-body" href="zotero://'), 9)

    def test_group_link_uses_group_not_user_id(self):
        self.zotero_data()["zotero"] = {"library": "group", "group_id": 123456, "attachment": "DEMO0001"}
        self.assertIn("zotero://open-pdf/groups/123456/items/DEMO0001?page=", renderer.render(self.data, True))

    def test_missing_page_stays_unlinked(self):
        self.zotero_data()
        self.data["lanes"][0]["nodes"][0]["source"] = {"section": "Location not verified"}
        self.assertEqual(renderer.render(self.data, True).count('class="node-body" href="zotero://'), 8)

    def test_inferences_are_visible_and_connections_dashed(self):
        output = renderer.render(self.data)
        self.assertEqual(output.count('<span class="badge">Inferred</span>'), 2)
        self.assertEqual(output.count('class="connection hypothesis"'), 2)

    def test_all_paper_text_is_escaped_and_not_interpreted_as_template(self):
        payload = '</script><script>alert("x")</script><img src=x onerror=alert(1)>'
        self.data["title"] = payload
        self.data["subtitle"] = "@@LANES@@"
        self.data["lanes"][0]["nodes"][0]["details"] = [payload]
        self.data["edges"][0]["label"] = payload
        output = renderer.render(self.data)
        self.assertNotIn(payload, output)
        self.assertIn("&lt;/script&gt;", output)
        self.assertIn("@@LANES@@", output)
        self.assertEqual(sum(tag == "script" for tag, _ in Tags(output).tags), 1)
        self.assertNotIn("innerHTML", output)
        self.assertNotIn("eval(", output)

    def test_csp_hash_matches_the_only_executable_script(self):
        output = renderer.render(self.data)
        script = re.search(r"<script>(.*?)</script>", output, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
        self.assertIn(f"script-src 'sha256-{digest}'", output)
        self.assertIn("default-src 'none'", output)

    def test_rejects_invalid_input(self):
        cases = []
        def case(name, edit):
            data = deepcopy(self.data)
            edit(data)
            cases.append((name, data))
        case("missing title", lambda d: d.pop("title"))
        case("lane order", lambda d: d["lanes"].reverse())
        case("empty lane", lambda d: d["lanes"][0].update(nodes=[]))
        case("duplicate ID", lambda d: d["lanes"][0]["nodes"][1].update(id="q-trust"))
        case("unsafe ID", lambda d: d["lanes"][0]["nodes"][0].update(id='a"onclick'))
        case("missing edge", lambda d: d["edges"][0].update(to="absent"))
        case("invalid edge", lambda d: d["edges"][0].update(to=[]))
        case("self-loop", lambda d: d["edges"][0].update(to="q-trust"))
        case("boolean page", lambda d: d["lanes"][0]["nodes"][0]["source"].update(page=True))
        case("zero page", lambda d: d["lanes"][0]["nodes"][0]["source"].update(page=0))
        case("string page", lambda d: d["lanes"][0]["nodes"][0]["source"].update(page="1"))
        case("HTML details", lambda d: d["lanes"][0]["nodes"][0].update(details="not a list"))
        case("inferred string", lambda d: d["lanes"][0]["nodes"][0].update(inferred="yes"))
        case("bad annotation", lambda d: d["lanes"][0]["nodes"][0]["source"].update(annotation="bad"))
        for name, data in cases:
            with self.subTest(name=name), self.assertRaises(ValueError):
                renderer.render(data)

    def test_annotation_without_page_is_rejected(self):
        self.zotero_data()["lanes"][0]["nodes"][0]["source"].pop("page")
        with self.assertRaisesRegex(ValueError, "annotation requires"):
            renderer.render(self.data, True)

    def test_zotero_requires_valid_library_and_attachment(self):
        for config in (None, {}, {"library": "personal", "attachment": "bad"},
                       {"library": "group", "attachment": "DEMO0001", "group_id": True}):
            self.data["zotero"] = config
            with self.subTest(config=config), self.assertRaises(ValueError):
                renderer.render(self.data, True)

    def test_cli_does_not_overwrite_or_leak_input_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "map.html"
            command = [sys.executable, str(SCRIPT), str(ROOT / "examples/demo.json"), str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            output.write_text("do not replace")
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("File exists", second.stderr)
            self.assertEqual(output.read_text(), "do not replace")
            bad_input = Path(temp) / "invalid.json"
            bad_input.write_text('{"title": "unpublished text"}')
            command[-2:] = [str(bad_input), str(Path(temp) / "bad.html")]
            failure = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)
            self.assertNotIn("unpublished text", failure.stderr)
            self.assertFalse((Path(temp) / "bad.html").exists())

    def test_lane_badges_have_readable_contrast_in_both_themes(self):
        template = (ROOT / "skills/paper-graph-note/assets/map.html").read_text()
        palettes = re.findall(r":root\s*\{(.*?)\}", template, re.S)[:2]
        def luminance(color):
            channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
            return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
        for theme, palette in enumerate(palettes):
            colors = dict(re.findall(r"--([a-z-]+):\s*(#[a-f0-9]{6})\b", palette))
            for lane in ("question", "related", "method", "experiments", "future"):
                lo, hi = sorted((luminance(colors[lane]), luminance(colors[lane + "-wash"])))
                with self.subTest(theme=theme, lane=lane):
                    self.assertGreaterEqual((hi + .05) / (lo + .05), 4.5)

    def test_checked_in_preview_matches_renderer(self):
        self.assertEqual((ROOT / "examples/demo.html").read_text(), renderer.render(self.data))

    def test_distribution_has_no_machine_paths_or_credentials(self):
        files = [ROOT / "README.md", ROOT / "package.json"]
        for directory in ("skills", "examples"):
            files.extend(path for path in (ROOT / directory).rglob("*")
                         if path.is_file() and path.suffix in (".md", ".py", ".html", ".json"))
        for path in files:
            with self.subTest(path=str(path.relative_to(ROOT))):
                content = path.read_text()
                self.assertNotIn("/" + "Users/", content)
                self.assertNotIn("/" + "home/", content)
                self.assertNotRegex(content, r"(?i)(?:zotero-api-key|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}")


if __name__ == "__main__":
    unittest.main()
