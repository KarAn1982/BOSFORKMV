import json
from pathlib import Path

from lxml import html


ROOT = Path(__file__).parent / "website"
errors = []
warnings = []
coverage = []

for html_file in ROOT.glob("*.html"):
    document = html.fromstring(html_file.read_text(encoding="utf-8"))
    page_errors = []
    page_warnings = []

    language = document.get("lang")
    if language != "ru":
        page_errors.append(f"html lang is {language!r}, expected 'ru'")

    ids = [value for value in document.xpath("//*[@id]/@id") if value]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        page_errors.append(f"duplicate ids: {duplicates}")

    main_count = len(document.xpath("//main"))
    if main_count != 1:
        page_errors.append(f"expected one main landmark, found {main_count}")

    if document.xpath("//body/header") and not document.xpath('//a[contains(@class, "skip-link")]'):
        page_warnings.append("page with header has no skip link")

    for button in document.xpath("//button"):
        text = " ".join(button.itertext()).strip()
        if not text and not button.get("aria-label"):
            page_errors.append("button without accessible name")

    for link in document.xpath("//a"):
        text = " ".join(link.itertext()).strip()
        image_alts = [value.strip() for value in link.xpath(".//img/@alt") if value.strip()]
        if not text and not link.get("aria-label") and not image_alts:
            page_errors.append(f"link without accessible name: {link.get('href')}")
        if link.get("target") == "_blank" and "noopener" not in (link.get("rel") or ""):
            page_errors.append(f"target=_blank without noopener: {link.get('href')}")

    for field in document.xpath("//input|//select|//textarea"):
        if field.get("type") == "hidden":
            continue
        field_id = field.get("id")
        wrapped = bool(field.xpath("ancestor::label"))
        labelled = bool(
            field.get("aria-label")
            or field.get("aria-labelledby")
            or (field_id and document.xpath(f'//label[@for="{field_id}"]'))
        )
        if not wrapped and not labelled:
            page_errors.append(
                f"{field.tag}[name={field.get('name')}] has no associated label"
            )

    heading_levels = [
        int(node.tag[1])
        for node in document.xpath("//h1|//h2|//h3|//h4|//h5|//h6")
    ]
    for previous, current in zip(heading_levels, heading_levels[1:]):
        if current > previous + 1:
            page_warnings.append(f"heading level jumps from h{previous} to h{current}")

    errors.extend(f"{html_file.name}: {item}" for item in page_errors)
    warnings.extend(f"{html_file.name}: {item}" for item in page_warnings)
    coverage.append({
        "page": html_file.name,
        "errors": len(page_errors),
        "warnings": len(page_warnings),
    })

print(json.dumps({
    "page_count": len(coverage),
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
    "coverage": coverage,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
