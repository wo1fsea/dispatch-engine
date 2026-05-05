/* global React, ReactDOM */
const { useState, useEffect, useMemo, useRef, useCallback } = React;
const D = window.DE_DATA;

// ──────────────────────────────────────────────────────────
// Live clock — ticking elapsed time since run start
// ──────────────────────────────────────────────────────────
function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(t);
  }, [intervalMs]);
  return now;
}

function fmtElapsed(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}
function fmtRel(secAgo) {
  if (secAgo == null) return "—";
  const s = Math.abs(Math.round(secAgo));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s/60)}m ${s%60}s ago`;
  return `${Math.floor(s/3600)}h ${Math.floor((s%3600)/60)}m ago`;
}
function fmtClock(d) {
  const z = (n) => String(n).padStart(2,"0");
  return `${z(d.getUTCHours())}:${z(d.getUTCMinutes())}:${z(d.getUTCSeconds())}Z`;
}

// ──────────────────────────────────────────────────────────
// Status helpers
// ──────────────────────────────────────────────────────────
const STATUS_CLASS = {
  running: "run", completed: "ok", queued: "muted",
  blocked: "warn", failed: "danger", cancelled: "muted",
  passed: "ok", skipped: "muted", late: "warn", ok: "ok",
};
function StatusPill({ status, children }) {
  const cls = STATUS_CLASS[status] || "muted";
  return <span className={`pill ${cls}`}>{children || status}</span>;
}
function Dot({ status, pulse }) {
  const cls = STATUS_CLASS[status] || "muted";
  return <span className={`dot ${cls} ${pulse ? "dot-pulse" : ""}`} />;
}

// ──────────────────────────────────────────────────────────
// Topbar
// ──────────────────────────────────────────────────────────
const THEMES = [
  { id: "solar",   name: "Solar",         desc: "paper light",           sw: ["#fbf7ee", "#b15c2b"] },
  { id: "default", name: "Mission cyan",  desc: "cool dark",             sw: ["#0c1117", "#5fc6e0"] },
  { id: "carbon",  name: "Carbon",        desc: "neutral + amber",       sw: ["#131315", "#e7c479"] },
  { id: "indigo",  name: "Indigo",        desc: "midnight violet",       sw: ["#11142a", "#8c7cff"] },
  { id: "forest",  name: "Forest",        desc: "muted green",           sw: ["#121817", "#84d2a8"] },
  { id: "crimson", name: "Crimson",       desc: "high stakes",           sw: ["#15110f", "#ff7066"] },
];

function SettingsPopover({ theme, onThemeChange, zoom, onZoomChange, onClose, anchorRef }) {
  const ref = React.useRef(null);
  const [pos, setPos] = React.useState({ top: 0, right: 0 });
  React.useLayoutEffect(() => {
    if (anchorRef && anchorRef.current) {
      const r = anchorRef.current.getBoundingClientRect();
      setPos({ top: r.bottom + 8, right: window.innerWidth - r.right });
    }
  }, [anchorRef]);
  React.useEffect(() => {
    const onDoc = (e) => {
      if (ref.current && ref.current.contains(e.target)) return;
      if (anchorRef && anchorRef.current && anchorRef.current.contains(e.target)) return;
      onClose();
    };
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [onClose, anchorRef]);
  const ZOOMS = [0.7, 0.8, 0.9, 1.0];
  return (
    <div className="tb-pop" ref={ref} style={{ top: pos.top, right: pos.right }}>
      <div className="tb-pop-h">
        <span>theme</span>
        <span className="hint">applies instantly</span>
      </div>
      {THEMES.map(t => (
        <div key={t.id}
             className={"tb-theme-row" + (theme === t.id ? " active" : "")}
             onClick={() => onThemeChange(t.id)}>
          <div className="tb-theme-sw">
            <span style={{ background: t.sw[0] }} />
            <span style={{ background: t.sw[1] }} />
          </div>
          <div className="tb-theme-meta">
            <span className="tb-theme-name">{t.name}</span>
            <span className="tb-theme-desc">{t.desc}</span>
          </div>
          <svg className="tb-theme-check" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 8l3.5 3.5L13 5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      ))}
      <div className="tb-pop-h" style={{ marginTop: 6 }}>
        <span>density</span>
        <span className="hint">UI scale</span>
      </div>
      <div className="tb-zoom-row">
        {ZOOMS.map(z => (
          <button key={z}
                  className={"tb-zoom-btn" + (Math.abs((zoom ?? 1) - z) < 0.001 ? " active" : "")}
                  onClick={() => onZoomChange(z)}>
            {Math.round(z * 100)}%
          </button>
        ))}
      </div>
    </div>
  );
}

function Topbar({ crumbs, onCancel, onShow, theme, onThemeChange, zoom, onZoomChange, scenario, onScenarioChange, empty }) {
  const now = useNow(1000);
  const elapsed = now - D.RUN.startedAt;
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const settingsBtnRef = React.useRef(null);
  // synthesise a "frozen at" elapsed for terminal scenarios so the clock doesn't keep ticking
  const frozenScenarios = ["completed", "failed", "cancelled", "coordinator-dead"];
  const isFrozen = frozenScenarios.indexOf(scenario) !== -1;
  const stopElapsed = isFrozen ? (D.RUN.terminalElapsedMs || elapsed) : elapsed;
  const stopNow = isFrozen ? (D.RUN.terminalAt || now) : now;
  const dotCls = (() => {
    switch (scenario) {
      case "completed": return "ok";
      case "failed": return "danger";
      case "cancelled": return "muted";
      case "coordinator-dead": return "danger";
      case "disconnected": return "warn";
      case "waiting-input": return "warn";
      case "violation-flash": return "danger";
      default: return "run";
    }
  })();
  const stateLabel = (() => {
    switch (scenario) {
      case "completed": return "completed";
      case "failed": return "failed";
      case "cancelled": return "cancelled";
      case "coordinator-dead": return "coordinator dead";
      case "disconnected": return "stream paused";
      case "waiting-input": return "elapsed (paused)";
      case "violation-flash": return "elapsed";
      case "starting": return "spinning up";
      default: return "elapsed";
    }
  })();
  return (
    <div className="topbar">
      <div className="crumb">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className="sep">/</span>}
            <span className={i === crumbs.length - 1 ? "here" : ""}>
              {c.mono ? <span className="mono">{c.label}</span> : c.label}
            </span>
          </React.Fragment>
        ))}
      </div>
      <div className="tb-spacer" />
      <div className={"tb-clock state-" + (scenario || "running")}>
        <span className={"pulse pulse-" + dotCls} />
        <span>{stateLabel}</span>
        {!empty && <b style={{ color: "var(--fg-0)" }}>{fmtElapsed(stopElapsed)}</b>}
        <span style={{ color: "var(--fg-3)" }}>·</span>
        <span>{fmtClock(new Date(stopNow))}</span>
      </div>
      <button className="tb-btn icon" title="Tail logs" onClick={() => onShow("tail")}><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 4h12M2 8h8M2 12h10" strokeLinecap="round"/></svg></button>
      <button className="tb-btn icon" title="status --json" onClick={() => onShow("status")}><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="12" height="12" rx="2"/><path d="M5 6h6M5 8.5h4M5 11h5" strokeLinecap="round"/></svg></button>
      <div className="tb-settings">
        <button ref={settingsBtnRef} className={"tb-btn icon" + (settingsOpen ? " active" : "")} title="Settings" onClick={() => setSettingsOpen(s => !s)}>
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="8" cy="8" r="2.2"/>
            <path d="M8 1.5v1.8M8 12.7v1.8M14.5 8h-1.8M3.3 8H1.5M12.6 3.4l-1.3 1.3M4.7 11.3l-1.3 1.3M12.6 12.6l-1.3-1.3M4.7 4.7L3.4 3.4" strokeLinecap="round"/>
          </svg>
        </button>
        {settingsOpen && (
          <SettingsPopover
            theme={theme}
            anchorRef={settingsBtnRef}
            zoom={zoom}
            onZoomChange={onZoomChange}
            onThemeChange={(id) => { onThemeChange(id); setSettingsOpen(false); }}
            onClose={() => setSettingsOpen(false)}
          />
        )}
      </div>
      {!empty && !isFrozen && (
        <button className="tb-btn icon danger" title="Cancel run (x)" onClick={onCancel}><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="6"/><path d="M5 5l6 6M11 5l-6 6" strokeLinecap="round"/></svg></button>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Sidebar
// ──────────────────────────────────────────────────────────
function Sidebar({ screen, setScreen, scenario, empty }) {
  const dec = scenario === "waiting-input" ? { txt: "1", cls: "warn pulse" }
            : empty ? null : { txt: "3", cls: "info" };
  const cap = scenario === "violation-flash" ? { txt: "1", cls: "danger pulse" }
            : empty ? null : { txt: "1", cls: "danger" };
  const alerts = scenario === "violation-flash" ? { txt: "3", cls: "danger pulse" }
               : scenario === "coordinator-dead" ? { txt: "4", cls: "danger" }
               : empty ? null : { txt: "2", cls: "warn" };
  const items = [
    { k: "overview", label: "Overview" },
    { k: "agents",   label: "Agents", badge: empty ? null : { txt: "10", cls: "" } },
    { k: "plan",     label: "Plan & workstreams" },
    { k: "decisions",label: "Decisions", badge: dec },
    { k: "capabilities", label: "Capabilities", badge: cap },
    { k: "validators", label: "Validators" },
    { k: "alerts",   label: "Alerts", badge: alerts },
    { k: "history",  label: "Run history" },
  ];
  const recent = [
    { short: "7af3c1", label: "octane-api · plan-014", st: "run",  active: true },
    { short: "e2a4f9", label: "octane-api · plan-013", st: "ok"  },
    { short: "c8810a", label: "octane-api · plan-012", st: "ok"  },
    { short: "91be20", label: "octane-api · plan-011", st: "muted" },
    { short: "6604fe", label: "ledger-svc · plan-007", st: "danger" },
  ];
  return (
    <div className="sidebar">
      <div className="sb-brand">
        <div className="sb-brand-mark">de</div>
        <div className="sb-brand-name">
          <b>Dispatch Engine</b>
          <span>v0.4.2 · skill</span>
        </div>
      </div>
      <div className="sb-section">{empty ? "No active run" : "Active run"}</div>
      <div className="sb-nav">
        {items.map(it => (
          <div key={it.k}
               className={`sb-nav-item ${screen === it.k ? "active" : ""}`}
               onClick={() => setScreen(it.k)}>
            <span>{it.label}</span>
            {it.badge && <span className={`badge ${it.badge.cls}`}>{it.badge.txt}</span>}
          </div>
        ))}
      </div>
      <div className="sb-runs">
        <div className="sb-runs-title">
          <span>RECENT RUNS</span>
          <span style={{fontFamily:"var(--font-mono)", fontSize:10, color:"var(--fg-3)"}}>5</span>
        </div>
        {recent.map(r => (
          <div key={r.short} className={`sb-run ${r.active ? "active" : ""}`}>
            <span className={`dot ${r.st}`} />
            <span className="acc" style={{color: r.active ? "var(--accent)" : "var(--fg-2)"}}>{r.short}</span>
            <span style={{color:"var(--fg-3)", fontSize:10, marginLeft:"auto"}}>{r.label.split(" · ")[1]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Streaming event log (footer strip)
// ──────────────────────────────────────────────────────────
function EventStream({ paused }) {
  const startedAt = useRef(Date.now());
  const seedTs = useRef(Date.now() - 1000 * 60 * 6);
  const [events, setEvents] = useState(() => {
    // pre-seed with ~12 events spaced over the last few minutes
    const out = [];
    let ts = seedTs.current;
    for (let i = 0; i < 12; i++) {
      ts += 4500 + Math.floor(Math.random() * 18000);
      const tpl = D.EVENT_TEMPLATES[i % D.EVENT_TEMPLATES.length];
      out.push({ id: `seed-${i}`, ts, ...tpl });
    }
    return out;
  });
  const [filter, setFilter] = useState("all");
  const [collapsed, setCollapsed] = useState(false);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (paused) return;
    let alive = true;
    function tick() {
      if (!alive) return;
      const tpl = D.EVENT_TEMPLATES[Math.floor(Math.random() * D.EVENT_TEMPLATES.length)];
      setEvents(prev => {
        const next = [...prev, { id: `e-${Date.now()}-${Math.random()}`, ts: Date.now(), ...tpl }];
        return next.slice(-50);
      });
      setTimeout(tick, 1800 + Math.random() * 2500);
    }
    const t = setTimeout(tick, 1500);
    return () => { alive = false; clearTimeout(t); };
  }, [paused]);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [events]);

  const filtered = events.filter(e => filter === "all" || e.lvl === filter || e.src === filter);

  return (
    <div className="event-strip" style={collapsed ? { height: "auto" } : undefined}>
      <div className="es-h">
        <span className="t">
          <span className={"dot " + (paused ? "warn" : "run dot-pulse")} />
          {paused ? "EVENTS · stream paused" : "EVENTS · streaming"}
        </span>
        {!collapsed && (
          <span style={{ color: "var(--fg-3)" }}>tail .dispatch/runs/{D.RUN.short}/events.jsonl</span>
        )}
        {collapsed && (
          <span style={{ color: "var(--fg-2)" }}>
            {events.length} buffered · latest {filtered.length > 0 ? fmtClock(new Date(filtered[filtered.length-1].ts)) : "—"}
          </span>
        )}
        <div className="filters" style={collapsed ? { display: "none" } : undefined}>
          {["all","ok","warn","error","coord","worker","runtime"].map(f => (
            <span key={f} className={`filt ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>{f}</span>
          ))}
        </div>
        <span
          className="filt"
          title={collapsed ? "expand events" : "collapse events"}
          onClick={() => setCollapsed(c => !c)}
          style={{ marginLeft: collapsed ? "auto" : 8, cursor: "pointer", fontFamily: "var(--font-mono)", padding: "3px 8px" }}>
          {collapsed ? "▲" : "▼"}
        </span>
      </div>
      <div className="es-body" ref={bodyRef} style={collapsed ? { display: "none" } : undefined}>
        {filtered.map(e => (
          <div key={e.id} className={`ev lvl-${e.lvl}`}>
            <span className="ts">{fmtClock(new Date(e.ts))}</span>
            <span className="lvl">{e.lvl === "ok" ? "✓" : e.lvl === "warn" ? "!" : e.lvl === "error" ? "✗" : "·"}</span>
            <span className={`src ${e.src}`}>{e.src}</span>
            <span className="msg" dangerouslySetInnerHTML={{ __html: e.tpl }} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Run header (overview hero)
// ──────────────────────────────────────────────────────────
function RunHeader() {
  const now = useNow(1000);
  const elapsed = now - D.RUN.startedAt;

  const wsCounts = useMemo(() => {
    const out = { completed: 0, running: 0, blocked: 0, queued: 0, failed: 0 };
    D.WORKSTREAMS.forEach(w => out[w.status] = (out[w.status]||0) + 1);
    return out;
  }, []);
  const total = D.WORKSTREAMS.length;

  return (
    <div className="run-header">
      <div className="rh-l">
        <div className="rh-id-row">
          <StatusPill status="running"><Dot status="run" pulse /> running · detached</StatusPill>
          <span className="rh-id">run <span className="acc">{D.RUN.short}</span> · {D.RUN.id.slice(4, 24)}…</span>
        </div>
        <div className="rh-title">{D.RUN.objective}</div>
        <div className="rh-meta">
          <span><b>repo</b> <span className="mono">{D.RUN.repo}</span></span>
          <span><b>plan</b> <span className="mono">{D.RUN.plan}</span></span>
          <span><b>provider</b> <span className="mono">{D.RUN.provider}</span></span>
          <span><b>coordinator</b> <span className="mono">{D.RUN.coordinator}</span></span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
          <div className="bar split thick">
            <span style={{ flex: wsCounts.completed }} title={`${wsCounts.completed} completed`} />
            <span className="running" style={{ flex: wsCounts.running }} title={`${wsCounts.running} running`} />
            <span className="blocked" style={{ flex: wsCounts.blocked }} title={`${wsCounts.blocked} blocked`} />
            <span className="pending" style={{ flex: wsCounts.queued }} title={`${wsCounts.queued} queued`} />
          </div>
          <div style={{ display: "flex", gap: 16, fontFamily: "var(--font-mono)", fontSize: 10.5, color: "var(--fg-3)" }}>
            <span><span style={{color:"var(--ok)"}}>■</span> {wsCounts.completed} completed</span>
            <span><span style={{color:"var(--accent)"}}>■</span> {wsCounts.running} running</span>
            <span><span style={{color:"var(--warn)"}}>■</span> {wsCounts.blocked} blocked</span>
            <span><span style={{color:"var(--fg-3)"}}>■</span> {wsCounts.queued} queued</span>
          </div>
        </div>
      </div>
      <div className="rh-r">
        <div className="rh-stats">
          <div className="stat"><span className="k">elapsed</span><span className="v">{fmtElapsed(elapsed)}</span></div>
          <div className="stat"><span className="k">workers</span><span className="v">10</span></div>
          <div className="stat"><span className="k">decisions</span><span className="v warn">3</span></div>
          <div className="stat"><span className="k">violations</span><span className="v danger">1</span></div>
        </div>
        <div style={{display:"flex", gap:8, marginTop:"auto", flexWrap:"wrap", justifyContent:"flex-end"}}>
          <span className="pill muted" style={{textTransform:"none", letterSpacing:0}}>
            host heartbeat owner: <b style={{color:"var(--fg-1)"}}>interactive-codex</b>
          </span>
          <span className="pill muted" style={{textTransform:"none", letterSpacing:0}}>
            mode: <b style={{color:"var(--fg-1)"}}>{D.RUN.mode}</b>
          </span>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Workstream timeline list
// ──────────────────────────────────────────────────────────
function WorkstreamList() {
  return (
    <div className="panel" style={{ minHeight: 0 }}>
      <div className="panel-h">
        <span className="title">Workstreams</span>
        <span className="sub">plans/plan-014.json · 8 total</span>
        <div className="actions">
          <button className="tb-btn icon" title="Expand all"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 6l4 4 4-4" strokeLinecap="round" strokeLinejoin="round"/></svg></button>
        </div>
      </div>
      <div className="panel-b tight">
        <div className="ws-list">
          {D.WORKSTREAMS.map((w, i) => (
            <div key={w.id} className="ws-row">
              <div className="ws-idx">{String(i+1).padStart(2,"0")}</div>
              <div className="ws-name">
                <div className="n"><Dot status={w.status} pulse={w.status === "running"} /> {w.name}</div>
                <div className="meta">
                  <span>{w.id}</span>
                  <span>→ {w.assignee}</span>
                  <span>{w.files} files</span>
                  {w.blockedReason && <span style={{color:"var(--warn)"}}>· {w.blockedReason}</span>}
                </div>
              </div>
              <div className="ws-bar">
                <div className="bar"><span style={{ width: `${w.pct}%`,
                  background: w.status === "completed" ? "var(--ok)"
                            : w.status === "blocked"   ? "var(--warn)"
                            : w.status === "queued"    ? "transparent"
                                                       : undefined }} /></div>
                <div className="lab">
                  <span>{w.pct}%</span>
                  <span>{w.started ? `started ${fmtRel(-w.started)}` : "queued"}</span>
                </div>
              </div>
              <div className="ws-status"><StatusPill status={w.status} /></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Heartbeat ring
// ──────────────────────────────────────────────────────────
function HeartbeatCard({ scenario }) {
  // 15-min interval, simulate countdown from a random offset so it feels live
  const TOTAL = 15 * 60;
  const startedAt = useRef(Date.now() - 1000 * 9 * 60); // 9 min into cycle
  const now = useNow(1000);
  const elapsed = Math.floor((now - startedAt.current) / 1000);
  const remaining = TOTAL - (elapsed % TOTAL);
  const pct = remaining / TOTAL;

  const C = 2 * Math.PI * 38;
  const offset = C * (1 - pct);

  const fmtMin = (s) => `${String(Math.floor(s/60)).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;

  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Host heartbeat</span>
        <span className="sub">interval=15m · owner=interactive-codex</span>
      </div>
      <div className="hb-card">
        <div className="hb-ring">
          <svg viewBox="0 0 88 88">
            <circle className="track" cx="44" cy="44" r="38" />
            <circle className="prog" cx="44" cy="44" r="38"
                    strokeDasharray={C}
                    strokeDashoffset={offset} />
          </svg>
          <div className="label">
            <span className="v">{fmtMin(remaining)}</span>
            <span className="k">until next</span>
          </div>
        </div>
        <div className="hb-info">
          <div className="l">Last wakeup <b>{fmtMin(elapsed % TOTAL)} ago</b></div>
          <div className="meta">3 of 4 unanswered <span style={{color:"var(--fg-2)"}}>· decision-014</span></div>
          <div className="meta" style={{color:"var(--warn)"}}>1 more miss → autonomous-technical eligibility</div>
          <div style={{display:"flex", gap:6, marginTop:6}}>
            <button className="btn-sm icon" title="Poke now"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M7 2v5l3 2" strokeLinecap="round"/><circle cx="7" cy="7" r="5.5"/></svg></button>
            <button className="btn-sm icon" title="Heartbeat log"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1 7h3l1.5-3 3 6L10 7h3" strokeLinecap="round" strokeLinejoin="round"/></svg></button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Decisions list
// ──────────────────────────────────────────────────────────
function DecisionsList({ onOpen }) {
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Pending decisions</span>
        <span className="sub">3 open · 1 with autonomous risk</span>
      </div>
      <div className="panel-b tight">
        <div className="list">
          {D.DECISIONS.map(d => (
            <div key={d.id} className="list-row dec-row" onClick={() => onOpen && onOpen(d.id)} style={{cursor: onOpen ? "pointer" : "default"}}>
              <div className={`stripe ${d.severity}`} />
              <div>
                <div className="dec-q">{d.q}</div>
                <div className="dec-meta">
                  <span style={{color:"var(--accent)"}}>{d.id}</span>
                  <span>· raised by {d.agent}</span>
                  <span>· {fmtRel(d.since)}</span>
                  <span>· options: {d.options.join(" / ")}</span>
                  {d.heartbeats > 0 && <span className="h">· {d.heartbeats}/4 heartbeats unanswered</span>}
                </div>
              </div>
              <div className="dec-cta" onClick={(e) => e.stopPropagation()}>
                <button className="btn-sm icon" title="Defer"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="7" cy="7" r="5.5"/><path d="M7 4v3l2 2" strokeLinecap="round"/></svg></button>
                <button className="btn-sm primary icon" title="Resolve decision" onClick={() => onOpen && onOpen(d.id)}><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 7.5l3 3 5-6" strokeLinecap="round" strokeLinejoin="round"/></svg></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Alerts list
// ──────────────────────────────────────────────────────────
function AlertsList() {
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Alerts & violations</span>
        <span className="sub">3 active</span>
      </div>
      <div className="panel-b tight">
        <div className="list">
          {D.ALERTS.map(a => (
            <div key={a.id} className={`list-row alert-row ${a.level}`}>
              <div className="ico-wrap">
                {a.level === "danger" ? "✗" : "!"}
              </div>
              <div>
                <div className="what">{a.msg}</div>
                <div className="who">{a.who}</div>
              </div>
              <div className="when">{fmtRel(a.when)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Agent roster (cards)
// ──────────────────────────────────────────────────────────
function AgentRoster({ onPick, compact }) {
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Agent roster</span>
        <span className="sub">{D.AGENTS.length} registered · 5 running · 2 completed · 3 queued</span>
        <div className="actions">
          <button className="tb-btn icon" title="Filter roles"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 3h12l-4.5 6v4l-3 1.5V9z" strokeLinejoin="round"/></svg></button>
        </div>
      </div>
      <div className="agent-grid">
        {D.AGENTS.map(a => (
          <div key={a.id}
               className={`agent-card ${a.role === "coordinator" ? "coord" : ""}`}
               onClick={() => onPick(a.id)}>
            <div className="ac-top">
              <Dot status={a.status} pulse={a.status === "running"} />
              <div style={{display:"flex", flexDirection:"column", lineHeight:1.2, minWidth:0, flex:1}}>
                <span className="ac-role">{a.role}</span>
                <span className="ac-id"><span className="acc">{a.id}</span></span>
              </div>
              <StatusPill status={a.status} />
            </div>
            {!compact && <div className="ac-task">{a.task}</div>}
            <div className="ac-cap">
              {a.caps.map(c => (
                <span key={c.k} className={`chip ${c.hi ? "hi" : ""}`}>{c.k}</span>
              ))}
            </div>
            <div className="ac-foot">
              <div className="l">
                <span>hb {a.hb === "late" ? <span style={{color:"var(--warn)"}}>late</span>
                          : a.hb === "ok" ? <span style={{color:"var(--ok)"}}>ok</span> : "—"}</span>
                <span>{fmtRel(a.lastHb)}</span>
              </div>
              <span>{a.files} files</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Command modal — shows simulated CLI output
// ──────────────────────────────────────────────────────────
function CommandModal({ kind, onClose }) {
  if (!kind) return null;

  const STATUS_JSON = {
    run_id: "run-2026-05-05T05-12-44Z-7af3c1",
    repo: "wo1fsea/octane-api",
    plan: "plans/plan-014.json",
    provider: "codex",
    mode: "detached",
    status: "running",
    started_at: "2026-05-05T05:12:44Z",
    elapsed_s: 2845,
    coordinator: { id: "coordinator-001", status: "running", profile: "coordinator-elevated", uptime_s: 2842 },
    workstreams: { total: 8, completed: 2, running: 2, blocked: 1, queued: 3, failed: 0 },
    agents: { coordinator: 1, worker: 5, reviewer: 2, validator: 2 },
    decisions: { open: 3, autonomous_eligible: 0, escalated: 1 },
    capability_profiles: { active: 5, queued: 2, violations: 1, escalations: 2 },
    heartbeat: { interval_s: 900, owner: "interactive-codex", unanswered: 1, next_in_s: 322 },
    alerts: { warn: 2, danger: 1 },
    last_event_ts: "2026-05-05T05:59:51Z"
  };

  const TAIL_LINES = [
    ["05:59:43Z", "INFO",  "coord", "progress ws-03=66% (8/11 files)"],
    ["05:59:46Z", "OK",    "worker-b", "file.write billing/handlers/dispute.py (+91 −38)"],
    ["05:59:48Z", "INFO",  "validator-a", "test.run tests/contract/test_invoice.py::test_get PASSED"],
    ["05:59:51Z", "WARN",  "runtime", "agent.heartbeat.late worker-c, last=94s ago threshold=60s"],
    ["05:59:53Z", "INFO",  "coord", "decision.opened decision-016 by validator-a (severity=warn)"],
    ["05:59:55Z", "OK",    "worker-c", "file.write invoice/handlers/list.py (+44 −22)"],
    ["05:59:58Z", "INFO",  "runtime", "agent.heartbeat coordinator-001 uptime=00:47:14"],
    ["06:00:01Z", "INFO",  "coord", "progress ws-04=33% (3/8 files)"],
    ["06:00:04Z", "OK",    "validator-a", "test.run tests/contract/test_billing.py::test_refund PASSED"],
    ["06:00:08Z", "INFO",  "reviewer-a", "review.note refund.py: missing trailing context propagation"],
    ["06:00:11Z", "OK",    "worker-b", "file.write billing/handlers/charge.py (+12 −4)"],
    ["06:00:14Z", "INFO",  "runtime", "capability.escalation.requested validator-b → docker.socket"],
  ];

  function renderJson(obj, depth = 0) {
    const pad = "  ".repeat(depth);
    if (obj === null) return <span className="b">null</span>;
    if (typeof obj === "number") return <span className="n">{obj}</span>;
    if (typeof obj === "string") return <span className="s">"{obj}"</span>;
    if (typeof obj === "boolean") return <span className="b">{String(obj)}</span>;
    if (Array.isArray(obj)) {
      return <>[{obj.map((v, i) => <React.Fragment key={i}>{renderJson(v, depth+1)}{i < obj.length-1 ? ", " : ""}</React.Fragment>)}]</>;
    }
    const entries = Object.entries(obj);
    return (
      <>{"{"}{"\n"}{entries.map(([k, v], i) => (
        <React.Fragment key={k}>
          {pad}{"  "}<span className="k">"{k}"</span>: {renderJson(v, depth+1)}{i < entries.length-1 ? "," : ""}{"\n"}
        </React.Fragment>
      ))}{pad}{"}"}</>
    );
  }

  const isTail = kind === "tail";

  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-h">
          <span className="title">$ {isTail ? "de tail" : "de status --json"} {D.RUN.repo}</span>
          <span className="sub">live · refreshes every 1s</span>
          <button className="x" onClick={onClose} title="close">✕</button>
        </div>
        <div className="modal-b">
          <pre>
            {isTail
              ? TAIL_LINES.map((l, i) => (
                  <div key={i}>
                    <span className="k">{l[0]}</span>{"  "}
                    <span style={{color: l[1]==="WARN" ? "var(--warn)" : l[1]==="OK" ? "var(--ok)" : "var(--accent)"}}>{l[1].padEnd(5)}</span>{" "}
                    <span className="s">{l[2].padEnd(14)}</span>{l[3]}
                  </div>
                ))
              : <span>{renderJson(STATUS_JSON)}</span>
            }
          </pre>
        </div>
      </div>
    </div>
  );
}

window.DEUI = { useNow, fmtElapsed, fmtRel, fmtClock, StatusPill, Dot,
                Topbar, Sidebar, EventStream, RunHeader, WorkstreamList,
                HeartbeatCard, DecisionsList, AlertsList, AgentRoster,
                CommandModal };
