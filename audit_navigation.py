import json
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parent / "website"
START = "index.html"
KEY_PAGES = {
    "private-clients.html",
    "developers.html",
    "architects.html",
    "aluminum-windows.html",
    "pvc-windows.html",
    "facades.html",
    "portal-systems.html",
    "doors.html",
    "panoramic-glazing.html",
    "sun-protection.html",
    "production.html",
    "engineering.html",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.noindex = False
        self.has_form = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.noindex = "noindex" in values.get("content", "").lower()
        if tag == "form" and "data-demo-form" in values:
            self.has_form = True


def local_target(source, href):
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or href.startswith(("#", "tel:", "mailto:")):
        return None
    target = parsed.path
    if not target:
        return source
    resolved = (Path(source).parent / target).as_posix()
    if resolved.endswith("/"):
        resolved += "index.html"
    return resolved


pages = {}
for file_path in ROOT.glob("*.html"):
    parser = PageParser()
    parser.feed(file_path.read_text(encoding="utf-8"))
    pages[file_path.name] = {
        "links": {
            target
            for href in parser.links
            if (target := local_target(file_path.name, href)) in {item.name for item in ROOT.glob("*.html")}
        },
        "noindex": parser.noindex,
        "has_form": parser.has_form,
    }

distance = {START: 0}
queue = deque([START])
while queue:
    current = queue.popleft()
    for target in pages[current]["links"]:
        if target not in distance:
            distance[target] = distance[current] + 1
            queue.append(target)

indexable = {name for name, data in pages.items() if not data["noindex"]}
unreachable = sorted(indexable - distance.keys())
key_depths = {name: distance.get(name) for name in sorted(KEY_PAGES)}
too_deep = {name: depth for name, depth in key_depths.items() if depth is None or depth > 3}

journeys = {
    "b2c_entry_reachable": distance.get("private-clients.html"),
    "b2c_has_form": pages.get("private-clients.html", {}).get("has_form", False),
    "b2b_entry_reachable": distance.get("developers.html"),
    "b2b_has_form": pages.get("developers.html", {}).get("has_form", False),
}

errors = []
if unreachable:
    errors.append(f"Indexable pages unreachable from home: {', '.join(unreachable)}")
if too_deep:
    errors.append(f"Key pages deeper than three clicks: {too_deep}")
if not all(journeys.values()):
    errors.append(f"Incomplete B2C/B2B journeys: {journeys}")

result = {
    "page_count": len(pages),
    "indexable_count": len(indexable),
    "reachable_indexable_count": len(indexable - set(unreachable)),
    "max_key_page_depth": max(depth for depth in key_depths.values() if depth is not None),
    "key_page_depths": key_depths,
    "journeys": journeys,
    "error_count": len(errors),
    "errors": errors,
}

print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
