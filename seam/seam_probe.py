#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seam_probe.py — 代际缝探针：W13 四机制指纹自动归类（rocqwash seam/·20261031 席 rqwash）

README「W13 Seam Mechanisms」四机制的 grep 指纹落地：对单件 .v 做语句/证明体分段
（注释/字符串掩蔽后），逐机制出「指纹命中清单＋处方映射」——机械报候选，不出定谳：

  W13-① ==语句 × rewrite/ring/reflexivity：语句面含裸 ==（implyM 守卫
          (?<![=<>])==(?!>)·承 scan/mac_stmt_scan.py CH_P2 冻结口径）且其证明体
          出现 rewrite/ring./reflexivity. → 处方：先 qeq_imp_qeqT 回向（Qeq→QeqT）。
  W13-② 键配实例化：证明体 apply (/rewrite ( 全应用形 → 处方：供给侧参数须取
          目标实形（键配 · not 命名猜测）。
  W13-③ 载前件引理消费：rewrite <name> 的 <name> 解析到本文件语句且其类型位
          （depth-0 冒号后）含 -> → 处方：assert-化＋双岸桥。
  W13-④ 跨行 Require 拓扑漏：(a) Require 语句跨行（语句级多行感知）；
          (b) 语句面出现 Mod.name 限定名而 Mod 不在本文件 Require 集
          （PRELUDE_MODS 冻结豁免册除外）→ 处方：驱动幂等续跑＋拓扑补列。

E364 盲区律（报清单不报清白）：命中＝代际缝**候选**（指纹级证据，非定谳）；
0 命中＝「无候选出账」，永不判「无缝」——判词唯内核判据可出。0 命中须另过
--selftest 内嵌冻结向量组（四机制正例＋掩蔽负例）方可采信探针本身在况。

分段与词面口径承 scan/mac_stmt_scan.py 冻结正典（DECL_RE/stmt_end/
strip_comments_strings 1:1 本地重实现·不 import 冻结件——防冻结件漂移牵连；
等价性由 --selftest 机械背书）。

用法：
  python3 seam/seam_probe.py --file <path.v> [--json out.json] [--hits-csv out.csv] [--selftest]
  cli/rocqwash seam --file <path.v>          # 统一入口自动路由

退出码：0=出账完成（命中是发现不是失败·与 scan 同口径）；2=--selftest 向量失败；
        9=--file 路径缺失。
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys

PROG = "seam_probe"
WB = r"[\w']"

# —— 词面口径（承 scan/mac_stmt_scan.py 冻结正典·1:1 本地重实现）——
DECL_RE = re.compile(
    r"[ \t]*(?:(?:#\[[^\]]*\])[ \t]*(?:\r?\n)?[ \t]*|(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Lemma|Theorem|Definition|Corollary|Fixpoint|CoFixpoint|Proposition|Instance)\b")
PROOF_RE = re.compile(r"[ \t]*Proof\b")
END_RE = re.compile(r"\b(?:Qed|Defined|Admitted|Abort)\b")
CH_P2 = re.compile(r"(?<![=<>])==(?!>)")          # implyM 守卫
CH_ARROW = re.compile(r"->")
CH_APPLY_FULL = re.compile(r"\b(apply|rewrite)\s+\(")
CH_REWRITE_NAME = re.compile(r"\brewrite\s+((?:<-|->)\s*)?[({]?\s*([A-Za-z_][A-Za-z0-9_']*)")
CH_QUALIFIED = re.compile(r"(?<![\w'])([A-Za-z_][A-Za-z0-9_']*)\.([A-Za-z_][A-Za-z0-9_']*)")
CH_REQUIRE = re.compile(
    r"\bRequire\b(?:\s+(?:Import|Export))*\s+([A-Za-z_][A-Za-z0-9_'., \t\n]*)")

# W13-④ 前奏豁免册（冻结·不在 Require 集也不报；prologue 命名空间从宽）
PRELUDE_MODS = ("Coq", "Init", "Datatypes", "Logic", "Specif", "Nat", "Peano",
                "Decimal", "Hexadecimal", "Number", "Bool", "Ordinals")

LANES = ("W13-1_qeq_backflip", "W13-2_keyed_instantiation",
         "W13-3_premiss_lemma", "W13-4_require_topology")

PRESCRIPTION = {
    "W13-1_qeq_backflip": "先 qeq_imp_qeqT 回向（Qeq→QeqT）再上 rewrite/ring/reflexivity",
    "W13-2_keyed_instantiation": "键配实例化：供给侧参数须取目标实形",
    "W13-3_premiss_lemma": "载前件引理消费：assert-化＋双岸桥",
    "W13-4_require_topology": "跨行 Require 拓扑漏：语句级多行感知＋驱动幂等续跑（补列 Require）",
}


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_comments_strings(text):
    """状态机剥嵌套注释与字符串字面量；被剥区域替换为空格保持行号（E364 T8/T3）。

    1:1 冻结继承 scan/mac_stmt_scan.py:104-125；本地重实现不 import。
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1; out.append("  "); i += 2; continue
            if text.startswith("*)", i):
                depth -= 1; out.append("  "); i += 2; continue
            out.append(c if c == "\n" else " "); i += 1; continue
        if text.startswith("(*", i):
            depth = 1; out.append("  "); i += 2; continue
        if c == '"':
            out.append(" "); i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " "); i += 1
            if i < n: out.append(" "); i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def stmt_end(clean, start_idx):
    """语句终止：行首 Proof. 或边界句号（承 scan/mac_stmt_scan.py:129 形）。"""
    i, n = start_idx, len(clean)
    line_start = True
    while i < n:
        c = clean[i]
        if c == "\n":
            line_start = True; i += 1; continue
        if line_start:
            m = re.match(r"\s*Proof\b", clean[i:i + 200])
            if m:
                return i + m.end(), "Proof"
            line_start = False
        if c == ".":
            prev = clean[i - 1] if i > 0 else " "
            nxt = clean[i + 1] if i + 1 < n else " "
            if prev != "." and (nxt in " \t\r\n" or nxt == ""):
                return i + 1, "Dot"
        i += 1
    return n, "EOF"


def depth0_arrow(s, start, end):
    """[start,end) 内 depth-0（括号感知）首个 ->；无则 -1。"""
    depth = 0
    i = start
    while i < end:
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif depth == 0 and s.startswith("->", i):
            return i
        i += 1
    return -1


def split_statements(clean):
    """掩蔽文分段：[(kind, name, face_s, face_e, body_s, body_e, decl_s)]。"""
    out = []
    decl_end = 0
    for m in DECL_RE.finditer(clean):
        if m.start() < decl_end:
            continue
        kind = m.group(1)
        name_m = re.match(r"\s*[^\s:({[]+\s+([A-Za-z_][A-Za-z0-9_']*)",
                          clean[m.start():m.end() + 300])
        name = name_m.group(1) if name_m else "?"
        fe, how = stmt_end(clean, m.end())
        # 证明体＝语句面终点 → 终结词（Qed/Defined/Admitted/Abort）末，且终结词
        # 须先于下一语句（Proof. 可省·Definition 无证明体则 body=None）。
        qm = END_RE.search(clean, fe)
        nm = DECL_RE.search(clean, fe)
        body_s = body_e = fe
        if qm and (nm is None or qm.end() <= nm.start()):
            body_s, body_e = fe, qm.end()
        else:
            body_s = body_e = None
        out.append(dict(kind=kind, name=name, face_s=m.start(), face_e=fe,
                        body_s=body_s, body_e=body_e, decl_s=m.start()))
        decl_end = fe
    return out


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def probe_file(fp):
    with io.open(fp, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    clean = strip_comments_strings(text)
    stmts = split_statements(clean)
    hits = []

    # 本文件语句表（W13-③ 消费解析用）：name -> 类型位是否含 depth-0 ->
    stmt_types = {}
    for st in stmts:
        # depth-0 冒号（binders 后类型位起点）
        depth = 0
        colon_i = -1
        for i in range(st["face_s"], st["face_e"]):
            c = clean[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == ":" and depth == 0 and clean[i + 1:i + 2] != "=":
                colon_i = i
                break
        has_prem = colon_i >= 0 and depth0_arrow(clean, colon_i, st["face_e"]) >= 0
        stmt_types[st["name"]] = has_prem

    # Require 集（W13-④）：Require 起至下一边界句点段内的模块名（掩蔽文·句号即界）
    requires = set()
    for m in re.finditer(r"\bRequire\b", clean):
        end_m = re.compile(r"\.(?=\s)").search(clean, m.start())
        seg = clean[m.start():end_m.end() if end_m else m.start() + 200]
        names = re.findall(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", seg)
        names = [n for n in names if n != "Require"]
        for n in names:
            requires.add(n.split(".")[0])
            requires.add(n)
        require_spans = (m.start(), end_m.end() if end_m else m.start())
        if end_m and "\n" in clean[require_spans[0]:require_spans[1]]:
            hits.append(dict(lane="W13-4_require_topology", line=line_of(text, m.start()),
                             stmt="(Require)", evidence="Require 语句跨行（%d 行）"
                                   % (1 + clean[m.start():end_m.end()].count("\n")),
                             note="语句级多行感知"))

    for st in stmts:
        face = clean[st["face_s"]:st["face_e"]]
        body = clean[st["body_s"]:st["body_e"]] if st["body_s"] is not None else ""
        line = line_of(text, st["decl_s"])

        # W13-①：== 语句面 × rewrite/ring/reflexivity 证明体
        if CH_P2.search(face):
            ev = []
            if re.search(r"\brewrite\b", body):
                ev.append("rewrite")
            if re.search(r"\bring\s*\.", body):
                ev.append("ring.")
            if re.search(r"\breflexivity\s*\.", body):
                ev.append("reflexivity.")
            if ev:
                hits.append(dict(lane="W13-1_qeq_backflip", line=line,
                                 stmt="%s %s" % (st["kind"], st["name"]),
                                 evidence="语句面裸 == × 证明体 %s" % "·".join(ev),
                                 note="候选非定谳"))

        # W13-②：全应用实例化形
        for m in CH_APPLY_FULL.finditer(body):
            hits.append(dict(lane="W13-2_keyed_instantiation", line=line_of(text, st["body_s"] + m.start()),
                             stmt="%s %s" % (st["kind"], st["name"]),
                             evidence="%s ( 全应用形" % m.group(1),
                             note="候选非定谳"))

        # W13-③：rewrite <name> 消费载前件引理（限本文件语句表）
        for m in CH_REWRITE_NAME.finditer(body):
            nm = m.group(2)
            if stmt_types.get(nm):
                hits.append(dict(lane="W13-3_premiss_lemma", line=line_of(text, st["body_s"] + m.start()),
                                 stmt="%s %s" % (st["kind"], st["name"]),
                                 evidence="rewrite %s × 载前件引理（本文件类型位含 ->）" % nm,
                                 note="候选非定谳"))

        # W13-④b：语句面限定名 Mod.name 且 Mod 不在 Require 集（前奏豁免册除外）
        for m in CH_QUALIFIED.finditer(face):
            mod = m.group(1)
            if mod in PRELUDE_MODS or mod in requires or mod == st["name"]:
                continue
            hits.append(dict(lane="W13-4_require_topology", line=line_of(text, st["face_s"] + m.start()),
                             stmt="%s %s" % (st["kind"], st["name"]),
                             evidence="限定名 %s.%s × Require 集无 %s" % (mod, m.group(2), mod),
                             note="候选非定谳"))

    return {"file": fp, "md5": md5_of(fp), "n_stmts": len(stmts),
            "requires": sorted(requires), "hits": hits}


def print_report(res, hits_csv=None):
    print("== seam_probe W13 四机制指纹账（file=%s·md5=%s）==" % (res["file"], res["md5"]))
    print("语句分段 n=%d·Require 集=%s" % (res["n_stmts"], res["requires"] or "∅"))
    for h in res["hits"]:
        print("  %-26s L%-5d %-22s %s [%s]" % (h["lane"], h["line"], h["stmt"],
                                               h["evidence"], h["note"]))
    per = {lane: sum(1 for h in res["hits"] if h["lane"] == lane) for lane in LANES}
    for lane in LANES:
        print("  %-26s %d 候选 · 处方：%s" % (lane, per[lane], PRESCRIPTION[lane]))
    total = len(res["hits"])
    print("TOTAL: %d 候选" % total)
    if total == 0:
        print("E364 盲区律：0 命中＝无候选出账，非「无缝」判词——判词唯内核判据可出；"
              "采信前须过 --selftest 负证对照。")
    if hits_csv:
        with io.open(hits_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["lane", "line", "stmt", "evidence", "note", "prescription"])
            for h in res["hits"]:
                w.writerow([h["lane"], h["line"], h["stmt"], h["evidence"],
                            h["note"], PRESCRIPTION[h["lane"]]])
        print("hits-csv ->", hits_csv)


def selftest():
    """冻结向量组：四机制各一正例＋掩蔽/前奏负例。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_seam_self_")
    try:
        pos = os.path.join(tmp, "pos.v")
        with io.open(pos, "w", encoding="utf-8", newline="") as fh:
            fh.write(
                "Require Import G10_LoebFam.\n"
                "Lemma m1_eq : forall x y : Q, x == y.\n"
                "Proof.\n"
                "  intros x y. rewrite m1_eq_aux. reflexivity.\n"
                "Qed.\n"
                "Lemma m1_eq_aux : forall x y : Q, x == y -> x == y.\n"
                "Proof.\n"
                "  intros x y H. exact H.\n"
                "Qed.\n"
                "Lemma m2_key : forall x : nat, x = x.\n"
                "Proof.\n"
                "  intros x. apply (Nat.eq_refl x).\n"
                "Qed.\n"
                "Lemma m3_consume : forall a b : nat, a = b -> a = b.\n"
                "Proof.\n"
                "  intros a b H. rewrite m3_prem. reflexivity.\n"
                "Qed.\n"
                "Lemma m3_prem : forall a b : nat, a = b -> b = a.\n"
                "Proof.\n"
                "  intros a b H. exact (eq_sym H).\n"
                "Qed.\n"
                "Lemma m4_qual : forall x : Datatypes2.foo, x = x.\n"
                "Proof.\n"
                "  intros x. reflexivity.\n"
                "Qed.\n")
        res = probe_file(pos)
        lanes = {h["lane"] for h in res["hits"]}
        for lane in LANES:
            assert lane in lanes, "W13 正例缺 %s\n%s" % (lane, res["hits"])
        # 逐机制点查
        m1 = [h for h in res["hits"] if h["lane"] == "W13-1_qeq_backflip"]
        assert any("m1_eq" == h["stmt"].split()[1] for h in m1), m1
        m3 = [h for h in res["hits"] if h["lane"] == "W13-3_premiss_lemma"]
        assert any(h["evidence"].startswith("rewrite m3_prem") for h in m3), m3
        m4 = [h for h in res["hits"] if h["lane"] == "W13-4_require_topology"]
        assert any("Datatypes2.foo" in h["evidence"] for h in m4), m4

        # 负例：注释/字符串里的 ==、前奏册限定名、非载前件 rewrite 不得咬
        neg = os.path.join(tmp, "neg.v")
        with io.open(neg, "w", encoding="utf-8", newline="") as fh:
            fh.write(
                "Require Import List.\n"
                "(* 注释诱饵：x == y 与 rewrite bait 都在注释内 *)\n"
                "Lemma clean_a : forall x : Datatypes.nat, x = x.\n"
                "Proof.\n"
                "  intros x. rewrite clean_b. reflexivity.\n"
                "Qed.\n"
                "Lemma clean_b : forall x : Datatypes.nat, x = x.\n"
                "Proof.\n"
                "  intros x. reflexivity.\n"
                "Qed.\n")
        res2 = probe_file(neg)
        assert res2["hits"] == [], "负例不应有命中：%s" % res2["hits"]
        assert "List" in res2["requires"]

        print("SEAM-PROBE-SELFTEST PASS: W13 四机制正例各一＋掩蔽/前奏册负例全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    ap = argparse.ArgumentParser(prog=PROG, description="W13 四机制代际缝指纹探针（报清单不报清白）")
    ap.add_argument("--file", "-f", default=None, help="被探 .v 文件")
    ap.add_argument("--json", default=None, help="账目 JSON 出账路径")
    ap.add_argument("--hits-csv", default=None, help="命中清单 CSV 出账路径")
    ap.add_argument("--selftest", action="store_true", help="冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        rc = selftest()
        sys.exit(rc)

    if not args.file:
        print("FAIL-LOUD: 缺 --file（探针须显式靶件；--selftest 除外）", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.file):
        print("FAIL-LOUD: --file 路径缺失: %s" % args.file, file=sys.stderr)
        sys.exit(9)

    res = probe_file(args.file)
    print_report(res, hits_csv=args.hits_csv)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(0)


if __name__ == "__main__":
    main()
