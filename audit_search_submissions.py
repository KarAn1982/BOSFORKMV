import json
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent
registry = json.loads((ROOT / "BOSFOR_SEARCH_SUBMISSIONS.json").read_text(encoding="utf-8"))
errors = []
warnings = []
statuses = set(registry.get("allowed_statuses", []))
required_ids = {
    "google_sitemap",
    "yandex_sitemap",
    "indexnow_canonical_urls",
    "google_priority_recrawl",
    "yandex_priority_recrawl",
}
items = registry.get("submissions", [])
ids = [item.get("id") for item in items]
if set(ids) != required_ids:
    errors.append("required_submission_ids_mismatch")
if len(ids) != len(set(ids)):
    errors.append("duplicate_submission_id")

root = ET.parse(ROOT / "website" / "sitemap.xml").getroot()
namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
sitemap_urls = {
    node.text.strip()
    for node in root.findall("s:url/s:loc", namespace)
    if node.text
}

for item in items:
    item_id = item.get("id", "unknown")
    status = item.get("status")
    if status not in statuses:
        errors.append(f"{item_id}:invalid_status")
    target = item.get("target")
    if isinstance(target, list):
        unknown = set(target) - sitemap_urls
        if unknown:
            errors.append(f"{item_id}:targets_outside_sitemap:{sorted(unknown)}")
    elif item.get("type") == "sitemap":
        if target != "https://www.bosforkmv.ru/sitemap.xml":
            errors.append(f"{item_id}:wrong_sitemap_target")
    if item_id == "indexnow_canonical_urls":
        if item.get("expected_url_count") != len(sitemap_urls):
            errors.append(f"{item_id}:url_count_mismatch")
    if status in {"submitted", "verified"}:
        for field in ["submitted_at", "submitted_by", "receipt"]:
            if not item.get(field):
                errors.append(f"{item_id}:{field}_required")
        timestamp = item.get("submitted_at")
        if timestamp:
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    errors.append(f"{item_id}:timestamp_must_have_timezone")
            except ValueError:
                errors.append(f"{item_id}:timestamp_invalid")
    if status == "verified" and not item.get("verified_at"):
        errors.append(f"{item_id}:verified_at_required")
    if status in {"pending_access", "ready_to_submit", "failed"}:
        warnings.append(f"{item_id}:{status}")

summary = Counter(item["status"] for item in items)
print(
    json.dumps(
        {
            "integrity_ok": not errors,
            "submission_complete": all(
                item["status"] in {"submitted", "verified"} for item in items
            ) and not errors,
            "sitemap_url_count": len(sitemap_urls),
            "status_counts": dict(summary),
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
