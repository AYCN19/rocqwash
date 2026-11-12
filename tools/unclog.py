#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""unclog.py — blockage-clearing closed-loop engine for rocqwash (tools/).

Closes the manual five-step unblocking procedure used by the real-time support
workflow into a self-driving loop (orchestrates existing engines rather than
reimplementing them — probe_engine/chain_graph/cure_applier/scan_v4_token/
frozen8 are always invoked as subprocesses; this tool supplies only the glue
and the state machine, following the pushci.py orchestration precedent):

  manual five steps (real-time support workflow)         this tool's loop (--rounds cap, default 5)
  ① probe collects the failure set        →  ① collect: any of three candidate sources →
                                            probe_engine produces the current failure set
  ② chain_graph picks chain roots from the graph
                                          →  ② chain root: chain_graph merges the top list →
                                            take the first entry with self.washable=true
                                            (all false = no actionable root → honest wall;
                                            nothing is forced)
  ③ cure_applier applies the cure         →  ③ apply: dry-run the root file to produce a plan →
                                            apply only when a plan exists and --apply is given
                                            (the canonical cure pack only; no free-form edits);
                                            no plan → the root is recorded as cure-miss in the
                                            wall table
  ④ re-scan / re-probe verification       →  ④ verify: scan_v4_token re-scans the treated file
                                            (cured-token residual should be zero) + probe_engine
                                            re-probes it (rc should be 0)
  ⑤ human judgment                        →  ⑤ verdict: empty failure set = verdict unclogged,
                                            exit 0; non-empty and rounds remain → next round;
                                            rounds exhausted → verdict rounds-exhausted, exit 1
                                            (with each round's record + a final probe)

Three candidate sources (mutually exclusive):
  --candidates TSV      feed the candidate list directly to probe_engine
                        (located by header column names, same convention as
                        probe_engine)
  --chain-ledgers JSON  merge existing probe ledgers (argv order = merge
                        order, later batches override earlier ones, same as
                        chain_graph); re-probe ledgers from later rounds are
                        merged round by round (resprobe: later overrides
                        earlier — the post-repair state is recorded). This
                        mode has no per-round full re-probe (runs with zero
                        world dependency).
  (neither given)       --src full-tree enumeration: walk --src collecting
                        *.v files with per-file md5 → generate the TSV (the
                        RED column is not declared; probe_engine honestly
                        reports RC0 for rc0 — the chain-root washability
                        criterion is self.rc, not verdict; same convention as
                        chain_graph.py)

Failure-set criteria: a probe record with rc != 0 (rc1 failure / rc124
TIMEOUT / NO-SRC) counts as failed; the union of chain_graph stats.rc1 +
stats.other is the failure set (chain_graph.py:116-121). The verdict is
judged only on the failure set (a failing result is data, not a tool
failure; a probe_engine rc1 candidate is produced data, not a tool failure).

Honest wall (nothing is forced): when every TOP entry has
self.washable=false (a mid-chain ring: self-unwashable; or the root is not
in the candidate set: unprobed), or every washable root hits a dead end
(cure-miss: the canonical pack offers no plan / root-file-missing /
frozen-in-service: the root is on the frozen roster and is refused /
exclusive-group-conflict: variants require human selection /
idempotence-fail: the apply-time idempotence assertion refuses to write) →
verdict=wall exit 1; the wall table lists the non-actionable reason per
root; zero applies, nothing forced.

Safety rules:
  --apply defaults to off = everything is a dry run with zero disk writes
    (single switch; --yes is not needed); applies go only through the
    cure_applier canonical pack (--pack default wash/cure_pack.json);
    the apply target is always the chain-root file (<src>/<root>.v — outside
    pick there is no cure call path, so restricting applies to chain roots is
    a structural guarantee); files on the frozen roster (certify/frozen8.py
    --ledger, eight files, fetched via subprocess; a missing roster fails
    closed with 9) are pre-checked and refused: if the root name collides
    with a rostered rel / basename / extension-stripped name, or the root
    file's realpath collides with a rostered file (resolved on both the
    --src and --repo-path sides), it is refused — recorded in the wall table
    as reason=frozen-in-service, zero applies.

--audit read-only audit (real-tree blockage baseline):
  A single-pass probe dry-run collection → chain_graph → a "blockage baseline
  report" (schema rocqwash-unclog/1: final.verdict=audit; one round with
  probe_summary/chain_top present; cure/rescan/resprobe always None;
  cures_planned/cures_applied always 0; the wall table records every graph
  case — unprobed/self-unwashable/frozen-in-service per root (data recorded,
  not a stop condition — audit neither picks roots nor applies); a failure
  set with no chain root adds a no-chain-root wall entry instead of staying
  silent; exit 0 — a failing result is baseline data, not a tool failure).
  Mutual exclusions: --audit with --apply → rc=2 (audit is read-only); with
  --loop → rc=2 (single-pass baseline; watch-mode cycling is not audit
  semantics); with --state-file → rc=2 (seen-state differencing is not audit
  semantics); --rounds does not apply to a single pass.
  Zero-write hard guarantee = the --src full-file md5 manifest is self-checked
  identical before and after the run (probe_engine itself copies the tree out
  for compilation — wash/probe_engine.py — and cleans up artifacts; any
  manifest mismatch fails loudly with 9; a contaminated baseline is never
  reported); workdir/--json/events writes are the audit's own duty and are
  outside the guarded domain.
  Per-phase timings (enumerate/manifest/probe+chain/total) enter
  report["timing"] = measured wall clock — the only non-deterministic part of
  the report (byte-identical reruns still hold for everything except the
  timing section); the timing section also records the jobs dimension = the
  --probe-parallel K value passed through to probe_engine --jobs (default 1)
  — runs over the same candidate set with different K are comparable
  (parallel-profile collection; see examples/baselines/perf-README.md; in
  injector canned mode the parameter is bypassed but still recorded).
  Offline-testable like the closed loop: --injector canned probe doubles as
  the audit probe (selftest vector ⑩); a real-tree audit live run belongs to
  the main session (this tool proves the fixture level only).

--probe-parallel K (pass-through to probe_engine --jobs; default 1 = per-file
serial, zero drift):
  ① collect probe / ④ re-probe resprobe / --audit all share the parameter —
  candidate files are sharded across a ThreadPool (ledger record order always
  follows candidate order; completion order never changes output order — the
  determinism rule; md5_match/verdict logic unchanged; per-file build logs
  still land independently in logdir; real compilation still goes through
  --guard cpu_guard per file; the guard FRONT profile applies its own
  clamping). K>1 = multiple concurrent rocqworker processes on one machine =
  higher thermal load — with --guard given, K≤2 is advised (advisory note,
  not enforced; the user decides; thermal-control details in the parallelism
  section of the wash/probe_engine.py docstring). Injector canned mode does
  zero real compilation; the parameter is bypassed (canned data lands
  directly in workdir).

--once/--loop dual mode (shared three-tool interface rule):
  --once (default) runs a single closed loop; --loop is watch mode: the loop
  repeats (--interval seconds between cycles; --sleep-scale multiplier;
  --selftest uses 0 = zero real sleep); round events + cycle events are
  written as a JSONL stream to --events (default <workdir>/events.jsonl); a
  terminal verdict (unclogged/wall) stops and exits immediately;
  rounds-exhausted is not terminal → wait --interval and start the next
  cycle (--loop-max cap, 0 = unlimited). Mutual exclusion, spelled out:
  --rounds with --loop → rc=2 (--rounds caps the rounds of a single closed
  loop; watch-mode cycling is not its semantics; the per-cycle round cap is
  always the default 5 — same rule as --audit with --loop; no silent choice
  between them).
--state-file watch-mode seen state (rocqwash-sentinel-state/1, same shape as
  cw_sentinel --state-file — same schema, same keys repos/ledgers/buildlogs;
  mutually read/write compatible):
  inter-round failure-set differencing, only-new events — each round's
  failure set is diffed against state.red_seen; newly appearing failed files
  emit {"event":"red-new", new_red:[...]} (already-seen failures are not
  reported again; seen grows monotonically); events are emitted before the
  state is saved (prefer duplicates over losing events); default None =
  differencing off (zero behavior change); a corrupted state (parse failure /
  malformed keys) → fail-loud 9, hard refusal, no silent rebuild (recovery =
  delete the file manually; the tool never swallows it).

Offline-testable (hard requirement; the subprocess-call layer is injectable;
zero real network and zero real compilation in --selftest):
  --injector DIR  DIR/scenario.json = {"probe":[probe_ledger...],
                  "resprobe":[probe_ledger...]} — the two probe_engine call
                  classes (probe/resprobe) are consumed strictly in order
                  from the canned ledgers (written verbatim into workdir and
                  then fed to the **real** chain_graph; exhaustion / missing
                  entry / malformed shape fails loudly with 2; zero real
                  compilation); chain_graph/cure_applier/scan_v4_token/
                  frozen8 are pure stdlib with zero compilation and zero
                  network and run for real under injection (real
                  orchestration, not a stub).
  --sleep-scale F multiplies every sleep by F (--selftest uses 0 = zero real
                  sleep).

Output (deterministic; sort_keys; --json reruns are byte-identical on the
same input; the report carries zero wall clock and zero absolute paths —
paths are reported as basenames only, full paths go to explicit stdout; in
audit mode the timing section is the exception = measured wall clock differs
per run, all other sections stay identical):
  --json report, schema=rocqwash-unclog/1:
    {schema, mode{source,apply,injector,loop[,audit]}, args, cycles?,
     rounds[{round, probe_summary{source,n_records,n_red,red_files,ledgers},
             chain_top[{lib,n,dependents,self{probed,rc,verdict,washable}}],
             root, root_file, cure{stage,rc,total_matches,patterns,md5_before,
             md5_after,on_disk_md5_match,reason}?, cures_planned, cures_applied,
             rescan{rc,ids,station_count,residual_zero}?,
             resprobe{rc,rc_ok,n_records,md5_match}?}],
     wall{root:{root,reason,detail}}, timing? (audit: per-phase timings + the
     jobs dimension),
     final{verdict,rounds_run,red_files,
     cures_planned_total,cures_applied_total,wall_count}, verdict}
  verdict ∈ unclogged|wall|rounds-exhausted|audit (audit = read-only
  baseline, exit 0).
  Per-round progress log line (explicit stdout): [round k/N] root=X cures=Y.

Usage (all paths parameterized; zero hardcoded absolute paths; component
paths are derived from the repository this file lives in, following the
pushci precedent):
  python3 tools/unclog.py --src DIR --world DIR \\
      [--candidates TSV | --chain-ledgers LEDGER.json ...] \\
      [--repo-path DIR] [--rounds 5] [--apply] [--top 25] [--scan-ids S]
      [--probe-resume] [--probe-parallel K] [--rocq-cmd TPL] [--guard PATH
      --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N
      --timeout S]
      [--pack cure_pack.json] [--workdir DIR] [--json out.json] [--events out.jsonl]
      [--once | --loop [--interval 60] [--loop-max 0]] [--sleep-scale 1.0]
      [--injector DIR] [--state-file STATE.json]
  python3 tools/unclog.py --src DIR [--world DIR] --audit [--injector DIR] \\
      [--repo-path DIR] [--top 25] [--probe-parallel K] [--workdir DIR] \\
      [--json out.json]
  python3 tools/unclog.py --selftest

Exit codes: 0 = unclogged / audit; 1 = wall / rounds-exhausted (a failing result is
  data, not a tool failure; explicit stdout); 2 = usage error / injection-scenario
  shape error (--rounds with --loop / --audit with --apply, --loop, or
  --state-file / --probe-parallel<1 / --state-file directory missing);
  9 = fail-loud (path missing / tool error: an engine subprocess exits nonzero
  for non-data reasons / frozen roster unavailable / full-tree enumeration
  finds zero candidates / audit zero-write self-check broken / state file
  corrupted and refused — no silent rebuild).
  --selftest: 0 = all pass / 2 = assertion failure.

World discipline: this tool never writes --world (the world's .vo foundation
is seeded by the caller per the certification rules of wash/world_hook.py;
whether a post-repair re-probe clears the failure set depends on world
generation; this tool reports honestly and never forces an outcome).
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "unclog"
SCHEMA = "rocqwash-unclog/1"
CHAIN_SCHEMA = "rocqwash-chain-graph/1"
STATE_SCHEMA = "rocqwash-sentinel-state/1"   # --state-file 同形承 cw_sentinel
VERDICT_EXIT = {"unclogged": 0, "wall": 1, "rounds-exhausted": 1, "audit": 0}
TERMINAL_VERDICTS = ("unclogged", "wall")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
PROBE_TOOL = os.path.join(REPO_ROOT, "wash", "probe_engine.py")
CHAIN_TOOL = os.path.join(REPO_ROOT, "tools", "chain_graph.py")
CURE_TOOL = os.path.join(REPO_ROOT, "wash", "cure_applier.py")
SCAN_TOOL = os.path.join(REPO_ROOT, "scan", "scan_v4_token.py")
FROZEN8_TOOL = os.path.join(REPO_ROOT, "certify", "frozen8.py")
DEFAULT_PACK = os.path.join(REPO_ROOT, "wash", "cure_pack.json")


class UnclogError(Exception):
    """带退出码的 fail-loud 异常（2=用法/场景形错·9=路径缺失/器红）。"""

    def __init__(self, msg, code=9):
        super(UnclogError, self).__init__(msg)
        self.code = code


# ---- 小件（确定性 helpers）---------------------------------------------------

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def basename_of(p):
    return os.path.basename(p.rstrip(os.sep)) if p else p


def sleep_scaled(sec, scale):
    """time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·pushci 同款）。"""
    time.sleep(max(0.0, float(sec) * float(scale)))


def dump_json(obj, path):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


def load_json(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, UnicodeDecodeError, OSError) as e:
        raise UnclogError("%s JSON 形坏: %s (%s)" % (what, path, e), 2)


def emit(events_fh, obj):
    """JSONL 事件流一行（sort_keys·零墙钟·确定性内容）。"""
    if events_fh is None:
        return
    events_fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
    events_fh.flush()


def run_py(tool_path, cli):
    """python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·pushci 同款）。缺件→9。"""
    if not os.path.isfile(tool_path):
        raise UnclogError("工具链件缺失: %s" % tool_path, 9)
    p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def write_cands_tsv(path, pairs):
    """候选清单 TSV（件名/md5 双列·probe_engine 必需列形制）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("件名\tmd5\n")
        for name, md5 in pairs:
            fh.write("%s\t%s\n" % (name, md5))


def enumerate_tree(src):
    """--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·双排序）。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, src).replace(os.sep, "/")
                out.append((rel[:-2], md5_of(fp)))
    return out


def tree_manifest(src):
    """--src 全文件 {rel(POSIX 形): md5} 清单（audit 零写盘自证用·全文件非仅
    .v——增删改一字节即现形）。"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            out[os.path.relpath(fp, src).replace(os.sep, "/")] = md5_of(fp)
    return out


# ---- state（--loop 哨态 seen 持久层·与 cw_sentinel --state-file 同形）--------

def new_state():
    """零态账（同形 cw_sentinel.new_state：三域 dict＋本器差分域 red_seen）。"""
    return {"schema": STATE_SCHEMA, "repos": {}, "ledgers": {},
            "buildlogs": {}, "red_seen": []}


def load_state(path):
    """state 装载（同形 cw_sentinel.load_state）：缺省 None/文件缺失＝零态
    起步；损坏（JSON 解析失败/repos/ledgers/buildlogs 键缺 dict/red_seen 非
    list）→ fail-loud 9 红拒·禁静默重建（seen 是差分账·静默重建＝红事件
    重报面失守·损坏原件原样不动——恢复＝人工删件下轮零态起步）。"""
    if path is None:
        return new_state()
    if not os.path.isfile(path):
        return new_state()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise UnclogError("state 文件形坏（解析失败·禁静默重建）: %s (%s)"
                          % (path, e), 9)
    for k in ("repos", "ledgers", "buildlogs"):
        if not isinstance(st.get(k), dict):
            raise UnclogError("state 文件形坏（缺 %s dict·禁静默重建）: %s"
                              % (k, path), 9)
    if not isinstance(st.get("red_seen", []), list):
        raise UnclogError("state 文件形坏（red_seen 须 list·禁静默重建）: %s"
                          % path, 9)
    return st


def save_state(path, st):
    """state 落盘（sort_keys 规范式·差分事件先 emit 后存本函数——宁重复不
    丢件承哨纪律）。目录缺 → 9。"""
    if path is None:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise UnclogError("state 文件目录缺失: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- 注入点：probe/resprobe 两类探针调用 canned（离线零真编译）----------------

class Injector(object):
    """--injector DIR/scenario.json＝{"probe":[ledger...],"resprobe":[ledger...]}
    按序严格消费（probe_engine canned 台账原样落 workdir 后仍喂真 chain_graph）；
    耗尽/缺列/形坏 fail-loud 2。"""

    def __init__(self, dirpath):
        sj = os.path.join(dirpath, "scenario.json")
        if not os.path.isfile(sj):
            raise UnclogError("injector 场景缺失: %s" % sj, 9)
        scen = load_json(sj, "injector 场景")
        if not isinstance(scen, dict):
            raise UnclogError("injector 场景形坏（须 dict）: %s" % sj, 2)
        probe = scen.get("probe")
        if not isinstance(probe, list) or not probe:
            raise UnclogError("injector 场景缺 canned probe 序列（离线零真编译"
                              "纪律·probe 必给非空 list）: %s" % sj, 2)
        self.canned = {"probe": list(probe)}
        rp = scen.get("resprobe")
        self.canned["resprobe"] = list(rp) if isinstance(rp, list) else None
        self.counts = {"probe": 0, "resprobe": 0}

    def take(self, kind):
        lst = self.canned.get(kind)
        nth = self.counts.get(kind, 0) + 1
        if lst is None:
            raise UnclogError("injector 场景缺 canned %s 序列（第 %d 次 %s 调用）"
                              % (kind, nth, kind), 2)
        if not lst:
            raise UnclogError("injector canned %s 序列耗尽（第 %d 次调用）"
                              % (kind, nth), 2)
        item = lst.pop(0)
        self.counts[kind] = nth
        if not isinstance(item, dict) or not isinstance(item.get("records"), dict):
            raise UnclogError("injector canned %s 第 %d 项形坏（须含 records dict"
                              " 的 probe_ledger）" % (kind, nth), 2)
        return item


# ---- 器件编排层（probe_engine/chain_graph/cure_applier/scan_v4_token）---------

class Engines(object):
    """四器子进程编排（probe/resprobe 可注入·chain/cure/scan 恒真跑——纯 stdlib
    零编译零网络·真编排非傀儡）。"""

    def __init__(self, args, injector, workdir):
        self.a = args
        self.inj = injector
        self.workdir = workdir

    # -- probe_engine（①归集／④复探·可注入）--------------------------------
    def probe(self, kind, cands_tsv, out_json):
        if self.inj is not None:
            canned = self.inj.take(kind)
            dump_json(canned, out_json)
            return 0, "[injector] canned %s -> %s" % (kind, out_json), canned
        a = self.a
        if not a.world:
            raise UnclogError("--world 必给（%s 真探针；离线请 --injector）" % kind, 9)
        cli = ["--candidates", cands_tsv, "--src", a.src, "--world", a.world,
               "--out", out_json,
               "--logdir", os.path.join(self.workdir, "probe-logs"),
               "--rocq-cmd", a.rocq_cmd, "--timeout", str(a.timeout),
               "--jobs", str(a.probe_parallel)]   # --probe-parallel 透传（缺省 1）
        if a.guard:
            cli += ["--guard", a.guard, "--guard-reg", a.guard_reg,
                    "--guard-front", str(a.guard_front),
                    "--guard-mid", str(a.guard_mid),
                    "--guard-maxwait", str(a.guard_maxwait)]
        if not a.probe_resume:
            cli += ["--fresh"]   # 每轮真探=当前红账（resume 会对未变件 skip 留陈账）
        rc, out = run_py(PROBE_TOOL, cli)
        if rc != 0:
            raise UnclogError("probe_engine 器红 rc=%d（%s）: %s"
                              % (rc, kind, out[-300:]), 9)
        return rc, out, load_json(out_json, "probe 台账")

    def resprobe(self, names_md5, out_json):
        """④复探受治件：mini 候选清单 → probe_engine（fresh·world 同归集）。"""
        tsv = out_json[:-len(".json")] + ".cands.tsv"
        write_cands_tsv(tsv, names_md5)
        return self.probe("resprobe", tsv, out_json)

    # -- chain_graph（②链根·恒真跑）------------------------------------------
    def chain(self, ledger_paths, out_json):
        cli = list(ledger_paths) + ["--json", out_json, "--top", str(self.a.top)]
        rc, out = run_py(CHAIN_TOOL, cli)
        if rc != 0:
            raise UnclogError("chain_graph 器红 rc=%d: %s" % (rc, out[-300:]), 9)
        graph = load_json(out_json, "链根图")
        if graph.get("schema") != CHAIN_SCHEMA:
            raise UnclogError("链根图 schema 不识: %r（期待 %s）"
                              % (graph.get("schema"), CHAIN_SCHEMA), 9)
        return graph, out

    # -- cure_applier（③落刀·恒真跑·干跑缺省 --apply 落刀）--------------------
    def cure(self, root_file, apply_flag, out_json):
        cli = ["--file", root_file, "--pack", self.a.pack, "--json", out_json]
        if apply_flag:
            cli += ["--apply"]
        rc, out = run_py(CURE_TOOL, cli)
        rep = load_json(out_json, "cure 报告") if os.path.exists(out_json) else None
        return rc, rep, out

    # -- scan_v4_token（④复扫·恒真跑）-----------------------------------------
    def scan(self, root_file, out_json):
        cli = ["--file", root_file, "--ids", self.a.scan_ids, "--json", out_json]
        rc, out = run_py(SCAN_TOOL, cli)
        if rc != 0:
            raise UnclogError("scan_v4_token 器红 rc=%d: %s" % (rc, out[-300:]), 9)
        return load_json(out_json, "token 普查")


# ---- frozen 在册（certify/frozen8.py·预检红拒·缺册 fail-closed）---------------

def frozen8_rels():
    """frozen8 --ledger 子进程实取在册八件 rel（fail-closed：rc!=0/零行→9）。"""
    rc, out = run_py(FROZEN8_TOOL, ["--ledger"])
    if rc != 0:
        raise UnclogError("frozen8 在册不可得 rc=%d（fail-closed 禁落刀）: %s"
                          % (rc, out[-300:]), 9)
    rels = []
    for ln in out.splitlines():
        f = ln.split()
        if len(f) == 2 and len(f[0]) == 32 and all(c in "0123456789abcdef" for c in f[0]):
            rels.append(f[1])
    if not rels:
        raise UnclogError("frozen8 --ledger 输出无可解析在册行（fail-closed 禁落刀）", 9)
    return rels


def build_frozen_hit(src, repo_path):
    """在册名单→红拒判定闭包：根名撞 rel/基名/去扩展名 或根件 realpath 撞在册
    文件（--src/--repo-path 双侧解析）即 True。→ (hit, 在册件数)。"""
    names, files = set(), set()
    rels = frozen8_rels()
    for rel in rels:
        names.add(rel)
        base = os.path.basename(rel)
        names.add(base)
        names.add(base.rsplit(".", 1)[0] if "." in base else base)
        for tree in (src, repo_path):
            files.add(os.path.realpath(os.path.join(tree, rel.replace("/", os.sep))))

    def hit(root_name, root_file):
        if root_name in names:
            return True
        try:
            return os.path.realpath(root_file) in files
        except OSError:
            return False

    return hit, len(rels)


# ---- 闭环状态机（一轮＝①归集→②链根→③落刀→④复核；判定在①口）----------------

def chain_top_of(graph, top_n):
    """链根 TOP 榜摘要（top_order 显式保秩·chain_graph 同秩）。"""
    out = []
    for lib in list(graph.get("top_order", []))[:top_n]:
        e = graph["libs"][lib]
        out.append({"lib": lib, "n": e["n"], "dependents": list(e["dependents"]),
                    "self": dict(e["self"])})
    return out


def args_summary(a):
    """args → report["args"] 摘要（路径只出基名·零绝对路径·闭环/audit 共用）。"""
    return {"rounds": a.rounds, "top": a.top, "scan_ids": a.scan_ids,
            "apply": bool(a.apply), "loop": bool(a.loop),
            "loop_max": a.loop_max, "interval": a.interval,
            "sleep_scale": a.sleep_scale, "probe_resume": bool(a.probe_resume),
            "probe_parallel": a.probe_parallel,
            "src": basename_of(a.src), "world": basename_of(a.world) if a.world else None,
            "repo_path": basename_of(a.repo_path),
            "candidates": basename_of(a.candidates) if a.candidates else None,
            "chain_ledgers": [basename_of(p) for p in (a.chain_ledgers or [])],
            "pack": basename_of(a.pack),
            "injector": basename_of(a.injector) if a.injector else None,
            "state_file": basename_of(a.state_file) if a.state_file else None,
            "guard": basename_of(a.guard) if a.guard else None,
            "rocq_cmd": a.rocq_cmd, "timeout": a.timeout}


class UnclogRun(object):
    """单周闭环。红账空→unclogged；无正典可洗根/全根碰壁→wall；轮尽红未清→
    rounds-exhausted（终判探在轮尽后补一发①）。"""

    def __init__(self, args, engines, frozen_hit, events_fh, cycle, source,
                 cands_tsv, workdir, state=None, state_path=None):
        self.a = args
        self.engines = engines
        self.frozen_hit = frozen_hit
        self.events_fh = events_fh
        self.cycle = cycle
        self.source = source
        self.cands_tsv = cands_tsv
        self.workdir = workdir
        self.state = state          # 同形哨态 seen 账（--state-file 在场时）
        self.state_path = state_path
        self.resprobe_ledgers = []
        self.last_red = []
        self.report = {
            "schema": SCHEMA,
            "mode": {"source": source, "apply": bool(args.apply),
                     "injector": args.injector is not None, "loop": bool(args.loop)},
            "args": self._args_summary(),
            "rounds": [],
            "wall": {},
            "final": {"verdict": None, "rounds_run": 0, "red_files": [],
                      "cures_planned_total": 0, "cures_applied_total": 0,
                      "wall_count": 0},
            "verdict": None,
        }

    def _args_summary(self):
        return args_summary(self.a)

    # -- 墙账（按根去重·确定性）------------------------------------------------
    def wall_add(self, root, reason, detail):
        if root not in self.report["wall"]:
            self.report["wall"][root] = {"root": root, "reason": reason,
                                         "detail": detail}
            print("WALL: %s — %s（%s）" % (root, reason, detail))

    def wall_from_graph(self, graph):
        """TOP 榜不可洗根入墙（幂等·已有因者不重记）。"""
        for lib in graph.get("top_order", []):
            if lib in self.report["wall"]:
                continue
            s = graph["libs"][lib]["self"]
            if not s.get("probed"):
                self.wall_add(lib, "unprobed", "根件未入候选集（UNPROBED·候补探）")
            elif not s.get("washable"):
                self.wall_add(lib, "self-unwashable",
                              "根件自身被阻 rc=%s verdict=%s（链中环·先治根的因）"
                              % (s.get("rc"), s.get("verdict")))
            # washable 而已在墙（cure-miss/frozen）者因已在册·不重记

    # -- ①归集 -----------------------------------------------------------------
    def collect(self, k):
        """→ (graph, red_files, probe_summary)·红账=stats.rc1∪stats.other。"""
        wd = self.workdir
        if self.source == "chain-ledgers":
            ledgers = list(self.a.chain_ledgers) + list(self.resprobe_ledgers)
            graph, _out = self.engines.chain(
                ledgers, os.path.join(wd, "round-%d.chain.json" % k))
            tag = "merge"
            led_bns = [basename_of(p) for p in ledgers]
        else:
            pj = os.path.join(wd, "round-%d.probe.json" % k)
            _rc, _out, _ledger = self.engines.probe("probe", self.cands_tsv, pj)
            graph, _out = self.engines.chain([pj],
                                             os.path.join(wd, "round-%d.chain.json" % k))
            tag = "probe"
            led_bns = [os.path.basename(pj)]
        red = sorted(set(graph["stats"]["rc1"]) | set(graph["stats"]["other"]))
        summary = {"source": tag, "n_records": graph["stats"]["merged_total"],
                   "n_red": len(red), "red_files": red, "ledgers": led_bns}
        return graph, red, summary

    # -- 红账差分（--state-file 同形哨态 seen·only-new）------------------------
    def red_diff(self, red):
        """轮间红账差分事件 only-new：新现红件（不在 state.red_seen）→ emit
        {"event":"red-new", new_red:[...], red_total, seen_before}·seen 并账
        落盘（事件先 emit 后存 state——宁重复不丢件承哨纪律）。已 seen 红
        不再报（seen 单调只增·only-new 语义）；缺省无 --state-file＝差分关
        （零事件零写盘·行为不变）。"""
        if self.state_path is None:
            return
        seen = self.state.setdefault("red_seen", [])
        known = set(seen)
        new_red = [f for f in red if f not in known]
        if new_red:
            emit(self.events_fh, {"event": "red-new", "cycle": self.cycle,
                                  "new_red": list(new_red),
                                  "red_total": len(red),
                                  "seen_before": len(known)})
            seen.extend(new_red)
            seen.sort()
            save_state(self.state_path, self.state)

    # -- ②链根挑根（frozen 预检红拒内嵌）---------------------------------------
    def pick_root(self, graph):
        """取 self.washable=true 之首（跳过已在墙者·frozen 红拒入墙续挑）。
        → (root|None, root_file|None)。"""
        for lib in graph.get("top_order", []):
            s = graph["libs"][lib]["self"]
            if not s.get("washable"):
                continue
            if lib in self.report["wall"]:
                continue
            root_file = os.path.join(self.a.src, lib.replace("/", os.sep) + ".v")
            if self.frozen_hit(lib, root_file):
                self.wall_add(lib, "frozen-in-service",
                              "根名/根件撞 frozen8 在册（预检红拒·零落刀）")
                continue
            return lib, root_file
        return None, None

    # -- 单轮 -------------------------------------------------------------------
    def run_round(self, k):
        a = self.a
        rd = {"round": k}
        graph, red, summary = self.collect(k)
        rd["probe_summary"] = summary
        rd["chain_top"] = chain_top_of(graph, a.top)
        self.last_red = red
        print("[round %d/%d] 归集: %s 红账 %d: %s"
              % (k, a.rounds, summary["source"], len(red), ",".join(red) or "-"))
        self.red_diff(red)   # 轮间红账差分事件 only-new（--state-file 在场时）

        # ⑤判定口：红账空＝疏通（终判探含轮尽后补探）
        if not red:
            rd["root"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (red empty)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "red_empty": True})
            self.report["rounds"].append(rd)
            return "unclogged"
        # ⑤判定口：轮尽（终判探仍红）
        if k > a.rounds:
            rd["root"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (rounds exhausted)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "red_empty": False})
            self.report["rounds"].append(rd)
            return "rounds-exhausted"

        self.wall_from_graph(graph)
        root, root_file = self.pick_root(graph)
        if root is None:
            if not graph.get("top_order"):
                # 零链根（红账无一缺库分组·代差型/器因红）——墙账不得哑：
                # 补 no-chain-root 墙目逐件列红（verdict 仍 wall·禁硬凑）
                self.wall_add("-", "no-chain-root",
                              "红账 %d 件无一缺库链根（代差型/器因红·禁硬凑）: %s"
                              % (len(red), ",".join(red)))
            rd["root"] = None
            rd["cure"] = None
            rd["cures_planned"] = 0
            rd["cures_applied"] = 0
            rd["rescan"] = None
            rd["resprobe"] = None
            rd["log"] = "[round %d/%d] root=- cures=0 (wall)" % (k, a.rounds)
            print(rd["log"])
            emit(self.events_fh, {"event": "round", "cycle": self.cycle,
                                  "round": k, "root": None, "cures": 0,
                                  "wall": True})
            self.report["rounds"].append(rd)
            return "wall"
        rd["root"] = root
        rd["root_file"] = root + ".v"
        print("chain_top: " + ", ".join(
            "%s(n=%d,washable=%s)" % (t["lib"], t["n"], t["self"]["washable"])
            for t in rd["chain_top"][:3]))

        # ③落刀（只正典包·只对链根件）
        cure_info = None
        cures_planned = 0
        cures_applied = 0
        proceed = False
        if not os.path.exists(root_file):
            self.wall_add(root, "root-file-missing",
                          "链根件缺失: %s（红因所缺库无对应源件）" % rd["root_file"])
        else:
            cj = os.path.join(self.workdir, "round-%d.cure.json" % k)
            rc, rep, out = self.engines.cure(root_file, False, cj)
            if rc == 4:
                self.wall_add(root, "exclusive-group-conflict",
                              "变体须 --only 人择（禁自动代选）·groups=%s"
                              % ((rep or {}).get("exclusive_group_conflict")))
            elif rc != 0:
                raise UnclogError("cure_applier 器红 rc=%d（干跑 %s）: %s"
                                  % (rc, root_file, out[-300:]), 9)
            else:
                total = sum(int(v.get("matches", 0))
                            for v in (rep or {}).get("report", {}).values())
                cure_info = {"stage": "dry-run", "rc": rc, "total_matches": total,
                             "patterns": dict(
                                 (pid, int(v.get("matches", 0)))
                                 for pid, v in (rep or {}).get("report", {}).items()
                                 if v.get("matches")),
                             "md5_before": (rep or {}).get("md5_before"),
                             "md5_after": (rep or {}).get("md5_after")}
                if total == 0:
                    self.wall_add(root, "cure-miss",
                                  "正典包干跑零方案（total_matches=0）")
                else:
                    cures_planned = total
                    proceed = True
                    if a.apply:
                        aj = os.path.join(self.workdir, "round-%d.apply.json" % k)
                        rc2, rep2, out2 = self.engines.cure(root_file, True, aj)
                        if rc2 == 4:
                            self.wall_add(root, "exclusive-group-conflict",
                                          "落刀遇变体冲突（零写盘）")
                            proceed = False
                        elif rc2 == 1:
                            self.wall_add(root, "idempotence-fail",
                                          "落刀幂等断言败（cure_applier 拒写·文件未动）")
                            proceed = False
                        elif rc2 != 0:
                            raise UnclogError("cure_applier 器红 rc=%d（落刀 %s）: %s"
                                              % (rc2, root_file, out2[-300:]), 9)
                        else:
                            cures_applied = total
                            cure_info["stage"] = "applied"
                            cure_info["rc"] = rc2
                            cure_info["md5_after"] = (rep2 or {}).get("md5_after")
                            cure_info["on_disk_md5_match"] = (
                                md5_of(root_file) == cure_info["md5_after"])
                            print("APPLIED %s cures=%d md5_after=%s on_disk_match=%s"
                                  % (root, cures_applied, cure_info["md5_after"],
                                     cure_info["on_disk_md5_match"]))

        # ④复核（rescan 残差应零＋resprobe rc 应 0——如实出账不粉饰）
        rescan = None
        resprobe = None
        if proceed:
            sj = os.path.join(self.workdir, "round-%d.scan.json" % k)
            census = self.engines.scan(root_file, sj)
            st = census.get("station_count")
            rescan = {"rc": 0, "ids": a.scan_ids, "station_count": st,
                      "residual_zero": (st == 0)}
            rj = os.path.join(self.workdir, "round-%d.resprobe.json" % k)
            _rc, _out, led = self.engines.resprobe([(root, md5_of(root_file))], rj)
            recs = led.get("records", {})
            rec = recs.get(root, {})
            resprobe = {"rc": rec.get("rc"), "rc_ok": (rec.get("rc") == 0),
                        "n_records": len(recs), "md5_match": rec.get("md5_match")}
            self.resprobe_ledgers.append(rj)
            print("RECHECK %s rescan_station=%d resprobe_rc=%s"
                  % (root, st, resprobe["rc"]))

        rd["cure"] = cure_info
        rd["cures_planned"] = cures_planned
        rd["cures_applied"] = cures_applied
        rd["rescan"] = rescan
        rd["resprobe"] = resprobe
        cures_log = cures_applied if a.apply else cures_planned
        suffix = "" if (resprobe is None or resprobe["rc_ok"]) \
            else " resprobe-rc=%s（应 0 未达·如实入账）" % resprobe["rc"]
        rd["log"] = "[round %d/%d] root=%s cures=%d%s" % (k, a.rounds, root,
                                                          cures_log, suffix)
        print(rd["log"])
        emit(self.events_fh, {"event": "round", "cycle": self.cycle, "round": k,
                              "root": root, "cures": cures_log,
                              "cures_applied": cures_applied})
        self.report["rounds"].append(rd)
        return None   # 下一轮

    def run(self):
        k = 0
        verdict = None
        while True:
            k += 1
            verdict = self.run_round(k)
            if verdict:
                break
        fin = self.report["final"]
        fin["verdict"] = verdict
        fin["rounds_run"] = len(self.report["rounds"])
        fin["red_files"] = list(self.last_red)
        fin["cures_planned_total"] = sum(r.get("cures_planned", 0)
                                         for r in self.report["rounds"])
        fin["cures_applied_total"] = sum(r.get("cures_applied", 0)
                                         for r in self.report["rounds"])
        fin["wall_count"] = len(self.report["wall"])
        self.report["verdict"] = verdict
        emit(self.events_fh, {"event": "cycle_end", "cycle": self.cycle,
                              "verdict": verdict,
                              "rounds_run": fin["rounds_run"]})
        return verdict, self.report


# ---- --audit 只读审计（真树堵账基线·单遍·零落刀零写树）------------------------

def run_audit(args, engines, frozen_hit, events_fh, source, cands_tsv,
              workdir, enum_sec, holder):
    """--audit 单遍只读基线（v38 真实树基线数据用）：全树 probe 干跑归集→
    chain_graph→堵账基线报告。schema 同 rocqwash-unclog/1：final.verdict=
    audit·rounds 单轮（probe_summary/chain_top 全在·cure/rescan/resprobe
    恒 None·cures_planned/cures_applied 恒 0）·墙账 graph 判例全记——
    unprobed/self-unwashable/frozen-in-service 逐根（数据入账非停机条件·
    audit 不挑根不落刀）·零链根红账补 no-chain-root 目禁哑墙·exit 0（红是
    基线数据非器红）。零写盘硬保证＝--src 全文件 md5 清单跑前跑后自证恒同
    （probe_engine 本就 copyfile 出树编译·wash/probe_engine.py:163·产物清场
    py:194——清单违同即 fail-loud 9·染污基线不出账）。耗时各段入
    report["timing"]＝实测墙钟·报告唯一非确定段；jobs 维度（--probe-parallel
    K 实参·probe_engine --jobs 透传值·缺省 1）同段入账——同候选面异 K
    前后跑可比（并行剖面采集口）。"""
    a = args
    print("=== AUDIT 只读基线（单遍 probe 归集→chain_graph·零落刀零写树）===")
    t0 = time.time()
    before = tree_manifest(a.src)
    manifest_sec = time.time() - t0
    rd = {"round": 1}
    t1 = time.time()
    if source == "chain-ledgers":
        graph, _out = engines.chain(list(a.chain_ledgers),
                                    os.path.join(workdir, "audit.chain.json"))
        summary = {"source": "merge",
                   "ledgers": [basename_of(p) for p in a.chain_ledgers]}
    else:
        pj = os.path.join(workdir, "audit.probe.json")
        _rc, _out, _led = engines.probe("probe", cands_tsv, pj)
        graph, _out = engines.chain([pj],
                                    os.path.join(workdir, "audit.chain.json"))
        summary = {"source": "probe", "ledgers": [os.path.basename(pj)]}
    probe_chain_sec = time.time() - t1
    red = sorted(set(graph["stats"]["rc1"]) | set(graph["stats"]["other"]))
    summary.update({"n_records": graph["stats"]["merged_total"],
                    "n_red": len(red), "red_files": red})
    rd["probe_summary"] = summary
    rd["chain_top"] = chain_top_of(graph, a.top)
    print("[audit] 归集: %s 红账 %d: %s"
          % (summary["source"], len(red), ",".join(red) or "-"))
    print("chain_top: " + (", ".join(
        "%s(n=%d,washable=%s)" % (t["lib"], t["n"], t["self"]["washable"])
        for t in rd["chain_top"][:3]) or "-"))

    # 墙账（graph 判例全记·含 frozen 预检——数据入账非停机条件）
    wall = {}

    def wall_add(root, reason, detail):
        if root not in wall:
            wall[root] = {"root": root, "reason": reason, "detail": detail}
            print("WALL: %s — %s（%s）" % (root, reason, detail))

    for lib in graph.get("top_order", []):
        s = graph["libs"][lib]["self"]
        if not s.get("probed"):
            wall_add(lib, "unprobed", "根件未入候选集（UNPROBED·候补探）")
        elif not s.get("washable"):
            wall_add(lib, "self-unwashable",
                     "根件自身被阻 rc=%s verdict=%s（链中环·先治根的因）"
                     % (s.get("rc"), s.get("verdict")))
        elif frozen_hit(lib, os.path.join(a.src,
                                          lib.replace("/", os.sep) + ".v")):
            wall_add(lib, "frozen-in-service",
                     "根名/根件撞 frozen8 在册（预检红拒·人审域）")
    if red and not graph.get("top_order"):
        wall_add("-", "no-chain-root",
                 "红账 %d 件无一缺库链根（代差型/器因红·禁硬凑）: %s"
                 % (len(red), ",".join(red)))

    # 零写盘硬保证（--src 全文件 md5 清单前后自证·违即 fail-loud 9）
    after = tree_manifest(a.src)
    if after != before:
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(k for k in set(before) & set(after)
                         if before[k] != after[k])
        raise UnclogError(
            "audit 零写盘硬保证破：--src 树被动（改 %d/增 %d/删 %d: %s）"
            % (len(changed), len(added), len(removed),
               ",".join((changed + added + removed)[:8])), 9)

    rd["root"] = None
    rd["root_file"] = None
    rd["cure"] = None
    rd["cures_planned"] = 0
    rd["cures_applied"] = 0
    rd["rescan"] = None
    rd["resprobe"] = None
    rd["log"] = "[audit] root=- cures=0 (audit baseline·red=%d)" % len(red)
    print(rd["log"])
    emit(events_fh, {"event": "round", "cycle": 1, "round": 1, "root": None,
                     "cures": 0, "audit": True, "red_empty": not red})
    emit(events_fh, {"event": "cycle_end", "cycle": 1, "verdict": "audit",
                     "rounds_run": 1})
    timing = {"enumerate_s": (round(enum_sec, 3)
                              if enum_sec is not None else None),
              "manifest_s": round(manifest_sec, 3),
              "probe_chain_s": round(probe_chain_sec, 3),
              "total_s": round(time.time() - t0, 3),
              "jobs": a.probe_parallel}
    print("[audit] timing: jobs=%d enumerate=%s manifest=%gs probe+chain=%gs"
          " total=%gs"
          % (a.probe_parallel, timing["enumerate_s"], timing["manifest_s"],
             timing["probe_chain_s"], timing["total_s"]))
    report = {
        "schema": SCHEMA,
        "mode": {"source": source, "apply": False, "audit": True,
                 "injector": a.injector is not None, "loop": False},
        "args": args_summary(a),
        "rounds": [rd],
        "wall": wall,
        "timing": timing,
        "final": {"verdict": "audit", "rounds_run": 1, "red_files": list(red),
                  "cures_planned_total": 0, "cures_applied_total": 0,
                  "wall_count": len(wall)},
        "verdict": "audit",
    }
    holder["report"] = report
    print("AUDIT: 红账 %d·墙 %d——基线报告零落刀零写树（exit 0）"
          % (len(red), len(wall)))
    return "audit", report


# ---- 总控（--once/--loop 哨态）------------------------------------------------

def run(args, holder):
    # 值校验（2）
    if args.loop and args.rounds is not None:
        raise UnclogError("--rounds 与 --loop 互斥（--rounds 是单遍闭环轮帽·"
                          "哨态周循环非其语义·周内轮帽恒缺省 5——同给 rc=2 "
                          "禁静默择一）", 2)
    if args.rounds is None:
        args.rounds = 5           # 缺省轮帽（--rounds 未给·once/loop 同值）
    if args.rounds < 1:
        raise UnclogError("--rounds 须≥1 实测 %d" % args.rounds, 2)
    if args.probe_parallel < 1:
        raise UnclogError("--probe-parallel 须≥1 实测 %d（probe_engine --jobs "
                          "透传·缺省 1）" % args.probe_parallel, 2)
    if args.top < 1:
        raise UnclogError("--top 须≥1 实测 %d" % args.top, 2)
    if args.interval < 0:
        raise UnclogError("--interval 须≥0 实测 %s" % args.interval, 2)
    if args.sleep_scale < 0:
        raise UnclogError("--sleep-scale 须≥0 实测 %s" % args.sleep_scale, 2)
    if args.loop_max < 0:
        raise UnclogError("--loop-max 须≥0 实测 %d" % args.loop_max, 2)
    if args.audit and args.apply:
        raise UnclogError("--audit 与 --apply 互斥（审计只读零落刀·同给 rc=2）", 2)
    if args.audit and args.loop:
        raise UnclogError("--audit 与 --loop 互斥（审计单遍基线·哨态循环非"
                          "审计语义）", 2)
    if args.audit and args.state_file:
        raise UnclogError("--audit 与 --state-file 互斥（审计单遍基线·seen "
                          "哨态差分非审计语义）", 2)
    if args.candidates and args.chain_ledgers:
        raise UnclogError("--candidates 与 --chain-ledgers 互斥（候选面三源任选）", 2)

    # 路径校验（9·器件先验）
    for label, p in (("probe_engine", PROBE_TOOL), ("chain_graph", CHAIN_TOOL),
                     ("cure_applier", CURE_TOOL), ("scan_v4_token", SCAN_TOOL),
                     ("frozen8", FROZEN8_TOOL)):
        if not os.path.isfile(p):
            raise UnclogError("器件缺失: %s (%s)" % (label, p), 9)
    if not args.src:
        raise UnclogError("FAIL-LOUD: --src 必给", 2)
    if not os.path.isdir(args.src):
        raise UnclogError("--src 路径缺失: %s" % args.src, 9)
    if args.candidates and not os.path.exists(args.candidates):
        raise UnclogError("--candidates 路径缺失: %s" % args.candidates, 9)
    for p in (args.chain_ledgers or []):
        if not os.path.exists(p):
            raise UnclogError("--chain-ledgers 路径缺失: %s" % p, 9)
    if not os.path.exists(args.pack):
        raise UnclogError("--pack 路径缺失: %s" % args.pack, 9)
    if args.injector and not os.path.isdir(args.injector):
        raise UnclogError("--injector 目录缺失: %s" % args.injector, 9)
    if args.state_file:
        d = os.path.dirname(os.path.abspath(args.state_file))
        if d and not os.path.isdir(d):
            raise UnclogError("--state-file 目录缺失: %s" % d, 9)

    # state 装载（--state-file 同形哨态 seen·损坏红拒 9 fail-loud）
    state = load_state(args.state_file)
    if args.state_file:
        print("state -> %s（seen %d 件·rocqwash-sentinel-state/1 同形）"
              % (args.state_file, len(state.get("red_seen", []))))

    # workdir
    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)
        workdir = args.workdir
    else:
        workdir = tempfile.mkdtemp(prefix="rocqwash_unclog_")
    print("workdir -> %s" % workdir)

    # 候选面三源
    enum_sec = None
    if args.candidates:
        source, cands_tsv = "tsv", args.candidates
        print("候选面: --candidates %s" % args.candidates)
    elif args.chain_ledgers:
        source, cands_tsv = "chain-ledgers", None
        print("候选面: --chain-ledgers %s（merge 模式·无逐轮全量重探）"
              % " ".join(args.chain_ledgers))
    else:
        _t0 = time.time()
        pairs = enumerate_tree(args.src)
        enum_sec = time.time() - _t0
        if not pairs:
            raise UnclogError("--src 全树枚举零 .v 候选: %s" % args.src, 9)
        cands_tsv = os.path.join(workdir, "tree-cands.tsv")
        write_cands_tsv(cands_tsv, pairs)
        source = "tree"
        print("候选面: --src 全树枚举 %d 件 -> %s" % (len(pairs), cands_tsv))

    # 注入器（probe/resprobe canned·零真编译）
    inj = Injector(args.injector) if args.injector else None
    if inj is not None:
        print("injector: %s（probe canned %d 发·resprobe canned %s）"
              % (args.injector, len(inj.canned["probe"]),
                 len(inj.canned["resprobe"]) if inj.canned["resprobe"] is not None
                 else "缺列"))
    if args.probe_parallel > 1 and not inj and source != "chain-ledgers":
        print("ADVISE(温控): --probe-parallel %d>1＝机内多 rocqworker 并发·"
              "热负载↑（--guard 同给建议 K≤2·注记不强制·用户自裁）"
              % args.probe_parallel)

    # frozen 在册（fail-closed 预检）
    frozen_hit, frozen_n = build_frozen_hit(args.src, args.repo_path)
    print("frozen 在册: %d 件（certify/frozen8.py --ledger 实取·预检红拒）"
          % frozen_n)

    # 事件流（JSONL）
    events_path = args.events_file or \
        (os.path.join(workdir, "events.jsonl") if args.loop else None)
    events_fh = io.open(events_path, "w", encoding="utf-8", newline="\n") \
        if events_path else None

    engines = Engines(args, inj, workdir)
    cycles = []
    verdict = None
    report = None
    try:
        if args.audit:
            # --audit 单遍只读基线（不进闭环·零落刀·--src md5 前后自证）
            verdict, report = run_audit(args, engines, frozen_hit, events_fh,
                                        source, cands_tsv, workdir, enum_sec,
                                        holder)
            cycles.append({"cycle": 1, "verdict": verdict})
        else:
            while True:
                cycle = len(cycles) + 1
                u = UnclogRun(args, engines, frozen_hit, events_fh, cycle,
                              source, cands_tsv, workdir, state=state,
                              state_path=args.state_file)
                verdict, report = u.run()
                holder["report"] = report
                cycles.append({"cycle": cycle, "verdict": verdict})
                if verdict in TERMINAL_VERDICTS:
                    break
                if not args.loop:
                    break
                if args.loop_max and cycle >= args.loop_max:
                    break
                print("[cycle %d] %s — 哨态歇 %g s 后再巡"
                      % (cycle, verdict, args.interval * args.sleep_scale))
                sleep_scaled(args.interval, args.sleep_scale)
    finally:
        if events_fh is not None:
            events_fh.close()

    if len(cycles) > 1 or args.loop:
        report["cycles"] = cycles
    code = VERDICT_EXIT[verdict]
    if args.json_out:
        dump_json(report, args.json_out)
        print("report -> %s" % args.json_out)
    print("VERDICT: %s (exit %d)" % (verdict, code))
    return code


# ---- CLI ----------------------------------------------------------------------

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
        description="疏通堵塞闭环引擎（v37 旗舰）：probe 归集→chain_graph 链根→"
                    "cure_applier 落刀→scan/probe 复核→判定·--rounds 帽自旋·"
                    "--apply 缺省全干跑零写盘·离线可注入·schema rocqwash-unclog/1")
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="源树根（根件 <根>.v 取自此·全树枚举源亦自此）")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="世界目录（probe_engine 探针 cwd·.vo 基座调用方按 "
                         "world_hook 纪律播种·本器零写；merge 模式可省·真探针必给）")
    ap.add_argument("--candidates", default=None, metavar="FILE",
                    help="候选清单 TSV（源①·probe_engine 同款表头）")
    ap.add_argument("--chain-ledgers", dest="chain_ledgers", nargs="+",
                    default=None, metavar="LEDGER.json",
                    help="既有 probe 台账（源②·argv 序=合并序·后批覆盖前批）")
    ap.add_argument("--repo-path", default=REPO_ROOT, metavar="DIR",
                    help="frozen 在册文件解析根（默认本件所在仓）")
    ap.add_argument("--rounds", type=int, default=None, metavar="N",
                    help="单遍闭环轮帽（缺省 5·轮尽红未清=rounds-exhausted·"
                         "与 --loop 互斥同给 rc=2）")
    ap.add_argument("--apply", action="store_true",
                    help="落刀开关（缺省关＝全干跑零写盘·单开关 --yes 不需要）")
    ap.add_argument("--audit", action="store_true",
                    help="只读审计：单遍 probe 归集→chain_graph→堵账基线报告"
                         "（final=audit·零落刀·--src 全文件 md5 前后自证恒同·"
                         "cures 恒空·与 --apply/--loop 互斥）")
    ap.add_argument("--top", type=int, default=25, metavar="N",
                    help="链根 TOP 榜截断（默认 25·chain_graph 同款）")
    ap.add_argument("--scan-ids", dest="scan_ids", default="S", metavar="IDS",
                    help="scan_v4_token 跟踪标识（默认 S）")
    ap.add_argument("--pack", default=DEFAULT_PACK, metavar="FILE",
                    help="正典 cure_pack（默认 wash/cure_pack.json v1.3）")
    ap.add_argument("--probe-resume", dest="probe_resume", action="store_true",
                    help="probe_engine 用 resume（缺省每轮 --fresh 真探当前红账）")
    ap.add_argument("--probe-parallel", dest="probe_parallel", type=int,
                    default=1, metavar="K",
                    help="probe_engine --jobs 并行度透传（缺省 1＝逐件串行零"
                         "漂移·--audit 同享·--guard 同给建议 K≤2 温控自裁）")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd",
                    default='rocq c -Q . "" {name}.v', metavar="TPL",
                    help="探针命令模板透传 probe_engine")
    ap.add_argument("--guard", default=None, metavar="PATH",
                    help="cpu_guard.sh 透传 probe_engine（真编译必给）")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_unclog", metavar="DIR")
    ap.add_argument("--guard-front", dest="guard_front", type=int, default=0)
    ap.add_argument("--guard-mid", dest="guard_mid", type=int, default=1)
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int, default=600)
    ap.add_argument("--timeout", type=int, default=1500,
                    help="probe_engine 单件超时秒透传")
    ap.add_argument("--workdir", default=None, metavar="DIR",
                    help="逐轮台账/报告工件目录（缺省 mkdtemp·stdout 响亮路径）")
    ap.add_argument("--json", dest="json_out", default=None, metavar="out.json",
                    help="report 出账（rocqwash-unclog/1·sort_keys）")
    ap.add_argument("--events", dest="events_file", default=None, metavar="FILE",
                    help="JSONL 事件流出账（--loop 缺省 <workdir>/events.jsonl）")
    ap.add_argument("--once", action="store_true",
                    help="单次闭环（缺省·与 --loop 双模接口纪律成对）")
    ap.add_argument("--loop", action="store_true",
                    help="实时哨态：闭环周而复始至终局 verdict／--loop-max 帽")
    ap.add_argument("--interval", type=float, default=60.0, metavar="S",
                    help="哨态周间歇秒（默认 60·乘 --sleep-scale）")
    ap.add_argument("--loop-max", dest="loop_max", type=int, default=0, metavar="N",
                    help="哨态周帽（默认 0=不限）")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float, default=1.0,
                    metavar="F", help="全部 sleep 乘数（selftest 用 0＝零真睡）")
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="离线注入：DIR/scenario.json（probe/resprobe canned "
                         "probe_ledger 按序严格消费·零真编译）")
    ap.add_argument("--state-file", dest="state_file", default=None,
                    metavar="FILE",
                    help="哨态 seen 状态文件（rocqwash-sentinel-state/1·与 "
                         "cw_sentinel --state-file 同形互读写·轮间红账差分"
                         "事件 only-new·损坏红拒 9 禁静默重建）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    holder = {}
    try:
        code = run(args, holder)
    except UnclogError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        rep = holder.get("report")
        if rep is not None and args.json_out:
            rep.setdefault("final", {})["verdict"] = "engine-error"
            dump_json(rep, args.json_out)
            print("partial report -> %s" % args.json_out, file=sys.stderr)
        sys.exit(e.code)
    sys.exit(code)


# ---- --selftest（内嵌冻结向量组·tmp fixture 树·零真编译零网络）-----------------

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")
NOMATCH_BODY = "Lemma ok : True.\n"


def selftest():
    """十四矢量（tmp fixture 树＋injector canned probe_ledger 序列·probe/resprobe
    注入零真编译·chain/cure/scan/frozen8 真跑）：①绿径两轮疏通（--apply 落刀→
    次轮红账空 exit 0）②诚实墙（self-unwashable·零落刀）＋②b 零链根红账
    （no-chain-root 墙目·禁哑墙）③cure-miss 入墙④轮尽（--apply 已落刀而世界
    仍红→rounds-exhausted 附各轮账）⑤--apply 缺省关实证（零字节动）⑥JSON 幂等
    （字节恒同）⑦frozen 在册红拒 ⑧--loop 哨态 JSONL ⑨CLI 四码 ⑩--audit 只读
    基线（零写盘自证/final=audit/cures 恒空/墙账 graph 判例/frozen 预检/互斥
    rc=2·真树 audit 活跑归主会话本席只证 fixture 级）⑪--state-file 同形哨态
    seen（轮间红账差分事件 only-new 三连跑：新现红报/复现红不报/新红再报·
    state red_seen 跨进程续账·损坏 state 红拒 9 禁静默重建）⑫--rounds 与
    --loop 互斥 rc=2＋--audit 与 --state-file 互斥 rc=2⑬--jobs 维度（audit
    timing 段 jobs=K 入账·缺省 1/--probe-parallel 2 各录其值·前后跑可比）。"""
    tmp = tempfile.mkdtemp(prefix="rocqwash_unclog_self_")

    def run(aargs):
        p = subprocess.run(
            [sys.executable, "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          PROG + ".py")] + list(aargs),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def fixture(tag, a_body=CURE13_BODY, b_body="Require Import A.\n"):
        d = os.path.join(tmp, tag)
        src, world, wd = (os.path.join(d, x) for x in ("src", "world", "wd"))
        for p in (src, world, wd):
            os.makedirs(p)
        with io.open(os.path.join(src, "A.v"), "w", encoding="utf-8") as fh:
            fh.write(a_body)
        with io.open(os.path.join(src, "B.v"), "w", encoding="utf-8") as fh:
            fh.write(b_body)
        write_cands_tsv(os.path.join(d, "cands.tsv"),
                        [("A", md5_of(os.path.join(src, "A.v"))),
                         ("B", md5_of(os.path.join(src, "B.v")))])
        return d, src, world, wd

    def led(records):
        return {"schema": "rocqwash-probe-ledger/1", "n_records": len(records),
                "records": records}

    def rec0(f):
        return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
                "red_class": None, "verdict": "RC0", "red_count": None,
                "md5_match": None}

    def rec1(f, lib):
        return {"file": f, "md5": None, "rc": 1,
                "red": "Error: Unable to locate library | %s (while searching "
                       "for a .vos file)." % lib,
                "missing": lib, "red_class": "MISSING_LIB",
                "verdict": "RED-MISSING_LIB", "red_count": None,
                "md5_match": None}

    def scenario(dirpath, probes, resprobes=None):
        os.makedirs(dirpath, exist_ok=True)
        scen = {"probe": probes}
        if resprobes is not None:
            scen["resprobe"] = resprobes
        dump_json(scen, os.path.join(dirpath, "scenario.json"))
        return dirpath

    L1 = led({"A": rec0("A"), "B": rec1("B", "A")})          # A 可洗链根·B 缺 A
    L2_GREEN = led({"A": rec0("A"), "B": rec0("B")})         # 世界换代后全绿
    L2_RED = led({"A": rec0("A"), "B": rec1("B", "A")})      # 世界未换代仍红
    R1 = led({"A": rec0("A")})

    try:
        # 矢量① 绿径两轮疏通：round1 治根 A（正典 cure13 落刀）→round2 复探绿 exit 0
        d, src, world, wd = fixture("v1_green")
        j1 = os.path.join(wd, "report.json")
        b_before = md5_of(os.path.join(src, "B.v"))
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
                 "--workdir", wd, "--json", j1])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "unclogged", rep["verdict"]
        assert rep["final"]["cures_applied_total"] == 1, rep["final"]
        assert "[round 1/5] root=A cures=1" in p.stdout, p.stdout[-400:]
        a_text = io.open(os.path.join(src, "A.v"), encoding="utf-8").read()
        assert "S01_BaseRing.NatLe (gnPrf f pf) k" in a_text, "落刀非正典形"
        assert md5_of(os.path.join(src, "B.v")) == b_before, "非链根件被动＝违例"
        assert rep["rounds"][0]["rescan"]["residual_zero"] is True, rep["rounds"][0]
        assert rep["rounds"][0]["resprobe"]["rc_ok"] is True, rep["rounds"][0]
        assert rep["rounds"][0]["cure"]["on_disk_md5_match"] is True, rep["rounds"][0]
        assert rep["final"]["rounds_run"] == 2, rep["final"]
        print("矢量① 绿径两轮疏通（--apply 落刀→次轮红账空 exit 0）: PASS")

        # 矢量② 诚实墙：self-unwashable（链中环）·零落刀·exit 1
        d, src, world, wd = fixture("v2_wall")
        base = os.path.join(d, "base.json")
        dump_json({"Y": {"file": "Y", "md5": None, "rc": 1,
                         "red": "Error: Illegal application", "missing": None,
                         "red_class": None, "verdict": "RED-OTHER",
                         "red_count": None, "md5_match": None},
                   "C1": rec1("C1", "Y")}, base)
        j2 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", base,
                 "--workdir", wd, "--json", j2])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j2, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["rounds"][0]["cure"] is None, "wall 轮不得有落刀（禁硬凑）"
        assert rep["rounds"][0]["chain_top"][0]["lib"] == "Y", rep["rounds"][0]
        assert rep["rounds"][0]["chain_top"][0]["self"]["washable"] is False
        assert rep["wall"]["Y"]["reason"] == "self-unwashable", rep["wall"]
        print("矢量② 诚实墙（self-unwashable 零落刀 exit 1）: PASS")

        # 矢量②b 零链根红账（代差型/器因红）→ 墙账补 no-chain-root 目（禁哑墙）
        d, src, world, wd = fixture("v2b_noroot")
        base2 = os.path.join(d, "base2.json")
        dump_json({"Z1": {"file": "Z1", "md5": None, "rc": 127, "red": "",
                          "missing": None, "red_class": None,
                          "verdict": "RED-UNKNOWN", "red_count": None,
                          "md5_match": None}}, base2)
        j2b = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", base2,
                 "--workdir", wd, "--json", j2b])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j2b, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["-"]["reason"] == "no-chain-root", rep["wall"]
        assert rep["rounds"][0]["chain_top"] == [], rep["rounds"][0]
        assert rep["rounds"][0]["probe_summary"]["red_files"] == ["Z1"]
        print("矢量②b 零链根红账（no-chain-root 墙目·禁哑墙）: PASS")

        # 矢量③ cure-miss 入墙：可洗根但正典包零方案
        d, src, world, wd = fixture("v3_curemiss", a_body=NOMATCH_BODY)
        j3 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED]),
                 "--workdir", wd, "--json", j3])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j3, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["A"]["reason"] == "cure-miss", rep["wall"]
        assert rep["rounds"][0]["cure"]["total_matches"] == 0, rep["rounds"][0]
        assert rep["final"]["cures_applied_total"] == 0, rep["final"]
        print("矢量③ cure-miss 入墙（正典包零方案·禁硬凑）: PASS")

        # 矢量④ 轮尽：--apply 已落刀而世界仍红 → rounds-exhausted 附各轮账
        d, src, world, wd = fixture("v4_exhaust")
        j4 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--rounds", "1", "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED], [R1]),
                 "--workdir", wd, "--json", j4])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j4, encoding="utf-8"))
        assert rep["verdict"] == "rounds-exhausted", rep["verdict"]
        assert rep["final"]["cures_applied_total"] == 1, rep["final"]
        assert rep["final"]["red_files"] == ["B"], rep["final"]
        assert "S01_BaseRing.NatLe (gnPrf f pf) k" in io.open(
            os.path.join(src, "A.v"), encoding="utf-8").read()
        assert rep["rounds"][0]["resprobe"]["rc"] == 0, rep["rounds"][0]
        print("矢量④ 轮尽（--apply 落刀而世界仍红·附各轮账 exit 1）: PASS")

        # 矢量⑤ --apply 缺省关实证：有方案而零落刀 → tmp 树零字节动
        d, src, world, wd = fixture("v5_defaultoff")
        before = {}
        for dirpath, dirnames, filenames in os.walk(src):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                before[os.path.relpath(fp, src)] = md5_of(fp)
        j5 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--rounds", "1", "--injector",
                 scenario(os.path.join(d, "inj"), [L1, L2_RED], [R1]),
                 "--workdir", wd, "--json", j5])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j5, encoding="utf-8"))
        assert rep["verdict"] == "rounds-exhausted", rep["verdict"]
        assert rep["mode"]["apply"] is False, rep["mode"]
        assert rep["final"]["cures_planned_total"] == 1, "干跑应有方案"
        assert rep["final"]["cures_applied_total"] == 0, rep["final"]
        after = {}
        for dirpath, dirnames, filenames in os.walk(src):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                after[os.path.relpath(fp, src)] = md5_of(fp)
        assert before == after, "--apply 缺省关下源树字节被动＝违例"
        assert not os.path.exists(os.path.join(wd, "round-1.apply.json")), \
            "无 --apply 不得有落刀账"
        print("矢量⑤ --apply 缺省关实证（有方案而零字节动）: PASS")

        # 矢量⑥ JSON 幂等：同输入重跑 --json 字节级恒同
        d, src, world, wd = fixture("v6a_idem")
        ja = os.path.join(wd, "report.json")
        run(["--src", src, "--world", world,
             "--candidates", os.path.join(d, "cands.tsv"),
             "--apply", "--injector",
             scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
             "--workdir", wd, "--json", ja])
        d, src, world, wd = fixture("v6b_idem")
        jb = os.path.join(wd, "report.json")
        run(["--src", src, "--world", world,
             "--candidates", os.path.join(d, "cands.tsv"),
             "--apply", "--injector",
             scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
             "--workdir", wd, "--json", jb])
        ba = io.open(ja, "rb").read()
        bb = io.open(jb, "rb").read()
        assert ba == bb, "同输入重跑 --json 字节漂移＝违例\n%s\n%s" % (ba[-300:], bb[-300:])
        print("矢量⑥ JSON 幂等（同输入重跑字节恒同）: PASS")

        # 矢量⑦ frozen 在册红拒：根名撞在册（wash_engine）→零落刀入墙
        d, src, world, wd = fixture("v7_frozen")
        with io.open(os.path.join(src, "wash_engine.v"), "w",
                     encoding="utf-8") as fh:
            fh.write(CURE13_BODY)
        write_cands_tsv(os.path.join(d, "cands.tsv"),
                        [("A", md5_of(os.path.join(src, "A.v"))),
                         ("B", md5_of(os.path.join(src, "B.v"))),
                         ("wash_engine", md5_of(os.path.join(src, "wash_engine.v")))])
        LF = led({"wash_engine": rec0("wash_engine"), "D": rec1("D", "wash_engine")})
        j7 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--injector",
                 scenario(os.path.join(d, "inj"), [LF]),
                 "--workdir", wd, "--json", j7])
        assert p.returncode == 1, p.stdout[-600:]
        rep = json.load(io.open(j7, encoding="utf-8"))
        assert rep["verdict"] == "wall", rep["verdict"]
        assert rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", rep["wall"]
        assert rep["rounds"][0]["cure"] is None, "frozen 红拒后不得落刀"
        assert md5_of(os.path.join(src, "wash_engine.v")) == \
            md5_of(os.path.join(src, "wash_engine.v")), "sanity"
        frozen_body = io.open(os.path.join(src, "wash_engine.v"),
                              encoding="utf-8").read()
        assert "NatLe" not in frozen_body, "frozen 件被落刀＝违例"
        print("矢量⑦ frozen 在册红拒（frozen8 实取·零落刀）: PASS")

        # 矢量⑧ --loop 哨态：JSONL 事件流＋终局即停（loop-max 1·sleep-scale 0）
        d, src, world, wd = fixture("v8_loop")
        ev = os.path.join(wd, "events.jsonl")
        j8 = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world,
                 "--candidates", os.path.join(d, "cands.tsv"),
                 "--apply", "--loop", "--loop-max", "1",
                 "--interval", "7", "--sleep-scale", "0", "--events", ev,
                 "--injector", scenario(os.path.join(d, "inj"), [L1, L2_GREEN], [R1]),
                 "--workdir", wd, "--json", j8])
        assert p.returncode == 0, p.stdout[-600:]
        lines = [ln for ln in io.open(ev, encoding="utf-8").read().splitlines() if ln]
        assert len(lines) >= 3, "事件流应含 round/cycle_end 等事件: %r" % lines
        evs = [json.loads(ln) for ln in lines]
        assert evs[0]["event"] == "round" and evs[0]["root"] == "A", evs[0]
        assert evs[-1]["event"] == "cycle_end" and evs[-1]["verdict"] == "unclogged", evs[-1]
        rep = json.load(io.open(j8, encoding="utf-8"))
        assert rep["mode"]["loop"] is True and rep["cycles"][0]["verdict"] == "unclogged"
        print("矢量⑧ --loop 哨态（JSONL 事件流·终局即停）: PASS")

        # 矢量⑨ CLI 四码
        d, src, world, wd = fixture("v9_cli")
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺 --src 应 rc=2 实测 %d" % p.returncode
        p = run(["--src", os.path.join(tmp, "nope"), "--candidates",
                 os.path.join(d, "cands.tsv")])
        assert p.returncode == 9, "缺 src 应 rc=9 实测 %d" % p.returncode
        p = run(["--src", src, "--candidates", os.path.join(tmp, "nope.tsv")])
        assert p.returncode == 9, "缺清单应 rc=9 实测 %d" % p.returncode
        p = run(["--src", src, "--rounds", "0",
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, "--rounds 0 应 rc=2 实测 %d" % p.returncode
        p = run(["--src", src, "--candidates", os.path.join(d, "cands.tsv"),
                 "--chain-ledgers", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, "三源互斥应 rc=2 实测 %d" % p.returncode
        p = run(["--src", src, "--injector", os.path.join(tmp, "no_inj"),
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 9, "缺 injector 场景应 rc=9 实测 %d" % p.returncode
        print("矢量⑨ CLI 四码（0/2/9·互斥·injector 缺场景）: PASS")

        # 矢量⑩ --audit 只读基线：全树 probe 干跑归集→chain_graph→基线报告
        # （零写盘自证·final=audit·cures 恒空·墙账 graph 判例·exit 0）
        d, src, world, wd = fixture("v10_audit")
        j10 = os.path.join(wd, "report.json")
        m_before = tree_manifest(src)
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]),
                 "--workdir", wd, "--json", j10])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["verdict"] == "audit" \
            and rep["final"]["verdict"] == "audit", rep["verdict"]
        assert rep["mode"]["audit"] is True and rep["mode"]["apply"] is False \
            and rep["mode"]["loop"] is False, rep["mode"]
        assert rep["final"]["rounds_run"] == 1, rep["final"]
        assert rep["final"]["red_files"] == ["B"], rep["final"]  # L1: B 缺 A
        assert rep["final"]["cures_planned_total"] == 0 \
            and rep["final"]["cures_applied_total"] == 0, rep["final"]
        assert rep["rounds"][0]["cures_planned"] == 0 \
            and rep["rounds"][0]["cures_applied"] == 0 \
            and rep["rounds"][0]["cure"] is None \
            and rep["rounds"][0]["rescan"] is None \
            and rep["rounds"][0]["resprobe"] is None, rep["rounds"][0]
        assert rep["rounds"][0]["chain_top"][0]["lib"] == "A" \
            and rep["rounds"][0]["chain_top"][0]["self"]["washable"] is True, \
            rep["rounds"][0]["chain_top"]
        assert rep["wall"] == {}, rep["wall"]   # 可洗非 frozen·墙空
        assert rep["timing"]["enumerate_s"] is not None \
            and rep["timing"]["probe_chain_s"] >= 0 \
            and rep["timing"]["total_s"] >= 0, rep["timing"]
        assert tree_manifest(src) == m_before, "audit 源树字节被动＝违例"
        assert "NatLe" not in io.open(os.path.join(src, "A.v"),
                                      encoding="utf-8").read(), "链根件被动＝违例"
        print("矢量⑩ audit 只读基线（零写盘自证·final=audit·cures 恒空·"
              "timing 段）: PASS")

        # 矢量⑩b audit 墙账：self-unwashable 入墙（数据非停机·exit 0）
        d, src, world, wd = fixture("v10b_auditwall")
        baseb = os.path.join(d, "baseb.json")
        dump_json({"Y": {"file": "Y", "md5": None, "rc": 1,
                         "red": "Error: Illegal application", "missing": None,
                         "red_class": None, "verdict": "RED-OTHER",
                         "red_count": None, "md5_match": None},
                   "C1": rec1("C1", "Y")}, baseb)
        j10b = os.path.join(wd, "report.json")
        p = run(["--src", src, "--chain-ledgers", baseb, "--audit",
                 "--workdir", wd, "--json", j10b])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10b, encoding="utf-8"))
        assert rep["verdict"] == "audit" \
            and rep["wall"]["Y"]["reason"] == "self-unwashable", rep["wall"]
        assert rep["final"]["wall_count"] == 1 \
            and rep["final"]["red_files"] == ["C1", "Y"], rep["final"]  # Y 自身 rc1 亦红
        print("矢量⑩b audit 墙账（self-unwashable 入墙·exit 0 数据非停机）: PASS")

        # 矢量⑩c audit frozen 预检：可洗根撞在册 → frozen-in-service 入墙
        d, src, world, wd = fixture("v10c_frozen")
        with io.open(os.path.join(src, "wash_engine.v"), "w",
                     encoding="utf-8") as fh:
            fh.write(CURE13_BODY)
        LF = led({"wash_engine": rec0("wash_engine"),
                  "D": rec1("D", "wash_engine")})
        j10c = os.path.join(wd, "report.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [LF]),
                 "--workdir", wd, "--json", j10c])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j10c, encoding="utf-8"))
        assert rep["verdict"] == "audit" and \
            rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", \
            rep["wall"]
        assert "NatLe" not in io.open(os.path.join(src, "wash_engine.v"),
                                      encoding="utf-8").read(), \
            "frozen 件被落刀＝违例"
        print("矢量⑩c audit frozen 预检（frozen8 实取入墙·零落刀）: PASS")

        # 矢量⑩d audit 互斥：--apply／--loop 同给 rc=2
        d, src, world, wd = fixture("v10d_cli")
        p = run(["--src", src, "--audit", "--apply"])
        assert p.returncode == 2, "--audit --apply 同给应 rc=2 实测 %d" \
            % p.returncode
        p = run(["--src", src, "--audit", "--loop"])
        assert p.returncode == 2, "--audit --loop 同给应 rc=2 实测 %d" \
            % p.returncode
        print("矢量⑩d audit 互斥（--apply/--loop 同给 rc=2）: PASS")

        # 矢量⑪ --state-file 同形哨态 seen：轮间红账差分事件 only-new 三连跑
        # （新现红报／复现红不报／新红再报）＋state 跨进程续账＋损坏红拒 9
        # （chain-ledgers 源·零注入零真编译：根 A NOMATCH→cure-miss 墙·零
        # rescan/resprobe 路径）
        d, src, world, wd = fixture("v11_state", a_body=NOMATCH_BODY)
        led1 = os.path.join(d, "led1.json")
        dump_json({"A": rec0("A"), "B": rec1("B", "A")}, led1)
        led2 = os.path.join(d, "led2.json")
        dump_json({"A": rec0("A"), "B": rec1("B", "A"), "C": rec1("C", "A")},
                  led2)
        st11 = os.path.join(d, "sentinel_state.json")

        def loop_run(ledger, ev_path, j_path):
            return run(["--src", src, "--chain-ledgers", ledger, "--loop",
                        "--interval", "7", "--sleep-scale", "0",
                        "--state-file", st11, "--events", ev_path,
                        "--json", j_path, "--workdir",
                        os.path.join(wd, "w_%s" % os.path.basename(ledger))])

        def red_news(ev_path):
            return [json.loads(ln) for ln in io.open(ev_path, encoding="utf-8")
                    if ln.strip() and json.loads(ln).get("event") == "red-new"]

        # 跑 1：红账 {B} 全新 → red-new [B]·state 记 seen
        ev1 = os.path.join(d, "ev1.jsonl")
        j11 = os.path.join(d, "j11.json")
        p = loop_run(led1, ev1, j11)
        assert p.returncode == 1, p.stdout[-600:]   # 红是数据非器红（wall）
        rep = json.load(io.open(j11, encoding="utf-8"))
        assert rep["mode"]["loop"] is True, rep["mode"]
        assert rep["args"]["state_file"] == "sentinel_state.json", rep["args"]
        rn = red_news(ev1)
        assert len(rn) == 1 and rn[0]["new_red"] == ["B"] \
            and rn[0]["red_total"] == 1 and rn[0]["seen_before"] == 0 \
            and rn[0]["cycle"] == 1, rn
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["schema"] == STATE_SCHEMA and st["red_seen"] == ["B"] \
            and st["repos"] == {} and st["ledgers"] == {} \
            and st["buildlogs"] == {}, st
        # 跑 2：红账 {B,C}·B 已 seen → red-new 只 [C]（only-new）
        ev2 = os.path.join(d, "ev2.jsonl")
        p = loop_run(led2, ev2, os.path.join(d, "j11b.json"))
        assert p.returncode == 1, p.stdout[-600:]
        rn = red_news(ev2)
        assert len(rn) == 1 and rn[0]["new_red"] == ["C"] \
            and rn[0]["red_total"] == 2 and rn[0]["seen_before"] == 1, rn
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["red_seen"] == ["B", "C"], st
        # 跑 3：红账 {B,C} 全已 seen → 零 red-new（复现红不再报）
        ev3 = os.path.join(d, "ev3.jsonl")
        p = loop_run(led2, ev3, os.path.join(d, "j11c.json"))
        assert p.returncode == 1, p.stdout[-600:]
        assert red_news(ev3) == [], "复现红应零差分事件: %s" % red_news(ev3)
        st = json.load(io.open(st11, encoding="utf-8"))
        assert st["red_seen"] == ["B", "C"], st
        # 损坏 state 红拒 9（禁静默重建·原件不动）
        stc = os.path.join(d, "corrupt_state.json")
        corrupt = '{"red_seen": BROKEN{{{'
        with io.open(stc, "w", encoding="utf-8") as fh:
            fh.write(corrupt)
        p = run(["--src", src, "--chain-ledgers", led1, "--state-file", stc,
                 "--sleep-scale", "0"])
        assert p.returncode == 9, "损坏 state 应红拒 rc=9 实测 %d" % p.returncode
        assert "形坏" in p.stdout, p.stdout[-300:]
        assert io.open(stc, encoding="utf-8").read() == corrupt, \
            "损坏 state 被静默改写＝违例"
        print("矢量⑪ --state-file 同形哨态 seen（差分 only-new 三连跑/"
              "跨进程续账/损坏红拒 9 禁静默重建）: PASS")

        # 矢量⑫ --rounds 与 --loop 互斥明义 rc=2＋--audit 与 --state-file 互斥
        # ＋--probe-parallel<1 用法闸 rc=2（透传参数缺省 1·零漂移）
        d, src, world, wd = fixture("v12_mutex")
        p = run(["--src", src, "--loop", "--rounds", "3"])
        assert p.returncode == 2, "--rounds --loop 同给应 rc=2 实测 %d" \
            % p.returncode
        assert "互斥" in p.stdout, p.stdout[-300:]
        p = run(["--src", src, "--loop", "--rounds", "0"])
        assert p.returncode == 2, "--rounds 0 带 --loop 仍应 rc=2 实测 %d" \
            % p.returncode
        p = run(["--src", src, "--audit", "--state-file",
                 os.path.join(d, "aud_state.json")])
        assert p.returncode == 2, "--audit --state-file 同给应 rc=2 实测 %d" \
            % p.returncode
        assert "互斥" in p.stdout, p.stdout[-300:]
        p = run(["--src", src, "--probe-parallel", "0",
                 "--candidates", os.path.join(d, "cands.tsv")])
        assert p.returncode == 2, "--probe-parallel 0 应 rc=2 实测 %d" \
            % p.returncode
        assert "probe-parallel" in p.stdout, p.stdout[-300:]
        print("矢量⑫ --rounds/--loop 互斥明义＋--audit/--state-file 互斥＋"
              "--probe-parallel 0 用法闸（同给/越界 rc=2）: PASS")

        # 矢量⑬ --jobs 维度：audit timing 段记 jobs=K（--probe-parallel 实参·
        # probe_engine --jobs 透传值·缺省 1）——同候选面异 K 前后跑可比
        # （并行剖面采集口·injector 罐装模式本参旁路照记·零真编译）
        d, src, world, wd = fixture("v13_jobs")
        j13a = os.path.join(wd, "report_k1.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]),
                 "--workdir", wd, "--json", j13a])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j13a, encoding="utf-8"))
        assert rep["timing"]["jobs"] == 1 and rep["args"]["probe_parallel"] == 1, \
            (rep["timing"], rep["args"])
        assert "timing: jobs=1" in p.stdout, p.stdout[-300:]
        j13b = os.path.join(wd, "report_k2.json")
        p = run(["--src", src, "--world", world, "--audit", "--injector",
                 scenario(os.path.join(d, "inj"), [L1]), "--probe-parallel", "2",
                 "--workdir", wd, "--json", j13b])
        assert p.returncode == 0, p.stdout[-600:]
        rep = json.load(io.open(j13b, encoding="utf-8"))
        assert rep["timing"]["jobs"] == 2 and rep["args"]["probe_parallel"] == 2, \
            (rep["timing"], rep["args"])
        assert "timing: jobs=2" in p.stdout, p.stdout[-300:]
        print("矢量⑬ --jobs 维度（audit timing 段 jobs=K 入账·缺省 1/K=2 各录"
              "其值·前后跑可比）: PASS")

        print("UNCLOG-SELFTEST PASS: 十四矢量全过（绿径/诚实墙＋零链根补判/"
              "cure-miss/轮尽/缺省关实证/JSON 幂等/frozen 红拒/loop 哨态/"
              "CLI 四码/audit 只读基线零写盘自证/state-file 差分 only-new/"
              "--rounds·--loop 互斥＋--probe-parallel 用法闸＋--jobs 维度）")
        return 0
    except AssertionError as e:
        print("UNCLOG-SELFTEST FAIL: %s" % e)
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
