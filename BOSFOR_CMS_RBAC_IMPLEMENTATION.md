# БОСФОР — реализация CMS RBAC

Дата: 20 июня 2026 года

Источник правил: `deployment/cms-rbac.json`.

Исполняемый модуль `deployment/cms-policy.js`:

- проверяет разрешения роли на ресурс и действие;
- запрещает публикацию роли без `publish`;
- требует MFA для администратора и главного редактора;
- применяет обязательные publication gates по типу контента;
- валидирует полноту RBAC-конфигурации и обязательное журналирование.

## Publication gates

Project:

- техническое подтверждение;
- права на публикацию;
- только проверенные факты.

Partner:

- юридическое подтверждение;
- актуальный документ о статусе;
- разрешение на товарный знак.

Legal document:

- юридическое подтверждение.

## Подключение к Payload CMS

В `access` и `hooks.beforeChange` коллекции:

1. получить роль и MFA-состояние из авторизованного пользователя;
2. вызвать `hasPermission` для create/update/delete;
3. при переходе в `published` вызвать `publicationDecision`;
4. при отказе вернуть validation error с `reasons`;
5. записать actor, content ID, action, gates и timestamp в неизменяемый audit log.

Production-пункт считается закрытым после настройки пользователей, MFA,
Payload access hooks и проверки audit log на удалённом staging.
