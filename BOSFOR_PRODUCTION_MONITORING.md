# БОСФОР — автоматический мониторинг запуска

Дата: 20 июня 2026 года

`monitor_production.js` выполняет ежедневный технический контроль T+1–14:

- все 40 URL из production sitemap возвращают `200`;
- canonical каждого URL совпадает с адресом в sitemap;
- индексируемые страницы не получают `noindex` и содержат один H1;
- production robots открыт и содержит OAI-SearchBot, GPTBot и sitemap;
- `llms.txt` доступен и содержит все 40 canonical URL;
- IndexNow key-файл доступен, его содержимое совпадает с именем;
- случайный отсутствующий URL возвращает `404` с `noindex`;
- все 84 решения migration manifest возвращают ожидаемые `200/301/410`;
- `301` ведут на точное назначение, `410` закрыты от индексации;
- ответы медленнее 3000 мс попадают в предупреждения.

## Запуск

```powershell
node monitor_production.js
```

Результаты:

- `reports/production-monitoring-latest.json` — машинный отчёт;
- `reports/production-monitoring-latest.md` — оперативная сводка.

Проверка staging или локального reverse proxy:

```powershell
node monitor_production.js --target-origin http://127.0.0.1:4173 --no-write
```

`--target-origin` меняет только транспорт. Заголовок `Host` и проверяемые
canonical сохраняют production-домены. Поэтому один и тот же контроль применим
до и после переключения DNS.

## Расписание T+1–14

Запускать минимум раз в сутки после деплоя. Ненулевой exit code означает
release incident. JSON-отчёт сохранять как артефакт каждого запуска.

Скрипт проверяет техническую доступность, миграцию и SEO/GEO discovery files. CRM delivery, данные
Search Console/Яндекс Вебмастера, органический трафик и field CWV требуют
отдельных production-доступов и остаются ручными release gates.
