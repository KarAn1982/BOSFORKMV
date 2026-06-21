import json
from pathlib import Path


ROOT = Path(__file__).parent
config = (ROOT / "deployment" / "production-nginx.conf").read_text(encoding="utf-8")
policy = json.loads(
    (ROOT / "deployment" / "edge-cache-policy.json").read_text(encoding="utf-8")
)
errors = []

required_tokens = [
    "return 301 https://www.bosforkmv.ru$request_uri;",
    "ssl_protocols TLSv1.2 TLSv1.3;",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "proxy_cache_path",
    "proxy_cache_use_stale",
    "proxy_cache_background_update on;",
    "proxy_cache_lock on;",
    'add_header Cache-Control "no-store" always;',
    'add_header X-Robots-Tag "noindex, nofollow, noarchive" always;',
    "stale-while-revalidate=60",
    "stale-if-error=86400",
    "gzip on;",
]
for token in required_tokens:
    if token not in config:
        errors.append(f"missing:{token}")

if config.count("immutable") != 1:
    errors.append("immutable_must_exist_only_for_hashed_assets")
if "\\.[a-f0-9]{8,}\\." not in config:
    errors.append("hashed_asset_pattern_missing")
if policy["unhashed_assets"]["immutable"] is not False:
    errors.append("unhashed_assets_marked_immutable")
if policy["api"]["cache"] is not False:
    errors.append("api_cache_enabled")
if policy["errors"]["cache_5xx"] is not False:
    errors.append("5xx_cache_enabled")

print(
    json.dumps(
        {
            "policy_version": policy["version"],
            "html_edge_ttl": policy["html"]["edge_max_age_seconds"],
            "hashed_asset_ttl": policy["hashed_assets"]["max_age_seconds"],
            "unhashed_image_ttl": policy["unhashed_assets"][
                "image_font_max_age_seconds"
            ],
            "immutable_occurrences": config.count("immutable"),
            "error_count": len(errors),
            "errors": errors,
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(1 if errors else 0)
