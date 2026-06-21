import json
import re
from pathlib import Path


ROOT = Path(__file__).parent / "website"
archive_files = {
    "project-atrium-kislovodsk.html",
    "project-central-department-store-novocherkassk.html",
    "project-istochnik-essentuki.html",
    "project-magas-sports-palace.html",
    "project-rus-essentuki.html",
    "project-russia-my-history.html",
    "project-sochi-seaport.html",
    "project-sokol-rostov.html",
    "project-tselebny-narzan.html",
    "project-vershina-essentuki.html",
}
projects = sorted(ROOT.glob("project-*.html"))
errors = []
statuses = {}

for project in projects:
    source = project.read_text(encoding="utf-8")
    if source.count("data-project-evidence") != 1:
        errors.append(f"{project.name}: evidence block missing or duplicated")
    match = re.search(r'data-verification-status="([^"]+)"', source)
    status = match.group(1) if match else None
    statuses[project.name] = status
    expected = (
        "archive_only"
        if project.name in archive_files
        else "verification_in_progress"
    )
    if status != expected:
        errors.append(f"{project.name}: status {status}, expected {expected}")
    if '"dateModified":"2026-06-20"' not in source:
        errors.append(f"{project.name}: dateModified missing")
    if "Проверка редакции: 20 июня 2026 года" not in source:
        errors.append(f"{project.name}: visible review date missing")
    if project.name in archive_files:
        if '"creator":{"@id":"https://www.bosforkmv.ru/#organization"}' in source:
            errors.append(f"{project.name}: unverified creator claim in schema")
        if "архивный источник" not in source:
            errors.append(f"{project.name}: archive warning missing")
    elif "частичная верификация" not in source:
        errors.append(f"{project.name}: partial verification warning missing")

if len(projects) != 12:
    errors.append(f"Expected 12 projects, found {len(projects)}")

print(
    json.dumps(
        {
            "project_count": len(projects),
            "archive_only": sum(value == "archive_only" for value in statuses.values()),
            "verification_in_progress": sum(
                value == "verification_in_progress" for value in statuses.values()
            ),
            "error_count": len(errors),
            "errors": errors,
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(1 if errors else 0)
