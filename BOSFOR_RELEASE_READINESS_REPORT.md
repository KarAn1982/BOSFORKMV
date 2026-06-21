# БОСФОР — текущая готовность первого релиза

Дата: 20 июня 2026 года

## Статус

- выполнено пунктов мастер-чеклиста: 161;
- открыто пунктов: 41;
- full quality gate: 39/39;
- визуальная регрессия: 90/90 viewport-проверок;
- индексируемые страницы: 40;
- всего HTML-страниц прототипа: 45;
- формы: 32/32 соответствуют единому клиентскому контракту;
- structured data: 40/40 индексируемых страниц имеют связный entity graph.

## Доказано прототипом

- уникальные title, description, H1, canonical и Open Graph;
- sitemap содержит только 40 indexable canonical URL;
- стабильные `@id` Organization, WebSite, WebPage, редакции, услуг, статей и проектов;
- B2C/B2B-маршруты и услуги доступны не глубже двух кликов;
- 12 карточек проектов и 8 экспертных материалов;
- responsive AVIF/WebP, intrinsic image sizes и preload LCP-изображения;
- WOFF2 для критических начертаний: 70,2 КБ вместо 180,3 КБ;
- 32 API-ready формы с consent, named fields и стабильными ID;
- аналитические события, PII-фильтр и адаптер Метрики/GA4;
- загрузка и отклонение проектных файлов;
- доступность без автоматических ошибок и предупреждений;
- Chrome и Edge smoke tests;
- laboratory LCP главной 1,93 секунды, CLS 0;
- production redirect manifest, IndexNow dry-run и migration runbook.
- автоматический T+1–14 monitor: 40/40 canonical URL, robots/sitemap,
  404/noindex и 84/84 migration rules;
- исполняемая CMS policy для шести ролей, MFA и publication gates проектов,
  партнёров и юридических документов;
- CRM delivery adapter: четыре маршрута, idempotency, retry/backoff,
  PII-safe events и dead-letter queue;
- application/configuration backup и safe restore drill с SHA-256,
  secrets exclusion, path traversal protection и проверкой release ZIP;
- ZIP archive-bomb protection: entry/size/ratio limits, encrypted/executable/
  traversal/malformed archive rejection;
- field LCP/CLS/INP telemetry на публичных страницах: sampling, rating,
  PII-safe payload; общий JS 16,7 КБ при бюджете 30 КБ;
- privacy-safe AI referral attribution для ChatGPT, Perplexity, Gemini,
  Copilot, Claude и Google AI Mode без полного referrer/query;
- production edge template: HTTPS canonical host, CSP/HSTS, HTML SWR,
  API bypass, stale-on-error и безопасный cache policy для unhashed assets;
- PII-safe messenger click tracking без передачи URL, username и телефона;
- consent-gated production loader Метрики/GA4: default-off, ID validation,
  Webvisor/Google Signals off; общий JS 18,8 КБ из 30 КБ;
- fail-closed launch gate: 16 внешних блокеров с owners/evidence; текущий
  статус `NO-GO`, integrity PASS;
- валидируемый owner approval intake: 17 фактов, 8 NAP-решений, 5 партнёров;
  approve/replace запрещены без evidence;
- доступный consent manager на 43 публичных страницах: default-deny,
  versioned choice, повторное открытие настроек и Escape→necessary-only;
  общий JS 22 КБ из 30 КБ;
- draft retention/deletion contract для 9 классов данных и 5-фазный incident
  response plan; integrity PASS, юридические сроки/роли остаются открытыми;
- server schema allowlist для 32 форм: unknown fields, oversized tracking IDs
  и unsafe referrer отклоняются до enqueue;
- `llms.txt`: 40/40 canonical URL, 100% sitemap coverage, без
  неподтверждённых числовых claims и ложного partner status;
- production monitor проверяет llms.txt coverage и публичный IndexNow key
  вместе с canonical, robots/sitemap и migration rules;
- fail-closed search submission registry для пяти операций: receipt, actor и
  UTC timestamp обязательны; фактическая отправка остаётся incomplete;
- editorial evidence 8/8: author, datePublished/dateModified, visible review
  date и scope limitation;
- project evidence 12/12: 10 archive-only, 2 verification-in-progress;
  недоказанный creator claim удалён из schema архивных кейсов;
- исполняемый staging mode и versioned release ZIP из 156 файлов с SHA-256
  manifest и проверкой восстановления.
- инвентарь 239 материалов Alutech и источники для технических значений W77,
  SL160, F50 и ALT150.
- медиа-инвентарь 551 файла: 34 project candidates, 200 partner assets,
  100 unverified references, 131 QA/derived; доказательные production/team/
  montage/video originals пока отсутствуют.

## Требует подтверждения владельца

- регионы обслуживания;
- единый телефон: на действующем сайте найден конфликт;
- адреса, email и часы работы;
- производственные мощности и другие цифры;
- партнёрские статусы и сертификаты;
- права на логотипы, кейсы, отзывы, фото и видео;
- архивные факты по проектам.

## Требует production-доступов

- удалённый staging, DNS, CDN и TLS;
- production-пользователи, Payload access hooks, MFA, PostgreSQL PITR/WAL и
  media cross-region restore test;
- CRM credentials/mapping, durable queue, production-антиспам и файловое хранилище;
- Метрика, Search Console, Яндекс Вебмастер и IndexNow submit;
- фактические 301/410 и HTTP 404/500;
- field Core Web Vitals;
- baseline трафика и позиций;
- отправка sitemap и переобход;
- фактический запуск и сохранение ежедневных отчётов T+1–14.

## Требует людей и устройств

- юридическая проверка;
- 13–15 пользовательских интервью;
- screen reader;
- Firefox, Safari и реальные мобильные устройства;
- производство фото и видео.

## Команда проверки

Стандартный gate:

`python run_quality_gate.py`

Полный gate с 90 визуальными проверками:

`python run_quality_gate.py --full`
