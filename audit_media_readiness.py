import csv
import json
from pathlib import Path


ROOT = Path(__file__).parent
inventory = json.loads((ROOT / "BOSFOR_MEDIA_INVENTORY.json").read_text(encoding="utf-8"))
required_columns = {
    "asset_id",
    "file_or_folder",
    "content_type",
    "object_or_person",
    "author",
    "shoot_date",
    "source_owner",
    "client_permission",
    "property_release",
    "person_consent",
    "trademark_permission",
    "allowed_channels",
    "expiry_date",
    "status",
    "reviewed_by",
    "notes",
}
errors = []
warnings = []

with (ROOT / "BOSFOR_MEDIA_RIGHTS_REGISTER.csv").open(
    encoding="utf-8-sig", newline=""
) as handle:
    reader = csv.DictReader(handle)
    rows = list(reader)
    if set(reader.fieldnames or []) != required_columns:
        errors.append("Media rights register columns differ from contract")
    if not rows:
        errors.append("Media rights register is empty")

for gap, count in inventory["evidence_gaps"].items():
    if count == 0:
        warnings.append(f"Media gap remains: {gap}")

if inventory["video_count"] != 0:
    warnings.append("Video files exist and require manual rights review")

print(json.dumps({
    "inventory_files": inventory["total_files"],
    "rights_rows": len(rows),
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

