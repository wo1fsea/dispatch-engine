// ──────────────────────────────────────────────────────────
// Scenario-aware components: alternate run header states,
// empty state, toasts, disconnect banner, plan tree search,
// run-history compare. All read window.DE_SCENARIO.
// ──────────────────────────────────────────────────────────
const { useState: sUseState, useEffect: sUseEffect, useRef: sUseRef } = React;

const SCENARIOS = [
  { k: "running",        label: "running (default)", desc: "live run, all systems green" },
  { k: "waiting-input",  label: "waiting on operator", desc: "blocked on a user decision" },
  { k: "completed",      label: "completed", desc: "run finished cleanly" },
  { k: "failed",         label: "failed", desc: "validator failures, run aborted" },
  { k: "cancelled",      label: "cancelled", desc: "operator cancelled mid-run" },
  { k: "coordinator-dead", label: "coordinator dead", desc: "host process unreachable" },
  { k: "disconnected",   label: "stream disconnected", desc: "events not arriving" },
  { k: "violation-flash", label: "capability violation", desc: "new violation just landed" },
  { k: "empty",          label: "no active run", desc: "dashboard with nothing running" },
];

// ──────────────────────────────────────────────────────────
// Hero header that morphs by scenario
// ──────────────────────────────────────────────────────────
function ScenarioRunHeader({ scenario }) {
  const D = window.DE_DATA;
  const U = window.DEUI;
  const now = U.useNow(1000);
  const elapsed = now - D.RUN.startedAt;

  const cfg = HEADER_CFG[scenario] || HEADER_CFG.running;

  return (
    <div className={"panel run-hero hero-" + scenario}>
      <div className="run-hero-top">
        <span className={"run-hero-pill " + cfg.pillCls}>
          <span className={"dot " + cfg.dotCls + (cfg.pulse ? " dot-pulse" : "")} />
          <b>{cfg.label}</b>
          {cfg.sub && <span className="run-hero-pill-sub">· {cfg.sub}</span>}
        </span>
        <span className="run-hero-id">run <span className="mono">{D.RUN.short}</span> · <span className="mono">{cfg.timeText || "2026-05-05T05-12-44Z"}</span></span>
      </div>
      <h1 className="run-hero-obj">{D.RUN.objective}</h1>
      <div className="run-hero-meta">
        <span>repo <span className="mono">{D.RUN.repo}</span></span>
        <span>plan <span className="mono">{D.RUN.plan}</span></span>
        <span>provider <span className="mono">{D.RUN.provider}</span></span>
        {scenario !== "completed" && scenario !== "cancelled" && scenario !== "failed"
          ? <span>coordinator <span className="mono">{D.RUN.coordinator}</span></span>
          : <span>finished at <span className="mono">{cfg.finishedAt || "06:01:11Z"}</span></span>
        }
      </div>

      <div className="run-hero-bar">
        {cfg.bar.map((seg, i) => (
          <div key={i} className={"run-hero-bar-seg " + seg.cls} style={{ flex: seg.w }} title={seg.title}/>
        ))}
      </div>

      <div className="run-hero-stats">
        {cfg.stats.map((s, i) => (
          <div key={i} className={"run-hero-stat" + (s.big ? " big" : "")}>
            <div className={"run-hero-stat-n " + (s.cls || "")}>{s.n === "{elapsed}" ? U.fmtElapsed(elapsed) : s.n}</div>
            <div className="run-hero-stat-l">{s.l}</div>
          </div>
        ))}
      </div>

      <div className="run-hero-tags">
        {cfg.tags.map((t, i) => (
          <span key={i} className={"run-hero-tag " + (t.cls || "")}>
            <span className="run-hero-tag-k">{t.k}</span>
            <span className="run-hero-tag-v mono">{t.v}</span>
          </span>
        ))}
      </div>

      {cfg.cta && (
        <div className="run-hero-cta">
          <span className="run-hero-cta-msg">{cfg.cta.msg}</span>
          <div className="run-hero-cta-actions">
            {cfg.cta.actions.map((a, i) => (
              <button key={i} className={"btn btn-" + a.kind}>{a.label}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const HEADER_CFG = {
  running: {
    label: "RUNNING", sub: "DETACHED", pillCls: "ok", dotCls: "ok", pulse: true,
    bar: [
      { w: 2, cls: "ok",   title: "completed: 2 ws" },
      { w: 2, cls: "run",  title: "running: 2 ws" },
      { w: 1, cls: "warn", title: "blocked: 1 ws" },
      { w: 3, cls: "muted", title: "queued: 3 ws" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: 2, l: "running",   cls: "run" },
      { n: 1, l: "blocked",   cls: "warn" },
      { n: 3, l: "queued",    cls: "muted" },
      { n: "{elapsed}", l: "ELAPSED", big: true },
      { n: 10, l: "WORKERS",   big: true },
      { n: 3,  l: "DECISIONS", big: true, cls: "warn" },
      { n: 1,  l: "VIOLATIONS",big: true, cls: "danger" },
    ],
    tags: [
      { k: "host heartbeat", v: "interactive-codex" },
      { k: "mode:", v: "detached" },
    ],
  },
  "waiting-input": {
    label: "WAITING ON OPERATOR", sub: "AUTONOMOUS FALLBACK IN 04:32", pillCls: "warn", dotCls: "warn", pulse: true,
    bar: [
      { w: 2, cls: "ok" }, { w: 2, cls: "run" },
      { w: 2, cls: "warn" }, { w: 2, cls: "muted" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: 2, l: "running",   cls: "run" },
      { n: 2, l: "blocked on you", cls: "warn" },
      { n: 2, l: "queued",    cls: "muted" },
      { n: "{elapsed}", l: "ELAPSED", big: true },
      { n: "04:32", l: "FALLBACK IN", big: true, cls: "warn" },
      { n: 3, l: "DECISIONS PENDING", big: true, cls: "warn" },
      { n: 0, l: "VIOLATIONS", big: true },
    ],
    tags: [
      { k: "blocked since", v: "00:36:08" },
      { k: "next action:", v: "approve decision-014" },
    ],
    cta: {
      msg: "Coordinator will pick the recommended option in 4 minutes if you don't act.",
      actions: [
        { kind: "ghost", label: "review decision-014" },
        { kind: "primary", label: "approve recommendation" },
      ]
    }
  },
  completed: {
    label: "COMPLETED", sub: "ALL VALIDATORS PASSED", pillCls: "ok", dotCls: "ok",
    timeText: "01:42:18 total", finishedAt: "06:54:32Z",
    bar: [{ w: 8, cls: "ok" }],
    stats: [
      { n: 8, l: "completed", cls: "ok" },
      { n: 0, l: "running",  cls: "muted" },
      { n: 0, l: "blocked",  cls: "muted" },
      { n: 0, l: "queued",   cls: "muted" },
      { n: "01:42:18", l: "TOTAL TIME", big: true },
      { n: 10, l: "WORKERS",   big: true },
      { n: 4,  l: "DECISIONS", big: true },
      { n: 142, l: "TESTS PASSED", big: true, cls: "ok" },
    ],
    tags: [
      { k: "outcome:", v: "merged to main" },
      { k: "PR:", v: "#284" },
      { k: "files changed:", v: "47" },
    ],
    cta: {
      msg: "Run completed cleanly. Artifacts retained for 30 days.",
      actions: [
        { kind: "ghost", label: "open PR #284" },
        { kind: "ghost", label: "view final report" },
        { kind: "primary", label: "start next run" },
      ]
    }
  },
  failed: {
    label: "FAILED", sub: "VALIDATOR-A: 12 CONTRACT FAILURES", pillCls: "danger", dotCls: "danger",
    timeText: "01:18:42 before failure", finishedAt: "06:31:00Z",
    bar: [
      { w: 2, cls: "ok" }, { w: 4, cls: "danger" }, { w: 2, cls: "muted" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: 4, l: "FAILED",    cls: "danger" },
      { n: 2, l: "abandoned", cls: "muted" },
      { n: 0, l: "queued",    cls: "muted" },
      { n: "01:18:42", l: "BEFORE FAILURE", big: true },
      { n: 12, l: "CONTRACT FAILURES", big: true, cls: "danger" },
      { n: 4,  l: "DECISIONS", big: true },
      { n: 1,  l: "VIOLATIONS", big: true, cls: "danger" },
    ],
    tags: [
      { k: "fail point:", v: "validator-a · ws-06" },
      { k: "exit code:", v: "1" },
    ],
    cta: {
      msg: "Coordinator stopped after validator-a flagged 12 contract drift cases. Run state is preserved.",
      actions: [
        { kind: "ghost", label: "open failure report" },
        { kind: "ghost", label: "diff vs last green" },
        { kind: "primary", label: "retry from ws-04" },
      ]
    }
  },
  cancelled: {
    label: "CANCELLED", sub: "BY OPERATOR", pillCls: "muted", dotCls: "muted",
    timeText: "00:54:11 before cancel", finishedAt: "06:06:55Z",
    bar: [
      { w: 2, cls: "ok" }, { w: 2, cls: "muted" }, { w: 4, cls: "muted-dark" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: 0, l: "running",   cls: "muted" },
      { n: 6, l: "abandoned", cls: "muted" },
      { n: 0, l: "queued",    cls: "muted" },
      { n: "00:54:11", l: "BEFORE CANCEL", big: true },
      { n: 10, l: "WORKERS STOPPED", big: true },
      { n: 0,  l: "DECISIONS LEFT", big: true },
      { n: 1,  l: "VIOLATIONS", big: true, cls: "warn" },
    ],
    tags: [
      { k: "cancelled by:", v: "you · 06:06:55Z" },
      { k: "reason:", v: "\"reverting to plan-013 baseline\"" },
      { k: "kill mode:", v: "graceful" },
    ],
    cta: {
      msg: "Run cancelled. Partial artifacts kept at .dispatch/runs/7af3c1/.",
      actions: [
        { kind: "ghost", label: "open partial artifacts" },
        { kind: "primary", label: "start new run" },
      ]
    }
  },
  "coordinator-dead": {
    label: "COORDINATOR UNREACHABLE", sub: "LAST SEEN 02:14 AGO", pillCls: "danger", dotCls: "danger", pulse: true,
    bar: [
      { w: 2, cls: "ok" }, { w: 2, cls: "danger" }, { w: 1, cls: "warn" }, { w: 3, cls: "muted" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: "?", l: "running (last known: 2)", cls: "danger" },
      { n: 1, l: "blocked",   cls: "warn" },
      { n: 3, l: "queued",    cls: "muted" },
      { n: "{elapsed}", l: "ELAPSED", big: true },
      { n: "02:14", l: "SINCE HEARTBEAT", big: true, cls: "danger" },
      { n: 3, l: "DECISIONS",  big: true, cls: "warn" },
      { n: 1, l: "VIOLATIONS", big: true, cls: "danger" },
    ],
    tags: [
      { k: "host:", v: "interactive-codex" },
      { k: "last hb:", v: "06:46:08Z" },
      { k: "agent state:", v: "frozen on disk" },
    ],
    cta: {
      msg: "No heartbeat from coordinator-001 for 2m 14s (threshold 60s). Workers may still be running blind.",
      actions: [
        { kind: "ghost", label: "ssh into host" },
        { kind: "warn", label: "reattach to coordinator" },
        { kind: "danger", label: "force-stop run" },
      ]
    }
  },
  "violation-flash": {
    label: "RUNNING", sub: "VIOLATION 4s AGO", pillCls: "ok", dotCls: "ok", pulse: true,
    bar: [
      { w: 2, cls: "ok" }, { w: 2, cls: "run" }, { w: 1, cls: "warn" }, { w: 3, cls: "muted" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: 2, l: "running",   cls: "run" },
      { n: 1, l: "blocked",   cls: "warn" },
      { n: 3, l: "queued",    cls: "muted" },
      { n: "{elapsed}", l: "ELAPSED", big: true },
      { n: 10, l: "WORKERS",  big: true },
      { n: 3, l: "DECISIONS", big: true, cls: "warn" },
      { n: 2, l: "VIOLATIONS", big: true, cls: "danger" },
    ],
    tags: [
      { k: "host heartbeat", v: "interactive-codex" },
      { k: "mode:", v: "detached" },
    ],
  },
  disconnected: {
    label: "STREAM DISCONNECTED", sub: "RECONNECTING…", pillCls: "warn", dotCls: "warn", pulse: true,
    bar: [
      { w: 2, cls: "ok" }, { w: 2, cls: "muted" }, { w: 1, cls: "muted" }, { w: 3, cls: "muted" },
    ],
    stats: [
      { n: 2, l: "completed", cls: "ok" },
      { n: "—", l: "running",   cls: "muted" },
      { n: "—", l: "blocked",   cls: "muted" },
      { n: "—", l: "queued",    cls: "muted" },
      { n: "{elapsed}", l: "LAST KNOWN", big: true },
      { n: "00:18", l: "RECONNECTING", big: true, cls: "warn" },
      { n: 3, l: "DECISIONS",   big: true, cls: "warn" },
      { n: "—", l: "VIOLATIONS", big: true, cls: "muted" },
    ],
    tags: [
      { k: "stream:", v: ".dispatch/runs/7af3c1/events.jsonl" },
      { k: "last event:", v: "00:18 ago" },
    ],
  },
};

// ──────────────────────────────────────────────────────────
// Toasts + disconnect banner
// ──────────────────────────────────────────────────────────
function ScenarioOverlay({ scenario, onAction }) {
  if (scenario === "violation-flash") {
    return (
      <div className="toast-stack">
        <div className="toast toast-danger">
          <div className="toast-icon">!</div>
          <div className="toast-body">
            <div className="toast-title">Capability violation</div>
            <div className="toast-desc"><span className="mono">worker-c</span> attempted egress to <span className="mono">api.stripe.com</span> without grant — denied + agent paused</div>
            <div className="toast-meta">
              <span>4s ago</span>
              <span style={{color:"var(--fg-3)"}}>·</span>
              <span>2nd violation in this run</span>
            </div>
          </div>
          <div className="toast-actions">
            <button className="btn btn-ghost btn-sm" onClick={() => onAction && onAction("dismiss")}>dismiss</button>
            <button className="btn btn-warn btn-sm" onClick={() => onAction && onAction("review")}>review &amp; grant</button>
          </div>
        </div>
      </div>
    );
  }
  if (scenario === "disconnected") {
    return (
      <div className="disconnect-banner">
        <span className="dot warn dot-pulse" />
        <span><b>Event stream disconnected.</b> Last event was 18s ago. Reconnecting in 4s… (attempt 2/5)</span>
        <button className="btn btn-ghost btn-sm">retry now</button>
        <button className="btn btn-ghost btn-sm">show what we know</button>
      </div>
    );
  }
  return null;
}

// ──────────────────────────────────────────────────────────
// Empty state
// ──────────────────────────────────────────────────────────
function EmptyDashboard({ onStartRun }) {
  return (
    <div className="empty-shell">
      <div className="empty-hero">
        <div className="empty-icon">
          <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="8" y="14" width="48" height="36" rx="4"/>
            <path d="M8 22h48"/>
            <circle cx="14" cy="18" r="1.4" fill="currentColor"/>
            <circle cx="19" cy="18" r="1.4" fill="currentColor"/>
            <path d="M16 32l4 4 12-12" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1>No active run</h1>
        <p>Dispatch is idle. Start a run from a plan, or reattach to one of your recent runs.</p>
        <div className="empty-actions">
          <button className="btn btn-primary" onClick={onStartRun}>start a run</button>
          <button className="btn btn-ghost">attach to run…</button>
          <button className="btn btn-ghost">browse plans</button>
        </div>
        <div className="empty-cli mono">
          <span className="empty-cli-prompt">$</span>
          <span>de run --plan plans/plan-014.json --provider codex --detach</span>
        </div>
      </div>

      <div className="empty-grid">
        <div className="empty-card">
          <div className="empty-card-h">recent runs</div>
          <div className="empty-card-list">
            {window.DE_DATA.HISTORY.slice(0, 4).map(h => (
              <div key={h.id} className="empty-card-row">
                <span className={"dot " + (h.status === "completed" ? "ok" : h.status === "failed" ? "danger" : "muted")} />
                <span className="mono">{h.short}</span>
                <span style={{color:"var(--fg-2)"}}>{h.repo} · {h.plan}</span>
                <span style={{marginLeft:"auto", color:"var(--fg-3)"}}>{h.dur}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="empty-card">
          <div className="empty-card-h">plans in this repo</div>
          <div className="empty-card-list">
            {[
              { name: "plans/plan-014.json", desc: "Migrate billing to gRPC", ws: 8 },
              { name: "plans/plan-015.json", desc: "Cleanup deprecated handlers", ws: 4 },
              { name: "plans/draft-016.json", desc: "[draft] perf hardening", ws: 6 },
            ].map((p, i) => (
              <div key={i} className="empty-card-row">
                <span className="mono">{p.name}</span>
                <span style={{color:"var(--fg-2)"}}>{p.desc}</span>
                <span style={{marginLeft:"auto", color:"var(--fg-3)"}}>{p.ws} ws</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Plan tree search (wraps existing PlanTreePanel logic)
// ──────────────────────────────────────────────────────────
function PlanTreeWithSearch() {
  const D = window.DE_DATA;
  const [q, setQ] = sUseState("");
  const [collapsed, setCollapsed] = sUseState({});

  function matches(node) {
    if (!q) return true;
    const ql = q.toLowerCase();
    if (node.name.toLowerCase().includes(ql)) return true;
    if (node.children) return node.children.some(matches);
    return false;
  }

  function renderNode(node, depth) {
    const k = node.name + ":" + depth;
    const isCollapsed = collapsed[k];
    const visible = matches(node);
    if (!visible) return null;
    return (
      <div key={k} className="ptree-node" style={{ paddingLeft: depth * 14 }}>
        <div className="ptree-row" onClick={() => node.children && setCollapsed(c => ({...c, [k]: !isCollapsed}))}>
          {node.children && <span className="ptree-toggle">{isCollapsed ? "▸" : "▾"}</span>}
          {!node.children && <span className="ptree-toggle"> </span>}
          <span className={"dot " + (node.status === "ok" ? "ok" : node.status === "run" ? "run" : node.status === "warn" ? "warn" : "muted")} />
          <span className={"ptree-name" + (q && node.name.toLowerCase().includes(q.toLowerCase()) ? " hit" : "")}>
            {node.name}
          </span>
        </div>
        {node.children && !isCollapsed && node.children.map(c => renderNode(c, depth + 1))}
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-h">
        <span className="panel-h-name">Plan tree</span>
        <span className="panel-h-sub mono">{D.PLAN_TREE.name}</span>
        <div className="panel-h-spacer" />
        <div className="ptree-search">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="7" cy="7" r="4.5"/><path d="M11 11l3 3" strokeLinecap="round"/></svg>
          <input placeholder="filter (regex ok) — / to focus" value={q} onChange={(e)=>setQ(e.target.value)} />
          {q && <button className="ptree-clear" onClick={() => setQ("")}>esc</button>}
        </div>
      </div>
      <div className="panel-b ptree-body">
        <div className="ptree-root">{renderNode(D.PLAN_TREE, 0)}</div>
        <div className="ptree-footer">
          {q ? `filter: "${q}"` : "click rows to expand · / to filter"}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Run history with compare drawer
// ──────────────────────────────────────────────────────────
function RunHistoryCompare() {
  const D = window.DE_DATA;
  const [picked, setPicked] = sUseState(["7af3c1", "e2a4f9"]);

  function toggle(short) {
    if (picked.includes(short)) setPicked(picked.filter(p => p !== short));
    else if (picked.length < 2) setPicked([...picked, short]);
    else setPicked([picked[1], short]);
  }

  const all = [
    { short: "7af3c1", repo: "octane-api", plan: "plan-014", started: "now", dur: "00:47:23 (live)", status: "running",   workers: 10, decisions: 3, files: 47, tests: "87/142" },
    ...D.HISTORY.map(h => ({ short: h.short, repo: h.repo, plan: h.plan, started: relStart(h.started), dur: h.dur, status: h.status, workers: h.workers, decisions: h.decisions, files: 30 + Math.floor(Math.random()*20), tests: h.status === "failed" ? "120/142" : "142/142" })),
  ];

  const A = all.find(r => r.short === picked[0]);
  const B = all.find(r => r.short === picked[1]);

  return (
    <div className="panel">
      <div className="panel-h">
        <span className="panel-h-name">Run history</span>
        <span className="panel-h-sub">{all.length} total · pick 2 to compare</span>
        <div className="panel-h-spacer" />
        <span className="panel-h-tag mono">filter: octane-api</span>
      </div>
      <div className="panel-b" style={{padding: 0}}>
        <table className="rh-table">
          <thead>
            <tr>
              <th></th>
              <th>run</th>
              <th>repo · plan</th>
              <th>started</th>
              <th>duration</th>
              <th>status</th>
              <th>workers</th>
              <th>decisions</th>
              <th>tests</th>
            </tr>
          </thead>
          <tbody>
            {all.map(r => (
              <tr key={r.short} className={picked.includes(r.short) ? "rh-row picked" : "rh-row"}>
                <td>
                  <input type="checkbox"
                         checked={picked.includes(r.short)}
                         onChange={() => toggle(r.short)} />
                </td>
                <td><span className="mono">{r.short}</span></td>
                <td>{r.repo} · <span className="mono">{r.plan}</span></td>
                <td style={{color:"var(--fg-2)"}}>{r.started}</td>
                <td className="mono">{r.dur}</td>
                <td><span className={"pill " + (r.status === "running" ? "run" : r.status === "completed" ? "ok" : r.status === "failed" ? "danger" : "muted")}>{r.status}</span></td>
                <td className="mono">{r.workers}</td>
                <td className="mono">{r.decisions}</td>
                <td className="mono">{r.tests}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {picked.length === 2 && A && B && (
        <div className="rh-compare">
          <div className="rh-compare-h">
            <span>compare</span>
            <span className="mono">{A.short} ↔ {B.short}</span>
            <div className="panel-h-spacer" />
            <button className="btn btn-ghost btn-sm" onClick={() => setPicked([picked[0]])}>clear</button>
          </div>
          <div className="rh-compare-grid">
            {[
              ["duration",   A.dur,    B.dur],
              ["workers",    A.workers, B.workers],
              ["decisions",  A.decisions, B.decisions],
              ["files changed", A.files, B.files],
              ["tests",      A.tests,  B.tests],
              ["status",     A.status, B.status],
            ].map(([k, a, b]) => (
              <React.Fragment key={k}>
                <div className="rh-compare-k">{k}</div>
                <div className="rh-compare-v mono">{a}</div>
                <div className="rh-compare-arrow">→</div>
                <div className="rh-compare-v mono">{b}</div>
                <div className="rh-compare-delta">{deltaHint(k, a, b)}</div>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function relStart(seconds) {
  const abs = Math.abs(seconds);
  if (abs < 3600) return `${Math.floor(abs/60)}m ago`;
  if (abs < 86400) return `${Math.floor(abs/3600)}h ago`;
  return `${Math.floor(abs/86400)}d ago`;
}

function deltaHint(k, a, b) {
  if (typeof a === "number" && typeof b === "number") {
    const d = a - b;
    if (d === 0) return <span style={{color:"var(--fg-3)"}}>=</span>;
    if (d > 0)   return <span style={{color:"var(--warn)"}}>+{d}</span>;
    return <span style={{color:"var(--ok)"}}>{d}</span>;
  }
  return "";
}

window.DESCEN = {
  SCENARIOS, ScenarioRunHeader, ScenarioOverlay,
  EmptyDashboard, PlanTreeWithSearch, RunHistoryCompare
};
