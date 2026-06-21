# БОСФОР — tracking мессенджеров

Дата: 20 июня 2026 года

Подтверждённая ссылка размечается:

```html
<a
  href="https://t.me/confirmed_account"
  data-messenger="telegram"
  data-placement="header"
>Telegram</a>
```

Событие `messenger_click` передаёт только:

- `messenger`;
- `placement`;
- стандартный `page_path`.

URL, username, телефон и текст ссылки не передаются. Поэтому смена аккаунта не
создаёт PII в аналитике.

Фактические ссылки не добавляются до owner approval каналов. После публикации
проверить событие в Метрике/GA4 и связать с qualified leads.
