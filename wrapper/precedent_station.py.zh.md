#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""precedent_station.py — 三判例验收链组合器（rocqwash wrapper/·巡检打磨席 rqsup4·20261101）

五课件⑤【三判例剧本 toolify】。三个已愈判例（提取面 Obj.magic 病·三刀各异）的
验收链是同一条——各判例席曾各自 ad-hoc 手跑同一三连，本站把这条**共用验收链**
1:1 组合为一条站命令（wash_station.py 同款组合器形·姊妹站）：

  判例（刀面各异）                        验收链（三连共用）
  ────────────────────────────────      ──────────────────────────────────────
  E7 载体中继（fa56b_ext·seat_fa56re）    ①对表   names --compare 刀后件 vs 基件
    证明体 Empty_set 载体→`__` 载体                → N=N 有序全等（18=18 判例）
    ＋pre-map 内联 motive                    ②gate4 gate4_comment_guard --file
  R23 记号重载（ToyR_UpAblP7·seat_toyr）         刀后件 → PASS=1 FAIL=0（五禁词 0）
    非语句头区加 Notation 别名＋            ③gate7 gate7_probe.sh（可选步·重）
    Extraction Inline 具体面                       → magic=0/0 missing=0（硬验收）
  E5 投影重锚（UpReqSampling·seat_reanchor）      语句面零动判例 13=13／51=51 在卷
    语句面投影→具体面三映射重锚
    （处方件 recipes/S07_projection_reanchor_E5.md）

判据零复制律：三步红绿唯一判据源＝各正本自身退出码（names rc／gate4 rc／gate7
launcher 透传 rc）——本站只组合、出站账、聚合退出码。gate7 的 magic=0 硬验收由
gate7 正本自身判（调用者经裸 `--` 透传闸形 `… -- --gate --baseline B`；report-only
形 rc 0 不判 magic——站账只**如实录** magic 数，录词永不覆判）。

三步位置与序：①对表→②gate4→③gate7，顺序固定；--steps 可减不可重排（组合器
契约）。**缺省＝①②轻链**（零编译）；③gate7 为显式选入步（真编译重步——需世界
副本 --gate7-tree＋--gate7-module，编译整经 wrapper/gate7_probe.sh 内建 guard）。

用法：
  python3 wrapper/precedent_station.py --cured work/X.v --baseline src/X.v [站级旗标]
  # 追加提取执行硬验收（世界只读副本自备）：
  python3 wrapper/precedent_station.py --cured work/X.v --baseline src/X.v \
      --steps names,gate4,gate7 --gate7-tree <world> --gate7-module X \
      --gate7-workdir <dir> -- --gate --baseline gate7_extract_baseline.json

站级旗标：
  --cured FILE             刀后件（①②③ 共同靶·必填）
  --baseline FILE          基件（①对表基准·names 在步时必填）
  --knife NAME             刀面记名（E7-carrier|R23-notation|E5-reanchor|custom·
                           纯站账记录面·不影响任何判词）
  --root DIR               正本仓根（默认＝本站文件所在仓根）
  --steps LIST             步子集逗号分（names,gate4,gate7·缺省 names,gate4·
                           可减不可重排；gate7 显式选入）
  --include-let/--kinds/--expect-names   ①1:1 透传 names
  --gate4-json/--gate4-no-principle/--gate4-length-fail/--gate4-length-cap
                           ②1:1 透传 gate4
  --gate7-tree DIR         ③世界只读副本（gate7 在步时必填）
  --gate7-module NAME      ③模块名（可重复·gate7 在步时必填；须有 <tree>/<名>.v）
  --gate7-workdir DIR      ③工件目录（缺省 <tmp>/precedent_station_g7）
  --gate7-json PATH        ③gate7 --json 出账路径（站账读其 totals 录 magic）
  --gate7-timeout SEC      ③透传 --timeout
  -- <gate7 其余形参逐字透传>   ③首个裸 `--` 后形参全数透传 gate7 正本
                           （world_hook 同款切分律·如 -- --gate --baseline B）
  --check-pin              两冻结正本嵌记 md5 断言（gate7 launcher 非冻结件·只录不判）
  --expect-names-md5 HEX / --expect-gate4-md5 HEX   外附 md5 断言（可并用）
  --station-json PATH      站账 JSON（站唯一写面·缺省零写盘）
  --station-selftest       本站自检（十判·零写盘·不执行任何正本）
  -h / --help              本站帮助

退出码（聚合律·硬者胜·承 wash_station 同款）：0=在步全绿（① rc=0 ∧ ② rc=0 ∧
[③ rc=0]）；1=硬红（① rc≠0 名面 N≠N／② rc=1 硬违规／③ rc≠0 探针或闸红）；
2=复核级或站级（② rc=2 REVIEW／站级用法错／md5 断言败——断言败绝不带病开步）；
9=文件或正本缺失（cured/baseline/正本/gate7 树或模块 .v——预检不过零开步）。

幂等律：本站自身零写盘（唯一写面＝用户显式 --station-json 及转交正本的用户显式
--gate4-json/--gate7-json/--gate7-workdir）；子进程一律 `python3 -B`（gate7 步经
launcher 内建 `python3 -B`）；站内禁套 cpu_guard（嵌套死锁判例 seat_nw8——包裹
义务在调用席；gate7 步的编译温控由 launcher 内建 guard 承担）。
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

# —— 正本指认（相对仓根路径＋嵌记 md5）——
# names/gate4 为在役冻结件（pin 断言面）；gate7_probe.sh 为仓内适配层（非冻结·
# 在飞席位可持续改版）——其 md5 只录站账不设 pin（录词不判·防在飞误红）。
CANONICALS = {
    "names": {"rel": "names/mac_stmt_names.py",
              "pin": "9e26c0db2c60ced3629a13a821bdf615"},
    "gate4": {"rel": "verify/gate4_comment_guard.py",
              "pin": "d7ab397c5f0243d0c7320f91d0f14481"},
    "gate7": {"rel": "wrapper/gate7_probe.sh",
              "pin": None},  # 非冻结件·只录不判
}
PIN_NOTE = "names/gate4=20261031 冻结在册值；gate7 launcher=非冻结只录（20261101 实测 3bbfadfde7e5578d27047a107643d97b）"
STEP_ORDER = ("names", "gate4", "gate7")          # ①②③ 固定序（可减不可重排）
STEP_DEFAULT = ("names", "gate4")                 # 缺省轻链（gate7 显式选入·真编译）
STEP_LABEL = {"names": "①对表", "gate4": "②gate4", "gate7": "③gate7"}

# 三判例记名面（--knife 合法值·纯站账记录——判据零复制，刀面细节归各处方件/判例账）
KNIVES = {
    "E7-carrier": "fa56b_ext 载体中继（证明体 Empty_set 载体→`__` 载体＋pre-map 内联 motive·对表判例 18=18·sandbox/seat_fa56re/账/R22锚换代包-fa56b.md）",
    "R23-notation": "ToyR_UpAblP7 记号重载（非语句头区 Notation 别名＋Extraction Inline 具体面·语句面 13=13 逐字守恒·sandbox/seat_toyr/账/R23锚换代包-toyr.md）",
    "E5-reanchor": "UpReqSampling 投影重锚（语句面投影→具体面三映射·51=51·处方件 recipes/S07_projection_reanchor_E5.md）",
    "custom": "自定刀面（站账只记名·处方与判例自附）",
}

# 各正本退出码→站内 verdict 判表（判据零复制：verdict 唯一源自正本自身 rc）
NAMES_GATE = {0: "PASS"}                            # 2=不等 9=缺件 → FAIL
GATE4_GATE = {0: "PASS", 1: "FAIL", 2: "REVIEW"}    # REVIEW=0 才算净（nw8 口径）
GATE7_GATE = {0: "PASS", 1: "FAIL"}                 # 闸红/探针败→FAIL；表外 rc→FAIL

VERDICT_RANK = {"PASS": 0, "REVIEW": 1, "FAIL": 2, "MISSING": 3}
VERDICT_EXIT = {"PASS": 0, "REVIEW": 2, "FAIL": 1, "MISSING": 9}

# 站账信息抽取（仅出账·永不覆判——verdict 唯一源自 rc；抽取失败=字段 null 如实出）
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
    """--steps 解析：逗号分＋重复旗标合并；未知步名 raise ValueError；
    重排丢弃——恒归 ①②③ 固定序（可减不可重排）。"""
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
    """预检形制（组合形制面·文件存在性归 main 预检）。返回错误串或 None。"""
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
    """③gate7 launcher 装配：bash launcher --tree T --module M… [--workdir W]
    [--json J] [--timeout S] [-- extra…逐字尾透传]。"""
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
    """聚合律·硬者胜：MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)。"""
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
    """站账信息抽取（出账用·永不覆判；抽不到=None 如实出）。"""
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
    """本站自检十判（零写盘·不执行任何正本）。回 pass 布尔。"""
    ok = True
    root = default_root()

    # 判1 三正本在位（默认仓根）
    found = {s: canonical_path(root, s) for s in STEP_ORDER}
    j = all(os.path.isfile(p) for p in found.values())
    print("  judge1 三正本在位(default root):", "PASS" if j else "FAIL", found)
    ok = ok and j

    # 判2 冻结嵌记 32-hex 形制（names/gate4·gate7 launcher 无 pin）
    j = (all(norm_hex(CANONICALS[s]["pin"]) == CANONICALS[s]["pin"]
             for s in ("names", "gate4"))
         and CANONICALS["gate7"]["pin"] is None)
    print("  judge2 冻结嵌记形制（gate7 launcher 只录不判）:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判3 --steps 解析：子集固定序＋未知拒＋缺省轻链
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

    # 判4 聚合律硬者胜
    v1, e1 = aggregate(["PASS", "PASS"])
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
         and gate_step(GATE7_GATE, 0) == "PASS" and gate_step(GATE7_GATE, 1) == "FAIL"
         and gate_step(GATE7_GATE, 9) == "FAIL")
    print("  judge5 判表 names/gate4/gate7:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判6 三步 cmd 装配（gate7 extra 逐字尾透传）
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
    # 判6b `--` 切分律：argparse 面与 gate7 透传面分离（world_hook 同款）
    s_a, s_x = split_extra_argv(["--cured", "c.v", "--", "--gate", "--baseline", "B"])
    s_b, s_y = split_extra_argv(["--cured", "c.v"])
    j = j and s_a == ["--cured", "c.v"] and s_x == ["--gate", "--baseline", "B"] \
        and s_b == ["--cured", "c.v"] and s_y == []
    print("  judge6 cmd 装配＋`--`切分律:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判7 预检形制：baseline 依存＋同件拒绝＋gate7 依赖声明
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

    # 判8 三判例记名面：三刀齐＋各带判例锚（对表判例值与账源路径）
    j = (all(k in KNIVES for k in ("E7-carrier", "R23-notation", "E5-reanchor", "custom"))
         and "18=18" in KNIVES["E7-carrier"] and "13=13" in KNIVES["R23-notation"]
         and "51=51" in KNIVES["E5-reanchor"]
         and "seat_fa56re" in KNIVES["E7-carrier"]
         and "seat_toyr" in KNIVES["R23-notation"]
         and "S07_projection_reanchor_E5.md" in KNIVES["E5-reanchor"])
    print("  judge8 三判例记名面:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判9 断言形制核：32-hex 正过、伪值拒
    j = (norm_hex(" 9e26c0db2c60ced3629a13a821bdf615 ") == "9e26c0db2c60ced3629a13a821bdf615"
         and norm_hex("zz") is None and norm_hex("01dc") is None)
    print("  judge9 断言形制核正过伪拒:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判10 站账抽取：三正本样例行各抽出＋gate7 gate 词面＋非匹配行如实缺
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
    """首个裸 `--` 切分：前段＝站形参（argparse 面），后段＝gate7 形参逐字透传
    （world_hook 同款切分律——argparse 无法收 `--` 作旗标值）。"""
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

    # —— 预检：正本/靶件存在性（不过零开步·exit 9）——
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

    # —— 嵌记/外附 md5 断言（败→卡出 stderr·exit 2·绝不带病开步）——
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

    # —— 开步：①→②→③ 固定序·全步出账（组合器＝全账聚合·不短路）——
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

    # —— 站账信息抽取（出账·永不覆判）——
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
