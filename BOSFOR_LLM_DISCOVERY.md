# БОСФОР — AI-readable discovery

Дата: 20 июня 2026 года

В корне сайта подготовлен `website/llms.txt`.

Файл:

- следует формату открытого предложения llms.txt;
- содержит краткое описание и curated canonical links;
- дополняет, но не заменяет robots.txt, sitemap.xml и JSON-LD;
- явно предупреждает о незавершённом owner approval контактов, цифр, географии
  и партнёрских статусов;
- не содержит неподтверждённых числовых claims;
- не заявляет официальный статус производителя/партнёра.

`audit_llms_txt.py` проверяет формат, дубли, принадлежность ссылок sitemap и
запрещённые claims.

Важно: llms.txt — community proposal, не официальный ranking factor и не
гарантия использования поисковой или AI-системой. Основные сигналы остаются:
доступный HTML, canonical, robots, sitemap, structured data, проверяемые факты,
источники и внешняя entity consistency.
