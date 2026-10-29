#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mac_stmt_names.py — 顶层语句名有序清单提取器 Mac 形（S 系 Prop 清除战役·工具链 Mac 适配席·20261022）

用途：S10 会师件「487=487 有序全等」断言（E-STAGING-1656 交接书 §一/§七.5）与一切顶层语句
清单对照（会师缝合/波次改前改后 multiset 对拍）。

两口径（Let 计入开关）：
  默认（census 口径）    ：TARGET_KINDS＝Definition/Lemma/Theorem/Corollary/Fixpoint/
                           CoFixpoint/Proposition/Instance/Example——不含 Let
                           （对照 censusFIN manifest 口径·S10 底本=475）
  --include-let（会师口径）：Let 一并计入——S10 会师断言口径（底本=487·含 12 Let）

工艺继承（fail-loud 全程）：
  - 剥嵌套注释/字符串状态机（E364 T8/T3·与 _sortalive.py 席 1489 同法）
  - 边界句号判定（小数点/限定名排除）
  - ARM2 证明体独立成臂消费（T19：Proof..Qed/Defined token 级整句跳过·Line 锚禁用）
  - 属性前缀 #[..]＋Local/Global/Private 修饰词剥除（1549 判例）
  - Example 计入（1572 判例：Lemma 糖形·两器同盲修复）
  - Unicode 标识符名道（b5n_2S_kδ_le 判例）
  - 未知 vernacular/anomaly 逐笔出账禁静默；orphan closer fail-loud

用法：
  python3 mac_stmt_names.py <file.v>                     # census 口径清单＋计数
  python3 mac_stmt_names.py <file.v> --include-let       # 会师口径（含 Let）
  python3 mac_stmt_names.py <file.v> --json out.json
  python3 mac_stmt_names.py <a.v> --compare <b.v> --include-let
                                                          # 有序 1:1 全等断言（487=487 形）
                                                          # 不等 exit 2（fail-loud）
"""
import argparse
import io
import json
import os
import re
import sys

TARGET_KINDS = {"Definition", "Lemma", "Theorem", "Corollary", "Fixpoint",
                "CoFixpoint", "Proposition", "Instance", "Example"}
LET_KIND = "Let"
CLOSER_WORDS = {"Qed", "Defined", "Abort", "Save", "Admitted"}
SKIP_KINDS = {"Notation", "Infix", "Reserved", "Record", "Inductive", "CoInductive",
              "Variant", "Section", "Module", "Functor", "End", "Variable",
              "Variables", "Hypothesis", "Hypotheses", "Context", "Axiom", "Axioms",
              "Parameter", "Parameters", "Conjecture", "Constructor", "Import",
              "Export", "Require", "From", "Include", "Declare", "Arguments",
              "Hint", "Hints", "External", "Ltac", "Tactic", "Strategy", "Open",
              "Bind", "Delimit", "Set", "Unset", "Add", "Remove", "Print", "Eval",
              "Check", "Compute", "Goal", "Load", "Time",
              "Redirect", "Test", "Proof", "Obligation", "Program",
              "Opaque", "Transparent"}
MODIFIER_WORDS = {"Local", "Global", "Private"}
PROOF_WORDS = {"Proof"}

IDENT_RE = re.compile(r"[^\W\d][\w']*", re.UNICODE)


# ---------------------------------------------------------------- state machine
def strip_comments_strings(src):
    """注释（嵌套）/字符串掩码为空格·保行号保长度；EOF 未闭合 fail-loud（E364 T8）。"""
    out = list(src)
    i, n = 0, len(src)
    NORMAL, COMMENT, STRING = 0, 1, 2
    state = NORMAL
    depth = 0
    while i < n:
        c = src[i]
        if state == NORMAL:
            if c == '(' and i + 1 < n and src[i + 1] == '*':
                state = COMMENT
                depth = 1
                out[i] = ' '
                out[i + 1] = ' '
                i += 2
                continue
            if c == '"':
                state = STRING
                out[i] = ' '
                i += 1
                continue
            i += 1
            continue
        if state == COMMENT:
            if c == '(' and i + 1 < n and src[i + 1] == '*':
                depth += 1
                out[i] = ' '
                out[i + 1] = ' '
                i += 2
                continue
            if c == '*' and i + 1 < n and src[i + 1] == ')':
                depth -= 1
                out[i] = ' '
                out[i + 1] = ' '
                i += 2
                if depth == 0:
                    state = NORMAL
                continue
            if c != '\n':
                out[i] = ' '
            i += 1
            continue
        # STRING
        if c == '"' and src[i - 1] != '\\':
            state = NORMAL
            out[i] = ' '
            i += 1
            continue
        if c != '\n':
            out[i] = ' '
        i += 1
    if state != NORMAL:
        raise SystemExit("FAIL-LOUD: unterminated comment/string at EOF (state=%d)" % state)
    return ''.join(out)


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


def is_boundary_period(text, i):
    if text[i] != '.':
        return False
    if i + 1 < len(text) and text[i + 1] not in ' \t\r\n':
        return False
    return True


def find_boundary_period(text, start):
    i = start
    n = len(text)
    while i < n:
        if is_boundary_period(text, i):
            return i
        i += 1
    return -1


def skip_ws(text, i):
    n = len(text)
    while i < n and text[i] in ' \t\r\n':
        i += 1
    return i


def match_word(text, i):
    m = IDENT_RE.match(text, i)
    if not m:
        return None, i
    return m.group(0), m.end()


# ---------------------------------------------------------------- extractor
def extract_statements(path, include_let=False):
    """顶层语句名有序清单。include_let=False=census 口径；True=会师口径（Let 计入）。"""
    src = io.open(path, encoding='utf-8').read()
    masked = strip_comments_strings(src)
    stmts = []
    skips = {}
    anomalies = []
    dupes = {}
    i, n = 0, len(masked)
    while i < n:
        i = skip_ws(masked, i)
        if i >= n:
            break
        start = i
        word = None
        while True:
            if masked[i] == '#' and i + 1 < n and masked[i + 1] == '[':
                j = masked.find(']', i)
                if j == -1:
                    raise SystemExit("FAIL-LOUD: unterminated attribute at line %d" % line_of(masked, i))
                i = j + 1
                i = skip_ws(masked, i)
                continue
            w, j = match_word(masked, i)
            if w in MODIFIER_WORDS:
                i = skip_ws(masked, j)
                continue
            word = w
            i = j
            break
        if word is None:
            anomalies.append({"line": line_of(masked, start), "token": masked[i]})
            i += 1
            continue
        if word in CLOSER_WORDS:
            anomalies.append({"line": line_of(masked, start),
                              "note": "orphan closer %s" % word})
            i = skip_ws(masked, i)
            if i < n and masked[i] == '.':
                i += 1
            continue
        if word in PROOF_WORDS:
            anomalies.append({"line": line_of(masked, start),
                              "note": "standalone Proof sentence"})
            pe = find_boundary_period(masked, i)
            i = (pe + 1) if pe != -1 else n
            continue
        if word == LET_KIND:
            # Let 语句：census 口径跳过（SKIP 记账）；会师口径计入目标
            nm_i = skip_ws(masked, i)
            name, i2 = match_word(masked, nm_i)
            pe = find_boundary_period(masked, i)
            i = (pe + 1) if pe != -1 else n
            if include_let and name:
                stmts.append({"kind": LET_KIND, "name": name,
                              "decl_line": line_of(masked, start)})
                dupes[name] = dupes.get(name, 0) + 1
            else:
                skips[LET_KIND] = skips.get(LET_KIND, 0) + 1
            continue
        if word in TARGET_KINDS:
            nm_i = skip_ws(masked, i)
            name, i2 = match_word(masked, nm_i)
            if not name:
                anomalies.append({"line": line_of(masked, start),
                                  "note": "kind %s without name" % word})
                pe = find_boundary_period(masked, i)
                i = (pe + 1) if pe != -1 else n
                continue
            pe = find_boundary_period(masked, i2)
            if pe == -1:
                raise SystemExit("FAIL-LOUD: no boundary period for %s %s (line %d)"
                                 % (word, name, line_of(masked, start)))
            stmts.append({"kind": word, "name": name,
                          "decl_line": line_of(masked, start)})
            dupes[name] = dupes.get(name, 0) + 1
            i = pe + 1
            # ARM2：可证语句（及带 Proof 关键词的任意语句）证明体独立成臂整句消费
            j0 = skip_ws(masked, i)
            w0, _ = match_word(masked, j0)
            if w0 in PROOF_WORDS:
                while True:
                    j = skip_ws(masked, i)
                    if j >= n:
                        raise SystemExit("FAIL-LOUD: proof body of %s %s unterminated"
                                         % (word, name))
                    w2, j2 = match_word(masked, j)
                    if not w2:
                        i = j + 1
                        continue
                    if w2 in CLOSER_WORDS:
                        k = skip_ws(masked, j2)
                        if k < n and masked[k] == '.':
                            i = k + 1
                        else:
                            i = j2
                        break
                    pe2 = find_boundary_period(masked, j2)
                    if pe2 == -1:
                        raise SystemExit("FAIL-LOUD: proof body of %s %s has no closer"
                                         % (word, name))
                    i = pe2 + 1
            continue
        if word in SKIP_KINDS:
            skips[word] = skips.get(word, 0) + 1
            pe = find_boundary_period(masked, i)
            i = (pe + 1) if pe != -1 else n
            continue
        anomalies.append({"line": line_of(masked, start), "token": word})
        pe = find_boundary_period(masked, i)
        i = (pe + 1) if pe != -1 else n
    dupe_list = {k: v for k, v in dupes.items() if v > 1}
    return {"file": os.path.abspath(path), "include_let": bool(include_let),
            "statements": stmts, "skips": skips,
            "anomalies": anomalies, "duplicates": dupe_list,
            "let_skipped": skips.get(LET_KIND, 0)}


def names_of(inv):
    return [s["name"] for s in inv["statements"]]


def md5_of(path):
    h = __import__("hashlib").md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--include-let", action="store_true", help="会师口径：Let 计入")
    ap.add_argument("--json", help="JSON 落盘")
    ap.add_argument("--names-out", help="纯名单逐行落盘")
    ap.add_argument("--compare", help="第二件 .v：有序 1:1 全等断言（487=487 形·不等 exit 2）")
    ap.add_argument("--expect", type=int, help="计数断言（不等 exit 2）")
    ap.add_argument("--kinds", help="kind 过滤（逗号分·如 Definition,Lemma,Let——1656 席 487 口径"
                                   "＝Definition+Lemma+Let·其提取器 kind 表不含 Theorem/Fixpoint）")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not os.path.exists(args.file):
        print("FILE-MISSING:", args.file)
        sys.exit(9)
    inv = extract_statements(args.file, include_let=args.include_let)
    if args.kinds:
        want = set(k.strip() for k in args.kinds.split(",") if k.strip())
        inv["statements"] = [s for s in inv["statements"] if s["kind"] in want]
        inv["kinds_filter"] = sorted(want)
    names = names_of(inv)
    print("file:", inv["file"])
    print("md5:", md5_of(args.file))
    print("口径:", "会师（含 Let）" if args.include_let else "census（不含 Let）")
    print("total:", len(names), " let_skipped:", inv["let_skipped"])
    print("anomalies:", len(inv["anomalies"]), inv["anomalies"][:5])
    print("duplicates:", inv["duplicates"])
    ok = True
    if args.expect is not None:
        cnt_ok = len(names) == args.expect
        print("EXPECT count=%d got=%d : %s" % (args.expect, len(names),
                                               "OK" if cnt_ok else "FAIL"))
        ok = ok and cnt_ok
    if args.names_out:
        with io.open(args.names_out, "w", encoding="utf-8", newline="\n") as f:
            for nm in names:
                f.write(nm + "\n")
        print("names ->", args.names_out)
    if args.compare:
        if not os.path.exists(args.compare):
            print("COMPARE-FILE-MISSING:", args.compare)
            sys.exit(9)
        inv2 = extract_statements(args.compare, include_let=args.include_let)
        if args.kinds:
            want = set(k.strip() for k in args.kinds.split(",") if k.strip())
            inv2["statements"] = [s for s in inv2["statements"] if s["kind"] in want]
        names2 = names_of(inv2)
        same_len = len(names) == len(names2)
        first_diff = next((k for k in range(min(len(names), len(names2)))
                           if names[k] != names2[k]), None)
        ordered_eq = same_len and first_diff is None
        print("COMPARE %s" % os.path.basename(args.compare))
        print("  md5:", md5_of(args.compare), " total:", len(names2),
              " let_skipped:", inv2["let_skipped"])
        print("  断言 %d=%d 有序全等 : %s" % (len(names), len(names2),
                                             "PASS" if ordered_eq else "FAIL"))
        if not ordered_eq:
            only_a = [n for n in names if n not in set(names2)]
            only_b = [n for n in names2 if n not in set(names)]
            print("  first_diff_idx:", first_diff,
                  "A@diff:", names[first_diff] if first_diff is not None and first_diff < len(names) else None,
                  "B@diff:", names2[first_diff] if first_diff is not None and first_diff < len(names2) else None)
            print("  only_in_A(前10):", only_a[:10])
            print("  only_in_B(前10):", only_b[:10])
            ok = False
        inv["compare"] = {"file": inv2["file"], "total_b": len(names2),
                          "ordered_eq": ordered_eq, "first_diff": first_diff}
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(inv, f, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
