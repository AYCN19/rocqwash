#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cw_sentinel.py: real-time dynamic sentinel for rocqwash (tools/): a live
companion for workflows that performs cleaning, shape washing, troubleshooting,
and blockage clearing: the sentinel is an inspection event stream over three
signal sources; classification and chain-root selection are always delegated
to the existing engines (zero new engines, zero reimplementation).

Three signal sources (combinable; at least one required):
  ① CI path = --watch-repo ORG/REPO [--branch B]... (repeatable, multiple
     groups):
       GET /repos/{repo}/actions/runs?per_page=30 (RUNS_QUERY, same convention
       as pushci.py; the token comes from the ~/.netrc machine github.com
       line's 6th-column password; netrc_token is a same-convention copy of
       ci_triage.py's; tools/ has no package layout, so following the pushci
       precedent each tool carries its own copy; --netrc parameterized) →
       each new completed run (seen run ids recorded in --state-file,
       idempotent) → the sentinel fetches the jobs (GET
       .../runs/{id}/jobs?per_page=100&page=1, written to a tmp file) →
       subprocess ci_triage --offline (the same "real subprocess, real
       classification, zero network" pattern as pushci's run_triage injector
       mode) → run-level family/action taken from the rocqwash-ci-triage/1
       report → family≠none emits the event
       {kind:ci-red, repo, run, family, action}. The full classification
       authority (five families plus the all-passing state) lives in
       ci_triage (classification order: the ci_triage.py module docstring);
       the sentinel does not classify.
  ② Local ledger path = --watch-ledgers DIR:
       new probe/ledger JSON files on disk (seen by mtime+name; a changed
       mtime/size on the same file also counts as new) → subprocess
       chain_graph.py on the new file --json tmp → the first name in
       top_order is the TOP chain root → event {kind:blocking, top_root,
       dependents} (with n and the three-way self-washability; per chain_graph
       build_graph).
  ③ Local build path = --watch-buildlog FILE:
       tail incremental grep (byte offset recorded in state; only complete
       lines are matched, to avoid half-line false positives) → tokens
       BUILD-FAIL / EXIT=134 (family-C toolchain-break token, ci_triage.py) /
       Error: (family-A content-failure token, ci_triage.py) → event
       {kind:build-signal, hits[]}. A missing log file = compilation has not
       started writing; zero events, not a failure (the report notes
       present=false explicitly, never silently).

Event stream: --emit FILE (JSONL append, per-line flush+fsync) + stdout mirror
(explicit). Event-line schema = rocqwash-sentinel-event/1; keys sort_keys;
line order = production order; seq is monotonic within the event stream (with
--emit, the baseline for cross-process continuation is the file itself plus
its rotated generations; by default it is monotonic within the process); a
consumer sorting by seq recovers the global order. ts comes from the time
clock; with --sleep-scale 0, ts is disabled (--selftest determinism
dependency) and events carry the note "ts=off".
JSONL rotation (--emit-max-bytes N; bounds the on-disk footprint for
long-lived runs): checked before each append; if the file's current bytes
plus the new line's bytes exceed N → rotate first, then append:
FILE.1→FILE.2 (an existing FILE.2 is overwritten and discarded; two
generations are kept) →FILE→FILE.1→new FILE empty. A single line longer than
N = the line cannot be split; it is written into the gap anyway (after
rotation a single line may still exceed the cap; the next append pre-check
rotates again); rotation is noted explicitly on stdout and counted in the
report's emit_rotations; a rename failure → 9. seq continues across
generations (baseline = the file plus the line counts of .1/.2; rotated
generations belong to the same event stream; sorting by seq recovers the
global order across generations).

--on-red 'CMD template': the {family}/{run}/{repo} placeholders are
substituted from event fields (missing fields become the empty string) →
executed via a subprocess shell (60s timeout cap; rc≠0/timeout is recorded
explicitly in the actions log and stdout, and does not change the sentinel's
exit code; on-red is a side action, outside the tool's own verdict surface).
Requires --emit (side actions must accompany an on-disk event stream;
trigger evidence and the action log stay auditable; without --emit → 2; the
same guard as --on-red-preset). Default: none = report-only; **zero action is
the default** (same discipline as cure_applier's dry-run default).

--on-red-preset NAME: preset actions for failing events (**repeatable =
chained**; see below); presets are template sugar: expanded into internal
command templates, they run through the same executor as --on-red (60s cap;
rc≠0/timeout recorded explicitly in the actions log; the sentinel's exit
code unchanged; placeholder substitution reuses the existing --on-red path;
zero new execution paths). Mutually exclusive with --on-red (both given →
rc=2 fail-loud, no silent choice; "preset wins" means a preset occupies the
on-red action slot; giving both is an ambiguous-usage error). Five presets
(ON_RED_PRESETS table; program paths located relative to the sentinel itself,
following the TOOLS_DIR precedent):
  unclog = python3 -B tools/unclog.py --src {src} --json {emit_dir}/unclog_{run}.json
    (**--apply not included by default = unclog only dry-runs; a human
    reviews, then applies; the default-dry-run rule for automatic hookups**)
  pushci = python3 -B tools/pushci.py --repo-path {repo_path} --branch {branch}
    --json {emit_dir}/pushci_{run}.json --dry-run (--dry-run default = print
    the plan only, zero side effects)
  wash-shape = python3 -B tools/wash_shape.py --dir {src} --json
    {emit_dir}/wash_shape_{run}.json (**--apply not in the template = shape
    washing only produces a plan; the plan writes nothing to disk; a human
    reviews, then applies; the same default-dry-run rule**)
  triage = python3 -B tools/ci_triage.py --repo {repo} --run {run} --json
    {emit_dir}/triage_{run}.json (failing events carry repo/run, substituted
    directly into the template = re-diagnose and re-classify the same red
    run)
  cw-doctor = python3 -B tools/cw_doctor.py --json {emit_dir}/doctor_{run}.json
    (no arguments = full default checkup)
Required-argument table (PRESET_REQUIRED_ARGS, declarative):
  {unclog:[src] · pushci:[repo_path,branch] · wash-shape:[src] ·
  triage:[repo,run] · cw-doctor:[]}. Two placeholder families: the static
  {src}/{repo_path}/{branch} are substituted at expansion time from
  --on-red-arg K=V; the dynamic {family}/{run}/{repo} (= fire_on_red direct
  event-field substitution over existing keys) are left for event
  substitution (missing fields become the empty string, existing semantics).
  The required-argument guard checks key by key (same fail-loud): if
  --on-red-arg is given, the static value substitutes; if not given and the
  key belongs to the dynamic family, event substitution applies (triage's
  repo/run are exactly this: the failing event supplies the values; there is
  nothing to look up at expansion time); anything else → missing, rc=2; no
  '=' / empty K·V / duplicate keys / unknown keys (a key not in the parameter
  surface; for a chain, the parameter surface is the union over the whole
  chain) / an orphan --on-red-arg → 2; {emit_dir} resolves to the directory
  of --emit (preset outputs share the disk with the event stream; --emit is
  required, otherwise 2). A missing preset component → 9.
Chaining: --on-red-preset is repeatable (e.g. --on-red-preset unclog
  --on-red-preset triage) = chained, same trigger, expanded in the given
  order; on a failing event each entry **executes in order, continue after one
  fails** (an rc≠0/timeout on one entry is recorded explicitly but does not
  halt later entries; side actions are not the tool's verdict surface; the
  sentinel's exit code is unchanged); the actions log records one entry per
  template (N chained entries = N records; same schema as a single entry);
  --on-red-arg namespaces are shared across the chain (unknown-key checking
  uses the union parameter surface; missing-required checks run per preset).
  report on_red_preset = a single preset name string, or the chained name
  list (in the given order).

Dual mode: --once (a single inspection round, then report and exit;
workflow-step use) | --loop --interval S (long-lived; JSONL append; for
workflow background bash tasks), --max-rounds N round cap (0 = unlimited;
--selftest vector ⑤ depends on a three-round sequence).

Resilience layer: a real-urllib CI GET that meets 403/429/5xx retries with
exponential backoff (--retry-max default 3, base 2s; a parseable Retry-After
second count replaces the current delay; HTTP-date shapes are not guessed and
fall back to exponential; exhausted → original error 9; 4xx semantic codes
401/404 etc. are not retried; delay computation lives in the
tools/_http_backoff.py pure functions shared by three tools, imported by
same-directory sys.path injection, no __init__ package layout; injector
canned paths never touch the real network and never retry; the
offline-testability rule).
Subprocess anti-hang = --subproc-timeout S (default 120s): ci_triage /
chain_graph run_py calls kill the subprocess on timeout + fail-loud 9 naming
the call (--timeout separately covers single HTTP requests, default 30; two
different clocks, not merged); on-red side actions (including
--on-red-preset expansions, same executor) remain under the ON_RED_TIMEOUT
60s cap and do not change the sentinel's exit code (the previously agreed
convention is unchanged).

Resilience layer, transport guard (protects long-lived sentinel runs against
transport-layer crashes): ① transient transport classes
(TRANSIENT_TRANSPORT_ERRORS = IncompleteRead / RemoteDisconnected /
BadStatusLine / the full ConnectionError family / socket.timeout, distinct
from the HTTPError status-code class) → bounded retry (--net-retries default
3 attempts, backoff 5s/15s/45s = the net_backoff_delays pure function,
inheriting the bounded-backoff semantics = a bounded table indexed by
attempt; each attempt builds a fresh Request+urlopen and discards the
half-read body); retries are exhausted before raising 9 (fail-loud
preserved; after raising, ② provides the fallback); non-transient errors
(HTTPError status-code semantics / URLError connection-establishment / other
unknown exceptions) are never retried and propagate as-is; swallowing
non-transient errors is forbidden.
② loop-level fallback (skip a round rather than crash a long-lived run):
each poll_round signal source is wrapped by poll_source_guarded exception
handling (loop mode only) → that source skips this round + the event stream
records {kind:source-error} (explicit, not silent); the next round retries;
the exception path leaves the seen idempotence ledger unwritten, so the next
round naturally re-reports (the prefer-duplicates-over-lost-events
convention); once mode has no fallback and propagates through run_sentry
fail-loud rc 9 (the workflow-step semantics are preserved).

Exit codes: 0 = inspection completed (a failing result is data, not a tool
  failure;
  explicit stdout); 2 = usage error (missing mode / both modes given / all
  three sources missing / --branch before --watch-repo / malformed repo /
  negative arguments / once with loop-only arguments / --on-red-preset with
  --on-red / unrecognized preset / preset arguments missing, duplicated, or
  malformed [for a chain, unknown keys are judged on the chain-wide union
  surface] / --emit missing / --on-red without --emit (both the plain and
  preset paths guard this) / an orphan --on-red-arg / --emit-max-bytes must
  be given with --emit or N<1 / --rebuild-state without --state-file);
  9 = signal source unreachable (CI HTTP 4xx/5xx · transport-layer transient
  retry exhaustion [--net-retries] · netrc missing · empty token · runs/jobs
  shape errors · missing preset component · injector missing / malformed /
  canned coverage incomplete · ledgers directory missing · state shape
  errors · ci_triage/chain_graph subprocess rc≠0 · subprocess killed on
  timeout [--subproc-timeout] · event-stream rotation rename failure).
  --selftest: 0 = all pass / 2 = assertion failure.

Report schema (--json; overwritten each round; rocqwash-sentinel/1):
  {"schema","mode","round","sources"{ci[],ledgers{},buildlog{}},"events"[],
   "actions"[] (on-red execution log),"state_file"?,"state_rebuilt"?,
   "interval"?,"sleep_scale","ts_enabled","injector"?,"on_red_preset"?
   (single-preset string · chained list),"emit_max_bytes"?,"emit_rotations"?}
  events/actions elements are byte-identical to the event stream
  (deterministic: with --sleep-scale 0, reruns on the same input are
  byte-identical).

Injector file (--injector; schema=rocqwash-sentinel-injector/1) = a canned
API response table, offline-testable (zero real network):
  {"schema":"rocqwash-sentinel-injector/1","responses":[
     {"url_contains":"/actions/runs?","status":200,"body":{...workflow_runs...}},
     {"url_contains":"/runs/178/jobs","status":200,"body":{...jobs...}}]}
  First match in order wins; entries may be reused cyclically (the sentinel's
  polling is idempotent, unlike pushci's steps shape, which is consumed in
  order); a miss fails loudly with 9; the canned table must fully cover the
  run; **never silently fall through to the real network**. The runs body
  uses the real GitHub API shape {"total_count":N,"workflow_runs":[...]}
  (the "runs" key is also accepted, following pushci's watch evidence shape).

State file (--state-file; schema=rocqwash-sentinel-state/1): the seen
idempotence persistence layer
  {"repos":{"ORG/REPO":{"seen_runs":{"<id>":{conclusion,run_number,family}}}},
   "ledgers":{"<name>":{"mtime_ns","size"}},"buildlogs":{"<path>":{"offset"}}}
  Default None = in-memory state (a single --once round has no cross-round
  idempotence; --loop requires it).
Crash-recovery semantics (no silent rebuild): a corrupted state (JSON parse
failure / malformed keys) → fail-loud 9, hard refusal; the tool neither
swallows nor rebuilds (seen is an idempotence ledger; a silent rebuild would
break the duplicate-event protection and re-report failing events; the original
file is left untouched); recovery has exactly two paths: delete the file
manually (the next round starts from zero state) or --rebuild-state explicit
rebuild (discard the existing seen and start from zero; an explicit
STATE-REBUILD note on stdout + report state_rebuilt=true; must be given with
--state-file, otherwise rc=2; with no state there is nothing to rebuild).

Orchestration rule: ci_triage / chain_graph are always invoked as direct
subprocesses (the same pattern as pushci's _run_py, pure logic with zero
compilation, so cpu_guard is not applied; only real compilation needs the
guard wrapper, per probe_engine.py); the sentinel itself does zero
compilation and zero network (except online mode without an injector, where
the CI path is real).

Honesty rules (per CONTRIBUTING §0): accept only mechanical evidence;
a failing result is data, not a tool failure (inspection exits 0); fail-loud, no
silent degradation (unreachable source 9 · injector without coverage 9 ·
subprocess rc≠0 9); zero third-party dependencies (pure stdlib); --json
written with sort_keys; with --sleep-scale 0, reruns on the same input are
byte-identical; zero hardcoded absolute paths
(--netrc/--state-file/--emit/--injector all parameterized; engine components
located relative to the sentinel itself, following the pushci TOOLS_DIR
precedent).
"""
import argparse
import datetime
import http.client
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PROG = "cw_sentinel"
SCHEMA = "rocqwash-sentinel/1"
EVENT_SCHEMA = "rocqwash-sentinel-event/1"
STATE_SCHEMA = "rocqwash-sentinel-state/1"
INJECTOR_SCHEMA = "rocqwash-sentinel-injector/1"
API_ROOT = "https://api.github.com"
RUNS_QUERY = "/actions/runs?per_page=30"          # same convention as pushci.py:141
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
TRIAGE_TOOL = os.path.join(TOOLS_DIR, "ci_triage.py")
CHAIN_TOOL = os.path.join(TOOLS_DIR, "chain_graph.py")
UNCLOG_TOOL = os.path.join(TOOLS_DIR, "unclog.py")
PUSHCI_TOOL = os.path.join(TOOLS_DIR, "pushci.py")
WASH_SHAPE_TOOL = os.path.join(TOOLS_DIR, "wash_shape.py")
CW_DOCTOR_TOOL = os.path.join(TOOLS_DIR, "cw_doctor.py")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)   # same-directory shared backoff helper (no __init__ package layout)
import _http_backoff

# --on-red-preset preset table (designated templates; program paths located
# relative to the sentinel itself, following the TOOLS_DIR precedent; zero
# hardcoded absolute paths): static placeholders {src}/{repo_path}/{branch}/
# {emit_dir} are substituted at expansion time; dynamic {run}/{repo}/{family}
# are left for fire_on_red event substitution. unclog without --apply = the
# unclog round is a dry run only; wash-shape without --apply = shape
# normalization only produces a plan (dry run by default for both);
# pushci with --dry-run = print the plan only, zero side effects; triage
# substitutes {repo}/{run} from the event = re-diagnose the same failing
# run; cw-doctor with no arguments = full default checkup.
ON_RED_PRESETS = {
    "unclog": "python3 -B %s --src {src} --json {emit_dir}/unclog_{run}.json"
              % UNCLOG_TOOL,
    "pushci": "python3 -B %s --repo-path {repo_path} --branch {branch} "
              "--json {emit_dir}/pushci_{run}.json --dry-run" % PUSHCI_TOOL,
    "wash-shape": "python3 -B %s --dir {src} --json "
                  "{emit_dir}/wash_shape_{run}.json" % WASH_SHAPE_TOOL,
    "triage": "python3 -B %s --repo {repo} --run {run} "
              "--json {emit_dir}/triage_{run}.json" % TRIAGE_TOOL,
    "cw-doctor": "python3 -B %s --json {emit_dir}/doctor_{run}.json"
                 % CW_DOCTOR_TOOL,
}
ON_RED_PRESET_TOOLS = {"unclog": UNCLOG_TOOL, "pushci": PUSHCI_TOOL,
                       "wash-shape": WASH_SHAPE_TOOL, "triage": TRIAGE_TOOL,
                       "cw-doctor": CW_DOCTOR_TOOL}
# per-preset required-argument table (declarative; the static-family
# substitution surface for --on-red-arg K=V): missing (non-dynamic family) /
# duplicate / no '=' / unknown key → 2. triage's repo/run belong to the
# dynamic event-substitution family (existing fire_on_red keys, carried by
# the failing event; pushci's static key is named repo_path precisely to
# avoid the {repo} dynamic name); with no --on-red-arg given, event
# substitution applies, which is not "missing".
PRESET_REQUIRED_ARGS = {"unclog": ("src",),
                        "pushci": ("repo_path", "branch"),
                        "wash-shape": ("src",),
                        "triage": ("repo", "run"),
                        "cw-doctor": ()}
# dynamic placeholder family (fire_on_red event-substitution keys; missing
# fields substitute the empty string, existing semantics); the
# required-argument guard exempts this family (the event supplies the
# value; there is nothing to look up at expansion time).
PRESET_DYNAMIC_KEYS = ("family", "run", "repo")

# buildlog tokens (classification-spectrum tokens, ci_triage.py:95-108 same
# source): BUILD-FAIL / EXIT=134 (family-C toolchain breakage) /
# Error: (family-A content failure)
BUILDLOG_SIGNAL_RE = re.compile(r"BUILD-FAIL|EXIT=134|\bError:")

EVENT_EVIDENCE_CAP = 8      # evidence item cap per ci-red event (loud truncation note)
EVENT_LINE_CAP = 200        # per-line evidence/hit character cap inside an event
BUILDLOG_HIT_CAP = 50       # per-round build-signal hit cap (truncated note beyond it)
ON_RED_TIMEOUT = 60         # on-red subprocess timeout seconds (side-action anti-hang)

# transient transport classes (real crash precedent: an IncompleteRead of
# the shape http.client.IncompleteRead(371261 read, 72721 expected) raised
# from resp.read() during a long-lived run): mid-body stream truncation
# (IncompleteRead); server disconnect (RemoteDisconnected, covering the
# ConnectionResetError and BadStatusLine family faces); bad status line
# (BadStatusLine); connection dropped (ConnectionError full family incl.
# Reset/Refused/Aborted/BrokenPipe); read timeout (socket.timeout). All are
# transient and retryable. Distinct from the HTTPError status-code class
# (401/404 semantic faces judged under --retry-max) and the URLError
# connection-establishment face (DNS/connect failure = fast 9). Swallowing
# non-transient errors is forbidden: exceptions outside this tuple are
# never retried and propagate as-is (fail-loud).
TRANSIENT_TRANSPORT_ERRORS = (
    http.client.IncompleteRead,
    http.client.RemoteDisconnected,
    http.client.BadStatusLine,
    ConnectionError,
    socket.timeout,
)
NET_RETRY_BASE = 5.0        # transport-layer backoff base seconds (5s/15s/45s table)
NET_RETRY_RATIO = 3.0       # backoff ratio (5→15→45 = x3; default 3 attempts)


class SentryError(Exception):
    """Fail-loud exception carrying an exit code (code: 2 = usage error,
        9 = signal source unreachable / malformed shape)."""

    def __init__(self, msg, code=9):
        super(SentryError, self).__init__(msg)
        self.code = code


# ---- helpers ----------------------------------------------------------------

def sleep_scaled(sec, scale):
    """time.sleep(sec*scale); scale=0 means zero real sleep (same form as
    pushci.py:184 sleep_scaled; selftest vectors depend on it)."""
    time.sleep(max(0.0, float(sec) * float(scale)))


def net_backoff_delays(net_retries):
    """Transport-layer transient-disconnect backoff seconds table
    (5s/15s/45s = base 5, ratio 3; pure function, zero clock, zero random,
    identical reruns for identical arguments; inherits the bounded-backoff
    semantics = a bounded table indexed by attempt; exhausted retries raise
    fail-loud). Examples: net_retries=3 → [5.0, 15.0, 45.0]; 0 → [] (zero
    retries, decided by the single attempt); negative / non-int →
    ValueError (fail-loud)."""
    if not isinstance(net_retries, int) or isinstance(net_retries, bool) \
            or net_retries < 0:
        raise ValueError("net_retries must be a non-negative int, got %r"
                         % (net_retries,))
    return [NET_RETRY_BASE * (NET_RETRY_RATIO ** i) for i in range(net_retries)]


def _safe_exc(e):
    """Exception-safe message text "ClassName: str(e)": if str() itself
    raises (e.g. an IncompleteRead whose partial is not bytes, so its
    __str__ calls len() and raises again) → the class name only. Used by the
    exhausted-retry raise path and the loop fallback note path: the message
    layer must never raise again and shadow the original error."""
    try:
        return "%s: %s" % (type(e).__name__, e)
    except Exception:
        return type(e).__name__


def now_iso():
    """UTC ISO8601, second precision, Z form (ts field; unused for whole
    events when --sleep-scale 0)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def clip(s, cap=EVENT_LINE_CAP):
    """Single-line evidence truncation (<= cap characters; overlong lines
    end with "...")."""
    s = str(s)
    return s if len(s) <= cap else s[:cap - 3] + "..."


def netrc_token(path, machine="github.com"):
    """Manual netrc parsing: machine <m> login <l> password <p> → password
    token. Same-convention copy of ci_triage.py:226 (handles both the
    single-line 6-column form and the multi-line form); missing file / no
    entry / empty value → fail-loud 9 (the token is never echoed)."""
    if not os.path.isfile(path):
        raise SentryError("netrc missing: %s (the online CI path needs a "
                          "machine %s ... password-form credential)"
                          % (path, machine), 9)
    toks = []
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.lstrip().startswith("#"):
                continue
            toks.extend(line.split())
    cur = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "machine" and i + 1 < len(toks):
            cur = toks[i + 1]
            i += 2
            continue
        if t == "password" and i + 1 < len(toks):
            if cur == machine:
                tok = toks[i + 1]
                if len(tok) >= 2 and tok.startswith('"') and tok.endswith('"'):
                    tok = tok[1:-1]
                if not tok:
                    raise SentryError("netrc machine %s password is empty"
                                      % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise SentryError("netrc has no machine %s password-form entry (the "
                      "single-line 6-column form: 6th column = token): %s"
                      % (machine, path), 9)


def run_py(tool_path, cli, timeout=None):
    """python3 -B <tool> <cli> subprocess (stdout+stderr merged; same form
    as pushci.py:591). Pure-logic engines do zero compilation and therefore
    skip cpu_guard (probe_engine.py:10 precedent: only real compilation
    needs the guard); missing component → 9. Resilience layer: when timeout
    is given, anti-hang applies (--subproc-timeout, default 120s); on
    timeout the subprocess is killed plus fail-loud 9 naming the call (zero
    hanging)."""
    if not os.path.isfile(tool_path):
        raise SentryError("toolchain component missing: %s" % tool_path, 9)
    try:
        p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SentryError("subprocess killed on timeout (--subproc-timeout="
                          "%ss; call: python3 -B %s %s)"
                          % (timeout, os.path.basename(tool_path),
                             " ".join(str(c) for c in cli[:1])), 9)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


# ---- injector layer (offline-testability rule: with --injector present,
#      no real request is ever issued) ------------------------------------------

def load_injector(path):
    """injector file → {"responses":[...]}. Missing file / malformed shape /
    empty table → 9."""
    if not os.path.isfile(path):
        raise SentryError("injector missing: %s" % path, 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise SentryError("injector malformed (parse failure): %s (%s)"
                          % (path, e), 9)
    if not isinstance(data, dict) or not isinstance(data.get("responses"), list) \
            or not data["responses"]:
        raise SentryError("injector malformed (must be {\"schema\":...,"
                          "\"responses\":[{url_contains,status,body}...]} "
                          "non-empty table): %s" % path, 9)
    for i, r in enumerate(data["responses"]):
        if not isinstance(r, dict) or not isinstance(r.get("url_contains"), str):
            raise SentryError("injector malformed (responses[%d] missing "
                              "url_contains string): %s" % (i, path), 9)
    return data


def api_get_json(url, token, timeout, injector, retry_max=3, sleep_scale=1.0,
                 net_retries=3, _open=None, _sleep=None):
    """Read-only GET → (status, parsed_json). The single network action and
    the single injection point: with an injector present, the first
    url_contains match wins (entries reusable cyclically; the sentinel's
    polling is idempotent); a miss fails loudly with 9 and never silently
    falls through to the real network; the canned path never retries (the
    offline-testability rule). Without an injector, real urllib (resilience
    layer: 403/429/5xx exponential-backoff retries, base 2s, capped by
    retry_max; a parseable Retry-After second count replaces the current
    delay; _http_backoff pure functions; exhausted retries or 4xx semantic
    codes → 9; connection failure → 9; non-JSON body → 9). Transport-layer
    transient classes (TRANSIENT_TRANSPORT_ERRORS) retry within bounds:
    capped by net_retries (default 3 attempts), backoff net_backoff_delays
    (5s/15s/45s), each attempt builds a fresh Request+urlopen and discards
    the half-read body; retries are exhausted before raising 9 (fail-loud
    preserved; after the raise, poll_source_guarded provides the loop-level
    fallback: that source skips the round rather than crashing the run).
    Non-transient classes (URLError / other unknown exceptions) are never
    retried and propagate as-is; swallowing is forbidden. _open/_sleep are
    injection points (selftest zero-network vectors; a canned resp.read()
    that raises a transport exception is the read-function injection
    face)."""
    if injector is not None:
        for r in injector["responses"]:
            if r["url_contains"] in url:
                status = int(r.get("status", 200))
                body = r.get("body")
                if status != 200:
                    raise SentryError("CI API HTTP %d (injector canned): %s"
                                      % (status, url), 9)
                return 200, body
        raise SentryError("injector canned table does not cover GET %s "
                          "(the canned table must fully cover the run; "
                          "never silently fall through to the real network)"
                          % url, 9)
    do_open = urllib.request.urlopen if _open is None else _open
    do_sleep = (lambda s: sleep_scaled(s, sleep_scale)) if _sleep is None \
        else _sleep
    delays = _http_backoff.backoff_delays(retry_max)
    net_delays = net_backoff_delays(net_retries)
    attempt = 0
    net_attempt = 0
    while True:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rocqwash-cw-sentinel",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "token %s" % token,
        })
        try:
            with do_open(req, timeout=timeout) as resp:
                raw = resp.read()
            break
        except urllib.error.HTTPError as e:
            if attempt >= retry_max or not _http_backoff.is_retry_status(e.code):
                try:
                    body = (e.read() or b"").decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                raise SentryError("CI API HTTP %d: %s (%s)"
                                  % (e.code, body.strip()[:160], url), 9)
            ra = _http_backoff.parse_retry_after(
                e.headers.get("Retry-After") if e.headers is not None else None)
            do_sleep(ra if ra is not None else delays[attempt])
            attempt += 1
        except TRANSIENT_TRANSPORT_ERRORS as e:
            # transient transport faces retry within bounds (each attempt
            # builds a fresh connection; the half-read body is discarded);
            # retries are exhausted before raising 9, fail-loud preserved;
            # the loop layer catches, that source skips this round and
            # retries next round (skip a round rather than crash the run);
            # no swallowing = the counter is bounded and exhaustion is
            # always reported.
            if net_attempt >= net_retries:
                raise SentryError(
                    "CI API transport-layer transient-disconnect retries "
                    "exhausted (%d attempts; backoff %s): %s (%s)"
                    % (net_retries, net_delays, url, _safe_exc(e)), 9)
            do_sleep(net_delays[net_attempt])
            net_attempt += 1
        except (urllib.error.URLError, OSError) as e:
            raise SentryError("CI API unreachable: %s (%s)" % (url, e), 9)
    try:
        return 200, json.loads(raw.decode("utf-8"))
    except ValueError as e:
        raise SentryError("CI API body is not JSON: %s (%s)" % (url, e), 9)


# ---- state (seen idempotence persistence layer) ------------------------------

def new_state():
    return {"schema": STATE_SCHEMA, "repos": {}, "ledgers": {}, "buildlogs": {}}


def load_state(path, rebuild=False):
    """state loading (crash-recovery semantics): default / missing file =
    start from zero state; corrupted (JSON parse failure / malformed keys)
    → fail-loud 9, hard refusal, no silent rebuild (seen is an idempotence
    ledger; a silent rebuild would break duplicate-event protection and
    re-report failing events; the corrupted original file is left
    untouched); rebuild=True (--rebuild-state explicit rebuild) = the only
    legitimate rebuild path: discard existing content and start from zero
    (the loud note is printed by run_sentry)."""
    if path is None or rebuild:
        return new_state()
    if not os.path.isfile(path):
        return new_state()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise SentryError("state file malformed (parse failure; no silent "
                          "rebuild): %s (%s)" % (path, e), 9)
    for k in ("repos", "ledgers", "buildlogs"):
        if not isinstance(st.get(k), dict):
            raise SentryError("state file malformed (missing %s dict; no "
                              "silent rebuild): %s" % (k, path), 9)
    return st


def save_state(path, st):
    if path is None:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise SentryError("state file directory missing: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- event stream (JSONL append+fsync + stdout mirror) ------------------------

def make_event(sentry, kind, fields):
    """Event assembly: seq is monotonic within the event stream
    (sentry["seq"]; with emit present, numbering continues across processes
    from the file's existing line count); ts is disabled by --sleep-scale 0
    (noted; determinism). When fields carries its own note, the ts=off note
    is merged into its head (no clash)."""
    ev = {"schema": EVENT_SCHEMA, "seq": sentry["seq"], "kind": kind}
    sentry["seq"] += 1
    ev.update(fields)
    if sentry["ts_enabled"]:
        ev["ts"] = now_iso()
    else:
        off = "ts=off (--sleep-scale 0; deterministic output)"
        base = ev.pop("note", None)
        ev["note"] = (off + "|" + base) if base else off
    return ev


def rotate_emit(path):
    """JSONL rotation by one generation (--emit-max-bytes cap triggers; two
    generations kept): FILE.1→FILE.2 (an existing FILE.2 is overwritten and
    discarded) →FILE→FILE.1→new FILE empty. rename failure → 9."""
    gen1, gen2 = path + ".1", path + ".2"
    try:
        if os.path.exists(gen1):
            os.replace(gen1, gen2)
        if os.path.exists(path):
            os.replace(path, gen1)
    except OSError as e:
        raise SentryError("event stream rotation failed (%s → %s/%s): %s"
                          % (path, gen1, gen2, e), 9)


def emit_seq_base(emit_path):
    """Cross-process seq continuation baseline (with --emit present): the
    sum of existing non-empty lines over the file itself plus its rotated
    generations (.1/.2); rotated generations belong to the same event
    stream and numbering continues across generations without collision
    (a consumer sorting by seq recovers the global order). Read failure
    → 9."""
    base = 0
    for p in (emit_path, emit_path + ".1", emit_path + ".2"):
        if os.path.isfile(p):
            try:
                with io.open(p, "r", encoding="utf-8") as fh:
                    base += sum(1 for ln in fh if ln.strip())
            except OSError as e:
                raise SentryError("event stream baseline read failed: %s (%s)"
                                  % (p, e), 9)
    return base


def emit_event(sentry, ev):
    """--emit JSONL append (flush+fsync) + loud stdout mirror. With
    --emit-max-bytes present, the cap is checked before each append (file's
    current bytes + new line's bytes > cap) → rotate first, then append
    (.1/.2 keep two generations; loud stdout note; counted in the report's
    rotations); a single line over the cap = the line cannot be split and
    is written into the gap anyway. emit write failure / rotation
    failure → 9."""
    line = json.dumps(ev, ensure_ascii=False, sort_keys=True)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    path = sentry["emit"]
    if path:
        cap = sentry["emit_max_bytes"]
        if cap:
            nbytes = len(line.encode("utf-8")) + 1
            try:
                size = os.path.getsize(path) if os.path.isfile(path) else 0
            except OSError as e:
                raise SentryError("event stream size probe failed: %s (%s)"
                                  % (path, e), 9)
            if size > 0 and size + nbytes > cap:
                rotate_emit(path)
                sentry["rotations"] += 1
                sys.stdout.write("emit rotation: %s → %s.1 (old .1→.2 "
                                 "discarded; two generations kept)\n"
                                 % (path, path))
        try:
            with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as e:
            raise SentryError("event stream append failed: %s (%s)"
                              % (path, e), 9)
    sentry["events"].append(ev)


# ---- CI path (1: runs polling → new completed runs → ci_triage subprocess
#      classification) ----------------------------------------------------------

def runs_url(repo):
    return API_ROOT + "/repos/%s%s" % (repo, RUNS_QUERY)


def jobs_api_path(repo, run_id):
    return "/repos/%s/actions/runs/%s/jobs?per_page=100&page=1" % (repo, run_id)


def triage_run_offline(repo, run_id, jobs_body, timeout=None):
    """The sentinel fetches jobs (api_get_json, injector injectable) →
    writes a tmp file → subprocess ci_triage --offline (same pattern as
    pushci.py:969 run_triage injector mode; real subprocess, real
    classification, zero network) → rocqwash-ci-triage/1 report.
    ci_triage rc != 0 → 9; when timeout is given, --subproc-timeout
    anti-hang applies (timeout = kill plus 9 naming the call)."""
    fdj, jobs_path = tempfile.mkstemp(prefix="cw_sentinel_jobs_")
    os.close(fdj)
    fd, out_path = tempfile.mkstemp(prefix="cw_sentinel_triage_")
    os.close(fd)
    try:
        with io.open(jobs_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(jobs_body, fh, sort_keys=True)
        rc, out = run_py(TRIAGE_TOOL, ["--offline", jobs_path, "--json", out_path],
                         timeout=timeout)
        if rc != 0:
            raise SentryError("ci_triage subprocess rc=%d: %s"
                              % (rc, out[-300:]), 9)
        try:
            with io.open(out_path, "r", encoding="utf-8") as fh:
                rep = json.load(fh)
        except (ValueError, UnicodeDecodeError) as e:
            raise SentryError("ci_triage report malformed: %s (%s)"
                              % (out_path, e), 9)
        if rep.get("schema") != "rocqwash-ci-triage/1":
            raise SentryError("ci_triage report schema unrecognized: %r"
                              % rep.get("schema"), 9)
        return rep
    finally:
        for p in (jobs_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def poll_ci_repo(sentry, spec, st):
    """One repo, one round: GET runs → classify each new completed run →
    ci-red events. Passing runs are also recorded in seen (idempotent; a
    second round yields zero events and zero re-classification). Branch
    filter = head_branch in spec.branches (no branches = all accepted).
    In-flight runs are neither recorded nor classified (wait for
    completed)."""
    repo = spec["repo"]
    token = sentry["token"]            # None when an injector is present; lazily fetched
    _, body = api_get_json(runs_url(repo), token, sentry["timeout"],
                           sentry["injector"], retry_max=sentry["retry_max"],
                           net_retries=sentry["net_retries"],
                           sleep_scale=sentry["args"].sleep_scale)
    runs = None
    if isinstance(body, dict):
        runs = body.get("workflow_runs")     # real GitHub API shape
        if runs is None:
            runs = body.get("runs")          # pushci watch evidence shape (py:880)
    if not isinstance(runs, list):
        raise SentryError("runs API malformed (no workflow_runs/runs list): "
                          "%s" % runs_url(repo), 9)
    seen = st["repos"].setdefault(repo, {}).setdefault("seen_runs", {})
    matched = [r for r in runs if isinstance(r, dict)
               and (not spec["branches"]
                    or str(r.get("head_branch") or "") in spec["branches"])]
    matched.sort(key=lambda r: ((r.get("run_number") or 0),
                                (r.get("id") or 0)))   # ascending = older runs reported first; deterministic
    new_runs = red_runs = 0
    for r in matched:
        if r.get("status") != "completed":
            continue                      # in-flight/queued: not recorded in seen; wait for completion
        rid = r.get("id")
        if rid is None or str(rid) in seen:
            continue
        new_runs += 1
        family = action = None
        evidence = []
        conclusion = str(r.get("conclusion") or "")
        if conclusion == "success":
            note = "conclusion=success (passing; recorded in seen, no event)"
        else:
            _, jobs_body = api_get_json(
                API_ROOT + jobs_api_path(repo, rid), token, sentry["timeout"],
                sentry["injector"], retry_max=sentry["retry_max"],
                net_retries=sentry["net_retries"],
                sleep_scale=sentry["args"].sleep_scale)
            if not isinstance(jobs_body, dict) \
                    or not isinstance(jobs_body.get("jobs"), list):
                raise SentryError("jobs API malformed (must be "
                                  "{\"total_count\":N,\"jobs\":[...]}): "
                                  "run=%s" % rid, 9)
            rep = triage_run_offline(repo, rid, jobs_body,
                                     timeout=sentry["subproc_timeout"])
            runv = rep.get("run") or {}
            family = runv.get("family")
            action = runv.get("action")
            evidence = [clip(e) for e in (runv.get("evidence") or [])
                        ][:EVENT_EVIDENCE_CAP]
            note = "classification=rocqwash-ci-triage/1 (ci_triage subprocess --offline)"
        seen[str(rid)] = {"conclusion": conclusion,
                          "run_number": r.get("run_number"),
                          "branch": r.get("head_branch"),
                          "family": family}
        if family is not None and family != "none":
            red_runs += 1
            emit_event(sentry, make_event(sentry, "ci-red", {
                "repo": repo, "run": rid,
                "run_number": r.get("run_number"),
                "branch": r.get("head_branch"),
                "sha": r.get("head_sha"),
                "conclusion": conclusion,
                "family": family, "action": action,
                "evidence": evidence, "note": note}))
    return {"repo": repo, "branches": spec["branches"] or ["*"],
            "runs_seen": len(runs), "new_runs": new_runs, "red_runs": red_runs}


# ---- local ledger path (2: new ledger → chain_graph subprocess → TOP chain
#      root) --------------------------------------------------------------------

def poll_ledgers(sentry, ledgers_dir, st):
    """New probe/ledger JSON (seen by mtime+name) → chain_graph on the
    single file produces TOP → blocking event (first top_order name, with
    n / dependents / the three-way self-washability). Empty TOP (no rc1
    missing-library chain root; an all-passing ledger) = zero failing
    events; the report still records new loudly. chain_graph rc != 0
    (half-written or malformed file etc.) → 9."""
    if not os.path.isdir(ledgers_dir):
        raise SentryError("ledgers directory missing: %s" % ledgers_dir, 9)
    seen = st["ledgers"]
    new_names = []
    out = {"dir": ledgers_dir, "new": [], "red_events": 0}
    for name in sorted(os.listdir(ledgers_dir)):
        path = os.path.join(ledgers_dir, name)
        if not name.endswith(".json") or not os.path.isfile(path):
            continue
        try:
            sr = os.stat(path)
        except OSError as e:
            raise SentryError("ledger unreadable: %s (%s)" % (path, e), 9)
        sig = {"mtime_ns": sr.st_mtime_ns, "size": sr.st_size}
        old = seen.get(name)
        if old == sig:
            continue
        new_names.append(name)
        out["new"].append(name)
        fd, gpath = tempfile.mkstemp(prefix="cw_sentinel_chain_")
        os.close(fd)
        try:
            rc, cout = run_py(CHAIN_TOOL, [path, "--json", gpath],
                              timeout=sentry["subproc_timeout"])
            if rc != 0:
                raise SentryError("chain_graph subprocess rc=%d (file %s): %s"
                                  % (rc, path, cout[-300:]), 9)
            try:
                with io.open(gpath, "r", encoding="utf-8") as fh:
                    g = json.load(fh)
            except (ValueError, UnicodeDecodeError) as e:
                raise SentryError("chain_graph output malformed (file %s): %s"
                                  % (path, e), 9)
        finally:
            try:
                os.unlink(gpath)
            except OSError:
                pass
        if g.get("schema") != "rocqwash-chain-graph/1" \
                or not isinstance(g.get("top_order"), list):
            raise SentryError("chain_graph output schema/top_order "
                              "unrecognized (file %s)" % path, 9)
        top_order = g["top_order"]
        if top_order:
            top_root = top_order[0]
            e = (g.get("libs") or {}).get(top_root) or {}
            emit_event(sentry, make_event(sentry, "blocking", {
                "ledger": name,
                "top_root": top_root,
                "dependents": e.get("dependents") or [],
                "n": e.get("n"),
                "self": e.get("self") or {},
                "note": "TOP chain root = first name in chain_graph "
                        "rocqwash-chain-graph/1 top_order (self field "
                        "judges chain-root washability; chain_graph.py:88 "
                        "precedent)"}))
            out["red_events"] += 1
        # empty TOP = no rc1 missing-library chain root (all-passing ledger)
        # → zero failing events; the report's new list already records it
        seen[name] = sig
    return out


# ---- local build path (3: buildlog tail incremental grep) ---------------------

def poll_buildlog(sentry, log_path, st):
    """Tail incremental grep (byte offset recorded in state; only complete
    lines are matched, to avoid half-line false positives) → token hits
    emit a build-signal event. A missing file = compilation has not started
    writing; zero events, not a failure (present=false noted loudly, never
    silently); offset recorded as 0, waiting for the file to appear."""
    seen = st["buildlogs"]
    rec = seen.get(log_path) or {}
    offset = int(rec.get("offset") or 0)
    out = {"path": log_path, "present": False, "offset_before": offset,
           "offset_after": offset, "hits": 0}
    if not os.path.isfile(log_path):
        out["note"] = ("log file not present (compilation has not started "
                       "writing; zero events, not a failure; waiting for it "
                       "to appear)")
        return out
    with io.open(log_path, "rb") as fh:
        if offset:
            fh.seek(offset)
        data = fh.read()
    size = offset + len(data)
    full = data
    if data and not data.endswith(b"\n"):
        cut = data.rfind(b"\n")
        full = data[:cut + 1]          # half line left for the next round (avoids half-line false positives)
    lines = full.decode("utf-8", errors="replace").splitlines()
    hits = [clip(ln) for ln in lines if BUILDLOG_SIGNAL_RE.search(ln)]
    truncated = len(hits) > BUILDLOG_HIT_CAP
    out.update({"present": True, "offset_after": offset + len(full),
                "hits": len(hits) if not truncated else BUILDLOG_HIT_CAP,
                "hits_total": len(hits), "truncated": truncated})
    if hits:
        emit_event(sentry, make_event(sentry, "build-signal", {
            "log": log_path,
            "hits": hits[:BUILDLOG_HIT_CAP],
            "hits_total": len(hits), "truncated": truncated,
            "offset_before": offset, "offset_after": offset + len(full),
            "note": "tokens BUILD-FAIL/EXIT=134/Error: (classification-"
                    "spectrum A/C tokens; ci_triage.py:95-118 same "
                    "source)"}))
    seen[log_path] = {"offset": offset + len(full)}
    return out


# ---- on-red (side actions; zero action is the default) ------------------------

def parse_on_red_args(arg_pairs, face, face_label):
    """--on-red-arg K=V parsing + shape guard (no '=' / empty K or V /
    duplicate key / unknown key → 2). face = the legal key surface (single
    preset = its required-argument table; chained = the union parameter
    surface over the whole chain; a key declared by any preset in the
    chain is legal; the single-preset union = its own face, same as the
    existing guard). → params dict (substitution in sort_keys order;
    deterministic)."""
    params = {}
    for pair in (arg_pairs or []):
        if "=" not in pair:
            raise SentryError("--on-red-arg must have the form K=V: %r"
                              % pair, 2)
        k, v = pair.split("=", 1)
        if not k or not v:
            raise SentryError("--on-red-arg K/V must both be non-empty: %r"
                              % pair, 2)
        if k in params:
            raise SentryError("--on-red-arg duplicate key: %r" % k, 2)
        if k not in face:
            raise SentryError("--on-red-arg key %r does not belong to %s "
                              "(parameter surface %s)"
                              % (k, face_label,
                                 "/".join(face) if face else "empty"), 2)
        params[k] = v
    return params


def check_preset_required(name, params):
    """Required-argument guard (key by key over PRESET_REQUIRED_ARGS[name],
    same fail-loud): if --on-red-arg supplied the key, the static value
    substitutes; if not given and the key belongs to the dynamic family
    (PRESET_DYNAMIC_KEYS = existing fire_on_red event-substitution keys),
    event substitution applies (triage's repo/run, carried by the failing
    event, left as-is at expansion time, not missing); otherwise → missing,
    rc=2."""
    missing = [k for k in PRESET_REQUIRED_ARGS[name]
               if k not in params and k not in PRESET_DYNAMIC_KEYS]
    if missing:
        raise SentryError("--on-red-preset %s missing required argument "
                          "(--on-red-arg %s=...; dynamic family %s is "
                          "event-substituted and exempt): %s"
                          % (name, missing[0],
                             "/".join(PRESET_DYNAMIC_KEYS),
                             "/".join(PRESET_REQUIRED_ARGS[name])), 2)


def expand_preset_cmd(name, params, emit_path):
    """Single-preset command expansion (required-argument guard → --emit
    guard → tool file present → placeholder substitution). Static keys
    substitute in sort_keys order; {emit_dir} resolves to the directory of
    --emit (preset outputs share the disk with the event stream); the
    dynamic family is left as-is for fire_on_red event substitution
    (placeholder substitution reuses the existing --on-red path; zero new
    execution paths). Missing --emit → 2; missing preset tool file → 9."""
    check_preset_required(name, params)
    if not emit_path:
        raise SentryError("--on-red-preset requires --emit ({emit_dir} "
                          "resolves to the event stream's directory; preset "
                          "outputs share the disk)", 2)
    if not os.path.isfile(ON_RED_PRESET_TOOLS[name]):
        raise SentryError("preset tool file missing: %s"
                          % ON_RED_PRESET_TOOLS[name], 9)
    cmd = ON_RED_PRESETS[name]
    for k in sorted(params):
        cmd = cmd.replace("{%s}" % k, params[k])
    cmd = cmd.replace("{emit_dir}",
                      os.path.dirname(os.path.abspath(emit_path)))
    return cmd


def expand_on_red_preset(name, arg_pairs, emit_path):
    """--on-red-preset single-preset expansion → on-red command template
    string (ON_RED_PRESETS table; a preset is template sugar). Unrecognized
    preset / missing, duplicated, or malformed arguments (no '=', empty
    K/V, unknown key) / missing --emit → 2; missing preset tool file → 9."""
    if name not in ON_RED_PRESETS:
        raise SentryError("--on-red-preset unrecognized: %r (options: %s)"
                          % (name, "/".join(sorted(ON_RED_PRESETS))), 2)
    params = parse_on_red_args(arg_pairs, PRESET_REQUIRED_ARGS[name],
                               "preset %s" % name)
    return expand_preset_cmd(name, params, emit_path)


def expand_on_red_presets(names, arg_pairs, emit_path):
    """--on-red-preset chained expansion (flag repeatable): any
    unrecognized name → 2; the --on-red-arg namespace is shared across the
    whole chain: unknown keys are judged on the chain-wide union parameter
    surface (a chained unclog+triage example needs only src; triage's
    repo/run go through event substitution); missing required arguments are
    judged per preset (dynamic family exempt); --emit/tool guards are the
    same as for a single preset. → command template list (in the given
    order, zero reordering; the execute-in-order contract; sort_keys
    determinism unaffected)."""
    for name in names:
        if name not in ON_RED_PRESETS:
            raise SentryError("--on-red-preset unrecognized: %r (options: %s)"
                              % (name, "/".join(sorted(ON_RED_PRESETS))), 2)
    face = sorted({k for name in names for k in PRESET_REQUIRED_ARGS[name]})
    params = parse_on_red_args(arg_pairs, face,
                               "preset chain %s" % "+".join(names))
    return [expand_preset_cmd(name, params, emit_path) for name in names]


def fire_on_red(sentry, ev):
    """Failing-event side-action execution (--on-red single template and
    the --on-red-preset chain expansion table share one entry point and one
    executor): per-template placeholder substitution ({family}/{run}/{repo}
    event-field substitution, missing fields become the empty string) →
    subprocess shell execution. Execute in order, continue after one
    fails: an rc != 0/timeout on one entry is recorded loudly (stdout note +
    actions entry) but does not halt later entries and does not change the
    sentinel's exit code (side actions are outside the verdict surface).
    Each template contributes one actions entry (N chained entries = N
    entries; same schema as a single entry). → the entries list for this
    event."""
    entries = []
    for tpl in sentry["on_red"]:
        cmd = str(tpl)
        for key in ("family", "run", "repo"):
            cmd = cmd.replace("{%s}" % key, str(ev.get(key) if ev.get(key)
                                                is not None else ""))
        entry = {"seq": ev.get("seq"), "kind": ev.get("kind"), "cmd": cmd}
        try:
            p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=ON_RED_TIMEOUT)
            out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
                else (p.stdout or "")
            entry["rc"] = p.returncode
            entry["output"] = clip(out, 400)
            if p.returncode != 0:
                sys.stdout.write("on-red note: cmd rc=%d (side action; does "
                                 "not change the sentinel's exit code)\n"
                                 % p.returncode)
        except subprocess.TimeoutExpired:
            entry["rc"] = None
            entry["output"] = "timeout (%ds cap)" % ON_RED_TIMEOUT
            sys.stdout.write("on-red note: cmd timeout (side action; does "
                             "not change the sentinel's exit code)\n")
        sentry["actions"].append(entry)
        entries.append(entry)
    return entries


# ---- single inspection round ---------------------------------------------------

def poll_source_guarded(sentry, label, fn, *args):
    """Loop long-lived fallback (sentinel semantics: skip a round rather
    than crash the run): an exception from one signal source's inspection
    (api transport retries exhausted SentryError 9 / subprocess hard error /
    any unclassified exception, the residual face after transport-layer
    retry handling) → the event stream records {kind:source-error} (loud,
    not silent) + that source skips this round and retries next round; the
    exception path leaves the seen idempotence ledger unwritten, so the
    next round naturally re-reports (prefer duplicates over lost events).
    once mode has no fallback and propagates (workflow-step fail-loud rc 9
    semantics preserved). KeyboardInterrupt/SystemExit are not Exception
    subclasses and are never swallowed (long-lived runs stay interruptible);
    source-error is not an on-red trigger (the failing-event family filter
    is unchanged)."""
    if sentry["mode"] != "loop":
        return fn(*args)
    try:
        return fn(*args)
    except Exception as e:
        err = clip(_safe_exc(e), 400)
        emit_event(sentry, make_event(sentry, "source-error", {
            "source": label, "error": err,
            "note": "loop-level fallback: this source skips the round and "
                    "retries next round (skip a round rather than crash "
                    "the run; loud note, not silent; seen not recorded, so "
                    "the next round re-reports; prefer duplicates over "
                    "lost events)"}))
        sys.stdout.write("source-error note: %s skips this round (%s)\n"
                         % (label, err))
        return {"source": label, "skipped": True, "error": err}


def poll_round(sentry, st, round_no):
    """One round over all three source paths → the round's report dict
    (--json overwritten each round; sort_keys). A source hard error
    (SentryError) propagates up and run_sentry halts: fail-loud, never run
    in a broken state (once-mode semantics preserved); in loop mode each
    source goes through poll_source_guarded: the failing source skips this
    round with a source-error event note and retries next round (skip a
    round rather than crash the run)."""
    a = sentry["args"]
    sys.stdout.write("=== CW-SENTINEL round=%d mode=%s (a failing result is "
                     "data, not a tool failure) ===\n"
                     % (round_no, sentry["mode"]))
    rep = {"schema": SCHEMA, "mode": sentry["mode"], "round": round_no,
           "sources": {}, "events": [], "actions": sentry["actions"],
           "sleep_scale": a.sleep_scale, "ts_enabled": sentry["ts_enabled"]}
    ci_out = []
    for spec in sentry["specs"]:
        ci_out.append(poll_source_guarded(sentry, "ci:" + spec["repo"],
                                          poll_ci_repo, sentry, spec, st))
    if ci_out:
        rep["sources"]["ci"] = ci_out
    if a.watch_ledgers:
        rep["sources"]["ledgers"] = poll_source_guarded(
            sentry, "ledgers", poll_ledgers, sentry, a.watch_ledgers, st)
    if a.watch_buildlog:
        rep["sources"]["buildlog"] = poll_source_guarded(
            sentry, "buildlog", poll_buildlog, sentry, a.watch_buildlog, st)
    for ev in sentry["events"]:
        if ev.get("kind") in ("ci-red", "blocking", "build-signal") \
                and sentry["on_red"]:
            fire_on_red(sentry, ev)
    rep["events"] = list(sentry["events"])
    rep["actions"] = list(sentry["actions"])
    if a.state_file:
        rep["state_file"] = a.state_file
    if a.rebuild_state:
        rep["state_rebuilt"] = True
    if a.emit_max_bytes:
        rep["emit_max_bytes"] = a.emit_max_bytes
        rep["emit_rotations"] = sentry["rotations"]
    if a.injector:
        rep["injector"] = a.injector
    if sentry["on_red_preset"]:
        rep["on_red_preset"] = sentry["on_red_preset"]
    if a.interval is not None and sentry["mode"] == "loop":
        rep["interval"] = a.interval
    if sentry["events"]:
        sys.stdout.write("this round: %d events (seq %s..%s)\n"
                         % (len(sentry["events"]),
                            sentry["events"][0]["seq"],
                            sentry["events"][-1]["seq"]))
    else:
        sys.stdout.write("zero events this round (a failing result is data, "
                         "not a tool failure; exit 0)\n")
    return rep


def write_json_report(path, rep):
    """--json report overwritten each round (sort_keys; rocqwash-sentinel/1)."""
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise SentryError("report directory missing: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- main flow -----------------------------------------------------------------

def parse_watch_specs(argv):
    """argv pre-scan of --watch-repo/--branch group membership (argparse
    sees tokens, not groups; group semantics = --watch-repo opens a new
    group, --branch joins the current group). --branch before any
    --watch-repo → usage error 2."""
    specs = []
    cur = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--watch-repo" or a.startswith("--watch-repo="):
            val = a.split("=", 1)[1] if "=" in a else (
                argv[i + 1] if i + 1 < len(argv) else None)
            if val is None:
                raise SentryError("--watch-repo missing value (form ORG/REPO)",
                                  2)
            if not REPO_RE.match(val):
                raise SentryError("--watch-repo must have the form ORG/REPO: "
                                  "%r" % val, 2)
            cur = {"repo": val, "branches": []}
            specs.append(cur)
            i += 2 if "=" not in a else 1
        elif a == "--branch" or a.startswith("--branch="):
            val = a.split("=", 1)[1] if "=" in a else (
                argv[i + 1] if i + 1 < len(argv) else None)
            if val is None:
                raise SentryError("--branch missing value", 2)
            if cur is None:
                raise SentryError("--branch must follow inside a "
                                  "--watch-repo group (--watch-repo first, "
                                  "then --branch)", 2)
            cur["branches"].append(val)
            i += 2 if "=" not in a else 1
        else:
            i += 1
    return specs


def build_sentry(args):
    """args → sentry runtime state (lazy token; ts switch; injector
    loading; usage validation rc 2)."""
    if args.sleep_scale < 0:
        raise SentryError("--sleep-scale must be >= 0, got %s"
                          % args.sleep_scale, 2)
    if args.interval is not None and args.interval < 0:
        raise SentryError("--interval must be >= 0, got %s" % args.interval, 2)
    if args.max_rounds < 0:
        raise SentryError("--max-rounds must be >= 0, got %s"
                          % args.max_rounds, 2)
    mode = "loop" if args.loop else ("once" if args.once else None)
    if mode is None:
        raise SentryError("one of --once or --loop is required", 2)
    if args.once and args.loop:
        raise SentryError("--once and --loop are mutually exclusive", 2)
    specs = parse_watch_specs(sys.argv[1:])
    if not specs and not args.watch_ledgers and not args.watch_buildlog:
        raise SentryError("at least one of the three signal sources is "
                          "required: --watch-repo / --watch-ledgers / "
                          "--watch-buildlog", 2)
    if args.injector and not specs:
        raise SentryError("--injector only serves the CI path (must be "
                          "given with --watch-repo)", 2)
    if args.once and args.interval is not None:
        raise SentryError("--interval belongs to --loop only (a once round "
                          "has no round interval)", 2)
    if args.once and args.max_rounds:
        raise SentryError("--max-rounds belongs to --loop only", 2)
    if args.on_red_preset and args.on_red:
        raise SentryError("--on-red-preset and --on-red are mutually "
                          "exclusive (both given → rc=2; a preset occupies "
                          "the on-red action slot; no silent choice)", 2)
    if args.on_red_args and not args.on_red_preset:
        raise SentryError("--on-red-arg only serves --on-red-preset", 2)
    if args.on_red and not args.emit:
        raise SentryError("--on-red requires --emit (side actions must "
                          "accompany an on-disk event stream; trigger "
                          "evidence and the action log stay auditable; same "
                          "guard as --on-red-preset)", 2)
    if args.retry_max < 0:
        raise SentryError("--retry-max must be >= 0, got %s"
                          % args.retry_max, 2)
    if args.net_retries < 0:
        raise SentryError("--net-retries must be >= 0, got %s"
                          % args.net_retries, 2)
    if args.subproc_timeout < 1:
        raise SentryError("--subproc-timeout must be >= 1, got %s"
                          % args.subproc_timeout, 2)
    if args.emit_max_bytes is not None:
        if not args.emit:
            raise SentryError("--emit-max-bytes must be given with --emit "
                              "(rotation belongs to the event stream file "
                              "itself)", 2)
        if args.emit_max_bytes < 1:
            raise SentryError("--emit-max-bytes must be >= 1, got %d"
                              % args.emit_max_bytes, 2)
    if args.rebuild_state and not args.state_file:
        raise SentryError("--rebuild-state must be given with --state-file "
                          "(with no state there is nothing to rebuild)", 2)
    on_red = None
    if args.on_red_preset:
        on_red = expand_on_red_presets(args.on_red_preset, args.on_red_args,
                                       args.emit)
    elif args.on_red:
        on_red = [args.on_red]          # plain single template in the same table form (same executor entry)
    sentry = {
        "args": args, "mode": mode, "specs": specs,
        "seq": 1, "events": [], "actions": [],
        "emit": args.emit, "on_red": on_red,
        "on_red_preset": (args.on_red_preset[0]
                          if args.on_red_preset
                          and len(args.on_red_preset) == 1
                          else (list(args.on_red_preset)
                                if args.on_red_preset else None)),
        "emit_max_bytes": args.emit_max_bytes, "rotations": 0,
        "timeout": args.timeout, "injector": None, "token": None,
        "retry_max": args.retry_max,
        "net_retries": args.net_retries,
        "subproc_timeout": args.subproc_timeout,
        "ts_enabled": args.sleep_scale != 0,
    }
    if args.injector:
        sentry["injector"] = load_injector(args.injector)
    if args.emit:
        sentry["seq"] = emit_seq_base(args.emit) + 1   # numbering continues across generations (file itself + .1/.2)
    return sentry


def run_sentry(args):
    """Dual-mode main loop: once = a single round; loop = sequential rounds
    at interval (--max-rounds cap, 0 = unlimited). A source hard error →
    sentinel-error event (if emit is present) + rc 9 exit (fail-loud, never
    run in a broken state; the 9 semantics). In loop mode, source-level
    exceptions are handled per source inside poll_round (source-error note;
    skip a round rather than crash the run); a hard error reaching this
    layer means the fallback layer itself failed (e.g. emit append
    failure) and remains fail-loud. state is written at the end of each
    round (events are emitted before state is saved; prefer duplicates over
    lost events)."""
    sentry = build_sentry(args)
    if args.rebuild_state:
        existed = os.path.isfile(args.state_file)
        sys.stdout.write("STATE-REBUILD: %s (--rebuild-state explicit "
                         "rebuild; %s)\n"
                         % (args.state_file,
                            "existing seen discarded; starting from zero"
                            if existed
                            else "no prior state; starting from zero"))
    st = load_state(args.state_file, rebuild=bool(args.rebuild_state))
    interval = args.interval if args.interval is not None else 60.0
    round_no = 0
    try:
        if sentry["specs"] and sentry["injector"] is None:
            sentry["token"] = netrc_token(args.netrc)   # lazy; not fetched when an injector is present
        while True:
            round_no += 1
            sentry["events"] = []
            rep = poll_round(sentry, st, round_no)
            if args.json:
                write_json_report(args.json, rep)
            save_state(args.state_file, st)
            if sentry["mode"] == "once":
                break
            if args.max_rounds and round_no >= args.max_rounds:
                break
            sleep_scaled(interval, args.sleep_scale)
    except SentryError as e:
        ev = make_event(sentry, "sentinel-error", {
            "error": str(e), "code": e.code,
            "note": "source hard error; fail-loud rc=%d exit (never run in "
                    "a broken state)" % e.code})
        emit_event(sentry, ev)
        sys.stdout.write("FAIL-LOUD: %s\n" % e)
        return e.code
    return 0


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="real-time dynamic sentinel: three signal sources (CI "
                    "runs / local probe ledger chain roots / buildlog "
                    "tokens) → JSONL event stream; once/loop dual mode; "
                    "classification and chain roots fully delegated to "
                    "ci_triage/chain_graph subprocesses; zero new engines")
    ap.add_argument("--once", action="store_true",
                    help="a single inspection round, report, then exit "
                         "(workflow-step use)")
    ap.add_argument("--loop", action="store_true",
                    help="long-lived round polling with JSONL event stream "
                         "append (workflow background bash task use)")
    ap.add_argument("--interval", type=float, default=None, metavar="S",
                    help="loop round interval seconds (default 60; --loop "
                         "only)")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=0,
                    metavar="N", help="loop round cap (0 = unlimited; "
                                      "default 0; --loop only)")
    ap.add_argument("--watch-repo", dest="watch_repo", action="append",
                    default=None, metavar="ORG/REPO",
                    help="CI path: poll GET /actions/runs?per_page=30 "
                         "(repeatable; following --branch entries join the "
                         "current group)")
    ap.add_argument("--branch", action="append", default=None, metavar="B",
                    help="branch filter (joins the most recent --watch-repo "
                         "group; repeatable)")
    ap.add_argument("--watch-ledgers", dest="watch_ledgers", default=None,
                    metavar="DIR", help="local ledger path: directory of "
                                        "new probe/ledger JSON files")
    ap.add_argument("--watch-buildlog", dest="watch_buildlog", default=None,
                    metavar="FILE", help="local build path: incremental "
                                         "grep tail of the compilation log")
    ap.add_argument("--state-file", dest="state_file", default=None,
                    metavar="FILE", help="seen idempotence state file "
                                         "(required for loop; "
                                         "rocqwash-sentinel-state/1)")
    ap.add_argument("--emit", default=None, metavar="FILE",
                    help="event stream JSONL append (fsync); without it, "
                         "stdout mirror only")
    ap.add_argument("--emit-max-bytes", dest="emit_max_bytes", type=int,
                    default=None, metavar="N",
                    help="event stream rotation cap (rotate before append "
                         "when over the cap; .1/.2 keep two generations; "
                         "seq continues across generations; must be given "
                         "with --emit)")
    ap.add_argument("--rebuild-state", dest="rebuild_state",
                    action="store_true",
                    help="explicit state rebuild (discard existing seen and "
                         "start from zero; the only legitimate rebuild "
                         "path; a corrupted state is refused with 9 by "
                         "default, no silent rebuild; must be given with "
                         "--state-file)")
    ap.add_argument("--on-red", dest="on_red", default=None, metavar="CMD",
                    help="failing-event command template ({family}/{run}/"
                         "{repo} placeholders); requires --emit (same guard "
                         "as presets); default none = report-only, zero "
                         "action is the default")
    ap.add_argument("--on-red-preset", dest="on_red_preset", action="append",
                    default=None, metavar="NAME",
                    help="failing-event preset action templates (repeatable "
                         "= chained; executed in order, continue after one "
                         "fails: unclog = dry run only; pushci = push "
                         "dry-run; wash-shape = plan only; triage = "
                         "re-classify the failing run [repo/run "
                         "event-substituted]; cw-doctor = full default "
                         "checkup; parameters passed through --on-red-arg; "
                         "mutually exclusive with --on-red, both given → "
                         "rc=2; same executor, zero new execution paths)")
    ap.add_argument("--on-red-arg", dest="on_red_args", action="append",
                    default=None, metavar="K=V",
                    help="preset pass-through parameters (repeatable; "
                         "static family: unclog/wash-shape need src, "
                         "pushci needs repo_path+branch; triage's repo/"
                         "run belong to the dynamic event-substitution "
                         "family and are exempt; {emit_dir} resolves to "
                         "the directory of --emit)")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc path (default ~/.netrc; machine github.com "
                         "6th column = token; same convention as ci_triage)")
    ap.add_argument("--timeout", type=int, default=30, metavar="S",
                    help="single-request timeout seconds (default 30)")
    ap.add_argument("--retry-max", dest="retry_max", type=int, default=3,
                    metavar="N",
                    help="CI API 403/429/5xx backoff retry cap (default 3; "
                         "exponential base 2s; a parseable Retry-After "
                         "second count is honored; real urllib path only; "
                         "injector canned never retries)")
    ap.add_argument("--net-retries", dest="net_retries", type=int, default=3,
                    metavar="N",
                    help="transport-layer transient-disconnect retry cap "
                         "(default 3 attempts; backoff 5s/15s/45s; "
                         "transient classes = IncompleteRead/"
                         "RemoteDisconnected/BadStatusLine/ConnectionError/"
                         "socket.timeout; exhausted → 9 raised to the loop "
                         "layer, which skips that source per round rather "
                         "than crashing the run; --retry-max separately "
                         "covers the HTTP status-code face with base 2s)")
    ap.add_argument("--subproc-timeout", dest="subproc_timeout", type=int,
                    default=120, metavar="S",
                    help="subprocess anti-hang timeout seconds (default "
                         "120; ci_triage/chain_graph calls killed on "
                         "timeout plus fail-loud 9 naming the call; "
                         "--timeout separately covers the HTTP "
                         "single-request timeout)")
    ap.add_argument("--injector", default=None, metavar="FILE",
                    help="canned API response JSON (rocqwash-sentinel-"
                         "injector/1; zero real network, offline-testable; "
                         "must be given with --watch-repo)")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float,
                    default=1.0, metavar="F",
                    help="sleep scale (0 = zero real sleep + event ts "
                         "disabled; selftest dependency)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="per-round report output (rocqwash-sentinel/1; "
                         "overwritten)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        rc = run_sentry(args)
    except SentryError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(e.code)
    sys.exit(rc)


# ---- selftest (--injector canned + tmp fixtures + --sleep-scale 0; zero real
#      network, zero compilation) ------------------------------------------------

def selftest():
    """Embedded frozen vector set (tmp injector/ledger/buildlog fixtures;
    --sleep-scale 0; zero real network, zero compilation; classification
    really goes through the ci_triage subprocess and chain roots really go
    through the chain_graph subprocess):
    (1) once: a new run emits a ci-red event; a second round is
    seen-idempotent with zero events; (2) a new ledger file emits a
    blocking event; (3) buildlog incremental grep (no half-line false
    positives); (4) --on-red placeholder-substitution execution proof
    (canned command writes a tmp marker file); (5) loop three rounds, JSONL
    sequential; (6) --emit JSONL parses line by line + deterministic
    byte-identical reruns + CLI four exit codes + injector non-coverage 9 +
    missing directory 9; (9) --on-red-preset expansion sugar + trigger
    capture + mutual exclusion with --on-red rc=2 + preset argument errors
    rc=2 + plain --on-red without --emit rc=2 (both paths share the guard;
    the preset-path regression lives in the same section)
    (13) preset-table data-driven extension (the three new presets
    wash-shape/triage/cw-doctor placeholder substitution + triage repo/run
    event-substitution family + static override + missing required
    arguments/duplicate/malformed/unknown key/empty parameter surface rc2 +
    chained two-preset expansion [chain-wide union surface, given order,
    zero reordering] + chained trigger executes in order and continues
    after one fails, rc=9→rc=0, two entries logged)
    (10) resilience-layer backoff (403x3→[2,4,8]; Retry-After honored;
    exhaustion 9; 401 not retried; run_py canned sleep subprocess killed on
    timeout with 9 naming the call) (11) --state-file crash recovery
    (corrupted refused with 9, no silent rebuild, original untouched /
    --rebuild-state explicit rebuild reproduces the failing event / missing
    --state-file rc=2) (12) --emit-max-bytes JSONL rotation (rotate before
    append when over the cap; .1/.2 keep two generations; seq continues
    across generations without collision; missing --emit / N<1 rc=2)
    (14) transport-layer transient disconnects (canned IncompleteRead
    read-function injection [_Resp.read raises the real crash shape
    IncompleteRead(371261, 72721)]; first two attempts fail, third succeeds,
    backoff [5,15]; RemoteDisconnected/BadStatusLine/socket.timeout all
    retryable; exhausted retries raise 9 with the backoff sequence asserted
    [5,15,45]; --net-retries cap adjustable = one attempt, one sleep, then
    exhausted; non-transient ValueError propagates as-is, zero swallowing,
    zero sleeping; URLError connection-establishment fails fast 9 with zero
    retries; loop skips per source = canned 401 over two rounds, rc0, no
    crash, two source-error notes, seen untouched [skip a round rather than
    crash the run; prefer duplicates over lost events]; once with the same
    shape still 9, contrasted against the existing CLI-exit vector)
    (15) deployment-shape smoke test (supervisor shell
    examples/sentinel_supervisor.sh: bash -n syntax check + key-line grep
    assertions [restart cap / backoff / state continuation note / withdraw
    hook left empty with return 0 / guard position / rc triage /
    three-artifact placement names / zero hardcoded absolute paths];
    static assertions, not a real run; zero execution, zero network; only
    verifies the deployment artifact is in the repository with its
    structure present point by point)."""
    import shutil

    def run(args, cwd=None):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           cwd=cwd)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    tmp = tempfile.mkdtemp(prefix="rocqwash_cw_sentinel_self_")
    try:
        REPO = "org/repo"
        # canned: runs table (one completed failure run 178) + jobs table
        # (A-content-red shape; the failing step name Build is in
        # ci_triage's classification-spectrum A tokens)
        runs_body = {"total_count": 1, "workflow_runs": [
            {"id": 178, "name": "CI", "run_number": 9, "status": "completed",
             "conclusion": "failure", "head_branch": "main",
             "head_sha": "abc123def",
             "html_url": "https://github.com/org/repo/actions/runs/178"}]}
        jobs_body = {"total_count": 1, "jobs": [
            {"id": 501, "name": "build", "status": "completed",
             "conclusion": "failure",
             "started_at": "2026-11-10T08:00:00Z",
             "completed_at": "2026-11-10T08:01:00Z",
             "steps": [
                 {"number": 1, "name": "Build (coqc batch)",
                  "status": "completed", "conclusion": "failure",
                  "started_at": "2026-11-10T08:00:01Z",
                  "completed_at": "2026-11-10T08:00:30Z"}]}]}
        inj = {"schema": INJECTOR_SCHEMA, "responses": [
            {"url_contains": "/actions/runs?", "status": 200, "body": runs_body},
            {"url_contains": "/runs/178/jobs", "status": 200, "body": jobs_body}]}
        inj_path = os.path.join(tmp, "injector.json")
        with io.open(inj_path, "w", encoding="utf-8") as fh:
            json.dump(inj, fh, sort_keys=True)

        # [1] once: a new run emits a ci-red event; a second round is
        # seen-idempotent with zero events
        state1 = os.path.join(tmp, "state1.json")
        emit1 = os.path.join(tmp, "events1.jsonl")
        rep1 = os.path.join(tmp, "rep1.json")
        p = run(["--once", "--watch-repo", REPO, "--branch", "main",
                 "--injector", inj_path, "--state-file", state1,
                 "--emit", emit1, "--json", rep1, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(rep1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["mode"] == "once" \
            and rep["round"] == 1, rep.get("schema")
        evs = [json.loads(l) for l in io.open(emit1, encoding="utf-8")
               if l.strip()]
        assert len(evs) == 1 and evs[0]["kind"] == "ci-red", evs
        ev = evs[0]
        assert ev["repo"] == REPO and ev["run"] == 178 \
            and ev["family"] == "A-content-red" \
            and ev["action"] == "fix-content", ev
        assert ev["schema"] == EVENT_SCHEMA and ev["seq"] == 1, ev
        assert "ts" not in ev and "ts=off" in ev.get("note", ""), ev  # ts-off note present
        # state records seen; passing or not, all runs are recorded
        st = json.load(io.open(state1, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA \
            and st["repos"][REPO]["seen_runs"]["178"]["family"] \
            == "A-content-red", st
        # second round: seen idempotent, zero events
        p = run(["--once", "--watch-repo", REPO, "--branch", "main",
                 "--injector", inj_path, "--state-file", state1,
                 "--emit", emit1, "--json", rep1, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs2 = [json.loads(l) for l in io.open(emit1, encoding="utf-8")
                if l.strip()]
        assert len(evs2) == 1, "second round should have zero new events, " \
            "got %d" % len(evs2)
        rep = json.load(io.open(rep1, encoding="utf-8"))
        assert rep["events"] == [] and rep["sources"]["ci"][0]["new_runs"] == 0, rep

        # [2] a new ledger file emits a blocking event (LibX washable chain
        # root + B1 missing-library dependent)
        ldir = os.path.join(tmp, "ledgers")
        os.mkdir(ldir)
        ledger = {"LibX": {"file": "LibX", "rc": 0, "red": ""},
                  "B1": {"file": "B1", "rc": 1,
                         "red": "Error: Unable to locate library | LibX"}}
        lpath = os.path.join(ldir, "ledgerA.json")
        with io.open(lpath, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)
        state2 = os.path.join(tmp, "state2.json")
        emit2 = os.path.join(tmp, "events2.jsonl")
        p = run(["--once", "--watch-ledgers", ldir, "--state-file", state2,
                 "--emit", emit2, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs = [json.loads(l) for l in io.open(emit2, encoding="utf-8")
               if l.strip()]
        assert len(evs) == 1 and evs[0]["kind"] == "blocking", evs
        assert evs[0]["top_root"] == "LibX" \
            and evs[0]["dependents"] == ["B1"] and evs[0]["n"] == 1, evs[0]
        assert evs[0]["self"]["washable"] is True, evs[0]
        # unchanged file: second round idempotent, zero events
        p = run(["--once", "--watch-ledgers", ldir, "--state-file", state2,
                 "--emit", emit2, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs2 = [json.loads(l) for l in io.open(emit2, encoding="utf-8")
                if l.strip()]
        assert len(evs2) == 1, "unchanged file, second round should have " \
            "zero new events, got %d" % len(evs2)

        # [3] buildlog incremental grep (no half-line false positives; the
        # second round reports only new lines)
        log = os.path.join(tmp, "build.log")
        with io.open(log, "w", encoding="utf-8") as fh:
            fh.write("ok line\nBUILD-FAIL at step 2\nhalf line no newline")
        state3 = os.path.join(tmp, "state3.json")
        emit3 = os.path.join(tmp, "events3.jsonl")
        p = run(["--once", "--watch-buildlog", log, "--state-file", state3,
                 "--emit", emit3, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs = [json.loads(l) for l in io.open(emit3, encoding="utf-8")
               if l.strip()]
        assert len(evs) == 1 and evs[0]["kind"] == "build-signal", evs
        assert evs[0]["hits"] == ["BUILD-FAIL at step 2"], evs[0]  # no half-line false positive
        st = json.load(io.open(state3, encoding="utf-8"))
        assert st["buildlogs"][log]["offset"] > 0, st
        # append new signals (with a half line) → the second round reports
        # only the new complete lines
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("\nEXIT=134 in job3\nError: LibX.v:12: no\nHALF-NOEOL")
        p = run(["--once", "--watch-buildlog", log, "--state-file", state3,
                 "--emit", emit3, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs = [json.loads(l) for l in io.open(emit3, encoding="utf-8")
               if l.strip() and json.loads(l)["kind"] == "build-signal"
               and json.loads(l)["hits"] == ["EXIT=134 in job3",
                                             "Error: LibX.v:12: no"]]
        assert len(evs) == 1, "second round should report only the new " \
            "complete lines, got %s" % evs
        # negative lines do not match
        assert not BUILDLOG_SIGNAL_RE.search("EXIT=0 all good") \
            and not BUILDLOG_SIGNAL_RE.search("no errors here"), \
            "negative token examples matched"

        # [4] --on-red placeholder-substitution execution proof (canned
        # command writes a tmp marker file)
        marker_dir = os.path.join(tmp, "markers")
        os.mkdir(marker_dir)
        cmd = ("printf '%s|%s|%s' {family} {run} {repo} > "
               + os.path.join(marker_dir, "red.marker"))
        state4 = os.path.join(tmp, "state4.json")
        emit4 = os.path.join(tmp, "events4.jsonl")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state4, "--emit", emit4, "--on-red", cmd,
                 "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        m = io.open(os.path.join(marker_dir, "red.marker"),
                    encoding="utf-8").read()
        assert m == "A-content-red|178|org/repo", \
            "placeholder substitution mismatch: %r" % m
        # default zero action: no --on-red → no actions
        state4b = os.path.join(tmp, "state4b.json")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state4b, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]

        # [5] loop three rounds, JSONL sequential (--max-rounds 3; round 1
        # reports the failure; rounds 2/3 idempotent, zero new)
        state5 = os.path.join(tmp, "state5.json")
        emit5 = os.path.join(tmp, "events5.jsonl")
        rep5 = os.path.join(tmp, "rep5.json")
        p = run(["--loop", "--max-rounds", "3", "--interval", "5",
                 "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state5, "--emit", emit5, "--json", rep5,
                 "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(rep5, encoding="utf-8"))
        assert rep["mode"] == "loop" and rep["round"] == 3, rep
        evs = [json.loads(l) for l in io.open(emit5, encoding="utf-8")
               if l.strip()]
        assert len(evs) == 1 and evs[0]["kind"] == "ci-red", evs
        assert evs[0]["seq"] == 1, evs[0]

        # [6] --emit JSONL parses line by line + sort_keys byte form + seq
        # sequential
        for path in (emit1, emit2, emit3, emit4, emit5):
            seqs = []
            for line in io.open(path, encoding="utf-8"):
                if not line.strip():
                    continue
                ev = json.loads(line)          # each line parses
                assert ev["schema"] == EVENT_SCHEMA, ev
                assert line == json.dumps(ev, ensure_ascii=False,
                                          sort_keys=True) + "\n", \
                    "line is not the sort_keys canonical form: %s" % line
                seqs.append(ev["seq"])
            assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs), \
                "seq sequentiality broken: %s" % seqs

        # [7] determinism: once (ts off; same tmp state reset) rerun report
        # byte-identical
        d1 = os.path.join(tmp, "det1")
        os.mkdir(d1)
        rep_a = os.path.join(d1, "a.json")
        rep_b = os.path.join(d1, "b.json")
        common = ["--once", "--watch-ledgers", ldir, "--sleep-scale", "0"]
        assert run(common + ["--json", rep_a]).returncode == 0
        assert run(common + ["--json", rep_b]).returncode == 0
        assert io.open(rep_a, "rb").read() == io.open(rep_b, "rb").read(), \
            "report byte drift = violation"

        # [8] CLI four exit codes + usage face + unreachable source 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should be rc=2, got %d" \
            % p.returncode
        p = run([])
        assert p.returncode == 2, "missing mode should be rc=2, got %d" \
            % p.returncode
        p = run(["--once", "--loop"])
        assert p.returncode == 2, "both modes given should be rc=2, got %d" \
            % p.returncode
        p = run(["--once"])
        assert p.returncode == 2, "all three sources missing should be " \
            "rc=2, got %d" % p.returncode
        p = run(["--once", "--branch", "main", "--watch-ledgers", ldir])
        assert p.returncode == 2, "--branch before --watch-repo should be " \
            "rc=2, got %d" % p.returncode
        p = run(["--once", "--watch-repo", "justname"])
        assert p.returncode == 2, "malformed repo should be rc=2, got %d" \
            % p.returncode
        p = run(["--once", "--watch-repo", REPO, "--interval", "5"])
        assert p.returncode == 2, "once with interval should be rc=2, " \
            "got %d" % p.returncode
        p = run(["--once", "--max-rounds", "3", "--watch-ledgers", ldir])
        assert p.returncode == 2, "once with max-rounds should be rc=2, " \
            "got %d" % p.returncode
        p = run(["--once", "--watch-ledgers",
                 os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "missing directory should be rc=9, " \
            "got %d" % p.returncode
        # injector canned returns 401 → 9
        inj401 = {"schema": INJECTOR_SCHEMA, "responses": [
            {"url_contains": "/actions/runs?", "status": 401,
             "body": {"message": "Bad credentials"}}]}
        p401 = os.path.join(tmp, "inj401.json")
        with io.open(p401, "w", encoding="utf-8") as fh:
            json.dump(inj401, fh)
        p = run(["--once", "--watch-repo", REPO, "--injector", p401,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, "CI 401 should be rc=9, got %d" \
            % p.returncode
        assert "HTTP 401" in p.stdout or "HTTP 401" in p.stderr \
            or "sentinel-error" in p.stdout, p.stdout[-300:]
        # injector canned non-coverage → 9 (never silently fall through to
        # the real network)
        injgap = {"schema": INJECTOR_SCHEMA, "responses": [
            {"url_contains": "/definitely-not", "status": 200, "body": {}}]}
        pgap = os.path.join(tmp, "injgap.json")
        with io.open(pgap, "w", encoding="utf-8") as fh:
            json.dump(injgap, fh)
        p = run(["--once", "--watch-repo", REPO, "--injector", pgap,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, "canned non-coverage should be rc=9, " \
            "got %d" % p.returncode
        assert "does not cover" in p.stdout, p.stdout[-300:]
        # injector without a CI path → 2
        p = run(["--once", "--watch-ledgers", ldir, "--injector", inj_path])
        assert p.returncode == 2, "injector without a CI path should be " \
            "rc=2, got %d" % p.returncode

        # [9] --on-red-preset: expansion sugar unit assertions + trigger
        # capture (canned command logged in the actions list; placeholder
        # substitution asserted) + mutual exclusion with --on-red rc=2 +
        # argument errors rc=2
        ev9 = os.path.join(tmp, "events9.jsonl")
        cmd = expand_on_red_preset("unclog", ["src=/abs/fake_src"], ev9)
        assert cmd == ("python3 -B %s --src /abs/fake_src --json "
                       "%s/unclog_{run}.json" % (UNCLOG_TOOL, tmp)), cmd
        cmd = expand_on_red_preset("pushci", ["repo_path=/r", "branch=main"],
                                   ev9)
        assert cmd == ("python3 -B %s --repo-path /r --branch main --json "
                       "%s/pushci_{run}.json --dry-run" % (PUSHCI_TOOL, tmp)), \
            cmd
        assert cmd.endswith("--dry-run") and "{run}" in cmd, cmd  # dry run by default; {run} left for the executor
        for bad in (lambda: expand_on_red_preset("bogus", [], ev9),
                    lambda: expand_on_red_preset("unclog", [], ev9),
                    lambda: expand_on_red_preset("unclog", ["src=/a",
                                                            "src=/b"], ev9),
                    lambda: expand_on_red_preset("unclog", ["src"], ev9),
                    lambda: expand_on_red_preset("unclog", ["world=/w"], ev9),
                    lambda: expand_on_red_preset("pushci",
                                                 ["repo_path=/r"], ev9)):
            try:
                bad()
                assert False, "negative expansion should be rc=2"
            except SentryError as e:
                assert e.code == 2, "negative expansion should be 2, got %d" \
                    % e.code
        # trigger capture: real subprocess chain (canned CI failing event →
        # the same executor delegate-runs the unclog dry-run command;
        # rc != 0 logged loudly; the sentinel's exit code stays 0; side
        # actions outside the verdict surface, proven)
        psrc = os.path.join(tmp, "preset_src")
        os.mkdir(psrc)
        with io.open(os.path.join(psrc, "A.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma ok : True.\n")
        state9 = os.path.join(tmp, "state9.json")
        emit9b = os.path.join(tmp, "events9b.jsonl")
        rep9 = os.path.join(tmp, "rep9.json")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state9, "--emit", emit9b,
                 "--on-red-preset", "unclog", "--on-red-arg", "src=" + psrc,
                 "--json", rep9, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(rep9, encoding="utf-8"))
        assert rep.get("on_red_preset") == "unclog", rep.get("on_red_preset")
        assert len(rep["actions"]) == 1, rep["actions"]
        act = rep["actions"][0]
        assert act["cmd"] == ("python3 -B %s --src %s --json %s/unclog_178.json"
                              % (UNCLOG_TOOL, psrc, tmp)), \
            "preset expansion mismatch: %r" % act["cmd"]
        assert act["rc"] == 9, "delegate-run unclog (fixture has no " \
            "--world) should log rc=9: %r" % act
        mw = re.search(r"workdir -> (\S+)", act.get("output") or "")
        if mw:
            shutil.rmtree(mw.group(1), ignore_errors=True)  # clean up the delegate run's mkdtemp
        # --on-red together with a preset → 2; unrecognized preset / missing
        # arguments / missing --emit / orphan --on-red-arg → 2
        base9 = ["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--sleep-scale", "0"]
        p = run(base9 + ["--on-red", "echo x", "--on-red-preset", "unclog",
                         "--on-red-arg", "src=" + psrc, "--emit", emit9b])
        assert p.returncode == 2, "--on-red together with a preset should " \
            "be rc=2, got %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "bogus", "--emit", emit9b])
        assert p.returncode == 2, "unrecognized preset should be rc=2, " \
            "got %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "unclog", "--emit", emit9b])
        assert p.returncode == 2, "missing preset arguments should be " \
            "rc=2, got %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "unclog", "--on-red-arg",
                         "src=" + psrc])
        assert p.returncode == 2, "missing --emit should be rc=2, got %d" \
            % p.returncode
        # plain path, same guard: --on-red without --emit → 2; the
        # preset-path regression = the first two expansion assertions of
        # this section + trigger capture + the preset-without---emit rc=2
        # above, none disturbed by the guard (the guard only checks --emit
        # presence on the plain path).
        p = run(base9 + ["--on-red", "echo x"])
        assert p.returncode == 2, "plain --on-red without --emit should be " \
            "rc=2, got %d" % p.returncode
        assert "--emit" in p.stdout, p.stdout[-300:]
        p = run(base9 + ["--on-red-arg", "src=" + psrc, "--emit", emit9b])
        assert p.returncode == 2, "orphan --on-red-arg should be rc=2, " \
            "got %d" % p.returncode

        # [9b] preset-table data-driven extension: the three new presets'
        # placeholder substitution + missing required arguments rc2 +
        # chained two-preset expansion + chained trigger (in order; continue
        # after one fails, rc=9→rc=0, two entries logged; the sentinel's
        # exit code stays 0). triage/cw-doctor only get expansion-level
        # vectors (triggering them would hit the real network / a real
        # checkup; the zero-real-network rule must not break); the trigger
        # capture uses an [unclog, wash-shape] chain (both legs offline and
        # fast).
        ev9b = os.path.join(tmp, "events9b.jsonl")
        cmd = expand_on_red_preset("wash-shape", ["src=/abs/ws_src"], ev9b)
        assert cmd == ("python3 -B %s --dir /abs/ws_src --json "
                       "%s/wash_shape_{run}.json" % (WASH_SHAPE_TOOL, tmp)), \
            cmd
        assert "{run}" in cmd, cmd                    # dynamic family left for event substitution
        cmd = expand_on_red_preset("triage", [], ev9b)
        assert cmd == ("python3 -B %s --repo {repo} --run {run} --json "
                       "%s/triage_{run}.json" % (TRIAGE_TOOL, tmp)), cmd
        assert "{repo}" in cmd and "{run}" in cmd, cmd  # event-substitution family left as-is
        cmd = expand_on_red_preset("triage", ["repo=o/r", "run=178"], ev9b)
        assert cmd == ("python3 -B %s --repo o/r --run 178 --json "
                       "%s/triage_178.json" % (TRIAGE_TOOL, tmp)), cmd  # static override
        cmd = expand_on_red_preset("cw-doctor", [], ev9b)
        assert cmd == ("python3 -B %s --json %s/doctor_{run}.json"
                       % (CW_DOCTOR_TOOL, tmp)), cmd
        # missing required / malformed / duplicate key / unknown key / empty
        # surface → 2 (same guard; the dynamic-family exemption does not
        # cover the static family)
        for bad in (lambda: expand_on_red_preset("wash-shape", [], ev9b),
                    lambda: expand_on_red_preset("wash-shape",
                                                 ["src=/a", "src=/b"], ev9b),
                    lambda: expand_on_red_preset("wash-shape", ["src"], ev9b),
                    lambda: expand_on_red_preset("wash-shape",
                                                 ["world=/w"], ev9b),
                    lambda: expand_on_red_preset("cw-doctor",
                                                 ["src=/a"], ev9b)):
            try:
                bad()
                assert False, "new-preset negative expansion should be rc=2"
            except SentryError as e:
                assert e.code == 2, "new-preset negative expansion should " \
                    "be 2, got %d" % e.code
        p = run(base9 + ["--on-red-preset", "wash-shape", "--emit", emit9b])
        assert p.returncode == 2, "CLI preset with missing arguments " \
            "should be rc=2, got %d" % p.returncode
        # chained expansion: the --on-red-arg namespace is shared across the
        # chain (unknown keys judged on the chain-wide union surface;
        # unclog+triage needs only src to form a chain; triage's repo/run
        # go through event substitution); given order, zero reordering
        cmds = expand_on_red_presets(["unclog", "triage"], ["src=/s"], ev9b)
        assert cmds == [
            "python3 -B %s --src /s --json %s/unclog_{run}.json"
            % (UNCLOG_TOOL, tmp),
            "python3 -B %s --repo {repo} --run {run} --json "
            "%s/triage_{run}.json" % (TRIAGE_TOOL, tmp)], cmds
        for bad in (lambda: expand_on_red_presets(["unclog", "cw-doctor"],
                                                  ["world=/w"], ev9b),
                    lambda: expand_on_red_presets(["pushci", "cw-doctor"],
                                                  [], ev9b),
                    lambda: expand_on_red_presets(["bogus", "unclog"],
                                                  [], ev9b)):
            try:
                bad()
                assert False, "chained negative expansion should be rc=2"
            except SentryError as e:
                assert e.code == 2, "chained negative expansion should be " \
                    "2, got %d" % e.code
        # chained trigger capture: canned CI failing event → chain [unclog,
        # wash-shape] executed in order, continue after one fails; leg1
        # unclog (empty src, zero candidates) rc=9 logged loudly without
        # halting; leg2 wash-shape dry-run plan (empty tree, clean) rc=0;
        # both entries logged with the same schema; the sentinel's exit code
        # stays 0 (side actions outside the verdict surface)
        esrc = os.path.join(tmp, "empty_src")
        os.mkdir(esrc)
        state9b = os.path.join(tmp, "state9b.json")
        emit9c = os.path.join(tmp, "events9c.jsonl")
        rep9b = os.path.join(tmp, "rep9b.json")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state9b, "--emit", emit9c,
                 "--on-red-preset", "unclog", "--on-red-preset", "wash-shape",
                 "--on-red-arg", "src=" + esrc,
                 "--json", rep9b, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(rep9b, encoding="utf-8"))
        assert rep.get("on_red_preset") == ["unclog", "wash-shape"], \
            rep.get("on_red_preset")
        assert len(rep["actions"]) == 2, rep["actions"]
        act1, act2 = rep["actions"]
        assert act1["cmd"] == ("python3 -B %s --src %s --json "
                               "%s/unclog_178.json"
                               % (UNCLOG_TOOL, esrc, tmp)), act1["cmd"]
        assert act1["rc"] == 9, "leg1 unclog (empty src) should log rc=9: " \
            "%r" % act1
        assert act2["cmd"] == ("python3 -B %s --dir %s --json "
                               "%s/wash_shape_178.json"
                               % (WASH_SHAPE_TOOL, esrc, tmp)), act2["cmd"]
        assert act2["rc"] == 0, "leg2 wash-shape dry-run plan should be " \
            "rc=0 (continue-after-failure proof; leg1 rc=9 does not " \
            "halt): %r" % act2
        assert act1["seq"] == act2["seq"] == 1, (act1["seq"], act2["seq"])
        assert os.path.isfile(os.path.join(tmp, "wash_shape_178.json")), \
            "leg2's designated preset path should actually write the report"
        mw = re.search(r"workdir -> (\S+)", act1.get("output") or "")
        if mw:
            shutil.rmtree(mw.group(1), ignore_errors=True)  # clean up leg1's mkdtemp

        # [10] resilience layer: backoff sequence + Retry-After honored +
        # api_get_json retry runner + run_py timeout kill (zero network,
        # zero compilation; _open/_sleep injection; 403x3 → [2,4,8])
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        assert _http_backoff.parse_retry_after("30") == 30.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, \
            "HTTP-date shapes are not guessed"

        class _Resp(object):
            """canned response body (urlopen fake; zero network;
            context-manager form)."""
            def __init__(self, payload=b"{}"):
                self._p = payload
            def read(self):
                return self._p
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def _api_err(code, ra=None):
            hd = {"Retry-After": ra} if ra else {}
            return urllib.error.HTTPError(
                "https://x", code, "HTTP Error %d" % code, hd,
                io.BytesIO(b'{"message":"x"}'))

        def _seq_open(resps):
            it = iter(resps)
            def _open(req, timeout=None):
                r = next(it)
                if isinstance(r, Exception):
                    raise r          # canned error objects must raise (same semantics as urlopen)
                return r
            return _open

        slept = []
        st10, body10 = api_get_json("https://x", "tok", 5, None, retry_max=3,
                                    _open=_seq_open([_api_err(403)] * 3
                                                    + [_Resp(b'{"ok":1}')]),
                                    _sleep=slept.append)
        assert st10 == 200 and body10 == {"ok": 1} \
            and slept == [2.0, 4.0, 8.0], (st10, body10, slept)
        slept = []
        st10, _ = api_get_json("https://x", "tok", 5, None, retry_max=3,
                               _open=_seq_open([_api_err(429, ra="9"),
                                                _Resp()]),
                               _sleep=slept.append)
        assert st10 == 200 and slept == [9.0], \
            (st10, slept)                      # Retry-After header honored (replaces exponential)
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=3,
                         _open=_seq_open([_api_err(503)] * 4),
                         _sleep=slept.append)
            assert False, "503x4 retries exhausted should be 9"
        except SentryError as e:
            assert e.code == 9 and "HTTP 503" in str(e), e
        assert slept == [2.0, 4.0, 8.0], slept
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=3,
                         _open=_seq_open([_api_err(401)]), _sleep=slept.append)
            assert False, "401 semantic face should not retry and go " \
                "straight to 9"
        except SentryError as e:
            assert e.code == 9, e.code
        assert slept == [], "401: zero retries, zero sleeps"
        # run_py timeout kill (canned sleep subprocess; fail-loud 9 naming
        # the call)
        sleepy = os.path.join(tmp, "sleepy_sentinel.py")
        with io.open(sleepy, "w", encoding="utf-8") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        try:
            run_py(sleepy, ["--hang"], timeout=2)
            assert False, "timeout should fail loudly with 9"
        except SentryError as e:
            assert e.code == 9 and "sleepy_sentinel.py" in str(e) \
                and "2s" in str(e), e
        fastpy = os.path.join(tmp, "fast_sentinel.py")
        with io.open(fastpy, "w", encoding="utf-8") as fh:
            fh.write("print('ok')\n")
        rc10, out10 = run_py(fastpy, [], timeout=5)
        assert rc10 == 0 and "ok" in out10, (rc10, out10)

        # [11] --state-file crash-recovery semantics: corrupted refused with
        # 9, no silent rebuild (original untouched) / --rebuild-state
        # explicit rebuild (seen discarded from zero; the failing event
        # reappears)
        statec = os.path.join(tmp, "state_corrupt.json")
        corrupt = '{"repos": BROKEN-JSON{{{'
        with io.open(statec, "w", encoding="utf-8") as fh:
            fh.write(corrupt)
        emitc = os.path.join(tmp, "events_c.jsonl")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", statec, "--emit", emitc, "--sleep-scale", "0"])
        assert p.returncode == 9, "corrupted state should be refused with " \
            "rc=9, got %d" % p.returncode
        assert "malformed" in p.stdout, p.stdout[-300:]
        assert "STATE-REBUILD" not in p.stdout, p.stdout[-300:]
        assert io.open(statec, encoding="utf-8").read() == corrupt, \
            "corrupted state silently rewritten = violation (no silent " \
            "rebuild)"
        # --rebuild-state explicit rebuild: same corrupted file → rc0; the
        # failing event reappears (seen discarded)
        emitr = os.path.join(tmp, "events_r.jsonl")
        repr_ = os.path.join(tmp, "rep_rebuild.json")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", statec, "--emit", emitr, "--json", repr_,
                 "--rebuild-state", "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        assert "STATE-REBUILD" in p.stdout, p.stdout[-300:]
        rep = json.load(io.open(repr_, encoding="utf-8"))
        assert rep.get("state_rebuilt") is True, rep.get("state_rebuilt")
        evs = [json.loads(l) for l in io.open(emitr, encoding="utf-8")
               if l.strip()]
        assert len(evs) == 1 and evs[0]["kind"] == "ci-red", \
            "after rebuild, seen discarded should reproduce the ci-red " \
            "event: %s" % evs
        st = json.load(io.open(statec, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA \
            and st["repos"][REPO]["seen_runs"], \
            "after rebuild, state should be a fresh valid ledger"
        # --rebuild-state without --state-file → 2 (with no state there is
        # nothing to rebuild)
        p = run(["--once", "--watch-ledgers", ldir, "--rebuild-state"])
        assert p.returncode == 2, "rebuild without state-file should be " \
            "rc=2, got %d" % p.returncode

        # [12] --emit-max-bytes JSONL rotation (rotate before append when
        # over the cap; .1/.2 keep two generations; seq continues across
        # generations without collision)
        rot_emit = os.path.join(tmp, "events_rot.jsonl")
        repx = os.path.join(tmp, "rep_rot.json")
        for i in range(3):
            ldir_i = os.path.join(tmp, "rot_ledgers_%d" % i)
            os.mkdir(ldir_i)
            ledger_i = {"LibX": {"file": "LibX", "rc": 0, "red": ""},
                        "B%d" % i: {"file": "B%d" % i, "rc": 1,
                                    "red": "Error: Unable to locate library "
                                           "| LibX"}}
            with io.open(os.path.join(ldir_i, "ledgerR.json"), "w",
                         encoding="utf-8") as fh:
                json.dump(ledger_i, fh)
            p = run(["--once", "--watch-ledgers", ldir_i, "--emit", rot_emit,
                     "--emit-max-bytes", "300", "--json", repx,
                     "--sleep-scale", "0"])
            assert p.returncode == 0, p.stdout[-600:]
        assert "emit rotation" in p.stdout, \
            "the last round should note the rotation loudly: %s" \
            % p.stdout[-300:]
        assert os.path.isfile(rot_emit + ".1") \
            and os.path.isfile(rot_emit + ".2"), \
            "rotation should produce both .1/.2 generations"
        seqs = []
        for gpath in (rot_emit + ".2", rot_emit + ".1", rot_emit):
            for ln in io.open(gpath, encoding="utf-8"):
                if ln.strip():
                    ev = json.loads(ln)          # each line parses within the generation
                    assert ev["schema"] == EVENT_SCHEMA, ev
                    seqs.append(ev["seq"])
        assert sorted(seqs) == [1, 2, 3], \
            "seq should continue across generations without collision: %s" \
            % seqs
        rep = json.load(io.open(repx, encoding="utf-8"))
        assert rep.get("emit_max_bytes") == 300 \
            and rep.get("emit_rotations") == 1, \
            (rep.get("emit_max_bytes"), rep.get("emit_rotations"))
        # negative: missing --emit / N<1 → 2
        p = run(["--once", "--watch-ledgers", ldir, "--emit-max-bytes", "300"])
        assert p.returncode == 2, "rotation without --emit should be rc=2, " \
            "got %d" % p.returncode
        p = run(["--once", "--watch-ledgers", ldir, "--emit", rot_emit,
                 "--emit-max-bytes", "0"])
        assert p.returncode == 2, "rotation N=0 should be rc=2, got %d" \
            % p.returncode

        # [13] resilience layer: transport-layer transient bounded retries +
        # loop per-source skip (real crash shape IncompleteRead(371261,
        # 72721))
        assert net_backoff_delays(3) == [5.0, 15.0, 45.0], \
            net_backoff_delays(3)
        assert net_backoff_delays(0) == [], net_backoff_delays(0)
        for bad in (-1, "3", 1.5, None, True):
            try:
                net_backoff_delays(bad)
                assert False, "net_retries=%r should raise ValueError" \
                    % (bad,)
            except ValueError:
                pass

        class _BadReadResp(_Resp):
            """canned half-read truncated body (read-function injection
            face: resp.read() raises IncompleteRead with the real crash
            shape 371261 read/72721 expected; partial must be bytes; the
            int form's __str__ calls len() and raises by itself; the real
            crash text is "371261 bytes read, 72721 more expected")."""
            def read(self):
                raise http.client.IncompleteRead(b"\x00" * 371261, 72721)

        # first two attempts fail, third succeeds (default 3-attempt cap;
        # backoff 5s/15s; retry_max=0 isolates the status-code face)
        slept = []
        st13, body13 = api_get_json("https://x", "tok", 5, None, retry_max=0,
                                    _open=_seq_open([_BadReadResp(),
                                                     _BadReadResp(),
                                                     _Resp(b'{"ok":13}')]),
                                    _sleep=slept.append)
        assert st13 == 200 and body13 == {"ok": 13} \
            and slept == [5.0, 15.0], (st13, body13, slept)
        # every transient class is retryable (RemoteDisconnected/
        # BadStatusLine/socket.timeout raised on the first three attempts;
        # the fourth succeeds → full 5/15/45 backoff)
        slept = []
        st13, _ = api_get_json("https://x", "tok", 5, None, retry_max=0,
                               _open=_seq_open([
                                   http.client.RemoteDisconnected(),
                                   http.client.BadStatusLine("bogus"),
                                   socket.timeout("timed out"),
                                   _Resp(b'{"ok":1}')]),
                               _sleep=slept.append)
        assert st13 == 200 and slept == [5.0, 15.0, 45.0], (st13, slept)
        # exhausted retries raise (fail-loud preserved); the full backoff
        # sequence [5,15,45] is asserted; the real crash text is asserted
        # verbatim ("371261 bytes read, 72721 more expected")
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         _open=_seq_open([_BadReadResp()] * 4),
                         _sleep=slept.append)
            assert False, "transport-layer retries exhausted should be 9"
        except SentryError as e:
            assert e.code == 9 and "retries exhausted" in str(e) \
                and "IncompleteRead" in str(e) \
                and "371261 bytes read, 72721 more expected" in str(e), e
        assert slept == [5.0, 15.0, 45.0], slept          # backoff sequence assertion
        # message-layer defense: an exception whose str() blows up itself
        # (IncompleteRead with a non-bytes partial, whose __str__ len()
        # raises again) does not shadow the original error; the
        # exhausted-retry raise still yields a clean SentryError 9
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         _open=_seq_open(
                             [http.client.IncompleteRead(1, 2)] * 4),
                         _sleep=slept.append)
            assert False, "an exception whose str() blows up should still " \
                "yield 9 on exhaustion"
        except SentryError as e:
            assert e.code == 9 and "IncompleteRead" in str(e), e
        assert slept == [5.0, 15.0, 45.0], slept
        # --net-retries cap is adjustable: cap 1 → exhausted after one retry
        # (one 5s sleep)
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         net_retries=1,
                         _open=_seq_open([_BadReadResp(), _BadReadResp()]),
                         _sleep=slept.append)
            assert False, "net_retries=1 exhaustion should be 9"
        except SentryError as e:
            assert e.code == 9, e.code
        assert slept == [5.0], slept
        slept = []
        st13, _ = api_get_json("https://x", "tok", 5, None, retry_max=0,
                               net_retries=1,
                               _open=_seq_open([_BadReadResp(), _Resp()]),
                               _sleep=slept.append)
        assert st13 == 200 and slept == [5.0], (st13, slept)
        # non-transient: no swallowing, no retries; unknown exceptions
        # propagate as-is (fail-loud no-swallow boundary)
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None,
                         _open=_seq_open([ValueError("boom-nontransient")]),
                         _sleep=slept.append)
            assert False, "non-transient exceptions should propagate as-is"
        except ValueError as e:
            assert "boom-nontransient" in str(e), e
        assert slept == [], "non-transient: zero retries, zero sleeps"
        # URLError connection-establishment still fails fast with 9 (not
        # mixed into the transport-layer retry face)
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None,
                         _open=_seq_open([urllib.error.URLError("dns fail")]),
                         _sleep=slept.append)
            assert False, "URLError should fail fast with 9"
        except SentryError as e:
            assert e.code == 9 and "unreachable" in str(e), e
        assert slept == [], "URLError: zero retries, zero sleeps"
        # loop-level per-source skip: canned 401 skips each of two rounds →
        # rc 0, no crash (skip a round rather than crash the run); two
        # source-error notes; seen untouched (next round re-reports; prefer
        # duplicates over lost events)
        state13 = os.path.join(tmp, "state13.json")
        emit13 = os.path.join(tmp, "events13.jsonl")
        rep13 = os.path.join(tmp, "rep13.json")
        p = run(["--loop", "--max-rounds", "2", "--interval", "5",
                 "--watch-repo", REPO, "--injector", p401,
                 "--state-file", state13, "--emit", emit13, "--json", rep13,
                 "--sleep-scale", "0"])
        assert p.returncode == 0, \
            "loop per-source fallback should be rc=0 without crashing (skip " \
            "a round rather than crash the run): %s" % p.stdout[-600:]
        rep = json.load(io.open(rep13, encoding="utf-8"))
        assert rep["mode"] == "loop" and rep["round"] == 2, rep
        assert rep["sources"]["ci"][0].get("skipped") is True \
            and "HTTP 401" in rep["sources"]["ci"][0].get("error", ""), \
            rep["sources"]["ci"]
        evs13 = [json.loads(l) for l in io.open(emit13, encoding="utf-8")
                 if l.strip()]
        assert len(evs13) == 2 and all(e["kind"] == "source-error"
                                       for e in evs13), evs13
        assert [e["seq"] for e in evs13] == [1, 2], evs13
        assert evs13[0]["source"] == "ci:" + REPO \
            and "HTTP 401" in evs13[0]["error"], evs13[0]
        st13 = json.load(io.open(state13, encoding="utf-8"))
        assert st13["repos"] == {}, \
            "skipped rounds must not write seen (next round re-reports; " \
            "prefer duplicates over lost events): %s" % st13["repos"]
        # once-mode contrast (re-checking the existing [8] vector): canned
        # 401 still fails loudly with rc 9
        emit13b = os.path.join(tmp, "events13b.jsonl")
        p = run(["--once", "--watch-repo", REPO, "--injector", p401,
                 "--state-file", os.path.join(tmp, "state13b.json"),
                 "--emit", emit13b, "--sleep-scale", "0"])
        assert p.returncode == 9, "once with the same shape should keep " \
            "fail-loud rc=9, got %d" % p.returncode
        evs13b = [json.loads(l) for l in io.open(emit13b, encoding="utf-8")
                  if l.strip()]
        assert len(evs13b) == 1 and evs13b[0]["kind"] == "sentinel-error" \
            and evs13b[0]["code"] == 9, evs13b

        # [15] deployment-shape smoke test (supervisor shell
        # examples/sentinel_supervisor.sh; static assertions, not a real
        # run): bash -n parses without executing + key-line grep assertions that
        # verify the deployment artifact is in the repository with its
        # structure present point by point (restart cap / backoff / state
        # continuation note / withdraw hook left empty / guard position /
        # rc triage / three-artifact placement names / path parameterization
        # with zero hardcoded absolute paths). Zero execution, zero network.
        sup_sh = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.pardir, "examples", "sentinel_supervisor.sh"))
        assert os.path.isfile(sup_sh), \
            "supervisor deployment script missing: %s" % sup_sh
        p = subprocess.run(["bash", "-n", sup_sh],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out14 = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        assert p.returncode == 0, "bash -n syntax check should pass with " \
            "rc=0: %s" % out14[-300:]
        sup_text = io.open(sup_sh, encoding="utf-8").read()
        assert sup_text.startswith("#!/bin/bash"), \
            "the deployment shape should start with a bash shebang"
        for tok in (
                "SUPERVISOR_MAX_RESTARTS", "restart budget exhausted",   # restart cap
                "SUPERVISOR_BACKOFF_BASE", "SUPERVISOR_BACKOFF_MAX",
                "backoff",                                               # backoff
                "--state-file", "state continuation",                    # state continuation note
                "state.json", "events.jsonl", "report.json",             # three-artifact placement names
                "supervisor_withdraw_hook",                              # withdraw hook (empty form asserted separately)
                "SENTINEL_GUARD", "cpu_guard",                           # guard position
                "tools/cw_sentinel.py", "--loop",                        # sentinel subcommand
                "rc=2 usage error",                                      # rc triage (usage errors do not enter the restart loop)
        ):
            assert tok in sup_text, "supervisor shell key line missing: %r" \
                % tok
        assert re.search(r"supervisor_withdraw_hook\(\) \{\n  return 0",
                         sup_text), "the withdraw hook should be left " \
            "empty (default body return 0; the deployer fills it as needed)"
        assert "/Users/" not in sup_text, \
            "the deployment shape forbids hardcoded absolute paths (path " \
            "parameterization rule): /Users/ hit"
        # local bash 3.2 precedent (captured by the deployment-shape
        # functional smoke test): a bare $VAR followed directly by a
        # full-width character gets swallowed into the variable name →
        # under set -u an unbound variable crash (real crash shape
        # "rc=$RC)"); structural rule asserted here: bare $VAR must always
        # be ${} -braced (any directly following non-ASCII byte is a
        # violation)
        m_cjk = re.search(r"\$([A-Za-z_][A-Za-z0-9_]*)[^\x00-\x7F]", sup_text)
        assert m_cjk is None, \
            "bare $%s directly followed by a full-width character = bash " \
            "3.2 variable-name swallow crash; must be ${} -braced" \
            % (m_cjk.group(1) if m_cjk else "")

        print("CW-SENTINEL-SELFTEST PASS: (1)once ci-red + second round "
              "seen idempotent zero events/"
              "(2)ledger new file blocking + idempotent/"
              "(3)buildlog incremental grep + no half-line false positive/"
              "(4)on-red placeholder-substitution execution proof + default "
              "zero action/(5)loop three rounds JSONL sequential/"
              "(6)emit line-by-line valid sort_keys + seq sequential/"
              "deterministic byte-identical/CLI four exit codes+"
              "401→9+canned non-coverage→9+missing directory→9/"
              "(9)on-red-preset expansion+trigger capture+mutual exclusion "
              "rc=2+argument errors rc=2+"
              "plain without --emit rc=2 (both paths share the guard; "
              "preset regression)/"
              "(13)preset-table extension (wash-shape/triage/cw-doctor "
              "placeholder substitution; triage repo/run event-substitution "
              "family; missing required/unknown key/empty surface rc2; "
              "chained two-preset expansion, chain-wide union surface; "
              "chained trigger in order, continue after one fails, "
              "rc=9→rc=0, two entries logged)/"
              "(10)resilience backoff (403x3→[2,4,8]; Retry-After honored; "
              "503 exhaustion 9; 401 not retried; canned sleep subprocess "
              "killed on timeout with 9 naming the call)/"
              "(11)state crash recovery (corrupted refused with 9, no "
              "silent rebuild, original untouched; --rebuild-state explicit "
              "rebuild reproduces the failing event; missing --state-file "
              "rc=2)/"
              "(12)emit rotation (--emit-max-bytes rotates before append "
              "when over the cap; .1/.2 keep two generations; seq continues "
              "across generations; missing --emit/N<1 rc=2)/"
              "(14)transport-layer transient disconnects (canned "
              "IncompleteRead read-function injection; first two attempts "
              "fail, third succeeds with backoff [5,15]; "
              "RemoteDisconnected/BadStatusLine/socket.timeout all "
              "retryable; exhaustion 9 with backoff sequence [5,15,45] "
              "asserted; --net-retries cap adjustable; non-transient/"
              "URLError fail fast with zero swallowing and zero sleeping; "
              "loop per-source skip source-error note rc0, skip a round "
              "rather than crash the run, seen untouched; once with the "
              "same shape still 9)/"
              "(15)deployment-shape smoke test (supervisor shell "
              "examples/sentinel_supervisor.sh; bash -n syntax check + "
              "key-line grep assertions: restart cap/backoff/state "
              "continuation note/withdraw hook empty return 0/guard "
              "position/rc triage/three-artifact placement names/zero "
              "hardcoded absolute paths"
              "; static assertions, not a real run, zero execution, zero "
              "network) ALL PASS")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
