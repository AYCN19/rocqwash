#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""precedent_station.py - three-precedent acceptance-chain combiner (rocqwash wrapper/).
Purpose.  Three cured precedents (same `Obj.magic` extraction defect, three different
  repairs) share one acceptance chain; this station composes that chain 1:1 into one command:
  ① cross-check (`names --compare` cured vs baseline, N=N ordered equality), ②
  `gate4_comment_guard --file` cured (PASS=1 FAIL=0), ③ `wrapper/gate7_probe.sh` (magic=0/0
  missing=0; optional, true compile).  Each step's pass/fail source is the canonical tool's
  own exit code only; the station composes steps, emits the ledger, never re-judges (the
  `gate7` launcher judges its own magic=0 acceptance; the report-only form rc 0 does not
  judge magic and the ledger records magic numbers as-is).  Order ①②③ is fixed (shrink
  only, never reorder); default chain = ①② (zero compile).  Zero writes by default (only
  the explicit `--station-json` and forwarded explicit `--gate4-json`/`--gate7-json`/
  `--gate7-workdir`); children run under `python3 -B`; the station never nests `cpu_guard`
  (wrapping duty sits with the caller; step ③ temperature control rides the launcher guard).
Interface.  python3 wrapper/precedent_station.py --cured C.v --baseline B.v [station flags]
  | --station-selftest.  Key flags: --cured FILE; --baseline FILE (with `names` in step);
  --knife NAME (ledger record only); --steps LIST (names,gate4,gate7; default names,gate4);
  --check-pin/--expect-names-md5/--expect-gate4-md5 HEX assert md5 values; --station-json
  PATH writes the ledger; remaining flags and the bare `--` passthrough: see -h/--help.
Dependencies.  Python 3 standard library only; step ③ shells out to bash.  Canonicals are
  named in `CANONICALS` by repository-root-relative paths; the frozen `names`/`gate4` copies
  carry embedded md5 pins and the `gate7` launcher is unfrozen (recorded, never pinned).
Evidence.  --station-selftest runs the ten-judgment self-check with zero writes and no
  canonical execution (canonical presence, pin shape, step parsing and fixed order, the
  aggregation law, the verdict tables, command assembly and the bare `--` split, input
  preflight, knife records, md5 assertion shape, ledger extraction).
Exit-codes.  0 = every in-step verdict PASS; 1 = hard failing result (`names` ordered
  inequality, `gate4` hard violation, `gate7` probe or gate failing); 2 = REVIEW-grade
  (`gate4` rc 2) or station-level (usage error, failed md5 assertion; a failed assertion
  never starts the chain); 9 = missing file or canonical (a failed preflight runs no step).
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

PROG = "precedent_station"
WRAP_NAME = "wrapper/precedent_station.py"

# - Canonical tool registry (repository-root-relative paths plus embedded md5 pins) -
# names/gate4 are in-service frozen components (pin assertion face); gate7_probe.sh is an
# in-repo adapter layer (not frozen, revisable while in service), so its md5 is recorded
# in the station ledger without a pin (recording never judges; an in-service edit cannot
# trip the pin).
CANONICALS = {
    "names": {"rel": "names/mac_stmt_names.py",
              "pin": "9e26c0db2c60ced3629a13a821bdf615"},
    "gate4": {"rel": "verify/gate4_comment_guard.py",
              "pin": "d7ab397c5f0243d0c7320f91d0f14481"},
    "gate7": {"rel": "wrapper/gate7_probe.sh",
              "pin": None},  # not frozen: recorded, never judged
}
PIN_NOTE = "names/gate4=20261031 冻结在册值；gate7 launcher=非冻结只录（20261101 实测 3bbfadfde7e5578d27047a107643d97b）"
STEP_ORDER = ("names", "gate4", "gate7")          # fixed ①②③ order (shrink only, never reorder)
STEP_DEFAULT = ("names", "gate4")                 # default light chain (gate7 explicit opt-in, true compile)
STEP_LABEL = {"names": "①对表", "gate4": "②gate4", "gate7": "③gate7"}

# Precedent knife records (legal --knife values; station-ledger record only - judgment
# sources stay with the canonical tools, repair details live in the per-repair records)
KNIVES = {
    "E7-carrier": "fa56b_ext 载体中继（证明体 Empty_set 载体→`__` 载体＋pre-map 内联 motive·对表判例 18=18·sandbox/seat_fa56re/账/R22锚换代包-fa56b.md）",
    "R23-notation": "ToyR_UpAblP7 记号重载（非语句头区 Notation 别名＋Extraction Inline 具体面·语句面 13=13 逐字守恒·sandbox/seat_toyr/账/R23锚换代包-toyr.md）",
    "E5-reanchor": "UpReqSampling 投影重锚（语句面投影→具体面三映射·51=51·处方件 recipes/S07_projection_reanchor_E5.md）",
    "custom": "自定刀面（站账只记名·处方与判例自附）",
}

# Canonical exit code -> station verdict tables (zero-judgment-copy: a verdict comes
# only from the canonical tool's own rc)
NAMES_GATE = {0: "PASS"}                            # rc 2 (inequality) and rc 9 (missing) -> FAIL
GATE4_GATE = {0: "PASS", 1: "FAIL", 2: "REVIEW"}    # REVIEW is clean only at review count 0
GATE7_GATE = {0: "PASS", 1: "FAIL"}                 # gate failing or probe failure -> FAIL; off-table rc -> FAIL

VERDICT_RANK = {"PASS": 0, "REVIEW": 1, "FAIL": 2, "MISSING": 3}
VERDICT_EXIT = {"PASS": 0, "REVIEW": 2, "FAIL": 1, "MISSING": 9}

# Station-ledger information extraction (ledger output only, never overrides judgment -
# the verdict comes only from rc; extraction failure yields a null field, reported as-is)
RE_NAMES_ASSERT = re.compile(r"断言 (\d+)=(\d+) 有序全等 : (PASS|FAIL)")
RE_GATE4_SUM = re.compile(
    r"件数=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)\s+REVIEW\(人工复核\)=(\d+)\s+UNREADABLE=(\d+)")
RE_GATE7_LINE = re.compile(
    r"GATE7 \[(\d+)/(\d+)\] (\S+) names=(\d+) rc=(\d+) magic=(\d+)/(\d+) missing=(\d+)")
RE_GATE7_CENSUS = re.compile(r"GATE7-CENSUS: modules=(\d+) magic_total=(\d+)")
RE_GATE7_GATE = re.compile(r"GATE7-(GREEN|RED): (.*)")

STATION_USAGE = """precedent_station — 三判例验收链组合器（①对表→②gate4→③gate7·wrapper/）

用法 Usage:
  python3 wrapper/precedent_station.py --cured CURED.v --baseline BASE.v [站级旗标]
  # 追加提取执行硬验收（gate7 显式选入·真编译）：
  python3 wrapper/precedent_station.py --cured C.v --baseline B.v \\
      --steps names,gate4,gate7 --gate7-tree WORLD --gate7-module MOD \\
      -- --gate --baseline BASELINE.json

站级旗标 Station flags:
  --cured FILE          刀后件（三步共同靶·必填）
  --baseline FILE       基件（names 在步时必填）
  --knife NAME          刀面记名（E7-carrier|R23-notation|E5-reanchor|custom·纯记录）
  --root DIR            正本仓根（默认＝本站所在仓根）
  --steps LIST          步子集（names,gate4,gate7·缺省 names,gate4·可减不可重排）
  --include-let/--kinds LIST/--expect-names N     ①透传 names
  --gate4-json PATH / --gate4-no-principle / --gate4-length-fail / --gate4-length-cap N
                        ②透传 gate4
  --gate7-tree DIR / --gate7-module NAME（可重复）/ --gate7-workdir DIR /
  --gate7-json PATH / --gate7-timeout SEC
                        ③gate7 launcher 形参
  --check-pin           两冻结正本嵌记 md5 断言（gate7 launcher 非冻结只录不判）
  --expect-names-md5/--expect-gate4-md5 HEX   外附断言
  --station-json PATH   站账 JSON（站唯一写面·缺省零写盘）
  --station-selftest    本站自检（十判·零写盘·不执行正本）
  -h / --help           本帮助
  -- <gate7 其余形参逐字透传>   ③首个裸 `--` 后全数透传 gate7 正本

退出码: 0=在步全绿  1=硬红（对表不等/gate4 硬违/gate7 闸红或探针败）
        2=REVIEW/站级用法·断言败  9=文件或正本缺失
"""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def default_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canonical_path(root, step):
    return os.path.join(os.path.abspath(root), *CANONICALS[step]["rel"].split("/"))


def norm_hex(s):
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def parse_steps(spec_list):
    """Parse --steps: comma-separated with repeated flags merged; an unknown step name
    raises ValueError; the requested order is discarded and the result always follows the
    fixed ①②③ order (shrink only, never reorder)."""
    got = set()
    for spec in spec_list or []:
        for tok in spec.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if tok not in STEP_ORDER:
                raise ValueError("未知步名 %r（合法：names,gate4,gate7）" % tok)
            got.add(tok)
    if not got:
        raise ValueError("--steps 解析为空")
    return [s for s in STEP_ORDER if s in got]


def check_inputs(cured, baseline, steps, gate7_tree, gate7_modules):
    """Preflight the argument shape (composition-shape face; file existence belongs to
    the main preflight). Returns an error string or None."""
    if not cured:
        return "--cured 必填（三步共同靶）"
    if "names" in steps and not baseline:
        return "--baseline 必填（①对表基准·names 在步时）"
    if cured and baseline and os.path.abspath(cured) == os.path.abspath(baseline):
        return "刀后件与对表基准同件（对表退化为恒真·拒绝）：%s" % cured
    if "gate7" in steps:
        if not gate7_tree:
            return "--gate7-tree 必填（③gate7 在步时·世界只读副本）"
        if not gate7_modules:
            return "--gate7-module 必填（③gate7 在步时·至少一名）"
    return None


def child_argv(canonical, rest):
    py = sys.executable or "python3"
    return [py, "-B", canonical] + list(rest)


def names_cmd(canonical, cured, baseline, include_let, kinds, expect_names):
    rest = [cured, "--compare", baseline]
    if include_let:
        rest.append("--include-let")
    if kinds:
        rest += ["--kinds", kinds]
    if expect_names is not None:
        rest += ["--expect", str(expect_names)]
    return child_argv(canonical, rest)


def gate4_cmd(canonical, cured, gate4_json, no_principle, length_fail, length_cap):
    rest = ["--file", cured]
    if gate4_json:
        rest += ["--json", gate4_json]
    if no_principle:
        rest.append("--no-principle")
    if length_fail:
        rest.append("--length-fail")
    if length_cap is not None:
        rest += ["--length-cap", str(length_cap)]
    return child_argv(canonical, rest)


def gate7_cmd(launcher, tree, modules, workdir, jsonout, timeout, extra):
    """Assemble the step-③ gate7 launcher command: bash launcher --tree T --module M...
    [--workdir W] [--json J] [--timeout S] [-- extra... passed through verbatim at the
    tail]."""
    cmd = ["bash", launcher, "--tree", tree]
    for m in modules:
        cmd += ["--module", m]
    if workdir:
        cmd += ["--workdir", workdir]
    if jsonout:
        cmd += ["--json", jsonout]
    if timeout is not None:
        cmd += ["--timeout", str(timeout)]
    if extra:
        cmd += ["--"] + list(extra)
    return cmd


def gate_step(table, rc):
    return table.get(rc, "FAIL")


def aggregate(verdicts):
    """Aggregation law, hardest verdict wins: MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)."""
    if not verdicts:
        return "PASS", 0
    worst = max(verdicts, key=lambda v: VERDICT_RANK[v])
    return worst, VERDICT_EXIT[worst]


def run_child(argv):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace")
    if p.stdout:
        sys.stdout.write(p.stdout)
        sys.stdout.flush()
    if p.stderr:
        sys.stderr.write(p.stderr)
        sys.stderr.flush()
    return p.returncode, p.stdout or ""


def extract_info(stdout, gate7_json_path):
    """Station-ledger information extraction (ledger output only, never overrides
    judgment; an unmatchable field is reported as None)."""
    info = {}
    m = RE_NAMES_ASSERT.search(stdout)
    if m:
        info["names_assert"] = "%s=%s %s" % (m.group(1), m.group(2), m.group(3))
    m = RE_GATE4_SUM.search(stdout)
    if m:
        info["gate4_summary"] = {"files": int(m.group(1)), "pass": int(m.group(2)),
                                 "fail": int(m.group(3)), "review": int(m.group(4)),
                                 "unreadable": int(m.group(5))}
    m = RE_GATE7_LINE.search(stdout)
    if m:
        info["gate7_line"] = {"modules": int(m.group(1)), "total": int(m.group(2)),
                              "module": m.group(3), "names": int(m.group(4)),
                              "rc": int(m.group(5)),
                              "magic_ml": int(m.group(6)), "magic_mli": int(m.group(7)),
                              "missing": int(m.group(8))}
    m = RE_GATE7_CENSUS.search(stdout)
    if m:
        info["gate7_census"] = {"modules": int(m.group(1)), "magic_total": int(m.group(2))}
    m = RE_GATE7_GATE.search(stdout)
    if m:
        info["gate7_gate"] = {"verdict": m.group(1), "detail": m.group(2).strip()}
    if gate7_json_path and os.path.isfile(gate7_json_path):
        try:
            with io.open(gate7_json_path, encoding="utf-8") as fh:
                acc = json.load(fh)
            totals = acc.get("totals")
            if isinstance(totals, dict):
                info["gate7_json_totals"] = totals
        except Exception as e:
            info["gate7_json_read_error"] = str(e)
    return info


def station_selftest():
    """Ten-judgment station self-check (zero writes, executes no canonical). Returns
    the pass boolean."""
    ok = True
    root = default_root()

    # judgment 1: the three canonicals are present (default repository root)
    found = {s: canonical_path(root, s) for s in STEP_ORDER}
    j = all(os.path.isfile(p) for p in found.values())
    print("  judge1 三正本在位(default root):", "PASS" if j else "FAIL", found)
    ok = ok and j

    # judgment 2: the frozen pins are 32-hex shape (names/gate4; the gate7 launcher has none)
    j = (all(norm_hex(CANONICALS[s]["pin"]) == CANONICALS[s]["pin"]
             for s in ("names", "gate4"))
         and CANONICALS["gate7"]["pin"] is None)
    print("  judge2 冻结嵌记形制（gate7 launcher 只录不判）:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 3: --steps parsing (subset in fixed order, unknown rejected, default light chain)
    try:
        got = parse_steps(["gate7,names"])
        j = got == ["names", "gate7"]
    except ValueError:
        got, j = None, False
    print("  judge3 steps 子集固定序:", "PASS" if j else "FAIL", got)
    try:
        parse_steps(["bogus"])
        j = False
    except ValueError:
        j = True
    print("  judge3b 未知步名拒:", "PASS" if j else "FAIL")
    j = list(STEP_DEFAULT) == ["names", "gate4"]
    print("  judge3c 缺省轻链（gate7 显式选入）:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 4: aggregation law, hardest verdict wins
    v1, e1 = aggregate(["PASS", "PASS"])
    v2, e2 = aggregate(["PASS", "REVIEW"])
    v3, e3 = aggregate(["FAIL", "REVIEW"])
    v4, e4 = aggregate(["PASS", "MISSING"])
    j = (v1, e1) == ("PASS", 0) and (v2, e2) == ("REVIEW", 2) \
        and (v3, e3) == ("FAIL", 1) and (v4, e4) == ("MISSING", 9)
    print("  judge4 聚合律硬者胜:", "PASS" if j else "FAIL",
          (v1, e1), (v2, e2), (v3, e3), (v4, e4))
    ok = ok and j

    # judgment 5: the three verdict tables
    j = (gate_step(NAMES_GATE, 0) == "PASS" and gate_step(NAMES_GATE, 2) == "FAIL"
         and gate_step(GATE4_GATE, 0) == "PASS" and gate_step(GATE4_GATE, 1) == "FAIL"
         and gate_step(GATE4_GATE, 2) == "REVIEW" and gate_step(GATE4_GATE, 7) == "FAIL"
         and gate_step(GATE7_GATE, 0) == "PASS" and gate_step(GATE7_GATE, 1) == "FAIL"
         and gate_step(GATE7_GATE, 9) == "FAIL")
    print("  judge5 判表 names/gate4/gate7:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 6: the three step command assemblies (gate7 extras pass through verbatim at the tail)
    c1 = names_cmd("/R/names.py", "c.v", "b.v", True, "Definition,Lemma", 5)
    c2 = gate4_cmd("/R/gate4.py", "c.v", "g.json", False, False, None)
    c3 = gate7_cmd("/R/gate7_probe.sh", "/W", ["Mod"], "/wd", "j.json", 600,
                   ["--gate", "--baseline", "B.json"])
    head = [sys.executable or "python3", "-B"]
    j = (c1 == head + ["/R/names.py", "c.v", "--compare", "b.v", "--include-let",
                       "--kinds", "Definition,Lemma", "--expect", "5"]
         and c2 == head + ["/R/gate4.py", "--file", "c.v", "--json", "g.json"]
         and c3 == ["bash", "/R/gate7_probe.sh", "--tree", "/W", "--module", "Mod",
                    "--workdir", "/wd", "--json", "j.json", "--timeout", "600",
                    "--", "--gate", "--baseline", "B.json"])
    # judgment 6b: the bare `--` split separates the argparse face from the gate7 passthrough face
    s_a, s_x = split_extra_argv(["--cured", "c.v", "--", "--gate", "--baseline", "B"])
    s_b, s_y = split_extra_argv(["--cured", "c.v"])
    j = j and s_a == ["--cured", "c.v"] and s_x == ["--gate", "--baseline", "B"] \
        and s_b == ["--cured", "c.v"] and s_y == []
    print("  judge6 cmd 装配＋`--`切分律:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 7: preflight shape (baseline dependency, same-file refusal, gate7 dependency declaration)
    j = (check_inputs(None, None, ["names"], None, []) is not None
         and check_inputs("c.v", None, ["gate4"], None, []) is None
         and check_inputs("c.v", None, ["names"], None, []) is not None
         and check_inputs("c.v", "b.v", ["names"], None, []) is None
         and check_inputs("c.v", "c.v", ["names"], None, []) is not None
         and check_inputs("c.v", "b.v", ["names", "gate7"], None, []) is not None
         and check_inputs("c.v", "b.v", ["names", "gate7"], "/W", []) is not None
         and check_inputs("c.v", "b.v", ["names", "gate7"], "/W", ["Mod"]) is None)
    print("  judge7 预检形制:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 8: precedent knife records (all three knives present, each with its record
    # anchors: cross-check values and ledger source paths)
    j = (all(k in KNIVES for k in ("E7-carrier", "R23-notation", "E5-reanchor", "custom"))
         and "18=18" in KNIVES["E7-carrier"] and "13=13" in KNIVES["R23-notation"]
         and "51=51" in KNIVES["E5-reanchor"]
         and "seat_fa56re" in KNIVES["E7-carrier"]
         and "seat_toyr" in KNIVES["R23-notation"]
         and "S07_projection_reanchor_E5.md" in KNIVES["E5-reanchor"])
    print("  judge8 三判例记名面:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 9: assertion shape (a valid 32-hex value passes, a bogus value is refused)
    j = (norm_hex(" 9e26c0db2c60ced3629a13a821bdf615 ") == "9e26c0db2c60ced3629a13a821bdf615"
         and norm_hex("zz") is None and norm_hex("01dc") is None)
    print("  judge9 断言形制核正过伪拒:", "PASS" if j else "FAIL")
    ok = ok and j

    # judgment 10: ledger extraction (each canonical's sample lines extract, the gate7 gate
    # wording extracts, non-matching lines stay absent)
    s1 = "file: x\ntotal: 7  let_skipped: 0\n断言 7=7 有序全等 : PASS"
    s2 = "[gate4ext] v2.1 扫描时点=T  件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  " \
         "UNREADABLE=0  length_cap=30(review)  principle=on  deep_files=0"
    s3 = ("GATE7 [1/1] ToyR_X names=13 rc=0 magic=0/0 missing=0\n"
          "GATE7-CENSUS: modules=1 magic_total=0\n"
          "GATE7-GREEN: no extraction-execution regression (modules=1)")
    i1 = extract_info(s1, None)
    i2 = extract_info(s2, None)
    i3 = extract_info(s3, None)
    i0 = extract_info("没有可抽行", None)
    j = (i1.get("names_assert") == "7=7 PASS"
         and i2.get("gate4_summary") == {"files": 1, "pass": 1, "fail": 0,
                                         "review": 0, "unreadable": 0}
         and i3.get("gate7_line") == {"modules": 1, "total": 1, "module": "ToyR_X",
                                      "names": 13, "rc": 0, "magic_ml": 0,
                                      "magic_mli": 0, "missing": 0}
         and i3.get("gate7_census") == {"modules": 1, "magic_total": 0}
         and i3.get("gate7_gate", {}).get("verdict") == "GREEN"
         and "gate7_line" not in i0 and "names_assert" not in i0)
    print("  judge10 站账抽取正/负:", "PASS" if j else "FAIL")
    ok = ok and j

    return ok


def split_extra_argv(argv):
    """Split at the first bare `--`: the head is the station parameters (the argparse
    face) and the tail is the gate7 parameters passed through verbatim (argparse cannot
    take a bare `--` as a flag value)."""
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1:]
    return argv, []


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    argv, gate7_extra = split_extra_argv(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(
        prog=PROG, description="三判例验收链组合器（①对表→②gate4→③gate7·判据零复制）",
        usage=STATION_USAGE)
    ap.add_argument("--cured", default=None, help="刀后件（三步共同靶）")
    ap.add_argument("--baseline", default=None, help="①对表基准（基件）")
    ap.add_argument("--knife", default="unspecified",
                    help="刀面记名（E7-carrier|R23-notation|E5-reanchor|custom·纯站账记录）")
    ap.add_argument("--root", default=None, help="正本仓根（默认=本站所在仓根）")
    ap.add_argument("--steps", action="append", default=None,
                    help="步子集逗号分（names,gate4,gate7·缺省 names,gate4·可减不可重排）")
    ap.add_argument("--include-let", action="store_true", help="①会师口径（Let 计入）")
    ap.add_argument("--kinds", default=None, help="①kind 过滤（透传 names --kinds）")
    ap.add_argument("--expect-names", type=int, default=None, help="①计数断言（透传 --expect）")
    ap.add_argument("--gate4-json", default=None, help="②gate4 --json 落盘路径")
    ap.add_argument("--gate4-no-principle", action="store_true", help="②关判定原则启发式")
    ap.add_argument("--gate4-length-fail", action="store_true", help="②头注超标升格硬违规")
    ap.add_argument("--gate4-length-cap", type=int, default=None, help="②头注行数帽（默认 30）")
    ap.add_argument("--gate7-tree", default=None, help="③世界只读副本目录")
    ap.add_argument("--gate7-module", action="append", default=[], metavar="NAME",
                    help="③模块名（可重复）")
    ap.add_argument("--gate7-workdir", default=None, help="③工件目录（缺省系统临时目录）")
    ap.add_argument("--gate7-json", default=None, help="③gate7 --json 出账路径")
    ap.add_argument("--gate7-timeout", type=int, default=None, help="③透传 --timeout")
    ap.add_argument("--check-pin", action="store_true",
                    help="两冻结正本嵌记 md5 断言（gate7 launcher 非冻结只录不判）")
    ap.add_argument("--expect-names-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--expect-gate4-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--station-json", default=None, help="站账 JSON（站唯一写面）")
    ap.add_argument("--station-selftest", action="store_true", help="本站自检十判")
    args = ap.parse_args(argv)

    if args.station_selftest:
        p = station_selftest()
        print("PRECEDENT-STATION-SELFTEST (wrapper 自身十判·零写盘·不执行正本):",
              "PASS" if p else "FAIL")
        sys.exit(0 if p else 2)

    if args.knife != "unspecified" and args.knife not in KNIVES:
        print("precedent_station: 站级用法错: 未知刀面 %r（合法：%s）"
              % (args.knife, "|".join(KNIVES)), file=sys.stderr)
        sys.exit(2)
    try:
        steps = parse_steps(args.steps) if args.steps else list(STEP_DEFAULT)
    except ValueError as e:
        print("precedent_station: 站级用法错: %s" % e, file=sys.stderr)
        sys.exit(2)
    err = check_inputs(args.cured, args.baseline, steps, args.gate7_tree,
                       args.gate7_module)
    if err:
        print("precedent_station: 站级用法错: %s" % err, file=sys.stderr)
        sys.exit(2)

    # - Preflight: canonical/target file existence (a failure runs no step, exit 9) -
    root = args.root if args.root else default_root()
    canon = {}
    for s in STEP_ORDER:
        p = canonical_path(root, s)
        if not os.path.isfile(p):
            print("precedent_station: 正本缺失: %s（%s·于仓根 %s）"
                  % (CANONICALS[s]["rel"], s, root), file=sys.stderr)
            sys.exit(9)
        canon[s] = p
    for label, path in (("cured", args.cured), ("baseline", args.baseline)):
        if path and not os.path.isfile(path):
            print("precedent_station: 文件缺失: %s=%s" % (label, path), file=sys.stderr)
            sys.exit(9)
    if "gate7" in steps:
        if not os.path.isdir(args.gate7_tree):
            print("precedent_station: 目录缺失: --gate7-tree=%s" % args.gate7_tree,
                  file=sys.stderr)
            sys.exit(9)
        for m in args.gate7_module:
            mv = m[:-2] if m.endswith(".v") else m
            if not (os.path.isfile(os.path.join(args.gate7_tree, mv + ".v"))
                    or os.path.isfile(os.path.join(args.gate7_tree, m))):
                print("precedent_station: 模块 .v 不在世界副本中: %s/%s.v"
                      % (args.gate7_tree, mv), file=sys.stderr)
                sys.exit(9)

    # - Embedded/external md5 assertions (failure prints to stderr and exits 2; the chain
    # never starts with a failed assertion) -
    actual = {s: md5_of(canon[s]) for s in STEP_ORDER}
    expects = {"names": args.expect_names_md5, "gate4": args.expect_gate4_md5}
    bad = []
    for s in ("names", "gate4"):
        for e in expects[s]:
            v = norm_hex(e)
            if v is None or v != actual[s]:
                bad.append((s, e, actual[s]))
        if args.check_pin and CANONICALS[s]["pin"] != actual[s]:
            bad.append((s, "pin:%s" % CANONICALS[s]["pin"], actual[s]))
    if bad:
        for s, want, act in bad:
            print("precedent_station: md5 断言不符 [%s] want=%s actual=%s"
                  % (s, want, act), file=sys.stderr)
        print("precedent_station: 断言败·不带病开步（正本若经冻终权威改版须由适配席重嵌记）",
              file=sys.stderr)
        sys.exit(2)

    # - Run the steps: fixed order ①->②->③, every step reports into the ledger (the
    # combiner aggregates all steps, never short-circuits) -
    print("== precedent_station 三判例验收链（%s）==" % WRAP_NAME)
    print("cured:    %s" % args.cured)
    print("baseline: %s" % (args.baseline or "—（names 不在步）"))
    print("knife:    %s%s" % (args.knife,
                              ("（%s）" % KNIVES[args.knife]) if args.knife in KNIVES else ""))
    for s in STEP_ORDER:
        pin = CANONICALS[s]["pin"]
        print("canonical[%s]: %s  md5=%s  %s"
              % (s, canon[s], actual[s],
                 ("pin_match=%s" % (pin == actual[s])) if pin else "pin=None（非冻结·只录不判）"))

    step_rows = {}
    child_stdout = {}
    workdir = args.gate7_workdir
    if "gate7" in steps and not workdir:
        workdir = os.path.join(tempfile.gettempdir(), "precedent_station_g7")
    for s in steps:
        if s == "names":
            full = names_cmd(canon[s], args.cured, args.baseline,
                             args.include_let, args.kinds, args.expect_names)
        elif s == "gate4":
            full = gate4_cmd(canon[s], args.cured, args.gate4_json,
                             args.gate4_no_principle, args.gate4_length_fail,
                             args.gate4_length_cap)
        else:
            full = gate7_cmd(canon[s], args.gate7_tree, args.gate7_module, workdir,
                             args.gate7_json, args.gate7_timeout, gate7_extra)
        print("-- %s 直调 %s" % (STEP_LABEL[s], CANONICALS[s]["rel"]), file=sys.stderr)
        rc, out = run_child(full)
        verdict = gate_step({"names": NAMES_GATE, "gate4": GATE4_GATE,
                             "gate7": GATE7_GATE}[s], rc)
        step_rows[s] = {"rc": rc, "verdict": verdict}
        child_stdout[s] = out

    # - Station-ledger information extraction (ledger output, never overrides judgment) -
    info = {}
    if "names" in child_stdout:
        info.update(extract_info(child_stdout["names"], None))
    if "gate4" in child_stdout:
        info.update(extract_info(child_stdout["gate4"], None))
    if "gate7" in child_stdout:
        info.update(extract_info(child_stdout["gate7"], args.gate7_json))

    verdicts = [step_rows[s]["verdict"] for s in steps]
    verdict, exit_code = aggregate(verdicts)

    print("--- 站账：steps=%s knife=%s" % ("+".join(steps), args.knife))
    for s in steps:
        r = step_rows[s]
        note = ""
        if s == "names" and info.get("names_assert"):
            note = "（断言 %s）" % info["names_assert"]
        elif s == "gate4" and info.get("gate4_summary"):
            g = info["gate4_summary"]
            note = "（件数=%d PASS=%d FAIL=%d REVIEW=%d）" % (g["files"], g["pass"],
                                                             g["fail"], g["review"])
        elif s == "gate7":
            g7 = info.get("gate7_line")
            if g7:
                note = "（names=%d magic=%d/%d missing=%d·录词不覆判）" % (
                    g7["names"], g7["magic_ml"], g7["magic_mli"], g7["missing"])
            gg = info.get("gate7_gate")
            if gg:
                note += " gate=%s" % gg["verdict"]
        print("  %s %-6s rc=%-3d %-6s %s" % (STEP_LABEL[s], s, r["rc"], r["verdict"], note))
    print("verdict: %s" % verdict)

    if args.station_json:
        acc = {
            "station": WRAP_NAME, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "root": root, "knife": args.knife,
            "cured": {"path": args.cured, "md5": md5_of(args.cured)},
            "baseline": ({"path": args.baseline, "md5": md5_of(args.baseline)}
                         if args.baseline and "names" in steps else None),
            "canonicals": {s: {"rel": CANONICALS[s]["rel"], "md5": actual[s],
                               "pin": CANONICALS[s]["pin"],
                               "pin_match": (CANONICALS[s]["pin"] == actual[s])
                               if CANONICALS[s]["pin"] else None}
                           for s in STEP_ORDER},
            "steps": step_rows, "info": info, "verdict": verdict, "exit_code": exit_code,
        }
        with io.open(args.station_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("station-json ->", args.station_json)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
