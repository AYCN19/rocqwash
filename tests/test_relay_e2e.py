#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_relay_e2e.py — 接驳实战核 e2e：cw_sentinel --on-red-preset unclog
全链三判（tests/·20261111 v38 工装席·tmp fixture 零真网络零真编译）

把「见红即疏通（干跑）」接驳链在 tmp 全链实跑一遍，三判各证一环：
  判1 事件触发——哨 --once + injector canned CI 红炉（run 178 failure→
      ci_triage 子进程真判类 A-content-red）→ ci-red 事件落 --emit JSONL
      → --on-red-preset unclog 代跑：actions 账 cmd=preset 逐字展开（含
      unclog report 路径 {emit_dir}/unclog_{run}.json）·代跑 rc=9 如实入账
      （fixture 无 --world·fail-loud·哨退出码仍 0——旁路动作非器面铁律）。
      判例承 tools/cw_sentinel.py selftest ⑨ 触发捕获（cw_sentinel.py:1240-1265
      「代跑 unclog（fixture 无 --world）应 rc=9 入账」）＋ preset 表
      cw_sentinel.py:150-159。
  判2 unclog 干跑 rc=0 且零写盘——同一 fixture 树 unclog --audit（只读基线：
      单遍 canned probe 归集→chain_graph 真跑→堵账基线报告·final=audit·
      cures 恒 0·--src 全文件 md5 清单跑前跑后自证恒同）→ rc=0·见红
      （red_files=["B"]）·出可洗链根（A washable）·墙空。取形判例承
      unclog selftest 矢量⑩（unclog.py:1329-1363·--audit --injector 罐装
      零真编译＋tree_manifest 零写盘自证）·audit 契约 unclog.py:49-63。
      注：preset 代跑形（--src 单参·无 --world/--injector）离线必 rc=9
      （probe 真探针须 world·unclog.py:295-296），故疏通干跑 proper 由本判
      以 audit 罐装形实证——audit 是唯一「见红＋rc=0＋零写盘自证」的合法
      干跑形（红 canned 红账 dry-run 闭环形 verdict=rounds-exhausted rc=1·
      unclog selftest 矢量⑤ unclog.py:1208-1227 同判）。
  判3 JSONL 同盘 unclog report 路径——判1 的 actions[0].cmd 所记
      {emit_dir}/unclog_178.json（emit_dir=--emit JSONL 所在目录·预设出账
      与事件流同盘 cw_sentinel.py:53-55）与判2 实落 report 逐字节对拍：
      该路径文件存在·schema=rocqwash-unclog/1·verdict=audit。
      口径注记（如实）：哨 --emit JSONL 事件流仅载事件（emit_event 四类
      ci-red/blocking/build-signal/sentinel-error·cw_sentinel.py:503/568/612/
      868），actions 账（含 unclog report 路径）走 --json report——v38 实况
      如此；故本判以「JSONL 同盘＋actions 账所记路径与实落文件对拍」落判。

真实输出样例（2026-11-11 工装席 tmp 演练实跑·非手写·全文样例落
docs/ops-realtime-service-v1.0-20261111.md）：
  哨腿 stdout 尾：`on-red 注记: cmd rc=9（旁路动作·不改哨退出码）`·exit 0；
  unclog 腿 stdout 尾：`report -> …/unclog_178.json`＋`VERDICT: audit (exit 0)`；
  src md5 清单前后 diff 空（零写盘）。

fixture 三件（全金标引据·无自创形）：
  ①哨 injector canned runs/jobs——cw_sentinel.py:987-1006 selftest 同文；
  ②fixture src A.v=正典 cure_pack v1.3 体（unclog.py:1041-1043 CURE13_BODY
    同文）·B.v=Require Import A.（unclog.py:1068-1080 fixture 同形）；
  ③unclog scenario canned probe_ledger——unclog.py:1082-1097 led/rec0/rec1
    同形（L1：A 绿可洗·B 缺 A）。

用法：
  python3 tests/test_relay_e2e.py        # 手动（-B 禁 __pycache__）
  （run_tests.sh 总套挂接归集成席·本席零触总套）

零触律：零真网络零真编译零触真仓（哨/unclog 全 canned 罐装·真子进程编排
真跑——ci_triage/chain_graph/cure_applier/scan_v4_token/frozen8 纯 stdlib
零编译·probe_engine.py:10 判例真编译才须 guard）；tmp 自管（mkdtemp 进
finally rmtree）＋代跑 unclog mkdtemp 残留清扫（cw_sentinel.py:1263-1265
同款）；python3 -B 禁 __pycache__。
退出码：0=三判全过；1=任一红（fail-loud 响亮列红·禁静默）。
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENTINEL = os.path.join(REPO, "tools", "cw_sentinel.py")
UNCLOG = os.path.join(REPO, "tools", "unclog.py")

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"          # unclog.py:1041-1043 同文
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")


def run(tool, args):
    """子进程跑器（stdout+stderr 合流·canned 罐装零网络零编译）。"""
    p = subprocess.run([sys.executable, "-B", tool] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def tree_manifest(root):
    """--src 全文件 md5 清单（确定性双排序·unclog.py:225 tree_manifest 同判·
    本壳独立实算作零写盘对拍底账）。"""
    man = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            with io.open(fp, "rb") as fh:
                man[os.path.relpath(fp, root)] = hashlib.md5(fh.read()).hexdigest()
    return man


def build_fixture(tmp):
    """tmp fixture 三件（金标引据见 docstring）：src 树＋哨 injector＋unclog
    scenario。返回 (src, 哨 injector 路径, unclog scenario 目录)。"""
    src = os.path.join(tmp, "src")
    os.makedirs(src)
    with io.open(os.path.join(src, "A.v"), "w", encoding="utf-8") as fh:
        fh.write(CURE13_BODY)
    with io.open(os.path.join(src, "B.v"), "w", encoding="utf-8") as fh:
        fh.write("Require Import A.\n")
    # ①哨 injector：canned CI 红炉 run 178（cw_sentinel.py:987-1006 selftest 同文）
    inj = {"schema": "rocqwash-sentinel-injector/1", "responses": [
        {"url_contains": "/actions/runs?", "status": 200,
         "body": {"total_count": 1, "workflow_runs": [
             {"id": 178, "name": "CI", "run_number": 9, "status": "completed",
              "conclusion": "failure", "head_branch": "main",
              "head_sha": "abc123def",
              "html_url": "https://github.com/org/repo/actions/runs/178"}]}},
        {"url_contains": "/runs/178/jobs", "status": 200,
         "body": {"total_count": 1, "jobs": [
             {"id": 501, "name": "build", "status": "completed",
              "conclusion": "failure",
              "started_at": "2026-11-10T08:00:00Z",
              "completed_at": "2026-11-10T08:01:00Z",
              "steps": [{"number": 1, "name": "Build (coqc batch)",
                         "status": "completed", "conclusion": "failure",
                         "started_at": "2026-11-10T08:00:01Z",
                         "completed_at": "2026-11-10T08:00:30Z"}]}]}}]}
    inj_path = os.path.join(tmp, "inj_sentinel.json")
    with io.open(inj_path, "w", encoding="utf-8") as fh:
        json.dump(inj, fh, sort_keys=True)
    # ③unclog scenario：canned probe 红账（unclog.py:1082-1097 rec0/rec1 同形
    # ·L1 同文：A 绿可洗·B 缺 A）
    led = {"schema": "rocqwash-probe-ledger/1", "n_records": 2, "records": {
        "A": {"file": "A", "md5": None, "rc": 0, "red": "", "missing": None,
              "red_class": None, "verdict": "RC0", "red_count": None,
              "md5_match": None},
        "B": {"file": "B", "md5": None, "rc": 1,
              "red": "Error: Unable to locate library | A (while searching "
                     "for a .vos file).",
              "missing": "A", "red_class": "MISSING_LIB",
              "verdict": "RED-MISSING_LIB", "red_count": None,
              "md5_match": None}}}
    scen_dir = os.path.join(tmp, "scenario")
    os.makedirs(scen_dir)
    with io.open(os.path.join(scen_dir, "scenario.json"), "w",
                 encoding="utf-8") as fh:
        json.dump({"probe": [led]}, fh, sort_keys=True)
    return src, inj_path, scen_dir


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_relay_e2e_")
    try:
        src, inj_path, scen_dir = build_fixture(tmp)
        emit = os.path.join(tmp, "events.jsonl")
        rep_path = os.path.join(tmp, "report.json")
        emit_dir = os.path.dirname(os.path.abspath(emit))

        # ── 判1 事件触发：canned CI 红炉→ci-red 事件→on-red preset 代跑 ──
        rc, out = run(SENTINEL, [
            "--once", "--watch-repo", "org/repo", "--branch", "main",
            "--injector", inj_path,
            "--state-file", os.path.join(tmp, "state.json"),
            "--emit", emit, "--json", rep_path,
            "--on-red-preset", "unclog", "--on-red-arg", "src=" + src,
            "--sleep-scale", "0"])
        if rc != 0:
            fails.append("判1 哨应 rc=0（红是数据非器红）实测 %d\n%s"
                         % (rc, out[-600:]))
        try:
            evs = [json.loads(l) for l in io.open(emit, encoding="utf-8")
                   if l.strip()]
        except (ValueError, OSError) as e:
            evs = []
            fails.append("判1 事件流应可解析: %s" % e)
        if len(evs) != 1 or evs and evs[0].get("kind") != "ci-red" \
                or evs and evs[0].get("run") != 178 \
                or evs and evs[0].get("family") != "A-content-red" \
                or evs and evs[0].get("schema") != "rocqwash-sentinel-event/1" \
                or evs and evs[0].get("seq") != 1:
            fails.append("判1 JSONL 应 1 行 ci-red(run=178·family=A-content-red"
                         "·seq=1) 实测 %s" % (evs or "空"))
        rep = {}
        try:
            rep = json.load(io.open(rep_path, encoding="utf-8"))
        except (ValueError, OSError) as e:
            fails.append("判1 哨 report 应可读: %s" % e)
        acts = rep.get("actions") or []
        want_cmd = ("python3 -B %s --src %s --json %s/unclog_178.json"
                    % (UNCLOG, src, emit_dir))
        if len(acts) != 1 or acts and acts[0].get("cmd") != want_cmd \
                or acts and acts[0].get("rc") != 9:
            fails.append("判1 actions 账应 1 笔且 cmd=preset 展开（%s）·代跑 "
                         "rc=9 如实入账（fixture 无 world·哨 selftest ⑨ 同判例"
                         " cw_sentinel.py:1261）实测 %s" % (want_cmd, acts))
        if rep.get("on_red_preset") != "unclog":
            fails.append("判1 report.on_red_preset 应=unclog 实测 %r"
                         % rep.get("on_red_preset"))
        # 代跑 unclog mkdtemp 残留清扫（cw_sentinel.py:1263-1265 同款）
        if acts:
            mw = re.search(r"workdir -> (\S+)", acts[0].get("output") or "")
            if mw:
                shutil.rmtree(mw.group(1), ignore_errors=True)
        # 判3 前置证据（actions 账所记 unclog report 路径）
        named_report = os.path.join(emit_dir, "unclog_178.json")

        # ── 判2 unclog 干跑 rc=0 且零写盘：同一 fixture 树 --audit 罐装 ──
        man_before = tree_manifest(src)
        rc2, out2 = run(UNCLOG, [
            "--src", src, "--audit", "--injector", scen_dir,
            "--workdir", os.path.join(tmp, "wd"), "--json", named_report])
        if rc2 != 0:
            fails.append("判2 unclog --audit 应 rc=0（红是基线数据非器红）"
                         "实测 %d\n%s" % (rc2, out2[-600:]))
        urep = {}
        try:
            urep = json.load(io.open(named_report, encoding="utf-8"))
        except (ValueError, OSError) as e:
            fails.append("判2 unclog report 应可读: %s" % e)
        if urep:
            fin = urep.get("final") or {}
            r0 = (urep.get("rounds") or [{}])[0]
            ct0 = (r0.get("chain_top") or [{}])[0]
            if urep.get("schema") != "rocqwash-unclog/1" \
                    or urep.get("verdict") != "audit":
                fails.append("判2 report 应 schema=rocqwash-unclog/1·"
                             "verdict=audit 实测 %s/%r"
                             % (urep.get("schema"), urep.get("verdict")))
            if r0.get("probe_summary", {}).get("red_files") != ["B"] \
                    or fin.get("red_files") != ["B"]:
                fails.append("判2 应见红（red_files=[B]·canned 红账 B 缺 A）"
                             "实测 round=%s final=%s"
                             % (r0.get("probe_summary"), fin.get("red_files")))
            if ct0.get("lib") != "A" \
                    or ct0.get("self", {}).get("washable") is not True:
                fails.append("判2 应出可洗链根 A(washable=True) 实测 %s" % ct0)
            if fin.get("cures_planned_total") != 0 \
                    or fin.get("cures_applied_total") != 0:
                fails.append("判2 干跑 cures 应恒 0（audit 零落刀）实测 %s"
                             % fin)
            if urep.get("wall") != {}:
                fails.append("判2 可洗非 frozen 墙应空 实测 %s" % urep.get("wall"))
            if urep.get("mode", {}).get("audit") is not True \
                    or urep.get("mode", {}).get("apply") is not False:
                fails.append("判2 mode 应 audit=true·apply=false 实测 %s"
                             % urep.get("mode"))
        man_after = tree_manifest(src)
        if man_before != man_after or not man_before:
            fails.append("判2 零写盘自证破：src md5 清单前后应恒同且非空 "
                         "before=%s after=%s" % (man_before, man_after))

        # ── 判3 JSONL 同盘 unclog report 路径：actions 账所记≡实落文件 ──
        if not os.path.isfile(named_report):
            fails.append("判3 preset cmd 钦定路径应实落 report: %s" % named_report)
        elif os.path.dirname(os.path.abspath(emit)) != emit_dir \
                or not os.path.isfile(emit):
            fails.append("判3 emit JSONL 应在同盘在位: %s" % emit)
        elif urep.get("schema") != "rocqwash-unclog/1" \
                or urep.get("verdict") != "audit":
            fails.append("判3 同盘 report 应 schema=rocqwash-unclog/1·"
                         "verdict=audit（与 actions[0].cmd 路径对拍）实测 %s"
                         % urep.get("verdict"))
        if acts and "unclog_178.json" not in (acts[0].get("cmd") or ""):
            fails.append("判3 actions[0].cmd 应含 unclog report 路径名 实测 %s"
                         % acts[0].get("cmd"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("== test_relay_e2e: %d 过 / %d 红 ==" % (3 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
