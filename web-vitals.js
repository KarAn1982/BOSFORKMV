(() => {
  const config = window.BOSFOR_ANALYTICS_CONFIG || {};
  const sampleRate = Math.max(
    0,
    Math.min(1, Number(config.webVitalsSampleRate ?? 1))
  );
  if (
    !("PerformanceObserver" in window) ||
    sampleRate === 0 ||
    Math.random() > sampleRate
  ) {
    return;
  }

  window.dataLayer = window.dataLayer || [];
  const metrics = new Map();
  const sent = new Set();
  const navigationType =
    performance.getEntriesByType?.("navigation")?.[0]?.type || "navigate";

  const rating = (name, value) => {
    const thresholds = {
      LCP: [2500, 4000],
      CLS: [0.1, 0.25],
      INP: [200, 500],
    }[name];
    if (!thresholds) return "unknown";
    if (value <= thresholds[0]) return "good";
    if (value <= thresholds[1]) return "needs_improvement";
    return "poor";
  };

  const emit = (name, value) => {
    if (!Number.isFinite(value) || sent.has(name)) return;
    const precision = name === "CLS" ? 4 : 0;
    const normalized = Number(value.toFixed(precision));
    const payload = {
      event: "web_vital",
      metric_name: name,
      metric_value: normalized,
      metric_rating: rating(name, normalized),
      navigation_type: navigationType,
      page_path: window.location.pathname,
      sample_rate: sampleRate,
    };
    sent.add(name);
    window.dataLayer.push(payload);
    window.dispatchEvent(
      new CustomEvent("bosfor:analytics", { detail: payload })
    );
  };

  const observe = (type, callback, options = {}) => {
    if (!PerformanceObserver.supportedEntryTypes?.includes(type)) return;
    try {
      const observer = new PerformanceObserver((list) =>
        callback(list.getEntries())
      );
      observer.observe({ type, buffered: true, ...options });
    } catch {
      // Unsupported browser telemetry must never affect page behavior.
    }
  };

  observe("largest-contentful-paint", (entries) => {
    const last = entries.at(-1);
    if (last) metrics.set("LCP", last.startTime);
  });

  let cls = 0;
  observe("layout-shift", (entries) => {
    for (const entry of entries) {
      if (!entry.hadRecentInput) cls += entry.value;
    }
    metrics.set("CLS", cls);
  });

  const interactions = new Map();
  let fallbackInp = 0;
  observe(
    "event",
    (entries) => {
      for (const entry of entries) {
        if (entry.interactionId) {
          const previous = interactions.get(entry.interactionId) || 0;
          interactions.set(entry.interactionId, Math.max(previous, entry.duration));
        } else {
          fallbackInp = Math.max(fallbackInp, entry.duration);
        }
      }
      metrics.set(
        "INP",
        Math.max(fallbackInp, ...interactions.values(), 0)
      );
    },
    { durationThreshold: 40 }
  );

  const flush = () => {
    for (const [name, value] of metrics) emit(name, value);
  };
  window.addEventListener("pagehide", flush, { once: true });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flush();
  });
})();
