(function () {
  "use strict";

  const POLL_MS = 5000;
  const NAV = [
    ["overview", "Overview"],
    ["agents", "Agents"],
    ["plan", "Plan & workstreams"],
    ["decisions", "Decisions"],
    ["capabilities", "Capabilities"],
    ["validators", "Validators"],
    ["alerts", "Alerts"],
    ["history", "History"],
    ["logs", "Logs"],
  ];
  const PREF_THEME = "dispatch-engine.dashboard.theme";
  const PREF_ZOOM = "dispatch-engine.dashboard.zoom";
  const PREF_TAIL_HEIGHT = "dispatch-engine.dashboard.tailHeight";
  const DEFAULT_THEME = "carbon";
  const DEFAULT_ZOOM = 0.9;
  const DEFAULT_TAIL_HEIGHT = 210;
  const THEMES = [
    { id: "default", name: "Mission cyan", desc: "cool dark", swatch: ["#080b10", "#6fd2e8"] },
    { id: "solar", name: "Solar", desc: "paper light", swatch: ["#fbf7ee", "#b15c2b"] },
    { id: "carbon", name: "Carbon", desc: "neutral + amber", swatch: ["#131315", "#e7c479"] },
    { id: "indigo", name: "Indigo", desc: "midnight violet", swatch: ["#11142a", "#8c7cff"] },
    { id: "forest", name: "Forest", desc: "muted green", swatch: ["#121817", "#84d2a8"] },
    { id: "crimson", name: "Crimson", desc: "high stakes", swatch: ["#15110f", "#ff7066"] },
  ];
  const THEME_OPTIONS = THEMES.slice().sort((a, b) => a.name.localeCompare(b.name));
  const ZOOMS = [0.7, 0.8, 0.9, 1];
  const SCENARIO_IDS = [
    "empty",
    "starting",
    "running",
    "waiting-input",
    "violation-flash",
    "disconnected",
    "coordinator-dead",
    "completed",
    "cancelled",
    "failed",
  ];
  const TERMINAL_STATUSES = ["completed", "completed_with_concerns", "cancelled", "failed"];
  const STALE_POLL_LIMIT = 2;
  const SHORTCUTS = [
    ["?", "Open keyboard help"],
    ["esc", "Close modal or settings"],
    ["x", "Open cancel preview"],
    ["c", "Open coordinator tail"],
    ["s", "Open status JSON"],
    ["g o", "Overview"],
    ["g a", "Agents"],
    ["g p", "Plan & workstreams"],
    ["g d", "Decisions"],
    ["g c", "Capabilities"],
    ["g v", "Validators"],
    ["g h", "History"],
    ["g l", "Logs"],
    ["/", "Focus screen search when available"],
    ["t", "Cycle theme"],
    ["+ / -", "Step density"],
  ];

  const state = {
    screen: "overview",
    loading: true,
    refreshing: false,
    error: null,
    apiErrors: {},
    failedPolls: 0,
    lastSuccessfulAt: null,
    updatedAt: null,
    modal: null,
    modalContext: null,
    modalForm: {},
    lastModalFocus: null,
    settingsOpen: false,
    runSwitcherOpen: false,
    selectedAgentId: null,
    agentLoading: false,
    agentError: null,
    planSearch: "",
    historySearch: "",
    tailFilter: "all",
    tailCollapsed: false,
    tailHeight: loadTailHeight(),
    selectedCompareRunIds: [],
    selectedPlanNodeId: null,
    collapsedPlanNodes: {},
    prefs: loadPreferences(),
    fixtureScenario: fixtureScenarioFromLocation(),
    data: {
      status: null,
      events: null,
      alerts: null,
      tail: null,
      logs: null,
      history: null,
      plan: null,
      hostHeartbeat: null,
      agentDetails: {},
    },
  };

  const app = document.getElementById("app");
  let chord = null;
  let chordTimer = null;
  const scrollMemory = new Map();

  function rememberScrollPositions(root) {
    if (!root) return;
    root.querySelectorAll("[data-scroll-key]").forEach((node) => {
      const key = node.getAttribute("data-scroll-key");
      if (!key) return;
      scrollMemory.set(key, {
        left: node.scrollLeft,
        top: node.scrollTop,
      });
    });
  }

  function restoreScrollPositions(root) {
    if (!root) return;
    window.requestAnimationFrame(() => {
      root.querySelectorAll("[data-scroll-key]").forEach((node) => {
        const key = node.getAttribute("data-scroll-key");
        const position = key ? scrollMemory.get(key) : null;
        if (!position) return;
        node.scrollLeft = position.left;
        node.scrollTop = Math.min(position.top, Math.max(0, node.scrollHeight - node.clientHeight));
      });
    });
  }

  function updateLiveHeartbeatClocks(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-heartbeat-interval]").forEach((card) => {
      if (card.getAttribute("data-heartbeat-active") !== "true") return;
      const interval = count(card.getAttribute("data-heartbeat-interval")) || 900;
      const rawLastWake = card.getAttribute("data-heartbeat-last-wake");
      if (!rawLastWake) return;
      const lastWake = new Date(rawLastWake).getTime();
      if (!Number.isFinite(lastWake)) return;
      const ageSeconds = Math.max(0, Math.floor((Date.now() - lastWake) / 1000));
      const remaining = Math.max(0, interval - (ageSeconds % interval));
      const pct = Math.max(0, Math.min(100, Math.round((remaining / interval) * 100)));
      const ring = card.querySelector(".hb-ring");
      const time = card.querySelector(".hb-time");
      const age = card.querySelector(".hb-wakeup-age");
      if (ring) ring.style.setProperty("--pct", `${pct}%`);
      if (time) time.textContent = mmss(remaining);
      if (age) age.textContent = `${humanDuration(ageSeconds)} ago`;
    });
  }

  function fixtureScenarioFromLocation() {
    try {
      const params = new URLSearchParams(window.location.search);
      const value = params.get("fixture") || params.get("demo") || "";
      return SCENARIO_IDS.includes(value) ? value : null;
    } catch (error) {
      return null;
    }
  }

  function loadPreferences() {
    const fallback = { theme: DEFAULT_THEME, zoom: DEFAULT_ZOOM };
    try {
      const theme = localStorage.getItem(PREF_THEME) || fallback.theme;
      const zoom = Number(localStorage.getItem(PREF_ZOOM) || fallback.zoom);
      return {
        theme: THEMES.some((item) => item.id === theme) ? theme : fallback.theme,
        zoom: ZOOMS.some((item) => Math.abs(item - zoom) < 0.001) ? zoom : fallback.zoom,
      };
    } catch (error) {
      return fallback;
    }
  }

  function loadTailHeight() {
    try {
      const value = Number(localStorage.getItem(PREF_TAIL_HEIGHT) || DEFAULT_TAIL_HEIGHT);
      return clampTailHeight(value);
    } catch (error) {
      return DEFAULT_TAIL_HEIGHT;
    }
  }

  function saveTailHeight(height) {
    try {
      localStorage.setItem(PREF_TAIL_HEIGHT, String(Math.round(height)));
    } catch (error) {
      // Browser privacy modes can deny storage; the in-memory size still applies.
    }
  }

  function savePreference(key, value) {
    try {
      if (key === PREF_ZOOM && Math.abs(Number(value) - DEFAULT_ZOOM) < 0.001) {
        localStorage.removeItem(key);
      } else if (key === PREF_THEME && value === DEFAULT_THEME) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, String(value));
      }
    } catch (error) {
      // Browser privacy modes can deny storage; preferences still apply in memory.
    }
  }

  function clampTailHeight(height) {
    const viewport = Math.max(480, window.innerHeight || 0);
    const min = window.matchMedia && window.matchMedia("(max-width: 680px)").matches ? 140 : 120;
    const max = Math.max(min, Math.floor(viewport * 0.72));
    return Math.max(min, Math.min(max, Number(height) || DEFAULT_TAIL_HEIGHT));
  }

  function applyPreferences() {
    const root = document.documentElement;
    const body = document.body;
    if (state.prefs.theme && state.prefs.theme !== "default") {
      root.setAttribute("data-theme", state.prefs.theme);
      body.setAttribute("data-theme", state.prefs.theme);
    } else {
      root.removeAttribute("data-theme");
      body.removeAttribute("data-theme");
    }
    if (Math.abs(state.prefs.zoom - 1) < 0.001) {
      root.style.removeProperty("--ui-zoom");
      root.style.removeProperty("--ui-zoom-inv");
      body.classList.remove("ui-zoomed");
    } else {
      root.style.setProperty("--ui-zoom", String(state.prefs.zoom));
      root.style.setProperty("--ui-zoom-inv", String(1 / state.prefs.zoom));
      body.classList.add("ui-zoomed");
    }
  }

  function setTheme(theme) {
    if (!THEMES.some((item) => item.id === theme)) return;
    state.prefs.theme = theme;
    savePreference(PREF_THEME, theme);
    applyPreferences();
    render();
  }

  function setZoom(zoom) {
    if (!ZOOMS.some((item) => Math.abs(item - zoom) < 0.001)) return;
    state.prefs.zoom = zoom;
    savePreference(PREF_ZOOM, zoom);
    applyPreferences();
    render();
  }

  function stepZoom(direction) {
    const index = ZOOMS.findIndex((item) => Math.abs(item - state.prefs.zoom) < 0.001);
    const next = Math.max(0, Math.min(ZOOMS.length - 1, (index === -1 ? ZOOMS.length - 1 : index) + direction));
    setZoom(ZOOMS[next]);
  }

  function api(path) {
    return fetch(path, { headers: { Accept: "application/json" }, cache: "no-store" }).then((response) => {
      return response.text().then((body) => {
        let payload = null;
        try {
          payload = body ? JSON.parse(body) : {};
        } catch (error) {
          payload = { kind: "error", status: "invalid_json", summary: String(error), raw: body };
        }
        if (!response.ok) {
          const summary = payload && payload.summary ? payload.summary : `${response.status} ${response.statusText}`;
          throw new Error(summary);
        }
        return payload;
      });
    });
  }

  function load() {
    state.refreshing = true;
    render();
    return Promise.allSettled([
      api("/api/status"),
      api("/api/events"),
      api("/api/alerts"),
      api("/api/tail"),
      api("/api/logs/coordinator"),
      api("/api/history"),
      api("/api/plan"),
      api("/api/host-heartbeat"),
    ]).then((results) => {
      const keys = ["status", "events", "alerts", "tail", "logs", "history", "plan", "hostHeartbeat"];
      const errors = [];
      const apiErrors = {};
      results.forEach((result, index) => {
        if (result.status === "fulfilled") {
          state.data[keys[index]] = result.value;
        } else {
          errors.push(`${keys[index]}: ${result.reason.message}`);
          apiErrors[keys[index]] = result.reason.message;
        }
      });
      state.error = errors.length ? errors.join("; ") : null;
      state.apiErrors = apiErrors;
      if (errors.length) {
        state.failedPolls += 1;
      } else {
        state.failedPolls = 0;
        state.lastSuccessfulAt = new Date();
      }
      state.loading = false;
      state.refreshing = false;
      state.updatedAt = new Date();
      render();
    });
  }

  function setScreen(screen) {
    closeTransient();
    if (screen !== "agent") {
      state.selectedAgentId = null;
      state.agentError = null;
    }
    state.screen = screen;
    render();
  }

  function selectAgent(agentId) {
    closeTransient();
    state.selectedAgentId = agentId;
    state.screen = "agent";
    state.agentError = null;
    render();
    loadAgentDetail(agentId);
  }

  function loadAgentDetail(agentId) {
    if (!agentId) return Promise.resolve();
    state.agentLoading = true;
    render();
    return api(`/api/agent/${encodeURIComponent(agentId)}`).then((payload) => {
      state.data.agentDetails[agentId] = payload;
      state.agentError = null;
    }).catch((error) => {
      state.agentError = error.message;
    }).finally(() => {
      state.agentLoading = false;
      render();
    });
  }

  function openModal(modal, context) {
    state.lastModalFocus = document.activeElement && document.activeElement.focus ? document.activeElement : null;
    state.modal = modal;
    state.modalContext = context || null;
    state.modalForm = defaultModalForm(modal, context);
    state.settingsOpen = false;
    state.runSwitcherOpen = false;
    clearChord();
    render();
  }

  function closeModal() {
    const focus = state.lastModalFocus;
    state.modal = null;
    state.modalContext = null;
    state.modalForm = {};
    state.lastModalFocus = null;
    render();
    if (focus && focus.focus) {
      window.setTimeout(() => focus.focus(), 0);
    }
  }

  function closeTransient() {
    state.modal = null;
    state.modalContext = null;
    state.modalForm = {};
    state.settingsOpen = false;
    state.runSwitcherOpen = false;
    clearChord();
  }

  function defaultModalForm(modal, context) {
    if (modal === "cancel") {
      return {
        reason: "",
        includeToolCalls: true,
        keepArtifacts: true,
      };
    }
    if (modal === "decision") {
      const options = decisionOptions(context);
      return {
        option: options[0] && options[0].id ? options[0].id : "",
        auditNote: "",
      };
    }
    if (modal === "capability" || modal === "agentCapability") {
      return {
        scopeRepo: true,
        scopeAgent: true,
        scopeRuntime: false,
        ttl: "30m",
        auditNote: "",
      };
    }
    if (modal === "agentCancel") {
      return { reason: "" };
    }
    return {};
  }

  function clearChord() {
    chord = null;
    if (chordTimer) {
      window.clearTimeout(chordTimer);
      chordTimer = null;
    }
  }

  function el(tag, className, children, attrs) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (attrs) {
      Object.keys(attrs).forEach((key) => {
        if (key === "text") {
          node.textContent = attrs[key];
        } else if (key === "title") {
          node.title = attrs[key];
        } else if (key === "type") {
          node.type = attrs[key];
        } else {
          node.setAttribute(key, attrs[key]);
        }
      });
    }
    append(node, children);
    return node;
  }

  function append(parent, children) {
    if (children == null) return parent;
    const list = Array.isArray(children) ? children : [children];
    list.forEach((child) => {
      if (child == null) return;
      if (Array.isArray(child)) {
        append(parent, child);
        return;
      }
      if (typeof child === "string" || typeof child === "number") {
        parent.appendChild(document.createTextNode(String(child)));
      } else {
        parent.appendChild(child);
      }
    });
    return parent;
  }

  function svgIcon(name) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 16 16");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.5");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    const parts = {
      refresh: [["path", { d: "M13 6.5A5 5 0 1 0 11.5 11" }], ["path", { d: "M13 3v3.5H9.5" }]],
      tail: [["path", { d: "M2 4h12M2 8h8M2 12h10" }]],
      status: [["rect", { x: "2", y: "2", width: "12", height: "12", rx: "2" }], ["path", { d: "M5 6h6M5 8.5h4M5 11h5" }]],
      settings: [["circle", { cx: "8", cy: "8", r: "2.2" }], ["path", { d: "M8 1.5v1.8M8 12.7v1.8M14.5 8h-1.8M3.3 8H1.5M12.6 3.4l-1.3 1.3M4.7 11.3l-1.3 1.3M12.6 12.6l-1.3-1.3M4.7 4.7L3.4 3.4" }]],
      help: [["circle", { cx: "8", cy: "8", r: "6" }], ["path", { d: "M6.4 6.1a1.9 1.9 0 1 1 2.9 1.6c-.7.4-1.1.8-1.1 1.5" }], ["path", { d: "M8 12h.01" }]],
      cancel: [["circle", { cx: "8", cy: "8", r: "6" }], ["path", { d: "M5 5l6 6M11 5l-6 6" }]],
      back: [["path", { d: "M10 3L5 8l5 5" }]],
      capability: [["path", { d: "M8 2l5 2.5v3.8c0 2.7-1.8 4.9-5 5.7-3.2-.8-5-3-5-5.7V4.5z" }], ["path", { d: "M6 8l1.4 1.4L10.5 6" }]],
      search: [["circle", { cx: "7", cy: "7", r: "4.5" }], ["path", { d: "M10.5 10.5L14 14" }]],
      check: [["path", { d: "M3 8.5l3 3L13 4.5" }]],
    }[name] || [];
    parts.forEach(([tag, attrs]) => {
      const child = document.createElementNS(ns, tag);
      Object.keys(attrs).forEach((key) => child.setAttribute(key, attrs[key]));
      svg.appendChild(child);
    });
    return svg;
  }

  function button(className, title, text, onClick) {
    const node = el("button", className, text, { type: "button", title });
    node.addEventListener("click", onClick);
    return node;
  }

  function safe(value, fallback) {
    if (value === null || value === undefined || value === "") return fallback || "n/a";
    return String(value);
  }

  function repoPath() {
    const run = state.data.status || {};
    if (run.repo_root) return safe(run.repo_root, ".");
    const stateDir = safe(run.state_dir, "");
    const marker = "/.dispatch/runs/";
    const index = stateDir.indexOf(marker);
    if (index !== -1) return stateDir.slice(0, index);
    return ".";
  }

  function shellQuote(value) {
    const text = safe(value, "");
    if (!text) return "''";
    if (/^[A-Za-z0-9_./:=@%+,-]+$/.test(text)) return text;
    return `'${text.replace(/'/g, "'\"'\"'")}'`;
  }

  function commandBlock(command, caption) {
    return el("div", "command-block", [
      caption ? el("div", "command-caption", caption) : null,
      el("pre", "json-block command-preview", command),
    ]);
  }

  function formRow(label, control, hint) {
    return el("label", "form-row", [
      el("span", "form-label", label),
      control,
      hint ? el("span", "form-hint", hint) : null,
    ]);
  }

  function updateModalForm(key, value) {
    state.modalForm[key] = value;
    render();
  }

  function modalInput(key, attrs) {
    const input = el("input", "modal-input", null, Object.assign({ type: "text", value: state.modalForm[key] || "" }, attrs || {}));
    input.addEventListener("input", () => {
      state.modalForm[key] = input.value;
    });
    input.addEventListener("change", () => updateModalForm(key, input.value));
    return input;
  }

  function modalTextArea(key, attrs) {
    const textarea = el("textarea", "modal-textarea", null, Object.assign({ rows: "3" }, attrs || {}));
    textarea.value = state.modalForm[key] || "";
    textarea.addEventListener("input", () => {
      state.modalForm[key] = textarea.value;
    });
    textarea.addEventListener("change", () => updateModalForm(key, textarea.value));
    return textarea;
  }

  function checkboxRow(key, label, hint) {
    const input = el("input", "", null, { type: "checkbox" });
    input.checked = Boolean(state.modalForm[key]);
    input.addEventListener("change", () => updateModalForm(key, input.checked));
    return el("label", "check-row", [
      input,
      el("span", "", label),
      hint ? el("small", "", hint) : null,
    ]);
  }

  function count(value) {
    return Number.isFinite(Number(value)) ? Number(value) : 0;
  }

  function fmtTime(value) {
    if (!value) return "n/a";
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toISOString().slice(11, 19) + "Z";
  }

  function fmtDate(value) {
    if (!value) return "n/a";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toISOString().replace("T", " ").slice(0, 19) + "Z";
  }

  function shortId(value) {
    const text = safe(value, "");
    if (text.length <= 20) return text || "n/a";
    return `${text.slice(0, 10)}...${text.slice(-6)}`;
  }

  function tone(status) {
    const s = safe(status, "").toLowerCase();
    if (["completed", "completed_with_concerns", "passed", "ok", "healthy"].includes(s)) return "ok";
    if (["running", "assigned", "registered", "reused"].includes(s)) return "run";
    if (["blocked", "pending", "warning", "warn", "stale", "waiting", "waiting-input", "disconnected"].includes(s)) return "warn";
    if (["failed", "error", "danger", "missing_run", "no_run", "missing_run_file", "violation-flash", "coordinator-dead"].includes(s)) return "danger";
    if (["decision_required", "info"].includes(s)) return "info";
    if (["cancelled", "queued", "planned", "unknown", "starting", "empty"].includes(s)) return "queued";
    return "";
  }

  function statusPill(status, label) {
    return el("span", `status ${tone(status)}`, [
      el("span", `dot ${tone(status)}`),
      safe(label || status, "unknown"),
    ]);
  }

  function badge(value, badgeTone) {
    if (!value) return null;
    return el("span", `badge ${badgeTone || ""}`, String(value));
  }

  function panel(title, subtitle, body, extraClass) {
    return el("section", `panel ${extraClass || ""}`, [
      el("div", "panel-head", [
        el("span", "panel-title", title),
        subtitle ? el("span", "panel-sub", subtitle) : null,
      ]),
      body,
    ]);
  }

  function empty(message) {
    return el("div", "empty", message);
  }

  function currentRun() {
    if (state.fixtureScenario) return fixtureStatus(state.fixtureScenario);
    return state.data.status || {};
  }

  function currentAlerts() {
    if (state.fixtureScenario) return fixtureAlerts(state.fixtureScenario);
    return state.data.alerts && Array.isArray(state.data.alerts.alerts) ? state.data.alerts.alerts : [];
  }

  function currentHistoryRows() {
    if (state.fixtureScenario) return fixtureHistory();
    return state.data.history && Array.isArray(state.data.history.runs) ? state.data.history.runs : [];
  }

  function hostHeartbeatState() {
    if (state.fixtureScenario) {
      return {
        owner: "interactive-codex",
        interval_seconds: 900,
        effective_status: "active",
        active: true,
        source: "fixture",
        last_wakeup_at: new Date(Date.now() - 7 * 60 * 1000).toISOString(),
        last_observed_cursor: "fixture-event",
      };
    }
    return state.data.hostHeartbeat || {};
  }

  function dashboardScenario() {
    if (state.fixtureScenario) return fixtureScenario(state.fixtureScenario);
    const run = state.data.status || {};
    const alerts = currentAlerts();
    const status = safe(run.run_status || run.status, "").toLowerCase();
    const terminal = TERMINAL_STATUSES.includes(status);
    const violations = violationAlerts(alerts, run);
    const staleSupervisor = coordinatorDeadEvidence(run, alerts);
    const disconnected = !terminal && (state.failedPolls >= STALE_POLL_LIMIT || Boolean(state.apiErrors.status) || Boolean(state.apiErrors.events && state.lastSuccessfulAt));
    const pendingDecisions = count(run.pending_decisions) || decisions().length || alerts.some((item) => item.type === "pending_decision");
    let id = "running";
    if (!run.run_id || ["no_run", "missing_run"].includes(status)) id = "empty";
    else if (violations.length) id = "violation-flash";
    else if (staleSupervisor) id = "coordinator-dead";
    else if (disconnected) id = "disconnected";
    else if (pendingDecisions) id = "waiting-input";
    else if (status === "failed") id = "failed";
    else if (status === "cancelled") id = "cancelled";
    else if (status === "completed" || status === "completed_with_concerns") id = "completed";
    else if (["planned", "registered", "assigned", "queued", "starting"].includes(status) || !run.last_event_at) id = "starting";
    return scenarioFromLive(id, { run, alerts, violations, staleSupervisor, terminal });
  }

  function scenarioFromLive(id, context) {
    const run = context.run || {};
    const alerts = context.alerts || [];
    const agents = Array.isArray(run.agents) ? run.agents : [];
    const byRole = run.agent_counts && run.agent_counts.by_role || {};
    const pending = count(run.pending_decisions) || decisions().length;
    const materialAlerts = alerts.length;
    const terminalReason = terminalReasonFor(run, id);
    const progress = scenarioProgress(id, run);
    const subtitles = {
      empty: "No active Dispatch Engine run is bound to this dashboard.",
      starting: "Launch, import, or worker spawn evidence is still forming.",
      running: "Live run data is being read from Dispatch Engine state.",
      "waiting-input": "Operator input is required before affected work can continue.",
      "violation-flash": "Unresolved protocol or capability violation requires review.",
      disconnected: "The dashboard is showing last-known data after polling trouble.",
      "coordinator-dead": "Coordinator or detached supervisor evidence appears stale.",
      completed: "Run reached a terminal completed state; elapsed time is frozen.",
      cancelled: "Run was cancelled; evidence and history remain visible.",
      failed: "Run failed; inspect terminal reason, alerts, and logs.",
    };
    return {
      id,
      fixture: false,
      label: id.replace("-", " "),
      title: scenarioTitle(id, run),
      subtitle: subtitles[id],
      progress,
      terminal: ["completed", "cancelled", "failed"].includes(id),
      terminalReason,
      tags: scenarioTags(id, run, alerts, context),
      stats: [
        ["agents", agents.length],
        ["workers", count(byRole.worker)],
        ["pending", pending],
        ["alerts", materialAlerts],
      ],
      banner: scenarioBanner(id, run, alerts, context),
    };
  }

  function scenarioTitle(id, run) {
    if (id === "empty") return "No active run";
    if (id === "waiting-input") return "Waiting for operator input";
    if (id === "violation-flash") return "Protocol review required";
    if (id === "disconnected") return "Dashboard disconnected";
    if (id === "coordinator-dead") return "Coordinator heartbeat stale";
    if (id === "completed") return "Run completed";
    if (id === "cancelled") return "Run cancelled";
    if (id === "failed") return "Run failed";
    if (id === "starting") return "Run starting";
    return safe(run.objective || run.summary, "Run in progress");
  }

  function scenarioProgress(id, run) {
    if (id === "empty") return 0;
    if (id === "starting") return 14;
    if (id === "waiting-input") return 52;
    if (id === "violation-flash") return 58;
    if (id === "disconnected") return 63;
    if (id === "coordinator-dead") return 47;
    if (id === "completed") return 100;
    if (id === "cancelled") return 74;
    if (id === "failed") return 66;
    const counts = run.workstream_counts || {};
    const total = Object.values(counts).reduce((sum, value) => sum + count(value), 0);
    const done = count(counts.completed) + count(counts.validated) + count(counts.merged);
    return total ? Math.max(8, Math.min(96, Math.round((done / total) * 100))) : 38;
  }

  function scenarioTags(id, run, alerts, context) {
    const tags = [];
    if (state.fixtureScenario) tags.push("fixture mode");
    tags.push(id);
    if (run.run_id) tags.push(`run ${shortId(run.run_id)}`);
    if (context.terminal) tags.push("frozen clock");
    if (context.violations && context.violations.length) tags.push(`${context.violations.length} violation(s)`);
    if (count(run.pending_decisions)) tags.push(`${count(run.pending_decisions)} decision(s)`);
    if (state.lastSuccessfulAt && id === "disconnected") tags.push(`known ${fmtTime(state.lastSuccessfulAt)}`);
    return tags.slice(0, 5);
  }

  function scenarioBanner(id, run, alerts, context) {
    if (id === "violation-flash") {
      const first = context.violations && context.violations[0] || {};
      return {
        tone: "danger",
        title: "Violation flash",
        message: safe(first.summary || first.violation || "Protocol or capability violation is unresolved.", "Violation requires review."),
        action: "Review",
        onAction: () => openModal("capability", first),
      };
    }
    if (id === "disconnected") {
      return {
        tone: "warn",
        title: "Disconnected",
        message: `Last successful fetch ${state.lastSuccessfulAt ? fmtDate(state.lastSuccessfulAt) : "not recorded"}; showing known data.`,
        action: "Retry",
        onAction: load,
      };
    }
    if (id === "coordinator-dead") {
      return {
        tone: "danger",
        title: "Coordinator dead",
        message: safe(context.staleSupervisor && context.staleSupervisor.summary, "Coordinator heartbeat or supervisor process is stale."),
        action: "Logs",
        onAction: () => openModal("tail"),
      };
    }
    if (id === "waiting-input") {
      return {
        tone: "warn",
        title: "Waiting input",
        message: "Pending decisions are blocking or pausing workstreams.",
        action: "Decisions",
        onAction: () => setScreen("decisions"),
      };
    }
    return null;
  }

  function violationAlerts(alerts, run) {
    const rows = alerts.filter((alert) => {
      const text = [alert.type, alert.violation, alert.kind, alert.summary].map((item) => safe(item, "").toLowerCase()).join(" ");
      return text.includes("protocol") || text.includes("capability") || text.includes("violation");
    });
    const profile = run.capability_profiles || {};
    if (Array.isArray(profile.violations)) rows.push(...profile.violations);
    const protocol = run.protocol_violations || {};
    if (Array.isArray(protocol.unresolved)) rows.push(...protocol.unresolved);
    return rows;
  }

  function coordinatorDeadEvidence(run, alerts) {
    const supervisors = Array.isArray(run.supervisors) ? run.supervisors : [];
    const staleSupervisor = supervisors.find((item) => item.status === "stale" || item.process_alive === false);
    if (staleSupervisor) return staleSupervisor;
    const diagnostics = Array.isArray(run.lifecycle_diagnostics) ? run.lifecycle_diagnostics : [];
    const diagnostic = diagnostics.find((item) => safe(item.type, "").includes("stale") || safe(item.type, "").includes("orphaned"));
    if (diagnostic) return diagnostic;
    return alerts.find((alert) => safe(alert.type || alert.summary, "").toLowerCase().includes("stale_detached_supervisor"));
  }

  function terminalReasonFor(run, id) {
    if (id === "cancelled") return run.cancellation_reason || run.cancel_reason || run.reason || "Cancellation reason not exposed.";
    if (id === "failed") return run.failure_reason || run.error || run.reason || "Failure reason not exposed.";
    if (id === "completed") return run.completion_summary || run.summary || "Completion summary not exposed.";
    return null;
  }

  function allEvents() {
    const events = [];
    if (state.data.tail && Array.isArray(state.data.tail.events)) events.push(...state.data.tail.events);
    if (!events.length && state.data.events && Array.isArray(state.data.events.events)) {
      events.push(...state.data.events.events);
    }
    return events;
  }

  function workstreams() {
    const run = currentRun();
    const plan = state.data.plan || {};
    if (Array.isArray(plan.workstreams) && plan.workstreams.length) {
      return plan.workstreams.map((item) => ({
        id: item.id,
        title: item.title || item.name || item.id,
        status: item.status || "planned",
        agent: item.agent_id,
        role: item.role,
      })).sort((a, b) => safe(a.id).localeCompare(safe(b.id)));
    }
    const rows = new Map();
    const assignments = Array.isArray(run.workstream_assignments) ? run.workstream_assignments : [];
    assignments.forEach((item) => {
      const id = safe(item.workstream, "");
      if (!id) return;
      rows.set(id, {
        id,
        title: id,
        status: item.status || "assigned",
        agent: item.agent_id,
        role: item.role,
      });
    });
    allEvents().forEach((event) => {
      const id = event.workstream;
      if (!id) return;
      const existing = rows.get(id) || { id, title: id, status: "planned" };
      if (event.type === "workstream.planned" && event.payload && event.payload.title) {
        existing.title = event.payload.title;
        existing.status = existing.status || "planned";
      }
      if (event.type === "workstream.assigned" && event.payload && event.payload.agent_id) {
        existing.agent = event.payload.agent_id;
        existing.status = existing.status === "planned" ? "assigned" : existing.status;
      }
      rows.set(id, existing);
    });
    const alerts = currentAlerts();
    alerts.forEach((alert) => {
      if (!alert.workstream) return;
      const existing = rows.get(alert.workstream) || { id: alert.workstream, title: alert.workstream };
      if (alert.status) existing.status = alert.status;
      if (alert.type && alert.type.indexOf("blocked") !== -1) existing.status = "blocked";
      rows.set(alert.workstream, existing);
    });
    return Array.from(rows.values()).sort((a, b) => safe(a.id).localeCompare(safe(b.id)));
  }

  function decisions() {
    const run = currentRun();
    const rows = [];
    const actions = Array.isArray(run.next_actions) ? run.next_actions : [];
    actions.filter((item) => item.type === "decision_required").forEach((item) => {
      rows.push({
        id: item.decision_id,
        question: item.question,
        workstream: item.workstream,
        recommended: item.recommended_option,
        raised_by: item.agent_id || item.actor,
        heartbeat_age: item.heartbeat_age || item.unanswered_heartbeats,
        reason: item.reason || item.summary,
        options: item.options,
        risk: item.risk,
        affected_files: item.affected_files,
        source: "status",
      });
    });
    const alerts = currentAlerts();
    alerts.filter((item) => item.type === "pending_decision").forEach((item) => {
      if (!rows.some((row) => row.id === item.decision_id)) {
        rows.push({
          id: item.decision_id,
          question: item.question,
          workstream: item.workstream,
          recommended: item.recommended_option,
          raised_by: item.agent_id || item.actor,
          heartbeat_age: item.heartbeat_age || item.unanswered_heartbeats,
          reason: item.reason || item.summary,
          options: item.options,
          risk: item.risk || item.severity,
          affected_files: item.affected_files,
          source: "alerts",
        });
      }
    });
    return rows;
  }

  function validators() {
    const run = currentRun();
    const agents = Array.isArray(run.agents) ? run.agents : [];
    return agents.filter((agent) => agent.role === "validator");
  }

  function render() {
    if (!app) return;
    rememberScrollPositions(app);
    applyPreferences();
    const scenario = dashboardScenario();
    app.innerHTML = "";
    app.className = `app-shell scenario-${scenario.id} ${scenario.fixture ? "fixture-mode" : ""}`;
    append(app, [renderSidebar(), renderMain(), renderModal()]);
    restoreScrollPositions(app);
    updateLiveHeartbeatClocks(app);
  }

  function renderSidebar() {
    const run = currentRun();
    const alerts = currentAlerts();
    const agents = Array.isArray(run.agents) ? run.agents : [];
    const counts = {
      decisions: count(run.pending_decisions) || decisions().length,
      agents: agents.length,
      alerts: alerts.length,
      validators: validators().length,
      plan: workstreams().length || count(Object.values(run.workstream_counts || {}).reduce((a, b) => a + b, 0)),
    };
    const side = el("aside", "sidebar", [
      el("div", "brand", [
        el("div", "brand-mark", "de"),
        el("div", "brand-title", [
          el("strong", "", "Dispatch Engine"),
          el("span", "", safe(run.provider || run.profile, "local dashboard")),
        ]),
      ]),
      el("div", "nav-label", "Run surfaces"),
      el("nav", "nav"),
      renderRecentRuns(),
    ]);
    const nav = side.querySelector(".nav");
    NAV.forEach(([key, label]) => {
      const b = button(state.screen === key ? "active" : "", label, [
        el("span", "", label),
        badge(counts[key], key === "alerts" ? "warn" : key === "decisions" ? "danger" : ""),
      ], () => setScreen(key));
      nav.appendChild(b);
    });
    return side;
  }

  function renderRecentRuns() {
    const history = currentHistoryRows().slice(0, 6);
    const activeRunId = currentRun().run_id;
    return el("div", "run-list", [
      el("div", "side-label", "Recent runs"),
      history.length ? history.map((run) => button(`run-link ${run.run_id === activeRunId ? "active" : ""}`, runSwitchTitle(run), [
        el("span", `dot ${tone(run.status)}`),
        el("span", "", [
          el("strong", "", safe(run.short_id || shortId(run.run_id), "run")),
          el("small", "", `${safe(run.status, "unknown")} / ${safe(run.repo_name, "repo")}`),
        ]),
      ], () => pickRun(run))) : empty("No run history loaded."),
    ]);
  }

  function renderMain() {
    const run = currentRun();
    const scenario = dashboardScenario();
    return el("main", "main", [
      el("header", "topbar", [
        el("div", "crumbs", [
          el("span", "", "dispatch"),
          el("span", "", "/"),
          renderRunSwitcherControl(run),
        ]),
        el("div", "top-spacer"),
        el("div", `clock ${scenario.terminal ? "frozen" : ""}`, [el("span", `dot ${tone(scenario.id)}`), safe(scenario.label, "loading")]),
        el("div", "api-state", scenario.fixture ? `fixture ${scenario.id}` : state.updatedAt ? `updated ${fmtTime(state.updatedAt)}` : "waiting"),
        button("icon-button", "Refresh", svgIcon("refresh"), load),
        button("icon-button", "Tail logs (c)", svgIcon("tail"), () => openModal("tail")),
        button("icon-button", "Status JSON (s)", svgIcon("status"), () => openModal("status")),
        renderSettingsControl(),
        button("icon-button", "Keyboard help (?)", svgIcon("help"), () => openModal("keyboard")),
        button("icon-button danger", "Cancel preview (x)", svgIcon("cancel"), () => openModal("cancel")),
      ]),
      scenario.fixture ? renderFixtureStrip(scenario) : null,
      scenario.banner ? renderScenarioBanner(scenario.banner) : null,
      state.error ? el("div", "panel-body error-box", state.error) : null,
      el("div", "content", [
        el("div", "page", renderScreen(), { "data-scroll-key": `page:${state.screen}:${state.selectedAgentId || ""}` }),
        renderEventTail(),
      ]),
    ]);
  }

  function renderRunSwitcherControl(run) {
    return el("div", "run-switch-anchor", [
      button(
        `crumb-run ${state.runSwitcherOpen ? "active" : ""}`,
        "Open run switcher",
        [`run ${shortId(run.run_id)}`, el("span", "chevron", state.runSwitcherOpen ? "up" : "down")],
        () => {
          state.runSwitcherOpen = !state.runSwitcherOpen;
          state.settingsOpen = false;
          state.modal = null;
          render();
        },
      ),
      state.runSwitcherOpen ? renderRunSwitcherPopover() : null,
    ]);
  }

  function renderRunSwitcherPopover() {
    const history = historyRows().slice(0, 8);
    const currentId = currentRun().run_id;
    return el("div", "run-switcher", [
      el("div", "run-switcher-h", [
        el("span", "", "active / recent runs"),
        el("span", "hint", `${history.length} loaded`),
      ]),
      history.length ? history.map((run) => button(
        `run-switcher-row ${run.run_id === currentId ? "active" : ""}`,
        runSwitchTitle(run),
        [
          el("span", `dot ${tone(run.status)}`),
          el("div", "run-switcher-meta", [
            el("div", "run-switcher-name", [
              el("span", "mono", safe(run.short_id || shortId(run.run_id), "run")),
              el("span", "", safe(run.repo_name || run.repo, "repo unavailable")),
            ]),
            el("div", "run-switcher-sub", [
              el("span", "", safe(run.plan_id, "plan not exposed")),
              el("span", "", " / "),
              el("span", "", `${formatDuration(run.duration_ms)} elapsed`),
              el("span", "", " / "),
              el("span", "", `${valueOrUnavailable(run.agent_count)} agents`),
            ]),
          ]),
          statusPill(run.status),
        ],
        () => pickRun(run),
      )) : empty("No recent runs returned by /api/history."),
      el("div", "run-switcher-foot", "Different runs open a read-only command preview because this server is bound to the current run."),
    ]);
  }

  function runSwitchTitle(run) {
    return `${safe(run.run_id, "run")} / ${safe(run.status, "unknown")} / ${safe(run.repo_name || run.repo, "repo")}`;
  }

  function pickRun(run) {
    if (!run || run.run_id === currentRun().run_id) {
      state.runSwitcherOpen = false;
      render();
      return;
    }
    openModal("runPreview", run);
  }

  function renderScreen() {
    if (state.loading && !state.data.status) {
      return empty("Loading dashboard API data...");
    }
    switch (state.screen) {
      case "workstreams":
      case "plan":
        return renderWorkstreams();
      case "agents":
        return renderAgents();
      case "agent":
        return renderAgentDetail();
      case "decisions":
        return renderDecisions();
      case "capabilities":
        return renderCapabilities();
      case "validators":
        return renderValidators();
      case "alerts":
        return renderAlerts();
      case "history":
        return renderHistory();
      case "logs":
        return renderLogs();
      case "overview":
      default:
      return renderOverview();
    }
  }

  function renderOverview() {
    const run = currentRun();
    const scenario = dashboardScenario();
    if (scenario.id === "empty") return renderEmptyDashboard(scenario);
    const agents = Array.isArray(run.agents) ? run.agents : [];
    const counts = run.agent_counts || {};
    const byRole = counts.by_role || {};
    const materialAlerts = currentAlerts();
    const pending = decisions();
    const violations = violationAlerts(materialAlerts, run);
    const workstreamRows = workstreams();
    return el("div", "overview-command", [
      renderOverviewRunHeader(scenario, run, {
        agents: agents.length,
        workers: count(byRole.worker),
        decisions: pending.length || count(run.pending_decisions),
        violations: violations.length,
      }),
      el("div", "overview-main-grid", [
        renderOverviewWorkstreams(workstreamRows),
        el("div", "overview-side", [
          renderHostHeartbeatCard(run, pending),
          panel("Pending decisions", `${pending.length} open · ${autonomousRiskCount(pending)} with autonomous risk`, renderOverviewDecisions(pending), "overview-panel decisions-panel"),
          panel("Material alerts", "read-only alert feed", renderAlertRows(materialAlerts.slice(0, 4)), "overview-panel alerts-panel"),
        ]),
      ]),
    ]);
  }

  function renderOverviewRunHeader(scenario, run, metrics) {
    const wsCounts = normalizedWorkstreamCounts(run);
    const statusLabel = scenario.id === "waiting-input" ? "waiting · detached" : `${safe(run.run_status || run.status || scenario.id, scenario.id)} · detached`;
    const heartbeat = hostHeartbeatState();
    const heartbeatStatus = safe(heartbeat.effective_status || heartbeat.heartbeat_status || "unknown", "unknown");
    return el("section", `run-hero overview-run-header state-${scenario.id}`, [
      el("div", "overview-run-left", [
        el("div", "overview-id-row", [
          statusPill(scenario.id, statusLabel),
          el("span", "overview-run-id", ["run ", el("span", "accent-text", shortId(run.run_id)), " · ", safe(run.run_id, "").slice(0, 24)]),
        ]),
        el("div", "run-title overview-title", safe(run.objective || run.summary || scenario.title, scenario.title)),
        el("div", "overview-meta", [
          metaItem("repo", safe(run.repo || run.repo_name || repoPath(), "repo unavailable")),
          metaItem("plan", safe(run.plan_id || run.plan || run.plan_path || state.data.plan && state.data.plan.plan_id, "plan unavailable")),
          metaItem("provider", safe(run.provider || run.profile, "provider unavailable")),
          metaItem("coordinator", coordinatorId(run)),
        ]),
        renderOverviewSplit(wsCounts),
      ]),
      el("div", "overview-run-right", [
        el("div", "overview-stat-grid", [
          statBlock("completed", wsCounts.completed, "ok"),
          statBlock("running", wsCounts.running, wsCounts.running ? "danger" : ""),
          statBlock("blocked", wsCounts.blocked, wsCounts.blocked ? "warn" : ""),
          statBlock("queued", wsCounts.queued, ""),
          statBlock("elapsed", runElapsedText(run), ""),
          statBlock("workers", metrics.workers || metrics.agents, ""),
          statBlock("decisions", metrics.decisions, metrics.decisions ? "warn" : ""),
          statBlock("violations", metrics.violations, metrics.violations ? "danger" : ""),
        ]),
        el("div", "overview-mode-row", [
          el("span", "chip", ["host heartbeat ", el("b", "", safe(heartbeat.owner, "interactive-codex")), " · ", heartbeatStatus]),
          el("span", "chip", ["mode: ", el("b", "", detachedMode(run))]),
        ]),
      ]),
    ]);
  }

  function renderOverviewSplit(counts) {
    const entries = [
      ["completed", counts.completed],
      ["running", counts.running],
      ["blocked", counts.blocked],
      ["queued", counts.queued],
    ];
    const segments = entries.filter(([, value]) => count(value) > 0);
    return el("div", "overview-progress", [
      el("div", "splitbar overview-split", segments.length ? segments.map(([key, value]) => el("span", key, "", {
        title: `${key}: ${value}`,
        style: `flex:${count(value)};background:${segmentColor(key)}`,
      })) : el("span", "empty", "", { title: "no workstreams", style: "flex:1;background:var(--panel-3)" })),
      el("div", "overview-legend", entries.map(([key, value]) => el("span", "", [
        el("i", count(value) ? "" : "zero", "", { style: `background:${count(value) ? segmentColor(key) : "var(--panel-3)"}` }),
        `${value} ${key}`,
      ]))),
    ]);
  }

  function renderOverviewWorkstreams(rows) {
    return panel("Workstreams", `${safe(currentRun().plan_id || currentRun().plan, "plan")} · ${rows.length || count(Object.values(normalizedWorkstreamCounts(currentRun())).reduce((a, b) => a + b, 0))} total`, rows.length ? el("div", "overview-workstream-list", rows.map(renderOverviewWorkstreamRow)) : empty("No workstream rows available from the dashboard API yet."), "overview-panel overview-workstreams");
  }

  function renderOverviewWorkstreamRow(row, index) {
    const status = safe(row.status, "queued").toLowerCase();
    const pct = workstreamPercent(row);
    return el("div", "overview-work-row", [
      el("div", "overview-work-index", String(index + 1).padStart(2, "0")),
      el("div", "overview-work-name", [
        el("div", "overview-work-title", [
          el("span", `dot ${tone(status)}`, "", { title: status }),
          safe(row.title || row.id, "workstream"),
        ]),
        el("div", "overview-work-meta", [
          safe(row.id, "workstream"),
          row.agent ? `→ ${row.agent}` : "",
          row.role ? row.role : "",
        ].filter(Boolean).join(" · ")),
      ]),
      el("div", "overview-work-progress", [
        el("div", "bar", el("span", "", "", { style: `width:${pct}%;background:${segmentColor(status)}` })),
        el("div", "overview-work-lab", [
          el("span", "", `${pct}%`),
          el("span", "", status === "queued" ? "queued" : `state ${status}`),
        ]),
      ]),
      statusPill(status),
    ]);
  }

  function renderHostHeartbeatCard(run, pending) {
    const heartbeat = hostHeartbeatState();
    const intervalSeconds = count(heartbeat.interval_seconds) || 15 * 60;
    const effective = safe(heartbeat.effective_status || heartbeat.heartbeat_status || "missing", "missing").toLowerCase();
    const terminal = isTerminalRun(run);
    const active = heartbeat.active === true && !terminal;
    const missing = effective === "missing";
    const stopped = terminal || ["stopped", "cancelled", "paused", "disabled"].includes(effective);
    const lastWake = heartbeat.last_wakeup_at || heartbeat.last_wake_at || heartbeat.last_checked_at || null;
    const ageSeconds = lastWake ? Math.max(0, Math.floor((Date.now() - new Date(lastWake).getTime()) / 1000)) : null;
    const remaining = ageSeconds === null ? intervalSeconds : Math.max(0, intervalSeconds - (ageSeconds % intervalSeconds));
    const pct = Math.max(0, Math.min(100, Math.round((remaining / intervalSeconds) * 100)));
    const risk = autonomousRiskCount(pending);
    const ringTime = stopped ? "STOP" : missing ? "SETUP" : active ? mmss(remaining) : "PAUSE";
    const ringLabel = stopped ? "terminal" : missing ? "missing" : active ? "until next" : effective;
    const line = stopped
      ? ["Host heartbeat ", el("b", "hb-wakeup-age", "stopped")]
      : missing
        ? ["Host heartbeat ", el("b", "hb-wakeup-age", "state unavailable")]
        : ["Last host wakeup ", el("b", "hb-wakeup-age", ageSeconds === null ? "unknown" : `${humanDuration(ageSeconds)} ago`)];
    const metaOne = stopped
      ? safe(heartbeat.stop_reason, "terminal run reached; watcher should be off")
      : missing
        ? "No host-heartbeat record found under .dispatch for this run."
        : pending.length ? `${Math.min(3, pending.length)} of 4 unanswered · ${safe(pending[0] && pending[0].id, "decision")}` : "no pending user decision";
    const metaTwo = stopped
      ? "no autonomous fallback while stopped"
      : missing
        ? "Interactive Codex should create/update the host heartbeat snapshot."
        : risk ? `${risk} more miss → autonomous-technical eligibility` : "autonomous fallback not armed";
    return panel("Host heartbeat", "interval=15m · owner=interactive-codex", el("div", "hb-card", [
      el("div", `hb-ring ${stopped ? "stopped" : missing ? "missing" : ""}`, [
        el("div", "hb-ring-core", [
          el("span", "hb-time", ringTime),
          el("span", "hb-label", ringLabel),
        ]),
      ], { style: `--pct:${active ? pct : 0}%` }),
      el("div", "hb-info", [
        el("div", "hb-line", line),
        el("div", "hb-meta", metaOne),
        el("div", `hb-meta ${risk && !stopped && !missing ? "warn-text" : ""}`, metaTwo),
        el("div", "hb-actions", [
          button("btn-sm icon", "Poke heartbeat now", svgIcon("refresh"), () => openModal("tail")),
          button("btn-sm icon", "Open heartbeat evidence", svgIcon("status"), () => openModal("status")),
        ]),
      ]),
    ], {
      "data-heartbeat-interval": String(intervalSeconds),
      "data-heartbeat-last-wake": lastWake ? new Date(lastWake).toISOString() : "",
      "data-heartbeat-active": active ? "true" : "false",
    }), "overview-panel heartbeat-panel");
  }

  function renderOverviewDecisions(rows) {
    if (!rows.length) return empty("No pending decisions.");
    return el("div", "overview-decision-list", rows.slice(0, 3).map((row) => {
      const node = el("div", "overview-decision-row clickable", [
        el("span", `decision-stripe ${row.risk ? tone(row.risk) : "warn"}`),
        el("div", "", [
          el("div", "overview-decision-question", safe(row.question, "Decision required")),
          el("div", "overview-decision-meta", [
            safe(row.id, "decision"),
            row.raised_by ? ` · raised by ${row.raised_by}` : "",
            row.workstream ? ` · ${row.workstream}` : "",
          ]),
        ]),
        el("div", "overview-decision-actions", [
          button("btn-sm icon", "Defer decision", svgIcon("help"), () => openModal("decision", row)),
          button("btn-sm primary icon", "Resolve decision", svgIcon("check"), () => openModal("decision", row)),
        ]),
      ], { role: "button", tabindex: "0", title: `Open decision preview for ${safe(row.id, "decision")}` });
      node.addEventListener("click", () => openModal("decision", row));
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openModal("decision", row);
        }
      });
      return node;
    }));
  }

  function metaItem(label, value) {
    return el("span", "", [el("b", "", label), " ", el("span", "mono", value)]);
  }

  function statBlock(label, value, toneName) {
    return el("div", "overview-stat", [
      el("span", "overview-stat-value", safe(value, "0")),
      el("span", `overview-stat-key ${toneName || ""}`, label),
    ]);
  }

  function normalizedWorkstreamCounts(run) {
    const base = Object.assign({ completed: 0, running: 0, blocked: 0, queued: 0 }, run.workstream_counts || {});
    const rows = workstreams();
    if (!Object.values(base).some((value) => count(value)) && rows.length) {
      rows.forEach((row) => {
        const key = safe(row.status, "queued").toLowerCase();
        if (key === "planned" || key === "registered" || key === "unknown") base.queued += 1;
        else if (key === "assigned") base.running += 1;
        else if (Object.prototype.hasOwnProperty.call(base, key)) base[key] += 1;
        else base.queued += 1;
      });
    }
    return {
      completed: count(base.completed) + count(base.completed_with_concerns) + count(base.passed),
      running: count(base.running) + count(base.assigned) + count(base.registered),
      blocked: count(base.blocked) + count(base.pending),
      queued: count(base.queued) + count(base.planned),
    };
  }

  function workstreamPercent(row) {
    const explicit = Number(row.progress || row.pct || row.percent);
    if (Number.isFinite(explicit)) return Math.max(0, Math.min(100, Math.round(explicit)));
    const status = safe(row.status, "").toLowerCase();
    if (status === "completed" || status === "completed_with_concerns" || status === "passed") return 100;
    if (status === "running" || status === "assigned" || status === "registered") return 64;
    if (status === "blocked" || status === "pending") return 18;
    return 0;
  }

  function coordinatorId(run) {
    if (run.coordinator && typeof run.coordinator === "object") return safe(run.coordinator.agent_id, "coordinator unavailable");
    const agents = Array.isArray(run.agents) ? run.agents : [];
    const coordinator = agents.find((agent) => agent.role === "coordinator");
    return safe(run.coordinator || run.coordinator_id || coordinator && coordinator.agent_id, "coordinator unavailable");
  }

  function detachedMode(run) {
    const supervisors = Array.isArray(run.supervisors) ? run.supervisors : [];
    if (supervisors.length) return "detached";
    return safe(run.mode || run.launch_mode || "detached", "detached");
  }

  function runElapsedText(run) {
    if (Number.isFinite(Number(run.duration_ms))) return formatDuration(Number(run.duration_ms));
    const coordinator = run.coordinator && typeof run.coordinator === "object" ? run.coordinator : null;
    const start = run.started_at || run.created_at || coordinator && (coordinator.started_at || coordinator.created_at);
    if (!start) return "n/a";
    const started = new Date(start).getTime();
    const end = run.completed_at || run.cancelled_at || run.failed_at || run.updated_at || coordinator && (coordinator.completed_at || coordinator.updated_at);
    const stopped = end ? new Date(end).getTime() : Date.now();
    if (!Number.isFinite(started) || !Number.isFinite(stopped)) return "n/a";
    return formatDuration(Math.max(0, stopped - started));
  }

  function isTerminalRun(run) {
    const status = safe(run.run_status || run.status, "").toLowerCase();
    return TERMINAL_STATUSES.includes(status);
  }

  function humanDuration(seconds) {
    const value = Math.max(0, Math.floor(count(seconds)));
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const secs = value % 60;
    if (hours) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
    if (minutes) return `${minutes}m ${String(secs).padStart(2, "0")}s`;
    return `${secs}s`;
  }

  function autonomousRiskCount(rows) {
    return rows.filter((row) => count(row.heartbeat_age || row.unanswered_heartbeats) >= 3 || safe(row.risk || row.severity, "").toLowerCase().includes("autonomous")).length;
  }

  function mmss(seconds) {
    const value = Math.max(0, Math.floor(count(seconds)));
    const minutes = Math.floor(value / 60);
    return `${String(minutes).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
  }

  function renderRunHero(scenario, run, children) {
    return el("section", `run-hero state-${scenario.id}`, children);
  }

  function renderScenarioTags(scenario) {
    return el("div", "scenario-tags", scenario.tags.map((tag) => el("span", "chip", tag)));
  }

  function renderScenarioProgress(scenario) {
    return el("div", "scenario-progress", [
      el("div", "bar", el("span", "", "", { style: `width:${scenario.progress}%` })),
      el("span", "mono", `${scenario.progress}%`),
      scenario.terminal ? el("span", "frozen-label", "clock frozen") : null,
    ]);
  }

  function renderScenarioBanner(banner) {
    return el("div", `scenario-banner ${banner.tone || ""}`, [
      el("span", `dot ${banner.tone || "info"}`),
      el("div", "", [
        el("strong", "", banner.title),
        el("span", "", banner.message),
      ]),
      banner.action ? button("btn-sm", banner.action, banner.action, banner.onAction || (() => {})) : null,
    ]);
  }

  function renderFixtureStrip(scenario) {
    return el("div", "fixture-strip", [
      el("span", "badge warn", "Fixture mode"),
      el("span", "", `Rendering ${scenario.id} with browser-only demo data. No .dispatch state writes are performed.`),
      el("div", "fixture-links", SCENARIO_IDS.map((id) => el("a", id === scenario.id ? "active" : "", id, { href: `?fixture=${encodeURIComponent(id)}` }))),
    ]);
  }

  function renderEmptyDashboard(scenario) {
    const repo = repoPath();
    const history = currentHistoryRows().slice(0, 4);
    const command = `python3 scripts/de.py dashboard ${shellQuote(repo)} --detach --json`;
    return el("div", "empty-dashboard", [
      renderRunHero(scenario, currentRun(), [
        el("div", "", [
          statusPill("queued", "no active run"),
          el("div", "run-title", scenario.title),
          el("div", "scenario-subtitle", scenario.subtitle),
          renderScenarioTags(scenario),
          commandBlock(command, "Start or reuse dashboard command preview"),
        ]),
        el("div", "empty-actions", [
          button("btn-sm", "Refresh run state", "Refresh", load),
          button("btn-sm", "Open run history", "History", () => setScreen("history")),
          button("btn-sm", "Open status JSON", "Status JSON", () => openModal("status")),
        ]),
      ]),
      el("div", "grid two", [
        panel("Recent runs", "loaded history or fixture placeholder", history.length ? renderHistoryTable(history) : empty("No recent runs exposed by /api/history.")),
        panel("Plans", "read-only startup context", el("div", "panel-body", [
          empty("No active plan is bound to this dashboard shell."),
          commandBlock(`python3 scripts/de.py status ${shellQuote(repo)} --json`, "Inspect latest run status"),
        ])),
      ]),
    ]);
  }

  function stat(key, value, className) {
    return el("div", "stat", [
      el("div", "key", key),
      el("div", `value ${className || ""}`, String(value)),
    ]);
  }

  function renderSplitCounts(counts) {
    const entries = Object.keys(counts || {}).sort().map((key) => [key, count(counts[key])]);
    if (!entries.length) return empty("No workstream counts reported.");
    const total = entries.reduce((sum, item) => sum + item[1], 0) || 1;
    return el("div", "panel-body split-counts", [
      el("div", "splitbar", entries.map(([key, value]) => el("span", "", "", {
        title: `${key}: ${value}`,
        style: `flex:${Math.max(value, 1)};background:${segmentColor(key)}`,
      }))),
      el("div", "chips", entries.map(([key, value]) => el("span", "chip", `${key}: ${value}`))),
    ]);
  }

  function renderAgentSummary(byRole, byStatus) {
    const roleEntries = Object.keys(byRole || {}).sort().map((key) => el("span", "chip", `${key}: ${byRole[key]}`));
    const statusEntries = Object.keys(byStatus || {}).sort().map((key) => el("span", `chip ${tone(key)}`, `${key}: ${byStatus[key]}`));
    return el("div", "panel-body", [
      el("div", "section-kicker", "Roles"),
      el("div", "chips", roleEntries.length ? roleEntries : [el("span", "chip", "none")]),
      el("div", "section-kicker", "Statuses"),
      el("div", "chips", statusEntries.length ? statusEntries : [el("span", "chip", "none")]),
    ]);
  }

  function renderNextActions(actions) {
    if (!actions.length) return empty("No next actions reported.");
    return el("div", "row-list", actions.slice(0, 6).map((item) => el("div", "alert-row", [
      el("span", `dot ${tone(item.type)}`),
      el("div", "", [
        el("div", "row-title", safe(item.type, "action")),
        el("div", "row-meta", safe(item.question || item.summary || item.diagnostic_types && item.diagnostic_types.join(", "), "")),
      ]),
      item.count ? el("span", "badge warn", item.count) : null,
    ])));
  }

  function renderWorkstreams() {
    const plan = state.data.plan || {};
    const logs = state.data.logs || {};
    return el("div", "plan-screen", [
      renderPlanTreePanel(plan),
      renderCoordinatorLogPanel(logs),
    ]);
  }

  function renderPlanTreePanel(plan) {
    const tree = plan.tree || null;
    const subtitle = safe(plan.source_path || plan.plan_id, "plan metadata unavailable");
    const visibleTree = tree ? filterPlanNode(tree, state.planSearch.trim().toLowerCase()) : null;
    return panel("Plan tree", subtitle, el("div", "plan-tree-shell", [
      el("div", "plan-search", [
        el("span", "search-icon", svgIcon("search"), { "aria-hidden": "true" }),
        planSearchInput(),
        state.planSearch ? button("plan-clear", "Clear plan filter", "esc", () => {
          state.planSearch = "";
          render();
        }) : null,
      ]),
      tree && visibleTree ? el("div", "plan-tree", renderPlanNode(visibleTree, 0), { "data-scroll-key": `plan-tree:${state.planSearch ? "filtered" : "all"}` }) : empty(tree ? `No plan nodes match "${state.planSearch}".` : "No plan tree available from /api/plan."),
      el("div", "plan-footer", state.planSearch ? `filter: "${state.planSearch}"` : "click rows to expand · / to filter"),
    ]), "plan-tree-panel");
  }

  function planSearchInput() {
    const input = el("input", "plan-search-input", null, {
      type: "search",
      placeholder: "filter plan nodes — / to focus",
      value: state.planSearch,
      "aria-label": "Filter plan tree",
    });
    input.addEventListener("input", () => {
      state.planSearch = input.value;
      render();
      const next = app.querySelector(".plan-search-input");
      if (next) {
        next.focus();
        next.setSelectionRange(next.value.length, next.value.length);
      }
    });
    return input;
  }

  function filterPlanNode(node, query) {
    if (!query) return node;
    const children = Array.isArray(node.children) ? node.children.map((child) => filterPlanNode(child, query)).filter(Boolean) : [];
    const haystack = [node.name, node.label, node.title, node.id, node.status, node.agent_id].map((item) => safe(item, "").toLowerCase()).join(" ");
    if (haystack.includes(query) || children.length) return Object.assign({}, node, { children });
    return null;
  }

  function renderPlanNode(node, depth) {
    const children = Array.isArray(node.children) ? node.children : [];
    const hasChildren = children.length > 0;
    const nodeId = safe(node.id || node.name || node.label, `node-${depth}`);
    const collapsed = Boolean(state.collapsedPlanNodes[nodeId]) && !state.planSearch;
    const selected = state.selectedPlanNodeId === nodeId;
    const row = el("div", `plan-node-row ${selected ? "selected" : ""}`, [
      el("span", "plan-indent", "", { style: `width:${depth * 15}px` }),
      el("span", "plan-toggle", hasChildren ? (collapsed ? "▸" : "▾") : ""),
      el("span", `dot ${tone(planNodeStatus(node.status))}`, "", { title: safe(node.status, "unknown") }),
      el("span", "plan-node-kind", hasChildren ? "▣" : "·"),
      el("span", "plan-node-label", highlightText(safe(node.name || node.label || node.title || node.id, "plan node"), state.planSearch)),
      planNodeMeta(node),
    ], { role: "treeitem", tabindex: "0", "aria-expanded": hasChildren ? String(!collapsed) : "false" });
    row.addEventListener("click", () => {
      state.selectedPlanNodeId = nodeId;
      if (hasChildren && !state.planSearch) {
        state.collapsedPlanNodes[nodeId] = !collapsed;
      }
      render();
    });
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        row.click();
      }
    });
    return el("div", "plan-node", [
      row,
      hasChildren && !collapsed ? el("div", "plan-children", children.map((child) => renderPlanNode(child, depth + 1)), { role: "group" }) : null,
    ]);
  }

  function planNodeStatus(status) {
    const value = safe(status, "unknown").toLowerCase();
    if (["planned", "queued", "unknown"].includes(value)) return "queued";
    return value;
  }

  function planNodeMeta(node) {
    const parts = [];
    if (node.agent_id) parts.push(node.agent_id);
    if (Array.isArray(node.depends_on) && node.depends_on.length) parts.push(`depends ${node.depends_on.join(", ")}`);
    if (Number.isFinite(Number(node.file_count))) parts.push(`${node.file_count} files`);
    if (node.blocked_reason) parts.push(`blocked: ${node.blocked_reason}`);
    return parts.length ? el("span", "plan-node-meta", parts.join(" · ")) : null;
  }

  function highlightText(text, query) {
    if (!query) return text;
    const lower = text.toLowerCase();
    const needle = query.toLowerCase();
    const index = lower.indexOf(needle);
    if (index === -1) return text;
    return [
      text.slice(0, index),
      el("mark", "", text.slice(index, index + query.length)),
      text.slice(index + query.length),
    ];
  }

  function renderCoordinatorLogPanel(logs) {
    const stdout = logEntries(logs.stdout, "out");
    const stderr = logEntries(logs.stderr, "err");
    const rows = stdout.concat(stderr).slice(-160);
    return panel("Coordinator stdout / stderr", safe(logs.stdout_path || logs.stderr_path, "coordinator log paths unavailable"), el("div", "coord-log-shell", [
      el("div", "coord-log-head", [
        el("span", `status ${state.refreshing ? "run" : "ok"}`, [
          el("span", `dot ${state.refreshing ? "run" : "ok"}`),
          state.refreshing ? "live tail" : "tail cached",
        ]),
        el("span", "muted mono", `${stdout.length} stdout / ${stderr.length} stderr`),
      ]),
      rows.length ? el("div", "terminal coord-terminal", rows.map(renderTerminalEntry).concat([renderTerminalCaret()]), { "data-scroll-key": "coord-terminal:combined" }) : el("div", "terminal coord-terminal", [
        empty("No coordinator logs loaded."),
        logs.stdout_path ? empty(`stdout unavailable: ${logs.stdout_path}`) : empty("stdout path unavailable."),
        logs.stderr_path ? empty(`stderr unavailable: ${logs.stderr_path}`) : empty("stderr path unavailable."),
        renderTerminalCaret(),
      ], { "data-scroll-key": "coord-terminal:combined" }),
    ]), "coord-log-panel");
  }

  function logEntries(text, source) {
    return splitLines(text).map((line, index) => {
      const parsed = parseLogLine(line);
      return {
        time: parsed.time || String(index + 1).padStart(4, "0"),
        prefix: parsed.prefix || (source === "err" ? "ERR" : "INFO"),
        message: parsed.message,
        source,
      };
    });
  }

  function parseLogLine(line) {
    const match = String(line).match(/^(\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\S+)\s+([A-Z]+|WARN|ERR|ERROR|INFO|OK)?\s*(.*)$/);
    if (!match) return { message: line };
    return { time: match[1], prefix: match[2] || "", message: match[3] || line };
  }

  function renderTerminalEntry(entry) {
    return el("div", "log-line", [
      el("span", "log-time", compactLogTime(entry.time)),
      el("span", `log-source ${tone(entry.prefix) || (entry.source === "err" ? "danger" : "")}`, safe(entry.prefix || entry.source, "log").slice(0, 5)),
      el("span", "log-message", safe(entry.message, "")),
    ]);
  }

  function compactLogTime(value) {
    const text = safe(value, "----");
    if (/^\d{4}-\d{2}-\d{2}T/.test(text)) return fmtTime(text);
    return text;
  }

  function renderTerminalCaret() {
    return el("div", "log-line caret-row", [
      el("span", "log-time", fmtTime(new Date())),
      el("span", "log-source", "·"),
      el("span", "log-message", el("span", "caret", "")),
    ]);
  }

  function renderWorkstreamRows(rows) {
    if (!rows.length) return empty("No workstream rows available from the dashboard API yet.");
    return el("div", "row-list", rows.map((row, index) => {
      const pct = row.status === "completed" ? 100 : row.status === "running" ? 58 : row.status === "assigned" ? 25 : 8;
      return el("div", "work-row", [
        el("div", "row-index", String(index + 1).padStart(2, "0")),
        el("div", "", [
          el("div", "row-title", safe(row.title || row.id, "workstream")),
          el("div", "row-meta", [safe(row.id), row.agent ? ` / ${row.agent}` : "", row.role ? ` / ${row.role}` : ""]),
        ]),
        el("div", "", [
          el("div", "bar", el("span", "", "", { style: `width:${pct}%` })),
          el("div", "row-meta", `${pct}% observed`),
        ]),
        statusPill(row.status || "planned"),
      ]);
    }));
  }

  function renderAgents() {
    const run = currentRun();
    const agents = Array.isArray(run.agents) ? run.agents : [];
    return panel("Agents", "coordinator, workers, reviewers, and validators", agents.length ? el("div", "agent-grid", agents.map(renderAgentCard)) : empty("No agents registered."));
  }

  function renderAgentCard(agent) {
    const profile = agent.capability_profile || {};
    const highRisk = (((runProfile(profile).high_risk_capabilities || [])));
    const files = count((agent.assigned_files || []).length);
    const card = el("article", `agent-card clickable ${agent.role === "coordinator" ? "coordinator" : ""}`, [
      el("div", "agent-top", [
        el("div", "", [
          el("div", "agent-role", safe(agent.role, "agent")),
          el("div", "agent-id", safe(agent.agent_id, "unknown")),
        ]),
        statusPill(agent.status),
      ]),
      el("div", "agent-task", safe(agent.workstream || agent.prompt_path || agent.report_path, "No workstream assigned.")),
      el("div", "chips", [
        el("span", "chip", safe(profile.profile_id || agent.profile, "profile n/a")),
        agent.provider ? el("span", "chip", agent.provider) : null,
        highRisk.length ? el("span", "chip warn", `${highRisk.length} high-risk`) : null,
        el("span", "chip", `${files} files`),
      ]),
      el("div", "agent-foot", [
        el("span", "muted", `heartbeat ${fmtDate(agent.last_heartbeat_at)}`),
        el("span", `dot ${agent.last_heartbeat_at ? "ok" : ""}`, "", { title: agent.last_heartbeat_at ? "heartbeat recorded" : "no heartbeat recorded" }),
      ]),
    ], { role: "button", tabindex: "0", title: `Open Agent detail for ${safe(agent.agent_id, "agent")}` });
    card.addEventListener("click", () => selectAgent(agent.agent_id));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectAgent(agent.agent_id);
      }
    });
    return card;
  }

  function renderAgentDetail() {
    const agentId = state.selectedAgentId;
    const detail = agentId ? state.data.agentDetails[agentId] : null;
    const agent = detail && detail.agent ? detail.agent : findAgent(agentId) || {};
    if (!agentId) return empty("No agent selected.");
    if (state.agentLoading && !detail) return empty("Loading Agent detail...");
    if (state.agentError && !detail) {
      return panel("Agent detail", "unavailable", el("div", "panel-body", [
        empty(`Agent detail unavailable: ${state.agentError}`),
        button("btn-sm", "Back to agents", "Back to agents", () => setScreen("agents")),
      ]));
    }
    return el("div", "agent-detail", [
      renderAgentDetailHeader(agent, detail),
      el("div", "agent-detail-grid", [
        el("div", "agent-detail-stack", [
          panel("Recent stdout", safe(detail && detail.logs && detail.logs.stdout_path, "stdout path unavailable"), renderLogLines(splitLines(detail && detail.logs && detail.logs.stdout), "out")),
          panel("Recent stderr", safe(detail && detail.logs && detail.logs.stderr_path, "stderr path unavailable"), renderLogLines(splitLines(detail && detail.logs && detail.logs.stderr), "err")),
          panel("File scope / writes so far", fileScopeSubtitle(agent, detail), renderAgentFiles(agent, detail)),
        ]),
        el("div", "agent-detail-stack", [
          panel("Heartbeat history", heartbeatSubtitle(detail), renderHeartbeatMini(detail)),
          panel("Agent metadata", "registration, launch, and evidence paths", renderAgentMetadata(agent, detail)),
          panel("Capability grant", capabilitySubtitle(agent, detail), renderAgentCapabilities(agent, detail)),
        ]),
      ]),
    ]);
  }

  function renderAgentDetailHeader(agent, detail) {
    const profile = agent.capability_profile || {};
    return el("section", "agent-detail-head", [
      el("div", "", [
        el("div", "agent-role", safe(agent.role, "agent")),
        el("h2", "", safe(agent.agent_id || state.selectedAgentId, "unknown agent")),
        el("div", "agent-detail-task", safe(agent.workstream || agent.prompt_path || agent.report_path, "Task metadata unavailable.")),
        el("div", "chips", [
          statusPill(agent.status),
          el("span", "chip", `profile ${safe(profile.profile_id || agent.profile, "unavailable")}`),
          el("span", "chip", `spawned by ${safe(agent.spawned_by || agent.parent_agent_id, "unavailable")}`),
          el("span", "chip", `workstream ${safe(agent.workstream, "unavailable")}`),
          el("span", "chip", `provider ${safe(agent.provider, "unavailable")}`),
        ]),
      ]),
      el("div", "agent-toolbar", [
        button("icon-button", "Back to agents", svgIcon("back"), () => setScreen("agents")),
        button("icon-button", "Refresh Agent detail", svgIcon("refresh"), () => loadAgentDetail(state.selectedAgentId)),
        button("icon-button", "Agent logs", svgIcon("tail"), () => openModal("agentLogs")),
        button("icon-button", "Agent report", svgIcon("status"), () => openModal("agentReport")),
        button("icon-button", "Capability review", svgIcon("capability"), () => openModal("agentCapability")),
        button("icon-button danger", "Cancel agent preview", svgIcon("cancel"), () => openModal("agentCancel")),
      ]),
      detail && detail.empty_states && detail.empty_states.report ? el("div", "agent-detail-note", "No report yet") : null,
    ]);
  }

  function findAgent(agentId) {
    const agents = Array.isArray(currentRun().agents) ? currentRun().agents : [];
    return agents.find((agent) => agent.agent_id === agentId);
  }

  function fileScopeSubtitle(agent, detail) {
    const assigned = Array.isArray(agent.assigned_files) ? agent.assigned_files.length : 0;
    const changed = detail && Array.isArray(detail.changed_files) ? detail.changed_files.length : 0;
    return `${assigned} assigned / ${changed} changed`;
  }

  function renderAgentFiles(agent, detail) {
    const assigned = Array.isArray(agent.assigned_files) ? agent.assigned_files : [];
    const roots = Array.isArray(agent.allowed_write_roots) ? agent.allowed_write_roots : [];
    const changed = detail && Array.isArray(detail.changed_files) ? detail.changed_files : [];
    return el("div", "agent-files", [
      el("div", "section-kicker", "Assigned files"),
      assigned.length ? assigned.map((file) => fileRow("scope", file)) : empty("No assigned file scope recorded."),
      el("div", "section-kicker", "Allowed roots"),
      roots.length ? roots.map((root) => fileRow("root", root)) : empty("No allowed write roots recorded."),
      el("div", "section-kicker", "Changed files"),
      changed.length ? changed.map((file) => fileRow(file.status || file.change_type || "changed", file.path || file.file || file.name || JSON.stringify(file), file)) : empty("No changed files recorded."),
    ]);
  }

  function fileRow(kind, path, record) {
    const additions = record && Number.isFinite(Number(record.additions)) ? `+${record.additions}` : "";
    const deletions = record && Number.isFinite(Number(record.deletions)) ? `-${record.deletions}` : "";
    return el("div", "file-row", [
      el("span", `file-kind ${tone(kind)}`, safe(kind, "file")),
      el("span", "", safe(path, "unavailable")),
      additions || deletions ? el("span", "muted", `${additions} ${deletions}`.trim()) : null,
    ]);
  }

  function heartbeatSubtitle(detail) {
    const samples = detail && Array.isArray(detail.heartbeat_samples) ? detail.heartbeat_samples : [];
    return samples.length ? `${samples.length} sample(s) from runtime heartbeat evidence` : "No heartbeat samples recorded";
  }

  function renderHeartbeatMini(detail) {
    const samples = detail && Array.isArray(detail.heartbeat_samples) ? detail.heartbeat_samples.slice(-40) : [];
    if (!samples.length) return empty("No heartbeat samples recorded.");
    const ok = samples.filter((sample) => tone(sample.status) === "run" || tone(sample.status) === "ok").length;
    const late = samples.filter((sample) => tone(sample.status) === "warn").length;
    const miss = samples.length - ok - late;
    return el("div", "panel-body", [
      el("div", "hb-mini", samples.map((sample, index) => {
        const t = tone(sample.status);
        return el("span", `tick ${t === "warn" ? "late" : t === "danger" ? "miss" : ""}`, "", {
          title: `${fmtDate(sample.ts)} ${safe(sample.status, "heartbeat")}`,
          style: `height:${36 + (index % 5) * 12}%`,
        });
      })),
      el("div", "hb-legend", [
        el("span", "", safe(fmtDate(samples[0] && samples[0].ts), "start unavailable")),
        el("span", "ok-text", `${ok} ok`),
        el("span", "warn-text", `${late} late`),
        el("span", "danger-text", `${miss} miss`),
        el("span", "", safe(fmtDate(samples[samples.length - 1] && samples[samples.length - 1].ts), "now unavailable")),
      ]),
    ]);
  }

  function renderAgentMetadata(agent, detail) {
    const metadata = detail && detail.metadata ? detail.metadata : {};
    const rows = [
      ["id", agent.agent_id],
      ["role", agent.role],
      ["spawned by", metadata.spawned_by],
      ["spawned at", metadata.spawned_at],
      ["workstream", agent.workstream],
      ["capability", metadata.capability_profile],
      ["permission scope", JSON.stringify(metadata.permission_scope || { assigned_files: agent.assigned_files || [], allowed_write_roots: agent.allowed_write_roots || [] })],
      ["provider", agent.provider],
      ["prompt", agent.prompt_path],
      ["report", agent.report_path],
      ["launch evidence", metadata.launch_evidence],
    ];
    return el("dl", "kv panel-body", rows.map(([key, value]) => [
      el("dt", "", key),
      el("dd", "", safe(value, "unavailable")),
    ]));
  }

  function capabilitySubtitle(agent, detail) {
    const profile = agent.capability_profile || {};
    const grants = detail && Array.isArray(detail.capability_grants) ? detail.capability_grants.length : 0;
    return `${safe(profile.profile_id || agent.profile, "profile unavailable")} / ${grants} grant(s)`;
  }

  function renderAgentCapabilities(agent, detail) {
    const grants = detail && Array.isArray(detail.capability_grants) ? detail.capability_grants : [];
    const exercised = detail && Array.isArray(detail.capabilities_exercised) ? detail.capabilities_exercised : [];
    const escalations = detail && Array.isArray(detail.capability_escalations) ? detail.capability_escalations : [];
    return el("div", "panel-body", [
      el("div", "chips", grants.length ? grants.map((grant) => el("span", "chip", `${grant.capability}:${safe(grant.mode, "mode")}`)) : [el("span", "chip", "No capability grant recorded")]),
      el("div", "section-kicker", "Exercised"),
      exercised.length ? renderGenericRows(exercised) : empty("No exercised capabilities recorded."),
      el("div", "section-kicker", "Escalations"),
      escalations.length ? renderGenericRows(escalations) : empty("No capability escalations recorded."),
      button("btn-sm", "Open capability review preview", "Review capability grant", () => openModal("agentCapability")),
    ]);
  }

  function runProfile(profile) {
    if (!profile || typeof profile !== "object") return {};
    const high = [];
    const modes = {
      network_access: "none",
      package_install: "deny",
      dependency_resolution: "allow-existing-lockfiles",
      docker_socket: "deny",
      service_start: "deny",
      test_execution: "allow-listed",
      runtime_state_write: "report-only",
      github_issue_create: "deny",
    };
    Object.keys(profile.capabilities || {}).forEach((key) => {
      const mode = profile.capabilities[key] && profile.capabilities[key].mode;
      if (mode && modes[key] && mode !== modes[key]) high.push({ capability: key, mode });
    });
    return { high_risk_capabilities: high };
  }

  function renderDecisions() {
    return panel("Decisions", "pending operator choices from status and alert surfaces", renderDecisionRows(decisions()));
  }

  function renderDecisionRows(rows) {
    if (!rows.length) return empty("No pending decisions.");
    return el("div", "row-list", rows.map((row) => {
      const node = el("div", "decision-row clickable", [
      el("span", `decision-stripe ${row.recommended ? "warn" : ""}`),
      el("div", "", [
        el("div", "row-title", safe(row.question, "Decision required")),
        el("div", "row-meta", [
          safe(row.id, "decision"),
          row.workstream ? ` / ${row.workstream}` : "",
          row.recommended ? ` / recommended ${row.recommended}` : "",
        ]),
      ]),
      statusPill("pending"),
    ], { role: "button", tabindex: "0", title: `Open decision preview for ${safe(row.id, "decision")}` });
      node.addEventListener("click", () => openModal("decision", row));
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openModal("decision", row);
        }
      });
      return node;
    }));
  }

  function renderCapabilities() {
    const run = currentRun();
    const caps = run.capability_profiles || {};
    const rows = Array.isArray(caps.agents) ? caps.agents : [];
    const pending = Array.isArray(caps.pending_decisions) ? caps.pending_decisions : [];
    const escalations = Array.isArray(caps.pending_escalations) ? caps.pending_escalations : [];
    const violations = Array.isArray(caps.violations) ? caps.violations : [];
    return el("div", "grid", [
      panel("Capability Profiles", `${pending.length} pending decision(s), ${escalations.length} escalation(s), ${violations.length} violation(s)`, renderCapabilityRows(rows)),
      el("div", "grid two", [
        panel("Pending Capability Decisions", "capability escalation requests", pending.length ? renderCapabilityRequestRows(pending, "pending") : empty("No pending capability decisions.")),
        panel("Capability Violations", "unresolved protocol overreach", violations.length ? renderCapabilityRequestRows(violations, "violation") : empty("No capability violations reported.")),
      ]),
    ]);
  }

  function renderCapabilityRows(rows) {
    if (!rows.length) return empty("No capability profile summaries reported.");
    return el("div", "row-list", rows.map((row) => {
      const node = el("div", "cap-row clickable", [
      el("div", "", [
        el("div", "cap-id", safe(row.profile_id, "profile")),
        el("div", "row-meta", safe(row.agent_id, "agent")),
      ]),
      el("div", "chips", [
        row.role ? el("span", "chip", row.role) : null,
        row.workstream ? el("span", "chip", row.workstream) : null,
        ...(row.high_risk_capabilities || []).map((item) => el("span", "chip warn", `${item.capability}:${item.mode}`)),
      ]),
      statusPill(row.status),
    ], { role: "button", tabindex: "0", title: `Open capability review preview for ${safe(row.agent_id || row.profile_id, "profile")}` });
      node.addEventListener("click", () => openModal("capability", row));
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openModal("capability", row);
        }
      });
      return node;
    }));
  }

  function renderCapabilityRequestRows(rows, kind) {
    return el("div", "row-list", rows.map((row) => {
      const node = el("div", "alert-row clickable", [
        el("span", `dot ${tone(row.status || row.type || kind)}`),
        el("div", "", [
          el("div", "row-title", safe(row.summary || row.reason || row.violation || row.capability || row.decision_id, "capability record")),
          el("div", "row-meta", [
            safe(row.agent_id || row.profile_id || row.actor, "agent unavailable"),
            row.workstream ? ` / ${row.workstream}` : "",
          ]),
        ]),
        statusPill(row.status || kind),
      ], { role: "button", tabindex: "0", title: "Open capability review preview" });
      node.addEventListener("click", () => openModal("capability", row));
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openModal("capability", row);
        }
      });
      return node;
    }));
  }

  function renderValidators() {
    const rows = validators();
    return panel("Validators", "registered validation agents and current status", rows.length ? el("div", "row-list", rows.map((agent) => el("div", "validator-row", [
      el("span", `dot ${tone(agent.status)}`),
      el("div", "", [
        el("div", "row-title", safe(agent.agent_id, "validator")),
        el("div", "row-meta", safe(agent.report_path || agent.workstream, "no report path")),
      ]),
      el("span", "chip", safe(agent.profile, "profile")),
      statusPill(agent.status),
    ]))) : empty("No validator agents registered."));
  }

  function renderAlerts() {
    const alerts = currentAlerts();
    return panel("Alerts", "material run, lifecycle, protocol, and blocker alerts", renderAlertRows(alerts));
  }

  function renderAlertRows(alerts) {
    if (!alerts.length) return empty("No material alerts.");
    return el("div", "row-list", alerts.map((alert) => el("div", "alert-row", [
      el("span", `dot ${tone(alert.severity || alert.status || alert.type)}`),
      el("div", "", [
        el("div", "row-title", safe(alert.summary || alert.question || alert.type, "alert")),
        el("div", "row-meta", [
          safe(alert.id || alert.decision_id || alert.blocker_id || alert.violation, "alert"),
          alert.agent_id ? ` / ${alert.agent_id}` : "",
          alert.workstream ? ` / ${alert.workstream}` : "",
        ]),
      ]),
      alert.status ? statusPill(alert.status) : null,
    ])));
  }

  function renderHistory() {
    const all = historyRows();
    const rows = filteredHistoryRows();
    const selected = selectedCompareRuns();
    const search = el("input", "search-input history-search", null, {
      type: "search",
      placeholder: "Filter runs, repo, plan, status, reason...",
      "aria-label": "Filter run history",
    });
    search.value = state.historySearch;
    search.addEventListener("input", () => {
      state.historySearch = search.value;
      render();
    });
    const body = el("div", "history-screen", [
      el("div", "history-toolbar", [
        search,
        button("btn-sm", "Clear history filter", "Clear", () => {
          state.historySearch = "";
          render();
        }),
        button("btn-sm", "Export visible rows as CSV", "Export CSV", exportHistoryCsv),
        el("span", "history-count", `${rows.length} of ${all.length} run(s)`),
      ]),
      rows.length ? renderHistoryTable(rows) : empty(all.length ? "No runs match the current filter." : "No run history returned by /api/history."),
      selected.length === 2 ? renderCompareDrawer(selected[0], selected[1]) : empty("Select two rows to compare duration, workers, decisions, files, tests, and outcome."),
    ]);
    return panel("Run History", "search, export, and compare loaded read-only runs", body);
  }

  function historyRows() {
    return currentHistoryRows();
  }

  function filteredHistoryRows() {
    const query = state.historySearch.trim().toLowerCase();
    const rows = historyRows();
    if (!query) return rows;
    return rows.filter((run) => historySearchText(run).includes(query));
  }

  function historySearchText(run) {
    return [
      run.run_id,
      run.short_id,
      run.repo,
      run.repo_name,
      run.plan_id,
      run.objective,
      run.status,
      run.terminal_reason,
      run.worker_count,
      run.decision_count,
    ].map((item) => safe(item, "")).join(" ").toLowerCase();
  }

  function renderHistoryTable(rows) {
    return el("div", "history-table-wrap", [
      el("table", "rh-table", [
        el("thead", "", el("tr", "", [
          el("th", "", "Compare"),
          el("th", "", "Run"),
          el("th", "", "Repo / plan"),
          el("th", "", "Started"),
          el("th", "", "Duration"),
          el("th", "", "Workers"),
          el("th", "", "Decisions"),
          el("th", "", "Tests"),
          el("th", "", "Outcome"),
        ])),
        el("tbody", "", rows.map(renderHistoryRow)),
      ]),
    ]);
  }

  function renderHistoryRow(run) {
    const selected = state.selectedCompareRunIds.includes(run.run_id);
    const input = el("input", "", null, { type: "checkbox", "aria-label": `Compare ${safe(run.run_id, "run")}` });
    input.checked = selected;
    input.addEventListener("change", () => toggleCompareRun(run.run_id));
    return el("tr", `rh-row ${selected ? "picked" : ""}`, [
      el("td", "", input),
      el("td", "", [
        el("span", "history-id", safe(run.short_id || shortId(run.run_id), "n/a")),
        run.run_id === currentRun().run_id ? el("span", "chip current-chip", "current") : null,
      ]),
      el("td", "", [
        el("div", "row-title", safe(run.repo_name || run.repo, "repo unavailable")),
        el("div", "row-meta", `${safe(run.plan_id, "plan not exposed")} / ${safe(run.objective, "No objective recorded.")}`),
      ]),
      el("td", "mono", fmtDate(run.started_at || run.created_at)),
      el("td", "mono", formatDuration(run.duration_ms)),
      el("td", "mono", valueOrUnavailable(run.worker_count)),
      el("td", "mono", valueOrUnavailable(run.decision_count)),
      el("td", "mono", formatTests(run)),
      el("td", "", [
        statusPill(run.status),
        run.terminal_reason ? el("div", "row-meta danger-text", run.terminal_reason) : null,
      ]),
    ]);
  }

  function toggleCompareRun(runId) {
    const current = state.selectedCompareRunIds.filter((id) => historyRows().some((run) => run.run_id === id));
    if (current.includes(runId)) {
      state.selectedCompareRunIds = current.filter((id) => id !== runId);
    } else if (current.length < 2) {
      state.selectedCompareRunIds = current.concat([runId]);
    } else {
      state.selectedCompareRunIds = [current[1], runId];
    }
    render();
  }

  function selectedCompareRuns() {
    return state.selectedCompareRunIds.map((id) => historyRows().find((run) => run.run_id === id)).filter(Boolean);
  }

  function renderCompareDrawer(left, right) {
    const fields = [
      ["duration", left.duration_ms, right.duration_ms, formatDuration, true],
      ["workers", left.worker_count, right.worker_count, valueOrUnavailable, true],
      ["decisions", left.decision_count, right.decision_count, valueOrUnavailable, true],
      ["files changed", left.files_changed_count, right.files_changed_count, valueOrUnavailable, true],
      ["tests", testsRatio(left), testsRatio(right), (value) => valueOrUnavailable(value), false],
      ["status", left.status, right.status, (value) => safe(value, "unavailable"), false],
      ["outcome", left.terminal_reason, right.terminal_reason, (value) => safe(value, "not exposed"), false],
    ];
    return el("div", "rh-compare", [
      el("div", "rh-compare-h", [
        el("span", "", "compare"),
        el("span", "mono", `${safe(left.short_id || shortId(left.run_id), "left")} <-> ${safe(right.short_id || shortId(right.run_id), "right")}`),
        el("span", "history-count", "loaded data only"),
        button("btn-sm", "Clear comparison", "Clear", () => {
          state.selectedCompareRunIds = [];
          render();
        }),
      ]),
      el("div", "rh-compare-grid", fields.map(([key, a, b, formatter, numeric]) => [
        el("div", "rh-compare-k", key),
        el("div", "rh-compare-v mono", formatter(a)),
        el("div", "rh-compare-arrow", "->"),
        el("div", "rh-compare-v mono", formatter(b)),
        el("div", `rh-compare-delta ${deltaTone(a, b)}`, numeric ? numericDelta(a, b) : changeDelta(a, b)),
      ])),
    ]);
  }

  function exportHistoryCsv() {
    const headers = ["run_id", "repo", "plan_id", "objective", "started_at", "duration_ms", "worker_count", "decision_count", "files_changed_count", "tests_passed", "tests_total", "status", "terminal_reason"];
    const lines = [headers.join(",")].concat(filteredHistoryRows().map((run) => headers.map((key) => csvCell(run[key])).join(",")));
    const blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `dispatch-history-${fmtDate(new Date()).replace(/[^0-9]/g, "").slice(0, 14) || "export"}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function csvCell(value) {
    const text = safe(value, "");
    return `"${text.replace(/"/g, '""')}"`;
  }

  function testsRatio(run) {
    if (!Number.isFinite(Number(run.tests_total))) return null;
    return `${valueOrUnavailable(run.tests_passed)}/${valueOrUnavailable(run.tests_total)}`;
  }

  function formatTests(run) {
    const ratio = testsRatio(run);
    return ratio || "not exposed";
  }

  function valueOrUnavailable(value) {
    return value === null || value === undefined || value === "" ? "not exposed" : String(value);
  }

  function formatDuration(ms) {
    if (!Number.isFinite(Number(ms))) return "not exposed";
    const total = Math.max(0, Math.round(Number(ms) / 1000));
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const seconds = total % 60;
    return [hours, minutes, seconds].map((part) => String(part).padStart(2, "0")).join(":");
  }

  function numericDelta(left, right) {
    if (!Number.isFinite(Number(left)) || !Number.isFinite(Number(right))) return "unavailable";
    const delta = Number(right) - Number(left);
    if (delta === 0) return "no change";
    return `${delta > 0 ? "+" : ""}${delta}`;
  }

  function changeDelta(left, right) {
    if (left === null || left === undefined || right === null || right === undefined) return "unavailable";
    return String(left) === String(right) ? "same" : "changed";
  }

  function deltaTone(left, right) {
    if (!Number.isFinite(Number(left)) || !Number.isFinite(Number(right))) return "";
    const delta = Number(right) - Number(left);
    return delta > 0 ? "warn-text" : delta < 0 ? "ok-text" : "";
  }

  function renderLogs() {
    const logs = state.data.logs || {};
    const stdout = splitLines(logs.stdout);
    const stderr = splitLines(logs.stderr);
    return el("div", "grid two", [
      panel("Coordinator stdout", safe(logs.stdout_path, "stdout"), renderLogLines(stdout, "out")),
      panel("Coordinator stderr", safe(logs.stderr_path, "stderr"), renderLogLines(stderr, "err")),
    ]);
  }

  function splitLines(text) {
    return safe(text, "").split(/\r?\n/).filter(Boolean).slice(-120);
  }

  function renderLogLines(lines, source) {
    if (!lines.length) return empty("No log lines.");
    return el("div", "terminal", lines.map((line, index) => el("div", "log-line", [
      el("span", "log-time", String(index + 1).padStart(4, "0")),
      el("span", "log-source", source),
      el("span", "log-message", line),
    ])), { "data-scroll-key": `terminal:${state.screen}:${state.modal || "inline"}:${state.selectedAgentId || "run"}:${source}` });
  }

  function renderGenericRows(rows) {
    return el("div", "row-list", rows.map((row) => el("div", "alert-row", [
      el("span", `dot ${tone(row.status || row.type || row.violation)}`),
      el("div", "", [
        el("div", "row-title", safe(row.summary || row.reason || row.violation || row.capability || row.decision_id, "record")),
        el("div", "row-meta", JSON.stringify(row)),
      ]),
    ])));
  }

  function renderEventTail() {
    const events = allEvents().slice(-80);
    const filtered = filterTailEvents(events);
    const attrs = state.tailCollapsed ? {} : { style: `--tail-height: ${clampTailHeight(state.tailHeight)}px` };
    return el("section", `footer-tail ${state.tailCollapsed ? "collapsed" : ""}`, [
      state.tailCollapsed ? null : renderTailResizeHandle(),
      el("div", "tail", [
        el("div", "tail-head", [
          el("span", "tail-title", [
            el("span", `dot ${state.refreshing ? "run" : "ok"}`),
            el("span", "", state.tailCollapsed ? "event tail collapsed" : "event tail"),
            el("span", "muted", `${filtered.length}/${events.length} event(s)`),
          ]),
          state.tailCollapsed ? el("span", "tail-latest", latestTailLabel(filtered)) : null,
          state.tailCollapsed ? null : renderTailFilters(),
          button("tail-toggle", state.tailCollapsed ? "Expand event tail" : "Collapse event tail", state.tailCollapsed ? "▲" : "▼", () => {
            state.tailCollapsed = !state.tailCollapsed;
            render();
          }),
        ]),
        state.tailCollapsed ? null : el("div", "tail-body", filtered.length ? filtered.map((event) => el("div", "event", [
          el("span", "event-time", fmtTime(event.ts)),
          el("span", "event-type", safe(event.type, "event")),
          el("span", "event-message", eventMessage(event)),
        ])) : empty(events.length ? "No events match the current filter." : "No events loaded."), { "data-scroll-key": `event-tail:${state.tailFilter}` }),
      ]),
    ], attrs);
  }

  function renderTailResizeHandle() {
    const handle = el("div", "tail-resize", null, {
      role: "separator",
      tabindex: "0",
      "aria-label": "Resize event tail",
      "aria-orientation": "horizontal",
      title: "Drag to resize event tail",
    });
    handle.addEventListener("pointerdown", startTailResize);
    handle.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
      event.preventDefault();
      const delta = event.key === "ArrowUp" ? 20 : -20;
      state.tailHeight = clampTailHeight((state.tailHeight || DEFAULT_TAIL_HEIGHT) + delta);
      saveTailHeight(state.tailHeight);
      render();
    });
    return handle;
  }

  function startTailResize(event) {
    if (state.tailCollapsed) return;
    event.preventDefault();
    const footer = event.currentTarget.closest(".footer-tail");
    const startY = event.clientY;
    const startHeight = footer ? footer.getBoundingClientRect().height : (state.tailHeight || DEFAULT_TAIL_HEIGHT);
    document.body.classList.add("tail-resizing");
    const onMove = (moveEvent) => {
      state.tailHeight = clampTailHeight(startHeight + (startY - moveEvent.clientY));
      if (footer) footer.style.setProperty("--tail-height", `${state.tailHeight}px`);
    };
    const onEnd = () => {
      document.body.classList.remove("tail-resizing");
      saveTailHeight(state.tailHeight);
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onEnd);
      document.removeEventListener("pointercancel", onEnd);
    };
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onEnd);
    document.addEventListener("pointercancel", onEnd);
  }

  function renderTailFilters() {
    return el("div", "tail-filters", ["all", "ok", "warn", "error", "coord", "worker", "runtime"].map((filter) => button(
      `tail-filter ${state.tailFilter === filter ? "active" : ""}`,
      `Filter event tail: ${filter}`,
      filter,
      () => {
        state.tailFilter = filter;
        render();
      },
    )));
  }

  function filterTailEvents(events) {
    const filter = state.tailFilter || "all";
    if (filter === "all") return events;
    return events.filter((event) => tailEventTokens(event).includes(filter));
  }

  function tailEventTokens(event) {
    const text = [event.type, event.actor, event.workstream, eventMessage(event)].map((item) => safe(item, "").toLowerCase()).join(" ");
    const tokens = [];
    if (text.includes("fail") || text.includes("error") || text.includes("violation")) tokens.push("error");
    else if (text.includes("block") || text.includes("pending") || text.includes("decision") || text.includes("late")) tokens.push("warn");
    else tokens.push("ok");
    if (text.includes("coordinator")) tokens.push("coord");
    if (text.includes("worker")) tokens.push("worker");
    if (text.includes("dispatch-engine") || text.includes("runtime") || text.includes("supervisor")) tokens.push("runtime");
    return tokens;
  }

  function latestTailLabel(events) {
    const latest = events[events.length - 1];
    return latest ? `latest ${fmtTime(latest.ts)}` : "latest -";
  }

  function renderSettingsControl() {
    return el("div", "settings-anchor", [
      button(`icon-button settings-toggle ${state.settingsOpen ? "active" : ""}`, "Settings", svgIcon("settings"), () => {
        state.settingsOpen = !state.settingsOpen;
        state.modal = null;
        render();
      }),
      state.settingsOpen ? renderSettingsPopover() : null,
    ]);
  }

  function renderSettingsPopover() {
    return el("div", "settings-popover", [
      el("div", "popover-head", [
        el("span", "", "Theme"),
        el("span", "hint", "applies instantly"),
      ]),
      THEME_OPTIONS.map((theme) => button(`theme-row ${state.prefs.theme === theme.id ? "active" : ""}`, theme.name, [
        el("span", "theme-swatch", [
          el("span", "", "", { style: `background:${theme.swatch[0]}` }),
          el("span", "", "", { style: `background:${theme.swatch[1]}` }),
        ]),
        el("span", "theme-meta", [
          el("span", "theme-name", theme.name),
          el("span", "theme-desc", theme.desc),
        ]),
        el("span", "theme-check", state.prefs.theme === theme.id ? svgIcon("check") : ""),
      ], () => setTheme(theme.id))),
      el("div", "popover-head density-head", [
        el("span", "", "Density"),
        el("span", "hint", "UI scale"),
      ]),
      el("div", "zoom-row", ZOOMS.map((zoom) => button(
        `zoom-button ${Math.abs(state.prefs.zoom - zoom) < 0.001 ? "active" : ""}`,
        `${Math.round(zoom * 100)}% density`,
        `${Math.round(zoom * 100)}%`,
        () => setZoom(zoom),
      ))),
    ], { role: "dialog", "aria-label": "Dashboard settings" });
  }

  function renderModal() {
    if (!state.modal) return null;
    const specs = {
      keyboard: { title: "Keyboard Shortcuts", sub: "shell navigation", body: renderKeyboardHelp() },
      status: { title: "Status JSON", sub: "/api/status", body: renderJsonBlock(currentRun()), footer: renderReadOnlyFooter("Status data is fetched with GET /api/status.") },
      tail: { title: "Coordinator Tail", sub: "/api/tail and /api/logs/coordinator", body: renderTailModal(), footer: renderReadOnlyFooter("Tail data is fetched with GET endpoints only.") },
      cancel: { title: "Cancel Preview", sub: "read-only command preview", body: renderCancelPreview(), footer: renderPreviewFooter("Ask interactive Codex to run the command after reviewing the preview."), tone: "danger" },
      runs: { title: "Run Selector", sub: "recent runs are read-only in this dashboard", body: renderRunSwitcher() },
      runPreview: { title: "Open Run Preview", sub: "safe run switch command", body: renderRunOpenPreview(state.modalContext), footer: renderPreviewFooter("Ask interactive Codex to start or reuse that run's dashboard service.") },
      decision: { title: "Decision Preview", sub: safe(state.modalContext && state.modalContext.id, "pending decision"), body: renderDecisionModal(state.modalContext), footer: renderPreviewFooter("Use chat-mediated execution for the selected option.") },
      capability: { title: "Capability Review", sub: "read-only scope and command preview", body: renderCapabilityModal(state.modalContext), footer: renderPreviewFooter("Capability grant and deny previews are not executed by the dashboard.") },
      agentLogs: { title: "Agent Logs", sub: "read-only stdout/stderr preview", body: renderAgentLogsModal(), footer: renderReadOnlyFooter("Agent logs are loaded from /api/agent/<agent-id>.") },
      agentReport: { title: "Agent Report", sub: "report JSON or empty state", body: renderAgentReportModal(), footer: renderReadOnlyFooter("Report JSON is displayed without writing run state.") },
      agentCapability: { title: "Capability Review", sub: "selected agent capability grant preview", body: renderAgentCapabilityModal(), footer: renderPreviewFooter("Ask interactive Codex to review or change capability scope.") },
      agentCancel: { title: "Cancel Agent Preview", sub: "read-only command preview", body: renderAgentCancelPreview(), footer: renderPreviewFooter("Agent-specific cancellation is presented as a chat-mediated preview."), tone: "danger" },
    };
    const spec = specs[state.modal];
    if (!spec) return null;
    return el("div", "modal-bg", [
      el("section", `modal ${spec.tone || ""}`, [
        el("div", "modal-head", [
          el("div", "", [
            el("div", "modal-title", spec.title),
            el("div", "modal-sub", spec.sub),
          ]),
          button("modal-close", "Close", "x", closeModal),
        ]),
        el("div", "modal-body", spec.body, { "data-scroll-key": `modal-body:${state.modal}:${state.selectedAgentId || ""}` }),
        spec.footer ? el("div", "modal-footer", spec.footer) : null,
      ], { role: "dialog", "aria-modal": "true", "aria-label": spec.title }),
    ]);
  }

  function renderReadOnlyFooter(message) {
    return [
      el("span", "modal-note", message),
      button("btn-sm", "Close modal", "Close", closeModal),
    ];
  }

  function renderPreviewFooter(message) {
    return [
      el("span", "modal-note", message),
      button("btn-sm", "Close modal", "Close", closeModal),
    ];
  }

  function renderKeyboardHelp() {
    return el("div", "shortcut-grid", SHORTCUTS.map(([key, label]) => el("div", "shortcut-row", [
      el("kbd", "", key),
      el("span", "", label),
    ])));
  }

  function renderJsonBlock(value) {
    return el("pre", "json-block", JSON.stringify(value || {}, null, 2));
  }

  function renderTailModal() {
    const logs = state.data.logs || {};
    const rows = [
      ...allEvents().slice(-24).map((event) => ({
        time: fmtTime(event.ts),
        prefix: safe(event.type, "event"),
        message: eventMessage(event),
        source: "event",
      })),
      ...logEntries(logs.stdout, "out").slice(-36).map((line) => Object.assign({}, line, { prefix: `out:${line.prefix}` })),
      ...logEntries(logs.stderr, "err").slice(-36).map((line) => Object.assign({}, line, { prefix: `err:${line.prefix}` })),
    ].slice(-96);
    return el("div", "preview-stack", [
      el("div", "impact-grid", [
        impactTile("events", allEvents().length),
        impactTile("stdout", splitLines(logs.stdout).length),
        impactTile("stderr", splitLines(logs.stderr).length),
      ]),
      rows.length ? el("div", "terminal modal-terminal", rows.map(renderTerminalEntry).concat([renderTerminalCaret()]), { "data-scroll-key": "modal-terminal:tail" }) : empty("No coordinator tail data loaded from /api/tail or /api/logs/coordinator."),
    ]);
  }

  function renderCancelPreview() {
    const run = currentRun();
    const runId = safe(run.run_id, "<run-id>");
    const reason = state.modalForm.reason || "<reason>";
    const agents = Array.isArray(run.agents) ? run.agents : [];
    const activeAgents = agents.filter((agent) => !["completed", "completed_with_concerns", "failed", "cancelled"].includes(safe(agent.status, "").toLowerCase()));
    const command = `python3 scripts/de.py cancel ${shellQuote(repoPath())} --run-id ${shellQuote(runId)} --reason ${shellQuote(reason)} --json`;
    return el("div", "preview-stack", [
      el("p", "", "This dashboard is read-only. Ask interactive Codex to run the cancel command if you decide to stop the run."),
      formRow("Reason", modalInput("reason", { placeholder: "Short cancellation reason" }), "Required before a real operator request should be sent."),
      el("div", "check-grid", [
        checkboxRow("includeToolCalls", "Include in-flight tool calls", "preview impact only"),
        checkboxRow("keepArtifacts", "Keep artifacts and evidence", "Dispatch Engine cancellation preserves evidence"),
      ]),
      el("div", "impact-grid", [
        impactTile("agents", activeAgents.length),
        impactTile("workstreams", workstreams().length),
        impactTile("decisions", decisions().length),
      ]),
      commandBlock(command, "Exact command preview"),
      empty("Opening this modal does not mutate Dispatch Engine state."),
    ]);
  }

  function impactTile(label, value) {
    return el("div", "impact-tile", [
      el("span", "", label),
      el("strong", "", safe(value, "unavailable")),
    ]);
  }

  function selectedAgentDetail() {
    return state.selectedAgentId ? state.data.agentDetails[state.selectedAgentId] : null;
  }

  function decisionOptions(decision) {
    if (decision && Array.isArray(decision.options) && decision.options.length) {
      return decision.options.map((option, index) => {
        if (typeof option === "string") return { id: option, label: option };
        return {
          id: option.id || option.option_id || option.value || `option-${index + 1}`,
          label: option.label || option.title || option.summary || option.id || `Option ${index + 1}`,
          rationale: option.rationale || option.reason,
          risk: option.risk,
          pros: option.pros,
          cons: option.cons,
        };
      });
    }
    const recommended = decision && decision.recommended ? safe(decision.recommended, "") : "";
    return [
      recommended ? { id: recommended, label: `Use recommended option: ${recommended}` } : null,
      { id: "defer", label: "Defer and ask for more context", previewOnly: true },
      { id: "reject", label: "Reject current request", previewOnly: true },
    ].filter(Boolean);
  }

  function renderDecisionModal(decision) {
    const row = decision || {};
    const id = safe(row.id || row.decision_id, "<decision-id>");
    const options = decisionOptions(row);
    const selected = state.modalForm.option || (options[0] && options[0].id) || "";
    const selectedOption = options.find((option) => option.id === selected) || options[0] || {};
    const command = selectedOption.previewOnly
      ? `Ask interactive Codex to ${selectedOption.id} decision ${id}; no dashboard command is executed.`
      : `python3 scripts/de.py resolve-decision ${shellQuote(repoPath())} --id ${shellQuote(id)} --option ${shellQuote(selected || "<option-id>")} --json`;
    return el("div", "preview-stack", [
      el("dl", "kv modal-kv", [
        kv("decision id", id),
        kv("raised by", row.raised_by || row.actor || row.agent_id || "unavailable"),
        kv("heartbeat age", row.heartbeat_age || row.unanswered_heartbeats || "unavailable"),
        kv("workstream", row.workstream || "unavailable"),
        kv("source", row.source || row.type || "unavailable"),
      ]),
      panel("Question", "operator input required", el("div", "panel-body", safe(row.question, "Decision question unavailable."))),
      panel("Reasoning", "live runtime field or explicit gap", el("div", "panel-body", safe(row.reason || row.rationale, "Reasoning not exposed by runtime state."))),
      el("div", "option-list", options.map((option) => decisionOptionRow(option, selected))),
      el("div", "impact-grid", [
        impactTile("risk", row.risk || selectedOption.risk || "unavailable"),
        impactTile("files", Array.isArray(row.affected_files) ? row.affected_files.length : "not exposed"),
        impactTile("fallback", row.autonomous_fallback || row.autonomous_countdown || "unavailable"),
      ]),
      formRow("Audit note", modalTextArea("auditNote", { placeholder: "Optional note to include in the chat-mediated request" }), "Stored only in browser memory for this preview."),
      selectedOption.rationale || selectedOption.pros || selectedOption.cons ? panel("Option notes", "provided by runtime decision metadata", el("div", "panel-body", [
        selectedOption.rationale ? el("p", "", selectedOption.rationale) : null,
        selectedOption.pros ? el("p", "", `Pros: ${safe(Array.isArray(selectedOption.pros) ? selectedOption.pros.join(", ") : selectedOption.pros, "")}`) : null,
        selectedOption.cons ? el("p", "", `Cons: ${safe(Array.isArray(selectedOption.cons) ? selectedOption.cons.join(", ") : selectedOption.cons, "")}`) : null,
      ])) : empty("Option rationale, pros, and cons are not exposed by runtime state."),
      commandBlock(command, selectedOption.previewOnly ? "Preview-only chat action" : "Exact command preview"),
    ]);
  }

  function decisionOptionRow(option, selected) {
    const input = el("input", "", null, { type: "radio", name: "decision-option", value: option.id });
    input.checked = option.id === selected;
    input.addEventListener("change", () => updateModalForm("option", option.id));
    return el("label", `option-row ${input.checked ? "active" : ""}`, [
      input,
      el("span", "", [
        el("strong", "", safe(option.label || option.id, "option")),
        option.previewOnly ? el("small", "", "preview only") : null,
      ]),
    ]);
  }

  function kv(key, value) {
    return [
      el("dt", "", key),
      el("dd", "", safe(value, "unavailable")),
    ];
  }

  function renderCapabilityModal(record) {
    const detail = selectedAgentDetail();
    const agent = record && record.agent ? record.agent : detail && detail.agent ? detail.agent : record || {};
    const profile = agent.capability_profile || record && record.capability_profile || {};
    const capabilityName = safe(record && (record.capability || record.violation || record.decision_id) || agent.agent_id || agent.profile_id, "capability request");
    const violations = capabilityViolationsFor(agent.agent_id || record && record.agent_id);
    const grantCommand = `Ask interactive Codex to review capability grant ${shellQuote(capabilityName)} for ${shellQuote(agent.agent_id || record && record.agent_id || "<agent-id>")} with TTL ${shellQuote(state.modalForm.ttl || "30m")}.`;
    const violation = record && (record.violation || record.type === "protocol_violation" || record.type === "capability_violation");
    const auditCommand = violation
      ? `python3 scripts/de.py resolve-protocol-violation ${shellQuote(repoPath())} --run-id ${shellQuote(safe(currentRun().run_id, "<run-id>"))} --violation ${shellQuote(record.violation || capabilityName)} --resolution superseded_by_validation --rationale ${shellQuote(state.modalForm.auditNote || "<rationale>")} --evidence "<evidence>" --json`
      : grantCommand;
    return el("div", "preview-stack", [
      el("dl", "kv modal-kv", [
        kv("agent", agent.agent_id || record && record.agent_id || "unavailable"),
        kv("profile", profile.profile_id || agent.profile_id || agent.profile || "unavailable"),
        kv("transition", record && (record.transition || record.requested_mode || record.mode) || "not exposed"),
        kv("reason", record && (record.reason || record.summary) || "not exposed"),
      ]),
      panel("Capability diff", "runtime grant fields", renderCapabilityDiff(profile, record)),
      el("div", "grid two modal-grid", [
        panel("Scope", "preview controls only", el("div", "check-grid", [
          checkboxRow("scopeRepo", "Repository files", "assigned write scope"),
          checkboxRow("scopeAgent", "Selected agent", "agent-scoped request"),
          checkboxRow("scopeRuntime", "Runtime state", "requires explicit review"),
        ])),
        panel("TTL", "requested grant lifetime", renderTtlControls()),
      ]),
      panel("Prior violations", "from alert and capability profile surfaces", violations.length ? renderGenericRows(violations) : empty("No prior capability or protocol violations exposed.")),
      formRow("Audit note", modalTextArea("auditNote", { placeholder: "Reason, risk, and validation evidence for chat-mediated review" }), "Preview text only; the dashboard does not persist it."),
      commandBlock(auditCommand, violation ? "Audit command preview" : "Capability request preview"),
      el("div", "command-actions", [
        button("btn-sm disabled", "Preview only; no dashboard mutation", "Deny preview", () => {}),
        button("btn-sm disabled", "Preview only; no dashboard mutation", "Deny and pause preview", () => {}),
        button("btn-sm disabled", "Preview only; no dashboard mutation", "Grant preview", () => {}),
      ]),
    ]);
  }

  function renderCapabilityDiff(profile, record) {
    const capabilities = profile && typeof profile === "object" && profile.capabilities ? profile.capabilities : {};
    const rows = Object.keys(capabilities).sort().map((key) => {
      const value = capabilities[key] || {};
      return el("div", "diff-row", [
        el("span", "chip", key),
        el("span", "", safe(value.mode, "mode unavailable")),
        value.repositories ? el("span", "muted", safe(JSON.stringify(value.repositories), "")) : null,
      ]);
    });
    if (record && record.capability && !rows.length) {
      rows.push(el("div", "diff-row", [
        el("span", "chip", record.capability),
        el("span", "", safe(record.mode || record.requested_mode, "requested mode unavailable")),
      ]));
    }
    return rows.length ? el("div", "diff-list panel-body", rows) : empty("Capability diff is not exposed by runtime state.");
  }

  function renderTtlControls() {
    return el("div", "ttl-row", ["15m", "30m", "1h", "2h", "4h"].map((ttl) => button(
      `zoom-button ${state.modalForm.ttl === ttl ? "active" : ""}`,
      `${ttl} TTL preview`,
      ttl,
      () => updateModalForm("ttl", ttl),
    )));
  }

  function capabilityViolationsFor(agentId) {
    const alerts = currentAlerts();
    return alerts.filter((alert) => {
      const type = safe(alert.type || alert.violation || alert.capability, "").toLowerCase();
      return type.includes("capability") || type.includes("protocol") || (agentId && alert.agent_id === agentId);
    });
  }

  function renderAgentLogsModal() {
    const detail = selectedAgentDetail();
    const logs = detail && detail.logs ? detail.logs : {};
    const stdout = splitLines(logs.stdout);
    const stderr = splitLines(logs.stderr);
    return el("div", "grid two modal-grid", [
      panel("stdout", safe(logs.stdout_path, "stdout path unavailable"), stdout.length ? renderLogLines(stdout, "out") : empty("No stdout recorded.")),
      panel("stderr", safe(logs.stderr_path, "stderr path unavailable"), stderr.length ? renderLogLines(stderr, "err") : empty("No stderr recorded.")),
    ]);
  }

  function renderAgentReportModal() {
    const detail = selectedAgentDetail();
    if (!detail || !detail.report) return empty("No report yet.");
    return renderJsonBlock(detail.report);
  }

  function renderAgentCapabilityModal() {
    const detail = selectedAgentDetail();
    if (!detail) return empty("Capability metadata unavailable.");
    return el("div", "preview-stack", [
      renderCapabilityModal(detail),
    ]);
  }

  function renderAgentCancelPreview() {
    const run = currentRun();
    const agentId = safe(state.selectedAgentId, "<agent-id>");
    const reason = state.modalForm.reason || `Stop agent ${agentId}`;
    return el("div", "preview-stack", [
      el("p", "", "This dashboard is read-only. Ask interactive Codex to cancel or stop the agent if the runtime supports that operation."),
      formRow("Reason", modalInput("reason", { placeholder: `Stop agent ${agentId}` }), "Agent-scoped cancellation is not a direct dashboard mutation."),
      commandBlock(`python3 scripts/de.py cancel ${shellQuote(repoPath())} --run-id ${shellQuote(safe(run.run_id, "<run-id>"))} --reason ${shellQuote(reason)} --json`, "Run cancel command with agent-specific reason"),
      empty("No Dispatch Engine state is mutated by opening this preview."),
    ]);
  }

  function renderRunSwitcher() {
    const history = currentHistoryRows().slice(0, 8);
    if (!history.length) return empty("No recent runs returned by /api/history.");
    return el("div", "row-list", history.map((run) => el("div", `history-row ${run.run_id === currentRun().run_id ? "active" : ""}`, [
      el("div", "", [
        el("div", "history-id", safe(run.short_id || shortId(run.run_id), "n/a")),
        el("div", "row-meta", fmtDate(run.created_at)),
      ]),
      el("div", "", [
        el("div", "row-title", safe(run.objective, "No objective recorded.")),
        el("div", "row-meta", safe(run.repo || run.state_dir, "")),
      ]),
      statusPill(run.status),
    ])));
  }

  function renderRunOpenPreview(run) {
    const row = run || {};
    const command = row.dashboard_command_preview || `python3 scripts/de.py dashboard ${shellQuote(repoPath())} --run-id ${shellQuote(safe(row.run_id, "<run-id>"))} --detach --json`;
    return el("div", "preview-stack", [
      el("dl", "kv modal-kv", [
        kv("run id", row.run_id || "unavailable"),
        kv("repo", row.repo || "unavailable"),
        kv("plan", row.plan_id || "not exposed"),
        kv("status", row.status || "unknown"),
        kv("duration", formatDuration(row.duration_ms)),
      ]),
      empty("The current dashboard service is read-only and bound to one run. Opening a different run is previewed instead of mutating server state."),
      commandBlock(command, "Open or reuse dashboard command preview"),
    ]);
  }

  function fixtureScenario(id) {
    return scenarioFromLive(id, {
      run: fixtureStatus(id),
      alerts: fixtureAlerts(id),
      violations: fixtureAlerts(id).filter((alert) => alert.type.includes("violation") || alert.type.includes("capability")),
      staleSupervisor: id === "coordinator-dead" ? { summary: "Fixture supervisor process is no longer alive." } : null,
      terminal: ["completed", "cancelled", "failed"].includes(id),
    });
  }

  function fixtureStatus(id) {
    const now = "2026-05-05T01:35:00Z";
    const terminalAt = "2026-05-05T01:42:00Z";
    const statusByScenario = {
      empty: "no_run",
      starting: "planned",
      running: "running",
      "waiting-input": "running",
      "violation-flash": "running",
      disconnected: "running",
      "coordinator-dead": "running",
      completed: "completed",
      cancelled: "cancelled",
      failed: "failed",
    };
    const agents = id === "empty" ? [] : [
      { agent_id: "coordinator-001", role: "coordinator", status: id === "coordinator-dead" ? "stale" : "running", last_heartbeat_at: now, profile: "coordinator" },
      { agent_id: "worker-009-state-overlays", role: "worker", status: id === "waiting-input" ? "blocked" : id === "completed" ? "completed" : "running", workstream: "09-state-overlays", last_heartbeat_at: now, profile: "worker-standard", assigned_files: ["dashboard/app.js"], allowed_write_roots: ["dashboard/"] },
      { agent_id: "validator-010", role: "validator", status: id === "completed" ? "passed" : "registered", workstream: "10-parity-validation", profile: "validator-standard" },
    ];
    return {
      kind: "status",
      status: "ok",
      run_id: id === "empty" ? null : `fixture-${id}`,
      run_status: statusByScenario[id] || "running",
      objective: `Fixture ${id} dashboard state`,
      summary: `Fixture ${id} dashboard state`,
      state_dir: ".dispatch/runs/fixture-read-only",
      repo_root: repoPath(),
      started_at: "2026-05-05T01:00:00Z",
      updated_at: ["completed", "cancelled", "failed"].includes(id) ? terminalAt : now,
      completed_at: id === "completed" ? terminalAt : null,
      cancelled_at: id === "cancelled" ? terminalAt : null,
      failed_at: id === "failed" ? terminalAt : null,
      last_event_at: id === "disconnected" ? "2026-05-05T01:15:00Z" : now,
      pending_decisions: id === "waiting-input" ? 1 : 0,
      cancellation_reason: id === "cancelled" ? "Fixture cancellation requested by operator." : null,
      failure_reason: id === "failed" ? "Fixture validation failure after worker report review." : null,
      completion_summary: id === "completed" ? "Fixture run validated successfully." : null,
      agent_counts: {
        by_role: { coordinator: agents.filter((a) => a.role === "coordinator").length, worker: agents.filter((a) => a.role === "worker").length, validator: agents.filter((a) => a.role === "validator").length },
        by_status: agents.reduce((acc, agent) => {
          acc[agent.status] = (acc[agent.status] || 0) + 1;
          return acc;
        }, {}),
      },
      workstream_counts: id === "empty" ? {} : { planned: id === "starting" ? 2 : 0, running: id === "running" ? 2 : 1, blocked: id === "waiting-input" ? 1 : 0, completed: id === "completed" ? 3 : 0 },
      agents,
      workstream_assignments: agents.filter((agent) => agent.workstream).map((agent) => ({ workstream: agent.workstream, agent_id: agent.agent_id, role: agent.role, status: agent.status })),
      supervisors: id === "coordinator-dead" ? [{ agent_id: "coordinator-001", status: "stale", process_alive: false, summary: "Fixture supervisor process is no longer alive." }] : [{ agent_id: "coordinator-001", status: "running", process_alive: true }],
      lifecycle_diagnostics: id === "coordinator-dead" ? [{ type: "stale_detached_supervisor", summary: "Detached coordinator supervisor is stale." }] : [],
      next_actions: id === "waiting-input" ? [{ type: "decision_required", decision_id: "fixture-decision-1", question: "Choose whether to continue the blocked fixture worker.", recommended_option: "continue", workstream: "09-state-overlays", options: ["continue", "pause"] }] : [],
      protocol_violations: id === "violation-flash" ? { count: 1, unresolved: [{ violation: "capability_overreach", agent_id: "worker-fixture", summary: "Fixture worker attempted a denied capability." }] } : { count: 0, unresolved: [] },
    };
  }

  function fixtureAlerts(id) {
    if (id === "waiting-input") {
      return [{ type: "pending_decision", status: "pending", decision_id: "fixture-decision-1", question: "Choose whether to continue the blocked fixture worker.", workstream: "09-state-overlays", severity: "warning" }];
    }
    if (id === "violation-flash") {
      return [{ type: "protocol_violation", status: "unresolved", violation: "capability_overreach", agent_id: "worker-fixture", summary: "Fixture capability overreach requires protocol review.", severity: "danger" }];
    }
    if (id === "coordinator-dead") {
      return [{ type: "stale_detached_supervisor", status: "stale", summary: "Fixture coordinator supervisor is stale.", severity: "danger" }];
    }
    if (id === "failed") {
      return [{ type: "run_failed", status: "failed", summary: "Fixture validation failed.", severity: "danger" }];
    }
    if (id === "cancelled") {
      return [{ type: "run_cancelled", status: "cancelled", summary: "Fixture run was cancelled by operator.", severity: "warning" }];
    }
    return [];
  }

  function fixtureHistory() {
    return ["completed", "cancelled", "failed"].map((status, index) => ({
      run_id: `fixture-history-${status}`,
      short_id: `fx-${index + 1}`,
      repo: repoPath(),
      repo_name: "fixture",
      plan_id: "rfc-0024",
      objective: `Fixture ${status} history row`,
      status,
      started_at: "2026-05-05T01:00:00Z",
      duration_ms: 240000 + index * 30000,
      worker_count: 2,
      decision_count: index,
      files_changed_count: 3,
      tests_passed: status === "failed" ? 2 : 3,
      tests_total: 3,
      terminal_reason: status === "completed" ? "Fixture validated." : status === "cancelled" ? "Fixture cancelled." : "Fixture failure.",
      dashboard_command_preview: `python3 scripts/de.py dashboard ${shellQuote(repoPath())} --run-id fixture-history-${status} --detach --json`,
    }));
  }

  function isTypingTarget(target) {
    if (!target) return false;
    const tag = target.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
  }

  function focusSearchField() {
    const search = app && app.querySelector("input[type='search'], .search-input");
    if (search) search.focus();
  }

  function onKeyDown(event) {
    if (isTypingTarget(event.target)) return;
    if (event.key === "Escape") {
      if (state.modal) {
        event.preventDefault();
        closeModal();
        return;
      }
      if (state.settingsOpen || chord) {
        event.preventDefault();
        closeTransient();
        render();
      }
      return;
    }
    if (state.modal) return;
    if (event.key === "?") {
      event.preventDefault();
      openModal("keyboard");
      return;
    }
    if (event.key === "x") {
      event.preventDefault();
      openModal("cancel");
      return;
    }
    if (event.key === "c" && chord !== "g") {
      event.preventDefault();
      openModal("tail");
      return;
    }
    if (event.key === "s") {
      event.preventDefault();
      openModal("status");
      return;
    }
    if (event.key === "/") {
      event.preventDefault();
      focusSearchField();
      return;
    }
    if (event.key === "t") {
      event.preventDefault();
      const index = THEMES.findIndex((item) => item.id === state.prefs.theme);
      setTheme(THEMES[(index + 1) % THEMES.length].id);
      return;
    }
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      stepZoom(1);
      return;
    }
    if (event.key === "-") {
      event.preventDefault();
      stepZoom(-1);
      return;
    }
    if (chord === "g") {
      const map = { o: "overview", a: "agents", p: "plan", d: "decisions", c: "capabilities", v: "validators", h: "history", l: "logs" };
      if (map[event.key]) {
        event.preventDefault();
        setScreen(map[event.key]);
      }
      clearChord();
      return;
    }
    if (event.key === "g") {
      chord = "g";
      chordTimer = window.setTimeout(clearChord, 900);
    }
  }

  function onDocumentMouseDown(event) {
    if (state.modal && event.target.classList && event.target.classList.contains("modal-bg")) {
      closeModal();
      return;
    }
    if (!state.settingsOpen && !state.runSwitcherOpen) return;
    if (state.settingsOpen && event.target.closest(".settings-anchor")) return;
    if (state.runSwitcherOpen && event.target.closest(".run-switch-anchor")) return;
    if (state.settingsOpen || state.runSwitcherOpen) {
      state.settingsOpen = false;
      state.runSwitcherOpen = false;
      render();
    }
  }

  function eventMessage(event) {
    const payload = event.payload && typeof event.payload === "object" ? event.payload : {};
    const parts = [];
    if (event.actor) parts.push(event.actor);
    if (event.workstream) parts.push(event.workstream);
    if (payload.agent_id) parts.push(payload.agent_id);
    if (payload.title) parts.push(payload.title);
    if (payload.status) parts.push(payload.status);
    if (payload.objective) parts.push(payload.objective);
    return parts.length ? parts.join(" / ") : JSON.stringify(payload);
  }

  function segmentColor(status) {
    const colors = {
      completed: "var(--ok)",
      running: "var(--accent)",
      assigned: "var(--accent)",
      registered: "var(--accent)",
      blocked: "var(--warn)",
      pending: "var(--warn)",
      failed: "var(--danger)",
      cancelled: "var(--text-4)",
    };
    return colors[safe(status, "").toLowerCase()] || "var(--panel-3)";
  }

  applyPreferences();
  document.addEventListener("keydown", onKeyDown);
  document.addEventListener("mousedown", onDocumentMouseDown);
  load();
  window.setInterval(() => updateLiveHeartbeatClocks(app), 1000);
  window.setInterval(load, POLL_MS);
})();
