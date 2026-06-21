const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const menuToggle = document.querySelector("[data-menu-toggle]");

window.dataLayer = window.dataLayer || [];

const track = (event, parameters = {}) => {
  const payload = {
    event,
    page_path: window.location.pathname || window.location.href,
    page_title: document.title,
    ...parameters,
  };
  window.dataLayer.push(payload);
  window.dispatchEvent(new CustomEvent("bosfor:analytics", { detail: payload }));
};

const allowedProjectFileTypes = new Set([
  "pdf",
  "dwg",
  "dxf",
  "doc",
  "docx",
  "xls",
  "xlsx",
  "zip",
]);
const maxProjectFileSize = 20 * 1024 * 1024;
const createRequestId = () =>
  globalThis.crypto?.randomUUID?.() ||
  `bosfor-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const pageType = document.querySelector("article")
  ? "article"
  : document.querySelector(".case-hero")
    ? "project_or_product"
    : "landing";

track("page_view", { page_type: pageType });

const aluminumPages = new Set([
  "aluminum-windows.html",
  "doors.html",
  "portal-systems.html",
  "panoramic-glazing.html",
  "facades.html",
  "alutech.html",
]);
const currentFile = window.location.pathname.split("/").pop() || "index.html";
if (aluminumPages.has(currentFile)) {
  try {
    const viewed = new Set(
      JSON.parse(sessionStorage.getItem("bosfor_aluminum_pages") || "[]")
    );
    viewed.add(currentFile);
    sessionStorage.setItem("bosfor_aluminum_pages", JSON.stringify([...viewed]));
    if (
      viewed.size >= 3 &&
      !sessionStorage.getItem("bosfor_aluminum_depth_tracked")
    ) {
      sessionStorage.setItem("bosfor_aluminum_depth_tracked", "1");
      track("aluminum_depth", { aluminum_pages_viewed: viewed.size });
    }
  } catch {
    // Analytics storage must never block the page.
  }
}

const syncHeader = () => {
  header?.classList.toggle("scrolled", window.scrollY > 24);
};

syncHeader();
window.addEventListener("scroll", syncHeader, { passive: true });

menuToggle?.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Открыть меню" : "Закрыть меню");
  nav?.classList.toggle("open", !isOpen);
  document.body.classList.toggle("menu-open", !isOpen);
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || menuToggle?.getAttribute("aria-expanded") !== "true") {
    return;
  }
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Открыть меню");
  nav?.classList.remove("open");
  document.body.classList.remove("menu-open");
  menuToggle.focus();
});

nav?.addEventListener("click", (event) => {
  if (!(event.target instanceof HTMLAnchorElement)) return;
  menuToggle?.setAttribute("aria-expanded", "false");
  menuToggle?.setAttribute("aria-label", "Открыть меню");
  nav.classList.remove("open");
  document.body.classList.remove("menu-open");
});

document.querySelectorAll("[data-demo-form]").forEach((form) => {
  if (!form.id) {
    form.id = `form-${Array.from(document.querySelectorAll("[data-demo-form]")).indexOf(form) + 1}`;
  }

  const status = form.querySelector("[data-form-status]");
  status?.setAttribute("aria-live", "polite");
  status?.setAttribute("aria-atomic", "true");

  if (!form.querySelector(".form-trust")) {
    const trust = document.createElement("ul");
    trust.className = "form-trust form-wide";
    trust.setAttribute("aria-label", "Условия обработки обращения");
    trust.innerHTML =
      "<li>Ответ профильного специалиста</li><li>Без массовой рассылки</li><li>Данные защищены политикой сайта</li>";
    status?.before(trust);
  }

  let started = false;
  let startedAt = performance.now();
  const honeypot = document.createElement("input");
  honeypot.type = "text";
  honeypot.name = "_company_website";
  honeypot.tabIndex = -1;
  honeypot.autocomplete = "off";
  honeypot.setAttribute("aria-hidden", "true");
  honeypot.className = "form-honeypot";
  form.prepend(honeypot);

  form.addEventListener("focusin", () => {
    if (started) return;
    started = true;
    track("form_start", { form_id: form.id || "unnamed_form" });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const config = window.BOSFOR_FORM_CONFIG || {};
    const endpoint = config.endpoint;
    track("form_submit", {
      form_id: form.id || "unnamed_form",
      demo: !endpoint,
    });

    if (!endpoint) {
      if (status) {
        status.dataset.state = "success";
        status.textContent =
          "Форма работает в демонстрационном режиме. Интеграция с CRM будет добавлена на этапе разработки.";
      }
      return;
    }

    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button?.textContent;
    if (button) {
      button.disabled = true;
      button.textContent = "Отправляем…";
    }
    if (status) {
      status.dataset.state = "pending";
      status.textContent = "Отправляем заявку…";
    }

    const body = new FormData(form);
    body.set("form_id", form.id);
    body.set("audience", form.dataset.audience || body.get("audience") || "corporate");
    body.set("consent", body.get("consent") ? "true" : "false");
    body.set("page_url", window.location.href);
    body.set("referrer", document.referrer || "");
    const search = new URLSearchParams(window.location.search);
    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "yclid", "gclid"].forEach(
      (key) => {
        if (search.has(key)) body.set(key, search.get(key));
      }
    );

    const requestStarted = performance.now();
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body,
        headers: {
          "Idempotency-Key": createRequestId(),
          "X-Form-Elapsed-Ms": String(Math.round(performance.now() - startedAt)),
        },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || !result.ok) {
        const error = new Error(result.error || `http_${response.status}`);
        error.code = result.error || `http_${response.status}`;
        throw error;
      }
      if (status) {
        status.dataset.state = "success";
        status.textContent =
          result.message || "Заявка принята. Специалист свяжется с вами.";
      }
      track("lead_submit_success", {
        form_id: form.id,
        audience: form.dataset.audience || "corporate",
        lead_id: result.lead_id,
        response_time_ms: Math.round(performance.now() - requestStarted),
      });
      form.reset();
      startedAt = performance.now();
    } catch (error) {
      if (status) {
        status.dataset.state = "error";
        status.textContent =
          "Не удалось отправить заявку. Проверьте данные или позвоните нам.";
      }
      track("lead_submit_error", {
        form_id: form.id,
        audience: form.dataset.audience || "corporate",
        error_type: error.code || "network_error",
      });
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = originalButtonText;
      }
    }
  });

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("invalid", () => {
      if (!status) return;
      status.dataset.state = "error";
      status.textContent = "Проверьте обязательные поля формы.";
    });
    field.addEventListener("input", () => {
      if (!status || status.dataset.state !== "error") return;
      status.textContent = "";
      delete status.dataset.state;
    });
    if (field instanceof HTMLInputElement && field.type === "file") {
      field.addEventListener("change", () => {
        const files = Array.from(field.files || []);
        const rejected = files.find((file) => {
          const fileType = file.name.split(".").pop()?.toLowerCase() || "unknown";
          return !allowedProjectFileTypes.has(fileType) || file.size > maxProjectFileSize;
        });

        if (rejected) {
          const fileType = rejected.name.split(".").pop()?.toLowerCase() || "unknown";
          field.setCustomValidity(
            "Разрешены PDF, DWG, DXF, DOC, DOCX, XLS, XLSX и ZIP размером до 20 МБ."
          );
          if (status) {
            status.dataset.state = "error";
            status.textContent =
              "Файл не принят. Используйте PDF, DWG, DXF, DOC, DOCX, XLS, XLSX или ZIP до 20 МБ.";
          }
          track("file_upload_rejected", {
            form_id: form.id,
            file_type: fileType,
            file_size: rejected.size,
            rejection_reason: !allowedProjectFileTypes.has(fileType)
              ? "file_type"
              : "file_size",
          });
          return;
        }

        field.setCustomValidity("");
        files.forEach((file) => {
          track("file_upload", {
            form_id: form.id,
            file_type: file.name.split(".").pop()?.toLowerCase() || "unknown",
            file_size: file.size,
          });
        });
      });
    }
  });
});

document.addEventListener("click", (event) => {
  const link = event.target.closest("a");
  if (!link) return;
  const href = link.getAttribute("href") || "";
  const messenger = link.dataset.messenger;

  if (messenger) {
    track("messenger_click", {
      messenger,
      placement: link.dataset.placement || "unspecified",
    });
    return;
  }

  if (href.startsWith("tel:")) {
    track("phone_click", { phone: href.slice(4) });
    return;
  }
  if (href.startsWith("mailto:")) {
    track("email_click", { email: href.slice(7) });
    return;
  }

  if (link.classList.contains("button") || link.classList.contains("text-link")) {
    track("cta_click", {
      cta_text: link.textContent.trim().replace(/\s+/g, " ").slice(0, 120),
      target: href,
    });
  }

  if (/^https?:\/\//.test(href) && !href.includes(window.location.hostname)) {
    track("outbound_click", { target_url: href });
  }
});

if (document.querySelector(".article-page")) {
  let articleTracked = false;
  window.addEventListener(
    "scroll",
    () => {
      if (articleTracked) return;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      if (maxScroll > 0 && window.scrollY / maxScroll >= 0.75) {
        articleTracked = true;
        track("article_engaged", { article_title: document.title });
      }
    },
    { passive: true }
  );
}

const projectFilters = document.querySelector("[data-project-filters]");
const projectStatus = document.querySelector("[data-project-filter-status]");
const projectItems = Array.from(document.querySelectorAll("[data-project-category]"));

projectFilters?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-project-filter]");
  if (!button) return;
  const filter = button.dataset.projectFilter;

  projectFilters.querySelectorAll("[data-project-filter]").forEach((item) => {
    const active = item === button;
    item.classList.toggle("active", active);
    item.setAttribute("aria-pressed", String(active));
  });

  let visible = 0;
  projectItems.forEach((item) => {
    const matches = filter === "all" || item.dataset.projectCategory === filter;
    item.hidden = !matches;
    if (matches) visible += 1;
  });

  if (projectStatus) {
    projectStatus.textContent = `Показано проектов: ${visible}`;
  }
  track("project_filter", { project_filter: filter, visible_projects: visible });
});
