# БОСФОР — AI-search attribution

Дата: 20 июня 2026 года

`website/ai-attribution.js` классифицирует подтверждённые referrals:

- ChatGPT/OpenAI;
- Perplexity;
- Gemini;
- Microsoft Copilot;
- Claude;
- You.com;
- Phind;
- Google AI Mode при наличии характерного `udm=50` или AI-path.

Событие `ai_referral` содержит только:

- нормализованный `ai_source`;
- `landing_path` без query string.

Полный referrer, поисковый запрос, ID диалога и другие параметры не передаются.
Обычная Google-выдача не считается AI Mode.

Ограничение: часть AI-переходов не передаёт referrer. Для оценки используются
также брендовый спрос, landing pages, assisted conversions и вопрос об источнике
в CRM-квалификации.
