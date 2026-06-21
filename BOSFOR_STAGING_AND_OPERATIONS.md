# БОСФОР — staging и эксплуатационная готовность

Дата: 19 июня 2026 года

## Staging

Рекомендуемый адрес: `staging.bosforkmv.ru`.

Обязательные условия:

- Basic Authentication до любого контента;
- `X-Robots-Tag: noindex, nofollow, noarchive` на всех ответах;
- отдельный `robots.txt` с `Disallow: /`;
- тестовые CRM-воронки и счётчики аналитики;
- отсутствие production-секретов и реальных получателей уведомлений;
- preview CMS доступен только авторизованным пользователям;
- визуальная регрессия, link-check, structured data и формы входят в release gate.

Пример reverse proxy: `deployment/staging-nginx.conf`.

## Резервное копирование

Политика: `deployment/backup-policy.json`.

Минимальный стандарт:

- PostgreSQL: point-in-time recovery и ежедневная полная копия;
- медиа: versioning, soft delete и отдельная копия;
- конфигурация: versioned release artifacts без секретов в репозитории;
- ежемесячное восстановление на staging;
- RPO базы — 1 час, RTO — 4 часа.

Пункт считается настроенным только после успешного тестового восстановления.

Application/configuration restore drill реализован в `backup_restore.py` и
проверяется автоматически. Инструкция: `BOSFOR_BACKUP_RESTORE_IMPLEMENTATION.md`.
Database PITR/WAL, media cross-region copy и удалённый staging restore остаются
production gates.

## Роли CMS

Матрица: `deployment/cms-rbac.json`.

Критические правила:

- контент-менеджер не публикует самостоятельно;
- проект нельзя опубликовать без технического подтверждения и прав на контент;
- статус официального партнёра требует действующего документа;
- выгрузки лидов доступны только ограниченным ролям и журналируются;
- MFA обязательно для администратора и главного редактора.

## Формы и антиспам

Политика: `deployment/lead-security-policy.json`.

Клиентская проверка не считается защитой. На сервере обязательны rate limit,
honeypot, schema validation, проверка Origin, MIME и сигнатуры файлов, антивирус,
idempotency и очередь повторной передачи в CRM.

Retention/deletion draft и incident response plan:
`BOSFOR_PRIVACY_OPERATIONS.md`. Неутверждённые юридические сроки оставлены
пустыми и остаются production gate.

## IndexNow

В корне сайта подготовлен key-файл. Скрипт
`deployment/indexnow-submit.js` читает только URL из чистого sitemap.

Проверка без отправки:

`node deployment/indexnow-submit.js`

Фактическая отправка после production-деплоя:

`node deployment/indexnow-submit.js --submit`

Первую отправку выполнять только после проверки доступности key-файла и всех URL
с production-домена.

## Мониторинг запуска

`monitor_production.js` проверяет staging через transport override и production
напрямую. Контроль включает 40 canonical URL, robots/sitemap, 404/noindex и 84
решения migration manifest. Порядок запуска и артефакты описаны в
`BOSFOR_PRODUCTION_MONITORING.md`.

## Production edge

Шаблон CDN/reverse proxy: `deployment/production-nginx.conf`.
TTL-контракт: `deployment/edge-cache-policy.json`.
Unhashed assets не помечаются `immutable`; до внедрения content hashes каждый
релиз требует CDN purge. Детали: `BOSFOR_EDGE_CACHE.md`.
