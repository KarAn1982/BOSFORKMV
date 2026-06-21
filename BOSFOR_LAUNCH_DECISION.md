# БОСФОР — launch decision

Дата: 20 июня 2026 года

Источник: `BOSFOR_LAUNCH_GATES.json`. Политика `fail_closed`.

`audit_launch_gate.py` создаёт:

- `reports/launch-gate-latest.json`;
- `reports/launch-gate-latest.md`.

Текущий ожидаемый статус: `NO-GO`. Это не ошибка прототипа. Публикация требует
внешних доказательств: owner approval, legal review, CRM/analytics/search
доступы, staging, production backup/CDN, полевые CWV и ручной QA.

Quality gate проверяет целостность launch manifest и запрещает помечать
owner facts, legal review или external profiles как `ready`, если registries
этому противоречат.

Статус gate меняется на `ready` только после приложения проверяемого evidence.
Устное решение без артефакта не закрывает gate.
