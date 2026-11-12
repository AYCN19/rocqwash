#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cw_sentinel.py — real-time dynamic sentinel for rocqwash (tools/): a live
companion for workflows that performs cleaning, shape washing, troubleshooting,
and blockage clearing — the sentinel is an inspection event stream over three
signal sources; classification and chain-root selection are always delegated
to the existing engines (zero new engines, zero reimplementation).

Three signal sources (combinable; at least one required):
  ① CI path = --watch-repo ORG/REPO [--branch B]... (repeatable, multiple
     groups):
       GET /repos/{repo}/actions/runs?per_page=30 (RUNS_QUERY, same convention
       as pushci.py; the token comes from the ~/.netrc machine github.com
       line's 6th-column password — netrc_token is a same-convention copy of
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
       authority — five families plus the all-passing state — lives in
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
its rotated generations; by default it is monotonic within the process) — a
consumer sorting by seq recovers the global order. ts comes from the time
clock; with --sleep-scale 0, ts is disabled (--selftest determinism
dependency) and events carry the note "ts=off".
JSONL rotation (--emit-max-bytes N; bounds the on-disk footprint for
long-lived runs): checked before each append — if the file's current bytes
plus the new line's bytes exceed N → rotate first, then append:
FILE.1→FILE.2 (an existing FILE.2 is overwritten and discarded; two
generations are kept) →FILE→FILE.1→new FILE empty. A single line longer than
N = the line cannot be split; it is written into the gap anyway (after
rotation a single line may still exceed the cap; the next append pre-check
rotates again); rotation is noted explicitly on stdout and counted in the
report's emit_rotations; a rename failure → 9. seq continues across
generations (baseline = the file plus the line counts of .1/.2 — rotated
generations belong to the same event stream; sorting by seq recovers the
global order across generations).

--on-red 'CMD template': the {family}/{run}/{repo} placeholders are
substituted from event fields (missing fields become the empty string) →
executed via a subprocess shell (60s timeout cap; rc≠0/timeout is recorded
explicitly in the actions log and stdout, and does not change the sentinel's
exit code — on-red is a side action, outside the tool's own verdict surface).
Requires --emit (side actions must accompany an on-disk event stream —
trigger evidence and the action log stay auditable; without --emit → 2; the
same guard as --on-red-preset). Default: none = report-only; **zero action is
the default** (same discipline as cure_applier's dry-run default).

--on-red-preset NAME: preset actions for failing events (**repeatable =
chained**; see below) — presets are template sugar: expanded into internal
command templates, they run through the same executor as --on-red (60s cap;
rc≠0/timeout recorded explicitly in the actions log; the sentinel's exit
code unchanged; placeholder substitution reuses the existing --on-red path;
zero new execution paths). Mutually exclusive with --on-red (both given →
rc=2 fail-loud, no silent choice — "preset wins" means a preset occupies the
on-red action slot; giving both is an ambiguous-usage error). Five presets
(ON_RED_PRESETS table; program paths located relative to the sentinel itself,
following the TOOLS_DIR precedent):
  unclog = python3 -B tools/unclog.py --src {src} --json {emit_dir}/unclog_{run}.json
    (**--apply not included by default = unclog only dry-runs; a human
    reviews, then applies — the default-dry-run rule for automatic hookups**)
  pushci = python3 -B tools/pushci.py --repo-path {repo_path} --branch {branch}
    --json {emit_dir}/pushci_{run}.json --dry-run (--dry-run default = print
    the plan only, zero side effects)
  wash-shape = python3 -B tools/wash_shape.py --dir {src} --json
    {emit_dir}/wash_shape_{run}.json (**--apply not in the template = shape
    washing only produces a plan; the plan writes nothing to disk; a human
    reviews, then applies — the same default-dry-run rule**)
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
  repo/run are exactly this — the failing event supplies the values; there is
  nothing to look up at expansion time); anything else → missing, rc=2; no
  '=' / empty K·V / duplicate keys / unknown keys (a key not in the parameter
  surface — for a chain, the parameter surface is the union over the whole
  chain) / an orphan --on-red-arg → 2; {emit_dir} resolves to the directory
  of --emit (preset outputs share the disk with the event stream; --emit is
  required, otherwise 2). A missing preset component → 9.
Chaining: --on-red-preset is repeatable (e.g. --on-red-preset unclog
  --on-red-preset triage) = chained, same trigger — expanded in the given
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
canned paths never touch the real network and never retry — the
offline-testability rule).
Subprocess anti-hang = --subproc-timeout S (default 120s): ci_triage /
chain_graph run_py calls kill the subprocess on timeout + fail-loud 9 naming
the call (--timeout separately covers single HTTP requests, default 30 — two
different clocks, not merged); on-red side actions (including
--on-red-preset expansions, same executor) remain under the ON_RED_TIMEOUT
60s cap and do not change the sentinel's exit code (the previously agreed
convention is unchanged).

Resilience layer, transport guard (protects long-lived sentinel runs against
transport-layer crashes): ① transient transport classes
(TRANSIENT_TRANSPORT_ERRORS = IncompleteRead / RemoteDisconnected /
BadStatusLine / the full ConnectionError family / socket.timeout — distinct
from the HTTPError status-code class) → bounded retry (--net-retries default
3 attempts, backoff 5s/15s/45s = the net_backoff_delays pure function,
inheriting the bounded-backoff semantics = a bounded table indexed by
attempt; each attempt builds a fresh Request+urlopen and discards the
half-read body); retries are exhausted before raising 9 (fail-loud
preserved; after raising, ② provides the fallback); non-transient errors
(HTTPError status-code semantics / URLError connection-establishment / other
unknown exceptions) are never retried and propagate as-is — swallowing
non-transient errors is forbidden.
② loop-level fallback (skip a round rather than crash a long-lived run):
each poll_round signal source is wrapped by poll_source_guarded exception
handling (loop mode only) → that source skips this round + the event stream
records {kind:source-error} (explicit, not silent); the next round retries —
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
  polling is idempotent — unlike pushci's steps shape, which is consumed in
  order); a miss fails loudly with 9 — the canned table must fully cover the
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
failure / malformed keys) → fail-loud 9, hard refusal — the tool neither
swallows nor rebuilds (seen is an idempotence ledger; a silent rebuild would
break the duplicate-event protection and re-report failing events; the original
file is left untouched); recovery has exactly two paths: delete the file
manually (the next round starts from zero state) or --rebuild-state explicit
rebuild (discard the existing seen and start from zero; an explicit
STATE-REBUILD note on stdout + report state_rebuilt=true; must be given with
--state-file, otherwise rc=2 — with no state there is nothing to rebuild).

Orchestration rule: ci_triage / chain_graph are always invoked as direct
subprocesses (the same pattern as pushci's _run_py — pure logic with zero
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
RUNS_QUERY = "/actions/runs?per_page=30"          # 承 pushci.py:141 同款
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
    sys.path.insert(0, TOOLS_DIR)   # 同目录共享退避小模块（无 __init__ 包结构）
import _http_backoff

# --on-red-preset 预设表（任务书钦定模板·程序路径按哨自身相对定位承 TOOLS_DIR
# 先例·零硬编码绝对路径）：静态占位 {src}/{repo_path}/{branch}/{emit_dir} 展开
# 时实替·动态 {run}/{repo}/{family} 留给 fire_on_red 事件直替。unclog 不带
# --apply＝疏通只干跑·wash-shape 不带 --apply＝洗形只出 plan（两干跑缺省铁律）
# ·pushci 带 --dry-run＝只打计划零副作用·triage 事件直替 {repo}/{run}＝对本
# 红 run 复诊·cw-doctor 零参面＝全缺省体检。
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
# 各预设必传参数表（声明化·--on-red-arg K=V 静态族实替面）：缺（非动态族）/
# 重/无 '='/未知键 → 2。triage 的 repo/run 属动态事件直替族（fire_on_red
# 既有键·红事件自带·pushci 静态键命名 repo_path 正为避开 {repo} 动态名）——
# 未给 --on-red-arg 即事件直替非缺。
PRESET_REQUIRED_ARGS = {"unclog": ("src",),
                        "pushci": ("repo_path", "branch"),
                        "wash-shape": ("src",),
                        "triage": ("repo", "run"),
                        "cw-doctor": ()}
# 动态占位族（fire_on_red 事件直替键·缺字段替空串既有语义）——必传守卫对
# 此族放行（事件出值·展开期无可查）。
PRESET_DYNAMIC_KEYS = ("family", "run", "repo")

# buildlog 词面（判类谱 token·ci_triage.py:95-108 同源）：BUILD-FAIL／
# EXIT=134（C 环境断链）／Error:（A 内容红）
BUILDLOG_SIGNAL_RE = re.compile(r"BUILD-FAIL|EXIT=134|\bError:")

EVENT_EVIDENCE_CAP = 8      # ci-red 事件 evidence 条数帽（响亮截断注记）
EVENT_LINE_CAP = 200        # 事件内单行证据/命中行字符帽
BUILDLOG_HIT_CAP = 50       # 单轮 build-signal 命中行帽（超出 truncated 注记）
ON_RED_TIMEOUT = 60         # on-red 子进程超时秒（旁路动作防卡哨）

# v51 传输层瞬态类（承哨长驻 round10 IncompleteRead 崩·更新账 v50 在案＝真崩栈
# http.client.IncompleteRead(371261 read, 72721 expected) 自 resp.read() 抛出）：
# body 中途断流（IncompleteRead）/服务器断连（RemoteDisconnected·兼
# ConnectionResetError 与 BadStatusLine 两族面）/坏状态行（BadStatusLine）/
# 连接断（ConnectionError 全族含 Reset/Refused/Aborted/BrokenPipe）/读超时
# （socket.timeout）——均瞬态可重试。区别于 HTTPError 状态码类（401/404 语义面
# 走 --retry-max 判面）与 URLError 连接建立面（DNS/连接失败=9 快败）——禁吞
# 非瞬态错误：不在此列的异常零重试原样上抛（fail-loud）。
TRANSIENT_TRANSPORT_ERRORS = (
    http.client.IncompleteRead,
    http.client.RemoteDisconnected,
    http.client.BadStatusLine,
    ConnectionError,
    socket.timeout,
)
NET_RETRY_BASE = 5.0        # 传输层退避基秒（任务书钦定 5s/15s/45s）
NET_RETRY_RATIO = 3.0       # 退避指数比（5→15→45＝×3·缺省 3 发）


class SentryError(Exception):
    """带退出码的 fail-loud 异常（code: 2=用法错·9=信号源不可达/形坏）。"""

    def __init__(self, msg, code=9):
        super(SentryError, self).__init__(msg)
        self.code = code


# ---- 小件 -------------------------------------------------------------------

def sleep_scaled(sec, scale):
    """time.sleep(sec*scale)·scale=0 零真睡（pushci.py:184 sleep_scaled 同款·
    selftest 矢量依赖）。"""
    time.sleep(max(0.0, float(sec) * float(scale)))


def net_backoff_delays(net_retries):
    """传输层瞬断退避秒表（v51 任务书钦定 5s/15s/45s＝base 5·比 3·纯函数
    零钟零随机同参重跑恒同·继承 v38 backoff 语义＝有界表按 attempt 取延迟·
    耗尽上抛 fail-loud）。判例：net_retries=3 → [5.0, 15.0, 45.0]·0 → []
    （零重试一发定谳）；负/非 int → ValueError（fail-loud）。"""
    if not isinstance(net_retries, int) or isinstance(net_retries, bool) \
            or net_retries < 0:
        raise ValueError("net_retries 须非负 int·实测 %r" % (net_retries,))
    return [NET_RETRY_BASE * (NET_RETRY_RATIO ** i) for i in range(net_retries)]


def _safe_exc(e):
    """异常安全文案「ClassName: str(e)」——str 本身炸（如 IncompleteRead
    partial 非 bytes 形其 __str__ 内 len() 再炸）→ 仅类名。耗尽上抛与 loop
    兜底注记路径专用：文案层禁再炸遮蔽原错（v51 实测判例）。"""
    try:
        return "%s: %s" % (type(e).__name__, e)
    except Exception:
        return type(e).__name__


def now_iso():
    """UTC ISO8601 秒精度 Z 形（ts 字段·--sleep-scale 0 时整事件不用）。"""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def clip(s, cap=EVENT_LINE_CAP):
    """单行证据截断（≤cap 字符·超长 ... 尾）。"""
    s = str(s)
    return s if len(s) <= cap else s[:cap - 3] + "..."


def netrc_token(path, machine="github.com"):
    """netrc 手动解析：machine <m> login <l> password <p> → password token。
    ci_triage.py:226 同款副本（单行 6 列形与多行形通吃）·缺文件/无条目/空值
    → fail-loud 9（token 永不回显）。"""
    if not os.path.isfile(path):
        raise SentryError("netrc 缺失: %s（CI 线上路需 machine %s ... password "
                          "形凭据）" % (path, machine), 9)
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
                    raise SentryError("netrc machine %s password 为空" % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise SentryError("netrc 无 machine %s password 形条目（单行 6 列形："
                      "第 6 列=token）: %s" % (machine, path), 9)


def run_py(tool_path, cli, timeout=None):
    """python3 -B <tool> <cli> 子进程（stdout+stderr 合流·pushci.py:591 同款）。
    纯逻辑引擎零编译故不经 cpu_guard（probe_engine.py:10 判例：真编译才须
    guard）·缺件 → 9。韧性层 v37：timeout 给定时防挂（--subproc-timeout·
    缺省 120s）——超时=子进程杀＋fail-loud 9 报调用名（零悬挂）。"""
    if not os.path.isfile(tool_path):
        raise SentryError("工具链件缺失: %s" % tool_path, 9)
    try:
        p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SentryError("子进程超时被杀（--subproc-timeout=%ss·调用: "
                          "python3 -B %s %s）"
                          % (timeout, os.path.basename(tool_path),
                             " ".join(str(c) for c in cli[:1])), 9)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


# ---- 注入层（离线可测铁律④：--injector 在场绝不发真请求）---------------------

def load_injector(path):
    """injector 文件 → {"responses":[...]}。缺文件/形坏/空表 → 9。"""
    if not os.path.isfile(path):
        raise SentryError("injector 缺失: %s" % path, 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise SentryError("injector 形坏（解析失败）: %s (%s)" % (path, e), 9)
    if not isinstance(data, dict) or not isinstance(data.get("responses"), list) \
            or not data["responses"]:
        raise SentryError("injector 形坏（须 {\"schema\":...,\"responses\":"
                          "[{url_contains,status,body}...]} 非空表）: %s" % path, 9)
    for i, r in enumerate(data["responses"]):
        if not isinstance(r, dict) or not isinstance(r.get("url_contains"), str):
            raise SentryError("injector 形坏（responses[%d] 缺 url_contains 串）"
                              ": %s" % (i, path), 9)
    return data


def api_get_json(url, token, timeout, injector, retry_max=3, sleep_scale=1.0,
                 net_retries=3, _open=None, _sleep=None):
    """只读 GET → (status, parsed_json)。唯一网络动作·注入点单函数：
    injector 在场按 url_contains 首中即用（可循环复用·哨轮询幂等语义）·未命中
    fail-loud 9 绝不静默走真网络·且 canned 路径零重试（离线可测铁律）；缺席真
    urllib（韧性层 v37：403/429/5xx 指数退避重试·base 2s·帽 retry_max·
    Retry-After 秒数头优先替当次延迟·_http_backoff 纯函数；耗尽或 4xx 语义面
    → 9·连接失败 → 9·body 非合法 JSON → 9）。韧性层 v51：传输层瞬态类
    （TRANSIENT_TRANSPORT_ERRORS·IncompleteRead 真崩栈在案）有界重试——帽
    net_retries 缺省 3 发·退避 net_backoff_delays（5s/15s/45s）·每发全新
    Request+urlopen（半读残体弃）·耗尽才上抛 9（fail-loud 保持·上抛后由
    poll_source_guarded loop 兜底该源本轮 skip 宁跳轮不崩驻）；非瞬态类
    （URLError/其余未知异常）零重试原样上抛禁吞。_open/_sleep 注入位
    （selftest 零网络矢量·canned resp.read() 抛传输异常即读函数注入面）。"""
    if injector is not None:
        for r in injector["responses"]:
            if r["url_contains"] in url:
                status = int(r.get("status", 200))
                body = r.get("body")
                if status != 200:
                    raise SentryError("CI API HTTP %d（injector canned）: %s"
                                      % (status, url), 9)
                return 200, body
        raise SentryError("injector canned 未覆盖 GET %s（canned 表须全覆盖·"
                          "禁静默走真网络）" % url, 9)
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
                raise SentryError("CI API HTTP %d: %s（%s）"
                                  % (e.code, body.strip()[:160], url), 9)
            ra = _http_backoff.parse_retry_after(
                e.headers.get("Retry-After") if e.headers is not None else None)
            do_sleep(ra if ra is not None else delays[attempt])
            attempt += 1
        except TRANSIENT_TRANSPORT_ERRORS as e:
            # v51：瞬态传输面有界重试（每发全新连接·半读残体弃）·耗尽才上抛
            # 9 fail-loud 保持——loop 层捕获后该源本轮 skip 下轮再试（宁跳轮
            # 不崩驻）；禁吞＝计数器有界·耗尽必报。
            if net_attempt >= net_retries:
                raise SentryError(
                    "CI API 传输层瞬断重试耗尽（%d 发·退避 %s）: %s (%s)"
                    % (net_retries, net_delays, url, _safe_exc(e)), 9)
            do_sleep(net_delays[net_attempt])
            net_attempt += 1
        except (urllib.error.URLError, OSError) as e:
            raise SentryError("CI API 不可达: %s (%s)" % (url, e), 9)
    try:
        return 200, json.loads(raw.decode("utf-8"))
    except ValueError as e:
        raise SentryError("CI API body 非 JSON: %s (%s)" % (url, e), 9)


# ---- state（seen 幂等持久层）-------------------------------------------------

def new_state():
    return {"schema": STATE_SCHEMA, "repos": {}, "ledgers": {}, "buildlogs": {}}


def load_state(path, rebuild=False):
    """state 装载（崩溃恢复语义）：缺省/文件缺失＝零态起步；损坏（JSON 解析
    失败/键形坏）→ fail-loud 9 红拒·禁静默重建（seen 是幂等账·静默重建＝
    红事件重报面失守·损坏原件原样不动）；rebuild=True（--rebuild-state 显式
    重建）＝唯一合法重建路——弃既有内容从零起（响亮注记由 run_sentry 出）。"""
    if path is None or rebuild:
        return new_state()
    if not os.path.isfile(path):
        return new_state()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise SentryError("state 文件形坏（解析失败·禁静默重建）: %s (%s)"
                          % (path, e), 9)
    for k in ("repos", "ledgers", "buildlogs"):
        if not isinstance(st.get(k), dict):
            raise SentryError("state 文件形坏（缺 %s dict·禁静默重建）: %s"
                              % (k, path), 9)
    return st


def save_state(path, st):
    if path is None:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise SentryError("state 文件目录缺失: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- 事件流（JSONL append+fsync＋stdout 镜像）--------------------------------

def make_event(sentry, kind, fields):
    """事件组装：seq 事件流内单调（sentry["seq"]·emit 在位时以文件现有行数为
    基跨进程续号）·ts 由 --sleep-scale 0 关（注记·确定性）。fields 自带 note
    时 ts=off 注记并入头（不打架）。"""
    ev = {"schema": EVENT_SCHEMA, "seq": sentry["seq"], "kind": kind}
    sentry["seq"] += 1
    ev.update(fields)
    if sentry["ts_enabled"]:
        ev["ts"] = now_iso()
    else:
        off = "ts=off（--sleep-scale 0·确定性输出）"
        base = ev.pop("note", None)
        ev["note"] = (off + "｜" + base) if base else off
    return ev


def rotate_emit(path):
    """JSONL 轮转一代（--emit-max-bytes 超限触发·保留 2 代）：FILE.1→FILE.2
    （旧 FILE.2 覆盖弃）→FILE→FILE.1→新 FILE 空。rename 失败 → 9。"""
    gen1, gen2 = path + ".1", path + ".2"
    try:
        if os.path.exists(gen1):
            os.replace(gen1, gen2)
        if os.path.exists(path):
            os.replace(path, gen1)
    except OSError as e:
        raise SentryError("事件流轮转失败（%s → %s/%s）: %s"
                          % (path, gen1, gen2, e), 9)


def emit_seq_base(emit_path):
    """seq 跨进程续基（--emit 在位）：本体＋轮转代（.1/.2）现有非空行数和——
    轮转代同属一条事件流·跨代续号不重号（消费方按 seq 排序恢复全局序）。
    读败 → 9。"""
    base = 0
    for p in (emit_path, emit_path + ".1", emit_path + ".2"):
        if os.path.isfile(p):
            try:
                with io.open(p, "r", encoding="utf-8") as fh:
                    base += sum(1 for ln in fh if ln.strip())
            except OSError as e:
                raise SentryError("事件流读基失败: %s (%s)" % (p, e), 9)
    return base


def emit_event(sentry, ev):
    """--emit JSONL append（flush+fsync）＋stdout 镜像（响亮）。--emit-max-bytes
    在位时追加前查超限（本体现有字节＋新行字节＞帽）→ 先轮转再追加（.1/.2
    保留 2 代·stdout 响亮注记·rotations 计数入 report）；单行超帽＝行不可
    分割·空档直写。emit 写败/轮转败 → 9。"""
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
                raise SentryError("事件流大小探测失败: %s (%s)" % (path, e), 9)
            if size > 0 and size + nbytes > cap:
                rotate_emit(path)
                sentry["rotations"] += 1
                sys.stdout.write("emit 轮转: %s → %s.1（旧 .1→.2 弃·保留 2 代）\n"
                                 % (path, path))
        try:
            with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as e:
            raise SentryError("事件流出账失败: %s (%s)" % (path, e), 9)
    sentry["events"].append(ev)


# ---- CI 路（①runs 轮询→新 completed run→ci_triage 子进程判类）----------------

def runs_url(repo):
    return API_ROOT + "/repos/%s%s" % (repo, RUNS_QUERY)


def jobs_api_path(repo, run_id):
    return "/repos/%s/actions/runs/%s/jobs?per_page=100&page=1" % (repo, run_id)


def triage_run_offline(repo, run_id, jobs_body, timeout=None):
    """哨取 jobs（api_get_json·injector 可注入）→ 落盘 tmp → subprocess
    ci_triage --offline（pushci.py:969 run_triage injector 同款·真子进程真
    判类·零网络）→ rocqwash-ci-triage/1 report。ci_triage rc≠0 → 9；
    timeout 给定时 --subproc-timeout 防挂（超时=杀＋9 报调用名）。"""
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
            raise SentryError("ci_triage 子进程 rc=%d: %s" % (rc, out[-300:]), 9)
        try:
            with io.open(out_path, "r", encoding="utf-8") as fh:
                rep = json.load(fh)
        except (ValueError, UnicodeDecodeError) as e:
            raise SentryError("ci_triage report 形坏: %s (%s)" % (out_path, e), 9)
        if rep.get("schema") != "rocqwash-ci-triage/1":
            raise SentryError("ci_triage report schema 不识别: %r"
                              % rep.get("schema"), 9)
        return rep
    finally:
        for p in (jobs_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def poll_ci_repo(sentry, spec, st):
    """单 repo 单轮：GET runs → 新 completed run 逐个判类 → ci-red 事件。
    绿 run 亦记 seen（幂等·二跑零事件零重判）。branch 过滤＝head_branch ∈
    spec.branches（无 branches=全收）。在飞 run 不记不判（等 completed）。"""
    repo = spec["repo"]
    token = sentry["token"]            # injector 在场为 None·惰性已取
    _, body = api_get_json(runs_url(repo), token, sentry["timeout"],
                           sentry["injector"], retry_max=sentry["retry_max"],
                           net_retries=sentry["net_retries"],
                           sleep_scale=sentry["args"].sleep_scale)
    runs = None
    if isinstance(body, dict):
        runs = body.get("workflow_runs")     # GitHub API 真形
        if runs is None:
            runs = body.get("runs")          # pushci watch 证据形（py:880）
    if not isinstance(runs, list):
        raise SentryError("runs API 形坏（无 workflow_runs/runs 列表）: %s"
                          % runs_url(repo), 9)
    seen = st["repos"].setdefault(repo, {}).setdefault("seen_runs", {})
    matched = [r for r in runs if isinstance(r, dict)
               and (not spec["branches"]
                    or str(r.get("head_branch") or "") in spec["branches"])]
    matched.sort(key=lambda r: ((r.get("run_number") or 0),
                                (r.get("id") or 0)))   # 升序＝老 run 先报·确定性
    new_runs = red_runs = 0
    for r in matched:
        if r.get("status") != "completed":
            continue                      # 在飞/排队·不记 seen 等完成
        rid = r.get("id")
        if rid is None or str(rid) in seen:
            continue
        new_runs += 1
        family = action = None
        evidence = []
        conclusion = str(r.get("conclusion") or "")
        if conclusion == "success":
            note = "conclusion=success（绿·记 seen 不出事件）"
        else:
            _, jobs_body = api_get_json(
                API_ROOT + jobs_api_path(repo, rid), token, sentry["timeout"],
                sentry["injector"], retry_max=sentry["retry_max"],
                net_retries=sentry["net_retries"],
                sleep_scale=sentry["args"].sleep_scale)
            if not isinstance(jobs_body, dict) \
                    or not isinstance(jobs_body.get("jobs"), list):
                raise SentryError("jobs API 形坏（须 {\"total_count\":N,"
                                  "\"jobs\":[...]}）: run=%s" % rid, 9)
            rep = triage_run_offline(repo, rid, jobs_body,
                                     timeout=sentry["subproc_timeout"])
            runv = rep.get("run") or {}
            family = runv.get("family")
            action = runv.get("action")
            evidence = [clip(e) for e in (runv.get("evidence") or [])
                        ][:EVENT_EVIDENCE_CAP]
            note = "判类=rocqwash-ci-triage/1（ci_triage 子进程 --offline）"
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


# ---- 本地账路（②新 ledger→chain_graph 子进程→TOP 链根）-----------------------

def poll_ledgers(sentry, ledgers_dir, st):
    """新 probe/ledger JSON（mtime+名字 seen）→ chain_graph 单件出 TOP →
    blocking 事件（top_order 首名·附 n/dependents/self 三分）。TOP 空（无
    rc1 缺库链根·全绿账）＝零红事件·report 仍响亮记 new。chain_graph rc≠0
    （半写形坏件等）→ 9。"""
    if not os.path.isdir(ledgers_dir):
        raise SentryError("ledgers 目录缺失: %s" % ledgers_dir, 9)
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
            raise SentryError("ledger 不可读: %s (%s)" % (path, e), 9)
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
                raise SentryError("chain_graph 子进程 rc=%d（件 %s）: %s"
                                  % (rc, path, cout[-300:]), 9)
            try:
                with io.open(gpath, "r", encoding="utf-8") as fh:
                    g = json.load(fh)
            except (ValueError, UnicodeDecodeError) as e:
                raise SentryError("chain_graph 出账形坏（件 %s）: %s"
                                  % (path, e), 9)
        finally:
            try:
                os.unlink(gpath)
            except OSError:
                pass
        if g.get("schema") != "rocqwash-chain-graph/1" \
                or not isinstance(g.get("top_order"), list):
            raise SentryError("chain_graph 出账 schema/top_order 不识别"
                              "（件 %s）" % path, 9)
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
                "note": "TOP 链根=chain_graph rocqwash-chain-graph/1 top_order "
                        "首名（self 字段判链根可洗性·chain_graph.py:88 判例）"}))
            out["red_events"] += 1
        # TOP 空＝无 rc1 缺库链根（全绿账）→ 零红事件·report new 已响亮记
        seen[name] = sig
    return out


# ---- 本地堵路（③buildlog tail 增量 grep）-------------------------------------

def poll_buildlog(sentry, log_path, st):
    """tail 增量 grep（state 记字节 offset·只认完整行防半行误报）→ 词面命中
    出 build-signal 事件。文件未在卷＝编译未开写·零事件非红（present=false
    响亮注记非静默）·offset 记 0 等出现。"""
    seen = st["buildlogs"]
    rec = seen.get(log_path) or {}
    offset = int(rec.get("offset") or 0)
    out = {"path": log_path, "present": False, "offset_before": offset,
           "offset_after": offset, "hits": 0}
    if not os.path.isfile(log_path):
        out["note"] = "日志未在卷（编译未开写·零事件非红·等出现）"
        return out
    with io.open(log_path, "rb") as fh:
        if offset:
            fh.seek(offset)
        data = fh.read()
    size = offset + len(data)
    full = data
    if data and not data.endswith(b"\n"):
        cut = data.rfind(b"\n")
        full = data[:cut + 1]          # 半行留给下轮（防半行误报）
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
            "note": "词面 BUILD-FAIL/EXIT=134/Error:（判类谱 A/C token·"
                    "ci_triage.py:95-118 同源）"}))
    seen[log_path] = {"offset": offset + len(full)}
    return out


# ---- on-red（旁路动作·零动作是缺省）------------------------------------------

def parse_on_red_args(arg_pairs, face, face_label):
    """--on-red-arg K=V 解析＋形守卫（无 '='/空 K·V/重键/未知键 → 2）。face=
    合法键面（单预设＝其必传表·链式＝全链参数面并集——链中任一预设声明即
    合法·单预设并集＝其面与既有守卫同款）。→ params dict（替换按 sort_keys
    序·确定性）。"""
    params = {}
    for pair in (arg_pairs or []):
        if "=" not in pair:
            raise SentryError("--on-red-arg 形须 K=V: %r" % pair, 2)
        k, v = pair.split("=", 1)
        if not k or not v:
            raise SentryError("--on-red-arg K/V 皆须非空: %r" % pair, 2)
        if k in params:
            raise SentryError("--on-red-arg 重键: %r" % k, 2)
        if k not in face:
            raise SentryError("--on-red-arg 键 %r 不属 %s（参数面 %s）"
                              % (k, face_label,
                                 "/".join(face) if face else "空"), 2)
        params[k] = v
    return params


def check_preset_required(name, params):
    """必传守卫（PRESET_REQUIRED_ARGS[name] 逐键·同款 fail-loud）：--on-red-arg
    已给即静态实替；未给而键属动态族（PRESET_DYNAMIC_KEYS＝fire_on_red 事件
    直替既有键）即事件直替（triage 的 repo/run——红事件自带·展开期原样保留·
    非缺）；二者皆非 → 缺 rc=2。"""
    missing = [k for k in PRESET_REQUIRED_ARGS[name]
               if k not in params and k not in PRESET_DYNAMIC_KEYS]
    if missing:
        raise SentryError("--on-red-preset %s 必传参数缺（--on-red-arg "
                          "%s=...·动态族 %s 事件直替免传）: %s"
                          % (name, missing[0],
                             "/".join(PRESET_DYNAMIC_KEYS),
                             "/".join(PRESET_REQUIRED_ARGS[name])), 2)


def expand_preset_cmd(name, params, emit_path):
    """单预设命令展开（必传守卫 → --emit 守卫 → 器件在盘 → 占位实替）。静态
    键按 sort_keys 序实替·{emit_dir} 取 --emit 所在目录（预设出账与事件流
    同盘）；动态族原样保留给 fire_on_red 事件直替（占位替换复用现有 --on-red
    路径·零新执行路径）。--emit 缺 → 2·预设器件缺 → 9。"""
    check_preset_required(name, params)
    if not emit_path:
        raise SentryError("--on-red-preset 需 --emit（{emit_dir} 取事件流所在"
                          "目录·预设出账同盘）", 2)
    if not os.path.isfile(ON_RED_PRESET_TOOLS[name]):
        raise SentryError("预设器件缺失: %s" % ON_RED_PRESET_TOOLS[name], 9)
    cmd = ON_RED_PRESETS[name]
    for k in sorted(params):
        cmd = cmd.replace("{%s}" % k, params[k])
    cmd = cmd.replace("{emit_dir}",
                      os.path.dirname(os.path.abspath(emit_path)))
    return cmd


def expand_on_red_preset(name, arg_pairs, emit_path):
    """--on-red-preset 单预设展开 → on-red 命令模板串（ON_RED_PRESETS 表·
    预设即模板 sugar）。preset 不识别/参数缺·重·无 '='/空 K·V/未知键/
    --emit 缺 → 2·预设器件缺 → 9。"""
    if name not in ON_RED_PRESETS:
        raise SentryError("--on-red-preset 不识别: %r（可选 %s）"
                          % (name, "/".join(sorted(ON_RED_PRESETS))), 2)
    params = parse_on_red_args(arg_pairs, PRESET_REQUIRED_ARGS[name],
                               "preset %s" % name)
    return expand_preset_cmd(name, params, emit_path)


def expand_on_red_presets(names, arg_pairs, emit_path):
    """--on-red-preset 链式展开（旗可重复·v41 任务书③）：逐名不识别 → 2；
    --on-red-arg 命名空间全链共享——未知键判**全链参数面并集**（链式示例
    unclog+triage 仅传 src 即成链·triage 的 repo/run 走事件直替）；必传缺
    逐预设判（动态族放行）--emit/器件守卫同单预设。→ 命令模板列表（按给定
    序零重排——按序执行契约·sort_keys 确定性不受影响）。"""
    for name in names:
        if name not in ON_RED_PRESETS:
            raise SentryError("--on-red-preset 不识别: %r（可选 %s）"
                              % (name, "/".join(sorted(ON_RED_PRESETS))), 2)
    face = sorted({k for name in names for k in PRESET_REQUIRED_ARGS[name]})
    params = parse_on_red_args(arg_pairs, face,
                               "preset 链 %s" % "+".join(names))
    return [expand_preset_cmd(name, params, emit_path) for name in names]


def fire_on_red(sentry, ev):
    """红事件旁路动作执行（--on-red 单模板与 --on-red-preset 链展开表同一
    入口同一执行器）：模板逐条占位替换（{family}/{run}/{repo}·事件字段直替
    缺字段空串）→ subprocess shell 执行。**按序执行·一败续行**——某条
    rc≠0/超时只响亮入账（stdout 注记＋actions 笔）不裁停后条·不改哨退出码
    （旁路动作非器面）。每条模板一笔 actions 账（链 N 条=N 笔·schema 同
    单条）。→ 本事件出账笔列表。"""
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
                sys.stdout.write("on-red 注记: cmd rc=%d（旁路动作·不改哨退出码）"
                                 "\n" % p.returncode)
        except subprocess.TimeoutExpired:
            entry["rc"] = None
            entry["output"] = "timeout（%ds 帽）" % ON_RED_TIMEOUT
            sys.stdout.write("on-red 注记: cmd 超时（旁路动作·不改哨退出码）\n")
        sentry["actions"].append(entry)
        entries.append(entry)
    return entries


# ---- 单轮巡检 ----------------------------------------------------------------

def poll_source_guarded(sentry, label, fn, *args):
    """loop 长驻兜底（v51 任务书②·哨语义宁跳轮不崩驻）：单信号源巡检异常
    （api 传输耗尽 SentryError 9／子进程硬错／任何未分类异常——传输层重试
    修复后的残余面兜底）→ 事件流 {kind:source-error} 注记（响亮非静默）＋
    该源本轮 skip·下轮再试——异常路径 seen 幂等账未记＝下轮自然重报（宁重复
    不丢件判例同源）。once 模式直通不兜底（工作流步骤 fail-loud rc 9 语义
    保持）。KeyboardInterrupt/SystemExit 非 Exception 不吞（长驻可中断）；
    source-error 非 on-red 触发面（红事件族过滤不动）。"""
    if sentry["mode"] != "loop":
        return fn(*args)
    try:
        return fn(*args)
    except Exception as e:
        err = clip(_safe_exc(e), 400)
        emit_event(sentry, make_event(sentry, "source-error", {
            "source": label, "error": err,
            "note": "loop 长驻兜底：该源本轮 skip·下轮再试（宁跳轮不崩驻·"
                    "响亮注记非静默·seen 未记下轮重报宁重复不丢件）"}))
        sys.stdout.write("source-error 注记: %s 本轮 skip（%s）\n" % (label, err))
        return {"source": label, "skipped": True, "error": err}


def poll_round(sentry, st, round_no):
    """单轮三路巡检 → 轮 report dict（--json 覆盖写·sort_keys）。源硬错
    （SentryError）逐层上抛由 run_sentry 裁停——fail-loud 不带病运行（once
    模式语义保持）；loop 模式逐源经 poll_source_guarded 兜底＝异常源本轮
    skip＋source-error 事件注记·下轮再试（v51 任务书②·宁跳轮不崩驻）。"""
    a = sentry["args"]
    sys.stdout.write("=== CW-SENTINEL round=%d mode=%s（红是数据非器红）===\n"
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
        sys.stdout.write("本轮事件 %d 件（seq %s..%s）\n"
                         % (len(sentry["events"]),
                            sentry["events"][0]["seq"],
                            sentry["events"][-1]["seq"]))
    else:
        sys.stdout.write("本轮零事件（红是数据非器红·exit 0）\n")
    return rep


def write_json_report(path, rep):
    """--json report 每轮覆盖写（sort_keys·rocqwash-sentinel/1）。"""
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise SentryError("report 目录缺失: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- 主流程 -------------------------------------------------------------------

def parse_watch_specs(argv):
    """argv 预扫 --watch-repo/--branch 组归属（argparse 只认 token 不认组·
    组语义＝--watch-repo 开新组·--branch 归当前组）。--branch 先于任何
    --watch-repo → 用法错 2。"""
    specs = []
    cur = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--watch-repo" or a.startswith("--watch-repo="):
            val = a.split("=", 1)[1] if "=" in a else (
                argv[i + 1] if i + 1 < len(argv) else None)
            if val is None:
                raise SentryError("--watch-repo 缺值（形 ORG/REPO）", 2)
            if not REPO_RE.match(val):
                raise SentryError("--watch-repo 形须 ORG/REPO: %r" % val, 2)
            cur = {"repo": val, "branches": []}
            specs.append(cur)
            i += 2 if "=" not in a else 1
        elif a == "--branch" or a.startswith("--branch="):
            val = a.split("=", 1)[1] if "=" in a else (
                argv[i + 1] if i + 1 < len(argv) else None)
            if val is None:
                raise SentryError("--branch 缺值", 2)
            if cur is None:
                raise SentryError("--branch 须跟在 --watch-repo 组内"
                                  "（先 --watch-repo 后 --branch）", 2)
            cur["branches"].append(val)
            i += 2 if "=" not in a else 1
        else:
            i += 1
    return specs


def build_sentry(args):
    """args → sentry 运行态（惰性 token·ts 开关·injector 装载·用法校验 rc 2）。"""
    if args.sleep_scale < 0:
        raise SentryError("--sleep-scale 须≥0 实测 %s" % args.sleep_scale, 2)
    if args.interval is not None and args.interval < 0:
        raise SentryError("--interval 须≥0 实测 %s" % args.interval, 2)
    if args.max_rounds < 0:
        raise SentryError("--max-rounds 须≥0 实测 %s" % args.max_rounds, 2)
    mode = "loop" if args.loop else ("once" if args.once else None)
    if mode is None:
        raise SentryError("须 --once 或 --loop 二选一", 2)
    if args.once and args.loop:
        raise SentryError("--once 与 --loop 互斥", 2)
    specs = parse_watch_specs(sys.argv[1:])
    if not specs and not args.watch_ledgers and not args.watch_buildlog:
        raise SentryError("三路信号源至少一路：--watch-repo／--watch-ledgers／"
                          "--watch-buildlog", 2)
    if args.injector and not specs:
        raise SentryError("--injector 只服务 CI 路（须与 --watch-repo 同给）", 2)
    if args.once and args.interval is not None:
        raise SentryError("--interval 只属 --loop（once 单轮无轮间隔）", 2)
    if args.once and args.max_rounds:
        raise SentryError("--max-rounds 只属 --loop", 2)
    if args.on_red_preset and args.on_red:
        raise SentryError("--on-red-preset 与 --on-red 互斥（同给 rc=2·"
                          "preset 即占 on-red 动作槽·禁静默择一）", 2)
    if args.on_red_args and not args.on_red_preset:
        raise SentryError("--on-red-arg 只服务 --on-red-preset", 2)
    if args.on_red and not args.emit:
        raise SentryError("--on-red 须 --emit（旁路动作必伴随事件流落盘·"
                          "触发证据与动作账可审计·与 --on-red-preset 同款"
                          "守卫）", 2)
    if args.retry_max < 0:
        raise SentryError("--retry-max 须≥0 实测 %s" % args.retry_max, 2)
    if args.net_retries < 0:
        raise SentryError("--net-retries 须≥0 实测 %s" % args.net_retries, 2)
    if args.subproc_timeout < 1:
        raise SentryError("--subproc-timeout 须≥1 实测 %s"
                          % args.subproc_timeout, 2)
    if args.emit_max_bytes is not None:
        if not args.emit:
            raise SentryError("--emit-max-bytes 须与 --emit 同给（轮转只属"
                              "事件流本体）", 2)
        if args.emit_max_bytes < 1:
            raise SentryError("--emit-max-bytes 须≥1 实测 %d"
                              % args.emit_max_bytes, 2)
    if args.rebuild_state and not args.state_file:
        raise SentryError("--rebuild-state 须与 --state-file 同给（无 state "
                          "即无物可重建）", 2)
    on_red = None
    if args.on_red_preset:
        on_red = expand_on_red_presets(args.on_red_preset, args.on_red_args,
                                       args.emit)
    elif args.on_red:
        on_red = [args.on_red]          # plain 单模板同表形（执行器同入口）
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
        sentry["seq"] = emit_seq_base(args.emit) + 1   # 跨代续号（本体＋.1/.2）
    return sentry


def run_sentry(args):
    """双模主循环：once 单轮·loop interval 序贯（--max-rounds 轮帽 0=无限）。
    源硬错 → sentinel-error 事件（若 emit 在位）+ rc 9 退出（fail-loud 不带
    病运行·任务书 9 口径）。v51：loop 模式源级异常在 poll_round 内逐源兜底
    skip（source-error 注记·宁跳轮不崩驻·任务书②）——走到本层的硬错面＝
    兜底层自身再败（如 emit 出账失败）·仍 fail-loud。state 每轮末落盘
    （事件先 emit 后存 state·宁重复不丢件）。"""
    sentry = build_sentry(args)
    if args.rebuild_state:
        existed = os.path.isfile(args.state_file)
        sys.stdout.write("STATE-REBUILD: %s（--rebuild-state 显式重建·%s）\n"
                         % (args.state_file,
                            "既有 seen 弃·从零起" if existed
                            else "原无 state·从零起"))
    st = load_state(args.state_file, rebuild=bool(args.rebuild_state))
    interval = args.interval if args.interval is not None else 60.0
    round_no = 0
    try:
        if sentry["specs"] and sentry["injector"] is None:
            sentry["token"] = netrc_token(args.netrc)   # 惰性·injector 不取
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
            "note": "源硬错·fail-loud rc=%d 退出（不带病运行）" % e.code})
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
        description="实时动态哨（v37 用户令）——三路信号源（CI runs／本地 "
                    "probe 台账链根／buildlog 词面）→JSONL 事件流·once/loop "
                    "双模·判类链根全编排 ci_triage/chain_graph 子进程·零新引擎")
    ap.add_argument("--once", action="store_true",
                    help="单轮巡检出账退出（工作流步骤用）")
    ap.add_argument("--loop", action="store_true",
                    help="长驻轮巡·JSONL 事件流追加（工作流后台 bash 任务用）")
    ap.add_argument("--interval", type=float, default=None, metavar="S",
                    help="loop 轮间隔秒（默认 60·只属 --loop）")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=0,
                    metavar="N", help="loop 轮帽（0=无限·默认 0·只属 --loop）")
    ap.add_argument("--watch-repo", dest="watch_repo", action="append",
                    default=None, metavar="ORG/REPO",
                    help="CI 路：轮询 GET /actions/runs?per_page=30（可重复·"
                         "后随 --branch 归当前组）")
    ap.add_argument("--branch", action="append", default=None, metavar="B",
                    help="branch 过滤（归最近一个 --watch-repo 组·可多个）")
    ap.add_argument("--watch-ledgers", dest="watch_ledgers", default=None,
                    metavar="DIR", help="本地账路：新 probe/ledger JSON 目录")
    ap.add_argument("--watch-buildlog", dest="watch_buildlog", default=None,
                    metavar="FILE", help="本地堵路：编译日志 tail 增量 grep")
    ap.add_argument("--state-file", dest="state_file", default=None,
                    metavar="FILE", help="seen 幂等状态文件（loop 须给·"
                                         "rocqwash-sentinel-state/1）")
    ap.add_argument("--emit", default=None, metavar="FILE",
                    help="事件流 JSONL append（fsync）·缺省仅 stdout 镜像")
    ap.add_argument("--emit-max-bytes", dest="emit_max_bytes", type=int,
                    default=None, metavar="N",
                    help="事件流轮转帽（追加前超限即轮转 .1/.2 保留 2 代·seq "
                         "跨代续号·须与 --emit 同给）")
    ap.add_argument("--rebuild-state", dest="rebuild_state",
                    action="store_true",
                    help="显式重建 state（弃既有 seen 从零起·唯一合法重建路·"
                         "损坏 state 缺省红拒 9 禁静默重建·须与 --state-file "
                         "同给）")
    ap.add_argument("--on-red", dest="on_red", default=None, metavar="CMD",
                    help="红事件命令模板（{family}/{run}/{repo} 占位）·须 "
                         "--emit（与 preset 同款守卫）·缺省无=report-only "
                         "零动作是缺省")
    ap.add_argument("--on-red-preset", dest="on_red_preset", action="append",
                    default=None, metavar="NAME",
                    help="红事件预设动作模板（可重复＝链式·按序执行一败续行："
                         "unclog=疏通只干跑·pushci=推送 dry-run·wash-shape="
                         "洗形只出 plan·triage=红 run 重判类〔repo/run 事件"
                         "直替〕·cw-doctor=零参体检·参数经 --on-red-arg 透传"
                         "·与 --on-red 互斥同给 rc=2·同一执行器零新执行路径）")
    ap.add_argument("--on-red-arg", dest="on_red_args", action="append",
                    default=None, metavar="K=V",
                    help="预设透传参数（可重复·静态族：unclog/wash-shape 需 "
                         "src·pushci 需 repo_path+branch；triage 的 repo/"
                         "run 属动态族事件直替免传·{emit_dir} 取 --emit 所在"
                         "目录）")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc 路径（默认 ~/.netrc·machine github.com 第 6 "
                         "列=token·ci_triage 同款）")
    ap.add_argument("--timeout", type=int, default=30, metavar="S",
                    help="单请求超时秒（默认 30）")
    ap.add_argument("--retry-max", dest="retry_max", type=int, default=3,
                    metavar="N",
                    help="CI API 403/429/5xx 退避重试帽（默认 3·指数 base 2s·"
                         "Retry-After 秒数头尊重·仅真 urllib 路·injector "
                         "canned 不重试）")
    ap.add_argument("--net-retries", dest="net_retries", type=int, default=3,
                    metavar="N",
                    help="传输层瞬断重试帽（默认 3 发·退避 5s/15s/45s·瞬态类＝"
                         "IncompleteRead/RemoteDisconnected/BadStatusLine/"
                         "ConnectionError/socket.timeout·耗尽 9 上抛 loop 层"
                         "逐源 skip 宁跳轮不崩驻；--retry-max 另承 HTTP 状态码"
                         "面 base 2s）")
    ap.add_argument("--subproc-timeout", dest="subproc_timeout", type=int,
                    default=120, metavar="S",
                    help="子进程防挂超时秒（默认 120·ci_triage/chain_graph 调用"
                         "超时=杀＋fail-loud 9 报调用名；--timeout 另承 HTTP "
                         "单请求超时）")
    ap.add_argument("--injector", default=None, metavar="FILE",
                    help="canned API 响应 JSON（rocqwash-sentinel-injector/1·"
                         "零真网络离线可测·须与 --watch-repo 同给）")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float,
                    default=1.0, metavar="F",
                    help="sleep 缩放（0=零真睡＋关事件 ts·selftest 依赖）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="每轮 report 出账（rocqwash-sentinel/1·覆盖写）")
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


# ---- 自测（--injector canned＋tmp fixture＋--sleep-scale 0·零真网络零编译）----

def selftest():
    """内嵌冻结向量组（tmp injector/ledger/buildlog fixture·--sleep-scale 0·
    零真网络零编译·判类真走 ci_triage 子进程链根真走 chain_graph 子进程）：
    ①once 新 run 出 ci-red 事件·二跑 seen 幂等零事件 ②ledger 新件出 blocking
    ③buildlog 增量 grep（半行不误报）④--on-red 占位替换执行实证（canned 命令
    写 tmp 标记文件）⑤loop 三轮 JSONL 序贯 ⑥--emit JSONL 可解析逐行合法
    ＋确定性字节恒同＋CLI 四码＋injector 未覆盖 9＋目录缺 9⑨--on-red-preset
    展开 sugar＋触发捕获＋与 --on-red 互斥 rc=2＋预设参数缺误 rc=2＋plain
    --on-red 缺 --emit rc=2（双路同守卫·preset 路径回归同节）
    ⑬预设表数据化扩展（新三预设 wash-shape/triage/cw-doctor 占位替换＋
    triage repo/run 事件直替族＋静态覆盖＋必传缺/重/形坏/未知键/空参面
    rc2＋链式双预设展开〔全链并集面·按序零重排〕＋链式触发按序一败续行
    rc=9→rc=0 双笔入账）
    ⑩韧性层退避（403×3→[2,4,8]·Retry-After 尊重·耗尽 9·401 不重试·run_py
    canned sleep 子进程超时杀 9 报调用名）⑪--state-file 崩溃恢复（损坏红拒
    9 禁静默重建·原件不动／--rebuild-state 显式重建红事件复现／缺
    --state-file rc=2）⑫--emit-max-bytes JSONL 轮转（超限先轮转再追加·
    .1/.2 保留 2 代·seq 跨代续号不重·缺 --emit/N<1 rc=2）
    ⑭韧性层 v51 传输层瞬断（canned IncompleteRead 读函数注入〔_Resp.read 抛
    真崩栈同形 IncompleteRead(371261, 72721)〕·首二发抛第三发成退避 [5,15]·
    RemoteDisconnected/BadStatusLine/socket.timeout 全员可重试·重试耗尽上抛
    9 退避序断言 [5,15,45]·--net-retries 帽可调＝1 发一睡即耗尽·非瞬态
    ValueError 原样穿透零吞零睡·URLError 连接建立面快败 9 零重试·loop 逐源
    skip＝canned 401 双轮 rc0 不崩 source-error 注记×2 seen 零记账〔宁跳轮
    不崩驻·宁重复不丢件〕·once 同形仍 9 对照既有〔八〕）
    ⑮部署形冒烟（监督壳 examples/sentinel_supervisor.sh：bash -n 语法检＋
    关键行 grep 断言〔重启帽／退避／state 续接注记／收兵钩位留空 return 0／
    guard 位／rc 分诊／三件套落位名／零硬编码绝对路径〕——静态断言非真跑·
    零执行零网络·只验部署工件在库与结构逐点在位）。"""
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
        # canned：runs 表（1 个 completed failure run 178）＋jobs 表（A-content-red
        # 形·红步名 Build ∈ ci_triage 判类谱 A 词面）
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

        # 〔一〕once 新 run 出 ci-red 事件·二跑 seen 幂等零事件
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
        assert "ts" not in ev and "ts=off" in ev.get("note", ""), ev  # ts 关注记
        # state 记 seen·绿与否全记
        st = json.load(io.open(state1, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA \
            and st["repos"][REPO]["seen_runs"]["178"]["family"] \
            == "A-content-red", st
        # 二跑：seen 幂等零事件
        p = run(["--once", "--watch-repo", REPO, "--branch", "main",
                 "--injector", inj_path, "--state-file", state1,
                 "--emit", emit1, "--json", rep1, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs2 = [json.loads(l) for l in io.open(emit1, encoding="utf-8")
                if l.strip()]
        assert len(evs2) == 1, "二跑应零新事件·实测 %d" % len(evs2)
        rep = json.load(io.open(rep1, encoding="utf-8"))
        assert rep["events"] == [] and rep["sources"]["ci"][0]["new_runs"] == 0, rep

        # 〔二〕ledger 新件出 blocking（LibX 可洗链根＋B1 缺库消费者）
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
        # 同件不变二跑幂等零事件
        p = run(["--once", "--watch-ledgers", ldir, "--state-file", state2,
                 "--emit", emit2, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs2 = [json.loads(l) for l in io.open(emit2, encoding="utf-8")
                if l.strip()]
        assert len(evs2) == 1, "同件二跑应零新事件·实测 %d" % len(evs2)

        # 〔三〕buildlog 增量 grep（半行不误报·二跑只报新增）
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
        assert evs[0]["hits"] == ["BUILD-FAIL at step 2"], evs[0]  # 半行不误报
        st = json.load(io.open(state3, encoding="utf-8"))
        assert st["buildlogs"][log]["offset"] > 0, st
        # 追加新信号（含半行）→ 二跑只报新增完整行
        with io.open(log, "a", encoding="utf-8") as fh:
            fh.write("\nEXIT=134 in job3\nError: LibX.v:12: no\nHALF-NOEOL")
        p = run(["--once", "--watch-buildlog", log, "--state-file", state3,
                 "--emit", emit3, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]
        evs = [json.loads(l) for l in io.open(emit3, encoding="utf-8")
               if l.strip() and json.loads(l)["kind"] == "build-signal"
               and json.loads(l)["hits"] == ["EXIT=134 in job3",
                                             "Error: LibX.v:12: no"]]
        assert len(evs) == 1, "二跑应只报新增完整行·实测 %s" % evs
        # 负例行不命中
        assert not BUILDLOG_SIGNAL_RE.search("EXIT=0 all good") \
            and not BUILDLOG_SIGNAL_RE.search("no errors here"), "词面负例失守"

        # 〔四〕--on-red 占位替换执行实证（canned 命令写 tmp 标记文件）
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
            "占位替换失真: %r" % m
        # 缺省零动作：不给 --on-red → 无 actions
        state4b = os.path.join(tmp, "state4b.json")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", state4b, "--sleep-scale", "0"])
        assert p.returncode == 0, p.stdout[-600:]

        # 〔五〕loop 三轮 JSONL 序贯（--max-rounds 3·轮 1 报红·轮 2/3 幂等零新）
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

        # 〔六〕--emit JSONL 可解析逐行合法＋sort_keys 字节形＋seq 序贯
        for path in (emit1, emit2, emit3, emit4, emit5):
            seqs = []
            for line in io.open(path, encoding="utf-8"):
                if not line.strip():
                    continue
                ev = json.loads(line)          # 逐行可解析
                assert ev["schema"] == EVENT_SCHEMA, ev
                assert line == json.dumps(ev, ensure_ascii=False,
                                          sort_keys=True) + "\n", \
                    "行非 sort_keys 规范式: %s" % line
                seqs.append(ev["seq"])
            assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs), \
                "seq 序贯失守: %s" % seqs

        # 〔七〕确定性：once（ts off·同 tmp state 复位）重跑 report 字节恒同
        d1 = os.path.join(tmp, "det1")
        os.mkdir(d1)
        rep_a = os.path.join(d1, "a.json")
        rep_b = os.path.join(d1, "b.json")
        common = ["--once", "--watch-ledgers", ldir, "--sleep-scale", "0"]
        assert run(common + ["--json", rep_a]).returncode == 0
        assert run(common + ["--json", rep_b]).returncode == 0
        assert io.open(rep_a, "rb").read() == io.open(rep_b, "rb").read(), \
            "report 字节漂移＝违例"

        # 〔八〕CLI 四码＋用法面＋源不可达 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺模式应 rc=2 实测 %d" % p.returncode
        p = run(["--once", "--loop"])
        assert p.returncode == 2, "双模同给应 rc=2 实测 %d" % p.returncode
        p = run(["--once"])
        assert p.returncode == 2, "三源全缺应 rc=2 实测 %d" % p.returncode
        p = run(["--once", "--branch", "main", "--watch-ledgers", ldir])
        assert p.returncode == 2, "--branch 先于 --watch-repo 应 rc=2 实测 %d" \
            % p.returncode
        p = run(["--once", "--watch-repo", "justname"])
        assert p.returncode == 2, "repo 形错应 rc=2 实测 %d" % p.returncode
        p = run(["--once", "--watch-repo", REPO, "--interval", "5"])
        assert p.returncode == 2, "once 带 interval 应 rc=2 实测 %d" % p.returncode
        p = run(["--once", "--max-rounds", "3", "--watch-ledgers", ldir])
        assert p.returncode == 2, "once 带 max-rounds 应 rc=2 实测 %d" \
            % p.returncode
        p = run(["--once", "--watch-ledgers",
                 os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "目录缺应 rc=9 实测 %d" % p.returncode
        # injector canned 覆盖 401 → 9
        inj401 = {"schema": INJECTOR_SCHEMA, "responses": [
            {"url_contains": "/actions/runs?", "status": 401,
             "body": {"message": "Bad credentials"}}]}
        p401 = os.path.join(tmp, "inj401.json")
        with io.open(p401, "w", encoding="utf-8") as fh:
            json.dump(inj401, fh)
        p = run(["--once", "--watch-repo", REPO, "--injector", p401,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, "CI 401 应 rc=9 实测 %d" % p.returncode
        assert "HTTP 401" in p.stdout or "HTTP 401" in p.stderr \
            or "sentinel-error" in p.stdout, p.stdout[-300:]
        # injector canned 未覆盖 → 9（禁静默走真网络）
        injgap = {"schema": INJECTOR_SCHEMA, "responses": [
            {"url_contains": "/definitely-not", "status": 200, "body": {}}]}
        pgap = os.path.join(tmp, "injgap.json")
        with io.open(pgap, "w", encoding="utf-8") as fh:
            json.dump(injgap, fh)
        p = run(["--once", "--watch-repo", REPO, "--injector", pgap,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, "canned 未覆盖应 rc=9 实测 %d" % p.returncode
        assert "未覆盖" in p.stdout, p.stdout[-300:]
        # injector 单边（无 CI 路）→ 2
        p = run(["--once", "--watch-ledgers", ldir, "--injector", inj_path])
        assert p.returncode == 2, "injector 单边应 rc=2 实测 %d" % p.returncode

        # 〔九〕--on-red-preset：展开 sugar 单元断言＋触发捕获（canned 命令
        # 落 actions 账·占位替换断言）＋与 --on-red 互斥 rc=2＋参数缺误 rc=2
        ev9 = os.path.join(tmp, "events9.jsonl")
        cmd = expand_on_red_preset("unclog", ["src=/abs/fake_src"], ev9)
        assert cmd == ("python3 -B %s --src /abs/fake_src --json "
                       "%s/unclog_{run}.json" % (UNCLOG_TOOL, tmp)), cmd
        cmd = expand_on_red_preset("pushci", ["repo_path=/r", "branch=main"],
                                   ev9)
        assert cmd == ("python3 -B %s --repo-path /r --branch main --json "
                       "%s/pushci_{run}.json --dry-run" % (PUSHCI_TOOL, tmp)), \
            cmd
        assert cmd.endswith("--dry-run") and "{run}" in cmd, cmd  # 干跑缺省·{run} 留执行器
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
                assert False, "负面展开应 rc=2"
            except SentryError as e:
                assert e.code == 2, "负面展开应 2 实测 %d" % e.code
        # 触发捕获：真子进程链（canned CI 红事件 → 同一执行器代跑 unclog
        # 干跑命令·rc≠0 响亮入账·哨退出码仍 0——旁路动作非器面铁律实证）
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
            "预设展开失真: %r" % act["cmd"]
        assert act["rc"] == 9, "代跑 unclog（fixture 无 --world）应 rc=9 入账: %r" \
            % act
        mw = re.search(r"workdir -> (\S+)", act.get("output") or "")
        if mw:
            shutil.rmtree(mw.group(1), ignore_errors=True)  # 清代跑 mkdtemp
        # 同给 --on-red → 2；preset 不识别/参数缺/缺 --emit/孤儿 --on-red-arg → 2
        base9 = ["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--sleep-scale", "0"]
        p = run(base9 + ["--on-red", "echo x", "--on-red-preset", "unclog",
                         "--on-red-arg", "src=" + psrc, "--emit", emit9b])
        assert p.returncode == 2, "同给 --on-red 应 rc=2 实测 %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "bogus", "--emit", emit9b])
        assert p.returncode == 2, "preset 不识别应 rc=2 实测 %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "unclog", "--emit", emit9b])
        assert p.returncode == 2, "预设参数缺应 rc=2 实测 %d" % p.returncode
        p = run(base9 + ["--on-red-preset", "unclog", "--on-red-arg",
                         "src=" + psrc])
        assert p.returncode == 2, "缺 --emit 应 rc=2 实测 %d" % p.returncode
        # plain 同款守卫（v41 矩阵判据转正）：--on-red 缺 --emit → 2；
        # preset 路径回归＝本节首两展开断言＋触发捕获＋上行 preset 缺 --emit
        # rc=2，皆不受新守卫扰动（守卫只查 plain 路径 --emit 在位）。
        p = run(base9 + ["--on-red", "echo x"])
        assert p.returncode == 2, "plain --on-red 缺 --emit 应 rc=2 实测 %d" \
            % p.returncode
        assert "--emit" in p.stdout, p.stdout[-300:]
        p = run(base9 + ["--on-red-arg", "src=" + psrc, "--emit", emit9b])
        assert p.returncode == 2, "孤儿 --on-red-arg 应 rc=2 实测 %d" \
            % p.returncode

        # 〔九b〕预设表数据化扩展（v41 任务书①②③④）：新三预设占位替换＋
        # 必传缺 rc2＋链式双预设展开＋链式触发（按序·一败续行 rc=9→rc=0
        # 双笔入账·哨退出码仍 0）。triage/cw-doctor 只做展开级矢量（触发起
        # 真网络/真体检——零真网络铁律不破）·触发捕获用 [unclog,wash-shape]
        # 链（两腿皆离线速断）。
        ev9b = os.path.join(tmp, "events9b.jsonl")
        cmd = expand_on_red_preset("wash-shape", ["src=/abs/ws_src"], ev9b)
        assert cmd == ("python3 -B %s --dir /abs/ws_src --json "
                       "%s/wash_shape_{run}.json" % (WASH_SHAPE_TOOL, tmp)), \
            cmd
        assert "{run}" in cmd, cmd                    # 动态族留给事件直替
        cmd = expand_on_red_preset("triage", [], ev9b)
        assert cmd == ("python3 -B %s --repo {repo} --run {run} --json "
                       "%s/triage_{run}.json" % (TRIAGE_TOOL, tmp)), cmd
        assert "{repo}" in cmd and "{run}" in cmd, cmd  # 事件直替族原样保留
        cmd = expand_on_red_preset("triage", ["repo=o/r", "run=178"], ev9b)
        assert cmd == ("python3 -B %s --repo o/r --run 178 --json "
                       "%s/triage_178.json" % (TRIAGE_TOOL, tmp)), cmd  # 静态覆盖
        cmd = expand_on_red_preset("cw-doctor", [], ev9b)
        assert cmd == ("python3 -B %s --json %s/doctor_{run}.json"
                       % (CW_DOCTOR_TOOL, tmp)), cmd
        # 必传缺/形坏/重键/未知键/空参面 → 2（同款守卫·动态族放行不豁免静态族）
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
                assert False, "新预设负面展开应 rc=2"
            except SentryError as e:
                assert e.code == 2, "新预设负面展开应 2 实测 %d" % e.code
        p = run(base9 + ["--on-red-preset", "wash-shape", "--emit", emit9b])
        assert p.returncode == 2, "CLI 预设参数缺应 rc=2 实测 %d" % p.returncode
        # 链式展开：--on-red-arg 命名空间全链共享（未知键判全链并集面·
        # unclog+triage 仅传 src 即成链——triage 的 repo/run 走事件直替）·
        # 按给定序零重排
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
                assert False, "链式负面展开应 rc=2"
            except SentryError as e:
                assert e.code == 2, "链式负面展开应 2 实测 %d" % e.code
        # 链式触发捕获：canned CI 红事件 → 链 [unclog, wash-shape] 按序执行·
        # 一败续行——leg1 unclog（空 src 零候选）rc=9 响亮入账不裁停·leg2
        # wash-shape 干跑 plan（空树 clean）rc=0·两笔同 schema 入账·哨退出码
        # 仍 0（旁路动作非器面铁律）
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
        assert act1["rc"] == 9, "leg1 unclog（空 src）应 rc=9 入账: %r" % act1
        assert act2["cmd"] == ("python3 -B %s --dir %s --json "
                               "%s/wash_shape_178.json"
                               % (WASH_SHAPE_TOOL, esrc, tmp)), act2["cmd"]
        assert act2["rc"] == 0, "leg2 wash-shape 干跑 plan 应 rc=0" \
            "（一败续行实证·leg1 rc=9 不裁停）: %r" % act2
        assert act1["seq"] == act2["seq"] == 1, (act1["seq"], act2["seq"])
        assert os.path.isfile(os.path.join(tmp, "wash_shape_178.json")), \
            "leg2 预设钦定路径应实落 report"
        mw = re.search(r"workdir -> (\S+)", act1.get("output") or "")
        if mw:
            shutil.rmtree(mw.group(1), ignore_errors=True)  # 清 leg1 mkdtemp

        # 〔十〕韧性层：退避序列＋Retry-After 尊重＋api_get_json 重试 runner＋
        # run_py 超时杀（零网络零编译·_open/_sleep 注入·判例 403×3→[2,4,8]）
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        assert _http_backoff.parse_retry_after("30") == 30.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, "HTTP-date 不猜"

        class _Resp(object):
            """canned 响应体（urlopen 假件·零网络·上下文管理器形）。"""
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
                    raise r          # canned 错件须抛（urlopen 同语义）
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
            (st10, slept)                      # Retry-After 头尊重（替指数）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=3,
                         _open=_seq_open([_api_err(503)] * 4),
                         _sleep=slept.append)
            assert False, "503×4 重试耗尽应 9"
        except SentryError as e:
            assert e.code == 9 and "HTTP 503" in str(e), e
        assert slept == [2.0, 4.0, 8.0], slept
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=3,
                         _open=_seq_open([_api_err(401)]), _sleep=slept.append)
            assert False, "401 语义面应不重试直 9"
        except SentryError as e:
            assert e.code == 9, e.code
        assert slept == [], "401 零重试零睡"
        # run_py 超时杀（canned sleep 子进程·fail-loud 9 报调用名）
        sleepy = os.path.join(tmp, "sleepy_sentinel.py")
        with io.open(sleepy, "w", encoding="utf-8") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        try:
            run_py(sleepy, ["--hang"], timeout=2)
            assert False, "超时应 fail-loud 9"
        except SentryError as e:
            assert e.code == 9 and "sleepy_sentinel.py" in str(e) \
                and "2s" in str(e), e
        fastpy = os.path.join(tmp, "fast_sentinel.py")
        with io.open(fastpy, "w", encoding="utf-8") as fh:
            fh.write("print('ok')\n")
        rc10, out10 = run_py(fastpy, [], timeout=5)
        assert rc10 == 0 and "ok" in out10, (rc10, out10)

        # 〔十一〕--state-file 崩溃恢复语义：损坏红拒 9 禁静默重建（原件原样
        # 不动）／--rebuild-state 显式重建（弃 seen 从零起·红事件复现）
        statec = os.path.join(tmp, "state_corrupt.json")
        corrupt = '{"repos": BROKEN-JSON{{{'
        with io.open(statec, "w", encoding="utf-8") as fh:
            fh.write(corrupt)
        emitc = os.path.join(tmp, "events_c.jsonl")
        p = run(["--once", "--watch-repo", REPO, "--injector", inj_path,
                 "--state-file", statec, "--emit", emitc, "--sleep-scale", "0"])
        assert p.returncode == 9, "损坏 state 应红拒 rc=9 实测 %d" % p.returncode
        assert "形坏" in p.stdout, p.stdout[-300:]
        assert "STATE-REBUILD" not in p.stdout, p.stdout[-300:]
        assert io.open(statec, encoding="utf-8").read() == corrupt, \
            "损坏 state 被静默改写＝违例（禁静默重建）"
        # --rebuild-state 显式重建：同损坏件 → rc0·红事件复现（seen 弃）
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
            "重建后 seen 弃应复现 ci-red: %s" % evs
        st = json.load(io.open(statec, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA \
            and st["repos"][REPO]["seen_runs"], "重建后 state 应为合法新账"
        # --rebuild-state 缺 --state-file → 2（无 state 即无物可重建）
        p = run(["--once", "--watch-ledgers", ldir, "--rebuild-state"])
        assert p.returncode == 2, "rebuild 缺 state-file 应 rc=2 实测 %d" \
            % p.returncode

        # 〔十二〕--emit-max-bytes JSONL 轮转（超限先轮转再追加·.1/.2 保留
        # 2 代·seq 跨代续号不重）
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
        assert "emit 轮转" in p.stdout, "末轮应响亮轮转注记: %s" % p.stdout[-300:]
        assert os.path.isfile(rot_emit + ".1") \
            and os.path.isfile(rot_emit + ".2"), "轮转应产 .1/.2 两代"
        seqs = []
        for gpath in (rot_emit + ".2", rot_emit + ".1", rot_emit):
            for ln in io.open(gpath, encoding="utf-8"):
                if ln.strip():
                    ev = json.loads(ln)          # 代内逐行可解析
                    assert ev["schema"] == EVENT_SCHEMA, ev
                    seqs.append(ev["seq"])
        assert sorted(seqs) == [1, 2, 3], "seq 跨代应续号不重: %s" % seqs
        rep = json.load(io.open(repx, encoding="utf-8"))
        assert rep.get("emit_max_bytes") == 300 \
            and rep.get("emit_rotations") == 1, \
            (rep.get("emit_max_bytes"), rep.get("emit_rotations"))
        # 负面：缺 --emit / N<1 → 2
        p = run(["--once", "--watch-ledgers", ldir, "--emit-max-bytes", "300"])
        assert p.returncode == 2, "轮转缺 --emit 应 rc=2 实测 %d" % p.returncode
        p = run(["--once", "--watch-ledgers", ldir, "--emit", rot_emit,
                 "--emit-max-bytes", "0"])
        assert p.returncode == 2, "轮转 N=0 应 rc=2 实测 %d" % p.returncode

        # 〔十三〕韧性层 v51：传输层瞬断有界重试＋loop 逐源 skip（真崩栈
        # IncompleteRead(371261, 72721) 同形·更新账 v50 round10 在案）
        assert net_backoff_delays(3) == [5.0, 15.0, 45.0], \
            net_backoff_delays(3)
        assert net_backoff_delays(0) == [], net_backoff_delays(0)
        for bad in (-1, "3", 1.5, None, True):
            try:
                net_backoff_delays(bad)
                assert False, "net_retries=%r 应 ValueError" % (bad,)
            except ValueError:
                pass

        class _BadReadResp(_Resp):
            """canned 半读断流体（读函数注入面：resp.read() 抛 IncompleteRead·
            真崩栈同形 371261 read/72721 expected——partial 须 bytes 形·int 形
            其 __str__ 内 len() 自炸·真崩文案「371261 bytes read, 72721 more
            expected」）。"""
            def read(self):
                raise http.client.IncompleteRead(b"\x00" * 371261, 72721)

        # 首二发抛第三发成（缺省 3 发帽·退避 5s/15s·retry_max=0 隔离状态码面）
        slept = []
        st13, body13 = api_get_json("https://x", "tok", 5, None, retry_max=0,
                                    _open=_seq_open([_BadReadResp(),
                                                     _BadReadResp(),
                                                     _Resp(b'{"ok":13}')]),
                                    _sleep=slept.append)
        assert st13 == 200 and body13 == {"ok": 13} \
            and slept == [5.0, 15.0], (st13, body13, slept)
        # 瞬态类全员可重试（RemoteDisconnected/BadStatusLine/socket.timeout
        # 三发依次抛·第四发成→退避 5/15/45 全程）
        slept = []
        st13, _ = api_get_json("https://x", "tok", 5, None, retry_max=0,
                               _open=_seq_open([
                                   http.client.RemoteDisconnected(),
                                   http.client.BadStatusLine("bogus"),
                                   socket.timeout("timed out"),
                                   _Resp(b'{"ok":1}')]),
                               _sleep=slept.append)
        assert st13 == 200 and slept == [5.0, 15.0, 45.0], (st13, slept)
        # 重试耗尽上抛（fail-loud 保持）·退避序断言全程 [5,15,45]·真崩栈文案
        # 同形断言（「371261 bytes read, 72721 more expected」）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         _open=_seq_open([_BadReadResp()] * 4),
                         _sleep=slept.append)
            assert False, "传输层重试耗尽应 9"
        except SentryError as e:
            assert e.code == 9 and "传输层瞬断重试耗尽" in str(e) \
                and "IncompleteRead" in str(e) \
                and "371261 bytes read, 72721 more expected" in str(e), e
        assert slept == [5.0, 15.0, 45.0], slept          # 退避序断言
        # 文案层防御：str() 自炸异常（IncompleteRead partial 非 bytes 形其
        # __str__ len() 再炸）不遮蔽原错——耗尽上抛仍干净 SentryError 9
        # （v51 首跑实测判例器化）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         _open=_seq_open(
                             [http.client.IncompleteRead(1, 2)] * 4),
                         _sleep=slept.append)
            assert False, "str 自炸异常耗尽仍应 9"
        except SentryError as e:
            assert e.code == 9 and "IncompleteRead" in str(e), e
        assert slept == [5.0, 15.0, 45.0], slept
        # --net-retries 帽可调：帽 1 → 一发重试即耗尽（一睡 5s）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None, retry_max=0,
                         net_retries=1,
                         _open=_seq_open([_BadReadResp(), _BadReadResp()]),
                         _sleep=slept.append)
            assert False, "net_retries=1 耗尽应 9"
        except SentryError as e:
            assert e.code == 9, e.code
        assert slept == [5.0], slept
        slept = []
        st13, _ = api_get_json("https://x", "tok", 5, None, retry_max=0,
                               net_retries=1,
                               _open=_seq_open([_BadReadResp(), _Resp()]),
                               _sleep=slept.append)
        assert st13 == 200 and slept == [5.0], (st13, slept)
        # 非瞬态不吞不重试：未知异常原样穿透（fail-loud 禁吞边界）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None,
                         _open=_seq_open([ValueError("boom-nontransient")]),
                         _sleep=slept.append)
            assert False, "非瞬态应原样穿透"
        except ValueError as e:
            assert "boom-nontransient" in str(e), e
        assert slept == [], "非瞬态零重试零睡"
        # URLError 连接建立面仍快败 9（不混入传输层重试面）
        slept = []
        try:
            api_get_json("https://x", "tok", 5, None,
                         _open=_seq_open([urllib.error.URLError("dns fail")]),
                         _sleep=slept.append)
            assert False, "URLError 应快败 9"
        except SentryError as e:
            assert e.code == 9 and "不可达" in str(e), e
        assert slept == [], "URLError 零重试零睡"
        # loop 层逐源 skip：canned 401 双轮各 skip → rc 0 不崩（宁跳轮不崩驻）·
        # source-error 注记×2·seen 零记账（下轮重报·宁重复不丢件）
        state13 = os.path.join(tmp, "state13.json")
        emit13 = os.path.join(tmp, "events13.jsonl")
        rep13 = os.path.join(tmp, "rep13.json")
        p = run(["--loop", "--max-rounds", "2", "--interval", "5",
                 "--watch-repo", REPO, "--injector", p401,
                 "--state-file", state13, "--emit", emit13, "--json", rep13,
                 "--sleep-scale", "0"])
        assert p.returncode == 0, \
            "loop 逐源兜底应 rc=0 不崩（宁跳轮不崩驻）: %s" % p.stdout[-600:]
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
            "skip 轮 seen 不得记账（下轮重报·宁重复不丢件）: %s" % st13["repos"]
        # once 同形对照（既有〔八〕矢量复证）：canned 401 仍 fail-loud rc 9
        emit13b = os.path.join(tmp, "events13b.jsonl")
        p = run(["--once", "--watch-repo", REPO, "--injector", p401,
                 "--state-file", os.path.join(tmp, "state13b.json"),
                 "--emit", emit13b, "--sleep-scale", "0"])
        assert p.returncode == 9, "once 同形应保持 fail-loud rc=9 实测 %d" \
            % p.returncode
        evs13b = [json.loads(l) for l in io.open(emit13b, encoding="utf-8")
                  if l.strip()]
        assert len(evs13b) == 1 and evs13b[0]["kind"] == "sentinel-error" \
            and evs13b[0]["code"] == 9, evs13b

        # 〔十四〕部署形冒烟（监督壳 examples/sentinel_supervisor.sh·静态断言
        # 非真跑）：bash -n 仅解析不执行＋关键行 grep 断言——验部署工件在库与
        # 结构逐点在位（重启帽／退避／state 续接注记／收兵钩位留空／guard 位／
        # rc 分诊／三件套落位名／路径参数化零硬编码）。零执行零网络。
        sup_sh = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.pardir, "examples", "sentinel_supervisor.sh"))
        assert os.path.isfile(sup_sh), "监督壳部署形脚本缺库: %s" % sup_sh
        p = subprocess.run(["bash", "-n", sup_sh],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out14 = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        assert p.returncode == 0, "bash -n 语法检应过 rc=0: %s" % out14[-300:]
        sup_text = io.open(sup_sh, encoding="utf-8").read()
        assert sup_text.startswith("#!/bin/bash"), "部署形应 bash 正典头"
        for tok in (
                "SUPERVISOR_MAX_RESTARTS", "重启预算耗尽",           # 重启帽
                "SUPERVISOR_BACKOFF_BASE", "SUPERVISOR_BACKOFF_MAX",
                "退避",                                              # 退避
                "--state-file", "state 续接",                        # state 续接注记
                "state.json", "events.jsonl", "report.json",         # 三件套落位名
                "supervisor_withdraw_hook",                          # 收兵钩位（留空形另断言）
                "SENTINEL_GUARD", "cpu_guard",                       # guard 钩位
                "tools/cw_sentinel.py", "--loop",                    # 哨子命令
                "rc=2 用法错",                                       # rc 分诊（用法错不进重启环）
        ):
            assert tok in sup_text, "监督壳关键形缺: %r" % tok
        assert re.search(r"supervisor_withdraw_hook\(\) \{\n  return 0",
                         sup_text), "收兵钩位应留空（缺省体 return 0·部署方按需填形）"
        assert "/Users/" not in sup_text, \
            "部署形禁硬编码绝对路径（路径参数化铁律）: /Users/ 命中"
        # 本机 bash 3.2 判例（部署形功能冒烟实捕·20261112）：裸 $VAR 后紧贴
        # 全角字会被吞进变量名 → set -u 下 unbound variable 崩（真崩形
        # 「rc=$RC）」）——裸 $VAR 一律 ${} 括起的结构律断言（紧跟非 ASCII
        # 字节即违例）
        m_cjk = re.search(r"\$([A-Za-z_][A-Za-z0-9_]*)[^\x00-\x7F]", sup_text)
        assert m_cjk is None, \
            "裸 $%s 紧贴全角字＝bash 3.2 变量名吞字崩形·须 \${} 括起" \
            % (m_cjk.group(1) if m_cjk else "")

        print("CW-SENTINEL-SELFTEST PASS: ①once ci-red+二跑 seen 幂等零事件/"
              "②ledger 新件 blocking+幂等/③buildlog 增量 grep+半行不误报/"
              "④on-red 占位替换执行实证+缺省零动作/⑤loop 三轮 JSONL 序贯/"
              "⑥emit 逐行合法 sort_keys+seq 序贯/确定性字节恒同/CLI 四码+"
              "401→9+canned 未覆盖→9+目录缺→9/"
              "⑨on-red-preset 展开+触发捕获+同给互斥 rc=2+参数缺误 rc=2+"
              "plain 缺 --emit rc=2（双路同守卫·preset 回归）/"
              "⑬预设表扩展（wash-shape/triage/cw-doctor 占位替换·triage "
              "repo/run 事件直替族·必传缺/未知键/空参面 rc2·链式双预设展开"
              "全链并集面·链式触发按序一败续行 rc=9→rc=0 双笔入账）/"
              "⑩韧性层退避（403×3→[2,4,8]·Retry-After 尊重·503 耗尽 9·401 "
              "不重试·canned sleep 子进程超时杀 9 报调用名）/"
              "⑪state 崩溃恢复（损坏红拒 9 禁静默重建原件不动·--rebuild-state "
              "显式重建红事件复现·缺 --state-file rc=2）/"
              "⑫emit 轮转（--emit-max-bytes 超限先轮转再追加·.1/.2 保留 2 代·"
              "seq 跨代续号·缺 --emit/N<1 rc=2）/"
              "⑭传输层瞬断 v51（canned IncompleteRead 读函数注入·首二发抛第三"
              "发成退避 [5,15]·RemoteDisconnected/BadStatusLine/socket.timeout"
              " 全员可重试·耗尽 9 退避序 [5,15,45] 断言·--net-retries 帽可调·"
              "非瞬态/URLError 快败零吞零睡·loop 逐源 skip source-error 注记 "
              "rc0 宁跳轮不崩驻 seen 零记账·once 同形仍 9）/"
              "⑮部署形冒烟（监督壳 examples/sentinel_supervisor.sh·bash -n "
              "语法检＋关键行 grep 断言：重启帽/退避/state 续接注记/收兵钩位"
              "留空 return 0/guard 位/rc 分诊/三件套落位名/零硬编码绝对路径"
              "——静态断言非真跑零执行零网络） 全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
