(() => {
  const storageKey = "bosfor_consent_v1";
  const version = "2026-06-20";

  const readChoice = () => {
    try {
      const stored = JSON.parse(localStorage.getItem(storageKey) || "null");
      return stored?.version === version ? stored : null;
    } catch {
      return null;
    }
  };

  const dispatch = (granted) => {
    window.dispatchEvent(
      new CustomEvent("bosfor:analytics-consent", {
        detail: { granted: granted === true, version },
      })
    );
  };

  const save = (analytics) => {
    const choice = {
      version,
      necessary: true,
      analytics,
      decided_at: new Date().toISOString(),
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(choice));
    } catch {
      // Choice still applies to current page when storage is unavailable.
    }
    dispatch(analytics);
    return choice;
  };

  const existing = readChoice();
  if (existing) dispatch(existing.analytics);

  const render = () => {
    const settings = document.createElement("button");
    settings.type = "button";
    settings.className = "consent-settings";
    settings.textContent = "Настройки cookies";
    settings.setAttribute("aria-haspopup", "dialog");

    const banner = document.createElement("section");
    banner.className = "consent-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-modal", "false");
    banner.setAttribute("aria-labelledby", "consent-title");
    banner.hidden = Boolean(existing);
    banner.innerHTML = `
      <div class="consent-banner__body">
        <h2 id="consent-title">Настройки аналитики</h2>
        <p>Необходимые технологии обеспечивают работу сайта. Аналитика помогает оценивать страницы и включается только с вашего согласия.</p>
        <p><a href="privacy.html">Проект политики конфиденциальности</a></p>
      </div>
      <div class="consent-banner__actions">
        <button type="button" class="button button-outline" data-consent="necessary">Только необходимые</button>
        <button type="button" class="button" data-consent="analytics">Разрешить аналитику</button>
      </div>
    `;

    const close = () => {
      banner.hidden = true;
      settings.hidden = false;
      settings.focus();
    };
    banner.addEventListener("click", (event) => {
      const button = event.target.closest("[data-consent]");
      if (!button) return;
      save(button.dataset.consent === "analytics");
      close();
    });
    banner.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      save(false);
      close();
    });
    settings.addEventListener("click", () => {
      banner.hidden = false;
      settings.hidden = true;
      banner.querySelector("[data-consent='necessary']")?.focus();
    });

    settings.hidden = !existing;
    document.body.append(banner, settings);
    if (!existing) {
      banner.querySelector("[data-consent='necessary']")?.focus();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render, { once: true });
  } else {
    render();
  }
})();
