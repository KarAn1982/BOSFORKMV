import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parent / "website"


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "form" and "data-demo-form" in values:
            self.current = {
                "id": values.get("id"),
                "fields": [],
                "has_status": False,
            }
            self.forms.append(self.current)
        elif self.current and tag in {"input", "textarea", "select"}:
            self.current["fields"].append({
                "tag": tag,
                "type": values.get("type", "text"),
                "name": values.get("name"),
                "required": "required" in values,
            })
        elif self.current and "data-form-status" in values:
            self.current["has_status"] = True

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


errors = []
coverage = []
for html_file in ROOT.glob("*.html"):
    parser = FormParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    for index, form in enumerate(parser.forms, start=1):
        form_name = form["id"] or f"{html_file.name}#{index}"
        names = {field["name"] for field in form["fields"] if field["name"]}
        unnamed = [
            f"{field['tag']}:{field['type']}"
            for field in form["fields"]
            if not field["name"]
        ]
        has_contact = "phone" in names or "email" in names
        has_consent = "consent" in names
        has_consent_version = "consent_version" in names
        if not form["id"]:
            errors.append(f"{form_name}: no stable form id")
        if unnamed:
            errors.append(f"{form_name}: unnamed fields {unnamed}")
        if not has_contact:
            errors.append(f"{form_name}: no named phone or email")
        if not has_consent:
            errors.append(f"{form_name}: no consent field")
        if not has_consent_version:
            errors.append(f"{form_name}: no consent version")
        if not form["has_status"]:
            errors.append(f"{form_name}: no status region")
        coverage.append({
            "page": html_file.name,
            "form": form_name,
            "field_count": len(form["fields"]),
            "has_contact": has_contact,
            "has_consent": has_consent,
            "has_consent_version": has_consent_version,
            "unnamed_count": len(unnamed),
        })

print(json.dumps({
    "form_count": len(coverage),
    "error_count": len(errors),
    "errors": errors,
    "coverage": coverage,
}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
