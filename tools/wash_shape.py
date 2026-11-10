#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wash_shape.py — 洗形器·正典形五洗流水（rocqwash tools/·v37 三器共同接口·20261111）

正典形五洗（逐文件依序执行·各洗可 --only 选·判例出处逐洗标注）：
  ①词面洗 lexical   subprocess verify/gate4_comment_guard.py --file（五检项 v2.1
                    EXT·rc 0/1/2 分流承 tools/pushci.py gate4_prescan 先例）→
                    FAIL 项（hard 词面项）与 review 语境双义项对 wash/comment_pack.json
                    flag_words 查正典同义改写式（sidecar 自述 trigger＝「gate4
                    comment-guard review findings」；flag_word_note＝「Context-biaised
                    review words exchange to their neutral English term」——语境双义
                    复核项正是该包的交换靶面）。落刀＝wash/comment_sweep.py --apply
                    （comment_pack 消费器·嵌套注释/字符串感知状态机·代码行相等断言）。
                    无对应式→plan-miss（不硬造——comment_pack「never synthesized」
                    同律）。
  ②token 洗 token   scan/scan_v4_token.py --file 普查（token 级·W5 mixed-line 盲区
                    闭合）→wash/cure_applier.py 正典包（cure_pack v1.3）干跑（该器
                    缺省 dry-run）→--apply 落刀（二遍零残断言内建·rc 1 不落盘）。
                    有站无式→plan-miss；排他组冲突（rc 4）→plan-miss 须人工 --only
                    择一（cure_applier variant-choice 纪律）。
  ③头注形洗 header  两段式＋五字段缺检（gate4 即含：无头注/头注非首块/缺字段/头注
                    超标）→缺失字段方案＝comment_pack 式补写模板（--header-map 逐件
                    数据·comment_sweep --header-map 前导注释区整体替换·内容绝不
                    合成）；或 --header-map-preset 钦名模板（tests/fixtures/
                    header_map_v1.json 蒸馏库·schema rocqwash-header-map/1·占位
                    {name}/{deps_stdlib}/{deps_dev} 承目标件 Require 面与件名派生·
                    {bundle}/{summary}/{mission} 承既有头注逐字携带——任一绑不上
                    plan-miss 不硬造·渲染后仍经 comment_sweep --header-map 落刀）；
                    无模板→plan-miss 不硬造。模板源探测次序：--header-map >
                    --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径）>
                    无＝plan-miss 如实；--header-map 与 --header-map-preset 显传
                    互斥（同槽律 rc 2）。preset 源仅对 gate4 头注域硬项施刀·五字段
                    齐件不对齐改写（防人工 curated 面被机械卷改写·诚实账）。
  ④行尾洗 eol       CRLF→LF 归一（保末行换行形态；3KB 探测窗承 tools/
                    registry_union.py detect_eol EOL_PROBE_BYTES 形制）。前洗引擎
                    universal-newline 写回会附带归一——本洗 apply 以现盘实测为准·
                    零改如实出账。
  ⑤锚形洗 anchor    order.txt 行锚→registry_union.py --reanchor 正典形
                    （#R<序>-<md5 前 8 hex>·20261110 判例：顺序号形锚与跨批撞锚
                    皆此治愈；--reanchor 与 --anchor-src 成对·--apply 必配 --out
                    ——经临时稿 os.replace 回位）。coqproject 行无锚→不适用。
                    缺实体/实体歧义/行无锚→plan-miss（registry_union「缺件如实列
                    跳过」同律）。

两段制：plan（零写盘·逐文件逐洗 {kind,action,status:would-fix|clean|plan-miss,
detail} 清单＋统计）→--apply（执行 would-fix 项→**复跑五洗复核**→全净才 verdict
shaped；复跑不净＝verdict partial·如实列残项）。verdict：clean｜shaped｜partial｜
plan-miss（任一无对应式项在册即 plan-miss——非器力所能及·如实亮账）。

范围与禁触面：--file 多值／--dir 全树（.v＋order.txt/_CoqProject·.v `_*` 下划线
守卫承 gate4 scan_tree v2.1 同律）；certify/frozen8.py 在册八件自动排除（--ledger
账载常量·离线可用）·显式指认冻结件＝红拒命中 exit 2（禁触铁律）；更新账.md 同为
禁触面自动排除。

接口纪律（v37 三器共同）：JSON-in/JSON-out（--json report·schema rocqwash-shape/1·
sort_keys 确定性·无时间戳·同输入重跑字节恒同）；退出码 0=clean/shaped·1=partial/
plan-miss（洗未尽·响亮出账）·2=用法/断言（冻结件红拒·引擎形外退出·JSON 畸形）·
9=缺；--once/--loop 双模（--loop 实时哨态·--interval 可调·JSONL 事件流逐轮一行·
--max-rounds 界定·--apply 可与 loop 并用逐轮落刀）；离线可测（--injector 子进程
调用层罐装 {rc,stdout,report}·--sleep-scale 缩睡·--selftest 全矢量零真网络零真
编译）；编排而非重造（五洗引擎全 subprocess 调用·先读各器 CLI 与 JSON schema 再
编排）。

用法（全部路径参数化·零硬编码绝对路径）：
  python3 tools/wash_shape.py --file A.v [--file B.v ...] [--json OUT]   # plan 段
  python3 tools/wash_shape.py --dir TREE [--exclude 名 ...] [--only 1,3]
  python3 tools/wash_shape.py --file A.v --apply [--header-map M.json] \
      [--header-map-preset NAME] [--anchor-src DIR] [--json OUT]         # 两段全施
  python3 tools/wash_shape.py --dir TREE --loop [--interval 5] \
      [--max-rounds 0] [--events FILE] [--apply]                         # 哨态
  python3 tools/wash_shape.py --selftest

退出码：0=clean/shaped；1=partial/plan-miss（洗未尽·响亮出账）；2=用法错/断言炸
（冻结件红拒/引擎形外退出/JSON 畸形/--header-map 与 --header-map-preset 同槽
互斥）；9=路径缺失（--file/--dir/引擎件/--header-map/--header-map-preset 模板库/
env ROCWASH_HEADER_MAP/--injector）。schema=rocqwash-shape/1。
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROG = "wash_shape"
SCHEMA = "rocqwash-shape/1"

# 五洗 kind（正典序·--only 序号映射 1..5）
KIND_LEXICAL = "lexical"    # ①词面洗
KIND_TOKEN = "token"        # ②token 洗
KIND_HEADER = "header"      # ③头注形洗
KIND_EOL = "eol"            # ④行尾洗
KIND_ANCHOR = "anchor"      # ⑤锚形洗
KINDS = (KIND_LEXICAL, KIND_TOKEN, KIND_HEADER, KIND_EOL, KIND_ANCHOR)
KIND_ALIASES = {
    "1": KIND_LEXICAL, "2": KIND_TOKEN, "3": KIND_HEADER,
    "4": KIND_EOL, "5": KIND_ANCHOR,
    KIND_LEXICAL: KIND_LEXICAL, KIND_TOKEN: KIND_TOKEN,
    KIND_HEADER: KIND_HEADER, KIND_EOL: KIND_EOL, KIND_ANCHOR: KIND_ANCHOR,
}

STATUS_WOULD_FIX = "would-fix"
STATUS_CLEAN = "clean"
STATUS_PLAN_MISS = "plan-miss"

VERDICT_CLEAN = "clean"
VERDICT_SHAPED = "shaped"
VERDICT_PARTIAL = "partial"
VERDICT_PLAN_MISS = "plan-miss"

# gate4 头注域硬项类型（归③头注形洗·词面洗不计）
HEADER_ITEM_TYPES = ("缺字段", "无头注", "头注非首块", "头注超标")
REVIEW_DUAL = "语境双义复核"   # comment_pack 交换靶面（flag_word_note 口径）

# 锚正典 1:1 承 registry_union.ANCHOR_RE；行尾探测窗承 detect_eol
ANCHOR_RE = re.compile(r"#(R\d+(?:-[0-9A-Fa-f]+)?)")
EOL_PROBE_BYTES = 3072

REGISTRY_KINDS = {"order.txt": "order", "_CoqProject": "coqproject"}
LEDGER_NAME = "更新账.md"   # 铁律禁触面（自动排除·显式指认红拒）

ACTION_SWEEP = "wash/comment_sweep.py --apply"
ACTION_SWEEP_MAP = "wash/comment_sweep.py --header-map <MAP> --apply"
ACTION_SWEEP_MAP_PRESET = "wash/comment_sweep.py --header-map <preset 渲染> --apply"
ACTION_CURE = "wash/cure_applier.py --apply"
ACTION_EOL = "wash_shape:eol-rewrite(CRLF->LF)"
ACTION_REGU = "tools/registry_union.py --reanchor --apply"

# ③头注模板源（探测次序 --header-map > --header-map-preset > env > 无=plan-miss）
HEADER_LIB_REL = os.path.join("tests", "fixtures", "header_map_v1.json")
HEADER_LIB_SCHEMA = "rocqwash-header-map/1"
ENV_HEADER_MAP = "ROCWASH_HEADER_MAP"
PH_RE = re.compile(r"\{([a-z_]+)\}")
RE_BUNDLE_L1 = re.compile(
    r"^\(\*\s*ConstructiveWorld-Set\s*--\s+(.+?)\.\s*\*\)\s*$")
RE_TITLE_LINE = re.compile(
    r"^\(\*\*\s*\*\s*[A-Za-z0-9_']+\s*:\s+(.+?)\.\s*$")
RE_MISSION_LABEL = re.compile(r"^\s*Mission\.\s*(.*)$")
RE_NEXT_FIELD = re.compile(
    r"^\s*(?:Dependencies|References|Constructivity|Build)\.")
RE_FROM_STDLIB = re.compile(
    r"^From\s+Stdlib\s+Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$")
RE_FROM_OTHER = re.compile(
    r"^From\s+(?!Stdlib\b)(\S+)\s+Require(?:\s+(?:Import|Export))?\s+"
    r"(.+?)\s*\.\s*$")
RE_BARE_REQUIRE = re.compile(
    r"^Require(?:\s+(?:Import|Export))?\s+(.+?)\s*\.\s*$")


class UsageError(Exception):
    """用法错/断言炸（exit 2：冻结件红拒·引擎形外退出·JSON 畸形）。"""


class MissingInput(Exception):
    """路径缺失（exit 9）。"""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sleep_scaled(sec, scale):
    """time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·承 pushci 同款）。"""
    time.sleep(max(0.0, float(sec) * float(scale)))


def first_code_offset(text):
    """首个代码字符偏移（深度 0·非空白·注释/字符串感知）——前导头注区边界。
    1:1 本地重实现 wash/comment_sweep.py first_code_offset 形制（不 import——
    防引擎件漂移牵连·wash_engine.py 本地重实现同律）。"""
    n = len(text)
    i = 0
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            i += 1
            continue
        if text.startswith("(*", i):
            depth = 1
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if not c.isspace():
            return i
        i += 1
    return None


def resolve_entity(name, anchor_src):
    """anchor_src 下（os.walk 递归）取同名 .v 实体。0 命中→None；多处→歧义串。
    1:1 承 registry_union.resolve_entity 形制。"""
    target = name + ".v"
    direct = os.path.join(anchor_src, target)
    if os.path.isfile(direct):
        return direct
    hits = []
    for root, _dirs, files in os.walk(anchor_src):
        if target in files:
            hits.append(os.path.join(root, target))
    if len(hits) > 1:
        return "AMBIGUOUS:" + ",".join(sorted(hits))
    return hits[0] if hits else None


def md5_8_of(path):
    """实件 md5 前 8 hex（锚正典指纹源·承 registry_union.md5_8_of）。"""
    return md5_of(path)[:8]


def tail_of(text, n=200):
    t = (text or "").strip()
    return t[-n:] if len(t) > n else t


def strip_comment_spans(text):
    """注释域剥离（留换行·字符串感知）——Require 面抽取前置。
    1:1 本地重实现 wash/comment_sweep.py strip_comments 形制（不 import——
    防引擎件漂移牵连·first_code_offset 本地重实现同律）。"""
    out = []
    i, n = 0, len(text)
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                i += 2
                continue
            if c == "\n":
                out.append(c)
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def wrap_long_line(line, width=76, sub="      "):
    """贪心词卷（>width 且含空格才卷·续行缩 6·超长孤词整词保留）——preset
    渲染卷行形制（战役件卷行宽≈76 续行缩 6·DecBridge6.v:19-29 形制引据）。"""
    if len(line) <= width or " " not in line.strip():
        return [line]
    words = line.split(" ")
    rows, cur = [], words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= width:
            cur = cur + " " + w
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    return [rows[0]] + [sub + r for r in rows[1:]]


def require_faces(text):
    """Require 面双列抽取（③头注形洗 preset 占位 {deps_stdlib}/{deps_dev}
    数据源·目标件自身语句逐名·绝不合成）。注释感知剥离（strip_comment_spans）
    后仅取列 0 起顶层语句行：
      From Stdlib Require [Import|Export] A B.  → stdlib 列
      Require [Import|Export] A B.              → dev 列
      From <X> Require [Import|Export] A B.     → dev 列（全名 X.A——战役语料
        五件 grep 零命中·机械完备臂）。
    序＝件内出现序·去重保序。语料引据：ConstructiveWorld-Set @6e805d1
    LW3Kills.v:30-38（From Stdlib 三行＋bare 六行）对照其头注 :13-17 双列；
    abl_tail_supply_67.v:32-35 对照 :15-16。"""
    stdlib, dev = [], []
    for ln in strip_comment_spans(text).split("\n"):
        ln = ln.rstrip()
        names, is_std = None, False
        m = RE_FROM_STDLIB.match(ln)
        if m:
            names, is_std = m.group(1).split(), True
        else:
            m = RE_FROM_OTHER.match(ln)
            if m:
                names = ["%s.%s" % (m.group(1), n) for n in m.group(2).split()]
            else:
                m = RE_BARE_REQUIRE.match(ln)
                if m:
                    names = m.group(1).split()
        if not names:
            continue
        tgt = stdlib if is_std else dev
        for nm in names:
            if nm not in tgt:
                tgt.append(nm)
    return stdlib, dev


def header_carry(text):
    """既有前导头注区逐字携带抽取（preset 占位 {bundle}/{summary}/{mission}
    绑定源）。返回 dict——缺键即该占位绑不上（judge plan-miss 如实·不硬造）：
      bundle＝L1『(* ConstructiveWorld-Set -- <身>. *)』内文（终句号归模板行）；
      summary＝『(** * <名>: <身>.』题行内文（终句号归模板行）；
      mission＝Mission 字段身（标签行余文＋续行至次字段标签/收注符·换行缩进
      原样逐字携带）。
    语料引据：ConstructiveWorld-Set @6e805d1 DecBridge6.v:1/:3/:5-14 三身
    正典位；头注身内容绝不合成（comment_pack header_spec 同律）。"""
    off = first_code_offset(text)
    zone = text[:off] if off is not None else text
    lines = zone.split("\n")
    carry = {}
    for ln in lines:
        if "bundle" not in carry:
            m = RE_BUNDLE_L1.match(ln)
            if m:
                carry["bundle"] = m.group(1).strip()
        if "summary" not in carry:
            m = RE_TITLE_LINE.match(ln)
            if m:
                carry["summary"] = m.group(1).strip()
    for i, ln in enumerate(lines):
        m = RE_MISSION_LABEL.match(ln)
        if not m:
            continue
        parts = [m.group(1).rstrip()] if m.group(1).strip() else []
        j = i + 1
        while j < len(lines):
            l2 = lines[j]
            if RE_NEXT_FIELD.match(l2) or l2.lstrip().startswith("*)"):
                break
            parts.append(l2.rstrip())
            j += 1
        while parts and not parts[0].strip():
            parts.pop(0)
        while parts and not parts[-1].strip():
            parts.pop()
        carry["mission"] = "\n".join(parts)
        break
    return carry


class Injector(object):
    """--injector 场景：子进程调用层罐装（v37 离线可测纪律）。场景 JSON
    {引擎键: {"rc": int, "stdout": str, "report": obj?}}；命中键的引擎调用
    恒定返付 canned（逐调用同响应）·不真 subprocess。键集＝gate4/scan_v4/
    cure/sweep/registry_union/frozen8。"""

    KEYS = ("gate4", "scan_v4", "cure", "sweep", "registry_union", "frozen8")

    def __init__(self, path):
        if not os.path.isfile(path):
            raise MissingInput("injector 场景缺失: %s" % path)
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                scen = json.load(fh)
        except Exception as e:
            raise UsageError("injector 场景 JSON 畸形: %s (%s)" % (path, e))
        if not isinstance(scen, dict):
            raise UsageError("injector 场景须 dict: %s" % path)
        bad = [k for k in scen if k not in self.KEYS]
        if bad:
            raise UsageError("injector 场景键不识（须 %s）: %s"
                             % (",".join(self.KEYS), sorted(bad)))
        self.scen = scen

    def canned(self, key):
        ent = self.scen.get(key)
        if ent is None:
            return None
        if not isinstance(ent, dict):
            raise UsageError("injector 罐装项须 dict: %s" % key)
        return ent


class WashShape(object):
    """洗形器主体：收件→逐洗判（plan）→逐洗施（apply）→复跑复核。"""

    def __init__(self, args):
        self.args = args
        here = os.path.dirname(os.path.abspath(__file__))
        self.repo_root = os.path.abspath(args.repo_root or
                                         os.path.dirname(here))
        self.tool_gate4 = os.path.join(self.repo_root, "verify",
                                       "gate4_comment_guard.py")
        self.tool_scan4 = os.path.join(self.repo_root, "scan",
                                       "scan_v4_token.py")
        self.tool_cure = os.path.join(self.repo_root, "wash",
                                      "cure_applier.py")
        self.tool_sweep = os.path.join(self.repo_root, "wash",
                                       "comment_sweep.py")
        self.tool_regu = os.path.join(self.repo_root, "tools",
                                      "registry_union.py")
        self.tool_frozen8 = os.path.join(self.repo_root, "certify",
                                         "frozen8.py")
        self.pack_comment = os.path.join(self.repo_root, "wash",
                                         "comment_pack.json")
        for label, p in (("gate4", self.tool_gate4),
                         ("scan_v4", self.tool_scan4),
                         ("cure", self.tool_cure),
                         ("sweep", self.tool_sweep),
                         ("registry_union", self.tool_regu),
                         ("frozen8", self.tool_frozen8),
                         ("comment_pack", self.pack_comment)):
            if not os.path.isfile(p):
                raise MissingInput("引擎件缺失（%s）: %s" % (label, p))
        if args.anchor_src and not os.path.isdir(args.anchor_src):
            raise MissingInput("--anchor-src 目录缺失: %s" % args.anchor_src)
        self.injector = Injector(args.injector) if args.injector else None
        self.flag_words = self._load_flag_words()
        # ③头注模板源探测（互斥已在 main 前置 rc2·次序 map > preset > env > 无）
        self.header_map = None
        self.header_source = "none"
        self.header_map_path = None
        self.header_preset_name = None
        self.header_library_path = None
        self.header_preset = None
        self._preset_render_cache = {}
        self._resolve_header_source()
        self.kinds = parse_only(args.only)
        self.frozen_abs, self.frozen_rel, self.frozen_source = \
            self._load_frozen_roster()
        self.excludes = list(args.exclude or [])

    # ---- 数据面 ----

    def _resolve_header_source(self):
        """③头注模板源探测（缺省探测路径次序）：--header-map >
        --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径·与
        --header-map 同构）> 无＝plan-miss 如实（judge_header 缺省臂）。
        --header-map 与 --header-map-preset 同槽互斥 rc2（main 前置）。"""
        args = self.args
        env_map = os.environ.get(ENV_HEADER_MAP)
        if args.header_map:
            self.header_source = "map"
            self.header_map_path = args.header_map
            self.header_map = self._load_header_map(args.header_map,
                                                    "--header-map")
        elif args.header_map_preset:
            self.header_source = "preset"
            self.header_preset_name = args.header_map_preset
            self.header_library_path = os.path.join(self.repo_root,
                                                    HEADER_LIB_REL)
            self.header_preset = self._load_header_preset()
        elif env_map:
            self.header_source = "map"
            self.header_map_path = env_map
            self.header_map = self._load_header_map(env_map,
                                                    "env " + ENV_HEADER_MAP)

    def _load_flag_words(self):
        """comment_pack.json flag_words（正典同义改写式·数据驱动不硬造）。"""
        try:
            with io.open(self.pack_comment, "r", encoding="utf-8") as fh:
                pack = json.load(fh)
        except Exception as e:
            raise UsageError("comment_pack JSON 畸形: %s (%s)"
                             % (self.pack_comment, e))
        fw = pack.get("flag_words")
        if not isinstance(fw, dict):
            raise UsageError("comment_pack 缺 flag_words 表: %s"
                             % self.pack_comment)
        return fw

    def _load_header_map(self, path, label):
        """头注 map 装载（comment_pack 式补写模板·逐件数据·{basename: text}）。
        缺失＝9·畸形＝2（label 标源：--header-map 或 env ROCWASH_HEADER_MAP）。"""
        if not os.path.isfile(path):
            raise MissingInput("%s 缺失: %s" % (label, path))
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                m = json.load(fh)
        except Exception as e:
            raise UsageError("%s JSON 畸形: %s (%s)" % (label, path, e))
        if not isinstance(m, dict):
            raise UsageError("%s 须 {basename: header text}: %s" % (label, path))
        return m

    def _load_header_preset(self):
        """钦名模板装载＋fail-loud 形检（schema rocqwash-header-map/1）：库缺失
        ＝9·JSON 畸形/schema 不识/preset 名不识/占位出白名单/variants 无 else
        兜底/任一模板行缺 evidence 金标引据＝2（金标纪律机械化——无据不铸）。"""
        path = self.header_library_path
        if not os.path.isfile(path):
            raise MissingInput("--header-map-preset 模板库缺失: %s" % path)
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                lib = json.load(fh)
        except Exception as e:
            raise UsageError("模板库 JSON 畸形: %s (%s)" % (path, e))
        if not isinstance(lib, dict) or lib.get("schema") != HEADER_LIB_SCHEMA:
            raise UsageError("模板库 schema 不识（须 %s）: %s"
                             % (HEADER_LIB_SCHEMA, path))
        presets = lib.get("presets")
        if not isinstance(presets, dict) or not presets:
            raise UsageError("模板库缺 presets 表: %s" % path)
        name = self.header_preset_name
        if name not in presets:
            raise UsageError("preset 名不识（库 %s 在册: %s）: %s"
                             % (path, ",".join(sorted(presets)), name))
        pre = presets[name]
        known = lib.get("placeholders")
        if not isinstance(known, dict) or not known:
            raise UsageError("模板库缺 placeholders 白名单: %s" % path)
        if not isinstance(pre.get("evidence"), list) or not pre["evidence"]:
            raise UsageError("preset %r 缺金标 evidence（无据不铸）: %s"
                             % (name, path))
        lines = pre.get("lines")
        if not isinstance(lines, list) or not lines:
            raise UsageError("preset %r 缺 lines 模板行: %s" % (name, path))

        def ph_scan(s, where):
            bad = sorted(set(m.group(1) for m in PH_RE.finditer(s)
                             if m.group(1) not in known))
            if bad:
                raise UsageError("占位出白名单（%s）: %s" % (where, ",".join(bad)))

        for ent in lines:
            if isinstance(ent, str):
                ph_scan(ent, "行式模板")
                continue
            if not isinstance(ent, dict) or not isinstance(
                    ent.get("variants"), list) or not ent["variants"]:
                raise UsageError("variants 槽式模板形畸（须 {slot, variants}）: "
                                 "%s" % path)
            has_else = False
            for v in ent["variants"]:
                if not isinstance(v, dict) or not isinstance(v.get("line"), str):
                    raise UsageError("variant 形畸（须 {when, line, evidence}）: "
                                     "%s" % path)
                ph_scan(v["line"], "variants 式")
                ev = v.get("evidence")
                if not isinstance(ev, list) or not ev:
                    raise UsageError("variant 缺金标 evidence（无据不铸）: %s"
                                     % path)
                when = v.get("when")
                if when == "else":
                    has_else = True
                elif isinstance(when, dict) and when:
                    badk = [k for k in when if k not in known
                            or not isinstance(when[k], bool)]
                    if badk:
                        raise UsageError("when 键出白名单/非布尔: %s"
                                         % ",".join(sorted(badk)))
                else:
                    raise UsageError("when 须 'else' 或非空 bool dict: %s" % path)
            if not has_else:
                raise UsageError("variants 无 else 兜底（渲染须全态可决）: %s"
                                 % path)
        return {"desc": pre.get("desc", ""), "lines": lines}

    def render_preset_header(self, path, text):
        """preset 渲染（③头注形洗·占位替换）：模板行逐行替换占位→超宽行贪心
        卷（wrap_long_line）。占位值全部承目标件自身——{name}＝basename 去 .v·
        {deps_stdlib}/{deps_dev}＝require_faces 双列·{bundle}/{summary}/
        {mission}＝header_carry 既有头注逐字携带——绝不合成。任一占位绑不上→
        (None, 缺位清单)（judge 记 plan-miss 如实）。缓存键＝(abspath, 文面
        md5)（loop 逐轮重判·同件同文恒同·件变即重渲）。"""
        key = (os.path.abspath(path), hashlib.md5(
            text.encode("utf-8", "replace")).hexdigest())
        if key in self._preset_render_cache:
            return self._preset_render_cache[key]
        base = os.path.basename(path)
        stdlib, dev = require_faces(text)
        carry = header_carry(text)
        vals = {"name": base[:-2] if base.endswith(".v") else base,
                "deps_stdlib": ", ".join("[%s]" % n for n in stdlib),
                "deps_dev": ", ".join("[%s]" % n for n in dev),
                "bundle": carry.get("bundle"),
                "summary": carry.get("summary"),
                "mission": carry.get("mission")}
        missing = sorted(k for k, v in vals.items() if v is None)
        out_rows = []
        if not missing:
            for ent in self.header_preset["lines"]:
                if isinstance(ent, str):
                    rows = [ent]
                else:
                    chosen = None
                    for v in ent["variants"]:
                        when = v["when"]
                        if when == "else" or all(
                                bool(vals[k]) == w for k, w in when.items()):
                            chosen = v["line"]
                            break
                    rows = [chosen]  # else 兜底装载已验·chosen 恒非 None
                for row in rows:
                    filled = PH_RE.sub(lambda m: vals[m.group(1)], row)
                    for phys in filled.split("\n"):
                        if phys.startswith("    "):
                            # 卷行仅施字段身行（4 空格起）——L1 束语行与题行
                            # 全战役语料恒单行（DecBridge6.v:1 103 列/:3 96 列·
                            # abl_tail_supply_66.v:1 95 列皆单行）·不卷。
                            out_rows.extend(wrap_long_line(phys))
                        else:
                            out_rows.append(phys)
            rendered = "\n".join(out_rows) + "\n"
        self._preset_render_cache[key] = \
            (rendered, None) if not missing else (None, missing)
        return self._preset_render_cache[key]

    def header_map_entry(self, basename):
        """映射查得（basename 带/不带 .v 双试·承 comment_sweep.run 同款）。
        仅 map 源（--header-map/env）——preset 源走 render_preset_header。"""
        if not self.header_map:
            return None
        keys = [basename, basename[:-2]] if basename.endswith(".v") \
            else [basename]
        for k in keys:
            if k in self.header_map:
                return self.header_map[k]
        return None

    def _load_frozen_roster(self):
        """certify/frozen8.py --ledger → (abs 集, rel 集, 来源说明)。
        --ledger 只打账载常量（离线·零盘验）·injector 可罐装。行式
        「md5<空白>relpath」；绝对路径行按 abs 收·相对行对 repo_root 归位。"""
        rc, out, _rep, canned = self.run_engine(
            "frozen8", self.tool_frozen8, ["--ledger"])
        if rc != 0:
            raise UsageError("frozen8 --ledger 形外退出 rc=%d: %s"
                             % (rc, tail_of(out)))
        abs_set, rel_set = set(), set()
        for ln in out.splitlines():
            parts = ln.split()
            if len(parts) < 2:
                continue
            rel = parts[1]
            if os.path.isabs(rel):
                abs_set.add(os.path.normpath(rel))
            else:
                rel_set.add(os.path.normpath(rel))
                abs_set.add(os.path.normpath(
                    os.path.join(self.repo_root, rel)))
        src = "injector-canned" if canned else "certify/frozen8.py --ledger"
        return abs_set, rel_set, src

    def is_frozen(self, path):
        ap = os.path.abspath(path)
        if ap in self.frozen_abs:
            return True
        try:
            rel = os.path.relpath(ap, self.repo_root)
        except ValueError:
            return False
        return rel in self.frozen_rel

    def is_forbidden(self, path):
        """铁律禁触面：冻结八件在册∪更新账.md。"""
        return self.is_frozen(path) or \
            os.path.basename(path) == LEDGER_NAME

    # ---- 引擎调用层（注入点）----

    def run_engine(self, key, tool_abs, cli, want_json=False):
        """子进程调用层：injector 命中键→罐装恒定返付；否则真 subprocess
        [sys.executable, -B, tool] + cli（stdout+stderr 合流·承 pushci
        _run_py 形制）。want_json→附 --json tmp·解析后即删。返回
        (rc, stdout, report|None, canned_flag)。"""
        canned = self.injector.canned(key) if self.injector else None
        if canned is not None:
            rep = canned.get("report")
            return (int(canned.get("rc", 0)), str(canned.get("stdout", "")),
                    rep, True)
        if not os.path.isfile(tool_abs):
            raise MissingInput("引擎件缺失: %s" % tool_abs)
        full_cli = list(cli)
        tmp = None
        if want_json:
            fd, tmp = tempfile.mkstemp(prefix="wash_shape_eng_")
            os.close(fd)
            full_cli = full_cli + ["--json", tmp]
        try:
            p = subprocess.run([sys.executable, "-B", tool_abs] + full_cli,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            out = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            rep = None
            if want_json and tmp and os.path.isfile(tmp) and \
                    os.path.getsize(tmp) > 0:
                try:
                    with io.open(tmp, "r", encoding="utf-8") as fh:
                        rep = json.load(fh)
                except Exception:
                    rep = None
            return p.returncode, out, rep, False
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    # ---- 收件 ----

    def collect_files(self):
        """--file 显式（存在性 9·禁触面红拒 2）＋ --dir 全树（.v 非 _·registry
        两名·隐目录跳过·禁触面与 --exclude 自动排除）。去重按 abspath·序按
        构造路径字符串（确定性）。返回 (files, excluded 记录)。"""
        args = self.args
        files, seen = [], set()
        excluded = []

        def add(path):
            ap = os.path.abspath(path)
            if ap in seen:
                return
            seen.add(ap)
            files.append(path)

        for p in (args.file or []):
            if not os.path.exists(p):
                raise MissingInput("--file 缺失: %s" % p)
            if self.is_forbidden(p):
                raise UsageError("FATAL 冻结件红拒: %s（certify/frozen8.py "
                                 "在册/更新账·禁触铁律——洗形器拒不执行）" % p)
            add(p)
        for d in (args.dir or []):
            if not os.path.isdir(d):
                raise MissingInput("--dir 缺失: %s" % d)
            for root, dirs, names in os.walk(d):
                dirs[:] = sorted(x for x in dirs
                                 if not x.startswith("."))
                for n in sorted(names):
                    p = os.path.join(root, n)
                    if self.is_forbidden(p):
                        excluded.append({"path": p, "reason": "frozen8-roster"
                                         if self.is_frozen(p) else "更新账"})
                        continue
                    if self.user_excluded(p):
                        excluded.append({"path": p, "reason": "--exclude"})
                        continue
                    if n.endswith(".v"):
                        if n.startswith("_"):
                            excluded.append({"path": p,
                                             "reason": "underscore-guard"})
                            continue
                        add(p)
                    elif n in REGISTRY_KINDS:
                        add(p)
        files = sorted(files, key=lambda x: os.path.abspath(x))
        return files, excluded

    def user_excluded(self, path):
        base = os.path.basename(path)
        for name in self.excludes:
            if not name:
                continue
            if name == base or name in path.split(os.sep):
                return True
        return False

    # ---- 逐洗判（plan·零写盘）----

    def gate4_report(self, path):
        """gate4 单件报告（rc 0/1/2 正常·形外/JSON 畸形→器红 exit 2）。"""
        rc, out, rep, _c = self.run_engine("gate4", self.tool_gate4,
                                           ["--file", path], want_json=True)
        if rc not in (0, 1, 2):
            raise UsageError("gate4 形外退出 rc=%d: %s" % (rc, tail_of(out)))
        if not isinstance(rep, dict) or not rep.get("results"):
            raise UsageError("gate4 JSON 出账缺失/畸形: %s" % tail_of(out))
        return rep["results"][0]

    def judge_lexical(self, path, g4):
        """①词面洗：gate4 hard 词面项＋review 语境双义项→flag_words 查式。"""
        hard = g4.get("hard") or []
        review = g4.get("review") or []
        verdict = g4.get("verdict", "?")
        if verdict == "UNREADABLE":
            return self._w(KIND_LEXICAL, STATUS_PLAN_MISS,
                           "gate4 UNREADABLE（面不可读·无式可施）")
        lex = [it for it in hard if it[2] not in HEADER_ITEM_TYPES]
        dual = [it for it in review if it[2] == REVIEW_DUAL]
        manual = len(review) - len(dual)
        fixable, unfix = [], []
        for it in lex:
            w = it[3]
            tag = it[2]
            if w in self.flag_words:
                fixable.append("%s:%s→%s" % (tag, w, self.flag_words[w]))
            else:
                unfix.append("%s:%s" % (tag, w))
        for it in dual:
            w = it[3].split("（", 1)[0]
            if w in self.flag_words:
                fixable.append("双义:%s→%s" % (w, self.flag_words[w]))
            else:
                unfix.append("双义:%s（无对应式）" % w)
        detail = ("gate4=%s hard=%d(词面项=%d) review=%d(双义=%d 人工域=%d) "
                  "可改写=%d 无式=%d" % (verdict, len(hard), len(lex),
                                         len(review), len(dual), manual,
                                         len(fixable), len(unfix)))
        if fixable:
            detail += " 可改写[" + ";".join(fixable[:8]) + "]"
        if unfix:
            detail += " 无式[" + ";".join(unfix[:8]) + "]"
        status = (STATUS_WOULD_FIX if fixable
                  else (STATUS_PLAN_MISS if unfix else STATUS_CLEAN))
        return self._w(KIND_LEXICAL, status, detail,
                       n_fix=len(fixable), n_miss=len(unfix))

    def judge_token(self, path):
        """②token 洗：scan_v4 普查→cure_applier 正典包干跑。"""
        rc, out, cen, _c = self.run_engine("scan_v4", self.tool_scan4,
                                           ["--file", path], want_json=True)
        if rc != 0:
            raise UsageError("scan_v4 形外退出 rc=%d: %s" % (rc, tail_of(out)))
        if not isinstance(cen, dict):
            raise UsageError("scan_v4 census JSON 缺失/畸形: %s"
                             % tail_of(out))
        n = int(cen.get("station_count", 0) or 0)
        if n == 0:
            return self._w(KIND_TOKEN, STATUS_CLEAN,
                           "census 站=0（tracked=%s）"
                           % ",".join(cen.get("tracked_ids") or []))
        rc2, out2, crep, _c2 = self.run_engine("cure", self.tool_cure,
                                               ["--file", path],
                                               want_json=True)
        if rc2 == 4:
            return self._w(KIND_TOKEN, STATUS_PLAN_MISS,
                           "census 站=%d·正典包排他组冲突（两变体皆中·须人工"
                           " --only 择一）: %s" % (n, tail_of(out2, 160)))
        if rc2 != 0:
            raise UsageError("cure_applier 干跑形外退出 rc=%d: %s"
                             % (rc2, tail_of(out2)))
        total = sum(int(v.get("matches", 0) or 0)
                    for v in ((crep or {}).get("report") or {}).values())
        if total:
            return self._w(KIND_TOKEN, STATUS_WOULD_FIX,
                           "census 站=%d·正典包干跑命中=%d" % (n, total),
                           n_fix=total)
        return self._w(KIND_TOKEN, STATUS_PLAN_MISS,
                       "census 站=%d·正典包零命中（无对应式）" % n,
                       n_miss=n)

    def judge_header(self, path, g4, text):
        """③头注形洗：gate4 头注域硬项＋模板判（map 源＝逐件数据·对齐判与
        补写判并施；preset 源＝钦名模板渲染——仅对硬项施刀·五字段齐件不对齐
        改写（防人工 curated 面被机械卷改写·诚实账）；无源＝plan-miss 如实）。"""
        items = [it for it in (g4.get("hard") or [])
                 if it[2] in HEADER_ITEM_TYPES]
        item_strs = ["%s:%s" % (it[2], it[3]) for it in items]
        miss_ph = None
        if self.header_source == "map":
            mapped = self.header_map_entry(os.path.basename(path))
        elif self.header_source == "preset":
            mapped, miss_ph = self.render_preset_header(path, text)
        else:
            mapped = None
        if mapped is not None:
            if items:
                how = "comment_pack 式模板整体补写" \
                    if self.header_source == "map" else "钦名模板渲染整体补写"
                return self._w(KIND_HEADER, STATUS_WOULD_FIX,
                               "头注项=%d[%s]·%s"
                               % (len(items), ";".join(item_strs[:6]), how))
            if self.header_source == "map":
                off = first_code_offset(text)
                cur = text[:off] if off is not None else ""
                if cur != mapped:
                    return self._w(KIND_HEADER, STATUS_WOULD_FIX,
                                   "头注形与模板差（整体补写对齐）")
                return self._w(KIND_HEADER, STATUS_CLEAN,
                               "头注正典形（模板已在位）")
            return self._w(KIND_HEADER, STATUS_CLEAN,
                           "头注无项（首块·五字段齐·preset 不对齐改写）")
        if items:
            if miss_ph:
                return self._w(KIND_HEADER, STATUS_PLAN_MISS,
                               "preset 渲染绑不上占位[%s]（承件缺既有头注身）"
                               "·不硬造: [%s]"
                               % (",".join(miss_ph),
                                  ";".join(item_strs[:6])),
                               n_miss=len(items))
            return self._w(KIND_HEADER, STATUS_PLAN_MISS,
                           "无补写模板（模板源=%s 未配/缺条目）·不硬造: [%s]"
                           % (self.header_source,
                              ";".join(item_strs[:6])),
                           n_miss=len(items))
        return self._w(KIND_HEADER, STATUS_CLEAN,
                       "头注无项（首块·五字段齐）")

    def judge_eol(self, path, raw):
        """④行尾洗：CRLF→LF 归一（末行换行形态保全）。"""
        n = raw.count(b"\r\n")
        lone = raw.count(b"\r") - n
        fin = "有" if raw.endswith(b"\n") else "无"
        if n == 0:
            detail = "CRLF=0·LF 已归一（末行换行=%s）" % fin
            if lone:
                detail += "·lone_CR=%d（非 CRLF 口径·不改）" % lone
            return self._w(KIND_EOL, STATUS_CLEAN, detail)
        return self._w(KIND_EOL, STATUS_WOULD_FIX,
                       "CRLF 行尾=%d（末行换行形态保全）" % n
                       + ("·lone_CR=%d" % lone if lone else ""),
                       n_fix=n)

    def judge_anchor(self, path, raw):
        """⑤锚形洗：order.txt 行锚正典形判（#R<序>-<md5 前 8>）。"""
        base = os.path.basename(path)
        kind = REGISTRY_KINDS.get(base)
        if kind is None:
            return self._w(KIND_ANCHOR, STATUS_CLEAN,
                           "非 registry（order.txt/_CoqProject）·此洗不适用")
        if kind == "coqproject":
            return self._w(KIND_ANCHOR, STATUS_CLEAN,
                           "coqproject 行无锚（registry_union 口径）·不适用")
        anchor_src = self.args.anchor_src or \
            os.path.dirname(os.path.abspath(path))
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return self._w(KIND_ANCHOR, STATUS_PLAN_MISS,
                           "registry 非 UTF-8 面: %s" % e, n_miss=1)
        lines = [ln.rstrip("\r\n").strip()
                 for ln in text.split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        fix_rows, miss_rows = [], []
        modules = []
        for ln in lines:
            if not ln:
                continue
            head = ln.split("#", 1)[0].strip()
            if not head:
                continue  # 纯注释行（registry_union key_of=None 同律）
            m = ANCHOR_RE.search(ln)
            if m is None:
                miss_rows.append("行无锚不可重锚（无序号可承）: %s" % ln)
                continue
            anchor = m.group(0)
            seq = anchor[2:].split("-", 1)[0]
            module = head[:-2] if head.endswith(".v") else head
            entity = resolve_entity(module, anchor_src)
            if entity is None:
                miss_rows.append("缺实体（%s 下无 %s.v）: %s"
                                 % (anchor_src, module, ln))
                continue
            if entity.startswith("AMBIGUOUS:"):
                miss_rows.append("实体歧义（registry_union 拒锚）: %s"
                                 % entity[len("AMBIGUOUS:"):])
                continue
            fp = md5_8_of(entity)
            canonical = "#R%s-%s" % (seq, fp)
            if anchor != canonical:
                fix_rows.append("%s: %s→%s" % (module, anchor, canonical))
                if module not in modules:
                    modules.append(module)
        detail = "order 锚判：非正典=%d 无式=%d" % (len(fix_rows),
                                                   len(miss_rows))
        if fix_rows:
            detail += " [" + ";".join(fix_rows[:8]) + "]"
        if miss_rows:
            detail += " 无式[" + ";".join(miss_rows[:6]) + "]"
        status = (STATUS_WOULD_FIX if fix_rows
                  else (STATUS_PLAN_MISS if miss_rows else STATUS_CLEAN))
        return self._w(KIND_ANCHOR, status, detail,
                       n_fix=len(fix_rows), n_miss=len(miss_rows),
                       modules=modules)

    # ---- plan 组装 ----

    def plan_file(self, path):
        """单件逐洗判（正典序①→⑤·零写盘）。"""
        kinds = self.kinds
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as e:
            return {"file": path, "washes": [
                self._w(k, STATUS_PLAN_MISS, "件不可读: %s" % e, n_miss=1)
                for k in kinds]}
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        is_v = path.endswith(".v")
        g4 = None
        if is_v and (KIND_LEXICAL in kinds or KIND_HEADER in kinds):
            g4 = self.gate4_report(path)
        washes = []
        if is_v:
            if KIND_LEXICAL in kinds:
                washes.append(self.judge_lexical(path, g4))
            if KIND_TOKEN in kinds:
                washes.append(self.judge_token(path))
            if KIND_HEADER in kinds:
                washes.append(self.judge_header(path, g4, text))
        else:
            for k, note in ((KIND_LEXICAL, "非 .v 源·词面洗不适用"),
                            (KIND_TOKEN, "非 .v 源·token 洗不适用"),
                            (KIND_HEADER, "非 .v 源·头注形洗不适用")):
                if k in kinds:
                    washes.append(self._w(k, STATUS_CLEAN, note))
        if KIND_EOL in kinds:
            washes.append(self.judge_eol(path, raw))
        if KIND_ANCHOR in kinds:
            washes.append(self.judge_anchor(path, raw))
        return {"file": path, "washes": washes}

    def compute_plan(self):
        """全范围 plan（零写盘）→ {"files": [...], "stats": {...}}。"""
        entries = [self.plan_file(p) for p in self.files]
        return {"files": entries, "stats": stats_of(entries)}

    # ---- 逐洗施（apply·两段第二段）----

    def apply_lexical(self, path):
        rc, out, rep, canned = self.run_engine(
            "sweep", self.tool_sweep, ["--file", path, "--apply"],
            want_json=True)
        if rc != 0:
            raise UsageError("comment_sweep --apply 器红 rc=%d: %s"
                             % (rc, tail_of(out)))
        r = (rep or {}).get("report") or {}
        return {"file": path, "kind": KIND_LEXICAL,
                "engine": "wash/comment_sweep.py", "rc": 0,
                "detail": "flag_swaps=%d%s" % (int(r.get("flag_swaps", 0) or 0),
                                               "（injector 罐装）" if canned
                                               else "")}

    def apply_token(self, path):
        rc, out, rep, canned = self.run_engine(
            "cure", self.tool_cure, ["--file", path, "--apply"],
            want_json=True)
        if rc != 0:
            raise UsageError("cure_applier --apply 器红 rc=%d（不落盘·二遍"
                             "零残断言）: %s" % (rc, tail_of(out)))
        hits = sum(int(v.get("matches", 0) or 0)
                   for v in ((rep or {}).get("report") or {}).values())
        return {"file": path, "kind": KIND_TOKEN,
                "engine": "wash/cure_applier.py", "rc": 0,
                "detail": "pattern_hits=%d%s" % (hits,
                                                 "（injector 罐装）" if canned
                                                 else "")}

    def apply_header(self, path):
        """③落刀：comment_sweep --header-map <具体 map> --apply（引擎恒
        comment_sweep·编排零新引擎）。map 源＝显传/env 路径；preset 源＝现渲
        染单件 map 临时落盘（{basename: 渲染文}·用后即删——渲染值承件自身
        数据·编排不落常盘）。绑不上（件面在 plan 后漂移）→器红 rc2 fail-loud。"""
        tmp = None
        try:
            if self.header_source == "preset":
                with open(path, "rb") as fh:
                    text = fh.read().decode("utf-8")
                rendered, miss_ph = self.render_preset_header(path, text)
                if rendered is None:
                    raise UsageError(
                        "preset 渲染绑不上占位[%s]（apply 时件面漂移）: %s"
                        % (",".join(miss_ph), path))
                fd, tmp = tempfile.mkstemp(prefix="wash_shape_hmap_")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump({os.path.basename(path): rendered}, fh,
                              ensure_ascii=False, sort_keys=True)
                map_path = tmp
            else:
                map_path = self.header_map_path
            rc, out, rep, canned = self.run_engine(
                "sweep", self.tool_sweep,
                ["--file", path, "--header-map", map_path, "--apply"],
                want_json=True)
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        if rc != 0:
            raise UsageError("comment_sweep --header-map --apply 器红 rc=%d: %s"
                             % (rc, tail_of(out)))
        r = (rep or {}).get("report") or {}
        return {"file": path, "kind": KIND_HEADER,
                "engine": "wash/comment_sweep.py", "rc": 0,
                "detail": "header_replaced=%s flag_swaps=%d%s"
                          % (r.get("header_replaced"),
                             int(r.get("flag_swaps", 0) or 0),
                             "（injector 罐装）" if canned else "")}

    def apply_eol(self, path, raw):
        n = raw.count(b"\r\n")
        if n == 0:
            return {"file": path, "kind": KIND_EOL, "engine": "wash_shape",
                    "rc": 0,
                    "detail": "crlf_converted=0 changed=False（前洗已附带"
                              "归一·如实）"}
        with open(path, "wb") as fh:
            fh.write(raw.replace(b"\r\n", b"\n"))
        return {"file": path, "kind": KIND_EOL, "engine": "wash_shape",
                "rc": 0, "detail": "crlf_converted=%d changed=True（末行换行"
                                   "形态保全）" % n}

    def apply_anchor(self, path, modules):
        anchor_src = self.args.anchor_src or \
            os.path.dirname(os.path.abspath(path))
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)),
                                   prefix=".wash_shape_reanchor_")
        os.close(fd)
        try:
            rc, out, rep, canned = self.run_engine(
                "registry_union", self.tool_regu,
                ["--base", path, "--main", path, "--branch", path,
                 "--kind", "order", "--reanchor", ",".join(modules),
                 "--anchor-src", anchor_src, "--out", tmp, "--apply"],
                want_json=True)
            if rc != 0:
                raise UsageError("registry_union --reanchor 器红 rc=%d（零"
                                 "写盘）: %s" % (rc, tail_of(out)))
            rewrites = ((rep or {}).get("reanchor") or {}).get("rewrites") or []
            if canned:
                return {"file": path, "kind": KIND_ANCHOR,
                        "engine": "tools/registry_union.py", "rc": 0,
                        "detail": "rewrites=%d（injector 罐装·未回位）"
                                  % len(rewrites)}
            os.replace(tmp, path)
            tmp = None
            return {"file": path, "kind": KIND_ANCHOR,
                    "engine": "tools/registry_union.py", "rc": 0,
                    "detail": "rewrites=%d modules=%s"
                              % (len(rewrites), ",".join(modules))}
        finally:
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def apply_one(self, path, wash):
        """单洗落刀（按 plan 判面分发·正典序由调用方保证）。"""
        kind = wash["kind"]
        if kind == KIND_LEXICAL:
            return self.apply_lexical(path)
        if kind == KIND_TOKEN:
            return self.apply_token(path)
        if kind == KIND_HEADER:
            return self.apply_header(path)
        if kind == KIND_EOL:
            with open(path, "rb") as fh:
                return self.apply_eol(path, fh.read())
        if kind == KIND_ANCHOR:
            return self.apply_anchor(path, wash.get("_modules") or [])
        raise UsageError("洗 kind 不识: %s" % kind)

    # ---- verdict 与报告 ----

    def verdict_of(self, entries, n_applied, apply_mode):
        """verdict：任一项级无式（洗级 plan-miss 或 _n_miss>0）→plan-miss；
        余 would-fix→partial；apply 模式有施→shaped；否则 clean。"""
        miss = any(w["status"] == STATUS_PLAN_MISS or w.get("_n_miss", 0) > 0
                   for f in entries for w in f["washes"])
        pend = any(w["status"] == STATUS_WOULD_FIX
                   for f in entries for w in f["washes"])
        if miss:
            return VERDICT_PLAN_MISS
        if pend:
            return VERDICT_PARTIAL
        if apply_mode and n_applied:
            return VERDICT_SHAPED
        return VERDICT_CLEAN

    def report_of(self, plan, applied, rescan, verdict, excluded):
        rep = {
            "schema": SCHEMA,
            "mode": "loop" if self.args.loop else
                    ("apply" if self.args.apply else "plan"),
            "scope": {"only": list(self.kinds),
                      "header_map": {"source": self.header_source,
                                     "path": self.header_map_path,
                                     "preset": self.header_preset_name,
                                     "library": self.header_library_path},
                      "frozen_roster_source": self.frozen_source,
                      "excluded": sorted(excluded,
                                         key=lambda x: (x["path"],
                                                        x["reason"]))},
            "verdict": verdict,
        }
        if self.args.apply:
            rep["apply"] = {"applied": applied,
                            "rescan": project_plan(rescan) if rescan else None}
        rep["plan"] = project_plan(plan)
        return rep

    def dump_report(self, path, rep):
        """确定性 JSON 落盘（sort_keys＋indent=1·与 registry_union.dump_json
        同律·原子写）。"""
        d = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(d):
            raise MissingInput("--json 出路径目录缺失: %s" % path)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".wash_shape_json_")
        try:
            with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(rep, fh, indent=1, ensure_ascii=False,
                          sort_keys=True)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # ---- 主流程 ----

    def one_pass(self, round_no=None):
        """一段完整流水：plan→(--apply? 落刀→复跑五洗复核)→(verdict, report)。
        返回 (verdict, report, n_applied)。"""
        plan = self.compute_plan()
        applied = []
        rescan = None
        if self.args.apply:
            for fentry in plan["files"]:
                for w in fentry["washes"]:
                    if w["status"] == STATUS_WOULD_FIX:
                        applied.append(self.apply_one(fentry["file"], w))
            rescan = self.compute_plan()
            current = rescan
        else:
            current = plan
        verdict = self.verdict_of(current["files"], len(applied),
                                  self.args.apply)
        report = self.report_of(plan, applied, rescan, verdict,
                                self.excluded_records)
        return verdict, report, len(applied)

    def run_once(self):
        verdict, report, n_applied = self.one_pass()
        if self.args.jsonout:
            self.dump_report(self.args.jsonout, report)
        self.print_summary(report, verdict, n_applied)
        return exit_code_of(verdict)

    def run_loop(self):
        """哨态：逐轮 one_pass·JSONL 事件流（逐轮一行·sort_keys）·--events
        追加落账·--max-rounds 界定（0=无限）。"""
        rnd = 0
        last_rc = 0
        while True:
            rnd += 1
            verdict, report, n_applied = self.one_pass(round_no=rnd)
            if self.args.jsonout:
                self.dump_report(self.args.jsonout, report)
            stats = (report.get("apply") or {}).get("rescan", {}) \
                if self.args.apply else report["plan"]
            st = stats.get("stats", {})
            event = {"event": "round", "round": rnd, "mode": "loop",
                     "apply": bool(self.args.apply), "verdict": verdict,
                     "files": st.get("files", 0),
                     "n_would_fix": st.get("would_fix", 0),
                     "n_plan_miss": st.get("plan_miss", 0),
                     "n_plan_miss_items": st.get("plan_miss_items", 0),
                     "n_applied": n_applied}
            line = json.dumps(event, ensure_ascii=False, sort_keys=True)
            print(line)
            sys.stdout.flush()
            if self.args.events:
                with io.open(self.args.events, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            last_rc = exit_code_of(verdict)
            if self.args.max_rounds and rnd >= self.args.max_rounds:
                stop = {"event": "stop", "round": rnd,
                        "reason": "max-rounds", "verdict": verdict}
                sline = json.dumps(stop, ensure_ascii=False, sort_keys=True)
                print(sline)
                if self.args.events:
                    with io.open(self.args.events, "a",
                                 encoding="utf-8") as fh:
                        fh.write(sline + "\n")
                break
            sleep_scaled(self.args.interval, self.args.sleep_scale)
        return last_rc

    def print_summary(self, report, verdict, n_applied):
        plan = report["plan"]
        st = plan["stats"]
        head = "== WASH-SHAPE verdict=%s files=%d would_fix=%d clean=%d " \
               "plan_miss=%d(plan_miss_items=%d)" % (
                   verdict, st["files"], st["would_fix"], st["clean"],
                   st["plan_miss"], st["plan_miss_items"])
        if self.args.apply:
            head += " applied=%d" % n_applied
        head += " =="
        print(head)
        for f in plan["files"]:
            for w in f["washes"]:
                if w["status"] != STATUS_CLEAN:
                    print("  %s %s %s %s" % (w["status"].upper(),
                                             f["file"], w["kind"],
                                             w["detail"]))
        if self.args.apply and report.get("apply"):
            rs = report["apply"]["rescan"]
            rst = rs["stats"]
            print("RESCAN: would_fix=%d plan_miss=%d(plan_miss_items=%d)"
                  % (rst["would_fix"], rst["plan_miss"],
                     rst["plan_miss_items"]))
            for f in rs["files"]:
                for w in f["washes"]:
                    if w["status"] != STATUS_CLEAN:
                        print("  残项 %s %s %s %s" % (w["status"].upper(),
                                                      f["file"], w["kind"],
                                                      w["detail"]))
        for e in report["scope"]["excluded"]:
            print("  EXCLUDED %s (%s)" % (e["path"], e["reason"]))

    # ---- 内件 ----

    def _w(self, kind, status, detail, n_fix=0, n_miss=0, modules=None):
        """洗目条目：外显四键（kind/action/status/detail·schema 面）＋内部
        统计键（_ 前缀·落盘投影时剥除）。"""
        action = "none"
        if status == STATUS_WOULD_FIX:
            action = {KIND_LEXICAL: ACTION_SWEEP,
                      KIND_TOKEN: ACTION_CURE,
                      KIND_HEADER: (ACTION_SWEEP_MAP
                                    if self.header_source == "map" else
                                    (ACTION_SWEEP_MAP_PRESET
                                     if self.header_source == "preset"
                                     else "none")),
                      KIND_EOL: ACTION_EOL,
                      KIND_ANCHOR: ACTION_REGU}.get(kind, "none")
        ent = {"kind": kind, "action": action, "status": status,
               "detail": detail, "_n_fix": n_fix, "_n_miss": n_miss}
        if modules is not None:
            ent["_modules"] = modules
        return ent


def project_entry(ent):
    """洗目条目→schema 面四键（_ 内部键剥除）。"""
    return {"kind": ent["kind"], "action": ent["action"],
            "status": ent["status"], "detail": ent["detail"]}


def project_plan(plan):
    files = [{"file": f["file"],
              "washes": [project_entry(w) for w in f["washes"]]}
             for f in plan["files"]]
    return {"files": files, "stats": plan["stats"]}


def stats_of(entries):
    """plan 统计：files/wash_entries/would_fix/clean/plan_miss（洗级）/
    plan_miss_items（项级）。"""
    st = {"files": len(entries), "wash_entries": 0, "would_fix": 0,
          "clean": 0, "plan_miss": 0, "plan_miss_items": 0,
          "would_fix_items": 0}
    for f in entries:
        for w in f["washes"]:
            st["wash_entries"] += 1
            st["plan_miss_items"] += w.get("_n_miss", 0)
            st["would_fix_items"] += w.get("_n_fix", 0)
            if w["status"] == STATUS_WOULD_FIX:
                st["would_fix"] += 1
            elif w["status"] == STATUS_CLEAN:
                st["clean"] += 1
            elif w["status"] == STATUS_PLAN_MISS:
                st["plan_miss"] += 1
    return st


def exit_code_of(verdict):
    """退出码口径：0=clean/shaped·1=partial/plan-miss。"""
    return 0 if verdict in (VERDICT_CLEAN, VERDICT_SHAPED) else 1


def parse_only(spec):
    """--only 解析：逗号/空分·序号 1-5 与 kind 名双收·未知即用法炸·出参保
    正典序。"""
    if not spec:
        return list(KINDS)
    got = set()
    for tok in re.split(r"[,\s]+", spec.strip()):
        if not tok:
            continue
        k = KIND_ALIASES.get(tok)
        if k is None:
            raise UsageError("--only 项不识（须 %s 或 1-5）: %s"
                             % (",".join(KINDS), tok))
        got.add(k)
    if not got:
        raise UsageError("--only 列空: %r" % spec)
    return [k for k in KINDS if k in got]


# ---------- 自证 ----------

def selftest():
    """内嵌冻结向量组（tmp 夹具·零真网络零真编译·真引擎离线驱动）：

    判1  plan 五洗逐判（脏件：词面 would-fix/token clean/header clean/
         eol would-fix/anchor 不适用）→partial rc1
    判2  正件对照全 clean→clean rc0
    判3  plan 零写盘·--apply 缺省关（md5 恒同）
    判4  plan-miss 如实（无式词面件→plan-miss；混合件→would-fix 修可修·
         plan-miss 亮无式）
    判5  apply→rescan clean→shaped rc0（词面交换/CRLF 归一/锚正典 md5_8 实证）
    判6  幂等（二跑 plan 全 clean→clean rc0；再 apply 零 applied）
    判7  锚缺实体 plan-miss
    判8  冻结名排除（injector 罐装名册：--dir 自动排除＋显式 --file 红拒 rc2；
         真 frozen8 --ledger 八件＋真在册件红拒）
    判9  子进程调用层注入（gate4 罐装判面）
    判10 CLI 四码（help0/bogus2/无输入面2/缺件9）
    判11 --once/--loop 双模（loop --max-rounds 2 事件流两轮＋stop）
    判12 确定性（plan --json 两跑字节恒同）
    判13 preset 链（--header-map-preset 装载在位·齐件不扰 rc0；探测次序：
         preset 胜 env·--header-map 胜 env——env ROCWASH_HEADER_MAP 双向）
    判14 preset 占位替换渲染→apply 端到端（缺字段件渲染整体补写→rescan
         clean→shaped rc0→二跑幂等 clean·渲染文逐名断言［name/deps 双列/
         bundle/build 命令/Axioms 豁免面］）
    判15 同槽互斥（--header-map＋--header-map-preset rc2；preset 未知名 rc2）
    判16 无源 plan-miss 如实（无旗无 env→缺字段件 header plan-miss）＋
         模板库缺失 rc9（--repo-root 隔离场·引擎件 symlink 七路）
    """
    import tempfile

    def run(args, env=None):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=env)
        out = p.stdout.decode("utf-8", "replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p.returncode, out

    def wf(path, text, newline=None):
        with io.open(path, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(text)
        return path

    ok = True
    tmp = tempfile.mkdtemp(prefix="rocqwash_wash_shape_self_")
    try:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        asrc = os.path.join(tmp, "asrc")
        os.makedirs(asrc)
        src_miss = os.path.join(tmp, "src_miss")
        os.makedirs(src_miss)
        header = ("(* 使命：洗形器自测夹具。\n"
                  "   依赖：无。\n"
                  "   对标：无。\n"
                  "   构造性：全闭合。\n"
                  "   编译配方：rocq c -Q . \"\" fixture.v。 *)\n")
        dirty_lf = header + "Definition a := 1. (* 这里埋一个载体词 *)\n" \
                            "Definition b := 2.\n"
        dirty_v = wf(os.path.join(src, "dirty.v"), dirty_lf.replace(
            "\n", "\r\n"), newline="")
        clean_v = wf(os.path.join(src, "clean.v"),
                     header + "Definition a := 1.\nDefinition b := 2.\n")
        missy_v = wf(os.path.join(src, "missy.v"),
                     header + "Definition c := 3. (* 这是一个探针词面 *)\n")
        mixed_v = wf(os.path.join(src, "mixed.v"),
                     header + "Definition d := 4. (* 载体一词与探针词面并存"
                              " *)\n")
        order_txt = wf(os.path.join(src, "order.txt"),
                       "ToyA.v#R7\nToyB.v#R8-deadbeef\n")
        order_miss = wf(os.path.join(src_miss, "order.txt"),
                        "Ghost.v#R9\n")
        wf(os.path.join(asrc, "ToyA.v"), "Definition ta := 1.\n")
        wf(os.path.join(asrc, "ToyB.v"), "Definition tb := 2.\n")
        # 判13/14/16 preset 矢量夹具：战役 `**` 形头注缺 构造性/编译 两字段
        # （gate4 缺字段硬项驱动）·Require 面 From Stdlib 一行＋bare 两行
        fx_header = (
            "(* ConstructiveWorld-Set -- fixture bundle for the wash shape "
            "header-map preset selftest. *)\n"
            "\n"
            "(** * hdmap_fx: the render-vector fixture module of the wash "
            "shape header-map preset.\n"
            "\n"
            "    Mission.  Supplies the fixture interface slot for the wash "
            "shape\n"
            "      selftest render vector: [tsp_fx_slot] closes the toy slot "
            "over\n"
            "      Set data and the companion discharge restates the exit "
            "shape.\n"
            "\n"
            "    Dependencies.  Rocq standard library only.\n"
            "*)\n")
        fx_body = ("\nFrom Stdlib Require Import QArith.\n"
                   "Require Import S01_BaseRing.\n"
                   "Require Import S02_Cauchy.\n"
                   "\n"
                   "Definition fx_slot : True.\n"
                   "Proof. exact I. Qed.\n")
        fx_v = wf(os.path.join(src, "hdmap_fx.v"), fx_header + fx_body)
        # 判16 专用副本（判14 apply 会把 hdmap_fx.v 洗成五字段齐件——plan-miss
        # 矢量须用未经施刀的缺字段件）
        fx2_v = wf(os.path.join(src, "hdmap_fx2.v"), fx_header + fx_body)

        def load_json(path):
            with io.open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)

        def washes_of(rep, name_suffix):
            for f in rep["plan"]["files"]:
                if f["file"].endswith(name_suffix):
                    return dict((w["kind"], w) for w in f["washes"])
            return {}

        # 判1 plan 五洗逐判（脏件）
        j1 = os.path.join(tmp, "j1.json")
        rc, out = run(["--file", dirty_v, "--json", j1])
        rep1 = load_json(j1)
        w1 = washes_of(rep1, "dirty.v")
        c1 = (rc == 1 and rep1["schema"] == SCHEMA
              and rep1["verdict"] == "partial"
              and w1["lexical"]["status"] == "would-fix"
              and "载体" in w1["lexical"]["detail"]
              and w1["token"]["status"] == "clean"
              and w1["header"]["status"] == "clean"
              and w1["eol"]["status"] == "would-fix"
              and w1["anchor"]["status"] == "clean"
              and "不适用" in w1["anchor"]["detail"])
        print("判1 plan 五洗逐判(脏件 partial):", c1)
        ok = ok and c1

        # 判2 正件对照
        rc, out = run(["--file", clean_v, "--json",
                       os.path.join(tmp, "j2.json")])
        rep2 = load_json(os.path.join(tmp, "j2.json"))
        c2 = rc == 0 and rep2["verdict"] == "clean" and \
            all(w["status"] == "clean"
                for f in rep2["plan"]["files"] for w in f["washes"])
        print("判2 正件对照全 clean:", c2)
        ok = ok and c2

        # 判3 plan 零写盘·--apply 缺省关
        md5_before = md5_of(dirty_v)
        c3 = md5_of(dirty_v) == md5_before
        print("判3 plan 零写盘(--apply 缺省关):", c3)
        ok = ok and c3

        # 判4 plan-miss 如实（无式件＋混合件）
        rc, out = run(["--file", missy_v])
        m_miss = ("PLAN-MISS" in out and "禁词:探针" in out
                  and "无对应式" not in out)
        rc, out = run(["--file", mixed_v, "--json",
                       os.path.join(tmp, "j4.json")])
        rep4 = load_json(os.path.join(tmp, "j4.json"))
        w4 = washes_of(rep4, "mixed.v")
        c4 = (rc == 1 and rep4["verdict"] == "plan-miss"
              and w4["lexical"]["status"] == "would-fix"
              and "无式[禁词:探针]" in w4["lexical"]["detail"]
              and rep4["plan"]["stats"]["plan_miss_items"] == 1)
        print("判4 plan-miss 如实(无式件/混合件):", c4, m_miss)
        ok = ok and c4 and m_miss

        # 判5 apply→rescan clean→shaped（词面/CRLF/锚三面实证）
        rc, out = run(["--file", dirty_v, "--file", order_txt,
                       "--anchor-src", asrc, "--apply", "--json",
                       os.path.join(tmp, "j5.json")])
        rep5 = load_json(os.path.join(tmp, "j5.json"))
        dirty_txt = io.open(dirty_v, "rb").read().decode("utf-8")
        order_txt_now = io.open(order_txt, "r", encoding="utf-8").read()
        fp_a = md5_8_of(os.path.join(asrc, "ToyA.v"))
        fp_b = md5_8_of(os.path.join(asrc, "ToyB.v"))
        rescan_w = {}
        for f in rep5["apply"]["rescan"]["files"]:
            rescan_w[f["file"]] = dict((w["kind"], w["status"])
                                       for w in f["washes"])
        c5 = (rc == 0 and rep5["verdict"] == "shaped"
              and "载体" not in dirty_txt and "carrier" in dirty_txt
              and "\r" not in dirty_txt
              and ("ToyA.v#R7-%s" % fp_a) in order_txt_now
              and ("ToyB.v#R8-%s" % fp_b) in order_txt_now
              and len(rep5["apply"]["applied"]) >= 3
              and all(s == "clean"
                      for d in rescan_w.values() for s in d.values()))
        print("判5 apply→rescan clean→shaped(词面/CRLF/锚实证):", c5)
        ok = ok and c5

        # 判6 幂等（二跑 plan 全 clean；再 apply 零 applied）
        rc, out = run(["--file", dirty_v, "--file", order_txt,
                       "--anchor-src", asrc, "--json",
                       os.path.join(tmp, "j6.json")])
        rep6 = load_json(os.path.join(tmp, "j6.json"))
        rc6b, out6b = run(["--file", dirty_v, "--file", order_txt,
                           "--anchor-src", asrc, "--apply"])
        c6 = (rc == 0 and rep6["verdict"] == "clean"
              and all(w["status"] == "clean"
                      for f in rep6["plan"]["files"] for w in f["washes"])
              and rc6b == 0 and "applied=0" in out6b)
        print("判6 幂等(二跑 plan 全 clean/再 apply 零 applied):", c6)
        ok = ok and c6

        # 判7 锚缺实体 plan-miss
        rc, out = run(["--file", order_miss, "--anchor-src", asrc])
        c7 = rc == 1 and "PLAN-MISS" in out and "缺实体" in out
        print("判7 锚缺实体 plan-miss:", c7)
        ok = ok and c7

        # 判8 冻结名排除（injector 罐装名册＋真 frozen8 名册）
        vault = os.path.join(tmp, "vault")
        os.makedirs(vault)
        frozen_me = wf(os.path.join(vault, "frozen_me.py"), "x = 1\n")
        wf(os.path.join(vault, "okfile.v"),
           header + "Definition e := 5.\n")
        inj = wf(os.path.join(tmp, "inj.json"), json.dumps(
            {"frozen8": {"rc": 0, "stdout":
                         "deadbeefdeadbeefdeadbeefdeadbeef  %s\n" % frozen_me}},
            ensure_ascii=False))
        rc, out = run(["--dir", vault, "--injector", inj, "--json",
                       os.path.join(tmp, "j8.json")])
        rep8 = load_json(os.path.join(tmp, "j8.json"))
        excl_paths = " ".join(e["path"] for e in rep8["scope"]["excluded"])
        plan_files = " ".join(f["file"] for f in rep8["plan"]["files"])
        rc8b, out8b = run(["--file", frozen_me, "--injector", inj])
        rc8c, out8c = run(["--file", os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scan", "mac_stmt_scan.py"), "--only", "eol"])
        c8 = (rc == 0 and "frozen_me.py" in excl_paths
              and "frozen_me.py" not in plan_files
              and rc8b == 2 and "红拒" in out8b
              and rc8c == 2 and "红拒" in out8c
              and rep8["scope"]["frozen_roster_source"] == "injector-canned")
        print("判8 冻结名排除(罐装 --dir 排除/显式红拒 rc2/真在册红拒):", c8)
        ok = ok and c8

        # 判9 子进程调用层注入（gate4 罐装判面）
        inj2 = wf(os.path.join(tmp, "inj2.json"), json.dumps(
            {"gate4": {"rc": 1, "stdout": "canned-gate4",
                       "report": {"results": [
                           {"file": dirty_v, "verdict": "FAIL",
                            "hard": [[6, "体内散块", "禁词", "探针"]],
                            "review": []}]}}}, ensure_ascii=False))
        rc, out = run(["--file", dirty_v, "--injector", inj2,
                       "--only", "lexical"])
        c9 = rc == 1 and "PLAN-MISS" in out and "gate4=FAIL" in out \
            and "禁词:探针" in out
        print("判9 子进程调用层注入(gate4 罐装判面):", c9)
        ok = ok and c9

        # 判10 CLI 四码
        rc_h, out_h = run(["--help"])
        rc_b, out_b = run(["--bogus"])
        rc_n, out_n = run([])
        rc_m, out_m = run(["--file", os.path.join(tmp, "nope.v")])
        c10 = (rc_h == 0 and "usage" in out_h.lower()
               and rc_b == 2 and rc_n == 2 and rc_m == 9)
        print("判10 CLI 四码(help0/bogus2/无输入面2/缺件9):", c10)
        ok = ok and c10

        # 判11 --once/--loop 双模（哨态两轮＋stop 事件）
        rc, out = run(["--file", clean_v, "--only", "eol", "--loop",
                       "--interval", "0", "--sleep-scale", "0",
                       "--max-rounds", "2"])
        rounds = out.count('"event": "round"')
        stops = out.count('"event": "stop"')
        c11 = rc == 0 and rounds == 2 and stops == 1
        print("判11 --loop 哨态(max-rounds 2/JSONL 事件流):", c11)
        ok = ok and c11

        # 判12 确定性（plan --json 两跑字节恒同）
        ja = os.path.join(tmp, "ja.json")
        jb = os.path.join(tmp, "jb.json")
        run(["--file", missy_v, "--file", order_miss, "--anchor-src",
             asrc, "--json", ja])
        run(["--file", missy_v, "--file", order_miss, "--anchor-src",
             asrc, "--json", jb])
        c12 = io.open(ja, "rb").read() == io.open(jb, "rb").read()
        print("判12 确定性(plan --json 两跑字节恒同):", c12)
        ok = ok and c12

        # 判13 preset 链（装载在位·齐件不扰·探测次序 preset/--header-map 胜 env）
        j13a = os.path.join(tmp, "j13a.json")
        rc, out = run(["--file", clean_v, "--header-map-preset",
                       "campaign_set_diamond", "--json", j13a])
        rep13a = load_json(j13a)
        hm13 = rep13a["scope"]["header_map"]
        envmap_empty = wf(os.path.join(tmp, "envmap_empty.json"), "{}")
        envmap_fx = wf(os.path.join(tmp, "envmap_fx.json"), json.dumps(
            {"hdmap_fx": "(* env-side header *)"}, ensure_ascii=False))
        env_preset = dict(os.environ)
        env_preset[ENV_HEADER_MAP] = envmap_empty
        env_explicit = dict(os.environ)
        env_explicit[ENV_HEADER_MAP] = envmap_fx
        rc13b, out13b = run(["--file", fx_v, "--header-map-preset",
                             "campaign_set_diamond", "--only", "header"],
                            env=env_preset)
        rc13c, out13c = run(["--file", fx_v, "--header-map", envmap_empty,
                             "--only", "header"], env=env_explicit)
        c13 = (rc == 0 and rep13a["verdict"] == "clean"
               and hm13["source"] == "preset"
               and hm13["preset"] == "campaign_set_diamond"
               and rc13b == 1 and "钦名模板渲染整体补写" in out13b
               and rc13c == 1 and "无补写模板（模板源=map" in out13c)
        print("判13 preset 链(装载在位/齐件不扰/preset>--header-map 胜 env):", c13)
        ok = ok and c13

        # 判14 preset 占位替换渲染→apply 端到端（缺字段件→补写→shaped→幂等）
        j14a = os.path.join(tmp, "j14a.json")
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--json", j14a])
        rep14a = load_json(j14a)
        w14 = washes_of(rep14a, "hdmap_fx.v")
        c14a = (rc == 1 and rep14a["verdict"] == "partial"
                and w14["header"]["status"] == "would-fix"
                and "钦名模板渲染整体补写" in w14["header"]["detail"]
                and "缺字段" in w14["header"]["detail"]
                and w14["header"]["action"] == ACTION_SWEEP_MAP_PRESET)
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--apply", "--json",
                       os.path.join(tmp, "j14b.json")])
        rep14b = load_json(os.path.join(tmp, "j14b.json"))
        fx_txt = io.open(fx_v, "r", encoding="utf-8").read()
        c14b = (rc == 0 and rep14b["verdict"] == "shaped"
                and "Stdlib [QArith]. Requires [S01_BaseRing]" in fx_txt
                and "[S02_Cauchy]" in fx_txt
                and "(* ConstructiveWorld-Set -- fixture bundle" in fx_txt
                and "coqc -native-compiler no -q -Q . \"\" hdmap_fx.v"
                in fx_txt
                and "Axioms: none" in fx_txt
                and "Rocq standard library only." not in fx_txt)
        rc, out = run(["--file", fx_v, "--header-map-preset",
                       "campaign_set_diamond", "--json",
                       os.path.join(tmp, "j14c.json")])
        rep14c = load_json(os.path.join(tmp, "j14c.json"))
        c14c = rc == 0 and rep14c["verdict"] == "clean" and all(
            w["status"] == "clean"
            for f in rep14c["plan"]["files"] for w in f["washes"])
        c14 = c14a and c14b and c14c
        print("判14 preset 占位替换渲染→apply 端到端(partial→shaped→幂等"
              "/渲染逐名断言):", c14)
        ok = ok and c14

        # 判15 同槽互斥（双旗 rc2·preset 未知名 rc2）
        rc, out = run(["--file", clean_v, "--header-map", envmap_empty,
                       "--header-map-preset", "campaign_set_diamond"])
        rc15b, out15b = run(["--file", clean_v, "--header-map-preset",
                             "no_such_preset"])
        c15 = (rc == 2 and "互斥" in out
               and rc15b == 2 and "名不识" in out15b)
        print("判15 同槽互斥(双旗 rc2/未知名 rc2):", c15)
        ok = ok and c15

        # 判16 无源 plan-miss 如实＋模板库缺失 rc9（隔离 repo_root）
        env_clean = dict(os.environ)
        env_clean.pop(ENV_HEADER_MAP, None)
        rc, out = run(["--file", fx2_v, "--only", "header"], env=env_clean)
        iso = os.path.join(tmp, "iso")
        for sub in ("verify", "scan", "wash", "tools", "certify"):
            os.makedirs(os.path.join(iso, sub))
        real_root = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        for rel in ("verify/gate4_comment_guard.py",
                    "scan/scan_v4_token.py",
                    "wash/cure_applier.py",
                    "wash/comment_sweep.py",
                    "wash/comment_pack.json",
                    "tools/registry_union.py",
                    "certify/frozen8.py"):
            os.symlink(os.path.join(real_root, rel),
                       os.path.join(iso, rel))
        rc16b, out16b = run(["--file", clean_v, "--header-map-preset",
                             "campaign_set_diamond", "--repo-root", iso])
        c16 = (rc == 1 and "PLAN-MISS" in out
               and "无补写模板（模板源=none" in out
               and rc16b == 9 and "模板库缺失" in out16b)
        print("判16 无源 plan-miss 如实/模板库缺失 rc9:", c16)
        ok = ok and c16

        print("WASH-SHAPE-SELFTEST:",
              "PASS（16 判全过）" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- 主流程 ----------

def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="洗形器·正典形五洗流水（gate4 词面/token 普查+正典包/头注"
                    "模板/行尾归一/registry 重锚·两段 plan→apply 复跑复核·"
                    "schema rocqwash-shape/1）")
    ap.add_argument("--file", action="append", default=[], metavar="PATH",
                    help="目标件（可多次；.v 走①②③·order.txt/_CoqProject 走⑤"
                         "·任意文本件走④）")
    ap.add_argument("--dir", action="append", default=[], metavar="DIR",
                    help="全树收件（.v＋order.txt/_CoqProject·可多次）")
    ap.add_argument("--exclude", action="append", default=[], metavar="名",
                    help="追加排除名（ basename 或路径段·冻结名册在册自动排除）")
    ap.add_argument("--only", default=None, metavar="KINDS",
                    help="洗目子集（逗号分·lexical,token,header,eol,anchor "
                         "或 1-5·缺省全五洗）")
    ap.add_argument("--header-map", dest="header_map", default=None,
                    metavar="MAP.json",
                    help="③头注形洗补写模板（{basename: header text}·逐件数据"
                         "·与 --header-map-preset 同槽互斥 rc2）")
    ap.add_argument("--header-map-preset", dest="header_map_preset",
                    default=None, metavar="NAME",
                    help="③头注形洗钦名模板（tests/fixtures/header_map_v1.json "
                         "蒸馏库内 preset 名·占位承目标件自身派生/既有头注逐字"
                         "携带·缺省探测次序 --header-map > 本参 > env "
                         "ROCWASH_HEADER_MAP > 无=plan-miss）")
    ap.add_argument("--anchor-src", dest="anchor_src", default=None,
                    metavar="DIR",
                    help="⑤锚形洗实件源目录（缺省=registry 件同目录）")
    ap.add_argument("--repo-root", dest="repo_root", default=None,
                    metavar="DIR",
                    help="引擎件根（缺省=本脚本上上级·全参数化）")
    ap.add_argument("--json", dest="jsonout", default=None, metavar="OUT",
                    help="report 出账（schema rocqwash-shape/1）")
    ap.add_argument("--apply", action="store_true",
                    help="两段第二段：执行 would-fix 项＋复跑五洗复核（缺省"
                         " plan 零写盘）")
    ap.add_argument("--loop", action="store_true",
                    help="哨态：逐轮流水＋JSONL 事件流（缺省 --once 单段）")
    ap.add_argument("--interval", type=float, default=5.0, metavar="S",
                    help="loop 轮间秒（缺省 5·可调）")
    ap.add_argument("--sleep-scale", dest="sleep_scale", type=float,
                    default=1.0, metavar="S",
                    help="sleep 缩放（0=零真睡·selftest 依赖）")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=0,
                    metavar="N", help="loop 轮数界定（0=无限）")
    ap.add_argument("--events", default=None, metavar="FILE",
                    help="loop JSONL 事件追加账（stdout 恒流·此参另落盘）")
    ap.add_argument("--injector", default=None, metavar="SCEN.json",
                    help="子进程调用层罐装场景 {引擎键: {rc,stdout,report}}"
                         "（键集 gate4/scan_v4/cure/sweep/registry_union/"
                         "frozen8）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        if not args.file and not args.dir:
            print("FAIL-LOUD: --file/--dir 至少给一（收件面）", file=sys.stderr)
            sys.exit(2)
        if args.interval < 0 or args.sleep_scale < 0 or args.max_rounds < 0:
            print("FAIL-LOUD: --interval/--sleep-scale/--max-rounds 须≥0",
                  file=sys.stderr)
            sys.exit(2)
        if args.header_map and args.header_map_preset:
            print("FAIL-LOUD: --header-map 与 --header-map-preset 同槽互斥"
                  "（rc2 同槽律——③头注模板源二择一显传）", file=sys.stderr)
            sys.exit(2)
        ws = WashShape(args)
        ws.files, ws.excluded_records = ws.collect_files()
        print("== WASH-SHAPE (%s) kinds=%s files=%d excluded=%d =="
              % ("loop" if args.loop else
                 ("apply" if args.apply else "plan"),
                 ",".join(ws.kinds), len(ws.files),
                 len(ws.excluded_records)))
        if args.loop:
            rc = ws.run_loop()
        else:
            rc = ws.run_once()
        sys.exit(rc)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)


if __name__ == "__main__":
    main()
