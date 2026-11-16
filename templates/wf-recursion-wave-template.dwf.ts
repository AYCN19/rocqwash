/* rocqwash recursion wave template — construction-wave workflow (parameterized).
   Provenance: distilled from five live waves (E/F lanes, X lanes) executed on a
   receiver-side host against this repository; machine-truth hardened (stub-python
   escape, PATH-resolved git, pre-PR alignment gate, PR landing form, markdown
   receipt publication). Fill the parameter block, keep the discipline strings
   byte-stable, and submit through your workflow host.
   Parameters you must fill are marked <<FILL>>. */

interface Std { zeroth: string; limits: string; }
interface SeatOut {
  faces: string;      // repo-relative paths, pipe-separated
  impl: string;
  checks: string;     // py_compile / selftest rc lines
  standards: Std;
}
interface PrPayload { payloadPath: string; checks: string; standards: Std; }

/* ============ parameter block (fill once; changes here are the only sanctioned edits) ============ */
const TREE = "<<FILL: absolute path of your aligned working tree>>";
const ORIGIN = "<<FILL: upstream https URL>>";
const FORK = "<<FILL: your fork https URL>>";
const OUT = "<<FILL: absolute output dir (receipts, payloads, evidence)>>";
const BRANCH = "<<FILL: supply/<wave>-<date>>";
const NETRC = "<<FILL: netrc path carrying your GitHub credentials>>";
const REPO_SLUG = "<<FILL: org/repo>>";
/* seat specs: one entry per construction seat (name must be unique; ask strings must stay
   byte-stable across amends — that stability IS the cache key) */
const SEATS: { name: string; brief: string }[] = [
  { name: "seat-a", brief: "<<FILL: face 1 contract>>" },
  { name: "seat-b", brief: "<<FILL: face 2 contract>>" },
];

let recon = "";
let implNote = "";
let prNote = "";
let ci = "";

const LIMITS =
  "gates: py_compile per face / frozen8 check --list / fitness real run / suite reds ⊆ anchor roster; " +
  "landing form = PR (no direct pushes to main); NETRED resets = built-in 4x retry; skip ≠ red.";

function fail(at: string, detail: string) {
  return { recon: recon, implNote: implNote, prNote: prNote, ci: ci,
           limitations: LIMITS + " failure at: " + at + " — " + detail.slice(0, 500) };
}

phase("P0 align with origin/main (fetch 4x retry + ff-only; stale tree = no construction)");
let fetchNote = "";
for (let a = 0; a < 4; a++) {
  const f = await world.run("git", ["-C", TREE, "fetch", "origin", "main"]);
  if (f.exitCode === 0) { fetchNote = "ok(try" + String(a + 1) + ")"; break; }
  if (a === 3) { return fail("P0-fetch", f.stderr.slice(0, 200)); }
  await world.run("powershell.exe", ["-NoProfile", "-Command", "Start-Sleep -Seconds " + String(10 + 10 * a)], { timeoutMs: 120000 });
}
const ff = await world.run("git", ["-C", TREE, "merge", "--ff-only", "origin/main"]);
if (ff.exitCode !== 0) { return fail("P0-ff", (ff.stdout + ff.stderr).slice(0, 300)); }
const head = await world.run("git", ["-C", TREE, "rev-parse", "HEAD"]);
recon = "aligned at " + head.stdout.trim().slice(0, 7) + " (" + fetchNote + ")";
log("P0: " + recon);
report({ milestone: "P0-ok", head: head.stdout.trim().slice(0, 7) });

phase("construction seats in parallel (mechanical interpreter discipline: py, never stub python)");
const outs = await Promise.all(SEATS.map((s) =>
  agent(s.name).ask<SeatOut>(
    "You are a construction seat for this repository (" + s.brief + ").\n"
    + "Repo tree: " + TREE + ".\n"
    + "Interpreter discipline: bare python/python3 is a store stub (rc 49) — always use the real launcher (py).\n"
    + "Scope: certification faces and frozen files are out of reach; minimal diff; every new .py carries a five-field English header; no third-party deps; no AI-flavor vocabulary; every write face lands with a row in tests/test_destructive_matrix.py.\n"
    + "Self-check: py_compile rc=0 + your face's selftest rc=0.\n"
    + "Reply JSON: {\"faces\":\"a|b\",\"impl\":\"…\",\"checks\":\"…\",\"standards\":{\"zeroth\":\"…\",\"limits\":\"…\"}}"
  )));
const allFaces = outs.map((g) => g.faces).join("|").split("|").filter((x) => x.trim() !== "");
implNote = "seats=" + String(SEATS.length) + " faces=" + String(allFaces.length);
log("impl: " + implNote);
report({ milestone: "impl-done", faces: String(allFaces.length) });

phase("verification gates (per-face py_compile + repo gates)");
for (const rel of allFaces.filter((x) => x.endsWith(".py"))) {
  const c = await world.run("py", ["-I", "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)", TREE + "/" + rel, OUT + "/c_" + String(pyFacesIndex(rel)) + ".pyc"]);
  if (c.exitCode !== 0) { return fail("compile " + rel, (c.stderr + c.stdout).slice(0, 400)); }
}
function pyFacesIndex(rel: string): number { return allFaces.indexOf(rel); }
/* replace these two calls with your repo's canonical forms (verified against --help first):
   - frozen trust-anchor check   (this repo: frozen8.py check --repo . --list … --tier2 …)
   - fitness real run            (this repo: axiom_guard.py --repo . --rocq … --coqchk …)  */
log("gates: per-face compile ✓ (repo gates run at CI; anchor re-sign per SOP if HEAD moved past freeze_commit)");
report({ milestone: "gates-done" });

phase("branch, push fork, open PR");
await world.run("git", ["-C", TREE, "checkout", "-b", BRANCH]);
await world.run("git", ["-C", TREE, "add", "--", "."]); // safe only when P0 proved the tree clean; otherwise add the explicit face list
await world.run("git", ["-C", TREE, "commit", "-m", "<<FILL: english commit message>>"]);
const sha = await world.run("git", ["-C", TREE, "rev-parse", "HEAD"]);
let pushOk = false;
for (let a = 0; a < 4; a++) {
  if (a > 0) { await world.run("powershell.exe", ["-NoProfile", "-Command", "Start-Sleep -Seconds " + String(15 + 10 * a)], { timeoutMs: 120000 }); }
  const p = await world.run("git", ["-C", TREE, "push", FORK, "HEAD:refs/heads/" + BRANCH], { timeoutMs: 300000 });
  pushOk = p.exitCode === 0;
  if (pushOk) break;
}
if (!pushOk) { return fail("push", "commit " + sha.stdout.trim().slice(0, 7) + " kept locally; retry the window"); }
const prSeat = await agent("PR-assembler").ask<{ payloadPath: string; checks: string; standards: Std }>(
`Compose the PR payload JSON at ${OUT}/pr-payload.json (valid JSON; keys title/head/base/body).
title: "<supply prefix>: <summary>"; head: "AYCN19:${BRANCH}"; base: "main".
body: dual-role header (技术总监：王宝军（笔名：王小哥）（递归演进线·Steward） / 执行总监：<contributor>), deliverables,
baseline declaration (anchor + alignment), verification evidence, known deltas honestly,
AI-assistance disclosure quoted VERBATIM from docs/license-protocol-v1.0-20261114.md §7 (three sanctioned slots only),
ICLA section (signed statement reference or pending — never proxy-signed).
checks = "JSON.parse ok, four keys present".`);
let prUrl = "n/a"; let prNum = "0";
for (let a = 0; a < 3; a++) {
  const cr = await world.run("curl", ["-s", "--netrc-file", NETRC, "-X", "POST", "-H", "Accept: application/vnd.github+json", "https://api.github.com/repos/" + REPO_SLUG + "/pulls", "--data-binary", "@" + prSeat.payloadPath], { timeoutMs: 120000 });
  try {
    const j = JSON.parse(cr.stdout) as { number?: number; html_url?: string; message?: string };
    if (j.number !== undefined) { prUrl = j.html_url ?? "n/a"; prNum = String(j.number); break; }
    if ((j.message ?? "").indexOf("already exists") >= 0) { prUrl = "existing"; prNum = "existing"; break; }
    if (a === 2) { return fail("PR", (j.message ?? cr.stdout).slice(0, 300)); }
  } catch { if (a === 2) { return fail("PR", cr.stdout.slice(0, 300)); } }
  await world.run("powershell.exe", ["-NoProfile", "-Command", "Start-Sleep -Seconds 20"], { timeoutMs: 60000 });
}
prNote = "PR#" + prNum + " " + prUrl;
log("PR: " + prNote);
report({ milestone: "PR-open", pr: prNum });

phase("CI judge on the PR head");
let ciV = "";
for (let i = 0; i < 14; i++) {
  await world.run("powershell.exe", ["-NoProfile", "-Command", "Start-Sleep -Seconds " + String(60 + 10 * i)], { timeoutMs: 400000 });
  const rr = await world.run("curl", ["-s", "--netrc-file", NETRC, "https://api.github.com/repos/" + REPO_SLUG + "/actions/runs?per_page=8&_=" + String(i)], { timeoutMs: 60000 });
  let runs: { id: number; head_sha: string; status: string; conclusion: string | null; name: string }[] = [];
  try { runs = (JSON.parse(rr.stdout) as { workflow_runs?: typeof runs }).workflow_runs ?? []; } catch { runs = []; }
  const mine = runs.filter((r) => r.head_sha === sha.stdout.trim() && r.name !== "rocqwash self-heal");
  if (mine.length === 0 || !mine.every((r) => r.status === "completed")) { continue; }
  ciV = mine.every((r) => r.conclusion === "success") ? "GREEN" : "RED:" + mine.filter((r) => r.conclusion !== "success").map((r) => String(r.id)).join(",");
  break;
}
if (ciV === "") { ciV = "UNSETTLED (judge handed to the maintainer)"; }
ci = ciV + " (" + sha.stdout.trim().slice(0, 7) + ")";
await world.run("powershell.exe", ["-NoProfile", "-Command", "Set-Content -Path '" + OUT + "/wave-done.marker' -Value '" + sha.stdout.trim() + "|" + prNum + "'"]);

phase("receipt");
const md = ["# wave receipt", "", "- baseline: " + recon, "- impl: " + implNote, "- PR: " + prNote, "- CI: " + ci, "- limits: " + LIMITS].join("\n");
await artifact.markdown("wave-receipt", md, { title: "wave receipt", primary: true });
return { recon: recon, implNote: implNote, prNote: prNote, ci: ci,
         limitations: LIMITS + (ciV === "GREEN" ? " CI=GREEN — wave closed." : " CI not settled — judge handed over.") };
