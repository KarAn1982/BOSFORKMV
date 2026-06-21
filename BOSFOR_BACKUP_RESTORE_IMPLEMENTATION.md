# БОСФОР — backup и restore drill

Дата: 20 июня 2026 года

`backup_restore.py` создаёт проверяемую копию application/configuration слоя:

- последний immutable release ZIP и его SHA-256 manifest;
- deployment-конфигурацию и политики;
- migration manifest;
- runbook запуска и эксплуатации;
- отдельный backup manifest с размером и SHA-256 каждого файла.

Restore verifier:

- блокирует абсолютные пути и `../` path traversal;
- отклоняет секретные файлы и ключи;
- проверяет размер и SHA-256;
- восстанавливает в отдельный каталог;
- открывает вложенный release ZIP и проверяет обязательные файлы сайта.

Создание:

```powershell
python backup_restore.py create
```

Проверка без изменения рабочей папки:

```powershell
python backup_restore.py verify backups/<archive>.zip
```

## Граница готовности

Этот пакет закрывает application/configuration restore drill. Production-пункт
«резервное копирование» остаётся открытым до подтверждения:

- PostgreSQL PITR/WAL и ежедневного полного backup;
- S3 versioning, inventory и cross-region copy;
- зашифрованных отдельных credentials;
- ежемесячного restore на удалённый staging;
- измеренного RPO ≤ 1 час и RTO ≤ 4 часа.
