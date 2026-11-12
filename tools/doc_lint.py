#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doc_lint.py — 文档←→实现一致性三查器（docs↔tools 对账·防文档漂移·rocqwash
tools/·v38 工装席任务书·20261111 入账）

三查（全部纯本地·零网络零编译·python3 纯 stdlib·编排零新引擎——解析规则逐条
锚在盘件现行行，不发明新形）：
  ①工具表查＝cw.sh 头注/usage/hint/case 四处工具清单互检＋与 tools/ 目录实有
    通用入口对账（路由缺/表多/表少逐条列）。四处＝头注工具表（cw.sh:10-50·name
    desc -> path·两行折行体 cw.sh:25-26 doctor 等同形）、usage() heredoc 工具表
    （cw.sh:83-124）、hint_for() 一行提示（cw.sh:133-153·echo 串尾缀 -> path）、
    case 分派（cw.sh:170-186·run_tool <name> "<rel>"）。互检＝有路由者四处俱在
    （缺一处即表少·逐器逐处列）＋四处路径逐器咬合（不符/缺 -> 路径即列）；
    对账＝case 路由目标缺盘即「表多（悬路由）」、tools/ 非 _ 前缀 .py（通用
    入口·定义锚 cli/rocqwash:9「模块目录下唯一一个不带前导下划线的 .py」）
    无 case 路由即「路由缺」。help 为伪路由不参赛（cw.sh:49 头注行＋
    cw.sh:187 help|-h|--help 特例分派·hint_for 无分支——四处本就不对称）。
  ②计数查＝tests/run_tests.sh CASES 数（run_tests.sh:140-192 静态在册例·
    t_fail_probe 为 FAIL_PROBE 自检注入例不计·run_tests.sh:194-197）vs
    tests/README.md 计数行（:12「预期 52 过」＋:15「## 覆盖面（52 例）」）vs
    README.md 例数行（:59「自测套件（52 例）— test suite (52 cases)」）——
    数值三处一致·漂移即列；计数行形未现＝计数行缺失亦列。README.md:83/92/
    101/112/123/139/156「扩至 N 例」等增补史行为版本化历史非现势计数（逐轮
    累进属设计内·v38 轮 cw.sh:2「共十六」同款史行）·不在对账面——只锚上述
    四形，宁缺毋滥不造新计数形。
  ③旗标查＝README-cw.md/README.md/examples/workflows/*.md/docs/*.md（docs/
    递归·*.zh.md 与 docs/zh/ 归档面免扫——注释规范卡 §5.2 归档件非正本面）
    中引用的器旗标（--xxx 形）逐枚对照各器 --help 实出输出
    （subprocess 真跑 --help·rc!=0/超时=器红 fail-loud 9·帽 --help-cap 25 器）。
    器集＝cw.sh 路由 ∪ tools/ 非 _ 前缀 .py＝25 器（现势·帽 25 有余）；
    超帽按典序截断·溢出器如实列「未实跑 --help·引用 N 处未证」。归账规则＝
    器引用两级（一级强引用＝盘路径形/cli/rocqwash/cw.sh 路由形·二级弱引用＝
    裸名形——路由名/器 stem/在盘 oos 器 stem），旗标归其逻辑行最近前驱一级
    引用·无则二级（README.md:232「cli/rocqwash certify push_gate union-freeze
    --world…」内 union-freeze 裸名 union 不得咬走 primary 的实证律）；旗标
    token 先掩码再找器引用（防 --probe-resume 内 \bprobe\b 误吞）。池兜底三
    路：散文段＝空行/围栏/标题界整段引用两遍收集（段首旗标如 README-cw.md:77
    「① --once/--loop 双模」实证）；代码围栏命令行＝反斜杠续行拼行后严格
    只在命令自身内归账（幻引判定最强面）；代码围栏注释行＝块池归账
    （step-pushci.md:75-77「# 可选追加：--pre-scan-gate4／--merge…」实形）。漂移两向＝
    缺旗标（幻引/多余引用·同面两词：doc 侧引用为多余·器侧实出缺此旗标——
    primary 器 help 实出无＋池内 registry 器全缺＋池内无可证 oos/unknown 器；
    「同一旗标 token 重复≥2 即多余」的机械判据被 README.md:232 union-freeze
    --world wa=… --world wb=… 合法多值实证否弃·不采）＋悬引（primary 引用
    不识——cw.sh 非路由/路由目标缺盘而旗标无器可证；cw.sh bogus 等退出码
    示例行无旗标故不误咬）。无主旗标与池含 oos/unknown 器者＝unresolved
    如实计不判漂（不可证≠漂——docs/zh/architecture.md:54 台账行「--json/
    --hits-csv」属 scan 阶段件 mac_stmt_scan、上下文在文档节层·机检不可归账
    不作漂判的实证律）。cli/rocqwash 及 registry 外器（certify/watch/wrapper/
    战役件等）旗标非本查对象——计入 out_of_scope 如实出账（cli/rocqwash 为
    v29 前路由层·旗标属子工具·cli/rocqwash:8-11 路由契约）。
    argparse 折行复原：break_on_hyphens 断词实出「--on-red-<LF>arg」（cw_sentinel
    --help 实证）——(--tok)-\n<ws>(cont) 复原后再取 token；registry_union --help:14
    「--ref-*」词面为 glob 散文·截断 token 属噪音不害幻引判定（本查只单向
    doc→help：help 散文多收旗标仅致漏报不致误报——精度换零误报·宁缺毋滥）。

输出：--json report schema=rocqwash-doclint/1（checks[{kind,target,status,
detail}]·verdict consistent|drift·counts·out_of_scope·registry·args·sort_keys
落盘·无墙钟字段·路径一律仓相对——同输入重跑字节恒同）。checks 逐条列：
kind∈{tool_table,count,flag}·status∈{ok,drift}·detail 单行（截 300 字符）。

退出码：0=consistent（三查零漂）；1=drift（任一条 drift·红是数据非器红·
响亮 stdout）；2=用法错（argparse/--help-cap<1）；9=缺（--repo 缺目录/被审
仓必需输入缺失：cw.sh·README.md·README-cw.md·tests/run_tests.sh·
tests/README.md·docs/·examples/workflows/·--json 父目录缺·器 --help 器红/
超时·doc 件不可解码）。

本器一次性静态对账·无巡检环——--once/--loop 无涉（cw_doctor 同例）；子进程
仅本地 --help 真跑（毫秒级·零网络零编译零睡）——--injector/--sleep-scale 无涉
·离线天然可测（--selftest 全 tmp 迷你仓夹具）。

--selftest 矢量（tmp 迷你仓 fixture·四判＋CLI 三码＋幂等一判）：
  V1 一致迷你仓（2 路由四处齐·计数 2 三处一致·旗标实引全证）→ rc0·verdict
     consistent·checks 零 drift。
  V2 工具表缺一（hint_for 摘 b 行）→ rc1·tool_table drift 指向 cw.sh:hint。
  V3 计数漂（tests/README.md 覆盖面改 3）→ rc1·count drift 数值 3≠2。
  V4 旗标幻引（docs/note.md 增 --bogus-flag 引用）→ rc1·flag drift 幻引。
  V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9）＋--help-cap 0→2。
  V6 JSON 幂等（同仓两跑异 --json 路径字节恒同——report 不嵌 json 路径）。

用法（全部路径参数化·零硬编码）：
  python3 tools/doc_lint.py [--repo DIR] [--json OUT] [--help-cap N]
  python3 tools/doc_lint.py --selftest
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROG = "doc_lint"
SCHEMA = "rocqwash-doclint/1"

DEFAULT_HELP_CAP = 27     # ③ --help 真跑器帽（v38 波 20→24 换代·v46 时点 23 器有余——集成席登记帽溢出 cure_applier/probe_engine 后主会话裁决换代·注释面规范化波 tools/norm_lint.py 入册后 25 器——帽溢出 wash/probe_engine.py 同 precedent 换代 24→25）— tools/registry_regen.py registered as the 26th tool: cap raised 25->26, same precedent as the 24->25 bump at the norm-lint registration — tools/contrib_intake.py registered as the 27th tool: cap raised 26->27, same precedent (registry_rel sorted order again puts wash/probe_engine.py last; its doc-flag references need the real --help run to stay phantom-free)
HELP_TIMEOUT = 60         # --help 子进程秒帽（本地件防挂·fail-loud）
DETAIL_CAP = 300          # checks[].detail 截断（cw_doctor non_form ln[:120] 同款）
DRIFT_LINE_CAP = 20       # ③ 每文件幻引/悬引列帽（总数如实·cw_doctor 帽 20 同款）
LIST_CAP = 20             # out_of_scope/registry 溢出清单帽（总数如实）

PSEUDO_ROUTES = ("help",)  # 伪路由（cw.sh:49 头注行·cw.sh:187 特例分派）

# 仓级通用器旗标（不入幻引判定）：--help 恒有；--selftest 承套件纪律——
# run_tests.sh 在册各器例全数真跑 --selftest（t_scan_selftest:t_cw_doctor
# 十二器直跑＋t_cw_sentinel/t_wash_shape/t_unclog 同），部分器以 pre-argparse
# 形处理（cw_doctor.py:1014 `if "--selftest" in argv` 先于 argparse 同款）
# 致 --help 输出不列——按 help 缺失判幻引即误报，故恒认。
UNIVERSAL_FLAGS = ("--help", "--selftest")

PLACE_ORDER = ("header", "usage", "hint", "case")

# ---- ① cw.sh 四处解析正则（1:1 锚 cw.sh 现行行·见 docstring 引据）----
ROUTE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROW_PATH_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\s+.*->\s*(\S+)\s*$")
CONT_PATH_RE = re.compile(r"^->\s*(\S+)\s*$")
PENDING_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\s+\S")
TABLE_STOP_RE = re.compile(r"^(路由契约|退出码|路由说明|覆盖面注)")
HINT_RE = re.compile(r'^\s*([a-z0-9][a-z0-9-]*)\)\s+echo\s+"(.+)"\s*;;\s*$')
HINT_PATH_RE = re.compile(r"->\s*(\S+)\s*$")
CASE_RE = re.compile(
    r'^\s*([a-z0-9][a-z0-9-]*)\)\s+shift;\s*run_tool\s+\S+\s+"([^"]+)"')

# ---- ② 计数行形（1:1 锚 tests/README.md:12/:15·README.md:59 现行行）----
COUNT_PATTERNS = (
    ("tests/README.md", re.compile(r"覆盖面（(\d+) 例）"), "覆盖面（N 例）"),
    ("tests/README.md", re.compile(r"预期 (\d+) 过"), "预期 N 过"),
    ("README.md", re.compile(r"自测套件（(\d+) 例）"), "自测套件（N 例）"),
    ("README.md", re.compile(r"test suite \((\d+) cases\)"),
     "test suite (N cases)"),
)
CASES_RE = re.compile(r'(?ms)^CASES="(.*?)"')

# ---- ③ doc 扫描正则 ----
FLAG_RE = re.compile(r"--[A-Za-z0-9][A-Za-z0-9_-]*")
# argparse break_on_hyphens 折行复原：(--tok)-\n<ws>(cont) → --tok-cont
HYPHEN_WRAP_RE = re.compile(
    r"(--[A-Za-z0-9][A-Za-z0-9_-]*)-\n\s*([A-Za-z0-9][A-Za-z0-9_-]*)")
HELP_TOKEN_RE = re.compile(r"--([A-Za-z0-9][A-Za-z0-9_-]*)")
PATH_RE = re.compile(
    r"\b((?:tools|wash|scan|verify|certify|wrapper|watch|seam|names|recipes"
    r"|examples|docs|tests)/[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh))\b")
CLI_RE = re.compile(r"\bcli/rocqwash\b")
ROUTE_MENTION_RE = re.compile(r"\bcw\.sh\s+([a-z][a-z0-9-]*)")


class UsageError(Exception):
    """用法错/值校验败（exit 2）。"""


class MissingInput(Exception):
    """输入缺失（exit 9）。"""


class ToolError(Exception):
    """器红/--help 失败（exit 9·fail-loud 禁静默降级）。"""


# ---- 小件（确定性 helpers·cw_doctor 同款本地副本·无包结构不互 import）----

def read_text(path, what):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as e:
        raise MissingInput("%s 不可读/解码失败: %s (%s)" % (what, path, e))


def dump_json(obj, path):
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as e:
        raise MissingInput("--json 落盘失败: %s (%s)" % (path, e))


def rel_of(repo, p):
    """仓相对路径（确定性·报告零绝对路径纪律）。"""
    return os.path.relpath(p, repo).replace(os.sep, "/")


def clip(s, cap=DETAIL_CAP):
    s = s if isinstance(s, str) else str(s)
    return s if len(s) <= cap else s[:cap - 1] + "…"


def line_no_of(text, pos):
    return text[:pos].count("\n") + 1


# ---- ① 工具表查 ----------------------------------------------------------------

def parse_table_rows(lines, ln0):
    """表体行 → {name: {"path": str|None, "line": int}}（仅认路由名形
    ^[a-z0-9][a-z0-9-]*$·三体：单行 name desc -> path／续行 -> path／折行
    pending name 待续行赋 path·cw.sh:25-26 doctor 折行体 1:1）。
    路由契约/退出码等段界行截停（TABLE_STOP_RE）。"""
    rows = {}
    pending = None
    for i, raw in enumerate(lines):
        s = raw.lstrip("#").strip()
        no = ln0 + i + 1
        if TABLE_STOP_RE.match(s):
            break
        if not s:
            pending = None
            continue
        m = CONT_PATH_RE.match(s)
        if m is not None:
            if pending is not None and pending in rows \
                    and rows[pending]["path"] is None:
                rows[pending]["path"] = m.group(1)
            pending = None
            continue
        m = ROW_PATH_RE.match(s)
        if m is not None:
            rows[m.group(1)] = {"path": m.group(2), "line": no}
            pending = None
            continue
        m = PENDING_RE.match(s)
        if m is not None:
            name = m.group(1)
            if name not in rows:
                rows[name] = {"path": None, "line": no}
            pending = name
            continue
        pending = None
    return rows


def parse_cw_sh(repo):
    """cw.sh 四处清单解析 → {place: {name: {"path", "line"}}}。
    区域界锚：头注至首个 set -u（cw.sh:73）；usage 至首 EOF（heredoc 终）；
    hint_for 至首个列 0 }；case 至 EOF（case "${1:-}" in 唯一分派 case·
    hint_for 内 case "$1" in 不误咬）。"""
    path = os.path.join(repo, "cw.sh")
    if not os.path.isfile(path):
        raise MissingInput("被审仓缺 cw.sh: %s" % path)
    text = read_text(path, "cw.sh")
    lines = text.split("\n")

    def idx_of(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        return None

    setu = idx_of(lambda ln: ln.strip() == "set -u")
    if setu is None:
        raise ToolError("cw.sh 形不识（无 set -u 界）: %s" % path)
    u_start = idx_of(lambda ln: "usage() {" in ln)
    u_end = idx_of(lambda ln: ln.strip() == "EOF",
                   (u_start + 1) if u_start is not None else 0)
    h_start = idx_of(lambda ln: "hint_for() {" in ln)
    h_end = idx_of(lambda ln: ln.rstrip() == "}",
                   (h_start + 1) if h_start is not None else 0)
    c_start = idx_of(lambda ln: 'case "${1:-}" in' in ln)
    if u_start is None or h_start is None or c_start is None:
        raise ToolError("cw.sh 形不识（usage/hint_for/case 界缺一）: %s" % path)

    def table_start(lines, lo, hi, marker):
        seg = idx_of(lambda ln: marker in ln, lo)
        return seg if seg is not None and seg < hi else lo

    hdr_lo = table_start(lines, 0, setu, "工具表 Tools")
    hdr = parse_table_rows(lines[hdr_lo:setu], hdr_lo)
    usg_lo = table_start(lines, u_start, u_end, "工具 Tools:")
    usg = parse_table_rows(lines[usg_lo:u_end], usg_lo)
    hint = {}
    for i in range(h_start, (h_end if h_end is not None else len(lines))):
        m = HINT_RE.match(lines[i])
        if m is None:
            continue
        hp = HINT_PATH_RE.search(m.group(2))
        hint[m.group(1)] = {"path": hp.group(1) if hp else None,
                            "line": i + 1}
    case = {}
    for i in range(c_start, len(lines)):
        m = CASE_RE.match(lines[i])
        if m is None:
            continue
        case[m.group(1)] = {"path": m.group(2), "line": i + 1}
    return {"header": hdr, "usage": usg, "hint": hint, "case": case}


def check_tool_table(repo, places):
    """①四处互检＋tools/ 通用入口对账 → checks 列表（逐条·kind=tool_table）。"""
    checks = []
    routed = set(places["case"]) - set(PSEUDO_ROUTES)
    # 四处互检：有路由者四处俱在（表少/悬名逐器逐处列）
    for place in PLACE_ORDER:
        names = set(places[place]) - set(PSEUDO_ROUTES)
        for t in sorted(routed - names):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:%s" % place, "status": "drift",
                           "detail": clip("工具 %s 于 case 路由在册而 %s 表缺行"
                                          "（互检表少）" % (t, place))})
        for t in sorted(names - routed):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:%s:%s" % (place, t),
                           "status": "drift",
                           "detail": clip("工具 %s 仅 %s 表在册而 case 无路由"
                                          "（互检悬名）" % (t, place))})
    # 路径逐器咬合（case 路径为正·他处缺失/不符即列）
    for t in sorted(routed):
        for place in PLACE_ORDER[:-1]:
            ent = places[place].get(t)
            if ent is None:
                continue
            if ent["path"] is None:
                checks.append({"kind": "tool_table",
                               "target": "cw.sh:%s:%s" % (place, t),
                               "status": "drift",
                               "detail": clip("工具 %s 于 %s 行缺 -> 路径"
                                              "（折行体断裂）" % (t, place))})
            elif ent["path"] != places["case"][t]["path"]:
                checks.append({"kind": "tool_table",
                               "target": "cw.sh:%s:%s" % (place, t),
                               "status": "drift",
                               "detail": clip("工具 %s 路径不一：%s=%s vs "
                                              "case=%s" % (t, place,
                                                           ent["path"],
                                                           places["case"][t]
                                                           ["path"]))})
    # 对账：case 路由目标缺盘＝表多（悬路由）
    tools_dir = os.path.join(repo, "tools")
    if not os.path.isdir(tools_dir):
        raise MissingInput("被审仓缺 tools/ 目录: %s" % tools_dir)
    for t in sorted(routed):
        p = places["case"][t]["path"]
        if not os.path.isfile(os.path.join(repo, p)):
            checks.append({"kind": "tool_table",
                           "target": "cw.sh:case:%s" % t, "status": "drift",
                           "detail": clip("路由目标缺盘 %s（表多·悬路由）"
                                          % p)})
    # 对账：tools/ 非 _ 前缀 .py 无 case 路由＝路由缺（cli/rocqwash:9 定义）
    generic = sorted(fn for fn in os.listdir(tools_dir)
                     if fn.endswith(".py") and not fn.startswith("_"))
    routed_paths = set(places["case"][t]["path"] for t in routed)
    unrouted = []
    for fn in generic:
        rel = "tools/" + fn
        if rel not in routed_paths:
            unrouted.append(rel)
            checks.append({"kind": "tool_table", "target": rel,
                           "status": "drift",
                           "detail": clip("tools/ 通用入口（cli/rocqwash:9 "
                                          "非 _ 前缀 .py 定义）无 cw.sh case "
                                          "路由（路由缺）")})
    if not checks:
        checks.append({"kind": "tool_table", "target": "cw.sh 四处＋tools/",
                       "status": "ok",
                       "detail": clip("互检一致（%d 器四处齐·路径咬合）＋对账"
                                      "零缺口（tools/ 通用入口 %d 全路由）"
                                      % (len(routed), len(generic)))})
    registry_rel = sorted(set(routed_paths) |
                          set("tools/" + fn for fn in generic))
    return checks, registry_rel, unrouted


# ---- ② 计数查 -----------------------------------------------------------------

def check_counts(repo):
    """②CASES 数 vs tests/README.md 计数行 vs README.md 例数行 → checks。"""
    checks = []
    rt_rel = "tests/run_tests.sh"
    rt_path = os.path.join(repo, rt_rel)
    if not os.path.isfile(rt_path):
        raise MissingInput("被审仓缺 %s: %s" % (rt_rel, rt_path))
    rt_text = read_text(rt_path, rt_rel)
    m = CASES_RE.search(rt_text)
    if m is None:
        raise ToolError("run_tests.sh 形不识（CASES=\" 块缺）: %s" % rt_path)
    # bash 引号串内反斜杠续行（run_tests.sh:140 `CASES="\`＋逐行尾 `\`）还原
    # 成空白后再取 token——字面 `\` 不是用例名
    tokens = m.group(1).replace("\\\n", " ").split()
    cases_n = len(tokens)
    cases_line = line_no_of(rt_text, m.start())
    checks.append({"kind": "count", "target": "%s:%d" % (rt_rel, cases_line),
                   "status": "ok",
                   "detail": clip("CASES 在册 %d 例（静态在册·t_fail_probe 为"
                                  " FAIL_PROBE 注入例不计）" % cases_n)})
    for rel, rx, label in COUNT_PATTERNS:
        fpath = os.path.join(repo, rel)
        if not os.path.isfile(fpath):
            raise MissingInput("被审仓缺 %s: %s" % (rel, fpath))
        text = read_text(fpath, rel)
        hits = list(rx.finditer(text))
        if not hits:
            checks.append({"kind": "count", "target": rel, "status": "drift",
                           "detail": clip("计数行形「%s」未现（计数行缺失）"
                                          % label)})
            continue
        for h in hits:
            no = line_no_of(text, h.start())
            val = int(h.group(1))
            if val == cases_n:
                checks.append({"kind": "count",
                               "target": "%s:%d" % (rel, no), "status": "ok",
                               "detail": clip("「%s」＝%d 与 CASES %d 一致"
                                              % (label, val, cases_n))})
            else:
                checks.append({"kind": "count",
                               "target": "%s:%d" % (rel, no),
                               "status": "drift",
                               "detail": clip("「%s」＝%d ≠ CASES %d（计数漂）"
                                              % (label, val, cases_n))})
    return checks, cases_n


# ---- ③ 旗标查 -----------------------------------------------------------------

def run_help_flags(repo, rel):
    """subprocess 真跑 --help → 实出旗标集（含折行复原）。rc!=0/超时=器红 9。"""
    p = os.path.join(repo, rel)
    try:
        pr = subprocess.run([sys.executable, "-B", p, "--help"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=HELP_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise ToolError("--help 超时（>%ds）: %s (%s)" % (HELP_TIMEOUT, rel, e))
    out = pr.stdout.decode("utf-8", "replace") if isinstance(pr.stdout, bytes) \
        else (pr.stdout or "")
    if pr.returncode != 0:
        raise ToolError("--help 器红 rc=%d: %s (%s)" % (pr.returncode, rel,
                                                        out[-200:]))
    fixed = HYPHEN_WRAP_RE.sub(r"\1-\2", out)
    return set("--" + t for t in HELP_TOKEN_RE.findall(fixed))


class LintCtx(object):
    """③扫描上下文：器集映射＋help 实出集＋账面。
    器引用两级：一级强引用（盘路径形/cli/rocqwash/cw.sh 路由形）·二级弱引用
    （裸名形——路由名/器 stem/在盘 oos 器 stem）。primary 取行内最近前驱一级
    引用·无则二级（防 README.md:232「cli/rocqwash certify push_gate
    union-freeze --world…」内 union-freeze 的裸名 union 咬走 primary）。"""

    def __init__(self, repo, registry_rel, route_map, help_cap):
        self.repo = repo
        self.route_map = dict(route_map)
        self.stem_map = {}
        for rel in registry_rel:
            base = os.path.basename(rel)
            if base.endswith(".py"):
                self.stem_map[base[:-3]] = rel
        # 在盘 oos 器 stem（模块目录非 _ 前缀 .py＋tools/*.sh·registry 除外）——
        # 令「wash_engine.py」等裸件名引用可归账为 oos（不可证但可归·非无主）
        self.oos_stem_map = {}
        for d in ("tools", "wash", "scan", "verify", "certify", "wrapper",
                  "watch", "seam", "names", "recipes"):
            dd = os.path.join(repo, d)
            if not os.path.isdir(dd):
                continue
            for fn in sorted(os.listdir(dd)):
                stem = None
                if fn.endswith(".py") and not fn.startswith("_"):
                    stem = fn[:-3]
                elif d == "tools" and fn.endswith(".sh"):
                    stem = fn[:-3]
                if stem is None:
                    continue
                rel = d + "/" + fn
                if not os.path.isfile(os.path.join(repo, rel)) \
                        or rel in set(registry_rel):
                    continue
                self.oos_stem_map.setdefault(stem, rel)
        names = sorted(set(self.route_map) - set(PSEUDO_ROUTES) |
                       set(self.stem_map) | set(self.oos_stem_map),
                       key=lambda s: (-len(s), s))
        self.bare_re = re.compile(
            r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")
        self.registry = set(registry_rel)
        self.help = {}
        self.help_order = [r for r in registry_rel
                           if os.path.isfile(os.path.join(repo, r))]
        self.overflow = self.help_order[help_cap:]
        self.help_order = self.help_order[:help_cap]
        self.oos = {}          # (file_rel, target) → refs
        self.oos_total = 0

    def load_helps(self):
        """逐器真跑 --help（典序·帽内）→ help 集（并集仓级通用旗标——
        UNIVERSAL_FLAGS 注）。"""
        for rel in self.help_order:
            self.help[rel] = run_help_flags(self.repo, rel) | set(
                UNIVERSAL_FLAGS)

    def resolve_path(self, p):
        if p in self.registry:
            return ("tool", p)
        if os.path.isfile(os.path.join(self.repo, p)):
            return ("oos", p)
        return ("unknown", p)

    def resolve_route(self, r):
        if r in PSEUDO_ROUTES:
            return None
        p = self.route_map.get(r)
        if p is None:
            return ("unknown", "cw.sh %s（非路由）" % r)
        if not os.path.isfile(os.path.join(self.repo, p)):
            return ("unknown", "cw.sh %s（路由目标缺盘 %s）" % (r, p))
        return ("tool", p)

    def resolve_bare(self, b):
        p = self.route_map.get(b) or self.stem_map.get(b)
        if p:
            return ("tool", p)
        q = self.oos_stem_map.get(b)
        if q:
            return ("oos", q)
        return None


def doc_files(repo):
    """③ 对账面文件序（README 系→examples/workflows/*.md→docs/ 递归·典序）。"""
    out = ["README-cw.md", "README.md"]
    wf = os.path.join(repo, "examples", "workflows")
    if not os.path.isdir(wf):
        raise MissingInput("被审仓缺 examples/workflows/: %s" % wf)
    out += sorted("examples/workflows/" + fn
                  for fn in os.listdir(wf) if fn.endswith(".md"))
    dd = os.path.join(repo, "docs")
    if not os.path.isdir(dd):
        raise MissingInput("被审仓缺 docs/: %s" % dd)
    for dirpath, dirnames, filenames in os.walk(dd):
        dirnames.sort()
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            rel = rel_of(repo, os.path.join(dirpath, fn))
            # 注释规范卡 §5.2：归档件非正本面——*.zh.md 同目录留档形与
            # docs/zh/ 追认形为冻结历史存档（声明不随代码演进维护），
            # 对活实现的一致性查在其上无意义，免扫
            if rel.startswith("docs/zh/") or rel.endswith(".zh.md"):
                continue
            out.append(rel)
    return out


def scan_doc(repo, rel, ctx):
    """单文件 ③ 扫描 → (item, drift_n, refs_n)。
    三路归账：①散文段＝空行/围栏/标题界的整段两遍处理（一遍收全段引用池·
    二遍逐行归账——段首旗标如 README-cw.md:77「① --once/--loop 双模」前驱
    无器引用，段池兜底）；②代码围栏命令行＝反斜杠续行拼行后逐命令严格归账
    （池＝命令自身引用·幻引判定最强面）；③代码围栏注释行（step-pushci.md:75-77
    「# 可选追加：--pre-scan-gate4…」实形）＝块池归账（全块引用两遍收集）。
    引用两级：一级（路径/cli/路由）＞二级（裸名）——primary 取最近前驱一级·
    无则二级。漂移两向：缺旗标（幻引/多余引用——primary 器 help 实出无此
    旗标＋池内 registry 器全缺＋池内无可证 oos/unknown 器）；悬引（primary
    引用不识——cw.sh 非路由/路由目标缺盘）。无主旗标与池含 oos/unknown 者
    ＝unresolved 如实计（不可证≠漂——zh/en architecture 台账行「--json/
    --hits-csv」属 scan 阶段件 mac_stmt_scan 实证：上下文在文档节层·机检
    不可归账不作漂判）。旗标 token 先掩码再找器引用（防 --probe-resume 内
    \\bprobe\\b 误吞）。"""
    text = read_text(os.path.join(repo, rel), rel)
    lines = text.split("\n")
    drifts = []            # (line_no, detail)
    refs_total = [0]
    unres_total = [0]
    oos_local = [0]
    in_code = False
    para = []              # 散文段缓冲 [(line_no, seg)]
    code_block = []        # 代码块逻辑行缓冲 [(line_no, joined)]
    cur = []               # 代码续行拼装缓冲 [(line_no, seg)]
    pend_join = False

    def mentions_of(seg):
        """→ (mentions 有序[(pos, tier, (kind,key))], flag_hits[(pos,tok)])。
        tier 1＝路径/cli/路由强引用·2＝裸名弱引用。旗标 token 先掩码（同长
        空格·位置不漂）再找器引用。"""
        flag_hits = [(m.start(), m.group(0)) for m in FLAG_RE.finditer(seg)]
        masked = FLAG_RE.sub(lambda m: " " * len(m.group(0)), seg)
        mentions = []
        for m in PATH_RE.finditer(masked):
            mentions.append((m.start(), 1, ctx.resolve_path(m.group(1))))
        for m in CLI_RE.finditer(masked):
            mentions.append((m.start(), 1, ("oos", "cli/rocqwash")))
        for m in ROUTE_MENTION_RE.finditer(masked):
            ent = ctx.resolve_route(m.group(1))
            if ent is not None:
                mentions.append((m.start(), 1, ent))
        for m in ctx.bare_re.finditer(masked):
            ent = ctx.resolve_bare(m.group(1))
            if ent is not None:
                mentions.append((m.start(), 2, ent))
        mentions.sort(key=lambda t: (t[0], t[1]))
        return mentions, flag_hits

    def account(no, mentions, flag_hits, pool):
        """单逻辑行归账 → (drifts, refs, unresolved)。primary＝行内最近前驱
        一级引用·无则二级；pool＝兜底池（kind-tagged·tool/oos/unknown）。"""
        out = []
        refs = 0
        unres = 0
        reg_pool = list(dict.fromkeys(
            k for kind, k in pool if kind == "tool"))
        unverifiable = any(kind in ("oos", "unknown") for kind, _ in pool)
        for pos, tok in flag_hits:
            refs += 1
            prim = None
            for mpos, _tier, ent in reversed(mentions):
                if mpos < pos:
                    prim = ent
                    break
            kind, key = prim if prim is not None else (None, None)
            if kind == "tool":
                if tok in ctx.help.get(key, set()):
                    continue
                if any(tok in ctx.help.get(t, set()) for t in reg_pool):
                    continue
                if unverifiable:
                    unres += 1
                    continue
                out.append((no, "缺旗标（幻引/多余引用）：%s 前最近器 %s "
                                "help 实出无此旗标（实出 %d 枚）·池 %s 亦无"
                                % (tok, key,
                                   len(ctx.help.get(key, set())),
                                   ",".join(reg_pool) if reg_pool else "空")))
            elif kind == "oos":
                ek = (rel, key)
                ctx.oos[ek] = ctx.oos.get(ek, 0) + 1
                ctx.oos_total += 1
                oos_local[0] += 1
            elif kind == "unknown":
                out.append((no, "悬引：旗标 %s 前最近器引用不识（%s）——无器"
                                "可证" % (tok, key)))
            else:
                if any(tok in ctx.help.get(t, set()) for t in reg_pool):
                    continue
                unres += 1
        return out, refs, unres

    def flush_code_block():
        """代码块两遍：一遍收全块引用池（注释行用）·二遍逐逻辑行归账
        （命令行严格自身池·注释行块池）。"""
        nonlocal code_block, drifts
        if not code_block:
            return
        buf = code_block
        code_block = []
        scanned = []
        block_pool = []
        for no, joined in buf:
            mentions, flags = mentions_of(joined)
            for _pos, _tier, ent in mentions:
                if ent not in block_pool:
                    block_pool.append(ent)
            scanned.append((no, joined, mentions, flags))
        for no, joined, mentions, flags in scanned:
            is_comment = joined.lstrip().startswith("#")
            pool = block_pool if is_comment else \
                [ent for _pos, _tier, ent in mentions]
            d, r, u = account(no, mentions, flags, pool)
            drifts.extend(d)
            refs_total[0] += r
            unres_total[0] += u

    def flush_para():
        """散文段两遍：一遍收全段引用池·二遍逐行归账（段池兜底）。"""
        nonlocal para, drifts
        if not para:
            return
        buf = para
        para = []
        pool = []
        scanned = []
        for no, seg in buf:
            mentions, flags = mentions_of(seg)
            for _pos, _tier, ent in mentions:
                if ent not in pool:
                    pool.append(ent)
            scanned.append((no, seg, mentions, flags))
        for no, seg, mentions, flags in scanned:
            d, r, u = account(no, mentions, flags, pool)
            drifts.extend(d)
            refs_total[0] += r
            unres_total[0] += u

    def flush_join():
        """续行拼装收口 → 逻辑行入代码块缓冲。"""
        nonlocal cur, pend_join, code_block
        if not cur:
            return
        ln0 = cur[0][0]
        joined = " ".join(s for _, s in cur)
        code_block.append((ln0, joined))
        cur = []
        pend_join = False

    for no, raw in enumerate(lines, start=1):
        seg = raw.rstrip("\r")
        st = seg.strip()
        if st.startswith("```"):
            flush_para()
            if pend_join:
                cur.append((no, ""))
                flush_join()
            flush_code_block()
            in_code = not in_code
            continue
        if in_code:
            if pend_join:
                if seg.rstrip().endswith("\\") and len(seg.rstrip()) > 1:
                    cur.append((no, seg.rstrip()[:-1]))
                    continue
                cur.append((no, seg))
                flush_join()
                continue
            if seg.rstrip().endswith("\\") and len(seg.rstrip()) > 1:
                cur.append((no, seg.rstrip()[:-1]))
                pend_join = True
                continue
            cur.append((no, seg))
            flush_join()
            continue
        # 散文：标题行独立成段（防池跨节泄漏）·空行收段
        if st.startswith("#"):
            flush_para()
            para.append((no, seg))
            continue
        if not st:
            flush_para()
            continue
        para.append((no, seg))
    flush_para()
    if pend_join or cur:
        flush_join()
    flush_code_block()

    drift_n = len(drifts)
    parts = ["refs=%d" % refs_total[0], "unresolved=%d" % unres_total[0],
             "oos=%d" % oos_local[0]]
    if drift_n:
        shown = drifts[:DRIFT_LINE_CAP]
        parts.append("drift=%d" % drift_n)
        parts += ["L%d: %s" % (no, clip(d, 160)) for no, d in shown]
        if len(drifts) > DRIFT_LINE_CAP:
            parts.append("另 %d 条未列（帽 %d）"
                         % (len(drifts) - DRIFT_LINE_CAP, DRIFT_LINE_CAP))
    else:
        parts.append("drift=0")
    item = {"kind": "flag", "target": rel,
            "status": "drift" if drift_n else "ok",
            "detail": clip("；".join(parts))}
    return item, drift_n, refs_total[0]


def check_flags(repo, ctx):
    """③旗标查总控：help 真跑→逐件扫描→checks（每文件一项＋溢出器未证项）。"""
    checks = []
    files = doc_files(repo)
    ctx.load_helps()
    total_drift = 0
    for rel in files:
        item, drift_n, _refs = scan_doc(repo, rel, ctx)
        checks.append(item)
        total_drift += drift_n
    for ov_rel in ctx.overflow:
        n = _refs_for(ctx, files, ov_rel)
        if n:
            checks.append({"kind": "flag", "target": ov_rel,
                           "status": "drift",
                           "detail": clip("help 帽 %d 溢出未实跑 --help·doc "
                                          "引用 %d 处未证（旗标查未竟）"
                                          % (DEFAULT_HELP_CAP, n))})
    return checks, total_drift, files


def _refs_for(ctx, files, tool_rel):
    """溢出器在 doc 面的引用计数（重扫轻量：仅器引用不跑旗标判定）。"""
    n = 0
    for rel in files:
        text = read_text(os.path.join(ctx.repo, rel), rel)
        masked = FLAG_RE.sub(lambda m: " " * len(m.group(0)), text)
        for m in PATH_RE.finditer(masked):
            if ctx.resolve_path(m.group(1)) == ("tool", tool_rel):
                n += 1
        for m in ctx.bare_re.finditer(masked):
            if ctx.resolve_bare(m.group(1)) == ("tool", tool_rel):
                n += 1
    return n


# ---- 总控 ---------------------------------------------------------------------

def run(args):
    """总控：值校验（2）→被审仓先验（9）→①②③逐查→report（0/1）。"""
    if args.help_cap < 1:
        raise UsageError("--help-cap 须≥1 实测 %d" % args.help_cap)
    repo = args.repo
    if not os.path.isdir(repo):
        raise MissingInput("--repo 缺目录: %s" % repo)
    for req in ("cw.sh", "README.md", "README-cw.md", "tests/run_tests.sh",
                "tests/README.md"):
        if not os.path.isfile(os.path.join(repo, req)):
            raise MissingInput("被审仓必需输入缺失: %s" % req)
    print("=== DOC-LINT（文档←→实现一致性三查）=== repo=%s"
          % os.path.basename(os.path.abspath(repo)))

    # ①工具表查
    places = parse_cw_sh(repo)
    tt_checks, registry_rel, unrouted = check_tool_table(repo, places)
    route_map = {name: ent["path"] for name, ent in places["case"].items()
                 if name not in PSEUDO_ROUTES}
    print("[tool_table] checks=%d unrouted=%s"
          % (len(tt_checks), ",".join(unrouted) if unrouted else "无"))

    # ②计数查
    cnt_checks, cases_n = check_counts(repo)
    print("[count] CASES=%d checks=%d" % (cases_n, len(cnt_checks)))

    # ③旗标查
    ctx = LintCtx(repo, registry_rel, route_map, args.help_cap)
    flag_checks, flag_drift, files = check_flags(repo, ctx)
    print("[flag] docs=%d help_run=%d/%d（帽 %d）drift=%d"
          % (len(files), len(ctx.help_order), len(registry_rel),
             args.help_cap, flag_drift))

    checks = tt_checks + cnt_checks + flag_checks
    drift_n = sum(1 for c in checks if c["status"] == "drift")
    verdict = "drift" if drift_n else "consistent"
    counts = {}
    for kind in ("tool_table", "count", "flag"):
        counts[kind] = {
            "ok": sum(1 for c in checks
                      if c["kind"] == kind and c["status"] == "ok"),
            "drift": sum(1 for c in checks
                         if c["kind"] == kind and c["status"] == "drift")}
    oos_list = [{"file": f, "tool": t, "refs": n}
                for (f, t), n in sorted(ctx.oos.items())]
    report = {
        "schema": SCHEMA,
        "verdict": verdict,
        "repo": os.path.basename(os.path.abspath(repo)),
        "checks": checks,
        "counts": counts,
        "drift_total": drift_n,
        "out_of_scope": {"total": ctx.oos_total,
                         "refs": oos_list[:LIST_CAP],
                         "capped": max(0, len(oos_list) - LIST_CAP)},
        "registry": {"scripts": registry_rel,
                     "help_run": ctx.help_order,
                     "cap": args.help_cap,
                     "overflow": ctx.overflow},
        "args": {"repo": os.path.basename(os.path.abspath(repo)),
                 "help_cap": args.help_cap},
    }
    print("--- checks ---")
    for c in checks:
        print("  [%s] %-6s %s\n    %s"
              % (c["kind"], c["status"], c["target"], c["detail"]))
    if args.json:
        dump_json(report, args.json)
        print("json -> %s" % args.json)
    print("VERDICT: %s (exit %d)"
          % (verdict, 0 if verdict == "consistent" else 1))
    return 0 if verdict == "consistent" else 1


# ---- --selftest（tmp 迷你仓 fixture·四判＋CLI 三码＋幂等一判）-------------------

MINI_TOOL_A = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_a.py — 演示器甲（doc_lint --selftest 迷你仓夹具·旗标形制仿
scan_v4_token --file/--json 形）"""
import argparse
ap = argparse.ArgumentParser(prog="tool_a",
                             description="演示器甲：--file/--json 两旗标")
ap.add_argument("--file", metavar="F", help="目标件")
ap.add_argument("--json", metavar="OUT", help="报告出账")
ap.parse_args()
'''

MINI_TOOL_B = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tool_b.py — 演示器乙（doc_lint --selftest 迷你仓夹具·旗标形制仿
cure_applier --dir/--apply 形）"""
import argparse
ap = argparse.ArgumentParser(prog="tool_b",
                             description="演示器乙：--dir/--apply 两旗标")
ap.add_argument("--dir", metavar="DIR", help="目标目录")
ap.add_argument("--apply", action="store_true", help="落刀")
ap.parse_args()
'''


def make_mini_repo(root, hint_drop=None, count_drift=False, phantom=False):
    """tmp 迷你仓 fixture（形制 1:1 仿真仓四处：头注表/usage heredoc/hint_for/
    case 分派＋CASES 块＋三计数行＋doc 面）。落盘即返（None）。"""
    os.makedirs(os.path.join(root, "tools"))
    for name, body in (("tool_a.py", MINI_TOOL_A), ("tool_b.py", MINI_TOOL_B)):
        with io.open(os.path.join(root, "tools", name), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    hint_b = ('    b) echo "cw.sh b --dir DIR [--apply]   # 演示器乙 -> '
              'tools/tool_b.py" ;;\n') if hint_drop != "b" else ""
    cw = (
        "#!/usr/bin/env bash\n"
        "# cw.sh — mini fixture 统一入口（a/b 两器）\n"
        "#\n"
        "# 用法 Usage: bash cw.sh <tool> [args...]\n"
        "#\n"
        "# 工具表 Tools:\n"
        "#   a           演示器甲 -> tools/tool_a.py\n"
        "#               cw.sh a --file <f.v> [--json out.json]\n"
        "#   b           演示器乙 -> tools/tool_b.py\n"
        "#               cw.sh b --dir DIR [--apply]\n"
        "#   help        本帮助（help <tool> = 该工具一行提示）\n"
        "#\n"
        "# 路由契约 Routing contract:\n"
        "#   1. 参数与退出码 1:1 透传。\n"
        "set -u\n"
        "ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "usage() {\n"
        "  cat <<'EOF'\n"
        "cw.sh — mini fixture\n"
        "用法 Usage: bash cw.sh <tool> [args...]\n"
        "工具 Tools:\n"
        "  a           演示器甲 -> tools/tool_a.py\n"
        "  b           演示器乙 -> tools/tool_b.py\n"
        "  help        本帮助\n"
        "退出码 Exit codes: 0=pass 2=unknown-tool 9=missing\n"
        "EOF\n"
        "}\n"
        "hint_for() {\n"
        "  case \"$1\" in\n"
        "    a) echo \"cw.sh a --file <f.v> [--json out.json]   # 演示器甲 -> "
        "tools/tool_a.py\" ;;\n"
        + hint_b +
        "    *) return 1 ;;\n"
        "  esac\n"
        "}\n"
        "run_tool() {\n"
        "  local tool=\"$1\" rel=\"$2\"\n"
        "  shift 2\n"
        "  exec python3 \"$ROOT/$rel\" \"$@\"\n"
        "}\n"
        "case \"${1:-}\" in\n"
        "  a) shift; run_tool a \"tools/tool_a.py\" \"$@\" ;;\n"
        "  b) shift; run_tool b \"tools/tool_b.py\" \"$@\" ;;\n"
        "  help|-h|--help)\n"
        "    usage\n"
        "    exit 0 ;;\n"
        "  *)\n"
        "    echo \"cw.sh: 未知工具 unknown tool: $1\" >&2\n"
        "    exit 2 ;;\n"
        "esac\n")
    with io.open(os.path.join(root, "cw.sh"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(cw)
    os.makedirs(os.path.join(root, "tests"))
    with io.open(os.path.join(root, "tests", "run_tests.sh"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "#!/bin/bash\n"
            "# run_tests.sh — mini fixture 套件\n"
            "set -u\n"
            "REPO=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n"
            "CASES=\"\\\n"
            "t_a \\\n"
            "t_b\"\n"
            "t_a() { python3 -B \"$REPO/tools/tool_a.py\" --help >/dev/null; }\n"
            "t_b() { python3 -B \"$REPO/tools/tool_b.py\" --help >/dev/null; }\n"
            "for c in $CASES; do \"$c\" || exit 1; done\n")
    n = "3" if count_drift else "2"
    with io.open(os.path.join(root, "tests", "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# tests/ — mini\n"
            "套件自检（注入一恒红例）：\n"
            "ROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   "
            "# 预期 2 过 / 1 红 / EXIT 1\n"
            "\n"
            "## 覆盖面（%s 例）\n" % n +
            "| # | 用例 |\n|---|------|\n| 1 | `t_a` |\n| 2 | `t_b` |\n")
    with io.open(os.path.join(root, "README.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# mini repo\n"
            "```\n"
            "├── tests/  # 自测套件（2 例）— test suite (2 cases)\n"
            "```\n")
    with io.open(os.path.join(root, "README-cw.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# cw.sh mini 速查\n"
            "| 工具 | 目标脚本 | 一行示例 |\n"
            "|------|----------|----------|\n"
            "| `a` | `tools/tool_a.py` | `bash cw.sh a --file demo.v "
            "--json out.json` |\n"
            "| `b` | `tools/tool_b.py` | `bash cw.sh b --dir src/ --apply` |\n")
    phantom_line = ("python3 tools/tool_a.py --bogus-flag demo.v 幻引判例。\n"
                    if phantom else "")
    os.makedirs(os.path.join(root, "docs"))
    with io.open(os.path.join(root, "docs", "note.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# note\n"
            "普查用 python3 tools/tool_a.py --file demo.v --json out.json。\n"
            "收哨按 --max-rounds 界定（无器上下文·unresolved 不判漂判例）。\n"
            + phantom_line)
    os.makedirs(os.path.join(root, "examples", "workflows"))
    with io.open(os.path.join(root, "examples", "workflows", "wf.md"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(
            "# wf\n"
            "```bash\n"
            "bash cw.sh a --file demo.v --json out.json\n"
            "bash cw.sh b --dir src/ --apply\n"
            "```\n")
    return root


def selftest():
    """矢量组（tmp 迷你仓 fixture·全离线·真 subprocess --help 于夹具小器）：
    V1 一致迷你仓 0 漂（rc0·verdict consistent·三查全 ok）
    V2 工具表缺一（hint 摘 b）→ rc1·tool_table drift 指 cw.sh:hint
    V3 计数漂（覆盖面 3≠2）→ rc1·count drift
    V4 旗标幻引（docs/note.md --bogus-flag）→ rc1·flag drift
    V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9·--help-cap 0→2）
    V6 JSON 幂等（同仓两跑异 --json 路径字节恒同）
    """
    tmp = tempfile.mkdtemp(prefix="rocqwash_doclint_self_")
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, PROG + ".py")

    def run(aargs):
        e = dict(os.environ)
        p = subprocess.run([sys.executable, "-B", script] + list(aargs),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=e)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    try:
        # ---- V1 一致迷你仓 0 漂 ----
        v1 = os.path.join(tmp, "v1")
        make_mini_repo(v1)
        j1 = os.path.join(tmp, "v1.json")
        p = run(["--repo", v1, "--json", j1])
        assert p.returncode == 0, p.stdout[-1200:]
        rep = json.loads(io.open(j1, encoding="utf-8").read())
        assert rep["schema"] == SCHEMA and rep["verdict"] == "consistent", rep
        assert rep["drift_total"] == 0, rep["drift_total"]
        assert all(c["status"] == "ok" for c in rep["checks"]), rep["checks"]
        kinds = sorted(set(c["kind"] for c in rep["checks"]))
        assert kinds == ["count", "flag", "tool_table"], kinds
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["count"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["flag"]["drift"] == 0, rep["counts"]
        assert len(rep["registry"]["help_run"]) == 2, rep["registry"]
        # 引用旗标确已逐枚对账：a 器 --file/--json＋b 器 --dir/--apply
        v1_flag = [c for c in rep["checks"]
                   if c["kind"] == "flag" and c["target"]
                   == "examples/workflows/wf.md"]
        assert v1_flag and "refs=" in v1_flag[0]["detail"], v1_flag
        # 无器上下文旗标引用＝unresolved 如实计·不判漂（V1 仍 consistent）
        note = [c for c in rep["checks"]
                if c["kind"] == "flag" and c["target"] == "docs/note.md"]
        assert note and "unresolved=1" in note[0]["detail"], note

        # ---- V2 工具表缺一（hint 摘 b）----
        v2 = os.path.join(tmp, "v2")
        make_mini_repo(v2, hint_drop="b")
        j2 = os.path.join(tmp, "v2.json")
        p = run(["--repo", v2, "--json", j2])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j2, encoding="utf-8").read())
        assert rep["verdict"] == "drift", rep["verdict"]
        hit = [c for c in rep["checks"]
               if c["kind"] == "tool_table" and c["status"] == "drift"
               and c["target"] == "cw.sh:hint" and " b " in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["tool_table"]["drift"] >= 1, rep["counts"]

        # ---- V3 计数漂（覆盖面 3≠2）----
        v3 = os.path.join(tmp, "v3")
        make_mini_repo(v3, count_drift=True)
        j3 = os.path.join(tmp, "v3.json")
        p = run(["--repo", v3, "--json", j3])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j3, encoding="utf-8").read())
        hit = [c for c in rep["checks"] if c["kind"] == "count"
               and c["status"] == "drift" and "3 ≠ CASES 2" in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["count"]["drift"] == 1, rep["counts"]
        # 其余两查仍零漂（漂移只在计数域·不连带）
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["flag"]["drift"] == 0, rep["counts"]

        # ---- V4 旗标幻引（docs/note.md --bogus-flag）----
        v4 = os.path.join(tmp, "v4")
        make_mini_repo(v4, phantom=True)
        j4 = os.path.join(tmp, "v4.json")
        p = run(["--repo", v4, "--json", j4])
        assert p.returncode == 1, p.stdout[-1200:]
        rep = json.loads(io.open(j4, encoding="utf-8").read())
        hit = [c for c in rep["checks"] if c["kind"] == "flag"
               and c["status"] == "drift" and c["target"] == "docs/note.md"
               and "幻引" in c["detail"] and "--bogus-flag" in c["detail"]]
        assert hit, rep["checks"]
        assert rep["counts"]["flag"]["drift"] == 1, rep["counts"]
        # 其余两查仍零漂
        assert rep["counts"]["tool_table"]["drift"] == 0, rep["counts"]
        assert rep["counts"]["count"]["drift"] == 0, rep["counts"]

        # ---- V5 CLI 三码＋--help-cap 值校验 ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-300:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run(["--repo", os.path.join(tmp, "no_dir")])
        assert p.returncode == 9, "--repo 缺目录应 rc=9 实测 %d" % p.returncode
        p = run(["--repo", v1, "--help-cap", "0"])
        assert p.returncode == 2, "--help-cap 0 应 rc=2 实测 %d" % p.returncode

        # ---- V6 JSON 幂等：同仓两跑异 --json 路径字节恒同 ----
        j6a = os.path.join(tmp, "v6a.json")
        j6b = os.path.join(tmp, "v6b.json")
        p = run(["--repo", v1, "--json", j6a])
        assert p.returncode == 0, p.stdout[-400:]
        p = run(["--repo", v1, "--json", j6b])
        assert p.returncode == 0, p.stdout[-400:]
        ba = io.open(j6a, "rb").read()
        bb = io.open(j6b, "rb").read()
        assert ba == bb, "json 字节漂移＝违例"
        rep = json.loads(ba.decode("utf-8"))
        assert rep["schema"] == SCHEMA and "doclint" in rep["schema"]

        print("DOC-LINT-SELFTEST PASS: 一致仓0漂/工具表缺一(hint)/计数漂"
              "(3≠2)/旗标幻引(--bogus-flag)/CLI 三码＋cap 值校验/JSON 幂等"
              "字节恒同 六节全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
        description="文档←→实现一致性三查器：工具表查（cw.sh 四处互检＋tools/"
                    " 通用入口对账）＋计数查（CASES vs tests/README.md vs "
                    "README.md）＋旗标查（doc 引用旗标 vs --help 实出·帽 20 器）"
                    "（schema rocqwash-doclint/1）")
    ap.add_argument("--repo", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), metavar="DIR",
        help="被审仓根（缺省＝本件所在 tools/ 的上一级）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="报告出账（rocqwash-doclint/1·sort_keys 确定性）")
    ap.add_argument("--help-cap", dest="help_cap", type=int,
                    default=DEFAULT_HELP_CAP, metavar="N",
                    help="③ --help 真跑器帽（缺省 25·溢出典序截断如实列）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        code = run(args)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except (MissingInput, ToolError) as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
