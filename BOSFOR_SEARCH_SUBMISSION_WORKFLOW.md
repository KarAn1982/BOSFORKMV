# БОСФОР — search submission evidence

Дата: 20 июня 2026 года

Журнал: `BOSFOR_SEARCH_SUBMISSIONS.json`.

Он фиксирует sitemap в Google Search Console и Яндекс Вебмастере, batch 40
canonical URL через IndexNow и переобход шести приоритетных URL.

Статус `submitted` или `verified` допустим только при наличии UTC timestamp,
ответственного и receipt: URL, screenshot path, API response ID или экспорт
кабинета.

Проверка:

```powershell
python audit_search_submissions.py
```

Скрипт запрещает переобход URL вне sitemap и сверяет размер IndexNow batch с
текущими 40 canonical URL.

До production-доступов статусы остаются `pending_access` или
`ready_to_submit`. Это корректная подготовка, не фактическая отправка.
