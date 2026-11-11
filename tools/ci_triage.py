#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ci_triage.py — CI 红炉分诊器（rocqwash tools/·20261110 判类谱代码化·六幕实战判例工具化）

[判类谱]（20261110 六幕实战判例·全部代码化；五族＋绿炉）：
  A 内容红 A-content-red＝失败步指向具体件：Build/COQCHK 出 Error:/FAIL/
    ORDER-MISSING/Axioms 非零（COQCHK_EXIT≠0·公理总数≠0）→ action=fix-content。
  B 网络窗 B-netred＝checkout unable to access / port 443 / Connection was reset；
    上传步 ENOTFOUND / Upload progress stalled；403 Forbidden: job is completed
    （中断连坐形：cancelled 有步骤零红步同归此族）→ action=rerun-after-stable-window。
  C 环境断链 C-toolchain-break＝批量 EXIT=134 / Abort trap: 6（SKIP 件全过）。
    log 直证：日志抓到 EXIT=134/Abort trap: 6 → 该 job 即 C；run 级批量判：
    同形内容红（A）≥2 件 → 全数升 C（EXIT=134 日志确证建议 --logs）
    → action=restore-toolchain。
  D 排队资源墙 D-queue-wall＝cancelled 且 steps=[]（job 零步骤·logs 404）
    → action=queue-etiquette。
  E coqchk-skipped 签名 E-coqchk-skipped＝上传步红＋coqchk 步 skipped（＋gate2
    GATE-BANNER-ABSENT 日志确证）＝B 族变体·勿当内容红
    → action=rerun-after-stable-window。
  E 变体（gate2-only 连坐形·20261112 Main retro 六事件证据人工指认入谱）＝
    红步集 ⊆ {gate2＋上传族} 且纯 gate2 红步在册（gate2 名非上传名——防
    「Upload artifact (gate2 ledger)」gate2 子串词面搭便误吞上传红）·前置
    build/coqchk 非 content 红＝「coqchk 产物缺·gate2 连坐」（GATE-BANNER-ABSENT
    同义·run#7 job 127903477736 日志 200 实测确证在册）＝E 族内变体
    → family=E-coqchk-skipped·action=rerun-after-stable-window。
    判类谱序 UNRECOGNIZED>C>A>E>B>D 不动（E 变体在 E 内·出处六事件中
    #7/#8/#10/#20/#26 五发 gate2-only 形入谱·#3 runner 失联形仍谱外不充谱）。
  绿炉＝无红件 → family=none·action=watch-only。在飞/条件跳过（conclusion 空或
    skipped/neutral）同记 none·但 evidence 显式注记「判类暂缓非绿判」·绝不充绿。
  判类谱外红形 → family=UNRECOGNIZED·action=watch-only（不充谱·run 级判类序
    置顶·人工指认优先·fail-loud）。

  判类序（逐 job·先到先归）：绿/在飞/条件跳过 → D（cancelled·零步骤）→ B 连坐形
  （cancelled·有步骤零红步）→ log 直证 C（EXIT=134/Abort trap: 6）→ E 签名
  （上传红＋coqchk skipped）→ E 变体（gate2-only 连坐：红步集 ⊆ {gate2+上传族}·
  build/coqchk 非 content 红）→ log B → 步名 B（checkout/upload/artifact/cache/…）
  → log A（Error:/FAIL/ORDER-MISSING/COQCHK_EXIT≠0/公理总数≠0）→ 步名 A
  （build/compile/coqchk/…）→ UNRECOGNIZED。

用途：
  对 GitHub Actions run 的 jobs 做红/绿分诊：打印步级表（步名/status/conclusion/
  起止/时长秒），逐 job 归族（family）并给处置（action）；--baseline-seconds 给
  同 sync 历史时长值则出倍数对表（判例 coqchk 561s vs 7480s=13.3x＝本机挤压
  嫌疑非卡死）。红是数据非器红：分诊恒 exit 0 响亮出账。

用法（路径全参数化·零硬编码绝对路径）：
  线上模式（只读 GET·token 取 ~/.netrc machine github.com 行第 6 列 password，
  --netrc 可换路径）：
    python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs] [--netrc PATH]
        [--baseline-seconds N] [--baseline-step NAME] [--timeout S]
        [--retry-max N] [--json out.json]
    （GET /repos/{repo}/actions/runs/{run}/jobs?per_page=100&page=N 分页到齐；
      --logs 时对红件再 GET /repos/{repo}/actions/jobs/{job}/logs 抓关键行入证据：
      COQCHK_EXIT/COQCHK_ALL_PASS/判定=CLEAN/公理总数/GATE-BANNER-ABSENT/
      ENOTFOUND/ORDER-MISSING/EXIT=134 等；取日志两跳形（20261112 415 修法·
      实测定）：第一跳 Accept: application/vnd.github+json（text/plain 现 415 拒）
      禁自动重定向 GET → 302 Location 签名 URL；第二跳对签名 URL 零 Authorization
      再 GET（签名自带凭据——带 token 转发 403 Azure AuthenticationFailed·实测）；
      logs GET 404/403/415 本身入证据——403 Forbidden: job is completed 即判类谱
      B 中断连坐 token·重试耗尽后原码照旧入证据）
  韧性层（v37 限流退避·承任务书①）：线上 GET 遇 403/429/5xx → 指数退避重试
    （base 2s·帽 --retry-max 缺省 3·Retry-After 秒数头尊重——可解析秒数替当
    次指数延迟·HTTP-date 形不猜落回指数；重试耗尽或 4xx 语义面（401/404 等）
    原错原样上抛 9 不重试）。延迟计算抽公共件 tools/_http_backoff.py 纯函数
    backoff_delays()/parse_retry_after()/is_retry_status()（三器共享·同目录
    sys.path 注入 import·无 __init__ 包结构）。
  离线模式（selftest 与断网环境走此路·零网络）：
    python3 tools/ci_triage.py --offline JOBS.json [--baseline-seconds N ...]
        [--json out.json]
    （canned jobs JSON 同 API 真形 {"total_count":N,"jobs":[...]}；
      fixtures 见 tests/fixtures/ci_triage_*.json 六件套＋Main 形 coq93
      真形一件 ci_triage_main_coq93.json（v48 勘形小改①·单 Windows job
      「Main CI 9.3」16 步真名·绿样张）＋gate2-only 真形两件
      ci_triage_gate2_only_{cancelled,failure}.json（20261112 retro 台账
      run#7/#10 逐字段誊录）＝九件）
  python3 tools/ci_triage.py --selftest

退出码：0=分诊完成（红是数据非器红·响亮 stdout）；2=用法错（参数缺失/互斥/
  形不对）；9=API/文件不可达或形坏（netrc 缺失·token 空·HTTP 4xx/5xx·连接
  失败·jobs 文件缺失或 JSON 形坏·时间戳形不识别）。--selftest：0=全过／2=断言
  失败。

report schema（--json）= rocqwash-ci-triage/1：
  {"schema","mode","source",
   "run"{repo,run_id,total_count,jobs_total,red_job_ids,family,action,evidence},
   "jobs"[{id,name,status,conclusion,started_at,completed_at,duration_sec,
     "steps"[{number,name,status,conclusion,started_at,completed_at,duration_sec}],
     "classification"{family,action,evidence,red_steps}}],
   "family","action","evidence","baseline_note"?}
  family ∈ A-content-red / B-netred / C-toolchain-break / D-queue-wall /
    E-coqchk-skipped / none / UNRECOGNIZED；
  action ∈ rerun-after-stable-window / fix-content / restore-toolchain /
    queue-etiquette / watch-only；
  baseline_note（仅 --baseline-seconds 时在册）：{applied,step_query,
    baseline_seconds,matched?,current_seconds?,ratio?,note|reason}
    （applied=false＝基线步未在场或未完·响亮注记非静默·rc 仍 0）。

诚实律（承 CONTRIBUTING §0）：只认机械证据；判类谱外不充谱；红是数据非器红
  （分诊 exit 0）；--json 落盘 sorted+sort_keys·同输入重跑字节级恒同；stdout 全
  数据驱动（零 now() 零随机）；零第三方依赖（纯 stdlib）；fail-loud 禁静默降级。
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
# logs 端点 Accept 实测定值（20261112 415 修法）：text/plain 现 415 拒（探针 P1
# 原词 {"message":"Unsupported 'Accept' header: 'text/plain'. Must accept
# 'application/json'. ..."}）；application/vnd.github+json → 302 Location 签名
# URL（探针 P2）；第二跳对签名 URL 零 Authorization → 200 实日志（探针 P4·
# 1673483 bytes）；带 token 转发 → 403 Azure AuthenticationFailed（探针 P5
# 对照·证两跳零认证必要面）。探针 /tmp/probe_logs_415.py·job 127903477736。
LOGS_ACCEPT = "application/vnd.github+json"
REDIRECT_CODES = (301, 302, 303, 307, 308)   # 签名 URL 重定向族（两跳手工续接）

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)   # 同目录共享退避小模块（无 __init__ 包结构）
import _http_backoff

# ---- 判类谱词面（冻结向量·正负判见 --selftest）-----------------------------

# 日志关键行抓取器（tag, regex）——命中行原样入 evidence（≤200 字符·去重保序·帽 60）
KEY_LOG_PATTERNS = [
    ("COQCHK_EXIT", re.compile(r"COQCHK_EXIT=(-?\d+)")),
    ("COQCHK_ALL_PASS", re.compile(r"COQCHK_ALL_PASS=(\d+)")),
    ("判定=CLEAN", re.compile(r"判定=CLEAN")),
    ("公理总数", re.compile(r"公理总数=(\d+)")),
    ("GATE-BANNER-ABSENT", re.compile(r"GATE-BANNER-ABSENT")),
    ("ORDER-MISSING", re.compile(r"ORDER-MISSING")),
    ("ENOTFOUND", re.compile(r"ENOTFOUND")),
    ("EXIT=134", re.compile(r"EXIT=134")),
    ("Abort-trap-6", re.compile(r"Abort trap: 6")),
    ("NET-ACCESS", re.compile(r"unable to access|port 443|Connection was reset")),
    ("UPLOAD-STALL", re.compile(r"Upload progress stalled")),
    ("JOB-COMPLETED-403", re.compile(r"403 Forbidden: job is completed")),
    ("Error", re.compile(r"\bError:")),
]

# 家族判定 regex（log 直证）
RED_CONTENT_RE = re.compile(
    r"\bError:|ORDER-MISSING|(?<![A-Za-z])FAIL(?![A-Za-z])"
    r"|COQCHK_EXIT=(?!0\b)\d+|公理总数=(?!0\b)\d+")
RED_NET_RE = re.compile(
    r"unable to access|port 443|Connection was reset|ENOTFOUND"
    r"|Upload progress stalled|403 Forbidden: job is completed")
RED_ABORT_RE = re.compile(r"EXIT=134|Abort trap: 6")
GATE_BANNER_ABSENT_RE = re.compile(r"GATE-BANNER-ABSENT")

# 步名族 regex（步级推断·无日志时的兜底判面）
CONTENT_STEP_RE = re.compile(r"(?i)build|compile|coqchk|coqc|rocq|check|verify|make")
NET_STEP_RE = re.compile(r"(?i)checkout|upload|artifact|cache|download|publish")
UPLOAD_STEP_RE = re.compile(r"(?i)upload|artifact")
COQCHK_STEP_RE = re.compile(r"(?i)coqchk")
GATE2_STEP_RE = re.compile(r"(?i)gate2")   # gate2-only 连坐形判据词（纯 gate2
# 红步＝GATE2 命中且 UPLOAD 不命中——「Upload artifact (gate2 ledger)」gate2
# 子串词面搭便不算纯 gate2·防误吞上传红·组合判据在 classify E 变体分支）

RED_STEP_CONCLUSIONS = ("failure", "timed_out")

# family → action（判类谱处置表）
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
    "A-content-red": "内容红",
    "B-netred": "网络窗",
    "C-toolchain-break": "环境断链",
    "D-queue-wall": "排队资源墙",
    "E-coqchk-skipped": "coqchk-skipped 签名（B 族变体）",
    "none": "绿/无红",
    "UNRECOGNIZED": "判类谱外未识别红形",
}

# run 级判类序（先到先取）：谱外红形置顶（人工指认优先·不被已识别族遮蔽）
RUN_FAMILY_PRECEDENCE = ["UNRECOGNIZED", "C-toolchain-break", "A-content-red",
                         "E-coqchk-skipped", "B-netred", "D-queue-wall"]

BASELINE_SQUEEZE_RATIO = 3.0   # 倍数≥此阈→「本机挤压嫌疑非卡死」（判例 13.3x 远超阈）
LOG_EVIDENCE_CAP = 60          # 单 job 日志证据行帽
LOGS_FETCH_CAP = 20            # --logs 红件日志抓取件数帽（超额响亮注记）


class TriageError(Exception):
    """带退出码的 fail-loud 异常（code: 2=用法错·9=API/文件不可达或形坏）。"""

    def __init__(self, msg, code=9):
        super(TriageError, self).__init__(msg)
        self.code = code


class ApiHTTPError(Exception):
    """只读 GET 的 HTTP 错误（body 头入账·由调用方决定转 9 还是入 evidence）。"""

    def __init__(self, code, body, url):
        super(ApiHTTPError, self).__init__("HTTP %d: %s" % (code, url))
        self.code = code
        self.body = body or ""
        self.url = url


# ---- 时间与时长 -------------------------------------------------------------

def parse_iso(ts):
    """ISO8601 → aware datetime（UTC 缺省）；空/None → None；形不识别 → fail-loud 9。"""
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
        raise TriageError("时间形不识别: %r" % ts, 9)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def duration_sec(started_at, completed_at):
    """起止 → 整秒（None/未完 → None；负值钳 0）。"""
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


# ---- 凭据（netrc machine github.com 第 6 列）--------------------------------

def netrc_token(path, machine="github.com"):
    """netrc 手动解析：machine <m> login <l> password <p>（单行 6 列形与多行形
    通吃）→ password token。缺文件/无条目/空值 → fail-loud 9（token 永不回显）。"""
    if not os.path.isfile(path):
        raise TriageError("netrc 缺失: %s（线上模式需 machine %s ... password 形凭据）"
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
                    raise TriageError("netrc machine %s password 为空" % machine, 9)
                return tok
            i += 2
            continue
        i += 1
    raise TriageError("netrc 无 machine %s password 形条目（单行 6 列形：第 6 列=token）: %s"
                      % (machine, path), 9)


# ---- 只读 GET（唯一网络动作）-------------------------------------------------

def http_get(url, token, timeout, accept="application/vnd.github+json",
             retry_max=3, _open=None, _sleep=None):
    """只读 GET → bytes。403/429/5xx 指数退避重试（_http_backoff 纯函数：
    base 2s·帽 retry_max·Retry-After 秒数头优先替当次延迟）；重试耗尽或
    4xx 语义面原错上抛——HTTPError → ApiHTTPError（body 头随行）；连接失败
    → 9。_open/_sleep 注入位（selftest 零网络矢量·缺省真 urlopen/真 sleep）。"""
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
            raise TriageError("API 不可达: %s (%s)" % (url, e), 9)


def jobs_url(repo, run_id):
    return "%s/repos/%s/actions/runs/%d/jobs" % (API_ROOT, repo, run_id)


def fetch_jobs_online(repo, run_id, token, timeout, retry_max=3):
    """GET jobs（per_page=100 分页到齐）→ (jobs, total_count)。HTTP 4xx/5xx
    → 9（403/429/5xx 先经 http_get 指数退避重试·耗尽才判 9）。"""
    jobs = []
    total = None
    page = 1
    while True:
        url = "%s?per_page=100&page=%d" % (jobs_url(repo, run_id), page)
        data = json.loads(http_get(url, token, timeout,
                                   retry_max=retry_max).decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise TriageError("API 形坏（无 jobs 列表）: %s" % url, 9)
        if total is None:
            total = data.get("total_count")
        jobs.extend(data["jobs"])
        if len(data["jobs"]) < 100:
            break
        if total is not None and len(jobs) >= total:
            break
        page += 1
        if page > 50:
            raise TriageError("jobs 分页超帽（50 页）·拒绝续拉", 9)
    return jobs, (total if total is not None else len(jobs))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁自动重定向 handler（302 以 HTTPError 形上抛·供 fetch_job_log 两跳手工
    续接——urllib 缺省跟随时会把 Authorization 头一并转发签名 URL·Azure 侧
    403 AuthenticationFailed 实测形；两跳零认证第二跳即修）。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _logs_error_note(e):
    """logs HTTPError → 证据注记（body 头 120 字符·原码在册·同旧注记形）。"""
    try:
        body = (e.read() or b"").decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return "logs-GET: HTTP %d %s（日志不可达·入证据）" % (
        e.code, body.strip()[:120])


def fetch_job_log(repo, job_id, token, timeout, retry_max=3, _open=None,
                  _sleep=None):
    """GET 单 job 日志原文 → (text, None)；HTTP 4xx/5xx → (None, 证据注记)。

    两跳取日志（20261112 415 修法·实测定）：第一跳 GET logs 端点
    （Accept: application/vnd.github+json——text/plain 现 415 拒·禁自动重定向
    _NoRedirect opener）→ 302 Location 签名 URL；第二跳对签名 URL 零
    Authorization 再 GET（签名自带凭据——urllib 缺省随重定向转发 token 会
    403 Azure AuthenticationFailed·探针 P5 实测）。403/429/5xx 第一跳指数退避
    重试（_http_backoff 同款·Retry-After 秒数头尊重·耗尽落证据注记）；
    404/415 等语义面不重试原码照旧入证据；第二跳失败落证据注记不重试；
    连接失败仍 TriageError 9（API 不可达）。_open/_sleep 注入位（selftest
    零网络矢量·缺省真 opener/真 sleep）。"""
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
                    return None, "logs-GET: HTTP %d 无 Location（重定向形坏）" \
                        % e.code
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
            raise TriageError("API 不可达: %s (%s)" % (url, e), 9)


# ---- 离线装载 ---------------------------------------------------------------

def load_jobs_offline(path):
    """canned jobs JSON（同 API 真形 {"total_count":N,"jobs":[...]}）→ (jobs, total)。
    缺文件/解析败/形坏 → fail-loud 9。"""
    if not os.path.isfile(path):
        raise TriageError("jobs JSON 缺失: %s" % path, 9)
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise TriageError("jobs JSON 形坏（解析失败）: %s (%s)" % (path, e), 9)
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise TriageError(
            "jobs JSON 形坏（须 {\"total_count\":N,\"jobs\":[...]} 同 API 形）: %s" % path, 9)
    for idx, j in enumerate(data["jobs"]):
        if not isinstance(j, dict) or not isinstance(j.get("name"), str) \
                or not isinstance(j.get("steps") or [], list):
            raise TriageError("jobs JSON 形坏（jobs[%d] 非 job 形）: %s" % (idx, path), 9)
    return data["jobs"], data.get("total_count", len(data["jobs"]))


# ---- 判类器 -----------------------------------------------------------------

def scan_log_evidence(text):
    """日志原文 → 关键行证据表（tag＋命中行原样 ≤200 字符·去重保序·帽 60）。"""
    out = []
    for line in text.splitlines():
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


def classify(job, log_text=None):
    """判类谱逐 job 判类 → {"family","action","evidence","red_steps"}（判类序见
    模块 docstring·失败步名与 redSteps 全入 evidence）。"""
    ev = []
    status = str(job.get("status") or "")
    conclusion = job.get("conclusion")
    steps = job.get("steps") or []
    red_steps = [s for s in steps
                 if s.get("conclusion") in RED_STEP_CONCLUSIONS]
    red_names = [str(s.get("name") or "(unnamed)") for s in red_steps]

    if conclusion == "success":
        return {"family": "none", "action": "watch-only",
                "evidence": ["conclusion=success（绿）"], "red_steps": []}
    if conclusion is None or status != "completed":
        return {"family": "none", "action": "watch-only",
                "evidence": ["在飞/未完（status=%s conclusion=%s）·判类暂缓非绿判"
                             % (status or "-", conclusion or "-")],
                "red_steps": []}
    if conclusion in ("skipped", "neutral"):
        return {"family": "none", "action": "watch-only",
                "evidence": ["conclusion=%s（条件跳过/中立·非红）" % conclusion],
                "red_steps": []}

    ev.append("job conclusion=%s status=%s" % (conclusion, status or "-"))
    for n in red_names:
        ev.append("failure-step: %s" % n)

    # D：cancelled 且零步骤（logs 404 形）
    if conclusion == "cancelled" and not steps:
        ev.append("steps=0（零步骤）·logs 404 形（排队资源墙判例）")
        return {"family": "D-queue-wall", "action": ACTION_OF["D-queue-wall"],
                "evidence": ev, "red_steps": []}
    # B 连坐形：cancelled·有步骤·零红步
    if conclusion == "cancelled" and not red_steps:
        ev.append("cancelled·有步骤零红步＝中断连坐形（判类谱 B·"
                  "403 Forbidden: job is completed 同族）")
        return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                "evidence": ev, "red_steps": []}

    # log 直证 C：EXIT=134 / Abort trap: 6（判类谱 C·SKIP 件全过）
    if log_text and RED_ABORT_RE.search(log_text):
        ev.append("log 直证：EXIT=134/Abort trap: 6（判类谱 C·环境断链）")
        return {"family": "C-toolchain-break",
                "action": ACTION_OF["C-toolchain-break"],
                "evidence": ev + scan_log_evidence(log_text),
                "red_steps": red_names}

    # E 签名：上传步红＋coqchk 步 skipped（B 族变体·勿当内容红）
    upload_red = [s for s in red_steps if UPLOAD_STEP_RE.search(str(s.get("name") or ""))]
    coqchk_skipped = [s for s in steps
                      if s.get("conclusion") == "skipped"
                      and COQCHK_STEP_RE.search(str(s.get("name") or ""))]
    if upload_red and coqchk_skipped:
        ev.append("coqchk 步 skipped＝gate2 未达（E 签名·GATE-BANNER-ABSENT 同义·"
                  "--logs 可确证）")
        if log_text:
            if GATE_BANNER_ABSENT_RE.search(log_text):
                ev.append("log 确证：GATE-BANNER-ABSENT（E 签名第三件齐）")
            ev.extend(scan_log_evidence(log_text))
        return {"family": "E-coqchk-skipped",
                "action": ACTION_OF["E-coqchk-skipped"],
                "evidence": ev, "red_steps": red_names}

    # E 变体（gate2-only 连坐形·20261112 Main retro 六事件证据人工指认入谱）：
    # 红步集 ⊆ {gate2＋上传族} 且纯 gate2 红步在册（gate2 名非上传名——防
    # 「Upload artifact (gate2 ledger)」gate2 子串词面搭便误吞上传红）＝前置
    # build/coqchk 非 content 红（Build/coqchk proper 步名既不沾 gate2 也不沾
    # 上传族·在红步集即破子集条件）＝「coqchk 产物缺·gate2 连坐」（GATE-BANNER-
    # ABSENT 同义·run#7 job 127903477736 日志 200 实测确证）
    # → family=E-coqchk-skipped（E 族内变体·判类谱序 UNRECOGNIZED>C>A>E>B>D
    #   不动）·action=rerun-after-stable-window。出处：retro 台账 §二主表
    #   UNREC 六事件中 #7/#8/#10/#20/#26 五发 gate2-only 形·#3 runner 失联形
    #   （零红步）仍走 UNRECOGNIZED 不充谱。
    gate2_only_red = [s for s in red_steps
                      if GATE2_STEP_RE.search(str(s.get("name") or ""))
                      and not UPLOAD_STEP_RE.search(str(s.get("name") or ""))]
    subset_gate2_upload = all(
        GATE2_STEP_RE.search(str(s.get("name") or ""))
        or UPLOAD_STEP_RE.search(str(s.get("name") or ""))
        for s in red_steps)
    if gate2_only_red and subset_gate2_upload:
        ev.append("gate2-only 连坐形（E 变体）：红步集 ⊆ {gate2+上传族}·纯 gate2"
                  " 红步在册·前置 build/coqchk 非 content 红＝coqchk 产物缺·"
                  "gate2 连坐（GATE-BANNER-ABSENT 同义·20261112 Main retro "
                  "#7/#8/#10/#20/#26 五事件形入谱）")
        if log_text:
            if GATE_BANNER_ABSENT_RE.search(log_text):
                ev.append("log 确证：GATE-BANNER-ABSENT（gate2-only E 变体第三件）")
            ev.extend(scan_log_evidence(log_text))
        return {"family": "E-coqchk-skipped",
                "action": ACTION_OF["E-coqchk-skipped"],
                "evidence": ev, "red_steps": red_names}

    if log_text:
        ev.extend(scan_log_evidence(log_text))
        if RED_NET_RE.search(log_text):
            ev.append("log 命中网络窗词面（判类谱 B）")
            return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                    "evidence": ev, "red_steps": red_names}
    for s in red_steps:
        if NET_STEP_RE.search(str(s.get("name") or "")):
            ev.append("红步名∈网络邻接步（checkout/upload/artifact/cache/…）: %s"
                      % s.get("name"))
            return {"family": "B-netred", "action": ACTION_OF["B-netred"],
                    "evidence": ev, "red_steps": red_names}
    if log_text and RED_CONTENT_RE.search(log_text):
        ev.append("log 命中内容红词面（Error:/FAIL/ORDER-MISSING/EXIT≠0/公理≠0·判类谱 A）")
        return {"family": "A-content-red", "action": ACTION_OF["A-content-red"],
                "evidence": ev, "red_steps": red_names}
    for s in red_steps:
        if CONTENT_STEP_RE.search(str(s.get("name") or "")):
            ev.append("红步名∈内容步（build/compile/coqchk/…·判类谱 A·具体件见 --logs）: %s"
                      % s.get("name"))
            return {"family": "A-content-red", "action": ACTION_OF["A-content-red"],
                    "evidence": ev, "red_steps": red_names}

    ev.append("step-conclusions: %s" % ",".join(
        "%s=%s" % (s.get("name") or "(unnamed)", s.get("conclusion") or "-")
        for s in steps))
    ev.append("判类谱外红形·不充谱·人工看日志指认")
    return {"family": "UNRECOGNIZED", "action": "watch-only",
            "evidence": ev, "red_steps": red_names}


def batch_upgrade_c(per, jobs):
    """run 级批量判（判类谱 C）：同形内容红（A）≥2 件 → 全数升 C
    （判例：批量 EXIT=134/Abort trap: 6·SKIP 件全过·--logs 可确证）。"""
    idxs = [i for i, c in enumerate(per) if c["family"] == "A-content-red"]
    if len(idxs) < 2:
        return
    for i in idxs:
        c = per[i]
        c["family"] = "C-toolchain-break"
        c["action"] = ACTION_OF["C-toolchain-break"]
        c["evidence"].append(
            "run 级批量判：同形内容红 %d 件（判例 C：批量 EXIT=134/Abort trap: 6·"
            "SKIP 件全过）·EXIT=134 确证建议 --logs" % len(idxs))


def run_verdict(per, jobs, extra_evidence=None):
    """run 级判类：按 RUN_FAMILY_PRECEDENCE 取先（谱外置顶）→ {family,action,
    evidence,red_job_ids}。"""
    reds = [(j, c) for j, c in zip(jobs, per) if c["family"] != "none"]
    fams = set(c["family"] for _, c in reds)
    ev = list(extra_evidence or [])
    if not fams:
        ev.append("全绿：0 红件（watch-only）")
        return {"family": "none", "action": ACTION_OF["none"],
                "evidence": ev, "red_job_ids": []}
    fam = next(f for f in RUN_FAMILY_PRECEDENCE if f in fams)
    ev.append("红件 %d/%d：ids=%s" % (len(reds), len(jobs),
                                      [j.get("id") for j, _ in reds]))
    ev.append("在册族：%s（判类序取先）" % ",".join(sorted(fams)))
    if "UNRECOGNIZED" in fams:
        ev.append("UNRECOGNIZED 在册·判类谱外红形人工指认优先（不充谱）")
    return {"family": fam, "action": ACTION_OF[fam],
            "evidence": ev, "red_job_ids": [j.get("id") for j, _ in reds]}


# ---- 时长对表（--baseline-seconds）------------------------------------------

def build_baseline_note(jobs, baseline_seconds, baseline_step):
    """基线对表：现值（--baseline-step 名含匹配·多命中取最长者·全部在册）
    vs 基线秒 → 倍数；≥BASELINE_SQUEEZE_RATIO → 本机挤压嫌疑非卡死注记。
    基线步未在场或未完（skipped/未跑）→ applied=false 响亮注记（rc 仍 0）。"""
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
                "reason": "基线步未在场或未完（skipped/未跑）·对表未施（响亮注记非静默）"}
    cur = max(m["duration_sec"] for m in matches)
    ratio = round(cur / float(baseline_seconds), 1)
    note = "步 %s 现 %ds vs 基线 %ds = %.1fx" % (query, cur, baseline_seconds, ratio)
    if ratio >= BASELINE_SQUEEZE_RATIO:
        note += "（≥%.0fx＝本机挤压嫌疑非卡死·判例 coqchk 561s vs 7480s=13.3x）" \
                % BASELINE_SQUEEZE_RATIO
    else:
        note += "（＜%.0fx·时长量级如常）" % BASELINE_SQUEEZE_RATIO
    return {"applied": True, "step_query": query,
            "baseline_seconds": baseline_seconds,
            "matched": sorted(matches, key=lambda m: (str(m["job"]),
                                                      str(m["step"]),
                                                      m["duration_sec"])),
            "current_seconds": cur, "ratio": ratio, "note": note}


# ---- 出账 -------------------------------------------------------------------

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
    print("=== ROCQWASH CI-TRIAGE（20261110 判类谱·六幕实战代码化）===")
    print(source_desc)
    print("jobs total=%d" % len(jobs))
    for j, c in zip(jobs, per):
        jd = duration_sec(j.get("started_at"), j.get("completed_at"))
        print("--- JOB #%s 「%s」 status=%s conclusion=%s dur=%s ---"
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
        print("  判类: family=%s（%s） action=%s"
              % (c["family"], FAMILY_LABEL.get(c["family"], ""), c["action"]))
        for e in c["evidence"]:
            print("    - %s" % e)
    print("=== RUN VERDICT: family=%s（%s） action=%s ==="
          % (verdict["family"], FAMILY_LABEL.get(verdict["family"], ""),
             verdict["action"]))
    for e in verdict["evidence"]:
        print("  - %s" % e)
    if baseline is not None:
        print("baseline: %s" % (baseline.get("note") or baseline.get("reason") or ""))
    print("（分诊完成·红是数据非器红·exit 0）")


# ---- 主流程 -----------------------------------------------------------------

def run_triage(args):
    """装载（线上/离线）→ 逐 job 判类 → run 级批量判 C → run 判类 → 基线对表
    → (report, jobs, per, verdict, baseline, source_desc)。用法错 → 2·不可达 → 9。"""
    online = args.repo is not None or args.run is not None
    if args.offline and online:
        raise TriageError("--offline 与 --repo/--run 互斥（二选一）", 2)
    if not args.offline and not online:
        raise TriageError("须给 --offline JOBS.json（离线）或 --repo ORG/REPO "
                          "--run ID（线上）", 2)
    if online and (args.repo is None or args.run is None):
        raise TriageError("线上模式须 --repo ORG/REPO 与 --run ID 成对", 2)
    if args.repo is not None and not re.match(r"^[^/\s]+/[^/\s]+$", args.repo):
        raise TriageError("--repo 形须 ORG/REPO", 2)
    if args.offline and args.logs:
        raise TriageError("--logs 仅线上模式（离线零网络·日志证据走 canned 形或 "
                          "--selftest regex 单元）", 2)
    if args.baseline_seconds is not None and args.baseline_seconds <= 0:
        raise TriageError("--baseline-seconds 须正整数", 2)
    if args.retry_max < 0:
        raise TriageError("--retry-max 须≥0 实测 %d" % args.retry_max, 2)

    log_notes = {}
    if args.offline:
        jobs, total = load_jobs_offline(args.offline)
        mode, source, repo, run_id = "offline", args.offline, None, None
        source_desc = "mode=offline source=%s" % args.offline
    else:
        token = netrc_token(args.netrc)
        try:
            jobs, total = fetch_jobs_online(args.repo, args.run, token,
                                            args.timeout,
                                            retry_max=args.retry_max)
        except ApiHTTPError as e:
            raise TriageError("API HTTP %d: %s（GET jobs 失败·%s）"
                              % (e.code, e.body.strip()[:160], e.url), 9)
        mode, source, repo, run_id = "online", jobs_url(args.repo, args.run), \
            args.repo, args.run
        source_desc = ("mode=online repo=%s run=%d api=%s token=***MASKED***"
                       "（netrc machine github.com·%s）"
                       % (repo, run_id, source, args.netrc))

    logs_by_id = {}
    if mode == "online" and args.logs:
        reds = [j for j in jobs
                if j.get("conclusion") in ("failure", "timed_out", "cancelled")
                and (j.get("steps") or [])]
        if len(reds) > LOGS_FETCH_CAP:
            log_notes["_meta"] = "logs 抓取帽 %d：仅抓前 %d 红件（余 %d 件未抓·响亮非静默）" \
                % (LOGS_FETCH_CAP, LOGS_FETCH_CAP, len(reds) - LOGS_FETCH_CAP)
        for j in reds[:LOGS_FETCH_CAP]:
            text, note = fetch_job_log(repo, j.get("id"), token, args.timeout,
                                       retry_max=args.retry_max)
            logs_by_id[j.get("id")] = text or ""
            if note:
                log_notes[j.get("id")] = note

    per = [classify(j, logs_by_id.get(j.get("id"))) for j in jobs]
    for j, c in zip(jobs, per):
        note = log_notes.get(j.get("id"))
        if note:
            c["evidence"].append(note)
    batch_upgrade_c(per, jobs)
    verdict = run_verdict(per, jobs, extra_evidence=[
        v for k, v in sorted(log_notes.items()) if k == "_meta"])
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
        description="CI 红炉分诊器（20261110 判类谱代码化）——步级表＋五族＋绿炉"
                    "判类＋处置 action＋可选时长基线对表")
    ap.add_argument("--offline", default=None, metavar="JOBS.json",
                    help="离线模式：canned jobs JSON（同 API 真形）——selftest 与"
                         "断网环境走此路")
    ap.add_argument("--repo", default=None, metavar="ORG/REPO",
                    help="线上模式：仓库形 ORG/REPO（与 --run 成对）")
    ap.add_argument("--run", type=int, default=None, metavar="ID",
                    help="线上模式：Actions run id（与 --repo 成对）")
    ap.add_argument("--logs", action="store_true",
                    help="线上模式加抓红件日志抓关键行入证据（仅线上·离线拒）")
    ap.add_argument("--netrc",
                    default=os.path.join(os.path.expanduser("~"), ".netrc"),
                    metavar="PATH",
                    help="netrc 路径（默认 ~/.netrc·machine github.com 第 6 列"
                         "=token）")
    ap.add_argument("--baseline-seconds", type=int, default=None, metavar="N",
                    help="同 sync 历史时长秒（判例 coqchk 561s）→ 出倍数对表")
    ap.add_argument("--baseline-step", default="coqchk", metavar="NAME",
                    help="对表步名（名含匹配·默认 coqchk=判例形）")
    ap.add_argument("--timeout", type=int, default=30, metavar="S",
                    help="单请求超时秒（默认 30）")
    ap.add_argument("--retry-max", type=int, default=3, metavar="N",
                    help="403/429/5xx 退避重试帽（默认 3·指数 base 2s·"
                         "Retry-After 秒数头尊重·耗尽原错 9）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="分诊 report 出账（rocqwash-ci-triage/1·sort_keys）")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        report, jobs, per, verdict, baseline, source_desc = run_triage(args)
    except ApiHTTPError as e:
        print("FAIL-LOUD: API HTTP %d: %s（%s）" % (e.code, e.body.strip()[:200],
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


# ---- 自测（--offline fixtures·零真网络零编译·纯逻辑向量）---------------------

def selftest():
    """内嵌冻结向量组：五族＋绿炉六 canned 样张全命中＋基线 13.3x 判例＋基线步
    缺席响亮注记＋分类器单元（关键行 regex 正负判·连坐/在飞/UNRECOGNIZED 分流·
    E 勿当内容红负证）＋netrc 解析单元＋确定性字节恒同＋CLI 四码＋韧性层退避
    （403×3→[2,4,8]·Retry-After 尊重·耗尽上抛·401 不重试·_open/_sleep 注入
    零网络）＋〔九〕Main 形判读矢（v48 勘形小改①·coq93.yml 真形步名×五族
    判类兼容机检钉——勘形 §3.1「即用」判据的机械实证）＋〔十〕gate2-only
    E 变体矢（两 fixture 全命中＋规则正负判·出处六事件 #7/#8/#10/#20/#26
    入谱 #3 不充谱）＋logs 两跳 415 修法矢（302→零 Authorization 第二跳
    200·415/403/无 Location 原码入证据·canned 零网络）。
    全程 --offline fixtures 零真网络零编译。"""
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
        # 〔一〕五族＋绿炉六样张全命中（family/action 逐张咬合）
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
            assert os.path.isfile(path), "fixture 缺失（六件套须在卷）: %s" % path
            out = os.path.join(tmp, stem + ".json")
            p = run(["--offline", path, "--json", out])
            assert p.returncode == 0, (stem, p.stdout[-400:])
            rep = json.load(io.open(out, encoding="utf-8"))
            assert rep["schema"] == SCHEMA, rep.get("schema")
            assert rep["family"] == fam and rep["action"] == act, \
                (stem, rep["family"], rep["action"])
            outs[stem] = out
        # A：红步名入 evidence·且非 B/E（内容红正判）
        repA = json.load(io.open(outs["A_content_red"], encoding="utf-8"))
        cjA = repA["jobs"][0]["classification"]
        assert cjA["family"] == "A-content-red" and any(
            e.startswith("failure-step: Build") for e in cjA["evidence"]), cjA
        # B：checkout 红步归 B；cancelled 连坐形（有步骤零红步）亦归 B
        repB = json.load(io.open(outs["B_netred"], encoding="utf-8"))
        assert repB["jobs"][0]["classification"]["family"] == "B-netred"
        assert repB["jobs"][1]["classification"]["family"] == "B-netred", \
            "连坐形应归 B"
        assert any("连坐" in e
                   for e in repB["jobs"][1]["classification"]["evidence"])
        # C：run 级批量升 C（三红 job 全 C·绿控制件仍 none·批量注记在 per-job 证据）
        repC = json.load(io.open(outs["C_toolchain_break"], encoding="utf-8"))
        famsC = [j["classification"]["family"] for j in repC["jobs"]]
        assert famsC == ["C-toolchain-break"] * 3 + ["none"], famsC
        assert any("批量" in e
                   for e in repC["jobs"][0]["classification"]["evidence"]), repC["jobs"][0]
        # D：零步骤（steps=[]）在册·证据含 steps=0
        repD = json.load(io.open(outs["D_queue_wall"], encoding="utf-8"))
        assert repD["jobs"][0]["steps"] == []
        assert "steps=0" in "".join(
            repD["jobs"][0]["classification"]["evidence"])
        # E：E 签名命中·且勿当内容红（family≠A·coqchk skipped 注记在册）
        repE = json.load(io.open(outs["E_coqchk_skipped"], encoding="utf-8"))
        cjE = repE["jobs"][0]["classification"]
        assert cjE["family"] == "E-coqchk-skipped" \
            and cjE["family"] != "A-content-red", cjE
        assert any("coqchk" in e for e in cjE["evidence"]), cjE
        # 绿炉：family=none·action=watch-only
        repG = json.load(io.open(outs["green"], encoding="utf-8"))
        assert repG["family"] == "none" and repG["action"] == "watch-only"

        # 〔二〕基线对表：绿炉 COQCHK 7480s vs 基线 561s = 13.3x（判例）
        out = os.path.join(tmp, "baseline.json")
        p = run(["--offline", fx("green"), "--baseline-seconds", "561",
                 "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        bn = json.load(io.open(out, encoding="utf-8"))["baseline_note"]
        assert bn["applied"] is True and bn["current_seconds"] == 7480 \
            and bn["ratio"] == 13.3, bn
        assert "本机挤压嫌疑非卡死" in bn["note"] and "561" in bn["note"], bn
        # 基线步缺席（A 夹具 COQCHK skipped）→ applied=False 响亮注记·rc 仍 0
        p = run(["--offline", fx("A_content_red"), "--baseline-seconds", "561",
                 "--json", out])
        assert p.returncode == 0, p.stdout[-400:]
        bn = json.load(io.open(out, encoding="utf-8"))["baseline_note"]
        assert bn["applied"] is False and "响亮" in bn["reason"], bn

        # 〔三〕确定性：C 夹具同输入重跑 --json 字节级恒同
        before = io.open(outs["C_toolchain_break"], "rb").read()
        p = run(["--offline", fx("C_toolchain_break"),
                 "--json", outs["C_toolchain_break"]])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(outs["C_toolchain_break"], "rb").read() == before, \
            "json 字节漂移＝违例"

        # 〔四〕CLI 四码＋互斥形
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺模式应 rc=2 实测 %d" % p.returncode
        p = run(["--offline", os.path.join(tmp, "nope.json")])
        assert p.returncode == 9, "缺 jobs 文件应 rc=9 实测 %d" % p.returncode
        p = run(["--offline", fx("green"), "--logs"])
        assert p.returncode == 2, "--logs 离线拒应 rc=2 实测 %d" % p.returncode
        p = run(["--repo", "org/repo"])
        assert p.returncode == 2, "repo 缺 run 应 rc=2 实测 %d" % p.returncode
        p = run(["--repo", "justname", "--run", "1"])
        assert p.returncode == 2, "repo 形错应 rc=2 实测 %d" % p.returncode
        p = run(["--offline", fx("green"), "--repo", "o/r", "--run", "1"])
        assert p.returncode == 2, "双模式互斥应 rc=2 实测 %d" % p.returncode

        # 〔五〕分类器单元（零网络·直接调）
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
        assert c["family"] == "none" and any("在飞" in e for e in c["evidence"]), c
        c = classify(mkjob(conclusion="cancelled"))
        assert c["family"] == "D-queue-wall" and c["action"] == "queue-etiquette"
        c = classify(mkjob(conclusion="cancelled",
                           steps=[mkstep(1, "Build (coqc batch)", "cancelled")]))
        assert c["family"] == "B-netred" and any("连坐" in e for e in c["evidence"]), c
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
        assert c["family"] == "B-netred", "上传红无 E 签名（coqchk 非 skipped）→B"
        c = classify(mkjob(steps=[mkstep(1, "Report coverage", "failure")]))
        assert c["family"] == "UNRECOGNIZED" and c["action"] == "watch-only", c

        # 〔六〕关键行 regex 正负判（判类谱词面冻结向量）
        for s in ["Error: LibX.v:12: syntax", "ORDER-MISSING: names",
                  "COQCHK_EXIT=1", "公理总数=3", "task FAIL at step 2"]:
            assert RED_CONTENT_RE.search(s), "内容红正例应命中: %s" % s
        for s in ["COQCHK_EXIT=0", "公理总数=0", "0 FAILURES found",
                  "no error today", "all good"]:
            assert not RED_CONTENT_RE.search(s), "内容红负例不应命中: %s" % s
        for s in ["fatal: unable to access 'https://github.com/o/r.git/'",
                  "connect to github.com port 443 failed",
                  "ssh: Connection was reset",
                  "upload ENOTFOUND on github.com",
                  "Upload progress stalled at 90%",
                  "403 Forbidden: job is completed"]:
            assert RED_NET_RE.search(s), "网络窗正例应命中: %s" % s
        for s in ["Upload artifact success (3 files)",
                  "listening on port 8080", "connected ok"]:
            assert not RED_NET_RE.search(s), "网络窗负例不应命中: %s" % s
        for s in ["EXIT=134", "Abort trap: 6"]:
            assert RED_ABORT_RE.search(s), "断链正例应命中: %s" % s
        for s in ["EXIT=0", "EXIT=139", "Abort trap: 8"]:
            assert not RED_ABORT_RE.search(s), "断链负例不应命中: %s" % s
        assert GATE_BANNER_ABSENT_RE.search("GATE-BANNER-ABSENT")
        assert not GATE_BANNER_ABSENT_RE.search("gate banner ok")

        # 〔七〕netrc 解析单元（单行 6 列形＋多行形＋负例·零网络）
        nf = os.path.join(tmp, "netrc")
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine api.github.com login octo password AAAA\n"
                     "machine github.com login octocat password TOK-1234\n")
        assert netrc_token(nf) == "TOK-1234", "单行 6 列形应取 github.com 行第 6 列"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine github.com\nlogin octocat\npassword TOK-9\n")
        assert netrc_token(nf) == "TOK-9", "多行形应同解析"
        with io.open(nf, "w", encoding="utf-8") as fh:
            fh.write("machine gitlab.com login x password Y\n")
        try:
            netrc_token(nf)
            assert False, "无 github.com 条目应 fail-loud"
        except TriageError as e:
            assert e.code == 9, e.code

        # 〔八〕韧性层：退避序列＋Retry-After 尊重＋http_get canned 重试 runner
        # （零网络·_open/_sleep 注入位·判例 403×3→[2,4,8]）
        assert _http_backoff.backoff_delays(3) == [2.0, 4.0, 8.0]
        assert _http_backoff.backoff_delays(0) == []
        try:
            _http_backoff.backoff_delays(-1)
            assert False, "负帽应 ValueError"
        except ValueError:
            pass
        assert _http_backoff.parse_retry_after("60") == 60.0
        assert _http_backoff.parse_retry_after(
            "Wed, 21 Oct 2026 07:28:00 GMT") is None, "HTTP-date 不猜"

        class _Resp(object):
            """canned 响应体（urlopen 假件·零网络·上下文管理器形）。"""
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
                    raise r          # canned 错件须抛（urlopen 同语义）
                return r
            return _open

        slept = []
        got = http_get("https://x", "tok", 5, retry_max=3,
                       _open=_seq_open([_http_err(403)] * 3 + [_Resp()]),
                       _sleep=slept.append)
        assert got == b"JOBS" and slept == [2.0, 4.0, 8.0], \
            (got, slept)                       # 403×3→[2,4,8] 判例
        slept = []
        got = http_get("https://x", "tok", 5, retry_max=3,
                       _open=_seq_open([_http_err(429, ra="7"), _Resp(b"OK2")]),
                       _sleep=slept.append)
        assert got == b"OK2" and slept == [7.0], \
            (got, slept)                       # Retry-After 头尊重（替指数）
        slept = []
        try:
            http_get("https://x", "tok", 5, retry_max=3,
                     _open=_seq_open([_http_err(403)] * 4), _sleep=slept.append)
            assert False, "403×4 重试耗尽应上抛"
        except ApiHTTPError as e:
            assert e.code == 403, e.code
        assert slept == [2.0, 4.0, 8.0], slept
        slept = []
        try:
            http_get("https://x", "tok", 5, retry_max=3,
                     _open=_seq_open([_http_err(401)]), _sleep=slept.append)
            assert False, "401 语义面应不重试直上抛"
        except ApiHTTPError as e:
            assert e.code == 401, e.code
        assert slept == [], "401 零重试零睡"

        # 〔九〕Main 形判读矢（v48 勘形小改①·勘形档 §3.1 兼容表的机检钉）：
        # coq93.yml 真形（workflow「Main CI 9.3」·单 Windows job「Rocq 9.3
        # build + coqchk (self-hosted seed cache, Windows)」）步名 16 枚逐枚
        # 咬合＋五族判类对 Main 步名兼容逐行机械验证（真红不漏红·UNRECOGNIZED
        # 兜底不误断）。机检与勘形 §3.1 散文一处不符如实登记：gate1 步名
        # 「pre-build」含 build 子串→CONTENT 搭便归 A（fix-content·poison-token
        # 红语义上属内容红·可接受同 gate5/attest 词面搭便）——非 §3.1 所记
        # 「零命中→UNRECOGNIZED 兜底」；「五族骨架即用」判据不受影响（不漏红
        # 不误断）。20261112 增注：gate2 行原钉 UNRECOGNIZED（v48 勘形兼容表
        # 时点器面）——Main retro 六事件证据人工指认后 gate2-only 连坐形入谱
        # （E 变体·见〔十〕）·本行现钉 E-coqchk-skipped·兜底行剩 gate3/RAM/
        # tree-stats-gen 三枚（20261112 自查日志注记·与勘形 §八判读不追溯）。
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
            "Main 形 fixture 缺失（真形七件套须在卷）: %s" % main_path
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
            "Main 真形步名咬合失守（16 枚·序按 coq93.yml 实取）"
        assert all(s["conclusion"] == "success" for s in jm["steps"]), \
            "Main 绿样张应全步 success"
        # 确定性：Main 夹具同输入重跑 --json 字节级恒同
        out2 = os.path.join(tmp, "main_coq93.2.json")
        p = run(["--offline", main_path, "--json", out2])
        assert p.returncode == 0, p.stdout[-400:]
        assert io.open(out2, "rb").read() == io.open(out, "rb").read(), \
            "Main 形 json 字节漂移＝违例"
        # 兼容表逐行机检（真形单红步形·无日志·判类序 步名 B 先于 步名 A）
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
                ("Main 形判读矢失配", nm, fam, c["family"])
        # 词面暗礁/搭便机制钉：gate4=artifact 子串→步名 B 先判（勘形 §3.1
        # 暗礁行·Set :120 同款非 Main 新增）；gate1=pre-build 子串→步名 A 搭便
        c = classify(mkjob(id=33, steps=[mkstep(
            1, "gate4 comment guard (pre-build, exit1=red exit2=yellow"
               " artifact-only)", "failure")]))
        assert c["family"] == "B-netred" and any(
            "网络邻接步" in e and "artifact" in e for e in c["evidence"]), c
        c = classify(mkjob(id=34, steps=[mkstep(
            1, "gate1 poison-token guard (pre-build fail-fast)", "failure")]))
        assert c["family"] == "A-content-red" and any(
            "内容步" in e for e in c["evidence"]), c
        # E 族 Main 形两件齐（勘形 §3.1 E 行：上传红＋coqchk skipped·
        # Main 步名两件齐→E 可发）：Upload coqchk logs 红＋coqchk 步 skipped
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

        # 〔十〕gate2-only E 变体判读矢＋logs 两跳 415 修法矢（20261112·
        # Main retro 六事件证据人工指认入谱·全部 canned 零网络）
        # 1) 两件新 fixture（真形自 retro 台账 run#7 cancelled／run#10 failure）
        #    全命中 E 变体（family/action/连坐注记/红步咬合）
        for stem, concl in (("gate2_only_cancelled", "cancelled"),
                            ("gate2_only_failure", "failure")):
            path = fx(stem)
            assert os.path.isfile(path), "gate2-only fixture 缺失: %s" % path
            out = os.path.join(tmp, stem + ".json")
            p = run(["--offline", path, "--json", out])
            assert p.returncode == 0, p.stdout[-400:]
            rep = json.load(io.open(out, encoding="utf-8"))
            assert rep["schema"] == SCHEMA and rep["family"] \
                == "E-coqchk-skipped" \
                and rep["action"] == "rerun-after-stable-window", \
                (stem, rep["family"], rep["action"])
            assert rep["jobs"][0]["conclusion"] == concl, \
                (stem, rep["jobs"][0]["conclusion"])
            cj = rep["jobs"][0]["classification"]
            assert cj["family"] == "E-coqchk-skipped" and any(
                "gate2-only 连坐" in e for e in cj["evidence"]), cj
            assert cj["red_steps"] == [
                "gate2 axioms sentinel (block-state-machine, fail-loud;"
                " attest branch)"], cj["red_steps"]
        # 2) 规则正判（classify 直调·canned 形）：run#7 形 cancelled＋唯 gate2 红
        #    → E 变体；log GATE-BANNER-ABSENT 词面入证据（第三件）
        g2_steps = [mkstep(1, "Build full tree (order topology, fingerprint"
                           " skip, thermal-guarded)", "cancelled"),
                    mkstep(2, "coqchk full-tree certification (parallel"
                              " root-grouped, thermal-guarded)", "skipped",
                           started_at=None, completed_at=None),
                    mkstep(3, "gate2 axioms sentinel (block-state-machine,"
                              " fail-loud; attest branch)", "failure")]
        c = classify(mkjob(id=71, conclusion="cancelled", steps=g2_steps))
        assert c["family"] == "E-coqchk-skipped" \
            and c["action"] == "rerun-after-stable-window" \
            and any("gate2-only 连坐" in e for e in c["evidence"]), c
        c = classify(mkjob(id=72, conclusion="cancelled", steps=g2_steps),
                     log_text="2026-11-06T12:54:20Z gate2: "
                              "GATE-BANNER-ABSENT ledger missing\n")
        assert c["family"] == "E-coqchk-skipped" and any(
            "GATE-BANNER-ABSENT" in e for e in c["evidence"]), c
        # 3) 规则负判四发：build/coqchk proper content 红→A（连坐被破）；
        #    「Upload artifact (gate2 ledger)」gate2 子串搭便上传红→B（防误吞
        #    既钉）；非 gate2/上传红步→UNRECOGNIZED；零红步 failure（runner
        #    失联形＝出处六事件 #3）→UNRECOGNIZED 不充谱
        c = classify(mkjob(id=73, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", "failure"),
            mkstep(2, "gate2 axioms sentinel (block-state-machine,"
                     " fail-loud; attest branch)", "failure")]))
        assert c["family"] == "A-content-red", c
        c = classify(mkjob(id=74, steps=[
            mkstep(1, "coqchk full-tree certification (parallel"
                     " root-grouped, thermal-guarded)", "failure"),
            mkstep(2, "gate2 axioms sentinel (block-state-machine,"
                     " fail-loud; attest branch)", "failure")]))
        assert c["family"] == "A-content-red", c
        c = classify(mkjob(id=75, steps=[
            mkstep(1, "Upload artifact (gate2 ledger)", "failure"),
            mkstep(2, "COQCHK", "success")]))
        assert c["family"] == "B-netred", \
            "gate2 子串搭便上传红仍归 B（防误吞）实测 %s" % c["family"]
        c = classify(mkjob(id=76, steps=[
            mkstep(1, "Generate tree-stats (six-dimension counts,"
                     " three-caliber breakdown)", "failure")]))
        assert c["family"] == "UNRECOGNIZED", c
        c = classify(mkjob(id=77, steps=[
            mkstep(1, "Build full tree (order topology, fingerprint skip,"
                     " thermal-guarded)", None, status="in_progress",
                     conclusion=None)]))
        assert c["family"] == "UNRECOGNIZED", \
            "runner 失联零红步形仍谱外不充谱实测 %s" % c["family"]
        # 4) logs 两跳 415 修法矢（canned _open 注入·零网络）：
        #    修后形 hop1 Accept=LOGS_ACCEPT（≠text/plain 415 债）→ 302 Location
        #    → hop2 零 Authorization → 200 日志文本；旧形对照 415 原码入证据；
        #    第二跳 403 Azure 形原码入证据；重定向无 Location 形坏入证据。
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
            "第二跳须零 Authorization（带 token 转发 403 Azure 实测形）"
        assert h2.get("Accept") == LOGS_ACCEPT, h2
        assert slept == [], "两跳矢量零重试零睡"
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
        assert slept == [], "415 语义面不重试零睡"
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
        assert slept == [], "第二跳失败不重试零睡"

        def _open_noloc(req, timeout=None):
            raise _redirect_err(302, "")

        text, note = fetch_job_log("o/r", 42, "tok", 5,
                                   _open=_open_noloc, _sleep=slept.append)
        assert text is None and note is not None \
            and "无 Location" in note, (text, note)

        print("CI-TRIAGE-SELFTEST PASS: 五族+绿炉六样张全命中/基线 13.3x 判例+缺席"
              "响亮注记/分类器单元（regex 正负·连坐·在飞·E 勿当内容红·UNRECOGNIZED）/"
              "netrc 解析/确定性字节恒同/CLI 四码/韧性层退避（403×3→[2,4,8]·"
              "Retry-After 尊重·403 耗尽 9·401 不重试）/Main 形判读矢（coq93 真形"
              " 16 步咬合+兼容表 15 行+E 两件齐）/〔十〕gate2-only E 变体矢"
              "（两 fixture 全命中+正判+负判四发·六事件 #3 不充谱）+logs 两跳"
              " 415 修法矢（302→零 Authorization 第二跳 200·415/403/无 Location"
              " 原码入证据） 全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
