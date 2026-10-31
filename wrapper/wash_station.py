#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""wash_station.py — 洗形⑤⑥⑦三步组合器（rocqwash wrapper/·适配席 rqadapt·20261031）

在役冻结件零改适配（各在飞席位实时引用·适配一律新文件 wrapper/）：本站把 nw8+ 洗形席
候批账「三、born／R4／对表／gate4／探针（⑤⑥⑦）」节里的三步 ad-hoc 手工循环——
  ⑤对表  names/mac_stmt_names.py  work/X.v --compare src/X.v   （N=N 有序全等断言）
  ⑥gate4 verify/gate4_comment_guard.py --file work/X.v          （头注五字段机检 v2.1 EXT）
  ⑦探针  seam/seam_probe.py --file work/X.v                     （W13 四机制指纹候选）
1:1 组合为一条站命令，全部直调冻结正本（subprocess `python3 -B <正本绝对路径>`），
零改冻结、判据零复制——三步红绿唯一判据源仍为各冻结正本自身退出码；本站只组合、
出站账、聚合退出码（对齐 scan_station.py「只指认＋透传」与 gate7_probe.sh
「判据零复制」适配纪律）。

域注记（双域各安其位·承 seam 补齐轮判定）：⑦＝W13 源面代际缝**指纹候选**探针
（E364 盲区律：命中=候选非定谳、0 命中=无候选出账非「无缝」——报清单不报清白），
供洗形②分诊 probe-first 与续洗台账驱动；它不是 gate7 提取执行闸
（ConstructiveWorld-Set scripts/gates/gate7_extract_run.py·仓外正本只读）的替代，
提取闸红绿仍走 wrapper/gate7_probe.sh 链。

九步洗形中的位置（承 seat_nw8 候批账小节编号）：⑤对表→⑥gate4→⑦探针，顺序固定；
--steps 可减步不可重排（组合器契约）。

用法：
  python3 wrapper/wash_station.py --washed work/X.v --baseline src/X.v [站级旗标]

站级旗标：
  --washed FILE            洗后件（⑤⑥⑦ 共同靶·必填）
  --baseline FILE          ⑤对表基准（洗前源·names 在步时必填）
  --root DIR               冻结正本仓根（默认＝本包装所在仓根）
  --steps LIST             步子集逗号分（names,gate4,probe·默认三步全开·可减不可重排）
  --include-let            ⑤会师口径（Let 计入）·1:1 透传 names --include-let
  --kinds LIST             ⑤kind 过滤·1:1 透传 names --kinds
  --expect-names N         ⑤计数断言·1:1 透传 names --expect
  --gate4-json PATH        ⑥gate4 --json 落盘（由冻结件自写·站只转交路径）
  --gate4-no-principle     ⑥关判定原则启发式（默认开·承 nw8 v2.1 EXT principle=on 口径）
  --gate4-length-fail      ⑥头注超标升格硬违规（默认复核级）
  --gate4-length-cap N     ⑥头注行数帽（默认 30＝冻结件默认）
  --probe-json PATH        ⑦探针 --json 落盘（站读其 hits 出站账）
  --probe-csv PATH         ⑦探针 --hits-csv 落盘
  --check-pin              三正本嵌记 md5 断言（20261031 适配时实测·任一不符 exit 2 不开步）
  --expect-names-md5 HEX / --expect-gate4-md5 HEX / --expect-probe-md5 HEX
                           外附 md5 断言（各自对应正本·可并用）
  --station-json PATH      站账 JSON（三步 rc/verdict/摘要·站唯一写面·缺省零写盘）
  --station-selftest       本站自检（九判·零写盘·不执行任何冻结件）
  -h / --help              本站帮助

退出码（聚合律·硬者胜）：0=三步全绿（⑤ rc=0 ∧ ⑥ rc=0 ∧ ⑦ rc=0——探针命中是候选
非失败·E364 律）；1=硬红（⑤ rc≠0 名面 N≠N／⑥ rc=1 硬违规／⑦ rc≠0 出账失败）；
2=复核级或站级（⑥ rc=2 REVIEW 项／站级用法错／md5 断言败——断言败绝不带病开步）；
9=文件或正本缺失（washed/baseline/任一正本·预检不过零开步）。

幂等律：本包装自身零写盘（不写正本、不写仓、不写临时）——唯一写面＝用户显式指定的
--station-json（及转交各冻结件的用户显式 --gate4-json/--probe-json/--probe-csv）。
子进程一律 `python3 -B`（禁 __pycache__ 落只读面）；站内禁套 cpu_guard（嵌套死锁
判例 seat_nw8——包裹义务在调用席，席位纪律同 nw8「零裸调」惯例）。
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

PROG = "wash_station"
WRAP_NAME = "wrapper/wash_station.py"

# —— 冻结正本指认（相对仓根路径＋20261031 适配时实测嵌记 md5）——
# 正本若经冻终权威改版，须由适配席对实盘重嵌记；本站不擅改正本。
CANONICALS = {
    "names": {"rel": "names/mac_stmt_names.py",
              "pin": "01dc635ce445b05628bdd6e728990ce3"},
    "gate4": {"rel": "verify/gate4_comment_guard.py",
              "pin": "d7ab397c5f0243d0c7320f91d0f14481"},
    "probe": {"rel": "seam/seam_probe.py",
              "pin": "7a01359a22b8960b352191f1a4490b37"},
}
PIN_NOTE = "20261031 rqadapt 适配时嵌记"
STEP_ORDER = ("names", "gate4", "probe")          # ⑤⑥⑦ 固定序（可减不可重排）
STEP_LABEL = {"names": "⑤对表", "gate4": "⑥gate4", "probe": "⑦探针"}

# 各冻结件退出码→站内 verdict 判表（判据零复制：verdict 唯一源自正本自身 rc）
NAMES_GATE = {0: "PASS"}                            # 其余（2=不等 9=缺件）→ FAIL
GATE4_GATE = {0: "PASS", 1: "FAIL", 2: "REVIEW"}    # nw8 口径：REVIEW=0 才算净
PROBE_GATE = {0: "PASS"}                            # 命中=候选非失败（E364 律）；rc≠0=出账失败

VERDICT_RANK = {"PASS": 0, "REVIEW": 1, "FAIL": 2, "MISSING": 3}
VERDICT_EXIT = {"PASS": 0, "REVIEW": 2, "FAIL": 1, "MISSING": 9}

# 站账信息抽取（仅出账·永不覆判——verdict 唯一源自 rc；抽取失败=字段 null 如实出）
RE_NAMES_ASSERT = re.compile(r"断言 (\d+)=(\d+) 有序全等 : (PASS|FAIL)")
RE_NAMES_TOTAL = re.compile(r"^total: (\d+)", re.M)
RE_GATE4_SUM = re.compile(
    r"件数=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)\s+REVIEW\(人工复核\)=(\d+)\s+UNREADABLE=(\d+)")
RE_PROBE_TOTAL = re.compile(r"^TOTAL: (\d+) 候选", re.M)

STATION_USAGE = """wash_station — 洗形⑤⑥⑦三步组合器（wrapper/）

用法 Usage:
  python3 wrapper/wash_station.py --washed WORK.v --baseline SRC.v [站级旗标]

站级旗标 Station flags:
  --washed FILE         洗后件（三步共同靶·必填）
  --baseline FILE       ⑤对表基准（names 在步时必填）
  --root DIR            冻结正本仓根（默认＝本包装所在仓根）
  --steps LIST          步子集逗号分（names,gate4,probe·默认全开·可减不可重排）
  --include-let/--kinds LIST/--expect-names N     ⑤透传 names
  --gate4-json PATH / --gate4-no-principle / --gate4-length-fail / --gate4-length-cap N
                        ⑥透传 gate4
  --probe-json PATH / --probe-csv PATH            ⑦透传 seam_probe
  --check-pin           三正本嵌记 md5 断言（20261031）
  --expect-names-md5/--expect-gate4-md5/--expect-probe-md5 HEX   外附断言
  --station-json PATH   站账 JSON（站唯一写面·缺省零写盘）
  --station-selftest    本站自检（九判·零写盘·不执行冻结件）
  -h / --help           本帮助

退出码: 0=三步全绿  1=硬红（对表不等/gate4 硬违/探针出账败）  2=REVIEW/站级用法·断言败
        9=文件或正本缺失
"""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def default_root():
    """默认正本仓根＝本包装文件的上上级目录（wrapper/ 的父目录）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canonical_path(root, step):
    return os.path.join(os.path.abspath(root), *CANONICALS[step]["rel"].split("/"))


def norm_hex(s):
    """断言值形制核：剥空白/引号、小写；非 32 位 hex 回 None。"""
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def parse_steps(spec_list):
    """--steps 解析：逗号分＋重复旗标合并；未知步名 raise ValueError；
    重排丢弃——恒归 ⑤⑥⑦ 固定序（组合器契约：可减不可重排）。"""
    got = set()
    for spec in spec_list or []:
        for tok in spec.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if tok not in STEP_ORDER:
                raise ValueError("未知步名 %r（合法：names,gate4,probe）" % tok)
            got.add(tok)
    if not got:
        raise ValueError("--steps 解析为空")
    return [s for s in STEP_ORDER if s in got]


def check_inputs(washed, baseline, steps):
    """预检形制：返回错误串或 None（文件存在性由 main 预检·此处只查组合形制）。"""
    if not washed:
        return "--washed 必填（三步共同靶）"
    if "names" in steps and not baseline:
        return "--baseline 必填（⑤对表基准·names 在步时）"
    if washed and baseline and os.path.abspath(washed) == os.path.abspath(baseline):
        return "洗后件与对表基准同件（对表退化为恒真·拒绝）：%s" % washed
    return None


def child_argv(canonical, rest):
    """子进程直调形：[python, -B, 冻结正本绝对路径, ...透传参]。-B 禁 __pycache__。"""
    py = sys.executable or "python3"
    return [py, "-B", canonical] + list(rest)


def names_cmd(canonical, washed, baseline, include_let, kinds, expect_names):
    rest = [washed, "--compare", baseline]
    if include_let:
        rest.append("--include-let")
    if kinds:
        rest += ["--kinds", kinds]
    if expect_names is not None:
        rest += ["--expect", str(expect_names)]
    return child_argv(canonical, rest)


def gate4_cmd(canonical, washed, gate4_json, no_principle, length_fail, length_cap):
    rest = ["--file", washed]
    if gate4_json:
        rest += ["--json", gate4_json]
    if no_principle:
        rest.append("--no-principle")
    if length_fail:
        rest.append("--length-fail")
    if length_cap is not None:
        rest += ["--length-cap", str(length_cap)]
    return child_argv(canonical, rest)


def probe_cmd(canonical, washed, probe_json, probe_csv):
    rest = ["--file", washed]
    if probe_json:
        rest += ["--json", probe_json]
    if probe_csv:
        rest += ["--hits-csv", probe_csv]
    return child_argv(canonical, rest)


def gate_step(table, rc):
    """判表查 verdict；表外 rc 一律 FAIL（fail-loud 不放水）。"""
    return table.get(rc, "FAIL")


def aggregate(verdicts):
    """聚合律·硬者胜：MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)。"""
    if not verdicts:
        return "PASS", 0
    worst = max(verdicts, key=lambda v: VERDICT_RANK[v])
    return worst, VERDICT_EXIT[worst]


def run_child(argv):
    """直调冻结件：子进程捕获→逐字回显（操作手可见性同 ad-hoc 循环）；rc 原样上呈。"""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding="utf-8", errors="replace")
    if p.stdout:
        sys.stdout.write(p.stdout)
        sys.stdout.flush()
    if p.stderr:
        sys.stderr.write(p.stderr)
        sys.stderr.flush()
    return p.returncode, p.stdout or ""


def extract_info(stdout, probe_json_path):
    """站账信息抽取（出账用·永不覆判；抽不到=None 如实出）。"""
    info = {}
    m = RE_NAMES_ASSERT.search(stdout)
    if m:
        info["names_assert"] = "%s=%s %s" % (m.group(1), m.group(2), m.group(3))
    m = RE_NAMES_TOTAL.search(stdout)
    if m:
        info["names_total"] = int(m.group(1))
    m = RE_GATE4_SUM.search(stdout)
    if m:
        info["gate4_summary"] = {"files": int(m.group(1)), "pass": int(m.group(2)),
                                 "fail": int(m.group(3)), "review": int(m.group(4)),
                                 "unreadable": int(m.group(5))}
    m = RE_PROBE_TOTAL.search(stdout)
    hits_total = int(m.group(1)) if m else None
    per_lane = None
    if probe_json_path and os.path.isfile(probe_json_path):
        try:
            with io.open(probe_json_path, encoding="utf-8") as fh:
                acc = json.load(fh)
            hits = acc.get("hits")
            if isinstance(hits, list):
                hits_total = len(hits)
                per_lane = {}
                for h in hits:
                    lane = h.get("lane")
                    if lane:
                        per_lane[lane] = per_lane.get(lane, 0) + 1
        except Exception as e:
            info["probe_json_read_error"] = str(e)
    if hits_total is not None:
        info["probe_hits_total"] = hits_total
    if per_lane is not None:
        info["probe_hits_per_lane"] = per_lane
    return info


def station_selftest():
    """本站自检九判（零写盘·不执行任何冻结件）。回 pass 布尔。"""
    ok = True
    root = default_root()

    # 判1 三正本在位（默认仓根）
    found = {s: canonical_path(root, s) for s in STEP_ORDER}
    j = all(os.path.isfile(p) for p in found.values())
    print("  judge1 三正本在位(default root):", "PASS" if j else "FAIL", found)
    ok = ok and j

    # 判2 三嵌记 32-hex 形制
    j = all(norm_hex(CANONICALS[s]["pin"]) == CANONICALS[s]["pin"] for s in STEP_ORDER)
    print("  judge2 三嵌记 32-hex 形制:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判3 --steps 解析：子集固定序（可减不可重排）＋未知步名拒
    try:
        got = parse_steps(["probe,names"])
        j = got == ["names", "probe"]
    except ValueError:
        got, j = None, False
    print("  judge3 steps 子集固定序:", "PASS" if j else "FAIL", got)
    try:
        parse_steps(["bogus"])
        j = False
    except ValueError:
        j = True
    print("  judge3b 未知步名拒:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判4 聚合律硬者胜
    v1, e1 = aggregate(["PASS", "PASS", "PASS"])
    v2, e2 = aggregate(["PASS", "REVIEW"])
    v3, e3 = aggregate(["FAIL", "REVIEW"])
    v4, e4 = aggregate(["PASS", "MISSING"])
    j = (v1, e1) == ("PASS", 0) and (v2, e2) == ("REVIEW", 2) \
        and (v3, e3) == ("FAIL", 1) and (v4, e4) == ("MISSING", 9)
    print("  judge4 聚合律硬者胜:", "PASS" if j else "FAIL",
          (v1, e1), (v2, e2), (v3, e3), (v4, e4))
    ok = ok and j

    # 判5 三判表
    j = (gate_step(NAMES_GATE, 0) == "PASS" and gate_step(NAMES_GATE, 2) == "FAIL"
         and gate_step(GATE4_GATE, 0) == "PASS" and gate_step(GATE4_GATE, 1) == "FAIL"
         and gate_step(GATE4_GATE, 2) == "REVIEW" and gate_step(GATE4_GATE, 7) == "FAIL"
         and gate_step(PROBE_GATE, 0) == "PASS" and gate_step(PROBE_GATE, 9) == "FAIL")
    print("  judge5 判表 names/gate4/probe:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判6 三步 cmd 装配（子进程直调形·[python, -B, 正本, ...透传]）
    c1 = names_cmd("/R/names.py", "w.v", "b.v", True, "Definition,Lemma", 5)
    c2 = gate4_cmd("/R/gate4.py", "w.v", "g.json", False, False, None)
    c3 = probe_cmd("/R/probe.py", "w.v", "p.json", "p.csv")
    head = [sys.executable or "python3", "-B"]
    j = (c1 == head + ["/R/names.py", "w.v", "--compare", "b.v", "--include-let",
                       "--kinds", "Definition,Lemma", "--expect", "5"]
         and c2 == head + ["/R/gate4.py", "--file", "w.v", "--json", "g.json"]
         and c3 == head + ["/R/probe.py", "--file", "w.v", "--json", "p.json",
                           "--hits-csv", "p.csv"])
    print("  judge6 cmd 装配:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判7 预检形制：baseline 依存＋同件拒绝
    j = (check_inputs(None, None, ["names"]) is not None
         and check_inputs("w.v", None, ["probe"]) is None
         and check_inputs("w.v", None, ["names"]) is not None
         and check_inputs("w.v", "b.v", ["names"]) is None
         and check_inputs("w.v", "w.v", ["names"]) is not None)
    print("  judge7 预检形制:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判8 站账抽取：三冻结件样例行各抽出＋非匹配行如实 None
    s1 = "file: x\nmd5: ab\ntotal: 7  let_skipped: 0\n断言 7=7 有序全等 : PASS"
    s2 = "[gate4ext] v2.1 扫描时点=T  件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  " \
         "UNREADABLE=0  length_cap=30(review)  principle=on  deep_files=0"
    s3 = "TOTAL: 3 候选"
    i1 = extract_info(s1, None)
    i2 = extract_info(s2, None)
    i3 = extract_info(s3, None)
    i0 = extract_info("没有可抽行", None)
    j = (i1.get("names_total") == 7 and i1.get("names_assert") == "7=7 PASS"
         and i2.get("gate4_summary") == {"files": 1, "pass": 1, "fail": 0,
                                         "review": 0, "unreadable": 0}
         and i3.get("probe_hits_total") == 3
         and "probe_hits_total" not in i0 and "names_total" not in i0)
    print("  judge8 站账抽取正/负:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判9 断言形制核：32-hex 正过、伪值拒
    j = (norm_hex(" 01dc635ce445b05628bdd6e728990ce3 ") == "01dc635ce445b05628bdd6e728990ce3"
         and norm_hex("zz") is None and norm_hex("01dc") is None)
    print("  judge9 断言形制核正过伪拒:", "PASS" if j else "FAIL")
    ok = ok and j

    return ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(prog=PROG, description="洗形⑤⑥⑦三步组合器（直调冻结件·零改冻结）",
                                 usage=STATION_USAGE)
    ap.add_argument("--washed", default=None, help="洗后件（三步共同靶）")
    ap.add_argument("--baseline", default=None, help="⑤对表基准（洗前源）")
    ap.add_argument("--root", default=None, help="冻结正本仓根（默认=本包装所在仓根）")
    ap.add_argument("--steps", action="append", default=None,
                    help="步子集逗号分（names,gate4,probe·默认全开·可减不可重排）")
    ap.add_argument("--include-let", action="store_true", help="⑤会师口径（Let 计入）")
    ap.add_argument("--kinds", default=None, help="⑤kind 过滤（透传 names --kinds）")
    ap.add_argument("--expect-names", type=int, default=None, help="⑤计数断言（透传 --expect）")
    ap.add_argument("--gate4-json", default=None, help="⑥gate4 --json 落盘路径")
    ap.add_argument("--gate4-no-principle", action="store_true", help="⑥关判定原则启发式")
    ap.add_argument("--gate4-length-fail", action="store_true", help="⑥头注超标升格硬违规")
    ap.add_argument("--gate4-length-cap", type=int, default=None, help="⑥头注行数帽（默认 30）")
    ap.add_argument("--probe-json", default=None, help="⑦探针 --json 落盘路径")
    ap.add_argument("--probe-csv", default=None, help="⑦探针 --hits-csv 落盘路径")
    ap.add_argument("--check-pin", action="store_true", help="三正本嵌记 md5 断言")
    ap.add_argument("--expect-names-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--expect-gate4-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--expect-probe-md5", action="append", default=[], metavar="HEX")
    ap.add_argument("--station-json", default=None, help="站账 JSON（站唯一写面）")
    ap.add_argument("--station-selftest", action="store_true", help="本站自检九判")
    args = ap.parse_args(argv)

    if args.station_selftest:
        p = station_selftest()
        print("WASH-STATION-SELFTEST (wrapper 自身九判·零写盘·不执行冻结件):",
              "PASS" if p else "FAIL")
        sys.exit(0 if p else 2)

    try:
        steps = parse_steps(args.steps) if args.steps else list(STEP_ORDER)
    except ValueError as e:
        print("wash_station: 站级用法错: %s" % e, file=sys.stderr)
        sys.exit(2)
    err = check_inputs(args.washed, args.baseline, steps)
    if err:
        print("wash_station: 站级用法错: %s" % err, file=sys.stderr)
        sys.exit(2)

    # —— 预检：正本/靶件存在性（不过零开步·exit 9）——
    root = args.root if args.root else default_root()
    canon = {}
    for s in STEP_ORDER:
        p = canonical_path(root, s)
        if not os.path.isfile(p):
            print("wash_station: 正本缺失: %s（%s·于仓根 %s）" % (CANONICALS[s]["rel"], s, root),
                  file=sys.stderr)
            sys.exit(9)
        canon[s] = p
    for label, path in (("washed", args.washed), ("baseline", args.baseline)):
        if path and not os.path.isfile(path):
            print("wash_station: 文件缺失: %s=%s" % (label, path), file=sys.stderr)
            sys.exit(9)

    # —— 嵌记/外附 md5 断言（败→卡出 stderr·exit 2·绝不带病开步）——
    actual = {s: md5_of(canon[s]) for s in STEP_ORDER}
    expects = {"names": args.expect_names_md5, "gate4": args.expect_gate4_md5,
               "probe": args.expect_probe_md5}
    bad = []
    for s in STEP_ORDER:
        for e in expects[s]:
            v = norm_hex(e)
            if v is None or v != actual[s]:
                bad.append((s, e, actual[s]))
        if args.check_pin and CANONICALS[s]["pin"] != actual[s]:
            bad.append((s, "pin:%s" % CANONICALS[s]["pin"], actual[s]))
    if bad:
        for s, want, act in bad:
            print("wash_station: md5 断言不符 [%s] want=%s actual=%s" % (s, want, act),
                  file=sys.stderr)
        print("wash_station: 断言败·不带病开步（正本若经冻终权威改版须由适配席重嵌记）",
              file=sys.stderr)
        sys.exit(2)

    # —— 开步：⑤→⑥→⑦ 固定序·全步出账（组合器＝全账聚合·不短路）——
    print("== wash_station 洗形⑤⑥⑦ 三步组合（%s）==" % WRAP_NAME)
    print("washed:   %s" % args.washed)
    print("baseline: %s" % (args.baseline or "—（names 不在步）"))
    for s in STEP_ORDER:
        print("canonical[%s]: %s  md5=%s  pin_match=%s"
              % (s, canon[s], actual[s], CANONICALS[s]["pin"] == actual[s]))

    step_rows = {}
    child_stdout = {}
    for s in steps:
        if s == "names":
            full = names_cmd(canon[s], args.washed, args.baseline,
                             args.include_let, args.kinds, args.expect_names)
        elif s == "gate4":
            full = gate4_cmd(canon[s], args.washed, args.gate4_json,
                             args.gate4_no_principle, args.gate4_length_fail,
                             args.gate4_length_cap)
        else:
            full = probe_cmd(canon[s], args.washed, args.probe_json, args.probe_csv)
        print("-- %s 直调 %s" % (STEP_LABEL[s], CANONICALS[s]["rel"]), file=sys.stderr)
        rc, out = run_child(full)
        verdict = gate_step({"names": NAMES_GATE, "gate4": GATE4_GATE,
                             "probe": PROBE_GATE}[s], rc)
        step_rows[s] = {"rc": rc, "verdict": verdict}
        child_stdout[s] = out

    # —— 站账信息抽取（出账·永不覆判）——
    info = {}
    if "names" in child_stdout:
        info.update(extract_info(child_stdout["names"], None))
    if "gate4" in child_stdout:
        info.update(extract_info(child_stdout["gate4"], None))
    if "probe" in child_stdout:
        info.update(extract_info(child_stdout["probe"], args.probe_json))

    verdicts = [step_rows[s]["verdict"] for s in steps]
    verdict, exit_code = aggregate(verdicts)

    print("--- 站账：steps=%s" % "+".join(steps))
    for s in steps:
        r = step_rows[s]
        note = ""
        if s == "names" and info.get("names_assert"):
            note = "（断言 %s·total=%s）" % (info["names_assert"], info.get("names_total", "?"))
        elif s == "gate4" and info.get("gate4_summary"):
            g = info["gate4_summary"]
            note = "（件数=%d PASS=%d FAIL=%d REVIEW=%d）" % (g["files"], g["pass"],
                                                             g["fail"], g["review"])
        elif s == "probe" and info.get("probe_hits_total") is not None:
            note = "（TOTAL %d 候选·E364 候选非定谳）" % info["probe_hits_total"]
        print("  %s %-6s rc=%-3d %-6s %s" % (STEP_LABEL[s], s, r["rc"], r["verdict"], note))
    print("verdict: %s" % verdict)

    if args.station_json:
        acc = {
            "station": WRAP_NAME, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "root": root, "washed": {"path": args.washed, "md5": md5_of(args.washed)},
            "baseline": ({"path": args.baseline, "md5": md5_of(args.baseline)}
                         if args.baseline and "names" in steps else None),
            "canonicals": {s: {"rel": CANONICALS[s]["rel"], "md5": actual[s],
                               "pin": CANONICALS[s]["pin"],
                               "pin_match": CANONICALS[s]["pin"] == actual[s]}
                           for s in STEP_ORDER},
            "steps": step_rows, "info": info, "verdict": verdict, "exit_code": exit_code,
        }
        with io.open(args.station_json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("station-json ->", args.station_json)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
