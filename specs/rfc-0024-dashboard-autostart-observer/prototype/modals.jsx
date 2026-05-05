// ──────────────────────────────────────────────────────────
// Modals: Cancel run · Approve decision · Grant capability ·
//         Keyboard help · Multi-run switcher
// All modals share the .modal-bg / .modal shell.
// ──────────────────────────────────────────────────────────
const { useState: mUseState, useEffect: mUseEffect, useRef: mUseRef } = React;

// generic shell
function ModalShell({ title, sub, onClose, children, footer, width = 640, danger }) {
  mUseEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="modal-bg" onClick={onClose}>
      <div className={"modal modal-confirm" + (danger ? " danger" : "")}
           style={{ width, maxWidth: "92vw" }}
           onClick={e => e.stopPropagation()}>
        <div className="modal-h">
          <span className="title">{title}</span>
          {sub && <span className="sub">{sub}</span>}
          <button className="x" onClick={onClose} title="close (esc)">✕</button>
        </div>
        <div className="modal-b modal-b-form">
          {children}
        </div>
        {footer && <div className="modal-f">{footer}</div>}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Cancel run confirm
// ──────────────────────────────────────────────────────────
function CancelRunModal({ onClose, onConfirm }) {
  const D = window.DE_DATA;
  const [reason, setReason] = mUseState("");
  const [killInflight, setKillInflight] = mUseState(true);
  const [keepArtifacts, setKeepArtifacts] = mUseState(true);
  const affected = D.AGENTS.filter(a => a.status === "running" || a.status === "blocked");
  const inflight = D.WORKSTREAMS.filter(w => w.status === "running" || w.status === "blocked");
  const valid = reason.trim().length >= 4;

  return (
    <ModalShell
      danger
      width={620}
      title={<><span style={{color:"var(--danger)"}}>⏹</span> Cancel run · <span className="mono">{D.RUN.short}</span></>}
      sub="this stops the coordinator and ALL workers"
      onClose={onClose}
      footer={(
        <>
          <span className="mf-hint">cmd: <span className="mono">de cancel {D.RUN.short} --reason "…"{killInflight ? " --kill-inflight" : ""}{!keepArtifacts ? " --purge-artifacts" : ""}</span></span>
          <div className="mf-actions">
            <button className="btn btn-ghost" onClick={onClose}>keep running</button>
            <button className={"btn btn-danger" + (valid ? "" : " disabled")} disabled={!valid}
                    onClick={() => valid && onConfirm({reason, killInflight, keepArtifacts})}>
              cancel run
            </button>
          </div>
        </>
      )}
    >
      <div className="mform">
        <div className="mform-row">
          <label className="mform-label">reason <span className="req">*</span></label>
          <textarea
            className="mform-input mono"
            rows={2}
            placeholder="why are you cancelling? (required, ≥4 chars — surfaces in run history & audit log)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            autoFocus
          />
        </div>

        <div className="mform-row">
          <label className="mform-label">in-flight tool calls</label>
          <div className="mform-toggle-row">
            <label className="mform-toggle">
              <input type="checkbox" checked={killInflight} onChange={(e)=>setKillInflight(e.target.checked)} />
              <span>kill in-flight tool calls (SIGTERM, then SIGKILL after 5s)</span>
            </label>
            <span className="mform-help">unchecked = let current step finish, then stop. recommended for file writes.</span>
          </div>
        </div>

        <div className="mform-row">
          <label className="mform-label">artifacts</label>
          <div className="mform-toggle-row">
            <label className="mform-toggle">
              <input type="checkbox" checked={keepArtifacts} onChange={(e)=>setKeepArtifacts(e.target.checked)} />
              <span>keep partial artifacts in <span className="mono">.dispatch/runs/{D.RUN.short}/</span></span>
            </label>
            <span className="mform-help">unchecked = purge logs, agent reports, validator output. cannot undo.</span>
          </div>
        </div>

        <div className="mform-impact">
          <div className="mform-impact-h">will affect</div>
          <div className="mform-impact-grid">
            <div className="mform-impact-cell">
              <div className="mform-impact-num">{affected.length}</div>
              <div className="mform-impact-lbl">live agents</div>
              <div className="mform-impact-list">
                {affected.slice(0, 4).map(a => (
                  <span key={a.id} className="mono">{a.id}</span>
                ))}
                {affected.length > 4 && <span style={{color:"var(--fg-3)"}}>+{affected.length-4} more</span>}
              </div>
            </div>
            <div className="mform-impact-cell">
              <div className="mform-impact-num">{inflight.length}</div>
              <div className="mform-impact-lbl">workstreams in-flight</div>
              <div className="mform-impact-list">
                {inflight.slice(0, 3).map(w => (
                  <span key={w.id} className="mono">{w.id} · {w.pct}%</span>
                ))}
              </div>
            </div>
            <div className="mform-impact-cell">
              <div className="mform-impact-num">3</div>
              <div className="mform-impact-lbl">decisions will be marked <span className="pill warn">cancelled</span></div>
            </div>
          </div>
        </div>
      </div>
    </ModalShell>
  );
}

// ──────────────────────────────────────────────────────────
// Approve / reject decision
// ──────────────────────────────────────────────────────────
function DecisionModal({ decision, onClose, onResolve }) {
  const D = window.DE_DATA;
  const dec = decision || D.DECISIONS[0];
  const [picked, setPicked] = mUseState(dec.options[0]);
  const [note, setNote] = mUseState("");

  // synthesize agent reasoning + alternatives + risk on the fly
  const reasoning = REASONING[dec.id] || REASONING.default;

  return (
    <ModalShell
      width={760}
      title={<>Decision · <span className="mono">{dec.id}</span></>}
      sub={<>raised by <span className="mono">{dec.agent}</span> · {dec.heartbeats} heartbeats ago</>}
      onClose={onClose}
      footer={(
        <>
          <span className="mf-hint">
            autonomous fallback in <b className="mono" style={{color:"var(--warn)"}}>04:32</b> ·
            picks <span className="mono">{reasoning.fallback}</span>
          </span>
          <div className="mf-actions">
            <button className="btn btn-ghost" onClick={() => onResolve({verdict:"defer"})}>defer to autonomous</button>
            <button className="btn btn-warn" onClick={() => onResolve({verdict:"reject", note})}>reject all</button>
            <button className="btn btn-primary" onClick={() => onResolve({verdict:"approve", choice:picked, note})}>
              approve · <span className="mono">{picked}</span>
            </button>
          </div>
        </>
      )}
    >
      <div className="mdec-q">{dec.q}</div>

      <div className="mdec-section-h">agent reasoning</div>
      <div className="mdec-reasoning mono">
        {reasoning.thought.map((line, i) => (
          <div key={i} className={"mdec-line" + (line.startsWith("//") ? " comment" : "")}>{line}</div>
        ))}
      </div>

      <div className="mdec-section-h">options &nbsp;<span className="mdec-section-sub">pick one</span></div>
      <div className="mdec-options">
        {dec.options.map(opt => {
          const meta = reasoning.options[opt] || { risk: "unknown", pros: [], cons: [] };
          const isPick = picked === opt;
          return (
            <div key={opt}
                 className={"mdec-opt" + (isPick ? " active" : "")}
                 onClick={() => setPicked(opt)}>
              <div className="mdec-opt-head">
                <span className="mdec-radio">{isPick ? <span className="dot ok" /> : <span className="dot muted" />}</span>
                <span className="mdec-opt-name mono">{opt}</span>
                <span className={"pill " + (meta.risk === "low" ? "ok" : meta.risk === "medium" ? "warn" : meta.risk === "high" ? "danger" : "muted")}>
                  risk: {meta.risk}
                </span>
                {meta.recommended && <span className="pill info">agent recommends</span>}
              </div>
              <div className="mdec-opt-body">
                <div className="mdec-opt-col">
                  <div className="mdec-opt-col-h">+ pros</div>
                  {meta.pros.map((p, i) => <div key={i} className="mdec-opt-li ok">+ {p}</div>)}
                </div>
                <div className="mdec-opt-col">
                  <div className="mdec-opt-col-h">− cons</div>
                  {meta.cons.map((c, i) => <div key={i} className="mdec-opt-li warn">− {c}</div>)}
                </div>
              </div>
              {meta.affects && (
                <div className="mdec-opt-affects">
                  affects: {meta.affects.map((a, i) => <span key={i} className="mono">{a}</span>)}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mdec-section-h">decision note &nbsp;<span className="mdec-section-sub">(optional, written to audit log)</span></div>
      <textarea
        className="mform-input mono"
        rows={2}
        placeholder="why this choice? — viewable later in run history"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
    </ModalShell>
  );
}

const REASONING = {
  "decision-014": {
    fallback: "in-process-shim",
    thought: [
      "// worker-d analysing rest gateway compat",
      "client traffic profile (last 7d):",
      "  · 87% gRPC-native paths via new clients",
      "  · 13% legacy REST clients (3 known partners, all wired through gateway)",
      "constraint: cannot break partner ABI in this run (plan §4.2)",
      "two viable paths emerged after reading envoy/transcoder.md and",
      "scratch/proxy-bench.md — recommending in-process-shim for blast radius.",
    ],
    options: {
      "envoy-transcoder": {
        risk: "medium", pros: [
          "battle-tested in prod by 2 sister teams",
          "config is declarative, lives in repo",
          "good observability via envoy admin",
        ], cons: [
          "+1 hop latency (~3-7ms p99 measured in scratch/proxy-bench.md)",
          "requires envoy 1.28+ on every edge node — not yet baked",
          "yaml config drift risk vs proto truth",
        ], affects: ["ws-05", "infra/edge", "deploy-pipeline"],
      },
      "in-process-shim": {
        recommended: true,
        risk: "low", pros: [
          "no extra hop, no extra dep",
          "shim lives next to handlers, evolves with proto",
          "blast radius = 1 service",
        ], cons: [
          "boilerplate per endpoint (~30 LOC)",
          "must hand-write field-mapping for 2 oneof fields",
        ], affects: ["ws-05", "billing/gateway/"],
      },
      "both": {
        risk: "high", pros: ["belt-and-suspenders during rollout"],
        cons: ["doubles the surface area to maintain", "config divergence almost certain", "out of scope for this run"],
        affects: ["ws-05", "ws-06", "infra/edge"],
      },
    }
  },
  default: {
    fallback: "—", thought: ["// no reasoning recorded by agent"],
    options: {},
  }
};

// ──────────────────────────────────────────────────────────
// Capability escalation review
// ──────────────────────────────────────────────────────────
function CapabilityModal({ request, onClose, onResolve }) {
  const req = request || DEFAULT_CAP_REQUEST;
  const [scope, setScope] = mUseState(req.requestedScope);
  const [ttlMin, setTtlMin] = mUseState(req.ttlMin);

  const TTLS = [15, 30, 60, 120, 240];

  return (
    <ModalShell
      width={720}
      title={<>Grant capability · <span className="mono">{req.agent}</span></>}
      sub={<>requested {req.requestedAt} · profile <span className="mono">{req.currentProfile}</span> → <span className="mono">{req.targetProfile}</span></>}
      onClose={onClose}
      footer={(
        <>
          <span className="mf-hint">grant TTL: <b className="mono">{ttlMin}m</b> · auto-revokes at <b className="mono">{plusMinutes(ttlMin)}</b></span>
          <div className="mf-actions">
            <button className="btn btn-ghost" onClick={() => onResolve({verdict:"deny"})}>deny</button>
            <button className="btn btn-warn" onClick={() => onResolve({verdict:"deny-and-pause"})}>deny + pause agent</button>
            <button className="btn btn-primary" onClick={() => onResolve({verdict:"grant", scope, ttlMin})}>
              grant for {ttlMin}m
            </button>
          </div>
        </>
      )}
    >
      <div className="mcap-reason">
        <div className="mform-label">why agent is asking</div>
        <div className="mcap-reason-body mono">{req.reason}</div>
      </div>

      <div className="mform-label">capability diff</div>
      <div className="mcap-diff">
        {req.diff.map((row, i) => (
          <div key={i} className={"mcap-diff-row " + row.kind}>
            <span className="mcap-diff-sym">
              {row.kind === "add" ? "+" : row.kind === "remove" ? "−" : " "}
            </span>
            <span className="mono">{row.cap}</span>
            <span className="mcap-diff-why">{row.why}</span>
          </div>
        ))}
      </div>

      <div className="mform-label">scope (what this allows)</div>
      <div className="mcap-scope">
        {req.scopeAll.map(s => {
          const checked = scope.includes(s.k);
          return (
            <label key={s.k} className={"mcap-scope-row" + (checked ? " active" : "") + (s.dangerous ? " dangerous" : "")}>
              <input type="checkbox" checked={checked}
                     onChange={(e) => {
                       setScope(e.target.checked ? [...scope, s.k] : scope.filter(x => x !== s.k));
                     }} />
              <div className="mcap-scope-meta">
                <div className="mcap-scope-k mono">{s.k}</div>
                <div className="mcap-scope-d">{s.desc}</div>
              </div>
              {s.dangerous && <span className="pill danger">elevated</span>}
            </label>
          );
        })}
      </div>

      <div className="mform-label">TTL</div>
      <div className="mcap-ttl">
        {TTLS.map(m => (
          <button key={m}
                  className={"mcap-ttl-btn" + (ttlMin === m ? " active" : "")}
                  onClick={() => setTtlMin(m)}>
            {m < 60 ? `${m}m` : `${m/60}h`}
          </button>
        ))}
        <span className="mcap-ttl-hint">scope auto-revokes after TTL · audit recorded</span>
      </div>

      <div className="mcap-prior">
        <div className="mform-label">prior violations by this agent</div>
        {req.priorViolations.length === 0
          ? <div className="mcap-prior-none">no prior violations on file</div>
          : req.priorViolations.map((v, i) => (
              <div key={i} className="mcap-prior-row">
                <span className="mono" style={{color:"var(--danger)"}}>!</span>
                <span className="mono">{v.when}</span>
                <span>{v.what}</span>
              </div>
            ))
        }
      </div>
    </ModalShell>
  );
}

function plusMinutes(m) {
  const d = new Date(Date.now() + m * 60 * 1000);
  const z = (n) => String(n).padStart(2, "0");
  return `${z(d.getUTCHours())}:${z(d.getUTCMinutes())}Z`;
}

const DEFAULT_CAP_REQUEST = {
  agent: "worker-c",
  requestedAt: "00:21:08",
  currentProfile: "worker-extended",
  targetProfile: "worker-extended+net.stripe",
  reason: "I need to call api.stripe.com/v1/charges to verify the new gRPC handler returns the same payload as the old REST one. This is for trace replay validation only — no writes, no auth tokens used outside this scope.",
  requestedScope: ["network.egress.api.stripe.com", "network.egress.dns"],
  scopeAll: [
    { k: "network.egress.api.stripe.com", desc: "outbound HTTPS to api.stripe.com only" },
    { k: "network.egress.dns",            desc: "DNS resolution for above hostname" },
    { k: "network.egress.*",              desc: "outbound to anywhere on the internet", dangerous: true },
    { k: "secrets.read.STRIPE_TEST_KEY",  desc: "read the project's Stripe test key", dangerous: true },
  ],
  ttlMin: 30,
  diff: [
    { kind: "context", cap: "fs.read /workspace/**",     why: "(unchanged)" },
    { kind: "context", cap: "fs.write /workspace/**",    why: "(unchanged)" },
    { kind: "add",     cap: "network.egress.api.stripe.com", why: "for trace replay" },
    { kind: "add",     cap: "network.egress.dns",            why: "needed by above" },
    { kind: "remove",  cap: "shell.exec.git",                why: "not needed for this scope" },
  ],
  priorViolations: [
    { when: "01:21:08", what: "attempted egress to api.stripe.com without grant — denied" },
  ],
};

// ──────────────────────────────────────────────────────────
// Keyboard help overlay
// ──────────────────────────────────────────────────────────
function KeyboardHelpModal({ onClose }) {
  const groups = [
    { name: "navigation", items: [
      ["g o", "go to overview"],
      ["g a", "go to agents"],
      ["g p", "go to plan"],
      ["g d", "go to decisions"],
      ["g c", "go to capabilities"],
      ["g v", "go to validators"],
      ["g h", "go to run history"],
      ["esc", "close modal / back"],
    ]},
    { name: "actions", items: [
      ["c",   "open coordinator log tail"],
      ["s",   "open status JSON"],
      ["x",   "cancel run"],
      ["/",   "focus search (in plan / agents)"],
      ["f",   "focus event-stream filter"],
      [".",   "pause / resume event stream"],
    ]},
    { name: "decisions & capabilities", items: [
      ["1-9", "approve nth option"],
      ["a",   "approve current decision"],
      ["r",   "reject current decision"],
      ["G",   "grant capability (in cap modal)"],
      ["D",   "deny capability"],
    ]},
    { name: "view", items: [
      ["?",   "show this help"],
      ["t",   "cycle theme"],
      ["+ −", "zoom in / out"],
    ]},
  ];

  return (
    <ModalShell
      width={720}
      title="Keyboard shortcuts"
      sub="press ? again to dismiss"
      onClose={onClose}
    >
      <div className="mkbd-grid">
        {groups.map(g => (
          <div key={g.name} className="mkbd-col">
            <div className="mkbd-col-h">{g.name}</div>
            {g.items.map(([k, label], i) => (
              <div key={i} className="mkbd-row">
                <span className="mkbd-key">
                  {k.split(" ").map((part, j) => (
                    <React.Fragment key={j}>
                      {j > 0 && <span className="mkbd-key-sep">then</span>}
                      <kbd>{part}</kbd>
                    </React.Fragment>
                  ))}
                </span>
                <span className="mkbd-lbl">{label}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </ModalShell>
  );
}

// ──────────────────────────────────────────────────────────
// Multi-run switcher (popover anchored under the breadcrumb)
// ──────────────────────────────────────────────────────────
function RunSwitcher({ runs, currentId, onPick, anchorRef, onClose }) {
  const ref = mUseRef(null);
  const [pos, setPos] = mUseState({ top: 0, left: 0 });
  React.useLayoutEffect(() => {
    if (anchorRef && anchorRef.current) {
      const r = anchorRef.current.getBoundingClientRect();
      setPos({ top: r.bottom + 8, left: r.left });
    }
  }, [anchorRef]);
  mUseEffect(() => {
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

  return (
    <div className="run-switcher" ref={ref} style={{ top: pos.top, left: pos.left }}>
      <div className="run-switcher-h">
        <span>active runs</span>
        <span className="hint">{runs.length} live</span>
      </div>
      {runs.map(r => (
        <div key={r.id} className={"run-switcher-row" + (r.id === currentId ? " active" : "")}
             onClick={() => onPick(r.id)}>
          <span className={"dot " + (r.status === "running" ? "ok" : r.status === "waiting" ? "warn" : r.status === "failed" ? "danger" : "muted")} />
          <div className="run-switcher-meta">
            <div className="run-switcher-name">
              <span className="mono">{r.short}</span>
              <span style={{color:"var(--fg-2)"}}>{r.repo}</span>
            </div>
            <div className="run-switcher-sub">
              <span>{r.plan}</span>
              <span style={{color:"var(--fg-3)"}}>·</span>
              <span>{r.elapsed} elapsed</span>
              <span style={{color:"var(--fg-3)"}}>·</span>
              <span>{r.workers} agents</span>
            </div>
          </div>
          <span className={"pill " + (r.status === "running" ? "ok" : r.status === "waiting" ? "warn" : r.status === "failed" ? "danger" : "muted")}>{r.status}</span>
        </div>
      ))}
      <div className="run-switcher-foot">
        <span className="mono">de list --active</span>
      </div>
    </div>
  );
}

window.DEMODALS = {
  ModalShell, CancelRunModal, DecisionModal, CapabilityModal,
  KeyboardHelpModal, RunSwitcher, DEFAULT_CAP_REQUEST
};
