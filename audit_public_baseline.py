import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent
snapshot_candidates = sorted(
    item
    for item in (ROOT / "snapshots").glob("20??-??-??")
    if item.is_dir()
)
snapshot = snapshot_candidates[-1] if snapshot_candidates else ROOT / "snapshots" / "missing"
manifest_path = snapshot / "manifest.json"
errors = []

if not manifest_path.exists():
    errors.append(f"Snapshot manifest missing: {manifest_path}")
    manifest = {"sites": []}
else:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

expected_sites = {
    "https://www.bosforkmv.ru/",
    "https://bosfor-b2b.web-booster.ru/",
}
actual_sites = {item["site"] for item in manifest.get("sites", [])}
if actual_sites != expected_sites:
    errors.append(f"Snapshot sites differ: {sorted(actual_sites)}")

for site in manifest.get("sites", []):
    if not site.get("pages"):
        errors.append(f"{site['site']}: no pages captured")
    if site.get("robots", {}).get("status") is None:
        errors.append(f"{site['site']}: robots.txt status was not recorded")
    for page in site.get("pages", []):
        content_type = (page.get("content_type") or "").lower()
        if "html" not in content_type and content_type:
            continue
        saved_as = page.get("saved_as")
        if not saved_as:
            continue
        file_path = snapshot / Path(site["site"].split("//", 1)[1].strip("/")) / saved_as
        if not file_path.exists():
            errors.append(f"Missing saved body: {file_path}")
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if digest != page["sha256"]:
            errors.append(f"Checksum mismatch: {file_path}")

archive = ROOT / "snapshots" / f"bosfor-public-baseline-{snapshot.name}.zip"
if not archive.exists() or archive.stat().st_size == 0:
    errors.append("Snapshot archive missing or empty")

print(json.dumps({
    "site_count": len(manifest.get("sites", [])),
    "page_count": sum(len(site.get("pages", [])) for site in manifest.get("sites", [])),
    "archive_bytes": archive.stat().st_size if archive.exists() else 0,
    "error_count": len(errors),
    "errors": errors,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
