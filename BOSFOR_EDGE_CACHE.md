# БОСФОР — production edge/cache contract

Дата: 20 июня 2026 года

Файлы:

- `deployment/production-nginx.conf` — deployable edge template;
- `deployment/edge-cache-policy.json` — машинная политика TTL;
- `audit_edge_config.py` — release gate.

Политика:

- HTML: browser `max-age=0`, CDN `s-maxage=300`, SWR 60 секунд;
- stale HTML при upstream error: до 24 часов;
- hashed assets: 1 год + `immutable`;
- текущие unhashed CSS/JS: 7 дней;
- текущие unhashed images/fonts: 30 дней, без `immutable`;
- robots/sitemap: 1 час;
- API/admin/preview: `no-store`, cache bypass;
- 404: 60 секунд; 5xx не кешируются.

На каждом deploy обязателен CDN purge для unhashed assets. Лучший production
вариант — content hashes в именах CSS/JS/images, после чего годовой immutable
cache безопасен.

Фактический пункт CDN закрывается после настройки провайдера, TLS, origin
shield, purge webhook и проверки response headers с публичного домена.
