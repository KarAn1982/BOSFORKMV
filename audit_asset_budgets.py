import json
from pathlib import Path


ROOT = Path(__file__).parent / "website"
BUDGETS = {
    "javascript_kb": 30,
    "css_kb": 120,
    "critical_font_kb": 220,
}

javascript_files = [
    ROOT / "runtime-config.js",
    ROOT / "analytics-loader.js",
    ROOT / "consent-manager.js",
    ROOT / "script.js",
    ROOT / "analytics-adapter.js",
    ROOT / "ai-attribution.js",
    ROOT / "web-vitals.js",
]
css_files = [ROOT / "styles.css"]
font_files = [
    ROOT / "assets/fonts/HelveticaNeue-LightCondensed.woff2",
    ROOT / "assets/fonts/HelveticaNeue-BoldCondensed.woff2",
]


def total_kb(files):
    return round(sum(item.stat().st_size for item in files) / 1024, 1)


sizes = {
    "javascript_kb": total_kb(javascript_files),
    "css_kb": total_kb(css_files),
    "critical_font_kb": total_kb(font_files),
}
violations = [
    f"{name}: {size} KB exceeds {BUDGETS[name]} KB"
    for name, size in sizes.items()
    if size > BUDGETS[name]
]

print(json.dumps({
    "sizes": sizes,
    "budgets": BUDGETS,
    "error_count": len(violations),
    "errors": violations,
}, ensure_ascii=False, indent=2))

raise SystemExit(1 if violations else 0)
