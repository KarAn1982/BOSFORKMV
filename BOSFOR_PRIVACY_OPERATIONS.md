# БОСФОР — privacy operations

Дата: 20 июня 2026 года

Подготовлены draft-контракты:

- `deployment/data-retention-policy.json`;
- `deployment/incident-response-plan.json`;
- `audit_privacy_operations.py`.

Retention contract покрывает rejected payload, CRM retry/dead-letter, leads,
project files, security logs, analytics и consent evidence. Неутверждённые
юристом сроки оставлены `null`, а не выдуманы.

Deletion workflow требует:

- проверки личности заявителя;
- register запроса;
- удаления из DB, CRM, storage, email/exports и processors;
- tombstone для предотвращения возврата удалённых данных из backup.

Incident response содержит последовательность detect → contain → assess →
recover → close. Возврат production требует повторного release/security gate.

Production блокеры: назначить роли, утвердить сроки хранения и SLA удаления,
выбрать processors, заключить DPA и согласовать notification procedure.
