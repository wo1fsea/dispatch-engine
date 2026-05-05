// Dispatch Engine Dashboard — mock data store
// Simulates an active run with coordinator, workers, reviewers, validators,
// streaming events, heartbeats, decisions, capabilities, validators, history.

const RUN = {
  id: "run-2026-05-05T05-12-44Z-7af3c1",
  short: "7af3c1",
  repo: "wo1fsea/octane-api",
  repoPath: "~/code/octane-api",
  plan: "plans/plan-014.json",
  provider: "codex",
  mode: "detached",
  startedAt: Date.now() - 1000 * 60 * 47, // 47 min ago
  status: "running",
  coordinator: "coordinator-001",
  objective: "Migrate billing-service from REST to gRPC, preserve external API surface, add contract tests",
};

const WORKSTREAMS = [
  { id: "ws-01", name: "Generate proto schemas from OpenAPI spec",          assignee: "worker-a", status: "completed", pct: 100, started: -42*60, ended: -36*60, files: 4 },
  { id: "ws-02", name: "Scaffold gRPC service stubs (Python)",              assignee: "worker-a", status: "completed", pct: 100, started: -36*60, ended: -28*60, files: 7 },
  { id: "ws-03", name: "Port BillingService handlers to gRPC",              assignee: "worker-b", status: "running",   pct: 64,  started: -28*60, ended: null,    files: 11 },
  { id: "ws-04", name: "Port InvoiceService handlers to gRPC",              assignee: "worker-c", status: "running",   pct: 31,  started: -22*60, ended: null,    files: 8 },
  { id: "ws-05", name: "Update REST gateway to proxy gRPC backend",         assignee: "worker-d", status: "blocked",   pct: 18,  started: -16*60, ended: null,    files: 3, blockedReason: "decision-014 pending" },
  { id: "ws-06", name: "Contract tests (proto-replay against staging)",     assignee: "reviewer-a", status: "queued", pct: 0,   started: null,   ended: null,    files: 0 },
  { id: "ws-07", name: "Migration runbook + rollback procedure",            assignee: "worker-e", status: "queued", pct: 0,   started: null,   ended: null,    files: 0 },
  { id: "ws-08", name: "Performance baseline + load harness",               assignee: "validator-a", status: "queued", pct: 0,   started: null,   ended: null,    files: 0 },
];

const AGENTS = [
  { id: "coordinator-001", role: "coordinator", status: "running", task: "Orchestrating workstreams; awaiting decision on gateway proxy strategy", profile: "coordinator-elevated", caps: [{k:"network",hi:false},{k:"pkg-install",hi:true},{k:"docker",hi:true},{k:"runtime-write",hi:false}], hb: "ok", lastHb: -22, files: 0, exec: "codex exec --sandbox danger-full-access" },
  { id: "worker-a",        role: "worker",      status: "completed", task: "Generated proto schemas + gRPC stubs (ws-01, ws-02)", profile: "worker-standard", caps: [{k:"pkg-install",hi:false},{k:"runtime-write",hi:false}], hb: "ok", lastHb: -2*60, files: 11 },
  { id: "worker-b",        role: "worker",      status: "running",   task: "Porting BillingService.charge / refund / dispute handlers to gRPC", profile: "worker-standard", caps: [{k:"pkg-install",hi:false},{k:"runtime-write",hi:false}], hb: "ok", lastHb: -8, files: 11 },
  { id: "worker-c",        role: "worker",      status: "running",   task: "Porting InvoiceService.list / get / pdfRender handlers", profile: "worker-extended", caps: [{k:"network",hi:false},{k:"pkg-install",hi:false}], hb: "late", lastHb: -94, files: 8 },
  { id: "worker-d",        role: "worker",      status: "blocked",   task: "REST gateway: blocked on decision-014 (envoy vs in-proc proxy)", profile: "worker-standard", caps: [{k:"runtime-write",hi:false}], hb: "ok", lastHb: -45, files: 3 },
  { id: "worker-e",        role: "worker",      status: "queued",    task: "Migration runbook + rollback (ws-07)", profile: "worker-docs", caps: [{k:"runtime-write",hi:false}], hb: "—", lastHb: null, files: 0 },
  { id: "reviewer-a",      role: "reviewer",    status: "running",   task: "Reviewing handler ports against API contract (PR draft #284)", profile: "reviewer-standard", caps: [{k:"runtime-write",hi:false}], hb: "ok", lastHb: -14, files: 0 },
  { id: "reviewer-b",      role: "reviewer",    status: "queued",    task: "Awaiting ws-03/ws-04 completion before contract review", profile: "reviewer-standard", caps: [{k:"runtime-write",hi:false}], hb: "—", lastHb: null, files: 0 },
  { id: "validator-a",     role: "validator",   status: "running",   task: "pytest tests/contract — 142 collected, 87 passed, 0 failed so far", profile: "validator-standard", caps: [{k:"test-exec",hi:false},{k:"network",hi:false}], hb: "ok", lastHb: -3, files: 0 },
  { id: "validator-b",     role: "validator",   status: "queued",    task: "k6 perf baseline (waits on ws-08)", profile: "validator-extended", caps: [{k:"test-exec",hi:false},{k:"docker",hi:true},{k:"network",hi:false}], hb: "—", lastHb: null, files: 0 },
];

const DECISIONS = [
  { id: "decision-014", q: "Use Envoy gRPC-JSON transcoding or in-process REST shim for backwards compat?", agent: "worker-d", since: -16*60, options: ["envoy-transcoder", "in-process-shim", "both"], heartbeats: 2, severity: "info" },
  { id: "decision-015", q: "Drop deprecated /v1/charges.refund endpoint or keep until Q3?", agent: "coordinator-001", since: -8*60, options: ["drop-now", "keep-until-q3"], heartbeats: 1, severity: "info" },
  { id: "decision-016", q: "validator-a found 3 contract drift cases — accept tightened schema or open ticket?", agent: "validator-a", since: -3*60, options: ["accept-tightened", "open-ticket", "rollback"], heartbeats: 0, severity: "warn" },
];

const ALERTS = [
  { id: "a1", level: "warn", msg: "worker-c heartbeat late (94s, threshold 60s)", who: "worker-c · ws-04", when: -94 },
  { id: "a2", level: "danger", msg: "Protocol violation: capability overreach — worker-c attempted network egress without grant", who: "worker-c · capability.violation", when: -120 },
  { id: "a3", level: "warn", msg: "Validator schema-repair: validator-a report missing capabilities_exercised", who: "validator-a · schema.repair", when: -180 },
];

const HISTORY = [
  { id: "run-...e2a4f9", short: "e2a4f9", repo: "octane-api", plan: "plan-013", started: -2*3600, dur: "1h 14m", status: "completed", workers: 6, decisions: 4 },
  { id: "run-...c8810a", short: "c8810a", repo: "octane-api", plan: "plan-012", started: -8*3600, dur: "42m",   status: "completed", workers: 4, decisions: 1 },
  { id: "run-...91be20", short: "91be20", repo: "octane-api", plan: "plan-011", started: -1*86400, dur: "2h 03m", status: "cancelled", workers: 7, decisions: 6, cancelReason: "user requested rollback" },
  { id: "run-...6604fe", short: "6604fe", repo: "ledger-svc", plan: "plan-007", started: -2*86400, dur: "33m",   status: "failed",    workers: 3, decisions: 2, failReason: "validator-a: 12 contract failures" },
  { id: "run-...a1d33c", short: "a1d33c", repo: "ledger-svc", plan: "plan-006", started: -3*86400, dur: "1h 47m", status: "completed", workers: 5, decisions: 3 },
];

// validators
const VALIDATORS = [
  { id: "v1", name: "pytest tests/contract",            cmd: "pytest -q tests/contract --maxfail=1", agent: "validator-a", status: "running", dur: "00:08:42", count: "87/142" },
  { id: "v2", name: "ruff + mypy strict",               cmd: "ruff check . && mypy --strict billing/", agent: "validator-c", status: "passed",  dur: "00:01:14" },
  { id: "v3", name: "proto compatibility check",        cmd: "buf breaking --against .git#branch=main", agent: "validator-c", status: "passed",  dur: "00:00:18" },
  { id: "v4", name: "openapi → gRPC trace replay",      cmd: "scripts/replay-traces.py --bench staging-7d", agent: "validator-a", status: "blocked", dur: "—", note: "waits on ws-04" },
  { id: "v5", name: "k6 baseline (10 RPS, 5 min)",      cmd: "k6 run perf/baseline.js --vus 10 --duration 5m", agent: "validator-b", status: "skipped", dur: "—", note: "scheduled after ws-08" },
];

// plan tree
const PLAN_TREE = {
  name: "plan-014.json",
  children: [
    { name: "phase: schema", status: "ok", children: [
      { name: "ws-01 generate-protos", status: "ok" },
      { name: "ws-02 scaffold-stubs",  status: "ok" },
    ]},
    { name: "phase: implement", status: "run", children: [
      { name: "ws-03 port-billing-handlers",  status: "run" },
      { name: "ws-04 port-invoice-handlers",  status: "run" },
      { name: "ws-05 update-rest-gateway",    status: "warn" },
    ]},
    { name: "phase: validate", status: "muted", children: [
      { name: "ws-06 contract-tests",       status: "muted" },
      { name: "ws-07 migration-runbook",    status: "muted" },
      { name: "ws-08 perf-baseline",        status: "muted" },
    ]},
  ],
};

// streaming events generator (timestamps relative to NOW)
const EVENT_TEMPLATES = [
  { lvl: "info",  src: "coord",   tpl: "<span class=\"key\">workstream.assigned</span> <span class=\"acc\">ws-04</span> → <span class=\"val\">worker-c</span>" },
  { lvl: "ok",    src: "worker",  tpl: "<span class=\"acc\">worker-b</span> <span class=\"key\">file.write</span> <span class=\"val\">billing/handlers/charge.py</span> (+82 −41)" },
  { lvl: "info",  src: "runtime", tpl: "<span class=\"key\">agent.heartbeat</span> <span class=\"acc\">worker-b</span> uptime=<span class=\"val\">00:18:42</span>" },
  { lvl: "info",  src: "worker",  tpl: "<span class=\"acc\">worker-c</span> <span class=\"key\">test.run</span> tests/contract/test_invoice.py::test_list <span class=\"val\">PASSED</span>" },
  { lvl: "info",  src: "worker",  tpl: "<span class=\"acc\">worker-c</span> <span class=\"key\">test.run</span> tests/contract/test_invoice.py::test_get <span class=\"val\">PASSED</span>" },
  { lvl: "warn",  src: "runtime", tpl: "<span class=\"key\">agent.heartbeat.late</span> worker-c, last=<span class=\"val\">94s ago</span> threshold=60s" },
  { lvl: "info",  src: "coord",   tpl: "<span class=\"key\">decision.opened</span> <span class=\"acc\">decision-016</span> by validator-a (severity=warn)" },
  { lvl: "ok",    src: "worker",  tpl: "<span class=\"acc\">worker-b</span> <span class=\"key\">file.write</span> <span class=\"val\">billing/handlers/refund.py</span> (+128 −62)" },
  { lvl: "info",  src: "runtime", tpl: "<span class=\"key\">capability.profile.granted</span> validator-b → <span class=\"val\">validator-extended</span> [docker, network, test-exec]" },
  { lvl: "error", src: "runtime", tpl: "<span class=\"key\">capability.violation</span> <span class=\"acc\">worker-c</span> attempted network egress to api.stripe.com (denied)" },
  { lvl: "info",  src: "worker",  tpl: "<span class=\"acc\">reviewer-a</span> <span class=\"key\">review.note</span> charge.py: handler signature drifts from .proto (line 47)" },
  { lvl: "ok",    src: "worker",  tpl: "<span class=\"acc\">validator-a</span> <span class=\"key\">test.run</span> tests/contract/test_billing.py::test_charge_idempotent <span class=\"val\">PASSED</span>" },
  { lvl: "info",  src: "coord",   tpl: "<span class=\"key\">progress</span> ws-03 = <span class=\"val\">64%</span> (7/11 files modified)" },
  { lvl: "info",  src: "worker",  tpl: "<span class=\"acc\">worker-b</span> <span class=\"key\">grep</span> 'def charge' billing/ → 4 hits" },
  { lvl: "info",  src: "runtime", tpl: "<span class=\"key\">agent.heartbeat</span> <span class=\"acc\">coordinator-001</span> uptime=<span class=\"val\">00:47:12</span>" },
  { lvl: "ok",    src: "worker",  tpl: "<span class=\"acc\">validator-a</span> <span class=\"key\">test.run</span> tests/contract/test_invoice.py::test_pdf_render <span class=\"val\">PASSED</span>" },
  { lvl: "info",  src: "worker",  tpl: "<span class=\"acc\">worker-c</span> <span class=\"key\">file.read</span> openapi/invoice.yaml" },
];

// pre-seed log lines for coordinator stdout
const COORD_LOG = [
  { ts: "00:42:01", pre: "INFO",  msg: "<span class=\"k\">coord</span> launched <span class=\"v\">codex exec --sandbox danger-full-access</span>" },
  { ts: "00:42:03", pre: "INFO",  msg: "<span class=\"k\">plan</span> imported plans/plan-014.json (8 workstreams)" },
  { ts: "00:42:04", pre: "INFO",  msg: "<span class=\"k\">spawn</span> worker-a → <span class=\"v\">ws-01 generate-protos</span>" },
  { ts: "00:48:11", pre: "OK",    msg: "<span class=\"k\">worker-a</span> reported completion (4 files, validator passed)" },
  { ts: "00:48:12", pre: "INFO",  msg: "<span class=\"k\">spawn</span> worker-a → <span class=\"v\">ws-02 scaffold-stubs</span>" },
  { ts: "00:56:38", pre: "OK",    msg: "<span class=\"k\">worker-a</span> reported completion (7 files)" },
  { ts: "00:56:39", pre: "INFO",  msg: "<span class=\"k\">spawn</span> worker-b → <span class=\"v\">ws-03 port-billing-handlers</span>" },
  { ts: "01:02:14", pre: "INFO",  msg: "<span class=\"k\">spawn</span> worker-c → <span class=\"v\">ws-04 port-invoice-handlers</span>" },
  { ts: "01:08:51", pre: "INFO",  msg: "<span class=\"k\">spawn</span> worker-d → <span class=\"v\">ws-05 update-rest-gateway</span>" },
  { ts: "01:10:19", pre: "INFO",  msg: "<span class=\"k\">spawn</span> reviewer-a → <span class=\"v\">PR draft #284</span>" },
  { ts: "01:14:02", pre: "WARN",  pre_cls: "warn", msg: "<span class=\"k\">decision.opened</span> decision-014 (worker-d): envoy-transcoder vs in-process-shim?" },
  { ts: "01:14:02", pre: "INFO",  msg: "<span class=\"k\">worker-d</span> blocked, awaiting decision-014" },
  { ts: "01:18:30", pre: "INFO",  msg: "<span class=\"k\">spawn</span> validator-a → <span class=\"v\">contract tests + trace replay</span>" },
  { ts: "01:21:08", pre: "ERR",   pre_cls: "err", msg: "<span class=\"k\">capability.violation</span> worker-c attempted network egress (denied)" },
  { ts: "01:21:09", pre: "WARN",  pre_cls: "warn", msg: "<span class=\"k\">protocol.violation</span> recorded; worker-c paused for review" },
  { ts: "01:22:42", pre: "INFO",  msg: "<span class=\"k\">worker-c</span> resumed after coordinator review (capability scope confirmed)" },
  { ts: "01:26:50", pre: "OK",    msg: "<span class=\"k\">validator-a</span> 87/142 contract tests passed (in progress)" },
  { ts: "01:28:33", pre: "WARN",  pre_cls: "warn", msg: "<span class=\"k\">decision.opened</span> decision-016 (validator-a): contract drift in 3 cases" },
  { ts: "01:29:04", pre: "INFO",  msg: "<span class=\"k\">progress</span> ws-03=64% ws-04=31% ws-05=18%(blocked)" },
  { ts: "01:29:15", pre: "INFO",  msg: "<span class=\"k\">heartbeat</span> waiting for next host wakeup (interval=15m, next in ~6m)" },
];

window.DE_DATA = { RUN, WORKSTREAMS, AGENTS, DECISIONS, ALERTS, HISTORY, VALIDATORS, PLAN_TREE, EVENT_TEMPLATES, COORD_LOG };
