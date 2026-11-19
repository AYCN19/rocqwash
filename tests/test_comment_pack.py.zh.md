#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_comment_pack.py — wash/comment_pack.json + wash/comment_sweep.py 自测
（tests/·v31 工具化·承 W39/W44/W52/W54 四席注释英化 sweep 工法判例工具化）

六节判：
  1 工具自证    comment_sweep --selftest 四判全过（rc 0）——注释域旗词换形/
                字符串与嵌套注释免疫/头注换代/w7 code 行全等投影/幂等
  2 pack 完整   comment_pack.json 解析：engine=comment-state-machine、旗词表
                （载体→carrier 单词现役）、header_spec 五字段英形＋行上界
  3 fixture 流程  干跑零写→--apply（旗词换形 2 处·字符串内 1 处禁换·嵌套
                注释深处换形）→code 行全等断言（w7 口径）→重跑零变更
  4 头注换代    --header-map 数据驱动换代（fixture 旧头注→五字段英形）→
                code 行全等→重跑零变更（换代幂等）
  5 头注形校验  五字段缺一报 problem（report-only 不硬红）＋header_end_line
                口径（尾空行不计）
  6 负例        字符串字面量与 code 域零触碰逐字断言

零触律：夹具临时目录副本驱动·零真编译零网络零触真仓。
退出码：0=六节全过；1=任一红。
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SWEEP = os.path.join(REPO, "wash", "comment_sweep.py")
PACK = os.path.join(REPO, "wash", "comment_pack.json")
FIXTURE = os.path.join(HERE, "fixtures", "comment_sweep_fixture.v")

HEADER_MAP = {
    "fixture": """(* ConstructiveWorld — comment-sweep demonstration file. *)

(** * fixture: comment-domain sweep demonstration.

    Mission.  Exercising the comment-domain flag-word exchange and the
      leading-header replacement with code lines held byte-stable.

    Dependencies.  The Require face below.

    References.  none.

    Constructivity.  The single proof closes by Qed.

    Build.  compiles cleanly (exit 0). *)

""",
}

fails = []


def check(name, cond, extra=""):
    print("  %-38s %s %s" % (name, "ok" if cond else "FAIL", extra))
    if not cond:
        fails.append(name)


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          **kw)


# 1. selftest
r = run([sys.executable, "-B", SWEEP, "--selftest"])
check("sweep --selftest rc=0", r.returncode == 0,
      "" if r.returncode == 0 else r.stdout.decode()[-300:])

# 2. pack integrity
pack = json.load(io.open(PACK, encoding="utf-8"))
check("engine is comment-state-machine",
      pack.get("engine") == "comment-state-machine")
check("flag word 载体→carrier",
      pack.get("flag_words") == {"载体": "carrier"})
spec = pack.get("header_spec", {})
check("header spec five dotted fields",
      spec.get("fields") == ["Mission.", "Dependencies.", "References.",
                             "Constructivity.", "Build."])
check("header end-line bound", spec.get("max_end_line") == 30)

# 3./4. fixture flows on a temp copy
tmp = tempfile.mkdtemp(prefix="rw_comment_")
try:
    tgt = os.path.join(tmp, "fixture.v")
    shutil.copy(FIXTURE, tgt)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--json",
             os.path.join(tmp, "dry.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry.json"), encoding="utf-8"))
    check("dry-run flag_swaps=2 (header+string exempt)",
          dry["report"]["flag_swaps"] == 2, str(dry["report"]["flag_swaps"]))
    check("dry-run wrote nothing",
          io.open(tgt, encoding="utf-8").read()
          == io.open(FIXTURE, encoding="utf-8").read())
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--apply"])
    check("flag sweep apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    swept = io.open(tgt, encoding="utf-8").read()
    check("comment-domain words exchanged",
          swept.count("carrier") == 2 and "载体词" not in swept
          and "载体 深处" not in swept)
    check("string literal untouched",
          '"载体 在字符串内（禁换形）"' in swept)
    check("nested comment depth reached",
          "(* carrier 深处 *)" in swept)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt])
    check("flag sweep re-run zero-change", "flag_swaps=0" in r.stdout.decode())

    # 4. header replacement (data-driven map)
    hmap = os.path.join(tmp, "hmap.json")
    with io.open(hmap, "w", encoding="utf-8") as fh:
        json.dump(HEADER_MAP, fh, ensure_ascii=False, indent=1)
    tgt = os.path.join(tmp, "fixture.v")
    shutil.copy(FIXTURE, tgt)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--apply",
             "--header-map", hmap, "--json", os.path.join(tmp, "hdr.json")])
    check("header replace apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    acc = json.load(io.open(os.path.join(tmp, "hdr.json"), encoding="utf-8"))
    swept = io.open(tgt, encoding="utf-8").read()
    check("leading header replaced wholesale",
          swept.startswith(HEADER_MAP["fixture"])
          and acc["report"]["header_replaced"] is True)
    check("w7 code-line equality holds",
          acc["report"]["code_lines_equal"] is True
          and "code-line equality holds" in r.stdout.decode())
    check("tail flag words still exchanged under replacement",
          swept.count("carrier") == 2
          and "载体词" not in swept and "载体 深处" not in swept
          and '"载体 在字符串内（禁换形）"' in swept)
    check("header replace re-run zero-change",
          "header_replaced=False" in run([sys.executable, "-B", SWEEP,
                                          "--file", tgt, "--header-map",
                                          hmap]).stdout.decode())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 5./6. shape validation negatives live in the selftest; CLI four codes here
r = run([sys.executable, "-B", SWEEP, "--help"])
check("help rc=0", r.returncode == 0 and "usage" in r.stdout.decode())
r = run([sys.executable, "-B", SWEEP])
check("missing --file rc=2", r.returncode == 2)
r = run([sys.executable, "-B", SWEEP, "--file",
         os.path.join(tmp, "gone.v")])
check("missing file rc=9", r.returncode == 9)

print("TEST-COMMENT-PACK:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
