import json
from pathlib import Path


ROOT = Path(__file__).parent
nap = json.loads((ROOT / "BOSFOR_NAP_PROFILE_CONTRACT.json").read_text(encoding="utf-8"))
profiles = json.loads((ROOT / "BOSFOR_EXTERNAL_PROFILE_REGISTRY.json").read_text(encoding="utf-8"))
search = json.loads((ROOT / "deployment" / "search-properties.json").read_text(encoding="utf-8"))

errors = []
warnings = []

required_nap = ["legal_name", "primary_phone", "email", "primary_address", "working_hours", "website", "service_regions"]
for field in required_nap:
    if field not in nap["nap"]:
        errors.append(f"NAP field missing: {field}")
    elif nap["nap"][field]["status"] in {"required", "conflict"}:
        warnings.append(f"Owner approval required: {field}")

priorities = {profile["priority"] for profile in profiles["profiles"]}
if "P0" not in priorities:
    errors.append("No P0 external profiles defined")

if search["google_search_console"]["preferred_property"] != "sc-domain:bosforkmv.ru":
    errors.append("Google Domain property is not configured")
if not search["google_search_console"]["sitemaps"]:
    errors.append("Google sitemap list is empty")
if not search["yandex_webmaster"]["sitemaps"]:
    errors.append("Yandex sitemap list is empty")
if search["google_search_console"]["verification_token"]:
    warnings.append("Google verification token is present; ensure it is not a placeholder")
if search["yandex_webmaster"]["verification_token"]:
    warnings.append("Yandex verification token is present; ensure it is not a placeholder")

print(json.dumps({
    "profile_count": len(profiles["profiles"]),
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)

