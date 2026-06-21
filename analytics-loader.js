(() => {
  const config = window.BOSFOR_ANALYTICS_CONFIG || {};
  let loaded = false;

  const validMetrikaId = (value) =>
    Number.isInteger(Number(value)) && Number(value) > 0;
  const validGa4Id = (value) => /^G-[A-Z0-9]+$/i.test(String(value || ""));

  const appendScript = (src, id) => {
    if (document.getElementById(id)) return;
    const script = document.createElement("script");
    script.id = id;
    script.async = true;
    script.src = src;
    document.head.append(script);
  };

  const start = () => {
    if (loaded) return;
    loaded = true;

    if (config.yandexMetrikaEnabled && validMetrikaId(config.yandexMetrikaId)) {
      window.ym =
        window.ym ||
        function (...args) {
          (window.ym.a = window.ym.a || []).push(args);
        };
      window.ym.l = Date.now();
      appendScript("https://mc.yandex.ru/metrika/tag.js", "bosfor-yandex-metrika");
      window.ym(Number(config.yandexMetrikaId), "init", {
        clickmap: true,
        trackLinks: true,
        accurateTrackBounce: true,
        webvisor: false,
      });
    }

    if (config.ga4Enabled && validGa4Id(config.ga4MeasurementId)) {
      window.dataLayer = window.dataLayer || [];
      window.gtag =
        window.gtag ||
        function (...args) {
          window.dataLayer.push(args);
        };
      appendScript(
        `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(
          config.ga4MeasurementId
        )}`,
        "bosfor-ga4"
      );
      window.gtag("js", new Date());
      window.gtag("config", config.ga4MeasurementId, {
        send_page_view: false,
        allow_google_signals: false,
        allow_ad_personalization_signals: false,
      });
    }
  };

  if (config.analyticsConsent === true) start();
  window.addEventListener("bosfor:analytics-consent", (event) => {
    if (event.detail?.granted === true) start();
  });
})();
