import csv
import json
from pathlib import Path

from lxml import html


ROOT = Path(__file__).parent
WEBSITE = ROOT / "website"
errors = []
warnings = []

for page_name in ["privacy.html", "consent.html"]:
    source = (WEBSITE / page_name).read_text(encoding="utf-8")
    document = html.fromstring(source)
    robots = " ".join(document.xpath('//meta[@name="robots"]/@content')).lower()
    if "noindex" not in robots:
        errors.append(f"{page_name}: legal draft must be noindex")
    visible = " ".join(document.itertext()).lower()
    if "не публиковать без согласования" not in visible:
        errors.append(f"{page_name}: legal warning missing")
    if "юридическое наименование" not in visible:
        errors.append(f"{page_name}: operator placeholder missing")

forms_checked = 0
for html_file in WEBSITE.glob("*.html"):
    document = html.fromstring(html_file.read_text(encoding="utf-8"))
    for form in document.xpath('//form[@data-demo-form]'):
        forms_checked += 1
        consent = form.xpath('.//input[@name="consent" and @required]')
        version = form.xpath('.//input[@name="consent_version"]/@value')
        consent_links = form.xpath('.//a[@href="consent.html"]')
        privacy_links = form.xpath('.//a[@href="privacy.html"]')
        if not consent:
            errors.append(f"{html_file.name}: required consent missing")
        if version != ["2026-06-19"]:
            errors.append(f"{html_file.name}: consent version missing or wrong")
        if not consent_links or not privacy_links:
            errors.append(f"{html_file.name}: legal links missing near form")

with (ROOT / "BOSFOR_LEGAL_REVIEW_MATRIX.csv").open(
    encoding="utf-8-sig", newline=""
) as handle:
    rows = list(csv.DictReader(handle))
    open_items = sum(row.get("status") == "open" for row in rows)
    if not rows:
        errors.append("Legal review matrix is empty")
    if open_items:
        warnings.append(f"Legal review items awaiting decision: {open_items}")

facts = json.loads((ROOT / "BOSFOR_FACT_REGISTRY.json").read_text(encoding="utf-8"))
approved = sum(fact["status"] == "approved" for fact in facts["facts"])
if approved == 0:
    warnings.append("No owner-approved production facts yet")

print(json.dumps({
    "forms_checked": forms_checked,
    "legal_matrix_rows": len(rows),
    "open_legal_items": open_items,
    "approved_facts": approved,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

