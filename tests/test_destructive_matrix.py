#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_destructive_matrix.py — 破坏面复核矩阵·一行一拒写判据（tests/·工装席·破坏面·20261111）

对全部「会写盘的器与路径」做系统化复核：先盘点（器×写面×护栏锚），再逐条断言其
拒写护栏——一行一判据，矩阵失败＝任一护栏破，exit 1 响亮列破口 file:line。

盘点表（会写盘的器 × 本矩阵行 × 护栏锚）：
  ① tools/unclog.py（落刀器·写面＝链根件 <src>/<根>.v）
     U1 缺 --apply 零写盘：tmp 源树 md5 恒同·无落刀账·cures_applied=0
        锚 tools/unclog.py:42（安全律 --apply 缺省关＝全干跑零写盘）＋:583/:607
        （cure 干跑/落刀唯一两调用口·:607 if a.apply 总闸）
     U2 --audit 零写盘＋与 --apply 互斥：audit 只读基线（--src 全文件 md5 前后
        自证·:762）＋同给 rc=2（:827）
     U3 frozen 红拒：根名/根件撞 frozen8 在册→wall frozen-in-service·零落刀
        锚 tools/unclog.py:506（pick_root frozen_hit 预检）
     U4 非链根件零被动：--apply 落刀后受治根件已正典化而其余件 md5 恒同——
        落刀对象恒为链根件（:43-44「pick 之外无 cure 调用路径」结构性保证）
  ② tools/wash_shape.py（洗形器·写面＝--file/--dir 收件面）
     W1 plan 缺省零写盘：真实脏件（CRLF＋禁词）plan 出 would-fix 而树 md5 恒同
        锚 tools/wash_shape.py:1254（one_pass if self.args.apply 落刀总闸）
     W2 --apply 后 rescan partial 不谎报 shaped：apply「成功」而复扫仍有
        would-fix → verdict=partial exit 1（禁把未净谎报成 shaped）
        锚 tools/wash_shape.py:1192-1205（verdict_of：rescan 未净不给 shaped）
     W3 冻结名红拒：显式 --file 指认 frozen8 在册件 → rc=2 红拒（收件即拒·
        零引擎零写盘；在册件只递路径不触内容）
        锚 tools/wash_shape.py:759-761（collect_files is_forbidden → UsageError）
     W4 --header-map 与 --header-map-preset 同槽互斥 rc=2
        锚 tools/wash_shape.py:1887-1890（main 前置互斥闸）
  ③ tools/pushci.py（推送流水线·写面＝git push／API POST rerun／PR merge）
     P1 --dry-run 零副作用：api_calls/git-caller 双流水皆空（零 git 调零 API 调
        零工具子进程）·stages 全空
        锚 tools/pushci.py:1163-1164（run() dry_run → run_dry 短路）＋:1116
     P2 内容红零 rerun：family=A-content-red → fix-content 裁停·heal.rounds 空
        ＝零 rerun 实证（api 流水零 POST）
        锚 tools/pushci.py:983-987（heal_round A 族禁代修先于 rerun）
     P3 heal 帽尽停：--max-heal 3 恰 3 发 POST 后 heal-exhausted exit 1——
        帽尽即停无第 4 发
        锚 tools/pushci.py:966-969（stage_watch heal 帽闸）
  ④ tools/cw_sentinel.py（实时哨·写面＝--on-red 旁路动作子进程）
     S1 缺省 report-only：无 --on-red 无 --on-red-preset 时零子进程动作
        （actions 账空·见红出事件而不动手）
        锚 tools/cw_sentinel.py:713-715（fire_on_red 门在 sentry["on_red"]）
     S2 on-red 双路同守卫：plain --on-red 与 --on-red-preset 缺 --emit 皆
        rc=2（旁路动作必伴随事件流落盘·触发证据与动作账可审计；{emit_dir}
        系 --emit 派生缺盘即拒）——v40 登记缺口（plain 路径缺同款守卫）v41
        补齐转正
        锚 tools/cw_sentinel.py:722-723（expand_on_red_preset）＋:884-886
        （build_sentry plain 守卫）
  ⑤ tools/registry_union.py（注册册手术器·写面＝--out union 稿）
     R1 干跑缺省零写盘：--out 已给而缺省不落盘
        锚 tools/registry_union.py:881-885（mode 总闸·if args.apply 才写）
     R2 --apply 才落刀（＋--apply 无 --out → rc=2 禁隐式覆写）
        锚 tools/registry_union.py:826＋:883-885
  ⑥ wash/cure_applier.py（正典包落刀器·写面＝--file 目标件）
     C1 干跑缺省零写盘：缺省只出报告·目标件 md5 恒同
        锚 wash/cure_applier.py:1109/:1134（if args.apply 写闸）
     C2 --apply 才落刀＋幂等断言拒写：--apply 落刀且二遍零残才写盘；幂等断言
        败（自定义非幂等包）→ rc=1 file NOT written
        锚 wash/cure_applier.py:1134-1150（IDEMPOTENCE-FAIL 拒写）

离线纪律（硬要求）：全判据走 tmp fixture＋--injector 罐装（unclog probe/resprobe
canned·wash_shape 引擎键 canned·pushci steps/jobs/git-caller canned·sentinel
canned API）——零真网络零真仓零真编译；真子进程仅限纯 stdlib 离线引擎
（chain_graph/cure_applier/scan_v4_token/frozen8 --ledger/gate4/ci_triage
--offline·判例：各器自带 --selftest 同款）。唯一例外 W3 递真在册件**路径**——
工具在 collect_files 即红拒·零读零写（wash_shape 自身判8 同款先例）。

自体纪律：python3 -B 禁 __pycache__；零仓写盘（全部工件在 tempfile.mkdtemp）；
输出确定性（零墙钟零绝对仓路径）；env 兜底清洗（ROCWASH_HEADER_MAP 剥除·
防环境渗判）；fail-loud——任一行炸（含环境异常）按破计不静默。

退出码：0=17 行判据全过；1=任一护栏破（响亮列破口 file:line＋违据）。

用法：
  python3 tests/test_destructive_matrix.py          # 套件内经 run_tests.sh 调
  python3 -B tests/test_destructive_matrix.py       # 手动
"""
import json
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNCLOG = os.path.join(REPO, "tools", "unclog.py")
WASH_SHAPE = os.path.join(REPO, "tools", "wash_shape.py")
PUSHCI = os.path.join(REPO, "tools", "pushci.py")
SENTINEL = os.path.join(REPO, "tools", "cw_sentinel.py")
REGISTRY_UNION = os.path.join(REPO, "tools", "registry_union.py")
CURE_APPLIER = os.path.join(REPO, "wash", "cure_applier.py")
FROZEN8 = os.path.join(REPO, "certify", "frozen8.py")
JOBS_A = os.path.join(REPO, "tests", "fixtures", "ci_triage_A_content_red.json")
JOBS_B = os.path.join(REPO, "tests", "fixtures", "ci_triage_B_netred.json")

SCHEMA_UNCLOG = "rocqwash-unclog/1"


# ---- 小件 ---------------------------------------------------------------------

def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_manifest(root):
    """目录全文件 {rel(POSIX): md5} 清单（增删改一字节即现形·unclog 同款口径）。"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            out[os.path.relpath(fp, root).replace(os.sep, "/")] = md5_of(fp)
    return out


def sh(tool_abs, argv):
    """python3 -B <tool> 子进程（stdout+stderr 合流·env 清洗 ROCWASH_HEADER_MAP
    防环境渗判）。"""
    env = dict(os.environ)
    env.pop("ROCWASH_HEADER_MAP", None)
    p = subprocess.run([sys.executable, "-B", tool_abs] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def wf(path, text, newline="\n"):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)
    return path


def wj(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, sort_keys=True)
    return path


def jl(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---- unclog 注入夹具（probe/resprobe canned 台账·与 unclog --selftest 同形）----

CURE13_BODY = ("Theorem t8 : forall f pf k,\n"
               "  (gnPrf f pf <= k)%nat -> NatOK f pf k.\n"
               "Proof. intros. apply g0. Qed.\n")


def u_led(records):
    return {"schema": "rocqwash-probe-ledger/1", "n_records": len(records),
            "records": records}


def u_rec0(f):
    return {"file": f, "md5": None, "rc": 0, "red": "", "missing": None,
            "red_class": None, "verdict": "RC0", "red_count": None,
            "md5_match": None}


def u_rec1(f, lib):
    return {"file": f, "md5": None, "rc": 1,
            "red": "Error: Unable to locate library | %s (while searching "
                   "for a .vos file)." % lib,
            "missing": lib, "red_class": "MISSING_LIB",
            "verdict": "RED-MISSING_LIB", "red_count": None, "md5_match": None}


def u_fixture(tmp, tag, extra_v=None):
    """unclog tmp 夹具：src 树（A 可洗链根＋B 消费者〔＋附加件〕）＋cands.tsv
    ＋injector 目录骨架。→ (src, cands, wd, injdir)。"""
    d = os.path.join(tmp, tag)
    src, wd, injdir = (os.path.join(d, x) for x in ("src", "wd", "inj"))
    for p in (src, wd, injdir):
        os.makedirs(p)
    wf(os.path.join(src, "A.v"), CURE13_BODY)
    wf(os.path.join(src, "B.v"), "Require Import A.\n")
    for name, body in (extra_v or []):
        wf(os.path.join(src, name), body)
    cands = wf(os.path.join(d, "cands.tsv"), "件名\tmd5\n")
    for dirpath, _dirs, filenames in os.walk(src):
        for fn in sorted(filenames):
            if fn.endswith(".v"):
                rel = os.path.relpath(os.path.join(dirpath, fn), src)[:-2]
                with io.open(cands, "a", encoding="utf-8", newline="\n") as fh:
                    fh.write("%s\t%s\n" % (rel.replace(os.sep, "/"),
                                           md5_of(os.path.join(dirpath, fn))))
    return src, cands, wd, injdir


def u_scenario(injdir, probes, resprobes=None):
    scen = {"probe": probes}
    if resprobes is not None:
        scen["resprobe"] = resprobes
    wj(os.path.join(injdir, "scenario.json"), scen)
    return injdir


L1 = None    # 模块级懒建（dict 不可哈希默认参）——见 rows()


# ---- ① unclog 四行 ------------------------------------------------------------

def row_u1(tmp):
    """缺 --apply 零写盘：有方案（cures_planned=1）而 tmp 源树 md5 恒同·
    无落刀账。"""
    src, cands, wd, injdir = u_fixture(tmp, "u1")
    u_scenario(injdir, [L1, L1], [u_led({"A": u_rec0("A")})])
    before = tree_manifest(src)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--rounds", "1",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 1, "缺 --apply 应 rounds-exhausted rc=1 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["schema"] == SCHEMA_UNCLOG and rep["verdict"] == "rounds-exhausted"
    assert rep["mode"]["apply"] is False, rep["mode"]
    assert rep["final"]["cures_planned_total"] == 1, "干跑应有方案"
    assert rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert tree_manifest(src) == before, "缺 --apply 下源树字节被动＝护栏破"
    assert not os.path.exists(os.path.join(wd, "round-1.apply.json")), \
        "无 --apply 不得有落刀账"


def row_u2(tmp):
    """--audit 零写盘＋与 --apply 互斥：audit 只读基线（cures 恒空·树恒同）；
    --audit --apply 同给 rc=2。"""
    src, cands, wd, injdir = u_fixture(tmp, "u2")
    u_scenario(injdir, [L1])
    before = tree_manifest(src)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--audit",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 0, "audit 只读基线应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "audit" and rep["mode"]["audit"] is True
    assert rep["final"]["cures_planned_total"] == 0 \
        and rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert rep["rounds"][0]["cure"] is None, "audit 不得有落刀判面"
    assert tree_manifest(src) == before, "audit 下源树字节被动＝护栏破"
    rc2, out2 = sh(UNCLOG, ["--src", src, "--candidates", cands, "--audit",
                            "--apply"])
    assert rc2 == 2, "--audit --apply 同给应 rc=2 实测 %d\n%s" % (rc2, out2[-300:])
    assert "mutually exclusive" in out2, out2[-300:]  # synced to the translated unclog mutex message


def row_u3(tmp):
    """frozen 红拒：根名 wash_engine 撞 frozen8 在册（certify/frozen8.py --ledger
    真实取册）→ wall frozen-in-service·零落刀·在册同名夹具件字节恒同。"""
    src, cands, wd, injdir = u_fixture(
        tmp, "u3", extra_v=[("wash_engine.v", CURE13_BODY)])
    LF = u_led({"wash_engine": u_rec0("wash_engine"),
                "D": u_rec1("D", "wash_engine")})
    u_scenario(injdir, [LF])
    frozen_v = os.path.join(src, "wash_engine.v")
    before = md5_of(frozen_v)
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--apply",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 1, "frozen 红拒应 wall rc=1 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "wall", rep["verdict"]
    assert rep["wall"]["wash_engine"]["reason"] == "frozen-in-service", rep["wall"]
    assert rep["rounds"][0]["cure"] is None, "frozen 红拒后不得有落刀判面"
    assert rep["final"]["cures_applied_total"] == 0, rep["final"]
    assert md5_of(frozen_v) == before, "frozen 在册件被落刀＝护栏破"


def row_u4(tmp):
    """非链根件零被动：--apply 落刀受治根件 A.v 正典化，而消费者 B.v md5 恒同
    （落刀对象恒为链根件·pick 之外无 cure 调用路径）。"""
    src, cands, wd, injdir = u_fixture(tmp, "u4")
    u_scenario(injdir, [L1, u_led({"A": u_rec0("A"), "B": u_rec0("B")})],
               [u_led({"A": u_rec0("A")})])
    b_before = md5_of(os.path.join(src, "B.v"))
    rc, out = sh(UNCLOG, ["--src", src, "--candidates", cands, "--apply",
                          "--injector", injdir, "--workdir", wd,
                          "--json", os.path.join(wd, "rep.json")])
    assert rc == 0, "绿径落刀应 unclogged rc=0 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(wd, "rep.json"))
    assert rep["verdict"] == "unclogged"
    assert rep["final"]["cures_applied_total"] == 1, rep["final"]
    a_text = io.open(os.path.join(src, "A.v"), encoding="utf-8").read()
    assert "S01_BaseRing.NatLe (gnPrf f pf) k" in a_text, "链根件未被正典落刀"
    assert rep["rounds"][0]["cure"]["on_disk_md5_match"] is True, rep["rounds"][0]
    assert md5_of(os.path.join(src, "B.v")) == b_before, \
        "非链根件被动＝护栏破（落刀面越界）"


# ---- ② wash_shape 四行 --------------------------------------------------------

SHAPE_HEADER = ("(* 使命：破坏面矩阵夹具。\n"
                "   依赖：无。\n"
                "   对标：无。\n"
                "   构造性：全闭合。\n"
                "   编译配方：rocq c -Q . \"\" fixture.v。 *)\n")


def row_w1(tmp):
    """plan 缺省零写盘：真实脏件（CRLF＋禁词 载体·真 gate4 判面）plan 出
    would-fix≥1（看见可洗面）而树 md5 恒同。"""
    d = os.path.join(tmp, "w1")
    tree, outd = os.path.join(d, "tree"), os.path.join(d, "out")
    os.makedirs(tree)
    os.makedirs(outd)
    dirty = wf(os.path.join(tree, "dirty.v"),
               (SHAPE_HEADER + "Definition a := 1. (* 这里埋一个载体词 *)\n"
                                "Definition b := 2.\n").replace("\n", "\r\n"),
               newline="")
    before = tree_manifest(tree)
    rc, out = sh(WASH_SHAPE, ["--file", dirty, "--json",
                              os.path.join(outd, "rep.json")])
    assert rc == 1, "脏件 plan 应 partial rc=1 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(outd, "rep.json"))
    assert rep["schema"] == "rocqwash-shape/1"
    assert rep["mode"] == "plan", rep["mode"]
    assert rep["verdict"] == "partial", rep["verdict"]
    assert rep["plan"]["stats"]["would_fix"] >= 1, "plan 应看见可洗面"
    assert tree_manifest(tree) == before, "plan 缺省下树字节被动＝护栏破"
    assert not os.path.exists(os.path.join(tree, ".wash_shape_json_0")), \
        "plan 落盘残留在收件面＝护栏破"


def row_w2(tmp):
    """--apply 后 rescan partial 不谎报 shaped：gate4/sweep 罐装——apply 账面
    成功而复扫仍 would-fix → verdict=partial exit 1（verdict_of 未净不给
    shaped）。"""
    d = os.path.join(tmp, "w2")
    outd = os.path.join(d, "out")
    os.makedirs(outd)
    dirty = wf(os.path.join(d, "dirty2.v"), "Definition x := 1.\n")
    inj = wj(os.path.join(d, "inj.json"), {
        "gate4": {"rc": 1, "stdout": "canned-gate4", "report": {"results": [
            {"file": dirty, "verdict": "FAIL",
             "hard": [[6, "体内散块", "禁词", "载体"]], "review": []}]}},
        "scan_v4": {"rc": 0, "stdout": "canned-scan",
                    "report": {"station_count": 0, "tracked_ids": []}},
        "sweep": {"rc": 0, "stdout": "canned-sweep",
                  "report": {"report": {"flag_swaps": 1}}}})
    rc, out = sh(WASH_SHAPE, ["--file", dirty, "--apply", "--injector", inj,
                              "--json", os.path.join(outd, "rep.json")])
    assert rc == 1, "rescan 未净应 partial rc=1 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(outd, "rep.json"))
    assert rep["verdict"] == "partial", \
        "rescan 未净谎报 shaped＝护栏破 实测 %r" % rep["verdict"]
    assert rep["apply"]["rescan"]["stats"]["would_fix"] == 1, rep["apply"]
    assert "RESCAN: would_fix=1" in out, out[-400:]


def row_w3(tmp):
    """冻结名红拒：显式 --file 指认 frozen8 真在册件（verify/gate4_comment_guard.py
    ·先验在册前提）→ rc=2 红拒·收件即拒零引擎（在册件只递路径不触内容）。"""
    rc, out = sh(FROZEN8, ["--ledger"])
    assert rc == 0, "frozen8 --ledger 应 rc=0（红拒前提·离线账载）"
    roster = [ln.split()[1] for ln in out.splitlines()
              if len(ln.split()) == 2]
    target = os.path.join(REPO, "verify", "gate4_comment_guard.py")
    assert "verify/gate4_comment_guard.py" in roster, \
        "红拒前提破：目标件不在 frozen8 在册: %s" % roster
    rc, out = sh(WASH_SHAPE, ["--file", target, "--only", "eol"])
    assert rc == 2, "显式指认冻结件应红拒 rc=2 实测 %d\n%s" % (rc, out[-400:])
    assert "rejection" in out, out[-300:]  # synced to the translated wash_shape frozen-surface rejection message


def row_w4(tmp):
    """--header-map 与 --header-map-preset 同槽互斥 rc=2（main 前置闸·先于
    引擎装载）。"""
    d = os.path.join(tmp, "w4")
    os.makedirs(d)
    clean = wf(os.path.join(d, "clean.v"),
               SHAPE_HEADER + "Definition a := 1.\n")
    mp = wj(os.path.join(d, "map.json"), {})
    rc, out = sh(WASH_SHAPE, ["--file", clean, "--header-map", mp,
                              "--header-map-preset", "campaign_set_diamond"])
    assert rc == 2, "同槽双旗应 rc=2 实测 %d\n%s" % (rc, out[-400:])
    assert "same-slot" in out, out[-300:]  # synced to the translated wash_shape same-slot exclusivity message


# ---- ③ pushci 三行 ------------------------------------------------------------

SHA40 = "5f1e2d3c4b5a69788796a5b4c3d2e1f0a9b8c7d6"
RUN_ID = 9026111201


def p_runs_body(conclusion):
    return {"total_count": 1, "workflow_runs": [
        {"id": RUN_ID, "run_number": 7, "name": "ci", "head_branch": "work",
         "head_sha": SHA40, "status": "completed", "conclusion": conclusion,
         "html_url": "https://github.com/org/repo/actions/runs/%d" % RUN_ID}]}


def p_setup(tmp, tag, api_steps, jobs=None, tools=None):
    """pushci steps 形注入场＋git-caller 场（get-url→rev-parse→push→ls-remote
    实调序）。→ (repo, injdir, gitjson, api_calls_path, git_calls_path)。"""
    d = os.path.join(tmp, tag)
    repo, injdir = os.path.join(d, "repo"), os.path.join(d, "inj")
    os.makedirs(repo)
    os.makedirs(injdir)
    scen = {"steps": api_steps,
            "tools": tools or {"toolchain_dyld_doctor": {"rc": 0,
                                                         "verdict": "healthy"},
                               "net_probe": {"rc": 0, "verdict": "STABLE"}}}
    if jobs is not None:
        scen["jobs"] = jobs
    wj(os.path.join(injdir, "scenario.json"), scen)
    gitjson = wj(os.path.join(d, "git.json"), {"responses": [
        {"args_contains": ["get-url"], "rc": 0,
         "stdout": "https://github.com/org/repo.git\n"},
        {"args_contains": ["rev-parse"], "rc": 0, "stdout": SHA40 + "\n"},
        {"args_contains": ["push"], "rc": 0,
         "stdout": "To https://github.com/org/repo.git\n"},
        {"args_contains": ["ls-remote"], "rc": 0,
         "stdout": "%s\trefs/heads/work\n" % SHA40}]})
    return repo, injdir, gitjson, os.path.join(injdir, "api_calls.json"), \
        os.path.join(d, "git.calls.json")


def p_fire(repo, injdir, gitjson, extra):
    env = dict(os.environ)
    env.pop("ROCWASH_MASK", None)
    cmd = [sys.executable, "-B", PUSHCI, "--repo-path", repo,
           "--branch", "work", "--remote", "origin", "--injector", injdir,
           "--git-caller", gitjson,
           "--netrc", os.path.join(tempfile.gettempdir(),
                                   "dm_no_such_netrc_parity"),
           "--sleep-scale", "0"] + list(extra)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env)
    out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")
    return p.returncode, out


def row_p1(tmp):
    """--dry-run 零副作用：rc=0 verdict=dry-run·stages 全空·api_calls 与
    git-caller 双流水皆空（零 git 调零 API 调零工具子进程）。"""
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p1", [])
    rep_path = os.path.join(tmp, "p1", "out.json")
    rc, out = p_fire(repo, injdir, gitjson,
                     ["--dry-run", "--pre-scan-gate4", "--json", rep_path])
    assert rc == 0, "dry-run 应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "dry-run" and rep["mode"] == "dry-run", rep["verdict"]
    assert rep["stages"] == {}, "dry-run 不得有段执行账: %s" % list(rep["stages"])
    assert rep.get("plan"), "dry-run 应出计划"
    assert os.path.isfile(api_calls) and os.path.isfile(git_calls), \
        "双流水出账件应在位（注入模式实证面）"
    assert jl(api_calls) == [], "dry-run 零 API 调用实证失守＝护栏破"
    assert jl(git_calls) == [], "dry-run 零 git 调用实证失守＝护栏破"


def row_p2(tmp):
    """内容红零 rerun：family=A-content-red → fix-content exit 2·heal.rounds
    空＝零 rerun 实证（api 流水零 POST）·证据含 禁代修。"""
    jobs_a = jl(JOBS_A)
    steps = [{"at_round": 1, "responses": [
        {"method": "GET", "path": "/actions/runs?per_page=30", "status": 200,
         "body": p_runs_body("failure")}]}]
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p2", steps,
                                                          jobs=jobs_a)
    rep_path = os.path.join(tmp, "p2", "out.json")
    rc, out = p_fire(repo, injdir, gitjson, ["--json", rep_path])
    assert rc == 2, "内容红应 fix-content exit 2 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "fix-content", rep["verdict"]
    h = rep["stages"]["heal"]
    assert h["rounds"] == [] and h["fired_total"] == 0, \
        "内容红零 rerun 实证失守＝护栏破: %r" % h
    assert h["last_triage"]["family"] == "A-content-red", h["last_triage"]
    calls = jl(api_calls)
    assert all(c["method"] != "POST" for c in calls), \
        "内容红下出现 POST rerun＝护栏破: %r" % calls
    assert any("禁代修" in e for e in rep["evidence"]), rep["evidence"]


def row_p3(tmp):
    """heal 帽尽停：--max-heal 3·NETRED 四轮 failure——恰 3 发 POST rerun 后
    heal-exhausted exit 1（帽尽即停·无第 4 发）。"""
    jobs_b = jl(JOBS_B)
    steps = []
    for i in range(1, 5):
        resps = [{"method": "GET", "path": "/actions/runs?per_page=30",
                  "status": 200, "body": p_runs_body("failure")}]
        if i <= 3:
            resps.append({"method": "POST", "path": "/rerun", "status": 201,
                          "body": {}})
        steps.append({"at_round": i, "responses": resps})
    repo, injdir, gitjson, api_calls, git_calls = p_setup(tmp, "p3", steps,
                                                          jobs=jobs_b)
    rep_path = os.path.join(tmp, "p3", "out.json")
    rc, out = p_fire(repo, injdir, gitjson,
                     ["--max-heal", "3", "--json", rep_path])
    assert rc == 1, "heal 帽尽应 heal-exhausted exit 1 实测 %d\n%s" \
        % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["verdict"] == "heal-exhausted", rep["verdict"]
    h = rep["stages"]["heal"]
    assert len(h["rounds"]) == 3 and h["fired_total"] == 3, h
    calls = jl(api_calls)
    n_post = sum(1 for c in calls if c["method"] == "POST")
    n_get = sum(1 for c in calls if c["method"] == "GET")
    assert n_post == 3, "帽 3 应恰 3 发 rerun（多发行/少发行均破）实测 %d" % n_post
    assert n_get == 4, "四轮 poll 应 4 GET 实测 %d" % n_get


# ---- ④ cw_sentinel 两行 -------------------------------------------------------

def s_canned(tmp, tag):
    """sentinel canned API（runs 红件 178＋jobs A 形红步）→ injector 路径。"""
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    runs_body = {"total_count": 1, "workflow_runs": [
        {"id": 178, "name": "CI", "run_number": 9, "status": "completed",
         "conclusion": "failure", "head_branch": "main",
         "head_sha": "abc123def",
         "html_url": "https://github.com/org/repo/actions/runs/178"}]}
    jobs_body = {"total_count": 1, "jobs": [
        {"id": 501, "name": "build", "status": "completed",
         "conclusion": "failure", "started_at": "2026-11-10T08:00:00Z",
         "completed_at": "2026-11-10T08:01:00Z",
         "steps": [{"number": 1, "name": "Build (coqc batch)",
                    "status": "completed", "conclusion": "failure",
                    "started_at": "2026-11-10T08:00:01Z",
                    "completed_at": "2026-11-10T08:00:30Z"}]}]}
    return wj(os.path.join(d, "injector.json"), {
        "schema": "rocqwash-sentinel-injector/1", "responses": [
            {"url_contains": "/actions/runs?", "status": 200,
             "body": runs_body},
            {"url_contains": "/runs/178/jobs", "status": 200,
             "body": jobs_body}]})


def row_s1(tmp):
    """缺省 report-only：无 --on-red 无 --on-red-preset 时零子进程动作——
    CI 红件出 ci-red 事件（见红）而 actions 账全空（不动手）。"""
    inj = s_canned(tmp, "s1")
    d = os.path.join(tmp, "s1")
    state = os.path.join(d, "state.json")
    emit = os.path.join(d, "events.jsonl")
    rep_path = os.path.join(d, "rep.json")
    rc, out = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                            "--injector", inj, "--state-file", state,
                            "--emit", emit, "--json", rep_path,
                            "--sleep-scale", "0"])
    assert rc == 0, "report-only 巡检应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(rep_path)
    assert rep["schema"] == "rocqwash-sentinel/1"
    evs = [json.loads(ln) for ln in io.open(emit, encoding="utf-8")
           if ln.strip()]
    assert any(e["kind"] == "ci-red" for e in evs), \
        "应见红出事件（ci-red 在流）: %r" % evs
    assert rep["actions"] == [], \
        "缺省 report-only 下出现动作账＝护栏破（零子进程动作失守）: %r" \
        % rep["actions"]
    assert "on-red" not in out.replace("on-red-preset", ""), out[-300:]


def row_s2(tmp):
    """on-red 双路同守卫：plain --on-red 与 --on-red-preset 缺 --emit 皆
    → rc=2（旁路动作必伴随事件流落盘·触发证据与动作账可审计；{emit_dir} 系
    --emit 派生缺盘即拒）——v40 矩阵登记缺口（plain 路径缺同款守卫）v41 补齐
    转正·build_sentry 前置·零巡检零动作。"""
    rc, out = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                            "--on-red", "echo x", "--sleep-scale", "0"])
    assert rc == 2, "plain 缺 --emit 应 rc=2 实测 %d\n%s" % (rc, out[-400:])
    assert "--emit" in out, out[-300:]
    rc2, out2 = sh(SENTINEL, ["--once", "--watch-repo", "org/repo",
                              "--on-red-preset", "unclog",
                              "--on-red-arg", "src=" + os.path.join(tmp, "s2"),
                              "--sleep-scale", "0"])
    assert rc2 == 2, "preset 缺 --emit 应 rc=2 实测 %d\n%s" % (rc2, out2[-400:])
    assert "--emit" in out2, out2[-300:]


# ---- ⑤ registry_union／cure_applier 四行 --------------------------------------

def r_fixture(tmp, tag):
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    base = wf(os.path.join(d, "base.txt"), "A.v\nB.v\n")
    main = wf(os.path.join(d, "main.txt"), "A.v\nB.v\n")
    branch = wf(os.path.join(d, "branch.txt"), "A.v\nB.v\nC.v\n")
    return d, base, main, branch


def row_r1(tmp):
    """registry_union 干跑缺省零写盘：--out 已给而缺省不落盘。"""
    d, base, main, branch = r_fixture(tmp, "r1")
    outp = os.path.join(d, "union.txt")
    rep = os.path.join(d, "rep.json")
    rc, out = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                  "--branch", branch, "--kind", "order",
                                  "--out", outp, "--json", rep])
    assert rc == 0, "干跑应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    assert not os.path.exists(outp), \
        "缺 --apply 时 --out 落盘＝护栏破（干跑零写盘失守）"
    assert "DRY-RUN" in out, out[-300:]


def row_r2(tmp):
    """registry_union --apply 才落刀：--apply 后 --out 在位含 union 行；且
    --apply 无 --out → rc=2 禁隐式覆写。"""
    d, base, main, branch = r_fixture(tmp, "r2")
    outp = os.path.join(d, "union.txt")
    rc, out = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                  "--branch", branch, "--kind", "order",
                                  "--out", outp, "--apply"])
    assert rc == 0, "--apply 应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    assert os.path.isfile(outp), "--apply 后 --out 未落盘＝护栏破"
    assert io.open(outp, encoding="utf-8").read() == "A.v\nB.v\nC.v\n", \
        "union 稿内容非预期: %r" % io.open(outp, encoding="utf-8").read()
    rc2, out2 = sh(REGISTRY_UNION, ["--base", base, "--main", main,
                                    "--branch", branch, "--kind", "order",
                                    "--apply"])
    assert rc2 == 2, "--apply 无 --out 应 rc=2 实测 %d\n%s" % (rc2, out2[-300:])
    assert "须配 --out" in out2, out2[-300:]


def row_c1(tmp):
    """cure_applier 干跑缺省零写盘：缺省（无 --apply）只出报告·目标件 md5
    恒同。"""
    d = os.path.join(tmp, "c1")
    os.makedirs(d)
    f = wf(os.path.join(d, "t.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    before = md5_of(f)
    rc, out = sh(CURE_APPLIER, ["--file", f, "--json", rep])
    assert rc == 0, "干跑应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    r = jl(rep)
    assert r["mode"] == "DRY-RUN", r["mode"]
    assert sum(v["matches"] for v in r["report"].values()) >= 1, \
        "干跑应有命中（有刀可落而未落）"
    assert md5_of(f) == before, "干跑下目标件字节被动＝护栏破"


def row_c2(tmp):
    """cure_applier --apply 才落刀＋幂等断言拒写：正典包 --apply 落刀（件正典
    化·md5 变·二遍幂等 rc=0）；自定义非幂等包 --apply → IDEMPOTENCE-FAIL
    rc=1 且件零字节动（拒写）。"""
    d = os.path.join(tmp, "c2")
    os.makedirs(d)
    f = wf(os.path.join(d, "t.v"), CURE13_BODY)
    before = md5_of(f)
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply",
                                "--json", os.path.join(d, "rep.json")])
    assert rc == 0, "--apply 正典落刀应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    text = io.open(f, encoding="utf-8").read()
    assert "S01_BaseRing.NatLe (gnPrf f pf) k" in text, "落刀未正典化"
    assert md5_of(f) != before, "--apply 后件未动＝落刀失守"
    rc2, out2 = sh(CURE_APPLIER, ["--file", f, "--apply"])
    assert rc2 == 0, "二遍幂等应 rc=0 实测 %d\n%s" % (rc2, out2[-300:])
    # 非幂等包：trigger "a"→template "aa"（输出再中触发）→ 幂等断言败拒写
    d2 = os.path.join(tmp, "c2b")
    os.makedirs(d2)
    g = wf(os.path.join(d2, "g.v"), "Lemma a : True.\n")
    pack = wj(os.path.join(d2, "nonidem_pack.json"), {
        "pack": "dm_nonidem", "version": "0",
        "patterns": [{"id": "dm_nonidem", "title": "matrix non-idempotent probe",
                      "engine": "line-regex", "trigger_regex": "a",
                      "template": "aa"}]})
    g_before = md5_of(g)
    rc3, out3 = sh(CURE_APPLIER, ["--file", g, "--pack", pack, "--apply"])
    assert rc3 == 1, "幂等断言败应 rc=1 实测 %d\n%s" % (rc3, out3[-400:])
    assert "IDEMPOTENCE-FAIL" in out3, out3[-300:]
    assert md5_of(g) == g_before, "幂等断言败后件被写＝护栏破（file NOT written 失守）"


# ---- 矩阵总装 -----------------------------------------------------------------

L1 = u_led({"A": u_rec0("A"), "B": u_rec1("B", "A")})   # A 可洗链根·B 缺 A

ROWS = [
    ("U1", "unclog", "缺 --apply 零写盘（tmp 树 md5 恒同·无落刀账）",
     "tools/unclog.py:42,583,607", row_u1),
    ("U2", "unclog", "--audit 零写盘（树自证）＋与 --apply 互斥 rc=2",
     "tools/unclog.py:827,762", row_u2),
    ("U3", "unclog", "frozen 在册红拒（frozen8 实取·零落刀）",
     "tools/unclog.py:506", row_u3),
    ("U4", "unclog", "非链根件零被动（落刀面恒为链根件）",
     "tools/unclog.py:43,583,607", row_u4),
    ("W1", "wash_shape", "plan 缺省零写盘（看见 would-fix 而树恒同）",
     "tools/wash_shape.py:1254", row_w1),
    ("W2", "wash_shape", "--apply 后 rescan partial 不谎报 shaped",
     "tools/wash_shape.py:1192-1205", row_w2),
    ("W3", "wash_shape", "冻结名显式指认红拒 rc=2（收件即拒）",
     "tools/wash_shape.py:759-761", row_w3),
    ("W4", "wash_shape", "--header-map 与 --header-map-preset 同槽互斥 rc=2",
     "tools/wash_shape.py:1887-1890", row_w4),
    ("P1", "pushci", "--dry-run 零副作用（api_calls/git-caller 双流水空）",
     "tools/pushci.py:1163-1164,1116", row_p1),
    ("P2", "pushci", "内容红零 rerun（heal.rounds 空·api 零 POST）",
     "tools/pushci.py:983-987", row_p2),
    ("P3", "pushci", "heal 帽尽停（--max-heal 3 恰 3 发后裁停）",
     "tools/pushci.py:966-969", row_p3),
    ("S1", "cw_sentinel", "缺省 report-only（无 on-red 旗零子进程动作）",
     "tools/cw_sentinel.py:713-715", row_s1),
    ("S2", "cw_sentinel", "on-red 双路同守卫（plain/preset 缺 --emit 皆 rc=2）",
     "tools/cw_sentinel.py:722-723,884-886", row_s2),
    ("R1", "registry_union", "干跑缺省零写盘（--out 给而不落）",
     "tools/registry_union.py:881-885", row_r1),
    ("R2", "registry_union", "--apply 才落刀（＋无 --out rc=2 禁隐式覆写）",
     "tools/registry_union.py:826,883-885", row_r2),
    ("C1", "cure_applier", "干跑缺省零写盘（目标件 md5 恒同）",
     "wash/cure_applier.py:1109,1134", row_c1),
    ("C2", "cure_applier", "--apply 才落刀＋幂等断言败拒写（rc=1 零字节动）",
     "wash/cure_applier.py:1134-1150", row_c2),
]


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_dm_")
    fails = []
    try:
        for rid, tool, guard, anchor, fn in ROWS:
            rowtmp = os.path.join(tmp, rid)
            os.makedirs(rowtmp)
            try:
                fn(rowtmp)
                print("PASS %s %-14s %s" % (rid, tool, guard))
            except AssertionError as e:
                fails.append((rid, anchor, guard, str(e)))
                print("FAIL %s %-14s %s" % (rid, tool, guard))
            except Exception as e:   # 行内环境炸亦按破计（fail-loud 不静默）
                fails.append((rid, anchor, guard, "行炸（环境/夹具）: %r" % e))
                print("FAIL %s %-14s %s（行炸）" % (rid, tool, guard))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("== destructive-matrix: %d 行过 / %d 行破 ==" % (len(ROWS) - len(fails),
                                                          len(fails)))
    if fails:
        print("MATRIX 破口清单（护栏破 file:line）:")
        for rid, anchor, guard, detail in fails:
            print("  破口 %s @ %s — %s\n    违据: %s" % (rid, anchor, guard,
                                                        detail))
        return 1
    print("DESTRUCTIVE-MATRIX PASS: 17 行拒写判据全过（unclog×4/wash_shape×4/"
          "pushci×3/cw_sentinel×2/registry_union×2/cure_applier×2·全 tmp "
          "fixture＋injector 罐装零真网络零真仓零真编译）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
