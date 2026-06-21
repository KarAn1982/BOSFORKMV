import json
import re
from pathlib import Path


ROOT = Path(__file__).parent / "website"
articles = sorted(ROOT.glob("article-*.html"))
errors = []
results = []

for article in articles:
    source = article.read_text(encoding="utf-8")
    item_errors = []
    if source.count("data-editorial-review") != 1:
        item_errors.append("visible editorial review missing or duplicated")
    if "Техническая редакция БОСФОР" not in source:
        item_errors.append("visible technical editorial author missing")
    if not re.search(r'"datePublished":"\d{4}-\d{2}-\d{2}"', source):
        item_errors.append("datePublished missing")
    if not re.search(r'"dateModified":"\d{4}-\d{2}-\d{2}"', source):
        item_errors.append("dateModified missing")
    if "не замен" not in source.lower():
        item_errors.append("scope limitation missing")
    if source.count('"@type":"Article"') != 1:
        item_errors.append("Article schema missing or duplicated")
    for error in item_errors:
        errors.append(f"{article.name}: {error}")
    results.append({"file": article.name, "passed": not item_errors})

if len(articles) != 8:
    errors.append(f"Expected 8 articles, found {len(articles)}")

print(
    json.dumps(
        {
            "article_count": len(articles),
            "passed_count": sum(item["passed"] for item in results),
            "error_count": len(errors),
            "errors": errors,
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(1 if errors else 0)
