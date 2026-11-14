#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_fix.py — 注册册处方执行器：registry_audit fix-plan 的落刀面（rocqwash
tools/·v46 待办 2 兑现·卫生波工具环闭合·20261112 入账）

v46 真仓 demo（Set Live 权威对）实证的 543 病灶（duplicates=12·_CoqProject 尾区
L492-515 逐字重复块＋anchors=523·撞锚 6 恰 v35 判例原文）由 tools/registry_audit.py
--fix-plan 出确定性处方（DEDUP 保首/锚刷/ORPHAN-ADD 模板/unresolvable）——本器把
处方逐条落刀：逐条 fail-loud·逐条前后 md5 账·执行后重跑审计断言·炸即回滚。

三类处方（audit fix_plan 逐条直执·键式/锚正典/重锚引擎零重造）：
  ① DEDUP 保首   duplicates 病灶按 fix-plan（keep=min 行号·drop=余行升序）重写册。
                 行尾/末行换行随正本（registry_union read_side/render_output 引擎
                 口径直用）；keep/drop 行号按 audit 原行号系逐条对键验尸（键不符
                 ＝audit↔册漂移→AssertBlast exit 2·禁静默）。
  ② 锚刷         anchors 病灶非正典形件（fix_plan.reanchor＝顺序号形/形怪诸键·
                 正典形撞不列靶）→内嵌直调 registry_union.apply_reanchor 同款函数
                 （md5 对 --anchor-src 落地实件重算·保原序号·该键全表行重写）：
                 实件缺→留原样列 skip 清单（不硬造）；实件歧义/列名行无锚→引擎
                 同款 fail-loud；audit 记 md5_8 与实件重算不符→AssertBlast（audit
                 ↔实件漂移·禁静默）。同输同出断言见 --selftest 矢量三（77c2b9a8
                 冻结向量：本器内嵌路径与 registry_union CLI 逐字节恒同）。
  ③ ORPHAN-ADD   缺模板序号 <SEQ>/缺 md5→skip 清单如实直传——补行序号须注册决定
                 （禁机械造锚）；audit 已列 unresolvable 族（正典形锚撞＝同内容
                 md5 同签或同签误植·重锚不改值）原样直传人工分判；anchor-missing
                 病灶（键行无锚·无序号可承）同归 skip 清单。

断言三判（--apply 执行后·重跑 registry_audit 同参）：
  A-fix-1  被治键 duplicates=0   重跑审计 duplicates 账中被治（book,key）零残留；
  A-fix-2  锚撞文本零新增        registry_union A3 同款引擎直算（post 对 pre 逐锚
           文本重复对数·增即炸——同内容 md5 同签的新撞＝真数据病·须人工分判）；
  A-fix-3  孤儿不增              重跑审计孤儿账 (kind,key) 集 ⊆ 执行前（不增）。
  任一炸＝exit 2＋回滚（写前 tmp 备份·炸即还原·还原 md5 对原值复核·证据入
  report）。处方演算全程内存 staging（零写盘）：逐条 md5 账为 staged-render 字节
  （行尾/末行随正本）——staging 炸＝册面零触碰零回滚；仅落盘后断言炸才回滚。

两态制（缺省干跑）：干跑＝处方逐条预演＋skip 清单＋md5 账（内存仿真如实标注）
＋断言 NOT-RUN（干跑零写盘·断言不适用——push_gate NOT-RUN 同律诚实记）＋零写盘
（work-dir 亦不建）；--apply 才写：写面＝显式指认的双册＋work-dir 备份＋显式
--json 出账路径。写前每册 shutil 备份入 --work-dir（缺省 tempfile.mkdtemp·可
--work-dir 固定）——回滚证据（备份路径/还原 md5）入 report。--apply 重跑已治册
＝stale 爆（keep/drop 行号超界或键不符）exit 2·零写盘（fresh audit 重出方可
复跑——处方与册面须同代）。

同参纪律：--audit-json 须为 registry_audit --fix-plan 产出（schema
rocqwash-registry-audit/1）且其 inputs.order/project 与执行器 --order/--project
逐字同（处方行号系绑定被审册面·异册即用法错 exit 2）。断言重跑参＝执行器自持
--order/--project/--anchor-src（--fix-plan 不重出·断言只读四账）。

输出：--json schema rocqwash-registry-fix/1（sort_keys 确定性·items 逐条 md5 账/
skip 清单/writes 盘面账/assertions 三判/rollback 证据）＋响亮 stdout。--apply 模
式 report 含 work-dir 备份路径（路径随 --work-dir·同输入重跑字节恒同以同
--work-dir 为准）；干跑 report 零易变路径（缺省 work-dir 不现形）。

退出码：0=干跑出账或 --apply 落盘＋断言三过；1=--selftest 炸；2=用法错（schema
不合/缺 fix_plan/同参破/条目缺键）或 AssertBlast（行号超界/键不符/md5 漂移/歧义/
无锚/A-fix 三判/写完整性）——AssertBlast 已回滚则报告带证据；9=输入缺（audit
JSON/双册/audit 器/anchor-src 目录缺）。

用法：
  python3 tools/registry_fix.py --audit-json AUDIT.json --order ORDER.txt \
      --project _CoqProject [--anchor-src DIR] [--json REPORT.json]        # 干跑
  python3 tools/registry_fix.py …同上… --apply [--work-dir DIR]            # 落刀
  python3 tools/registry_fix.py --selftest

确定性：无时间戳无环境噪声（唯一环境读数＝INJECT_ENV 人工炸点·selftest 专用·
真跑勿设）；同输入重跑输出字节恒同（selftest 断言）；纯 stdlib 零第三方零网络
零编译。禁触冻结八件/quad8/更新账.md——本器写面恰为 --apply 指认双册＋work-dir
备份＋显式 --json，不触任何在册冻结面。真树 --apply 候令不入本波（器备·真仓
不跑·本波全验在 tmp fixture）。

--selftest 矢量（tmp fixture·v46 audit demo 形态样张：_CoqProject 尾区 12 逐字
重复块＋锚 形怪/顺序号形/撞锚/缺锚/正典撞＋孤儿双向＋缺实件——零触真仓零网络）：
  1 干跑零写盘＋逐条 md5 账＋skip 清单全谱＋干跑 report 重跑字节恒同
  2 --apply：DEDUP 12 重复块→0（重跑审计 duplicates=0）＋断言三过＋md5 账对盘
  3 锚刷 md5 冻结向量（"module A content alpha\\n"→77c2b9a8）＋同输同出（本器
    落刀册 bytes ≡ registry_union CLI 同参产物·逐字节）
  4 回滚实证·人工炸点注入（INJECT_ENV=post-write）→exit 2＋册面逐字节还原
  5 自然炸点（同内容双键重锚→A-fix-2 新撞锚）→exit 2＋回滚＋A3 引擎同码
  6 staging 炸（audit 后册面漂移·保首键不符）→exit 2·零写盘（work-dir 不建）
  7 CLI 四码＋schema 面（help0/bogus2/无输入2/缺件9/坏schema2/无fix_plan2/
    同参破2/anchor-src 缺9）
  8 落刀确定性（双 fresh 夹具同处→册面 bytes 与 md5 账恒同）

ORPHAN-ADD apply path (--orphan-add, added 20261114): the order-only
direction of the orphan prescriptions is mechanically solvable: its
template is placeholder-free (derived from the order key path form) and
the coqproject book carries no anchor, so under the opt-in flag
--orphan-add those entries are executed: the template row is appended to
the coqproject book tail with the same per-item md5 accounting, staging
guards and post-apply assertions as the other classes. Guards: plan
template/key consistency under the coqproject keying (FailLoud); the key
must be present in the order book, else AssertBlast ORPHAN-ADD-KEY-NOT-
IN-ORDER (stale-audit discipline of the DEDUP stage); a coqproject row
already hashing to the key under the coqproject keying (for example an
extension-less module row that the audit .v-suffix criterion cannot see)
routes the entry to the skip list as ORPHAN-ADD-SKIP-KEY-PRESENT instead
of double-registering the module. Post-apply
assertions extend the re-audit face with A-fix-4 orphans_resolved (no
orphan-order-only finding survives for an executed key) and A-fix-5
orphan_add_duplicates_zero (the appended row created no duplicate-key
finding); either blast rolls back like the other assertion blasts.
Without the flag the tool behavior is byte-identical to the frozen face
above: every ORPHAN-ADD prescription stays on the skip list. A paired
project-only entry whose key equals the order-only key after stripping
repeated ".v" suffixes is a suffix-typo signature (e.g. order "X.v" vs
_CoqProject "X.v.v": the module is already registered under a misspelled
row), so such entries are skipped as ORPHAN-ADD-SKIP-SUFFIX-TWIN for
human adjudication instead of double-registering the module; the
project-only direction itself always stays non-mechanical because its
template embeds #R<SEQ> and the sequence number is a registry-side
decision. Vectors for this path live in
tests/test_registry_fix_orphan_add.py (fixture-based, zero real-repo
touch).

REANCHOR residual gate (A-fix-6 treated_anchors_canonical): the
reanchor stage had no post-apply oracle of its own —
A-fix-1 covers treated duplicate keys and A-fix-2 compares anchor-text
collision pairs post vs pre, so a reanchor that silently rewrote nothing
would still pass. After the same-parameter re-audit, every executed
REANCHOR key must now carry no anchor-seq-form / anchor-malformed
finding. The oracle is the audit producer's own classification
(registry_audit sections.anchors; those two kinds are exactly the
reanchor target face of its build_fix_plan), so no anchor semantics are
defined here. Scope is the executed keys only: skip-list keys (missing
entity, missing anchor) and the collision face (A-fix-2) are untouched.
A breach is ASSERT-TREATED-ANCHOR-NONZERO and rolls back like the other
assertion blasts. Vectors live in tests/test_registry_fix_anchor.py.
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

_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
try:
    import registry_union as _ru  # noqa: E402  （键式/锚正典/重锚/A3 引擎·只 import 不改）
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 同侪 tools/registry_union.py 不可导入（键式/锚正典/重锚"
          "引擎零重造依赖）: %s" % _e, file=sys.stderr)
    sys.exit(9)

PROG = "registry_fix"
SCHEMA = "rocqwash-registry-fix/1"
AUDIT_SCHEMA = "rocqwash-registry-audit/1"

MD5_PLACEHOLDER = "<MD5_8>"   # audit fix_plan 占位形（registry_audit 同款常量语义）
SEQ_PLACEHOLDER = "<SEQ>"     # orphan-row sequence placeholder (registry_audit
                              # SEQ_PLACEHOLDER, same constant semantics)
BOOK_KINDS = {"order": _ru.KIND_ORDER, "coqproject": _ru.KIND_COQPROJECT}
DUP_KIND_TO_BOOK = {"dup-order": "order", "dup-coqproject": "coqproject"}
# ORPHAN-ADD prescription direction -> target book (registry_audit
# build_fix_plan contract: order-only rows land in the coqproject book,
# project-only rows would land in the order book).
ORPHAN_DIRECTION_BOOK = {"order-only": "coqproject", "project-only": "order"}
PLACEHOLDER_TOKENS = (MD5_PLACEHOLDER, SEQ_PLACEHOLDER)
# Anchor finding kinds the reanchor stage treats (registry_audit
# build_fix_plan reanchor target face: K_ANCHOR_SEQ / K_ANCHOR_MALFORMED).
REANCHOR_TREATED_KINDS = ("anchor-seq-form", "anchor-malformed")

INJECT_ENV = "ROCWASH_REGISTRY_FIX_INJECT_BLAST"  # 人工炸点（selftest 专用·真跑勿设）


class FailLoud(Exception):
    """用法错（exit 2·无 report——audit 同款 FAIL-LOUD 短报面）。"""


def md5_bytes(b):
    """字节串 md5 全 hex（处方逐条 md5 账基）。"""
    return hashlib.md5(b).hexdigest()


def md5_file(path):
    """文件 md5 全 hex（盘面真值账基）。"""
    h = hashlib.md5()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def dump_json(path, obj):
    """确定性 JSON 落盘（sort_keys＋indent=1·registry_audit dump_json 同款）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


# ---------- 输入面 ----------

def load_audit_payload(path):
    """--audit-json 载入＋schema 验（缺件 9·不可解析/schema 不合＝用法 2）。"""
    if not os.path.isfile(path):
        raise _ru.MissingInput("--audit-json 文件缺失: %s" % path)
    try:
        with io.open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as e:
        raise FailLoud("--audit-json 不可解析（JSON）: %s" % e)
    if not isinstance(payload, dict):
        raise FailLoud("--audit-json 顶层须对象（JSON object）: %s" % path)
    if payload.get("schema") != AUDIT_SCHEMA:
        raise FailLoud("--audit-json schema 不合: %r（须 %s·registry_audit "
                       "--fix-plan 产出）" % (payload.get("schema"), AUDIT_SCHEMA))
    return payload


def validate_audit(payload, args):
    """同参纪律＋账面/处方结构验（fail-loud 用法 2）。返回 fix_plan。"""
    inputs = payload.get("inputs") or {}
    if payload.get("mode") != "files" \
            or inputs.get("order") != args.order \
            or inputs.get("project") != args.project:
        raise FailLoud(
            "同参纪律破：audit 输入面与执行器双册须逐字同（处方行号系绑定被审"
            "册面）——audit mode=%r inputs.order=%r inputs.project=%r；执行器"
            " --order=%r --project=%r"
            % (payload.get("mode"), inputs.get("order"), inputs.get("project"),
               args.order, args.project))
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        raise FailLoud("audit sections 缺或非对象（audit 自洽破）")
    for k in ("duplicates", "anchors", "orphans"):
        if not isinstance(sections.get(k), list):
            raise FailLoud("audit sections.%s 缺或非列（audit 自洽破）" % k)
    plan = payload.get("fix_plan")
    if not isinstance(plan, dict):
        raise FailLoud("audit 未带 fix_plan（registry_audit 须 --fix-plan 产出）"
                       "——执行器无处方可执")
    for k in ("dedup", "reanchor", "orphan", "unresolvable"):
        if not isinstance(plan.get(k), list):
            raise FailLoud("fix_plan.%s 缺或非列（audit 自洽破）" % k)
    return plan


# ---------- 册态 ----------

class BookState(object):
    """单册态：正本读形＋处方演化（原行号系 slots 保全·cur 现行）。

    行尾/末行换行随正本（read_side 探形·render_output 重建——registry_union
    引擎口径直用）；md5_staged＝处方演化的 staged-render 字节账。
    """

    def __init__(self, path, label):
        self.path = path
        self.label = label
        self.kind = BOOK_KINDS[label]
        self.orig_lines, self.eol, self.final_nl = _ru.read_side(
            path, "--%s" % label)  # 缺件 MissingInput→9
        self.slots = list(enumerate(self.orig_lines, 1))  # (audit 原行号, 行)
        self.deleted = set()     # 已处方删除的原行号系
        self.cur = list(self.orig_lines)

    def apply_deletes(self, orig_nos):
        """按原行号系删行（dedup 保首·slots 口径一次重组）。"""
        self.deleted.update(orig_nos)
        self.cur = [ln for (no, ln) in self.slots if no not in self.deleted]

    def render(self):
        return _ru.render_output(self.cur, self.eol, self.final_nl)

    def md5_staged(self):
        return md5_bytes(self.render())

    def touched(self):
        return self.cur != self.orig_lines


# ---------- 处方演算（staging·零写盘） ----------

def stage_dedup(plan, books, items):
    """① DEDUP 保首：fix_plan.dedup 逐条验尸＋演化（原行号系·keep=min 不动）。"""
    for e in plan["dedup"]:
        if not isinstance(e, dict):
            raise FailLoud("fix_plan.dedup 条目非对象: %r" % (e,))
        book = e.get("book")
        key = e.get("key")
        keep = e.get("keep_line")
        drops = e.get("drop_lines")
        if book not in BOOK_KINDS:
            raise FailLoud("fix_plan.dedup book 非法: %r（须 order|coqproject）"
                           % (book,))
        if not isinstance(key, str) or not key:
            raise FailLoud("fix_plan.dedup 条目缺 key: %r" % (e,))
        if not isinstance(keep, int) or not isinstance(drops, list) \
                or not drops or not all(isinstance(n, int) for n in drops):
            raise FailLoud("fix_plan.dedup 条目缺 keep_line/drop_lines: key=%r"
                           % key)
        bs = books[book]
        for n in [keep] + list(drops):
            if not 1 <= n <= len(bs.slots):
                raise _ru.AssertBlast(
                    "DEDUP-LINE-OUT-OF-RANGE",
                    ["book=%s key=%r 行 L%d 超界（1..%d）——audit↔册漂移"
                     "（stale audit 禁静默）" % (book, key, n, len(bs.slots))])
        if _ru.key_of(bs.slots[keep - 1][1], bs.kind) != key:
            raise _ru.AssertBlast(
                "DEDUP-KEEP-KEY-MISMATCH",
                ["book=%s keep=L%s 现行键 %r ≠ 处方键 %r——audit↔册漂移"
                 % (book, keep, _ru.key_of(bs.slots[keep - 1][1], bs.kind),
                    key)])
        for n in drops:
            if _ru.key_of(bs.slots[n - 1][1], bs.kind) != key:
                raise _ru.AssertBlast(
                    "DEDUP-DROP-KEY-MISMATCH",
                    ["book=%s drop=L%s 现行键 %r ≠ 处方键 %r——audit↔册漂移"
                     % (book, n, _ru.key_of(bs.slots[n - 1][1], bs.kind), key)])
        if keep in drops:
            raise _ru.AssertBlast(
                "DEDUP-KEEP-IN-DROP",
                ["book=%s key=%r keep=L%d 同时列 drop（audit 处方自洽破）"
                 % (book, key, keep)])
        overlap = sorted(set(drops) & bs.deleted)
        if overlap:
            raise _ru.AssertBlast(
                "DEDUP-DROP-ALREADY-DELETED",
                ["book=%s key=%r drop 行已先治（处方行号交叠·audit 自洽破）: L%s"
                 % (book, key, ",".join(str(n) for n in overlap))])
        before = bs.md5_staged()
        bs.apply_deletes(set(drops))
        items.append({"no": len(items) + 1, "kind": "DEDUP", "book": book,
                      "key": key, "keep_line": keep,
                      "drop_lines": sorted(drops),
                      "md5_before": before, "md5_after": bs.md5_staged()})


def stage_reanchor(plan, books, items, skips, anchor_src):
    """② 锚刷：fix_plan.reanchor 逐条→registry_union.apply_reanchor 同款直调。"""
    bs = books["order"]
    for e in plan["reanchor"]:
        if not isinstance(e, dict):
            raise FailLoud("fix_plan.reanchor 条目非对象: %r" % (e,))
        key = e.get("key")
        if not isinstance(key, str) or not key:
            raise FailLoud("fix_plan.reanchor 条目缺 key: %r" % (e,))
        bare = _ru.bare_name(key)
        if anchor_src is None:
            skips.append({"kind": "REANCHOR-SKIP-NO-ANCHOR-SRC", "key": key,
                          "reason": "执行器未给 --anchor-src（md5 无源·留原样"
                                    "如实列 skip·wash_shape plan-miss 同律）"})
            continue
        before = bs.md5_staged()
        # 引擎同款重锚（歧义 UsageError/无锚 AssertBlast 原样上抛＝引擎语义）
        out, rewrites, missing, not_in_table = _ru.apply_reanchor(
            bs.cur, [bare], anchor_src, _ru.KIND_ORDER)
        if not_in_table:
            raise _ru.AssertBlast(
                "REANCHOR-KEY-NOT-IN-TABLE",
                ["处方键 %r 不在现表（audit↔册漂移·禁静默）: %s"
                 % (key, not_in_table)])
        if missing:
            skips.append({"kind": "REANCHOR-SKIP-MISSING-ENTITY", "key": key,
                          "bare": bare,
                          "reason": "anchor-src 下缺同名 .v 实件（留原样·如实"
                                    "列 skip·不硬造）"})
            continue
        entity = _ru.resolve_entity(bare, anchor_src)  # missing 空故非 None
        engine_md5 = rewrites[0]["md5_8"] if rewrites else _ru.md5_8_of(entity)
        audit_md5 = e.get("md5_8")
        if audit_md5 and audit_md5 != MD5_PLACEHOLDER and audit_md5 != engine_md5:
            raise _ru.AssertBlast(
                "REANCHOR-MD5-DRIFT",
                ["处方键 %r：audit 记 md5_8=%s 而实件重算=%s（audit↔实件漂移"
                 "·禁静默）" % (key, audit_md5, engine_md5)])
        bs.cur = out
        items.append({"no": len(items) + 1, "kind": "REANCHOR", "book": "order",
                      "key": key, "bare": bare,
                      "old_anchor": e.get("old_anchor"), "md5_8": engine_md5,
                      "entity": entity,
                      "rewrites": [{"line_no": r["line_index"] + 1,
                                    "old_anchor": r["old_anchor"],
                                    "new_anchor": r["new_anchor"]}
                                   for r in rewrites],
                      "md5_before": before, "md5_after": bs.md5_staged()})


def stage_nons(plan, payload, skips):
    """③ 非机械可解→skip 清单如实直传（孤儿模板/unresolvable/缺锚）。"""
    for o in plan["orphan"]:
        if not isinstance(o, dict) or not o.get("key"):
            raise FailLoud("fix_plan.orphan 条目缺 key: %r" % (o,))
        skips.append({"kind": "ORPHAN-ADD-SKIP-NON-MECHANICAL",
                      "key": o.get("key"), "direction": o.get("direction"),
                      "template": o.get("template"),
                      "reason": "补行序号 <SEQ> 须注册决定·禁机械造锚（模板"
                                "直传·audit 处方同款）"})
    for u in plan["unresolvable"]:
        skips.append({"kind": "UNRESOLVABLE-PASSTHROUGH", "anchor": u.get("anchor"),
                      "lines": u.get("lines"), "note": u.get("note")})
    for f in (payload.get("sections") or {}).get("anchors") or []:
        if isinstance(f, dict) and f.get("kind") == "anchor-missing":
            skips.append({"kind": "ANCHOR-MISSING-SKIP", "key": f.get("key"),
                          "lines": f.get("lines"),
                          "reason": "键行无锚（无序号可承·序号须注册决定·禁机械"
                                    "造锚）"})


# ---------- ④ ORPHAN-ADD apply path (opt-in --orphan-add) ----------

def stage_orphan_add(plan, books, items, skips):
    """④ ORPHAN-ADD apply path: execute the mechanically solvable subset.

    An order-only prescription (target book coqproject, whose rows carry
    no anchor) with a placeholder-free template is executed by appending
    the template row to the coqproject book tail, one row per
    prescription, in plan order, with the same per-item md5 accounting as
    the DEDUP/REANCHOR stages. Guards (fail-loud):
      - plan contract: template must be a ".v" row and must hash to the
        prescription key under the coqproject keying (FailLoud on breach);
      - audit-vs-book drift: the key must be present in the order book
        (.v basename criterion, the audit orphan account source), else
        AssertBlast ORPHAN-ADD-KEY-NOT-IN-ORDER (stale-audit discipline
        of the DEDUP stage);
      - already-registered signature: a coqproject row already hashing
        to the key under the coqproject keying (for example an
        extension-less module row that the audit .v-suffix criterion
        cannot see) routes the entry to the skip list as
        ORPHAN-ADD-SKIP-KEY-PRESENT for human adjudication instead of
        double-registering the module;
      - suffix-typo signature: a project-only entry whose key equals the
        order-only key after stripping repeated ".v" suffixes (e.g. order
        "X.v" vs coqproject "X.v.v") means the module is already
        registered under a misspelled row; the entry is skipped as
        ORPHAN-ADD-SKIP-SUFFIX-TWIN for human adjudication instead of
        double-registering the module.
    Order-only entries carrying placeholders and every project-only entry
    are left in the returned residual list, so the existing non-mechanical
    passthrough (stage_nons) reports them with its own skip kind
    unchanged. Callers must invoke this stage after stage_dedup /
    stage_reanchor and feed the residual list to stage_nons, because the
    appended rows live in books["coqproject"].cur outside the original
    line-number slots that apply_deletes rebuilds from.
    Returns the residual (non-executed) orphan entry list.
    """
    bs = books["coqproject"]
    order_bases = set()
    for _no, ln in books["order"].slots:
        k = _ru.key_of(ln, _ru.KIND_ORDER)
        if k is not None and k.endswith(".v"):
            order_bases.add(_ru.bare_name(k).rsplit("/", 1)[-1])
    twins = {}
    for o in plan["orphan"]:
        if not isinstance(o, dict) or not o.get("key"):
            raise FailLoud("fix_plan.orphan entry missing key: %r" % (o,))
        if o.get("direction") == "project-only":
            k = o["key"]
            while isinstance(k, str) and k.endswith(".v"):
                k = k[:-2]
            if k in order_bases:
                twins[k] = o["key"]
    residual = []
    for o in plan["orphan"]:
        key = o["key"]
        direction = o.get("direction")
        template = o.get("template")
        if key in twins:
            skips.append({"kind": "ORPHAN-ADD-SKIP-SUFFIX-TWIN",
                          "key": key, "direction": direction,
                          "template": template, "twin_key": twins[key],
                          "reason": "paired project-only registration under "
                                    "a repeated-.v spelling (e.g. X.v.v): "
                                    "the module is already registered, "
                                    "appending a second spelling would "
                                    "double-register it; left for human "
                                    "adjudication"})
            continue
        if direction == "order-only" \
                and ORPHAN_DIRECTION_BOOK.get(direction) == "coqproject":
            if not isinstance(template, str) or not template.endswith(".v"):
                raise FailLoud("fix_plan.orphan order-only template must be "
                               "a .v row: key=%r template=%r"
                               % (key, template))
            if any(ph in template for ph in PLACEHOLDER_TOKENS):
                residual.append(o)   # non-mechanical passthrough (stage_nons)
                continue
            if _ru.key_of(template, _ru.KIND_COQPROJECT) != key:
                raise FailLoud("fix_plan.orphan template/key mismatch under "
                               "the coqproject keying: key=%r template=%r"
                               % (key, template))
            if key not in order_bases:
                raise _ru.AssertBlast(
                    "ORPHAN-ADD-KEY-NOT-IN-ORDER",
                    ["book=order has no .v basename %r (audit orphan account "
                     "source face) - audit-vs-book drift, stale audit is not "
                     "silently tolerated" % key])
            present = [i for i, ln in enumerate(bs.cur, 1)
                       if _ru.key_of(ln, _ru.KIND_COQPROJECT) == key]
            if present:
                skips.append({"kind": "ORPHAN-ADD-SKIP-KEY-PRESENT",
                              "key": key, "direction": direction,
                              "template": template, "present_lines": present,
                              "reason": "the target book already carries a "
                                        "row hashing to this key under the "
                                        "coqproject keying (for example an "
                                        "extension-less module row that the "
                                        "audit .v-suffix criterion cannot "
                                        "see); appending would "
                                        "double-register the module; left "
                                        "for human adjudication"})
                continue
            before = bs.md5_staged()
            bs.cur.append(template)
            items.append({"no": len(items) + 1, "kind": "ORPHAN-ADD",
                          "book": "coqproject", "key": key, "row": template,
                          "line_no": len(bs.cur),
                          "md5_before": before, "md5_after": bs.md5_staged()})
        else:
            residual.append(o)       # project-only: non-mechanical passthrough
    return residual


# ---------- 落盘／断言／回滚 ----------

def backup_and_write(books, work_dir):
    """--apply 写面：逐册写前备份→落盘→盘面 md5 对 staged 账复核。

    写面恰为显式指认双册＋work-dir 备份；写完整性炸＝AssertBlast（主流程回滚）。
    """
    os.makedirs(work_dir, exist_ok=True)
    out = []
    for label in sorted(BOOK_KINDS):  # coqproject < order（确定性序）
        bs = books[label]
        if not bs.touched():
            continue
        on_disk_before = md5_file(bs.path)
        backup = os.path.join(work_dir, "%s.%s.bak" % (label,
                                                       os.path.basename(bs.path)))
        shutil.copy2(bs.path, backup)
        if md5_file(backup) != on_disk_before:
            raise _ru.AssertBlast("BACKUP-INTEGRITY",
                                  ["%s 备份 md5 ≠ 原盘 md5（备份面破·禁落刀）"
                                   % bs.path])
        with io.open(bs.path, "wb") as fh:
            fh.write(bs.render())
        on_disk_after = md5_file(bs.path)
        if on_disk_after != bs.md5_staged():
            raise _ru.AssertBlast("WRITE-INTEGRITY",
                                  ["%s 写后盘 md5 %s ≠ 处方账 %s（写完整性破）"
                                   % (bs.path, on_disk_after, bs.md5_staged())])
        out.append({"book": label, "path": bs.path, "eol": bs.eol,
                    "final_nl": bs.final_nl,
                    "rows_before": len(bs.orig_lines),
                    "rows_after": len(bs.cur),
                    "md5_on_disk_before": on_disk_before,
                    "md5_on_disk_after": on_disk_after,
                    "backup": backup, "backup_md5": md5_file(backup)})
    return out


def rollback(writes):
    """炸即还原：逐册从备份逐字节还原＋md5 对原值复核（证据入 report）。"""
    restored = {}
    all_ok = True
    for w in writes:
        shutil.copy2(w["backup"], w["path"])
        m = md5_file(w["path"])
        ok = (m == w["md5_on_disk_before"])
        all_ok = all_ok and ok
        restored[w["book"]] = {"path": w["path"], "md5_restored": m,
                               "match": ok}
    return {"backups": {w["book"]: w["backup"] for w in writes},
            "restored": restored, "all_restored": all_ok}


def run_assertions(audit_payload, books, treated, args, audit_tool, work_dir):
    """断言三判（--apply 后）：A3 引擎直算＋重跑 registry_audit 同参。"""
    # A-fix-2 锚撞文本零新增（registry_union A3 同款引擎直算·post 对 pre）
    _ru.assert_anchor_no_new_dups(books["order"].cur, books["order"].orig_lines)
    # 重跑 registry_audit 同参（--fix-plan 不重出·断言只读四账）
    if not os.path.isfile(audit_tool):
        raise _ru.MissingInput("audit 器缺失: %s" % audit_tool)
    post_path = os.path.join(work_dir, "post_audit.json")
    cmd = [sys.executable, "-B", audit_tool,
           "--order", args.order, "--project", args.project]
    if args.anchor_src:
        cmd += ["--anchor-src", args.anchor_src]
    cmd += ["--json", post_path]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise _ru.AssertBlast("ASSERT-REAUDIT-FAILED",
                              ["重跑 registry_audit rc=%d: %s"
                               % (p.returncode,
                                  p.stdout.decode("utf-8", errors="replace")
                                  [-800:])])
    with io.open(post_path, encoding="utf-8") as fh:
        post = json.load(fh)
    if post.get("schema") != AUDIT_SCHEMA:
        raise _ru.AssertBlast("ASSERT-REAUDIT-SCHEMA",
                              ["重跑审计 schema 不合: %r" % post.get("schema")])
    # A-fix-1 被治键 duplicates=0
    hits = ["%s/%s" % (f["kind"], f["key"])
            for f in post["sections"]["duplicates"]
            if (DUP_KIND_TO_BOOK.get(f["kind"]), f.get("key")) in treated]
    if hits:
        raise _ru.AssertBlast("ASSERT-TREATED-DUP-NONZERO",
                              ["被治键 duplicates 残留: %s" % h for h in hits])
    # A-fix-3 孤儿不增
    pre_keys = {(f.get("kind"), f.get("key"))
                for f in audit_payload["sections"]["orphans"]}
    post_keys = {(f.get("kind"), f.get("key"))
                 for f in post["sections"]["orphans"]}
    new = sorted("%s/%s" % kv for kv in (post_keys - pre_keys))
    if new:
        raise _ru.AssertBlast("ASSERT-ORPHAN-NEW",
                              ["孤儿账新增: %s" % k for k in new])
    return {"ran": True, "anchor_text_no_new_dups": "PASS",
            "treated_duplicates_zero": "PASS", "orphans_no_new": "PASS",
            "reaudit_summary": post["summary"], "reaudit_inputs": post["inputs"]}


def assert_orphan_add_resolved(post_audit_path, executed_keys):
    """ORPHAN-ADD post-apply assertions (A-fix-4 / A-fix-5).

    Reads the post-apply audit JSON that run_assertions re-ran at the same
    parameters (work-dir post_audit.json) and asserts, for every executed
    orphan key:
      A-fix-4  orphans_resolved            no orphan-order-only finding
                                           survives for the key;
      A-fix-5  orphan_add_duplicates_zero  the appended row created no
                                           duplicate-key finding.
    Any breach is an AssertBlast like the other assertion blasts (the
    caller's rollback path applies unchanged).
    """
    with io.open(post_audit_path, encoding="utf-8") as fh:
        post = json.load(fh)
    resid = sorted(f.get("key") for f in post["sections"]["orphans"]
                   if f.get("kind") == "orphan-order-only"
                   and f.get("key") in executed_keys)
    dups = sorted(f.get("key") for f in post["sections"]["duplicates"]
                  if f.get("kind") == "dup-coqproject"
                  and f.get("key") in executed_keys)
    if resid:
        raise _ru.AssertBlast(
            "ASSERT-ORPHAN-ADD-RESIDUAL",
            ["treated orphan key still unresolved post-apply: %s" % k
             for k in resid])
    if dups:
        raise _ru.AssertBlast(
            "ASSERT-ORPHAN-ADD-DUP",
            ["appended row created a duplicate-key finding: %s" % k
             for k in dups])
    return {"orphans_resolved": "PASS",
            "orphan_add_duplicates_zero": "PASS"}


def assert_treated_anchors_canonical(post, treated_keys):
    """REANCHOR post-apply residual gate (A-fix-6 treated_anchors_canonical).

    Reads the same post-apply audit JSON the A-fix face already re-ran at
    the same parameters and asserts, for every executed REANCHOR key, that
    no anchor finding of the reanchor target kinds (anchor-seq-form /
    anchor-malformed — registry_audit build_fix_plan's own target face)
    survives. The audit producer's classification is the whole oracle; no
    anchor semantics are defined here. Scope is the executed keys only:
    skip-list keys (missing entity, missing anchor) keep their rows by
    design and the collision face stays owned by A-fix-2. Any breach is
    an AssertBlast (ASSERT-TREATED-ANCHOR-NONZERO) and the caller's
    rollback path applies unchanged.
    """
    resid = sorted("%s/%s" % (f.get("kind"), f.get("key"))
                   for f in post["sections"]["anchors"]
                   if f.get("kind") in REANCHOR_TREATED_KINDS
                   and f.get("key") in treated_keys)
    if resid:
        raise _ru.AssertBlast(
            "ASSERT-TREATED-ANCHOR-NONZERO",
            ["treated anchor key still carries an anchor finding "
             "(audit-vs-book drift or reanchor regression): %s" % k
             for k in resid])
    return {"treated_anchors_canonical": "PASS"}


# ---------- report ----------

def build_report(args, audit_payload, plan, books, items, skips, writes,
                 assertions, blast):
    """report（schema rocqwash-registry-fix/1·sort_keys 确定性）。"""
    summ = audit_payload.get("summary") or {}
    executed_dedup = sum(1 for it in items if it["kind"] == "DEDUP")
    executed_reanchor = sum(1 for it in items if it["kind"] == "REANCHOR")
    executed_orphan_add = sum(1 for it in items if it["kind"] == "ORPHAN-ADD")
    skip_by_kind = {}
    for s in skips:
        skip_by_kind[s["kind"]] = skip_by_kind.get(s["kind"], 0) + 1
    touched = sorted(label for label, bs in books.items() if bs.touched())
    report = {
        "schema": SCHEMA,
        "mode": "APPLY" if args.apply else "DRY-RUN",
        "inputs": {"audit_json": args.audit_json, "order": args.order,
                   "project": args.project,
                   "anchor_src": args.anchor_src,
                   "audit_tool": args.audit_tool,
                   "orphan_add": bool(args.orphan_add)},
        "audit_input_meta": {"schema": audit_payload.get("schema"),
                             "mode": audit_payload.get("mode"),
                             "anchor_src": audit_payload.get("anchor_src"),
                             "summary": summ},
        "engine": ("registry_union.apply_reanchor / assert_anchor_no_new_dups"
                   " 直用（键式/锚正典/重锚/A3 零新引擎）"),
        "stats": {
            "planned": {"dedup": len(plan["dedup"]),
                        "reanchor": len(plan["reanchor"]),
                        "orphan": len(plan["orphan"]),
                        "unresolvable": len(plan["unresolvable"])},
            "items_total": len(items),
            "items_executed_dedup": executed_dedup,
            "items_executed_reanchor": executed_reanchor,
            "items_executed_orphan_add": executed_orphan_add,
            "skips_total": len(skips),
            "skips_by_kind": {k: skip_by_kind[k] for k in sorted(skip_by_kind)},
            "rows": {"order_before": len(books["order"].orig_lines),
                     "order_after": len(books["order"].cur),
                     "coqproject_before": len(books["coqproject"].orig_lines),
                     "coqproject_after": len(books["coqproject"].cur)},
            "md5_basis": "逐条 md5＝处方演化的 staged-render 字节（read_side/"
                         "render_output 引擎口径·行尾/末行随正本）；writes."
                         "books 盘面 md5＝落盘真值",
        },
        "items": items,
        "skip": skips,
        "writes": writes,
        "assertions": assertions,
        "blast": blast,
        "summary": {
            "mode": "APPLY" if args.apply else "DRY-RUN",
            "items_total": len(items),
            "items_executed": (executed_dedup + executed_reanchor
                               + executed_orphan_add),
            "skips_total": len(skips),
            "books_touched": sorted(touched),
            "rolled_back": bool(writes and writes.get("rolled_back")),
            "assertions": ("PASS" if assertions and assertions.get("ran")
                           else "NOT-RUN（干跑零写盘·断言不适用）"
                           if not args.apply else "BLAST"),
        },
    }
    return report


def print_stdout(rep):
    """响亮 stdout 出账（确定性·逐条/skip/写面/断言全列）。"""
    print("=== REGISTRY-FIX (%s·%s) ===" % (rep["mode"], SCHEMA))
    for k in sorted(rep["inputs"]):
        print("  %s=%s" % (k, rep["inputs"][k] or "（未给）"))
    aim = rep["audit_input_meta"]["summary"] or {}
    print("audit 旁证: duplicates=%s anchors=%s orphans=%s total=%s（mode=%s）"
          % (aim.get("duplicates"), aim.get("anchors"), aim.get("orphans"),
             aim.get("total"), rep["audit_input_meta"].get("mode")))
    st = rep["stats"]
    print("处方: dedup=%d reanchor=%d（planned orphan=%d unresolvable=%d）"
          % (st["planned"]["dedup"], st["planned"]["reanchor"],
             st["planned"]["orphan"], st["planned"]["unresolvable"]))
    print("--- 处方逐条（%d 条·md5 账＝staged-render 口径） ---" % len(rep["items"]))
    for it in rep["items"]:
        if it["kind"] == "DEDUP":
            print("  #%d %s DEDUP book=%s key=%s keep=L%d drop=L%s  "
                  "md5 %s→%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["book"], it["key"], it["keep_line"],
                     ",".join("L%d" % n for n in it["drop_lines"]),
                     it["md5_before"][:8], it["md5_after"][:8]))
        elif it["kind"] == "ORPHAN-ADD":
            print("  #%d %s ORPHAN-ADD book=%s key=%s row=%s ->L%d  "
                  "md5 %s->%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["book"], it["key"], it["row"],
                     it["line_no"], it["md5_before"][:8],
                     it["md5_after"][:8]))
        else:
            rws = it["rewrites"]
            print("  #%d %s REANCHOR key=%s %s→%s（实件 %s·重写 %d 行）  "
                  "md5 %s→%s"
                  % (it["no"], "APPLIED" if rep["mode"] == "APPLY"
                     else "DRY-STAGED", it["key"],
                     rws[0]["old_anchor"] if rws else it["old_anchor"],
                     rws[0]["new_anchor"] if rws else "(已正典)",
                     it["entity"], len(rws),
                     it["md5_before"][:8], it["md5_after"][:8]))
    print("--- skip 清单（%d 条·如实直传） ---" % len(rep["skip"]))
    for s in rep["skip"]:
        if s["kind"] == "REANCHOR-SKIP-MISSING-ENTITY":
            print("  %s %s: %s" % (s["kind"], s["key"], s["reason"]))
        elif s["kind"] == "ORPHAN-ADD-SKIP-NON-MECHANICAL":
            print("  %s %s（%s）: template=%s"
                  % (s["kind"], s["key"], s.get("direction") or "-",
                     s.get("template")))
        elif s["kind"] == "ORPHAN-ADD-SKIP-SUFFIX-TWIN":
            print("  %s %s (twin %s): template=%s"
                  % (s["kind"], s["key"], s.get("twin_key") or "-",
                     s.get("template")))
        elif s["kind"] == "ORPHAN-ADD-SKIP-KEY-PRESENT":
            print("  %s %s (present L%s): template=%s"
                  % (s["kind"], s["key"],
                     ",".join(str(x) for x in s.get("present_lines") or []),
                     s.get("template")))
        elif s["kind"] == "UNRESOLVABLE-PASSTHROUGH":
            print("  %s 锚 %s L%s: %s"
                  % (s["kind"], s.get("anchor"),
                     ",".join(str(x) for x in (s.get("lines") or [])),
                     s.get("note") or ""))
        elif s["kind"] == "ANCHOR-MISSING-SKIP":
            print("  %s %s L%s: %s"
                  % (s["kind"], s.get("key"),
                     ",".join(str(x) for x in (s.get("lines") or [])),
                     s.get("reason") or ""))
        else:
            print("  %s %s: %s" % (s["kind"], s.get("key"),
                                   s.get("reason") or ""))
    if rep["writes"] is not None:
        wr = rep["writes"]
        print("--- 写面（%d 册%s） ---"
              % (len(wr.get("books") or []),
                 "·已回滚" if wr.get("rolled_back") else ""))
        for w in wr.get("books") or []:
            print("  %s %s rows %d→%d md5 %s→%s（备份 %s）"
                  % (w["book"], w["path"], w["rows_before"], w["rows_after"],
                     w["md5_on_disk_before"][:8], w["md5_on_disk_after"][:8],
                     w["backup"]))
    else:
        print("--- 写面: 零写盘（干跑／staging 炸未落刀） ---")
    an = rep["assertions"]
    if an is None:
        print("--- 断言: NOT-RUN（%s） ---"
              % ("干跑零写盘·断言不适用——push_gate NOT-RUN 同律"
                 if rep["mode"] == "DRY-RUN" else
                 "staging 炸未落盘·断言未至"))
    elif an.get("ran"):
        print("--- 断言（重跑 registry_audit 同参） ---")
        print("  treated_duplicates_zero=PASS anchor_text_no_new_dups=PASS "
              "orphans_no_new=PASS")
        if an.get("orphans_resolved"):
            print("  orphans_resolved=%s orphan_add_duplicates_zero=%s"
                  % (an["orphans_resolved"],
                     an["orphan_add_duplicates_zero"]))
        if an.get("treated_anchors_canonical"):
            print("  treated_anchors_canonical=%s"
                  % an["treated_anchors_canonical"])
    else:
        print("--- 断言: NOT-RUN（%s） ---" % an.get("reason"))
    bl = rep["blast"]
    if bl:
        print("BLAST %s（%s·rc=2）：" % (bl.get("code"), bl.get("phase")))
        for it in bl.get("items") or []:
            print("  - %s" % it)
    summ = rep["summary"]
    print("REGISTRY-FIX: executed=%d skipped=%d books_touched=%s "
          "rolled_back=%s assertions=%s"
          % (summ["items_executed"], summ["skips_total"],
             ",".join(summ["books_touched"]) or "-", summ["rolled_back"],
             summ["assertions"]))


# ---------- 主流程 ----------

def run_fix(args):
    """主流程 → (report, exit_code)。AssertBlast 已收拢（回滚已做·证据入 report）。"""
    audit_payload = load_audit_payload(args.audit_json)
    if args.anchor_src is not None and not os.path.isdir(args.anchor_src):
        raise _ru.MissingInput("--anchor-src 目录缺失: %s" % args.anchor_src)
    books = {"order": BookState(args.order, "order"),
             "coqproject": BookState(args.project, "coqproject")}
    plan = validate_audit(audit_payload, args)  # 同参纪律后置（缺册 9 先于同参破 2）
    if args.apply:
        if not os.path.isfile(args.audit_tool):
            raise _ru.MissingInput("audit 器缺失: %s" % args.audit_tool)

    items, skips = [], []
    writes = None
    assertions = None
    executed_orphan_keys = set()
    try:
        stage_dedup(plan, books, items)
        stage_reanchor(plan, books, items, skips, args.anchor_src)
        if args.orphan_add:
            residual_orphans = stage_orphan_add(plan, books, items, skips)
            executed_orphan_keys = {
                it["key"] for it in items if it["kind"] == "ORPHAN-ADD"}
            stage_nons(dict(plan, orphan=residual_orphans), audit_payload,
                       skips)
        else:
            stage_nons(plan, audit_payload, skips)
    except _ru.AssertBlast as e:
        blast = {"code": e.code, "phase": "stage（零写盘·册面零触碰）",
                 "items": list(e.items)}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              None, None, blast)
        print("ASSERT-BLAST %s（staging·exit 2·零写盘）：" % e.code,
              file=sys.stderr)
        for it in e.items:
            print("  - %s" % it, file=sys.stderr)
        return report, 2

    if not args.apply:
        report = build_report(args, audit_payload, plan, books, items, skips,
                              None,
                              {"ran": False,
                               "reason": "dry-run 零写盘·断言不适用（--apply 后"
                                         "重跑同参方判）"},
                              None)
        return report, 0

    work_dir = args.work_dir or tempfile.mkdtemp(prefix="rocqwash_rf_")
    treated = {(it["book"], it["key"]) for it in items if it["kind"] == "DEDUP"}
    try:
        writes = {"books": backup_and_write(books, work_dir),
                  "rolled_back": False}
        if os.environ.get(INJECT_ENV, "").strip() == "post-write":
            raise _ru.AssertBlast(
                "INJECTED-POST-WRITE-BLAST",
                ["人工炸点注入（%s=post-write·selftest 专用·真跑勿设）"
                 % INJECT_ENV])
        assertions = run_assertions(audit_payload, books, treated, args,
                                    args.audit_tool, work_dir)
        # A-fix-6: executed reanchor keys leave no residual anchor findings
        # (same post_audit.json the assertion face just re-ran)
        executed_anchor_keys = {it["key"] for it in items
                                if it["kind"] == "REANCHOR"}
        if executed_anchor_keys:
            with io.open(os.path.join(work_dir, "post_audit.json"),
                         encoding="utf-8") as fh:
                assertions.update(assert_treated_anchors_canonical(
                    json.load(fh), executed_anchor_keys))
        if executed_orphan_keys:
            assertions.update(assert_orphan_add_resolved(
                os.path.join(work_dir, "post_audit.json"),
                executed_orphan_keys))
    except _ru.AssertBlast as e:
        ev = rollback(writes["books"]) if writes["books"] else {
            "backups": {}, "restored": {}, "all_restored": True}
        writes["rolled_back"] = True
        blast = {"code": e.code, "phase": "apply（已落盘→已回滚）",
                 "items": list(e.items)}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              writes,
                              {"ran": False,
                               "reason": "断言炸·回滚后不出 PASS（%s）" % e.code},
                              blast)
        report["rollback_evidence"] = ev
        print("ASSERT-BLAST %s（exit 2·已回滚）：" % e.code, file=sys.stderr)
        for it in e.items:
            print("  - %s" % it, file=sys.stderr)
        print("rollback: %s（all_restored=%s）"
              % (sorted(ev["backups"]), ev["all_restored"]), file=sys.stderr)
        return report, 2
    except OSError as e:
        ev = rollback(writes["books"]) if writes["books"] else {
            "backups": {}, "restored": {}, "all_restored": True}
        writes["rolled_back"] = True
        blast = {"code": "IO-BLAST", "phase": "apply（已落盘→已回滚）",
                 "items": ["OSError: %s" % e]}
        report = build_report(args, audit_payload, plan, books, items, skips,
                              writes,
                              {"ran": False,
                               "reason": "IO 炸·回滚后不出 PASS"},
                              blast)
        report["rollback_evidence"] = ev
        print("ASSERT-BLAST IO-BLAST（exit 2·已回滚）: %s" % e, file=sys.stderr)
        return report, 2

    report = build_report(args, audit_payload, plan, books, items, skips,
                          writes, assertions, None)
    return report, 0


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="注册册处方执行器：registry_audit fix-plan 逐条落刀"
                    "（DEDUP 保首/锚刷引擎直用/孤儿 skip 直传）＋断言三判＋"
                    "炸即回滚（缺省干跑·--apply 才写）")
    ap.add_argument("--audit-json", default=None, metavar="FILE",
                    help="registry_audit 产出（rocqwash-registry-audit/1·"
                         "须 --fix-plan 产出）")
    ap.add_argument("--order", default=None, metavar="PATH",
                    help="order.txt 册（与 --project 成对·须与 audit 同参）")
    ap.add_argument("--project", default=None, metavar="PATH",
                    help="_CoqProject 册（与 --order 成对·须与 audit 同参）")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="锚刷 md5 实件源目录（缺件键留原样列 skip）")
    ap.add_argument("--apply", action="store_true",
                    help="允许落刀（缺省干跑零写盘·写前 tmp 备份·炸即回滚）")
    ap.add_argument("--orphan-add", action="store_true",
                    help="execute the mechanically solvable ORPHAN-ADD "
                         "prescriptions (order-only direction: append the "
                         "template row to the coqproject book); default off "
                         "keeps every ORPHAN-ADD prescription on the skip "
                         "list (frozen legacy behavior)")
    ap.add_argument("--work-dir", default=None, metavar="DIR",
                    help="备份/重跑审计出账目录（--apply 用·缺省 mkdtemp）")
    ap.add_argument("--audit-tool", default=None, metavar="PATH",
                    help="registry_audit.py 路径（缺省同侪 tools/）")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="report 出账（schema rocqwash-registry-fix/1·炸时"
                         "亦出＝回滚证据）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    def die(msg, code):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(code)

    if not args.audit_json:
        die("无输入面：--audit-json 必给（registry_audit --fix-plan 产出）", 2)
    if (args.order is None) != (args.project is None):
        die("--order 与 --project 须成对（双册口径·缺一不可）", 2)
    if not args.order:
        die("无输入面：--order＋--project 双册必给", 2)
    args.audit_tool = args.audit_tool or os.path.join(
        _TOOLS_DIR, "registry_audit.py")

    try:
        report, code = run_fix(args)
    except _ru.MissingInput as e:
        die(str(e), 9)
    except FailLoud as e:
        die(str(e), 2)
    except _ru.UsageError as e:
        die("引擎用法炸: %s" % e, 2)

    print_stdout(report)
    if args.json:
        try:
            dump_json(args.json, report)
            print("json -> %s" % args.json)
        except OSError as e:
            die("--json 出账写盘失败: %s" % e, 2)
    sys.exit(code)


# ---------- 自证 ----------

FIXTURE_ORDER = [
    "ToyA.v#R3-ffffff",        # L1  形怪 6 位签 → 锚刷（实体=冻结向量 77c2b9a8）
    "SeqB.v#R7",               # L2  顺序号形 → 锚刷（实体在）
    "Ghost.v#R9-abcabc",       # L3  形怪·缺实件 → skip 清单
    "NoEnt.v#R11",             # L4  顺序号形·缺实件 → skip 清单
    "CollA.v#R0-d66910",       # L5  形怪·撞锚（v35 判例形）→ 锚刷解消
    "CollB.v#R0-d66910",       # L6  形怪·撞锚 → 锚刷解消（异内容）
    "MissAnchor.v",            # L7  缺锚 → skip 清单（非机械）
    "CanA.v#R0-11111111",      # L8  正典撞锚 → unresolvable 直传
    "CanB.v#R0-11111111",      # L9  正典撞锚 → unresolvable 直传
    "OrphO.v#R5-aaaa0001",     # L10 孤儿（order-only）→ ORPHAN-ADD skip
    "# 注释行",                # L11 注释（键 None 不入账）
] + ["M%02d.v#R21-aaaa%04x" % (i, i) for i in range(1, 13)]  # L12-L23

FIXTURE_PROJECT_HEAD = [
    '-Q . ""',                 # L1  旗标行（滤除）
    "ToyA.v", "SeqB.v", "Ghost.v", "NoEnt.v", "CollA.v", "CollB.v",
    "MissAnchor.v", "CanA.v", "CanB.v", "OrphP.v",     # L2-L11（OrphP 孤儿）
]
FIXTURE_PROJECT_DUP = ["M%02d.v" % i for i in range(1, 13)]  # 12 逐字重复块


def build_fixture(base, shared=False):
    """v46 audit demo 形态样张夹具（world 实体＋双册·零触真仓零网络）。

    shared=True 增 SameC/SameD（同内容双键·异形怪锚）＝A-fix-2 自然炸点专用。
    返回 (order_path, project_path, world_dir)。
    """
    world = os.path.join(base, "world")
    os.makedirs(world)
    ents = {"ToyA.v": "module A content alpha\n",   # registry_union 冻结向量
            "SeqB.v": "module SeqB beta\n",
            "CollA.v": "module CollA one\n",
            "CollB.v": "module CollB two\n",
            "OrphP.v": "module OrphP\n"}
    if shared:
        ents["SameC.v"] = "module Same shared\n"
        ents["SameD.v"] = "module Same shared\n"   # 同内容＝重锚新撞炸点
    for name in sorted(ents):
        with io.open(os.path.join(world, name), "wb") as fh:
            fh.write(ents[name].encode("utf-8"))
    order_rows = list(FIXTURE_ORDER)
    project_rows = list(FIXTURE_PROJECT_HEAD) + FIXTURE_PROJECT_DUP * 2
    if shared:
        order_rows += ["SameC.v#R0-aaaaaa", "SameD.v#R0-bbbbbb"]
        project_rows += ["SameC.v", "SameD.v"]
    order_path = os.path.join(base, "order.txt")
    project_path = os.path.join(base, "_CoqProject")
    with io.open(order_path, "wb") as fh:
        fh.write(("\n".join(order_rows) + "\n").encode("utf-8"))
    with io.open(project_path, "wb") as fh:
        fh.write(("\n".join(project_rows) + "\n").encode("utf-8"))
    return order_path, project_path, world


def selftest():
    """内嵌矢量组（tmp fixture·v46 audit demo 形态样张·零触真仓零网络零编译）：

    1 干跑零写盘＋逐条 md5 账＋skip 清单全谱＋干跑 report 重跑字节恒同
    2 --apply：DEDUP 12 重复块→0＋断言三过＋md5 账对盘面复核
    3 锚刷 md5 冻结向量 77c2b9a8＋同输同出（registry_union CLI 逐字节对拍）
    4 回滚实证·人工炸点注入（post-write→已还原）
    5 自然炸点（同内容重锚新撞→A3 引擎同码→已回滚）
    6 staging 炸（audit↔册漂移·零写盘·work-dir 不建）
    7 CLI 四码＋schema 面
    8 落刀确定性（双 fresh 夹具册面 bytes/md5 账恒同）
    """
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    fix_py = os.path.join(here, PROG + ".py")
    audit_py = os.path.join(here, "registry_audit.py")
    union_py = os.path.join(here, "registry_union.py")

    def run(argv, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        p = subprocess.run([sys.executable, "-B", fix_py] + argv,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=env)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def run_audit(order_p, project_p, world, json_p, fix_plan=True):
        argv = [sys.executable, "-B", audit_py, "--order", order_p,
                "--project", project_p, "--anchor-src", world,
                "--json", json_p]
        if fix_plan:
            argv.append("--fix-plan")
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        assert p.returncode == 0, "audit 出账应 rc=0 实测 %d\n%s" % (
            p.returncode, p.stdout)
        with io.open(json_p, encoding="utf-8") as fh:
            return json.load(fh)

    def wf(path, text):
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    def md5_of(path):
        return md5_file(path)

    def tree_md5(root):
        """目录树内容指纹（零写盘旁证·文件名+md5 序列）。"""
        rows = []
        for dirpath, _dirs, fnames in os.walk(root):
            for fn in sorted(fnames):
                p = os.path.join(dirpath, fn)
                rows.append((os.path.relpath(p, root), md5_of(p)))
        return sorted(rows)

    tmp = tempfile.mkdtemp(prefix="rocqwash_rf_self_")
    try:
        # 冻结向量守卫（引擎 md5 基先验：registry_union 冻结样张内容→77c2b9a8）
        d0 = os.path.join(tmp, "vec0")
        os.makedirs(d0)
        wf(os.path.join(d0, "ToyA.v"), "module A content alpha\n")
        assert _ru.md5_8_of(os.path.join(d0, "ToyA.v")) == "77c2b9a8", \
            "registry_union 冻结向量破（内容→md5-8）"

        # ---- 矢量 1：干跑零写盘＋逐条 md5 账＋skip 清单全谱＋确定性 ----
        d1 = os.path.join(tmp, "vec1")
        os.makedirs(d1)
        o1, p1, w1 = build_fixture(d1)
        a1 = run_audit(o1, p1, w1, os.path.join(d1, "audit.json"))
        pre_tree = tree_md5(d1)  # 零写盘基线（audit 出账后取·含 audit.json）
        assert a1["summary"]["duplicates"] == 12, a1["summary"]
        assert a1["summary"]["anchors"] == 9, a1["summary"]
        assert a1["summary"]["orphans"] == 2, a1["summary"]
        assert a1["summary"]["total"] == 23, a1["summary"]
        r1 = os.path.join(tmp, "rep1.json")
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1, "--anchor-src", w1,
                 "--json", r1])
        assert p.returncode == 0, "干跑应 rc=0 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert tree_md5(d1) == pre_tree, "干跑写盘＝违例（夹具树漂移）"
        rep1 = json.load(io.open(r1, encoding="utf-8"))
        assert rep1["schema"] == SCHEMA, rep1["schema"]
        assert rep1["mode"] == "DRY-RUN", rep1["mode"]
        assert rep1["writes"] is None, rep1["writes"]
        assert rep1["assertions"]["ran"] is False, rep1["assertions"]
        assert rep1["stats"]["items_total"] == 16, rep1["stats"]  # 12+4
        kinds = {s["kind"] for s in rep1["skip"]}
        assert kinds == {"REANCHOR-SKIP-MISSING-ENTITY",
                         "ORPHAN-ADD-SKIP-NON-MECHANICAL",
                         "UNRESOLVABLE-PASSTHROUGH",
                         "ANCHOR-MISSING-SKIP"}, rep1["skip"]
        assert len(rep1["skip"]) == 6, rep1["skip"]  # 2+2+1+1
        assert rep1["items"][0]["kind"] == "DEDUP" \
            and rep1["items"][0]["book"] == "coqproject" \
            and rep1["items"][0]["keep_line"] == 12 \
            and rep1["items"][0]["drop_lines"] == [24], rep1["items"][0]
        # 锚刷靶：ToyA 占位 audit md5 已实解（77c2b9a8）·Ghost 缺实件 skip
        ra = {it["key"]: it for it in rep1["items"] if it["kind"] == "REANCHOR"}
        assert set(ra) == {"ToyA.v", "SeqB.v", "CollA.v", "CollB.v"}, \
            sorted(ra)
        assert ra["ToyA.v"]["md5_8"] == "77c2b9a8", ra["ToyA.v"]
        # 干跑确定性：重跑 report 逐字节恒同
        r1b = os.path.join(tmp, "rep1b.json")
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1, "--anchor-src", w1,
                 "--json", r1b])
        assert p.returncode == 0, p.stdout
        assert io.open(r1b, "rb").read() == io.open(r1, "rb").read(), \
            "干跑 report 字节漂移＝违例"
        print("  [1/8] 干跑零写盘 OK（夹具树恒同·items=16 skip=6 全谱·"
              "ToyA md5=77c2b9a8·report 重跑字节恒同）")

        # ---- 矢量 2：--apply·DEDUP 12 重复块→0＋断言三过＋账对盘 ----
        d2 = os.path.join(tmp, "vec2")
        os.makedirs(d2)
        o2, p2, w2 = build_fixture(d2)
        run_audit(o2, p2, w2, os.path.join(d2, "audit.json"))
        wd2 = os.path.join(d2, "work")
        r2 = os.path.join(d2, "rep.json")
        p = run(["--audit-json", os.path.join(d2, "audit.json"),
                 "--order", o2, "--project", p2, "--anchor-src", w2,
                 "--apply", "--work-dir", wd2, "--json", r2])
        assert p.returncode == 0, "--apply 应 rc=0 实测 %d\n%s" % (
            p.returncode, p.stdout)
        rep2 = json.load(io.open(r2, encoding="utf-8"))
        assert rep2["mode"] == "APPLY", rep2["mode"]
        assert rep2["assertions"]["ran"] is True \
            and rep2["assertions"]["treated_duplicates_zero"] == "PASS" \
            and rep2["assertions"]["anchor_text_no_new_dups"] == "PASS" \
            and rep2["assertions"]["orphans_no_new"] == "PASS" \
            and rep2["assertions"]["treated_anchors_canonical"] == "PASS", \
            rep2["assertions"]
        assert rep2["summary"]["books_touched"] == ["coqproject", "order"], \
            rep2["summary"]
        wr = {w["book"]: w for w in rep2["writes"]["books"]}
        assert wr["coqproject"]["rows_before"] == 35 \
            and wr["coqproject"]["rows_after"] == 23, wr["coqproject"]
        assert wr["order"]["rows_before"] == 23 \
            and wr["order"]["rows_after"] == 23, wr["order"]
        # 账对盘：末条 per-book md5_after ≡ 盘面 md5（clean 夹具 render faithful）
        for label, path in (("coqproject", p2), ("order", o2)):
            last = [it for it in rep2["items"] if it["book"] == label][-1]
            assert last["md5_after"] == wr[label]["md5_on_disk_after"] \
                == md5_of(path), (label, last, wr[label])
        assert rep2["writes"]["rolled_back"] is False, rep2["writes"]
        assert os.path.isfile(wr["order"]["backup"]), "备份证据应在卷"
        # 重跑独立审计实证：duplicates=0·被治 12 键零残留
        post = run_audit(o2, p2, w2, os.path.join(d2, "post_check.json"),
                         fix_plan=False)
        assert post["summary"]["duplicates"] == 0, post["summary"]
        assert post["summary"]["orphans"] == 2, post["summary"]
        print("  [2/8] --apply OK（12 重复块→0·断言三过·md5 账≡盘面·"
              "重跑审计 duplicates=0 orphans=2 恒）")

        # ---- 矢量 3：锚刷 md5 冻结向量＋同输同出（registry_union CLI 对拍） ----
        seqb_md5 = _ru.md5_8_of(os.path.join(w2, "SeqB.v"))
        colla_md5 = _ru.md5_8_of(os.path.join(w2, "CollA.v"))
        collb_md5 = _ru.md5_8_of(os.path.join(w2, "CollB.v"))
        with io.open(o2, encoding="utf-8") as fh:
            got = [ln.strip() for ln in fh.read().split("\n") if ln.strip()]
        assert got[0] == "ToyA.v#R3-77c2b9a8", got[0]     # 冻结向量正典形
        assert got[1] == "SeqB.v#R7-%s" % seqb_md5, got[1]
        assert got[4] == "CollA.v#R0-%s" % colla_md5, got[4]
        assert got[5] == "CollB.v#R0-%s" % collb_md5, got[5]
        assert got[2] == "Ghost.v#R9-abcabc" \
            and got[3] == "NoEnt.v#R11", "缺实件键须留原样"
        # 同输同出：registry_union CLI 同参（三面同册＋同名清单）→ 逐字节恒同
        d3 = os.path.join(tmp, "vec3")
        os.makedirs(d3)
        o3, p3, w3 = build_fixture(d3)
        pre_o3 = wf(os.path.join(d3, "pre_order.txt"),
                    io.open(o3, "rb").read().decode("utf-8"))
        run_audit(o3, p3, w3, os.path.join(d3, "audit.json"))
        r3 = os.path.join(d3, "rep.json")
        p = run(["--audit-json", os.path.join(d3, "audit.json"),
                 "--order", o3, "--project", p3, "--anchor-src", w3,
                 "--apply", "--work-dir", os.path.join(d3, "work"),
                 "--json", r3])
        assert p.returncode == 0, p.stdout
        u3 = os.path.join(d3, "union_out.txt")
        pu = subprocess.run(
            [sys.executable, "-B", union_py,
             "--main", pre_o3, "--base", pre_o3, "--branch", pre_o3,
             "--kind", "order",
             "--reanchor", "CollA,CollB,Ghost,ToyA,NoEnt,SeqB",
             "--anchor-src", w3, "--out", u3, "--apply"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert pu.returncode == 0, pu.stdout.decode("utf-8", errors="replace")
        assert io.open(u3, "rb").read() == io.open(o3, "rb").read(), \
            "同输同出违例：registry_union CLI 产物 ≠ 本器落刀册"
        print("  [3/8] 锚刷向量 OK（ToyA→77c2b9a8 冻结·SeqB/CollA/CollB 实件"
              "重算·缺件留原样·registry_union 同输同出逐字节恒同）")

        # ---- 矢量 4：回滚实证·人工炸点注入（post-write→已还原） ----
        d4 = os.path.join(tmp, "vec4")
        os.makedirs(d4)
        o4, p4, w4 = build_fixture(d4)
        run_audit(o4, p4, w4, os.path.join(d4, "audit.json"))
        pre4 = (md5_of(o4), md5_of(p4))
        wd4 = os.path.join(d4, "work")
        r4 = os.path.join(d4, "rep.json")
        p = run(["--audit-json", os.path.join(d4, "audit.json"),
                 "--order", o4, "--project", p4, "--anchor-src", w4,
                 "--apply", "--work-dir", wd4, "--json", r4],
                env_extra={INJECT_ENV: "post-write"})
        assert p.returncode == 2, "注入炸应 rc=2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert "INJECTED-POST-WRITE-BLAST" in p.stdout, p.stdout[-400:]
        assert (md5_of(o4), md5_of(p4)) == pre4, "回滚违例：册面未逐字节还原"
        rep4 = json.load(io.open(r4, encoding="utf-8"))
        assert rep4["writes"]["rolled_back"] is True, rep4["writes"]
        assert rep4["rollback_evidence"]["all_restored"] is True, \
            rep4["rollback_evidence"]
        for w in rep4["writes"]["books"]:
            assert os.path.isfile(w["backup"]), w
            assert rep4["rollback_evidence"]["restored"][w["book"]]["match"] \
                is True, rep4["rollback_evidence"]
        print("  [4/8] 回滚实证 OK（人工炸点 post-write→rc2·册面逐字节还原"
              "·备份与还原 md5 证据入 report）")

        # ---- 矢量 5：自然炸点（同内容重锚→A-fix-2 新撞→A3 引擎同码） ----
        d5 = os.path.join(tmp, "vec5")
        os.makedirs(d5)
        o5, p5, w5 = build_fixture(d5, shared=True)
        a5 = run_audit(o5, p5, w5, os.path.join(d5, "audit.json"))
        assert a5["summary"]["duplicates"] == 12 \
            and a5["summary"]["anchors"] == 11, a5["summary"]  # +2 形怪+1 撞
        pre5 = (md5_of(o5), md5_of(p5))
        r5 = os.path.join(d5, "rep.json")
        p = run(["--audit-json", os.path.join(d5, "audit.json"),
                 "--order", o5, "--project", p5, "--anchor-src", w5,
                 "--apply", "--work-dir", os.path.join(d5, "work"),
                 "--json", r5])
        assert p.returncode == 2, "A-fix-2 自然炸应 rc=2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert "A3-ANCHOR-TEXT-NEW-DUP" in p.stdout, p.stdout[-400:]
        assert (md5_of(o5), md5_of(p5)) == pre5, "回滚违例（自然炸点）"
        rep5 = json.load(io.open(r5, encoding="utf-8"))
        assert rep5["writes"]["rolled_back"] is True, rep5["writes"]
        assert rep5["blast"]["code"] == "A3-ANCHOR-TEXT-NEW-DUP", rep5["blast"]
        print("  [5/8] 自然炸点 OK（同内容双键重锚新撞→A3-ANCHOR-TEXT-NEW-DUP"
              "·rc2·回滚还原）")

        # ---- 矢量 6：staging 炸（audit↔册漂移·零写盘·work-dir 不建） ----
        d6 = os.path.join(tmp, "vec6")
        os.makedirs(d6)
        o6, p6, w6 = build_fixture(d6)
        run_audit(o6, p6, w6, os.path.join(d6, "audit.json"))
        wf(p6, 'ZZZ.v#R9-99999999\n' + io.open(p6, "rb").read()
            .decode("utf-8"))  # 册顶插行→keep=L12 键漂移
        pre6 = (md5_of(o6), md5_of(p6))
        wd6 = os.path.join(d6, "work")
        r6 = os.path.join(d6, "rep.json")
        p = run(["--audit-json", os.path.join(d6, "audit.json"),
                 "--order", o6, "--project", p6, "--anchor-src", w6,
                 "--apply", "--work-dir", wd6, "--json", r6])
        assert p.returncode == 2, "staging 炸应 rc=2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert "DEDUP-KEEP-KEY-MISMATCH" in p.stdout, p.stdout[-400:]
        assert (md5_of(o6), md5_of(p6)) == pre6, "staging 炸不得触册面"
        assert not os.path.exists(wd6), "staging 炸 work-dir 不应建（零写盘）"
        rep6 = json.load(io.open(r6, encoding="utf-8"))
        assert rep6["writes"] is None and rep6["blast"]["code"] \
            == "DEDUP-KEEP-KEY-MISMATCH", rep6
        print("  [6/8] staging 炸 OK（audit↔册漂移→DEDUP-KEEP-KEY-MISMATCH"
              "·零写盘·work-dir 不建）")

        # ---- 矢量 7：CLI 四码＋schema 面 ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "无输入应 rc=2 实测 %d" % p.returncode
        p = run(["--audit-json", os.path.join(tmp, "nope.json"),
                 "--order", o1, "--project", p1])
        assert p.returncode == 9, "缺 audit-json 应 rc=9 实测 %d" % p.returncode
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", os.path.join(tmp, "nope.txt"), "--project", p1])
        assert p.returncode == 9, "缺册应 rc=9 实测 %d" % p.returncode
        bad = wf(os.path.join(tmp, "badschema.json"),
                 json.dumps({"schema": "bogus/9"}))
        p = run(["--audit-json", bad, "--order", o1, "--project", p1])
        assert p.returncode == 2, "坏 schema 应 rc=2 实测 %d" % p.returncode
        nofp = os.path.join(tmp, "nofix.json")
        run_audit(o1, p1, w1, nofp, fix_plan=False)
        p = run(["--audit-json", nofp, "--order", o1, "--project", p1])
        assert p.returncode == 2, "无 fix_plan 应 rc=2 实测 %d" % p.returncode
        d7 = os.path.join(tmp, "vec7")
        os.makedirs(d7)
        o7, p7, w7 = build_fixture(d7)
        a7 = run_audit(o7, p7, w7, os.path.join(d7, "audit.json"))
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o7, "--project", p7])   # 异册同参破
        assert p.returncode == 2, "同参破应 rc=2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        p = run(["--audit-json", os.path.join(d1, "audit.json"),
                 "--order", o1, "--project", p1,
                 "--anchor-src", os.path.join(tmp, "noworld")])
        assert p.returncode == 9, "缺 anchor-src 目录应 rc=9 实测 %d" % (
            p.returncode)
        print("  [7/8] CLI 四码 OK（help0/bogus2/无输入2/缺audit9/缺册9/"
              "坏schema2/无fix_plan2/同参破2/缺anchor-src9）")

        # ---- 矢量 8：落刀确定性（双 fresh 夹具同处→册面/账恒同） ----
        outs = []
        for tag in ("a", "b"):
            d8 = os.path.join(tmp, "vec8" + tag)
            os.makedirs(d8)
            o8, p8, w8 = build_fixture(d8)
            run_audit(o8, p8, w8, os.path.join(d8, "audit.json"))
            r8 = os.path.join(d8, "rep.json")
            p = run(["--audit-json", os.path.join(d8, "audit.json"),
                     "--order", o8, "--project", p8, "--anchor-src", w8,
                     "--apply", "--work-dir", os.path.join(d8, "work"),
                     "--json", r8])
            assert p.returncode == 0, p.stdout
            with io.open(r8, encoding="utf-8") as fh:
                items8 = json.load(fh)["items"]
            outs.append((io.open(o8, "rb").read(),
                         io.open(p8, "rb").read(),
                         [(it["kind"], it["key"], it["md5_before"],
                           it["md5_after"]) for it in items8]))
        assert outs[0][0] == outs[1][0] and outs[0][1] == outs[1][1], \
            "落刀册面字节漂移＝违例"
        assert outs[0][2] == outs[1][2], "逐条 md5 账漂移＝违例"
        print("  [8/8] 落刀确定性 OK（双 fresh 夹具→册面 bytes＋逐条 md5 账"
              "恒同）")

        print("REGISTRY-FIX-SELFTEST PASS: 干跑零写盘/12重复块→0+断言三过/"
              "77c2b9a8同输同出/注入回滚/自然炸回滚/staging零写盘/CLI四码/"
              "落刀确定性 八判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
