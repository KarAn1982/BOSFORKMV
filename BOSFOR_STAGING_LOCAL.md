# БОСФОР — исполняемый staging-профиль

Локальный staging запускается тем же `prototype_server.js`:

```powershell
$env:BOSFOR_STAGING_MODE="1"
$env:BOSFOR_STAGING_USER="review"
$env:BOSFOR_STAGING_PASSWORD="<strong-secret>"
node prototype_server.js
```

## Поведение

- все страницы и API закрыты Basic Authentication;
- `/robots.txt` доступен без авторизации и возвращает `Disallow: /`;
- каждый ответ содержит `X-Robots-Tag: noindex, nofollow, noarchive`;
- production canonical сохраняются для проверки миграции;
- формы используют prototype API;
- реальные CRM, Метрика и production-уведомления не подключаются.

Пароли не записываются в репозиторий и не должны совпадать с production.

Автоматическая проверка: `test_staging_mode.js`.

