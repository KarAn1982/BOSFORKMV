from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).parent / "site_audit_sources"
ROOT.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (compatible; BosforSiteAudit/1.0)"
SSL = ssl.create_default_context()


def fetch(url: str) -> tuple[int, dict[str, str], bytes, str]:
    last_error = ""
    for attempt in range(3):
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(request, timeout=60, context=SSL) as response:
                return (
                    response.status,
                    {k.lower(): v for k, v in response.headers.items()},
                    response.read(),
                    response.geturl(),
                )
        except urllib.error.HTTPError as error:
            return (
                error.code,
                {k.lower(): v for k, v in error.headers.items()},
                error.read(),
                error.geturl(),
            )
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = str(error)
            time.sleep(1.5 * (attempt + 1))
    return 0, {"fetch-error": last_error}, b"", url


def sitemap_urls(url: str, visited: set[str] | None = None) -> list[str]:
    visited = visited or set()
    if url in visited:
        return []
    visited.add(url)
    status, _, body, _ = fetch(url)
    if status != 200:
        print(f"  sitemap fetch failed: {status} {url}")
        return []
    root = ET.fromstring(body)
    tag = root.tag.rsplit("}", 1)[-1]
    locations = [
        node.text.strip()
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text
    ]
    if tag == "sitemapindex":
        pages: list[str] = []
        for location in locations:
            pages.extend(sitemap_urls(location, visited))
        return pages
    return locations


class PageParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.hreflang: list[dict[str, str]] = []
        self.headings: list[tuple[str, str]] = []
        self.links: list[str] = []
        self.images: list[dict[str, str]] = []
        self.schemas: list[str] = []
        self.text_parts: list[str] = []
        self.current_tag = ""
        self.current_heading = ""
        self.in_title = False
        self.in_script = False
        self.script_type = ""
        self.script_text = ""
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.current_tag = tag
        if tag in {"style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = values.get("name") or values.get("property")
            if key and values.get("content"):
                self.meta[key.lower()] = values["content"].strip()
        if tag == "link":
            rel = values.get("rel", "").lower()
            href = values.get("href", "")
            if "canonical" in rel:
                self.canonical = urljoin(self.base_url, href)
            if "alternate" in rel and values.get("hreflang"):
                self.hreflang.append(
                    {
                        "hreflang": values["hreflang"],
                        "href": urljoin(self.base_url, href),
                    }
                )
        if tag in {"h1", "h2", "h3"}:
            self.current_heading = tag
            self.text_parts.append("\n")
        if tag == "a" and values.get("href"):
            self.links.append(urljoin(self.base_url, values["href"]))
        if tag == "img":
            self.images.append(
                {
                    "src": urljoin(self.base_url, values.get("src", "")),
                    "alt": values.get("alt", "").strip(),
                    "loading": values.get("loading", ""),
                    "width": values.get("width", ""),
                    "height": values.get("height", ""),
                }
            )
        if tag == "script":
            self.in_script = True
            self.script_type = values.get("type", "").lower()
            self.script_text = ""

    def handle_endtag(self, tag):
        if tag in {"style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self.in_title = False
        if tag == self.current_heading:
            text = re.sub(r"\s+", " ", "".join(self.text_parts).split("\n")[-1]).strip()
            if text:
                self.headings.append((tag, text))
            self.current_heading = ""
        if tag == "script":
            if "ld+json" in self.script_type and self.script_text.strip():
                self.schemas.append(self.script_text.strip())
            self.in_script = False
            self.script_type = ""
            self.script_text = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_script:
            self.script_text += data
            return
        if not self.skip_depth:
            text = data.strip()
            if text:
                self.text_parts.append(text + " ")


def schema_types(raw_schemas: list[str]) -> list[str]:
    found: list[str] = []
    for raw in raw_schemas:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                value = item.get("@type")
                if isinstance(value, str):
                    found.append(value)
                elif isinstance(value, list):
                    found.extend(str(part) for part in value)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return sorted(set(found))


def audit_page(url: str, domain: str) -> dict:
    started = time.perf_counter()
    status, headers, body, final_url = fetch(url)
    elapsed = round(time.perf_counter() - started, 3)
    content_type = headers.get("content-type", "")
    result = {
        "url": url,
        "final_url": final_url,
        "status": status,
        "seconds": elapsed,
        "bytes": len(body),
        "content_type": content_type,
        "x_robots_tag": headers.get("x-robots-tag", ""),
        "cache_control": headers.get("cache-control", ""),
        "server": headers.get("server", ""),
    }
    if status != 200 or "html" not in content_type:
        return result
    charset = "utf-8"
    match = re.search(r"charset=([\w-]+)", content_type, re.I)
    if match:
        charset = match.group(1)
    html = body.decode(charset, errors="replace")
    parser = PageParser(final_url)
    parser.feed(html)
    text = re.sub(r"\s+", " ", "".join(parser.text_parts)).strip()
    internal_links = [
        link
        for link in parser.links
        if urlparse(link).netloc.lower().removeprefix("www.")
        == domain.lower().removeprefix("www.")
    ]
    result.update(
        {
            "title": re.sub(r"\s+", " ", parser.title).strip(),
            "description": parser.meta.get("description", ""),
            "robots_meta": parser.meta.get("robots", ""),
            "canonical": parser.canonical,
            "og_title": parser.meta.get("og:title", ""),
            "og_description": parser.meta.get("og:description", ""),
            "og_image": parser.meta.get("og:image", ""),
            "headings": parser.headings,
            "h1_count": sum(1 for level, _ in parser.headings if level == "h1"),
            "word_count": len(re.findall(r"\b[\w-]+\b", text, re.UNICODE)),
            "internal_links": len(set(internal_links)),
            "external_links": len(set(parser.links)) - len(set(internal_links)),
            "images": len(parser.images),
            "images_missing_alt": sum(1 for image in parser.images if not image["alt"]),
            "images_lazy": sum(
                1 for image in parser.images if image["loading"].lower() == "lazy"
            ),
            "images_missing_dimensions": sum(
                1 for image in parser.images if not image["width"] or not image["height"]
            ),
            "schema_types": schema_types(parser.schemas),
            "hreflang": parser.hreflang,
        }
    )
    return result


sites = {
    "main": {
        "domain": "www.bosforkmv.ru",
        "sitemap": "https://www.bosforkmv.ru/sitemap.xml",
    },
    "b2b": {
        "domain": "bosfor-b2b.web-booster.ru",
        "sitemap": "https://bosfor-b2b.web-booster.ru/sitemap.xml",
    },
}

report: dict[str, dict] = {}
for site_name, config in sites.items():
    urls = sitemap_urls(config["sitemap"])
    # Remove non-content plugin entities that should not be indexed.
    urls = sorted(set(urls))
    pages = []
    for index, url in enumerate(urls, 1):
        print(f"[{site_name} {index}/{len(urls)}] {url}")
        pages.append(audit_page(url, config["domain"]))
    report[site_name] = {"urls": urls, "pages": pages}

(ROOT / "site_audit.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)

for site_name, data in report.items():
    pages = data["pages"]
    html_pages = [page for page in pages if "title" in page]
    titles = Counter(page.get("title", "") for page in html_pages if page.get("title"))
    descriptions = Counter(
        page.get("description", "")
        for page in html_pages
        if page.get("description")
    )
    print(
        json.dumps(
            {
                "site": site_name,
                "urls": len(pages),
                "status_counts": Counter(page["status"] for page in pages),
                "html_pages": len(html_pages),
                "missing_title": sum(not page.get("title") for page in html_pages),
                "missing_description": sum(
                    not page.get("description") for page in html_pages
                ),
                "missing_canonical": sum(
                    not page.get("canonical") for page in html_pages
                ),
                "bad_h1": sum(page.get("h1_count") != 1 for page in html_pages),
                "duplicate_titles": sum(count - 1 for count in titles.values() if count > 1),
                "duplicate_descriptions": sum(
                    count - 1 for count in descriptions.values() if count > 1
                ),
                "schema_types": sorted(
                    {
                        schema
                        for page in html_pages
                        for schema in page.get("schema_types", [])
                    }
                ),
            },
            ensure_ascii=False,
            default=dict,
        )
    )
