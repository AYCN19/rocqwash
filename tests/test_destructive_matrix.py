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
        锚 wash/cure_applier.py:1272/:1338（if args.apply 写闸）
     C2 --apply 才落刀＋幂等断言拒写：--apply 落刀且二遍零残才写盘；幂等断言
        败（自定义非幂等包）→ rc=1 file NOT written
        锚 wash/cure_applier.py:1282-1285（IDEMPOTENCE-FAIL 拒写）
     C3 write-face byte contract: after --apply on an LF fixture the on-disk
        bytes md5 equals the reported md5_after and no \r\n ever lands on
        disk (io.open newline="" pin; without it Windows text mode wrote
        CRLF while the report md5 was LF-caliber — the T0-5 md5-caliber
        defect; second pass must stay byte-identical)
        anchor wash/cure_applier.py:1338-1341 (pinned write face)
     C4 compile-leg write face (T0-2/T0-3 S1 sync): the --apply compile
        leg compiles temp-only copies (.vo never lands in the repo tree);
        env unset -> honest not-run record with the write proceeding
        unchanged; env set but binary missing -> rc=9 fail-loud with the
        file NOT written (never a simulated green)
        锚 wash/cure_applier.py:660（compile_leg）＋:1286-1336（leg 总闸）＋
        :1300-1306（rc=9 fail-loud 面）
  ⑦ certify/frozen8.py（冻结名单器·写面＝freeze 显式 --out/--tier2 两径＋
     timestamp 显式 --out 回执一径）
     F1 freeze 只落显式两径＋账载漂移 fail-closed 拒出名单（rc=1 零写）：
        scratch git skeleton 十件冻结面 freeze 后仓树 md5 恒同；verify_vo.py
        一字节篡改 → 拒出名单且 --out 零字节
        锚 certify/frozen8.py:357,366（显式两写口）＋:334（拒出名单 fail-closed）
     F2 timestamp 唯一写面＝显式 --out 回执且绑定复验后才落：--out 缺席
        rc=2 零写；TSA 不可达（闭合回环指认 ROCWASH_TSA_URL）rc=9 零写
        ——回执只在 digest 绑定本地复验通过后落盘
        锚 certify/frozen8.py:806（唯一写口·:799-803 绑定闸前置）＋:772
        （可达性自勘失败 rc=9）
  ⑧ tools/axiom_guard.py (axiom guard; write face = the caller-named --out
     report volume plus one private temp workdir path; the .vo output face
     is temp-only, zero bytes into the repository tree)
     G1 compile-leg write face temp-only + honest skip: toolchain
        unconfigured (no env, no flags) -> rc=111 honest skip, zero
        judgment, the watched scratch tree md5-constant, no --out created;
        configured binaries missing -> rc=9 fail-loud before any work
        (zero writes, zero compiles)
        锚 tools/axiom_guard.py:main env gate (rc 111 / rc 9 ahead of
        guard()) + :guard private mkdtemp (write faces = workdir and the
        caller-named --out only)
  ⑨ tools/jargon_apply.py (wash-map applier; write face = the .py/.sh/.md
     prose faces under --tree, or the one --file target)
     J1 self-reference guard: the wash map's own source table
        (--a2-table, default docs/jargon-to-standard-mapping-v1.md) is never
        a wash target — --tree excludes it from the target set and --file on
        it is refused rc=1 loud (a tool never washes its own map; the
        e04f2f6 round washed it and stripped 11 of the 13 contract rows the
        seed pins by md5)
        锚 tools/jargon_apply.py:550-560（skip_abs 自引用排除）＋:471-484
        （--file 红拒面）
  ⑩ tools/scheduler_lite.py（排程 lite·X2 面·写面＝显式 --out 一径）
     SL1 plan 缺省零写盘：全旗标 tmp fixture 罐装下 plan 出 due 判面而
        tmp 树 md5 恒同·无 --out 即无任何落盘（dryRun=true 恒钉）
        锚 tools/scheduler_lite.py:364-366（run_plan if args.out 唯一写闸）
        ＋:309（build_plan dryRun=True 恒真）
     SL2 唯一写面＝显式 --out 且字节确定：给 --out 恰落一文件（plan 文档）
        ·输入树 md5 恒同·两跑字节恒同（plan_bytes sort_keys 确定性字节形）
        锚 tools/scheduler_lite.py:364-366＋:328-331（plan_bytes 确定性字节）
  ⑪ tools/auto_merge.py（自动合并门·X5 面·写面＝--apply 合并账 append 一径）
     AM1 缺 --apply 零写盘：merge-ok＋supply/* 白名单内（rail 裁 allowed）
        而台账不落盘不创建（report --json 显式另计）
        锚 tools/auto_merge.py:244-247（run_rail if apply_mode append 总闸）
     AM2 hold 永不授权＋越权分支红拒：hold-red 判定 --apply 亦零写（rail
        not-eligible 先于合并账）；非 supply/* 头 rc=1 白名单红拒零写
        锚 tools/auto_merge.py:220-221（verdict!=merge-ok 先决）＋:225-228
        （branch 白名单闸）
     AM3 日预算帽＋重复拒：--daily-cap 3 恰 3 行 authorize 后第 4 拒
        rc=1·同日同 PR 重复拒 rc=1·合并账恰 3 行不增
        锚 tools/auto_merge.py:229-233（日帽闸）＋:234-239（重复闸）
  ⑫ tools/repair_scope.py（共享排除名册·F1/E2 单源）＋E 波四守卫类
     RS1 --check 查询面零写盘＋排除判词咬合：共享 full_frozen_files（运行
        LEDGER8 AST 读·缺件退化快照 loud）＋FROZEN_DIR_FAMILIES＋
        LEGAL_DATA_DIR_FAMILIES＋docs/zh＋.zh.md 档案镜像全 EXCLUDED；
        class-2 三可修面（tests/README.md·README.md·账面）REPAIRABLE；
        查询零写盘
        锚 tools/repair_scope.py:140-160（exclusion_roster/full_frozen_files）
        ＋:556-576（RosterResyncScope.refusal_reason）＋:590-620（check_faces）
     E2A class-1 lane-extract（--lane-detect/--lane-apply）：缺省零写零账；
        排除账面（seeds/ 族）rc=2 红拒且零创建；预算帽（2 前科）rc=2
        拒写·套件字节恒同·只落 escalated(budget-cap) 账行
        锚 tools/repair_scope.py:477-482（excluded face 拒）＋:400-411
        （_lane_ledger_gate 账面同闸）＋:487-493（预算帽）
     E2B class-2 roster-resync（tools/roster_resync.py）：缺省零写零账；
        --apply 单向派生（roster 文件字节恒同·计数面修至=名册值·一
        修复一账行）；预算帽 rc=1 拒写·面字节恒同·只落 escalated 行
        锚 tools/roster_resync.py:246-248（缺省零写盘闸）＋:256-265（预算帽）
        ＋:327-334（frozen 面升格不落刀）＋tools/repair_scope.py:556-576
     E2C class-3 flaky-quarantine（tools/flaky_guard.py --move）：冻结靶
        （seeds/ 族名册）rc=1 红拒零写零账（scope 闸先于探针）；预算帽
        rc=1 拒写·名册字节恒同·只落 escalated 账行
        锚 tools/flaky_guard.py:390-396（_scope_check 单源消费·先于一切
        计划）＋:514-523（预算帽）
     E2D class-4 doc-count（--doc-count-detect/--doc-count-apply）：缺省
        零写零账；--apply 修至 face=source 且幂等（二遍零字节）；预算帽
        rc=2 拒写·目标面字节恒同·只落 escalated(budget-cap) 行
        锚 tools/repair_scope.py:917-926（apply 写面前置闸）＋:975-994
        （预算帽）＋:997-1009（post-assertion 拒写）

离线纪律（硬要求）：全判据走 tmp fixture＋--injector 罐装（unclog probe/resprobe
canned·wash_shape 引擎键 canned·pushci steps/jobs/git-caller canned·sentinel
canned API）——零真网络零真仓零真编译；真子进程仅限纯 stdlib 离线引擎
（chain_graph/cure_applier/scan_v4_token/frozen8 --ledger/--selftest/freeze
（scratch skeleton）/gate4/ci_triage --offline·判例：各器自带 --selftest
同款；E2C 预算帽面经 flaky_guard 探针跑 tmp 内三行 bash 夹具套件，
flaky_guard --selftest 同款先例）。唯一例外 W3 递真在册件**路径**：
工具在 collect_files 即红拒·零读零写（wash_shape 自身判8 同款先例）。

自体纪律：python3 -B 禁 __pycache__；零仓写盘（全部工件在 tempfile.mkdtemp）；
输出确定性（零墙钟零绝对仓路径）；env 兜底清洗（ROCWASH_HEADER_MAP／
ROCWASH_ROCQ／ROCWASH_COQCHK 剥除·防环境渗判防真编译渗阵）；fail-loud——
任一行炸（含环境异常）按破计不静默。

退出码：0=33 行判据全过；1=任一护栏破（响亮列破口 file:line＋违据）。

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
AXIOM_GUARD = os.path.join(REPO, "tools", "axiom_guard.py")
FROZEN8 = os.path.join(REPO, "certify", "frozen8.py")
JARGON_APPLY = os.path.join(REPO, "tools", "jargon_apply.py")
SCHEDULER_LITE = os.path.join(REPO, "tools", "scheduler_lite.py")
AUTO_MERGE = os.path.join(REPO, "tools", "auto_merge.py")
REPAIR_SCOPE = os.path.join(REPO, "tools", "repair_scope.py")
ROSTER_RESYNC = os.path.join(REPO, "tools", "roster_resync.py")
FLAKY_GUARD = os.path.join(REPO, "tools", "flaky_guard.py")
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


def tree_manifest(root, skip_dirs=(".git",)):
    """目录全文件 {rel(POSIX): md5} 清单（增删改一字节即现形·unclog 同款口径）。

    The .git directory is skipped by default: git legitimately rewrites its
    own metadata (reflog, index, gc.log) when it resolves HEAD or refreshes
    the index, and counting those bytes turns the tool's write-face judgment
    into a statement about git's internal bookkeeping. The rows that guard
    git-object writes assert on the object store explicitly, not on the
    surrounding metadata.
    """
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            out[os.path.relpath(fp, root).replace(os.sep, "/")] = md5_of(fp)
    return out


def sh(tool_abs, argv, env_extra=None):
    """python3 -B <tool> subprocess (stdout+stderr merged; environment
    sanitation strips ROCWASH_HEADER_MAP/ROCWASH_ROCQ/ROCWASH_COQCHK so no
    caller environment leaks into a verdict and no real compile leaks into
    the offline matrix).  env_extra is the explicit injection face for the
    configured-but-missing fail-loud rows only (it can never launch a real
    compile: the missing binary check precedes every work face)."""
    env = dict(os.environ)
    env.pop("ROCWASH_HEADER_MAP", None)
    env.pop("ROCWASH_ROCQ", None)
    env.pop("ROCWASH_COQCHK", None)
    if env_extra:
        env.update(env_extra)
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
    assert any("no automatic repair" in e for e in rep["evidence"]), rep["evidence"]


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


# ---- ⑤ registry_union／cure_applier 五行 --------------------------------------

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


def row_c3(tmp):
    """Write-face byte contract (S1 sync for the T0-5 newline change at
    wash/cure_applier.py:1090): after --apply on an all-LF fixture the
    on-disk byte md5 must equal the report's md5_after (md5s = md5 of the
    utf-8 text), no \\r\\n may land on disk, and the second idempotent pass
    must leave the bytes unchanged. Without the newline="" pin, Windows text
    mode wrote CRLF while the report md5 stayed LF-caliber, so the reported
    md5 never described the file it claims to describe."""
    d = os.path.join(tmp, "c3")
    os.makedirs(d)
    f = wf(os.path.join(d, "t3.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply",
                                "--json", os.path.join(d, "rep.json")])
    assert rc == 0, "--apply canonical write should exit 0, got %d\n%s" \
        % (rc, out[-400:])
    raw = open(f, "rb").read()
    r = jl(rep)
    on_disk_md5 = hashlib.md5(raw).hexdigest()
    assert on_disk_md5 == r["md5_after"], \
        "on-disk byte md5 %s != report md5_after %s = newline contract " \
        "broken (CRLF-caliber write face)" % (on_disk_md5, r["md5_after"])
    assert b"\r\n" not in raw, \
        "CRLF landed on disk from an all-LF fixture = byte face translated"
    rc2, out2 = sh(CURE_APPLIER, ["--file", f, "--apply",
                                  "--json", os.path.join(d, "rep2.json")])
    assert rc2 == 0, "second idempotent pass should exit 0, got %d\n%s" \
        % (rc2, out2[-300:])
    assert open(f, "rb").read() == raw, \
        "second pass drifted the on-disk bytes = idempotence broken"


# ---- ⑧ axiom_guard one row (T0-2 axiom guard S1 sync) ------------------------

def row_g1(tmp):
    """axiom_guard compile-leg write face (T0-2 axiom guard S1 sync): the
    run's only write faces are the caller-named --out report and its
    private temp workdir (the .vo output face is temp-only).  Face 1:
    toolchain unconfigured (env stripped by matrix sanitation) -> rc 111
    honest skip, zero judgment, the watched scratch tree gains zero bytes,
    and --out is not even created (the skip precedes every write face).
    Face 2: configured-but-missing binaries -> rc 9 fail-loud before any
    work (no compile can launch), the tree still gains zero bytes.  Face 3
    re-checks the --out non-creation explicitly with --out passed.  The
    real-compile coverage of the temp-only .vo face lives in the seat's
    live evidence run, outside the offline matrix (zero-real-compile
    discipline)."""
    d = os.path.join(tmp, "g1")
    tree = os.path.join(d, "tree")
    os.makedirs(tree)
    wf(os.path.join(tree, "one.v"), "Definition x := 1.\n")
    before = tree_manifest(tree)
    outp = os.path.join(d, "evid")
    rc, out = sh(AXIOM_GUARD, ["--repo", tree, "--out", outp])
    assert rc == 111, \
        "unconfigured toolchain must honestly skip rc 111, got %d\n%s" \
        % (rc, out[-400:])
    assert "SKIP" in out, \
        "rc 111 face must carry the SKIP banner: %s" % out[-300:]
    assert tree_manifest(tree) == before, \
        "skip face wrote the watched tree = write-face contract broken"
    assert not os.path.exists(outp), \
        "skip face created the --out dir = skip precedes every write face"
    rc2, out2 = sh(AXIOM_GUARD, ["--repo", tree],
                   env_extra={"ROCWASH_ROCQ": "D:/no_such_dir/rocq.exe",
                              "ROCWASH_COQCHK": "D:/no_such_dir/coqchk.exe"})
    assert rc2 == 9, \
        "configured-but-missing binaries must fail loud rc 9, got %d\n%s" \
        % (rc2, out2[-400:])
    assert "FAIL-LOUD" in out2, \
        "rc 9 face must carry the fail-loud banner: %s" % out2[-300:]
    assert tree_manifest(tree) == before, \
        "rc 9 face wrote the watched tree = write-face contract broken"


# ---- ⑥ addendum: the cure_applier compile-leg row (T0-2/T0-3 S1 duty:
# whoever writes a face, pins it in this matrix) -----------------------------

def row_c4(tmp):
    """cure_applier compile-leg write face (T0-2/T0-3 S1 sync): the --apply
    compile leg compiles temp-only copies (the repository tree gains zero
    bytes from the leg) and never activates offline.  Face 1: toolchain env
    stripped by matrix sanitation -> the leg records the honest
    not-configured status and the write proceeds with rc unchanged.
    Face 2: env set but the binary missing -> rc 9 fail-loud with the file
    NOT written (never a simulated green; the binary existence check
    precedes any compile launch, so this face stays offline).
    Face 3: a no-change second pass -> the leg records skipped-no-change
    without launching any compile.  The green->red interception and the
    temp-only .vo face of a live compile live in tests/test_cure_pack.py's
    env-gated section and the seat's evidence run, outside the offline
    matrix."""
    d = os.path.join(tmp, "c4")
    os.makedirs(d)
    f = wf(os.path.join(d, "t4.v"), CURE13_BODY)
    rep = os.path.join(d, "rep.json")
    rc, out = sh(CURE_APPLIER, ["--file", f, "--apply", "--json", rep])
    assert rc == 0, "offline --apply should exit 0, got %d\n%s" \
        % (rc, out[-400:])
    assert "COMPILE-LEG: SKIP" in out, \
        "unconfigured leg must carry the SKIP record: %s" % out[-300:]
    r = jl(rep)
    assert r.get("compile_check", {}).get("status") == "not-configured", \
        "not-configured leg must be recorded honestly: %r" % r.get("compile_check")
    d2 = os.path.join(tmp, "c4b")
    os.makedirs(d2)
    g = wf(os.path.join(d2, "g.v"), CURE13_BODY)
    g_before = md5_of(g)
    rc2, out2 = sh(CURE_APPLIER, ["--file", g, "--apply"],
                   env_extra={"ROCWASH_ROCQ": "D:/no_such_dir/rocq.exe"})
    assert rc2 == 9, \
        "configured-but-missing compiler must fail loud rc 9, got %d\n%s" \
        % (rc2, out2[-400:])
    assert "FAIL-LOUD" in out2, \
        "rc 9 face must carry the fail-loud banner: %s" % out2[-300:]
    assert md5_of(g) == g_before, \
        "rc 9 face wrote the target = write-face contract broken"
    rc3, out3 = sh(CURE_APPLIER, ["--file", f, "--apply",
                                  "--json", os.path.join(d, "rep3.json")])
    assert rc3 == 0, "no-change second pass should exit 0, got %d" % rc3
    r3 = jl(os.path.join(d, "rep3.json"))
    assert r3.get("compile_check", {}).get("status") == "skipped-no-change", \
        "no-change pass must record skipped-no-change: %r" \
        % r3.get("compile_check")


# ---- ⑦ frozen8 两行（A1 席 S1 强化律·20261115·谁写谁进阵）--------------------

F8_ROSTER = [
    "certify/freeze_manifest.py",
    "certify/frozen8.py",
    "certify/push_gate.py",
    "names/mac_stmt_names.py",
    "scan/mac_stmt_scan.py",
    "seam/seam_probe.py",
    "tools/cpu_guard.sh",
    "verify/gate4_comment_guard.py",
    "verify/verify_vo.py",
    "wash/wash_engine.py",
]


def f8_skeleton(root):
    """scratch git skeleton: byte-identical copies of the ten roster files,
    one scratch commit → usable as a freeze --repo target (offline)."""
    os.makedirs(root)
    for rel in F8_ROSTER:
        fp = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        shutil.copyfile(os.path.join(REPO, rel.replace("/", os.sep)), fp)
    ident = ["-c", "user.name=dm-frozen8", "-c", "user.email=dm@frozen8.invalid"]
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    subprocess.run(["git", "-C", root] + ident + ["add", "-A"], check=True)
    subprocess.run(["git", "-C", root] + ident + ["commit", "-q", "-m", "dm"],
                   check=True)


def row_f1(tmp):
    """freeze 写面：只落显式 --out/--tier2 两径；账载漂移 fail-closed 拒出
    名单（rc=1·--out 零字节）。锚 certify/frozen8.py:357,366＋:334。"""
    skel = os.path.join(tmp, "skel")
    f8_skeleton(skel)
    before = tree_manifest(skel)
    rc, out = sh(FROZEN8, ["freeze", "--repo", skel,
                           "--out", os.path.join(tmp, "m.json"),
                           "--tier2", os.path.join(tmp, "t2.md5")])
    assert rc == 0, "freeze 绿径应 0 实测 %d\n%s" % (rc, out[-400:])
    assert tree_manifest(skel) == before, \
        "freeze 越界写仓树＝护栏破（写面仅显式 --out/--tier2）"
    vo = os.path.join(skel, "verify", "verify_vo.py")
    with open(vo, "rb") as fh:
        data = bytearray(fh.read())
    data[len(data) // 2] ^= 0x01
    with open(vo, "wb") as fh:
        fh.write(bytes(data))
    out2 = os.path.join(tmp, "m2.json")
    rc2, o2 = sh(FROZEN8, ["freeze", "--repo", skel, "--out", out2])
    assert rc2 == 1, "账载漂移 freeze 应 rc=1 实测 %d\n%s" % (rc2, o2[-400:])
    assert not os.path.exists(out2), "拒出名单仍落 --out＝护栏破（零写）"
    assert "拒出名单" in o2, o2[-400:]


def row_f2(tmp):
    """timestamp 写面：唯一写面＝显式 --out 回执且绑定复验后才落；--out 缺席
    rc=2 零写；TSA 不可达 rc=9 零写。锚 certify/frozen8.py:806＋:772。"""
    before = tree_manifest(tmp)
    man = os.path.join(REPO, "certify", "frozen8_manifest.json")
    rc, out = sh(FROZEN8, ["timestamp", "--list", man])
    assert rc == 2, "--out 缺席应 rc=2 实测 %d\n%s" % (rc, out[-300:])
    assert "需 --out" in out, out[-300:]
    tsr = os.path.join(tmp, "x.tsr")
    os.environ["ROCWASH_TSA_URL"] = "http://127.0.0.1:1/tsr"  # closed loopback
    try:
        rc9, o9 = sh(FROZEN8, ["timestamp", "--list", man, "--out", tsr])
    finally:
        os.environ.pop("ROCWASH_TSA_URL", None)
    assert rc9 == 9, "TSA 不可达应 rc=9 实测 %d\n%s" % (rc9, o9[-300:])
    assert "可达性自勘失败" in o9, o9[-300:]
    assert not os.path.exists(tsr), "不可达仍落回执＝护栏破（零写）"
    assert tree_manifest(tmp) == before, "timestamp 失败路径越界写盘＝护栏破"


def row_j1(tmp):
    """洗面器自引用护栏：映射源表（--a2-table）永不进洗面目标面——--tree 目标面
    排除它（--plan 零写盘·报告面可查），--file 显式指认则 rc=1 红拒。
    锚 tools/jargon_apply.py:550-560（skip_abs 自引用排除）＋:471-484（--file 红拒）。"""
    d = os.path.join(tmp, "j1")
    os.makedirs(d)
    mapdoc = wf(os.path.join(d, "jargon-to-standard-mapping-v1.md"),
                "| 判词 | conclusion | contract row. |\n")
    wf(os.path.join(d, "victim.md"), "这里有一个判词。\n")
    rep = os.path.join(tmp, "j1-report.json")
    before = tree_manifest(d)
    rc, out = sh(JARGON_APPLY, ["--tree", d, "--plan", "--a2-table", mapdoc,
                                "--json", rep])
    assert rc == 0, "plan 应 rc=0 实测 %d\n%s" % (rc, out[-400:])
    paths = [f["path"] for f in jl(rep)["files"]]
    assert "jargon-to-standard-mapping-v1.md" not in paths, \
        "映射源表不得进洗面目标面（器不洗自己的地图）: %s" % paths
    assert "victim.md" in paths, \
        "同目录普通件应仍在目标面（排除不得过宽）: %s" % paths
    assert tree_manifest(d) == before, "plan 路径越界写盘＝护栏破"
    rc, out = sh(JARGON_APPLY, ["--file", mapdoc, "--plan",
                                "--a2-table", mapdoc])
    assert rc == 1, "显式指认映射源表应红拒 rc=1 实测 %d\n%s" % (rc, out[-400:])
    assert "never washes its own map" in out, out[-300:]
    assert tree_manifest(d) == before, "红拒路径越界写盘＝护栏破"


# ---- ⑩ scheduler_lite 两行（X6 波·谁写谁进阵）--------------------------------

SL_GAP = json.dumps({
    "schema": "rocqwash-exp/1", "id": "fix-001", "ts": "T0",
    "tool": "matrix-fixture", "batch": "b",
    "points": "uncovered face (TODO-SEAT counted, no silent "
              "degradation): ineq.demo @ D:/fix/x.lean",
    "evidence": "status=todo_seat", "fingerprint": "4" * 64}) + "\n"

SL_ROUNDS = (json.dumps({"schema": "rocqwash-round/1", "round_id": 1,
                         "timestamp_utc": "2026-11-15T04:49:24Z",
                         "verify_rc": 0, "mode": "auto"}) + "\n"
             + json.dumps({"schema": "rocqwash-round/1", "round_id": 2,
                           "timestamp_utc": "2026-11-15T16:05:30Z",
                           "verify_rc": 0, "mode": "auto"}) + "\n")

SL_AUTONOMY = json.dumps({"mode": "auto"}) + "\n"
SL_STATE = json.dumps({"schema": "rocqwash.round-state/1",
                       "admitted_classes": [
                           {"class": "jargon", "confidence": 1.0,
                            "basis": "matrix fixture"}]}) + "\n"


def sl_fixture(tmp, tag):
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    ledger = wf(os.path.join(d, "gap.jsonl"), SL_GAP)
    rounds = wf(os.path.join(d, "rounds.jsonl"), SL_ROUNDS)
    marker = wf(os.path.join(d, "ef-done.marker"), "abcdef1234567890\n")
    autonomy = wf(os.path.join(d, "autonomy.json"), SL_AUTONOMY)
    state = wf(os.path.join(d, "state.json"), SL_STATE)
    return ledger, rounds, marker, autonomy, state


def sl_run(argv, now="2026-11-17T00:00:00Z"):
    return sh(SCHEDULER_LITE, list(argv) + ["--now-utc", now])


def row_sl1(tmp):
    """排程 plan 缺省零写盘：全旗标 tmp 罐装（gap/rounds/marker/gear 全绿）
    plan 出 due 判面而 tmp 树 md5 恒同：无 --out 即无任何落盘；dryRun=true
    恒钉（ignition 面只 informational，此面永不点火）。"""
    ledger, rounds, marker, autonomy, state = sl_fixture(tmp, "sl1")
    before = tree_manifest(tmp)
    rc, out = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                      "--ef-marker", marker, "--autonomy", autonomy,
                      "--state", state, "--json"])
    assert rc == 0, "plan 数据态应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    plan = json.loads(out)
    assert plan["schema"] == "rocqwash.scheduler-lite.plan/1", plan["schema"]
    assert plan["verdict"] == "due" and plan["fireReady"] is True, plan
    assert plan["dryRun"] is True, "dryRun 恒真失守＝护栏破: %r" % plan["dryRun"]
    assert plan["ignitePipeline"] and all(s.startswith("py -I")
                                          for s in plan["ignitePipeline"]), \
        "点火管线只 informational"
    assert tree_manifest(tmp) == before, \
        "plan 缺 --out 下 tmp 树字节被动＝护栏破（零写盘失守）"


def row_sl2(tmp):
    """排程唯一写面＝显式 --out：给 --out 恰落一文件（确定性 plan 文档）·
    输入树 md5 恒同·两跑字节恒同（sort_keys 确定性形）。"""
    ledger, rounds, marker, autonomy, state = sl_fixture(tmp, "sl2")
    outp = os.path.join(tmp, "sl2", "plan.json")
    before = tree_manifest(tmp)
    rc, out = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                      "--ef-marker", marker, "--autonomy", autonomy,
                      "--state", state, "--out", outp])
    assert rc == 0, "plan --out 应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    assert os.path.isfile(outp), "--out 未落盘＝写面失守"
    assert tree_manifest(tmp) == before | {
        os.path.relpath(outp, tmp).replace(os.sep, "/"): md5_of(outp)}, \
        "--out 之外出现写面＝护栏破（写面越界）"
    plan = jl(outp)
    assert plan["dryRun"] is True and plan["verdict"] == "due", plan
    first = io.open(outp, "rb").read()
    rc2, _ = sl_run(["plan", "--gap-ledger", ledger, "--rounds", rounds,
                     "--ef-marker", marker, "--autonomy", autonomy,
                     "--state", state, "--out", outp])
    assert rc2 == 0, rc2
    assert io.open(outp, "rb").read() == first, \
        "两跑 plan 字节漂移＝确定性形破（字节失守）"


# ---- ⑪ auto_merge 三行（X6 波·谁写谁进阵）------------------------------------

AM_SHA = "1befa2798beef00112233445566778899aabbccd"


def am_facts(path, pr, branch="supply/seat-pack", family="green", merged=False,
             ahead=1, mergeable=True, state="clean"):
    return wj(path, {
        "schema": "rocqwash-automerge-facts/1", "pr": pr,
        "repo": "rocqwash", "merged": merged, "mergeable": mergeable,
        "mergeable_state": state, "ci": {"family": family},
        "compare": {"ahead": ahead, "behind": 0,
                    "head_in_base": False,
                    "content_landed_in_base": False},
        "head_branch": branch, "note": "matrix fixture"})


def am_run(base, facts, extra):
    return sh(AUTO_MERGE, ["--facts", facts, "--ledger",
                           os.path.join(base, "am-ledger.jsonl")]
              + list(extra))


def row_am1(tmp):
    """缺 --apply 零写盘：merge-ok＋supply/* 白名单内（rail 裁 allowed）而
    合并账不落盘不创建：allowed 判面只走报告面（--json 显式另计）。"""
    d = os.path.join(tmp, "am1")
    os.makedirs(d)
    facts = am_facts(os.path.join(d, "facts.json"), 7)
    rep = os.path.join(d, "rep.json")
    before = tree_manifest(d)
    rc, out = am_run(d, facts, ["--head-branch", "supply/seat-pack",
                                "--json", rep])
    assert rc == 0, "allowed 干跑应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    assert "AUTO-MERGE-VERDICT: merge-ok" in out, out[-300:]
    assert "AUTO-MERGE-RAIL: allowed" in out, out[-300:]
    assert "dry run, row not written" in out, "allowed 干跑应响亮出干跑账"
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "缺 --apply 时合并账落盘＝护栏破（零写盘失守）"
    r = jl(rep)
    assert r["rail"]["ledger_row_written"] is False, r["rail"]
    assert tree_manifest(d) == before | {
        os.path.relpath(rep, d).replace(os.sep, "/"): md5_of(rep)}, \
        "--json 报告面之外出现写盘＝护栏破"


def row_am2(tmp):
    """hold 永不授权＋越权分支红拒：hold-red 判定 --apply 亦零写（rail
    not-eligible 先于合并账）；非 supply/* 头 rc=1 白名单红拒零写。"""
    d = os.path.join(tmp, "am2")
    os.makedirs(d)
    hold = am_facts(os.path.join(d, "hold.json"), 15, family="content",
                    mergeable=False, state="dirty")
    foreign = am_facts(os.path.join(d, "foreign.json"), 16)
    before = tree_manifest(d)
    rc, out = am_run(d, hold, ["--head-branch", "supply/old-head",
                               "--apply"])
    assert rc == 0, "hold 判定是数据应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    assert "AUTO-MERGE-VERDICT: hold-red" in out, out[-300:]
    assert "AUTO-MERGE-RAIL: not-eligible:hold-red" in out, out[-300:]
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "hold 裁定 --apply 落合并账＝护栏破（hold 永不授权失守）"
    rc2, out2 = am_run(d, foreign, ["--head-branch", "feature/quick-fix",
                                    "--apply"])
    assert rc2 == 1, "越权分支应 rc=1 红拒实测 %d\n%s" % (rc2, out2[-400:])
    assert "refused:branch-whitelist" in out2, out2[-300:]
    assert not os.path.exists(os.path.join(d, "am-ledger.jsonl")), \
        "白名单红拒仍落合并账＝护栏破（零写失守）"
    assert tree_manifest(d) == before, "红拒路径越界写盘＝护栏破"


def row_am3(tmp):
    """日预算帽＋重复拒：--daily-cap 3 恰 3 行 authorize 后第 4 拒 rc=1；
    同日同 PR 重复拒 rc=1；合并账恰 3 行不增（帽尽即停无第 4 行）。"""
    d = os.path.join(tmp, "am3")
    os.makedirs(d)
    ledger = os.path.join(d, "am-ledger.jsonl")
    f1 = am_facts(os.path.join(d, "f1.json"), 101, branch="supply/seat-1")
    rc, out = am_run(d, f1, ["--head-branch", "supply/seat-1", "--apply",
                             "--ledger", ledger])
    assert rc == 0, "首发应 allowed exit 0 实测 %d\n%s" % (rc, out[-400:])
    dup = am_facts(os.path.join(d, "dup.json"), 101, branch="supply/seat-1b")
    rc2, out2 = am_run(d, dup, ["--head-branch", "supply/seat-1b", "--apply",
                                "--ledger", ledger])
    assert rc2 == 1, "同日重复应 rc=1 拒实测 %d\n%s" % (rc2, out2[-400:])
    assert "refused:duplicate-authorization" in out2, out2[-300:]
    for i in (2, 3):
        f = am_facts(os.path.join(d, "f%d.json" % i), 100 + i,
                     branch="supply/seat-%d" % i)
        rc, out = am_run(d, f, ["--head-branch", "supply/seat-%d" % i,
                                "--apply", "--ledger", ledger])
        assert rc == 0, "第 %d 发应 allowed exit 0 实测 %d\n%s" \
            % (i, rc, out[-300:])
    rows = [json.loads(ln) for ln in io.open(ledger, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and all(r["kind"] == "authorize"
                                  and r["decision"] == "allowed"
                                  for r in rows), rows
    f4 = am_facts(os.path.join(d, "f4.json"), 104, branch="supply/seat-4")
    rc, out = am_run(d, f4, ["--head-branch", "supply/seat-4", "--apply",
                             "--ledger", ledger])
    assert rc == 1, "帽尽第 4 发应 rc=1 拒实测 %d\n%s" % (rc, out[-400:])
    assert "refused:daily-budget" in out, out[-300:]
    rows2 = [json.loads(ln) for ln in io.open(ledger, encoding="utf-8")
             if ln.strip()]
    assert len(rows2) == 3, "帽尽/重复后合并账不增（恰 3 行）实测 %d" % len(rows2)


# ---- ⑫ repair_scope 共享名册一行＋E 波四守卫类四行（X6 波·谁写谁进阵）--------

LANE_SUITE = (
    '#!/bin/bash\n'
    '# matrix fixture suite (tmp only)\n'
    'CASES="\\\n'
    't_real_one \\\n'
    't_ghost_lane"\n'
    'NCASES=$(echo $CASES | wc -w | tr -d \' \')\n'
    '\n'
    't_real_one() {\n'
    '  "$PY" -B "$REPO/tests/t_real_one.py"\n'
    '}\n'
    '\n'
    't_ghost_lane() {\n'
    '  "$PY" -B "$REPO/tests/t_ghost_lane.py"\n'
    '}\n')


def row_rs1(tmp):
    """repair_scope --check 查询面零写盘＋排除判词咬合：快照退化场（沙箱无
    frozen8.py·fallback loud）下，append-only 账面/frozen 行/family 目录/
    legal-data 面/zh 档案全 EXCLUDED，class-2 三可修面 REPAIRABLE；查询
    零写盘。"""
    d = os.path.join(tmp, "rs1")
    os.makedirs(d)
    before = tree_manifest(d)
    rc, out = sh(REPAIR_SCOPE,
                 ["--repo", d, "--check", "更新账.md", "wash/wash_engine.py",
                  "certify/x.py", "README-cw.zh.md", "docs/mcp.md",
                  "tests/README.md", "README.md", "docs/repair-ledger.jsonl"])
    assert rc == 1, "有排除面查询应 exit 1（判词是数据）实测 %d\n%s" \
        % (rc, out[-400:])
    excluded = {ln.split()[1] for ln in out.splitlines()
                if ln.startswith("EXCLUDED ")}
    repairable = {ln.split()[1] for ln in out.splitlines()
                  if ln.startswith("REPAIRABLE ")}
    assert excluded == {"更新账.md", "wash/wash_engine.py", "certify/x.py",
                        "README-cw.zh.md", "docs/mcp.md"}, excluded
    assert repairable == {"tests/README.md", "README.md",
                          "docs/repair-ledger.jsonl"}, repairable
    assert tree_manifest(d) == before, "查询路径越界写盘＝护栏破"


def lane_repo(tmp, tag):
    """lane-extract 夹具仓：套件（CASES 两车道）＋真件在位（$REPO/tests/
    引用形）·幽灵件缺席（tests/t_ghost_lane.py 不落盘＝R1 ENOENT 形）。
    → (repo, suite_path)。"""
    d = os.path.join(tmp, tag)
    os.makedirs(os.path.join(d, "tests"))
    sp = wf(os.path.join(d, "run_tests.sh"), LANE_SUITE)
    wf(os.path.join(d, "tests", "t_real_one.py"), "# fixture lane file\n")
    return d, sp


def row_e2a(tmp):
    """E2-1 lane-extract（--lane-detect/--lane-apply）：干跑零写零账；排除
    账面（seeds/ 族）rc=2 红拒且零创建；预算帽（2 前科）rc=2 拒写·
    套件字节恒同·只落 escalated(budget-cap) 账行。"""
    d, sp = lane_repo(tmp, "e2a")
    before = md5_of(sp)
    rc, out = sh(REPAIR_SCOPE, ["--repo", d, "--suite", "run_tests.sh",
                                "--lane-detect", "--json-out",
                                os.path.join(tmp, "e2a-rep.json")])
    assert rc == 0, "干跑侦应 exit 0 实测 %d\n%s" % (rc, out[-400:])
    rep = jl(os.path.join(tmp, "e2a-rep.json"))
    assert [g["lane"] for g in rep["ghosts"]] == ["t_ghost_lane"], rep["ghosts"]
    assert rep["applied"] is False, rep
    assert md5_of(sp) == before, "干落下套件字节被动＝护栏破"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "干跑建账＝护栏破"
    rc2, out2 = sh(REPAIR_SCOPE, ["--repo", d, "--suite", "run_tests.sh",
                                  "--lane-detect", "--lane-apply",
                                  "--ledger", "seeds/ledger.jsonl"])
    assert rc2 == 2, "排除账面应 rc=2 红拒实测 %d\n%s" % (rc2, out2[-400:])
    assert "REFUSED" in out2 and "excluded ledger face" in out2, out2[-300:]
    assert not os.path.isfile(os.path.join(d, "seeds", "ledger.jsonl")), \
        "排除面红拒仍建账＝护栏破（零写失守）"
    d4 = os.path.join(tmp, "e2a-budget")
    os.makedirs(os.path.join(d4, "tests"))
    sp4 = wf(os.path.join(d4, "run_tests.sh"), LANE_SUITE)
    wf(os.path.join(d4, "tests", "t_real_one.py"), "# fixture lane file\n")
    led = os.path.join(tmp, "e2a-ledger.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "class": "lane-extract",
             "target": "run_tests.sh",
             "outcome": "repaired(lane-unregister)", "utc": "T0"}
    with io.open(led, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_4 = md5_of(sp4)
    rc3, out3 = sh(REPAIR_SCOPE, ["--repo", d4, "--suite", "run_tests.sh",
                                  "--lane-detect", "--lane-apply",
                                  "--ledger", led])
    assert rc3 == 2, "预算帽应 rc=2 拒写实测 %d\n%s" % (rc3, out3[-400:])
    assert "budget exhausted" in out3, out3[-300:]
    assert md5_of(sp4) == md5_4, "帽尽落刀＝护栏破（套件字节恒同失守）"
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and rows[-1]["outcome"] == "escalated(budget-cap)", \
        "帽面只落升格账行: %r" % rows[-1]


def row_e2b(tmp):
    """E2-2 roster-resync（tools/roster_resync.py）：干跑零写零账；--apply
    单向派生（roster 字节恒同·计数面修至名册值·一修复一账行）；预算帽
    rc=1 拒写·面字节恒同·只落 escalated 行。"""
    MINI = ('#!/bin/bash\nCASES="\\\nt_a \\\nt_b"\n'
            'for c in $CASES; do :; done\n')
    d = os.path.join(tmp, "e2b")
    os.makedirs(os.path.join(d, "tests"))
    rt = wf(os.path.join(d, "tests", "run_tests.sh"), MINI)
    cov = wf(os.path.join(d, "tests", "README.md"),
             "# mini\n\n预期 2 过\n\n## 覆盖面（3 例）\n")
    wf(os.path.join(d, "README.md"),
       "# mini\ntests/  # 自测套件（2 例） - test suite (2 cases)\n")
    md5_rt = md5_of(rt)
    before_cov = md5_of(cov)
    rc, out = sh(ROSTER_RESYNC, ["--repo", d])
    assert rc == 1, "漂移干跑应 exit 1（漂移是数据）实测 %d\n%s" \
        % (rc, out[-400:])
    assert "drift=1" in out, out[-300:]
    assert md5_of(cov) == before_cov, "干跑写计数面＝护栏破"
    assert md5_of(rt) == md5_rt, "干跑写名册＝护栏破（roster 单向失守）"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "干跑建账＝护栏破"
    rc2, out2 = sh(ROSTER_RESYNC, ["--repo", d, "--apply"])
    assert rc2 == 0, "apply 应修复至净实测 %d\n%s" % (rc2, out2[-400:])
    assert "applied=1" in out2 and "escalated=0" in out2, out2[-300:]
    assert md5_of(rt) == md5_rt, "apply 越界写名册＝护栏破（单向失守）"
    assert "覆盖面（2 例）" in io.open(cov, encoding="utf-8").read(), \
        "计数面未修至名册值"
    led = os.path.join(d, "docs", "repair-ledger.jsonl")
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 1 and rows[0]["class"] == "roster-resync" \
        and rows[0]["outcome"] == "repaired(count-resync)", rows
    d4 = os.path.join(tmp, "e2b-budget")
    os.makedirs(os.path.join(d4, "tests"))
    rt4 = wf(os.path.join(d4, "tests", "run_tests.sh"), MINI)
    cov4 = wf(os.path.join(d4, "tests", "README.md"),
              "# mini\n\n预期 2 过\n\n## 覆盖面（9 例）\n")
    wf(os.path.join(d4, "README.md"),
       "# mini\ntests/  # 自测套件（2 例） - test suite (2 cases)\n")
    led4 = os.path.join(tmp, "e2b-ledger4.jsonl")
    prior = {"schema": "rocqwash-repair/1", "class": "roster-resync",
             "target": "tests/README.md:1", "branch": "unknown",
             "outcome": "repaired(count-resync)", "ts": "T0"}
    with io.open(led4, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_cov4 = md5_of(cov4)
    rc3, out3 = sh(ROSTER_RESYNC, ["--repo", d4, "--apply",
                                   "--ledger", led4])
    assert rc3 == 1, "预算帽应 rc=1 拒写实测 %d\n%s" % (rc3, out3[-400:])
    assert "escalated(budget-cap)" in out3, out3[-300:]
    assert md5_of(cov4) == md5_cov4, "帽尽落刀＝护栏破（面字节恒同失守）"
    rows4 = [json.loads(ln) for ln in io.open(led4, encoding="utf-8")
             if ln.strip()]
    assert len(rows4) == 3 and rows4[-1]["outcome"] == "escalated(budget-cap)", \
        "帽面只落升格账行: %r" % rows4[-1]


def flaky_repo(tmp, tag):
    """flaky-quarantine 夹具仓：套件（CASES 一车道·ONLY 探针单独跑绿）
    ＋空名册。→ (repo, suite_path, roster_path)。"""
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    suite = ('#!/bin/bash\n'
             'CASES="\\\n'
             't_a"\n'
             'if [ -n "${ROCWASH_TESTS_ONLY:-}" ]; then exit 0; fi\n'
             'exit 1\n')
    sp = wf(os.path.join(d, "run_tests.sh"), suite)
    roster = wf(os.path.join(d, "advisory_roster.txt"), "# empty\n")
    return d, sp, roster


def row_e2c(tmp):
    """E2-3 flaky-quarantine（tools/flaky_guard.py --move）：冻结靶（seeds/
    族名册）rc=1 红拒零写零账（scope 闸先于探针）；预算帽 rc=1 拒写·名册
    字节恒同·只落 escalated 账行。"""
    d, sp, roster = flaky_repo(tmp, "e2c")
    before = tree_manifest(d)
    rc, out = sh(FLAKY_GUARD, ["--repo", d, "--suite",
                               os.path.join(d, "run_tests.sh"),
                               "--roster", os.path.join(d, "seeds", "adv.txt"),
                               "--ledger", os.path.join(d, "led.jsonl"),
                               "--move", "t_a", "--apply"])
    assert rc == 1, "冻结靶应 rc=1 红拒实测 %d\n%s" % (rc, out[-400:])
    assert "REFUSED" in out and "outside the repair scope" in out, out[-300:]
    assert tree_manifest(d) == before, \
        "冻结靶红拒越界写盘＝护栏破（零写零账失守）"
    d2, _sp2, roster2 = flaky_repo(tmp, "e2c-budget")
    led = os.path.join(d2, "led.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "kind": "repair",
             "class": "flaky-quarantine", "ticket": "E2-3", "target": "t_x",
             "outcome": "repaired", "branch": "nogit", "head_sha": "nogit",
             "roster": "advisory_roster.txt", "ts_utc": "T0"}
    with io.open(led, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_r2 = md5_of(roster2)
    rc2, out2 = sh(FLAKY_GUARD, ["--repo", d2, "--suite",
                                 os.path.join(d2, "run_tests.sh"),
                                 "--roster", roster2, "--ledger", led,
                                 "--move", "t_a", "--apply"])
    assert rc2 == 1, "预算帽应 rc=1 拒写实测 %d\n%s" % (rc2, out2[-400:])
    assert "budget exhausted" in out2, out2[-300:]
    assert md5_of(roster2) == md5_r2, "帽尽落刀＝护栏破（名册字节恒同失守）"
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 3 and rows[-1]["outcome"] == "escalated", \
        "帽面只落升格账行: %r" % rows[-1]


def row_e2d(tmp):
    """E2-4 doc-count（--doc-count-detect/--doc-count-apply）：干跑零写零
    账；--apply 修至 face=source 且幂等（二遍零字节）；预算帽 rc=2 拒写·
    目标面字节恒同·只落 escalated(budget-cap) 行。"""
    CW = ("#!/usr/bin/env bash\nset -u\nusage() {\ncat <<'EOF'\n"
          "alpha   tools/alpha.py\nbeta    tools/beta.py\nEOF\n}\n"
          "hint_for() {\n  case \"$1\" in\n"
          "    alpha) echo a ;;\n    beta) echo b ;;\n  esac\n}\n"
          "case \"${1:-}\" in\n"
          "  alpha) shift; run_tool alpha \"tools/alpha.py\" \"$@\" ;;\n"
          "  beta) shift; run_tool beta \"tools/beta.py\" \"$@\" ;;\n"
          "  *) usage; exit 2 ;;\nesac\n")
    MINI_RT = '#!/usr/bin/env bash\nCASES="\\\nt_one \\\nt_two \\\n"\n'
    TOOL = '#!/usr/bin/env python3\n"""mini tool fixture."""\n'

    def mk_repo(tag, routes, tools_n):
        d = os.path.join(tmp, tag)
        os.makedirs(os.path.join(d, "tools"))
        os.makedirs(os.path.join(d, "tests"))
        wf(os.path.join(d, "cw.sh"), CW)
        wf(os.path.join(d, "tests", "run_tests.sh"), MINI_RT)
        wf(os.path.join(d, "tools", "alpha.py"), TOOL)
        wf(os.path.join(d, "tools", "beta.py"), TOOL)
        wf(os.path.join(d, "README-cw.md"),
           "# cw.sh - unified entry quick reference (rocqos (rocqwash) tool"
           " suite | %d routes over %d tools)\n" % (routes, tools_n))
        return d

    d = mk_repo("e2d", 3, 4)
    readme = os.path.join(d, "README-cw.md")
    before = md5_of(readme)
    rc, out = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-detect"])
    assert rc == 1, "漂移侦应 exit 1（漂移是数据）实测 %d\n%s" \
        % (rc, out[-400:])
    assert "drift" in out and "doc={'routes': 3, 'tools': 4}" in out, \
        out[-400:]
    assert md5_of(readme) == before, "干跑写目标面＝护栏破"
    assert not os.path.isfile(os.path.join(d, "docs", "repair-ledger.jsonl")), \
        "干跑建账＝护栏破"
    rc2, out2 = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-apply"])
    assert rc2 == 0, "apply 应修复至净实测 %d\n%s" % (rc2, out2[-400:])
    assert "outcome=repaired" in out2, out2[-300:]
    assert io.open(readme, encoding="utf-8").read() == \
        ("# cw.sh - unified entry quick reference (rocqos (rocqwash) tool"
         " suite | 2 routes over 2 tools)\n"), \
        "face 未修至 source 值"
    md5_mid = md5_of(readme)
    led = os.path.join(d, "docs", "repair-ledger.jsonl")
    rows = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
            if ln.strip()]
    assert len(rows) == 1 and rows[0]["class"] == "doc-count" \
        and rows[0]["outcome"] == "repaired(doc-count-sync)", rows
    rc3, _ = sh(REPAIR_SCOPE, ["--repo", d, "--doc-count-apply"])
    assert rc3 == 0 and md5_of(readme) == md5_mid, \
        "二遍非幂等＝护栏破（零字节失守）"
    rows3 = [json.loads(ln) for ln in io.open(led, encoding="utf-8")
             if ln.strip()]
    assert len(rows3) == 1, "幂等遍不得加账行实测 %d" % len(rows3)
    d4 = mk_repo("e2d-budget", 9, 9)
    readme4 = os.path.join(d4, "README-cw.md")
    led4 = os.path.join(tmp, "e2d-ledger4.jsonl")
    prior = {"schema": "rocqwash-repair-ledger/1", "class": "doc-count",
             "target": "README-cw.md", "outcome": "repaired(doc-count-sync)",
             "utc": "T0"}
    with io.open(led4, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
        fh.write(json.dumps(prior, sort_keys=True) + "\n")
    md5_r4 = md5_of(readme4)
    rc4, out4 = sh(REPAIR_SCOPE, ["--repo", d4, "--doc-count-apply",
                                  "--ledger", led4])
    assert rc4 == 2, "预算帽应 rc=2 拒写实测 %d\n%s" % (rc4, out4[-400:])
    assert "budget exhausted" in out4, out4[-300:]
    assert md5_of(readme4) == md5_r4, "帽尽落刀＝护栏破（目标面恒同失守）"
    rows4 = [json.loads(ln) for ln in io.open(led4, encoding="utf-8")
             if ln.strip()]
    assert len(rows4) == 3 and rows4[-1]["outcome"] == "escalated(budget-cap)", \
        "帽面只落升格账行: %r" % rows4[-1]


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
     "wash/cure_applier.py:1272,1338", row_c1),
    ("C2", "cure_applier", "--apply 才落刀＋幂等断言败拒写（rc=1 零字节动）",
     "wash/cure_applier.py:1282-1285", row_c2),
    ("C3", "cure_applier", "write-face byte contract: on-disk md5 == report md5_after, no CRLF, second pass byte-stable",
     "wash/cure_applier.py:1338-1341", row_c3),
    ("C4", "cure_applier", "compile-leg write face: temp-only copies, honest skip record, missing-binary rc=9 refuses the write, no-change pass compiles nothing",
     "wash/cure_applier.py:660,1286-1336,1300-1306", row_c4),
    ("F1", "frozen8", "freeze 只落显式 --out/--tier2（账载漂移拒出名单 rc=1 零写）",
     "certify/frozen8.py:357,366,334", row_f1),
    ("F2", "frozen8", "timestamp 唯一写面=显式 --out 回执绑定复验后落（缺参 rc=2/不可达 rc=9 皆零写）",
     "certify/frozen8.py:806,772", row_f2),
    ("G1", "axiom_guard", "compile-leg write face temp-only: rc 111 honest skip with zero judgment and no --out / missing binaries rc=9 ahead of every work face",
     "tools/axiom_guard.py:main env gate, guard mkdtemp", row_g1),
    ("J1", "jargon_apply", "洗面器自引用护栏：映射源表永不入目标面（--tree 排除·--file rc=1 红拒）",
     "tools/jargon_apply.py:550-560,471-484", row_j1),
    ("SL1", "scheduler_lite", "plan 缺省零写盘（全旗标罐装出 due 判面·树恒同·dryRun 恒真）",
     "tools/scheduler_lite.py:364-366,309", row_sl1),
    ("SL2", "scheduler_lite", "唯一写面=显式 --out（恰落一文件·输入树恒同·两跑字节恒同）",
     "tools/scheduler_lite.py:364-366,328-331", row_sl2),
    ("AM1", "auto_merge", "缺 --apply 零写盘（rail allowed 而合并账不创建）",
     "tools/auto_merge.py:244-247", row_am1),
    ("AM2", "auto_merge", "hold 永不授权（--apply 亦零写）＋越权分支 rc=1 白名单红拒零写",
     "tools/auto_merge.py:220-221,225-228", row_am2),
    ("AM3", "auto_merge", "日预算帽＋重复拒（恰 3 行 authorize 后第 4/同 PR 拒·合并账不增）",
     "tools/auto_merge.py:229-233,234-239", row_am3),
    ("RS1", "repair_scope", "--check 查询面零写盘（共享名册判词咬合·快照退化 loud）",
     "tools/repair_scope.py:140-160,556-576,590-620", row_rs1),
    ("E2A", "repair_scope", "class-1 lane-extract：缺省零写零账／排除账面 rc=2 零创建／预算帽拒写只落升格行",
     "tools/repair_scope.py:477-482,400-411,487-493", row_e2a),
    ("E2B", "roster_resync", "class-2 roster-resync：缺省零写零账／roster 单向＋一修复一行／预算帽拒写只落升格行",
     "tools/roster_resync.py:246-248,256-265,327-334", row_e2b),
    ("E2C", "flaky_guard", "class-3 flaky-quarantine：冻结靶 rc=1 零写零账（scope 闸先于探针）／预算帽拒写只落升格行",
     "tools/flaky_guard.py:390-396,514-523", row_e2c),
    ("E2D", "repair_scope", "class-4 doc-count：干跑零写零账／apply 修至 face=source 幂等二遍零字节／预算帽 rc=2 拒写",
     "tools/repair_scope.py:917-926,975-994,997-1009", row_e2d),
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
    print("DESTRUCTIVE-MATRIX PASS: 33 行拒写判据全过（unclog×4/wash_shape×4/"
          "pushci×3/cw_sentinel×2/registry_union×2/cure_applier×4/frozen8×2/"
          "axiom_guard×1/jargon_apply×1/scheduler_lite×2/auto_merge×3/"
          "repair_scope×1+E波四守卫×4·全 tmp fixture＋injector 罐装零真网络"
          "零真仓零真编译）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
