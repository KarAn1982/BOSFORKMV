# БОСФОР — активация Метрики и GA4

Дата: 20 июня 2026 года

`website/analytics-loader.js` загружает внешние счётчики только после явного
analytics consent. По умолчанию сеть не вызывается.

Production-конфигурация:

```js
window.BOSFOR_ANALYTICS_CONFIG = {
  yandexMetrikaEnabled: true,
  yandexMetrikaId: 12345678,
  ga4Enabled: false,
  ga4MeasurementId: null,
  analyticsConsent: false,
  webVitalsSampleRate: 0.1
};
```

После согласия CMP должна вызвать:

```js
window.dispatchEvent(
  new CustomEvent("bosfor:analytics-consent", {
    detail: { granted: true }
  })
);
```

Prototype CMP реализован в `website/consent-manager.js`.
Поведение и юридическая граница: `BOSFOR_CONSENT_MANAGER.md`.

Защита:

- неверные ID отклоняются;
- скрипты не загружаются повторно;
- Webvisor выключен по умолчанию;
- GA4 signals и ad personalization выключены;
- автоматический GA4 page_view выключен, чтобы не дублировать measurement plan;
- PII удаляет `analytics-adapter.js`.

Фактические пункты Метрики/GA4 закрываются после owner/legal approval, выдачи ID,
настройки CMP и проверки событий в production debug tools.
