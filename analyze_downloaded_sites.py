from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).parent / "site_audit_sources"
PAGES = ROOT / "pages"


class Parser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.headings: list[dict[str, str]] = []
        self.links: list[str] = []
        self.images: list[dict[str, str]] = []
        self.schemas: list[str] = []
        self.text_parts: list[str] = []
        self.in_title = False
        self.heading_tag = ""
        self.heading_parts: list[str] = []
        self.script_type = ""
        self.script_parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"style", "svg", "noscript"}:
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key and values.get("content"):
                self.meta[key.lower()] = values["content"].strip()
        elif tag == "link":
            rel = values.get("rel", "").lower()
            if "canonical" in rel and values.get("href"):
                self.canonical = urljoin(self.base_url, values["href"])
        elif tag in {"h1", "h2", "h3"}:
            self.heading_tag = tag
            self.heading_parts = []
        elif tag == "a" and values.get("href"):
            self.links.append(urljoin(self.base_url, values["href"]))
        elif tag == "img":
            self.images.append(
                {
                    "src": urljoin(self.base_url, values.get("src", "")),
                    "alt": values.get("alt", "").strip(),
                    "loading": values.get("loading", "").lower(),
                    "width": values.get("width", ""),
                    "height": values.get("height", ""),
                }
            )
        elif tag == "script":
            self.script_type = values.get("type", "").lower()
            self.script_parts = []

    def handle_endtag(self, tag):
        if tag in {"style", "svg", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self.in_title = False
        elif tag == self.heading_tag:
            value = clean(" ".join(self.heading_parts))
            if value:
                self.headings.append({"level": tag, "text": value})
            self.heading_tag = ""
            self.heading_parts = []
        elif tag == "script":
            raw = "".join(self.script_parts).strip()
            if "ld+json" in self.script_type and raw:
                self.schemas.append(raw)
            self.script_type = ""
            self.script_parts = []

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.script_type:
            self.script_parts.append(data)
            return
        if self.skip_depth:
            return
        value = data.strip()
        if value:
            self.text_parts.append(value)
            if self.heading_tag:
                self.heading_parts.append(value)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def schema_types(schemas: list[str]) -> list[str]:
    output: set[str] = set()
    for raw in schemas:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        queue = [data]
        while queue:
            current = queue.pop()
            if isinstance(current, dict):
                kind = current.get("@type")
                if isinstance(kind, str):
                    output.add(kind)
                elif isinstance(kind, list):
                    output.update(str(item) for item in kind)
                queue.extend(current.values())
            elif isinstance(current, list):
                queue.extend(current)
    return sorted(output)


def detect_tech(raw: str) -> list[str]:
    checks = {
        "WordPress": r"wp-content|wp-includes",
        "Yoast SEO": r"yoast-schema-graph|wordpress-seo",
        "All in One SEO": r"all-in-one-seo|aioseo|All in One SEO",
        "Divi": r"et_pb_|Divi",
        "Elementor": r"elementor",
        "Contact Form 7": r"contact-form-7|wpcf7",
        "jQuery": r"jquery(?:\.min)?\.js",
        "Yandex Metrica": r"mc\.yandex\.ru|ym\(",
        "Google Analytics": r"googletagmanager|google-analytics",
        "reCAPTCHA": r"recaptcha",
    }
    return [name for name, pattern in checks.items() if re.search(pattern, raw, re.I)]


with (ROOT / "page_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
    manifest = list(csv.DictReader(handle))

records = []
for row in manifest:
    path = PAGES / row["File"]
    record = {
        "site": row["Site"],
        "url": row["Url"],
        "status": int(row["Status"] or 0),
        "final_url": row["FinalUrl"],
        "bytes": int(row["Length"] or 0),
    }
    if record["status"] != 200 or not path.exists():
        records.append(record)
        continue
    raw_bytes = path.read_bytes()
    raw = raw_bytes.decode("utf-8", errors="replace")
    parser = Parser(row["FinalUrl"])
    parser.feed(raw)
    text = clean(" ".join(parser.text_parts))
    domain = urlparse(row["FinalUrl"]).netloc.lower().removeprefix("www.")
    internal = {
        link
        for link in parser.links
        if urlparse(link).netloc.lower().removeprefix("www.") == domain
    }
    h1 = [item["text"] for item in parser.headings if item["level"] == "h1"]
    record.update(
        {
            "title": clean(" ".join(parser.title_parts)),
            "description": parser.meta.get("description", ""),
            "robots": parser.meta.get("robots", ""),
            "canonical": parser.canonical,
            "og_title": parser.meta.get("og:title", ""),
            "og_description": parser.meta.get("og:description", ""),
            "og_image": parser.meta.get("og:image", ""),
            "h1": h1,
            "h1_count": len(h1),
            "headings": parser.headings,
            "word_count": len(re.findall(r"\b[\w-]+\b", text, re.UNICODE)),
            "text_hash": hashlib.sha256(text.lower().encode("utf-8")).hexdigest(),
            "internal_links": len(internal),
            "external_links": len(set(parser.links) - internal),
            "images": len(parser.images),
            "images_missing_alt": sum(not image["alt"] for image in parser.images),
            "images_lazy": sum(image["loading"] == "lazy" for image in parser.images),
            "images_missing_dimensions": sum(
                not image["width"] or not image["height"] for image in parser.images
            ),
            "schema_types": schema_types(parser.schemas),
            "tech": detect_tech(raw),
            "has_faq_text": bool(re.search(r"часто задаваем|вопрос.{0,20}ответ", text, re.I)),
            "has_breadcrumb_text": bool(re.search(r"хлебн|breadcrumb", raw, re.I)),
            "has_phone": bool(re.search(r"(?:\+7|8)[\s()\-]*\d{3}", text)),
            "has_address": bool(re.search(r"(?:ул\.|улица|г\.|город)\s", text, re.I)),
        }
    )
    records.append(record)

(ROOT / "downloaded_page_audit.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
)

lines = []
for site in ("main", "b2b"):
    pages = [record for record in records if record["site"] == site]
    ok = [record for record in pages if record["status"] == 200 and "title" in record]
    title_counts = Counter(page["title"] for page in ok if page["title"])
    description_counts = Counter(
        page["description"] for page in ok if page["description"]
    )
    hash_groups = defaultdict(list)
    for page in ok:
        hash_groups[page["text_hash"]].append(page["url"])
    duplicates = [urls for urls in hash_groups.values() if len(urls) > 1]
    schema_counts = Counter(
        schema for page in ok for schema in page.get("schema_types", [])
    )
    tech_counts = Counter(tech for page in ok for tech in page.get("tech", []))
    lines.extend(
        [
            f"# {site}",
            f"URLs: {len(pages)}; 200: {sum(p['status'] == 200 for p in pages)}; non-200: {sum(p['status'] != 200 for p in pages)}",
            f"Missing title: {sum(not p['title'] for p in ok)}",
            f"Missing description: {sum(not p['description'] for p in ok)}",
            f"Missing canonical: {sum(not p['canonical'] for p in ok)}",
            f"Bad H1 count: {sum(p['h1_count'] != 1 for p in ok)}",
            f"Duplicate title extras: {sum(c - 1 for c in title_counts.values() if c > 1)}",
            f"Duplicate description extras: {sum(c - 1 for c in description_counts.values() if c > 1)}",
            f"Exact duplicate content groups: {len(duplicates)}",
            f"Pages under 300 words: {sum(p['word_count'] < 300 for p in ok)}",
            f"Pages under 100 words: {sum(p['word_count'] < 100 for p in ok)}",
            f"Pages with FAQ-like text: {sum(p['has_faq_text'] for p in ok)}",
            f"Pages with phone: {sum(p['has_phone'] for p in ok)}",
            f"Pages with address: {sum(p['has_address'] for p in ok)}",
            f"Images: {sum(p['images'] for p in ok)}; missing alt: {sum(p['images_missing_alt'] for p in ok)}; lazy: {sum(p['images_lazy'] for p in ok)}; missing dimensions: {sum(p['images_missing_dimensions'] for p in ok)}",
            f"Schema: {dict(schema_counts)}",
            f"Tech: {dict(tech_counts)}",
            "",
            "## Weak pages",
        ]
    )
    for page in sorted(ok, key=lambda item: (item["word_count"], item["url"]))[:15]:
        lines.append(
            f"- {page['url']} | words={page['word_count']} | h1={page['h1_count']} | title={page['title']}"
        )
    lines.extend(["", "## Non-200"])
    for page in pages:
        if page["status"] != 200:
            lines.append(f"- {page['status']} {page['url']}")
    lines.extend(["", "## Duplicate content groups"])
    for group in duplicates:
        lines.append("- " + " | ".join(group))
    lines.append("")

(ROOT / "audit_summary.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
