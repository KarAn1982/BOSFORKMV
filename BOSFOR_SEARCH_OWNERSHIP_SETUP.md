# БОСФОР — Search Console, Яндекс Вебмастер и отправка URL

## Рекомендуемая модель владения

### Google Search Console

Создать Domain property `bosforkmv.ru` и подтвердить DNS TXT. Domain property
охватывает HTTP/HTTPS и все поддомены. TXT-запись нельзя удалять после успешной
проверки. Дополнительно назначить минимум двух владельцев компании.

### Яндекс Вебмастер

Добавить `https://www.bosforkmv.ru/` и подтвердить права способом, выданным
кабинетом. Предпочтителен DNS; HTML-файл допустим, если он остаётся доступным без
авторизации и редиректа на другой домен.

Не создавать вымышленные verification-файлы: имя и содержимое выдаются
конкретным кабинетом и должны совпадать дословно.

## После подтверждения

1. Отправить `sitemap.xml` и `image-sitemap.xml`.
2. Проверить canonical host, HTTPS, robots и отсутствие случайного noindex.
3. Запросить переобход главной, ключевых услуг, каталога проектов и центра знаний.
4. Выполнить IndexNow submit только после production smoke test.
5. Сохранить владельцев, property ID, метод проверки и дату в реестре доступов.
6. Не удалять verification-токены при редизайне.

## Контроль

- verification URL/TXT реально доступен;
- sitemap возвращает 200 и корректный XML;
- URL из sitemap возвращают 200 и self-canonical;
- staging не добавляется в поисковые кабинеты;
- данные экспортируются до миграции и через 7, 14, 30 и 90 дней.

Конфигурация: `deployment/search-properties.json`.

Официальные инструкции:

- Google Search Console: https://support.google.com/webmasters/answer/9008080
- Яндекс Вебмастер: https://yandex.com/support/webmaster/en/service/rights

