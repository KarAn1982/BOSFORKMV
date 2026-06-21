import json
from pathlib import Path


ROOT = Path(__file__).parent
retention = json.loads(
    (ROOT / "deployment" / "data-retention-policy.json").read_text(
        encoding="utf-8"
    )
)
incident = json.loads(
    (ROOT / "deployment" / "incident-response-plan.json").read_text(
        encoding="utf-8"
    )
)
lead_security = json.loads(
    (ROOT / "deployment" / "lead-security-policy.json").read_text(
        encoding="utf-8"
    )
)
errors = []
warnings = []

required_records = {
    "rejected_form_payload",
    "crm_retry_queue",
    "crm_dead_letter",
    "lead_record",
    "project_upload_quarantine",
    "project_upload_accepted",
    "security_logs",
    "analytics_raw",
    "consent_record",
}
missing = required_records - set(retention.get("records", {}))
if missing:
    errors.append(f"missing_retention_records:{sorted(missing)}")

retry_hours = retention["records"]["crm_retry_queue"].get("retention_hours")
policy_retry_hours = lead_security["fallback"]["maximum_retry_hours"]
if retry_hours != policy_retry_hours:
    errors.append(
        f"crm_retry_retention_mismatch:{retry_hours}!={policy_retry_hours}"
    )
if retention["records"]["rejected_form_payload"].get("retention_days") != 0:
    errors.append("rejected_payload_must_not_persist")
if not retention["records"]["crm_retry_queue"].get("encryption_required"):
    errors.append("crm_retry_queue_encryption_required")

deletion = retention.get("deletion_request", {})
for target in ["primary_database", "CRM", "object_storage", "processors"]:
    if target not in deletion.get("targets", []):
        errors.append(f"deletion_target_missing:{target}")
if "tombstone" not in deletion.get("backup_handling", ""):
    errors.append("backup_deletion_tombstone_missing")

required_phases = ["detect", "contain", "assess", "recover", "close"]
actual_phases = [item.get("id") for item in incident.get("phases", [])]
if actual_phases != required_phases:
    errors.append("incident_phase_order_invalid")
for phase in incident.get("phases", []):
    if not phase.get("required_actions"):
        errors.append(f"incident_phase_empty:{phase.get('id')}")
for role, assignee in incident.get("roles", {}).items():
    if assignee is None:
        warnings.append(f"incident_role_unassigned:{role}")
if not incident.get("rules", {}).get("production_return_requires_gate_pass"):
    errors.append("production_return_gate_required")

for blocker in retention.get("production_blockers", []):
    warnings.append(f"retention_legal_blocker:{blocker}")

result = {
    "integrity_ok": not errors,
    "production_ready": not errors and not warnings,
    "retention_record_count": len(retention.get("records", {})),
    "incident_phase_count": len(incident.get("phases", [])),
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
