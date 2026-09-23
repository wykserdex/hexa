"use strict";
const paths = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
  flask:
    '<path d="M9 3h6m-5 0v6l-6 10a1.4 1.4 0 0 0 1.2 2h13.6a1.4 1.4 0 0 0 1.2-2L14 9V3M7 15h10"/><path d="M10 18h.01M14 17h.01"/>',
  terminal:
    '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3m6 0h4"/>',
  download: '<path d="M12 3v12m-4-4 4 4 4-4M4 16v4h16v-4"/>',
  upload: '<path d="M12 16V4m-4 4 4-4 4 4M4 16v4h16v-4"/>',
  shield:
    '<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  play: '<path d="m8 4 13 8-13 8V4Z"/>',
  pause: '<path d="M8 5v14M16 5v14" stroke-width="3"/>',
  reset: '<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
  plug: '<path d="M8 3v5m8-5v5M6 8h12v3a6 6 0 0 1-12 0V8Zm6 9v4"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  crosshair:
    '<circle cx="12" cy="12" r="7"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/><circle cx="12" cy="12" r="1"/>',
  route:
    '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 6h9a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h8"/>',
  hand: '<path d="M8 12V5a2 2 0 0 1 4 0v7-9a2 2 0 0 1 4 0v9-6a2 2 0 0 1 4 0v8c0 5-2 7-6 7h-1c-3 0-5-2-6-4l-3-4a2 2 0 0 1 3-3l1 2"/>',
  mouse: '<rect x="6" y="2" width="12" height="20" rx="6"/><path d="M12 2v6"/>',
  sparkles:
    '<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7L12 3ZM19 2v4m-2-2h4"/>',
  bolt: '<path d="m14 2-10 12h7l-1 8 10-12h-7l1-8Z"/>',
  heart:
    '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
  "heart-pulse":
    '<path d="M3 12H1m22 0h-5l-3-5-4 10-3-5H3m17.8-7.4a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.01"/>',
  sliders:
    '<path d="M4 6h6m4 0h6M4 12h2m4 0h10M4 18h10m4 0h2"/><circle cx="12" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="16" cy="18" r="2"/>',
  "arrow-up-right": '<path d="M6 18 18 6M6 6h12v12"/>',
  trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
  wind: '<path d="M3 8h12a3 3 0 1 0-3-3M2 12h17a3 3 0 1 1-3 3M5 17h5a2 2 0 1 1-2 2"/>',
  flame:
    '<path d="M12 2c1 6-5 6-5 11a5 5 0 0 0 10 0c0-3-2-4-2-6-1 2-2 3-2 3s2-4-1-8Z"/><path d="M11 15c-2 3 1 5 3 3"/>',
  waves:
    '<path d="M2 6c3-4 5 4 8 0s5 4 8 0 4 0 4 0M2 12c3-4 5 4 8 0s5 4 8 0 4 0 4 0M2 18c3-4 5 4 8 0s5 4 8 0 4 0 4 0"/>',
  sword: '<path d="m4 3 6 2 10 11-4 4L5 10 4 3Zm9 13 5-5M3 21l5-5m-4-1 5 5"/>',
  users:
    '<circle cx="8" cy="7" r="3"/><path d="M2 21v-4a6 6 0 0 1 12 0v4M15 4a3 3 0 0 1 0 6m2 4a5 5 0 0 1 5 5v2"/>',
  x: '<path d="m6 6 12 12M6 18 18 6"/>',
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.grid}</svg>`;
}
function fillIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => {
    el.innerHTML = icon(el.dataset.icon);
  });
}
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const stamp = (t, decimal = false) =>
  `${Math.floor(t / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(t % 60)
    .toString()
    .padStart(2, "0")}${decimal ? "." + Math.floor((t % 1) * 10) : ""}`;
const fmt = (n) => Math.round(n).toLocaleString("ru-RU");
const meta = {
  combo: {
    icon: "bolt",
    desc: "Четыре способности · точные интервалы",
    details:
      "Последовательность с резервированием героя. Фарм ждёт завершения; ошибка адаптера или ручной ввод отменяют оставшиеся шаги.",
    note: "0 → 0.60 → 1.25 → 1.95 с",
    contract: "CAST · цель · группа · дедлайн",
  },
  guardian: {
    icon: "shield",
    desc: "Восстановление при низком HP",
    details:
      "Наблюдает за здоровьем и использует предмет по порогу. Проверяет перезарядку и может сработать во время комбо, не прерывая его.",
    note: "Приоритет выживания",
    contract: "ITEM · исполнитель · дедлайн",
  },
  farm: {
    icon: "sword",
    desc: "Ближайший лагерь · фоновая задача",
    details:
      "Выбирает ближайшего живого нейтрала, подходит на дистанцию и атакует. Уступает героя комбо и немедленно останавливается по ручному вводу.",
    note: "Низкий приоритет",
    contract: "MOVE / ATTACK · цель",
  },
  micro: {
    icon: "users",
    desc: "Два союзника · независимые приказы",
    details:
      "Управляет двумя Искрами отдельно от героя. Здоровые юниты сближаются и атакуют, раненые с HP ниже 35% отступают к герою.",
    note: "Отдельная очередь на юнита",
    contract: "MOVE / ATTACK · исполнитель",
  },
};
let state = null,
  connected = false,
  currentPage = "overview",
  logFilter = "all",
  fetching = false,
  lastReceived = 0,
  failureCount = 0;
let renderSignature = "",
  logSignature = "",
  eventSignature = "",
  queueSignature = "";
const positions = new Map();
function toast(text, error = false) {
  const el = document.createElement("div");
  el.className = "toast" + (error ? " error" : "");
  el.innerHTML = icon(error ? "info" : "check") + `<span>${esc(text)}</span>`;
  $("toast-container").append(el);
  setTimeout(() => {
    el.classList.add("out");
    setTimeout(() => el.remove(), 230);
  }, 3500);
}
function setConnected(value) {
  connected = value;
  $("connection-dot").style.background = value ? "var(--green)" : "var(--red)";
  $("connection-label").textContent = value
    ? "Движок подключён"
    : "Нет подключения";
  $("offline-overlay").hidden = value;
}
async function getState() {
  if (fetching) return;
  fetching = true;
  try {
    const r = await fetch(
      currentPage === "logs" ? "/api/export" : "/api/state",
      { signal: AbortSignal.timeout(5000) },
    );
    if (!r.ok) throw new Error("Server error");
    const next = await r.json();
    if (!state || next.run_id !== state.run_id) {
      positions.clear();
      renderSignature = "";
      logSignature = "";
      eventSignature = "";
      queueSignature = "";
    }
    state = next;
    lastReceived = performance.now();
    failureCount = 0;
    setConnected(true);
    render();
  } catch (e) {
    failureCount++;
    if (failureCount >= 2 || !state) setConnected(false);
  } finally {
    fetching = false;
  }
}
async function poll() {
  await getState();
  setTimeout(poll, document.hidden ? 800 : 180);
}
async function command(action, params = {}, success = "") {
  try {
    const r = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...params }),
      signal: AbortSignal.timeout(5000),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Не удалось выполнить действие");
    if (success) toast(success);
    await getState();
    return true;
  } catch (e) {
    toast(
      e.message === "Failed to fetch" ? "Нет связи с движком" : e.message,
      true,
    );
    return false;
  }
}
function download(name, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function route() {
  let page = location.hash.slice(1) || "overview";
  if (!["overview", "modules", "scenarios", "logs"].includes(page))
    page = "overview";
  currentPage = page;
  document.querySelectorAll(".page").forEach((el) => {
    el.hidden = el.id !== `page-${page}`;
    el.classList.toggle("active", !el.hidden);
  });
  document
    .querySelectorAll(".nav-item")
    .forEach((el) => el.classList.toggle("active", el.dataset.page === page));
  $("breadcrumb-current").textContent = {
    overview: "Полигон",
    modules: "Модули",
    scenarios: "Сценарии",
    logs: "Журнал",
  }[page];
  window.scrollTo({ top: 0, behavior: "instant" });
  if (state) render();
  getState();
}
const TITLE_MAP = {
  combo: "Комбо",
  guardian: "Автопредметы",
  farm: "Фарм",
  micro: "Микроконтроль",
};
const titleOf = (key) => TITLE_MAP[key] || meta[key]?.title || key;
function switchMarkup(key) {
  return `<button class="module-switch" role="switch" aria-checked="false" aria-label="${esc(titleOf(key))}" data-toggle-module="${key}"><span class="toggle-track"></span></button>`;
}
function initialiseModules() {
  $("module-list").innerHTML = Object.entries(meta)
    .map(
      ([key, m]) =>
        `<div class="module-row" id="module-row-${key}"><div class="module-row-top"><div class="module-icon ${key}">${icon(m.icon)}</div><div class="module-row-info"><div class="module-row-title">${esc(titleOf(key))} <span class="priority-chip" id="priority-${key}"></span></div><div class="module-row-desc">${m.desc}</div></div>${switchMarkup(key)}</div><div class="module-row-foot"><span class="mini-dot"></span><span id="status-${key}">Ожидание</span></div></div>`,
    )
    .join("");
  $("module-settings").innerHTML = Object.entries(meta)
    .map(
      ([key, m]) =>
        `<article class="panel module-setting-card"><div class="module-setting-head"><div class="module-icon ${key}">${icon(m.icon)}</div><div><h2>${esc(titleOf(key))}</h2><small>${m.contract}</small></div>${switchMarkup(key)}</div><p>${m.details}</p><div class="module-detail-line"><span>${m.note}</span><strong>Приоритет <span id="settings-priority-${key}"></span></strong></div>${key === "guardian" ? '<div class="threshold-control"><div class="threshold-label"><label for="threshold-slider">Использовать предмет при HP ≤</label><strong id="threshold-label">40%</strong></div><input id="threshold-slider" type="range" min="20" max="80" step="5" value="40" aria-label="Порог здоровья для автопредмета"></div>' : ""}${key === "combo" ? '<div class="sequence-preview"><span class="sequence-pill">Вихрь<small>0.00 с</small></span><b>→</b><span class="sequence-pill">Импульс<small>0.60 с</small></span><b>→</b><span class="sequence-pill">Метеор<small>1.25 с</small></span><b>→</b><span class="sequence-pill">Волна<small>1.95 с</small></span></div>' : ""}<div class="module-status-big"><span class="mini-dot green"></span><span id="settings-status-${key}">Ожидание</span></div></article>`,
    )
    .join("");
  $("threshold-slider").addEventListener(
    "input",
    (e) => ($("threshold-label").textContent = e.target.value + "%"),
  );
  $("threshold-slider").addEventListener("change", (e) =>
    command(
      "module",
      { key: "guardian", threshold: Number(e.target.value) },
      "Порог автопредмета сохранён",
    ),
  );
}
function pluginEntry(m) {
  return {
    title: m.title || m.key,
    icon: "plug",
    desc: m.description || "Внешний модуль-плагин",
    details:
      m.description ||
      "Плагин загружен из каталога --plugins-dir и соблюдает общие правила: намерения вместо прямого ввода, приоритеты, ручной контроль игрока.",
    note: "Внешний плагин · файл читается при старте сервера",
    contract: "LabModule · намерения · приоритет",
  };
}
function ensurePluginRows() {
  state.modules.forEach((m) => {
    if (meta[m.key] || $("module-row-" + m.key)) return;
    meta[m.key] = pluginEntry(m);
    const key = m.key;
    const visual = meta[key];
    $("module-list").insertAdjacentHTML(
      "beforeend",
      `<div class="module-row" id="module-row-${key}"><div class="module-row-top"><div class="module-icon plugin">${icon(visual.icon)}</div><div class="module-row-info"><div class="module-row-title">${esc(titleOf(key))} <span class="priority-chip" id="priority-${key}"></span></div><div class="module-row-desc">${esc(visual.desc)}</div></div>${switchMarkup(key)}</div><div class="module-row-foot"><span class="mini-dot"></span><span id="status-${key}">Ожидание</span></div></div>`,
    );
    $("module-settings").insertAdjacentHTML(
      "beforeend",
      `<article class="panel module-setting-card"><div class="module-setting-head"><div class="module-icon plugin">${icon(visual.icon)}</div><div><h2>${esc(titleOf(key))}</h2><small>${esc(visual.contract)}</small></div>${switchMarkup(key)}</div><p>${esc(visual.details)}</p><div class="module-detail-line"><span>${esc(visual.note)}</span><strong>Приоритет <span id="settings-priority-${key}"></span></strong></div><div class="module-status-big"><span class="mini-dot green"></span><span id="settings-status-${key}">Ожидание</span></div></article>`,
    );
  });
}
function renderModules() {
  ensurePluginRows();
  state.modules.forEach((m) => {
    document
      .querySelectorAll(`[data-toggle-module="${m.key}"]`)
      .forEach((b) => {
        b.setAttribute("aria-checked", String(m.enabled));
        b.disabled = !m.supported;
      });
    $(`module-row-${m.key}`).classList.toggle("off", !m.enabled);
    $(`status-${m.key}`).textContent = m.status;
    $(`settings-status-${m.key}`).textContent = m.status;
    $(`priority-${m.key}`).textContent = `P${m.priority}`;
    $(`settings-priority-${m.key}`).textContent = m.priority;
  });
  if (document.activeElement !== $("threshold-slider")) {
    $("threshold-slider").value = state.item.threshold;
    $("threshold-label").textContent = state.item.threshold + "%";
  }
  $("modules-count-nav").textContent = state.modules.length;
  $("modules-count-panel").textContent = state.modules.length;
}
function labelCommand(c) {
  return c.kind === "cast"
    ? { tornado: "Вихрь", emp: "Импульс", meteor: "Метеор", blast: "Волна" }[
        c.ability
      ] || c.ability
    : c.kind === "item"
      ? "Восстановление"
      : c.kind === "move"
        ? "Движение"
        : c.kind === "attack"
          ? "Атака"
          : "Остановка";
}
const sourceName = (key) =>
  TITLE_MAP[key] ||
  {
    manual: "Игрок",
    engine: "Движок",
    scenario: "Сценарий",
    config: "Конфигурация",
    plugins: "Плагины",
  }[key] ||
  state?.modules.find((m) => m.key === key)?.title ||
  key;
const unitName = (id) => state?.units.find((u) => u.id === id)?.name || id;
function renderQueue() {
  const history = state.history
    .filter(
      (c) =>
        ["combo", "guardian", "manual"].includes(c.source) &&
        state.time - (c.finished || 0) < 8,
    )
    .slice(-4);
  const rows = state.pending.length ? state.pending : history;
  const sig =
    JSON.stringify(rows.map((c) => [c.id, c.status])) +
    Math.floor(state.time * 10);
  if (sig === queueSignature) return;
  queueSignature = sig;
  $("queue-count").textContent = state.pending.length;
  if (!rows.length) {
    $("queue-list").innerHTML =
      `<div class="queue-empty"><span>${icon("check")}</span><div><strong>Очередь свободна</strong><small>Запусти комбо — здесь появятся шаги и подтверждения.</small></div></div>`;
    return;
  }
  $("queue-list").innerHTML = rows
    .map(
      (c) =>
        `<div class="queue-row"><span class="queue-time">${c.status === "pending" ? "+" + Math.max(0, c.due - state.time).toFixed(2) : stamp(c.finished || 0)}</span><div class="queue-action">${esc(labelCommand(c))}<small>${esc(unitName(c.actor))} → ${esc(c.target ? unitName(c.target) : "позиция")}</small></div><span class="priority-chip">P${c.priority}</span><span class="queue-status ${c.status}">${{ pending: "В ОЧЕРЕДИ", executed: "ИСПОЛНЕНО", cancelled: "ОТМЕНЕНО", rejected: "ОТКАЗ", expired: "ИСТЕКЛО" }[c.status]}</span></div>`,
    )
    .join("");
}
function renderEvents() {
  const rows = state.events.slice(-5).reverse();
  const sig = JSON.stringify(rows.map((e) => e.id));
  if (sig === eventSignature) return;
  eventSignature = sig;
  $("event-list").innerHTML = rows
    .map(
      (e) =>
        `<div class="event ${esc(e.level)}"><span class="event-status"></span><div class="event-text">${esc(e.text)}<small>${esc(sourceName(e.source))}</small></div><span class="event-time">${stamp(e.time)}</span></div>`,
    )
    .join("");
}
function renderTarget() {
  const u = state.units.find((u) => u.id === state.selected);
  const h = state.units.find((u) => u.id === "hero");
  if (!u || !h) return;
  const distance = Math.round(Math.hypot(u.x - h.x, u.y - h.y));
  $("target-team").textContent = {
    enemy: "ПРОТИВНИК",
    ally: "СОЮЗНИК",
    neutral: "НЕЙТРАЛ",
  }[u.team];
  $("target-detail").innerHTML =
    `<div class="target-title"><span>${esc(u.name)}</span><span>${fmt(u.hp)} / ${fmt(u.max_hp)}</span></div><div class="target-health-track"><div class="target-health" style="width:${(100 * u.hp) / u.max_hp}%;background:${u.team === "enemy" ? "var(--red)" : u.team === "ally" ? "var(--blue)" : "var(--orange)"}"></div></div><div class="target-info"><span>${u.alive ? "Дистанция от героя" : "Возрождение через несколько секунд"}</span><span>${u.alive ? distance + " ед." : ""}</span></div>`;
  const sig =
    state.selected +
    state.units
      .filter((u) => u.team !== "ally")
      .map((u) => u.alive)
      .join("");
  if ($("target-options").dataset.sig !== sig) {
    $("target-options").dataset.sig = sig;
    $("target-options").innerHTML = state.units
      .filter((u) => u.team === "enemy" || u.id === "creep-1")
      .map(
        (u) =>
          `<button class="target-option ${u.id === state.selected ? "selected" : ""}" data-target="${u.id}" aria-pressed="${u.id === state.selected}">${esc(u.name)}</button>`,
      )
      .join("");
  }
}
function renderLogs() {
  if (currentPage !== "logs") return;
  const records = state.history
    .slice()
    .reverse()
    .filter(
      (c) =>
        logFilter === "all" ||
        (logFilter === "rejected"
          ? ["rejected", "expired"].includes(c.status)
          : c.status === logFilter),
    );
  const sig = logFilter + JSON.stringify(records.map((c) => [c.id, c.status]));
  if (sig === logSignature) return;
  logSignature = sig;
  $("log-total").textContent = `${records.length} записей`;
  $("log-empty").hidden = records.length > 0;
  $("log-body").innerHTML = records
    .map(
      (c) =>
        `<tr><td>#${String(c.id).padStart(3, "0")}<small>${stamp(c.finished || c.created, true)}</small></td><td>${esc(sourceName(c.source))}<small>${esc(unitName(c.actor))}</small></td><td>${esc(labelCommand(c))}<small>${c.target ? esc(unitName(c.target)) : c.point ? `${Math.round(c.point.x)}, ${Math.round(c.point.y)}` : "—"}</small></td><td><span class="priority-chip">P${c.priority}</span></td><td><span class="log-status ${c.status}">${{ executed: "Исполнено", cancelled: "Отменено", rejected: "Отклонено", expired: "Истёк срок" }[c.status]}</span><small>${esc(c.reason)}</small></td></tr>`,
    )
    .join("");
}
function render() {
  if (!state) return;
  $("clock").textContent = stamp(state.time, true);
  $("metric-executed").textContent = state.metrics.executed;
  $("metric-cancelled").textContent = state.metrics.cancelled;
  $("metric-rejected").textContent =
    state.metrics.rejected + state.metrics.expired;
  $("metric-pending").textContent = state.metrics.pending;
  $("gold-value").textContent = state.gold;
  $("kills-value").textContent = state.kills;
  $("owner-value").textContent = {
    idle: "Ожидание",
    farm: "Фарм-модуль",
    combo: "Комбо-модуль",
    manual: "Игрок",
  }[state.hero_owner];
  $("owner-value").style.color =
    state.hero_owner === "manual"
      ? "#dfbd83"
      : state.hero_owner === "combo"
        ? "#c6b5e2"
        : "var(--text)";
  $("owner-detail").textContent = {
    idle: "Нажми Q, чтобы запустить комбо",
    farm: "P10 · уступает более важным задачам",
    combo: "P60 · герой зарезервирован",
    manual: `P100 · ещё ${state.manual_remaining.toFixed(1)} с`,
  }[state.hero_owner];
  $("pause-button").innerHTML = icon(state.paused ? "play" : "pause");
  $("pause-button").title = state.paused ? "Продолжить" : "Пауза";
  $("pause-button").setAttribute(
    "aria-label",
    state.paused ? "Продолжить" : "Пауза",
  );
  $("speed-button").textContent = state.speed + "×";
  $("arena-status").textContent = state.paused
    ? "ПАУЗА"
    : state.manual_remaining > 0
      ? "УПРАВЛЯЕТ ИГРОК"
      : "СИМУЛЯЦИЯ АКТИВНА";
  $("manual-overlay").hidden = state.manual_remaining <= 0;
  $("manual-countdown").textContent = state.manual_remaining.toFixed(1) + " с";
  const hero = state.units.find((u) => u.id === "hero");
  if (hero) {
    $("hero-hp-bar").style.width = (100 * hero.hp) / hero.max_hp + "%";
    $("hero-mana-bar").style.width = (100 * hero.mana) / hero.max_mana + "%";
    $("hero-hp").textContent = fmt(hero.hp) + " / " + fmt(hero.max_hp);
    $("hero-mana").textContent = fmt(hero.mana) + " / " + fmt(hero.max_mana);
  }
  $("item-cooldown").textContent =
    state.item.remaining > 0 ? Math.ceil(state.item.remaining) : "";
  $("restore-slot").classList.toggle("on-cooldown", state.item.remaining > 0);
  if (!$("ability-slots").children.length) {
    $("ability-slots").innerHTML = state.skills
      .map(
        (s, i) =>
          `<div class="ability-slot ${s.key}" id="skill-${s.key}" title="${esc(s.title)} · ${s.mana} маны · ${s.damage} урона · ${s.cooldown} с перезарядки">${icon({ tornado: "wind", emp: "bolt", meteor: "flame", blast: "waves" }[s.key])}<span class="ability-index">${i + 1}</span><span class="cooldown-label"></span></div>`,
      )
      .join("");
  }
  state.skills.forEach((s) => {
    const el = $("skill-" + s.key);
    el.classList.toggle("on-cooldown", s.remaining > 0);
    el.querySelector(".cooldown-label").textContent =
      s.remaining > 0 ? Math.ceil(s.remaining) : "";
  });
  const combo = state.modules.find((m) => m.key === "combo");
  $("combo-button").disabled =
    !combo.enabled ||
    state.manual_remaining > 0 ||
    state.skills.some((s) => s.remaining > 0) ||
    state.hero_owner === "combo";
  $("combo-button").title = !combo.enabled
    ? "Включи модуль «Комбо»"
    : state.skills.some((s) => s.remaining > 0)
      ? "Способности перезаряжаются"
      : "Запустить четыре шага по выбранной цели";
  renderModules();
  renderQueue();
  renderTarget();
  renderEvents();
  renderLogs();
  const scenario = state.scenario;
  $("scenario-banner").hidden = !scenario;
  if (scenario) {
    $("scenario-title").textContent = scenario.title;
    $("scenario-result").textContent =
      scenario.result || "Проверка идёт автоматически…";
    $("scenario-state").textContent = {
      running: "ПРОВЕРКА",
      passed: "ПРОЙДЕНО",
      failed: "НЕ ПРОЙДЕНО",
    }[scenario.status];
    $("scenario-state").style.color =
      scenario.status === "failed" ? "var(--red)" : "";
  }
}
const scenarios = [
  {
    key: "priority",
    title: "Комбо против фарма",
    duration: "4 СЕКУНДЫ",
    desc: "Фарм ведёт героя к лагерю. Комбо забирает управление и выполняет четыре шага, после чего фарм продолжает работу.",
    expected: "Ни одного приказа фарма во время комбо.",
    color: "#c3b2e0",
    art: "priority",
  },
  {
    key: "survival",
    title: "Экстренное восстановление",
    duration: "1.5 СЕКУНДЫ",
    desc: "Здоровье героя падает до 28%. Автопредмет замечает пересечение порога и восстанавливает 420 HP.",
    expected: "Предмет срабатывает один раз и уходит на перезарядку.",
    color: "#bde197",
    art: "survival",
  },
  {
    key: "manual",
    title: "Игрок важнее автоматики",
    duration: "2.5 СЕКУНДЫ",
    desc: "Посреди комбо игрок перехватывает управление. Оставшиеся шаги отменяются, все автоматические модули ждут.",
    expected: "Очередь отменена. Четыре секунды ручного контроля.",
    color: "#d9bd89",
    art: "manual",
  },
  {
    key: "micro",
    title: "Два юнита, две задачи",
    duration: "3 СЕКУНДЫ",
    desc: "Одна Искра получает критический урон и отступает. Вторая независимо продолжает сближение с противником.",
    expected: "Разные приказы двум юнитам в одном тике.",
    color: "#93c9da",
    art: "micro",
  },
];
function scenarioArt(s, index) {
  let shapes = "";
  const c = s.color;
  if (s.key === "priority")
    shapes = `<path d="M40 105H155" stroke="#597746" stroke-dasharray="4 6"/><path d="M190 75h180" stroke="${c}" stroke-opacity=".5"/>${[190, 250, 310, 370].map((x, i) => `<circle cx="${x}" cy="75" r="18" fill="#242334" stroke="${c}" stroke-opacity=".6"/><text x="${x}" y="79" text-anchor="middle" fill="${c}" font-size="11" font-family="monospace">0${i + 1}</text>`).join("")}<path d="m146 102 15-14m-15 0 15 14" stroke="#738465"/><path d="M65 104V75H164" stroke="#597746" fill="none"/>`;
  else if (s.key === "survival")
    shapes = `<path d="M40 87h85l15-23 16 43 22-70 22 101 20-51h150" fill="none" stroke="${c}" stroke-width="2"/><rect x="280" y="48" width="100" height="51" rx="7" fill="#1d2b1c" stroke="#4e6c3d"/><text x="330" y="79" text-anchor="middle" fill="${c}" font-size="23" font-family="monospace">+420</text>`;
  else if (s.key === "manual")
    shapes = `<path d="M50 79h330" stroke="#79745b" stroke-dasharray="5 7"/><circle cx="116" cy="79" r="20" fill="#303329" stroke="#657258"/><path d="m106 78 7 7 13-14" fill="none" stroke="#b8d889"/><circle cx="212" cy="79" r="29" fill="#342e21" stroke="${c}"/><path d="M204 89V66m15 0v23" stroke="${c}" stroke-width="3"/>${[310, 365].map((x) => `<circle cx="${x}" cy="79" r="16" fill="#22251e" stroke="#515141"/><path d="m${x - 5} 74 10 10m-10 0 10-10" stroke="#75765e"/>`).join("")}`;
  else
    shapes = `<circle cx="210" cy="77" r="30" fill="#1b3033" stroke="#50767f"/><path d="M210 47V23m-4 7 4-7 4 7M182 91l-55 30m10-1-10 1 4-10M238 91l67 25m-5-8 5 8-11 1" stroke="${c}" fill="none"/><path d="m210 64 13 13-13 13-13-13Z" fill="#629398"/>${[
      [99, 124],
      [331, 124],
    ]
      .map(
        ([x, y], i) =>
          `<path d="m${x} ${y - 13} 13 13-13 13-13-13Z" fill="${i ? "#365f5f" : "#55452e"}" stroke="${i ? c : "#c6a067"}"/>`,
      )
      .join("")}`;
  return `<svg viewBox="0 0 450 155" fill="none" aria-hidden="true"><defs><pattern id="grid-${index}" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" stroke="#6e8b6b" stroke-opacity=".055"/></pattern></defs><rect width="450" height="155" fill="url(#grid-${index})"/>${shapes}</svg>`;
}
function initialiseScenarios() {
  $("scenario-cards").innerHTML = scenarios
    .map(
      (s, i) =>
        `<article class="scenario-card"><div class="scenario-art">${scenarioArt(s, i)}<span class="scenario-number">TEST / 0${i + 1}</span><span class="scenario-duration">${s.duration}</span></div><div class="scenario-card-body"><h2>${s.title}</h2><p>${s.desc}</p><div class="scenario-expected">${icon("check")}<span>${s.expected}</span></div><button class="button secondary" data-scenario="${s.key}">${icon("play")}Запустить проверку</button></div></article>`,
    )
    .join("");
}
// Canvas is just a view. Positions, damage, cooldowns and command results come from Python.
const canvas = $("arena"),
  ctx = canvas.getContext("2d"),
  terrain = document.createElement("canvas");
terrain.width = 1000;
terrain.height = 600;
function makeTerrain() {
  const c = terrain.getContext("2d");
  const grad = c.createLinearGradient(0, 600, 1000, 0);
  grad.addColorStop(0, "#182a24");
  grad.addColorStop(0.5, "#1c2a28");
  grad.addColorStop(1, "#26302c");
  c.fillStyle = grad;
  c.fillRect(0, 0, 1000, 600);
  let seed = 423;
  function rnd() {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  }
  for (let i = 0; i < 1200; i++) {
    c.fillStyle = `rgba(153,177,137,${0.012 + rnd() * 0.03})`;
    c.fillRect(rnd() * 1000, rnd() * 600, 1 + rnd() * 5, 1 + rnd() * 3);
  }
  c.strokeStyle = "#58756415";
  c.lineWidth = 0.6;
  for (let x = 0; x <= 1000; x += 50) {
    c.beginPath();
    c.moveTo(x, 0);
    c.lineTo(x, 600);
    c.stroke();
  }
  for (let y = 0; y <= 600; y += 50) {
    c.beginPath();
    c.moveTo(0, y);
    c.lineTo(1000, y);
    c.stroke();
  }
  function river() {
    c.beginPath();
    c.moveTo(330, -40);
    c.bezierCurveTo(235, 115, 425, 136, 475, 235);
    c.bezierCurveTo(515, 316, 639, 282, 649, 408);
    c.bezierCurveTo(653, 490, 788, 520, 737, 640);
  }
  c.lineCap = "round";
  river();
  c.lineWidth = 101;
  c.strokeStyle = "#3e4a3990";
  c.stroke();
  river();
  c.lineWidth = 82;
  c.strokeStyle = "#1c353b";
  c.stroke();
  river();
  c.lineWidth = 55;
  c.strokeStyle = "#1b3036";
  c.stroke();
  river();
  c.lineWidth = 1;
  c.strokeStyle = "#67989722";
  c.stroke();
  for (let i = 0; i < 70; i++) {
    const y = rnd() * 600,
      x = 300 + y * 0.7 + (rnd() - 0.5) * 30;
    c.strokeStyle = "#638a8614";
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(x, y);
    c.lineTo(x + 12 + rnd() * 14, y - 3);
    c.stroke();
  }
  c.beginPath();
  c.moveTo(-20, 545);
  c.bezierCurveTo(200, 505, 190, 379, 344, 373);
  c.bezierCurveTo(465, 370, 578, 251, 680, 194);
  c.bezierCurveTo(795, 125, 887, 130, 1030, 37);
  c.lineWidth = 45;
  c.strokeStyle = "#1a2522";
  c.stroke();
  c.lineWidth = 33;
  c.strokeStyle = "#414840";
  c.stroke();
  c.lineWidth = 29;
  c.strokeStyle = "#37403a";
  c.stroke();
  c.lineWidth = 1;
  c.strokeStyle = "#84917a33";
  c.setLineDash([4, 15]);
  c.stroke();
  c.setLineDash([]);
  c.strokeStyle = "#455141";
  c.lineWidth = 18;
  c.beginPath();
  c.moveTo(345, 373);
  c.lineTo(440, 461);
  c.lineTo(495, 512);
  c.stroke();
  c.strokeStyle = "#2f3d31";
  c.lineWidth = 14;
  c.stroke();
  c.save();
  c.translate(504, 299);
  c.rotate(-0.73);
  c.fillStyle = "#27312e";
  c.strokeStyle = "#78826c66";
  c.lineWidth = 1.5;
  c.fillRect(-55, -34, 110, 68);
  c.strokeRect(-55, -34, 110, 68);
  for (let i = -48; i < 55; i += 13) {
    c.fillStyle = i % 2 ? "#465047" : "#40483f";
    c.fillRect(i, -30, 10, 60);
    c.strokeStyle = "#6b745933";
    c.strokeRect(i, -30, 10, 60);
  }
  c.fillStyle = "#69765b";
  c.fillRect(-60, -38, 120, 5);
  c.fillRect(-60, 33, 120, 5);
  c.restore();
  function pad(x, y, r, color) {
    c.strokeStyle = color;
    c.lineWidth = 1.1;
    c.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (i * Math.PI) / 3;
      const px = x + Math.cos(a) * r,
        py = y + Math.sin(a) * r * 0.67;
      i ? c.lineTo(px, py) : c.moveTo(px, py);
    }
    c.closePath();
    c.fillStyle = "#202c2788";
    c.fill();
    c.stroke();
    c.beginPath();
    c.ellipse(x, y, r * 0.6, r * 0.4, 0, 0, Math.PI * 2);
    c.stroke();
  }
  pad(260, 350, 58, "#80925e44");
  pad(645, 230, 67, "#9c766a35");
  pad(455, 450, 62, "#9a896530");
  const clusters = [
    [75, 100, 65, 17],
    [180, 130, 60, 15],
    [63, 340, 65, 18],
    [165, 530, 40, 10],
    [342, 540, 48, 12],
    [630, 70, 58, 16],
    [797, 490, 70, 19],
    [910, 390, 50, 15],
    [901, 112, 46, 12],
    [551, 95, 28, 8],
    [922, 570, 70, 14],
  ];
  const trees = [];
  clusters.forEach(([x, y, r, n]) => {
    for (let i = 0; i < n; i++) {
      const a = rnd() * Math.PI * 2,
        rr = Math.sqrt(rnd()) * r;
      trees.push({
        x: x + Math.cos(a) * rr,
        y: y + Math.sin(a) * rr,
        r: 9 + rnd() * 13,
        h: rnd(),
      });
    }
  });
  trees.sort((a, b) => a.y - b.y);
  trees.forEach((t) => {
    const { x, y, r } = t;
    c.fillStyle = "#09121060";
    c.beginPath();
    c.ellipse(x + 5, y + 9, r * 1.15, r * 0.65, 0, 0, Math.PI * 2);
    c.fill();
    c.fillStyle = "#283d2c";
    c.beginPath();
    c.moveTo(x, y - r * 1.5);
    c.lineTo(x - r * 0.8, y + r * 0.25);
    c.lineTo(x + r * 0.8, y + r * 0.25);
    c.closePath();
    c.fill();
    c.fillStyle = t.h > 0.5 ? "#3d5136" : "#354b34";
    c.beginPath();
    c.moveTo(x - 1, y - r * 1.7);
    c.lineTo(x - r * 0.7, y - r * 0.05);
    c.lineTo(x + r * 0.65, y - r * 0.05);
    c.closePath();
    c.fill();
    c.fillStyle = "#587047";
    c.beginPath();
    c.moveTo(x - 1, y - r * 1.7);
    c.lineTo(x - r * 0.7, y - r * 0.05);
    c.lineTo(x, y - r * 0.3);
    c.closePath();
    c.globalAlpha = 0.3;
    c.fill();
    c.globalAlpha = 1;
  });
  const rocks = [
    [590, 395],
    [613, 437],
    [376, 231],
    [369, 211],
    [470, 538],
    [779, 251],
    [87, 226],
    [856, 291],
  ];
  rocks.forEach(([x, y]) => {
    c.fillStyle = "#0c191344";
    c.beginPath();
    c.ellipse(x + 6, y + 7, 16, 10, 0, 0, Math.PI * 2);
    c.fill();
    c.fillStyle = "#3c4b40";
    c.strokeStyle = "#74836c44";
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(x - 12, y + 4);
    c.lineTo(x - 7, y - 10);
    c.lineTo(x + 7, y - 13);
    c.lineTo(x + 15, y);
    c.lineTo(x + 6, y + 8);
    c.closePath();
    c.fill();
    c.stroke();
  });
  c.font = "8px monospace";
  c.fillStyle = "#8b9c735b";
  c.fillText("БАЗА / 01", 145, 465);
  c.fillStyle = "#afa3815b";
  c.fillText("ЛАГЕРЬ / 02", 420, 561);
  c.fillStyle = "#b19d8b5b";
  c.fillText("ПОЛИГОН / 03", 699, 180);
  c.strokeStyle = "#b8c2a129";
  c.lineWidth = 1;
  [
    [18, 18, 1, 1],
    [982, 18, -1, 1],
    [18, 582, 1, -1],
    [982, 582, -1, -1],
  ].forEach(([x, y, dx, dy]) => {
    c.beginPath();
    c.moveTo(x + 23 * dx, y);
    c.lineTo(x, y);
    c.lineTo(x, y + 23 * dy);
    c.stroke();
  });
  const vignette = c.createRadialGradient(500, 300, 120, 500, 300, 620);
  vignette.addColorStop(0, "#080e1000");
  vignette.addColorStop(1, "#080e1088");
  c.fillStyle = vignette;
  c.fillRect(0, 0, 1000, 600);
}
makeTerrain();
function resizeCanvas() {
  const r = canvas.getBoundingClientRect();
  if (!r.width || !r.height) return;
  const d = Math.min(window.devicePixelRatio || 1, 2);
  if (
    canvas.width !== Math.round(r.width * d) ||
    canvas.height !== Math.round(r.height * d)
  ) {
    canvas.width = Math.round(r.width * d);
    canvas.height = Math.round(r.height * d);
  }
  ctx.setTransform(canvas.width / 1000, 0, 0, canvas.height / 600, 0, 0);
}
let lastFrame = performance.now();
function draw(now) {
  requestAnimationFrame(draw);
  if (currentPage !== "overview") return;
  resizeCanvas();
  ctx.clearRect(0, 0, 1000, 600);
  ctx.drawImage(terrain, 0, 0);
  if (!state) return;
  const elapsed = Math.min(0.05, (now - lastFrame) / 1000);
  lastFrame = now;
  const t =
    state.time +
    (state.paused
      ? 0
      : Math.min(0.2, (now - lastReceived) / 1000) * state.speed);
  const units = state.units;
  units.forEach((u) => {
    let p = positions.get(u.id);
    if (!p) {
      p = { x: u.x, y: u.y };
      positions.set(u.id, p);
    }
    const k = 1 - Math.exp(-elapsed * 18);
    p.x += (u.x - p.x) * k;
    p.y += (u.y - p.y) * k;
  });
  const hero = units.find((u) => u.id === "hero");
  const target = units.find((u) => u.id === state.selected);
  const hp = positions.get("hero");
  if (hero && hp) {
    ctx.save();
    ctx.strokeStyle = state.hero_owner === "manual" ? "#dbb98139" : "#a9c87514";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 10]);
    ctx.beginPath();
    ctx.arc(hp.x, hp.y, 110, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
    if (target?.alive && target.id !== "hero") {
      const tp = positions.get(target.id);
      ctx.save();
      ctx.strokeStyle =
        state.hero_owner === "combo" ? "#c2a6e18a" : "#aeb39b30";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 8]);
      ctx.lineDashOffset = -t * 8;
      ctx.beginPath();
      ctx.moveTo(hp.x, hp.y);
      ctx.lineTo(tp.x, tp.y);
      ctx.stroke();
      ctx.restore();
    }
  }
  for (const u of units) {
    const p = positions.get(u.id),
      selected = u.id === state.selected;
    const color =
      u.id === "hero"
        ? "#c1f383"
        : u.team === "ally"
          ? "#81bbcf"
          : u.team === "enemy"
            ? "#d99789"
            : "#c5aa72";
    const r = u.role === "hero" ? 17 : u.role === "summon" ? 11 : 10;
    ctx.save();
    ctx.globalAlpha = u.alive ? 1 : 0.25;
    ctx.fillStyle = "#050c0a99";
    ctx.beginPath();
    ctx.ellipse(p.x + 2, p.y + 9, r + 6, r * 0.55, 0, 0, Math.PI * 2);
    ctx.fill();
    if (selected) {
      ctx.strokeStyle = color + "bb";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let a = 0; a < 4; a++) {
        const start = (a * Math.PI) / 2 + t * 0.25;
        ctx.arc(p.x, p.y, r + 12, start, start + 0.55);
      }
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(p.x, p.y - r - 30);
      ctx.lineTo(p.x - 4, p.y - r - 37);
      ctx.lineTo(p.x + 4, p.y - r - 37);
      ctx.closePath();
      ctx.fill();
    }
    if (u.id === "hero") {
      const glow = ctx.createRadialGradient(p.x, p.y, 4, p.x, p.y, 42);
      glow.addColorStop(0, "#c2ef791b");
      glow.addColorStop(1, "#c2ef7900");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 42, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = color + "aa";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r + 4, 0, Math.PI * 2);
      ctx.stroke();
    }
    const orb = ctx.createRadialGradient(p.x - 5, p.y - 7, 1, p.x, p.y, r);
    orb.addColorStop(
      0,
      u.id === "hero"
        ? "#50663b"
        : u.team === "enemy"
          ? "#744e48"
          : u.team === "ally"
            ? "#355663"
            : "#5b5139",
    );
    orb.addColorStop(1, "#182220");
    ctx.fillStyle = orb;
    ctx.strokeStyle = color + "d0";
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    if (u.role === "summon") {
      ctx.moveTo(p.x, p.y - r);
      ctx.lineTo(p.x + r, p.y);
      ctx.lineTo(p.x, p.y + r);
      ctx.lineTo(p.x - r, p.y);
      ctx.closePath();
    } else ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.1;
    if (u.id === "hero") {
      ctx.beginPath();
      ctx.moveTo(p.x, p.y - 9);
      ctx.lineTo(p.x + 7, p.y + 7);
      ctx.lineTo(p.x, p.y + 3);
      ctx.lineTo(p.x - 7, p.y + 7);
      ctx.closePath();
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(p.x - 3, p.y);
      ctx.lineTo(p.x + 3, p.y);
      ctx.stroke();
    } else if (u.team === "enemy") {
      ctx.beginPath();
      ctx.moveTo(p.x - 6, p.y - 5);
      ctx.lineTo(p.x, p.y - 8);
      ctx.lineTo(p.x + 6, p.y - 5);
      ctx.lineTo(p.x + 4, p.y + 5);
      ctx.lineTo(p.x, p.y + 8);
      ctx.lineTo(p.x - 4, p.y + 5);
      ctx.closePath();
      ctx.stroke();
      ctx.fillRect(p.x - 3, p.y - 2, 6, 1);
    } else {
      ctx.beginPath();
      ctx.arc(p.x, p.y, u.role === "summon" ? 3 : 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
    const bw = u.role === "hero" ? 49 : 32;
    ctx.fillStyle = "#090f0e";
    ctx.fillRect(p.x - bw / 2 - 1, p.y - r - 13, bw + 2, 5);
    ctx.fillStyle = color + "bb";
    ctx.fillRect(p.x - bw / 2, p.y - r - 12, (bw * u.hp) / u.max_hp, 3);
    if (u.role === "hero" || selected) {
      ctx.font = `${u.id === "hero" ? "600 " : ""}10px -apple-system, sans-serif`;
      ctx.textAlign = "center";
      ctx.fillStyle = u.id === "hero" ? "#d2e4bc" : "#b0b6a4";
      ctx.shadowColor = "#07120d";
      ctx.shadowBlur = 4;
      ctx.fillText(u.name, p.x, p.y + r + 19);
      ctx.shadowBlur = 0;
    }
    ctx.restore();
  }
  for (const effect of state.effects) {
    const age = t - effect.time;
    if (age < 0 || age > 1.6) continue;
    const colors = {
      tornado: "#bbdceb",
      emp: "#c3a0ec",
      meteor: "#e6ad6f",
      blast: "#92d6bb",
      heal: "#c6f286",
      attack: "#b4c8a8",
      damage: "#e2a080",
      spawn: "#96ba7b",
    };
    const color = colors[effect.kind] || "#b6da93";
    const a = effect.from,
      b = effect.to;
    ctx.save();
    ctx.globalAlpha = Math.max(0, 1 - age / 1.6);
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    if (["tornado", "emp", "meteor", "blast", "attack"].includes(effect.kind)) {
      const progress = Math.min(1, age / 0.22);
      ctx.lineWidth = effect.kind === "attack" ? 1 : 2;
      ctx.globalAlpha *= 0.65;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(a.x + (b.x - a.x) * progress, a.y + (b.y - a.y) * progress);
      ctx.stroke();
      ctx.globalAlpha = Math.max(0, 1 - age / 1.2);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(
        b.x,
        b.y,
        10 + age * (effect.kind === "emp" ? 58 : 30),
        0,
        Math.PI * 2,
      );
      ctx.stroke();
      if (effect.kind === "meteor") {
        ctx.fillStyle = "#e6ad6f22";
        ctx.beginPath();
        ctx.arc(b.x, b.y, 22 + age * 20, 0, Math.PI * 2);
        ctx.fill();
      }
    } else {
      ctx.lineWidth = 1.7;
      ctx.beginPath();
      ctx.arc(b.x, b.y, 17 + age * 28, 0, Math.PI * 2);
      ctx.stroke();
      if (effect.kind === "heal") {
        for (let i = 0; i < 5; i++) {
          const ang = i * 1.26;
          const x = b.x + Math.cos(ang) * (15 + age * 14),
            y = b.y + Math.sin(ang) * (15 + age * 14) - age * 15;
          ctx.fillRect(x - 3, y, 6, 1);
          ctx.fillRect(x, y - 3, 1, 6);
        }
      }
    }
    if (effect.text) {
      ctx.globalAlpha = Math.max(0, 1 - age / 1.6);
      ctx.font = "600 13px monospace";
      ctx.textAlign = "center";
      ctx.shadowColor = "#050b08";
      ctx.shadowBlur = 6;
      ctx.fillStyle = color;
      ctx.fillText(effect.text, b.x, b.y - 35 - age * 20);
    }
    ctx.restore();
  }
  ctx.save();
  ctx.translate(957, 548);
  ctx.strokeStyle = "#71887966";
  ctx.fillStyle = "#8e9e88";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(0, 0, 14, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(0, -9);
  ctx.lineTo(-4, 5);
  ctx.lineTo(0, 2);
  ctx.lineTo(4, 5);
  ctx.closePath();
  ctx.stroke();
  ctx.font = "6px monospace";
  ctx.textAlign = "center";
  ctx.fillText("N", 0, -21);
  ctx.restore();
}
function worldPoint(e) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((e.clientX - rect.left) / rect.width) * 1000,
    y: ((e.clientY - rect.top) / rect.height) * 600,
  };
}
canvas.addEventListener("click", (e) => {
  if (!state) return;
  const p = worldPoint(e);
  const hit = state.units
    .map((u) => ({ u, d: Math.hypot(u.x - p.x, u.y - p.y) }))
    .sort((a, b) => a.d - b.d)[0];
  if (hit && hit.d < 45) command("select", { target: hit.u.id });
});
canvas.addEventListener("contextmenu", (e) => {
  e.preventDefault();
  if (!state) return;
  const p = worldPoint(e);
  command("move", {
    x: Math.max(20, Math.min(980, p.x)),
    y: Math.max(20, Math.min(580, p.y)),
  });
});
document.addEventListener("click", async (e) => {
  const toggle = e.target.closest("[data-toggle-module]");
  if (toggle && state) {
    const m = state.modules.find((m) => m.key === toggle.dataset.toggleModule);
    if (m) await command("module", { key: m.key, enabled: !m.enabled });
  }
  const target = e.target.closest("[data-target]");
  if (target) command("select", { target: target.dataset.target });
  const scenario = e.target.closest("[data-scenario]");
  if (scenario) {
    const ok = await command("scenario", { key: scenario.dataset.scenario });
    if (ok) location.hash = "overview";
  }
  const filter = e.target.closest("[data-filter]");
  if (filter) {
    logFilter = filter.dataset.filter;
    document
      .querySelectorAll("[data-filter]")
      .forEach((b) => b.classList.toggle("active", b === filter));
    logSignature = "";
    if (state) renderLogs();
  }
});
$("combo-button").addEventListener("click", () => command("combo"));
$("damage-button").addEventListener("click", () => command("damage"));
$("manual-button").addEventListener("click", () =>
  command("manual", {}, "Автоматика остановлена на 4 секунды"),
);
$("pause-button").addEventListener("click", () => command("pause"));
$("speed-button").addEventListener("click", () => {
  if (state)
    command("speed", {
      value: state.speed === 1 ? 2 : state.speed === 2 ? 0.5 : 1,
    });
});
$("reset-button").addEventListener("click", () =>
  $("reset-dialog").showModal(),
);
$("reset-dialog").addEventListener("close", () => {
  if ($("reset-dialog").returnValue === "reset")
    command("reset", {}, "Полигон сброшен");
  $("reset-dialog").returnValue = "cancel";
});
function exportConfig() {
  if (state) {
    download("hexa-lab-config.json", state.config);
    toast("Конфигурация экспортирована");
  }
}
$("export-config").addEventListener("click", exportConfig);
$("export-config-main").addEventListener("click", exportConfig);
$("import-config").addEventListener("click", () => $("config-file").click());
$("config-file").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    if (file.size > 32700) throw new Error("Слишком большой файл конфигурации");
    const data = JSON.parse(await file.text());
    await command("import", { config: data }, "Конфигурация импортирована");
  } catch (err) {
    toast(err.message, true);
  }
  e.target.value = "";
});
$("export-log").addEventListener("click", async () => {
  try {
    const r = await fetch("/api/export");
    if (!r.ok) throw new Error("Экспорт недоступен");
    download("hexa-lab-session.json", await r.json());
    toast("Состояние и журнал экспортированы");
  } catch (e) {
    toast(e.message, true);
  }
});
$("clear-log").addEventListener("click", () =>
  command("clear_log", {}, "Журнал очищен; активная очередь сохранена"),
);
document.addEventListener("keydown", (e) => {
  if (
    e.repeat ||
    e.ctrlKey ||
    e.metaKey ||
    e.altKey ||
    e.target.closest('input,textarea,select,[contenteditable="true"]') ||
    $("reset-dialog").open
  )
    return;
  if (e.code === "KeyQ") {
    e.preventDefault();
    command("combo");
  }
  if (e.code === "KeyH") {
    e.preventDefault();
    command("damage");
  }
  if (e.code === "Space") {
    e.preventDefault();
    command("manual");
  }
});
window.addEventListener("hashchange", route);
fillIcons();
initialiseModules();
initialiseScenarios();
route();
poll();
requestAnimationFrame(draw);
