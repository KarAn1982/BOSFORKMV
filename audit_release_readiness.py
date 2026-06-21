import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parent
WEBSITE = ROOT / "website"
DEPLOYMENT = ROOT / "deployment"


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.noindex = "noindex" in values.get("content", "").lower()


errors = []
checks = {}

indexable_canonicals = set()
for html_file in WEBSITE.glob("*.html"):
    parser = MetadataParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    if not parser.noindex:
        if not parser.canonical:
            errors.append(f"{html_file.name}: indexable page has no canonical")
        else:
            indexable_canonicals.add(parser.canonical)

sitemap_root = ET.parse(WEBSITE / "sitemap.xml").getroot()
namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
sitemap_urls = {
    node.text.strip()
    for node in sitemap_root.findall("s:url/s:loc", namespace)
    if node.text
}

missing_from_sitemap = sorted(indexable_canonicals - sitemap_urls)
extra_in_sitemap = sorted(sitemap_urls - indexable_canonicals)
if missing_from_sitemap:
    errors.append(f"Canonical URLs missing from sitemap: {missing_from_sitemap}")
if extra_in_sitemap:
    errors.append(f"Non-indexable or unknown sitemap URLs: {extra_in_sitemap}")

checks["indexable_canonical_count"] = len(indexable_canonicals)
checks["sitemap_url_count"] = len(sitemap_urls)
checks["sitemap_matches_indexable_pages"] = not missing_from_sitemap and not extra_in_sitemap

staging_config = (DEPLOYMENT / "staging-nginx.conf").read_text(encoding="utf-8")
required_staging_tokens = [
    'auth_basic "Bosfor staging"',
    'X-Robots-Tag "noindex, nofollow, noarchive"',
    'return 200 "User-agent: *\\nDisallow: /\\n"',
]
missing_staging_tokens = [
    token for token in required_staging_tokens if token not in staging_config
]
if missing_staging_tokens:
    errors.append(f"Staging config missing controls: {missing_staging_tokens}")
checks["staging_indexing_protection"] = not missing_staging_tokens

for filename in ["backup-policy.json", "cms-rbac.json", "lead-security-policy.json"]:
    try:
        json.loads((DEPLOYMENT / filename).read_text(encoding="utf-8"))
        checks[f"{filename}_valid"] = True
    except Exception as exc:
        checks[f"{filename}_valid"] = False
        errors.append(f"{filename}: {exc}")

key_files = [
    item
    for item in WEBSITE.glob("*.txt")
    if re.fullmatch(r"[a-z0-9-]{8,128}\.txt", item.name, flags=re.IGNORECASE)
    and item.name != "robots.txt"
]
if len(key_files) != 1:
    errors.append(f"Expected exactly one IndexNow key file, found {len(key_files)}")
    checks["indexnow_key_valid"] = False
else:
    key_file = key_files[0]
    key_value = key_file.read_text(encoding="utf-8").strip()
    checks["indexnow_key_valid"] = key_file.stem == key_value
    if not checks["indexnow_key_valid"]:
        errors.append("IndexNow key filename and content differ")

indexnow_script = (DEPLOYMENT / "indexnow-submit.js").read_text(encoding="utf-8")
checks["indexnow_uses_sitemap"] = 'path.join(siteRoot, "sitemap.xml")' in indexnow_script
checks["indexnow_dry_run_default"] = 'const submit = process.argv.includes("--submit")' in indexnow_script
if not checks["indexnow_uses_sitemap"]:
    errors.append("IndexNow script does not read sitemap.xml")
if not checks["indexnow_dry_run_default"]:
    errors.append("IndexNow script is not safe-by-default")

result = {
    "checks": checks,
    "error_count": len(errors),
    "errors": errors,
}

print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
