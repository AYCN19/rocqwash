#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ci_triage.py — failing-build triage tool for rocqwash CI (tools/).

Purpose.  Triages the jobs of a GitHub Actions run into failing and
  passing: prints a step-level table (step name/status/conclusion/start/
  end/duration in seconds), assigns each job a family from the five-family
  classification taxonomy plus the all-passing state, and prescribes an
  action; with --baseline-seconds given a historical duration for the same
  sync, prints a ratio table (example: coqchk 561s vs 7480s = 13.3x — a
  likely local resource squeeze, not a hang).  A failing result is data,
  not a tool failure: triage always exits 0 and reports the outcome
  explicitly on stdout.  Dry run by default in the network sense: online
  mode issues read-only GETs only.

Interface.  python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs]
  [--netrc PATH] [--baseline-seconds N] [--baseline-step NAME]
  [--timeout S] [--retry-max N] [--json out.json] (online, read-only GET)
  | --offline JOBS.json [...] (offline; canned API-shaped jobs JSON; zero
  network) | --selftest.  Report schema rocqwash-ci-triage/1 (--json,
  sort_keys).  The full classification taxonomy, the usage block, the
  report schema detail and the honesty rules live in the extended
  contract below.

Dependencies.  Python 3 standard library only; zero third-party
  dependencies; the shared retry helpers come from the same-directory
  tools/_http_backoff.py (sys.path injection, no __init__ package
  layout).  The online token is read from the ~/.netrc machine github.com
  line's 6th-column password field (--netrc selects another path); the
  token is never echoed.

Evidence.  --selftest frozen vectors on offline fixtures (zero real
  network, zero compiles): the six canned family samples, the 13.3x
  baseline example plus the loud absent-step note, classifier units
  (regex positives/negatives, cascade/in-flight/UNRECOGNIZED routing),
  netrc parsing, byte-identical determinism, CLI four codes, the backoff
  layer (403x3 -> [2,4,8], Retry-After honored, exhausted -> raise, 401
  no-retry, _open/_sleep injection), the Main-shape reading vector
  (coq93.yml real step names x the five-family compatibility table), the
  gate2-only E-variant vectors (the token dichotomy acceptance line),
  dump-line filtering vectors, the five-token roster vector, job_logs
  malformed fail-loud, and the two-hop logs-415 fix vector; suite
  membership tests/test_ci_triage.py.

Exit-codes.  0 = triage completed (a failing verdict is data, not a tool
  error; reported explicitly on stdout); 2 = usage error (missing /
  mutually exclusive / malformed arguments); 9 = API or file unreachable,
  or malformed (netrc missing, empty token, HTTP 4xx/5xx, connection
  failure, jobs file missing or malformed JSON, unrecognized timestamp
  shape).  --selftest: 0 = all vectors pass / 2 = assertion failure.

[Classification taxonomy] — five failure families plus the all-passing state:
  A content failure (A-content-red) = the failing step points at concrete
    content: Build/COQCHK emits Error:/FAIL/ORDER-MISSING, or COQCHK exits
    nonzero (COQCHK_EXIT≠0, nonzero axiom total) → action=fix-content.
  B network window (B-netred) = checkout unable to access / port 443 /
    Connection was reset; upload-step ENOTFOUND / Upload progress stalled;
    403 Forbidden: job is completed. (Cancellation cascade: a cancelled job
    that has steps but zero failed steps also lands here.)
    → action=rerun-after-stable-window.
  C toolchain break (C-toolchain-break) = wholesale EXIT=134 / Abort trap: 6
    while every SKIP-marked file passes. Direct log evidence: the log contains
    EXIT=134 / Abort trap: 6 → the job is C. Run-level bulk rule: when two or
    more jobs show the same content-failure pattern (A), all are upgraded to C
    (confirm EXIT=134 via --logs) → action=restore-toolchain.
  D queue-resource wall (D-queue-wall) = cancelled with steps=[] (a job with
    zero steps; its logs 404) → action=queue-etiquette.
  E coqchk-skipped signature (E-coqchk-skipped) = the upload step failed and
    the coqchk step was skipped (with GATE-BANNER-ABSENT confirmable from the
    log) — a variant of family B; do not treat it as a content failure
    → action=rerun-after-stable-window.
  E variant (gate2-only cascade, banner-absent-restricted form) = the
    failed-step set is a subset of {gate2 + upload family} and at least one
    pure-gate2 failed step exists (a gate2 step name that is not an upload
    name — this guards against "Upload artifact (gate2 ledger)" being counted
    as a pure gate2 red through the gate2 substring), and the preceding
    build/coqchk steps are not content failures. Conclusion-position
    validation (judged on genuinely executed log lines after dump-line
    filtering):
    ① a genuinely executed GATE2-ATTEST-RED / 判定=CLEAN token is present =
       attested-red shape (the coqchk step completed with parser CLEAN and
       zero axioms) → the E variant does not hold; the job stays UNRECOGNIZED
       (manual identification takes precedence);
    ② the coqchk step succeeded = it ran to completion, so the "coqchk
       artifacts missing" cascade mechanism does not apply (the only
       corroborating signal when no log is available) → likewise stays
       UNRECOGNIZED;
    ③ a genuinely executed GATE-BANNER-ABSENT line is present = the
       banner-absent cascade applies (coqchk skipped/cancelled);
    ④ no log available and coqchk did not complete = the step-name rule keeps
       E (banner token unconfirmed; noted as such).
    → family=E-coqchk-skipped, action=rerun-after-stable-window. The
    run-level precedence order UNRECOGNIZED>C>A>E>B>D is unchanged (the E
    variant lives inside E).
  All passing = no failed jobs → family=none, action=watch-only. In-progress or
    conditionally skipped jobs (empty conclusion, or skipped/neutral) are also
    recorded as none, but the evidence explicitly notes "classification
    deferred, not a passing verdict" — they are never counted as passing.
  Failure shapes outside the taxonomy → family=UNRECOGNIZED, action=watch-only
    (never force-fitted into the taxonomy; takes top precedence at run level;
    manual log identification first; fail-loud).
  Maintained-UNRECOGNIZED evidence-package shapes (family unchanged, evidence
    enhanced only — never a reclassification; token-level ground truth per the
    review ledger, 复核台账 §二 S3/S6, §四-2/§四-3):
    ① runner-lost candidate = job failure + zero failed steps + a build-family
       step still hung (status=in_progress, conclusion=null) + a logs-GET
       HTTP 404 note (the log blob was never uploaded) → evidence notes
       "runner-lost-candidate"; the D shape (cancelled + zero steps) does not
       cover it and no family is assigned;
    ② attested-red auth-state = genuinely executed GATE2-ATTEST-RED +
       判定=CLEAN (dump-line-filtered) inside the gate2-only shape → evidence
       note "auth-state-red-maintained" with the UNREC maintained rationale
       auto-attached (the E gate2-only cascade variant does not hold for
       attested-red shapes).
    Both stay family=UNRECOGNIZED (manual identification first; no force-fit).
  Evidence-annihilation candidate note (R19; docs/ci-triage-table.json v1.5
    row; family unchanged, evidence enhanced only, fired on any family before
    the family branches): a log capture channel that engaged (log text was
    fetched/injected) and holds zero evidence bytes in its raw form (empty or
    whitespace-only) while every step recorded its conclusion ("rc recorded,
    log/output bytes = 0") - the capture mechanism is the disease, not the
    tool; log_text=None (no fetch) never fires the note, a failed fetch is
    the log_note channel (a different shape) and never fires it, and a log
    holding only dump/telemetry lines has bytes, so it is the dump-filter
    trap shape, not this note.

  Classification precedence (per job, first match wins): passing / in-progress /
    conditionally skipped → D (cancelled, zero steps) → B cascade (cancelled,
    has steps, zero failed steps) → direct-log C (EXIT=134 / Abort trap: 6) →
    E signature (upload-step red + coqchk skipped) → E variant (gate2-only
    cascade: failed-step set ⊆ {gate2+upload}, build/coqchk not content red,
    banner-absent-restricted — attested-token and coqchk-completed shapes stay
    UNRECOGNIZED) → log B → step-name B (checkout/upload/artifact/cache/…) →
    log A (Error:/FAIL/ORDER-MISSING/COQCHK_EXIT≠0/nonzero axiom total) →
    step-name A (build/compile/coqchk/…) → UNRECOGNIZED.

Extended contract (kept below the five-field block per the annotation
standard 30-line header budget).

Usage (all paths parameterized; zero hardcoded absolute paths):
  Online mode (read-only GET; the token is taken from the ~/.netrc machine
  github.com line's 6th-column password field; --netrc selects another path):
    python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs] [--netrc PATH]
        [--baseline-seconds N] [--baseline-step NAME] [--timeout S]
        [--retry-max N] [--json out.json]
    (GET /repos/{repo}/actions/runs/{run}/jobs?per_page=100&page=N, paginated
      to completion; with --logs, each failed job is additionally fetched via
      GET /repos/{repo}/actions/jobs/{job}/logs and key lines are recorded as
      evidence: COQCHK_EXIT / COQCHK_ALL_PASS / 判定=CLEAN / 公理总数 /
      GATE-BANNER-ABSENT / GATE2-ATTEST-RED / R4 覆盖划分 / appendix 缺 /
      ENOTFOUND / ORDER-MISSING / EXIT=134 and others. Dump-line filtering:
      evidence collection and token search first drop ANSI-cyan script echo
      lines ([36;1m) and ##[group]/##[endgroup] group-directive lines — script
      echo is not a real execution line, so "log confirmation" must be a real
      execution line (the filter rule is noted as-is: the number of dropped
      lines enters evidence); --no-dump-filter disables it (trap shapes then
      enter evidence verbatim, with an explicit run-level note). Two-hop log
      fetch (determined by probing): hop 1 sends Accept:
      application/vnd.github+json (text/plain is now rejected with 415) with
      automatic redirects disabled → 302 Location signed URL; hop 2 GETs the
      signed URL with no Authorization header (the signature carries the
      credentials — forwarding the token yields 403 Azure
      AuthenticationFailed). A logs GET 404/403/415 itself enters evidence —
      403 Forbidden: job is completed is a family-B cancellation-cascade
      token; after retries are exhausted the original status code enters
      evidence as before.)
  Resilience layer (rate-limit backoff): an online GET that meets 403/429/5xx
    retries with exponential backoff (base 2s, cap --retry-max default 3; a
    parseable Retry-After second count replaces the current exponential delay;
    an HTTP-date form is not guessed and falls back to exponential; when
    retries are exhausted, or on 4xx semantic errors (401/404 etc.), the
    original error propagates as 9 with no retry). Delay computation lives in
    the tools/_http_backoff.py pure functions backoff_delays()/
    parse_retry_after()/is_retry_status() (shared by three tools; imported by
    same-directory sys.path injection; no __init__ package layout).
  Offline mode (used by --selftest and in air-gapped environments; zero
  network):
    python3 tools/ci_triage.py --offline JOBS.json [--baseline-seconds N ...]
        [--no-dump-filter] [--json out.json]
    (canned jobs JSON in the same shape as the real API
      {"total_count":N,"jobs":[...]}, plus two optional top-level extensions,
      neither a real API shape and both noted as such: job_logs
      {"<job_id>": "log text"} dedicated to offline log injection, and
      job_log_notes {"<job_id>": "log-fetch note text"} dedicated to offline
      injection of the logs-GET evidence notes (the offline counterpart of
      the online fetch_job_log note path). Fixtures:
      tests/fixtures/ci_triage_*.json — the six-file set, plus one main-shape
      coq93 real-form file ci_triage_main_coq93.json (a single Windows job
      "Main CI 9.3", 16 real step names, passing sample), two gate2-only
      real-form files ci_triage_gate2_only_{cancelled,failure}.json, and one
      runner-lost real-form file ci_triage_runner_lost.json (Main#3 real
      form: single job, conclusion=failure with zero failed steps, the build
      step hung in_progress, canned logs-GET HTTP 404 note) — ten files in
      total.)
  python3 tools/ci_triage.py --selftest

Report schema (--json) = rocqwash-ci-triage/1:
  {"schema","mode","source",
   "run"{repo,run_id,total_count,jobs_total,red_job_ids,family,action,evidence},
   "jobs"[{id,name,status,conclusion,started_at,completed_at,duration_sec,
     "steps"[{number,name,status,conclusion,started_at,completed_at,duration_sec}],
     "classification"{family,action,evidence,red_steps}}],
   "family","action","evidence","baseline_note"?}
  family ∈ A-content-red / B-netred / C-toolchain-break / D-queue-wall /
    E-coqchk-skipped / none / UNRECOGNIZED;
  action ∈ rerun-after-stable-window / fix-content / restore-toolchain /
    queue-etiquette / watch-only;
  baseline_note (present only with --baseline-seconds): {applied,step_query,
    baseline_seconds,matched?,current_seconds?,ratio?,note|reason}
    (applied=false = the baseline step is absent or unfinished — reported
    explicitly, never silently; rc is still 0).

Honesty rules (per CONTRIBUTING §0): accept only mechanical evidence; never
  force-fit shapes outside the taxonomy; a failing result is data, not a tool
  failure (triage exits 0); --json is written sorted with sort_keys so reruns on
  the same input are byte-identical; stdout is fully data-driven (no now(), no
  randomness); zero third-party dependencies (pure stdlib); fail-loud, no
  silent degradation.
"""
import argparse
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

PROG = "ci_triage"
SCHEMA = "rocqwash-ci-triage/1"
API_ROOT = "https://api.github.com"
# logs-endpoint Accept value fixed by live probing (the 415 fix): text/plain is
# now rejected with 415 (verbatim body {"message":"Unsupported 'Accept' header:
# 'text/plain'. Must accept 'application/json'. ..."}); application/vnd.github+json
# -> 302 Location signed URL; the second hop sends zero Authorization against the
# signed URL -> 200 with the real log body; forwarding the token -> 403 Azure
# AuthenticationFailed (the contrast probe, proving the two-hop zero-auth
# necessity).  KEEP (data face): the token strings below are the frozen CI logs'
# own vocabulary and stay verbatim.
LOGS_ACCEPT = "application/vnd.github+json"
REDIRECT_CODES = (301, 302, 303, 307, 308)   # signed-URL redirect family (two-hop manual continuation)

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)   # same-directory shared backoff module (no __init__ package layout)
import _http_backoff

# ---- classification-taxonomy word faces (frozen vectors; positive/negative judging in --selftest) ----

# log key-line harvesters (tag, regex) — a hit line enters evidence verbatim
# (<=200 chars, dedup preserving order, cap 60).  KEEP (data faces): every tag
# and regex below parses the frozen CI logs' own output vocabulary — the
# review-ledger five-token roster (GATE2-ATTEST-RED / R4 coverage split /
# appendix missing added; 判定=CLEAN / 公理总数 already rostered) — and must
# never be rewritten.
KEY_LOG_PATTERNS = [
    ("COQCHK_EXIT", re.compile(r"COQCHK_EXIT=(-?\d+)")),
    ("COQCHK_ALL_PASS", re.compile(r"COQCHK_ALL_PASS=(\d+)")),
    ("判定=CLEAN", re.compile(r"判定=CLEAN")),
    ("公理总数", re.compile(r"公理总数=(\d+)")),
    ("GATE-BANNER-ABSENT", re.compile(r"GATE-BANNER-ABSENT")),
    ("GATE2-ATTEST-RED", re.compile(r"GATE2-ATTEST-RED")),
    ("R4-覆盖划分", re.compile(r"R4 覆盖划分")),
    ("APPENDIX-缺", re.compile(r"appendix 缺|appendix=\{present:false\}")),
    ("ORDER-MISSING", re.compile(r"ORDER-MISSING")),
    ("ENOTFOUND", re.compile(r"ENOTFOUND")),
    ("EXIT=134", re.compile(r"EXIT=134")),
    ("Abort-trap-6", re.compile(r"Abort trap: 6")),
    ("NET-ACCESS", re.compile(r"unable to access|port 443|Connection was reset")),
    ("UPLOAD-STALL", re.compile(r"Upload progress stalled")),
    ("JOB-COMPLETED-403", re.compile(r"403 Forbidden: job is completed")),
    ("Error", re.compile(r"\bError:")),
]

# family-judging regexes (direct log evidence)
RED_CONTENT_RE = re.compile(
    r"\bError:|ORDER-MISSING|(?<![A-Za-z])FAIL(?![A-Za-z])"
    r"|COQCHK_EXIT=(?!0\b)\d+|公理总数=(?!0\b)\d+")
RED_NET_RE = re.compile(
    r"unable to access|port 443|Connection was reset|ENOTFOUND"
    r"|Upload progress stalled|403 Forbidden: job is completed")
RED_ABORT_RE = re.compile(r"EXIT=134|Abort trap: 6")
GATE_BANNER_ABSENT_RE = re.compile(r"GATE-BANNER-ABSENT")
# gate2-only shape conclusion-position validation token (the review-ledger
# token dichotomy; the attested-red auth-state criterion): a genuinely executed
# GATE2-ATTEST-RED line (17:18:53Z) or 判定=CLEAN parser verdict line (17:18:52Z)
# on the roster means the auth-state shape holds and the E variant does not —
# the job stays UNRECOGNIZED, never force-fitted.
GATE2_ATTEST_RE = re.compile(r"GATE2-ATTEST-RED|判定=CLEAN")
# attested-red auth-state pair detection (maintained-UNREC evidence notes):
# the auth-state-red-maintained note fires only when both tokens are
# genuinely present on dump-filtered log text; a single token keeps the
# plain gate2 exclusion note (the E-variant exclusion condition itself is
# unchanged — evidence enhancement only, no classification change)
GATE2_ATTEST_RED_RE = re.compile(r"GATE2-ATTEST-RED")
GATE2_CLEAN_RE = re.compile(r"判定=CLEAN")
# coqchk-step-completed criterion (the review-ledger second discriminator; the
# run#10 form coqchk success 40398s = not the "artifacts missing" cascade
# mechanism): only a step NAME starting with coqchk counts — this blocks the
# "gate5 vo-binary quarantine (pre-coqchk...)" / "Upload coqchk logs" coqchk
# substring free-ride from misreading completion (the same free-ride reef rule
# as the survey doc §3.1 / retro §2.3-1).
COQCHK_DONE_RE = re.compile(r"(?i)^coqchk")
# dump/telemetry line filtering (the review-ledger evidence trap): GitHub step
# logs echo the whole script in cyan ([36;1m...[0m, ESC form or literal residue)
# plus ##[group]/##[endgroup] group-directive lines — a script echo is not a
# real execution line (the run#10 form: the banner-absent branch never actually
# ran; only the dump line exists), so "log confirmation" must be a real
# execution line.  The filter rule is noted as-is (the dropped-line count enters
# evidence); --no-dump-filter disables it (the trap shape then enters evidence
# verbatim with a run-level loud note).
DUMP_LINE_RE = re.compile(r"\[36;1m|##\[(?:group|endgroup)\]")

# step-name family regexes (step-level inference; the fallback judging face when no log is available)
CONTENT_STEP_RE = re.compile(r"(?i)build|compile|coqchk|coqc|rocq|check|verify|make")
NET_STEP_RE = re.compile(r"(?i)checkout|upload|artifact|cache|download|publish")
UPLOAD_STEP_RE = re.compile(r"(?i)upload|artifact")
COQCHK_STEP_RE = re.compile(r"(?i)coqchk")
GATE2_STEP_RE = re.compile(r"(?i)gate2")   # gate2-only cascade shape criterion word (a pure
# gate2 red step = GATE2 matches and UPLOAD does not — the "Upload artifact
# (gate2 ledger)" gate2 substring free-ride does not count as pure gate2, so an
# upload red is never swallowed; the combined criterion lives in the classify
# E-variant branch)

RED_STEP_CONCLUSIONS = ("failure", "timed_out")

# family -> action (the taxonomy disposition table)
ACTION_OF = {
    "A-content-red": "fix-content",
    "B-netred": "rerun-after-stable-window",
    "C-toolchain-break": "restore-toolchain",
    "D-queue-wall": "queue-etiquette",
    "E-coqchk-skipped": "rerun-after-stable-window",
    "none": "watch-only",
    "UNRECOGNIZED": "watch-only",
}

FAMILY_LABEL = {
    "A-content-red": "content red",
    "B-netred": "network window",
    "C-toolchain-break": "toolchain break",
    "D-queue-wall": "queue resource wall",
    "E-coqchk-skipped": "coqchk-skipped signature (family-B variant)",
    "none": "passing / no red",
    "UNRECOGNIZED": "unrecognized red shape outside the taxonomy",
}

# run-level classification precedence (first match wins): out-of-taxonomy red shapes go first (manual identification takes precedence; never shadowed by a recognized family)
RUN_FAMILY_PRECEDENCE = ["UNRECOGNIZED", "C-toolchain-break", "A-content-red",
                         "E-coqchk-skipped", "B-netred", "D-queue-wall"]

BASELINE_SQUEEZE_RATIO = 3.0   # ratio >= this threshold -> "likely a local resource squeeze, not a hang" (the 13.3x example is far above)
LOG_EVIDENCE_CAP = 60          # per-job log evidence line cap
LOGS_FETCH_CAP = 20            # --logs red-job log fetch count cap (over-cap noted loudly)


class TriageError(Exception):
    """fail-loud exception carrying an exit code (code: 2 = usage error; 9 = API/file unreachable or malformed)."""

    def __init__(self, msg, code=9):
        super(TriageError, self).__init__(msg)
        self.code = code


class ApiHTTPError(Exception):
    """HTTP error of a read-only GET (the body head is carried; the caller decides whether it becomes a 9 or enters evidence)."""

    def __init__(self, code, body, url):
        super(ApiHTTPError, self).__init__("HTTP %d: %s" % (code, url))
        self.code = code
        self.body = body or ""
        self.url = url


# ---- time and duration ----

def parse_iso(ts):
    """ISO8601 -> aware datetime (UTC default); empty/None -> None; unrecognized shape -> fail-loud 9."""
    if ts is None:
        return None
    t = str(ts).strip()
    if not t:
        return None
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = None
    try:
        dt = datetime.datetime.fromisoformat(t)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(t, fmt)
                break
            except ValueError:
                pass
    if dt is None:
        raise TriageError("unrecognized time shape: %r" % ts, 9)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def duration_sec(started_at, completed_at):
    """Start/end -> whole seconds (None/unfinished -> None; negatives clamp to 0)."""
    s = parse_iso(started_at)
    e = parse_iso(completed_at)
    if s is None or e is None:
        return None
    return max(0, int(round((e - s).total_seconds())))


def fmt_dur(sec):
    if sec is None:
        return "-"
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%dh%02dm%02ds" % (h, m, s)
    return "%dm%02ds" % (m, s)


# ---- credentials (netrc machine github.com, 6th column) ----

def netrc_token(path, machine="github.com"):
    """Manual netrc parsing: machine <m> login <l> password <p> (both the
    single-line 6-column form and the multi-line form) -> the password token.
    Missing file / no entry / empty value -> fail-loud 9 (the token is never
    echoed)."""
    if not os.path.isfile(path):
        raise TriageError("netrc missing: %s (online mode needs machine %s ..."
                          " password credentials)" % (path, machine), 9)
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
                    raise TriageError("netrc machine %s password is empty" % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise TriageError("netrc has no machine %s password entry (single-line 6-column"
                      " form: the 6th column is the token): %s" % (machine, path), 9)


# ---- read-only GET (the only network action) ----

def http_get(url, token, timeout, accept="application/vnd.github+json",
             retry_max=3, _open=None, _sleep=None):
    """Read-only GET -> bytes.  403/429/5xx retry with exponential backoff (the
    _http_backoff pure functions: base 2s, cap retry_max; a parseable
    Retry-After second count replaces that attempt's delay); exhausted retries
    or 4xx semantic errors raise the original error — HTTPError becomes
    ApiHTTPError (body head carried); connection failure -> 9.  _open/_sleep
    are injection points (selftest zero-network vectors; defaults are the real
    urlopen/real sleep)."""
    do_open = urllib.request.urlopen if _open is None else _open
    do_sleep = time.sleep if _sleep is None else _sleep
    delays = _http_backoff.backoff_delays(retry_max)
    attempt = 0
    while True:
        req = urllib.request.Request(url, headers={
            "Accept": accept,
            "User-Agent": "rocqwash-ci-triage",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "token %s" % token,
        })
        try:
            with do_open(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if attempt >= retry_max or not _http_backoff.is_retry_status(e.code):
                try:
                    body = (e.read() or b"").decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                raise ApiHTTPError(e.code, body, url)
            ra = _http_backoff.parse_retry_after(
                e.headers.get("Retry-After") if e.headers is not None else None)
            do_sleep(ra if ra is not None else delays[attempt])
            attempt += 1
        except (urllib.error.URLError, OSError) as e:
            raise TriageError("API unreachable: %s (%s)" % (url, e), 9)


def jobs_url(repo, run_id):
    return "%s/repos/%s/actions/runs/%d/jobs" % (API_ROOT, repo, run_id)


def fetch_jobs_online(repo, run_id, token, timeout, retry_max=3):
    """GET jobs (per_page=100, paginated to completion) -> (jobs, total_count).
    HTTP 4xx/5xx -> 9 (403/429/5xx first go through http_get exponential
    backoff; only exhaustion judges 9)."""
    jobs = []
    total = None
    page = 1
    while True:
        url = "%s?per_page=100&page=%d" % (jobs_url(repo, run_id), page)
        data = json.loads(http_get(url, token, timeout,
                                   retry_max=retry_max).decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise TriageError("API malformed (no jobs list): %s" % url, 9)
        if total is None:
            total = data.get("total_count")
        jobs.extend(data["jobs"])
        if len(data["jobs"]) < 100:
            break
        if total is not None and len(jobs) >= total:
            break
        page += 1
        if page > 50:
            raise TriageError("jobs pagination over cap (50 pages); refusing to fetch further", 9)
    return jobs, (total if total is not None else len(jobs))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Auto-redirect-disabled handler (a 302 raises as HTTPError so fetch_job_log
    can continue the two hops manually — urllib's default forwarding carries the
    Authorization header onto the signed URL, the live-probed 403
    AuthenticationFailed from Azure; the two-hop zero-auth second hop is the
    fix)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _logs_error_note(e):
    """logs HTTPError -> an evidence note (body head 120 chars; the original status code on the roster; same note form as before)."""
    try:
        body = (e.read() or b"").decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return "logs-GET: HTTP %d %s (log unreachable; enters evidence)" % (
        e.code, body.strip()[:120])


def fetch_job_log(repo, job_id, token, timeout, retry_max=3, _open=None,
                  _sleep=None):
    """GET one job's raw log -> (text, None); HTTP 4xx/5xx -> (None, evidence
    note).

    Two-hop log fetch (the live-probed 415 fix): hop 1 GETs the logs endpoint
    (Accept: application/vnd.github+json — text/plain is now rejected with 415;
    auto-redirects disabled via the _NoRedirect opener) -> 302 Location signed
    URL; hop 2 GETs the signed URL with zero Authorization (the signature
    carries the credentials — urllib's default redirect forwarding sends the
    token and gets 403 Azure AuthenticationFailed, live-probed).  403/429/5xx
    on hop 1 retry with exponential backoff (same _http_backoff; a
    Retry-After second count is honored; exhaustion lands in the evidence
    note); 404/415 and other semantic errors do not retry and enter evidence
    with the original status code; a failed hop 2 lands in the evidence note
    without retrying; connection failure stays TriageError 9 (API
    unreachable).  _open/_sleep are injection points (selftest zero-network
    vectors; defaults are the real opener/real sleep)."""
    url = "%s/repos/%s/actions/jobs/%s/logs" % (API_ROOT, repo, job_id)
    do_open = _open
    if do_open is None:
        do_open = urllib.request.build_opener(_NoRedirect).open
    do_sleep = time.sleep if _sleep is None else _sleep
    delays = _http_backoff.backoff_delays(retry_max)

    def _request(u, with_auth):
        headers = {
            "Accept": LOGS_ACCEPT,
            "User-Agent": "rocqwash-ci-triage",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if with_auth:
            headers["Authorization"] = "token %s" % token
        return urllib.request.Request(u, headers=headers)

    attempt = 0
    while True:
        try:
            with do_open(_request(url, True), timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace"), None
        except urllib.error.HTTPError as e:
            if e.code in REDIRECT_CODES:
                loc = e.headers.get("Location") if e.headers is not None \
                    else None
                if not loc:
                    return None, ("logs-GET: HTTP %d no Location (redirect"
                                  " malformed)") % e.code
                try:
                    with do_open(_request(loc, False),
                                 timeout=timeout) as r2:
                        return r2.read().decode(
                            "utf-8", errors="replace"), None
                except urllib.error.HTTPError as e2:
                    return None, _logs_error_note(e2)
            if attempt < retry_max and _http_backoff.is_retry_status(e.code):
                ra = _http_backoff.parse_retry_after(
                    e.headers.get("Retry-After")
                    if e.headers is not None else None)
                do_sleep(ra if ra is not None else delays[attempt])
                attempt += 1
                continue
            return None, _logs_error_note(e)
        except (urllib.error.URLError, OSError) as e:
            raise TriageError("API unreachable: %s (%s)" % (url, e), 9)


# ---- offline loading ----

def load_jobs_offline(path):
    """Canned jobs JSON -> (jobs, total, job_logs, job_log_notes).  Same shape
    as the real API {"total_count":N,"jobs":[...]} plus two optional top-level
    extensions (neither a real API shape; both noted as such): job_logs
    {"<job_id>": "log text"} (offline log injection — the canned channel for
    the review-ledger token-dichotomy acceptance verdicts) and job_log_notes
    {"<job_id>": "log-fetch note text"} (offline fetch-note injection — the
    offline counterpart of the online fetch_job_log evidence-note channel);
    numeric keys normalize to int to join job.id.  Missing file / parse
    failure / malformed shape (bad jobs shape; job_logs or job_log_notes not
    {str: str}) -> fail-loud 9."""
    if not os.path.isfile(path):
        raise TriageError("jobs JSON missing: %s" % path, 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise TriageError("jobs JSON malformed (parse failure): %s (%s)" % (path, e), 9)
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise TriageError(
            "jobs JSON malformed (need {\"total_count\":N,\"jobs\":[...]} in the"
            " real API shape): %s" % path, 9)
    for idx, j in enumerate(data["jobs"]):
        if not isinstance(j, dict) or not isinstance(j.get("name"), str) \
                or not isinstance(j.get("steps") or [], list):
            raise TriageError("jobs JSON malformed (jobs[%d] is not a job shape): %s" % (idx, path), 9)
    logs_raw = data.get("job_logs") or {}
    if not isinstance(logs_raw, dict) or any(
            not isinstance(v, str) for v in logs_raw.values()):
        raise TriageError(
            "jobs JSON malformed (job_logs must be the {\"<job_id>\": \"log"
            " text\"} extension shape): %s" % path, 9)
    notes_raw = data.get("job_log_notes") or {}
    if not isinstance(notes_raw, dict) or any(
            not isinstance(v, str) for v in notes_raw.values()):
        raise TriageError(
            "jobs JSON malformed (job_log_notes must be the {\"<job_id>\":"
            " \"log-fetch note\"} extension shape): %s" % path, 9)
    logs = {}
    for k, v in logs_raw.items():
        try:
            logs[int(k)] = v
        except (TypeError, ValueError):
            logs[k] = v
    notes = {}
    for k, v in notes_raw.items():
        try:
            notes[int(k)] = v
        except (TypeError, ValueError):
            notes[k] = v
    return (data["jobs"], data.get("total_count", len(data["jobs"])),
            logs, notes)


# ---- classifier ----

def filter_dump_lines(text):
    """Raw log text -> the text with dump/telemetry lines dropped (the
    review-ledger evidence trap).

    Filter rule (noted as-is; DUMP_LINE_RE): cyan script echo lines ([36;1m,
    ESC form or literal residue) plus ##[group]/##[endgroup] group-directive
    lines — a script echo is not a real execution line; in the run#10 form the
    banner-absent branch never actually ran and only the dump line exists, so
    without filtering a dump line could impersonate a "log confirmation" (the
    S6 evidence trap in its original form).  Real execution lines (mojibake GBK
    run lines / uncolored prefix lines) are all kept.  --no-dump-filter
    disables this (the function then stays out of the chain; the trap shape
    re-enters verbatim)."""
    if not text:
        return text
    return "\n".join(ln for ln in text.splitlines()
                     if not DUMP_LINE_RE.search(ln))


def scan_log_evidence(text, dump_filter=True):
    """Raw log text -> the key-line evidence list (tag + hit line verbatim,
    <=200 chars, dedup preserving order, cap 60).  dump_filter=True (default)
    drops dump/telemetry lines first (cyan script echo / group directives; the
    review-ledger evidence trap — a "log confirmation" must be a real
    execution line)."""
    out = []
    if dump_filter and text:
        text = filter_dump_lines(text)
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        for tag, rx in KEY_LOG_PATTERNS:
            if rx.search(s):
                if len(s) > 200:
                    s = s[:197] + "..."
                out.append("log[%s] %s" % (tag, s))
                break
    seen = set()
    ded = []
    for e in out:
        if e not in seen:
            seen.add(e)
            ded.append(e)
    return ded[:LOG_EVIDENCE_CAP]


def classify(job, log_text=None, dump_filter=True, log_note=None):
    """Per-job taxonomy classification -> {"family","action","evidence",
    "red_steps"} (precedence order in the module docstring; failing step names
    and red steps all enter evidence).  dump_filter=True (default) drops
    dump/telemetry lines from log_text first (cyan script echo / group
    directives; the review-ledger evidence trap — the dropped-line count enters
    evidence loudly, and only the filtered text feeds the criterion search and
    evidence collection).  log_note = the log-fetch note (the online
    fetch_job_log failure note or an offline canned note; it enters the
    evidence face only and never judges a family — the logs-GET 404 criterion
    leg of the runner-lost-candidate shape).  The family-judging face is
    unchanged: the shape notes only enhance evidence (the two
    maintained-UNREC shapes plus the evidence-annihilation candidate note
    (R19); see the module docstring)."""
    ev = []
    status = str(job.get("status") or "")
    conclusion = job.get("conclusion")
    steps = job.get("steps") or []
    red_steps = [s for s in steps
                 if s.get("conclusion") in RED_STEP_CONCLUSIONS]
    red_names = [str(s.get("name") or "(unnamed)") for s in red_steps]

    dump_dropped = 0
    # evidence-annihilation candidate (R19) leg 1, judged on the RAW log form
    # before dump filtering: the capture channel engaged (log_text is not
    # None) and holds zero evidence bytes (empty or whitespace-only).  A log
    # holding only dump/telemetry lines has bytes, so it is the dump-filter
    # trap shape (noted below), not annihilation; log_text=None (no fetch)
    # never fires.
    empty_log = log_text is not None and not log_text.strip()
    if log_text and dump_filter:
        _raw_lines = log_text.splitlines()
        log_text = filter_dump_lines(log_text)
        dump_dropped = len(_raw_lines) - len(log_text.splitlines())

    if conclusion == "success":
        return {"family": "none", "action": "watch-only",
                "evidence": ["conclusion=success (passing)"], "red_steps": []}
    if conclusion is None or status != "completed":
        return {"family": "none", "action": "watch-only",
                "evidence": ["in-flight/unfinished (status=%s conclusion=%s);"
                             " classification deferred, not a passing verdict"
                             % (status or "-", conclusion or "-")],
                "red_steps": []}
    if conclusion in ("skipped", "neutral"):
        return {"family": "none", "action": "watch-only",
                "evidence": ["conclusion=%s (conditionally skipped/neutral; not failing)" % conclusion],
                "red_steps": []}

    ev.append("job conclusion=%s status=%s" % (conclusion, status or "-"))
    for n in red_names:
        ev.append("failure-step: %s" % n)
    if dump_dropped:
        ev.append("dump lines dropped=%d (cyan script echo/group directives;"
                  " not real execution lines; review-ledger evidence trap;"
                  " --no-dump-filter disables)" % dump_dropped)

    # evidence-annihilation candidate note (R19; docs/ci-triage-table.json
    # v1.5 row; family unchanged, evidence enhanced only, fired on any family
    # before the family branches).  Two legs, both required:
    #   1. log/output bytes = 0: the raw injected/fetched log holds zero
    #      evidence bytes (empty_log, judged pre-filter);
    #   2. rc recorded: the job has steps and every step recorded a
    #      conclusion (the outcomes made it to the record while the output
    #      did not).
    # The note never reclassifies (the family branches below judge as usual)
    # and never fires on a failed fetch (the log_note channel: the
    # runner-lost shape, an unreachable log, not an annihilated one).
    if empty_log and steps and all(
            s.get("conclusion") is not None for s in steps):
        ev.append(
            "evidence annihilation candidate (R19): log/output bytes = 0 with"
            " rc recorded (steps: %s) - the capture mechanism is the disease,"
            " not the tool; a zero-byte output with rc recorded is a"
            " structural silent red; fix the capture mechanism then"
            " re-execute (re-running the original batch, not re-signing;"
            " auto_repairable=false)" % ", ".join(
                "%s=%s" % (s.get("name") or "(unnamed)",
                           s.get("conclusion") or "-") for s in steps))

    # D: cancelled with zero steps (the logs-404 shape)
    if conclusion == "cancelled" and not steps:
        ev.append("steps=0 (zero steps); logs-404 shape (the queue-resource-wall example)")
        return {"family": "D-queue-wall", "action": ACTION_OF["D-queue-wall"],
                "evidence": ev, "red_steps": []}
    # B cascade shape: cancelled, has steps, zero red steps
    if conclusion == "cancelled" and not red_steps:
        ev.append("cancelled with steps but zero red steps = the cancellation"
                  " cascade shape (taxonomy B; same family as"
                  " 403 Forbidden: job is completed)")
        return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                "evidence": ev, "red_steps": []}

    # direct-log C: EXIT=134 / Abort trap: 6 (taxonomy C; every SKIP-marked file passes)
    if log_text and RED_ABORT_RE.search(log_text):
        ev.append("direct log evidence: EXIT=134/Abort trap: 6 (taxonomy C; toolchain break)")
        return {"family": "C-toolchain-break",
                "action": ACTION_OF["C-toolchain-break"],
                "evidence": ev + scan_log_evidence(log_text, dump_filter),
                "red_steps": red_names}

    # E signature: upload step red + coqchk step skipped (a family-B variant; never treat as a content failure)
    upload_red = [s for s in red_steps if UPLOAD_STEP_RE.search(str(s.get("name") or ""))]
    coqchk_skipped = [s for s in steps
                      if s.get("conclusion") == "skipped"
                      and COQCHK_STEP_RE.search(str(s.get("name") or ""))]
    if upload_red and coqchk_skipped:
        ev.append("coqchk step skipped = gate2 never reached (the E signature;"
                  " synonymous with GATE-BANNER-ABSENT; confirmable via --logs)")
        if log_text:
            if GATE_BANNER_ABSENT_RE.search(log_text):
                ev.append("log confirmation: GATE-BANNER-ABSENT (the E signature's third leg)")
            ev.extend(scan_log_evidence(log_text, dump_filter))
        return {"family": "E-coqchk-skipped",
                "action": ACTION_OF["E-coqchk-skipped"],
                "evidence": ev, "red_steps": red_names}

    # E variant (the gate2-only cascade shape, banner-absent restricted form;
    # admitted from the manually identified evidence of the six Main retro
    # events plus the review-ledger token dichotomy restriction — the #10
    # false-positive discharge): the red-step set ⊆ {gate2 + upload family} and
    # a pure gate2 red step exists (a gate2 name that is not an upload name —
    # this blocks the "Upload artifact (gate2 ledger)" gate2 substring
    # free-ride from swallowing an upload red), with the preceding
    # build/coqchk steps not content failures (a proper Build/coqchk step name
    # matches neither gate2 nor the upload family, so its presence breaks the
    # subset condition).  Conclusion-position validation (the review-ledger
    # token dichotomy; judged on genuinely executed tokens after dump-line
    # filtering — run#7 job 127903477736's log fetched with HTTP 200 showed a
    # genuinely executed banner-absent line at 13:22:43Z; run#10 job
    # 128320751675's raw log showed genuinely executed 判定=CLEAN(exit 0)
    # 公理总数=0 at 17:18:52Z plus GATE2-ATTEST-RED at 17:18:53Z):
    #   1. a genuinely executed GATE2-ATTEST-RED / 判定=CLEAN token is present =
    #      the attested-red auth-state shape (the run#10 example: coqchk
    #      success 40398s, parser CLEAN, zero axioms, the R4 coverage split
    #      broken) -> the E variant does not hold; the job stays UNRECOGNIZED,
    #      never force-fitted (manual identification first);
    #   2. the coqchk step succeeded = it ran to completion, so the "coqchk
    #      artifacts missing" cascade mechanism does not apply (the review
    #      ledger's second discriminator; the only corroborating signal when no
    #      log is available) -> likewise stays UNRECOGNIZED;
    #   3. a genuinely executed GATE-BANNER-ABSENT line is present = the
    #      banner-absent cascade E (four occurrences across runs 7/8/20/26,
    #      coqchk skipped/cancelled, the log-confirmation third leg on the
    #      roster);
    #   4. no log and coqchk did not complete = the step-name rule keeps E
    #      (banner token unconfirmed; noted as such).
    # -> family=E-coqchk-skipped, action=rerun-after-stable-window (a variant
    #    inside family E; the run-level precedence UNRECOGNIZED>C>A>E>B>D is
    #    unchanged).  Provenance: of the six UNREC events in the retro ledger's
    #    main table, the four banner-absent forms (#7/#8/#20/#26) entered the
    #    taxonomy and the #10 auth-state form was converted to stay UNREC per
    #    the review verdict (machine ruling = review ruling; the acceptance
    #    verdict); the #3 runner-lost shape (zero red steps) still walks
    #    UNRECOGNIZED, never force-fitted.
    gate2_only_red = [s for s in red_steps
                      if GATE2_STEP_RE.search(str(s.get("name") or ""))
                      and not UPLOAD_STEP_RE.search(str(s.get("name") or ""))]
    subset_gate2_upload = all(
        GATE2_STEP_RE.search(str(s.get("name") or ""))
        or UPLOAD_STEP_RE.search(str(s.get("name") or ""))
        for s in red_steps)
    gate2_excl_note = None
    att_state_note = None
    if gate2_only_red and subset_gate2_upload:
        att_hit = bool(log_text and GATE2_ATTEST_RE.search(log_text))
        banner_hit = bool(log_text and GATE_BANNER_ABSENT_RE.search(log_text))
        coqchk_done = any(
            s.get("conclusion") == "success"
            and COQCHK_DONE_RE.search(str(s.get("name") or ""))
            for s in steps)
        if att_hit and not banner_hit:
            gate2_excl_note = (
                "gate2-only shape, conclusion-position validation: a"
                " genuinely executed GATE2-ATTEST-RED/判定=CLEAN token is"
                " present (after dump-line filtering) = the attested-red"
                " auth-state shape (review-ledger phase 2; the run#10 example:"
                " coqchk success 40398s, parser CLEAN, zero axioms, the R4"
                " coverage split broken) -> the E variant does not hold; the"
                " job stays UNRECOGNIZED, never force-fitted (manual"
                " identification)")
            # auth-state-red-maintained note (evidence enhancement only):
            # both tokens genuinely present on dump-filtered text = the
            # attested-red pair (run#10 form) — the UNREC maintained
            # rationale rides on the note automatically; family unchanged
            if (log_text and GATE2_ATTEST_RED_RE.search(log_text)
                    and GATE2_CLEAN_RE.search(log_text)):
                att_state_note = (
                    "auth-state-red-maintained: the genuinely executed"
                    " GATE2-ATTEST-RED + 判定=CLEAN pair (after dump-line"
                    " filtering) = the attested-red auth-state shape stays"
                    " UNREC — the maintained rationale rides automatically:"
                    " the E gate2-only cascade variant does not hold for"
                    " attested-red shapes; manual identification first; never"
                    " force-fitted (family unchanged, evidence enhanced;"
                    " review ledger phases 2/3)")
        elif coqchk_done:
            gate2_excl_note = (
                "gate2-only red step but the coqchk step succeeded (ran to"
                " completion) = not the \"coqchk artifacts missing\" cascade"
                " mechanism (the review ledger's second discriminator; the"
                " run#10 form; an attested-red candidate whose token face is"
                " unproven) -> the E variant does not hold; the job stays"
                " UNRECOGNIZED, never force-fitted")
    if gate2_only_red and subset_gate2_upload and gate2_excl_note is None:
        banner_hit = bool(log_text and GATE_BANNER_ABSENT_RE.search(log_text))
        ev.append("gate2-only cascade shape (the E variant, banner-absent"
                  " restricted form): the red-step set ⊆ {gate2+upload family},"
                  " a pure gate2 red step on the roster, the preceding"
                  " build/coqchk not content failures = coqchk artifacts"
                  " missing, the gate2 cascade (admitted from the banner-absent"
                  " genuinely-executed forms of the four Main retro events"
                  " #7/#8/#20/#26; the #10 auth-state shape is excluded)")
        if banner_hit:
            ev.append("log confirmation: GATE-BANNER-ABSENT (a genuinely"
                      " executed banner-absent line; the E variant's third"
                      " leg)")
        else:
            ev.append("banner token unconfirmed (no log or no genuinely executed line; noted as-is; the step-name shape)")
        if log_text:
            ev.extend(scan_log_evidence(log_text, dump_filter))
        return {"family": "E-coqchk-skipped",
                "action": ACTION_OF["E-coqchk-skipped"],
                "evidence": ev, "red_steps": red_names}
    if gate2_excl_note is not None:
        ev.append(gate2_excl_note)
    if att_state_note is not None:
        ev.append(att_state_note)

    if log_text:
        ev.extend(scan_log_evidence(log_text, dump_filter))
        if RED_NET_RE.search(log_text):
            ev.append("log hit a network-window word face (taxonomy B)")
            return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                    "evidence": ev, "red_steps": red_names}
    for s in red_steps:
        if NET_STEP_RE.search(str(s.get("name") or "")):
            ev.append("red step name in a network-adjacent step"
                      " (checkout/upload/artifact/cache/...): %s"
                      % s.get("name"))
            return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                    "evidence": ev, "red_steps": red_names}
    if log_text and RED_CONTENT_RE.search(log_text):
        ev.append("log hit a content-red word face (Error:/FAIL/ORDER-MISSING/EXIT!=0/axioms!=0; taxonomy A)")
        return {"family": "A-content-red", "action": ACTION_OF["A-content-red"],
                "evidence": ev, "red_steps": red_names}
    for s in red_steps:
        if CONTENT_STEP_RE.search(str(s.get("name") or "")):
            ev.append("red step name in a content step (build/compile/coqchk/..."
                      "; taxonomy A; the concrete files under --logs): %s"
                      % s.get("name"))
            return {"family": "A-content-red", "action": ACTION_OF["A-content-red"],
                    "evidence": ev, "red_steps": red_names}

    ev.append("step-conclusions: %s" % ",".join(
        "%s=%s" % (s.get("name") or "(unnamed)", s.get("conclusion") or "-")
        for s in steps))
    # runner-lost candidate shape (Main#3 real form; review ledger §二 S3/R1
    # and §三-6, §四-3): job failure with zero failed steps, a build-family
    # step still hung (status=in_progress, conclusion=null), and a logs-GET
    # HTTP 404 note (the log blob was never uploaded — the companion evidence
    # of a runner lost mid-step). Evidence-package form only: family stays
    # UNRECOGNIZED (never force-fitted; the D shape cancelled + zero steps
    # does not cover failure; manual identification first). The four legs
    # must all hold — a missing 404 note leaves the plain fallback below.
    if (conclusion == "failure" and not red_steps and log_note is not None
            and "logs-GET: HTTP 404" in log_note):
        hung = [str(s.get("name") or "(unnamed)") for s in steps
                if s.get("status") == "in_progress"
                and s.get("conclusion") is None
                and CONTENT_STEP_RE.search(str(s.get("name") or ""))]
        if hung:
            ev.append(
                "runner-lost-candidate: job failure + zero failed steps + "
                "build step hung in_progress (%s) + logs-GET HTTP 404 (log "
                "blob never uploaded)" % ", ".join(hung))
            dur = duration_sec(job.get("started_at"), job.get("completed_at"))
            if dur is not None:
                ev.append("runner-lost-candidate wall clock: %ds (job "
                          "duration; conclusion=failure, not timed_out)" % dur)
            ev.append(
                "runner-lost-candidate rationale: family stays UNRECOGNIZED "
                "— runner-lost infra shape outside the taxonomy; the D "
                "shape (cancelled + zero steps) does not cover failure; "
                "evidence package only, no force-fit; manual identification "
                "first")
    ev.append("red shape outside the taxonomy; never force-fitted; identify manually from the log")
    return {"family": "UNRECOGNIZED", "action": "watch-only",
            "evidence": ev, "red_steps": red_names}


def batch_upgrade_c(per, jobs):
    """Run-level batch rule (taxonomy C): two or more same-shape content
    failures (A) upgrade all of them to C (the example: batch EXIT=134/Abort
    trap: 6 with every SKIP-marked file passing; confirmable via --logs)."""
    idxs = [i for i, c in enumerate(per) if c["family"] == "A-content-red"]
    if len(idxs) < 2:
        return
    for i in idxs:
        c = per[i]
        c["family"] = "C-toolchain-break"
        c["action"] = ACTION_OF["C-toolchain-break"]
        c["evidence"].append(
            "run-level batch rule: %d same-shape content failures (the C"
            " example: batch EXIT=134/Abort trap: 6, every SKIP-marked file"
            " passing); confirm EXIT=134 via --logs" % len(idxs))


def run_verdict(per, jobs, extra_evidence=None):
    """Run-level verdict: first match by RUN_FAMILY_PRECEDENCE
    (out-of-taxonomy first) -> {family, action, evidence, red_job_ids}."""
    reds = [(j, c) for j, c in zip(jobs, per) if c["family"] != "none"]
    fams = set(c["family"] for _, c in reds)
    ev = list(extra_evidence or [])
    if not fams:
        ev.append("all passing: 0 red jobs (watch-only)")
        return {"family": "none", "action": ACTION_OF["none"],
                "evidence": ev, "red_job_ids": []}
    fam = next(f for f in RUN_FAMILY_PRECEDENCE if f in fams)
    ev.append("red jobs %d/%d: ids=%s" % (len(reds), len(jobs),
                                          [j.get("id") for j, _ in reds]))
    ev.append("rostered families: %s (first match by classification precedence)" % ",".join(sorted(fams)))
    if "UNRECOGNIZED" in fams:
        ev.append("UNRECOGNIZED on the roster; out-of-taxonomy red shapes take manual identification first (never force-fitted)")
    return {"family": fam, "action": ACTION_OF[fam],
            "evidence": ev, "red_job_ids": [j.get("id") for j, _ in reds]}


# ---- duration baseline (--baseline-seconds) ----

def build_baseline_note(jobs, baseline_seconds, baseline_step):
    """Baseline comparison: the current value (--baseline-step name-contains
    match; the longest name wins on multiple hits; all hits on the roster) vs
    the baseline seconds -> a ratio; >= BASELINE_SQUEEZE_RATIO -> a
    "likely a local resource squeeze, not a hang" note.  A baseline step
    absent or unfinished (skipped/not run) -> an applied=false loud note
    (rc stays 0)."""
    query = str(baseline_step or "coqchk")
    matches = []
    for j in jobs:
        for s in j.get("steps") or []:
            if query.lower() in str(s.get("name") or "").lower():
                d = duration_sec(s.get("started_at"), s.get("completed_at"))
                if d is not None:
                    matches.append({"job": j.get("name"), "step": s.get("name"),
                                    "duration_sec": d})
    if not matches:
        return {"applied": False, "step_query": query,
                "baseline_seconds": baseline_seconds,
                "reason": "the baseline step is absent or unfinished"
                          " (skipped/not run); the comparison was not applied"
                          " (a loud note, never silent)"}
    cur = max(m["duration_sec"] for m in matches)
    ratio = round(cur / float(baseline_seconds), 1)
    note = "step %s now %ds vs baseline %ds = %.1fx" % (query, cur, baseline_seconds, ratio)
    if ratio >= BASELINE_SQUEEZE_RATIO:
        note += (" (>= %.0fx = likely a local resource squeeze, not a hang;"
                 " the coqchk 561s vs 7480s = 13.3x example)"
                 % BASELINE_SQUEEZE_RATIO)
    else:
        note += " (< %.0fx; duration magnitude as usual)" % BASELINE_SQUEEZE_RATIO
    return {"applied": True, "step_query": query,
            "baseline_seconds": baseline_seconds,
            "matched": sorted(matches, key=lambda m: (str(m["job"]),
                                                      str(m["step"]),
                                                      m["duration_sec"])),
            "current_seconds": cur, "ratio": ratio, "note": note}


# ---- output ----

def build_report(mode, source, repo, run_id, total, jobs, per, verdict, baseline):
    rep = {
        "schema": SCHEMA,
        "mode": mode,
        "source": source,
        "run": {"repo": repo, "run_id": run_id, "total_count": total,
                "jobs_total": len(jobs), "red_job_ids": verdict["red_job_ids"],
                "family": verdict["family"], "action": verdict["action"],
                "evidence": verdict["evidence"]},
        "jobs": [],
        "family": verdict["family"],
        "action": verdict["action"],
        "evidence": verdict["evidence"],
    }
    for j, c in zip(jobs, per):
        rep["jobs"].append({
            "id": j.get("id"), "name": j.get("name"),
            "status": j.get("status"), "conclusion": j.get("conclusion"),
            "started_at": j.get("started_at"), "completed_at": j.get("completed_at"),
            "duration_sec": duration_sec(j.get("started_at"), j.get("completed_at")),
            "steps": [{
                "number": s.get("number"), "name": s.get("name"),
                "status": s.get("status"), "conclusion": s.get("conclusion"),
                "started_at": s.get("started_at"),
                "completed_at": s.get("completed_at"),
                "duration_sec": duration_sec(s.get("started_at"),
                                             s.get("completed_at")),
            } for s in (j.get("steps") or [])],
            "classification": {"family": c["family"], "action": c["action"],
                               "evidence": c["evidence"],
                               "red_steps": c["red_steps"]},
        })
    if baseline is not None:
        rep["baseline_note"] = baseline
    return rep


def render_stdout(source_desc, jobs, per, verdict, baseline):
    print("=== ROCQWASH CI-TRIAGE (five-family classification taxonomy, coded from six real-run battles) ===")
    print(source_desc)
    print("jobs total=%d" % len(jobs))
    for j, c in zip(jobs, per):
        jd = duration_sec(j.get("started_at"), j.get("completed_at"))
        print("--- JOB #%s [%s] status=%s conclusion=%s dur=%s ---"
              % (j.get("id"), j.get("name"), j.get("status"), j.get("conclusion"),
                 fmt_dur(jd)))
        print("    #  status     conclusion  started(UTC)         ended(UTC)"
              "           sec    step")
        for s in (j.get("steps") or []):
            sd = duration_sec(s.get("started_at"), s.get("completed_at"))
            num = s.get("number") if isinstance(s.get("number"), int) else 0
            print("  %3d  %-9s  %-10s  %-19s  %-19s  %6s  %s"
                  % (num, str(s.get("status") or "-")[:9],
                     str(s.get("conclusion") or "-")[:10],
                     str(s.get("started_at") or "-")[:19],
                     str(s.get("completed_at") or "-")[:19],
                     sd if sd is not None else "-",
                     s.get("name") or "(unnamed)"))
        print("  classification: family=%s (%s) action=%s"
              % (c["family"], FAMILY_LABEL.get(c["family"], ""), c["action"]))
        for e in c["evidence"]:
            print("    - %s" % e)
    print("=== RUN VERDICT: family=%s (%s) action=%s ==="
          % (verdict["family"], FAMILY_LABEL.get(verdict["family"], ""),
             verdict["action"]))
    for e in verdict["evidence"]:
        print("  - %s" % e)
    if baseline is not None:
        print("baseline: %s" % (baseline.get("note") or baseline.get("reason") or ""))
    print("(triage complete; a failing result is data, not a tool failure; exit 0)")


# ---- main flow ----

def run_triage(args):
    """Load (online/offline) -> per-job classification -> the run-level batch C
    rule -> the run verdict -> the baseline comparison -> (report, jobs, per,
    verdict, baseline, source_desc).  Usage error -> 2; unreachable -> 9."""
    online = args.repo is not None or args.run is not None
    if args.offline and online:
        raise TriageError("--offline and --repo/--run are mutually exclusive (pick one)", 2)
    if not args.offline and not online:
        raise TriageError("give --offline JOBS.json (offline) or --repo"
                          " ORG/REPO --run ID (online)", 2)
    if online and (args.repo is None or args.run is None):
        raise TriageError("online mode needs --repo ORG/REPO and --run ID as a pair", 2)
    if args.repo is not None and not re.match(r"^[^/\s]+/[^/\s]+$", args.repo):
        raise TriageError("--repo must be ORG/REPO", 2)
    if args.offline and args.logs:
        raise TriageError("--logs is online-mode only (offline is zero-network;"
                          " log evidence goes through the canned shape or the"
                          " --selftest regex units)", 2)
    if args.baseline_seconds is not None and args.baseline_seconds <= 0:
        raise TriageError("--baseline-seconds must be a positive integer", 2)
    if args.retry_max < 0:
        raise TriageError("--retry-max must be >= 0, got %d" % args.retry_max, 2)

    log_notes = {}
    logs_by_id = {}
    dump_filter = not args.no_dump_filter
    if args.offline:
        jobs, total, canned_logs, canned_notes = load_jobs_offline(args.offline)
        mode, source, repo, run_id = "offline", args.offline, None, None
        source_desc = ("mode=offline source=%s dump_filter=%s canned_logs=%d"
                       " canned_notes=%d"
                       % (args.offline, "on" if dump_filter else "off",
                          len(canned_logs), len(canned_notes)))
        logs_by_id = dict(canned_logs)
        log_notes.update(canned_notes)
    else:
        token = netrc_token(args.netrc)
        try:
            jobs, total = fetch_jobs_online(args.repo, args.run, token,
                                            args.timeout,
                                            retry_max=args.retry_max)
        except ApiHTTPError as e:
            raise TriageError("API HTTP %d: %s (GET jobs failed; %s)"
                              % (e.code, e.body.strip()[:160], e.url), 9)
        mode, source, repo, run_id = "online", jobs_url(args.repo, args.run), \
            args.repo, args.run
        source_desc = ("mode=online repo=%s run=%d api=%s token=***MASKED***"
                       " (netrc machine github.com; %s) dump_filter=%s"
                       % (repo, run_id, source, args.netrc,
                          "on" if dump_filter else "off"))

    if mode == "online" and args.logs:
        reds = [j for j in jobs
                if j.get("conclusion") in ("failure", "timed_out", "cancelled")
                and (j.get("steps") or [])]
        if len(reds) > LOGS_FETCH_CAP:
            log_notes["_meta"] = (
                "log fetch cap %d: only the first %d red jobs fetched"
                " (%d not fetched; loud, never silent)"
                % (LOGS_FETCH_CAP, LOGS_FETCH_CAP, len(reds) - LOGS_FETCH_CAP))
        for j in reds[:LOGS_FETCH_CAP]:
            text, note = fetch_job_log(repo, j.get("id"), token, args.timeout,
                                       retry_max=args.retry_max)
            logs_by_id[j.get("id")] = text or ""
            if note:
                log_notes[j.get("id")] = note

    per = [classify(j, logs_by_id.get(j.get("id")), dump_filter=dump_filter,
                    log_note=log_notes.get(j.get("id")))
           for j in jobs]
    for j, c in zip(jobs, per):
        note = log_notes.get(j.get("id"))
        if note:
            c["evidence"].append(note)
    batch_upgrade_c(per, jobs)
    verdict_notes = []
    if mode == "offline" and logs_by_id:
        verdict_notes.append(
            "offline canned logs %d (the job_logs top-level extension, not a"
            " real API shape; byte-identical on rerun)" % len(logs_by_id))
    if mode == "offline" and log_notes:
        verdict_notes.append(
            "offline canned log-fetch notes %d (job_log_notes top-level "
            "extension, not a real API shape; byte-identical on rerun)"
            % len(log_notes))
    if not dump_filter:
        verdict_notes.append(
            "dump-line filtering disabled (--no-dump-filter); cyan script echo"
            " and group-directive lines enter evidence and criteria verbatim"
            " (the review-ledger evidence trap re-forms as-is; filtering is on"
            " by default)")
    verdict = run_verdict(per, jobs, extra_evidence=verdict_notes + [
        v for k, v in log_notes.items() if k == "_meta"])
    baseline = None
    if args.baseline_seconds is not None:
        baseline = build_baseline_note(jobs, args.baseline_seconds,
                                       args.baseline_step)
    report = build_report(mode, source, repo, run_id, total, jobs, per,
                          verdict, baseline)
    return report, jobs, per, verdict, baseline, source_desc


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
        description="CI failing-build triage tool — step-level table plus the"
                    " five-family taxonomy with the all-passing state,"
                    " prescribed actions, and an optional duration baseline"
                    " comparison")
    ap.add_argument("--offline", default=None, metavar="JOBS.json",
                    help="offline mode: canned jobs JSON in the real API shape;"
                         " the path used by --selftest and air-gapped"
                         " environments")
    ap.add_argument("--repo", default=None, metavar="ORG/REPO",
                    help="online mode: the repository as ORG/REPO (paired with --run)")
    ap.add_argument("--run", type=int, default=None, metavar="ID",
                    help="online mode: the Actions run id (paired with --repo)")
    ap.add_argument("--logs", action="store_true",
                    help="online mode also fetches red jobs' logs and harvests"
                         " key lines into the evidence (online only; refused"
                         " offline)")
    ap.add_argument("--no-dump-filter", action="store_true",
                    help="disable dump-line filtering (cyan script echo [36;1m"
                         " and ##[group] lines enter evidence and criteria"
                         " verbatim — the review-ledger evidence trap re-forms"
                         " as-is; filtering is on by default; a run-level loud"
                         " note is emitted)")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc path (default ~/.netrc; the machine github.com"
                         " line's 6th column is the token)")
    ap.add_argument("--baseline-seconds", type=int, default=None, metavar="N",
                    help="historical duration in seconds for the same sync (the"
                         " coqchk 561s example) -> prints a ratio comparison")
    ap.add_argument("--baseline-step", default="coqchk", metavar="NAME",
                    help="the baseline step name (name-contains match; default coqchk = the example form)")
    ap.add_argument("--timeout", type=int, default=30, metavar="S",
                    help="per-request timeout seconds (default 30)")
    ap.add_argument("--retry-max", type=int, default=3, metavar="N",
                    help="403/429/5xx backoff retry cap (default 3;"
                         " exponential base 2s; a Retry-After second count is"
                         " honored; exhaustion raises the original error as 9)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="triage report output path (rocqwash-ci-triage/1;"
                         " sort_keys)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        report, jobs, per, verdict, baseline, source_desc = run_triage(args)
    except ApiHTTPError as e:
        print("FAIL-LOUD: API HTTP %d: %s (%s)" % (e.code, e.body.strip()[:200],
                                                   e.url), file=sys.stderr)
        sys.exit(9)
    except TriageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(e.code)

    render_stdout(source_desc, jobs, per, verdict, baseline)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False, sort_keys=True)
        print("json ->", args.json)
    sys.exit(0)


# ---- selftest (--offline fixtures; zero real network, zero compiles; pure logic vectors) ----

def selftest():
    """Frozen selftest vectors: the six canned family samples (five families
    plus the all-passing state) all hit; the 13.3x baseline example; the loud
    absent-baseline-step note; classifier units (key-line regex positives and
    negatives; cascade/in-flight/UNRECOGNIZED routing; the E-shapes-are-not-
    content-red negative); netrc parsing; byte-identical determinism; CLI four
    codes; the backoff layer (403x3 -> [2,4,8]; Retry-After honored;
    exhaustion raises; 401 no-retry; _open/_sleep injection, zero network);
    the Main-shape reading vector (the coq93.yml real step names x the
    five-family compatibility mechanical pins); the gate2-only E-variant
    vectors (the review-ledger token-dichotomy acceptance line: the #7 fixture
    with a genuinely executed banner-absent line canned -> stays E; the
    #8/#20/#26 shape vectors stay E; the #10 fixture with the attested-token
    canned -> the UNRECOGNIZED conversion acceptance verdict, machine ruling =
    review ruling; the coqchk-success corroborating vector; the auth-state
    tokens-never-enter-red-regexes check; four negative rules — of the six
    provenance events, four entered, one converted, one stays out); the
    dump-line filtering vectors (the review-ledger evidence trap: a dump-only
    banner never confirms, a genuinely executed line confirms,
    --no-dump-filter re-forms the trap as-is); the five-token roster vector
    (each roster candidate judged against its real ledger form); the job_logs
    malformed fail-loud vector; the canned-log determinism vector; the two-hop
    logs-415 fix vector (302 -> zero-Authorization second hop -> 200; 415/403/
    no-Location original codes enter evidence; canned, zero network); and the
    two-shape evidence-note vectors (runner-lost-candidate: the Main#3 real
    fixture four-legs pass plus the 57007s wall clock plus the canned 404 note
    in evidence plus determinism plus four negatives — missing note / note
    without 404 / hung step not build-family / red steps present, any one
    missing leg kills the note; auth-state-red-maintained: the fixture pair
    note assertion plus two single-token negatives — an incomplete pair keeps
    only the old note; the job_log_notes extension and malformed fail-loud
    vectors); and the evidence-annihilation candidate (R19) vectors (the
    triage-table v1.5 row: a zero-byte injected log with every outcome
    recorded fires the three-marker R19 note on evidence only, the family
    face unchanged; the empty-string and whitespace-only positives; the
    no-fetch / note-channel / non-empty-log / unrecorded-outcome negatives,
    any one missing leg kills the note; the canned-fixture end-to-end run
    carries the note in --json and stays byte-identical on rerun).
    All runs use --offline fixtures; zero real network, zero compiles."""
    import shutil
    import subprocess
    import tempfile

    def run(args):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    fxdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tests", "fixtures")

    def fx(name):
        return os.path.join(fxdir, "ci_triage_%s.json" % name)

    tmp = tempfile.mkdtemp(prefix="rocqwash_ci_triage_self_")
    try:
        # part 1: the six family samples (five families + all-passing) all hit (family/action pinned per sample)
        six = [("A_content_red", "A-content-red", "fix-content"),
               ("B_netred", "B-netred", "rerun-after-stable-window"),
               ("C_toolchain_break", "C-toolchain-break", "restore-toolchain"),
               ("D_queue_wall", "D-queue-wall", "queue-etiquette"),
               ("E_coqchk_skipped", "E-coqchk-skipped",
                "rerun-after-stable-window"),
               ("green", "none", "watch-only")]
        outs = {}
        for stem, fam, act in six:
            path = fx(stem)
            assert os.path.isfile(path), "fixture missing (the six-file set must be present): %s" % path
            out = os.path.join(tmp, stem + ".json")
            p = run(["--offline", path, "--json", out])
            assert p.returncode == 0, (stem, p.stdout[-400:])
            rep = json.load(io.open(out, encoding="utf-8"))
            assert rep["schema"] == SCHEMA, rep.get("schema")
            assert rep["family"] == fam and rep["action"] == act, \
                (stem, rep["family"], rep["action"])
            outs[stem] = out
        # A: the red step name enters evidence, and the family is not B/E (the content-red positive)
        repA = json.load(io.open(outs["A_content_red"], encoding="utf-8"))
        cjA = repA["jobs"][0]["classification"]
        assert cjA["family"] == "A-content-red" and any(
            e.startswith("failure-step: Build") for e in cjA["evidence"]), cjA
        # B: a checkout red step lands in B; the cancelled cascade shape (steps but zero red steps) also lands in B
        repB = json.load(io.open(outs["B_netred"], encoding="utf-8"))
        assert repB["jobs"][0]["classification"]["family"] == "B-netred"
        assert repB["jobs"][1]["classification"]["family"] == "B-netred", \
            "the cascade shape should land in B"
        assert any("cascade shape" in e
                   for e in repB["jobs"][1]["classification"]["evidence"])
        # C: the run-level batch rule upgrades to C (three red jobs all C; the green control stays none; the batch note in per-job evidence)
        repC = json.load(io.open(outs["C_toolchain_break"], encoding="utf-8"))
        famsC = [j["classification"]["family"] for j in repC["jobs"]]
        assert famsC == ["C-toolchain-break"] * 3 + ["none"], famsC
        assert any("batch rule" in e
                   for e in repC["jobs"][0]["classification"]["evidence"]), repC["jobs"][0]
        # D: zero steps (steps=[]) on the roster; evidence contains steps=0
        repD = json.load(io.open(outs["D_queue_wall"], encoding="utf-8"))
        assert repD["jobs"][0]["steps"] == []
        assert "steps=0" in "".join(
            repD["jobs"][0]["classification"]["evidence"])
        # E: the E signature hit, and never treated as a content failure (family != A; the coqchk skipped note on the roster)
        repE = json.load(io.open(outs["E_coqchk_skipped"], encoding="utf-8"))
        cjE = repE["jobs"][0]["classification"]
        assert cjE["family"] == "E-coqchk-skipped" \
            and cjE["family"] != "A-content-red", cjE
        assert any("coqchk" in e for e in cjE["evidence"]), cjE
        # all-passing: family=none, action=watch-only
        repG = json.load(io.open(outs["green"], encoding="utf-8"))
        assert repG["family"] == "none" and repG["action"] == "watch-only"

        # part 2: baseline comparison — the all-passing COQCHK 7480s vs baseline 561s = 13.3x (the example)
        out = os.path.join(tmp, "baseline.json")
        p = run(["--offline", fx("green"), "--baseline-seconds", "561",
                 "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        bn = json.load(io.open(out, encoding="utf-8"))["baseline_note"]
        assert bn["applied"] is True and bn["current_seconds"] == 7480 \
            and bn["ratio"] == 13.3, bn
        assert "local resource squeeze" in bn["note"] and "561" in bn["note"], bn
        # absent baseline step (the A fixture COQCHK skipped) -> applied=False with a loud note; rc stays 0
        p = run(["--offline", fx("A_content_red"), "--baseline-seconds", "561",
                 "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        bn = json.load(io.open(out, encoding="utf-8"))["baseline_note"]
        assert bn["applied"] is False and "loud" in bn["reason"], bn

        # part 3: determinism — the C fixture rerun with the same input is byte-identical in --json
        before = io.open(outs["C_toolchain_break"], "rb").read()
        p = run(["--offline", fx("C_toolchain_break"),
                 "--json", outs["C_toolchain_break"]])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(outs["C_toolchain_break"], "rb").read() == before, \
            "json byte drift = violation"

        # part 4: CLI four codes + mutual-exclusion shapes
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing mode should rc=2, got %d" % p.returncode
        p = run(["--offline", os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "missing jobs file should rc=9, got %d" % p.returncode
        p = run(["--offline", fx("green"), "--logs"])
        assert p.returncode == 2, "--logs refused offline should rc=2, got %d" % p.returncode
        p = run(["--repo", "org/repo"])
        assert p.returncode == 2, "repo without run should rc=2, got %d" % p.returncode
        p = run(["--repo", "justname", "--run", "1"])
        assert p.returncode == 2, "bad repo shape should rc=2, got %d" % p.returncode
        p = run(["--offline", fx("green"), "--repo", "o/r", "--run", "1"])
        assert p.returncode == 2, "dual-mode exclusivity should rc=2, got %d" % p.returncode

        # part 5: classifier units (zero network; called directly)
        def mkjob(**kw):
            base = {"id": 1, "name": "j", "status": "completed",
                    "conclusion": "failure",
                    "started_at": "2026-11-10T08:00:00Z",
                    "completed_at": "2026-11-10T08:01:00Z", "steps": []}
            base.update(kw)
            return base

        def mkstep(n, name, concl, **kw):
            d = {"number": n, "name": name, "status": "completed",
                 "conclusion": concl,
                 "started_at": "2026-11-10T08:00:01Z",
                 "completed_at": "2026-11-10T08:00:30Z"}
            d.update(kw)
            return d

        c = classify(mkjob(conclusion="success"))
        assert c["family"] == "none" and c["action"] == "watch-only"
        c = classify(mkjob(status="in_progress", conclusion=None))
        assert c["family"] == "none" and any("in-flight" in e
                                             for e in c["evidence"]), c
        c = classify(mkjob(conclusion="cancelled"))
        assert c["family"] == "D-queue-wall" and c["action"] == "queue-etiquette"
        c = classify(mkjob(conclusion="cancelled",
                           steps=[mkstep(1, "Build (coqc batch)", "cancelled")]))
        assert c["family"] == "B-netred" and any("cascade shape" in e
                                                 for e in c["evidence"]), c
        c = classify(mkjob(steps=[mkstep(1, "Build (coqc batch)", "failure")]))
        assert c["family"] == "A-content-red"
        c = classify(mkjob(id=7, steps=[mkstep(1, "Build (coqc batch)", "failure")]),
                     log_text="EXIT=134\nAbort trap: 6\n")
        assert c["family"] == "C-toolchain-break", c
        c = classify(mkjob(id=11, steps=[mkstep(1, "Build (coqc batch)", "failure")]),
                     log_text="Error: LibX.v:12: The reference eqR lacks\nCOQCHK_EXIT=1\n")
        assert c["family"] == "A-content-red" \
            and any("log[Error" in e for e in c["evidence"]) \
            and any("COQCHK_EXIT=1" in e for e in c["evidence"]), c
        c = classify(mkjob(steps=[mkstep(1, "Checkout repository", "failure")]))
        assert c["family"] == "B-netred"
        e_steps = [mkstep(1, "Build (coqc batch)", "success"),
                   mkstep(2, "Upload artifact (gate2 ledger)", "failure"),
                   mkstep(3, "COQCHK", "skipped",
                          started_at=None, completed_at=None)]
        c = classify(mkjob(id=9, steps=e_steps))
        assert c["family"] == "E-coqchk-skipped", c
        c = classify(mkjob(id=9, steps=e_steps),
                     log_text="GATE-BANNER-ABSENT\n")
        assert c["family"] == "E-coqchk-skipped" and any(
            "GATE-BANNER-ABSENT" in e for e in c["evidence"]), c
        c = classify(mkjob(steps=[mkstep(1, "Upload artifact (gate2 ledger)",
                                         "failure"),
                                  mkstep(2, "COQCHK", "success")]))
        assert c["family"] == "B-netred", "upload red without the E signature (coqchk not skipped) -> B"
        c = classify(mkjob(steps=[mkstep(1, "Report coverage", "failure")]))
        assert c["family"] == "UNRECOGNIZED" and c["action"] == "watch-only", c

        # part 6: key-line regex positives/negatives (the taxonomy word-face frozen vectors)
        for s in ["Error: LibX.v:12: syntax", "ORDER-MISSING: names",
                  "COQCHK_EXIT=1", "公理总数=3", "task FAIL at step 2"]:
            assert RED_CONTENT_RE.search(s), "content-red positive should match: %s" % s
        for s in ["COQCHK_EXIT=0", "公理总数=0", "0 FAILURES found",
                  "no error today", "all good"]:
            assert not RED_CONTENT_RE.search(s), "content-red negative should not match: %s" % s
        for s in ["fatal: unable to access 'https://github.com/o/r.git/'",
                  "connect to github.com port 443 failed",
                  "ssh: Connection was reset",
                  "upload ENOTFOUND on github.com",
                  "Upload progress stalled at 90%",
                  "403 Forbidden: job is completed"]:
            assert RED_NET_RE.search(s), "network-window positive should match: %s" % s
        for s in ["Upload artifact success (3 files)",
                  "listening on port 8080", "connected ok"]:
            assert not RED_NET_RE.search(s), "network-window negative should not match: %s" % s
        for s in ["EXIT=134", "Abort trap: 6"]:
            assert RED_ABORT_RE.search(s), "toolchain-break positive should match: %s" % s
        for s in ["EXIT=0", "EXIT=139", "Abort trap: 8"]:
            assert not RED_ABORT_RE.search(s), "toolchain-break negative should not match: %s" % s
        assert GATE_BANNER_ABSENT_RE.search("GATE-BANNER-ABSENT")
        assert not GATE_BANNER_ABSENT_RE.search("gate banner ok")

        # part 7: netrc parsing unit (single-line 6-column form + multi-line form + negatives; zero network)
        nf = os.path.join(tmp, "netrc")
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine api.github.com login octo password AAAA\n"
                     "machine github.com login octocat password TOK-1234\n")
        assert netrc_token(nf) == "TOK-1234", "the single-line 6-column form should take the github.com line's 6th column"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine github.com\nlogin octocat\npassword TOK-9\n")
        assert netrc_token(nf) == "TOK-9", "the multi-line form should parse the same way"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine gitlab.com login x password Y\n")
        try:
            netrc_token(nf)
            assert False, "no github.com entry should fail loud"
        except TriageError as e:
            assert e.code == 9, e.code

        # part 8: the resilience layer — backoff sequence + Retry-After honored
        # + http_get canned retry runner (zero network; _open/_sleep injection
        # points; the 403x3 -> [2,4,8] example)
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        try:
            _http_backoff.backoff_delays(-1)
            assert False, "negative cap should ValueError"
        except ValueError:
            pass
        assert _http_backoff.parse_retry_after("60") == 60.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, "an HTTP-date is never guessed"

        class _Resp(object):
            """Canned response body (a urlopen fake; zero network; context-manager form)."""
            def __init__(self, payload=b"JOBS"):
                self._p = payload
            def read(self):
                return self._p
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def _http_err(code, ra=None):
            hd = {"Retry-After": ra} if ra else {}
            return urllib.error.HTTPError(
                "https://x", code, "HTTP Error %d" % code, hd,
                io.BytesIO(b'{"message":"x"}'))

        def _seq_open(resps):
            it = iter(resps)
            def _open(req, timeout=None):
                r = next(it)
                if isinstance(r, Exception):
                    raise r          # a canned error must raise (urlopen semantics)
                return r
            return _open

        slept = []
        got = http_get("https://x", "tok", 5, retry_max=3,
                       _open=_seq_open([_http_err(403)] * 3 + [_Resp()]),
                       _sleep=slept.append)
        assert got == b"JOBS" and slept == [2.0, 4.0, 8.0], \
            (got, slept)                       # the 403x3 -> [2,4,8] example
        slept = []
        got = http_get("https://x", "tok", 5, retry_max=3,
                       _open=_seq_open([_http_err(429, ra="7"), _Resp(b"OK2")]),
                       _sleep=slept.append)
        assert got == b"OK2" and slept == [7.0], \
            (got, slept)                       # the Retry-After header honored (replaces the exponential delay)
        slept = []
        try:
            http_get("https://x", "tok", 5, retry_max=3,
                     _open=_seq_open([_http_err(403)] * 4), _sleep=slept.append)
            assert False, "403x4 exhausted retries should raise"
        except ApiHTTPError as e:
            assert e.code == 403, e.code
        assert slept == [2.0, 4.0, 8.0], slept
        slept = []
        try:
            http_get("https://x", "tok", 5, retry_max=3,
                     _open=_seq_open([_http_err(401)]), _sleep=slept.append)
            assert False, "a 401 semantic error should not retry and should raise directly"
        except ApiHTTPError as e:
            assert e.code == 401, e.code
        assert slept == [], "401: zero retries, zero sleeps"

        # part 9: the Main-shape reading vector (a mechanical pin on the
        # survey doc §3.1 compatibility table): the coq93.yml real form
        # (workflow "Main CI 9.3", the single Windows job "Rocq 9.3 build +
        # coqchk (self-hosted seed cache, Windows)") — all 16 step names pinned
        # one by one, plus the five-family classification mechanically verified
        # line by line against the Main step names (a real red is never
        # missed; the UNRECOGNIZED fallback never misfires).  One divergence
        # between this mechanical check and the §3.1 prose is registered
        # as-is: the gate1 step name "pre-build" contains the build substring,
        # so CONTENT matches it into A (fix-content; a poison-token red is
        # semantically a content red — the same free-ride as the
        # gate5/attest word faces is acceptable) — not the §3.1-recorded
        # "zero hits -> UNRECOGNIZED fallback"; the "five-family skeleton
        # usable as-is" criterion is unaffected (no missed reds, no
        # misfires).  Added note: the gate2 row was originally pinned
        # UNRECOGNIZED (the state of the tool when the v48 compatibility table
        # was written) — after the six Main retro events' manually identified
        # evidence admitted the gate2-only cascade shape into the taxonomy
        # (the E variant, part 10 below), this row is now pinned
        # E-coqchk-skipped; the fallback rows are down to gate3/RAM/
        # tree-stats-gen (three names; a self-audit note; the survey doc §8
        # reading is not retroactively rewritten).
        MAIN_JOB_NAME = ("Rocq 9.3 build + coqchk "
                         "(self-hosted seed cache, Windows)")
        MAIN_STEPS = [
            "Set up job",
            "actions/checkout@v5",
            "gate1 poison-token guard (pre-build fail-fast)",
            "gate4 comment guard (pre-build, exit1=red exit2=yellow artifact-only)",
            "gate3 cross-tree require-face diff",
            "Seed trust cache from local vo tree",
            "RAM guard (report commit headroom before heavy phase)",
            "Build full tree (order topology, fingerprint skip, thermal-guarded)",
            "Generate tree-stats (six-dimension counts, three-caliber breakdown)",
            "Upload tree-stats",
            "gate5 vo-binary quarantine (pre-coqchk, token+digest, control-calibrated)",
            "attest reconcile (archive-hit -> skip list, miss -> coqchk, cw.attest/v1)",
            "coqchk full-tree certification (parallel root-grouped, thermal-guarded)",
            "Upload vo trust cache (cross-machine sync)",
            "gate2 axioms sentinel (block-state-machine, fail-loud; attest branch)",
            "Upload coqchk logs",
        ]
        main_path = fx("main_coq93")
        assert os.path.isfile(main_path), \
            "Main-shape fixture missing (the real-form file set must be present): %s" % main_path
        out = os.path.join(tmp, "main_coq93.json")
        p = run(["--offline", main_path, "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        repM = json.load(io.open(out, encoding="utf-8"))
        assert repM["schema"] == SCHEMA and repM["family"] == "none" \
            and repM["action"] == "watch-only", (repM["family"],
                                                 repM["action"])
        jm = repM["jobs"][0]
        assert jm["name"] == MAIN_JOB_NAME, jm["name"]
        assert [s["name"] for s in jm["steps"]] == MAIN_STEPS, \
            "the Main real-form step names broke (16 names, ordered as taken from coq93.yml)"
        assert all(s["conclusion"] == "success" for s in jm["steps"]), \
            "the Main passing sample should have every step succeed"
        # determinism: the Main fixture rerun with the same input is byte-identical in --json
        out2 = os.path.join(tmp, "main_coq93.2.json")
        p = run(["--offline", main_path, "--json", out2])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(out2, "rb").read() == io.open(out, "rb").read(), \
            "Main-shape json byte drift = violation"
        # compatibility-table line-by-line mechanical check (real-form single-red-step shapes; no log; the step-name B rule precedes step-name A)
        MAIN_COMPAT = [
            ("Build full tree (order topology, fingerprint skip, thermal-guarded)",
             "A-content-red"),
            ("coqchk full-tree certification (parallel root-grouped, thermal-guarded)",
             "A-content-red"),
            ("gate5 vo-binary quarantine (pre-coqchk, token+digest, control-calibrated)",
             "A-content-red"),
            ("attest reconcile (archive-hit -> skip list, miss -> coqchk, cw.attest/v1)",
             "A-content-red"),
            ("gate1 poison-token guard (pre-build fail-fast)", "A-content-red"),
            ("actions/checkout@v5", "B-netred"),
            ("Seed trust cache from local vo tree", "B-netred"),
            ("Upload tree-stats", "B-netred"),
            ("Upload vo trust cache (cross-machine sync)", "B-netred"),
            ("Upload coqchk logs", "B-netred"),
            ("gate4 comment guard (pre-build, exit1=red exit2=yellow artifact-only)",
             "B-netred"),
            ("gate3 cross-tree require-face diff", "UNRECOGNIZED"),
            ("gate2 axioms sentinel (block-state-machine, fail-loud; attest branch)",
             "E-coqchk-skipped"),
            ("RAM guard (report commit headroom before heavy phase)",
             "UNRECOGNIZED"),
            ("Generate tree-stats (six-dimension counts, three-caliber breakdown)",
             "UNRECOGNIZED"),
        ]
        for nm, fam in MAIN_COMPAT:
            c = classify(mkjob(id=31,
                               steps=[mkstep(1, nm, "failure")]))
            assert c["family"] == fam, \
                ("Main-shape reading vector mismatch", nm, fam, c["family"])
        # word-face reef / free-ride mechanical pins: gate4's artifact substring
        # -> the step-name B rule judges first (a §3.1 reef row; the Set repo
        # :120 same-kind, not Main-specific); gate1's pre-build substring ->
        # the step-name A free-ride
        c = classify(mkjob(id=33, steps=[mkstep(
            1, "gate4 comment guard (pre-build, exit1=red exit2=yellow"
               " artifact-only)", "failure")]))
        assert c["family"] == "B-netred" and any(
            "network-adjacent step" in e and "artifact" in e
            for e in c["evidence"]), c
        c = classify(mkjob(id=34, steps=[mkstep(
            1, "gate1 poison-token guard (pre-build fail-fast)", "failure")]))
        assert c["family"] == "A-content-red" and any(
            "content step" in e for e in c["evidence"]), c
        # the E family Main form with both legs present (the §3.1 E row: an
        # upload red + a coqchk skipped step; with both Main step names in place
        # E can fire): Upload coqchk logs red + the coqchk step skipped
        e_main = [mkstep(1, "Build full tree (order topology, fingerprint"
                            " skip, thermal-guarded)", "success"),
                  mkstep(2, "Upload coqchk logs", "failure"),
                  mkstep(3, "coqchk full-tree certification (parallel"
                            " root-grouped, thermal-guarded)", "skipped",
                         started_at=None, completed_at=None),
                  mkstep(4, "gate2 axioms sentinel (block-state-machine,"
                            " fail-loud; attest branch)", "skipped",
                         started_at=None, completed_at=None)]
        c = classify(mkjob(id=32, steps=e_main))
        assert c["family"] == "E-coqchk-skipped", c
        assert any("coqchk" in e for e in c["evidence"]), c

        # part 10: the gate2-only E-variant reading vectors (the review-ledger
        # token-dichotomy acceptance line: banner-absent = E x4 /
        # ATTEST-RED = UNREC x1) plus the logs two-hop 415 fix vectors (all
        # canned, zero network)
        G2_RED = ("gate2 axioms sentinel (block-state-machine, fail-loud;"
                  " attest branch)")
        # 1) the two real-form fixture readings (canned job_logs genuinely
        #    executed lines judge): cancelled (run#7, a genuinely executed
        #    banner-absent line at 13:22:43Z + 2 dump lines) -> stays E;
        #    failure (run#10, genuinely executed GATE2-ATTEST-RED/判定=CLEAN
        #    lines + banner-absent only as a dump line + coqchk success) -> the
        #    UNRECOGNIZED conversion acceptance verdict (machine ruling =
        #    review ruling; the E false positive discharged)
        for stem, fam, act, concl in (
                ("gate2_only_cancelled", "E-coqchk-skipped",
                 "rerun-after-stable-window", "cancelled"),
                ("gate2_only_failure", "UNRECOGNIZED", "watch-only",
                 "failure")):
            path = fx(stem)
            assert os.path.isfile(path), "gate2-only fixture missing: %s" % path
            out = os.path.join(tmp, stem + ".json")
            p = run(["--offline", path, "--json", out])
            assert p.returncode == 0, p.stdout[-400:]
            rep = json.load(io.open(out, encoding="utf-8"))
            assert rep["schema"] == SCHEMA and rep["family"] == fam \
                and rep["action"] == act, (stem, rep["family"], rep["action"])
            assert rep["jobs"][0]["conclusion"] == concl, \
                (stem, rep["jobs"][0]["conclusion"])
            cj = rep["jobs"][0]["classification"]
            assert cj["family"] == fam and cj["red_steps"] == [G2_RED], cj
            assert any("offline canned logs 1" in e
                       for e in rep["evidence"]), rep["evidence"]
            if stem.endswith("cancelled"):
                assert any("gate2-only cascade" in e for e in cj["evidence"]), cj
                assert any("log confirmation: GATE-BANNER-ABSENT" in e
                           for e in cj["evidence"]), cj
                assert any("dump lines dropped=2" in e
                           for e in cj["evidence"]), cj
            else:
                assert any("conclusion-position validation" in e
                           and "attested-red auth-state" in e
                           for e in cj["evidence"]), cj
                assert any("auth-state-red-maintained" in e
                           for e in cj["evidence"]), cj
                assert any("log[GATE2-ATTEST-RED]" in e
                           for e in cj["evidence"]), cj  # log[...] = KEY_LOG_PATTERNS tag citations (data)
                assert any("log[判定=CLEAN]" in e for e in cj["evidence"]), cj
                assert any("log[R4-覆盖划分]" in e for e in cj["evidence"]), cj
                assert any("log[APPENDIX-缺]" in e for e in cj["evidence"]), cj
                assert not any("log confirmation: GATE-BANNER-ABSENT" in e
                               for e in cj["evidence"]), \
                    ("a dump-only banner must never confirm"
                     " (the review-ledger evidence trap)")
                assert any("dump lines dropped=1" in e
                           for e in cj["evidence"]), cj
        # 2) four vectors stay E (the review-ledger phase-1 banner-absent form;
        #    classify called directly with genuinely executed lines canned):
        #    #7 (Build cancelled -> coqchk skipped -> gate2 red + a real banner
        #    line); the #8/#20 shapes (Build success -> coqchk cancelled ->
        #    gate2 red); the #26 shape (same steps as #7, no log -> the banner
        #    token unconfirmed, noted as-is, still E)
        g2_steps = [mkstep(1, "Build full tree (order topology, fingerprint"
                           " skip, thermal-guarded)", "cancelled"),
                    mkstep(2, "coqchk full-tree certification (parallel"
                              " root-grouped, thermal-guarded)", "skipped",
                           started_at=None, completed_at=None),
                    mkstep(3, G2_RED, "failure")]
        # KEEP (data faces): BANNER_REAL / ATT_REAL replicate the real CI
        # logs' own lines verbatim (the review-ledger ground truth) — they are
        # fixture log content, never rewritten.
        BANNER_REAL = ("2026-11-06T13:22:43Z GATE-BANNER-ABSENT _chk_all.log"
                       " 不在盘——coqchk 未产出日志（上游 gate4/build 夭折连带，"
                       "红因看上游步）·非 COQLIB 代际失守")
        ATT_REAL = ("2026-11-07T17:18:52Z 判定=CLEAN(exit 0) Axioms段数=14"
                    " 公理总数=0 日志完整=True\n2026-11-07T17:18:53Z "
                    "GATE2-ATTEST-RED: 认证态覆盖断言不备")
        c = classify(mkjob(id=71, conclusion="cancelled", steps=g2_steps),
                     log_text=BANNER_REAL)
        assert c["family"] == "E-coqchk-skipped" \
            and c["action"] == "rerun-after-stable-window" \
            and any("gate2-only cascade" in e for e in c["evidence"]) \
            and any("log confirmation: GATE-BANNER-ABSENT" in e
                    for e in c["evidence"]), c
        for jid in (81, 82):
            c = classify(mkjob(id=jid, conclusion="cancelled", steps=[
                mkstep(1, "Build full tree (order topology, fingerprint"
                         " skip, thermal-guarded)", "success"),
                mkstep(2, "coqchk full-tree certification (parallel"
                         " root-grouped, thermal-guarded)", "cancelled"),
                mkstep(3, G2_RED, "failure")]), log_text=BANNER_REAL)
            assert c["family"] == "E-coqchk-skipped" and any(
                "gate2-only cascade" in e for e in c["evidence"]), (jid, c)
        c = classify(mkjob(id=83, conclusion="cancelled", steps=g2_steps))
        assert c["family"] == "E-coqchk-skipped" and any(
            "banner token unconfirmed" in e for e in c["evidence"]), c
        # 3) the #10 conversion vector (the attested-red auth-state shape;
        #    machine ruling UNREC = review ruling; review-ledger phase 2):
        #    a. the token-direct-evidence shape (canned genuinely executed
        #    lines) -> UNRECOGNIZED; b. the second-discriminator shape (no log,
        #    coqchk success ran to completion = not the artifacts-missing
        #    mechanism) -> UNRECOGNIZED; c. the auth-state tokens never enter
        #    any red word-face regex (the precondition for falling through to the
        #    UNREC fallback)
        steps10 = [mkstep(1, "Build full tree (order topology, fingerprint"
                          " skip, thermal-guarded)", "success"),
                   mkstep(2, "attest reconcile (archive-hit -> skip list,"
                             " miss -> coqchk, cw.attest/v1)", "success"),
                   mkstep(3, "coqchk full-tree certification (parallel"
                             " root-grouped, thermal-guarded)", "success"),
                   mkstep(4, "Upload vo trust cache (cross-machine sync)",
                          "success"),
                   mkstep(5, G2_RED, "failure")]
        c = classify(mkjob(id=84, steps=steps10), log_text=ATT_REAL)
        assert c["family"] == "UNRECOGNIZED" and c["action"] == "watch-only", c
        assert any("conclusion-position validation" in e
                   and "attested-red auth-state" in e
                   for e in c["evidence"]), c
        assert any("auth-state-red-maintained" in e for e in c["evidence"]), c
        assert any("log[GATE2-ATTEST-RED]" in e for e in c["evidence"]), c
        c = classify(mkjob(id=85, steps=steps10))
        assert c["family"] == "UNRECOGNIZED" and any(
            "coqchk step succeeded" in e for e in c["evidence"]), c
        for s in ["GATE2-ATTEST-RED: 认证态覆盖断言不备",
                  "判定=CLEAN(exit 0) Axioms段数=14 公理总数=0 日志完整=True",
                  "R4 覆盖划分破: skipped∪sent != surface 或交集非空或面空",
                  "appendix={present:false}"]:
            assert not RED_CONTENT_RE.search(s) and not RED_NET_RE.search(s) \
                and not RED_ABORT_RE.search(s), \
                "an auth-state token wrongly matched a red word face: %s" % s
        # 4) dump-line filtering vectors (the review-ledger evidence trap;
        #    canned, zero network): a. dump lines mixed with genuinely executed
        #    lines -> the dropped note + the genuine line confirms; b. the S6
        #    trap shape (the banner only as a dump line; the #10 step truth of
        #    coqchk success) -> no confirmation -> UNREC (the filter works);
        #    c. the same trap shape with --no-dump-filter (filter off) -> the
        #    dump line confirms verbatim (the trap re-forms as-is)
        DUMP_LINE = ("2026-11-07T17:18:49.5000000Z \x1b[36;1mif [ ! -f "
                     "\"_chk_all.log\" ]; then echo GATE-BANNER-ABSENT; "
                     "exit 1; fi\x1b[0m")
        c = classify(mkjob(id=71, conclusion="cancelled", steps=g2_steps),
                     log_text=DUMP_LINE + "\n" + BANNER_REAL)
        assert c["family"] == "E-coqchk-skipped" and any(
            "dump lines dropped=1" in e for e in c["evidence"]), c
        assert any("log[GATE-BANNER-ABSENT]" in e for e in c["evidence"]), c
        c = classify(mkjob(id=86, steps=steps10), log_text=DUMP_LINE)
        assert c["family"] == "UNRECOGNIZED" and not any(
            "log confirmation: GATE-BANNER-ABSENT" in e
            for e in c["evidence"]), c
        assert any("dump lines dropped=1" in e for e in c["evidence"]), c
        c = classify(mkjob(id=87, conclusion="cancelled", steps=g2_steps),
                     log_text=DUMP_LINE, dump_filter=False)
        assert c["family"] == "E-coqchk-skipped" and any(
            "log confirmation: GATE-BANNER-ABSENT" in e
            for e in c["evidence"]), c
        assert any("36;1m" in e for e in c["evidence"]), \
            "with filtering off the dump line enters evidence verbatim (the trap re-forms as-is)"
        # 5) the five-token roster vector (each review-ledger roster candidate
        #    judged positively against its real ledger form; every member
        #    rostered) plus the out-of-roster candidates never impersonate
        #    rostered members (the negative)
        for tag, line in [
                ("GATE2-ATTEST-RED", "GATE2-ATTEST-RED: 认证态覆盖断言不备"),
                ("判定=CLEAN",
                 "判定=CLEAN(exit 0) Axioms段数=14 公理总数=0 日志完整=True"),
                ("公理总数", "公理总数=0"),
                ("R4-覆盖划分",
                 "R4 覆盖划分破: skipped∪sent != surface 或交集非空或面空"),
                ("APPENDIX-缺", "appendix={present:false}")]:
            hits = [rx for t, rx in KEY_LOG_PATTERNS if t == tag]
            assert len(hits) == 1, "token not rostered or double-rostered: %s" % tag
            assert hits[0].search(line), "the token positive does not match: %s" % tag
            evl = scan_log_evidence(line)
            assert any(e.startswith("log[%s]" % tag) for e in evl), (tag, evl)
        assert not any("GATE2-AXIOMS-RED" in t or "GATE5-RED" in t
                       or "ATT-RECON-FAIL" in t for t, _ in KEY_LOG_PATTERNS), \
            "the review-ledger's three other candidates stay out of this round's five-token list and never impersonate rostered members"
        # 6) five negative rules: a proper build/coqchk content red -> A (the
        #    cascade is broken); the "Upload artifact (gate2 ledger)" gate2
        #    substring free-riding upload red -> B (the anti-swallow pin); a
        #    red step that is neither gate2 nor upload -> UNRECOGNIZED; a
        #    failure with zero red steps (the runner-lost shape = provenance
        #    event #3 of the six) -> UNRECOGNIZED, never force-fitted
        c = classify(mkjob(id=73, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", "failure"),
            mkstep(2, G2_RED, "failure")]))
        assert c["family"] == "A-content-red", c
        c = classify(mkjob(id=74, steps=[
            mkstep(1, "coqchk full-tree certification (parallel"
                     " root-grouped, thermal-guarded)", "failure"),
            mkstep(2, G2_RED, "failure")]))
        assert c["family"] == "A-content-red", c
        c = classify(mkjob(id=75, steps=[
            mkstep(1, "Upload artifact (gate2 ledger)", "failure"),
            mkstep(2, "COQCHK", "success")]))
        assert c["family"] == "B-netred", \
            "the gate2 substring free-riding upload red still lands in B (anti-swallow), got %s" % c["family"]
        c = classify(mkjob(id=76, steps=[
            mkstep(1, "Generate tree-stats (six-dimension counts,"
                     " three-caliber breakdown)", "failure")]))
        assert c["family"] == "UNRECOGNIZED", c
        c = classify(mkjob(id=77, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", None, status="in_progress",
                     conclusion=None)]))
        assert c["family"] == "UNRECOGNIZED", \
            "the runner-lost zero-red-step shape stays out of the taxonomy, never force-fitted, got %s" % c["family"]
        # 7) CLI vector: --no-dump-filter (the #10 canned fixture; filter off
        #    -> the dump-line banner enters the criteria; the auth-state token
        #    and the banner dump coexist -> the second discriminator falls back
        #    to UNREC with a run-level loud note) + job_logs malformed
        #    fail-loud 9 + canned-log byte-identical determinism
        out = os.path.join(tmp, "g10_nodumpfilter.json")
        p = run(["--offline", fx("gate2_only_failure"), "--no-dump-filter",
                 "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        rep = json.load(io.open(out, encoding="utf-8"))
        assert rep["family"] == "UNRECOGNIZED" \
            and rep["action"] == "watch-only", (rep["family"], rep["action"])
        assert any("filtering disabled" in e and "--no-dump-filter" in e
                   for e in rep["evidence"]), rep["evidence"]
        cj = rep["jobs"][0]["classification"]
        assert any("coqchk step succeeded" in e for e in cj["evidence"]), cj
        assert any("36;1m" in e for e in cj["evidence"]), cj
        bad = os.path.join(tmp, "bad_logs.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 1, "jobs": [mkjob()],
                       "job_logs": {"1": 42}}, fh)
        p = run(["--offline", bad])
        assert p.returncode == 9, "malformed job_logs should fail loud with 9, got %d" \
            % p.returncode
        outa = os.path.join(tmp, "g10_det_a.json")
        outb = os.path.join(tmp, "g10_det_b.json")
        p = run(["--offline", fx("gate2_only_failure"), "--json", outa])
        assert p.returncode == 0, p.stdout[-400:]
        p = run(["--offline", fx("gate2_only_failure"), "--json", outb])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(outa, "rb").read() == io.open(outb, "rb").read(), \
            "canned-log classification json byte drift = violation"
        # 8) the logs two-hop 415 fix vector (canned _open injection; zero
        #    network): the fixed form hop1 Accept=LOGS_ACCEPT (not the
        #    text/plain 415 debt) -> 302 Location -> hop2 zero Authorization ->
        #    200 with the log text; the old-form 415 original code enters
        #    evidence as the contrast; the second-hop 403 Azure form enters
        #    evidence with its original code; a redirect without Location
        #    enters evidence as a malformed shape.
        assert LOGS_ACCEPT == "application/vnd.github+json" \
            and LOGS_ACCEPT != "text/plain", LOGS_ACCEPT

        def _redirect_err(code, loc):
            return urllib.error.HTTPError(
                "https://x", code, "HTTP Error %d" % code,
                {"Location": loc}, io.BytesIO(b""))

        cap = []
        slept = []

        def _open_2hop(req, timeout=None):
            cap.append((str(req.full_url), dict(req.headers)))
            if len(cap) == 1:
                raise _redirect_err(
                    302, "https://blob.example/job-logs.txt?sig=1")
            return _Resp(b"BUILD LOG\nGATE-BANNER-ABSENT\n")

        text, note = fetch_job_log("o/r", 42, "tok", 5,
                                   _open=_open_2hop, _sleep=slept.append)
        assert text == "BUILD LOG\nGATE-BANNER-ABSENT\n" and note is None, \
            (text, note)
        assert len(cap) == 2, cap
        u1, h1 = cap[0]
        u2, h2 = cap[1]
        assert "/actions/jobs/42/logs" in u1, u1
        assert h1.get("Accept") == LOGS_ACCEPT \
            and h1.get("Authorization") == "token tok", h1
        assert u2.startswith("https://blob.example/job-logs.txt"), u2
        assert "Authorization" not in h2, \
            "the second hop must send zero Authorization (the live-probed 403 Azure form when the token is forwarded)"
        assert h2.get("Accept") == LOGS_ACCEPT, h2
        assert slept == [], "the two-hop vector: zero retries, zero sleeps"
        cap = []
        slept = []

        def _open_415(req, timeout=None):
            cap.append(str(req.full_url))
            raise _http_err(415)

        text, note = fetch_job_log("o/r", 42, "tok", 5,
                                   _open=_open_415, _sleep=slept.append)
        assert text is None and note is not None and "HTTP 415" in note, \
            (text, note)
        assert "415" in note and "logs-GET" in note, note
        assert slept == [], "the 415 semantic error: no retry, zero sleeps"
        cap = []
        slept = []

        def _open_2hop_403(req, timeout=None):
            cap.append(str(req.full_url))
            if len(cap) == 1:
                raise _redirect_err(
                    302, "https://blob.example/job-logs.txt?sig=1")
            raise _http_err(403)

        text, note = fetch_job_log("o/r", 42, "tok", 5,
                                   _open=_open_2hop_403, _sleep=slept.append)
        assert text is None and note is not None and "HTTP 403" in note, \
            (text, note)
        assert slept == [], "a failed second hop: no retry, zero sleeps"

        def _open_noloc(req, timeout=None):
            raise _redirect_err(302, "")

        text, note = fetch_job_log("o/r", 42, "tok", 5,
                                   _open=_open_noloc, _sleep=slept.append)
        assert text is None and note is not None \
            and "no Location" in note, (text, note)

        # part 12: the two-shape evidence-note vectors (the two
        # maintained-UNREC shapes; the family-judging face unchanged;
        # evidence enhancement only):
        # 1) shape 1, runner-lost-candidate: the Main#3 real-form fixture
        #    (failure + zero red steps + the Build step hung in_progress + a
        #    canned logs-GET 404 note) -> UNRECOGNIZED maintained + all four
        #    note legs in evidence + byte-identical determinism
        rl_path = fx("runner_lost")
        assert os.path.isfile(rl_path), "runner-lost fixture missing: %s" % rl_path
        out = os.path.join(tmp, "runner_lost.json")
        p = run(["--offline", rl_path, "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        rep = json.load(io.open(out, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["family"] == "UNRECOGNIZED" \
            and rep["action"] == "watch-only", (rep["family"],
                                                rep["action"])
        cj = rep["jobs"][0]["classification"]
        assert cj["family"] == "UNRECOGNIZED" \
            and cj["action"] == "watch-only", cj
        assert cj["red_steps"] == [], cj
        assert any("runner-lost-candidate: job failure + zero failed steps"
                   in e for e in cj["evidence"]), cj
        assert any("build step hung in_progress (Build full tree" in e
                   for e in cj["evidence"]), cj
        assert any("wall clock: 57007s" in e for e in cj["evidence"]), cj
        assert any("rationale" in e and "no force-fit" in e
                   for e in cj["evidence"]), cj
        assert any("logs-GET: HTTP 404" in e and "BlobNotFound" in e
                   for e in cj["evidence"]), cj
        assert any("offline canned log-fetch notes 1" in e
                   for e in rep["evidence"]), rep["evidence"]
        out2 = os.path.join(tmp, "runner_lost.2.json")
        p = run(["--offline", rl_path, "--json", out2])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(out2, "rb").read() == io.open(out, "rb").read(), \
            "runner-lost json byte drift = violation"
        # 2) shape 1, four negatives (classify called directly; any single
        #    missing leg kills the note; the plain UNREC fallback unchanged —
        #    the family-judging face untouched): a. no logs note; b. the note
        #    is not a 404; c. the hung step is not build-family (an upload
        #    hang); d. red steps present (A judges as usual).
        #    KEEP (data faces): RL_NOTE_404 and the inline canned notes below
        #    replicate the real evidence-note format including its Chinese
        #    suffix — fixture input data, never rewritten.
        RL_NOTE_404 = ("logs-GET: HTTP 404 <Error><Code>BlobNotFound</Code>"
                       "</Error>（日志不可达·入证据）")
        HUNG_BUILD = mkstep(2, "Build full tree (order topology, fingerprint"
                               " skip, thermal-guarded)", None,
                            status="in_progress", conclusion=None)
        c = classify(mkjob(id=91, steps=[HUNG_BUILD]))
        assert c["family"] == "UNRECOGNIZED" and not any(
            "runner-lost-candidate" in e for e in c["evidence"]), c
        c = classify(mkjob(id=92, steps=[HUNG_BUILD]),
                     log_note="logs-GET: HTTP 403 Azure AuthenticationFailed"
                              "（日志不可达·入证据）")  # canned note input (data face, kept)
        assert c["family"] == "UNRECOGNIZED" and not any(
            "runner-lost-candidate" in e for e in c["evidence"]), c
        c = classify(mkjob(id=93, steps=[
            mkstep(1, "Upload tree-stats", None, status="in_progress",
                   conclusion=None)]), log_note=RL_NOTE_404)
        assert c["family"] == "UNRECOGNIZED" and not any(
            "runner-lost-candidate" in e for e in c["evidence"]), c
        c = classify(mkjob(id=94, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", "failure"),
            mkstep(2, "gate2 axioms sentinel (block-state-machine,"
                     " fail-loud; attest branch)", None, status="in_progress",
                   conclusion=None)]), log_note=RL_NOTE_404)
        assert c["family"] == "A-content-red" and not any(
            "runner-lost-candidate" in e for e in c["evidence"]), c
        # 3) shape 2, auth-state-red-maintained: two pair negatives (the
        #    fixture positive is asserted in part 10.1): a single token on the
        #    roster (only ATTEST-RED or only 判定=CLEAN) -> only the old
        #    exclusion note, the pair note never fires (the pair criterion =
        #    both tokens genuinely executed together)
        c = classify(mkjob(id=95, steps=steps10),
                     log_text="2026-11-07T17:18:53Z GATE2-ATTEST-RED: "
                              "认证态覆盖断言不备\n")
        assert c["family"] == "UNRECOGNIZED" and any(
            "conclusion-position validation" in e for e in c["evidence"]), c
        assert not any("auth-state-red-maintained" in e
                       for e in c["evidence"]), c
        c = classify(mkjob(id=96, steps=steps10),
                     log_text="2026-11-07T17:18:52Z 判定=CLEAN(exit 0) "
                              "Axioms段数=14 公理总数=0 日志完整=True\n")
        assert c["family"] == "UNRECOGNIZED", c
        assert not any("auth-state-red-maintained" in e
                       for e in c["evidence"]), c
        # 4) job_log_notes malformed fails loud with 9 (the same judging face as malformed job_logs)
        bad_notes = os.path.join(tmp, "bad_notes.json")
        with io.open(bad_notes, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 1, "jobs": [mkjob()],
                       "job_log_notes": {"1": 42}}, fh)
        p = run(["--offline", bad_notes])
        assert p.returncode == 9, "malformed job_log_notes should fail loud with 9, got %d" \
            % p.returncode

        # part 13: the evidence-annihilation candidate (R19) vectors (the
        # docs/ci-triage-table.json v1.5 row; family unchanged, evidence
        # enhanced only): a zero-byte injected log with every outcome recorded
        # ("rc recorded" + "log/output bytes = 0") fires the three-marker R19
        # note; the note rides before the family branches, so a red Build
        # step still judges A via the step name (no reclassification).
        # Positives: the empty string and the whitespace-only form.
        # Negatives (any one missing leg kills the note): no fetch
        # (log_text=None); the note channel instead (a failed fetch = the
        # runner-lost shape: an unreachable log, not an annihilated one); a
        # non-empty log; an outcome not recorded (a step hung with
        # conclusion=None: rc not recorded).  End-to-end: a canned fixture
        # with job_logs {"<id>": ""} carries the note in --json and stays
        # byte-identical on rerun.
        steps_r19 = [mkstep(1, "Build (coqc batch)", "failure")]
        c = classify(mkjob(id=101, steps=steps_r19), log_text="")
        assert c["family"] == "A-content-red", \
            ("the R19 note never reclassifies (the step-name A rule judges)",
             c["family"])
        note19 = [e for e in c["evidence"]
                  if e.startswith("evidence annihilation candidate (R19)")]
        assert len(note19) == 1, c["evidence"]
        for marker in ("rc recorded", "log/output bytes = 0",
                       "evidence annihilation"):
            assert any(marker in e for e in note19), (marker, note19)
        assert "the capture mechanism is the disease" in note19[0], note19
        c = classify(mkjob(id=102, steps=steps_r19), log_text="\n  \n")
        assert any("evidence annihilation candidate (R19)" in e
                   for e in c["evidence"]), c
        c = classify(mkjob(id=103, steps=steps_r19))
        assert not any("evidence annihilation candidate (R19)" in e
                       for e in c["evidence"]), \
            ("no fetch (log_text=None) is not annihilation", c["evidence"])
        c = classify(mkjob(id=104, steps=steps_r19), log_note=RL_NOTE_404)
        assert not any("evidence annihilation candidate (R19)" in e
                       for e in c["evidence"]), \
            ("a failed fetch (the note channel) is a different shape, not"
             " R19", c["evidence"])
        c = classify(mkjob(id=105, steps=steps_r19),
                     log_text="BUILD LOG\nsome real execution line\n")
        assert not any("evidence annihilation candidate (R19)" in e
                       for e in c["evidence"]), \
            ("a non-empty log is not R19", c["evidence"])
        c = classify(mkjob(id=106, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", None, status="in_progress",
                   conclusion=None)]), log_text="")
        assert not any("evidence annihilation candidate (R19)" in e
                       for e in c["evidence"]), \
            ("an outcome not recorded (rc not recorded) is not R19",
             c["evidence"])
        ann = os.path.join(tmp, "annihilated.json")
        with io.open(ann, "w", encoding="utf-8") as fh:
            json.dump({"total_count": 1,
                       "jobs": [mkjob(id=107, steps=[
                           mkstep(1, "Build (coqc batch)", "failure")])],
                       "job_logs": {"107": ""}}, fh)
        out = os.path.join(tmp, "annihilated.out.json")
        p = run(["--offline", ann, "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        rep = json.load(io.open(out, encoding="utf-8"))
        cj = rep["jobs"][0]["classification"]
        assert cj["family"] == "A-content-red", cj
        assert any("evidence annihilation candidate (R19)" in e
                   for e in cj["evidence"]), cj
        out2 = os.path.join(tmp, "annihilated.out.2.json")
        p = run(["--offline", ann, "--json", out2])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(out2, "rb").read() == io.open(out, "rb").read(), \
            "annihilation-shape json byte drift = violation"

        print("CI-TRIAGE-SELFTEST PASS: the six family samples all hit / the"
              " 13.3x baseline example + the loud absent-step note / classifier"
              " units (regex positives-negatives; cascade; in-flight; E-shapes"
              " are not content reds; UNRECOGNIZED) / netrc parsing /"
              " byte-identical determinism / CLI four codes / the backoff layer"
              " (403x3 -> [2,4,8]; Retry-After honored; 403 exhausted -> 9; 401"
              " no retry) / the Main-shape reading vector (the coq93 real form,"
              " 16 step names pinned + the 15-row compatibility table + E with"
              " both legs) / the token-dichotomy vectors (#7 fixture"
              " banner-absent canned -> E; the #8/#20/#26 shape vectors stay E;"
              " the #10 fixture attested-red canned -> the UNREC conversion"
              " acceptance verdict, machine ruling = review ruling; the"
              " coqchk-success corroboration; the negatives with #3 never"
              " force-fitted) / the dump-line filtering vectors (a dump-only"
              " banner never confirms; a genuinely executed line confirms; the"
              " --no-dump-filter trap re-forms as-is) / the five-token roster"
              " vector (all review-ledger roster candidates) / job_logs"
              " malformed -> 9 / canned determinism / the logs two-hop 415 fix"
              " vector (302 -> the zero-Authorization second hop -> 200; the"
              " 415/403/no-Location original codes enter evidence) / the"
              " two-shape evidence-note vectors (runner-lost-candidate fixture"
              " four-legs pass + wall clock + canned 404 note + determinism +"
              " four negatives; the auth-state-red-maintained fixture pair note"
              " + two single-token negatives; malformed job_log_notes -> 9) /"
              " the evidence-annihilation candidate (R19) vectors (the"
              " triage-table v1.5 row: a zero-byte log with rc recorded fires"
              " the three-marker R19 note on evidence only, the family face"
              " unchanged; two positives + four negatives + the canned-fixture"
              " end-to-end run with determinism)"
              " — all pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
