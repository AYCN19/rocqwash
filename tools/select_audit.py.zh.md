#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""select_audit.py — 选件审计器：批选清单对树 order.txt 全表 grep 剔重（rocqwash tools/·
20261101 agent rqsupport·v6 判据轮打磨员 20261101 入账）

五课反馈轮打磨件②（nw6 课＋dver2-enbig7 课工具化）：
  - **nw6 课**：选件勘定员必须**实读树 order.txt 全表 grep 剔重·禁凭记忆**。
    判例源：`sandbox/seat_nw6/账/候批账-nw6批.md`（HansonLcm 混入实录在卷——同 agent 域
    他席在飞件 `work/HansonLcm.v`（15:33:04）与本席批作业同域并行，靠冻结时点全表
    实扫才勘明零互覆；凭记忆报批即有混入他席件之险）。本器把「全表实读」机械化：
    每个候选名都对 order.txt **逐行**归一化比对，不做任何记忆/缓存捷径。
  - **dver2-enbig7 课**：同件双席并行各带 born 闸必撞世界。判例源：
    `sandbox/seat_dver2/账/collision_enbig7_20261031.md`（enbig7 席越界写 seat_dver2
    域·两次 born 失败＝世界规格残缺仍 born 之工序缺陷·主会话仲裁 36c35816）。
    本器把「同件双认领」前兆机械化：同一模块名出现在 ≥2 份批选清单＝DUP-CROSS 撞名红。

v6 判据轮（打磨员·判例日期 20261030·账 v6 节载入）：
  - **nw10/abl6 空账判例**：主会话与两审计席同踩「Require 面审计把 Stdlib 件
    （QArith/Lia/List/Extraction/Lqa/Morphisms 等）误判为树内缺口」坑，且 grep
    单行解析漏 Require Export／多名行。侧证（本席只读实勘）：ConstructiveWorld repository
    `.zcode/workflow-drafts/nw10九件勘定审计席.dwf.ts:9` 与 `abl6六件审计验证席.dwf.ts:10`
    两席工单原文均为「①逐件 grep Require/From 面」＋「③闭包判定：Requires ⊆ 树
    197 ∪ 批内先序」——单行 grep 解析＋无白名单闭包式，即两坑源（空账回执本体不
    present in the tree·如实记）。本器固化正确工法三件套：
      ① Python 正则**语句级全 Require 形式解析**（From X Require Import/Export
        多名·多行·注释剥除）——parse_requires；
      ② **Stdlib 白名单豁免**（STDLIB_ROOTS 首段命中即豁免，不入树内缺口判定）；
      ③ **世界内 .v/.vo 文件存在性闭包**——audit_requires(file, world_dir)。
    用法：python3 tools/select_audit.py --requires <file.v> --world <world_dir>
    实盘补件（v6 轮当场现形·同族坑二连）：判据首版对本机 Live 世界 569 文件
    只读实扫即暴露两处解析面漏——①字符串字面量散文 Require（UpReqIndex.v:2821
    起 `"FA-D1S12 … zero Require on mother …"` 形）令 on/mother/of/six/face/
    delta 六散文词伪名入账→单趟扫描剥字符串；②裸形/短路径 Stdlib 件
    （Lists.List×92／PeanoNat／Permutation／QArith_base／Qring／Qfield／Qabs／
    ZArith_dec／ZArithRing／micromega.Lqa／Sorting.Sorted／String／Ascii／
    Wf_nat）首段不在册误报缺口→白名单补 16 根（逐件经本机工具链
    `Live/toolchain/opam/live/lib/coq/user-contrib/Stdlib/**` 实证在库）。

审计四判（全部 RED 才 exit 1·任一即红）：
  DUP-BATCH    同一批选清单内同名重复（凭记忆选件之典型误）
  DUP-CROSS   同一模块名出现在 ≥2 份批选清单（同域双席撞名前兆·enbig7 判例）
  NOT-IN-ORDER 候选名不在树 order.txt 全表（选了树里没有的件）
  DUP-ORDER    树 order.txt 自身同名多行（注册表重复·全表 grep 方能现形）
Requires 面判（--requires 形·v6）：REQ-GAP 非豁免 Require 在世界内无 .v/.vo 对应。

用法：
  python3 tools/select_audit.py --order <order.txt> --select <batch.txt>
                                [--select <batch2.txt> …] [--json out.json]
  python3 tools/select_audit.py --order <order.txt> --grep <名>   # 单名全表 grep
  python3 tools/select_audit.py --requires <file.v> --world <世界目录>  # v6 Require 面
  python3 tools/select_audit.py --selftest

名归一（order 行与批选行同律）：剥首尾空白→剥 #注释→剥 #代签（`名.v#R0-d66910`
与裸名与 `名.v` 三形同归一）→剥 .v 后缀。全词比对防前缀误咬（UpReqBanach ≠
UpReqBanachExp——born_world assert_md5 同律；requires 面同律：世界有
UpReqBanachExp.v 不判 UpReqBanach 闭）。

退出码：0=AUDIT-CLEAN（四判零发现）；1=AUDIT-RED（任一发现）；2=用法错；
        9=路径缺失（fail-loud 不模拟）。--grep 形：0=命中／1=未命中。
        --requires 形：0=REQUIRES-CLOSED（全闭）；1=REQ-GAP 缺口；2/9 同上。
写隔离：本件只读形参文件；唯一写盘面＝显式 --json 出账路径（requires 形无写盘）。
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "select_audit"


def normalize_line(line):
    """行→模块名：#注释/#代签剥离＋.v 后缀剥离＋空白剥离。空/注释行→None。

    名允许内嵌 `/` 路径形（实盘认证表 scripts/order.txt 671 行中有
    `Local/LW0LeibSeparation.v#R160-eb42d3` 一行·20261101 实测）——审计器必须能
    实读整表，禁因个别行形拒表。
    """
    s = line.strip()
    s = s.split("#", 1)[0].strip()  # 剥 #注释与 #代签（名.v#R0-d66910 → 名.v）
    if not s:
        return None
    if s.endswith(".v"):
        s = s[:-2]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*/?[A-Za-z0-9_'/]*", s):
        raise AuditError("非法模块名 %r（归一后须标识符或标识符/路径形）" % line.strip())
    return s


def read_names(path, what):
    """读清单文件 → (有序裸名列表, 行计数)。"""
    if not os.path.isfile(path):
        raise MissingPath("%s 文件缺失: %s" % (what, path))
    names = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            n = normalize_line(line)
            if n is not None:
                names.append(n)
    return names


class AuditError(Exception):
    pass


class MissingPath(Exception):
    pass


def audit(order_names, batches):
    """四判审计。order_names=全表有序裸名；batches=[(路径, 有序裸名列表)…]。
    返回 findings 列表（每项 dict(code/name/detail)）。"""
    findings = []
    # 判④ 树表自身同名多行（全表 grep 方能现形）
    seen_order = {}
    for n in order_names:
        seen_order[n] = seen_order.get(n, 0) + 1
    for n in sorted(seen_order):
        if seen_order[n] > 1:
            findings.append({"code": "DUP-ORDER", "name": n,
                             "detail": "order.txt 全表 %d 行同名（注册表重复）" % seen_order[n]})
    order_set = set(order_names)
    # 判① 批内重复（nw6 凭记忆负例）＋ 判② 跨批撞名（enbig7 判例）
    global_seen = {}  # name -> [batch_idx...]
    for bi, (bpath, names) in enumerate(batches, 1):
        seen = {}
        for n in names:
            seen[n] = seen.get(n, 0) + 1
        for n in sorted(seen):
            if seen[n] > 1:
                findings.append({"code": "DUP-BATCH", "name": n,
                                 "detail": "批 %d（%s）内 %d 次重复" % (bi, os.path.basename(bpath), seen[n])})
            global_seen.setdefault(n, []).append(bi)
    for n in sorted(global_seen):
        if len(global_seen[n]) > 1:
            findings.append({"code": "DUP-CROSS", "name": n,
                             "detail": "同件双认领：批 %s（同域双席撞名前兆·enbig7 判例）"
                                       % "、".join(str(b) for b in global_seen[n])})
    # 判③ 选了树里没有的件（全表实读·禁凭记忆）
    for n in sorted(set(k for _, names in batches for k in names)):
        if n not in order_set:
            findings.append({"code": "NOT-IN-ORDER", "name": n,
                             "detail": "不在树 order.txt 全表（实读全表 grep 未命中）"})
    return findings


def grep_rows(order_lines, name):
    """单名全表 grep（勘定员实读替身）——返回命中的原始行列表。全词比对。"""
    hits = []
    pat = re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\.v(\s|$|#)")
    for line in order_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pat.search(stripped):
            hits.append(stripped.rstrip("\n"))
    return hits


# ---------------------------------------------------------------------------
# v6 判据·Require 面审计（nw10/abl6 空账判例工具化·20261030 判例日期）
#
# 坑源（判例侧证·本席只读实勘 ConstructiveWorld repository）：
#   `.zcode/workflow-drafts/nw10九件勘定审计席.dwf.ts:9` ＋
#   `.zcode/workflow-drafts/abl6六件审计验证席.dwf.ts:10` 两席工单原文均为
#   「①逐件 grep Require/From 面」＋「③闭包判定：Requires ⊆ 树 197 ∪ 批内先序」
#   ——单行 grep 解析漏 Require Export／多名行，且无 Stdlib 白名单的闭包式把
#   QArith/Lia/List/Extraction/Lqa/Morphisms 等标准件全数误判为树内缺口
#   （空账回执本体不在盘·如实记；教训内容以上行工单为源转录）。
# 正确工法三件套（下三件即固化）：
#   ① parse_requires：语句级正则（Require…至终结点），天然收多名／多行／
#     From 前缀／Import·Export 动词；Coq 块注释先剥（注释内 Require 不入账）；
#     名区逐 token 扫描至终结点，越界即防停（畸形语句不产出垃圾名）。
#   ② STDLIB_ROOTS：Require 名**首段（root）**命中即豁免（QArith.QArith 首段
#     QArith·Lia 单段——与树内命名 S01_*／UpReq*／*Lcm 无碰撞面）。
#   ③ audit_requires：非豁免名对 world_dir 全索引（os.walk 收 .v/.vo 相对
#     路径）作「全等或 /路径结尾」存在性比对——兼容 -R 世界根前缀与 From
#     目录形；全词结尾比对防前缀误咬（世界有 UpReqBanachExp.v ≠ UpReqBanach 闭）。
# ---------------------------------------------------------------------------

# 工单点名六件打头，后接同族常用 Stdlib 逻辑根（首段豁免·可扩常量）。
# 实盘补件（v6 判据轮·工具链逐一验证）：Live 世界 569 文件 Require 面实扫发现
#   Lists.List×92／PeanoNat×21／Permutation×18／Qring×7／ZArith_dec×7／Qabs×6/
#   ZArithRing×5／micromega.Lqa×4／Sorting.Sorted×3／String×6／Ascii×2／Wf_nat×1
#   等裸形/短路径 Stdlib 件首段不在册——逐件经本机工具链
#   `Live/toolchain/opam/live/lib/coq/user-contrib/Stdlib/**` 实证在库后补根：
#   Lists/Strings/Sorting/String/Ascii/PeanoNat/Permutation/QArith_base/Qring/
#   Qfield/Qabs/ZArith_dec/ZArithRing/Wf_nat/micromega/setoid_ring。
STDLIB_ROOTS = frozenset((
    "QArith", "Lia", "List", "Extraction", "Lqa", "Morphisms",
    "Stdlib", "Coq", "Init", "Logic", "Program",
    "Arith", "ZArith", "NArith", "Nat", "Peano", "BinNums", "BinInt",
    "BinNat", "BinPos", "Decimal", "Hexadecimal", "Number", "Numbers",
    "Bool", "Setoid", "Setoids", "Decidable", "Orders", "Rings", "Fields",
    "Algebra", "Structures", "Relations", "Reals", "Rbase", "Rtrigo",
    "Nia", "Psatz", "Micromega",
    # v6 实盘补件（上表 Stdlib/** 实证在库·裸形与短路径首段）
    "Lists", "Strings", "Sorting", "String", "Ascii", "PeanoNat",
    "Permutation", "QArith_base", "Qring", "Qfield", "Qabs",
    "ZArith_dec", "ZArithRing", "Wf_nat", "micromega", "setoid_ring",
))

# 语句头：[From X] Require [Import|Export]（捕获 From 与动词·名区另行扫描）
_REQ_HEAD_RE = re.compile(
    r"(?:From\s+(?P<frm>[A-Za-z_][\w']*(?:\.[\w']*)*)\s+)?"
    r"Require(?P<verb>\s+(?:Import|Export))?(?![\w'])",
    re.S)
# 名 token：点路径形标识符
_REQ_NAME_RE = re.compile(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*")
# 名区越界防停词（裸 token 命中即停——点路径 token 不受影响·Local.LW0 形合法收名）
_VERNAC_STOP = frozenset((
    "Require", "From", "Import", "Export", "Definition", "Theorem",
    "Lemma", "Proof", "Qed", "Inductive", "CoInductive", "Fixpoint",
    "CoFixpoint", "Example", "Corollary", "Proposition", "Remark", "Fact",
    "Record", "Class", "Instance", "Module", "Section", "End", "Variable",
    "Variables", "Context", "Hypothesis", "Parameter", "Parameters",
    "Axiom", "Conjecture", "Notation", "Infix", "Reserved", "Ltac",
    "Hint", "Declare", "Load", "Canonical", "Coercion", "Include",
))


def _strip_coq_comments(text):
    """剥 Coq 块注释（(* … *)·嵌套）与字符串字面量（"…"·\\ 转义）——单趟扫描。

    注释内 Require 不得入账（nw10/abl6 判据面）；字符串内散文 Require 同不
    入账——实盘判例（v6 轮）：ConstructiveWorld_Live/UpReqIndex.v:2821 起三处
    `"FA-D1S12 … zero Require on mother …"` 字面量曾令 on/mother/of/six/face/
    delta 六散文词伪名入账，单趟剥离后根除。
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "(" and text[i:i + 2] == "(*":
            depth = 1
            i += 2
            while i < n and depth:
                if text[i:i + 2] == "(*":
                    depth += 1
                    i += 2
                elif text[i:i + 2] == "*)":
                    depth -= 1
                    i += 2
                else:
                    i += 1
            out.append(" ")
        elif ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_requires(text):
    """① 全 Require 形式解析 → 有序 [(module, from_prefix, verb)] 列表。

    收：`Require A B.`／`Require Import A B.`／`Require Export A B.`／
    `From X Require Import A B.` 及多名多行形（语句级至终结点·re.S）；
    块注释剥除；名区逐 token 扫描，终结点/非法 token/越界词防停。
    """
    text = _strip_coq_comments(text)
    out = []
    for head in _REQ_HEAD_RE.finditer(text):
        frm = head.group("frm")
        verb = (head.group("verb") or "").strip()
        pos = head.end()
        while pos < len(text):
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text):
                break  # 未闭语句（EOF 无终结点）——按已收名入账·不产垃圾
            ch = text[pos]
            if ch == ".":
                break  # 语句终结
            tok_m = _REQ_NAME_RE.match(text, pos)
            if not tok_m:
                break  # 括号等不可解析名区（如导出列 (x y)）——防停·已收名有效
            tok = tok_m.group(0)
            if "." not in tok and tok in _VERNAC_STOP:
                break  # 名区越界（畸形语句）——裸 vernacular 词防停
            out.append((tok, frm, verb))
            pos = tok_m.end()
    return out


_WORLD_INDEX_MEMO = {}


def world_index(world_dir):
    """③ world_dir → 相对 .v/.vo 路径集合（os.walk 全索引·进程内按 abspath 缓存）。"""
    root = os.path.abspath(world_dir)
    hit = _WORLD_INDEX_MEMO.get(root)
    if hit is not None:
        return hit
    files = set()
    for dirpath, _dirs, fnames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        for fn in fnames:
            if fn.endswith(".v") or fn.endswith(".vo"):
                rel = fn if rel_dir == "." else os.path.join(rel_dir, fn)
                files.add(rel.replace(os.sep, "/"))
    _WORLD_INDEX_MEMO[root] = files
    return files


def _in_world(name, files):
    """闭包存在性判：点路径→/ 展开，全等或 /路径结尾 命中 .v/.vo 任一即闭。

    结尾比对带 `/` 锚（全词同律防前缀误咬）——世界有 sub/UpReqBanachExp.v
    不判 UpReqBanach 闭。
    """
    rel = "/".join(name.split("."))
    for suf in (".v", ".vo"):
        if rel + suf in files:
            return True
    for suf in (".v", ".vo"):
        tail = "/" + rel + suf
        for f in files:
            if f.endswith(tail):
                return True
    return False


def audit_requires(file, world_dir, stats=None):
    """v6 判据：对一 .v 文件做 Require 面审计。

    正确工法三件套：parse_requires 全形式解析→STDLIB_ROOTS 首段豁免→
    world_index 存在性闭包。返回 findings 列表（dict code/name/detail·与
    audit() 同形）；REQ-GAP＝非豁免 Require 世界内无 .v/.vo 对应（树内缺口）。
    file/world_dir 缺失 → MissingPath（fail-loud 不模拟）。stats 传 dict 时
    回填 require_names/stdlib_exempt/tree_checked 三计数（可选·缺省 None）。
    """
    if not os.path.isfile(file):
        raise MissingPath("--requires 文件缺失: %s" % file)
    if not os.path.isdir(world_dir):
        raise MissingPath("--world 目录缺失: %s" % world_dir)
    with io.open(file, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    parsed = parse_requires(text)
    files = world_index(world_dir)
    findings = []
    seen = set()
    n_exempt = 0
    for name, _frm, verb in parsed:
        if name.split(".")[0] in STDLIB_ROOTS:
            n_exempt += 1
            continue  # ② Stdlib 白名单豁免——不入树内缺口判定
        if name in seen:
            continue
        seen.add(name)
        if not _in_world(name, files):
            findings.append({
                "code": "REQ-GAP", "name": name,
                "detail": "Require%s 面缺口：世界 %s 内无 %s.v/.vo"
                          "（全索引存在性判负·Stdlib 白名单已豁免在先）"
                          % ((" Export" if verb == "Export" else ""),
                             os.path.basename(os.path.normpath(world_dir)), name)})
    if stats is not None:
        stats["require_names"] = len(parsed)
        stats["stdlib_exempt"] = n_exempt
        stats["tree_checked"] = len(seen)
    return findings


def selftest():
    """内嵌向量组（临时文件驱动）：clean／批内重（nw6）／跨批撞（enbig7）／
    不在树／树表自重／grep 双判／名归一三形／用法与缺件。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_selectaudit_self_")
    try:
        order = os.path.join(tmp, "order.txt")
        with io.open(order, "w", encoding="utf-8") as fh:
            fh.write("S01_BaseRing.v#R0-d66910\n"
                     "S02_CauchyComplete.v#R0-d66910\n"
                     "S03_QExp.v#R0-d66910\n"
                     "HansonLcm.v#R0-d66910\n"
                     "zzm1_gauss.v\n"
                     "Local/LW0LeibSeparation.v#R160-eb42d3\n")

        # ① clean：名归一三形会师（#代签/裸名/.v 后缀·含 / 路径形）→ rc 0 CLEAN

        def run(args):
            return subprocess_run([sys.executable, "-B",
                                   os.path.join(os.path.dirname(os.path.abspath(__file__)), PROG + ".py")] + args)

        b1 = os.path.join(tmp, "b1.txt")
        with io.open(b1, "w", encoding="utf-8") as fh:
            fh.write("# 候批\nS03_QExp.v#R2-abc\nzzm1_gauss.v\nLocal/LW0LeibSeparation.v\n")
        # ① clean：名归一三形会师（#代签/裸名/.v 后缀·含 / 路径形）→ rc 0 CLEAN
        p = run(["--order", order, "--select", b1])
        assert p.returncode == 0, "clean 应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        assert "AUDIT-CLEAN" in p.stdout, p.stdout

        # ② 批内重复负判（nw6）→ rc 1·DUP-BATCH
        dupb = os.path.join(tmp, "dupb.txt")
        with io.open(dupb, "w", encoding="utf-8") as fh:
            fh.write("HansonLcm.v\nHansonLcm\n")
        p = run(["--order", order, "--select", dupb])
        assert p.returncode == 1 and "DUP-BATCH" in p.stdout, p.stdout

        # ③ 跨批撞名负判（enbig7）→ rc 1·DUP-CROSS
        b2 = os.path.join(tmp, "b2.txt")
        with io.open(b2, "w", encoding="utf-8") as fh:
            fh.write("zzm1_gauss\nHansonLcm.v\n")
        p = run(["--order", order, "--select", b1, "--select", b2])
        assert p.returncode == 1 and "DUP-CROSS" in p.stdout, p.stdout
        assert "zzm1_gauss" in p.stdout, p.stdout

        # ④ 不在树负判 → rc 1·NOT-IN-ORDER
        ghost = os.path.join(tmp, "ghost.txt")
        with io.open(ghost, "w", encoding="utf-8") as fh:
            fh.write("From_Memory_Only.v\n")
        p = run(["--order", order, "--select", ghost])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout, p.stdout

        # ⑤ 树表自重负判 → rc 1·DUP-ORDER
        order_dup = os.path.join(tmp, "order_dup.txt")
        with io.open(order_dup, "w", encoding="utf-8") as fh:
            fh.write("A_Mod.v\nB_Mod.v\nA_Mod.v#R1-ffff\n")
        bd = os.path.join(tmp, "bd.txt")
        with io.open(bd, "w", encoding="utf-8") as fh:
            fh.write("B_Mod\n")
        p = run(["--order", order_dup, "--select", bd])
        assert p.returncode == 1 and "DUP-ORDER" in p.stdout and "A_Mod" in p.stdout, p.stdout

        # ⑥ --grep 双判：命中 rc 0 逐行出；未命中 rc 1；全词不误咬
        p = run(["--order", order, "--grep", "HansonLcm"])
        assert p.returncode == 0 and "HansonLcm.v#R0-d66910" in p.stdout, p.stdout
        p = run(["--order", order, "--grep", "No_Such_Mod"])
        assert p.returncode == 1, "grep 未命中应 rc=1 实测 %d" % p.returncode
        # 前缀不误咬：grep S01_BaseRing 恰 1 行命中·不得咬出 S03 行
        p = run(["--order", order, "--grep", "S01_BaseRing"])
        hit_lines = [l for l in p.stdout.splitlines() if l.startswith("ORDER-HIT")]
        assert p.returncode == 0 and len(hit_lines) == 1 \
            and "S03" not in p.stdout, p.stdout

        # ⑦ 用法/缺件：缺 --select 且无 --grep → rc 2；order 缺失 → rc 9
        p = run(["--order", order])
        assert p.returncode == 2, "缺 select 应 rc=2 实测 %d" % p.returncode
        p = run(["--select", b1])
        assert p.returncode == 2, "select 缺 order 应 rc=2 实测 %d" % p.returncode
        p = run(["--order", os.path.join(tmp, "nope.txt"), "--select", b1])
        assert p.returncode == 9, "order 缺失应 rc=9 实测 %d" % p.returncode

        # ⑧ 前缀不误咬（审计本体）：选 UpReqBanach 不误认 UpReqBanachExp 在树
        order_pfx = os.path.join(tmp, "order_pfx.txt")
        with io.open(order_pfx, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanachExp.v\n")
        bp = os.path.join(tmp, "bp.txt")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write("UpReqBanach\n")
        p = run(["--order", order_pfx, "--select", bp])
        assert p.returncode == 1 and "NOT-IN-ORDER" in p.stdout \
            and "UpReqBanachExp" not in p.stdout, p.stdout

        # ⑨ v6 判据·Require 面 RED 判：nw10/abl6 空账判例三坑全现形——
        #   Stdlib 白名单豁免（QArith/Lia/List/Extraction/Lqa/Morphisms 不误判缺口）·
        #   多名多行/From/Export 全解析·注释内 Require 剥除·闭包存在性判缺口恰二
        #   （UpReqBanach 前缀不误咬 UpReqBanachExp.v）
        rw = os.path.join(tmp, "reqworld")
        os.makedirs(os.path.join(rw, "sub"))
        for fn, content in (("A.v", "Module A. End A.\n"),
                            ("UpReqBanachExp.v", "Module E. End E.\n"),
                            (os.path.join("sub", "B.v"), "Module B. End B.\n"),
                            (os.path.join("sub", "C.vo"), "fakevo\n")):
            with io.open(os.path.join(rw, fn), "w", encoding="utf-8") as fh:
                fh.write(content)
        reqf = os.path.join(tmp, "req.v")
        with io.open(reqf, "w", encoding="utf-8") as fh:
            fh.write("(* Require Import Ghost. 注释面不得入账 *)\n"
                     "From Stdlib Require Import\n"
                     "     QArith.QArith\n"
                     "     List.List.\n"
                     "Require Export Lia.\n"
                     "Require Import Lqa Morphisms Extraction.\n"
                     "From Foo Require Import A.\n"
                     "Require Export sub.B.\n"
                     "Require sub.C.\n"
                     "Require Import UpReqBanach.\n"
                     "From Local Require Import Missing_Mod.\n")
        p = run(["--requires", reqf, "--world", rw])
        gap_lines = [l for l in p.stdout.splitlines() if l.startswith("FINDING REQ-GAP")]
        assert p.returncode == 1 and "REQ-GAP" in p.stdout, p.stdout
        assert "UpReqBanach" in p.stdout and "Missing_Mod" in p.stdout, p.stdout
        assert "Ghost" not in p.stdout, "注释内 Require 泄账\n" + p.stdout
        assert len(gap_lines) == 2, "缺口应恰二（UpReqBanach/Missing_Mod）\n" + p.stdout
        assert "stdlib_exempt=6" in p.stdout, p.stdout

        # ⑩ v6 判据·CLEAN 与用法/缺件：全豁免 → REQUIRES-CLOSED rc 0；
        #   requires 缺 --world rc 2；对象缺失/世界缺失 → rc 9
        req_std = os.path.join(tmp, "req_std.v")
        with io.open(req_std, "w", encoding="utf-8") as fh:
            fh.write("Require Import QArith.\nRequire Export Lia.\n")
        p = run(["--requires", req_std, "--world", rw])
        assert p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout, p.stdout
        #   实盘补件向量：字符串字面量散文 Require（UpReqIndex.v:2821 判例形）不入账；
        #   Lists.List/PeanoNat/Permutation/QArith_base/Qring/ZArithRing/micromega.Lqa
        #   等裸形 Stdlib 件（工具链 Stdlib/** 逐一实证在库）豁免 → 对小世界亦全闭
        req_str = os.path.join(tmp, "req_str.v")
        with io.open(req_str, "w", encoding="utf-8") as fh:
            fh.write('"FA-D1S12 pack: zero Require on mother, slot reconciliation."\n'
                     "Require Import Lists.List PeanoNat Permutation.\n"
                     "Require Import QArith_base Qring Qfield Qabs ZArithRing.\n"
                     "Require Import String Ascii Wf_nat.\n"
                     "Require Import micromega.Lqa.\n")
        p = run(["--requires", req_str, "--world", rw])
        assert p.returncode == 0 and "REQUIRES-CLOSED" in p.stdout, p.stdout
        assert "mother" not in p.stdout and "reconciliation" not in p.stdout, p.stdout
        p = run(["--requires", req_std])
        assert p.returncode == 2, "requires 缺 world 应 rc=2 实测 %d" % p.returncode
        p = run(["--requires", os.path.join(tmp, "nope.v"), "--world", rw])
        assert p.returncode == 9, "requires 对象缺失应 rc=9 实测 %d" % p.returncode
        p = run(["--requires", req_std, "--world", os.path.join(tmp, "noworld")])
        assert p.returncode == 9, "world 缺失应 rc=9 实测 %d" % p.returncode

        print("SELECT-AUDIT-SELFTEST PASS: clean/批内重nw6/跨批撞enbig7/不在树/"
              "树表自重/grep双判/全词不误咬/用法2/缺件9/Require面RED(v6)/"
              "Require面CLEAN+用法+字符串散文剥+实盘补件白名单 十一判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def subprocess_run(argv):
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="选件审计器：批选清单对树 order.txt 全表 grep 剔重"
                               "＋Require 面审计（v6 判据）")
    ap.add_argument("--order", default=None, help="认证树 order.txt 全表（只读·"
                   "select/grep 形必给）")
    ap.add_argument("--select", action="append", default=[], metavar="批选清单",
                    help="候选批选文件（可重复＝多批·跨批撞名判据面）")
    ap.add_argument("--grep", default=None, help="单名全表 grep（勘定员实读替身）")
    ap.add_argument("--requires", default=None, metavar="FILE.v",
                    help="Require 面审计对象文件（v6 判据·nw10/abl6 空账判例工法）")
    ap.add_argument("--world", default=None, metavar="世界目录",
                    help="--requires 配套世界目录（.v/.vo 存在性闭包面）")
    ap.add_argument("--json", default=None, help="审计账 JSON 出账路径")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # v6 判据·Require 面审计形（--requires＋--world·独立于 order/select/grep）
    if args.requires:
        if not args.world:
            print("FAIL-LOUD: --requires 须配 --world <世界目录>"
                  "（.v/.vo 存在性闭包面）", file=sys.stderr)
            sys.exit(2)
        stats = {}
        try:
            findings = audit_requires(args.requires, args.world, stats)
        except MissingPath as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(9)
        print("REQUIRES-AUDIT file=%s world=%s require_names=%d "
              "stdlib_exempt=%d tree_checked=%d"
              % (args.requires, args.world, stats.get("require_names", 0),
                 stats.get("stdlib_exempt", 0), stats.get("tree_checked", 0)))
        for f in findings:
            print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
        if findings:
            print("REQUIRES-RED: %d 树内缺口（exit 1·补件或扩 STDLIB_ROOTS 豁免）"
                  % len(findings))
        else:
            print("REQUIRES-CLOSED: Require 面全闭（全形式解析·Stdlib 白名单豁免·"
                  "世界 .v/.vo 存在性闭包）")
        sys.exit(1 if findings else 0)

    if not args.order:
        print("FAIL-LOUD: select/grep 形须给 --order <order.txt>", file=sys.stderr)
        sys.exit(2)

    try:
        if args.grep:
            if not os.path.isfile(args.order):
                print("FAIL-LOUD: --order 文件缺失: %s" % args.order, file=sys.stderr)
                sys.exit(9)
            with io.open(args.order, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
            try:
                name = normalize_line(args.grep)
            except AuditError as e:
                print("FAIL-LOUD: %s" % e, file=sys.stderr)
                sys.exit(2)
            hits = grep_rows(lines, name)
            print("GREP %s 全表命中 %d 行:" % (name, len(hits)))
            for h in hits:
                print("ORDER-HIT %s" % h)
            sys.exit(0 if hits else 1)

        if not args.select:
            print("FAIL-LOUD: --select 与 --grep 必给其一（无单不审）", file=sys.stderr)
            sys.exit(2)
        order_names = read_names(args.order, "--order")
        batches = [(p, read_names(p, "--select")) for p in args.select]
    except MissingPath as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)
    except AuditError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    print("SELECT-AUDIT order=%s order_rows=%d order_names=%d batches=%d selected=%d"
          % (args.order, len(order_names), len(set(order_names)), len(batches),
             sum(len(n) for _, n in batches)))
    findings = audit(order_names, batches)
    for f in findings:
        print("FINDING %-12s %s — %s" % (f["code"], f["name"], f["detail"]))
    if findings:
        print("AUDIT-RED: %d 发现（exit 1·剔重后重报）" % len(findings))
        verdict = "RED"
    else:
        print("AUDIT-CLEAN: 四判零发现（全表实读·批内无重·跨批无撞·选件皆在树）")
        verdict = "CLEAN"

    if args.json:
        acc = {"order": args.order,
               "order_rows": len(order_names), "order_names": len(set(order_names)),
               "batches": [{"path": p, "count": len(n), "names": n} for p, n in batches],
               "findings": findings, "verdict": verdict}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
