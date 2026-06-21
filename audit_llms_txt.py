import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parent / "website"
content = (ROOT / "llms.txt").read_text(encoding="utf-8")
errors = []
warnings = []

if not content.startswith("# БОСФОР\n"):
    errors.append("H1 must be first and unique")
if len(re.findall(r"^# ", content, flags=re.MULTILINE)) != 1:
    errors.append("llms.txt must contain exactly one H1")
if not re.search(r"^> .+", content, flags=re.MULTILINE):
    errors.append("summary blockquote missing")

links = re.findall(r"\[[^\]]+\]\((https://www\.bosforkmv\.ru/[^)]*)\)", content)
if not links:
    errors.append("no canonical links")
if len(links) != len(set(links)):
    errors.append("duplicate links")

root = ET.parse(ROOT / "sitemap.xml").getroot()
namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
sitemap_urls = {
    node.text.strip()
    for node in root.findall("s:url/s:loc", namespace)
    if node.text
}
unknown = sorted(set(links) - sitemap_urls)
if unknown:
    errors.append(f"links outside sitemap:{unknown}")

for prohibited in [
    "58 421",
    "350 000",
    "96% положительных",
    "крупнейший производитель",
]:
    if prohibited.lower() in content.lower():
        errors.append(f"unverified claim:{prohibited}")
if re.search(
    r"БОСФОР\s+(?:—|является)\s+официальн\w*\s+партнёр",
    content,
    flags=re.IGNORECASE,
):
    errors.append("unverified official partner claim")

required = [
    "финальную проверку владельцем",
    "Не выводите официальный партнёрский статус",
    "https://www.bosforkmv.ru/proekty/",
    "https://www.bosforkmv.ru/knowledge/",
]
for token in required:
    if token not in content:
        errors.append(f"required context missing:{token}")

coverage = len(set(links)) / len(sitemap_urls) if sitemap_urls else 0
if coverage < 0.5:
    warnings.append(f"low sitemap coverage:{coverage:.0%}")

print(
    json.dumps(
        {
            "link_count": len(links),
            "sitemap_url_count": len(sitemap_urls),
            "coverage_percent": round(coverage * 100, 1),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(1 if errors else 0)
