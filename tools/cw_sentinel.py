#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cw_sentinel.py — 实时动态哨（rocqwash tools/·v37 用户令：配合工作流实时动态
提供清洗、洗形、排障、疏通堵塞——哨是三路信号源的巡检事件流·判类与链根全编排
既有引擎·零新引擎零重造·20261111 入账）

三路信号源（可组合·至少一路）：
  ① CI 路＝--watch-repo ORG/REPO [--branch B]...（可重复多组）：
       GET /repos/{repo}/actions/runs?per_page=30（RUNS_QUERY 承 pushci.py:141
       同款惯例；token 取 ~/.netrc machine github.com 行第 6 列 password——
       netrc_token 与 ci_triage.py:226 同款副本·tools/ 无包结构故随 pushci
       先例各带一份·--netrc 参数化）→ 新 completed run（--state-file 记 seen
       run id·幂等）→ 哨取 jobs（GET .../runs/{id}/jobs?per_page=100&page=1，
       落盘 tmp）→ subprocess ci_triage --offline（pushci.py:969 run_triage
       injector 同款「真子进程真判类·零网络」）→ run 级 family/action 取自
       rocqwash-ci-triage/1 报告 → family≠none 出事件
       {kind:ci-red, repo, run, family, action}。判类谱五族＋绿炉全权在
       ci_triage（20261110 判类谱·ci_triage.py docstring 判类序）·哨不判。
  ② 本地账路＝--watch-ledgers DIR：
       新 probe/ledger JSON 落盘（mtime+名字 seen·同件 mtime/size 变亦视新）
       → subprocess chain_graph.py 新件 --json tmp（chain_graph.py:21 CLI）→
       top_order 首名即 TOP 链根 → 事件 {kind:blocking, top_root, dependents}
       （附 n 与 self 可洗性三分——chain_graph.py:88 build_graph 判例）。
  ③ 本地堵路＝--watch-buildlog FILE：
       tail 增量 grep（字节 offset 记 state·只认完整行防半行误报）→ 词面
       BUILD-FAIL／EXIT=134（判类谱 C 环境断链 token·ci_triage.py:118）／
       Error:（判类谱 A 内容红 token·ci_triage.py:108）→ 事件
       {kind:build-signal, hits[]}。日志文件未在卷＝编译未开写·零事件非红
       （report 响亮注记 present=false·非静默）。

事件流：--emit FILE（JSONL append·逐行 flush+fsync）＋stdout 镜像（响亮）。
事件行 schema=rocqwash-sentinel-event/1·键 sort_keys·行序＝产出序·seq 事件流
内单调（--emit 在位时以文件现有行数为基跨进程续号·缺省时进程内单调）——
消费方按 seq 排序即恢复全局序。ts 由 time 钟出·--sleep-scale 0 时关 ts
（selftest 确定性依赖）·事件以 note「ts=off」注记。

--on-red 'CMD 模板'：{family}／{run}／{repo} 占位替换（事件字段直替·缺字段
替空串）→ subprocess shell 执行（超时帽 60s·rc≠0/超时响亮入 actions 账与
stdout·不改哨退出码——on-red 是旁路动作非器面）。缺省无＝report-only·
**零动作是缺省**（承 cure_applier 干跑缺省同纪律）。

双模：--once（单轮巡检出账退出·工作流步骤用）｜--loop --interval S（长驻·
JSONL 追加·工作流后台 bash 任务用）·--max-rounds N 轮帽（0=无限·selftest
矢量⑤三轮序贯依赖）。

退出码：0=巡检完成（红是数据非器红·响亮 stdout）；2=用法错（缺模式/双模
同给/三源全缺/--branch 先于 --watch-repo/repo 形坏/负参/once 带 loop 专属
参）；9=信号源不可达（CI HTTP 4xx/5xx·netrc 缺·token 空·runs/jobs 形坏·
injector 缺失/形坏/canned 未覆盖·ledgers 目录缺·state 形坏·ci_triage/
chain_graph 子进程 rc≠0）。--selftest：0=全过／2=断言失败。

report schema（--json·每轮覆盖写·rocqwash-sentinel/1）：
  {"schema","mode","round","sources"{ci[],ledgers{},buildlog{}},"events"[],
   "actions"[](on-red 执行账),"state_file"?,"interval"?,"sleep_scale",
   "ts_enabled","injector"?}
  events/actions 元素与事件流逐字节同源（确定性：--sleep-scale 0 时同输入
  重跑字节级恒同）。

injector 文件（--injector·schema=rocqwash-sentinel-injector/1）＝canned API
响应表·离线可测（铁律④零真网络）：
  {"schema":"rocqwash-sentinel-injector/1","responses":[
     {"url_contains":"/actions/runs?","status":200,"body":{...workflow_runs...}},
     {"url_contains":"/runs/178/jobs","status":200,"body":{...jobs...}}]}
  按序首中即用·可循环复用（哨轮询幂等语义·非 pushci steps 形按序耗尽）；
  未命中 fail-loud 9——canned 表须全覆盖·**绝不静默走真网络**。runs body
  同 GitHub API 真形 {"total_count":N,"workflow_runs":[...]}（兼收 "runs" 键
  承 pushci watch 证据形·pushci.py:880）。

state 文件（--state-file·schema=rocqwash-sentinel-state/1）：seen 幂等持久层
  {"repos":{"ORG/REPO":{"seen_runs":{"<id>":{conclusion,run_number,family}}}},
   "ledgers":{"<名>":{"mtime_ns","size"}},"buildlogs":{"<路径>":{"offset"}}}
  缺省 None=内存态（once 单轮无跨轮幂等·loop 须给）。

编排律（承 v37 用户令⑤）：ci_triage／chain_graph 全 subprocess 直调（pushci
_run_py 同款·py:591——纯逻辑零编译故不经 cpu_guard·真编译才须 guard 包裹，
probe_engine.py:10 判例）；哨自身零编译零网络（injector 缺席线上模式除外）。

诚实律（承 CONTRIBUTING §0）：只认机械证据；红是数据非器红（巡检 exit 0）；
fail-loud 禁静默降级（源不可达 9·injector 未覆盖 9·子进程 rc≠0 9）；零
第三方依赖（纯 stdlib）；--json 落盘 sort_keys·--sleep-scale 0 同输入重跑
字节级恒同；零硬编码绝对路径（--netrc/--state-file/--emit/--injector 全
参数化·引擎件按哨自身相对定位承 pushci TOOLS_DIR 先例）。
"""
import argparse
import datetime
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

# buildlog 词面（判类谱 token·ci_triage.py:95-108 同源）：BUILD-FAIL／
# EXIT=134（C 环境断链）／Error:（A 内容红）
BUILDLOG_SIGNAL_RE = re.compile(r"BUILD-FAIL|EXIT=134|\bError:")

EVENT_EVIDENCE_CAP = 8      # ci-red 事件 evidence 条数帽（响亮截断注记）
EVENT_LINE_CAP = 200        # 事件内单行证据/命中行字符帽
BUILDLOG_HIT_CAP = 50       # 单轮 build-signal 命中行帽（超出 truncated 注记）
ON_RED_TIMEOUT = 60         # on-red 子进程超时秒（旁路动作防卡哨）


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


def run_py(tool_path, cli):
    """python3 -B <tool> <cli> 子进程（stdout+stderr 合流·pushci.py:591 同款）。
    纯逻辑引擎零编译故不经 cpu_guard（probe_engine.py:10 判例：真编译才须
    guard）·缺件 → 9。"""
    if not os.path.isfile(tool_path):
        raise SentryError("工具链件缺失: %s" % tool_path, 9)
    p = subprocess.run([sys.executable, "-B", tool_path] + list(cli),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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


def api_get_json(url, token, timeout, injector):
    """只读 GET → (status, parsed_json)。唯一网络动作·注入点单函数：
    injector 在场按 url_contains 首中即用（可循环复用·哨轮询幂等语义）·未命中
    fail-loud 9 绝不静默走真网络；缺席真 urllib（HTTP 4xx/5xx → 9·连接失败
    → 9·body 非合法 JSON → 9）。"""
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
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "rocqwash-cw-sentinel",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": "token %s" % token,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        try:
            body = (e.read() or b"").decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise SentryError("CI API HTTP %d: %s（%s）"
                          % (e.code, body.strip()[:160], url), 9)
    except (urllib.error.URLError, OSError) as e:
        raise SentryError("CI API 不可达: %s (%s)" % (url, e), 9)
    try:
        return 200, json.loads(raw.decode("utf-8"))
    except ValueError as e:
        raise SentryError("CI API body 非 JSON: %s (%s)" % (url, e), 9)


# ---- state（seen 幂等持久层）-------------------------------------------------

def new_state():
    return {"schema": STATE_SCHEMA, "repos": {}, "ledgers": {}, "buildlogs": {}}


def load_state(path):
    if path is None:
        return new_state()
    if not os.path.isfile(path):
        return new_state()
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise SentryError("state 文件形坏（解析失败）: %s (%s)" % (path, e), 9)
    for k in ("repos", "ledgers", "buildlogs"):
        if not isinstance(st.get(k), dict):
            raise SentryError("state 文件形坏（缺 %s dict）: %s" % (k, path), 9)
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


def emit_event(sentry, ev):
    """--emit JSONL append（flush+fsync）＋stdout 镜像（响亮）。emit 写败 → 9。"""
    line = json.dumps(ev, ensure_ascii=False, sort_keys=True)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    path = sentry["emit"]
    if path:
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


def triage_run_offline(repo, run_id, jobs_body):
    """哨取 jobs（api_get_json·injector 可注入）→ 落盘 tmp → subprocess
    ci_triage --offline（pushci.py:969 run_triage injector 同款·真子进程真
    判类·零网络）→ rocqwash-ci-triage/1 report。ci_triage rc≠0 → 9。"""
    fdj, jobs_path = tempfile.mkstemp(prefix="cw_sentinel_jobs_")
    os.close(fdj)
    fd, out_path = tempfile.mkstemp(prefix="cw_sentinel_triage_")
    os.close(fd)
    try:
        with io.open(jobs_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(jobs_body, fh, sort_keys=True)
        rc, out = run_py(TRIAGE_TOOL, ["--offline", jobs_path, "--json", out_path])
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
                           sentry["injector"])
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
                sentry["injector"])
            if not isinstance(jobs_body, dict) \
                    or not isinstance(jobs_body.get("jobs"), list):
                raise SentryError("jobs API 形坏（须 {\"total_count\":N,"
                                  "\"jobs\":[...]}）: run=%s" % rid, 9)
            rep = triage_run_offline(repo, rid, jobs_body)
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
            rc, cout = run_py(CHAIN_TOOL, [path, "--json", gpath])
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

def fire_on_red(sentry, ev):
    """--on-red 模板占位替换（{family}/{run}/{repo}·事件字段直替缺字段空串）
    → subprocess shell 执行。rc≠0/超时响亮入账·不改哨退出码（旁路动作非
    器面）。"""
    cmd = str(sentry["on_red"])
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
    return entry


# ---- 单轮巡检 ----------------------------------------------------------------

def poll_round(sentry, st, round_no):
    """单轮三路巡检 → 轮 report dict（--json 覆盖写·sort_keys）。源硬错
    （SentryError）逐层上抛由 run_sentry 裁停——fail-loud 不带病运行。"""
    a = sentry["args"]
    sys.stdout.write("=== CW-SENTINEL round=%d mode=%s（红是数据非器红）===\n"
                     % (round_no, sentry["mode"]))
    rep = {"schema": SCHEMA, "mode": sentry["mode"], "round": round_no,
           "sources": {}, "events": [], "actions": sentry["actions"],
           "sleep_scale": a.sleep_scale, "ts_enabled": sentry["ts_enabled"]}
    ci_out = []
    for spec in sentry["specs"]:
        ci_out.append(poll_ci_repo(sentry, spec, st))
    if ci_out:
        rep["sources"]["ci"] = ci_out
    if a.watch_ledgers:
        rep["sources"]["ledgers"] = poll_ledgers(sentry, a.watch_ledgers, st)
    if a.watch_buildlog:
        rep["sources"]["buildlog"] = poll_buildlog(sentry, a.watch_buildlog, st)
    for ev in sentry["events"]:
        if ev.get("kind") in ("ci-red", "blocking", "build-signal") \
                and sentry["on_red"]:
            fire_on_red(sentry, ev)
    rep["events"] = list(sentry["events"])
    rep["actions"] = list(sentry["actions"])
    if a.state_file:
        rep["state_file"] = a.state_file
    if a.injector:
        rep["injector"] = a.injector
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
    sentry = {
        "args": args, "mode": mode, "specs": specs,
        "seq": 1, "events": [], "actions": [],
        "emit": args.emit, "on_red": args.on_red,
        "timeout": args.timeout, "injector": None, "token": None,
        "ts_enabled": args.sleep_scale != 0,
    }
    if args.injector:
        sentry["injector"] = load_injector(args.injector)
    if args.emit and os.path.isfile(args.emit):
        try:
            with io.open(args.emit, "r", encoding="utf-8") as fh:
                sentry["seq"] = sum(1 for ln in fh if ln.strip()) + 1
        except OSError as e:
            raise SentryError("事件流读基失败: %s (%s)" % (args.emit, e), 9)
    return sentry


def run_sentry(args):
    """双模主循环：once 单轮·loop interval 序贯（--max-rounds 轮帽 0=无限）。
    源硬错 → sentinel-error 事件（若 emit 在位）+ rc 9 退出（fail-loud 不带
    病运行·任务书 9 口径）。state 每轮末落盘（事件先 emit 后存 state·宁重复
    不丢件）。"""
    sentry = build_sentry(args)
    st = load_state(args.state_file)
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
    ap.add_argument("--on-red", dest="on_red", default=None, metavar="CMD",
                    help="红事件命令模板（{family}/{run}/{repo} 占位）·缺省"
                         "无=report-only 零动作是缺省")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc 路径（默认 ~/.netrc·machine github.com 第 6 "
                         "列=token·ci_triage 同款）")
    ap.add_argument("--timeout", type=int, default=30, metavar="S",
                    help="单请求超时秒（默认 30）")
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
    ＋确定性字节恒同＋CLI 四码＋injector 未覆盖 9＋目录缺 9。"""
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

        print("CW-SENTINEL-SELFTEST PASS: ①once ci-red+二跑 seen 幂等零事件/"
              "②ledger 新件 blocking+幂等/③buildlog 增量 grep+半行不误报/"
              "④on-red 占位替换执行实证+缺省零动作/⑤loop 三轮 JSONL 序贯/"
              "⑥emit 逐行合法 sort_keys+seq 序贯/确定性字节恒同/CLI 四码+"
              "401→9+canned 未覆盖→9+目录缺→9 全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
