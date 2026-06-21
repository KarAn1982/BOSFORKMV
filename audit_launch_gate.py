import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent
manifest = json.loads(
    (ROOT / "BOSFOR_LAUNCH_GATES.json").read_text(encoding="utf-8")
)
facts = json.loads(
    (ROOT / "BOSFOR_FACT_REGISTRY.json").read_text(encoding="utf-8")
)
profiles = json.loads(
    (ROOT / "BOSFOR_EXTERNAL_PROFILE_REGISTRY.json").read_text(encoding="utf-8")
)
with (ROOT / "BOSFOR_LEGAL_REVIEW_MATRIX.csv").open(
    encoding="utf-8-sig", newline=""
) as source:
    legal_rows = [row for row in csv.DictReader(source) if row.get("area")]

errors = []
allowed_statuses = {"blocked_external", "ready"}
gates = manifest.get("gates", [])
ids = [item.get("id") for item in gates]
if manifest.get("policy") != "fail_closed":
    errors.append("launch_policy_must_be_fail_closed")
if len(ids) != len(set(ids)):
    errors.append("duplicate_gate_id")
for item in gates:
    for field in ["id", "area", "owner", "status", "required_evidence"]:
        if not item.get(field):
            errors.append(f"{item.get('id', 'unknown')}:missing_{field}")
    if item.get("status") not in allowed_statuses:
        errors.append(f"{item.get('id')}:invalid_status")

approved_facts = [
    item for item in facts["facts"] if item.get("status") == "approved"
]
open_legal = [item for item in legal_rows if item.get("status") != "approved"]
profile_ready = [
    item
    for item in profiles["profiles"]
    if item.get("profile_url") and item.get("status") in {"verified", "synced"}
]

derived_blockers = {
    "owner_facts": len(approved_facts) == 0,
    "legal_review": len(open_legal) > 0,
    "external_profiles": len(profile_ready) == 0,
}
for gate_id, blocked in derived_blockers.items():
    gate = next((item for item in gates if item["id"] == gate_id), None)
    if not gate:
        errors.append(f"missing_derived_gate:{gate_id}")
    elif blocked and gate["status"] == "ready":
        errors.append(f"unsafe_ready_status:{gate_id}")

blocked = [item for item in gates if item["status"] != "ready"]
launch_ready = not blocked and not errors
summary = {
    "launch_ready": launch_ready,
    "integrity_ok": not errors,
    "gate_total": len(gates),
    "ready": len(gates) - len(blocked),
    "blocked": len(blocked),
    "approved_facts": len(approved_facts),
    "open_legal_decisions": len(open_legal),
    "verified_external_profiles": len(profile_ready),
    "blocked_by_area": dict(Counter(item["area"] for item in blocked)),
    "errors": errors,
}

reports = ROOT / "reports"
reports.mkdir(exist_ok=True)
(reports / "launch-gate-latest.json").write_text(
    json.dumps(
        {
            **summary,
            "blockers": blocked,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
lines = [
    "# БОСФОР — launch decision gate",
    "",
    f"Решение: {'GO' if launch_ready else 'NO-GO'}",
    f"Gate integrity: {'PASS' if not errors else 'FAIL'}",
    "",
    "## Сводка",
    "",
    f"- готово: {summary['ready']}/{summary['gate_total']};",
    f"- внешних блокеров: {summary['blocked']};",
    f"- owner-approved фактов: {summary['approved_facts']};",
    f"- открытых legal решений: {summary['open_legal_decisions']};",
    f"- проверенных внешних профилей: {summary['verified_external_profiles']}.",
    "",
    "## Блокеры",
    "",
]
for item in blocked:
    lines.append(
        f"- `{item['id']}` — {item['required_evidence']} · владелец: {item['owner']}."
    )
(reports / "launch-gate-latest.md").write_text(
    "\n".join(lines) + "\n", encoding="utf-8"
)

print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
