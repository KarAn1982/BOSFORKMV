(() => {
  const sources = [
    ["chatgpt", /(^|\.)chatgpt\.com$/i],
    ["openai", /(^|\.)openai\.com$/i],
    ["perplexity", /(^|\.)perplexity\.ai$/i],
    ["gemini", /(^|\.)gemini\.google\.com$/i],
    ["google_ai_mode", /(^|\.)google\.[a-z.]+$/i],
    ["copilot", /(^|\.)copilot\.microsoft\.com$/i],
    ["claude", /(^|\.)claude\.ai$/i],
    ["you", /(^|\.)you\.com$/i],
    ["phind", /(^|\.)phind\.com$/i],
  ];

  let referrer;
  try {
    referrer = document.referrer ? new URL(document.referrer) : null;
  } catch {
    return;
  }
  if (!referrer) return;

  let source = null;
  for (const [name, pattern] of sources) {
    if (!pattern.test(referrer.hostname)) continue;
    if (name === "google_ai_mode") {
      const path = `${referrer.pathname}${referrer.search}`;
      if (!/[?&]udm=50(?:&|$)|\/ai\//i.test(path)) continue;
    }
    source = name;
    break;
  }
  if (!source) return;

  window.dataLayer = window.dataLayer || [];
  const payload = {
    event: "ai_referral",
    ai_source: source,
    landing_path: window.location.pathname,
  };
  window.dataLayer.push(payload);
  window.dispatchEvent(
    new CustomEvent("bosfor:analytics", { detail: payload })
  );
})();
