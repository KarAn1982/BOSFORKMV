import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parent / "website"
ORG_ID = "https://www.bosforkmv.ru/#organization"
WEBSITE_ID = "https://www.bosforkmv.ru/#website"
EDITORIAL_ID = "https://www.bosforkmv.ru/#technical-editorial"


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.noindex = False
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.noindex = "noindex" in values.get("content", "").lower()
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")


errors = []
coverage = {}
for html_file in ROOT.glob("*.html"):
    text = html_file.read_text(encoding="utf-8")
    parser = MetadataParser()
    parser.feed(text)
    if parser.noindex:
        continue

    schemas = []
    for body in re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
        text,
        flags=re.DOTALL,
    ):
        schemas.append(json.loads(body))

    nodes = []
    for schema in schemas:
        nodes.extend(schema.get("@graph", [])) if "@graph" in schema else nodes.append(schema)
    ids = {node.get("@id") for node in nodes if isinstance(node, dict)}
    required = {
        ORG_ID,
        WEBSITE_ID,
        EDITORIAL_ID,
        f"{parser.canonical}#webpage",
    }
    missing = sorted(required - ids)
    if missing:
        errors.append(f"{html_file.name}: missing stable IDs {missing}")

    webpage = next(
        (
            node
            for node in nodes
            if isinstance(node, dict)
            and node.get("@id") == f"{parser.canonical}#webpage"
        ),
        None,
    )
    if not webpage or webpage.get("isPartOf", {}).get("@id") != WEBSITE_ID:
        errors.append(f"{html_file.name}: WebPage is not linked to WebSite")
    about = webpage.get("about") if webpage else None
    if isinstance(about, dict):
        about_ids = {about.get("@id")}
    elif isinstance(about, list):
        about_ids = {
            item.get("@id")
            for item in about
            if isinstance(item, dict)
        }
    else:
        about_ids = set()
    if ORG_ID not in about_ids:
        errors.append(f"{html_file.name}: WebPage is not linked to Organization")

    if html_file.name == "alutech.html":
        brand_id = f"{parser.canonical}#brand"
        brand = next(
            (
                node
                for node in nodes
                if isinstance(node, dict) and node.get("@id") == brand_id
            ),
            None,
        )
        if not brand or brand.get("@type") != "Brand":
            errors.append("alutech.html: Brand entity missing")
        if not brand or brand.get("sameAs") != "https://alutech-group.com/":
            errors.append("alutech.html: Brand official sameAs missing")

    coverage[html_file.name] = {
        "schema_blocks": len(schemas),
        "node_count": len(nodes),
        "has_main_entity": bool(webpage and webpage.get("mainEntity")),
    }

print(json.dumps({
    "indexable_pages_checked": len(coverage),
    "error_count": len(errors),
    "errors": errors,
    "coverage": coverage,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
