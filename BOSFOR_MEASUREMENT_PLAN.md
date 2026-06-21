# БОСФОР — measurement plan

Дата версии: 19 июня 2026 года

## Главный KPI

Количество квалифицированных обращений с сайта отдельно по B2C и B2B.

## Воронки

### B2C

`landing_view → solution_view → project_view → form_start/call_click → lead`

Основные разрезы: тип изделия, город, тип объекта, устройство, источник.

### B2B

`landing_view → competence_view → project_view → brief_start → qualified_lead`

Основные разрезы: тип объекта, стадия проекта, компания, регион, предполагаемый
объём и наличие документации.

## События

| Событие | Триггер | Ключевые параметры |
|---|---|---|
| `page_view` | открытие страницы | `page_path`, `page_title`, `page_type` |
| `phone_click` | клик по `tel:` | `phone`, `page_path` |
| `email_click` | клик по `mailto:` | `email`, `page_path` |
| `form_start` | первое взаимодействие с формой | `form_id`, `page_path` |
| `form_submit` | отправка формы | `form_id`, `page_path`, `demo` |
| `cta_click` | клик по основной кнопке | `cta_text`, `target`, `page_path` |
| `outbound_click` | переход на внешний домен | `target_url` |
| `article_engaged` | 75% глубины статьи | `page_path`, `article_title` |
| `project_view` | просмотр карточки проекта | `project_slug` |
| `file_upload` | добавление проектного файла | `file_type`, `form_id` |
| `file_upload_rejected` | отклонение файла | `file_type`, `file_size`, `rejection_reason` |
| `aluminum_depth` | просмотр 3+ алюминиевых направлений | `aluminum_pages_viewed` |
| `lead_submit_success` | сервер подтвердил создание лида | `form_id`, `audience`, `lead_id` |
| `lead_submit_error` | сервер отклонил или не принял лид | `form_id`, `audience`, `error_type` |
| `web_vital` | скрытие или закрытие страницы | `metric_name`, `metric_value`, `metric_rating`, `navigation_type` |
| `ai_referral` | подтверждённый переход из AI-интерфейса | `ai_source`, `landing_path` |
| `messenger_click` | клик по подтверждённому каналу | `messenger`, `placement`, `page_path` |

## Источники AI-search

Отдельно сохранять landing page и referrer для переходов с:

- ChatGPT;
- Perplexity;
- Gemini;
- Copilot;
- Claude;
- других AI-интерфейсов по мере появления данных.

Нельзя оценивать AI-search только по referrer: часть переходов приходит без него.
Дополнительно отслеживаются брендовый спрос, landing pages и лиды, указывающие
AI-систему как источник.

Классификатор и privacy-ограничения: `BOSFOR_AI_ATTRIBUTION.md`.

## Квалификация лида

### B2C

- город;
- тип объекта;
- тип конструкции;
- ориентировочное количество или размеры;
- срок принятия решения.

### B2B

- компания и роль контакта;
- тип и регион объекта;
- стадия проекта;
- ориентировочный объём;
- наличие документации;
- предполагаемый срок выбора подрядчика.

## Интеграция

Прототип отправляет нейтральные события в `window.dataLayer` и
`CustomEvent("bosfor:analytics")`. На production эти события подключаются к
Яндекс Метрике, CRM и при необходимости GA4 без переписывания интерфейса.

`analytics-adapter.js` передаёт события в Метрику и GA4 только при наличии
production-конфигурации. Имя, телефон, email, компания, текст заявки и имя файла
отбрасываются перед передачей.

`analytics-loader.js` загружает счётчики только после явного consent event.
Production activation: `BOSFOR_ANALYTICS_ACTIVATION.md`.

Field LCP, CLS и INP собираются модулем `web-vitals.js`. Sampling и критерии
28-дневной оценки описаны в `BOSFOR_FIELD_CWV.md`.

Messenger target/username/телефон не передаются. Разметка подтверждённых
каналов: `BOSFOR_MESSENGER_TRACKING.md`.

## Дашборд

Минимальный набор:

- обращения и квалифицированные лиды по неделям;
- конверсия B2C и B2B;
- источники и посадочные страницы;
- звонки и формы;
- услуги и проекты, просмотренные перед обращением;
- органические переходы и AI-search;
- доля потерянных и неквалифицированных лидов.
