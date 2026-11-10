#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pushci.py — 修复后推送 CI 一键流水线编排器（rocqwash tools/·v36 旗舰·20261111 入账）

五段管线（承 v35 四器判例·编排而非重造——doctor/net_probe/ci_triage/gate4 守卫
一律 subprocess 调用·本器只做胶水与状态机；每段可 --steps 独选·缺省全跑）：
  1 preflight（发射闸·禁发射律代码化）：
      ① toolchain：subprocess tools/toolchain_dyld_doctor.py --json <tmp>
        （--worker 缺省探测）→ verdict≠healthy 即停 verdict=toolchain；
      ② net：subprocess tools/net_probe.py --rounds 2 --interval <probe-interval>
        --stable-window --json <tmp> → UNSTABLE 即停 verdict=unstable
        （双探稳窗·单探禁发射的发射闸由四器自带·本器只认其裁决）；
      ③ 可选 --pre-scan-gate4：git -C <repo> diff --name-only <base>...<branch>
        取 .v 变更件 → verify/gate4_comment_guard.py 逐件（--file）→ FAIL=0 才放行
        （FAIL 清单入 report·verdict=gate4-block；REVIEW 件响亮入账不拦——
        守卫 rc 口径 0=PASS/1=FAIL/2=复核·形外退出 fail-loud）。
  2 push：git -C <repo> -c http.version=HTTP/1.1 push <remote> <branch>
      （重试 3 发×45s 间隔；三败且 remote URL 为 https://github.com/ 形→取前缀
      https://ghproxy.net/ 换路再试 2 发·非该形响亮注记跳过）；全败→verdict=
      unstable exit 1。pushed_sha＝push 成功后 ls-remote <remote>
      refs/heads/<branch> 取**远端 tip**（承 watch.py「真 rc＋ls-remote 复核」
      纪律·第 4 git 调·CI 构的是远端 tip·远端为准；与本地 rev-parse tip 异则
      响亮注记；rev-parse 先行只作分支在位性 fail-loud 9 预检·git 调序＝
      get-url→rev-parse→push→ls-remote 恒 4 调〔非 dry-run〕）。
  3 resolve+watch：轮询 GET /repos/{repo}/actions/runs?per_page=30（repo 由
      remote URL 推导·host 须 github.com）取 head_branch=<branch> 且
      head_sha==pushed_sha 最新 run（按 (run_number,id) 取 max·API 序无关）；
      每 --watch-interval 秒（默认 150）一询至 completed。**updated_at 冻结≠
      僵尸判例**——以 status 为准（status-only 口径·连续 N 轮 in_progress 属
      长步正常不误判·本器代码路径零 updated_at 判读）。
  4 heal（观测红时）：subprocess tools/ci_triage.py --repo --run（线上取 jobs
      分类）→ family 分派：B/E（NETRED/coqchk-skipped）→ net_probe
      --stable-window 过→POST /runs/{id}/rerun（403 already running 幂等接受）
      →回 watch（计 heal_round·帽 --max-heal 默认 3·超帽 verdict=heal-exhausted
      exit 1；probe UNSTABLE→禁发射 verdict=unstable exit 1）；
      A（内容红）→verdict=fix-content 停 exit 2（禁代修——修复是席/人职责）；
      C→verdict=toolchain 停 exit 1（附 doctor 重跑建议）；
      分派表外族（D-queue-wall/UNRECOGNIZED 等）→禁自动 rerun→人工指认
      （verdict=fix-content exit 2·family 原值响亮在册）。
      heal.rounds 语义＝**fired 重跑账**（probe+rerun 实动的轮才入册·A/C/表外
      裁停零轮入册＝零 rerun 实证）；历次判类 outcomes 全量在
      stages.heal.last_triage（family/action/evidence）。
  5 verdict＋可选 --merge：--merge 时先 GET /repos/{repo}/pulls?head=<owner>:
      <branch>&state=open 解 PR 号（或 --pr 显传·无 open PR→9 目标缺失）→
      PUT /pulls/{n}/merge（--merge-method merge|squash·缺省 merge〔分支含
      merge commit 判例〕；409→GET branches/main 重拉 tip 歇 60s 重试 ≤3·
      仍 409→verdict=fix-content exit 2〔merge 冲突＝内容活〕；其余 HTTP→
      fail-loud 9）。

离线可测（硬要求）：核心循环全注入——
  --injector DIR    注入场景·**双形通吃**：
      〔steps 形〕DIR/scenario.json＝{"steps":[{at_round,responses:[{method,path,
        status,body}...]}...], "tools":{doctor,probe canned}, "jobs"|"jobs_list"}
        ——responses 按轮按序严格消费（method+path 子串·失配 fail-loud）；
        tools canned 接 {"verdict":str,"rc":int} 或 {"report":{...}}（verdict 取
        report.verdict）；jobs 单 dict 复用或 jobs_list 逐判类调用消费。
      〔flat 形·承 tests/fixtures/pushci_scenarios 并行席契约〕DIR/scenario.json
        为夹具原件（含 "canned" 键即认）或 DIR 下 runs/NNNN.json+jobs/NNNN.json
        +rerun/NNNN.json+probe/NNNN.json+merge.json 平铺：canned.runs 逐 poll 消
        耗（体键 runs|workflow_runs 双认）·canned.probe 逐 heal 探针消耗（含
        net_probe 报告真形取 verdict）·canned.rerun[{"run_id","status"}] 逐 rerun
        消耗（run_id 与路径咬合校验）·canned.merge{"status","body"} 供 PUT·
        canned.jobs 逐判类调用消耗·canned.logs 不消费（测试席证据面）。flat 形
        未携闸 canned（doctor/probe）→preflight 双闸按缺省绿施·响亮注记在册
        （测试契约形·真发射闸以 steps 形或真模式为准）；merge 无 pulls canned→
        须 --pr 显传。
      API 调用流水落 <DIR>/api_calls.json 供实证。
  --git-caller FILE canned git 响应场景（responses[].args_contains 按序严格
                    匹配·同上 fail-loud）；调用流水落 <FILE 去展>.calls.json。
                    须与 --injector 成对（injector 无 canned git＝真 push 危险·
                    单边给出即用法错 exit 2）。
  --sleep-scale F   全部 sleep 乘 F（selftest 用 0＝零真睡）。
  _api(method,path,body) 单函数化（ApiClient.__call__）便于注入替换。
  --selftest        八矢量＋单元向量＋韧性层退避/超时杀矢量＋CLI 四码＋确定性
                    （零真网络零真 push 零编译；--netrc 故意指向不存在路径——
                    凭据惰性读证）。

用法（路径全参数化·零硬编码绝对路径·env 兜底只认 ROCQWASH_MASK〔遮蔽串·
承 watch.py 惯例〕）：
  python3 tools/pushci.py --repo-path DIR --branch B [--base-ref main]
      [--remote origin] [--pre-scan-gate4] [--pr N] [--merge]
      [--merge-method merge|squash] [--max-heal 3] [--watch-interval 150]
      [--probe-interval 60] [--watch-max-rounds 0] [--timeout 120]
      [--retry-max 3]
      [--steps preflight,push,watch,heal,verdict]
      [--injector DIR] [--git-caller FILE] [--sleep-scale 1.0] [--netrc PATH]
      [--json out] [--dry-run]
  python3 tools/pushci.py --selftest
  --dry-run=只打计划零副作用 exit 0（零 git 零 API 零工具子进程）。
  --watch-max-rounds（增补安全阀·默认 0=不限）＝轮询轮帽·超帽 fail-loud 9。
  --timeout S（韧性层 v37·缺省 120）＝全部真子进程防挂帽（git 四调＋四器工具
  _run_py）：超时=子进程杀＋fail-loud 9 报调用名（零悬挂）；canned 注入路径
  零真子进程不受此帽。
  --retry-max N（韧性层 v37·缺省 3）＝真 urllib _api 403/429/5xx 指数退避重试
  帽（base 2s·Retry-After 秒数头优先替当次延迟·HTTP-date 不猜落回指数；耗尽
  原码上交语义裁决·4xx 语义面 401/404/409 等不重试；延迟计算抽公共件
  tools/_http_backoff.py 纯函数·三器共享·同目录 sys.path 注入 import·
  无 __init__ 包结构；injector canned 路径零真网络一律不重试——离线可测铁律）。
  段依赖（用法错 2）：watch⇒push·heal⇒watch·--merge⇒watch。

退出码：0=success/dry-run；1=heal-exhausted/unstable/toolchain〔toolchain 停＝
  环境件·任务书退出码表未钦·比照 unstable 归 1 响亮入档〕；2=fix-content/
  gate4-block/用法错；9=目标缺失（repo/remote/分支/PR/工具链件缺失·netrc 缺·
  API 不可达·API 4xx/5xx 硬错·watch 轮帽达·真子进程超时被杀〔--timeout〕）。
  --selftest：0=全过／2=断言失败。

report schema（--json）= rocqwash-pushci/1：
  {schema, mode: online|injector|dry-run, steps, args,
   stages{preflight{toolchain{verdict,rc}, net{verdict,rc},
                    gate4?{files,pass_files,fail_files,review_files,
                           skipped_missing,fail_count}},
          push{sha,remote,url_masked,attempts[{target,rc}],ghproxy_used},
          watch{run_tag,run_id,rounds,conclusion,policy},
          heal{rounds[{round,family,action,probe,fired,http,evidence}],
               fired_total},
          merge?{pr,method,merged,attempts,main_tip?,merge_sha?}},
   plan?（仅 dry-run）, evidence, final{conclusion,verdict}, verdict}
  verdict ∈ success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|
  dry-run。

诚实律（承 CONTRIBUTING §0）：只认机械证据；分派表外不充谱不代 heal；A 族禁
代修；token 永不回显（netrc 解析承 ci_triage 同款口径：machine github.com 行
第 6 列·单行 6 列形与多行形通吃）；远端 URL 内嵌凭据与 ROCQWASH_MASK 串遮蔽
后出账；--json 落盘 sorted+sort_keys·同输入重跑字节级恒同（报告零墙钟字段）；
stdout 全数据驱动；零第三方依赖（纯 stdlib）；fail-loud 禁静默降级。
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
WATCH_POLICY = "status-only（updated_at 冻结非僵尸判据·以 status 为准）"

# verdict 封册 → 退出码（0=success/dry-run；1=heal-exhausted/unstable/toolchain；
# 2=fix-content/gate4-block；9 码留给 fail-loud 目标缺失不经此册）
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
    sys.path.insert(0, TOOLS_DIR)   # 同目录共享退避小模块（无 __init__ 包结构）
import _http_backoff


class PushciError(Exception):
    """带退出码的 fail-loud 异常（code: 2=用法/场景形错·9=目标缺失/API 硬错）。"""

    def __init__(self, msg, code=9):
        super(PushciError, self).__init__(msg)
        self.code = code


class StopVerdict(Exception):
    """管线裁停（verdict 携带出账·code 为任务书退出码口径·evidence 入 report）。"""

    def __init__(self, verdict, code, evidence=None):
        super(StopVerdict, self).__init__(verdict)
        self.verdict = verdict
        self.code = code
        self.evidence = list(evidence or [])


def subproc_run(cmd, timeout, what, merge_stderr=False):
    """统一真子进程执行＋--timeout 防挂（韧性层 v37·缺省 120s）：超时=子进程
    杀（subprocess.run 超时即杀后 raises·零悬挂）＋fail-loud 9 报调用名。
    timeout=None 传穿为无帽（canned 路径零真子进程不受此帽）。"""
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT if merge_stderr
                              else subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise PushciError("子进程超时被杀（--timeout=%ss·调用: %s）"
                          % (timeout, what), 9)


# ---- 小件（确定性 helpers）---------------------------------------------------

def sleep_scaled(sec, scale):
    """time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖）。"""
    time.sleep(max(0.0, float(sec) * float(scale)))


def url_secret_masks(url):
    """远端 URL 内嵌凭据（userinfo 密码部）→ 遮蔽串清单（承 watch.py 同款）。"""
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
    """把 masks 中每串替换为 ***MASKED***（空串忽略·承 watch.py 同款）。"""
    for m in masks:
        if m:
            s = s.replace(m, "***MASKED***")
    return s


def collect_masks(url):
    """遮蔽串总集：URL userinfo 密码部＋env ROCQWASH_MASK（冒号分隔·承
    watch.py 惯例·env 兜底只认 ROCQWASH_* 任务书钦名）。"""
    masks = url_secret_masks(url)
    env_masks = os.environ.get("ROCWASH_MASK", "")
    masks += [m for m in env_masks.split(":") if m]
    return masks


def url_host(url):
    """remote URL → host（https://·http://·git@·ssh:// 四形通吃·形外 None）。"""
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
    """remote URL → ORG/REPO（取路径末两段去 .git·https/http/git@/ssh 四形通吃；
    host 不限——测试 shim 远端假域同推导·ghproxy 换路另有 https://github.com/
    形独立门 ghproxy_url）。形外/段不足 → None（fail-loud 由调用方裁决）。"""
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
    """ghproxy 换路 URL：仅当 remote URL 为 https://github.com/ 形（判例换路
    前缀 https://ghproxy.net/https://github.com/）·否则 None（响亮跳过）。"""
    if url.strip().startswith("https://" + GHPROXY_HOST + "/"):
        return GHPROXY_PREFIX + url.strip()
    return None


def netrc_token(path, machine="github.com"):
    """netrc 手动解析（承 ci_triage.netrc_token 同款口径）：machine <m> login <l>
    password <p>·单行 6 列形与多行形通吃 → token。缺文件/无条目/空值 →
    fail-loud 9（token 永不回显·惰性：仅真模式首个 API 调用才读）。"""
    if not os.path.isfile(path):
        raise PushciError("netrc 缺失: %s（线上模式需 machine %s ... password 形凭据）"
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
                    raise PushciError("netrc machine %s password 为空" % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise PushciError("netrc 无 machine %s password 形条目（单行 6 列形：第 6 列"
                      "=token）: %s" % (machine, path), 9)


def snippet(body):
    """API body 摘录（诊断用·帽 160 字符）。"""
    if body is None:
        return ""
    s = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    return s[:160]


def parse_body(raw):
    """响应体 → parsed JSON 或原文（空 → None）。"""
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace") \
        if isinstance(raw, bytes) else str(raw)
    try:
        return json.loads(text)
    except ValueError:
        return text


# ---- 注入点①：git caller（缺省真 subprocess·--git-caller 换 canned）-----------

class GitCaller(object):
    """git 调用单点。canned=None → 真 git 子进程（--timeout 防挂帽·超时杀＋9
    报调用名）；canned=list → 场景脚本严格按序消费（首条未用响应必须命中
    args_contains 全部子串·否则 fail-loud——场景序bug 当场现形）。调用流水全记
    self.calls 供 .calls.json 实证。"""

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
                raise PushciError("canned git 场景响应耗尽（实调 %r）" % (args,), 2)
            for needle in resp.get("args_contains") or []:
                if not any(needle in a for a in args):
                    raise PushciError("canned git 失配：期待含 %r·实调 %r"
                                      % (needle, args), 2)
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


# ---- 注入点②：API 单函数 _api（缺省真 urllib·injector 换 canned）--------------

class ApiClient(object):
    """_api(method, path, body) 单函数化。canned=steps 形场景（按 at_round 严格
    按序消费）·flat=flat 形 canned（runs 逐 poll·rerun 逐 POST·merge 单发·并行
    席契约形）·皆 None → 真 urllib（token 惰性取 netrc·HTTP 4xx/5xx 返回
    (code, body) 交语义裁决·连接失败 fail-loud 9）。韧性层 v37：真 urllib 路
    403/429/5xx 指数退避重试（_http_backoff 纯函数·帽 retry_max·Retry-After
    秒数头优先·耗尽原码上交语义裁决·4xx 语义面不重试）；injector/canned 路径
    零真网络一律不重试。调用流水全记 self.calls。"""

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
        """flat 形 canned：GET runs 逐 poll·POST rerun 逐发（run_id 咬合校验）·
        PUT merge 单发（canned.merge {"status","body"}·409 流须 steps 形）。"""
        f = self.flat
        if method == "GET" and RUNS_QUERY in path:
            if self._flat_runs_i >= len(f["runs"]):
                raise PushciError("flat 场景 canned.runs 耗尽（poll %d）"
                                  % (self._flat_runs_i + 1), 2)
            b = f["runs"][self._flat_runs_i]
            self._flat_runs_i += 1
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": 200})
            return 200, b
        if method == "POST" and "/rerun" in path:
            if self._flat_rerun_i >= len(f["rerun"]):
                raise PushciError("flat 场景 canned.rerun 耗尽（rerun %d）"
                                  % (self._flat_rerun_i + 1), 2)
            e = f["rerun"][self._flat_rerun_i]
            self._flat_rerun_i += 1
            status = e.get("status", 200) if isinstance(e, dict) else int(e)
            m = re.search(r"/runs/(\d+)/rerun$", path)
            if isinstance(e, dict) and e.get("run_id") is not None \
                    and m and str(e["run_id"]) != m.group(1):
                raise PushciError("flat canned.rerun run_id 失配（canned %s vs "
                                  "路径 %s）" % (e["run_id"], m.group(1)), 2)
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": status})
            return status, None
        if method == "PUT" and "/merge" in path:
            mc = f.get("merge")
            if not isinstance(mc, dict):
                raise PushciError("flat 场景缺 canned.merge（PUT %s）" % path, 2)
            self.calls.append({"round": round_no, "method": method,
                               "path": path, "status": mc.get("status", 200)})
            return mc.get("status", 200), mc.get("body")
        raise PushciError("flat 场景不支持的 API 调用（pulls GET 须 --pr 显传）: "
                          "%s %s" % (method, path), 2)

    def _canned_call(self, method, path, body, round_no):
        step = None
        for s in self.canned.get("steps") or []:
            if s.get("at_round") == round_no:
                step = s
                break
        if step is None:
            raise PushciError("injector 场景无 at_round=%s 步（实调 %s %s）"
                              % (round_no, method, path), 2)
        resp = None
        for r in step.get("responses") or []:
            if not r.get("_used"):
                resp = r
                break
        if resp is None:
            raise PushciError("injector 场景 round=%s canned 响应耗尽（实调 %s %s）"
                              % (round_no, method, path), 2)
        if resp.get("method") != method:
            raise PushciError("injector 失配：期待 method=%s·实调 %s（path %s）"
                              % (resp.get("method"), method, path), 2)
        want = resp.get("path") or ""
        if want and want not in path:
            raise PushciError("injector 失配：canned path %r 非实调 %r 子串"
                              % (want, path), 2)
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
                raise PushciError("API 不可达: %s (%s)" % (url, e), 9)
            return code, parse_body(raw)


# ---- 管线本体 ----------------------------------------------------------------

class Pipeline(object):

    def __init__(self, args):
        self.args = args
        self.repo = None
        self.remote_url = None
        self.masks = []
        self.round_no = 0
        self.scen = None
        self.injector_kind = None          # "steps" | "flat" | None
        self._jobs_i = 0                   # canned jobs 逐判类调用消费指针
        self._flat_probe_i = 0             # flat canned.probe 逐 heal 探针指针
        self._flat_gate_noted = False      # flat 形 preflight 双闸缺省绿注记（一次）
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
                raise PushciError("git-caller 场景形坏（须 {\"responses\":[...]}）: %s"
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
            raise PushciError("%s JSON 形坏: %s (%s)" % (what, path, e), 2)

    def _load_injector(self, inj):
        """注入场景装载（双形通吃）：
        〔a〕DIR/scenario.json 含 "canned" dict → flat 形（夹具原件 verbatim·
             schema/scenario/summary/argv/expect 等未知键忽略）；
        〔b〕DIR/scenario.json（无 canned）→ steps 形（steps[].at_round）；
        〔c〕无 scenario.json 但有 runs/ 平铺目录 → flat 形（并行席占位布局：
             runs/NNNN.json+jobs/NNNN.json+rerun/NNNN.json+probe/NNNN.json+
             merge.json·文件名字典序＝消费序）。"""
        sj = os.path.join(inj, "scenario.json")
        if os.path.isfile(sj):
            scen = self._load_json_file(sj, "injector 场景")
            if not isinstance(scen, dict):
                raise PushciError("injector 场景形坏（须 dict）: %s" % sj, 2)
            return scen
        if os.path.isdir(os.path.join(inj, "runs")):
            def rd(kind):
                d = os.path.join(inj, kind)
                out = []
                if os.path.isdir(d):
                    for fn in sorted(os.listdir(d)):
                        if fn.endswith(".json"):
                            out.append(self._load_json_file(
                                os.path.join(d, fn), "flat canned %s/%s"
                                % (kind, fn)))
                return out
            mp = os.path.join(inj, "merge.json")
            merge = self._load_json_file(mp, "flat canned merge") \
                if os.path.isfile(mp) else None
            return {"canned": {"runs": rd("runs"), "jobs": rd("jobs"),
                               "rerun": rd("rerun"), "probe": rd("probe"),
                               "logs": {}, "merge": merge}}
        raise PushciError("injector 场景缺失（scenario.json 或 runs/ 平铺目录）: %s"
                          % inj, 9)

    # -- 工具子进程（四器编排·零新引擎）---------------------------------------

    def _run_py(self, tool_path, cli):
        """python3 -B <tool> <cli> 子进程（stdout+stderr 合流）。缺件 → 9；
        --timeout 防挂（缺省 120s）：超时=子进程杀＋fail-loud 9 报调用名。"""
        if not os.path.isfile(tool_path):
            raise PushciError("工具链件缺失: %s" % tool_path, 9)
        p = subproc_run([sys.executable, "-B", tool_path] + list(cli),
                        self.args.timeout,
                        "python3 -B %s %s" % (os.path.basename(tool_path),
                                              " ".join(str(c) for c in cli[:2])),
                        merge_stderr=True)
        out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        return p.returncode, out

    def _tool_report(self, tool_path, cli):
        """跑四器之一（附 --json tmp）→ (rc, report|None, stdout)。"""
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
        """判类 canned jobs 取用（逐判类调用消费）：flat 形 canned.jobs 列表→
        steps 形 jobs_list 列表→steps 形 jobs 单 dict（复用）。"""
        if self.injector_kind == "flat":
            lst = (self.scen.get("canned") or {}).get("jobs") or []
        elif isinstance(self.scen.get("jobs_list"), list):
            lst = self.scen["jobs_list"]
        else:
            return self.scen.get("jobs")
        if self._jobs_i >= len(lst):
            raise PushciError("injector 场景 canned jobs 耗尽（判类调用 %d）"
                              % (self._jobs_i + 1), 2)
        j = lst[self._jobs_i]
        self._jobs_i += 1
        return j

    def runs_path(self):
        return "/repos/%s%s" % (self.repo, RUNS_QUERY)

    # -- 段 1：preflight -------------------------------------------------------

    def stage_preflight(self):
        a = self.args
        pf = {"toolchain": None, "net": None}
        if a.pre_scan_gate4:
            pf["gate4"] = None
        self.report["stages"]["preflight"] = pf

        # ① toolchain（doctor --worker 缺省探测·verdict≠healthy 即停）
        if self.injector_kind == "steps":
            tc = self.scen_tools().get("toolchain_dyld_doctor") or {}
            if isinstance(tc.get("report"), dict):
                doc_rep = tc["report"]
                verdict = doc_rep.get("verdict")
                rc = tc.get("rc", 0 if verdict == "healthy" else 1)
            else:
                verdict, rc, doc_rep = tc.get("verdict"), tc.get("rc", 0), None
            if verdict is None:
                raise PushciError("injector 场景缺 tools.toolchain_dyld_doctor"
                                  ".verdict", 2)
        elif self.injector_kind == "flat":
            verdict, rc, doc_rep = "healthy", 0, None   # 闸缺省绿·注记在 probe_stable 施
        else:
            rc, doc_rep, out = self._tool_report(DOCTOR_TOOL, [])
            verdict = doc_rep.get("verdict") if isinstance(doc_rep, dict) else None
            if verdict is None:
                raise PushciError("doctor 报告形坏（无 verdict）rc=%d: %s"
                                  % (rc, out[-200:]), 2)
        pf["toolchain"] = {"verdict": verdict, "rc": rc}
        if verdict != "healthy":
            ev = ["doctor verdict=%s rc=%s（≠healthy·禁发射）" % (verdict, rc)]
            if isinstance(doc_rep, dict):
                for e in doc_rep.get("external_refs") or []:
                    if isinstance(e, dict) and not e.get("exists"):
                        ev.append("missing: %s" % e.get("path"))
            raise StopVerdict("toolchain", 1, ev)

        # ② net（net_probe 双探稳窗·UNSTABLE 即停）
        verdict, rc = self.probe_stable(with_record=True)
        if verdict != "STABLE":
            raise StopVerdict("unstable", 1,
                              ["net_probe verdict=%s rc=%s（UNSTABLE·禁发射）"
                               % (verdict, rc)])

        # ③ 可选 gate4 预扫（FAIL=0 才放行）
        if a.pre_scan_gate4:
            self.gate4_prescan(pf)

    def probe_stable(self, with_record=False, source="preflight"):
        """net_probe --rounds 2 --interval S --stable-window（真子进程或 canned）
        → (verdict, rc)。verdict 须 STABLE|UNSTABLE。
        steps 形：tools.net_probe canned（{"verdict"} 或 {"report":{...}}）。
        flat 形：preflight 闸缺省绿（响亮注记一次）·heal 探针逐消耗
        canned.probe（net_probe 报告真形取 verdict）。"""
        a = self.args
        if self.injector_kind == "steps":
            np = self.scen_tools().get("net_probe") or {}
            if isinstance(np.get("report"), dict):
                verdict = np["report"].get("verdict")
                rc = np.get("rc", 0 if verdict == "STABLE" else 1)
            else:
                verdict, rc = np.get("verdict"), np.get("rc", 0)
            if verdict is None:
                raise PushciError("injector 场景缺 tools.net_probe.verdict", 2)
        elif self.injector_kind == "flat":
            if source == "preflight":
                verdict, rc = "STABLE", 0
                if not self._flat_gate_noted:
                    self._flat_gate_noted = True
                    self.report["evidence"].append(
                        "flat 注入形：preflight toolchain/net 双闸按缺省绿施"
                        "（flat 形未携闸 canned·测试契约形·真发射闸走 steps 形"
                        "或真模式）")
            else:
                lst = (self.scen.get("canned") or {}).get("probe") or []
                if self._flat_probe_i >= len(lst):
                    raise PushciError("flat 场景 canned.probe 耗尽（heal 探针 %d）"
                                      % (self._flat_probe_i + 1), 2)
                rep = lst[self._flat_probe_i]
                self._flat_probe_i += 1
                verdict = rep.get("verdict") if isinstance(rep, dict) else None
                if verdict not in ("STABLE", "UNSTABLE"):
                    raise PushciError("flat canned.probe 形坏（verdict=%r）"
                                      % (verdict,), 2)
                rc = 0 if verdict == "STABLE" else 1
        else:
            rc, rep, out = self._tool_report(
                PROBE_TOOL, ["--rounds", "2",
                             "--interval", str(float(a.probe_interval)),
                             "--stable-window"])
            verdict = rep.get("verdict") if isinstance(rep, dict) else None
            if verdict not in ("STABLE", "UNSTABLE"):
                raise PushciError("net_probe 报告形坏（verdict=%r）rc=%d: %s"
                                  % (verdict, rc, out[-200:]), 2)
        if with_record:
            pf = self.report["stages"].get("preflight")
            if pf is not None:
                pf["net"] = {"verdict": verdict, "rc": rc}
        return verdict, rc

    def gate4_prescan(self, pf):
        """git diff --name-only <base>...<branch> → .v 变更件 → gate4 守卫逐件
        （--file·真子进程·两态 rc 0=PASS/1=FAIL/2=复核）→ FAIL=0 才放行。"""
        a = self.args
        rc, out, err = self.git(["-C", a.repo_path, "diff", "--name-only",
                                 "%s...%s" % (a.base_ref, a.branch)])
        if rc != 0:
            raise PushciError("git diff 失败 rc=%d: %s" % (rc, err.strip()[:160]), 9)
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
                raise PushciError("gate4 守卫形外退出 rc=%d: %s" % (rc, out[-160:]), 2)
        pf["gate4"] = {"files": sorted(files), "pass_files": pass_files,
                       "fail_files": fail_files, "review_files": review_files,
                       "skipped_missing": sorted(skipped),
                       "fail_count": len(fail_files)}
        if skipped:
            self.report["evidence"].append(
                "gate4 预扫跳过缺失件 %d（分支删除件无面可扫·响亮在册）: %s"
                % (len(skipped), ",".join(sorted(skipped))))
        if review_files:
            self.report["evidence"].append(
                "gate4 REVIEW=%d（复核级不拦·人工可阅）: %s"
                % (len(review_files), ",".join(review_files)))
        if fail_files:
            raise StopVerdict("gate4-block", 2,
                              ["gate4 FAIL=%d（FAIL=0 才放行）: %s"
                               % (len(fail_files), ",".join(fail_files))])

    # -- 段 2：push ------------------------------------------------------------

    def stage_push(self):
        a = self.args
        rec = {"sha": None, "remote": a.remote, "url_masked": None,
               "attempts": [], "ghproxy_used": False}
        self.report["stages"]["push"] = rec
        rc, out, err = self.git(["-C", a.repo_path, "rev-parse", "--verify",
                                 "refs/heads/%s" % a.branch])
        if rc != 0:
            raise PushciError("分支缺失: refs/heads/%s（%s）"
                              % (a.branch, err.strip()[:120]), 9)
        sha_local = out.strip().split()[0] if out.strip() else ""
        if not sha_local:
            raise PushciError("rev-parse 空输出（refs/heads/%s）" % a.branch, 9)
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
                    "ghproxy 换路不适用（remote URL 非 https://%s/ 形：%s）"
                    % (GHPROXY_HOST, mask_text(self.remote_url, self.masks)))
        if not ok:
            route = "直路 %d 发" % PUSH_TRIES
            if rec["ghproxy_used"]:
                route += "＋ghproxy %d 发" % GHPROXY_TRIES
            raise StopVerdict("unstable", 1,
                              ["push 全败（%s）·rc 逐发在册 stages.push.attempts"
                               % route])
        # ls-remote 复核（承 watch.py「真 rc＋ls-remote 复核」纪律·第 4 git 调）：
        # pushed_sha＝远端 tip（CI 构的是远端 tip·远端为准）；异于本地 tip 响亮注记。
        rc, out, err = self.git(["-C", a.repo_path, "ls-remote", a.remote,
                                 "refs/heads/%s" % a.branch])
        if rc != 0 or not out.strip():
            raise PushciError("push 后 ls-remote 复核失败 rc=%d（远端 tip 不可证）:"
                              " %s" % (rc, err.strip()[:120]), 9)
        sha_remote = out.strip().split()[0]
        if not re.match(r"^[0-9a-fA-F]{40}$", sha_remote):
            raise PushciError("ls-remote 输出非 40 位 sha 形: %r"
                              % mask_text(sha_remote, self.masks), 9)
        rec["sha"] = sha_remote
        if sha_remote.lower() != sha_local.lower():
            self.report["evidence"].append(
                "push 后 ls-remote sha 与本地 rev-parse tip 异（远端为准·watch "
                "锚远端 tip）")

    def _push_tries(self, cmd, tries, attempts_log, target_label):
        for i in range(tries):
            rc, out, err = self.git(cmd)
            attempts_log.append({"target": target_label, "rc": rc})
            if rc == 0:
                return True
            if i < tries - 1:
                sleep_scaled(PUSH_RETRY_WAIT, self.args.sleep_scale)
        return False

    # -- 段 3：resolve+watch（含段 4 heal 循环）---------------------------------

    def stage_watch(self):
        a = self.args
        push_rec = self.report["stages"].get("push") or {}
        sha = push_rec.get("sha")
        if not sha:
            raise PushciError("watch 依赖 pushed_sha（push 段未跑或未成）", 2)
        watch = {"run_tag": None, "run_id": None, "rounds": 0,
                 "conclusion": None, "policy": WATCH_POLICY}
        self.report["stages"]["watch"] = watch
        heal = {"rounds": [], "fired_total": 0, "last_triage": None}
        if "heal" in a.steps:
            self.report["stages"]["heal"] = heal   # 常在（rounds＝fired 账·绿则空）
        while True:
            self.round_no += 1
            watch["rounds"] = self.round_no
            if a.watch_max_rounds and self.round_no > a.watch_max_rounds:
                raise PushciError("watch 轮帽达（--watch-max-rounds=%d）·run 仍未 "
                                  "completed" % a.watch_max_rounds, 9)
            status, body = self.api("GET", self.runs_path(),
                                    round_no=self.round_no)
            if status != 200:
                raise PushciError("GET runs HTTP %d: %s"
                                  % (status, snippet(body)), 9)
            runs = None
            if isinstance(body, dict):
                runs = body.get("workflow_runs")   # GitHub API 真形
                if runs is None:
                    runs = body.get("runs")        # watch.py --runs-json 证据形
            if not isinstance(runs, list):
                raise PushciError("runs API 形坏（无 workflow_runs/runs 列表）", 9)
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
                                  ["watch 观测红（conclusion=%s）·heal 段未选"
                                   "（--steps 裁剪）·禁自动处置·人工分诊"
                                   % conclusion])
            if len(heal["rounds"]) >= a.max_heal:
                raise StopVerdict("heal-exhausted", 1,
                                  ["heal 帽达（--max-heal=%d·已 %d 轮）"
                                   % (a.max_heal, len(heal["rounds"]))])
            self.heal_round(run, heal)
            sleep_scaled(a.watch_interval, a.sleep_scale)

    def heal_round(self, run, heal):
        """单轮 heal：ci_triage 判类（真子进程）→ family 分派 → rerun 或裁停。
        heal.rounds＝fired 重跑账（B/E 实动轮入册·A/C/表外裁停零轮·零 rerun
        实证）；历次判类 outcome 全量在 heal.last_triage。"""
        t_rep = self.run_triage(run.get("id"))
        heal["last_triage"] = {"family": t_rep.get("family"),
                               "action": t_rep.get("action"),
                               "evidence": list(t_rep.get("evidence") or [])}
        fam = t_rep.get("family")
        if fam not in HEAL_RERUN_FAMILIES:
            if fam == "A-content-red":
                raise StopVerdict("fix-content", 2,
                                  ["heal: family=A-content-red（内容红·禁代修——"
                                   "修复是席/人职责）·判类证据在册 stages.heal."
                                   "last_triage.evidence·零 rerun"])
            if fam == "C-toolchain-break":
                raise StopVerdict("toolchain", 1,
                                  ["heal: family=C-toolchain-break（环境断链）·"
                                   "建议重跑 python3 tools/"
                                   "toolchain_dyld_doctor.py 复诊（只诊断＋"
                                   "restore 建议·禁代执行）·判类证据在册 "
                                   "stages.heal.last_triage.evidence"])
            raise StopVerdict("fix-content", 2,
                              ["heal: family=%s（heal 分派表外〔B/E/A/C 之外〕·"
                               "禁自动 rerun·人工指认·family 原值在册 last_triage）"
                               % fam])
        entry = {"round": len(heal["rounds"]) + 1, "family": fam,
                 "action": t_rep.get("action"), "probe": None, "fired": False,
                 "http": None, "evidence": list(t_rep.get("evidence") or [])}
        heal["rounds"].append(entry)
        verdict, _rc = self.probe_stable(source="heal")
        entry["probe"] = verdict
        if verdict != "STABLE":
            raise StopVerdict("unstable", 1,
                              ["heal round %d: probe=%s（禁发射律·UNSTABLE 不 "
                               "rerun）" % (entry["round"], verdict)])
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
                "rerun POST 403（already running 形）幂等接受·回 watch")
        else:
            raise PushciError("rerun POST HTTP %d: %s"
                              % (status, snippet(body)), 9)
        heal["fired_total"] = sum(1 for r in heal["rounds"] if r["fired"])

    def run_triage(self, run_id):
        """ci_triage 子进程：线上 --repo --run（token 走 --netrc 透传）或
        injector 模式 --offline canned jobs（真子进程真判类·零网络）。"""
        fd, out_json = tempfile.mkstemp(prefix="pushci_triage_")
        os.close(fd)
        jobs_path = None
        try:
            if self.scen is not None:
                jobs = self._next_jobs()
                if not isinstance(jobs, dict):
                    raise PushciError("injector 场景缺 canned jobs（ci_triage "
                                      "形 {\"total_count\":N,\"jobs\":[...]}）", 2)
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
                raise PushciError("ci_triage 失败 rc=%d: %s" % (rc, out[-200:]), 9)
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

    # -- 段 5：merge ------------------------------------------------------------

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
                raise PushciError("无 open PR（head=%s:%s·目标缺失）"
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
                                      ["merge 409×%d（重试帽 ≤%d）·PR #%s 冲突"
                                       "·人工解（verdict=fix-content）"
                                       % (i + 1, MERGE_409_RETRIES, pr)])
                bs, bb = self.api("GET", "/repos/%s/branches/main" % self.repo,
                                  round_no=self.round_no)
                if bs == 200 and isinstance(bb, dict):
                    rec["main_tip"] = (bb.get("commit") or {}).get("sha")
                self.report["evidence"].append(
                    "merge 409（attempt %d）→ GET branches/main 重拉 tip=%s → "
                    "歇 %ds 重试" % (i + 1, rec["main_tip"], MERGE_409_WAIT))
                sleep_scaled(MERGE_409_WAIT, a.sleep_scale)
                continue
            raise PushciError("merge PUT HTTP %d: %s" % (status, snippet(body)), 9)

    # -- dry-run ----------------------------------------------------------------

    def run_dry(self):
        a = self.args
        plan = []
        if "preflight" in a.steps:
            plan.append("[1] preflight.toolchain: python3 tools/"
                        "toolchain_dyld_doctor.py（--worker 缺省探测·gate "
                        "verdict=healthy）")
            plan.append("[1] preflight.net: python3 tools/net_probe.py --rounds 2"
                        " --interval %g --stable-window（gate STABLE）"
                        % a.probe_interval)
            if a.pre_scan_gate4:
                plan.append("[1] preflight.gate4: git -C <repo> diff --name-only "
                            "%s...%s → .v 件 → python3 verify/"
                            "gate4_comment_guard.py --file（gate FAIL=0）"
                            % (a.base_ref, a.branch))
            else:
                plan.append("[1] preflight.gate4: 未启（--pre-scan-gate4 未给）")
        if "push" in a.steps:
            plan.append("[2] push: git -C <repo> -c http.version=%s push %s %s"
                        "（重试 %d 发×%ds；三败且 remote host=%s → ghproxy 换路 "
                        "%d 发）" % (PUSH_HTTP_VERSION, a.remote, a.branch,
                                     PUSH_TRIES, PUSH_RETRY_WAIT, GHPROXY_HOST,
                                     GHPROXY_TRIES))
        if "watch" in a.steps:
            plan.append("[3] watch: GET /repos/<org/repo>%s（head_branch=%s 且 "
                        "head_sha=<pushed_sha>·间隔 %gs·%s 至 completed）"
                        % (RUNS_QUERY, a.branch, a.watch_interval, WATCH_POLICY))
        if "heal" in a.steps:
            plan.append("[4] heal: python3 tools/ci_triage.py --repo <org/repo> "
                        "--run <id>（帽 %d）→ B/E→probe+rerun（403 幂等接受）·"
                        "A→fix-content 停·C→toolchain 停·表外→人工"
                        % a.max_heal)
        plan.append("[5] verdict: report schema %s·退出码 0/1/2/9" % SCHEMA)
        if a.merge:
            plan.append("[5] merge: GET /pulls?head=<owner>:%s&state=open（%s）"
                        "→ PUT /pulls/{{n}}/merge（%s·409→GET branches/main 歇 "
                        "%ds 重试 ≤%d）"
                        % (a.branch, ("--pr %d 显传" % a.pr) if a.pr
                           else "解 PR 号", a.merge_method, MERGE_409_WAIT,
                           MERGE_409_RETRIES))
        self.report["plan"] = plan
        return "dry-run", 0, []

    # -- 主驱动 -------------------------------------------------------------------

    def run(self):
        a = self.args
        if a.dry_run:
            return self.run_dry()
        if "push" in a.steps or "watch" in a.steps:
            # remote URL：push 段（ghproxy 决策）与 watch 段（repo 推导）所需——
            # 纯 preflight 模式零 git 调
            rc, out, err = self.git(["-C", a.repo_path, "remote", "get-url",
                                     "--push", a.remote])
            if rc != 0:
                raise PushciError("远端缺失: %s（%s）"
                                  % (a.remote, err.strip()[:120]), 9)
            self.remote_url = out.strip()
            self.repo = repo_from_url(self.remote_url)
            if not self.repo:
                raise PushciError(
                    "remote URL 路径无法推导 ORG/REPO（末两段）: %s"
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

    # -- 出账 ---------------------------------------------------------------------

    def dump_canned_logs(self):
        """注入模式调用流水落盘（测试实证面·尽力而为不遮主错）。"""
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
        """终局裁定＋出账（verdict 段被选时渲染 stdout＋落 --json）。"""
        if verdict not in VERDICT_EXIT:
            raise PushciError("内部错误：verdict 越册 %r" % (verdict,), 2)
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
    """stdout 出账（全数据驱动·零墙钟·确定性）。"""
    print("=== ROCQWASH PUSHCI（修复后推送 CI 一键流水线·v36 旗舰）===")
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
        print("run=%s rounds=%d conclusion=%s（%s）"
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


# ---- 校验 ---------------------------------------------------------------------

def validate(args):
    """用法校验（fail-loud 2）＋目标校验（fail-loud 9）·全部副作用之前。"""
    steps = []
    for s in args.steps.split(","):
        s = s.strip()
        if s and s not in steps:
            steps.append(s)
    if not steps:
        raise PushciError("--steps 展开后为空", 2)
    unknown = [s for s in steps if s not in STAGE_ALL]
    if unknown:
        raise PushciError("--steps 未知段: %s（册：%s）"
                          % (",".join(unknown), ",".join(STAGE_ALL)), 2)
    args.steps = steps
    if "watch" in steps and "push" not in steps:
        raise PushciError("段依赖：watch⇒push（watch 需 pushed_sha）", 2)
    if "heal" in steps and "watch" not in steps:
        raise PushciError("段依赖：heal⇒watch", 2)
    if args.merge and "watch" not in steps:
        raise PushciError("段依赖：--merge⇒watch（merge 须绿后施）", 2)
    if args.max_heal < 0:
        raise PushciError("--max-heal 须≥0 实测 %d" % args.max_heal, 2)
    if args.watch_interval < 0:
        raise PushciError("--watch-interval 须≥0 实测 %s" % args.watch_interval, 2)
    if args.probe_interval < 0:
        raise PushciError("--probe-interval 须≥0 实测 %s" % args.probe_interval, 2)
    if args.watch_max_rounds < 0:
        raise PushciError("--watch-max-rounds 须≥0 实测 %d" % args.watch_max_rounds, 2)
    if args.sleep_scale < 0:
        raise PushciError("--sleep-scale 须≥0 实测 %s" % args.sleep_scale, 2)
    if args.timeout < 1:
        raise PushciError("--timeout 须≥1 实测 %d" % args.timeout, 2)
    if args.retry_max < 0:
        raise PushciError("--retry-max 须≥0 实测 %d" % args.retry_max, 2)
    if args.pr is not None and args.pr < 1:
        raise PushciError("--pr 须≥1 实测 %d" % args.pr, 2)
    if (args.injector is None) != (args.git_caller is None):
        raise PushciError("--injector 与 --git-caller 须成对（injector 无 canned "
                          "git＝真 push 危险）", 2)
    # 目标校验（9）·先于 --branch 必给校验（2）——repo 缺失债 9 优先口径
    if not args.repo_path:
        raise PushciError("--repo-path 必给", 2)
    if not os.path.isdir(args.repo_path):
        raise PushciError("仓库目录缺失: %s" % args.repo_path, 9)
    if not args.branch:
        raise PushciError("--branch 必给", 2)
    if args.injector:
        if not os.path.isdir(args.injector):
            raise PushciError("injector 目录缺失: %s" % args.injector, 9)
        if not os.path.isfile(os.path.join(args.injector, "scenario.json")) \
                and not os.path.isdir(os.path.join(args.injector, "runs")):
            raise PushciError("injector 场景缺失（scenario.json 或 runs/ 平铺"
                              "目录）: %s"
                              % os.path.join(args.injector, "scenario.json"), 9)
    if args.git_caller and not os.path.isfile(args.git_caller):
        raise PushciError("git-caller 场景缺失: %s" % args.git_caller, 9)


# ---- 自测（--selftest·八矢量＋单元＋CLI 四码·零真网络零真 push 零编译）----------

def selftest():
    """内嵌冻结向量组（--injector canned＋--git-caller canned＋--sleep-scale 0）：
    ①绿径 preflight→push→success（含确定性字节恒同）
    ②NETRED×1 愈合→attempt2 success（heal_rounds=1·真 ci_triage --offline 判 B）
    ③内容红停（A 族·零 rerun 实证·exit 2）
    ④heal×3 耗尽 exit 1（POST=3·GET=4）
    ⑤merge 200 流
    ⑥409→重拉 tip→200
    ⑦dry-run 计划零副作用（git/API 调用流水皆空）
    ⑧gate4-block 停（真 gate4 守卫·clean PASS＋dirty FAIL·零 push）
    ＋单元（repo 推导/ghproxy 形/遮蔽/netrc/verdict 封册）＋CLI 四码。
    全矢量 --netrc 故意指向不存在路径——凭据惰性读证（任何真 API 企图即 9）。"""
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
        """canned git 序列＝pushci 实调序：get-url→rev-parse→push→ls-remote。"""
        return [{"args_contains": ["get-url"], "rc": 0, "stdout": url + "\n"},
                {"args_contains": ["rev-parse"], "rc": 0,
                 "stdout": rev_sha + "\n"},
                {"args_contains": ["push"], "rc": push_rc,
                 "stdout": "To %s\n" % url},
                {"args_contains": ["ls-remote"], "rc": 0,
                 "stdout": "%s\trefs/heads/work\n" % ls_sha}]

    tmp = tempfile.mkdtemp(prefix="rocqwash_pushci_self_")
    try:
        netrc_missing = os.path.join(tmp, "no_such.netrc")  # 惰性凭据读证

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
            """flat 形注入目录：并行席夹具原件 verbatim → scenario.json。"""
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

        # 〔一〕绿径 preflight→push→success（①）
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
        assert "repo_path" not in rep["args"], "报告零本地路径（幂等契约）"
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
        # 确定性：同输入重跑 --json 字节级恒同
        out2 = s["out"] + ".2"
        rc, out = fire(s, json_path=out2)
        assert rc == 0, out[-300:]
        assert io.open(out2, "rb").read() == io.open(s["out"], "rb").read(), \
            "json 字节漂移＝违例"

        # 〔一b〕远端为准：ls-remote sha 与本地 rev-parse tip 异→响亮注记·
        # watch 仍锚 ls-remote sha（canned runs head_sha 咬合）
        s = setup("v1b_remote_tip",
                  git_common(rev_sha="b" * 40, ls_sha=SHA40),
                  poll_steps(["success"]))
        rc, out = fire(s)
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["stages"]["push"]["sha"] == SHA40, rep["stages"]["push"]
        assert any("远端为准" in e for e in rep["evidence"]), rep["evidence"]

        # 〔二〕NETRED×1 愈合→attempt2 success（②·真 ci_triage --offline 判 B）
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

        # 〔三〕内容红停（③·零 rerun 实证·exit 2）
        s = setup("v3_content", git_common(), poll_steps(["failure"]),
                  jobs=jobsA)
        rc, out = fire(s)
        assert rc == 2, "内容红应 exit 2 实测 %d\n%s" % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "fix-content"
        h = rep["stages"]["heal"]
        assert h["rounds"] == [] and h["fired_total"] == 0, \
            "零 rerun 实证＝heal.rounds 空·实测 %r" % (h,)
        assert h["last_triage"]["family"] == "A-content-red" \
            and h["last_triage"]["action"] == "fix-content", h["last_triage"]
        assert h["last_triage"]["evidence"], "判类证据应在册 last_triage"
        acalls = jload(s["api_calls"])
        assert all(c["method"] != "POST" for c in acalls), "零 rerun 实证失守"
        assert any("禁代修" in e for e in rep["evidence"]), rep["evidence"]
        assert json.dumps(rep["stages"], sort_keys=True).count("rerun") == 0, \
            "内容红 stages 面零 rerun 形（跨席咬合契约）"

        # 〔四〕heal×3 耗尽 exit 1（④）
        s = setup("v4_exhaust", git_common(),
                  poll_steps(["failure"] * 4, rerun_rounds=3), jobs=jobsB)
        rc, out = fire(s, ["--max-heal", "3"])
        assert rc == 1, "heal 耗尽应 exit 1 实测 %d\n%s" % (rc, out[-400:])
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

        # 〔五〕merge 200 流（⑤）
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

        # 〔六〕409→重拉 tip→200（⑥）
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

        # 〔七〕dry-run 计划零副作用（⑦）
        s = setup("v7_dryrun", [], [])
        rc, out = fire(s, ["--dry-run", "--pre-scan-gate4"])
        assert rc == 0, out[-500:]
        rep = jload(s["out"])
        assert rep["verdict"] == "dry-run" and rep["mode"] == "dry-run"
        assert rep["stages"] == {} and rep.get("plan"), rep
        assert any("push" in ln and "HTTP/1.1" in ln for ln in rep["plan"]), \
            rep["plan"]
        assert any("gate4" in ln for ln in rep["plan"]), rep["plan"]
        assert jload(s["git_calls"]) == [], "dry-run 零 git 调用实证失守"
        assert jload(s["api_calls"]) == [], "dry-run 零 API 调用实证失守"
        assert "PLAN [2] push" in out, out[-300:]

        # 〔八〕gate4-block 停（⑧·真 gate4 守卫·clean PASS＋dirty FAIL·零 push）
        s = setup("v8_gate4",
                  [{"args_contains": ["get-url"], "rc": 0,
                    "stdout": "https://github.com/org/repo.git\n"},
                   {"args_contains": ["diff"], "rc": 0,
                    "stdout": "clean.v\ndirty.v\n"}], [])
        with io.open(os.path.join(s["repo"], "clean.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("(* 使命: pushci selftest clean fixture.\n"
                     "   依赖: 无.\n   对标: 无.\n"
                     "   构造性: 无公理构造.\n   编译配方: coqc clean.v *)\n"
                     "Definition pushci_clean_unit : nat := 1.\n")
        with io.open(os.path.join(s["repo"], "dirty.v"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("Definition pushci_dirty_unit : nat := 1.\n")
        rc, out = fire(s, ["--pre-scan-gate4"])
        assert rc == 2, "gate4-block 应 exit 2 实测 %d\n%s" % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "gate4-block"
        g4 = rep["stages"]["preflight"]["gate4"]
        assert g4["fail_count"] == 1, g4
        assert g4["fail_files"] == [os.path.join(s["repo"], "dirty.v")], g4
        assert os.path.join(s["repo"], "clean.v") in g4["pass_files"], g4
        assert os.path.join(s["repo"], "clean.v") not in g4["fail_files"], g4
        gcalls = jload(s["git_calls"])
        assert len(gcalls) == 2, "gate4-block 应零 rev-parse 零 push: %s" % gcalls
        assert jload(s["api_calls"]) == [], "gate4-block 应零 API 调用"

        # 〔九〕flat 注入形绿径（并行席夹具 s1_green_path.json 原件 verbatim 直跑
        # ·pushci.invalid 假域推导·双闸缺省绿·canned.runs 双 poll）
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
        assert any("flat 注入形" in e for e in rep["evidence"]), rep["evidence"]
        assert len(jload(s["api_calls"])) == 2
        assert len(jload(s["git_calls"])) == 4

        # 〔十〕flat 注入形 NETRED 愈合（s2_netred_heal.json 原件直跑·真 triage
        # --offline 吃 canned.jobs[0]·canned.probe/rerun 逐消耗）
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

        # 〔十一〕ghproxy 换路：直路 3 败→ghproxy 首发成（verdict success·
        # attempts=[origin rc1×3, ghproxy rc0]·ghproxy_used=True）
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

        # 〔十二〕push 全败（直路 3 发＋ghproxy 2 发皆红）→ unstable exit 1
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
        assert rc == 1, "push 全败应 exit 1 实测 %d\n%s" % (rc, out[-400:])
        rep = jload(s["out"])
        assert rep["verdict"] == "unstable"
        push = rep["stages"]["push"]
        assert [a["rc"] for a in push["attempts"]] == [1, 1, 1, 1, 1], push
        assert any("push 全败" in e for e in rep["evidence"]), rep["evidence"]

        # 〔单元〕repo 推导/ghproxy 形/遮蔽/netrc/verdict 封册（零网络）
        assert repo_from_url("https://github.com/octo/rocq.git") == "octo/rocq"
        assert repo_from_url("https://tok@github.com/octo/rocq") == "octo/rocq"
        assert repo_from_url("git@github.com:octo/rocq.git") == "octo/rocq"
        assert repo_from_url("ssh://git@github.com/octo/rocq.git") == "octo/rocq"
        assert repo_from_url("https://gitlab.com/o/r.git") == "o/r", \
            "host 不限（假域 shim 远端同推导·ghproxy 另有形门）"
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
        assert netrc_token(nf) == "TOK-1234", "单行 6 列形应取第 6 列"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine github.com\nlogin octocat\npassword TOK-9\n")
        assert netrc_token(nf) == "TOK-9", "多行形应同解析"
        try:
            netrc_token(os.path.join(tmp, "absent.netrc"))
            assert False, "缺 netrc 应 fail-loud"
        except PushciError as e:
            assert e.code == 9, e.code
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine gitlab.com login x password Y\n")  # 覆写成无 github 形
        try:
            netrc_token(nf)
            assert False, "无 github.com 条目应 fail-loud"
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

        # 〔韧性层〕退避序列＋Retry-After 尊重＋真 urllib _api 重试 runner＋
        # 子进程超时杀（零网络零真 push·_urlopen/_sleep 注入·判例 403×3→[2,4,8]）
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        assert _http_backoff.parse_retry_after("45") == 45.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, "HTTP-date 不猜"

        class _Resp(object):
            """canned 响应体（urlopen 假件·零网络·上下文管理器形）。"""
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
                    raise r          # canned 错件须抛（urlopen 同语义）
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
            (code, slept)                      # Retry-After 头尊重（替指数）
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(429)] * 4),
                       _sleep=slept.append)
        code, body = ac("GET", "/repos/o/r/x")
        assert code == 429 and slept == [2.0, 4.0, 8.0], \
            (code, slept)                      # 耗尽原码上交语义裁决
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(401)]), _sleep=slept.append)
        code, body = ac("GET", "/repos/o/r/x")
        assert code == 401 and slept == [], (code, slept)   # 401 不重试
        slept = []
        ac = ApiClient(netrc_path=api_netrc, retry_max=3, sleep_scale=0,
                       _urlopen=_seq_open([_api_err(409)]), _sleep=slept.append)
        code, body = ac("PUT", "/repos/o/r/pulls/1/merge")
        assert code == 409 and slept == [], (code, slept)   # merge 409 不重试

        # 子进程超时杀（canned sleep 子进程·fail-loud 9 报调用名）
        sleepy = os.path.join(tmp, "sleepy_pushci.py")
        with io.open(sleepy, "w", encoding="utf-8") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        try:
            subproc_run([sys.executable, "-B", sleepy], 2,
                        "canned-sleep 子进程")
            assert False, "超时应 fail-loud 9"
        except PushciError as e:
            assert e.code == 9 and "canned-sleep" in str(e) \
                and "2s" in str(e), e
        p = subproc_run([sys.executable, "-B", "-c", "print('fast')"], 10,
                        "fast-proc")
        assert p.returncode == 0, p.returncode

        # 〔CLI 四码〕（真模式·全部在副作用之前 fail-loud）
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
        assert p == 2, "未知形参应 rc=2 实测 %d" % p
        p, o = raw([])
        assert p == 2, "缺必给应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", os.path.join(tmp, "no_repo"),
                    "--branch", "x"])
        assert p == 9, "缺仓库应 rc=9 实测 %d" % p
        p, o = raw(["--repo-path", os.path.join(tmp, "no_repo")])
        assert p == 9, "repo 缺失优先 9（branch 未给不遮蔽）实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "bogus"])
        assert p == 2, "未知段应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "watch"])
        assert p == 2, "watch⇒push 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--steps", "heal"])
        assert p == 2, "heal⇒watch 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x", "--merge",
                    "--steps", "preflight,push"])
        assert p == 2, "merge⇒watch 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--sleep-scale", "-1"])
        assert p == 2, "负 sleep-scale 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--timeout", "0"])
        assert p == 2, "timeout<1 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--retry-max", "-1"])
        assert p == 2, "负 retry-max 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--max-heal", "-1"])
        assert p == 2, "负 max-heal 应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--merge-method", "rebase"])
        assert p == 2, "merge-method 册外应 rc=2 实测 %d" % p
        inj = os.path.join(tmp, "v1_green", "inj")
        gitj = os.path.join(tmp, "v1_green", "git.json")
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--injector", inj])
        assert p == 2, "injector 单边应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--git-caller", gitj])
        assert p == 2, "git-caller 单边应 rc=2 实测 %d" % p
        p, o = raw(["--repo-path", empty_repo, "--branch", "x",
                    "--injector", os.path.join(tmp, "no_inj"),
                    "--git-caller", gitj])
        assert p == 9, "injector 目录缺失应 rc=9 实测 %d" % p

        print("PUSHCI-SELFTEST PASS: 八矢量（绿径+确定性字节恒同+远端为准/NETRED×1 "
              "愈合/内容红零 rerun/heal×3 耗尽/merge 200/409 重拉/dry-run 零副作用/"
              "gate4-block 真守卫）＋flat 咬合双矢（并行席 s1/s2 夹具原件 verbatim "
              "直跑）＋重试纪律双矢（ghproxy 换路成/push 全败 unstable）＋单元（repo "
              "推导/ghproxy/遮蔽/netrc/verdict 封册）＋韧性层（退避 403×3→[2,4,8]·"
              "Retry-After 尊重·429 耗尽上交·401/409 不重试·canned sleep 子进程"
              "超时杀 9 报调用名）＋CLI 四码 全过（零真网络零真 "
              "push 零编译·--netrc 惰性读证）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- 主流程 -------------------------------------------------------------------

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
        description="修复后推送 CI 一键流水线（preflight 发射闸→push→watch→"
                    "heal→verdict±merge·v35 四器编排·离线可测注入点内建）")
    ap.add_argument("--repo-path", default=None, metavar="DIR",
                    help="目标仓库目录（零硬编码·全参数化）")
    ap.add_argument("--branch", default=None, metavar="B",
                    help="要推送与观测的分支")
    ap.add_argument("--base-ref", default="main", metavar="REF",
                    help="gate4 预扫 diff 基（<base>...<branch>·默认 main）")
    ap.add_argument("--remote", default="origin", metavar="NAME",
                    help="推送远端名（默认 origin）")
    ap.add_argument("--pre-scan-gate4", action="store_true",
                    dest="pre_scan_gate4",
                    help="preflight 加做 gate4 头注守卫预扫（FAIL=0 才放行）")
    ap.add_argument("--pr", type=int, default=None, metavar="N",
                    help="PR 号显传（--merge 时跳过 pulls 解析）")
    ap.add_argument("--merge", action="store_true",
                    help="绿后合并 PR（缺省 merge 方式）")
    ap.add_argument("--merge-method", choices=("merge", "squash"),
                    default="merge", dest="merge_method",
                    help="合并方式（默认 merge〔分支含 merge commit 判例〕）")
    ap.add_argument("--max-heal", type=int, default=3, metavar="N",
                    help="heal 轮帽（默认 3·超帽 heal-exhausted）")
    ap.add_argument("--watch-interval", type=float, default=150.0, metavar="S",
                    help="watch 轮询间隔秒（默认 150）")
    ap.add_argument("--probe-interval", type=float, default=60.0, metavar="S",
                    help="net_probe 轮间隔秒（默认 60）")
    ap.add_argument("--watch-max-rounds", type=int, default=0, metavar="N",
                    help="watch 轮帽安全阀（默认 0=不限·超帽 fail-loud 9）")
    ap.add_argument("--timeout", type=int, default=120, metavar="S",
                    help="子进程防挂超时秒（默认 120·git/四器工具真子进程超时"
                         "=杀＋fail-loud 9 报调用名）")
    ap.add_argument("--retry-max", type=int, default=3, metavar="N",
                    help="真 urllib API 403/429/5xx 退避重试帽（默认 3·指数 "
                         "base 2s·Retry-After 秒数头尊重·canned 路径不重试）")
    ap.add_argument("--steps", default=",".join(STAGE_ALL), metavar="LIST",
                    help="段独选（默认全跑：%s）" % ",".join(STAGE_ALL))
    ap.add_argument("--injector", default=None, metavar="DIR",
                    help="离线注入：DIR/scenario.json 场景（steps[].at_round→"
                         "canned API＋tools canned＋jobs canned）")
    ap.add_argument("--git-caller", default=None, metavar="FILE",
                    dest="git_caller",
                    help="离线注入：canned git 响应场景（须与 --injector 成对）")
    ap.add_argument("--sleep-scale", type=float, default=1.0, metavar="F",
                    help="全部 sleep 乘数（selftest 用 0＝零真睡）")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc 路径（默认 ~/.netrc·machine github.com 第 6 列"
                         "=token·惰性读·injector 模式零读）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="report 出账（rocqwash-pushci/1·sort_keys）")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run",
                    help="只打计划零副作用 exit 0")
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
        print("FAIL-LOUD: 场景装载失败: %s" % e, file=sys.stderr)
        sys.exit(9)

    try:
        verdict, code, ev = pl.run()
    except StopVerdict as sv:
        verdict, code, ev = sv.verdict, sv.code, sv.evidence
        # 裁停恒响亮（verdict 段未选时 stdout 不出账·stderr 仍必报——禁哑退出）
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
