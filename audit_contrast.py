from __future__ import annotations

import json
from pathlib import Path


def channel(value: int) -> float:
    value /= 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    color = color.lstrip("#")
    red, green, blue = (int(color[index : index + 2], 16) for index in (0, 2, 4))
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def ratio(foreground: str, background: str) -> float:
    light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


pairs = [
    ("body text", "#111820", "#ffffff", 4.5),
    ("muted text", "#66717c", "#ffffff", 4.5),
    ("muted on surface", "#66717c", "#f2f5f7", 4.5),
    ("white on blue button", "#ffffff", "#00549a", 4.5),
    ("white on bright blue", "#ffffff", "#0877c9", 4.5),
    ("white on navy", "#ffffff", "#061b2d", 4.5),
    ("light blue on navy", "#62b4ea", "#061b2d", 3.0),
    ("blue on white", "#00549a", "#ffffff", 4.5),
]

results = []
errors = []
for name, foreground, background, minimum in pairs:
    measured = ratio(foreground, background)
    passed = measured >= minimum
    result = {
        "name": name,
        "foreground": foreground,
        "background": background,
        "ratio": round(measured, 2),
        "minimum": minimum,
        "passed": passed,
    }
    results.append(result)
    if not passed:
        errors.append(result)

report = {"checks": results, "error_count": len(errors), "errors": errors}
out = Path(__file__).parent / "website" / "qa" / "contrast-audit.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
