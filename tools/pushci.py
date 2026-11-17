#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pushci.py: one-shot push-then-CI pipeline orchestrator for rocqwash (tools/).

    Purpose.  Run the post-fix push-and-CI sequence as one command: preflight
      checks, push, run watch, heal, verdict, optional PR merge. The four
      existing tools (doctor, net_probe, ci_triage, gate4) always run as
      subprocesses; this file supplies only the glue and the state machine.

    Interface.  python tools/pushci.py --repo-path DIR --branch B [--base-ref
      main] [--steps preflight,push,watch,heal,verdict] plus the optional
      flags listed by --help; offline testability via paired --injector +
      --git-caller canned scenarios and --sleep-scale 0. Report (--json)
      schema rocqwash-pushci/1; verdict in success|fix-content|toolchain|
      unstable|heal-exhausted|gate4-block|dry-run; stage dependencies
      watch=>push, heal=>watch, --merge=>watch.

    Dependencies.  Python 3 stdlib only; same-directory _http_backoff imported
      via sys.path injection (no __init__ package layout); git on PATH; the
      only environment fallback is ROCQWASH_MASK; netrc read lazily.

    Evidence.  --selftest: eight scenario vectors + flat-shape, ghproxy,
      push-failure, unit, resilience and CLI-exit vectors + byte-identical
      rerun determinism; zero real network, zero real push (--netrc points
      at a nonexistent path); suite membership tests/test_pushci.py.

    Exit-codes.  0 = success/dry-run; 1 = heal-exhausted/unstable/toolchain;
      2 = fix-content/gate4-block/usage error; 9 = target missing (repo,
      remote, branch, PR, toolchain component, netrc, API unreachable, API
      4xx/5xx hard error, watch round cap, subprocess timeout kill);
      --selftest: 0 = all pass, 2 = assertion failure.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PROG = "pushci"
SCHEMA = "rocqwash-pushci/1"
API_ROOT = "https://api.github.com"
GHPROXY_PREFIX = "https://ghproxy.net/"
GHPROXY_HOST = "github.com"
PUSH_HTTP_VERSION = "HTTP/1.1"
PUSH_TRIES = 3
PUSH_RETRY_WAIT = 45
GHPROXY_TRIES = 2
MERGE_409_WAIT = 60
MERGE_409_RETRIES = 3
HEAL_RERUN_FAMILIES = ("B-netred", "E-coqchk-skipped")
STAGE_ALL = ("preflight", "push", "watch", "heal", "verdict")
RUNS_QUERY = "/actions/runs?per_page=30"
WATCH_POLICY = "status-only (a frozen updated_at is not a stall criterion; status is authoritative)"

# verdict-to-exit-code table (0=success/dry-run; 1=heal-exhausted/unstable/
# toolchain; 2=fix-content/gate4-block; exit 9 is reserved for fail-loud
# missing targets and never passes through this table)
VERDICT_EXIT = {
    "success": 0,
    "dry-run": 0,
    "heal-exhausted": 1,
    "unstable": 1,
    "toolchain": 1,
    "fix-content": 2,
    "gate4-block": 2,
}

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
DOCTOR_TOOL = os.path.join(TOOLS_DIR, "toolchain_dyld_doctor.py")
PROBE_TOOL = os.path.join(TOOLS_DIR, "net_probe.py")
TRIAGE_TOOL = os.path.join(TOOLS_DIR, "ci_triage.py")
GATE4_TOOL = os.path.join(REPO_ROOT, "verify", "gate4_comment_guard.py")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)   # shared same-directory backoff module (no __init__ package layout)
import _http_backoff


class PushciError(Exception):
    """Fail-loud exception carrying an exit code (code: 2 = usage/scenario-shape error, 9 = missing target / hard API error)."""

    def __init__(self, msg, code=9):
        super(PushciError, self).__init__(msg)
        self.code = code


class StopVerdict(Exception):
    """Pipeline stop verdict (carries the verdict out; code is the exit-code caliber; evidence lands in the report)."""

    def __init__(self, verdict, code, evidence=None):
        super(StopVerdict, self).__init__(verdict)
        self.verdict = verdict
        self.code = code
        self.evidence = list(evidence or [])


def subproc_run(cmd, timeout, what, merge_stderr=False):
    """Unified real-subprocess execution with the --timeout anti-hang cap
    (default 120s): on timeout the subprocess is killed (subprocess.run kills
    then raises, no hanging) and a fail-loud 9 names the call. timeout=None
    passes through as uncapped (canned paths spawn no real subprocess)."""
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT if merge_stderr
                              else subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise PushciError("subprocess killed on timeout (--timeout=%ss, "
                          "call: %s)" % (timeout, what), 9)


# ---- small deterministic helpers ---------------------------------------------

def sleep_scaled(sec, scale):
    """time.sleep(sec*scale); scale=0 means zero real sleep (selftest vectors rely on this)."""
    time.sleep(max(0.0, float(sec) * float(scale)))


def url_secret_masks(url):
    """Remote-URL embedded credentials (userinfo password part) to a mask-string list (same convention as watch.py)."""
    masks = []
    for sch in ("https://", "http://"):
        if url.startswith(sch):
            authority = url[len(sch):].partition("/")[0]
            if "@" in authority:
                userinfo = authority.rpartition("@")[0]
                _, _, secret = userinfo.partition(":")
                if secret:
                    masks.append(secret)
            break
    return masks


def mask_text(s, masks):
    """Replace every string in masks with ***MASKED*** (empty entries ignored; same convention as watch.py)."""
    for m in masks:
        if m:
            s = s.replace(m, "***MASKED***")
    return s


def collect_masks(url):
    """Full mask-string set: URL userinfo password part plus env ROCQWASH_MASK
    (colon-separated, watch.py convention; the env fallback accepts only the
    ROCQWASH_* named variable)."""
    masks = url_secret_masks(url)
    env_masks = os.environ.get("ROCWASH_MASK", "")
    masks += [m for m in env_masks.split(":") if m]
    return masks


def url_host(url):
    """Remote URL to host (https://, http://, git@, ssh:// shapes; None outside these shapes)."""
    u = url.strip()
    host = None
    if u.startswith("https://") or u.startswith("http://"):
        authority = u.split("://", 1)[1].partition("/")[0]
        host = authority.rpartition("@")[2]
    elif u.startswith("git@"):
        host = u[len("git@"):].partition(":")[0]
    elif u.startswith("ssh://"):
        authority = u[len("ssh://"):].partition("/")[0]
        host = authority.rpartition("@")[2]
    return host


def repo_from_url(url):
    """Remote URL to ORG/REPO (last two path segments minus .git; https/http/
    git@/ssh shapes; host unrestricted so test-shim fake domains derive the
    same way; the ghproxy reroute has its own https://github.com/ shape gate
    in ghproxy_url). Other shapes or too few segments return None (the
    caller fails loudly)."""
    u = url.strip()
    path = None
    if u.startswith("https://") or u.startswith("http://"):
        path = u.split("://", 1)[1].partition("/")[2]
    elif u.startswith("git@"):
        path = u[len("git@"):].partition(":")[2]
    elif u.startswith("ssh://"):
        path = u[len("ssh://"):].partition("/")[2]
    if not path:
        return None
    seg = [s for s in path.split("/") if s]
    if len(seg) < 2:
        return None
    repo = "/".join(seg[-2:])
    if repo.endswith(".git"):
        repo = repo[:-len(".git")]
    return repo


def ghproxy_url(url):
    """ghproxy reroute URL: only when the remote URL has the https://github.com/
    shape (reroute prefix https://ghproxy.net/https://github.com/), else None
    (skipped loudly)."""
    if url.strip().startswith("https://" + GHPROXY_HOST + "/"):
        return GHPROXY_PREFIX + url.strip()
    return None


def netrc_token(path, machine="github.com"):
    """Manual netrc parsing (same caliber as ci_triage.netrc_token):
    machine <m> login <l> password <p>; single-line 6-column and multi-line
    shapes both accepted; returns the token. Missing file / no entry / empty
    value fail loudly with 9 (the token is never echoed; lazy: read only on
    the first live-mode API call)."""
    if not os.path.isfile(path):
        raise PushciError("netrc missing: %s (live mode needs machine %s ... "
                          "password credentials)" % (path, machine), 9)
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
                    raise PushciError("netrc machine %s password is empty"
                                      % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise PushciError("netrc has no machine %s password entry (single-line "
                      "6-column shape: column 6 = token): %s"
                      % (machine, path), 9)


def snippet(body):
    """API body excerpt for diagnostics, capped at 160 characters."""
    if body is None:
        return ""
    s = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    return s[:160]


def parse_body(raw):
    """Response body to parsed JSON or raw text (empty becomes None)."""
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace") \
        if isinstance(raw, bytes) else str(raw)
    try:
        return json.loads(text)
    except ValueError:
        return text


# ---- injection point 1: git caller (real subprocess by default; --git-caller
# ---- swaps in canned) ----------------------------------------------------------

class GitCaller(object):
    """Single git-call point. canned=None runs the real git subprocess (with
    the --timeout anti-hang cap; on timeout it is killed and a fail-loud 9
    names the call); canned=list consumes the scenario strictly in order (the
    first unused response must match every args_contains substring, else
    fail-loud, so a scenario-order bug surfaces on the spot). All calls are
    recorded in self.calls as .calls.json evidence."""

    def __init__(self, canned=None, timeout=120):
        self.canned = canned
        self.timeout = timeout
        self.calls = []

    def __call__(self, args):
        if self.canned is not None:
            resp = None
            for r in self.canned:
                if not r.get("_used"):
                    resp = r
                    break
            if resp is None:
                raise PushciError("canned git scenario responses exhausted "
                                  "(actual call %r)" % (args,), 2)
            for needle in resp.get("args_contains") or []:
                if not any(needle in a for a in args):
                    raise PushciError("canned git mismatch: expected substring "
                                      "%r, actual call %r" % (needle, args), 2)
            resp["_used"] = True
            rc = resp.get("rc", 0)
            self.calls.append({"args": [str(a) for a in args], "rc": rc})
            return rc, resp.get("stdout", ""), resp.get("stderr", "")
        what = "git " + " ".join(str(a) for a in args)
        p = subproc_run(["git"] + list(args), self.timeout, what)
        so = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        se = p.stderr.decode("utf-8", "replace") if isinstance(p.stderr, bytes) \
            else (p.stderr or "")
        return p.returncode, so, se


# ---- injection point 2: the single _api function (real urllib by default;
# ---- injector swaps in canned) --------------------------------------------------

class ApiClient(object):
    """The single _api(method, path, body) function. canned = steps-shape
    scenario (consumed strictly in order per at_round); flat = flat-shape
    canned (runs consumed per poll, rerun per POST, merge single-shot; the
    parallel agent contract shape); both None means real urllib (token read
    lazily from netrc; HTTP 4xx/5xx return (code, body) for semantic
    adjudication; connection failure fails loudly with 9). Resilience layer:
    the real-urllib path retries 403/429/5xx with exponential backoff
    (_http_backoff pure functions, capped by retry_max, Retry-After second
    counts preferred; when exhausted the original status goes to semantic
    adjudication; 4xx semantic codes are not retried); injector/canned paths
    never touch the real network and never retry. All calls recorded in
    self.calls."""

    def __init__(self, canned=None, flat=None, netrc_path=None, timeout=30,
                 retry_max=3, sleep_scale=1.0, _urlopen=None, _sleep=None):
        self.canned = canned
        self.flat = flat
        self.netrc_path = netrc_path
        self.timeout = timeout
        self.retry_max = retry_max
        self.sleep_scale = sleep_scale
        self._urlopen = _urlopen
        self._sleep = _sleep
        self._token = None
        self._flat_runs_i = 0
        self._flat_rerun_i = 0
        self.calls = []

    def __call__(self, method, path, body=None, round_no=0):
        if self.canned is not None:
            return self._canned_call(method, path, body, round_no)
        if self.flat is not None:
            return self._flat_call(method, path, body, round_no)
        return self._live_call(method, path, body)

    def _flat_call(self, method, path, body, round_no):
        """Flat-shape canned: GET runs consumed per poll, POST rerun per fire
        (run_id cross-checked), PUT merge single-shot (canned.merge
        {"status","body"}; the 409 flow requires the steps shape)."""
        f = self.flat
        if method == "GET" and RUNS_QUERY in path:
            if self._flat_runs_i >= len(f["runs"]):
                raise PushciError("flat scenario canned.runs exhausted (poll %d)"
                                  % (self._flat_runs_i + 1), 2)
            b = f["runs"][self._flat_runs_i]
            self._flat_runs_i += 1
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": 200})
            return 200, b
        if method == "POST" and "/rerun" in path:
            if self._flat_rerun_i >= len(f["rerun"]):
                raise PushciError("flat scenario canned.rerun exhausted "
                                  "(rerun %d)" % (self._flat_rerun_i + 1), 2)
            e = f["rerun"][self._flat_rerun_i]
            self._flat_rerun_i += 1
            status = e.get("status", 200) if isinstance(e, dict) else int(e)
            m = re.search(r"/runs/(\d+)/rerun$", path)
            if isinstance(e, dict) and e.get("run_id") is not None \
                    and m and str(e["run_id"]) != m.group(1):
                raise PushciError("flat canned.rerun run_id mismatch (canned "
                                  "%s vs path %s)" % (e["run_id"], m.group(1)), 2)
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": status})
            return status, None
        if method == "PUT" and "/merge" in path:
            mc = f.get("merge")
            if not isinstance(mc, dict):
                raise PushciError("flat scenario missing canned.merge (PUT %s)"
                                  % path, 2)
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": mc.get("status", 200)})
            return mc.get("status", 200), mc.get("body")
        raise PushciError("API call not supported in the flat scenario (pulls "
                          "GET requires explicit --pr): %s %s" % (method, path), 2)

    def _canned_call(self, method, path, body, round_no):
        step = None
        for s in self.canned.get("steps") or []:
            if s.get("at_round") == round_no:
                step = s
                break
        if step is None:
            raise PushciError("injector scenario has no at_round=%s step "
                              "(actual call %s %s)"
                              % (round_no, method, path), 2)
        resp = None
        for r in step.get("responses") or []:
            if not r.get("_used"):
                resp = r
                break
        if resp is None:
            raise PushciError("injector scenario round=%s canned responses "
                              "exhausted (actual call %s %s)"
                              % (round_no, method, path), 2)
        if resp.get("method") != method:
            raise PushciError("injector mismatch: expected method=%s, actual "
                              "%s (path %s)"
                              % (resp.get("method"), method, path), 2)
        want = resp.get("path") or ""
        if want and want not in path:
            raise PushciError("injector mismatch: canned path %r is not a "
                              "substring of actual %r" % (want, path), 2)
        resp["_used"] = True
        status = resp.get("status", 200)
        self.calls.append({"round": round_no, "method": method, "path": path,
                           "status": status})
        return status, resp.get("body")

    def _live_call(self, method, path, body):
        if self._token is None:
            self._token = netrc_token(self.netrc_path)
        url = API_ROOT + path
        data = None
        headers = {"Accept": "application/vnd.github+json",
                   "User-Agent": "rocqwash-pushci",
                   "X-GitHub-Api-Version": "2022-11-28",
                   "Authorization": "token %s" % self._token}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        do_open = urllib.request.urlopen if self._urlopen is None \
            else self._urlopen
        do_sleep = (lambda s: sleep_scaled(s, self.sleep_scale)) \
            if self._sleep is None else self._sleep
        delays = _http_backoff.backoff_delays(self.retry_max)
        attempt = 0
        while True:
            req = urllib.request.Request(url, data=data, headers=headers,
                                         method=method)
            try:
                with do_open(req, timeout=self.timeout) as resp:
                    code = getattr(resp, "status", None)
                    if code is None and hasattr(resp, "getcode"):
                        code = resp.getcode()
                    raw = resp.read()
            except urllib.error.HTTPError as e:
                code = e.code
                try:
                    raw = e.read() or b""
                except Exception:
                    raw = b""
                if attempt < self.retry_max \
                        and _http_backoff.is_retry_status(code):
                    ra = _http_backoff.parse_retry_after(
                        e.headers.get("Retry-After")
                        if e.headers is not None else None)
                    do_sleep(ra if ra is not None else delays[attempt])
                    attempt += 1
                    continue
            except (urllib.error.URLError, OSError) as e:
                raise PushciError("API unreachable: %s (%s)" % (url, e), 9)
            return code, parse_body(raw)


# ---- pipeline body --------------------------------------------------------------

class Pipeline(object):

    def __init__(self, args):
        self.args = args
        self.repo = None
        self.remote_url = None
        self.masks = []
        self.round_no = 0
        self.scen = None
        self.injector_kind = None          # "steps" | "flat" | None
        self._jobs_i = 0                   # canned jobs pointer, consumed per triage call
        self._flat_probe_i = 0             # flat canned.probe pointer, consumed per heal probe
        self._flat_gate_noted = False      # flat-shape preflight default-green note (once)
        mode = "online"
        flat_canned = None
        if args.dry_run:
            mode = "dry-run"
        elif args.injector:
            mode = "injector"
            self.scen = self._load_injector(args.injector)
            if isinstance(self.scen.get("canned"), dict):
                self.injector_kind = "flat"
                c = self.scen["canned"]
                flat_canned = {"runs": list(c.get("runs") or []),
                               "rerun": list(c.get("rerun") or []),
                               "merge": c.get("merge")}
            else:
                self.injector_kind = "steps"
        canned_git = None
        if args.git_caller:
            with io.open(args.git_caller, "r", encoding="utf-8") as fh:
                gscen = json.load(fh)
            if not isinstance(gscen, dict) \
                    or not isinstance(gscen.get("responses"), list):
                raise PushciError("git-caller scenario shape bad (expected "
                                  "{\"responses\":[...]}): %s"
                                  % args.git_caller, 2)
            canned_git = [dict(r) for r in gscen["responses"]]
        self.git = GitCaller(canned=canned_git, timeout=args.timeout)
        self.api = ApiClient(
            canned=self.scen if self.injector_kind == "steps" else None,
            flat=flat_canned, netrc_path=args.netrc,
            retry_max=args.retry_max, sleep_scale=args.sleep_scale)
        self.report = {
            "schema": SCHEMA,
            "mode": mode,
            "steps": list(args.steps),
            "args": {
                "branch": args.branch, "base_ref": args.base_ref,
                "remote": args.remote, "pr": args.pr,
                "merge": bool(args.merge),
                "merge_method": args.merge_method,
                "max_heal": args.max_heal,
                "watch_interval": args.watch_interval,
                "probe_interval": args.probe_interval,
                "pre_scan_gate4": bool(args.pre_scan_gate4),
            },
            "stages": {},
            "evidence": [],
            "final": {"conclusion": None, "verdict": None},
            "verdict": None,
        }

    @staticmethod
    def _load_json_file(path, what):
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (ValueError, UnicodeDecodeError) as e:
            raise PushciError("%s JSON shape bad: %s (%s)" % (what, path, e), 2)

    def _load_injector(self, inj):
        """Injection-scenario loader (both shapes accepted):
        (a) DIR/scenario.json containing a "canned" dict = flat shape (the
            fixture original verbatim; unknown keys such as schema/scenario/
            summary/argv/expect are ignored);
        (b) DIR/scenario.json without "canned" = steps shape (steps[].at_round);
        (c) no scenario.json but a flat runs/ directory = flat shape (the
            parallel agent placeholder layout: runs/NNNN.json +
            jobs/NNNN.json
            + rerun/NNNN.json + probe/NNNN.json + merge.json; filename sort
            order = consumption order)."""
        sj = os.path.join(inj, "scenario.json")
        if os.path.isfile(sj):
            scen = self._load_json_file(sj, "injector scenario")
            if not isinstance(scen, dict):
                raise PushciError("injector scenario shape bad (expected "
                                  "dict): %s" % sj, 2)
            return scen
        if os.path.isdir(os.path.join(inj, "runs")):
            def rd(kind):
                d = os.path.join(inj, kind)
            out = []
            if os.path.isdir(d):
                for fn in sorted(os.listdir(d)):
                    if fn.endswith(".json"):
                        out.append(self._load_json_file(
                            os.path.join(d, fn),
                            "flat canned %s/%s" % (kind, fn)))
                return out
            mp = os.path.join(inj, "merge.json")
            merge = self._load_json_file(mp, "flat canned merge") \
                if os.path.isfile(mp) else None
            return {"canned": {"runs": rd("runs"), "jobs": rd("jobs"),
                               "rerun": rd("rerun"), "probe": rd("probe"),
                               "logs": {}, "merge": merge}}
        raise PushciError("injector scenario missing (scenario.json or flat "
                          "runs/ directory): %s" % inj, 9)

    # -- tool subprocesses (orchestrates the four tools, zero new engines) -----

    def _run_py(self, tool_path, cli):
        """python3 -B <tool> <cli> subprocess (stdout+stderr merged). A missing
        component fails with 9; --timeout anti-hang (default 120s): on timeout
        the subprocess is killed and a fail-loud 9 names the call."""
        if not os.path.isfile(tool_path):
            raise PushciError("toolchain component missing: %s" % tool_path, 9)
        p = subproc_run([sys.executable, "-B", tool_path] + list(cli),
                        self.args.timeout,
                        "python3 -B %s %s" % (os.path.basename(tool_path),
                                              " ".join(str(c) for c in cli[:2])),
                        merge_stderr=True)
        out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        return p.returncode, out

    def _tool_report(self, tool_path, cli):
        """Run one of the four tools (with --json tmp), returning
        (rc, report|None, stdout)."""
        fd, tmp = tempfile.mkstemp(prefix="pushci_toolrep_")
        os.close(fd)
        try:
            rc, out = self._run_py(tool_path, list(cli) + ["--json", tmp])
            rep = None
            try:
                with io.open(tmp, "r", encoding="utf-8") as fh:
                    rep = json.load(fh)
            except Exception:
                rep = None
            return rc, rep, out
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def scen_tools(self):
        t = (self.scen or {}).get("tools")
        return t if isinstance(t, dict) else {}

    def _next_jobs(self):
        """Triage canned-jobs fetch (consumed per triage call): flat-shape
        canned.jobs list, then steps-shape jobs_list list, then steps-shape
        single jobs dict (reused)."""
        if self.injector_kind == "flat":
            lst = (self.scen.get("canned") or {}).get("jobs") or []
        elif isinstance(self.scen.get("jobs_list"), list):
            lst = self.scen["jobs_list"]
        else:
            return self.scen.get("jobs")
        if self._jobs_i >= len(lst):
            raise PushciError("injector scenario canned jobs exhausted (triage "
                              "call %d)" % (self._jobs_i + 1), 2)
        j = lst[self._jobs_i]
        self._jobs_i += 1
        return j

    def runs_path(self):
        return "/repos/%s%s" % (self.repo, RUNS_QUERY)

    # -- stage 1: preflight ------------------------------------------------------

    def stage_preflight(self):
        a = self.args
        pf = {"toolchain": None, "net": None}
        if a.pre_scan_gate4:
            pf["gate4"] = None
        self.report["stages"]["preflight"] = pf

        # step 1 toolchain (doctor probed with --worker by default; verdict
        # other than healthy stops)
        if self.injector_kind == "steps":
            tc = self.scen_tools().get("toolchain_dyld_doctor") or {}
            if isinstance(tc.get("report"), dict):
                doc_rep = tc["report"]
                verdict = doc_rep.get("verdict")
                rc = tc.get("rc", 0 if verdict == "healthy" else 1)
            else:
                verdict, rc, doc_rep = tc.get("verdict"), tc.get("rc", 0), None
            if verdict is None:
                raise PushciError("injector scenario missing tools."
                                  "toolchain_dyld_doctor.verdict", 2)
        elif self.injector_kind == "flat":
            verdict, rc, doc_rep = "healthy", 0, None   # gate default green; the note is emitted in probe_stable
        else:
            rc, doc_rep, out = self._tool_report(DOCTOR_TOOL, [])
            verdict = doc_rep.get("verdict") if isinstance(doc_rep, dict) else None
            if verdict is None:
                raise PushciError("doctor report shape bad (no verdict) "
                                  "rc=%d: %s" % (rc, out[-200:]), 2)
        pf["toolchain"] = {"verdict": verdict, "rc": rc}
        if verdict != "healthy":
            ev = ["doctor verdict=%s rc=%s (not healthy, no initiate)"
                  % (verdict, rc)]
            if isinstance(doc_rep, dict):
                for e in doc_rep.get("external_refs") or []:
                    if isinstance(e, dict) and not e.get("exists"):
                        ev.append("missing: %s" % e.get("path"))
            raise StopVerdict("toolchain", 1, ev)

        # step 2 net (net_probe two-round stable window; UNSTABLE stops)
        verdict, rc = self.probe_stable(with_record=True)
        if verdict != "STABLE":
            raise StopVerdict("unstable", 1,
                              ["net_probe verdict=%s rc=%s (UNSTABLE, no "
                               "initiate)" % (verdict, rc)])

        # step 3 optional gate4 pre-scan (proceed only when FAIL=0)
        if a.pre_scan_gate4:
            self.gate4_prescan(pf)

    def probe_stable(self, with_record=False, source="preflight"):
        """net_probe --rounds 2 --interval S --stable-window (real subprocess
        or canned) returning (verdict, rc); verdict must be STABLE|UNSTABLE.
        Steps shape: tools.net_probe canned ({"verdict"} or {"report":{...}}).
        Flat shape: the preflight gate defaults green (noted loudly once) and
        heal probes consume canned.probe one per probe (verdict taken from
        the real net_probe report shape)."""
        a = self.args
        if self.injector_kind == "steps":
            np = self.scen_tools().get("net_probe") or {}
            if isinstance(np.get("report"), dict):
                verdict = np["report"].get("verdict")
                rc = np.get("rc", 0 if verdict == "STABLE" else 1)
            else:
                verdict, rc = np.get("verdict"), np.get("rc", 0)
            if verdict is None:
                raise PushciError("injector scenario missing "
                                  "tools.net_probe.verdict", 2)
        elif self.injector_kind == "flat":
            if source == "preflight":
                verdict, rc = "STABLE", 0
                if not self._flat_gate_noted:
                    self._flat_gate_noted = True
                    self.report["evidence"].append(
                        "flat injection shape: preflight toolchain/net gates "
                        "default green (the flat shape carries no gate canned "
                        "entries; test-contract shape; the real preflight runs "
                        "in the steps shape or live mode)")
            else:
                lst = (self.scen.get("canned") or {}).get("probe") or []
                if self._flat_probe_i >= len(lst):
                    raise PushciError("flat scenario canned.probe exhausted "
                                      "(heal probe %d)"
                                      % (self._flat_probe_i + 1), 2)
                rep = lst[self._flat_probe_i]
                self._flat_probe_i += 1
                verdict = rep.get("verdict") if isinstance(rep, dict) else None
                if verdict not in ("STABLE", "UNSTABLE"):
                    raise PushciError("flat canned.probe shape bad "
                                      "(verdict=%r)" % (verdict,), 2)
                rc = 0 if verdict == "STABLE" else 1
        else:
            rc, rep, out = self._tool_report(
                PROBE_TOOL, ["--rounds", "2",
                             "--interval", str(float(a.probe_interval)),
                             "--stable-window"])
            verdict = rep.get("verdict") if isinstance(rep, dict) else None
            if verdict not in ("STABLE", "UNSTABLE"):
                raise PushciError("net_probe report shape bad (verdict=%r) "
                                  "rc=%d: %s" % (verdict, rc, out[-200:]), 2)
        if with_record:
            pf = self.report["stages"].get("preflight")
            if pf is not None:
                pf["net"] = {"verdict": verdict, "rc": rc}
        return verdict, rc

    def gate4_prescan(self, pf):
        """git diff --name-only <base>...<branch> to the changed .v files, each
        run through the gate4 guard (--file, real subprocess; rc 0=PASS/
        1=FAIL/2=review); proceed only when FAIL=0."""
        a = self.args
        rc, out, err = self.git(["-C", a.repo_path, "diff", "--name-only",
                                 "%s...%s" % (a.base_ref, a.branch)])
        if rc != 0:
            raise PushciError("git diff failed rc=%d: %s"
                              % (rc, err.strip()[:160]), 9)
        names = [ln.strip() for ln in out.splitlines() if ln.strip()]
        files, skipped = [], []
        for n in names:
            if not n.endswith(".v"):
                continue
            p = n if os.path.isabs(n) else os.path.join(a.repo_path, n)
            (files if os.path.isfile(p) else skipped).append(p)
        pass_files, fail_files, review_files = [], [], []
        for f in sorted(files):
            rc, out = self._run_py(GATE4_TOOL, ["--file", f])
            if rc == 0:
                pass_files.append(f)
            elif rc == 1:
                fail_files.append(f)
            elif rc == 2:
                review_files.append(f)
            else:
                raise PushciError("gate4 guard exit outside its contract "
                                  "rc=%d: %s" % (rc, out[-160:]), 2)
        pf["gate4"] = {"files": sorted(files), "pass_files": pass_files,
                       "fail_files": fail_files, "review_files": review_files,
                       "skipped_missing": sorted(skipped),
                       "fail_count": len(fail_files)}
        if skipped:
            self.report["evidence"].append(
                "gate4 pre-scan skipped %d missing files (branch-deleted files "
                "have no face to scan, recorded loudly): %s"
                % (len(skipped), ",".join(sorted(skipped))))
        if review_files:
            self.report["evidence"].append(
                "gate4 REVIEW=%d (review grade does not block, human-readable): %s"
                % (len(review_files), ",".join(review_files)))
        if fail_files:
            raise StopVerdict("gate4-block", 2,
                              ["gate4 FAIL=%d (proceed only when FAIL=0): %s"
                               % (len(fail_files), ",".join(fail_files))])

    # -- stage 2: push ------------------------------------------------------------

    def stage_push(self):
        a = self.args
        rec = {"sha": None, "remote": a.remote, "url_masked": None,
               "attempts": [], "ghproxy_used": False}
        self.report["stages"]["push"] = rec
        rc, out, err = self.git(["-C", a.repo_path, "rev-parse", "--verify",
                                 "refs/heads/%s" % a.branch])
        if rc != 0:
            raise PushciError("branch missing: refs/heads/%s (%s)"
                              % (a.branch, err.strip()[:120]), 9)
        sha_local = out.strip().split()[0] if out.strip() else ""
        if not sha_local:
            raise PushciError("rev-parse empty output (refs/heads/%s)"
                              % a.branch, 9)
        rec["url_masked"] = mask_text(self.remote_url, self.masks)
        base_cmd = ["-C", a.repo_path, "-c",
                    "http.version=" + PUSH_HTTP_VERSION, "push"]
        ok = self._push_tries(base_cmd + [a.remote, a.branch], PUSH_TRIES,
                              rec["attempts"], a.remote)
        if not ok:
            proxy = ghproxy_url(self.remote_url)
            if proxy:
                rec["ghproxy_used"] = True
                ok = self._push_tries(
                    base_cmd + [proxy, a.branch], GHPROXY_TRIES,
                    rec["attempts"], mask_text(proxy, self.masks))
            else:
                self.report["evidence"].append(
                    "ghproxy reroute not applicable (remote URL is not the "
                    "https://%s/ shape: %s)"
                    % (GHPROXY_HOST, mask_text(self.remote_url, self.masks)))
        if not ok:
            route = "%d direct attempts" % PUSH_TRIES
            if rec["ghproxy_used"]:
                route += " plus %d ghproxy attempts" % GHPROXY_TRIES
            raise StopVerdict("unstable", 1,
                              ["all push attempts failed (%s); per-attempt rc "
                               "recorded in stages.push.attempts" % route])
        # ls-remote confirmation (watch.py's "real rc + ls-remote confirmation"
        # discipline; the 4th git call): pushed_sha = the remote tip (CI builds
        # the remote tip, so the remote is authoritative); a mismatch with the
        # local tip is noted loudly.
        rc, out, err = self.git(["-C", a.repo_path, "ls-remote", a.remote,
                                 "refs/heads/%s" % a.branch])
        if rc != 0 or not out.strip():
            raise PushciError("post-push ls-remote confirmation failed rc=%d "
                              "(remote tip unprovable): %s"
                              % (rc, err.strip()[:120]), 9)
        sha_remote = out.strip().split()[0]
        if not re.match(r"^[0-9a-fA-F]{40}$", sha_remote):
            raise PushciError("ls-remote output is not a 40-hex-digit sha: %r"
                              % mask_text(sha_remote, self.masks), 9)
        rec["sha"] = sha_remote
        if sha_remote.lower() != sha_local.lower():
            self.report["evidence"].append(
                "post-push ls-remote sha differs from the local rev-parse tip "
                "(remote is authoritative; watch anchors the remote tip)")

    def _push_tries(self, cmd, tries, attempts_log, target_label):
        for i in range(tries):
            rc, out, err = self.git(cmd)
            attempts_log.append({"target": target_label, "rc": rc})
            if rc == 0:
                return True
            if i < tries - 1:
                sleep_scaled(PUSH_RETRY_WAIT, self.args.sleep_scale)
        return False

    # -- stage 3: resolve+watch (contains the stage 4 heal loop) -----------------

    def stage_watch(self):
        a = self.args
        push_rec = self.report["stages"].get("push") or {}
        sha = push_rec.get("sha")
        if not sha:
            raise PushciError("watch depends on pushed_sha (push stage not run "
                              "or not successful)", 2)
        watch = {"run_tag": None, "run_id": None, "rounds": 0,
                 "conclusion": None, "policy": WATCH_POLICY}
        self.report["stages"]["watch"] = watch
        heal = {"rounds": [], "fired_total": 0, "last_triage": None}
        if "heal" in a.steps:
            self.report["stages"]["heal"] = heal   # always present (rounds = fired account; empty when green)
        while True:
            self.round_no += 1
            watch["rounds"] = self.round_no
            if a.watch_max_rounds and self.round_no > a.watch_max_rounds:
                raise PushciError("watch round cap reached "
                                  "(--watch-max-rounds=%d) with the run still "
                                  "not completed" % a.watch_max_rounds, 9)
            status, body = self.api("GET", self.runs_path(),
                                    round_no=self.round_no)
            if status != 200:
                raise PushciError("GET runs HTTP %d: %s"
                                  % (status, snippet(body)), 9)
            runs = None
            if isinstance(body, dict):
                runs = body.get("workflow_runs")   # real GitHub API shape
                if runs is None:
                    runs = body.get("runs")        # watch.py --runs-json evidence shape
            if not isinstance(runs, list):
                raise PushciError("runs API shape bad (no workflow_runs/runs "
                                  "list)", 9)
            matches = [r for r in runs if isinstance(r, dict)
                       and str(r.get("head_branch") or "") == a.branch
                       and str(r.get("head_sha") or "").lower() == sha.lower()]
            if not matches:
                sleep_scaled(a.watch_interval, a.sleep_scale)
                continue
            run = max(matches, key=lambda r: ((r.get("run_number") or 0),
                                              (r.get("id") or 0)))
            if watch["run_id"] is None:
                watch["run_id"] = run.get("id")
                watch["run_tag"] = "#%s id=%s" % (run.get("run_number"),
                                                  run.get("id"))
            if run.get("status") != "completed":
                sleep_scaled(a.watch_interval, a.sleep_scale)
                continue
            conclusion = run.get("conclusion")
            watch["conclusion"] = conclusion
            if conclusion == "success":
                return
            if "heal" not in a.steps:
                raise StopVerdict("fix-content", 2,
                                  ["watch observed a failing conclusion=%s; "
                                   "the heal stage was not selected (--steps "
                                   "trimmed); no automatic handling, manual "
                                   "triage" % conclusion])
            if len(heal["rounds"]) >= a.max_heal:
                raise StopVerdict("heal-exhausted", 1,
                                  ["heal cap reached (--max-heal=%d, already "
                                   "%d rounds)"
                                   % (a.max_heal, len(heal["rounds"]))])
            self.heal_round(run, heal)
            sleep_scaled(a.watch_interval, a.sleep_scale)

    def heal_round(self, run, heal):
        """One heal round: ci_triage classification (real subprocess), family
        routing, then rerun or stop. heal.rounds = the fired-rerun account
        (B/E rounds with an actual fire are recorded; A/C/out-of-table stops
        contribute zero rounds, provably zero reruns); every triage outcome is
        recorded in full in heal.last_triage."""
        t_rep = self.run_triage(run.get("id"))
        heal["last_triage"] = {"family": t_rep.get("family"),
                               "action": t_rep.get("action"),
                               "evidence": list(t_rep.get("evidence") or [])}
        fam = t_rep.get("family")
        if fam not in HEAL_RERUN_FAMILIES:
            if fam == "A-content-red":
                raise StopVerdict("fix-content", 2,
                                  ["heal: family=A-content-red (content failure, "
                                   "no automatic repair; repair is the operator's "
                                   "job); classification evidence recorded in "
                                   "stages.heal.last_triage.evidence; zero rerun"])
            if fam == "C-toolchain-break":
                raise StopVerdict("toolchain", 1,
                                  ["heal: family=C-toolchain-break (environment "
                                   "linkage failure); run python3 tools/"
                                   "toolchain_dyld_doctor.py again to "
                                   "re-diagnose (diagnosis plus restore "
                                   "suggestion only, no automatic execution); "
                                   "classification evidence recorded in "
                                   "stages.heal.last_triage.evidence"])
            raise StopVerdict("fix-content", 2,
                              ["heal: family=%s outside the heal routing table "
                               "(beyond B/E/A/C); no automatic rerun, manual "
                               "identification; the family value is recorded "
                               "verbatim in last_triage" % fam])
        entry = {"round": len(heal["rounds"]) + 1, "family": fam,
                 "action": t_rep.get("action"), "probe": None, "fired": False,
                 "http": None, "evidence": list(t_rep.get("evidence") or [])}
        heal["rounds"].append(entry)
        verdict, _rc = self.probe_stable(source="heal")
        entry["probe"] = verdict
        if verdict != "STABLE":
            raise StopVerdict("unstable", 1,
                              ["heal round %d: probe=%s (no-initiate rule, "
                               "UNSTABLE does not rerun)"
                               % (entry["round"], verdict)])
        status, body = self.api(
            "POST", "/repos/%s/actions/runs/%s/rerun" % (self.repo,
                                                         run.get("id")),
            round_no=self.round_no)
        entry["http"] = status
        if status in (200, 201, 202):
            entry["fired"] = True
        elif status == 403:
            entry["fired"] = True
            entry["evidence"].append(
                "rerun POST 403 (already-running shape) accepted "
                "idempotently, back to watch")
        else:
            raise PushciError("rerun POST HTTP %d: %s"
                              % (status, snippet(body)), 9)
        heal["fired_total"] = sum(1 for r in heal["rounds"] if r["fired"])

    def run_triage(self, run_id):
        """ci_triage subprocess: live --repo --run (token passed through via
        --netrc) or injector-mode --offline canned jobs (real subprocess, real
        classification, zero network)."""
        fd, out_json = tempfile.mkstemp(prefix="pushci_triage_")
        os.close(fd)
        jobs_path = None
        try:
            if self.scen is not None:
                jobs = self._next_jobs()
                if not isinstance(jobs, dict):
                    raise PushciError("injector scenario missing canned jobs "
                                      "(ci_triage shape {\"total_count\":N,"
                                      "\"jobs\":[...]})", 2)
                fdj, jobs_path = tempfile.mkstemp(prefix="pushci_jobs_")
                os.close(fdj)
                with io.open(jobs_path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(jobs, fh, sort_keys=True)
                cli = ["--offline", jobs_path, "--json", out_json]
            else:
                cli = ["--repo", self.repo, "--run", str(run_id),
                       "--netrc", self.args.netrc, "--json", out_json]
            rc, out = self._run_py(TRIAGE_TOOL, cli)
            if rc != 0:
                raise PushciError("ci_triage failed rc=%d: %s"
                                  % (rc, out[-200:]), 9)
            with io.open(out_json, "r", encoding="utf-8") as fh:
                return json.load(fh)
        finally:
            if jobs_path:
                try:
                    os.unlink(jobs_path)
                except OSError:
                    pass
            try:
                os.unlink(out_json)
            except OSError:
                pass

    # -- stage 5: merge ------------------------------------------------------------

    def stage_merge(self):
        a = self.args
        owner = self.repo.split("/")[0]
        rec = {"pr": a.pr, "method": a.merge_method, "merged": False,
               "attempts": [], "main_tip": None}
        self.report["stages"]["merge"] = rec
        pr = a.pr
        if pr is None:
            status, body = self.api(
                "GET", "/repos/%s/pulls?head=%s:%s&state=open"
                % (self.repo, owner, a.branch), round_no=self.round_no)
            if status != 200:
                raise PushciError("GET pulls HTTP %d: %s"
                                  % (status, snippet(body)), 9)
            nums = []
            if isinstance(body, list):
                nums = sorted(p.get("number") for p in body
                              if isinstance(p, dict)
                              and isinstance(p.get("number"), int))
            if not nums:
                raise PushciError("no open PR (head=%s:%s, missing target)"
                                  % (owner, a.branch), 9)
            pr = nums[0]
            rec["pr"] = pr
        for i in range(MERGE_409_RETRIES + 1):
            status, body = self.api(
                "PUT", "/repos/%s/pulls/%s/merge" % (self.repo, pr),
                body={"merge_method": a.merge_method}, round_no=self.round_no)
            rec["attempts"].append(status)
            if status == 200:
                rec["merged"] = True
                if isinstance(body, dict) and body.get("sha"):
                    rec["merge_sha"] = body.get("sha")
                return
            if status == 409:
                if i >= MERGE_409_RETRIES:
                    raise StopVerdict("fix-content", 2,
                                      ["merge 409 x%d (retry cap <=%d); PR #%s "
                                       "conflict, resolve manually "
                                       "(verdict=fix-content)"
                                       % (i + 1, MERGE_409_RETRIES, pr)])
                bs, bb = self.api("GET", "/repos/%s/branches/main" % self.repo,
                                  round_no=self.round_no)
                if bs == 200 and isinstance(bb, dict):
                    rec["main_tip"] = (bb.get("commit") or {}).get("sha")
                self.report["evidence"].append(
                    "merge 409 (attempt %d), GET branches/main re-read "
                    "tip=%s, wait %ds and retry"
                    % (i + 1, rec["main_tip"], MERGE_409_WAIT))
                sleep_scaled(MERGE_409_WAIT, a.sleep_scale)
                continue
            raise PushciError("merge PUT HTTP %d: %s" % (status, snippet(body)), 9)

    # -- dry-run ----------------------------------------------------------------

    def run_dry(self):
        a = self.args
        plan = []
        if "preflight" in a.steps:
            plan.append("[1] preflight.toolchain: python3 tools/"
                        "toolchain_dyld_doctor.py (--worker probed by default, "
                        "gate verdict=healthy)")
            plan.append("[1] preflight.net: python3 tools/net_probe.py --rounds 2"
                        " --interval %g --stable-window (gate STABLE)"
                        % a.probe_interval)
            if a.pre_scan_gate4:
                plan.append("[1] preflight.gate4: git -C <repo> diff --name-only "
                            "%s...%s, then the .v files through python3 verify/"
                            "gate4_comment_guard.py --file (gate FAIL=0)"
                            % (a.base_ref, a.branch))
            else:
                plan.append("[1] preflight.gate4: not enabled (--pre-scan-gate4 "
                            "not given)")
        if "push" in a.steps:
            plan.append("[2] push: git -C <repo> -c http.version=%s push %s %s "
                        "(%d attempts x %ds wait; after three failures with "
                        "remote host=%s, ghproxy reroute %d attempts)"
                        % (PUSH_HTTP_VERSION, a.remote, a.branch,
                           PUSH_TRIES, PUSH_RETRY_WAIT, GHPROXY_HOST,
                           GHPROXY_TRIES))
        if "watch" in a.steps:
            plan.append("[3] watch: GET /repos/<org/repo>%s (head_branch=%s and "
                        "head_sha=<pushed_sha>, every %gs, %s until completed)"
                        % (RUNS_QUERY, a.branch, a.watch_interval, WATCH_POLICY))
        if "heal" in a.steps:
            plan.append("[4] heal: python3 tools/ci_triage.py --repo <org/repo> "
                        "--run <id> (cap %d); B/E -> probe then rerun (403 "
                        "accepted idempotently); A -> stop fix-content; "
                        "C -> stop toolchain; out-of-table -> manual"
                        % a.max_heal)
        plan.append("[5] verdict: report schema %s, exit codes 0/1/2/9" % SCHEMA)
        if a.merge:
            plan.append("[5] merge: GET /pulls?head=<owner>:%s&state=open (%s) "
                        "then PUT /pulls/{{n}}/merge (%s; 409 -> GET "
                        "branches/main, wait %ds, retry <=%d)"
                        % (a.branch, ("explicit --pr %d" % a.pr) if a.pr
                           else "resolve the PR number", a.merge_method,
                           MERGE_409_WAIT, MERGE_409_RETRIES))
        self.report["plan"] = plan
        return "dry-run", 0, []

    # -- main driver -----------------------------------------------------------------

    def run(self):
        a = self.args
        if a.dry_run:
            return self.run_dry()
        if "push" in a.steps or "watch" in a.steps:
            # the remote URL is needed by the push stage (ghproxy decision) and
            # the watch stage (repo derivation); pure preflight mode makes zero
            # git calls
            rc, out, err = self.git(["-C", a.repo_path, "remote", "get-url",
                                     "--push", a.remote])
            if rc != 0:
                raise PushciError("remote missing: %s (%s)"
                                  % (a.remote, err.strip()[:120]), 9)
            self.remote_url = out.strip()
            self.repo = repo_from_url(self.remote_url)
            if not self.repo:
                raise PushciError(
                    "remote URL path cannot derive ORG/REPO (last two "
                    "segments): %s"
                    % mask_text(self.remote_url, collect_masks(self.remote_url)),
                    9)
            self.masks = collect_masks(self.remote_url)
        if "preflight" in a.steps:
            self.stage_preflight()
        if "push" in a.steps:
            self.stage_push()
        if "watch" in a.steps:
            self.stage_watch()
        if a.merge and "watch" in a.steps:
            self.stage_merge()
        return "success", 0, []

    # -- reporting -----------------------------------------------------------------

    def dump_canned_logs(self):
        """Persist injector-mode call traces (test-evidence surface; best
        effort, never masks the primary error)."""
        try:
            if self.args.git_caller:
                base = self.args.git_caller
                if base.endswith(".json"):
                    base = base[:-len(".json")]
                with io.open(base + ".calls.json", "w", encoding="utf-8",
                             newline="\n") as fh:
                    json.dump(self.git.calls, fh, indent=1,
                              ensure_ascii=False, sort_keys=True)
            if self.args.injector:
                with io.open(os.path.join(self.args.injector, "api_calls.json"),
                             "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(self.api.calls, fh, indent=1,
                              ensure_ascii=False, sort_keys=True)
        except OSError:
            pass

    def finalize(self, verdict, extra_evidence, code):
        """Final adjudication and reporting (renders stdout and writes --json
        when the verdict stage is selected)."""
        if verdict not in VERDICT_EXIT:
            raise PushciError("internal error: verdict outside the table %r"
                              % (verdict,), 2)
        rep = self.report
        rep["verdict"] = verdict
        watch = rep["stages"].get("watch")
        rep["final"] = {"conclusion": (watch or {}).get("conclusion"),
                        "verdict": verdict}
        rep["evidence"].extend(extra_evidence)
        self.dump_canned_logs()
        if self.args.dry_run or "verdict" in self.args.steps:
            render_report(rep, code)
            if self.args.json:
                with io.open(self.args.json, "w", encoding="utf-8",
                             newline="\n") as fh:
                    json.dump(rep, fh, indent=1, ensure_ascii=False,
                              sort_keys=True)
                print("json ->", self.args.json)
        return code


def render_report(rep, code):
    """stdout reporting (fully data-driven, zero wall-clock, deterministic)."""
    print("=== ROCQWASH PUSHCI (post-fix push-CI one-shot pipeline) ===")
    print("mode=%s steps=%s" % (rep["mode"], ",".join(rep["steps"])))
    for line in rep.get("plan") or []:
        print("PLAN %s" % line)
    st = rep["stages"]
    pf = st.get("preflight")
    if pf:
        print("--- [1] preflight ---")
        tc = pf.get("toolchain")
        if tc:
            print("toolchain: verdict=%s rc=%s" % (tc["verdict"], tc["rc"]))
        net = pf.get("net")
        if net:
            print("net: verdict=%s rc=%s" % (net["verdict"], net["rc"]))
        g4 = pf.get("gate4")
        if g4:
            print("gate4: files=%d pass=%d FAIL=%d review=%d skipped_missing=%d"
                  % (len(g4["files"]), len(g4["pass_files"]), g4["fail_count"],
                     len(g4["review_files"]), len(g4["skipped_missing"])))
            for f in g4["fail_files"]:
                print("  gate4 FAIL: %s" % f)
    push = st.get("push")
    if push:
        print("--- [2] push ---")
        print("sha=%s remote=%s url=%s ghproxy_used=%s attempts=%d"
              % (push["sha"], push["remote"], push["url_masked"],
                 str(push["ghproxy_used"]).lower(), len(push["attempts"])))
        for at in push["attempts"]:
            print("  attempt: target=%s rc=%s" % (at["target"], at["rc"]))
    watch = st.get("watch")
    if watch:
        print("--- [3] watch ---")
        print("run=%s rounds=%d conclusion=%s (%s)"
              % (watch["run_tag"] or "-", watch["rounds"],
                 watch["conclusion"] or "-", watch["policy"]))
    heal = st.get("heal")
    if heal is not None:
        print("--- [4] heal ---")
        print("rounds=%d fired_total=%d" % (len(heal["rounds"]),
                                            heal["fired_total"]))
        for r in heal["rounds"]:
            print("  round=%d family=%s action=%s probe=%s fired=%s http=%s"
                  % (r["round"], r["family"], r["action"], r["probe"],
                     str(r["fired"]).lower(), r["http"]))
            for e in r["evidence"]:
                print("    - %s" % e)
    merge = st.get("merge")
    if merge:
        print("--- [5] merge ---")
        print("pr=%s method=%s merged=%s attempts=%s main_tip=%s"
              % (merge["pr"], merge["method"],
                 str(merge["merged"]).lower(), merge["attempts"],
                 merge["main_tip"] or "-"))
    print("=== FINAL VERDICT: %s (exit %d) ===" % (rep["verdict"], code))
    for e in rep["evidence"]:
        print("  - %s" % e)


# ---- validation -------------------------------------------------------------------

def validate(args):
    """Usage validation (fail-loud 2) and target validation (fail-loud 9), all
    before any side effect."""
    steps = []
    for s in args.steps.split(","):
        s = s.strip()
        if s and s not in steps:
            steps.append(s)
    if not steps:
        raise PushciError("--steps expands to empty", 2)
    unknown = [s for s in steps if s not in STAGE_ALL]
    if unknown:
        raise PushciError("unknown --steps stage: %s (table: %s)"
                          % (",".join(unknown), ",".join(STAGE_ALL)), 2)
    args.steps = steps
    if "watch" in steps and "push" not in steps:
        raise PushciError("stage dependency: watch=>push (watch needs "
                          "pushed_sha)", 2)
    if "heal" in steps and "watch" not in steps:
        raise PushciError("stage dependency: heal=>watch", 2)
    if args.merge and "watch" not in steps:
        raise PushciError("stage dependency: --merge=>watch (merge runs only "
                          "after green)", 2)
    if args.max_heal < 0:
        raise PushciError("--max-heal must be >=0, got %d" % args.max_heal, 2)
    if args.watch_interval < 0:
        raise PushciError("--watch-interval must be >=0, got %s"
                          % args.watch_interval, 2)
    if args.probe_interval < 0:
        raise PushciError("--probe-interval must be >=0, got %s"
                          % args.probe_interval, 2)
    if args.watch_max_rounds < 0:
        raise PushciError("--watch-max-rounds must be >=0, got %d"
                          % args.watch_max_rounds, 2)
    if args.sleep_scale < 0:
        raise PushciError("--sleep-scale must be >=0, got %s"
                          % args.sleep_scale, 2)
    if args.timeout < 1:
        raise PushciError("--timeout must be >=1, got %d" % args.timeout, 2)
    if args.retry_max < 0:
        raise PushciError("--retry-max must be >=0, got %d" % args.retry_max, 2)
    if args.pr is not None and args.pr < 1:
        raise PushciError("--pr must be >=1, got %d" % args.pr, 2)
    if (args.injector is None) != (args.git_caller is None):
        raise PushciError("--injector and --git-caller must be paired (an "
                          "injector without canned git is a real-push "
                          "hazard)", 2)
    # target validation (9) precedes the --branch required check (2): a
    # missing repo reports 9 first
    if not args.repo_path:
        raise PushciError("--repo-path is required", 2)
    if not os.path.isdir(args.repo_path):
        raise PushciError("repository directory missing: %s" % args.repo_path, 9)
    if not args.branch:
        raise PushciError("--branch is required", 2)
    if args.injector:
        if not os.path.isdir(args.injector):
            raise PushciError("injector directory missing: %s"
                              % args.injector, 9)
        if not os.path.isfile(os.path.join(args.injector, "scenario.json")) \
                and not os.path.isdir(os.path.join(args.injector, "runs")):
            raise PushciError("injector scenario missing (scenario.json or "
                              "flat runs/ directory): %s"
                              % os.path.join(args.injector, "scenario.json"), 9)
    if args.git_caller and not os.path.isfile(args.git_caller):
        raise PushciError("git-caller scenario missing: %s"
                          % args.git_caller, 9)


# ---- selftest (--selftest: eight vectors + unit vectors + CLI four codes;
# ---- zero real network, zero real push, zero compilation) ----------------------

def selftest():
    """Frozen vector suite (--injector canned + --git-caller canned +
    --sleep-scale 0):
    (1) green path preflight -> push -> success (with byte-identical
        determinism)
    (2) one NETRED heal then attempt2 success (heal_rounds=1, real ci_triage
        --offline classifying B)
    (3) content-failure stop (family A, provably zero reruns, exit 2)
    (4) heal x3 exhausted exit 1 (POST=3, GET=4)
    (5) merge 200 flow
    (6) 409 -> re-read tip -> 200
    (7) dry-run plan with zero side effects (git/API call traces both empty)
    (8) gate4-block stop (real gate4 guard, clean PASS + dirty FAIL, zero
        push)
    plus unit vectors (repo derivation, ghproxy shape, masking, netrc,
    verdict table) and the CLI four-code checks.
    Every vector points --netrc at a nonexistent path on purpose: proof that
    credentials are read lazily (any real API attempt would exit 9)."""
    import shutil
    import tempfile

    pushci = os.path.abspath(__file__)
    repo_root = os.path.dirname(os.path.dirname(pushci))
    fx = lambda name: os.path.join(repo_root, "tests", "fixtures",
                                   "ci_triage_%s.json" % name)
    SHA40 = "5f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6"
    RUN_ID = 9026111201
    jobsB = json.load(io.open(fx("B_netred"), encoding="utf-8"))
    jobsA = json.load(io.open(fx("A_content_red"), encoding="utf-8"))
    TOOLS_CANNED = {"toolchain_dyld_doctor": {"rc": 0, "verdict": "healthy"},
                    "net_probe": {"rc": 0, "verdict": "STABLE"}}

    def runs_body(conclusion):
        return {"total_count": 1, "workflow_runs": [
            {"id": RUN_ID, "run_number": 7, "name": "ci",
             "head_branch": "work", "head_sha": SHA40,
             "status": "completed", "conclusion": conclusion,
             "html_url": "https://github.com/org/repo/actions/runs/%d" % RUN_ID}]}

    def poll_steps(outcomes, rerun_rounds=0):
        steps = []
        for i, c in enumerate(outcomes, start=1):
            resps = [{"method": "GET", "path": RUNS_QUERY, "status": 200,
                      "body": runs_body(c)}]
            if i <= rerun_rounds:
                resps.append({"method": "POST", "path": "/rerun",
                              "status": 201, "body": {}})
            steps.append({"at_round": i, "responses": resps})
        return steps

    def git_common(push_rc=0, rev_sha=SHA40, ls_sha=SHA40,
                   url="https://github.com/org/repo.git"):
        """Canned git sequence = the pushci call order: get-url, rev-parse,
        push, ls-remote."""
        return [{"args_contains": ["get-url"], "rc": 0, "stdout": url + "\n"},
                {"args_contains": ["rev-parse"], "rc": 0,
                 "stdout": rev_sha + "\n"},
                {"args_contains": ["push"], "rc": push_rc,
                 "stdout": "To %s\n" % url},
                {"args_contains": ["ls-remote"], "rc": 0,
                 "stdout": "%s\trefs/heads/work\n" % ls_sha}]

    tmp = tempfile.mkdtemp(prefix="rocqwash_pushci_self_")
    try:
        netrc_missing = os.path.join(tmp, "no_such.netrc")  # lazy-credential proof

        def setup(name, git_resps, api_steps, tools=None, jobs=None):
            d = os.path.join(tmp, name)
            repo = os.path.join(d, "repo")
            inj = os.path.join(d, "inj")
            os.makedirs(repo)
            os.makedirs(inj)
            scen = {"steps": api_steps, "tools": tools if tools else TOOLS_CANNED}
            if jobs is not None:
                scen["jobs"] = jobs
            with io.open(os.path.join(inj, "scenario.json"), "w",
                         encoding="utf-8", newline="\n") as fh:
                json.dump(scen, fh, indent=1, ensure_ascii=False, sort_keys=True)
            git_json = os.path.join(d, "git.json")
            with io.open(git_json, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"responses": git_resps}, fh, indent=1,
                          ensure_ascii=False, sort_keys=True)
            return {"dir": d, "repo": repo, "inj": inj, "git": git_json,
                    "out": os.path.join(d, "out.json"),
                    "git_calls": git_json[:-len(".json")] + ".calls.json",
                    "api_calls": os.path.join(inj, "api_calls.json")}

        def setup_flat(name, fixture, git_resps):
            """Flat-shape injection dir: the parallel agent fixture
            original verbatim becomes scenario.json."""
            d = os.path.join(tmp, name)
            repo = os.path.join(d, "repo")
            inj = os.path.join(d, "inj")
            os.makedirs(repo)
            os.makedirs(inj)
            shutil.copyfile(
                os.path.join(repo_root, "tests", "fixtures", "pushci_scenarios",
                             fixture + ".json"),
                os.path.join(inj, "scenario.json"))
            git_json = os.path.join(d, "git.json")
            with io.open(git_json, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"responses": git_resps}, fh, indent=1,
                          ensure_ascii=False, sort_keys=True)
            return {"dir": d, "repo": repo, "inj": inj, "git": git_json,
                    "out": os.path.join(d, "out.json"),
                    "git_calls": git_json[:-len(".json")] + ".calls.json",
                    "api_calls": os.path.join(inj, "api_calls.json")}

        def fire(s, extra=(), json_path=None, branch="work"):
            cmd = [sys.executable, "-B", pushci,
                   "--repo-path", s["repo"], "--branch", branch,
                   "--remote", "origin", "--injector", s["inj"],
                   "--git-caller", s["git"], "--netrc", netrc_missing,
                   "--sleep-scale", "0", "--json", json_path or s["out"]] \
                  + list(extra)
            p = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            out = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            return p.returncode, out

        def jload(path):
            with io.open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)

        # vector 1: green path preflight -> push -> success
        s = setup("v1_green", git_common(), poll_steps(["success"]))
        rc, out = fire(s)
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["schema"] == SCHEMA and rep["mode"] == "injector"
        assert rep["verdict"] == "success" and rep["final"]["verdict"] == "success"
        assert rep["final"]["conclusion"] == "success"
        assert rep["stages"]["push"]["sha"] == SHA40
        assert rep["stages"]["push"]["remote"] == "origin"
        assert rep["stages"]["push"]["ghproxy_used"] is False
        assert rep["stages"]["watch"]["rounds"] == 1
        assert rep["stages"]["watch"]["conclusion"] == "success"
        assert rep["stages"]["watch"]["run_tag"] == "#7 id=%d" % RUN_ID
        assert rep["stages"]["watch"]["policy"] == WATCH_POLICY
        assert rep["stages"]["heal"] == {"rounds": [], "fired_total": 0,
                                         "last_triage": None}, \
            rep["stages"].get("heal")
        assert "merge" not in rep["stages"]
        assert "repo_path" not in rep["args"], \
            "report carries no local paths (idempotence contract)"
        assert rep["stages"]["preflight"]["toolchain"] == {"verdict": "healthy",
                                                           "rc": 0}
        assert rep["stages"]["preflight"]["net"] == {"verdict": "STABLE", "rc": 0}
        assert "gate4" not in rep["stages"]["preflight"]
        gcalls = jload(s["git_calls"])
        assert len(gcalls) == 4, gcalls
        assert "http.version=HTTP/1.1" in gcalls[2]["args"] \
            and "push" in gcalls[2]["args"] and "origin" in gcalls[2]["args"] \
            and "work" in gcalls[2]["args"], gcalls[2]
        assert any("ls-remote" in a for a in gcalls[3]["args"]), gcalls[3]
        acalls = jload(s["api_calls"])
        assert len(acalls) == 1 and acalls[0]["method"] == "GET" \
            and acalls[0]["status"] == 200 \
            and RUNS_QUERY in acalls[0]["path"], acalls
        assert "FINAL VERDICT: success (exit 0)" in out, out[-300:]
        # determinism: rerunning with the same input keeps --json byte-identical
        out2 = s["out"] + ".2"
        rc, out = fire(s, json_path=out2)
        assert rc == 0, out[-300:]
        assert io.open(out2, "rb").read() == io.open(s["out"], "rb").read(), \
            "json byte drift is a violation"

        # vector 1b remote-is-authoritative: the ls-remote sha differs from the
        # local rev-parse tip -> loud note; watch still anchors the ls-remote
        # sha (canned runs head_sha matched)
        s = setup("v1b_remote_tip",
                  git_common(rev_sha="b" * 40, ls_sha=SHA40),
                  poll_steps(["success"]))
        rc, out = fire(s)
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["stages"]["push"]["sha"] == SHA40, rep["stages"]["push"]
        assert any("remote is authoritative" in e
                   for e in rep["evidence"]), rep["evidence"]

        # vector 2: one NETRED heal then attempt2 success (real ci_triage
        # --offline classifies B)
        s = setup("v2_netred", git_common(),
                  poll_steps(["failure", "success"], rerun_rounds=1),
                  jobs=jobsB)
        rc, out = fire(s)
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success"
        h = rep["stages"]["heal"]
        assert h["fired_total"] == 1 and len(h["rounds"]) == 1, h
        r0 = h["rounds"][0]
        assert r0["round"] == 1 and r0["family"] == "B-netred"
        assert r0["action"] == "rerun-after-stable-window"
        assert r0["probe"] == "STABLE" and r0["fired"] is True \
            and r0["http"] == 201, r0
        assert rep["stages"]["watch"]["rounds"] == 2
        assert h["last_triage"]["family"] == "B-netred", h["last_triage"]
        acalls = jload(s["api_calls"])
        assert sum(1 for c in acalls if c["method"] == "POST") == 1, acalls
        assert sum(1 for c in acalls if c["method"] == "GET") == 2, acalls

        # vector 3: content-failure stop (provably zero reruns, exit 2)
        s = setup("v3_content", git_common(), poll_steps(["failure"]),
                  jobs=jobsA)
        rc, out = fire(s)
        assert rc == 2, "content failure should exit 2, got %d\n%s" \
            % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "fix-content"
        h = rep["stages"]["heal"]
        assert h["rounds"] == [] and h["fired_total"] == 0, \
            "zero-rerun proof = heal.rounds empty, got %r" % (h,)
        assert h["last_triage"]["family"] == "A-content-red" \
            and h["last_triage"]["action"] == "fix-content", h["last_triage"]
        assert h["last_triage"]["evidence"], \
            "classification evidence should be recorded in last_triage"
        acalls = jload(s["api_calls"])
        assert all(c["method"] != "POST" for c in acalls), \
            "zero-rerun proof broken"
        assert any("no automatic repair" in e for e in rep["evidence"]), \
            rep["evidence"]
        assert json.dumps(rep["stages"], sort_keys=True).count("rerun") == 0, \
            "content-failure stages face carries zero rerun tokens " \
            "(cross-agent coupling contract)"

        # vector 4: heal x3 exhausted exit 1
        s = setup("v4_exhaust", git_common(),
                  poll_steps(["failure"] * 4, rerun_rounds=3), jobs=jobsB)
        rc, out = fire(s, ["--max-heal", "3"])
        assert rc == 1, "heal exhaustion should exit 1, got %d\n%s" \
            % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "heal-exhausted"
        h = rep["stages"]["heal"]
        assert len(h["rounds"]) == 3 and h["fired_total"] == 3, h
        assert all(r["fired"] and r["http"] == 201 for r in h["rounds"]), h
        assert rep["stages"]["watch"]["rounds"] == 4
        assert h["last_triage"]["family"] == "B-netred", h["last_triage"]
        acalls = jload(s["api_calls"])
        assert sum(1 for c in acalls if c["method"] == "POST") == 3, acalls
        assert sum(1 for c in acalls if c["method"] == "GET") == 4, acalls

        # vector 5: merge 200 flow
        merge_ok = [{"method": "GET", "path": RUNS_QUERY, "status": 200,
                     "body": runs_body("success")},
                    {"method": "GET", "path": "/pulls?head=org:work",
                     "status": 200, "body": [{"number": 42, "state": "open"}]},
                    {"method": "PUT", "path": "/pulls/42/merge", "status": 200,
                     "body": {"merged": True, "sha": "c" * 40}}]
        s = setup("v5_merge", git_common(),
                  [{"at_round": 1, "responses": merge_ok}])
        rc, out = fire(s, ["--merge"])
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success"
        m = rep["stages"]["merge"]
        assert m["pr"] == 42 and m["merged"] is True and m["attempts"] == [200], m
        assert m["method"] == "merge" and m["merge_sha"] == "c" * 40, m

        # vector 6: 409 then re-read tip then 200
        merge_409 = [{"method": "GET", "path": RUNS_QUERY, "status": 200,
                      "body": runs_body("success")},
                     {"method": "GET", "path": "/pulls?head=org:work",
                      "status": 200, "body": [{"number": 42}]},
                     {"method": "PUT", "path": "/pulls/42/merge", "status": 409,
                      "body": {"message": "Pull Request is not mergeable"}},
                     {"method": "GET", "path": "/branches/main", "status": 200,
                      "body": {"name": "main", "commit": {"sha": "b" * 40}}},
                     {"method": "PUT", "path": "/pulls/42/merge", "status": 200,
                      "body": {"merged": True, "sha": "c" * 40}}]
        s = setup("v6_merge409", git_common(),
                  [{"at_round": 1, "responses": merge_409}])
        rc, out = fire(s, ["--merge"])
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success"
        m = rep["stages"]["merge"]
        assert m["attempts"] == [409, 200] and m["merged"] is True, m
        assert m["main_tip"] == "b" * 40, m
        assert any("409" in e and "branches/main" in e
                   for e in rep["evidence"]), rep["evidence"]

        # vector 7: dry-run plan with zero side effects
        s = setup("v7_dryrun", [], [])
        rc, out = fire(s, ["--dry-run", "--pre-scan-gate4"])
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "dry-run" and rep["mode"] == "dry-run"
        assert rep["stages"] == {} and rep.get("plan"), rep
        assert any("push" in ln and "HTTP/1.1" in ln for ln in rep["plan"]), \
            rep["plan"]
        assert any("gate4" in ln for ln in rep["plan"]), rep["plan"]
        assert jload(s["git_calls"]) == [], "dry-run zero-git-call proof broken"
        assert jload(s["api_calls"]) == [], "dry-run zero-API-call proof broken"
        assert "PLAN [2] push" in out, out[-300:]

        # vector 8: gate4-block stop (real gate4 guard, clean PASS + dirty
        # FAIL, zero push)
        s = setup("v8_gate4",
                  [{"args_contains": ["get-url"], "rc": 0,
                    "stdout": "https://github.com/org/repo.git\n"},
                   {"args_contains": ["diff"], "rc": 0,
                    "stdout": "clean.v\ndirty.v\n"}], [])
        with io.open(os.path.join(s["repo"], "clean.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("(* Mission. pushci selftest clean fixture.\n"
                     "   Dependencies. none.\n   References. none.\n"
                     "   Constructivity. axiom-free construction.\n"
                     "   Build. coqc clean.v *)\n"
                     "Definition pushci_clean_unit : nat := 1.\n")
        with io.open(os.path.join(s["repo"], "dirty.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("Definition pushci_dirty_unit : nat := 1.\n")
        rc, out = fire(s, ["--pre-scan-gate4"])
        assert rc == 2, "gate4-block should exit 2, got %d\n%s" \
            % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "gate4-block"
        g4 = rep["stages"]["preflight"]["gate4"]
        assert g4["fail_count"] == 1, g4
        assert g4["fail_files"] == [os.path.join(s["repo"], "dirty.v")], g4
        assert os.path.join(s["repo"], "clean.v") in g4["pass_files"], g4
        assert os.path.join(s["repo"], "clean.v") not in g4["fail_files"], g4
        gcalls = jload(s["git_calls"])
        assert len(gcalls) == 2, "gate4-block should make zero rev-parse and " \
            "zero push calls: %s" % gcalls
        assert jload(s["api_calls"]) == [], \
            "gate4-block should make zero API calls"

        # vector 9: flat injection shape green path (parallel agent
        # fixture s1_green_path.json original verbatim; pushci.invalid
        # fake-domain derivation; both gates default green; canned.runs two
        # polls)
        S1SHA = "c0ffee00c0ffee00c0ffee00c0ffee00c0ffee01"
        S2SHA = "c0ffee00c0ffee00c0ffee00c0ffee00c0ffee02"
        INVURL = "https://pushci.invalid/octo-org/rocqwash-verify.git"

        def git_flat(sha, branch):
            return [{"args_contains": ["get-url"], "rc": 0,
                     "stdout": INVURL + "\n"},
                    {"args_contains": ["rev-parse"], "rc": 0,
                     "stdout": sha + "\n"},
                    {"args_contains": ["push"], "rc": 0,
                     "stdout": "To %s\n" % INVURL},
                    {"args_contains": ["ls-remote"], "rc": 0,
                     "stdout": "%s\trefs/heads/%s\n" % (sha, branch)}]

        s = setup_flat("v9_flat_s1", "s1_green_path", git_flat(S1SHA,
                                                               "topic-pushci-s1"))
        rc, out = fire(s, branch="topic-pushci-s1")
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success" and rep["mode"] == "injector"
        assert rep["stages"]["push"]["sha"] == S1SHA
        assert rep["stages"]["push"]["ghproxy_used"] is False
        assert rep["stages"]["watch"]["rounds"] == 2 \
            and rep["stages"]["watch"]["conclusion"] == "success"
        assert rep["stages"]["heal"]["rounds"] == [] \
            and rep["stages"]["heal"]["last_triage"] is None
        assert any("flat injection shape" in e
                   for e in rep["evidence"]), rep["evidence"]
        assert len(jload(s["api_calls"])) == 2
        assert len(jload(s["git_calls"])) == 4

        # vector 10: flat injection shape NETRED heal (s2_netred_heal.json
        # original verbatim; real triage --offline consumes canned.jobs[0];
        # canned.probe/rerun consumed one per use)
        s = setup_flat("v10_flat_s2", "s2_netred_heal", git_flat(S2SHA,
                                                                 "topic-pushci-s2"))
        rc, out = fire(s, branch="topic-pushci-s2")
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success"
        h = rep["stages"]["heal"]
        assert len(h["rounds"]) == 1 and h["fired_total"] == 1, h
        r0 = h["rounds"][0]
        assert r0["family"] == "B-netred" and r0["probe"] == "STABLE" \
            and r0["fired"] is True and r0["http"] == 201, r0
        assert h["last_triage"]["family"] == "B-netred"
        assert rep["stages"]["watch"]["rounds"] == 3
        acalls = jload(s["api_calls"])
        assert sum(1 for c in acalls if c["method"] == "POST") == 1, acalls
        assert sum(1 for c in acalls if c["method"] == "GET") == 3, acalls

        # vector 11: ghproxy reroute, three direct failures then the first
        # ghproxy attempt succeeds (verdict success; attempts=[origin rc1 x3,
        # ghproxy rc0]; ghproxy_used=True)
        ghp_url = "https://ghproxy.net/https://github.com/org/repo.git"
        s = setup("v11_ghproxy",
                  [{"args_contains": ["get-url"], "rc": 0,
                    "stdout": "https://github.com/org/repo.git\n"},
                   {"args_contains": ["rev-parse"], "rc": 0,
                    "stdout": SHA40 + "\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["ghproxy.net"], "rc": 0,
                    "stdout": "To %s\n" % ghp_url},
                   {"args_contains": ["ls-remote"], "rc": 0,
                    "stdout": "%s\trefs/heads/work\n" % SHA40}],
                  poll_steps(["success"]))
        rc, out = fire(s)
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "success"
        push = rep["stages"]["push"]
        assert push["ghproxy_used"] is True, push
        assert [a["rc"] for a in push["attempts"]] == [1, 1, 1, 0], push
        assert push["attempts"][-1]["target"] == ghp_url, push
        assert push["sha"] == SHA40
        gcalls = jload(s["git_calls"])
        assert len(gcalls) == 7, gcalls

        # vector 12: all push attempts fail (3 direct + 2 ghproxy, all
        # failing) -> unstable exit 1
        s = setup("v12_push_dead",
                  [{"args_contains": ["get-url"], "rc": 0,
                    "stdout": "https://github.com/org/repo.git\n"},
                   {"args_contains": ["rev-parse"], "rc": 0,
                    "stdout": SHA40 + "\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["push"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["ghproxy.net"], "rc": 1,
                    "stderr": "fatal: unable to access\n"},
                   {"args_contains": ["ghproxy.net"], "rc": 1,
                    "stderr": "fatal: unable to access\n"}],
                  poll_steps(["success"]))
        rc, out = fire(s)
        assert rc == 1, "all push attempts failing should exit 1, got %d\n%s" \
            % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "unstable"
        push = rep["stages"]["push"]
        assert [a["rc"] for a in push["attempts"]] == [1, 1, 1, 1, 1], push
        assert any("all push attempts failed" in e
                   for e in rep["evidence"]), rep["evidence"]

        # unit vectors: repo derivation / ghproxy shape / masking / netrc /
        # verdict table (zero network)
        assert repo_from_url("https://github.com/octo/rocq.git") == "octo/rocq"
        assert repo_from_url("https://tok@github.com/octo/rocq") == "octo/rocq"
        assert repo_from_url("git@github.com:octo/rocq.git") == "octo/rocq"
        assert repo_from_url("ssh://git@github.com/octo/rocq.git") == "octo/rocq"
        assert repo_from_url("https://gitlab.com/o/r.git") == "o/r", \
            "host unrestricted (fake-domain shim remotes derive the same " \
            "way; ghproxy has its own shape gate)"
        assert repo_from_url("https://pushci.invalid/octo-org/rocqwash-verify.git") \
            == "octo-org/rocqwash-verify"
        assert repo_from_url("https://github.com/solo") is None
        assert ghproxy_url("https://github.com/o/r.git") == \
            "https://ghproxy.net/https://github.com/o/r.git"
        assert ghproxy_url("https://gitlab.com/o/r.git") is None
        assert ghproxy_url("git@github.com:o/r.git") is None
        assert url_host("git@github.com:o/r.git") == "github.com"
        assert url_host("ssh://git@github.com/o/r.git") == "github.com"
        masks = url_secret_masks("https://u:sek@github.com/o/r")
        assert masks == ["sek"] and \
            mask_text("https://u:sek@github.com/o/r", masks) == \
            "https://u:***MASKED***@github.com/o/r"
        nf = os.path.join(tmp, "unit.netrc")
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine api.github.com login x password AAAA\n"
                     "machine github.com login octocat password TOK-1234\n")
        assert netrc_token(nf) == "TOK-1234", \
            "single-line 6-column shape should take column 6"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine github.com\nlogin octocat\npassword TOK-9\n")
        assert netrc_token(nf) == "TOK-9", "multi-line shape should parse the same"
        try:
            netrc_token(os.path.join(tmp, "absent.netrc"))
            assert False, "missing netrc should fail loudly"
        except PushciError as e:
            assert e.code == 9, e.code
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine gitlab.com login x password Y\n")  # overwrite with a no-github shape
        try:
            netrc_token(nf)
            assert False, "no github.com entry should fail loudly"
        except PushciError as e:
            assert e.code == 9, e.code
        assert set(VERDICT_EXIT) == {"success", "dry-run", "heal-exhausted",
                                     "unstable", "toolchain", "fix-content",
                                     "gate4-block"}, VERDICT_EXIT
        assert VERDICT_EXIT["success"] == 0 and VERDICT_EXIT["dry-run"] == 0
        assert VERDICT_EXIT["heal-exhausted"] == 1 \
            and VERDICT_EXIT["unstable"] == 1 \
            and VERDICT_EXIT["toolchain"] == 1
        assert VERDICT_EXIT["fix-content"] == 2 \
            and VERDICT_EXIT["gate4-block"] == 2

        # resilience layer: backoff sequence, Retry-After honored, real-urllib
        # _api retry runner, subprocess timeout kill (zero network, zero real
        # push; _urlopen/_sleep injected; the 403 x3 case yields [2,4,8])
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        assert _http_backoff.parse_retry_after("45") == 45.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, "HTTP-date is not guessed"

        class _Resp(object):
            """Canned response body (urlopen fake, zero network,
            context-manager shape)."""
            def __init__(self, payload=b"{}"):
                self.status = 200
                self._p = payload
                self.headers = {}
            def read(self):
                return self._p
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def _api_err(code, ra=None):
            hd = {"Retry-After": ra} if ra else {}
            return urllib.error.HTTPError(
                "https://api.github.com/x", code, "HTTP Error %d" % code, hd,
                io.BytesIO(b'{"message":"x"}'))

        def _seq_open(resps):
            it = iter(resps)
            def _open(req, timeout=None):
                r = next(it)
                if isinstance(r, Exception):
                    raise r          # canned error objects must raise (same semantics as urlopen)
                return r
            return _open

        api_netrc = os.path.join(tmp, "api.netrc")
        with io.open(api_netrc, "w", encoding="utf-8") as fh:
            fh.write("machine github.com login o password TOK\n")
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(403)] * 3
                                          + [_Resp(b'{"ok":1}')]),
                       _sleep=slept.append)
        code, body = ac("GET", "/repos/o/r/actions/runs?per_page=30")
        assert code == 200 and body == {"ok": 1} \
            and slept == [2.0, 4.0, 8.0], (code, body, slept)
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(503, ra="9"),
                                           _api_err(503), _api_err(503),
                                           _Resp(b'{"ok":2}')]),
                       _sleep=slept.append)
        code, body = ac("PUT", "/repos/o/r/pulls/1/merge",
                        body={"merge_method": "merge"})
        assert code == 200 and slept == [9.0, 4.0, 8.0], \
            (code, slept)                      # Retry-After header honored (replaces exponential)
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(429)] * 4),
                       _sleep=slept.append)
        code, body = ac("GET", "/repos/o/r/x")
        assert code == 429 and slept == [2.0, 4.0, 8.0], \
            (code, slept)                      # exhausted: original status handed to semantic adjudication
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(401)]), _sleep=slept.append)
        code, body = ac("GET", "/repos/o/r/x")
        assert code == 401 and slept == [], (code, slept)   # 401 is not retried
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(409)]), _sleep=slept.append)
        code, body = ac("PUT", "/repos/o/r/pulls/1/merge")
        assert code == 409 and slept == [], (code, slept)   # merge 409 is not retried

        # subprocess timeout kill (canned sleep subprocess, fail-loud 9 names
        # the call)
        sleepy = os.path.join(tmp, "sleepy_pushci.py")
        with io.open(sleepy, "w", encoding="utf-8") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        try:
            subproc_run([sys.executable, "-B", sleepy], 2,
                        "canned-sleep subprocess")
            assert False, "timeout should fail loudly with 9"
        except PushciError as e:
            assert e.code == 9 and "canned-sleep" in str(e) \
                and "2s" in str(e), e
        p = subproc_run([sys.executable, "-B", "-c", "print('fast')"], 10,
                        "fast-proc")
        assert p.returncode == 0, p.returncode

        # CLI four-code checks (real mode, all failing loudly before any side
        # effect)
        def raw(argv):
            p = subprocess.run([sys.executable, "-B", pushci] + argv,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            o = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            return p.returncode, o

        empty_repo = os.path.join(tmp, "empty_repo")
        os.makedirs(empty_repo)
        p, o = raw(["--help"])
        assert p == 0 and "usage" in o and "--timeout" in o \
            and "--retry-max" in o, o[-200:]
        p, o = raw(["--bogus"])
        assert p == 2, "unknown flag should rc=2, got %d" % p
        p, o = raw([])
        assert p == 2, "missing required args should rc=2, got %d" % p
        p, o = raw(["--repo-path", os.path.join(tmp, "no_repo"),
                    "--branch", "x"])
        assert p == 9, "missing repo should rc=9, got %d" % p
        p, o = raw(["--repo-path", os.path.join(tmp, "no_repo")])
        assert p == 9, "missing repo takes priority with 9 (absent --branch " \
            "does not mask it), got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "bogus"])
        assert p == 2, "unknown stage should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "watch"])
        assert p == 2, "watch=>push dependency should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "heal"])
        assert p == 2, "heal=>watch dependency should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x", "--merge",
                    "--steps", "preflight,push"])
        assert p == 2, "merge=>watch dependency should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--sleep-scale", "-1"])
        assert p == 2, "negative sleep-scale should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--timeout", "0"])
        assert p == 2, "timeout<1 should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--retry-max", "-1"])
        assert p == 2, "negative retry-max should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--max-heal", "-1"])
        assert p == 2, "negative max-heal should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--merge-method", "rebase"])
        assert p == 2, "merge-method outside the table should rc=2, got %d" % p
        inj = os.path.join(tmp, "v1_green", "inj")
        gitj = os.path.join(tmp, "v1_green", "git.json")
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--injector", inj])
        assert p == 2, "injector alone should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--git-caller", gitj])
        assert p == 2, "git-caller alone should rc=2, got %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--injector", os.path.join(tmp, "no_inj"),
                    "--git-caller", gitj])
        assert p == 9, "missing injector directory should rc=9, got %d" % p

        print("PUSHCI-SELFTEST PASS: eight vectors (green path + byte-identical "
              "determinism + remote-is-authoritative / NETRED x1 heal / content "
              "failure zero rerun / heal x3 exhausted / merge 200 / 409 "
              "re-read / dry-run zero side effects / gate4-block real guard) + "
              "two flat-shape vectors (parallel seat-worker s1/s2 fixture "
              "verbatim) + two retry-discipline vectors (ghproxy reroute "
              "success / all-push-failed unstable) + unit vectors (repo "
              "derivation, ghproxy, masking, netrc, verdict table) + "
              "resilience layer (backoff 403 x3 -> [2,4,8], Retry-After "
              "honored, 429 exhaustion handed up, 401/409 not retried, canned "
              "sleep subprocess timeout kill with 9 naming the call) + CLI "
              "four codes, all passed (zero real network, zero real push, "
              "zero compilation; --netrc lazily-read proof)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- main flow -------------------------------------------------------------------

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
        description="one-shot post-fix push-and-CI pipeline (preflight checks, "
                    "push, watch, heal, verdict, optional merge; orchestrates "
                    "the four tools; offline-testable injection built in)")
    ap.add_argument("--repo-path", default=None, metavar="DIR",
                    help="target repository directory (zero hardcoding, fully "
                         "parameterized)")
    ap.add_argument("--branch", default=None, metavar="B",
                    help="branch to push and watch")
    ap.add_argument("--base-ref", default="main", metavar="REF",
                    help="gate4 pre-scan diff base (<base>...<branch>, "
                         "default main)")
    ap.add_argument("--remote", default="origin", metavar="NAME",
                    help="push remote name (default origin)")
    ap.add_argument("--pre-scan-gate4", action="store_true",
                    dest="pre_scan_gate4",
                    help="preflight also runs the gate4 header-guard pre-scan "
                         "(proceeds only when FAIL=0)")
    ap.add_argument("--pr", type=int, default=None, metavar="N",
                    help="explicit PR number (skips pulls resolution under "
                         "--merge)")
    ap.add_argument("--merge", action="store_true",
                    help="merge the PR after green (default merge method)")
    ap.add_argument("--merge-method", choices=("merge", "squash"),
                    default="merge", dest="merge_method",
                    help="merge method (default merge, the merge-commit-"
                         "on-branch precedent)")
    ap.add_argument("--max-heal", type=int, default=3, metavar="N",
                    help="heal round cap (default 3; over the cap = "
                         "heal-exhausted)")
    ap.add_argument("--watch-interval", type=float, default=150.0, metavar="S",
                    help="watch poll interval seconds (default 150)")
    ap.add_argument("--probe-interval", type=float, default=60.0, metavar="S",
                    help="net_probe round interval seconds (default 60)")
    ap.add_argument("--watch-max-rounds", type=int, default=0, metavar="N",
                    help="watch round-cap safety valve (default 0 = "
                         "unlimited; over the cap fails loudly with 9)")
    ap.add_argument("--timeout", type=int, default=120, metavar="S",
                    help="subprocess anti-hang timeout seconds (default 120; "
                         "git and the four tool subprocesses are killed on "
                         "timeout, fail-loud 9 names the call)")
    ap.add_argument("--retry-max", type=int, default=3, metavar="N",
                    help="retry cap for real-urllib API 403/429/5xx with "
                         "backoff (default 3, exponential base 2s, "
                         "Retry-After seconds header honored, canned paths "
                         "never retry)")
    ap.add_argument("--steps", default=",".join(STAGE_ALL), metavar="LIST",
                    help="stage selection (default runs all: %s)"
                         % ",".join(STAGE_ALL))
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="offline injection: DIR/scenario.json scenario "
                         "(steps[].at_round -> canned API + canned tools + "
                         "canned jobs)")
    ap.add_argument("--git-caller", default=None, metavar="FILE",
                    dest="git_caller",
                    help="offline injection: canned git response scenario "
                         "(must be paired with --injector)")
    ap.add_argument("--sleep-scale", type=float, default=1.0, metavar="F",
                    help="multiplier on every sleep (selftest uses 0 = zero "
                         "real sleep)")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc path (default ~/.netrc; machine github.com "
                         "column 6 = token; read lazily; never read in "
                         "injector mode)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="report output path (rocqwash-pushci/1, sort_keys)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run",
                    help="print the plan only, zero side effects, exit 0")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        validate(args)
        pl = Pipeline(args)
    except PushciError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(e.code)
    except (ValueError, OSError) as e:
        print("FAIL-LOUD: scenario load failed: %s" % e, file=sys.stderr)
        sys.exit(9)

    try:
        verdict, code, ev = pl.run()
    except StopVerdict as sv:
        verdict, code, ev = sv.verdict, sv.code, sv.evidence
        # stops are always loud (without the verdict stage stdout stays
        # silent, but stderr still reports; silent exit is forbidden)
        print("STOP-VERDICT: %s (exit %d)" % (sv.verdict, sv.code),
              file=sys.stderr)
        for e in ev:
            print("  - %s" % e, file=sys.stderr)
    except PushciError as e:
        pl.dump_canned_logs()
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(e.code)
    sys.exit(pl.finalize(verdict, ev, code))


if __name__ == "__main__":
    main()
