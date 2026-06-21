import json
from pathlib import Path


ROOT = Path(__file__).parent
registry = json.loads((ROOT / "BOSFOR_FACT_REGISTRY.json").read_text(encoding="utf-8"))
website_text = "\n".join(
    item.read_text(encoding="utf-8") for item in (ROOT / "website").glob("*.html")
)

errors = []
valid_statuses = set(registry["statuses"])
ids = set()
for fact in registry["facts"]:
    fact_id = fact.get("id")
    if not fact_id or fact_id in ids:
        errors.append(f"Missing or duplicate fact id: {fact_id}")
    ids.add(fact_id)
    if fact.get("status") not in valid_statuses:
        errors.append(f"{fact_id}: unknown status {fact.get('status')}")
    if not fact.get("sources"):
        errors.append(f"{fact_id}: no source")
    if fact.get("status") == "approved" and not fact.get("approved_by"):
        errors.append(f"{fact_id}: approved fact has no approver")

for prohibited in ["58 421", "350 000 м²", "96% положительных"]:
    schema_fragments = [
        line
        for line in website_text.splitlines()
        if "application/ld+json" in line and prohibited in line
    ]
    if schema_fragments:
        errors.append(f"Unverified numerical claim found in JSON-LD: {prohibited}")

print(json.dumps({
    "fact_count": len(registry["facts"]),
    "approved_count": sum(
        fact["status"] == "approved" for fact in registry["facts"]
    ),
    "conflict_count": sum(
        fact["status"] == "conflict" for fact in registry["facts"]
    ),
    "error_count": len(errors),
    "errors": errors,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
