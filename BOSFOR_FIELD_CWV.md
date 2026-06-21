# БОСФОР — field Core Web Vitals

Дата: 20 июня 2026 года

`website/web-vitals.js` собирает реальные пользовательские метрики:

- LCP;
- CLS без shifts после недавнего ввода;
- INP как худшее взаимодействие по `interactionId`.

При `pagehide` или скрытии страницы отправляется событие `web_vital`:

- `metric_name`;
- `metric_value`;
- `metric_rating`;
- `navigation_type`;
- `page_path`;
- `sample_rate`.

PII, URL query и содержимое формы не передаются. Повторная отправка метрики в
одной странице блокируется.

Production sampling:

```js
window.BOSFOR_ANALYTICS_CONFIG = {
  yandexMetrikaId: 12345678,
  ga4Enabled: false,
  webVitalsSampleRate: 0.1
};
```

Рекомендуемый старт: 10%. Целевые пороги оцениваются на 75-м перцентиле за
28 дней отдельно mobile/desktop и по типам страниц. Пункт CWV закрывается
только полевыми данными: LCP ≤ 2500 мс, INP ≤ 200 мс, CLS ≤ 0,1.
