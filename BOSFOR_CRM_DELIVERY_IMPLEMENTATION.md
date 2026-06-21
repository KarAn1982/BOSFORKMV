# БОСФОР — CRM delivery layer

Дата: 20 июня 2026 года

`deployment/crm-delivery.js` отделяет приём заявки от конкретной CRM:

- маршрутизирует четыре аудитории по `deployment/crm-routing.json`;
- передаёт стабильный `Idempotency-Key` при каждой попытке;
- повторяет временные `429/5xx/timeout` с exponential backoff;
- прекращает повторы после лимита или 24 часов;
- переносит постоянные ошибки в dead-letter queue;
- пишет server events без имени, телефона, email, сообщения и файлов.

Mock CRM-тест подтверждает: две временные ошибки, успешная третья доставка,
сохранение idempotency key, подавление дубля и dead-letter для постоянной ошибки.

## Production-подключение

До запуска владелец процесса подтверждает:

- CRM-вендора и endpoint;
- ID воронок и ответственных вместо symbolic keys;
- секрет webhook;
- зашифрованную durable queue в PostgreSQL/managed queue;
- закрытое файловое хранилище и signed URLs;
- alert после трёх ошибок;
- retention и доступ к dead-letter queue.

`MemoryDeliveryQueue` предназначена только для тестов. Production-интеграция
обязана внедрить durable queue с транзакционным enqueue до ответа пользователю.
