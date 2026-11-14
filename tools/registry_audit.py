#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_audit.py — 注册册卫生审计器：双册只读出账＋确定性处方（rocqwash tools/·
v35 登记候卫生波判例代码化·20261111 入账）

v35 判例（登记候卫生波·任务书背景）：Set 仓 order.txt/_CoqProject 双册既有 12 模块
重复行（#40 直并遗留——键同锚异的世系行，registry_union.py:8「坑判例」同源）＋6 锚
文本重复（R0-d66910/R97-b44a002/3/R0-18dbeac/R97-b43a001/2——跨批携锚撞文本）＋顺序
号形锚（b48a 系——git 史可勘：e3dc1b8 时代该行缺锚，b3ae0ad 铸 b48a001-014 七位签；
本仓现存 LW2TrigBridge.v#R152-TBR880 与 u5c_inst_e.v#R43a003 两行在 registry_union
ANCHOR_RE 口径下皆读作无指纹顺序号形）。本器把该波逐项人工勘验代码化：四账只读出账
——病灶是数据非器红（ci_triage.py「红是数据非器红·恒 exit 0 响亮出账」同律）。

键式与锚正典零重造（编排零新引擎）：直接 import tools/registry_union.py 同款函数——
  键式 key_of（registry_union.py:152）：
    order       行首到首 #（注释/代签止）——键含 .v（如 Local/LW0.v）；
    coqproject  末个 / 后去 .v 扩展名——键为裸名（如 Arch/ToyR_01.v→ToyR_01）。
  锚读形 anchor_of/ANCHOR_RE（registry_union.py:81/170）：行内首 #R<序>[-<hex>]；
  锚正典＝#R<序>-<md5 前 8 hex 小写>（registry_union --reanchor 产出形·wash_shape ⑤
  锚形洗同源）。非正典逐类如实录：
    顺序号形  读形无指纹（#R97；#R43a003 读作 #R43、#R152-TBR880 读作 #R152 同归此）；
    形怪      指纹槽在而非 8 位小写 hex（b48a 系七位签、六位历史铸签 d66910 系、
              大写 hex、超长）；
    缺锚      键行无 #R 可读 token。

四账（审计项）：
  ① 重复行账   同键多行逐键列行号组（order/coqproject 各审·键式如上；order 侧
               锚异注记＝键同锚异世系形，#40 直并遗留判例）。
  ② 锚账       order 册专审（coqproject 行无锚——wash_shape ⑤ 同律）：锚撞文本
               （不同键同锚文本·registry_union A3 dup_pairs 读形同款口径）/顺序号
               形/形怪/缺锚 逐类。
  ③ 孤儿账     order 有键而 coqproject 无对应（.v 基名口径：order 键剥 .v 取末段
               路径分量）或反之。order 侧非 .v 键行与 coqproject 旗标/注释行
               （-Q . "" 等非 .v 结尾行）滤除不参匹配（registry_union「两侧恒同
               即滤」同律）——滤除数入 stats 不入病灶。
  ④ 拓扑引用账 可选 --live-src DIR：order 键行（relpath 形·无 .v 尾者补 .v，
               registry_union resolve_entity 同律）对目录 .v 实件（os.walk 全索引
               ·posix 相对路径）双向对账——缺件（表有盘无）/多件（盘有表无），
               relpath 全等口径（select_audit world_index 同款索引法）。

输入两形（互斥）：
  双册文件形  --order PATH --project PATH（须成对·缺一即用法错）；
  git 直读形  --git REPO --ref X（subprocess git -C REPO show REF:PATH——
              registry_union git_show 同款；--git-path-order/--git-path-project
              可覆写，缺省 order.txt/_CoqProject）。
  可选：--live-src DIR（④账）/ --anchor-src DIR（处方 md5 源·wash_shape ⑤ 同律）。

输出：--json schema rocqwash-registry-audit/1（sort_keys 确定性·sections{duplicates,
anchors,orphans,live?}——live 未开时为 null（缺席旁证如实记·push_gate NOT-RUN 同款
诚实律）·每病灶恰 {key,lines[],kind,evidence} 四键·summary 计数含 by_kind）＋ --md
出人读台账（markdown·与 JSON 同序）。--fix-plan 只出确定性处方（零写盘——**--apply
不存在**·处方留 v39 执行器）：
  dedup 保首    DEDUP book=<册> key='<键>' keep=L<首> drop=L<余,…>（keep=min 行号）；
  锚刷          直用既有引擎（编排零新引擎）：python3 tools/registry_union.py
                --main/--base/--branch 同册（或 --git REPO --ref-* 三同 ref）
                --kind order --reanchor <裸名> --anchor-src <SRC> --out <OUT> --apply
                ——md5 对 --anchor-src 落地实件重算（registry_union md5_8_of 同款）；
                给了 --anchor-src 且实件唯一命中即嵌实值（期望锚 #R<序>-<md5_8>），
                未给/缺件/歧义嵌 <MD5_8> 占位（wash_shape ⑤ plan-miss 同律·不硬造）；
  孤儿补行模板  ORPHAN-ADD book=<册> key='<基名>' template='<补行>'——order 方向模板
                <proj原行>#R<SEQ>-<md5_8|占位>（序号须注册决定·非机械可造）；
  非机械可解    正典形锚撞（8 位 md5 同签＝同内容或误植——重锚重算不改值）如实列
                人工分判。
锚刷靶面＝顺序号形/形怪诸键（处方 lines＝该键全表行——registry_union apply_reanchor
重写该键全表行同口径·正典形撞不列靶）。处方命令文法（DEDUP/ORPHAN-ADD）为
v39 执行器契约·本文法即定义。

只读纪律（本器铁律）：审计面（--order/--project/--git/--live-src/--anchor-src 指认
的双册与目录树）零写零触；--apply 形参不存在（喂了即 argparse 用法错 exit 2）；写
面恰为显式 --json/--md 出账路径（调用方指认）。行号口径＝剥终止符行序 1 基（尾空行
不计·registry_union read_side 同款）。

退出码：0=出账（病灶是数据·count>0 仍 0·响亮 stdout）；1=--selftest 炸；
2=用法错（形参咬合/无输入面/半册）；9=输入缺（册件/git show/live-src/anchor-src
缺）。

用法：
  python3 tools/registry_audit.py --order ORDER.txt --project _CoqProject \
      [--live-src DIR] [--anchor-src DIR] [--json out.json] [--md out.md] [--fix-plan]
  python3 tools/registry_audit.py --git REPO --ref REF [--git-path-order PATH] \
      [--git-path-project PATH] [同上可选参]
  python3 tools/registry_audit.py --selftest

确定性：无时间戳无环境噪声·同输入重跑 --json/--md/stdout 字节级恒同（selftest 断
言）；纯 stdlib 零第三方零网络零编译。
--selftest 矢量（tmp 合成·v35 真账形态样张·零触真仓零网络）：重复行/锚撞/顺序号形/
形怪/缺锚/孤儿/旗标滤除/live 缺件多件 各判＋处方行正确性（dedup 保首·锚刷命令含正
确 md5——"module A content alpha\\n"→77c2b9a8 registry_union 冻结向量）＋只读实证
（双册与 live 树前后 md5 恒同·--apply 不存在）＋--git 直读（本地 tmp clone·坏 ref
9）＋CLI 四码＋确定性重跑恒同。
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

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  （键式/锚正典正本·只 import 不改）
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 同侪 tools/registry_union.py 不可导入（键式/锚正典零重造"
          "依赖）: %s" % _e, file=sys.stderr)
    sys.exit(9)

PROG = "registry_audit"
SCHEMA = "rocqwash-registry-audit/1"

KIND_ORDER = _ru.KIND_ORDER          # "order"
KIND_COQPROJECT = _ru.KIND_COQPROJECT  # "coqproject"

# 锚正典：#R<序>-<md5 前 8 hex 小写>（registry_union --reanchor 产出形·wash_shape ⑤ 同源）
CANONICAL_ANCHOR_RE = re.compile(r"^#R\d+-[0-9a-f]{8}$")
# 顺序号读形（无指纹槽）：ANCHOR_RE 读出 #R<序> 且无 '-'
MD5_PLACEHOLDER = "<MD5_8>"          # 处方 md5 占位（未给/缺件/歧义·wash_shape plan-miss 同律）
SEQ_PLACEHOLDER = "<SEQ>"            # 孤儿补行模板序号占位（注册决定·非机械可造）
GIT_PATH_ORDER_DEFAULT = "order.txt"
GIT_PATH_PROJECT_DEFAULT = "_CoqProject"

# 病灶 kind 谱（每病灶恰 {key,lines,kind,evidence} 四键·kind 编码册别与病类）
K_DUP_ORDER = "dup-order"
K_DUP_PROJECT = "dup-coqproject"
K_ANCHOR_COLLISION = "anchor-collision"
K_ANCHOR_SEQ = "anchor-seq-form"
K_ANCHOR_MALFORMED = "anchor-malformed"
K_ANCHOR_MISSING = "anchor-missing"
K_ORPHAN_ORDER_ONLY = "orphan-order-only"
K_ORPHAN_PROJECT_ONLY = "orphan-project-only"
K_LIVE_MISSING = "live-missing"
K_LIVE_EXTRA = "live-extra"

EVIDENCE_LINE_CAP = 120  # evidence 内原行截断幅（确定性截断）


class UsageError(Exception):
    """用法错（exit 2）。"""


class MissingInput(Exception):
    """输入缺失（exit 9）。"""


# ---------- 读面 ----------

def read_book_file(path, what):
    """册文件 → 行列表（registry_union read_side 同款口径：剥终止符与首尾空白·
    尾空行不计）。缺件 fail-loud 9。"""
    try:
        lines, _eol, _final = _ru.read_side(path, what)
    except _ru.MissingInput as e:
        raise MissingInput(str(e))
    return lines


def read_book_git(repo, ref, path, what):
    """git show 直读册（registry_union git_show/read_side_text 同款）。"""
    try:
        text = _ru.git_show(repo, ref, path)
    except _ru.MissingInput as e:
        raise MissingInput(str(e))
    return _ru.read_side_text(text, what)


def clip(s, cap=EVIDENCE_LINE_CAP):
    """evidence 原行确定性截断。"""
    return s if len(s) <= cap else s[:cap] + "…"


# ---------- ① 重复行账 ----------

def audit_duplicates(lines, kind):
    """同键多行逐键列行号组。返回 findings（kind=dup-order|dup-coqproject）。"""
    groups = {}
    for i, ln in enumerate(lines, 1):
        k = _ru.key_of(ln, kind)
        if k is not None:
            groups.setdefault(k, []).append(i)
    findings = []
    for k in sorted(groups):
        nos = groups[k]
        if len(nos) < 2:
            continue
        if kind == KIND_ORDER:
            anchors = sorted({_ru.anchor_of(lines[n - 1]) or "" for n in nos})
            if len(anchors) > 1:
                ev = ("同键 %d 行 L%s·锚异（键同锚异世系形·#40 直并遗留判例）: %s"
                      % (len(nos), ",".join(str(x) for x in nos),
                         " | ".join(clip(lines[n - 1]) for n in nos)))
            else:
                ev = ("同键 %d 行 L%s·锚同（逐字重复行）: %s"
                      % (len(nos), ",".join(str(x) for x in nos),
                         clip(lines[nos[0] - 1])))
            findings.append({"key": k, "lines": nos, "kind": K_DUP_ORDER,
                             "evidence": ev})
        else:
            findings.append({
                "key": k, "lines": nos, "kind": K_DUP_PROJECT,
                "evidence": "同键 %d 行 L%s: %s"
                            % (len(nos), ",".join(str(x) for x in nos),
                               clip(lines[nos[0] - 1]))})
    return findings


# ---------- ② 锚账 ----------

def classify_anchor(line):
    """order 行 → (锚读形 token|None, 形类)。

    形类：'canonical'（#R<序>-<8 位小写 hex>）/ 'seq-form'（读形无指纹·顺序号形）/
    'malformed'（指纹槽非 8 位小写 hex·形怪）/ None（无 #R 可读·缺锚）。
    """
    tok = _ru.anchor_of(line)
    if tok is None:
        return None, None
    if CANONICAL_ANCHOR_RE.match(tok):
        return tok, "canonical"
    if "-" not in tok:
        return tok, "seq-form"
    return tok, "malformed"


def audit_anchors(order_lines):
    """order 册锚账：锚撞文本/顺序号形/形怪/缺锚 逐类。"""
    keyed = []  # (line_no, key, raw, tok, form)
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue  # 注释/空行不入锚账（registry_union 键 None 同律）
        tok, form = classify_anchor(ln)
        keyed.append((i, k, ln, tok, form))

    findings = []
    # 锚撞文本：读形 token → 出现键集（>1 键即撞——registry_union A3 读形同款口径）
    by_tok = {}
    for i, k, ln, tok, form in keyed:
        if tok is not None:
            by_tok.setdefault(tok, []).append((i, k, form))
    for tok in sorted(by_tok):
        rows = by_tok[tok]
        keys = sorted({k for _i, k, _f in rows})
        if len(keys) > 1:
            forms = sorted({f for _i, _k, f in rows})
            findings.append({
                "key": tok,
                "lines": sorted(i for i, _k, _f in rows),
                "kind": K_ANCHOR_COLLISION,
                "evidence": "锚文本 %s 被 %d 键共享（%s·形类 %s）——跨批携锚撞"
                            "（v35 判例 R0-d66910 系）"
                            % (tok, len(keys), ",".join(keys), "/".join(forms))})
    # 形类逐键（非正典三类）
    for cls, kind_id, why in (
            ("seq-form", K_ANCHOR_SEQ,
             "锚 %s 读形无指纹（顺序号形·registry_union ANCHOR_RE 口径）"),
            ("malformed", K_ANCHOR_MALFORMED, None),  # evidence 逐例构造
            (None, K_ANCHOR_MISSING,
             "键行无锚（无 #R 可读 token）")):
        per_key = {}
        for i, k, ln, tok, form in keyed:
            if form == cls:
                per_key.setdefault(k, []).append(i)
        for k in sorted(per_key):
            nos = per_key[k]
            raw = clip(order_lines[nos[0] - 1])
            if cls == "malformed":
                tok0 = _ru.anchor_of(order_lines[nos[0] - 1])
                fp = tok0.split("-", 1)[1]
                ev = ("锚 %s 指纹 %r 非 md5-8 正典形（%d 位·须 #R<序>-<8 位小写"
                      " hex>·b48a 系/六位历史铸签同此）: %s"
                      % (tok0, fp, len(fp), raw))
            else:
                ev = (why % (_ru.anchor_of(order_lines[nos[0] - 1]),)
                      if cls == "seq-form" else why) + ": " + raw
            findings.append({"key": k, "lines": nos, "kind": kind_id,
                             "evidence": ev})
    return findings


# ---------- ③ 孤儿账 ----------

def order_base_name(key):
    """order 键 → .v 基名（剥 .v 后取末段路径分量——Local/LW0.v→LW0）。"""
    bare = _ru.bare_name(key)
    return bare.rsplit("/", 1)[-1]


def audit_orphans(order_lines, project_lines):
    """order↔coqproject 双册孤儿（.v 基名口径·旗标/注释行滤除）。

    返回 (findings, stats_extra)——stats_extra 携滤除计数。
    """
    order_base = {}   # 基名 → [行号]
    order_keyed = 0
    order_nonv = 0
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue
        order_keyed += 1
        if not k.endswith(".v"):
            order_nonv += 1  # 非 .v 键行不参基名匹配（口径注记）
            continue
        order_base.setdefault(order_base_name(k), []).append(i)
    proj_keys = {}    # 基名 → [行号]
    proj_module = 0
    flag_filtered = 0
    proj_raw = {}     # 基名 → 原行首例（补行模板用）
    for i, ln in enumerate(project_lines, 1):
        if not ln.endswith(".v"):
            flag_filtered += 1  # 旗标/注释行（-Q . "" 等）滤除不参匹配
            continue
        k = _ru.key_of(ln, KIND_COQPROJECT)
        proj_module += 1
        proj_keys.setdefault(k, []).append(i)
        proj_raw.setdefault(k, ln)
    findings = []
    for base in sorted(set(order_base) - set(proj_keys)):
        findings.append({
            "key": base, "lines": order_base[base],
            "kind": K_ORPHAN_ORDER_ONLY,
            "evidence": "order 有 .v 基名 %r（键形 %s）而 coqproject 模块面无对应"
                        "（基名口径·旗标滤除 %d 行）"
                        % (base, clip(order_lines[order_base[base][0] - 1]),
                           flag_filtered)})
    for base in sorted(set(proj_keys) - set(order_base)):
        findings.append({
            "key": base, "lines": proj_keys[base],
            "kind": K_ORPHAN_PROJECT_ONLY,
            "evidence": "coqproject 有模块 %r（%s）而 order 册无对应"
                        % (base, clip(proj_raw[base]))})
    stats_extra = {"order_keyed": order_keyed, "order_keyed_nonv": order_nonv,
                   "project_module_rows": proj_module,
                   "flag_filtered": flag_filtered}
    return findings, stats_extra


# ---------- ④ 拓扑引用账 ----------

def audit_live(order_lines, live_src):
    """order 键行 vs --live-src .v 实件双向对账（relpath 全等口径）。"""
    if not os.path.isdir(live_src):
        raise MissingInput("--live-src 目录缺失: %s" % live_src)
    disk = set()
    for dirpath, _dirs, fnames in os.walk(live_src):
        rel_dir = os.path.relpath(dirpath, live_src)
        for fn in fnames:
            if fn.endswith(".v"):
                rel = fn if rel_dir == "." else os.path.join(rel_dir, fn)
                disk.add(rel.replace(os.sep, "/"))
    table = {}  # order 表内 relpath → [行号]
    for i, ln in enumerate(order_lines, 1):
        k = _ru.key_of(ln, KIND_ORDER)
        if k is None:
            continue
        rel = k if k.endswith(".v") else k + ".v"
        table.setdefault(rel, []).append(i)
    findings = []
    for rel in sorted(set(table) - disk):
        findings.append({
            "key": rel, "lines": table[rel], "kind": K_LIVE_MISSING,
            "evidence": "order 表有而 live-src 下缺 .v 实件: %s"
                        % os.path.join(live_src, rel)})
    for rel in sorted(disk - set(table)):
        findings.append({
            "key": rel, "lines": [], "kind": K_LIVE_EXTRA,
            "evidence": "live-src 盘有 .v 实件而 order 表无此键: %s" % rel})
    return findings


# ---------- 处方（--fix-plan·零写盘·v39 执行器契约） ----------

def shq(s):
    """处方路径值 shell 引用（确定性：含空白/引号/空即单引号转义·否则裸值）。"""
    if s and re.fullmatch(r"[A-Za-z0-9_./@+=,:^-]+", s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def shq_always(s):
    """处方数据值（key/template）恒单引号引用（统一文法·转义确定性）。"""
    return "'" + s.replace("'", "'\\''") + "'"


def resolve_md5_8(bare, anchor_src):
    """--anchor-src 实件 md5-8 解析（registry_union resolve_entity/md5_8_of 直用）。

    未给源/缺件/歧义 → (MD5_PLACEHOLDER, 注记)（wash_shape ⑤ plan-miss 同律·不硬
    造·审计不因处方 md5 不可解而炸）。
    """
    if not anchor_src:
        return MD5_PLACEHOLDER, "未给 --anchor-src"
    try:
        entity = _ru.resolve_entity(bare, anchor_src)
    except _ru.UsageError as e:
        return MD5_PLACEHOLDER, "实体歧义（%s）" % str(e).strip()
    if entity is None:
        return MD5_PLACEHOLDER, "anchor-src 下缺同名 .v 实件"
    return _ru.md5_8_of(entity), "实件 %s" % entity


def build_fix_plan(order_lines, project_lines, sections, args):
    """确定性处方（dedup 保首/锚刷/孤儿补行模板/非机械可解·零写盘）。"""
    plan = {"dedup": [], "reanchor": [], "orphan": [], "unresolvable": []}

    # dedup 保首（keep=min 行号·drop=余行升序）
    for f in sections["duplicates"]:
        book = "order" if f["kind"] == K_DUP_ORDER else "coqproject"
        nos = sorted(f["lines"])
        keep, drop = nos[0], nos[1:]
        cmd = ("DEDUP book=%s key=%s keep=L%d drop=%s"
               % (book, shq_always(f["key"]), keep,
                  ",".join("L%d" % n for n in drop)))
        plan["dedup"].append({"book": book, "key": f["key"],
                              "keep_line": keep, "drop_lines": drop,
                              "command": cmd})

    # 锚刷靶面：顺序号形/形怪诸键（正典形撞不列靶——重算不改值）。
    # 处方 lines＝该键全表行（registry_union apply_reanchor 重写该键全表行口径——
    # 同键良行亦随重算·expected_anchor 取首 affected 行）。
    reanchor_src = args.anchor_src
    for f in sections["anchors"]:
        if f["kind"] not in (K_ANCHOR_SEQ, K_ANCHOR_MALFORMED):
            continue
        k = f["key"]
        bare = _ru.bare_name(k)
        affected = sorted(f["lines"])
        nos = sorted(i for i, ln in enumerate(order_lines, 1)
                     if _ru.key_of(ln, KIND_ORDER) == k)
        raw = order_lines[affected[0] - 1]
        tok = _ru.anchor_of(raw)
        seq = tok[2:].split("-", 1)[0] if tok else ""
        md5_8, how = resolve_md5_8(bare, reanchor_src)
        if md5_8 == MD5_PLACEHOLDER:
            expected = "#R%s-%s" % (seq, MD5_PLACEHOLDER)
        else:
            expected = "#R%s-%s" % (seq, md5_8)
        src_part = reanchor_src if reanchor_src else "<ANCHOR_SRC>"
        if args.git is not None:
            head = ("python3 tools/registry_union.py --git %s --ref-base %s "
                    "--ref-main %s --ref-branch %s --kind order"
                    % (shq(args.git), shq(args.ref), shq(args.ref), shq(args.ref)))
        else:
            head = ("python3 tools/registry_union.py --main %s --base %s "
                    "--branch %s --kind order"
                    % (shq(args.order), shq(args.order), shq(args.order)))
        cmd = ("%s --reanchor %s --anchor-src %s --out <OUT> --apply"
               % (head, shq(bare), shq(src_part)))
        plan["reanchor"].append({
            "key": k, "bare": bare, "lines": nos, "seq": seq,
            "old_anchor": tok, "md5_8": md5_8, "expected_anchor": expected,
            "md5_source": how, "command": cmd})

    # 孤儿补行模板
    for f in sections["orphans"]:
        if f["kind"] == K_ORPHAN_ORDER_ONLY:
            base = f["key"]
            # order 键原形（补 _CoqProject 行＝键自身路径形）
            raw = order_lines[sorted(f["lines"])[0] - 1]
            template = raw.split("#", 1)[0].strip()
            cmd = ("ORPHAN-ADD book=coqproject key=%s template=%s"
                   % (shq_always(base), shq_always(template)))
            plan["orphan"].append({"direction": "order-only", "key": base,
                                   "template": template, "command": cmd})
        else:
            base = f["key"]
            raw = project_lines[sorted(f["lines"])[0] - 1]
            md5_8, _how = resolve_md5_8(base, args.anchor_src)
            template = "%s#R%s-%s" % (raw, SEQ_PLACEHOLDER, md5_8)
            cmd = ("ORPHAN-ADD book=order key=%s template=%s"
                   % (shq_always(base), shq_always(template)))
            plan["orphan"].append({"direction": "project-only", "key": base,
                                   "template": template, "command": cmd})

    # 非机械可解：正典形锚撞（同 md5 同签或误植·重锚不改值·人工分判）
    for f in sections["anchors"]:
        if f["kind"] != K_ANCHOR_COLLISION:
            continue
        tok = f["key"]
        if CANONICAL_ANCHOR_RE.match(tok):
            plan["unresolvable"].append({
                "reason": "canonical-anchor-collision", "anchor": tok,
                "lines": f["lines"], "evidence": f["evidence"],
                "note": "正典形锚撞＝同内容 md5 同签或同签误植——--reanchor 重算"
                        "不改值·非机械可解·须人工分判（wash_shape plan-miss 同律）"})
    return plan


# ---------- 出账 ----------

def sort_findings(findings):
    """病灶确定性序：(kind, key)。lines 已升序。"""
    return sorted(findings, key=lambda f: (f["kind"], f["key"]))


def build_payload(mode, inputs, stats, sections, fix_plan, want_fix):
    """report（schema rocqwash-registry-audit/1·sort_keys 确定性）。"""
    by_kind = {}
    total = 0
    for sec in ("duplicates", "anchors", "orphans", "live"):
        for f in sections.get(sec) or []:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
            total += 1
    payload = {
        "schema": SCHEMA,
        "mode": mode,
        "inputs": inputs,
        "live_src": sections.get("_live_src"),
        "anchor_src": sections.get("_anchor_src"),
        "stats": stats,
        "sections": {
            "duplicates": sections["duplicates"],
            "anchors": sections["anchors"],
            "orphans": sections["orphans"],
            "live": sections["live"],  # 未开＝null（缺席如实记）
        },
        "summary": {
            "duplicates": len(sections["duplicates"]),
            "anchors": len(sections["anchors"]),
            "orphans": len(sections["orphans"]),
            "live": len(sections["live"] or []),
            "total": total,
            "by_kind": {k: by_kind[k] for k in sorted(by_kind)},
        },
    }
    if want_fix:
        payload["fix_plan"] = fix_plan
    return payload


def dump_json(path, obj):
    """确定性 JSON 落盘（sort_keys＋indent=1·registry_union dump_json 同款）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def render_md(payload):
    """人读台账 markdown（与 JSON 同序·确定性）。"""
    secs = payload["sections"]
    summ = payload["summary"]
    out = ["# 注册册卫生台账（%s）" % SCHEMA, ""]
    out.append("- mode: %s" % payload["mode"])
    for k in sorted(payload["inputs"]):
        out.append("- %s: %s" % (k, payload["inputs"][k]))
    out.append("- live_src: %s" % (payload["live_src"] or "（未开）"))
    out.append("- anchor_src: %s" % (payload["anchor_src"] or "（未给）"))
    st = payload["stats"]
    out.append("- 行数: order 全行 %d·键行 %d（非 .v 键行 %d）｜coqproject 全行 %d"
               "·模块行 %d（旗标/注释滤除 %d）"
               % (st["order_rows"], st["order_keyed"], st["order_keyed_nonv"],
                  st["project_rows"], st["project_module_rows"],
                  st["flag_filtered"]))
    out.append("")
    titles = {
        "duplicates": "① 重复行账",
        "anchors": "② 锚账（order 册·coqproject 行无锚不适用）",
        "orphans": "③ 孤儿账（.v 基名口径·旗标滤除）",
        "live": "④ 拓扑引用账",
    }
    for sec in ("duplicates", "anchors", "orphans", "live"):
        rows = secs[sec]
        if rows is None:
            out.append("## %s（未开——--live-src 未给）" % titles[sec])
            out.append("")
            continue
        out.append("## %s（%d 病灶）" % (titles[sec], len(rows)))
        out.append("")
        if not rows:
            out.append("（零病灶·账面洁净）")
            out.append("")
            continue
        out.append("| # | kind | key | lines | evidence |")
        out.append("|---|------|-----|-------|----------|")
        for n, f in enumerate(rows, 1):
            ev = f["evidence"].replace("|", "\\|").replace("\n", " ")
            out.append("| %d | %s | %s | %s | %s |"
                       % (n, f["kind"], f["key"].replace("|", "\\|"),
                          ",".join(str(x) for x in f["lines"]) or "—", ev))
        out.append("")
    if "fix_plan" in payload:
        fp = payload["fix_plan"]
        out.append("## 处方（--fix-plan·零写盘·--apply 不存在·v39 执行器专用）")
        out.append("")
        out.append("### dedup 保首")
        out.append("")
        if fp["dedup"]:
            for d in fp["dedup"]:
                out.append("- `%s`" % d["command"])
        else:
            out.append("（无）")
        out.append("")
        out.append("### 锚刷（registry_union --reanchor·md5 对 --anchor-src 实件）")
        out.append("")
        if fp["reanchor"]:
            for r in fp["reanchor"]:
                out.append("- `%s`（期望 `%s`←`%s`；md5_8=%s·%s）"
                           % (r["command"], r["expected_anchor"],
                              r["old_anchor"], r["md5_8"], r["md5_source"]))
        else:
            out.append("（无锚刷靶面）")
        out.append("")
        out.append("### 孤儿补行模板")
        out.append("")
        if fp["orphan"]:
            for o in fp["orphan"]:
                out.append("- `%s`（%s）" % (o["command"], o["direction"]))
        else:
            out.append("（无）")
        out.append("")
        out.append("### 非机械可解（人工分判）")
        out.append("")
        if fp["unresolvable"]:
            for u in fp["unresolvable"]:
                out.append("- 锚 `%s`（L%s）：%s"
                           % (u["anchor"], ",".join(str(x) for x in u["lines"]),
                              u["note"]))
        else:
            out.append("（无）")
        out.append("")
    out.append("---")
    out.append("总病灶 %d（duplicates=%d anchors=%d orphans=%d live=%d）——"
               "病灶是数据·审计器 exit 0（ci_triage 同律）"
               % (summ["total"], summ["duplicates"], summ["anchors"],
                  summ["orphans"], summ["live"]))
    out.append("")
    return "\n".join(out)


def print_stdout(payload):
    """响亮 stdout 出账（病灶是数据·rc 恒 0）。"""
    secs = payload["sections"]
    summ = payload["summary"]
    print("=== REGISTRY-AUDIT (%s·%s) ===" % (payload["mode"], SCHEMA))
    for k in sorted(payload["inputs"]):
        print("  %s=%s" % (k, payload["inputs"][k]))
    st = payload["stats"]
    print("rows: order=%d(keyed=%d nonv=%d) coqproject=%d(module=%d "
          "flag_filtered=%d)"
          % (st["order_rows"], st["order_keyed"], st["order_keyed_nonv"],
             st["project_rows"], st["project_module_rows"],
             st["flag_filtered"]))
    for sec, label in (("duplicates", "① 重复行账"), ("anchors", "② 锚账"),
                       ("orphans", "③ 孤儿账"), ("live", "④ 拓扑引用账")):
        rows = secs[sec]
        if rows is None:
            print("--- %s: 未开（--live-src 未给） ---" % label)
            continue
        print("--- %s: %d 病灶 ---" % (label, len(rows)))
        for f in rows:
            print("  [%s] key=%s lines=%s" % (f["kind"], f["key"],
                                              ",".join(str(x) for x in f["lines"]) or "-"))
            print("      %s" % f["evidence"])
    if "fix_plan" in payload:
        fp = payload["fix_plan"]
        print("--- 处方（--fix-plan·零写盘·v39 执行器） ---")
        for d in fp["dedup"]:
            print("  %s" % d["command"])
        for r in fp["reanchor"]:
            print("  %s  # 期望 %s←%s（md5_8=%s·%s）"
                  % (r["command"], r["expected_anchor"], r["old_anchor"],
                     r["md5_8"], r["md5_source"]))
        for o in fp["orphan"]:
            print("  %s" % o["command"])
        for u in fp["unresolvable"]:
            print("  UNRESOLVED 锚 %s: %s" % (u["anchor"], u["note"]))
    print("REGISTRY-AUDIT: total=%d 病灶（duplicates=%d anchors=%d orphans=%d "
          "live=%d）——病灶是数据·exit 0"
          % (summ["total"], summ["duplicates"], summ["anchors"],
             summ["orphans"], summ["live"]))


# ---------- 主流程 ----------

def run_audit(args):
    """审计主流程（读面→四账→payload）。raises UsageError/MissingInput。"""
    if args.live_src is not None and not os.path.isdir(args.live_src):
        raise MissingInput("--live-src 目录缺失: %s" % args.live_src)
    if args.anchor_src is not None and not os.path.isdir(args.anchor_src):
        raise MissingInput("--anchor-src 目录缺失: %s" % args.anchor_src)

    if args.git is not None:
        git_po = args.git_path_order or GIT_PATH_ORDER_DEFAULT
        git_pp = args.git_path_project or GIT_PATH_PROJECT_DEFAULT
        inputs = {"git": args.git, "ref": args.ref,
                  "git_path_order": git_po, "git_path_project": git_pp}
        order_lines = read_book_git(args.git, args.ref, git_po, "order(ref)")
        project_lines = read_book_git(args.git, args.ref, git_pp,
                                      "project(ref)")
        mode = "git"
    else:
        inputs = {"order": args.order, "project": args.project}
        order_lines = read_book_file(args.order, "--order")
        project_lines = read_book_file(args.project, "--project")
        mode = "files"

    sections = {
        "duplicates": sort_findings(audit_duplicates(order_lines, KIND_ORDER)
                                    + audit_duplicates(project_lines,
                                                       KIND_COQPROJECT)),
        "anchors": sort_findings(audit_anchors(order_lines)),
    }
    orphan_findings, stats_extra = audit_orphans(order_lines, project_lines)
    sections["orphans"] = sort_findings(orphan_findings)
    if args.live_src is not None:
        sections["live"] = sort_findings(audit_live(order_lines, args.live_src))
        sections["_live_src"] = args.live_src
    else:
        sections["live"] = None
        sections["_live_src"] = None
    sections["_anchor_src"] = args.anchor_src

    stats = {"order_rows": len(order_lines),
             "project_rows": len(project_lines)}
    stats.update(stats_extra)

    fix_plan = None
    if args.fix_plan:
        fix_plan = build_fix_plan(order_lines, project_lines, sections, args)
    payload = build_payload(mode, inputs, stats, sections, fix_plan,
                            args.fix_plan)
    return payload


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="注册册卫生审计器：order.txt/_CoqProject 双册只读四账出账"
                    "＋确定性处方（--apply 不存在·零改盘·v35 判例代码化）")
    ap.add_argument("--order", default=None, metavar="PATH",
                    help="order.txt 册（与 --project 成对）")
    ap.add_argument("--project", default=None, metavar="PATH",
                    help="_CoqProject 册（与 --order 成对）")
    ap.add_argument("--git", default=None, metavar="REPO",
                    help="改直读：仓路径（--ref 必配·与双册文件形互斥）")
    ap.add_argument("--ref", default=None, metavar="REF",
                    help="git 直读 ref（审计该时点双册快照）")
    ap.add_argument("--git-path-order", default=None, metavar="PATH",
                    help="仓内 order.txt 路径（缺省 order.txt）")
    ap.add_argument("--git-path-project", default=None, metavar="PATH",
                    help="仓内 _CoqProject 路径（缺省 _CoqProject）")
    ap.add_argument("--live-src", default=None, metavar="DIR",
                    help="④拓扑引用账实件目录（可选·os.walk 收 .v 对账）")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="处方 md5 源目录（可选·os.walk 取同名 .v 重算）")
    ap.add_argument("--fix-plan", action="store_true",
                    help="附确定性处方（零写盘·--apply 不存在·留 v39 执行器）")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="出账 JSON（schema rocqwash-registry-audit/1）")
    ap.add_argument("--md", default=None, metavar="FILE",
                    help="出账人读台账 markdown")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # ---- 形参咬合（fail-loud 用法面） ----
    def die_usage(msg):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(2)

    file_mode = args.order is not None or args.project is not None
    git_mode = args.git is not None
    if file_mode and git_mode:
        die_usage("--order/--project 双册形与 --git 直读形互斥，两形混给")
    if not file_mode and not git_mode:
        die_usage("无输入面：--order＋--project 双册 或 --git＋--ref 直读"
                  "（--selftest 除外）")
    if file_mode and (args.order is None or args.project is None):
        die_usage("--order 与 --project 须成对（双册口径·缺一不可）")
    if git_mode and args.ref is None:
        die_usage("--git 直读须 --ref（审计该时点双册快照）")
    if not git_mode and (args.git_path_order or args.git_path_project):
        die_usage("--git-path-order/--git-path-project 仅 --git 直读形有效")
    if args.ref is not None and not git_mode:
        die_usage("--ref 仅 --git 直读形有效")

    # ---- 审计（读面缺件→9·其余 fail-loud） ----
    try:
        payload = run_audit(args)
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except _ru.UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    # ---- 出账（写面恰为显式 --json/--md 出账路径） ----
    print_stdout(payload)
    if args.json:
        dump_json(args.json, payload)
        print("json -> %s" % args.json)
    if args.md:
        with io.open(args.md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(payload))
        print("md -> %s" % args.md)
    sys.exit(0)


# ---------- 自证 ----------

def selftest():
    """内嵌矢量组（tmp 合成·v35 真账形态样张·零触真仓零网络零编译）：

    1  四账判类全谱（重复行/锚撞/顺序号形/形怪/缺锚/孤儿/旗标滤除/live 缺件多件）
    2  处方行正确性（dedup 保首·锚刷命令含正确 md5——77c2b9a8 冻结向量·占位形）
    3  只读实证（双册与 live 树前后 md5 恒同·--apply 不存在 rc 2）
    4  --git 直读（本地 tmp clone·与文件形同账·坏 ref 9）
    5  CLI 四码＋确定性（help0/bogus2/无输入2/半册2/缺件9/重跑 json md 字节恒同）
    """
    import tempfile

    def run(argv):
        p = subprocess.run(
            [sys.executable, "-B",
             os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          PROG + ".py")] + argv,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wf(path, text):
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    def md5_of(path):
        h = hashlib.md5()
        with io.open(path, "rb") as fh:
            h.update(fh.read())
        return h.hexdigest()

    tmp = tempfile.mkdtemp(prefix="rocqwash_ra_self_")
    try:
        # ---- 真账形态样张（v35 判例形态：键同锚异世系行/跨批撞锚/顺序号形/七位签） ----
        order_text = ("\n".join([
            "A.v#R0-d66910",          # L1 形怪（6 位历史铸签）·撞锚·与 L8 键同锚异
            "B.v#R0-d66910",          # L2 撞锚（异键同锚文本）
            "C.v#R97",                # L3 顺序号形（无指纹·registry_union 判例原形）
            "D.v#R43a003",            # L4 顺序号形（读形 #R43）
            "E.v#R97-b48a001",        # L5 形怪（七位签·b48a 系判例形）
            "F.v",                    # L6 缺锚
            "G.v#R0-11111111",        # L7 正典（8 位小写 hex）
            "A.v#R40-22222222",       # L8 键同锚异世系行（#40 直并遗留形·锚恰正典形）
            "# 注释行",               # L9 注释（键 None 不入账）
        ]) + "\n")
        project_text = ("\n".join([
            "-Q . \"\"",              # L1 旗标行（滤除不参匹配）
            "A.v",                    # L2
            "A.v",                    # L3 同键重复
            "C.v",                    # L4
            "E.v",                    # L5
            "H.v",                    # L6 孤儿（project-only）
        ]) + "\n")
        d1 = os.path.join(tmp, "case")
        os.makedirs(d1)
        order_f = wf(os.path.join(d1, "order.txt"), order_text)
        project_f = wf(os.path.join(d1, "_CoqProject"), project_text)
        live = os.path.join(d1, "live")
        os.makedirs(live)
        for name, content in (("A.v", "module A.\n"), ("C.v", "module C.\n"),
                              ("E.v", "module E.\n"), ("H.v", "module H.\n")):
            wf(os.path.join(live, name), content)
        world = os.path.join(d1, "world")
        os.makedirs(world)
        # registry_union 冻结 md5 向量："module A content alpha\n" → 77c2b9a8
        wf(os.path.join(world, "A.v"), "module A content alpha\n")
        assert _ru.md5_8_of(os.path.join(world, "A.v")) == "77c2b9a8"

        j1 = os.path.join(d1, "r.json")
        m1 = os.path.join(d1, "r.md")
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--anchor-src", world,
                 "--json", j1, "--md", m1, "--fix-plan"])
        assert p.returncode == 0, "出账应 rc=0（病灶是数据）实测 %d\n%s" % (
            p.returncode, p.stdout)
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]
        secs = rep["sections"]
        summ = rep["summary"]

        # ① 重复行账：order A [1,8]（锚异注记）＋coqproject A [2,3]
        dups = {(f["kind"], f["key"]): f for f in secs["duplicates"]}
        assert (K_DUP_ORDER, "A.v") in dups and dups[(K_DUP_ORDER, "A.v")]["lines"] == [1, 8], secs["duplicates"]
        assert "锚异" in dups[(K_DUP_ORDER, "A.v")]["evidence"], dups[(K_DUP_ORDER, "A.v")]
        assert (K_DUP_PROJECT, "A") in dups and dups[(K_DUP_PROJECT, "A")]["lines"] == [2, 3], secs["duplicates"]

        # ② 锚账：撞锚/顺序号形/形怪/缺锚 各判·正典 G 不列
        an = {(f["kind"], f["key"]): f for f in secs["anchors"]}
        assert (K_ANCHOR_COLLISION, "#R0-d66910") in an, secs["anchors"]
        assert sorted(an[(K_ANCHOR_COLLISION, "#R0-d66910")]["lines"]) == [1, 2], an
        assert (K_ANCHOR_SEQ, "C.v") in an and an[(K_ANCHOR_SEQ, "C.v")]["lines"] == [3], an
        assert (K_ANCHOR_SEQ, "D.v") in an and "#R43" in an[(K_ANCHOR_SEQ, "D.v")]["evidence"], an
        assert (K_ANCHOR_MALFORMED, "A.v") in an and an[(K_ANCHOR_MALFORMED, "A.v")]["lines"] == [1], an
        assert (K_ANCHOR_MALFORMED, "B.v") in an and an[(K_ANCHOR_MALFORMED, "B.v")]["lines"] == [2], an
        assert (K_ANCHOR_MALFORMED, "E.v") in an and "7 位" in an[(K_ANCHOR_MALFORMED, "E.v")]["evidence"] \
            and "b48a001" in an[(K_ANCHOR_MALFORMED, "E.v")]["evidence"], an
        assert (K_ANCHOR_MISSING, "F.v") in an and an[(K_ANCHOR_MISSING, "F.v")]["lines"] == [6], an
        assert all("G.v" != f["key"] for f in secs["anchors"]), "正典锚不得列病灶"

        # ③ 孤儿账：order-only {B,D,F,G}·project-only {H}·旗标滤除 1
        orph = {(f["kind"], f["key"]): f for f in secs["orphans"]}
        assert {(k, ) for (kd, k) in orph if kd == K_ORPHAN_ORDER_ONLY} == {("B",), ("D",), ("F",), ("G",)}, secs["orphans"]
        assert [k for (kd, k) in orph if kd == K_ORPHAN_PROJECT_ONLY] == ["H"], secs["orphans"]
        assert rep["stats"]["flag_filtered"] == 1, rep["stats"]
        assert rep["stats"]["project_module_rows"] == 5, rep["stats"]

        # ④ live 账：缺件 {B,D,F,G}·多件 {H.v}
        lv = {(f["kind"], f["key"]): f for f in secs["live"]}
        assert {k for (kd, k) in lv if kd == K_LIVE_MISSING} == {"B.v", "D.v", "F.v", "G.v"}, secs["live"]
        assert {k for (kd, k) in lv if kd == K_LIVE_EXTRA} == {"H.v"}, secs["live"]
        assert summ["total"] == 19, summ
        # 精确盘点：duplicates=2 anchors=7（撞1+怪3+序2+缺1）orphans=5 live=5
        assert summ["duplicates"] == 2 and summ["anchors"] == 7 \
            and summ["orphans"] == 5 and summ["live"] == 5, summ

        # 处方行正确性
        fp = rep["fix_plan"]
        dd = {(d["book"], d["key"]): d for d in fp["dedup"]}
        assert dd[("order", "A.v")]["command"] == \
            "DEDUP book=order key='A.v' keep=L1 drop=L8", fp["dedup"]
        assert dd[("coqproject", "A")]["command"] == \
            "DEDUP book=coqproject key='A' keep=L2 drop=L3", fp["dedup"]
        ra = {r["key"]: r for r in fp["reanchor"]}
        assert set(ra) == {"A.v", "B.v", "C.v", "D.v", "E.v"}, fp["reanchor"]
        # 锚刷命令含正确 md5（77c2b9a8 冻结向量·A 有实件）＋期望锚形
        assert ra["A.v"]["md5_8"] == "77c2b9a8", ra["A.v"]
        assert ra["A.v"]["expected_anchor"] == "#R0-77c2b9a8", ra["A.v"]
        assert "--reanchor A" in ra["A.v"]["command"] and "--apply" in ra["A.v"]["command"], ra["A.v"]
        # 锚刷处方 lines＝该键全表行（apply_reanchor 口径·良行 L8 亦随重算）
        assert ra["A.v"]["lines"] == [1, 8], ra["A.v"]
        # 未给/缺实件 → <MD5_8> 占位（不硬造）
        assert ra["C.v"]["md5_8"] == MD5_PLACEHOLDER \
            and ra["C.v"]["expected_anchor"] == "#R97-<MD5_8>", ra["C.v"]
        assert ra["D.v"]["seq"] == "43" and ra["E.v"]["seq"] == "97", fp["reanchor"]
        orz = {(o["direction"], o["key"]): o for o in fp["orphan"]}
        assert orz[("order-only", "B")]["template"] == "B.v", fp["orphan"]
        assert orz[("project-only", "H")]["template"] == "H.v#R<SEQ>-<MD5_8>", fp["orphan"]
        # 正典形撞不列锚刷靶；无正典撞 → unresolvable 空
        assert fp["unresolvable"] == [], fp["unresolvable"]
        b_json = io.open(j1, "rb").read()  # 确定性基线（②覆写前捕获）
        b_md = io.open(m1, "rb").read()
        print("  [1/5] 四账判类全谱 OK（重复/撞锚/顺序号/形怪/缺锚/孤儿/旗标滤/"
              "live 缺件多件·total=19）＋处方 dedup 保首/锚刷 77c2b9a8/占位")

        # ---- ② 只读实证：双册与 live 树前后 md5 恒同 ----
        before = ([md5_of(order_f), md5_of(project_f)]
                  + [md5_of(os.path.join(live, n)) for n in sorted(os.listdir(live))])
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--json", j1, "--md", m1])
        assert p.returncode == 0, p.stdout
        after = ([md5_of(order_f), md5_of(project_f)]
                 + [md5_of(os.path.join(live, n)) for n in sorted(os.listdir(live))])
        assert before == after, "只读违例：册/树字节漂移"
        assert "fix_plan" not in json.load(io.open(j1, encoding="utf-8")), \
            "无 --fix-plan 不得附处方"
        p = run(["--order", order_f, "--project", project_f, "--apply"])
        assert p.returncode == 2, "--apply 不存在（应 argparse rc=2）实测 %d" % p.returncode
        print("  [2/5] 只读实证 OK（双册+live 树 md5 恒同·无 --fix-plan 无处方·"
              "--apply 不存在 rc2）")

        # ---- ③ 确定性：同输入重跑 json/md 字节恒同（基线取自①） ----
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", live, "--anchor-src", world,
                 "--json", j1, "--md", m1, "--fix-plan"])
        assert p.returncode == 0, p.stdout
        assert io.open(j1, "rb").read() == b_json, "json 字节漂移＝违例"
        assert io.open(m1, "rb").read() == b_md, "md 字节漂移＝违例"
        print("  [3/5] 确定性 OK（json/md 重跑逐字节恒同）")

        # ---- ④ --git 直读（本地 tmp clone·与文件形同账·坏 ref 9） ----
        if shutil.which("git") is None:
            print("  [4/5] git 直读 SKIP（git 不在卷·让席不充红）")
        else:
            d4 = os.path.join(tmp, "repo")
            os.makedirs(d4)
            env = dict(os.environ)
            env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t",
                        "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
                        "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"})

            def g(*a):
                p4 = subprocess.run(["git", "-C", d4] + list(a), env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
                assert p4.returncode == 0, p4.stdout
                return p4.stdout.decode("utf-8", errors="replace").strip()

            g("init")
            branch = g("symbolic-ref", "--short", "HEAD")
            wf(os.path.join(d4, "order.txt"), order_text)
            wf(os.path.join(d4, "_CoqProject"), project_text)
            g("add", "order.txt", "_CoqProject")
            g("commit", "-m", "registry snapshot")
            j4 = os.path.join(tmp, "r4.json")
            p = run(["--git", d4, "--ref", branch, "--json", j4, "--fix-plan"])
            assert p.returncode == 0, p.stdout
            rep4 = json.load(io.open(j4, encoding="utf-8"))
            assert rep4["mode"] == "git", rep4["mode"]
            assert rep4["summary"]["duplicates"] == 2 \
                and rep4["summary"]["anchors"] == 7 \
                and rep4["summary"]["orphans"] == 5 \
                and rep4["summary"]["live"] == 0 \
                and rep4["summary"]["total"] == 14, rep4["summary"]
            assert any(f["kind"] == K_DUP_ORDER and f["key"] == "A.v"
                       for f in rep4["sections"]["duplicates"]), rep4
            # git 形锚刷处方走 registry_union --git 面（shq 形匹配——路径含
            # 空格/反斜杠时 shq 引用包裹·POSIX tmp 裸形与原字面恒同）
            assert any(("--git %s" % shq(d4)) in r["command"]
                       for r in rep4["fix_plan"]["reanchor"]), rep4["fix_plan"]
            p = run(["--git", d4, "--ref", "no-such-ref", "--json", j4])
            assert p.returncode == 9, "坏 ref 应 rc=9 实测 %d" % p.returncode
            print("  [4/5] git 直读 OK（tmp clone 同账·锚刷处方 --git 面·坏 ref 9）")

        # ---- ⑤ CLI 四码＋schema 面 ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "无输入应 rc=2 实测 %d" % p.returncode
        p = run(["--order", order_f])
        assert p.returncode == 2, "半册应 rc=2 实测 %d" % p.returncode
        p = run(["--order", order_f, "--project", project_f, "--ref", "x"])
        assert p.returncode == 2, "--ref 混入文件形应 rc=2 实测 %d" % p.returncode
        p = run(["--order", os.path.join(tmp, "nope.txt"),
                 "--project", project_f])
        assert p.returncode == 9, "缺册应 rc=9 实测 %d" % p.returncode
        p = run(["--order", order_f, "--project", project_f,
                 "--live-src", os.path.join(tmp, "nolive")])
        assert p.returncode == 9, "缺 live-src 应 rc=9 实测 %d" % p.returncode
        print("  [5/5] CLI 四码 OK（help0/bogus2/无输入2/半册2/混参2/缺册9/"
              "缺live-src9）")

        print("REGISTRY-AUDIT-SELFTEST PASS: 四账判类全谱/处方保首+md5向量+占位/"
              "只读实证/确定性/git直读/CLI四码 五判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
