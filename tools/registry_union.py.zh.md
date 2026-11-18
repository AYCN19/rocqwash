#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry_union.py — 注册册 union 手术器（rocqwash tools/·20261110 实战手术
工具化·20261111 入账）

20261110 判例：分支撞 main 尾区——order.txt／_CoqProject 双方 tail-append，逐行
merge 不可行。手术定式：**main 现版为底＋分支对 merge-base 真独有行尾插**。
坑判例（本器存在理由）：独有行必须**对 merge-base 提取而非对 main**——main 侧
#40 世系同名不同形 12 行（键同锚异）若对 main 提取会被误判独有而重插成撞键。
锚正典＝`名.v#R<序>-<md5 前 8 hex>`（md5 对 anchor-src 下落地实件重算）：
顺序号形锚（`#R97` 无指纹）与跨批锚撞文本（他批原样携锚）皆此治愈。

键提取式（--kind）：
  order       行首到 `#R97`（首 `#` 代签/注释）或 `.v` 止——键含 `.v`（如
              `Local/LW0.v`），与 tools/select_audit.py「剥 #代签」同律；
  coqproject  末个 `/` 后去 `.v` 扩展名——键为裸名（如 `Arch/ToyR_01.v`→
              `ToyR_01`）；无 `/` 行原样为键（`-Q . ""` 等旗标行两侧恒同即滤）。

union 算法：main 行序为底（逐字保全，含无键行）＋ branch-unique（行在 branch
∧ 不在 base·键级去重保首·按 branch 原序）尾插。三断言 fail-loud，任一炸即
exit 2 并列清单、零写盘：
  A1 新增行内部键零撞   键级去重后置守卫（去重实现自证·内部自检断言）；
  A2 新增键 ∉ main 键集 对 base 提取的真独有键若已在 main（双方各增同名模块）
                       即撞——坑判例的机检防线；
  A3 全表锚文本零新增重复 锚文本（`#R…` 尾段）重复对数 output ≤ main 基线，
                       main 既有病灶如实录不判（select_audit DUP-ORDER 同律），
                       union/重锚引入新对即炸。

--reanchor 名1,名2 --anchor-src DIR：对列名件在 anchor-src 下（os.walk 递归）
取同名 `.v` 实体算 md5 前 8 hex，重写全表中该键行的锚为正典形（保原序号·
`#R97` → `#R97-<md5_8>`；已带指纹则重算）。列名件无实体→如实列缺件跳过；
不在全表→如实列 not-in-table；列名行无锚/锚形不识→fail-loud exit 2（禁静默）。
同名实体多处→歧义 fail-loud。--reanchor 仅 order 形（coqproject 无锚）。

行尾保全：探 main 正本首 3KB 计 `\r` 定 CRLF/LF，输出随 main；末行换行有无
亦随 main。三面对读时行内容一律剥终止符比对（CRLF main × LF branch 不误判）。

两态制（dry run by default）：干跑零写盘打统计（main N＋unique M＝union K·重锚清单·
断言三过）＋逐行 diff 摘要（仅新增 `+`／改锚 `~` 行）；--out 落盘须 --apply。
--json 出 report（schema rocqwash-registry-union/1，sort_keys 确定性）。

输入三面：--base/--main/--branch 三文件路径（用户自行 git show 物化），或
--git REPO --ref-base/--ref-main/--ref-branch 三 ref 直读（subprocess
`git -C REPO show REF:PATH`·仓路径参数化·PATH 缺省按 kind＝order.txt／
_CoqProject·--git-path 可覆写）。两形互斥混给即用法错。

用法：
  python3 tools/registry_union.py --base BASE --main MAIN --branch BRANCH \
      --kind order [--reanchor 名1,名2 --anchor-src DIR] \
      [--out out.txt] [--apply] [--json report.json]
  python3 tools/registry_union.py --git REPO --ref-base RB --ref-main RM \
      --ref-branch XB --kind order [--git-path order.txt] [同上可选参]
  python3 tools/registry_union.py --selftest

退出码：0=出稿（含干跑）；2=断言炸（A1/A2/A3·重锚畸形·歧义）或用法错；
9=输入缺失（三面件/git show/anchor-src 目录缺）。--selftest：0=全过；2=炸。

确定性：输出 sorted+sort_keys 落盘、同输入重跑字节级恒同；纯 stdlib 零第三方
零网络零编译。写隔离：写面恰为 --out（须 --apply）与显式 --json 出账路径，
断言炸时零写盘。
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
from collections import Counter

PROG = "registry_union"
SCHEMA = "rocqwash-registry-union/1"

KIND_ORDER = "order"
KIND_COQPROJECT = "coqproject"
KINDS = (KIND_ORDER, KIND_COQPROJECT)

# 锚正典：#R<序号>[-<hex 指纹>]；重锚后恒为 #R<序号>-<md5 前 8 hex>
ANCHOR_RE = re.compile(r"#(R\d+(?:-[0-9A-Fa-f]+)?)")
EOL_PROBE_BYTES = 3072  # 行尾探测窗（首 3KB 计 \r）

GIT_PATH_DEFAULT = {KIND_ORDER: "order.txt", KIND_COQPROJECT: "_CoqProject"}


class UsageError(Exception):
    """用法错（exit 2）。"""


class MissingInput(Exception):
    """输入缺失（exit 9）。"""


class AssertBlast(Exception):
    """断言炸（exit 2·携清单）。"""

    def __init__(self, code, items):
        super(AssertBlast, self).__init__(code)
        self.code = code
        self.items = items


# ---------- 读面与行尾 ----------

def detect_eol(raw):
    """main 正本字节 → (行尾形, 末行换行有无)。首 3KB 计 \\r：见 \\r 即 CRLF。"""
    head = raw[:EOL_PROBE_BYTES]
    eol = "CRLF" if b"\r" in head else "LF"
    final_nl = raw.endswith(b"\n") if raw else True
    return eol, final_nl


def read_side(path, what):
    """三面件 → (行列表[剥终止符与首尾空白], eol, final_nl)。缺件 fail-loud 9。"""
    if not os.path.isfile(path):
        raise MissingInput("%s 文件缺失: %s" % (what, path))
    with io.open(path, "rb") as fh:
        raw = fh.read()
    eol, final_nl = detect_eol(raw)
    text = raw.decode("utf-8")
    lines = [ln.rstrip("\r\n").strip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines, eol, final_nl


def read_side_text(text, what):
    """git show 直读文本 → 行列表（eol 以 main 面为准，此处仅拆行）。"""
    lines = [ln.rstrip("\r\n").strip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def git_show(repo, ref, path):
    """`git -C REPO show REF:PATH` 直读（仓路径参数化·fail-loud 9）。"""
    cmd = ["git", "-C", repo, "show", "%s:%s" % (ref, path)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        raise MissingInput("git 不可用: %s" % e)
    if p.returncode != 0:
        raise MissingInput("git show 失败 rc=%d: %s\n%s"
                           % (p.returncode, " ".join(cmd),
                              p.stderr.decode("utf-8", errors="replace").strip()))
    return p.stdout.decode("utf-8")


# ---------- 键与锚 ----------

def key_of(line, kind):
    """行 → 键（order=首 # 前段·含 .v；coqproject=末 / 后去 .v 扩展名）。

    空行/注释行（剥 # 后为空）→ None（main 侧原样保全，branch 侧如实列 skip）。
    """
    s = line.strip()
    if not s:
        return None
    if kind == KIND_ORDER:
        head = s.split("#", 1)[0].strip()
        return head or None
    # coqproject：末个 / 后去扩展名（本域扩展名＝.v；无 .v 行原样为键）
    tail = s.rsplit("/", 1)[-1]
    if tail.endswith(".v"):
        tail = tail[:-2]
    return tail or None


def anchor_of(line):
    """行 → 锚文本（首 `#R<序>[-<hex>]` 尾段·含 #）或 None。"""
    m = ANCHOR_RE.search(line)
    return m.group(0) if m else None


def bare_name(name):
    """列名件名归一：剥首尾空白与 .v 后缀（order 键对齐用）。"""
    n = name.strip()
    if n.endswith(".v"):
        n = n[:-2]
    return n


def key_bare(key):
    """表内键 → 裸名（order 键剥 .v；coqproject 键本裸）。"""
    return bare_name(key)


# ---------- union 算法 ----------

def extract_unique(base_lines, branch_lines, kind):
    """branch-unique＝行在 branch ∧ 不在 base（行级）→键级去重保首→branch 原序。

    **独有须对 merge-base 提取**（坑判例）：对 main 提取会把 main 侧同名不同形
    世系行误判独有。返回 (added 行列表, no_key_skipped 行列表)。
    """
    base_set = set(base_lines)
    seen_keys = set()
    added = []
    no_key = []
    for ln in branch_lines:
        if ln in base_set:
            continue
        k = key_of(ln, kind)
        if k is None:
            no_key.append(ln)
            continue
        if k in seen_keys:
            continue
        seen_keys.add(k)
        added.append(ln)
    return added, no_key


def assert_internal_key_unique(added, kind):
    """A1：新增行内部键零撞（键级去重后置守卫·去重实现自证）。"""
    seen = {}
    for ln in added:
        k = key_of(ln, kind)
        if k in seen:
            raise AssertBlast("A1-INTERNAL-KEY-DUP",
                              ["键 %r 新增行内部撞：%r ↔ %r" % (k, seen[k], ln)])
        seen[k] = ln


def assert_added_keys_not_in_main(added, main_lines, kind):
    """A2：新增键 ∉ main 键集（坑判例机检防线·双方各增同名即撞）。"""
    main_keys = set()
    for ln in main_lines:
        k = key_of(ln, kind)
        if k is not None:
            main_keys.add(k)
    hits = []
    seen = set()
    for ln in added:
        k = key_of(ln, kind)
        if k in main_keys and k not in seen:
            seen.add(k)
            hits.append(k)
    if hits:
        raise AssertBlast("A2-ADDED-KEY-IN-MAIN",
                          ["新增键已在 main（对 merge-base 提取后仍撞·逐键）: %s"
                           % k for k in sorted(hits)])


def dup_pairs(texts):
    """锚文本 → 重复对数 c*(c-1)/2（main 既有病灶如实录不判的度量基）。"""
    return {t: c * (c - 1) // 2 for t, c in Counter(texts).items()}


def assert_anchor_no_new_dups(out_lines, main_lines):
    """A3：全表锚文本零新增重复（重复对数 output > main 基线即炸）。"""
    out_texts = [anchor_of(ln) for ln in out_lines]
    main_texts = [anchor_of(ln) for ln in main_lines]
    out_pairs = dup_pairs([t for t in out_texts if t])
    main_pairs = dup_pairs([t for t in main_texts if t])
    hits = []
    for t in sorted(out_pairs):
        if out_pairs[t] > main_pairs.get(t, 0):
            hits.append("%s（main 对数 %d → union 对数 %d）"
                        % (t, main_pairs.get(t, 0), out_pairs[t]))
    if hits:
        raise AssertBlast("A3-ANCHOR-TEXT-NEW-DUP", hits)


# ---------- 重锚 ----------

def resolve_entity(name, anchor_src):
    """列名件 → anchor-src 下唯一同名 .v 实件路径。

    目录缺→MissingInput(9)；零实体→None（如实列缺件）；多处→歧义用法炸(2)。
    名含 `/` 时优先直拼路径，不命中即如实缺件（不再递归捞同基名）。
    """
    if not os.path.isdir(anchor_src):
        raise MissingInput("--anchor-src 目录缺失: %s" % anchor_src)
    n = name.strip()
    target = n + ".v" if not n.endswith(".v") else n
    if "/" in n.replace("\\", "/"):
        cand = os.path.join(anchor_src, target)
        return cand if os.path.isfile(cand) else None
    hits = []
    for root, _dirs, files in os.walk(anchor_src):
        if target in files:
            hits.append(os.path.join(root, target))
    if len(hits) > 1:
        raise UsageError("实体歧义：--reanchor 名 %r 在 %s 下多处命中：%s"
                         % (n, anchor_src, sorted(hits)))
    return hits[0] if hits else None


def md5_8_of(path):
    """实件 md5 前 8 hex（锚正典指纹源）。"""
    h = hashlib.md5()
    with io.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def apply_reanchor(lines, names, anchor_src, kind):
    """对列名件全表重锚为正典形（保原序号·指纹对落地实件重算）。

    返回 (新行列表, rewrites 清单, missing_entity 名单, not_in_table 名单)。
    列名行无锚/锚形不识→AssertBlast(2)；coqproject 无锚→用法炸。
    """
    if kind != KIND_ORDER:
        raise UsageError("--reanchor 仅 --kind order 有效（coqproject 行无锚）")
    bare_to_names = {}
    for i, ln in enumerate(lines):
        k = key_of(ln, kind)
        if k is not None:
            bare_to_names.setdefault(key_bare(k), []).append(i)
    rewrites = []
    missing = []
    not_in_table = []
    out = list(lines)
    for raw_name in names:
        n = bare_name(raw_name)
        if not n:
            continue
        if n not in bare_to_names:
            not_in_table.append(n)
            continue
        entity = resolve_entity(n, anchor_src)
        if entity is None:
            missing.append(n)
            continue
        fp = md5_8_of(entity)
        for i in bare_to_names[n]:
            ln = out[i]
            m = ANCHOR_RE.search(ln)
            if m is None:
                raise AssertBlast("REANCHOR-NO-ANCHOR",
                                  ["列名件 %r 行无锚不可重锚（无序号可承）: %r"
                                   % (n, ln)])
            old = m.group(0)
            seq = old[2:].split("-", 1)[0]
            new = "#R%s-%s" % (seq, fp)
            if old == new:
                continue  # 已是正典形（已在盘即 skip·幂等律）
            out[i] = ln[:m.start()] + new + ln[m.end():]
            rewrites.append({"module": n, "line_index": i, "old_anchor": old,
                             "new_anchor": new, "md5_8": fp,
                             "entity": entity})
    rewrites.sort(key=lambda r: (r["line_index"], r["old_anchor"]))
    return out, rewrites, sorted(set(missing)), sorted(set(not_in_table))


# ---------- 组装与出稿 ----------

def build_union(main_lines, base_lines, branch_lines, kind,
                reanchor_names=None, anchor_src=None):
    """全流程：union→重锚→三断言。返回 (out_lines, added, rewrites, missing,
    not_in_table, no_key)。断言炸即 AssertBlast（主流程 exit 2 零写盘）。"""
    added, no_key = extract_unique(base_lines, branch_lines, kind)
    out_lines = list(main_lines) + added
    rewrites, missing, not_in_table = [], [], []
    if reanchor_names:
        out_lines, rewrites, missing, not_in_table = apply_reanchor(
            out_lines, reanchor_names, anchor_src, kind)
    assert_internal_key_unique(added, kind)
    assert_added_keys_not_in_main(added, main_lines, kind)
    assert_anchor_no_new_dups(out_lines, main_lines)
    return out_lines, added, rewrites, missing, not_in_table, no_key


def render_output(out_lines, eol, final_nl):
    """行列表 → 输出字节（行尾随 main·末行换行随 main）。"""
    nl = "\r\n" if eol == "CRLF" else "\n"
    text = nl.join(out_lines)
    if final_nl and out_lines:
        text += nl
    return text.encode("utf-8")


def diff_summary(main_lines, out_lines, added, kind):
    """逐行 diff 摘要（仅新增/改锚行·确定性按 union 表序）。"""
    rows = []
    main_set = set(main_lines)
    added_set = set(added)
    for i, ln in enumerate(out_lines):
        if ln in added_set and ln not in main_set:
            rows.append(("add", i + 1, ln, None))
    # 改锚行：main 原行与 union 行同键不同锚（重锚所致）逐位对出
    for i, old, new in _anchor_changed(main_lines, out_lines, kind):
        rows.append(("reanchor", i + 1, new, old))
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows


def _anchor_changed(main_lines, out_lines, kind):
    """main↔union 同键行锚变更对（重锚清单的可复算对拍面）。"""
    main_by_key = {}
    for ln in main_lines:
        k = key_of(ln, kind)
        if k is not None and k not in main_by_key:
            main_by_key[k] = ln
    main_lines_set = set(main_lines)
    rows = []
    for i, ln in enumerate(out_lines):
        k = key_of(ln, kind)
        if k is None or ln in main_lines_set:
            continue
        old = main_by_key.get(k)
        if old is not None and anchor_of(old) != anchor_of(ln) \
                and old != ln:
            rows.append((i, old, ln))
    return rows


def build_report(args_desc, kind, eol, final_nl, main_lines, base_lines,
                 branch_lines, added, no_key, out_lines, rewrites, missing,
                 not_in_table, reanchor_names, mode):
    """report（schema rocqwash-registry-union/1·sort_keys 确定性落盘）。"""
    return {
        "schema": SCHEMA,
        "kind": kind,
        "mode": mode,
        "inputs": args_desc,
        "eol": {"detected": eol, "final_newline": final_nl},
        "stats": {"main": len(main_lines), "base": len(base_lines),
                  "branch": len(branch_lines), "unique": len(added),
                  "union": len(out_lines),
                  "reanchor_rewrites": len(rewrites),
                  "no_key_skipped": sorted(no_key)},
        "added": [{"line": ln, "key": key_of(ln, kind)} for ln in added],
        "reanchor": {"requested": [bare_name(x) for x in (reanchor_names or [])],
                     "rewrites": rewrites,
                     "missing_entity": missing,
                     "not_in_table": not_in_table},
        "assertions": {"internal_key_unique": True,
                       "added_keys_not_in_main": True,
                       "anchor_text_no_new_dups": True},
        "diff": [{"op": op, "line_no": no, "line": ln,
                  **({"from": old} if old else {})}
                 for op, no, ln, old in diff_summary(main_lines, out_lines,
                                                     added, kind)],
    }


def dump_json(path, obj):
    """确定性 JSON 落盘（sort_keys＋indent=1·与 chain_graph 同律）。"""
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=True)


# ---------- 自证 ----------

def selftest():
    """内嵌冻结向量组（tmp 目录合成·零触真仓零网络零编译）：

    1 正 union（3+2=5·main 序底＋branch 原序尾插＋--apply 落盘）
    2 同名不同形陷阱（branch 行≠main 行但键同·对 base 判非独有必过滤——
      若误对 main 提取该键即 A2 炸，正道零新增）
    3 reanchor md5 向量（已知内容→已知 md5-8＝77c2b9a8·正典形重写·缺件如实列）
    4 CRLF 保全（首 3KB 计 \\r·输出随 main·末行换行有无随 main）
    5 断言三炸各一例（A1 内部键撞内部守卫直证／A2 CLI 撞 main 键／A3 CLI
      锚文本新增重复——各 exit 2 零写盘）
    6 干跑零写盘（--out 不落盘→--apply 落盘→幂等字节恒同）
    7 CLI 四码＋--json schema＋确定性（help0/bogus2/缺件9/无输入2/重跑恒同）
    8 git 三 ref 直读（tmp 仓合成·缺 git 让席 SKIP）
    """
    import tempfile

    def run(args):
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    def wf(path, text):
        with io.open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
        return path

    tmp = tempfile.mkdtemp(prefix="rocqwash_ru_self_")
    try:
        # ---- ① 正 union：main 3 行＋真独有 2 行＝union 5 行 ----
        d1 = os.path.join(tmp, "v1")
        os.makedirs(d1)
        base = wf(os.path.join(d1, "base.txt"),
                  "A.v#R0-11111111\nB.v#R0-22222222\n")
        main = wf(os.path.join(d1, "main.txt"),
                  "A.v#R0-11111111\nB.v#R0-22222222\nC.v#R0-33333333\n")
        branch = wf(os.path.join(d1, "branch.txt"),
                    "A.v#R0-11111111\nB.v#R0-22222222\n"
                    "D.v#R1-44444444\nE.v#R1-55555555\n")
        out1 = os.path.join(d1, "union.txt")
        p = run(["--base", base, "--main", main, "--branch", branch,
                 "--kind", "order", "--out", out1, "--apply",
                 "--json", os.path.join(d1, "r.json")])
        assert p.returncode == 0, p.stdout
        got = io.open(out1, "rb").read().decode("utf-8").splitlines()
        assert len(got) == 5, got  # 3+2=5
        assert got == ["A.v#R0-11111111", "B.v#R0-22222222", "C.v#R0-33333333",
                       "D.v#R1-44444444", "E.v#R1-55555555"], got
        rep = json.load(io.open(os.path.join(d1, "r.json"), encoding="utf-8"))
        assert rep["schema"] == SCHEMA, rep["schema"]
        assert rep["stats"]["unique"] == 2 and rep["stats"]["union"] == 5, rep
        assert rep["stats"]["main"] == 3, rep
        assert rep["eol"]["detected"] == "LF", rep
        print("  [1/8] 正 union 3+2=5 OK（main 序底＋branch 原序尾插＋schema）")

        # ---- ② 同名不同形陷阱：对 base 判非独有必过滤 ----
        d2 = os.path.join(tmp, "v2")
        os.makedirs(d2)
        wf(os.path.join(d2, "base.txt"),
           "X40.v#R40-3333bbbb\n")
        wf(os.path.join(d2, "main.txt"),
           "X40.v#R40-deadbeef\nM.v#R40-aaaa1111\n")
        wf(os.path.join(d2, "branch.txt"),
           "X40.v#R40-3333bbbb\nB.v#R41-cccc2222\n")
        out2 = os.path.join(d2, "union.txt")
        p = run(["--base", os.path.join(d2, "base.txt"),
                 "--main", os.path.join(d2, "main.txt"),
                 "--branch", os.path.join(d2, "branch.txt"),
                 "--kind", "order", "--out", out2, "--apply"])
        assert p.returncode == 0, p.stdout
        got = io.open(out2, "rb").read().decode("utf-8").splitlines()
        # 陷阱行（键同 X40 形异）必过滤：union＝main 原样＋B 一行
        assert got == ["X40.v#R40-deadbeef", "M.v#R40-aaaa1111",
                       "B.v#R41-cccc2222"], got
        # 反证：若误对 main 提取，X40 行会成「独有」→A2 炸（正道零炸即正道）
        assert "X40.v#R40-3333bbbb" not in got, got
        print("  [2/8] 同名不同形陷阱 OK（对 merge-base 提取·键同必过滤）")

        # ---- ③ reanchor md5 向量：已知内容→已知 md5-8 ----
        d3 = os.path.join(tmp, "v3")
        os.makedirs(os.path.join(d3, "world"))
        wf(os.path.join(d3, "world", "ToyA.v"), "module A content alpha\n")
        assert md5_8_of(os.path.join(d3, "world", "ToyA.v")) == "77c2b9a8"
        wf(os.path.join(d3, "base.txt"),
           "ToyA.v#R3-00000000\nGhost.v#R9-00000000\n")
        wf(os.path.join(d3, "main.txt"),
           "ToyA.v#R3-ffffffff\nGhost.v#R9-11111111\n")
        wf(os.path.join(d3, "branch.txt"),
           "ToyA.v#R3-00000000\nGhost.v#R9-00000000\n")
        out3 = os.path.join(d3, "union.txt")
        p = run(["--base", os.path.join(d3, "base.txt"),
                 "--main", os.path.join(d3, "main.txt"),
                 "--branch", os.path.join(d3, "branch.txt"),
                 "--kind", "order", "--reanchor", "ToyA",
                 "--anchor-src", os.path.join(d3, "world"),
                 "--out", out3, "--apply"])
        assert p.returncode == 0, p.stdout
        got = io.open(out3, "rb").read().decode("utf-8").splitlines()
        assert got == ["ToyA.v#R3-77c2b9a8", "Ghost.v#R9-11111111"], got
        # 表内缺件＋不在全表，均如实列（Ghost 在表无实体→缺件；GhostX 不在表
        # →not-in-table；exit 仍 0·跳过不扰动他行）
        p = run(["--base", os.path.join(d3, "base.txt"),
                 "--main", os.path.join(d3, "main.txt"),
                 "--branch", os.path.join(d3, "branch.txt"),
                 "--kind", "order", "--reanchor", "ToyA,Ghost,GhostX",
                 "--anchor-src", os.path.join(d3, "world"),
                 "--out", out3, "--apply"])
        assert p.returncode == 0, p.stdout
        assert "Ghost" in p.stdout and "缺件" in p.stdout, p.stdout
        assert "GhostX" in p.stdout and "不在全表" in p.stdout, p.stdout
        assert io.open(out3, "rb").read().decode("utf-8").splitlines() \
            == ["ToyA.v#R3-77c2b9a8", "Ghost.v#R9-11111111"], \
            "缺件跳过不得扰动他行"
        print("  [3/8] reanchor md5 向量 OK（77c2b9a8 冻结·缺件如实列跳过）")

        # ---- ④ CRLF 保全：输出随 main（含末行换行有无） ----
        d4 = os.path.join(tmp, "v4")
        os.makedirs(d4)
        wf(os.path.join(d4, "base.txt"), "A.v\r\nB.v\r\n")
        wf(os.path.join(d4, "main.txt"), "A.v\r\nB.v\r\nC.v\r\n")
        wf(os.path.join(d4, "branch.txt"), "A.v\nB.v\nD.v\n")  # LF branch 不误判
        out4 = os.path.join(d4, "union.txt")
        p = run(["--base", os.path.join(d4, "base.txt"),
                 "--main", os.path.join(d4, "main.txt"),
                 "--branch", os.path.join(d4, "branch.txt"),
                 "--kind", "order", "--out", out4, "--apply"])
        assert p.returncode == 0, p.stdout
        raw = io.open(out4, "rb").read()
        assert raw == "A.v\r\nB.v\r\nC.v\r\nD.v\r\n".encode("utf-8"), raw
        # 末行无换行的 main → 输出亦无
        wf(os.path.join(d4, "main2.txt"), "A.v\r\nB.v\r\nC.v")
        out4b = os.path.join(d4, "union2.txt")
        p = run(["--base", os.path.join(d4, "base.txt"),
                 "--main", os.path.join(d4, "main2.txt"),
                 "--branch", os.path.join(d4, "branch.txt"),
                 "--kind", "order", "--out", out4b, "--apply"])
        assert p.returncode == 0, p.stdout
        assert io.open(out4b, "rb").read() \
            == "A.v\r\nB.v\r\nC.v\r\nD.v".encode("utf-8")
        print("  [4/8] CRLF 保全 OK（首 3KB 计 \\r·末行换行有无随 main）")

        # ---- ⑤ 断言三炸各一例（exit 2·零写盘） ----
        d5 = os.path.join(tmp, "v5")
        os.makedirs(d5)
        # A2：双方各增同名（键不在 base·在 main）→ CLI exit 2
        wf(os.path.join(d5, "a2_base.txt"), "Z.v#R0-00000000\n")
        wf(os.path.join(d5, "a2_main.txt"),
           "Z.v#R0-00000000\nK.v#R0-11111111\n")
        wf(os.path.join(d5, "a2_branch.txt"),
           "Z.v#R0-00000000\nK.v#R0-11111111\n")
        out5 = os.path.join(d5, "union.txt")
        p = run(["--base", os.path.join(d5, "a2_base.txt"),
                 "--main", os.path.join(d5, "a2_main.txt"),
                 "--branch", os.path.join(d5, "a2_branch.txt"),
                 "--kind", "order", "--out", out5, "--apply"])
        assert p.returncode == 2, "A2 应炸 exit 2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert "A2" in p.stdout and "K" in p.stdout, p.stdout
        assert not os.path.exists(out5), "断言炸零写盘违例"
        # A3：新增行锚文本与 main 行相撞（键异锚同）→ CLI exit 2
        wf(os.path.join(d5, "a3_base.txt"), "Z.v#R0-00000000\n")
        wf(os.path.join(d5, "a3_main.txt"), "Z.v#R0-abcabcab\n")
        wf(os.path.join(d5, "a3_branch.txt"),
           "Z.v#R0-00000000\nY9.v#R0-abcabcab\n")
        p = run(["--base", os.path.join(d5, "a3_base.txt"),
                 "--main", os.path.join(d5, "a3_main.txt"),
                 "--branch", os.path.join(d5, "a3_branch.txt"),
                 "--kind", "order", "--out", out5, "--apply"])
        assert p.returncode == 2, "A3 应炸 exit 2 实测 %d\n%s" % (
            p.returncode, p.stdout)
        assert "A3" in p.stdout and "abcabcab" in p.stdout, p.stdout
        assert not os.path.exists(out5), "断言炸零写盘违例"
        # A1：新增行内部键撞（键级去重后置守卫·内部直证）
        try:
            assert_internal_key_unique(["P.v#R1-11111111", "P.v#R1-22222222"],
                                       KIND_ORDER)
            raise AssertionError("A1 守卫未炸＝违例")
        except AssertBlast as e:
            assert e.code == "A1-INTERNAL-KEY-DUP", e.code
        # 重锚畸形面：列名行无锚 → fail-loud exit 2
        wf(os.path.join(d5, "na_base.txt"), "N.v#R0-00000000\n")
        wf(os.path.join(d5, "na_main.txt"), "N.v#R0-00000000\nNA.v\n")
        wf(os.path.join(d5, "na_branch.txt"), "N.v#R0-00000000\n")
        os.makedirs(os.path.join(d5, "w5"))
        wf(os.path.join(d5, "w5", "NA.v"), "x\n")
        p = run(["--base", os.path.join(d5, "na_base.txt"),
                 "--main", os.path.join(d5, "na_main.txt"),
                 "--branch", os.path.join(d5, "na_branch.txt"),
                 "--kind", "order", "--reanchor", "NA",
                 "--anchor-src", os.path.join(d5, "w5"),
                 "--out", out5, "--apply"])
        assert p.returncode == 2 and "REANCHOR-NO-ANCHOR" in p.stdout, p.stdout
        print("  [5/8] 断言三炸各一例 OK（A1 内证／A2 CLI／A3 CLI＋重锚畸形）")

        # ---- ⑥ 干跑零写盘→--apply→幂等 ----
        d6 = os.path.join(tmp, "v6")
        os.makedirs(d6)
        wf(os.path.join(d6, "base.txt"), "A.v#R0-11111111\n")
        wf(os.path.join(d6, "main.txt"), "A.v#R0-11111111\nC.v#R0-3333\n")
        wf(os.path.join(d6, "branch.txt"),
           "A.v#R0-11111111\nD.v#R1-44444444\n")
        out6 = os.path.join(d6, "union.txt")
        p = run(["--base", os.path.join(d6, "base.txt"),
                 "--main", os.path.join(d6, "main.txt"),
                 "--branch", os.path.join(d6, "branch.txt"),
                 "--kind", "order", "--out", out6])
        assert p.returncode == 0, p.stdout
        assert not os.path.exists(out6), "干跑写盘＝违例"
        assert "unique=1" in p.stdout and "union=3" in p.stdout, p.stdout
        p = run(["--base", os.path.join(d6, "base.txt"),
                 "--main", os.path.join(d6, "main.txt"),
                 "--branch", os.path.join(d6, "branch.txt"),
                 "--kind", "order", "--out", out6, "--apply"])
        assert p.returncode == 0 and os.path.exists(out6), p.stdout
        first = io.open(out6, "rb").read()
        p = run(["--base", os.path.join(d6, "base.txt"),
                 "--main", os.path.join(d6, "main.txt"),
                 "--branch", os.path.join(d6, "branch.txt"),
                 "--kind", "order", "--out", out6, "--apply"])
        assert p.returncode == 0 and io.open(out6, "rb").read() == first, \
            "重跑字节漂移＝违例"
        print("  [6/8] 干跑零写盘 OK（--out 须 --apply·幂等字节恒同）")

        # ---- ⑦ CLI 四码＋--json 确定性＋coqproject 键形 ----
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "无输入应 rc=2 实测 %d" % p.returncode
        p = run(["--base", os.path.join(tmp, "nope.txt"),
                 "--main", os.path.join(tmp, "nope2.txt"),
                 "--branch", os.path.join(tmp, "nope3.txt"), "--kind", "order"])
        assert p.returncode == 9, "缺件应 rc=9 实测 %d" % p.returncode
        # coqproject 键形（末 / 后去扩展名）＋JSON 确定性
        d7 = os.path.join(tmp, "v7")
        os.makedirs(d7)
        wf(os.path.join(d7, "base.txt"), '-Q . ""\nArch/ToyR_01.v\n')
        wf(os.path.join(d7, "main.txt"),
           '-Q . ""\nArch/ToyR_01.v\nMainAdd.v\n')
        wf(os.path.join(d7, "branch.txt"),
           '-Q . ""\nArch/ToyR_01.v\nDeep/BrNew.v\n')
        j7 = os.path.join(d7, "r.json")
        p = run(["--base", os.path.join(d7, "base.txt"),
                 "--main", os.path.join(d7, "main.txt"),
                 "--branch", os.path.join(d7, "branch.txt"),
                 "--kind", "coqproject", "--json", j7])
        assert p.returncode == 0, p.stdout
        rep = json.load(io.open(j7, encoding="utf-8"))
        assert [a["key"] for a in rep["added"]] == ["BrNew"], rep["added"]
        before = io.open(j7, "rb").read()
        p = run(["--base", os.path.join(d7, "base.txt"),
                 "--main", os.path.join(d7, "main.txt"),
                 "--branch", os.path.join(d7, "branch.txt"),
                 "--kind", "coqproject", "--json", j7])
        assert p.returncode == 0 and io.open(j7, "rb").read() == before, \
            "json 字节漂移＝违例"
        print("  [7/8] CLI 四码 OK（help0/bogus2/无输入2/缺件9）＋coqproject"
              " 键形＋json 确定性")

        # ---- ⑧ git 三 ref 直读（tmp repository·缺 git 让席 SKIP） ----
        if shutil.which("git") is None:
            print("  [8/8] git 直读 SKIP（git 不在卷·让席不充红）")
        else:
            d8 = os.path.join(tmp, "v8repo")
            os.makedirs(d8)
            env = dict(os.environ)
            env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t",
                        "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
                        "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"})

            def g(*a):
                p8 = subprocess.run(["git", "-C", d8] + list(a), env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
                assert p8.returncode == 0, p8.stdout
                return p8.stdout.decode("utf-8", errors="replace").strip()

            def commit_order(text, msg):
                wf(os.path.join(d8, "order.txt"), text)
                g("add", "order.txt")
                g("commit", "-m", msg)

            g("init")
            main_ref = g("symbolic-ref", "--short", "HEAD")  # master|main 随版
            commit_order("A.v#R0-11111111\nB.v#R0-22222222\n", "base")
            g("branch", "merge-base-ref")
            commit_order("A.v#R0-11111111\nB.v#R0-22222222\n"
                         "C.v#R0-33333333\n", "main")
            g("checkout", "-b", "br")
            commit_order("A.v#R0-11111111\nB.v#R0-22222222\n"
                         "D.v#R1-44444444\n", "branch")
            out8 = os.path.join(tmp, "v8_union.txt")
            p = run(["--git", d8, "--ref-base", "merge-base-ref",
                     "--ref-main", main_ref, "--ref-branch", "br",
                     "--kind", "order", "--out", out8, "--apply"])
            assert p.returncode == 0, p.stdout
            got = io.open(out8, "rb").read().decode("utf-8").splitlines()
            assert len(got) == 4 and got[-1] == "D.v#R1-44444444", got
            # 坏 ref → 9
            p = run(["--git", d8, "--ref-base", "no-such-ref",
                     "--ref-main", main_ref, "--ref-branch", "br",
                     "--kind", "order"])
            assert p.returncode == 9, "坏 ref 应 rc=9 实测 %d" % p.returncode
            print("  [8/8] git 三 ref 直读 OK（subprocess git show·坏 ref 9）")

        print("REGISTRY-UNION-SELFTEST PASS: 正union/陷阱过滤/md5向量/CRLF保全/"
              "断言三炸/干跑零写盘/CLI四码/git直读 八判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- 主流程 ----------

def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="注册册 union 手术器：main 现版为底＋分支对 merge-base "
                    "真独有行尾插＋三断言 fail-loud＋锚正典重锚"
                    "（20261110 实战手术工具化）")
    ap.add_argument("--base", default=None, metavar="FILE",
                    help="merge-base 面注册册（用户自行 git show 物化）")
    ap.add_argument("--main", default=None, metavar="FILE",
                    help="main 现版注册册（union 底）")
    ap.add_argument("--branch", default=None, metavar="FILE",
                    help="分支版注册册（独有行源）")
    ap.add_argument("--git", default=None, metavar="REPO",
                    help="改直读：仓路径（--ref-* 三 ref 必配·与三文件互斥）")
    ap.add_argument("--ref-base", default=None, metavar="REF")
    ap.add_argument("--ref-main", default=None, metavar="REF")
    ap.add_argument("--ref-branch", default=None, metavar="REF")
    ap.add_argument("--git-path", default=None, metavar="PATH",
                    help="仓内注册册路径（缺省按 kind＝order.txt/_CoqProject）")
    ap.add_argument("--kind", default=None, choices=KINDS,
                    help="键提取式：order｜coqproject")
    ap.add_argument("--reanchor", default=None, metavar="名1,名2",
                    help="重锚列名件（逗号分隔·仅 --kind order）")
    ap.add_argument("--anchor-src", default=None, metavar="DIR",
                    help="重锚实件源目录（os.walk 递归取同名 .v）")
    ap.add_argument("--out", default=None, metavar="FILE",
                    help="union 稿出路径（落盘须 --apply）")
    ap.add_argument("--apply", action="store_true",
                    help="允许 --out 落盘（缺省干跑零写盘）")
    ap.add_argument("--json", default=None, metavar="FILE",
                    help="report 出账（schema rocqwash-registry-union/1）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    def die_usage(msg):
        print("FAIL-LOUD: %s" % msg, file=sys.stderr)
        sys.exit(2)

    # ---- 形参咬合（fail-loud 用法面） ----
    file_mode = any(v is not None for v in (args.base, args.main, args.branch))
    git_mode = args.git is not None
    if file_mode and git_mode:
        die_usage("--base/--main/--branch 与 --git 直读互斥，两形混给")
    if not file_mode and not git_mode:
        die_usage("输入三面缺省：--base/--main/--branch 三件 或 --git＋三 ref"
                  "（--selftest 除外）")
    if args.kind is None:
        die_usage("--kind 必给（order|coqproject）")
    if args.apply and not args.out:
        die_usage("--apply 须配 --out（无 in-place 缺省·禁隐式覆写）")
    if (args.reanchor is None) != (args.anchor_src is None):
        die_usage("--reanchor 与 --anchor-src 须成对给")
    if git_mode:
        refs = (args.ref_base, args.ref_main, args.ref_branch)
        if any(r is None for r in refs):
            die_usage("--git 直读须 --ref-base/--ref-main/--ref-branch 三 ref"
                      "齐给")

    reanchor_names = None
    if args.reanchor is not None:
        reanchor_names = [x for x in args.reanchor.split(",") if x.strip()]
        if not reanchor_names:
            die_usage("--reanchor 列名空")

    # ---- 读三面 ----
    try:
        if git_mode:
            git_path = args.git_path or GIT_PATH_DEFAULT[args.kind]
            args_desc = {"git": args.git, "git_path": git_path,
                         "ref_base": args.ref_base, "ref_main": args.ref_main,
                         "ref_branch": args.ref_branch}
            base_lines = read_side_text(
                git_show(args.git, args.ref_base, git_path), "base(ref)")
            main_text = git_show(args.git, args.ref_main, git_path)
            main_lines = read_side_text(main_text, "main(ref)")
            branch_lines = read_side_text(
                git_show(args.git, args.ref_branch, git_path), "branch(ref)")
            main_raw = main_text.encode("utf-8")
            eol, final_nl = detect_eol(main_raw)
        else:
            args_desc = {"base": args.base, "main": args.main,
                         "branch": args.branch}
            base_lines, _, _ = read_side(args.base, "base")
            main_lines, eol, final_nl = read_side(args.main, "main")
            branch_lines, _, _ = read_side(args.branch, "branch")
    except MissingInput as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(9)

    # ---- union＋重锚＋三断言（炸即 exit 2 零写盘） ----
    try:
        out_lines, added, rewrites, missing, not_in_table, no_key = \
            build_union(main_lines, base_lines, branch_lines, args.kind,
                        reanchor_names, args.anchor_src)
    except AssertBlast as e:
        print("ASSERT-BLAST %s（exit 2·零写盘）：" % e.code, file=sys.stderr)
        for it in e.items:
            print("  - %s" % it, file=sys.stderr)
        sys.exit(2)
    except UsageError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    # ---- 出稿面 ----
    mode = "APPLY" if args.apply else "DRY-RUN"
    payload = render_output(out_lines, eol, final_nl)
    if args.apply:
        with io.open(args.out, "wb") as fh:
            fh.write(payload)

    print("=== REGISTRY-UNION (%s) ===" % mode)
    print("kind=%s eol=%s final_nl=%s" % (args.kind, eol, final_nl))
    for k in sorted(args_desc):
        print("  %s=%s" % (k, args_desc[k]))
    print("stats: main=%d + unique=%d = union=%d"
          % (len(main_lines), len(added), len(out_lines)))
    print("assertions: internal_key_unique=PASS "
          "added_keys_not_in_main=PASS anchor_text_no_new_dups=PASS")
    if reanchor_names:
        print("reanchor: %s" % ",".join(
            bare_name(x) for x in reanchor_names))
        for r in rewrites:
            print("  rewrite L%d %s: %s -> %s (md5_8=%s)"
                  % (r["line_index"] + 1, r["module"], r["old_anchor"],
                     r["new_anchor"], r["md5_8"]))
        if missing:
            print("  缺件（无 .v 实体·如实跳过）: %s" % ",".join(missing))
        if not_in_table:
            print("  不在全表（如实跳过）: %s" % ",".join(not_in_table))
    if no_key:
        print("no-key 行（branch 侧无键不插·如实列）: %s" % ";".join(no_key))
    print("--- diff（仅新增/改锚行） ---")
    rows = diff_summary(main_lines, out_lines, added, args.kind)
    if not rows:
        print("  (无新增/改锚行)")
    for op, no, ln, old in rows:
        if op == "add":
            print("+ L%d: %s" % (no, ln))
        else:
            print("~ L%d: %s -> %s" % (no, old, ln))
    if args.out:
        print("out -> %s%s" % (args.out,
                               "" if args.apply else "（干跑未写盘）"))
    if args.json:
        rep = build_report(args_desc, args.kind, eol, final_nl, main_lines,
                           base_lines, branch_lines, added, no_key, out_lines,
                           rewrites, missing, not_in_table, reanchor_names,
                           mode)
        dump_json(args.json, rep)
        print("json -> %s" % args.json)
    sys.exit(0)


if __name__ == "__main__":
    main()
