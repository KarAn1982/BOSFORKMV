from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parent / "website"


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta = {}
        self.canonical = ""
        self.h1 = 0
        self.images = []
        self.links = []
        self.schemas = []
        self.script_type = ""
        self.script_data = ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[key] = values.get("content", "")
        elif tag == "link" and "canonical" in values.get("rel", ""):
            self.canonical = values.get("href", "")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.images.append(values)
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "script":
            self.script_type = values.get("type", "")
            self.script_data = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            if self.script_type == "application/ld+json":
                self.schemas.append(self.script_data)
            self.script_type = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.script_type:
            self.script_data += data


pages = []
errors = []
for path in sorted(ROOT.glob("*.html")):
    parser = Parser()
    parser.feed(path.read_text(encoding="utf-8"))
    page_errors = []
    if not parser.title.strip():
        page_errors.append("missing title")
    if not parser.meta.get("description"):
        page_errors.append("missing description")
    if parser.h1 != 1:
        page_errors.append(f"h1 count {parser.h1}")
    for image in parser.images:
        source = image.get("src", "")
        if not image.get("alt"):
            page_errors.append(f"missing alt: {source}")
        if source and not source.startswith(("http:", "https:", "data:")):
            if not (ROOT / source).exists():
                page_errors.append(f"missing image: {source}")
        if not image.get("width") or not image.get("height"):
            page_errors.append(f"missing image dimensions: {source}")
        for candidate in image.get("srcset", "").split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            responsive_source = candidate.split()[0]
            if not responsive_source.startswith(("http:", "https:", "data:")):
                if not (ROOT / responsive_source).exists():
                    page_errors.append(
                        f"missing responsive image: {responsive_source}"
                    )
    for href in parser.links:
        parsed = urlparse(href)
        if parsed.scheme or href.startswith(("#", "tel:", "mailto:")):
            continue
        target = href.split("#", 1)[0]
        if target and not (ROOT / target).exists():
            page_errors.append(f"broken local link: {href}")
    for raw in parser.schemas:
        try:
            json.loads(raw)
        except json.JSONDecodeError as exc:
            page_errors.append(f"invalid JSON-LD: {exc}")
    pages.append(
        {
            "file": path.name,
            "title": parser.title.strip(),
            "description": bool(parser.meta.get("description")),
            "canonical": parser.canonical,
            "h1": parser.h1,
            "images": len(parser.images),
            "links": len(parser.links),
            "errors": page_errors,
        }
    )
    errors.extend(f"{path.name}: {error}" for error in page_errors)

report = {"pages": pages, "error_count": len(errors), "errors": errors}
(ROOT / "qa" / "structural-audit.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
