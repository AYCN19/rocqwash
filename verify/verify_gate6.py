#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_gate6.py — gate6 census 薄包装＋EntropyUnsatMark 判例器化（rocqwash verify/·
20261101 席 rqsupport）

五课反馈轮打磨件③（gate6 ch1 课工具化）。定位承仓内双层分工：
  - `wrapper/gate6_census.sh`（rqadapt 轮·guard 接线启动层）＝正典启动面——**判据零复制**，
    census/gate 红绿唯一出处仍是仓外正本 `ConstructiveWorld-Set/scripts/gates/
    gate6_statement_census.py`（在其仓只读禁改）；
  - 本件＝verify/ 逐件绿判入口面（verify_vo.py 同款形）：①**薄调**正本（subprocess
    `python3 -B`·rc 1:1 透传·零判据复制）；②**EntropyUnsatMark 判例器化**——把
    seat_eum 判例（语句面裸 Prop 量词 ch1 治理）机械化成可复用判读。

判例源（只读已核在盘）：`sandbox/seat_eum/账/gate6_report_before.json`（EntropyUnsatMark.v
ch1=1·L135 Theorem eum_EntropyDiffReal_section_vacuous·语句面 `forall (Omega_A : forall
(E_A : Real), …)` 嵌套裸 Prop 量词）→ `gate6_report_after.json`（ch1=0·**statement_names
5=5 零漂移**·ch2/ch3 恒 0）。判例语义（EUM-VERDICT）：
  治必降      ch1 总量 after < before，或两侧恒 0；ch1 反升＝红（R15 存量冻结只罚增长同律）
  治不摇名    逐文件 statement names 有序全等 before→after（签名稳定律）；名单漂移＝红
  旁道零涨    ch2/ch3 零增长；after 新现文件（before 无）各通道须全零（born-clean）
  退役不罚    before 有 after 无的文件＝INFO 不计红（存量退役合法·正本 gate 同律）

用法：
  # ① 薄调正本（形参 1:1 对齐正本 argparse·rc 透传）：
  python3 verify/verify_gate6.py --tree <.v 树目录> [--json o] [--text]
                                 [--gate --baseline B] [--baseline-out O]
                                 [--script <gate6.py>]
  # ② 判例器化（对两份 census JSON 报告机械判读）：
  python3 verify/verify_gate6.py --judge-before before.json --judge-after after.json
                                 [--judge-json out.json]
  # ③ 自证：
  python3 verify/verify_gate6.py --selftest

退出码：0=判例绿/正本 census 报告或闸绿透传；1=判例红/正本闸红透传；2=用法或报告畸形；
        9=路径缺失（正本/--tree/--judge-* 文件——fail-loud 不模拟）。
零网络零编译：正本为纯静态词面扫描（其头注自述），本件 subprocess 亦零编译；
不内建 guard 接线（启动面归 wrapper/gate6_census.sh·调用者按需套温控）。
"""
import argparse
import io
import json
import os
import subprocess
import sys

PROG = "verify_gate6"
GATE6_SCRIPT_DEF = ("/Users/apple/Desktop/ConstructiveWorld-Set/scripts"
                    "/gates/gate6_statement_census.py")


# ---------------------------------------------------------------------------
# 判例器（EUM-VERDICT）
# ---------------------------------------------------------------------------

def load_report(path):
    """读 census JSON 报告并做形校（正本 reports 形）。畸形＝JudgeError。"""
    if not os.path.isfile(path):
        raise MissingPath("报告文件缺失: %s" % path)
    try:
        with io.open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        raise JudgeError("报告 JSON 解析失败 %s: %s" % (path, e))
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        raise JudgeError("报告须 {\"files\": {…}} 形: %s" % path)
    for fname, c in data["files"].items():
        if not isinstance(c, dict):
            raise JudgeError("报告 files[%s] 须对象: %s" % (fname, path))
        for k in ("ch1", "ch2", "ch3", "names"):
            if k not in c:
                raise JudgeError("报告 files[%s] 缺 %s 键: %s" % (fname, k, path))
    return data


def judge(before, after):
    """EntropyUnsatMark 判例四判。返回 (ok, rows)。

    rows 每项 dict(judge/ok/detail)；judge ∈ 治必降/治不摇名/旁道零涨/退役不罚。
    """
    rows = []
    bf, af = before["files"], after["files"]

    def ch_totals(rep, ch):
        return sum(len(rep["files"][f].get(ch, [])) for f in rep["files"])

    # 判一 治必降（ch1）
    b1, a1 = ch_totals(before, "ch1"), ch_totals(after, "ch1")
    ok1 = (a1 < b1) or (a1 == 0 and b1 == 0)
    rows.append({"judge": "治必降", "ok": ok1,
                 "detail": "ch1 before=%d after=%d（须降或两侧恒零）" % (b1, a1)})
    # 判二 治不摇名（逐文件 names 有序全等·只在「存活文件」上判——
    #   整文件退役随件带名属退役不罚面，不算漂移；新现文件的语句名属正常增长面）
    drift = []
    common = sorted(set(bf) & set(af))
    for f in common:
        if bf[f]["names"] != af[f]["names"]:
            drift.append(f)
    nb = sum(len(bf[f]["names"]) for f in common)
    na = sum(len(af[f]["names"]) for f in common)
    ok2 = (not drift) and (nb == na)
    rows.append({"judge": "治不摇名", "ok": ok2,
                 "detail": "names 存活文件 before=%d after=%d 漂移文件=%s（须有序全等·总量恒等）"
                           % (nb, na, drift or "无")})
    # 判三 旁道零涨（ch2/ch3）＋新现文件 born-clean
    grows = []
    for ch in ("ch2", "ch3"):
        b, a = ch_totals(before, ch), ch_totals(after, ch)
        if a > b:
            grows.append("%s %d→%d" % (ch, b, a))
    for f in sorted(set(af) - set(bf)):
        for ch in ("ch1", "ch2", "ch3"):
            if af[f].get(ch):
                grows.append("新现文件 %s %s=%d（born-clean 须全零）" % (f, ch, len(af[f][ch])))
    rows.append({"judge": "旁道零涨", "ok": not grows,
                 "detail": "；".join(grows) if grows else "ch2/ch3 零增长·新现文件全零"})
    # 判四 退役不罚（INFO）
    gone = sorted(set(bf) - set(af))
    rows.append({"judge": "退役不罚", "ok": True,
                 "detail": ("退役文件=%s（INFO·不计红）" % gone) if gone else "无退役"})
    return all(r["ok"] for r in rows if r["judge"] != "退役不罚"), rows


class JudgeError(Exception):
    pass


class MissingPath(Exception):
    pass


# ---------------------------------------------------------------------------
# 薄调正本
# ---------------------------------------------------------------------------

def run_census(script, passthrough_args):
    """subprocess python3 -B 正本·rc 1:1 透传（零判据复制）。"""
    if not os.path.isfile(script):
        print("FAIL-LOUD: gate6 正本缺失: %s (可用 --script/GATE6_SCRIPT 覆写)" % script,
              file=sys.stderr)
        sys.exit(9)
    cmd = [sys.executable, "-B", script] + list(passthrough_args)
    sys.stdout.flush()
    return subprocess.run(cmd).returncode


# ---------------------------------------------------------------------------
# 自证（判例向量用 seat_eum 实测报告形·wrapper 用夹具脚本·零真仓写）
# ---------------------------------------------------------------------------

EUM_NAMES = ["fa52_EDP_E_B_pos_unsat", "fa52_EntropyDiffReal_premises_unsat",
             "eum_E_B_pos_slot_unsat_ref", "eum_premises_unsat_ref",
             "eum_EntropyDiffReal_section_vacuous"]
EUM_CH1_HIT = {"line": 135, "cmd": "Theorem", "name": "eum_EntropyDiffReal_section_vacuous",
               "excerpt": "Theorem eum_EntropyDiffReal_section_vacuous : forall (Omega_A : "
                          "forall (E_A : Real), real_lt real_zero E_A -> Real) -> Real"}


def eum_report(ch1_hits):
    """seat_eum 报告形夹具（EntropyUnsatMark.v·ch1 按 before/after 给）。"""
    return {"summary": {"files": 1,
                        "totals": {"ch1": len(ch1_hits), "ch2": 0, "ch3": 0},
                        "statement_names": len(EUM_NAMES)},
            "files": {"EntropyUnsatMark.v": {"ch1": ch1_hits, "ch2": [], "ch3": [],
                                             "names": list(EUM_NAMES)}}}


def selftest():
    """内嵌向量组：eum before/after 判例绿·ch1 未降红·名漂移红·旁道涨红·新现文件
    红/绿·退役 INFO·报告畸形 2·缺件 9·正本缺失 9·透传 rc 双判（夹具脚本零真仓）。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_verifygate6_self_")
    here = os.path.dirname(os.path.abspath(__file__))

    def run(args):
        p = subprocess.run([sys.executable, "-B", os.path.join(here, PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else ""
        return p

    def wf(name, obj):
        fp = os.path.join(tmp, name)
        with io.open(fp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
        return fp

    try:
        before = eum_report([EUM_CH1_HIT])
        after = eum_report([])
        # ① eum 判例正判：before(ch1=1)→after(ch1=0·names 5=5) → GREEN rc 0
        jb, ja = wf("eum_before.json", before), wf("eum_after.json", after)
        p = run(["--judge-before", jb, "--judge-after", ja])
        assert p.returncode == 0, "eum 判例应绿 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        assert "EUM-VERDICT-GREEN" in p.stdout and "治必降" in p.stdout, p.stdout

        # ② ch1 未降负判（before=after·存量冻结只罚增长与滞治）→ RED rc 1
        p = run(["--judge-before", jb, "--judge-after", jb])
        assert p.returncode == 1 and "治必降" in p.stdout, p.stdout

        # ③ 名漂移负判（names 改序）→ RED rc 1·治不摇名
        shaken = eum_report([])
        shaken["files"]["EntropyUnsatMark.v"]["names"] = list(reversed(EUM_NAMES))
        js = wf("eum_shaken.json", shaken)
        p = run(["--judge-before", jb, "--judge-after", js])
        assert p.returncode == 1 and "治不摇名" in p.stdout, p.stdout

        # ④ 旁道涨负判（ch2 出现）→ RED rc 1·旁道零涨
        grown = eum_report([])
        grown["files"]["EntropyUnsatMark.v"]["ch2"] = [{"line": 9, "cmd": "Class", "name": "",
                                                        "excerpt": "Class C : Prop := {}."}]
        jg = wf("eum_grown.json", grown)
        p = run(["--judge-before", jb, "--judge-after", jg])
        assert p.returncode == 1 and "旁道零涨" in p.stdout, p.stdout

        # ⑤ 新现文件：带 ch1 → 红；全零 → 绿（born-clean 同律）
        plus = json.loads(json.dumps(after))
        plus["files"]["NewBorn.v"] = {"ch1": [{"line": 3, "cmd": "Lemma", "name": "bad",
                                               "excerpt": "Lemma bad : Prop."}],
                                      "ch2": [], "ch3": [], "names": ["bad"]}
        jp = wf("eum_plus.json", plus)
        p = run(["--judge-before", jb, "--judge-after", jp])
        assert p.returncode == 1 and "新现文件" in p.stdout, p.stdout
        plus2 = json.loads(json.dumps(after))
        plus2["files"]["NewBorn.v"] = {"ch1": [], "ch2": [], "ch3": [], "names": []}
        jp2 = wf("eum_plus2.json", plus2)
        p = run(["--judge-before", jb, "--judge-after", jp2])
        assert p.returncode == 0, "新现文件全零应绿 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)

        # ⑥ 退役 INFO 不罚：after 少一文件 → 仍绿（判四 INFO 行在账）
        minus = eum_report([])
        minus["files"] = {}
        jm = wf("eum_minus.json", minus)
        p = run(["--judge-before", jb, "--judge-after", jm])
        assert p.returncode == 0 and "退役不罚" in p.stdout, p.stdout

        # ⑦ 报告畸形 → rc 2；judge 文件缺失 → rc 9
        bad = os.path.join(tmp, "bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write('{"nope": 1}')
        p = run(["--judge-before", jb, "--judge-after", bad])
        assert p.returncode == 2, "报告畸形应 rc=2 实测 %d" % p.returncode
        p = run(["--judge-before", os.path.join(tmp, "nope.json"), "--judge-after", ja])
        assert p.returncode == 9, "judge 缺件应 rc=9 实测 %d" % p.returncode

        # ⑧ 薄调正本：缺 --tree → 2；tree 缺失 → 9；正本缺失 → 9（fail-loud 先于运行）
        p = run([])
        assert p.returncode == 2, "缺 --tree 应 rc=2 实测 %d" % p.returncode
        p = run(["--tree", os.path.join(tmp, "no_tree_dir")])
        assert p.returncode == 9, "tree 缺失应 rc=9 实测 %d" % p.returncode
        fake = wf("fake.json", {})
        p = run(["--script", os.path.join(tmp, "no_gate6.py"), "--tree", tmp])
        assert p.returncode == 9 and "正本缺失" in p.stdout, p.stdout

        # ⑨ 透传 rc 双判（夹具脚本替身·零真仓零真 census）
        child_ok = os.path.join(tmp, "child_ok.py")
        with io.open(child_ok, "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('CHILD-OK')\nsys.exit(0)\n")
        p = run(["--script", child_ok, "--tree", tmp, "--text"])
        assert p.returncode == 0 and "CHILD-OK" in p.stdout, p.stdout
        child_red = os.path.join(tmp, "child_red.py")
        with io.open(child_red, "w", encoding="utf-8") as fh:
            fh.write("import sys\nprint('CHILD-RED')\nsys.exit(1)\n")
        p = run(["--script", child_red, "--tree", tmp])
        assert p.returncode == 1 and "CHILD-RED" in p.stdout, p.stdout

        print("VERIFY-GATE6-SELFTEST PASS: eum判例绿/ch1未降红/名漂移红/旁道涨红/"
              "新现文件红绿/退役INFO/畸形2/缺件9/正本缺9/透传rc双判 十判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="gate6 census 薄包装＋EntropyUnsatMark 判例器化")
    ap.add_argument("--tree", default=None, help="被普查 .v 树目录（薄调形）")
    ap.add_argument("--json", dest="json_out", default=None, help="1:1 透传正本")
    ap.add_argument("--text", action="store_true", help="1:1 透传正本")
    ap.add_argument("--gate", action="store_true", help="1:1 透传正本")
    ap.add_argument("--baseline", default=None, help="1:1 透传正本")
    ap.add_argument("--baseline-out", dest="baseline_out", default=None, help="1:1 透传正本")
    ap.add_argument("--script", default=os.environ.get("GATE6_SCRIPT", GATE6_SCRIPT_DEF),
                    help="gate6 正本路径（缺省 ConstructiveWorld-Set 正典路径）")
    ap.add_argument("--judge-before", default=None, help="census 报告 before（判例形）")
    ap.add_argument("--judge-after", default=None, help="census 报告 after（判例形）")
    ap.add_argument("--judge-json", default=None, help="判读账 JSON 出账路径")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # —— 判例形 ——
    if args.judge_before or args.judge_after:
        if not (args.judge_before and args.judge_after):
            print("FAIL-LOUD: --judge-before 与 --judge-after 必成对", file=sys.stderr)
            sys.exit(2)
        try:
            before = load_report(args.judge_before)
            after = load_report(args.judge_after)
        except MissingPath as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(9)
        except JudgeError as e:
            print("FAIL-LOUD: %s" % e, file=sys.stderr)
            sys.exit(2)
        print("EUM-VERDICT before=%s after=%s" % (args.judge_before, args.judge_after))
        ok, rows = judge(before, after)
        for r in rows:
            print("  %s %s — %s" % ("PASS" if r["ok"] else "RED ", r["judge"], r["detail"]))
        if args.judge_json:
            with io.open(args.judge_json, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"before": args.judge_before, "after": args.judge_after,
                           "verdict": "GREEN" if ok else "RED", "rows": rows},
                          fh, ensure_ascii=False, indent=1)
            print("json ->", args.judge_json)
        print("EUM-VERDICT-%s（EntropyUnsatMark 判例：治必降·治不摇名·旁道零涨·退役不罚）"
              % ("GREEN" if ok else "RED"))
        sys.exit(0 if ok else 1)

    # —— 薄调形 ——
    if not args.tree:
        print("FAIL-LOUD: 缺 --tree <.v 树目录>（或走 --judge-before/--judge-after 判例形）",
              file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.tree):
        print("FAIL-LOUD: --tree 目录缺失: %s" % args.tree, file=sys.stderr)
        sys.exit(9)
    if args.gate and not args.baseline:
        print("FAIL-LOUD: --gate 需配 --baseline（正本 GATE6-USAGE 同律·此处前置）",
              file=sys.stderr)
        sys.exit(2)
    passthrough = ["--tree", args.tree]
    if args.json_out:
        passthrough += ["--json", args.json_out]
    if args.text:
        passthrough += ["--text"]
    if args.gate:
        passthrough += ["--gate", "--baseline", args.baseline]
    if args.baseline_out:
        passthrough += ["--baseline-out", args.baseline_out]
    sys.exit(run_census(args.script, passthrough))


if __name__ == "__main__":
    main()
