(() => {
  const config = window.BOSFOR_ANALYTICS_CONFIG || {};
  const prohibitedKeys = new Set([
    "name",
    "phone",
    "email",
    "company",
    "message",
    "file_name",
  ]);

  const sanitize = (value) =>
    Object.fromEntries(
      Object.entries(value || {}).filter(
        ([key, item]) =>
          !prohibitedKeys.has(key) &&
          ["string", "number", "boolean"].includes(typeof item)
      )
    );

  window.addEventListener("bosfor:analytics", (event) => {
    const payload = sanitize(event.detail);
    const eventName = payload.event;
    if (!eventName) return;
    delete payload.event;

    if (
      config.yandexMetrikaId &&
      typeof window.ym === "function"
    ) {
      window.ym(config.yandexMetrikaId, "reachGoal", eventName, payload);
    }

    if (
      config.ga4Enabled &&
      typeof window.gtag === "function"
    ) {
      window.gtag("event", eventName, payload);
    }
  });
})();
