#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""red_dispatch.py — 红事件路由器（rocqwash tools/·v37 候选「on-red→自动接驳」兑现·
哨红事件→动作预设路由·编排零新引擎·20261111 任务书入账）

读哨事件（cw_sentinel 事件流·rocqwash-sentinel-event/1 JSONL·make_event 产出形
cw_sentinel.py:435-443），按 kind/family 查路由表出**动作预设**：三档 preset 缺省
report-only 零执行（红是数据·零动作是缺省·承 cw_sentinel.py:47 干跑缺省同纪律）；
auto 档**显式才代跑**——建议命令真执行（每事件 60s 帽·rc≠0 响亮入 dispatch 账不改
退出码·执行器形承 cw_sentinel fire_on_red py:820-849 同款·ON_RED_TIMEOUT=60 同帽
py:229）。

输入（--event-file PATH｜stdin JSONL·--event-file 在场即文件为源 stdin 不读）：
  JSONL 逐行单事件（空行跳过·混合形坏 → 9 全列明）；全行皆败 → 整体单 JSON 对象
  兜底（多行 pretty 单事件）。事件三 kind 必传字段表（REQUIRED_FIELDS·路由消费面·
  缺字段 fail-loud 9 逐件逐字段列明）：
    ci-red       repo/run/family/action（cw_sentinel.py:614 产出形·family ∈ ci_triage
                 判类谱五族名 ci_triage.py:74·单字母 A-E 缩写容差归一）
    blocking     top_root（cw_sentinel.py:679 产出形）
    build-signal hits（cw_sentinel.py:723 产出形·须 list）
  批内任一件形坏 → 全批不派发不执行（validate-all-then-execute·半批派发＝半真半假账·
  逐件逐字段全列明后 9）。

路由表（判类谱承 ci_triage.py:143 ACTION_OF 五族处置·路由只挂既有引擎零新引擎）：
  ci-red+B/E（B-netred/E-coqchk-skipped）→ pushci 重派建议：
      bash cw.sh pushci --repo-path <repo> --branch <branch> --max-heal 3
      （cw.sh:37 路由·--max-heal 3＝pushci.py:2018 缺省同值）
  ci-red+A（A-content-red 内容红）→ manual-fix-note·**禁代修**：出 fix 清单
      （evidence 摘要逐条 clip 200·缺则退化为 repo/run/branch 指针面）·零命令零执行
      （内容面修复须人工·自动接驳不落内容刀）
  ci-red+C（C-toolchain-break）→ doctor 建议：bash cw.sh doctor（cw.sh:28 路由＝
      toolchain_dyld_doctor·全参可选故裸形·toolchain_dyld_doctor.py:391 零参可跑·
      只诊断不代修）
  ci-red+D/UNRECOGNIZED/none/谱外 → watch-only（零命令面人工看·ci_triage ACTION_OF
      谱外处置同款）
  blocking → unclog 建议：bash cw.sh unclog --src <src> --world <world>（cw.sh:45
      路由·--world 面 unclog.py:1091）[--apply] 仅 --param apply=1/true/yes/on 显式
      才缀——缺省干跑是铁律（cw_sentinel.py:57 unclog 预设同款「--apply 缺省不加」）
  build-signal → wash-shape 建议：bash cw.sh wash-shape --file <受治件>...（cw.sh:43
      路由·--file 面 wash_shape.py:2060·plan 缺省零写盘人审后 apply 同铁律）·受治件
      解算序＝--param file > 事件 file > hits 词面 .v 收割（\.v\b 词界·.vo 不误吞）
      > 9 列明

参数解算（三级·逐键记账 source∈param/event/derive/default）：
  ① --param K=V／--on-args K=V（同面别名——任务书 pushci 行名 --param 与 blocking 行
    名 --on-args 归一；可重复·键面并集 PARAM_KEYS=repo_path,branch,max_heal,src,
    world,file,apply·未知键/重键/无'='/空 K·V → 2·连字符归一下划线·cw_sentinel
    --on-red-arg 守卫同款 py:70-79）
  ② 事件字段（repo_path←repo·branch←branch·src/world←事件同名键）
  ③ 推导缺省：max_heal="3"；src/world=--repo-path 锚＋ConstructiveWorld_Live 相对名
    （cw_doctor.py:102 REGISTRY_REL 同款相对锚·零硬编码绝对路径）——--repo-path 未
    给而推导 → 9 列明
  皆无 → 9 列明（先全批解算后执行·零半批派发）。
  shell 守卫：凡入命令的值逐字符查元字符 ; & | < > ( ) $ ` " ' 反斜杠 Tab 换行与
  空格——命中即 9 拒构造（防注入 fail-loud·事件值是数据·auto 执行是动作·构造面
  先把关·三档一致）。

三档 --preset：
  report-only（缺省）只打印路由建议零执行·零副作用（state 不写·state 在案键仍照常
              出账——任务书「report-only 档仍出账」）
  suggest      同 report-only＋stdout 出可复制命令行块（JSON 同 report-only 形）
  auto         **显式才代跑**：建议命令真执行（subprocess shell·60s 帽——帽是防挂非
               求全·pushci 长流水线在此帽下超时即 rc=null 入账）·rc≠0 响亮入账不改
               退出码·--dry-run 同给只打将执行命令零真跑（--dry-run 须 auto·他档给
               → 2）

防重触发（--state-file PATH·schema=rocqwash-red-dispatch-state/1）：
  {"schema","dispatched":{"<kind|repo|run|family>":{"ts","rc","cmd"}}}
  键式＝kind+repo+run+family 任务书直译（缺槽空串占位——blocking/build-signal 无此
  四字段·键粒度=kind 级·cooldown 窗内同 kind 只派首件·粒度局限在此响亮注记）。
  auto 档同键再遇：距上次派发 < --cooldown S（缺省 600）→ 跳过（skipped=true·未重
  派不更新 ts）；窗满 → 再派。--state-file 缺省＝进程内存态（单批内防重仍有效·跨进
  程不持久）。state 形坏（JSON 败/schema 不识/dispatched 非 dict）→ 9 红拒不重建
  （cw_sentinel.py:136 崩溃恢复纪律同款——seen 是幂等账·静默重建＝防重失守）。
  仅 auto 真执行入账（超时 rc=null 亦入——派发已发生）·report-only/suggest 零 state
  写。同批多事件同键：批内第二件起同样过 cooldown 判（内存态即判）。

JSON（--json OUT·覆盖写·sort_keys·rocqwash-red-dispatch/1）：
  {"schema","preset","cooldown","events":[{event,route,action_cmd?,executed?,rc?,
   output?,key,params?,notes?,skipped?,fix_list?}],
   "summary":{routed,executed,skipped},"state_file"?,"dry_run"?}
  action_cmd 三档均在（命令面路由才有）；executed/rc 仅 auto 真执行后出现（rc=null
  ＝60s 超时）；output=执行回显 clip 400（真执行回显非确定域）；params=参数解算账
  {k:{value,source}}；fix_list=A 族清单；skipped=true=auto 防重跳过。确定性域＝解析
  ＋路由＋命令构造＋summary（同输入同 state 初态重跑字节恒同·ts 只入 state 文件
  不入 report）。

退出码：0=处理完成（红是数据非器红·rc≠0/超时/跳过皆入账不改退出码）；2=用法错
（--param 守卫/--dry-run 误档/--cooldown 负/selftest 断言）；9=输入缺失（事件文件
缺·字段缺逐件列明·参数无解列明·元字符拒构造·state 形坏）；1=预留（本器路由语义
零数据性未竟面——红是数据 exit 0）。
--selftest：0=全过／2=断言失败（矢量①-⑫·tmp fixtures 离线零网络·auto 实证以假
cw.sh 标记文件·本器命令模板相对形「bash cw.sh …」故实证矢量 chdir tmp 假仓根）：
  ① 路由表全族覆盖（B/E/A/C/blocking/build-signal 六样张·五路由行全咬合）
  ② 占位替换（param 显式超驰/event 缺省/max-heal 缺省 3/derive ConstructiveWorld_Live）
  ③ auto 执行实证（假 cw.sh 标记文件·executed=1·state 入账）
  ④ state 防重（同事件二跑 skipped=1 零重跑）
  ⑤ cooldown（缺省 600 二跑跳过·--cooldown 0 三跑再派）
  ⑥ report-only 缺省零执行（标记文件不出·exit 0）
  ⑦ JSONL stdin 多事件（三行逐条·suggest 复制块在）
  ⑧ fail-loud 面（字段缺 9 列明/param 未知·重·形坏 2/dry-run 误档 2/元字符 9/
    state 形坏 9/kind 不识 9）
  ⑨ rc≠0 不改退出码（假 cw.sh exit 3·main 返 0·rc=3 入账）
  ⑩ A 族 fix 清单＋C 族定令
  ⑪ 确定性（suggest 双跑 JSON 字节恒同）
  ⑫ 整体单对象兜底（多行 pretty 单事件）

编排律（承 v37 用户令·零新引擎）：路由只做「事件→既有 cw.sh 路由命令」的胶水与
账面（pushci/unclog/wash-shape/doctor 四路由全在库·cw.sh:27-47）；本器自身零编译
零网络（auto 执行的是本地命令·真编译温控由 cw.sh 路由内部自管——unclog --guard
面在库 unclog.py:1125·哨 on-red 执行器不包 guard 同款先例）；「一切 python 执行经
cpu_guard 包裹」是会话铁律非本器语义（零硬编码 guard 路径）。

诚实律（承 CONTRIBUTING §0）：只认机械证据（退出码/标记文件/字节恒同）；fail-loud
禁静默降级（字段缺 9·参数无解 9·state 形坏 9·元字符拒 9·输入空 9）；零第三方
依赖（纯 stdlib）；--json 落盘 sort_keys；零硬编码绝对路径（--event-file/--json/
--state-file/--repo-path 全参数化·ConstructiveWorld_Live 为相对名锚承
cw_doctor.py:102 判例）。写域声明：只写调用方显式指认的 --json/--state-file 出路径
＋auto 真执行的派发命令自身副作用；selftest 只写 mkdtemp 临时目录（测毕即删）。
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "red_dispatch"
SCHEMA = "rocqwash-red-dispatch/1"
STATE_SCHEMA = "rocqwash-red-dispatch-state/1"

EVENT_KINDS = ("ci-red", "blocking", "build-signal")
REQUIRED_FIELDS = {
    "ci-red": ("repo", "run", "family", "action"),
    "blocking": ("top_root",),
    "build-signal": ("hits",),
}
FAMILY_ALIASES = {"A": "A-content-red", "B": "B-netred", "C": "C-toolchain-break",
                  "D": "D-queue-wall", "E": "E-coqchk-skipped"}
PUSHCI_FAMILIES = ("B-netred", "E-coqchk-skipped")

WORLD_REL = "ConstructiveWorld_Live"   # 相对名锚（cw_doctor.py:102 REGISTRY_REL 同款）
DEFAULT_MAX_HEAL = "3"                 # pushci.py:2018 --max-heal 缺省 3 同值
DEFAULT_COOLDOWN = 600
EXEC_TIMEOUT = 60                      # cw_sentinel.py:229 ON_RED_TIMEOUT 同帽
OUTPUT_CLIP = 400                      # cw_sentinel.py:843 clip(out, 400) 同帽
FIX_CLIP = 200
STATE_CMD_CLIP = 200

PARAM_KEYS = ("repo_path", "branch", "max_heal", "src", "world", "file", "apply")
APPLY_TRUTHY = ("1", "true", "yes", "on")

V_FILE_RE = re.compile(r"[A-Za-z0-9_./][A-Za-z0-9_./-]*\.v\b")  # \b 词界·.vo 不误吞
_SHELL_UNSAFE = set('; & | < > ( ) $ ` " \' \t \r \n \\')


class DispatchError(Exception):
    """fail-loud 载体：msg 响亮文本·code ∈ 2(用法/断言)/9(输入缺失)。"""

    def __init__(self, msg, code):
        super().__init__(msg)
        self.msg = msg
        self.code = code


def clip(s, cap=OUTPUT_CLIP):
    """定长截断（cw_sentinel.py:254 clip 同款形）。"""
    s = str(s)
    return s if len(s) <= cap else s[:cap] + "...[clip]"


def shell_unsafe(v):
    """命令构造面元字符守卫（防注入·值含元字符即拒）。"""
    return any(c in _SHELL_UNSAFE for c in str(v))


# ---- 输入解析 ------------------------------------------------------------------

def parse_events(text, source):
    """输入文本 → 事件 dict 列表（JSONL 逐行·空行跳过·混合形坏 9 全列明；
    全行皆败 → 整体单 JSON 对象兜底）。确定性：行序＝事件序。"""
    lines = [(i, l) for i, l in enumerate(text.splitlines(), 1) if l.strip()]
    if not lines:
        raise DispatchError("输入缺失: %s 零有效行（JSONL 空输入）" % source, 9)
    parsed, problems = [], []
    for lineno, line in lines:
        try:
            ev = json.loads(line)
        except ValueError as e:
            problems.append("行 %d: JSON 解析失败 %s" % (lineno, e))
            continue
        if not isinstance(ev, dict):
            problems.append("行 %d: 事件形非 dict（实测 %s）" % (lineno, type(ev).__name__))
            continue
        parsed.append(ev)
    if problems and parsed:
        raise DispatchError("输入形坏: %s（%d 行坏·混合形拒——JSONL 逐行单事件形）:\n  %s"
                            % (source, len(problems), "\n  ".join(problems)), 9)
    if parsed:
        return parsed
    try:
        ev = json.loads(text)
    except ValueError as e:
        raise DispatchError("输入形坏: %s（JSONL 逐行 %d 处败＋整体 JSON 败 %s·双形均败）"
                            % (source, len(problems), e), 9)
    if not isinstance(ev, dict):
        raise DispatchError("输入形坏: %s（整体 JSON 非 dict·实测 %s）"
                            % (source, type(ev).__name__), 9)
    return [ev]


def collect_field_problems(ev, where):
    """必传字段表逐键判（缺字段 fail-loud 列明）→ (problems, kind|None)。"""
    problems = []
    kind = ev.get("kind")
    if kind is None:
        return ["%s: kind 缺（必传·形 ∈ %s）" % (where, ",".join(EVENT_KINDS))], None
    if kind not in EVENT_KINDS:
        return ["%s: kind 不识别（实测 %r·须 ∈ %s）" % (where, kind, ",".join(EVENT_KINDS))], None
    for f in REQUIRED_FIELDS[kind]:
        v = ev.get(f)
        if v is None or (isinstance(v, str) and not v.strip()) \
                or (isinstance(v, (list, dict)) and not v):
            problems.append("%s: %s 缺（%s 必传）" % (where, f, kind))
    if kind == "ci-red" and ev.get("family") is not None \
            and not isinstance(ev.get("family"), str):
        problems.append("%s: family 形须 str（实测 %s）"
                        % (where, type(ev["family"]).__name__))
    if kind == "build-signal" and ev.get("hits") is not None \
            and not isinstance(ev.get("hits"), list):
        problems.append("%s: hits 形须 list（实测 %s）"
                        % (where, type(ev["hits"]).__name__))
    return problems, kind


def state_key(ev):
    """防重键＝kind+repo+run+family 任务书直译（缺槽空串占位·blocking/build-signal
    无四字段 → 键粒度=kind 级·粒度局限已在 docstring 响亮注记）。"""
    parts = []
    for k in ("kind", "repo", "run", "family"):
        v = ev.get(k)
        parts.append("" if v is None else str(v))
    return "|".join(parts)


# ---- 参数解算 ------------------------------------------------------------------

def resolve_param(key, ev, params, event_field=None):
    """三级解算前两级：--param 显式 > 事件字段 → (value|None, source|None)。"""
    if key in params:
        return str(params[key]), "param"
    v = ev.get(event_field or key)
    if v is None:
        return None, None
    sv = str(v)
    if not sv.strip():
        return None, None
    return sv, "event"


def derive_world(repo_path):
    """三级解算第三级：--repo-path 锚＋ConstructiveWorld_Live 相对名
    （cw_doctor.py:102 REGISTRY_REL 同款相对锚）。→ (value|None, source|None)"""
    if not repo_path:
        return None, None
    return os.path.join(repo_path, WORLD_REL), "derive"


def build_route(ev, kind, params, repo_path):
    """路由表查表 → (route dict, problems)。
    route dict: {id, cmd?, params?, fix_list?, notes[]}；problems 非空＝该事件命令面
    无解（调用方全批列明 9·validate-all-then-execute）。"""
    notes = []
    problems = []
    route = {"id": None, "notes": notes}

    def _guard(k, v):
        if v is None:
            return False
        if shell_unsafe(v):
            problems.append("路由参数 %s 含 shell 元字符·拒构造（防注入 fail-loud）: %r"
                            % (k, clip(v, 80)))
            return False
        return True

    if kind == "ci-red":
        fam = ev.get("family")
        if fam in FAMILY_ALIASES:
            notes.append("family 别名 %s→%s（判类谱缩写容差）" % (fam, FAMILY_ALIASES[fam]))
            fam = FAMILY_ALIASES[fam]
        if fam in PUSHCI_FAMILIES:
            route["id"] = "pushci"
            rp, s1 = resolve_param("repo_path", ev, params, event_field="repo")
            br, s2 = resolve_param("branch", ev, params, event_field="branch")
            mh, s3 = resolve_param("max_heal", ev, params)
            if mh is None:
                mh, s3 = DEFAULT_MAX_HEAL, "default"
            for k, v in (("repo_path", rp), ("branch", br), ("max_heal", mh)):
                if v is None:
                    problems.append("pushci 路由参数无解: %s（--param/事件皆缺）" % k)
                else:
                    _guard(k, v)
            if not problems:
                route["cmd"] = ("bash cw.sh pushci --repo-path %s --branch %s "
                                "--max-heal %s" % (rp, br, mh))
                route["params"] = {"repo_path": {"value": rp, "source": s1},
                                   "branch": {"value": br, "source": s2},
                                   "max_heal": {"value": mh, "source": s3}}
        elif fam == "A-content-red":
            route["id"] = "manual-fix-note"
            notes.append("A 族内容红＝内容面修复·禁代修（任务书铁律·自动接驳不落内容刀"
                         "·零命令零执行）")
            evidence = ev.get("evidence")
            if isinstance(evidence, list) and evidence:
                route["fix_list"] = [clip(str(x), FIX_CLIP) for x in evidence]
            else:
                notes.append("evidence 缺（事件未带）·fix 清单退化指针面")
                route["fix_list"] = ["repo=%s run=%s branch=%s（人工取 run 日志指认受治件"
                                     "·禁代修）" % (ev.get("repo"), ev.get("run"),
                                                    ev.get("branch"))]
        elif fam == "C-toolchain-break":
            route["id"] = "doctor"
            route["cmd"] = "bash cw.sh doctor"
            notes.append("doctor＝toolchain_dyld_doctor 路由（cw.sh:28·全参可选故裸形"
                         "·只诊断不代修）")
        else:
            route["id"] = "watch-only"
            notes.append("family=%r 路由表外·watch-only 零命令面人工看（D/UNRECOGNIZED/"
                         "none 及谱外·ci_triage.py:143 ACTION_OF 谱外处置同款）" % (fam,))
    elif kind == "blocking":
        route["id"] = "unclog"
        src, s1 = resolve_param("src", ev, params)
        if src is None:
            src, s1 = derive_world(repo_path)
        world, s2 = resolve_param("world", ev, params)
        if world is None:
            world, s2 = derive_world(repo_path)
        for k, v in (("src", src), ("world", world)):
            if v is None:
                problems.append("unclog 路由参数无解: %s（--param/事件皆缺·--repo-path "
                                "未给无法推导 %s）" % (k, WORLD_REL))
            else:
                _guard(k, v)
        apply_on = "apply" in params and params["apply"].lower() in APPLY_TRUTHY
        if "apply" in params:
            notes.append("apply 显式=%s（人令才缀 --apply·缺省干跑铁律不动——"
                         "cw_sentinel.py:57 同款）" % params["apply"])
        if not problems:
            route["cmd"] = ("bash cw.sh unclog --src %s --world %s%s"
                            % (src, world, " --apply" if apply_on else ""))
            route["params"] = {"src": {"value": src, "source": s1},
                               "world": {"value": world, "source": s2}}
    elif kind == "build-signal":
        route["id"] = "wash-shape"
        if "file" in params:
            files, fsource = [params["file"]], "param"
        elif isinstance(ev.get("file"), list) and ev["file"]:
            files, fsource = [str(x) for x in ev["file"]], "event"
        elif isinstance(ev.get("file"), str) and ev["file"].strip():
            files, fsource = [ev["file"]], "event"
        else:
            files, fsource = [], "derive"
            for h in (ev.get("hits") or []):
                for m in V_FILE_RE.findall(str(h)):
                    if m not in files:
                        files.append(m)
        if not files:
            problems.append("wash-shape 路由参数无解: file（--param/事件 file/"
                            "hits 词面 .v 收割皆空）")
        else:
            _guard("file", " ".join(files))
        if not problems:
            route["cmd"] = "bash cw.sh wash-shape" + "".join(
                " --file %s" % f for f in files)
            route["params"] = {"file": {"value": files, "source": fsource}}
    return route, problems


# ---- state（防重持久层·形坏红拒不重建）------------------------------------------

def load_state(path):
    if not os.path.isfile(path):
        return {"schema": STATE_SCHEMA, "dispatched": {}}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            st = json.load(fh)
    except (ValueError, UnicodeDecodeError) as e:
        raise DispatchError("state 形坏: %s（%s）——红拒不重建（cw_sentinel.py:136 "
                            "崩溃恢复纪律同款·恢复唯人工删件）" % (path, e), 9)
    if not isinstance(st, dict) or st.get("schema") != STATE_SCHEMA \
            or not isinstance(st.get("dispatched"), dict):
        raise DispatchError("state 形坏: %s（schema/dispatched 面不识·红拒不重建）"
                            % path, 9)
    return st


def save_state(path, st):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise DispatchError("state 目录缺失: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(st, fh, indent=1, ensure_ascii=False, sort_keys=True)


def write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        raise DispatchError("出账目录缺失: %s" % d, 9)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---- 执行与处理 ----------------------------------------------------------------

def run_dispatch_cmd(cmd):
    """派发执行器（cw_sentinel fire_on_red py:831-842 同款形·60s 帽）
    → (rc|None, output)。rc=None＝超时（帽是防挂非求全）。"""
    try:
        p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=EXEC_TIMEOUT)
        out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return None, "timeout（%ds 帽）" % EXEC_TIMEOUT


def process(args, items):
    """逐事件路由处理 → report dict。auto 档才执行与防重（report-only/suggest 零
    副作用·state 在案键仍出账）。rc≠0/超时响亮入账不改退出码。"""
    state = load_state(args.state_file) if args.state_file \
        else {"schema": STATE_SCHEMA, "dispatched": {}}
    entries, executed, skipped = [], 0, 0
    now = time.time()
    dirty = False
    for it in items:
        route = it["route"]
        entry = {"event": it["ev"], "route": route["id"], "key": it["key"],
                 "notes": list(route.get("notes") or [])}
        if route.get("cmd"):
            entry["action_cmd"] = route["cmd"]
        if route.get("params"):
            entry["params"] = route["params"]
        if route.get("fix_list") is not None:
            entry["fix_list"] = route["fix_list"]
        if args.preset == "auto" and entry.get("action_cmd"):
            if args.dry_run:
                entry["notes"].append("dry-run·将执行未真跑（executed 计 0·state 不写）")
            else:
                rec = state["dispatched"].get(it["key"])
                if rec is not None and \
                        (now - float(rec.get("ts") or 0.0)) < args.cooldown:
                    skipped += 1
                    entry["skipped"] = True
                    entry["notes"].append("cooldown 窗内跳过（cooldown=%ds·state 在案"
                                          "·未重派不更新 ts）" % args.cooldown)
                else:
                    rc, out = run_dispatch_cmd(entry["action_cmd"])
                    entry["executed"] = True
                    entry["rc"] = rc
                    entry["output"] = clip(out)
                    executed += 1
                    dirty = True
                    state["dispatched"][it["key"]] = {
                        "ts": now, "rc": rc,
                        "cmd": clip(entry["action_cmd"], STATE_CMD_CLIP)}
                    if rc is None:
                        sys.stdout.write("dispatch 注记: 超时（%ds 帽·入账不改退出码）"
                                         " cmd=%s\n" % (EXEC_TIMEOUT, entry["action_cmd"]))
                    elif rc != 0:
                        sys.stdout.write("dispatch 注记: rc=%d≠0（响亮入账·不改退出码）"
                                         " cmd=%s\n" % (rc, entry["action_cmd"]))
        entries.append(entry)
    if dirty and args.state_file:
        save_state(args.state_file, state)
    rep = {"schema": SCHEMA, "preset": args.preset, "cooldown": args.cooldown,
           "events": entries,
           "summary": {"routed": len(items), "executed": executed,
                       "skipped": skipped}}
    if args.state_file:
        rep["state_file"] = args.state_file
    if args.dry_run:
        rep["dry_run"] = True
    return rep


def identity(ev):
    """事件身份响亮短串（stdout 逐件行用）。"""
    k = ev.get("kind")
    if k == "ci-red":
        return "repo=%s run=%s family=%s" % (ev.get("repo"), ev.get("run"),
                                             ev.get("family"))
    if k == "blocking":
        return "top_root=%s ledger=%s" % (ev.get("top_root"), ev.get("ledger"))
    if k == "build-signal":
        return "log=%s hits=%d" % (ev.get("log"), len(ev.get("hits") or []))
    return ""


def render(rep, args):
    """stdout 响亮账（确定性文案·无 ts·rc 值入账）。"""
    w = sys.stdout.write
    preset = rep["preset"]
    mode_note = {"report-only": "红是数据·路由零执行",
                 "suggest": "红是数据·路由零执行＋复制块",
                 "auto": "自动接驳·60s 帽·rc≠0 入账不改退出码"}[preset]
    if rep.get("dry_run"):
        mode_note += "·dry-run 只打未跑"
    w("=== RED-DISPATCH preset=%s events=%d（%s）===\n"
      % (preset, len(rep["events"]), mode_note))
    for i, e in enumerate(rep["events"], 1):
        w("[%d] %s %s → %s\n" % (i, e["event"].get("kind"),
                                 identity(e["event"]), e["route"]))
        if "action_cmd" in e:
            w("    cmd: %s\n" % e["action_cmd"])
        for n in e.get("notes") or []:
            w("    注: %s\n" % n)
        for f in e.get("fix_list") or []:
            w("    fix清单: %s\n" % f)
        if preset == "suggest" and "action_cmd" in e:
            w("    +-- 复制即用 --+\n    %s\n    +----------------+\n"
              % e["action_cmd"])
        if e.get("skipped"):
            w("    跳过（cooldown 窗内·未重派）\n")
        if "executed" in e:
            rc = e.get("rc")
            if rc is None:
                w("    执行超时（%ds 帽·入账不改退出码）\n" % EXEC_TIMEOUT)
            elif rc == 0:
                w("    执行 rc=0\n")
            else:
                w("    执行 rc=%d（≠0·响亮入账·不改退出码）\n" % rc)
    s = rep["summary"]
    w("=== SUMMARY routed=%d executed=%d skipped=%d（exit 0·红是数据非器红）===\n"
      % (s["routed"], s["executed"], s["skipped"]))


# ---- CLI -----------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(prog=PROG)
    ap.add_argument("--event-file", dest="event_file", default=None, metavar="PATH",
                    help="哨事件 JSONL 文件（缺省读 stdin·在场即 stdin 不读）")
    ap.add_argument("--preset", choices=("report-only", "suggest", "auto"),
                    default="report-only",
                    help="report-only=缺省零执行｜suggest=＋复制块｜auto=显式代跑(60s帽)")
    ap.add_argument("--json", dest="json_out", default=None, metavar="OUT",
                    help="路由账 JSON 出路径（rocqwash-red-dispatch/1·sort_keys）")
    ap.add_argument("--state-file", dest="state_file", default=None, metavar="PATH",
                    help="防重 state（rocqwash-red-dispatch-state/1·缺省内存态）")
    ap.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN, metavar="S",
                    help="同键再派最小间隔秒（缺省 600·0=关窗）")
    ap.add_argument("--repo-path", dest="repo_path", default=None, metavar="DIR",
                    help="本地仓根锚（unclog src/world 推导 %s 的基）" % WORLD_REL)
    ap.add_argument("--param", dest="params", action="append", default=[],
                    metavar="K=V",
                    help="路由补参（可重复·键面 %s）" % ",".join(PARAM_KEYS))
    ap.add_argument("--on-args", dest="params", action="append", metavar="K=V",
                    help="同 --param（任务书两处名号归一别名）")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="auto 档下只打将执行命令零真跑（他档给 → 2）")
    ap.add_argument("--selftest", action="store_true",
                    help="矢量自证（离线零网络·tmp fixtures·0=全过/2=断言）")
    a = ap.parse_args(argv)
    if a.cooldown < 0:
        raise DispatchError("--cooldown 须≥0 实测 %d" % a.cooldown, 2)
    if a.dry_run and a.preset != "auto":
        raise DispatchError("--dry-run 须与 --preset auto 同给（任务书 auto 档语义·"
                            "实测 preset=%s）" % a.preset, 2)
    seen = {}
    for raw in (a.params or []):
        if "=" not in raw:
            raise DispatchError("--param/--on-args 形坏（须 K=V）: %r" % raw, 2)
        k, v = raw.split("=", 1)
        k = k.strip().replace("-", "_")
        if not k:
            raise DispatchError("--param/--on-args 空 K: %r" % raw, 2)
        if not v.strip():
            raise DispatchError("--param/--on-args 空 V: %r" % raw, 2)
        if k not in PARAM_KEYS:
            raise DispatchError("--param/--on-args 未知键（键面并集 %s）: %s"
                                % (",".join(PARAM_KEYS), k), 2)
        if k in seen:
            raise DispatchError("--param/--on-args 重键: %s" % k, 2)
        seen[k] = v
    if "apply" in seen and seen["apply"].lower() not in APPLY_TRUTHY:
        raise DispatchError("--param apply 取值须 ∈ %s（实测 %r）"
                            % ("/".join(APPLY_TRUTHY), seen["apply"]), 2)
    a.params = seen
    return a


def _loud_err(e):
    tag = {2: "用法错", 9: "输入缺失/形坏"}.get(e.code, "错(rc=%d)" % e.code)
    sys.stdout.write("RED-DISPATCH %s（rc=%d）: %s\n" % (tag, e.code, e.msg))


def main(argv=None, stdin_text=None):
    """入口 → 退出码（0 处理完成/2 用法/9 输入缺失）。stdin_text＝测试注入口
    （selftest 用·绕 tty 判）。"""
    try:
        args = parse_args(sys.argv[1:] if argv is None else list(argv))
    except DispatchError as e:
        _loud_err(e)
        return e.code
    if args.selftest:
        return selftest()
    try:
        if args.event_file:
            if not os.path.isfile(args.event_file):
                raise DispatchError("输入缺失: 事件文件不在卷: %s" % args.event_file, 9)
            with io.open(args.event_file, "r", encoding="utf-8") as fh:
                text = fh.read()
            source = args.event_file
        else:
            if stdin_text is not None:
                text = stdin_text
            elif sys.stdin.isatty():
                raise DispatchError("输入缺失: --event-file 缺且 stdin 为终端"
                                    "（无管道输入·用法见 --help）", 9)
            else:
                text = sys.stdin.read()
            source = "stdin"
        events = parse_events(text, source)
        items, all_problems = [], []
        for idx, ev in enumerate(events, 1):
            where = "事件%d" % idx
            problems, kind = collect_field_problems(ev, where)
            all_problems.extend(problems)
            if kind is None:
                continue
            route, rproblems = build_route(ev, kind, args.params, args.repo_path)
            all_problems.extend(rproblems)
            items.append({"ev": ev, "route": route, "key": state_key(ev)})
        if all_problems:
            raise DispatchError("输入缺失/形坏 %d 处（validate-all-then-execute·"
                                "全批零派发零执行）:\n  %s"
                                % (len(all_problems), "\n  ".join(all_problems)), 9)
        rep = process(args, items)
        if args.json_out:
            write_json(args.json_out, rep)
        render(rep, args)
        return 0
    except DispatchError as e:
        _loud_err(e)
        return e.code


# ---- selftest（矢量①-⑫·tmp fixtures·离线零网络）--------------------------------

def _write_tmp(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _load_tmp(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def selftest():
    sys.stdout.write("=== RED-DISPATCH SELFTEST（tmp fixtures·离线零网络）===\n")
    failures = []

    def check(name, cond, detail=""):
        if cond:
            sys.stdout.write("  PASS %s\n" % name)
        else:
            failures.append(name)
            sys.stdout.write("  FAIL %s %s\n" % (name, detail))

    tmp = tempfile.mkdtemp(prefix="rocqwash_red_dispatch_self_")
    oldcwd = os.getcwd()
    old_log = os.environ.get("RED_DISPATCH_LOG")
    old_rc = os.environ.get("RED_DISPATCH_RC")
    live = os.path.join(tmp, "ConstructiveWorld_Live")
    try:
        # 假仓根：假 cw.sh 以标记文件实证派发（RED_DISPATCH_LOG/RC 环境注参）
        _write_tmp(os.path.join(tmp, "cw.sh"),
                   '#!/bin/bash\nprintf \'%s\\n\' "$*" >> "$RED_DISPATCH_LOG"\n'
                   'exit ${RED_DISPATCH_RC:-0}\n')
        logp = os.path.join(tmp, "dispatched.log")

        EV_B = {"kind": "ci-red", "repo": "ORG/R1", "run": 178, "branch": "main",
                "family": "B-netred", "action": "rerun-after-stable-window",
                "evidence": ["failure-step: upload-artifact"]}
        EV_E = {"kind": "ci-red", "repo": "ORG/R1", "run": 179, "branch": "main",
                "family": "E-coqchk-skipped", "action": "rerun-after-stable-window",
                "evidence": ["coqchk 步 skipped＝gate2 未达（E 签名）"]}
        EV_A = {"kind": "ci-red", "repo": "ORG/R1", "run": 180, "branch": "dev",
                "family": "A-content-red", "action": "fix-content",
                "evidence": ["Error: AbsSq.v:12", "FAIL 公理计数≠0"]}
        EV_C = {"kind": "ci-red", "repo": "ORG/R1", "run": 181, "branch": "main",
                "family": "C-toolchain-break", "action": "restore-toolchain",
                "evidence": ["EXIT=134"]}
        EV_D = {"kind": "ci-red", "repo": "ORG/R1", "run": 182, "branch": "main",
                "family": "D-queue-wall", "action": "queue-etiquette",
                "evidence": ["steps=0（零步骤）"]}
        EV_BL = {"kind": "blocking", "ledger": "probe_x.json", "top_root": "FooBasics",
                 "dependents": ["A.v", "B.v"], "n": 2}
        EV_BS = {"kind": "build-signal", "log": "/tmp/build.log",
                 "hits": ["Error: src/AbsSq.v:12: syntax error", "BUILD-FAIL: rc=1"]}

        # 矢① 路由表全族覆盖（六样张·五路由行全咬合＋谱外 watch-only）
        r_b, p1 = build_route(EV_B, "ci-red", {}, None)
        check("①B pushci 路由", r_b["id"] == "pushci" and not p1, str(p1))
        check("①B 命令形", r_b.get("cmd") ==
              "bash cw.sh pushci --repo-path ORG/R1 --branch main --max-heal 3",
              str(r_b.get("cmd")))
        r_e, _ = build_route(EV_E, "ci-red", {}, None)
        check("①E pushci 同路由", r_e["id"] == "pushci")
        r_a, _ = build_route(EV_A, "ci-red", {}, None)
        check("①A manual-fix-note", r_a["id"] == "manual-fix-note"
              and not r_a.get("cmd"))
        r_c, _ = build_route(EV_C, "ci-red", {}, None)
        check("①C doctor 定令", r_c["id"] == "doctor"
              and r_c.get("cmd") == "bash cw.sh doctor")
        r_bl, pbl = build_route(EV_BL, "blocking", {}, tmp)
        check("①BL unclog 推导", r_bl["id"] == "unclog" and not pbl
              and r_bl.get("cmd") ==
              "bash cw.sh unclog --src %s --world %s" % (live, live)
              and r_bl["params"]["src"]["source"] == "derive", str(r_bl.get("cmd")))
        r_bs, pbs = build_route(EV_BS, "build-signal", {}, None)
        check("①BS wash-shape 收割", r_bs["id"] == "wash-shape" and not pbs
              and r_bs.get("cmd") == "bash cw.sh wash-shape --file src/AbsSq.v"
              and r_bs["params"]["file"]["source"] == "derive", str(r_bs.get("cmd")))
        r_d, _ = build_route(EV_D, "ci-red", {}, None)
        check("①D watch-only", r_d["id"] == "watch-only" and not r_d.get("cmd"))

        # 矢② 占位替换（param 显式超驰/event 缺省/derive 锚）
        r2, p2 = build_route(EV_B, "ci-red", {"branch": "dev", "max_heal": "5"}, None)
        check("② param 超驰", not p2 and r2.get("cmd") ==
              "bash cw.sh pushci --repo-path ORG/R1 --branch dev --max-heal 5"
              and r2["params"]["branch"]["source"] == "param", str(p2))
        r2b, _ = build_route(EV_B, "ci-red", {"repo_path": "/tmp/local"}, None)
        check("② repo_path 显式超驰事件", "--repo-path /tmp/local" in r2b.get("cmd", ""))
        r2c, _ = build_route(EV_BL, "blocking", {"src": "/x/s", "world": "/x/w"}, None)
        check("② src/world 显式", r2c.get("cmd") ==
              "bash cw.sh unclog --src /x/s --world /x/w")
        r2d, _ = build_route(EV_BL, "blocking", {"apply": "on"}, tmp)
        check("② apply 显式缀", r2d.get("cmd", "").endswith(" --apply"))
        r2e, _ = build_route(EV_BL, "blocking", {}, tmp)
        check("② 缺省无 --apply", "--apply" not in r2e.get("cmd", ""))

        # 矢③④⑤ auto 执行实证＋state 防重＋cooldown（chdir 假仓根·标记文件）
        os.chdir(tmp)
        os.environ["RED_DISPATCH_LOG"] = logp
        evfile = os.path.join(tmp, "ev_b.jsonl")
        _write_tmp(evfile, json.dumps(EV_B, sort_keys=True) + "\n")
        argv3 = ["--event-file", evfile, "--preset", "auto",
                 "--state-file", os.path.join(tmp, "st3.json"),
                 "--json", os.path.join(tmp, "r3.json")]
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            rc3 = main(argv3)
        check("③ auto exit 0", rc3 == 0, str(rc3))
        log3 = _load_tmp(logp) if os.path.isfile(logp) else ""
        check("③ 标记文件实证", "--repo-path ORG/R1 --branch main --max-heal 3"
              in log3, repr(log3[:120]))
        rep3 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("③ executed=1 rc=0",
              rep3["summary"] == {"routed": 1, "executed": 1, "skipped": 0}
              and rep3["events"][0].get("rc") == 0
              and rep3["events"][0].get("executed") is True,
              json.dumps(rep3["summary"], sort_keys=True))
        st3 = json.loads(_load_tmp(os.path.join(tmp, "st3.json")))
        check("③ state 键入账",
              "ci-red|ORG/R1|178|B-netred" in st3["dispatched"]
              and st3["schema"] == "rocqwash-red-dispatch-state/1",
              json.dumps(st3, sort_keys=True)[:160])
        buf4 = io.StringIO()
        with contextlib.redirect_stdout(buf4):
            rc4 = main(argv3)
        rep4 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("④ 二跑防重 skipped", rc4 == 0
              and rep4["summary"] == {"routed": 1, "executed": 0, "skipped": 1}
              and rep4["events"][0].get("skipped") is True
              and len(log3.splitlines()) == len(_load_tmp(logp).splitlines()),
              json.dumps(rep4["summary"], sort_keys=True))
        argv5 = argv3 + ["--cooldown", "0"]
        buf5 = io.StringIO()
        with contextlib.redirect_stdout(buf5):
            rc5 = main(argv5)
        rep5 = json.loads(_load_tmp(os.path.join(tmp, "r3.json")))
        check("⑤ cooldown=0 窗开再派", rc5 == 0
              and rep5["summary"] == {"routed": 1, "executed": 1, "skipped": 0}
              and len(_load_tmp(logp).splitlines()) == 2,
              json.dumps(rep5["summary"], sort_keys=True))

        # 矢⑥ report-only 缺省零执行（标记文件不出）
        if os.path.isfile(logp):
            os.unlink(logp)
        argv6 = ["--event-file", evfile, "--json", os.path.join(tmp, "r6.json")]
        buf6 = io.StringIO()
        with contextlib.redirect_stdout(buf6):
            rc6 = main(argv6)
        check("⑥ report-only 零执行", rc6 == 0 and not os.path.isfile(logp)
              and json.loads(_load_tmp(os.path.join(tmp, "r6.json")))
              ["summary"] == {"routed": 1, "executed": 0, "skipped": 0},
              str(rc6))

        # 矢⑦ JSONL stdin 多事件（suggest 复制块）
        jsonl3 = "\n".join(json.dumps(x, sort_keys=True)
                           for x in (EV_B, EV_BL, EV_BS)) + "\n"
        argv7 = ["--preset", "suggest", "--repo-path", tmp,
                 "--json", os.path.join(tmp, "r7.json")]
        buf7 = io.StringIO()
        with contextlib.redirect_stdout(buf7):
            rc7 = main(argv7, stdin_text=jsonl3)
        rep7 = json.loads(_load_tmp(os.path.join(tmp, "r7.json")))
        out7 = buf7.getvalue()
        check("⑦ stdin 三事件逐条", rc7 == 0
              and rep7["summary"]["routed"] == 3
              and [e["route"] for e in rep7["events"]] ==
              ["pushci", "unclog", "wash-shape"],
              json.dumps(rep7["summary"], sort_keys=True))
        check("⑦ suggest 复制块", out7.count("+-- 复制即用 --+") == 3, out7[-300:])

        # 矢⑧ fail-loud 面
        buf8a = io.StringIO()
        with contextlib.redirect_stdout(buf8a):
            rc8a = main(["--preset", "report-only", "--json",
                         os.path.join(tmp, "r8a.json")],
                        stdin_text=json.dumps({"kind": "ci-red", "repo": "ORG/R2",
                                               "run": 9, "action": "fix-content"}))
        check("⑧a 缺 family 9 列明", rc8a == 9 and "family 缺" in buf8a.getvalue(),
              "%d %s" % (rc8a, buf8a.getvalue()[:200]))
        buf8b = io.StringIO()
        with contextlib.redirect_stdout(buf8b):
            rc8b = main(["--preset", "report-only", "--param", "bogus=1"],
                        stdin_text=json.dumps(EV_B))
        check("⑧b 未知 param 键 2", rc8b == 2, str(rc8b))
        buf8c = io.StringIO()
        with contextlib.redirect_stdout(buf8c):
            rc8c = main(["--preset", "report-only", "--param", "branch=a",
                         "--on-args", "branch=b"], stdin_text=json.dumps(EV_B))
        check("⑧c 重键 2", rc8c == 2, str(rc8c))
        buf8d = io.StringIO()
        with contextlib.redirect_stdout(buf8d):
            rc8d = main(["--preset", "report-only", "--dry-run"],
                        stdin_text=json.dumps(EV_B))
        check("⑧d dry-run 误档 2", rc8d == 2, str(rc8d))
        bad_meta = dict(EV_B, repo="ORG/R;rm")
        buf8e = io.StringIO()
        with contextlib.redirect_stdout(buf8e):
            rc8e = main(["--preset", "report-only"],
                        stdin_text=json.dumps(bad_meta))
        check("⑧e 元字符拒 9", rc8e == 9 and "shell 元字符" in buf8e.getvalue(),
              "%d %s" % (rc8e, buf8e.getvalue()[:200]))
        _write_tmp(os.path.join(tmp, "st8f.json"), "]{not json")
        buf8f = io.StringIO()
        with contextlib.redirect_stdout(buf8f):
            rc8f = main(["--preset", "auto", "--event-file", evfile,
                         "--state-file", os.path.join(tmp, "st8f.json")])
        check("⑧f state 形坏 9", rc8f == 9 and "state 形坏" in buf8f.getvalue(),
              "%d %s" % (rc8f, buf8f.getvalue()[:200]))
        buf8g = io.StringIO()
        with contextlib.redirect_stdout(buf8g):
            rc8g = main(["--preset", "report-only"],
                        stdin_text=json.dumps({"kind": "weird"}))
        check("⑧g kind 不识 9", rc8g == 9 and "kind 不识别" in buf8g.getvalue(),
              "%d" % rc8g)

        # 矢⑨ rc≠0 不改退出码（假 cw.sh exit 3·rc=3 入账）
        os.environ["RED_DISPATCH_RC"] = "3"
        argv9 = ["--event-file", evfile, "--preset", "auto",
                 "--state-file", os.path.join(tmp, "st9.json"),
                 "--json", os.path.join(tmp, "r9.json")]
        buf9 = io.StringIO()
        with contextlib.redirect_stdout(buf9):
            rc9 = main(argv9)
        rep9 = json.loads(_load_tmp(os.path.join(tmp, "r9.json")))
        check("⑨ rc≠0 不改退出码", rc9 == 0
              and rep9["events"][0].get("rc") == 3
              and rep9["summary"]["executed"] == 1
              and "rc=3≠0" in buf9.getvalue(),
              "%d %s" % (rc9, json.dumps(rep9["summary"], sort_keys=True)))
        if old_rc is None:
            os.environ.pop("RED_DISPATCH_RC", None)
        else:
            os.environ["RED_DISPATCH_RC"] = old_rc

        # 矢⑩ A 族 fix 清单＋C 族定令（内容面咬合）
        check("⑩A fix 清单=evidence 摘要",
              r_a.get("fix_list") == ["Error: AbsSq.v:12", "FAIL 公理计数≠0"]
              and any("禁代修" in n for n in r_a.get("notes") or []),
              json.dumps(r_a.get("fix_list"), ensure_ascii=False))
        ev_a_noev = {"kind": "ci-red", "repo": "ORG/R1", "run": 183,
                     "branch": "dev", "family": "A-content-red",
                     "action": "fix-content"}
        r_a2, _ = build_route(ev_a_noev, "ci-red", {}, None)
        check("⑩A evidence 缺退化指针",
              any("evidence 缺" in n for n in r_a2.get("notes") or [])
              and r_a2.get("fix_list"), json.dumps(r_a2.get("notes")))
        check("⑩C doctor 裸形", r_c.get("cmd") == "bash cw.sh doctor")

        # 矢⑪ 确定性（suggest 双跑 JSON 字节恒同）
        det_in = "\n".join(json.dumps(x, sort_keys=True)
                           for x in (EV_B, EV_A, EV_C)) + "\n"
        out_a, out_b = os.path.join(tmp, "d1.json"), os.path.join(tmp, "d2.json")
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--preset", "suggest", "--json", out_a], stdin_text=det_in)
            main(["--preset", "suggest", "--json", out_b], stdin_text=det_in)
        check("⑪ 双跑字节恒同", _load_tmp(out_a) == _load_tmp(out_b))

        # 矢⑫ 整体单对象兜底
        pretty = json.dumps(EV_B, indent=1, sort_keys=True)
        check("⑫ pretty 单对象兜底", len(parse_events(pretty, "t")) == 1)
        check("⑫ JSONL 三行", len(parse_events(jsonl3, "t")) == 3)
    finally:
        os.chdir(oldcwd)
        if old_log is None:
            os.environ.pop("RED_DISPATCH_LOG", None)
        else:
            os.environ["RED_DISPATCH_LOG"] = old_log
        if old_rc is not None:
            os.environ["RED_DISPATCH_RC"] = old_rc
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        sys.stdout.write("RED-DISPATCH-SELFTEST FAIL: %d 判红: %s\n"
                         % (len(failures), ",".join(failures)))
        return 2
    sys.stdout.write("RED-DISPATCH-SELFTEST PASS: 12 矢量全绿（路由全族/占位/auto "
                     "实证/state 防重/cooldown/report-only 零执行/stdin 多事件/"
                     "fail-loud/rc≠0 不改码/fix 清单/确定性/单对象兜底）\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
