#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolve.py — autonomous evolution engine v1 for rocqwash (tools/).

Purpose.  The law-three harvest→derive→draft pipeline: turn live repository
  signals into a reviewed, human-gated task-brief draft for the next round.
  Harvest collects five signal classes by subprocess of the existing engines
  (zero new engines): norm-lint fitness (current tree vs baseline, frozen
  surfaces excluded), new ci-red events from one sentinel --once round, the
  suite last state (captured ledger or a live run), registry-audit accounts
  with increment, and maintained UNRECOGNIZED sentinel events. Derive applies
  fixed scoring rules plus genetic standing candidates; draft renders the
  human-gated brief to --draft-out; draft-only: selection is not implemented
  in this code, no candidate is executed, the repository is never written.

Interface.  python3 tools/evolve.py --draft-out PATH [--json PATH] [--top N]
  [--baseline PATH] [--watch-repo ORG/REPO]... [--sentinel-state PATH]
  [--suite-ledger PATH | --suite-now] [--registry-git REPO --registry-ref
  REF] | --selftest; every flag and the rocqwash-evolve/1 schema face are
  specified in the extended contract below.

Dependencies.  Python 3 stdlib only; sibling engines norm_lint.py /
  cw_sentinel.py / registry_audit.py / tests/run_tests.sh and the frozen eight
  list in certify/frozen8.py live relative to this engine; git on PATH.

Evidence.  --selftest vectors: canned signal injection via real subprocesses,
  candidate-rule unit judgments, draft formation, frozen exclusion, sentinel
  seen-idempotence, deterministic double run.

Exit-codes.  0 = harvest/derive/draft completed (adverse signals are data);
  2 = usage error; 9 = missing or unreachable input (fail-loud).
"""
# Extended contract (help face; kept below the five-field block so the
#   header stays within the 30-line budget of the annotation standard):
# --draft-out PATH      the task-brief draft (markdown). Required for a
#                       normal run: no draft means the spawn-gate deliverable
#                       is missing. The parent directory must exist (fail
#                       loud 9, no implicit mkdir).
# --json PATH           report target, schema rocqwash-evolve/1, sort_keys,
#                       overwritten. Optional: the stdout summary line is
#                       always printed.
# --repo-root DIR       repository root for the norm scan and the suite run;
#                       default = the parent of the directory holding this
#                       engine (same TOOLS_DIR precedent as the siblings).
# --top N               draft width, default 5. Candidates beyond the top
#                       stay in the JSON with in_draft=false.
# --baseline PATH       the norm-lint baseline report (schema
#                       rocqwash-norm-lint/1) the fitness delta is computed
#                       against. Missing file = 9. Without it the norm
#                       signal is not harvested and fitness.baseline_delta
#                       is null (reported, never guessed).
# --jargon-map PATH     forwarded to norm_lint --tree; default
#                       docs/jargon-to-standard-mapping-v1.md resolved under
#                       the repo root.
# --watch-repo ORG/REPO enables the sentinel signal (repeatable, dual-repo
#                       form). Requires --sentinel-state (2 without it: a
#                       "new events" account is undefined without a seen
#                       ledger). --sentinel-state-seed PATH copies an
#                       existing state file (never written) to the harvest
#                       state first, so the first round reports only runs
#                       the long-lived stream has not yet seen; the seed is
#                       validated before the copy (9 on missing/malformed).
# --sentinel-events PATH  an existing event stream JSONL (read-only) scanned
#                       for maintained UNRECOGNIZED events (signal e).
# --sentinel-branch B   branch filter forwarded to each watched repository.
# --sentinel-injector PATH  canned API responses forwarded to the sentinel
#                       child (its own --injector flag); keeps offline
#                       rounds off the network.
# --suite-ledger PATH   a captured run_tests.sh output; its summary line
#                       (the pass/red/skip/total counts in the tool's own
#                       summary form) is parsed.
# --suite-now           run tests/run_tests.sh live instead (mutually
#                       exclusive with --suite-ledger, 2 if both given).
# --registry-git REPO / --registry-ref REF  enable the registry signal
#                       (git direct-read form); --git-path-order /
#                       --git-path-project override the book paths
#                       (default order.txt / _CoqProject at the ref root).
# --registry-baseline PATH  a prior rocqwash-registry-audit/1 report the
#                       increment is computed against; without it the
#                       increment is null with an explicit first-run note.
# Fitness accounting.  baseline_delta = current minus baseline on the raw
#                       counts (schema face). translatable_delta applies the
#                       same subtraction after excluding the frozen surfaces
#                       from both sides (the frozen ledger grows by design,
#                       so its growth is not a fitness regression);
#                       reduction_rate = (baseline - current) / baseline per
#                       counter, 0.0 when the baseline counter is zero.
# Scoring.  score = impact * min(evidence_raw, 10) / effort, rounded to 4
#                       decimals; evidence_raw is the underlying item count
#                       per rule (regressing files, error mass, maintained
#                       UNRECOGNIZED events, new A-family events,
#                       duplicates+orphans, suite reds); the clamp keeps the
#                       five rule families comparable and the raw count is
#                       preserved in the candidate basis. Order = score
#                       descending, then kind, then title (all deterministic).
# Rule table (signals to candidates; a rule fires only when its signal was
#   harvested): norm translatable regression -> norm-regression; norm
#   translatable error mass remaining -> longtail-translation (next
#   echelon, reduction rate carried in the evidence text); maintained
#   UNRECOGNIZED events -> taxonomy-supplement; new A-family events ->
#   red-triage (the other families follow the `red_dispatch.py` routing
#   conventions and are not re-derived here); duplicates+orphans ->
#   registry-hygiene; suite reds -> suite-repair. Genetic standing
#   candidates (heredity) fire whenever their topic has no live candidate
#   this round; each cites its frozen-ledger entry (entry id and section,
#   never a line number that would rot on append).
# Determinism.  No wall-clock, no randomness in the engine; the only live
#   data are the harvested signal fields (event ids, timestamps, counts),
#   which are data. On canned inputs the whole pipeline reruns
#   byte-identical (selftest vector).
# Orchestration discipline.  The engine invokes each signal engine exactly
#   as its own interface defines, per-stage subprocess timeout kills the
#   child and fails loud 9 naming the stage; a signal engine exiting
#   nonzero propagates as 9 with its stderr tail (fail-loud, no swallowing).
# Honesty rules (per CONTRIBUTING §0): accept only mechanical evidence;
#   adverse signals are data (exit stays 0); fail-loud, no silent
#   degradation; zero third-party dependencies; --json written sort_keys;
#   zero hardcoded absolute paths (every input and output path is a flag).
# Write-surface declaration: only the explicit --json and --draft-out
#   targets, plus the caller-designated --sentinel-state file (written by
#   the sentinel child). Selftest writes only a mkdtemp directory (removed
#   on exit).
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROG = "evolve"
SCHEMA = "rocqwash-evolve/1"

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
NORM_TOOL = os.path.join(TOOLS_DIR, "norm_lint.py")
SENTINEL_TOOL = os.path.join(TOOLS_DIR, "cw_sentinel.py")
AUDIT_TOOL = os.path.join(TOOLS_DIR, "registry_audit.py")
SUITE_ENTRY = os.path.join(REPO_ROOT, "tests", "run_tests.sh")
CERTIFY_DIR = os.path.join(REPO_ROOT, "certify")
if CERTIFY_DIR not in sys.path:
    sys.path.insert(0, CERTIFY_DIR)
import frozen8 as _frozen8  # noqa: E402  (frozen ledger list, single source)

DEFAULT_JARGON_MAP = "docs/jargon-to-standard-mapping-v1.md"
DEFAULT_TOP = 5
EVIDENCE_CAP = 10          # evidence clamp entering the score formula
NORM_TIMEOUT = 180         # norm_lint child cap (seconds)
SENTINEL_TIMEOUT = 600     # sentinel once-round cap (network retries included)
SUITE_TIMEOUT = 900        # run_tests.sh cap (measured run ~150s)
AUDIT_TIMEOUT = 180        # registry_audit child cap (tmp clone included)
FROZEN_LEDGER = "更新账.md"   # append-only frozen ledger (read-only surface)
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")
SUITE_SUMMARY_RE = re.compile(
    r"== 汇总: (\d+) 过 / (\d+) 红 / (\d+) 略 / 共 (\d+) 例 ==")
NORM_SCHEMA = "rocqwash-norm-lint/1"
SENTINEL_REPORT_SCHEMA = "rocqwash-sentinel/1"
SENTINEL_STATE_SCHEMA = "rocqwash-sentinel-state/1"
SENTINEL_EVENT_SCHEMA = "rocqwash-sentinel-event/1"
AUDIT_SCHEMA = "rocqwash-registry-audit/1"
ERROR_KINDS = ("header", "jargon", "parse")   # error-level finding kinds
FAMILY_A = "A-content-red"
FAMILY_UNREC = "UNRECOGNIZED"

# Genetic standing candidates (heredity face): topics the frozen ledger
# keeps re-listing as pending human-gated work. A standing candidate fires
# only when no live candidate of the same topic was derived this round, so
# a live signal always outranks the persisted memory. Anchors cite the
# ledger entry id and section (append-stable), never a line number.
STANDING_CANDIDATES = (
    {"topic": "registry", "kind": "standing-candidate",
     "title": "Apply the audited duplicate-block prescription to the live books",
     "impact": 1, "effort": 2,
     "goal": "Close the long-standing duplicate-block and anchor findings on "
             "the serviced books by running the audited prescription path.",
     "approach": "registry_audit --fix-plan for the prescription, then "
                 "registry_fix dry run, then human review, then --apply "
                 "(staged per-row md5 accounting with rollback); the books "
                 "are regenerated on the current mainline per the isolation "
                 "protocol, never hand-edited.",
     "acceptance": "A rerun audit shows zero duplicate residue on treated "
                   "keys, no new anchor-text collisions, no orphan growth; "
                   "the books are byte-identical outside the treated rows.",
     "anchor": "ledger v54 entry, boundary list (re-statement); origin "
               "ledger v47 entry, roadmap section"},
    {"topic": "main-dispatch", "kind": "standing-candidate",
     "title": "Land the multi-repo real-push step behind its recorded "
              "preconditions",
     "impact": 1, "effort": 2,
     "goal": "Execute the recorded final step of the multi-repo adaptation "
             "path (a real push against the protected main repository) "
             "once its recorded preconditions hold.",
     "approach": "Confirm the working-clone placement decision and the "
                 "branch-protection posture recorded in the ledger, run the "
                 "push planner in dry-run first, then the real push "
                 "only after the human gate accepts the plan.",
     "acceptance": "The dry-run plan matches the recorded expectations; the "
                   "real push (if approved) lands with its run evidence "
                   "captured; no direct push to a protected branch.",
     "anchor": "ledger v54 entry, boundary list; origin ledger v49 entry, "
               "boundary list"},
    {"topic": "quad8", "kind": "standing-candidate",
     "title": "Restore the four-repo reconciliation suite case when the "
              "archive returns",
     "impact": 1, "effort": 2,
     "goal": "Bring the single skipped suite case back into the running set "
             "once its missing input archive is restored.",
     "approach": "Restore the four-repo copy set the case reconciles (a "
                 "desktop-archive decision recorded as pending), then run "
                 "the case and confirm it joins the passing set.",
     "acceptance": "The suite runs with zero skips on a full local run; the "
                   "case passes twice in a row.",
     "anchor": "ledger v54 entry, boundary list; origin ledger v47 entry, "
               "boundary list"},
)

# Draft templates per live candidate kind (goal/approach/acceptance are
# rendered with the harvested numbers; grading states the formula inputs).
CAND_SPECS = {
    "norm-regression": {
        "impact": 4, "effort": 2,
        "title": "Repair the norm-lint fitness regression on translatable faces",
        "goal": "Bring the translatable error-level finding count back to or "
                "below the baseline before any new surface work ({delta_grow} "
                "error findings regressed across {n_regress} file(s) since "
                "the baseline).",
        "approach": "Diff the current findings against the baseline per file "
                    "(the regressing files are listed in Evidence), apply "
                    "translation replacement or header completion per the "
                    "mapping table on exactly those faces, and archive each "
                    "replaced Chinese prose in its .zh.md sibling.",
        "acceptance": "The translatable error count is back to or below the "
                      "baseline; norm_lint --selftest rc=0; the full suite "
                      "is green (0 red) twice; doc_lint consistent.",
    },
    "longtail-translation": {
        "impact": 3, "effort": 3,
        "title": "Carry the translation-replacement program into the next "
                 "echelon",
        "goal": "Continue the law-one translation program on the prose long "
                "tail: reduce the remaining translatable error mass "
                "({err_mass} error findings on non-frozen faces) by at least "
                "the next echelon ({top_files}).",
        "approach": "Take the next echelon from the top error-carrying files "
                    "in Evidence, translate each face per the mapping table "
                    "with .zh.md archive siblings, keep code identifiers, "
                    "CLI flags, schema field names and exit codes unchanged.",
        "acceptance": "The translatable error count strictly decreases "
                      "against the starting account; every touched tool "
                      "keeps --selftest rc=0; the full suite is green "
                      "twice; zero jargon residue on the touched faces.",
    },
    "taxonomy-supplement": {
        "impact": 2, "effort": 2,
        "title": "Extend the classification taxonomy to close the maintained "
                 "UNRECOGNIZED events",
        "goal": "Reduce the maintained UNRECOGNIZED event set ({unrec_n} "
                "maintained event(s)) by extending the classification "
                "taxonomy with reviewed rules or a written ground-truth "
                "note per event.",
        "approach": "For each maintained event: re-diagnose with the triage "
                    "engine --repo --run --logs (real execution lines only), "
                    "extract the discriminating token, either add the rule "
                    "with an UNRECOGNIZED-maintenance acceptance vector "
                    "(machine verdict = review verdict) or keep the event "
                    "UNRECOGNIZED with a written ground-truth note; never "
                    "force-fit a shape outside the taxonomy.",
        "acceptance": "Every maintained event either re-classifies into a "
                      "documented family or stays UNRECOGNIZED with a "
                      "written note; the triage engine --selftest rc=0 with "
                      "the new vectors; the full suite is green twice.",
    },
    "red-triage": {
        "impact": 3, "effort": 2,
        "title": "Dispatch the new failing-run events through the routing "
                 "table",
        "goal": "Give every new failing-run event of this round an explicit "
                "route row ({a_n} new A-family event(s); family histogram in "
                "Evidence).",
        "approach": "Re-diagnose each event with the triage engine (real "
                    "execution lines only), then route per the routing table "
                    "of `red_dispatch.py`: B/E families to the push "
                    "re-route suggestion, C family to the toolchain doctor "
                    "suggestion, D family and UNRECOGNIZED to watch-only, "
                    "and A family to a manual fix note — a content repair "
                    "is proposed, never automatically applied.",
        "acceptance": "Every new failing event carries a route row in the "
                      "round account; A-family fixes stay proposal-only; the "
                      "affected runs return to passing or carry a "
                      "documented cause.",
    },
    "registry-hygiene": {
        "impact": 2, "effort": 2,
        "title": "Apply the registry audit prescriptions to the serviced books",
        "goal": "Reduce the mechanically prescribable registry findings "
                "({dup_n} duplicate + {orph_n} orphan findings; anchor "
                "histogram in Evidence) on the audited books.",
        "approach": "registry_audit --fix-plan for the deterministic "
                    "prescriptions, registry_fix dry run by default, human "
                    "review, then --apply with per-row md5 accounting and "
                    "automatic rollback on any post-apply assertion failure; "
                    "rows are regenerated on the current mainline, never "
                    "hand-edited.",
        "acceptance": "A rerun audit shows zero duplicate residue on treated "
                      "keys, no new anchor-text collisions, no orphan "
                      "growth; the books are byte-identical outside the "
                      "treated rows; the full suite is green twice.",
    },
    "suite-repair": {
        "impact": 5, "effort": 1,
        "title": "Bring the self-test suite back to all-green",
        "goal": "Repair the {red_n} red suite case(s) named in Evidence; the "
                "suite is the selection face of the evolution loop, so a "
                "red suite outranks every other signal.",
        "approach": "Reproduce each red case in isolation, fix the tool face "
                    "the case attests (never weaken the case), then rerun "
                    "the full suite twice.",
        "acceptance": "The full suite reports 0 red twice in a row; "
                      "doc_lint consistent; no case was skipped or weakened "
                      "to reach the green state.",
    },
}


# Agenda-slot mapping: each live kind consumes the standing-candidate topic
# it supersedes, so a live signal always outranks the persisted memory of
# the same agenda slot.
KIND_TOPIC = {
    "norm-regression": "translation",
    "longtail-translation": "translation",
    "taxonomy-supplement": "taxonomy",
    "red-triage": "red",
    "registry-hygiene": "registry",
    "suite-repair": "suite",
}


class EvolveError(Exception):
    """Fail-loud exception carrying its own exit code (2 usage, 9 missing)."""

    def __init__(self, msg, code=9):
        super(EvolveError, self).__init__(msg)
        self.code = code


def fail(msg, code):
    """Fail loud: write the reason to stderr and raise the coded error."""
    raise EvolveError(msg, code)


def load_json(path, what):
    """Load a JSON file fail-loud (9 on missing/unreadable/malformed)."""
    if not os.path.isfile(path):
        fail("%s missing: %s" % (what, path), 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        fail("%s unreadable or malformed: %s (%s)" % (what, path, exc), 9)


def require_schema(obj, schema, what):
    """Schema check fail-loud (9 on mismatch or non-object shape)."""
    if not isinstance(obj, dict) or obj.get("schema") != schema:
        fail("%s has wrong or missing schema (want %s)" % (what, schema), 9)


def ensure_parent(path, what):
    """The parent directory of an output target must exist (9, no mkdir)."""
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        fail("%s parent directory missing: %s" % (what, parent), 9)


def write_text(path, text):
    """Write a text file with a trailing newline, utf-8, lf endings."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text if text.endswith("\n") else text + "\n")


def dump_json(path, obj):
    """Deterministic JSON write (sort_keys, indent=1, trailing newline)."""
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=1,
                                sort_keys=True))


def run_child(cmd, what, timeout, cwd=None):
    """Run a subprocess with a hard cap; kill on timeout; fail loud 9.

    Returns (returncode, stdout_text, stderr_text). A nonzero return code is
    NOT failed here — signal engines report adverse outcomes as data; the
    caller decides which codes mean unreachable (9) and which are data.
    """
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=timeout, cwd=cwd)
    except FileNotFoundError:
        fail("%s engine not found: %s" % (what, cmd[0]), 9)
    except subprocess.TimeoutExpired:
        fail("%s timed out after %ds (killed): %s"
             % (what, timeout, " ".join(cmd[:4])), 9)
    out = p.stdout.decode("utf-8", errors="replace") if p.stdout else ""
    err = p.stderr.decode("utf-8", errors="replace") if p.stderr else ""
    return p.returncode, out, err


def clip(text, cap=200):
    """Single-line evidence clip (same convention as the event stream)."""
    text = " ".join(str(text).split())
    return text if len(text) <= cap else text[:cap - 3] + "..."


# ---- stage 1: harvest -------------------------------------------------------


def frozen_surfaces():
    """The read-only exclusion set: the frozen ledger plus the frozen eight.

    The frozen eight come from the single-source ledger list in
    `certify/frozen8.py`; the append-only ledger grows by design and is
    never a fitness-regression surface. quad8 material is json and never a
    lint face, so it needs no entry here.
    """
    rows = {FROZEN_LEDGER}
    for rel, _md5 in _frozen8.LEDGER8:
        rows.add(rel)
    return rows


def norm_counts(report, exclude=None):
    """Aggregate error/warn finding counts over a norm-lint report.

    exclude is a set of tree-relative paths omitted from the aggregation
    (the frozen surfaces). Returns {error, warn, files, cjk_ratio}.
    """
    error = warn = 0
    files = 0
    cjk_sum = 0.0
    for rec in report.get("files", []):
        if exclude and rec.get("path") in exclude:
            continue
        files += 1
        for fd in rec.get("findings", []):
            if fd.get("kind") in ("cjk", "forbidden", "budget"):
                warn += 1
            else:
                error += 1
        cjk_sum += float(rec.get("cjk_ratio", 0.0))
    return {"error": error, "warn": warn, "files": files,
            "cjk_ratio": round(cjk_sum / files, 6) if files else 0.0}


def harvest_norm(repo_root, jargon_map, baseline_path, tmpdir):
    """Signal (a): current tree scan vs the baseline ledger.

    Runs the norm engine as a subprocess on the repo root, loads the
    baseline report, and computes the raw delta, the translatable delta
    (frozen surfaces excluded from both sides), the reduction rates, the
    per-file error deltas on translatable faces, and the top error
    carriers. Any engine failure or shape error fails loud 9.
    """
    if not os.path.isdir(repo_root):
        fail("repo root missing: %s" % repo_root, 9)
    out_json = os.path.join(tmpdir, "norm_current.json")
    cmd = [sys.executable, "-B", NORM_TOOL, "--tree", repo_root,
           "--jargon-map", jargon_map, "--json", out_json]
    rc, _out, err = run_child(cmd, "norm-lint scan", NORM_TIMEOUT)
    if rc != 0:
        fail("norm-lint scan failed rc=%d: %s" % (rc, clip(err or _out)), 9)
    current = load_json(out_json, "norm-lint scan report")
    require_schema(current, NORM_SCHEMA, "norm-lint scan report")
    baseline = load_json(baseline_path, "norm-lint baseline")
    require_schema(baseline, NORM_SCHEMA, "norm-lint baseline")
    frozen = frozen_surfaces()
    cur_raw = norm_counts(current)
    base_raw = norm_counts(baseline)
    cur_tr = norm_counts(current, exclude=frozen)
    base_tr = norm_counts(baseline, exclude=frozen)

    def rate(base_v, cur_v):
        return round((base_v - cur_v) / float(base_v), 6) if base_v else 0.0

    # per-file error deltas on translatable faces (regressions and top carriers)
    cur_err = {}
    base_err = {}
    cur_warn = {}
    for rec in current.get("files", []):
        if rec.get("path") in frozen:
            continue
        e = w = 0
        for fd in rec.get("findings", []):
            if fd.get("kind") in ("cjk", "forbidden", "budget"):
                w += 1
            else:
                e += 1
        if e:
            cur_err[rec["path"]] = e
        if w:
            cur_warn[rec["path"]] = w
    for rec in baseline.get("files", []):
        if rec.get("path") in frozen:
            continue
        e = sum(1 for fd in rec.get("findings", [])
                if fd.get("kind") not in ("cjk", "forbidden", "budget"))
        if e:
            base_err[rec["path"]] = e
    regressions = []
    for path in sorted(set(cur_err) | set(base_err)):
        d = cur_err.get(path, 0) - base_err.get(path, 0)
        if d > 0:
            regressions.append({"path": path, "delta": d,
                                "current": cur_err.get(path, 0)})
    regressions.sort(key=lambda r: (-r["delta"], r["path"]))
    carriers = sorted(cur_err.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    top_files = [{"path": p, "error": e, "warn": cur_warn.get(p, 0)}
                 for p, e in carriers]
    return {
        "present": True,
        "baseline_path": os.path.relpath(
            os.path.abspath(baseline_path), repo_root)
        if os.path.abspath(baseline_path).startswith(
            os.path.abspath(repo_root) + os.sep)
        else os.path.abspath(baseline_path),
        "current": cur_raw,
        "baseline": base_raw,
        "baseline_delta": {"error": cur_raw["error"] - base_raw["error"],
                           "warn": cur_raw["warn"] - base_raw["warn"],
                           "files": cur_raw["files"] - base_raw["files"]},
        "translatable_delta": {
            "error": cur_tr["error"] - base_tr["error"],
            "warn": cur_tr["warn"] - base_tr["warn"],
            "files": cur_tr["files"] - base_tr["files"]},
        "translatable_error_mass": cur_tr["error"],
        "reduction_rate": {"error": rate(base_raw["error"], cur_raw["error"]),
                           "warn": rate(base_raw["warn"], cur_raw["warn"])},
        "regressions": regressions,
        "top_error_files": top_files,
        "excluded_frozen": sorted(frozen),
    }


def harvest_sentinel(watch_repos, state_path, seed_path, branch, tmpdir,
                     injector_path=None):
    """Signal (b): one sentinel --once round over the watched repositories.

    A caller-provided seed state is validated and copied (never written)
    before the round, so the first round reports only the runs the
    long-lived stream has not yet seen. The round report supplies the new
    events; the state file is left for the caller's next round. The
    injector pass-through (the sentinel's own canned-response flag) keeps
    offline rounds off the network. A nonzero child exit propagates as 9
    with the stderr tail.
    """
    for repo in watch_repos:
        if not REPO_RE.match(repo):
            fail("malformed --watch-repo (want ORG/REPO): %r" % repo, 2)
    if seed_path:
        if os.path.abspath(seed_path) == os.path.abspath(state_path):
            fail("--sentinel-state-seed and --sentinel-state are the same "
                 "file (the seed is never written)", 2)
        seed = load_json(seed_path, "sentinel state seed")
        require_schema(seed, SENTINEL_STATE_SCHEMA, "sentinel state seed")
        shutil.copyfile(seed_path, state_path)
    out_json = os.path.join(tmpdir, "sentinel_report.json")
    cmd = [sys.executable, "-B", SENTINEL_TOOL, "--once"]
    for repo in watch_repos:
        cmd += ["--watch-repo", repo]
        if branch:
            cmd += ["--branch", branch]
    cmd += ["--state-file", state_path, "--json", out_json]
    if injector_path:
        cmd += ["--injector", injector_path, "--sleep-scale", "0"]
    rc, _out, err = run_child(cmd, "sentinel once round", SENTINEL_TIMEOUT)
    if rc != 0:
        fail("sentinel once round failed rc=%d: %s" % (rc, clip(err)), 9)
    report = load_json(out_json, "sentinel round report")
    require_schema(report, SENTINEL_REPORT_SCHEMA, "sentinel round report")
    events = [e for e in report.get("events", [])
              if isinstance(e, dict) and e.get("kind") == "ci-red"]
    fam_hist = {}
    for e in events:
        fam = e.get("family", "?")
        fam_hist[fam] = fam_hist.get(fam, 0) + 1
    events.sort(key=lambda e: (e.get("repo", ""), str(e.get("run", ""))))
    compact = [{"repo": e.get("repo", ""), "run": e.get("run"),
                "run_number": e.get("run_number"),
                "branch": e.get("branch", ""), "family": e.get("family", ""),
                "action": e.get("action", ""), "ts": e.get("ts")}
               for e in events]
    sources = []
    for s in report.get("sources", {}).get("ci", []):
        if isinstance(s, dict):
            sources.append({"repo": s.get("repo"),
                            "runs_seen": s.get("runs_seen"),
                            "new_runs": s.get("new_runs"),
                            "red_runs": s.get("red_runs")})
    return {
        "present": True,
        "watch_repos": list(watch_repos),
        "state_file": os.path.abspath(state_path),
        "seeded": bool(seed_path),
        "new_ci_red": len(events),
        "family_histogram": {k: fam_hist[k] for k in sorted(fam_hist)},
        "new_a_family": fam_hist.get(FAMILY_A, 0),
        "events": compact,
        "sources": sources,
    }


def harvest_suite(repo_root, ledger_path, suite_now, tmpdir):
    """Signal (c): the suite last state from a captured ledger or a live run.

    The ledger form parses the run_tests.sh summary line; the live form runs
    the suite entry and parses its stdout. A red suite is data (the exit
    stays 0); an unparsable ledger or a live run without a summary line
    fails loud 9.
    """
    if suite_now:
        if not os.path.isfile(SUITE_ENTRY):
            fail("suite entry missing: %s" % SUITE_ENTRY, 9)
        rc, out, _err = run_child(["bash", SUITE_ENTRY], "suite run",
                                  SUITE_TIMEOUT, cwd=repo_root)
        source = "now(rc=%d)" % rc
    else:
        if not os.path.isfile(ledger_path):
            fail("suite ledger missing: %s" % ledger_path, 9)
        try:
            with io.open(ledger_path, "r", encoding="utf-8",
                         errors="replace") as fh:
                out = fh.read()
        except OSError as exc:
            fail("suite ledger unreadable: %s (%s)" % (ledger_path, exc), 9)
        source = "ledger"
    m = SUITE_SUMMARY_RE.search(out)
    if not m:
        fail("suite %s carries no parsable summary line (want the "
             "run_tests.sh summary form)" % source, 9)
    passed, red, skip, total = (int(m.group(1)), int(m.group(2)),
                                int(m.group(3)), int(m.group(4)))
    reds = []
    if red:
        for line in out.splitlines():
            mm = re.match(r"\[\d+/\d+\] (\S+)\s+FAIL \(rc=(\d+)\)", line)
            if mm:
                reds.append({"case": mm.group(1), "rc": int(mm.group(2))})
    return {"present": True, "source": source, "pass": passed, "red": red,
            "skip": skip, "total": total, "red_cases": reds}


def harvest_registry(git_repo, ref, path_order, path_project,
                     baseline_path, tmpdir):
    """Signal (d): registry audit accounts over the serviced books.

    Runs the audit engine in its git direct-read form (a local tmp clone,
    read-only) and reports the four accounts; with a prior audit report the
    per-account increment is computed, without one the increment is null
    with an explicit first-run note.
    """
    out_json = os.path.join(tmpdir, "registry_audit.json")
    cmd = [sys.executable, "-B", AUDIT_TOOL, "--git", git_repo, "--ref", ref]
    if path_order:
        cmd += ["--git-path-order", path_order]
    if path_project:
        cmd += ["--git-path-project", path_project]
    cmd += ["--json", out_json]
    rc, _out, err = run_child(cmd, "registry audit", AUDIT_TIMEOUT)
    if rc != 0:
        fail("registry audit failed rc=%d: %s" % (rc, clip(err)), 9)
    report = load_json(out_json, "registry audit report")
    require_schema(report, AUDIT_SCHEMA, "registry audit report")
    summary = report.get("summary", {})
    increment = None
    increment_note = "first-run (no --registry-baseline given)"
    if baseline_path:
        prior = load_json(baseline_path, "registry audit baseline")
        require_schema(prior, AUDIT_SCHEMA, "registry audit baseline")
        psum = prior.get("summary", {})
        increment = {k: summary.get(k, 0) - psum.get(k, 0)
                     for k in ("duplicates", "anchors", "orphans", "live",
                               "total")}
        increment_note = "increment vs the supplied prior audit"
    return {
        "present": True,
        "git_repo": os.path.abspath(git_repo),
        "ref": ref,
        "path_order": path_order or "order.txt",
        "path_project": path_project or "_CoqProject",
        "summary": {k: summary.get(k, 0)
                    for k in ("duplicates", "anchors", "orphans", "live",
                              "total")},
        "by_kind": summary.get("by_kind", {}),
        "increment": increment,
        "increment_note": increment_note,
    }


def harvest_unrec(events_path, state_path):
    """Signal (e): maintained UNRECOGNIZED events from the stream and state.

    The event stream is read-only; each UNRECOGNIZED ci-red event is kept
    with its stream sequence and timestamp. When a state file is given, each
    event is annotated with whether the seen ledger still carries it
    (state_present); state-only UNRECOGNIZED entries absent from the stream
    are listed as well (the stream rotates). A malformed stream line fails
    loud 9 with its line number.
    """
    items = {}
    if events_path:
        if not os.path.isfile(events_path):
            fail("sentinel event stream missing: %s" % events_path, 9)
        try:
            with io.open(events_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError as exc:
            fail("sentinel event stream unreadable: %s (%s)"
                 % (events_path, exc), 9)
        bad = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                bad.append(i)
                continue
            if not isinstance(ev, dict) \
                    or ev.get("schema") != SENTINEL_EVENT_SCHEMA:
                bad.append(i)
                continue
            if ev.get("kind") == "ci-red" \
                    and ev.get("family") == FAMILY_UNREC:
                key = (ev.get("repo", ""), str(ev.get("run", "")))
                items[key] = {
                    "repo": ev.get("repo", ""), "run": ev.get("run"),
                    "run_number": ev.get("run_number"),
                    "stream_seq": ev.get("seq"), "stream_ts": ev.get("ts"),
                    "evidence": [clip(x) for x in
                                 (ev.get("evidence") or [])[:3]],
                }
        if bad:
            fail("sentinel event stream has malformed lines: %s"
                 % (", ".join(str(b) for b in bad)), 9)
    state_fams = {}
    if state_path and os.path.isfile(state_path):
        state = load_json(state_path, "sentinel state")
        require_schema(state, SENTINEL_STATE_SCHEMA, "sentinel state")
        for repo, info in sorted(state.get("repos", {}).items()):
            for rid, meta in sorted((info.get("seen_runs") or {}).items(),
                                    key=lambda kv: str(kv[0])):
                if meta.get("family") == FAMILY_UNREC:
                    state_fams[(repo, str(rid))] = meta
    for (repo, rid), meta in state_fams.items():
        key = (repo, str(meta.get("run_number", rid)))
        if key not in items:
            items[key] = {"repo": repo, "run": rid,
                          "run_number": meta.get("run_number"),
                          "stream_seq": None, "stream_ts": None,
                          "evidence": []}
    out = []
    for (repo, _rid), item in sorted(items.items()):
        item["state_present"] = (repo, str(item.get("run"))) in state_fams \
            if state_fams else None
        out.append(item)
    return {"present": True, "events_file": events_path,
            "state_file": os.path.abspath(state_path) if state_path else None,
            "maintained": out, "count": len(out)}


# ---- stage 2: derive --------------------------------------------------------


def score_of(impact, evidence_raw, effort):
    """score = impact * clamped(evidence) / effort, 4-decimal deterministic."""
    return round(impact * min(max(evidence_raw, 0), EVIDENCE_CAP)
                 / float(effort), 4)


def make_candidate(kind, evidence_raw, basis, top):
    """Build one live candidate from its spec, evidence count and basis."""
    spec = CAND_SPECS[kind]
    score = score_of(spec["impact"], evidence_raw, spec["effort"])
    return {"kind": kind, "title": spec["title"], "impact": spec["impact"],
            "effort": spec["effort"], "evidence_raw": evidence_raw,
            "evidence": min(max(evidence_raw, 0), EVIDENCE_CAP),
            "score": score, "topic": KIND_TOPIC[kind], "basis": basis,
            "in_draft": False, "rank": None, "_spec": spec, "_top": top}


def derive_candidates(signals, top):
    """Stage 2: fixed rules from signals to scored, ranked candidates.

    Live rules fire only on their harvested signal; genetic standing
    candidates fire when their topic has no live candidate. A round whose
    translatable error mass is zero yields a completion note (returned
    separately, never a candidate). Order is score descending then kind
    then title; ranks are 1-based and contiguous; the top-N carry
    in_draft=true. Returns (candidates, notes).
    """
    cands = []
    notes = []
    norm = signals.get("norm")
    if norm:
        tr_delta = norm["translatable_delta"]["error"]
        if tr_delta > 0:
            cands.append(make_candidate(
                "norm-regression", len(norm["regressions"]),
                {"translatable_delta": norm["translatable_delta"],
                 "regressions": norm["regressions"]}, top))
        elif norm["translatable_error_mass"] > 0:
            cands.append(make_candidate(
                "longtail-translation", norm["translatable_error_mass"],
                {"translatable_error_mass": norm["translatable_error_mass"],
                 "reduction_rate": norm["reduction_rate"],
                 "top_error_files": norm["top_error_files"]}, top))
        else:
            notes.append("law-one translation program complete on "
                         "translatable faces; no translation candidate "
                         "derived")
    unrec = signals.get("unrec")
    if unrec and unrec["count"] > 0:
        cands.append(make_candidate(
            "taxonomy-supplement", unrec["count"],
            {"maintained": unrec["maintained"]}, top))
    sent = signals.get("sentinel")
    if sent and sent["new_a_family"] > 0:
        cands.append(make_candidate(
            "red-triage", sent["new_a_family"],
            {"family_histogram": sent["family_histogram"],
             "new_ci_red": sent["new_ci_red"],
             "events": sent["events"]}, top))
    reg = signals.get("registry")
    if reg and (reg["summary"]["duplicates"] + reg["summary"]["orphans"]) > 0:
        cands.append(make_candidate(
            "registry-hygiene",
            reg["summary"]["duplicates"] + reg["summary"]["orphans"],
            {"summary": reg["summary"], "by_kind": reg["by_kind"],
             "increment": reg["increment"],
             "increment_note": reg["increment_note"]}, top))
    suite = signals.get("suite")
    if suite and suite["red"] > 0:
        cands.append(make_candidate(
            "suite-repair", suite["red"], {"red_cases": suite["red_cases"],
                                           "source": suite["source"]}, top))
    live_topics = set(c["topic"] for c in cands)
    for standing in STANDING_CANDIDATES:
        if standing["topic"] in live_topics:
            continue
        score = score_of(standing["impact"], 1, standing["effort"])
        cands.append({"kind": standing["kind"], "title": standing["title"],
                      "impact": standing["impact"], "effort": standing["effort"],
                      "evidence_raw": 1, "evidence": 1, "score": score,
                      "topic": standing["topic"], "basis": {
                          "anchor": standing["anchor"],
                          "goal": standing["goal"],
                          "approach": standing["approach"],
                          "acceptance": standing["acceptance"]},
                      "in_draft": False, "rank": None,
                      "_spec": standing, "_top": top})
    cands.sort(key=lambda c: (-c["score"], c["kind"], c["title"]))
    for i, c in enumerate(cands, 1):
        c["rank"] = i
        c["in_draft"] = i <= top
    return cands, notes


# ---- stage 3: draft ---------------------------------------------------------

PREAMBLE = """\
## Preamble — constitution three laws (auto-carried)

1. Law one (annotation / normalization / English-ization): every newly
   written face is English-only, passes the normalization lint with zero
   error-level findings, and carries zero jargon residue against the mapping
   table (`docs/jargon-to-standard-mapping-v1.md`); translation replacement
   archives the replaced Chinese prose in a sibling `.zh.md` file.
2. Law two (contributor isolation): this round does not touch contrib-lane
   semantics; core-lane registry rows cross only through the intake pipeline
   (`docs/contrib-isolation-protocol-v1.0-20261113.md`); fetch before
   claiming, first canonical write wins, file-face layering holds.
3. Law three (autonomous evolution): this brief is produced by the evolution
   engine (`tools/evolve.py`); mutation = live-signal-derived candidates,
   selection = the suite/lint/gate checks, heredity = the frozen-ledger
   lineage.

Safety track: every candidate below is a proposal only. The
autonomous-execution gate stays with human review — the reviewer decides
which candidates become round tasks; nothing in this draft has been
executed, and the engine wrote nothing outside its explicit output paths.
"""


def fmt_int(v):
    """Deterministic integer rendering (delta values keep their sign)."""
    return "%+d" % v if v < 0 or v > 0 else "0"


def candidate_section(c, idx):
    """Render one candidate as the four-section draft block."""
    lines = []
    lines.append("## Candidate %d — %s (rank %d, score %.4f)"
                 % (idx, c["kind"], c["rank"], c["score"]))
    lines.append("")
    spec = c["_spec"]
    basis = c["basis"]
    goal = spec.get("goal", basis.get("goal", ""))
    approach = spec.get("approach", basis.get("approach", ""))
    acceptance = spec.get("acceptance", basis.get("acceptance", ""))
    if c["kind"] == "norm-regression":
        goal = goal.format(
            delta_grow=sum(r["delta"] for r in basis["regressions"]),
            n_regress=len(basis["regressions"]))
    elif c["kind"] == "longtail-translation":
        tops = ", ".join("`%s` (%d)" % (f["path"], f["error"])
                         for f in basis["top_error_files"][:4])
        goal = goal.format(err_mass=basis["translatable_error_mass"],
                           top_files=tops or "none listed")
    elif c["kind"] == "taxonomy-supplement":
        goal = goal.format(unrec_n=c["evidence_raw"])
    elif c["kind"] == "red-triage":
        goal = goal.format(a_n=c["evidence_raw"])
    elif c["kind"] == "registry-hygiene":
        goal = goal.format(dup_n=basis["summary"]["duplicates"],
                           orph_n=basis["summary"]["orphans"])
    elif c["kind"] == "suite-repair":
        goal = goal.format(red_n=c["evidence_raw"])
    lines.append("- **Goal** — " + goal)
    lines.append("- **Approach** — " + approach)
    lines.append("- **Acceptance** — " + acceptance)
    lines.append("- **Grading** — impact %d x evidence %d (raw %d, clamped "
                 "to %d) / effort %d = score %.4f; %s."
                 % (c["impact"], c["evidence"], c["evidence_raw"],
                    EVIDENCE_CAP, c["effort"], c["score"],
                    _grading_reason(c)))
    lines.append("- **Evidence** — " + _evidence_line(c))
    lines.append("")
    return "\n".join(lines)


def _grading_reason(c):
    """One mechanical sentence on why this grading holds for the kind."""
    return {
        "norm-regression": "a fitness regression blocks new surface work "
                           "and touches few files",
        "longtail-translation": "the fitness main signal, a broad long tail",
        "taxonomy-supplement": "each maintained event needs review, not "
                               "code mass",
        "red-triage": "failing runs block the serviced lane and route "
                      "mechanically",
        "registry-hygiene": "prescriptions are deterministic but touch a "
                            "multi-writer surface",
        "suite-repair": "the suite is the selection face; a red suite "
                        "outranks all",
        "standing-candidate": "persisted memory with no live signal this "
                              "round; baseline agenda weight",
    }[c["kind"]]


def _evidence_line(c):
    """One mechanical evidence sentence per kind (counts and pointers).

    Cited paths are backticked: backtick spans are identifier citations and
    the scanners mask them on the jargon and CJK faces alike.
    """
    b = c["basis"]
    if c["kind"] == "norm-regression":
        rows = "; ".join("`%s` +%d" % (r["path"], r["delta"])
                         for r in b["regressions"][:8])
        return "norm signal: translatable delta %s; regressing files: %s." \
               % (fmt_int(b["translatable_delta"]["error"]), rows)
    if c["kind"] == "longtail-translation":
        tops = "; ".join("`%s` (%d)" % (f["path"], f["error"])
                         for f in b["top_error_files"])
        return "norm signal: translatable error mass %d; reduction rate " \
               "error %.4f warn %.4f since baseline; top carriers: %s." \
               % (b["translatable_error_mass"], b["reduction_rate"]["error"],
                  b["reduction_rate"]["warn"], tops or "none")
    if c["kind"] == "taxonomy-supplement":
        rows = "; ".join(
            "%s run %s%s" % (m["repo"], m.get("run_number", m.get("run")),
                             " (seq %s)" % m["stream_seq"]
                             if m.get("stream_seq") is not None else "")
            for m in b["maintained"][:8])
        return "UNRECOGNIZED maintained events: %s." % (rows or "none")
    if c["kind"] == "red-triage":
        hist = ", ".join("%s=%d" % (k, v)
                         for k, v in sorted(b["family_histogram"].items()))
        return "sentinel signal: %d new ci-red event(s), histogram %s." \
               % (b["new_ci_red"], hist or "none")
    if c["kind"] == "registry-hygiene":
        kinds = ", ".join("%s=%d" % (k, v)
                          for k, v in sorted(b["by_kind"].items()))
        inc = ("increment %s" % json.dumps(b["increment"], sort_keys=True)
               if b["increment"] is not None else b["increment_note"])
        return "registry signal: duplicates %d, anchors %d, orphans %d, " \
               "total %d (%s); by kind: %s." \
               % (b["summary"]["duplicates"], b["summary"]["anchors"],
                  b["summary"]["orphans"], b["summary"]["total"], inc, kinds)
    if c["kind"] == "suite-repair":
        rows = ", ".join("%s (rc=%d)" % (r["case"], r["rc"])
                         for r in b["red_cases"][:8])
        return "suite signal: %d red case(s) from %s: %s." \
               % (len(b["red_cases"]), b["source"], rows or "none")
    return "heredity: %s." % b.get("anchor", "frozen-ledger lineage")


def render_draft(draft_path, repo_root, candidates, notes, signals, top):
    """Stage 3: render the task-brief draft (deterministic bytes).

    The banner derives from the --draft-out basename; the constitution
    preamble is auto-carried; each in-draft candidate renders as the
    four-section block; rule completion notes and non-selected candidates
    are listed so the reviewer sees the full account and the cut line.
    """
    name = os.path.basename(draft_path)
    in_draft = [c for c in candidates if c["in_draft"]]
    dropped = [c for c in candidates if not c["in_draft"]]
    L = []
    L.append("# %s — next-round task-brief draft produced by tools/evolve.py "
             "(human-review gate deliverable)." % name)
    L.append("")
    L.append("> **EvolveDraft**: the next-round task brief generated from "
             "harvested repository signals; candidates are proposals, the "
             "autonomous-execution gate stays with human review.")
    L.append(">")
    L.append("> Purpose.  Carry the evolution round's selected candidates to "
             "the reviewer as concrete task briefs: each carries a goal, an "
             "approach, an acceptance set and a mechanical grading; the "
             "constitution three-law preamble rides on every draft this "
             "engine emits.")
    L.append(">")
    L.append("> Interface.  Produced by `python3 tools/evolve.py --draft-out "
             "%s` (with the harvested signal flags recorded below); consumed "
             "by the human reviewer, who turns accepted candidates into the "
             "next round's task assignments." % name)
    L.append(">")
    L.append("> Dependencies.  None to read this file; the engine that "
             "produced it runs on the Python 3 standard library and "
             "subprocesses the sibling engines only.")
    L.append(">")
    L.append("> Evidence.  Every candidate cites the harvested signal that "
             "derived it (the round inputs section below carries the full "
             "counts); the grading formula is impact x evidence / effort "
             "with evidence clamped to %d." % EVIDENCE_CAP)
    L.append(">")
    L.append("> Exit-codes.  Not applicable to a data face; the producing "
             "engine exits 0 on completion, 2 on usage error, 9 on missing "
             "or unreachable input.")
    L.append("")
    L.append(PREAMBLE.rstrip())
    L.append("")
    L.append("## Round inputs (fitness account)")
    L.append("")
    L.append("- Repository root: `%s`" % repo_root)
    L.append("- Draft width (--top): %d; candidates derived: %d; drafted: %d."
             % (top, len(candidates), len(in_draft)))
    norm = signals.get("norm")
    if norm:
        L.append("- Norm fitness: current error %d / warn %d vs baseline %d / "
                 "%d; raw delta %s / %s; translatable delta %s / %s; "
                 "reduction rate error %.4f warn %.4f."
                 % (norm["current"]["error"], norm["current"]["warn"],
                    norm["baseline"]["error"], norm["baseline"]["warn"],
                    fmt_int(norm["baseline_delta"]["error"]),
                    fmt_int(norm["baseline_delta"]["warn"]),
                    fmt_int(norm["translatable_delta"]["error"]),
                    fmt_int(norm["translatable_delta"]["warn"]),
                    norm["reduction_rate"]["error"],
                    norm["reduction_rate"]["warn"]))
        L.append("  - Frozen surfaces excluded from the translatable metric: "
                 "%s." % ", ".join("`%s`" % p for p in norm["excluded_frozen"]))
    else:
        L.append("- Norm fitness: not harvested (no --baseline given); "
                 "fitness.baseline_delta is null in the report.")
    sent = signals.get("sentinel")
    if sent:
        L.append("- Sentinel round: %d new ci-red event(s) over %s; family "
                 "histogram %s."
                 % (sent["new_ci_red"],
                    ", ".join("`%s`" % r for r in sent["watch_repos"]),
                    json.dumps(sent["family_histogram"], sort_keys=True)))
    else:
        L.append("- Sentinel round: not harvested (no --watch-repo given).")
    suite = signals.get("suite")
    if suite:
        L.append("- Suite state (%s): %d pass / %d red / %d skip / %d total."
                 % (suite["source"], suite["pass"], suite["red"],
                    suite["skip"], suite["total"]))
    else:
        L.append("- Suite state: not harvested (no --suite-ledger or "
                 "--suite-now given).")
    reg = signals.get("registry")
    if reg:
        L.append("- Registry audit (`%s`@`%s`): duplicates %d, anchors %d, "
                 "orphans %d, total %d; %s."
                 % (reg["git_repo"], reg["ref"], reg["summary"]["duplicates"],
                    reg["summary"]["anchors"], reg["summary"]["orphans"],
                    reg["summary"]["total"], reg["increment_note"]))
    else:
        L.append("- Registry audit: not harvested (no --registry-git given).")
    unrec = signals.get("unrec")
    if unrec:
        L.append("- Maintained UNRECOGNIZED events: %d."
                 % unrec["count"])
    else:
        L.append("- Maintained UNRECOGNIZED events: not harvested (no "
                 "--sentinel-events/--sentinel-state given).")
    L.append("")
    for i, c in enumerate(in_draft, 1):
        L.append(candidate_section(c, i))
    if notes:
        L.append("## Notes")
        L.append("")
        for note in notes:
            L.append("- %s." % note)
        L.append("")
    if dropped:
        L.append("## Not drafted this round (beyond the top-%d cut)" % top)
        L.append("")
        for c in dropped:
            L.append("- rank %d — %s (score %.4f)."
                     % (c["rank"], c["title"], c["score"]))
        L.append("")
    L.append("## Boundary")
    L.append("")
    L.append("This draft is a deliverable of the harvest→derive→draft "
             "pipeline only. The engine does not execute candidates, does "
             "not modify the repository, and does not touch the frozen "
             "surfaces; turning a candidate into a round task is the "
             "reviewer's decision.")
    return "\n".join(L) + "\n"


# ---- pipeline ---------------------------------------------------------------


def build_report(repo_root, top, signals, candidates, notes, draft_path):
    """Assemble the rocqwash-evolve/1 report (fitness face included)."""
    norm = signals.get("norm")
    fitness = {
        "baseline_delta": (norm["baseline_delta"] if norm else None),
        "translatable_delta": (norm["translatable_delta"] if norm else None),
        "reduction_rate": (norm["reduction_rate"] if norm else None),
    }
    public = []
    for c in candidates:
        public.append({k: c[k] for k in ("rank", "kind", "title", "score",
                                         "impact", "effort", "evidence",
                                         "evidence_raw", "in_draft", "topic",
                                         "basis")})
    return {
        "schema": SCHEMA,
        "tool": PROG,
        "repo_root": os.path.abspath(repo_root),
        "top": top,
        "signals": signals,
        "candidates": public,
        "notes": list(notes),
        "draft_path": os.path.abspath(draft_path),
        "fitness": fitness,
    }


def run_pipeline(args):
    """harvest → derive → draft; returns the report object."""
    tmpdir = tempfile.mkdtemp(prefix="rocqwash_evolve_")
    try:
        signals = {}
        if args.baseline:
            jargon_map = args.jargon_map or os.path.join(
                args.repo_root, DEFAULT_JARGON_MAP)
            signals["norm"] = harvest_norm(
                args.repo_root, jargon_map, args.baseline, tmpdir)
        if args.watch_repos:
            signals["sentinel"] = harvest_sentinel(
                args.watch_repos, args.sentinel_state,
                args.sentinel_state_seed, args.sentinel_branch, tmpdir,
                injector_path=args.sentinel_injector)
        if args.suite_now or args.suite_ledger:
            signals["suite"] = harvest_suite(
                args.repo_root, args.suite_ledger, args.suite_now, tmpdir)
        if args.registry_git:
            signals["registry"] = harvest_registry(
                args.registry_git, args.registry_ref, args.git_path_order,
                args.git_path_project, args.registry_baseline, tmpdir)
        if args.sentinel_events or args.sentinel_state:
            signals["unrec"] = harvest_unrec(
                args.sentinel_events, args.sentinel_state)
        if not signals:
            fail("no signal source requested: give at least one of "
                 "--baseline / --watch-repo / --suite-ledger / --suite-now / "
                 "--registry-git / --sentinel-events", 2)
        candidates, notes = derive_candidates(signals, args.top)
        draft_text = render_draft(args.draft_out, args.repo_root, candidates,
                                  notes, signals, args.top)
        write_text(args.draft_out, draft_text)
        return build_report(args.repo_root, args.top, signals, candidates,
                            notes, args.draft_out)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def parse_args(argv):
    """CLI parsing with the cross-flag guards (usage errors exit 2)."""
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="autonomous evolution engine v1 — harvest signals from "
                    "the existing engines, derive scored candidates, draft "
                    "the human-gated next-round task brief")
    ap.add_argument("--draft-out", dest="draft_out", default=None,
                    metavar="PATH",
                    help="task-brief draft output (required; parent must "
                         "exist)")
    ap.add_argument("--json", default=None, metavar="PATH",
                    help="report output (rocqwash-evolve/1, sort_keys)")
    ap.add_argument("--repo-root", dest="repo_root", default=REPO_ROOT,
                    metavar="DIR", help="repository root (default: the "
                    "parent of the directory holding this engine)")
    ap.add_argument("--top", type=int, default=DEFAULT_TOP, metavar="N",
                    help="draft width (default 5)")
    ap.add_argument("--baseline", default=None, metavar="PATH",
                    help="norm-lint baseline report (fitness signal)")
    ap.add_argument("--jargon-map", dest="jargon_map", default=None,
                    metavar="PATH",
                    help="mapping table forwarded to the norm scan "
                    "(default docs/jargon-to-standard-mapping-v1.md under "
                    "the repo root)")
    ap.add_argument("--watch-repo", dest="watch_repos", action="append",
                    default=None, metavar="ORG/REPO",
                    help="enable the sentinel signal (repeatable)")
    ap.add_argument("--sentinel-state", dest="sentinel_state", default=None,
                    metavar="PATH",
                    help="harvest state file (required with --watch-repo)")
    ap.add_argument("--sentinel-state-seed", dest="sentinel_state_seed",
                    default=None, metavar="PATH",
                    help="existing state copied to the harvest state before "
                    "the round (read-only seed)")
    ap.add_argument("--sentinel-branch", dest="sentinel_branch", default=None,
                    metavar="B", help="branch filter forwarded to each "
                    "watched repository")
    ap.add_argument("--sentinel-events", dest="sentinel_events",
                    default=None, metavar="PATH",
                    help="existing event stream JSONL scanned for "
                    "maintained UNRECOGNIZED events (read-only)")
    ap.add_argument("--sentinel-injector", dest="sentinel_injector",
                    default=None, metavar="PATH",
                    help="canned API responses forwarded to the sentinel "
                    "child (its own --injector flag; offline rounds)")
    ap.add_argument("--suite-ledger", dest="suite_ledger", default=None,
                    metavar="PATH",
                    help="captured run_tests.sh output (suite signal)")
    ap.add_argument("--suite-now", dest="suite_now", action="store_true",
                    help="run the suite live instead of reading a ledger")
    ap.add_argument("--registry-git", dest="registry_git", default=None,
                    metavar="REPO",
                    help="enable the registry signal (git direct-read form)")
    ap.add_argument("--registry-ref", dest="registry_ref", default=None,
                    metavar="REF", help="ref the audit reads (required with "
                    "--registry-git)")
    ap.add_argument("--git-path-order", dest="git_path_order", default=None,
                    metavar="PATH", help="order.txt path override inside the "
                    "ref")
    ap.add_argument("--git-path-project", dest="git_path_project",
                    default=None, metavar="PATH",
                    help="_CoqProject path override inside the ref")
    ap.add_argument("--registry-baseline", dest="registry_baseline",
                    default=None, metavar="PATH",
                    help="prior audit report for the increment accounting")
    args = ap.parse_args(argv)
    if not args.draft_out:
        fail("--draft-out is required (the draft is the spawn-gate "
             "deliverable)", 2)
    if args.top < 1:
        fail("--top must be >= 1 (got %d)" % args.top, 2)
    if args.suite_now and args.suite_ledger:
        fail("--suite-now and --suite-ledger are mutually exclusive "
              "(one suite source per round)", 2)
    if args.watch_repos and not args.sentinel_state:
        fail("--watch-repo requires --sentinel-state (a new-events account "
             "is undefined without a seen ledger)", 2)
    if bool(args.registry_git) != bool(args.registry_ref):
        fail("--registry-git and --registry-ref must be given together", 2)
    return args


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    try:
        args = parse_args(argv)
        ensure_parent(args.draft_out, "--draft-out")
        if args.json:
            ensure_parent(args.json, "--json")
        report = run_pipeline(args)
    except EvolveError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(e.code)
    if args.json:
        dump_json(args.json, report)
    n_draft = sum(1 for c in report["candidates"] if c["in_draft"])
    delta = report["fitness"]["baseline_delta"]
    delta_txt = ("error %s warn %s" % (fmt_int(delta["error"]),
                                       fmt_int(delta["warn"]))
                 if delta else "not harvested")
    print("evolve %s: signals=%d candidates=%d drafted=%d draft=%s "
          "fitness_delta(%s)" % (SCHEMA, len(report["signals"]),
                                 len(report["candidates"]), n_draft,
                                 report["draft_path"], delta_txt))
    if args.json:
        print("json: " + os.path.abspath(args.json))
    return 0


# ---- selftest ----------------------------------------------------------------


def _expect(cond, msg, fails):
    """Selftest assertion collector (fail-loud at the vector level)."""
    if not cond:
        fails.append(msg)


def _wf(path, text):
    """Write a selftest fixture file (utf-8, lf)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# Fixture constants (data, not prose faces: string literals passed as
# arguments are invisible to the prose scanner — the norm engine only scans
# comments and bare-string statements). The map fixture mirrors the mapping
# table shape the norm engine parses; the book fixtures mirror the audit
# engine's frozen vector set (expected accounts: duplicates 2, anchors 7,
# orphans 5, total 14).
MAP_FIXTURE = (
    "# fixture mapping table (selftest)\n"
    "\n"
    "| \u9ed1\u8bdd (jargon face) | \u6807\u51c6 (standard expression) "
    "| \u8bed\u5883\u6ce8\u8bb0 (context note) |\n"
    "|---|---|---|\n"
    "| persist-to-disk | write to file | fixture row |\n")
CLEAN_FIXTURE = (
    '"""clean_mod: a compliant fixture face.\n'
    "\n"
    "    Purpose.  A fixture that passes all five fields.\n"
    "    Interface.  None (fixture).\n"
    "    Dependencies.  None.\n"
    "    Evidence.  Selftest vector.\n"
    "    Exit-codes.  0.\n"
    '"""\n'
    "x = 1\n")
DIRTY_FIXTURE = (
    '"""dirty_mod: a fixture carrying a known term.\n'
    "\n"
    "    Purpose.  A fixture that trips the jargon face.\n"
    "    Interface.  None (fixture).\n"
    "    Dependencies.  None.\n"
    "    Evidence.  Selftest vector.\n"
    "    Exit-codes.  0.\n"
    '"""\n'
    "# persist-to-disk here\n"
    "y = 2\n")
ORDER_FIXTURE = "\n".join([
    "A.v#R0-d66910",        # shape-odd six-digit stamp, anchor collision
    "B.v#R0-d66910",        # anchor collision (different key, same text)
    "C.v#R97",              # sequence-only form (no fingerprint)
    "D.v#R43a003",          # sequence-only form (reads as R43)
    "E.v#R97-b48a001",      # shape-odd seven-digit stamp
    "F.v",                  # missing anchor
    "G.v#R0-11111111",      # canonical (8 lowercase hex digits)
    "A.v#R40-22222222",     # same key, different anchor generation row
    "# comment line",       # comment (no key, outside the books)
]) + "\n"
PROJECT_FIXTURE = "\n".join([
    "-Q . \"\"",            # flag line (filtered out of matching)
    "A.v",
    "A.v",                  # duplicate key
    "C.v",
    "E.v",
    "H.v",                  # orphan (project-only)
]) + "\n"


def selftest():
    """Embedded frozen vector group (tmp fixtures, zero network, zero
    repository writes).

    Vectors:
      [1] canned norm signal through the real norm engine on a tmp tree,
          with the frozen-surface exclusion unit-checked;
      [2] suite ledger parse (green and red forms) and a malformed ledger;
      [3] UNRECOGNIZED maintained events from a canned stream and state;
      [4] registry harvest against a tmp git repo (real audit child) with
          the increment and first-run faces;
      [5] candidate rules (kinds, scores, clamping, ordering);
      [6] genetic standing candidates and live-topic dedup;
      [7] draft formation (preamble, four sections, deterministic bytes);
      [8] deterministic double run of the full CLI on canned inputs;
      [9] sentinel canned injector round, seen-idempotence second round,
          and the seeded harvest face;
      [10] CLI usage contract (2/9 faces).
    """
    fails = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_evolve_self_")
    tool = os.path.abspath(__file__)
    try:
        # ---- [1] canned norm signal (real subprocess on a tmp tree) ----
        tree = os.path.join(tmp, "tree")
        os.makedirs(tree)
        map_path = os.path.join(tmp, "map.md")
        _wf(map_path, MAP_FIXTURE)
        _wf(os.path.join(tree, "clean.py"), CLEAN_FIXTURE)
        _wf(os.path.join(tree, "dirty.py"), DIRTY_FIXTURE)
        first_scan = os.path.join(tmp, "baseline_scan.json")
        rc, _o, err = run_child(
            [sys.executable, "-B", NORM_TOOL, "--tree", tree,
             "--jargon-map", map_path, "--json", first_scan],
            "selftest norm scan", NORM_TIMEOUT)
        _expect(rc == 0, "vector1 baseline scan rc=%d %s" % (rc, err), fails)
        norm_sig = harvest_norm(tree, map_path, first_scan, tmp)
        _expect(norm_sig["translatable_delta"]["error"] == 0
                and norm_sig["translatable_delta"]["warn"] == 0,
                "vector1 clean-vs-baseline delta should be 0: %s"
                % norm_sig["translatable_delta"], fails)
        _expect(norm_sig["translatable_error_mass"] == 1,
                "vector1 dirty fixture should carry 1 error finding: %s"
                % norm_sig["translatable_error_mass"], fails)
        # frozen exclusion: a synthetic growth sitting only on the ledger
        base_rep = load_json(first_scan, "fixture baseline")
        grow_rep = json.loads(json.dumps(base_rep))
        grow_rep["files"].append(
            {"path": FROZEN_LEDGER, "kind": "md", "cjk_ratio": 0.0,
             "cjk_chars": 0, "face_chars": 10,
             "findings": [{"line": 1, "kind": "jargon", "term": "x",
                           "suggest": "s"}] * 8})
        grow_path = os.path.join(tmp, "grow.json")
        _wf(grow_path, json.dumps(grow_rep, ensure_ascii=False))
        norm_base = norm_counts(base_rep)
        norm_grow = norm_counts(load_json(grow_path, "grow"))
        _expect(norm_grow["error"] - norm_base["error"] == 8,
                "vector1 raw delta should be 8", fails)
        base_tr = norm_counts(base_rep, exclude=frozen_surfaces())
        grow_tr = norm_counts(load_json(grow_path, "grow"),
                              exclude=frozen_surfaces())
        _expect(grow_tr["error"] - base_tr["error"] == 0,
                "vector1 frozen growth must not enter the translatable delta",
                fails)
        print("PASS [1] canned norm signal + frozen exclusion")

        # ---- [2] suite ledger parse ----
        green = os.path.join(tmp, "suite_green.txt")
        _wf(green,
            "== rocqwash tests/ suite ==\n"
            "[62/62] t_last                 PASS\n"
            "== \u6c47\u603b: 61 \u8fc7 / 0 \u7ea2 / 1 \u7565 / \u5171 62 \u4f8b ==\n")
        s = harvest_suite(tmp, green, False, tmp)
        _expect((s["pass"], s["red"], s["skip"], s["total"])
                == (61, 0, 1, 62), "vector2 green parse: %s" % s, fails)
        redl = os.path.join(tmp, "suite_red.txt")
        _wf(redl,
            "[1/2] t_alpha                    FAIL (rc=1)\n"
            "[2/2] t_beta                     PASS\n"
            "== \u6c47\u603b: 1 \u8fc7 / 1 \u7ea2 / 0 \u7565 / \u5171 2 \u4f8b ==\n")
        s = harvest_suite(tmp, redl, False, tmp)
        _expect(s["red"] == 1 and s["red_cases"][0]["case"] == "t_alpha"
                and s["red_cases"][0]["rc"] == 1,
                "vector2 red parse: %s" % s, fails)
        bad = os.path.join(tmp, "suite_bad.txt")
        _wf(bad, "no summary line here\n")
        try:
            harvest_suite(tmp, bad, False, tmp)
            fails.append("vector2 malformed ledger must fail loud 9")
        except EvolveError as e:
            _expect(e.code == 9, "vector2 malformed ledger code=%d" % e.code,
                    fails)
        print("PASS [2] suite ledger parse green/red/malformed")

        # ---- [3] UNRECOGNIZED maintained events ----
        ev1 = {"schema": SENTINEL_EVENT_SCHEMA, "kind": "ci-red", "seq": 12,
               "repo": "org/r1", "run": 111, "run_number": 3,
               "family": FAMILY_UNREC, "action": "watch-only",
               "ts": None, "evidence": ["e1"]}
        ev2 = {"schema": SENTINEL_EVENT_SCHEMA, "kind": "ci-red", "seq": 13,
               "repo": "org/r1", "run": 222, "run_number": 4,
               "family": FAMILY_A, "action": "fix-content",
               "ts": None, "evidence": []}
        ev3 = {"schema": SENTINEL_EVENT_SCHEMA, "kind": "ci-red", "seq": 14,
               "repo": "org/r2", "run": 333, "run_number": 5,
               "family": FAMILY_UNREC, "action": "watch-only",
               "ts": None, "evidence": []}
        stream = os.path.join(tmp, "events.jsonl")
        _wf(stream, "\n".join(
            json.dumps(e, sort_keys=True) for e in (ev1, ev2, ev3)) + "\n")
        state = {"schema": SENTINEL_STATE_SCHEMA, "repos": {
            "org/r1": {"seen_runs": {
                "111": {"family": FAMILY_UNREC},
                "222": {"family": FAMILY_A}}}},
            "ledgers": {}, "buildlogs": {}}
        state_path = os.path.join(tmp, "state.json")
        _wf(state_path, json.dumps(state))
        u = harvest_unrec(stream, state_path)
        _expect(u["count"] == 2, "vector3 maintained count: %d" % u["count"],
                fails)
        _expect(u["maintained"][0]["repo"] == "org/r1"
                and u["maintained"][0]["state_present"] is True,
                "vector3 first maintained row: %s" % u["maintained"][0],
                fails)
        _expect(u["maintained"][1]["repo"] == "org/r2"
                and u["maintained"][1]["state_present"] is False,
                "vector3 stream-only row: %s" % u["maintained"][1], fails)
        badstream = os.path.join(tmp, "bad_events.jsonl")
        _wf(badstream, "not json\n")
        try:
            harvest_unrec(badstream, None)
            fails.append("vector3 malformed stream must fail loud 9")
        except EvolveError as e:
            _expect(e.code == 9, "vector3 malformed stream code=%d" % e.code,
                    fails)
        print("PASS [3] UNRECOGNIZED maintained events (stream+state)")

        # ---- tmp git repo (shared by vectors 4 and 8; registry_audit
        #      selftest pattern: fixed identity env, symbolic-ref branch) --
        gdir = os.path.join(tmp, "grepo")
        os.makedirs(gdir)
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00 +0000",
                    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00 +0000"})

        def g(*a):
            p = subprocess.run(["git", "-C", gdir] + list(a), env=env,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            _expect(p.returncode == 0,
                    "git %s failed: %s" % (a[0], p.stdout[-200:]), fails)
            return p.stdout.decode("utf-8", errors="replace").strip()

        g("init")
        branch = g("symbolic-ref", "--short", "HEAD")
        _wf(os.path.join(gdir, "order.txt"), ORDER_FIXTURE)
        _wf(os.path.join(gdir, "_CoqProject"), PROJECT_FIXTURE)
        g("add", "order.txt", "_CoqProject")
        g("commit", "-m", "books")

        # ---- [4] registry harvest (real audit child) + increment ----
        reg = harvest_registry(gdir, branch, None, None, None, tmp)
        _expect(reg["summary"] == {"duplicates": 2, "anchors": 7,
                                   "orphans": 5, "live": 0, "total": 14},
                "vector4 audit accounts: %s" % reg["summary"], fails)
        _expect(reg["increment"] is None
                and "first-run" in reg["increment_note"],
                "vector4 first-run face: %s" % reg["increment_note"], fails)
        pri = {"schema": AUDIT_SCHEMA, "mode": "git", "inputs": {},
               "stats": {}, "sections": {}, "summary": {
                   "duplicates": 1, "anchors": 7, "orphans": 4, "live": 0,
                   "total": 12, "by_kind": {}}}
        pri_path = os.path.join(tmp, "audit_pri.json")
        _wf(pri_path, json.dumps(pri))
        reg2 = harvest_registry(gdir, branch, None, None, pri_path, tmp)
        _expect(reg2["increment"] == {"duplicates": 1, "anchors": 0,
                                      "orphans": 1, "live": 0, "total": 2},
                "vector4 increment: %s" % reg2["increment"], fails)
        print("PASS [4] registry harvest (real child) + increment")

        # ---- [5] candidate rules ----
        sig = {}
        sig["suite"] = {"present": True, "source": "ledger", "pass": 60,
                        "red": 2, "skip": 0, "total": 62,
                        "red_cases": [{"case": "t_a", "rc": 1}]}
        sig["unrec"] = {"present": True, "events_file": None,
                        "state_file": None, "maintained": [], "count": 9}
        sig["norm"] = {"present": True, "baseline_path": "b",
                       "current": {"error": 100, "warn": 10, "files": 5,
                                   "cjk_ratio": 0.0},
                       "baseline": {"error": 90, "warn": 10, "files": 5,
                                    "cjk_ratio": 0.0},
                       "baseline_delta": {"error": 10, "warn": 0,
                                          "files": 0},
                       "translatable_delta": {"error": 10, "warn": 0,
                                              "files": 0},
                       "translatable_error_mass": 100,
                       "reduction_rate": {"error": -0.111111, "warn": 0.0},
                       "regressions": [{"path": "a.py", "delta": 10,
                                        "current": 10}],
                       "top_error_files": [{"path": "a.py", "error": 10,
                                            "warn": 0}],
                       "excluded_frozen": [FROZEN_LEDGER]}
        cands, notes = derive_candidates(sig, 5)
        _expect(notes == [], "vector5 no notes on a live round", fails)
        kinds = [c["kind"] for c in cands]
        _expect(kinds[0] == "suite-repair",
                "vector5 suite repair must outrank (impact 5): %s" % kinds,
                fails)
        _expect("norm-regression" in kinds and "taxonomy-supplement" in kinds,
                "vector5 kinds: %s" % kinds, fails)
        reg_c = [c for c in cands if c["kind"] == "norm-regression"][0]
        _expect(reg_c["evidence_raw"] == 1 and reg_c["score"] == 2.0,
                "vector5 regression score impact4*ev1/effort2: %s" % reg_c,
                fails)
        # clamp: a 100-item error mass scores on evidence 10
        sig2 = {"norm": dict(sig["norm"],
                             translatable_delta={"error": 0, "warn": 0,
                                                 "files": 0},
                             regressions=[])}
        cands2, _n2 = derive_candidates(sig2, 5)
        lt = [c for c in cands2 if c["kind"] == "longtail-translation"][0]
        _expect(lt["evidence_raw"] == 100 and lt["evidence"] == 10
                and lt["score"] == 10.0,
                "vector5 clamp: raw 100 -> evidence 10, score 10: %s" % lt,
                fails)
        scores = [c["score"] for c in cands]
        _expect(scores == sorted(scores, reverse=True),
                "vector5 order by score desc: %s" % scores, fails)
        _expect([c["rank"] for c in cands] == list(range(1, len(cands) + 1)),
                "vector5 contiguous ranks", fails)
        print("PASS [5] candidate rules (kinds, scores, clamp, order)")

        # ---- [6] standing candidates + dedup ----
        sig3 = {"registry": {"present": True, "git_repo": "r", "ref": "x",
                             "path_order": "order.txt",
                             "path_project": "_CoqProject",
                             "summary": {"duplicates": 12, "anchors": 0,
                                         "orphans": 0, "live": 0, "total": 12},
                             "by_kind": {}, "increment": None,
                             "increment_note": "first-run"}}
        cands3, _n3 = derive_candidates(sig3, 5)
        kinds3 = [c["kind"] for c in cands3]
        _expect("registry-hygiene" in kinds3,
                "vector6 live registry candidate: %s" % kinds3, fails)
        _expect("standing-candidate" in kinds3,
                "vector6 standing candidates present: %s" % kinds3, fails)
        topics = [c["topic"] for c in cands3
                  if c["kind"] == "standing-candidate"]
        _expect("registry" not in topics,
                "vector6 registry standing deduped by live topic: %s"
                % topics, fails)
        _expect(all(c["score"] == 0.5 for c in cands3
                    if c["kind"] == "standing-candidate"),
                "vector6 standing score 1*1/2: %s"
                % [c["score"] for c in cands3
                   if c["kind"] == "standing-candidate"], fails)
        print("PASS [6] standing candidates + live-topic dedup")

        # ---- [7] draft formation ----
        draft_a = os.path.join(tmp, "d1", "draft_run.md")
        os.makedirs(os.path.join(tmp, "d1"))
        text = render_draft(draft_a, tmp, cands3, [], sig3, 5)
        _expect("## Preamble \u2014 constitution three laws" in text,
                "vector7 preamble auto-carried", fails)
        _expect("- **Goal** \u2014" in text and "- **Approach** \u2014" in text
                and "- **Acceptance** \u2014" in text
                and "- **Grading** \u2014" in text,
                "vector7 four sections per candidate", fails)
        _expect("registry-hygiene" in text,
                "vector7 live candidate rendered", fails)
        _expect(text.startswith("# draft_run.md \u2014 "),
                "vector7 banner derives from the output basename", fails)
        _expect(text == render_draft(draft_a, tmp, cands3, [], sig3, 5),
                "vector7 draft deterministic bytes", fails)
        text_note = render_draft(draft_a, tmp, [], ["all faces translated"],
                                 sig3, 5)
        _expect("## Notes" in text_note and "all faces translated" in text_note,
                "vector7 notes section renders", fails)
        print("PASS [7] draft formation (preamble, sections, determinism)")

        # ---- [8] deterministic double run of the full CLI ----
        run_root = os.path.join(tmp, "run")
        os.makedirs(run_root)
        _wf(os.path.join(run_root, "mod.py"), CLEAN_FIXTURE)
        ledger8 = os.path.join(run_root, "ledger.txt")
        _wf(ledger8,
            "[1/1] t_one                     PASS\n"
            "== \u6c47\u603b: 1 \u8fc7 / 0 \u7ea2 / 0 \u7565 / \u5171 1 \u4f8b ==\n")
        ev_a = {"schema": SENTINEL_EVENT_SCHEMA, "kind": "ci-red", "seq": 1,
                "repo": "org/g", "run": 7, "run_number": 1,
                "family": FAMILY_UNREC, "action": "watch-only", "ts": None,
                "evidence": []}
        ev_path = os.path.join(run_root, "ev.jsonl")
        _wf(ev_path, json.dumps(ev_a, sort_keys=True) + "\n")
        os.makedirs(os.path.join(tmp, "d2"))
        draft_b = os.path.join(tmp, "d2", "draft_run.md")
        out_a = os.path.join(tmp, "report_a.json")
        out_b = os.path.join(tmp, "report_b.json")
        common = ["--repo-root", run_root, "--suite-ledger", ledger8,
                  "--sentinel-events", ev_path,
                  "--registry-git", gdir, "--registry-ref", branch,
                  "--top", "3"]
        rc, sout, _e = run_child(
            [sys.executable, "-B", tool, "--draft-out", draft_a,
             "--json", out_a] + common, "selftest run a", SUITE_TIMEOUT)
        _expect(rc == 0, "vector8 run a rc=%d: %s" % (rc, sout[-400:]), fails)
        rc, sout, _e = run_child(
            [sys.executable, "-B", tool, "--draft-out", draft_b,
             "--json", out_b] + common, "selftest run b", SUITE_TIMEOUT)
        _expect(rc == 0, "vector8 run b rc=%d: %s" % (rc, sout[-400:]), fails)
        rep_a = load_json(out_a, "report a")
        rep_b = load_json(out_b, "report b")
        rep_a.pop("draft_path")
        rep_b.pop("draft_path")
        _expect(json.dumps(rep_a, sort_keys=True)
                == json.dumps(rep_b, sort_keys=True),
                "vector8 report bytes equal across runs", fails)
        _expect(io.open(draft_a, encoding="utf-8").read()
                == io.open(draft_b, encoding="utf-8").read(),
                "vector8 draft bytes equal across runs", fails)
        _expect(rep_a["schema"] == SCHEMA and "fitness" in rep_a
                and "candidates" in rep_a and "signals" in rep_a,
                "vector8 report schema face", fails)
        print("PASS [8] deterministic double run (CLI, canned inputs)")

        # ---- [9] sentinel canned injector round + idempotence + seed ----
        inj = {"schema": "rocqwash-sentinel-injector/1", "responses": [
            {"url_contains": "/actions/runs?", "status": 200, "body": {
                "total_count": 1, "workflow_runs": [
                    {"id": 178, "name": "CI", "run_number": 9,
                     "status": "completed", "conclusion": "failure",
                     "head_branch": "main", "head_sha": "abc123def",
                     "html_url": "https://example.org/runs/178"}]}},
            {"url_contains": "/runs/178/jobs", "status": 200, "body": {
                "total_count": 1, "jobs": [
                    {"id": 501, "name": "build", "status": "completed",
                     "conclusion": "failure",
                     "started_at": "2026-11-10T08:00:00Z",
                     "completed_at": "2026-11-10T08:01:00Z",
                     "steps": [
                         {"number": 1, "name": "Build (coqc batch)",
                          "status": "completed", "conclusion": "failure",
                          "started_at": "2026-11-10T08:00:01Z",
                          "completed_at": "2026-11-10T08:00:30Z"}]}]}}]}
        inj_path = os.path.join(tmp, "injector.json")
        _wf(inj_path, json.dumps(inj, sort_keys=True))
        st = os.path.join(tmp, "sent_state.json")
        rep = os.path.join(tmp, "sent_rep.json")
        sent_sig = harvest_sentinel(["org/repo"], st, None, None, tmp,
                                    injector_path=inj_path)
        _expect(sent_sig["new_ci_red"] == 1
                and sent_sig["new_a_family"] == 1,
                "vector9 one A-family event from the canned injector: %s"
                % sent_sig["new_ci_red"], fails)
        _expect(sent_sig["events"][0]["run"] == 178,
                "vector9 event carries the run id: %s"
                % sent_sig["events"][0], fails)
        sent_sig2 = harvest_sentinel(["org/repo"], st, None, None, tmp,
                                     injector_path=inj_path)
        _expect(sent_sig2["new_ci_red"] == 0,
                "vector9 seen idempotence: second round 0 new events",
                fails)
        seed_state = os.path.join(tmp, "seed_state.json")
        shutil.copyfile(st, seed_state)
        st3 = os.path.join(tmp, "harvest_state.json")
        sent_sig3 = harvest_sentinel(["org/repo"], st3, seed_state, None,
                                     tmp, injector_path=inj_path)
        _expect(sent_sig3["new_ci_red"] == 0
                and sent_sig3["seeded"] is True,
                "vector9 seeded harvest round reports 0 new: %s"
                % sent_sig3["new_ci_red"], fails)
        try:
            harvest_sentinel(["org/repo"], seed_state, seed_state, None, tmp,
                             injector_path=inj_path)
            fails.append("vector9 seed==state must fail loud 2")
        except EvolveError as e:
            _expect(e.code == 2, "vector9 seed==state code=%d" % e.code,
                    fails)
        print("PASS [9] sentinel canned round + idempotence + seed")

        # ---- [10] CLI usage contract ----
        def cli(*a):
            r, o, e = run_child([sys.executable, "-B", tool] + list(a),
                                "selftest cli", NORM_TIMEOUT)
            return r, o, e
        r, _o, _e = cli("--bogus")
        _expect(r == 2, "vector10 bogus flag rc=2 (got %d)" % r, fails)
        r, _o, _e = cli("--json", os.path.join(tmp, "x.json"))
        _expect(r == 2, "vector10 missing --draft-out rc=2 (got %d)" % r,
                fails)
        r, _o, _e = cli("--draft-out", os.path.join(tmp, "d.md"))
        _expect(r == 2, "vector10 no signal source rc=2 (got %d)" % r, fails)
        r, _o, _e = cli("--draft-out", os.path.join(tmp, "d.md"),
                        "--baseline",
                        os.path.join(tmp, "no-such-baseline.json"))
        _expect(r == 9, "vector10 missing baseline rc=9 (got %d)" % r, fails)
        r, _o, _e = cli("--draft-out", os.path.join(tmp, "d.md"),
                        "--suite-now", "--suite-ledger", green)
        _expect(r == 2, "vector10 two suite sources rc=2 (got %d)" % r, fails)
        r, _o, _e = cli("--draft-out", os.path.join(tmp, "d.md"),
                        "--watch-repo", "org/repo")
        _expect(r == 2, "vector10 watch-repo without state rc=2 (got %d)" % r,
                fails)
        r, _o, _e = cli("--draft-out",
                        os.path.join(tmp, "no-such-dir", "d.md"),
                        "--suite-ledger", green)
        _expect(r == 9, "vector10 missing output parent rc=9 (got %d)" % r,
                fails)
        r, _o, _e = cli("--draft-out", os.path.join(tmp, "d.md"), "--top",
                        "0", "--suite-ledger", green)
        _expect(r == 2, "vector10 top 0 rc=2 (got %d)" % r, fails)
        print("PASS [10] CLI usage contract (2/9 faces)")

        if fails:
            print("== evolve selftest: %d FAIL ==" % len(fails))
            for f in fails:
                print("FAIL:", f)
            return 2
        print("EVOLVE-SELFTEST PASS: ten vector groups green")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
