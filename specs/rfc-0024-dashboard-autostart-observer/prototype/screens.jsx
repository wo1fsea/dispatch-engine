/* global React, DEUI */
const { useState: useState2, useEffect: useEffect2, useRef: useRef2, useMemo: useMemo2 } = React;
const D2 = window.DE_DATA;
const U = window.DEUI;

// ──────────────────────────────────────────────────────────
// Plan tree (recursive)
// ──────────────────────────────────────────────────────────
function TreeNode({ node, depth = 0, sel, onSel }) {
  const [open, setOpen] = useState2(true);
  const has = node.children && node.children.length > 0;
  const isSel = sel === node.name;
  const statusMap = {
    ok:    { tone: "ok",     label: "completed" },
    run:   { tone: "run",    label: "running"   },
    warn:  { tone: "warn",   label: "blocked"   },
    queue: { tone: "queue",  label: "queued"    },
  };
  const s = node.status ? statusMap[node.status] || statusMap.queue : null;
  return (
    <div className="tree-node">
      <div className={`tree-row ${isSel ? "sel" : ""}`}
           onClick={() => { onSel(node.name); if (has) setOpen(!open); }}>
        <span className="twist">{has ? (open ? "▼" : "▶") : ""}</span>
        {s ? (
          <span className={`tn-dot ${s.tone}`} title={s.label} />
        ) : (
          <span className="tn-dot empty" />
        )}
        <span className="ico">{has ? "▣" : "·"}</span>
        <span className="lab">{node.name}</span>
      </div>
      {has && open && (
        <div className="tree-children">
          {node.children.map((c, i) => <TreeNode key={i} node={c} depth={depth+1} sel={sel} onSel={onSel} />)}
        </div>
      )}
    </div>
  );
}

function PlanTreePanel() {
  const [sel, setSel] = useState2("ws-03 port-billing-handlers");
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Plan tree</span>
        <span className="sub">{D2.RUN.plan}</span>
      </div>
      <div className="panel-b" style={{padding: 6}}>
        <div className="tree">
          <TreeNode node={D2.PLAN_TREE} sel={sel} onSel={setSel} />
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Capability profiles table
// ──────────────────────────────────────────────────────────
function CapabilityTable({ onReview }) {
  const profiles = [
    { id: "coordinator-elevated", agents: ["coordinator-001"], grants: [["network",false],["pkg-install",true],["docker",true],["runtime-write",false],["github-issue",false]], status: "active", esc: 0, viol: 0 },
    { id: "worker-standard",      agents: ["worker-a","worker-b","worker-d"], grants: [["pkg-install",false],["runtime-write",false]], status: "active", esc: 0, viol: 0 },
    { id: "worker-extended",      agents: ["worker-c"], grants: [["network",false],["pkg-install",false]], status: "violation", esc: 1, viol: 1 },
    { id: "worker-docs",          agents: ["worker-e"], grants: [["runtime-write",false]], status: "queued", esc: 0, viol: 0 },
    { id: "reviewer-standard",    agents: ["reviewer-a","reviewer-b"], grants: [["runtime-write",false]], status: "active", esc: 0, viol: 0 },
    { id: "validator-standard",   agents: ["validator-a"], grants: [["test-exec",false],["network",false]], status: "active", esc: 0, viol: 0 },
    { id: "validator-extended",   agents: ["validator-b"], grants: [["test-exec",false],["docker",true],["network",false]], status: "queued", esc: 1, viol: 0 },
  ];
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Capability profiles</span>
        <span className="sub">7 profiles · 2 high-risk modes active · 1 violation · 2 escalations</span>
        <span className="panel-cta">
          {onReview && <button className="btn-sm primary" onClick={onReview}>Review escalation</button>}
        </span>
      </div>
      <div className="panel-b tight">
        <table className="cap-table">
          <thead>
            <tr>
              <th style={{width:"22%"}}>Profile</th>
              <th style={{width:"24%"}}>Bound to</th>
              <th>Grants</th>
              <th style={{width:90}}>Esc.</th>
              <th style={{width:90}}>Viol.</th>
              <th style={{width:120}}>Status</th>
            </tr>
          </thead>
          <tbody>
            {profiles.map(p => (
              <tr key={p.id}>
                <td className="profile">{p.id}</td>
                <td className="agent">{p.agents.join(", ")}</td>
                <td>
                  <div className="grants">
                    {p.grants.map(([k,hi]) => <span key={k} className={`gchip ${hi ? "hi" : ""}`}>{k}{hi ? " · hi-risk" : ""}</span>)}
                  </div>
                </td>
                <td style={{fontFamily:"var(--font-mono)", color: p.esc ? "var(--warn)" : "var(--fg-3)"}}>{p.esc}</td>
                <td style={{fontFamily:"var(--font-mono)", color: p.viol ? "var(--danger)" : "var(--fg-3)"}}>{p.viol}</td>
                <td>
                  <U.StatusPill status={p.status === "violation" ? "failed" : p.status === "queued" ? "queued" : "running"}>
                    {p.status}
                  </U.StatusPill>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Validator results
// ──────────────────────────────────────────────────────────
function ValidatorPanel() {
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Validators</span>
        <span className="sub">5 registered · 1 running · 2 passed · 1 blocked · 1 skipped</span>
      </div>
      <div className="panel-b tight">
        <div className="val-list">
          {D2.VALIDATORS.map(v => (
            <div key={v.id} className="val-row">
              <U.Dot status={v.status} pulse={v.status === "running"} />
              <div>
                <span className="vname">{v.name} {v.count && <span style={{color:"var(--fg-2)", fontFamily:"var(--font-mono)", fontSize:11}}>· {v.count}</span>}</span>
                <code className="vcmd">$ {v.cmd}</code>
                {v.note && <div style={{fontSize:10.5, color:"var(--warn)", marginTop:3, fontFamily:"var(--font-mono)"}}>{v.note}</div>}
              </div>
              <span className="vdur">{v.dur}</span>
              <U.StatusPill status={v.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Coordinator log tail (terminal)
// ──────────────────────────────────────────────────────────
function CoordLogPanel() {
  const [lines, setLines] = useState2(D2.COORD_LOG);
  const ref = useRef2(null);
  useEffect2(() => {
    let alive = true;
    const updates = [
      { pre: "INFO", msg: "<span class=\"k\">progress</span> ws-03=66% (8/11 files)" },
      { pre: "OK",   msg: "<span class=\"k\">worker-b</span> <span class=\"v\">file.write</span> billing/handlers/dispute.py (+91 −38)" },
      { pre: "INFO", msg: "<span class=\"k\">validator-a</span> 91/142 contract tests passed" },
      { pre: "WARN", pre_cls: "warn", msg: "<span class=\"k\">heartbeat</span> next host wakeup in ~5m" },
      { pre: "INFO", msg: "<span class=\"k\">reviewer-a</span> review.note refund.py: missing trailing context propagation" },
      { pre: "OK",   msg: "<span class=\"k\">worker-c</span> file.write invoice/handlers/list.py (+44 −22)" },
    ];
    let i = 0;
    function tick() {
      if (!alive) return;
      const u = updates[i % updates.length]; i++;
      const now = new Date();
      const ts = `0${now.getUTCHours() % 2 + 1}:${String(now.getUTCMinutes()).padStart(2,"0")}:${String(now.getUTCSeconds()).padStart(2,"0")}`;
      setLines(prev => [...prev.slice(-80), { ts, ...u }]);
      setTimeout(tick, 2400 + Math.random() * 2800);
    }
    const t = setTimeout(tick, 2000);
    return () => { alive = false; clearTimeout(t); };
  }, []);
  useEffect2(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  return (
    <div className="panel" style={{minHeight:0, display:"flex"}}>
      <div className="panel-h">
        <span className="title">Coordinator stdout</span>
        <span className="sub">.dispatch/runs/{D2.RUN.short}/logs/coordinator-001.stdout.log</span>
        <div className="actions">
          <span className="pill run"><U.Dot status="run" pulse /> live tail</span>
        </div>
      </div>
      <div className="panel-b tight" style={{flex:1, minHeight:0, padding:0, display:"flex"}}>
        <div className="term" ref={ref} style={{borderRadius:0, border:"none", flex:1}}>
          {lines.map((l, i) => (
            <div key={i} className="ln">
              <span className="ts">{l.ts}</span>
              <span className={`pre ${l.pre_cls || ""}`}>{l.pre.padEnd(4," ")}</span>
              <span className="msg" dangerouslySetInnerHTML={{__html: l.msg}} />
            </div>
          ))}
          <div className="ln"><span className="ts">{new Date().toISOString().slice(11,19)}</span><span className="pre">·</span><span className="msg"><span className="caret" /></span></div>
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Run history
// ──────────────────────────────────────────────────────────
function RunHistoryPanel() {
  return (
    <div className="panel">
      <div className="panel-h">
        <span className="title">Run history</span>
        <span className="sub">last 30 days · 5 of 47 shown</span>
        <div className="actions">
          <button className="tb-btn icon" title="Filter"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 3h12l-4.5 6v4l-3 1.5V9z" strokeLinejoin="round"/></svg></button>
          <button className="tb-btn icon" title="Export CSV"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10" strokeLinecap="round" strokeLinejoin="round"/></svg></button>
        </div>
      </div>
      <div className="panel-b tight">
        <table className="hist-table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Repo</th>
              <th>Plan</th>
              <th>Started</th>
              <th>Duration</th>
              <th>Workers</th>
              <th>Decisions</th>
              <th>Outcome</th>
            </tr>
          </thead>
          <tbody>
            {D2.HISTORY.map(h => (
              <tr key={h.id}>
                <td className="runid"><span className="acc">{h.short}</span></td>
                <td>{h.repo}</td>
                <td style={{fontFamily:"var(--font-mono)", fontSize:11, color:"var(--fg-2)"}}>{h.plan}</td>
                <td style={{color:"var(--fg-2)", fontFamily:"var(--font-mono)", fontSize:11}}>{U.fmtRel(h.started)}</td>
                <td style={{fontFamily:"var(--font-mono)", fontSize:11}}>{h.dur}</td>
                <td style={{fontFamily:"var(--font-mono)", fontSize:11}}>{h.workers}</td>
                <td style={{fontFamily:"var(--font-mono)", fontSize:11}}>{h.decisions}</td>
                <td>
                  <U.StatusPill status={h.status} />
                  {h.cancelReason && <span style={{marginLeft:8, color:"var(--fg-3)", fontFamily:"var(--font-mono)", fontSize:10.5}}>{h.cancelReason}</span>}
                  {h.failReason && <span style={{marginLeft:8, color:"var(--danger)", fontFamily:"var(--font-mono)", fontSize:10.5}}>{h.failReason}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────
// Agent detail screen
// ──────────────────────────────────────────────────────────
function AgentDetail({ agentId, onBack, onGrant }) {
  const a = D2.AGENTS.find(x => x.id === agentId) || D2.AGENTS[2]; // default worker-b

  // mini heartbeat history (40 ticks, mostly ok, a couple late)
  const ticks = useMemo2(() => {
    const out = [];
    for (let i = 0; i < 40; i++) {
      const r = Math.random();
      out.push(r > 0.92 ? "miss" : r > 0.82 ? "late" : "ok");
    }
    return out;
  }, [agentId]);

  return (
    <div style={{display:"flex", flexDirection:"column", gap:14}}>
      <div className="ad-head">
        <div>
          <div className="role-tag">{a.role}</div>
          <h2>{a.id}</h2>
          <div style={{marginTop:8, fontSize:13, color:"var(--fg-1)"}}>{a.task}</div>
          <div style={{marginTop:10, display:"flex", gap:8, flexWrap:"wrap"}}>
            <U.StatusPill status={a.status}><U.Dot status={a.status} pulse={a.status === "running"} /> {a.status}</U.StatusPill>
            <span className="pill muted" style={{textTransform:"none", letterSpacing:0}}>profile <b style={{color:"var(--fg-1)"}}>{a.profile}</b></span>
            <span className="pill muted" style={{textTransform:"none", letterSpacing:0}}>spawned by <b style={{color:"var(--fg-1)"}}>coordinator-001</b></span>
            <span className="pill muted" style={{textTransform:"none", letterSpacing:0}}>workstream <b style={{color:"var(--accent)"}}>ws-03</b></span>
          </div>
        </div>
        <div style={{display:"flex", gap:8, alignItems:"flex-start"}}>
          <button className="tb-btn icon" title="Back to agents" onClick={onBack}><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M10 3l-5 5 5 5" strokeLinecap="round" strokeLinejoin="round"/></svg></button>
          <button className="tb-btn icon" title="Tail logs"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 4h12M2 8h8M2 12h10" strokeLinecap="round"/></svg></button>
          <button className="tb-btn icon" title="View report"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 2h7l3 3v9H3z" strokeLinejoin="round"/><path d="M10 2v3h3M5 8h6M5 11h4" strokeLinecap="round"/></svg></button>
          <button className="tb-btn icon danger" title="Cancel agent"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="6"/><path d="M5 5l6 6M11 5l-6 6" strokeLinecap="round"/></svg></button>
        </div>
      </div>

      <div className="grid col-2">
        <div style={{display:"flex", flexDirection:"column", gap:14}}>
          <div className="panel">
            <div className="panel-h">
              <span className="title">Recent stdout</span>
              <span className="sub">.dispatch/runs/{D2.RUN.short}/logs/{a.id}.stdout.log</span>
              <div className="actions"><span className="pill run"><U.Dot status="run" pulse /> tailing</span></div>
            </div>
            <div className="panel-b tight" style={{padding:0}}>
              <div className="term" style={{borderRadius:0, border:"none", height:300}}>
                <div className="ln"><span className="ts">01:14:08</span><span className="pre">INFO</span><span className="msg"><span className="k">spawn</span> received prompt snapshot at /prompts/{a.id}.md</span></div>
                <div className="ln"><span className="ts">01:14:09</span><span className="pre">INFO</span><span className="msg"><span className="k">capability.profile</span> {a.profile} loaded (4 grants)</span></div>
                <div className="ln"><span className="ts">01:14:11</span><span className="pre">INFO</span><span className="msg"><span className="k">read</span> billing/handlers/charge.py (412 lines)</span></div>
                <div className="ln"><span className="ts">01:14:14</span><span className="pre">INFO</span><span className="msg"><span className="k">read</span> proto/billing.proto (89 lines)</span></div>
                <div className="ln"><span className="ts">01:14:22</span><span className="pre">INFO</span><span className="msg"><span className="k">grep</span> 'def charge' billing/ → 4 matches</span></div>
                <div className="ln"><span className="ts">01:18:51</span><span className="pre">OK</span><span className="msg"><span className="k">file.write</span> billing/handlers/charge.py (+82 −41)</span></div>
                <div className="ln"><span className="ts">01:21:02</span><span className="pre">INFO</span><span className="msg"><span className="k">test.run</span> tests/contract/test_billing.py::test_charge <span className="v">PASSED</span></span></div>
                <div className="ln"><span className="ts">01:21:04</span><span className="pre">INFO</span><span className="msg"><span className="k">test.run</span> tests/contract/test_billing.py::test_charge_idempotent <span className="v">PASSED</span></span></div>
                <div className="ln"><span className="ts">01:21:30</span><span className="pre">INFO</span><span className="msg"><span className="k">heartbeat</span> uptime=00:18:42</span></div>
                <div className="ln"><span className="ts">01:24:15</span><span className="pre">INFO</span><span className="msg"><span className="k">read</span> billing/handlers/refund.py (287 lines)</span></div>
                <div className="ln"><span className="ts">01:27:03</span><span className="pre">OK</span><span className="msg"><span className="k">file.write</span> billing/handlers/refund.py (+128 −62)</span></div>
                <div className="ln"><span className="ts">01:28:44</span><span className="pre">INFO</span><span className="msg"><span className="k">test.run</span> tests/contract/test_billing.py::test_refund <span className="v">PASSED</span></span></div>
                <div className="ln"><span className="ts">01:29:01</span><span className="pre">INFO</span><span className="msg"><span className="k">read</span> billing/handlers/dispute.py (412 lines)</span></div>
                <div className="ln"><span className="ts">01:29:45</span><span className="pre">·</span><span className="msg"><span className="caret" /></span></div>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-h">
              <span className="title">File scope · writes so far</span>
              <span className="sub">11 files · +301 / −163</span>
            </div>
            <div className="panel-b ad-files">
              {[
                ["new", "billing/handlers/__init__.py", "+22 −0"],
                ["mod", "billing/handlers/charge.py", "+82 −41"],
                ["mod", "billing/handlers/refund.py", "+128 −62"],
                ["new", "billing/grpc_server.py", "+47 −0"],
                ["mod", "billing/services/contract.py", "+18 −7"],
                ["del", "billing/rest/charges.py", "+0 −53"],
                ["mod", "tests/contract/test_billing.py", "+4 −0"],
                ["mod", "billing/handlers/dispute.py", "in progress…"],
              ].map(([v, f, ch], i) => (
                <div key={i} className="f">
                  <span className={`verb ${v === "mod" ? "mod" : v === "del" ? "del" : ""}`}>{v.toUpperCase()}</span>
                  <span style={{flex:1}}>{f}</span>
                  <span style={{color:"var(--fg-3)"}}>{ch}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:"flex", flexDirection:"column", gap:14}}>
          <div className="panel">
            <div className="panel-h">
              <span className="title">Heartbeat history</span>
              <span className="sub">last 40 ticks · 30s interval</span>
            </div>
            <div className="hb-mini">
              {ticks.map((t, i) => <div key={i} className={`tick ${t === "late" ? "late" : t === "miss" ? "miss" : ""}`} style={{height: `${30 + Math.random()*60}%`}} />)}
            </div>
            <div style={{display:"flex", justifyContent:"space-between", padding:"0 14px 12px", fontFamily:"var(--font-mono)", fontSize:10.5, color:"var(--fg-3)"}}>
              <span>20 min ago</span>
              <span style={{color:"var(--ok)"}}>{ticks.filter(t=>t==="ok").length} ok</span>
              <span style={{color:"var(--warn)"}}>{ticks.filter(t=>t==="late").length} late</span>
              <span style={{color:"var(--danger)"}}>{ticks.filter(t=>t==="miss").length} miss</span>
              <span>now</span>
            </div>
          </div>

          <div className="panel">
            <div className="panel-h">
              <span className="title">Agent metadata</span>
            </div>
            <dl className="kv">
              <dt>id</dt>             <dd><span className="acc">{a.id}</span></dd>
              <dt>role</dt>           <dd>{a.role}</dd>
              <dt>spawned by</dt>     <dd>coordinator-001</dd>
              <dt>spawned at</dt>     <dd>{U.fmtRel(-1680)}</dd>
              <dt>workstream</dt>     <dd>ws-03 port-billing-handlers</dd>
              <dt>capability</dt>     <dd>{a.profile}</dd>
              <dt>permission scope</dt><dd>billing/**, tests/contract/**</dd>
              <dt>provider</dt>       <dd>codex (exec, danger-full-access)</dd>
              <dt>prompt</dt>         <dd style={{color:"var(--accent)"}}>prompts/{a.id}.md ↗</dd>
              <dt>report</dt>         <dd style={{color:"var(--fg-3)"}}>reports/{a.id}.json — pending</dd>
            </dl>
          </div>

          <div className="panel">
            <div className="panel-h">
              <span className="title">Capability grant</span>
              <span className="sub">{a.profile}</span>
              <span className="panel-cta">
                {onGrant && <button className="btn-sm primary" onClick={onGrant}>Grant escalation…</button>}
              </span>
            </div>
            <div className="panel-b" style={{display:"flex", flexWrap:"wrap", gap:6}}>
              {a.caps.map(c => (
                <span key={c.k} className={`gchip ${c.hi ? "hi" : ""}`} style={{fontFamily:"var(--font-mono)", fontSize:10.5, padding:"3px 8px", border:"1px solid var(--line-2)", background: c.hi ? "var(--warn-soft)" : "var(--bg-2)", borderRadius:4, color: c.hi ? "var(--warn)" : "var(--fg-1)"}}>
                  {c.k}{c.hi ? " · hi-risk" : ""}
                </span>
              ))}
              <div style={{flexBasis:"100%", marginTop:8, fontSize:11.5, color:"var(--fg-2)"}}>
                Exercised so far: <span style={{fontFamily:"var(--font-mono)", color:"var(--fg-1)"}}>file.write, test.run, grep, read</span>
              </div>
              <div style={{flexBasis:"100%", fontSize:11.5, color:"var(--fg-2)"}}>
                Escalations: <span style={{fontFamily:"var(--font-mono)", color:"var(--fg-3)"}}>none</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

window.DESCREENS = { PlanTreePanel, CapabilityTable, ValidatorPanel, CoordLogPanel, RunHistoryPanel, AgentDetail };
