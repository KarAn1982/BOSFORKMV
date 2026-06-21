# БОСФОР — owner approval workflow

Дата: 20 июня 2026 года

Рабочий файл: `BOSFOR_OWNER_APPROVAL_INPUT.json`.

Он содержит:

- 8 NAP/географических решений;
- все 17 фактов из fact registry;
- 5 производителей/партнёров;
- approver, роль и дату решения;
- evidence для каждого подтверждения или замены.

Правила:

- `approve` без evidence запрещён;
- `replace` требует новый claim/value и evidence;
- решение по конфликтному телефону требует явного `conflict_resolution`;
- официальный партнёрский статус требует evidence и дату окончания;
- разрешение на логотип требует evidence;
- файл не обновляет сайт автоматически.

Проверка:

```powershell
python validate_owner_approval.py
```

После заполнения редактор вручную переносит решения в fact registry, NAP,
CMS и legal documents. Затем запускаются все audits. Разделение intake и
публикации предотвращает случайный выпуск неподтверждённых данных.
