#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registry_union.py — tools/registry_union.py 自测（tests/·20261110 实战
手术工具化轮·20261111）

注册册 union 手术器九节判：
  1 工具自证    --selftest 八判全过（rc 0）
  2 coq 夹具组  coq_base/main/branch 三件套 union：main 6＋unique 2＝union 8·
                `-Q . ""` 旗标行保全·路径键（Deep/BrNew2.v→BrNew）去扩展名
  3 陷阱夹具组  order_trap 三件套：#40 世系同名不同形（C40 基线形 vs main 重锚
                形）对 merge-base 判非独有必过滤——union 6＝main 4＋BrNew×2，
                C40 行不重插（若误对 main 提取即 A2 炸，正道零炸）
  4 重锚冻结向  anchor_src/C40.v 实件 md5 前 8＝1414cddb 冻结·保序号重写
                #R40-deadbeef→#R40-1414cddb·缺件（MainAdd）与不在全表（Ghost）
                如实列跳过·exit 0
  5 A2 负判     双方各增同名（键不在 base 在 main）→exit 2 列键·零写盘
  6 A3 负判     新增行锚文本与 main 行相撞（键异锚同）→exit 2 列文本·零写盘
  7 dry run/apply  干跑零写盘→--apply 落盘→幂等重跑字节恒同＋--json schema
                rocqwash-registry-union/1＋确定性重跑恒同
  8 CLI/用法面  help0／未知形参2／无输入2／缺件9／--apply 无 --out 2／
                --reanchor 无 --anchor-src 2／--git 与三文件混给 2／
                --reanchor×coqproject 2
  9 git 直读    tmp 仓三 ref subprocess git show（缺 git 让席 SKIP 不充红）

零触律：夹具只读，全部输出落 mktemp 临时目录即写即清；零真编译零网络零触真仓。
幂等：python3 -B 禁 __pycache__。退出码：0=九节全过；1=任一红。
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "registry_union.py")
FIX = os.path.join(REPO, "tests", "fixtures", "registry_union")

_spec = importlib.util.spec_from_file_location("registry_union_mod", TOOL)
ru = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ru)


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(path, text):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def rd(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def three(base, main, branch, kind, extra=None):
    """夹具三件套＋kind 的 CLI 实参（--out/--apply 由调用方加）。"""
    return ["--base", os.path.join(FIX, base),
            "--main", os.path.join(FIX, main),
            "--branch", os.path.join(FIX, branch), "--kind", kind] \
        + (extra or [])


def sec1_selftest():
    rc, out = run(["--selftest"])
    assert rc == 0, "selftest 应 rc=0 实测 %d\n%s" % (rc, out)
    assert "REGISTRY-UNION-SELFTEST PASS" in out, out
    assert "八判全过" in out, out
    return "selftest 八判绿"


def sec2_coq_fixture(tmp):
    out = os.path.join(tmp, "coq_union.txt")
    rc, sout = run(three("coq_base.txt", "coq_main.txt", "coq_branch.txt",
                         "coqproject", ["--out", out, "--apply"]))
    assert rc == 0, sout
    got = rd(out).decode("utf-8").splitlines()
    assert len(got) == 8, got  # main 6 + unique 2 = union 8
    assert got[:6] == rd(os.path.join(FIX, "coq_main.txt")) \
        .decode("utf-8").splitlines(), "main 底序错"
    assert got[6:] == ["BrNew1.v", "Deep/BrNew2.v"], got
    assert got[0] == '-Q . ""', "旗标行保全违例"
    rc2, sout2 = run(three("coq_base.txt", "coq_main.txt", "coq_branch.txt",
                           "coqproject", ["--json", os.path.join(tmp, "c.json"),
                                          "--out", out, "--apply"]))
    assert rc2 == 0, sout2
    rep = json.load(io.open(os.path.join(tmp, "c.json"), encoding="utf-8"))
    assert rep["schema"] == ru.SCHEMA, rep["schema"]
    assert rep["kind"] == "coqproject", rep
    assert [a["key"] for a in rep["added"]] == ["BrNew1", "BrNew2"], \
        "路径键应末 / 后去 .v：%s" % rep["added"]
    assert rep["assertions"]["added_keys_not_in_main"] is True, rep
    return "coq 三件套 union 6+2=8＋路径键形＋json 咬合"


def sec3_trap_fixture(tmp):
    out = os.path.join(tmp, "trap_union.txt")
    rc, sout = run(three("order_trap_base.txt", "order_trap_main.txt",
                         "order_trap_branch.txt", "order",
                         ["--out", out, "--apply"]))
    assert rc == 0, sout
    got = rd(out).decode("utf-8").splitlines()
    assert len(got) == 6, got  # main 4 + BrNew×2
    # 坑判例机械实证：C40 行（branch 携基线形·main 已重锚异形）必过滤不重插
    assert got.count("C40.v#R40-deadbeef") == 1, got
    assert "C40.v#R40-3333cccc" not in got, \
        "对 base 提取失效：基线形 C40 被误判独有重插＝坑判例复发"
    assert got[4:] == ["BrNew1.v#R41-5555eeee", "BrNew2.v#R41-6666ffff"], got
    # 干跑面 stats 咬合
    rc2, sout2 = run(three("order_trap_base.txt", "order_trap_main.txt",
                           "order_trap_branch.txt", "order"))
    assert rc2 == 0 and "main=4 + unique=2 = union=6" in sout2, sout2
    return "陷阱组：同名不同形对 base 必过滤（union 6）＋stats 咬合"


def sec4_reanchor_frozen(tmp):
    out = os.path.join(tmp, "ra_union.txt")
    rc, sout = run(three("order_trap_base.txt", "order_trap_main.txt",
                         "order_trap_branch.txt", "order",
                         ["--reanchor", "C40,MainAdd,Ghost",
                          "--anchor-src", os.path.join(FIX, "anchor_src"),
                          "--out", out, "--apply"]))
    assert rc == 0, "缺件/不在全表属披露非红：%s" % sout
    # 冻结向量：anchor_src/C40.v 内容 md5 前 8＝1414cddb（保序号 R40）
    assert rd(out).decode("utf-8").splitlines()[2] == "C40.v#R40-1414cddb", \
        rd(out).decode("utf-8").splitlines()
    assert "C40.v#R40-1414cddb" in sout and "1414cddb" in sout, sout
    assert "MainAdd" in sout and "缺件" in sout, sout
    assert "Ghost" in sout and "不在全表" in sout, sout
    # 已是正典形即 skip（幂等律）：main 喂正典锚行 → 零 rewrite 输出恒同
    bdir = os.path.join(tmp, "ra_canon")
    os.makedirs(bdir)
    shutil.copy(os.path.join(FIX, "order_trap_base.txt"),
                os.path.join(bdir, "base.txt"))
    shutil.copy(os.path.join(FIX, "order_trap_branch.txt"),
                os.path.join(bdir, "branch.txt"))
    main_lines = io.open(os.path.join(FIX, "order_trap_main.txt"),
                         encoding="utf-8").read()
    wf(os.path.join(bdir, "main.txt"),
       main_lines.replace("#R40-deadbeef", "#R40-1414cddb"))
    rc2, sout2 = run(["--base", os.path.join(bdir, "base.txt"),
                      "--main", os.path.join(bdir, "main.txt"),
                      "--branch", os.path.join(bdir, "branch.txt"),
                      "--kind", "order", "--reanchor", "C40",
                      "--anchor-src", os.path.join(FIX, "anchor_src"),
                      "--out", os.path.join(bdir, "union.txt"), "--apply"])
    assert rc2 == 0, sout2
    assert "rewrite" not in sout2, "正典形应零 rewrite：%s" % sout2
    return "重锚冻结向量 1414cddb＋缺件/不在全表披露＋正典形零 rewrite"


def sec5_a2_blast(tmp):
    # 负判夹具临时变形（改 branch 复制件·零触原夹具）：双方各增同名 K40
    bdir = os.path.join(tmp, "a2")
    os.makedirs(bdir)
    shutil.copy(os.path.join(FIX, "order_trap_base.txt"),
                os.path.join(bdir, "base.txt"))
    shutil.copy(os.path.join(FIX, "order_trap_main.txt"),
                os.path.join(bdir, "main.txt"))
    shutil.copy(os.path.join(FIX, "order_trap_branch.txt"),
                os.path.join(bdir, "branch.txt"))
    with io.open(os.path.join(bdir, "branch.txt"), "a", encoding="utf-8") as fh:
        fh.write("BothAdd.v#R42-9999eeee\n")  # 不在 base·在 main→A2
    with io.open(os.path.join(bdir, "main.txt"), "a", encoding="utf-8") as fh:
        fh.write("BothAdd.v#R42-8888eeee\n")
    out = os.path.join(bdir, "union.txt")
    rc, sout = run(["--base", os.path.join(bdir, "base.txt"),
                    "--main", os.path.join(bdir, "main.txt"),
                    "--branch", os.path.join(bdir, "branch.txt"),
                    "--kind", "order", "--out", out, "--apply"])
    assert rc == 2, "A2 应炸 exit 2 实测 %d\n%s" % (rc, sout)
    assert "A2" in sout and "BothAdd.v" in sout, sout
    assert not os.path.exists(out), "断言炸零写盘违例"
    return "A2 双方各增同名 exit 2 列键零写盘"


def sec6_a3_blast(tmp):
    bdir = os.path.join(tmp, "a3")
    os.makedirs(bdir)
    shutil.copy(os.path.join(FIX, "order_trap_base.txt"),
                os.path.join(bdir, "base.txt"))
    shutil.copy(os.path.join(FIX, "order_trap_main.txt"),
                os.path.join(bdir, "main.txt"))
    shutil.copy(os.path.join(FIX, "order_trap_branch.txt"),
                os.path.join(bdir, "branch.txt"))
    # 新增行键独有但锚文本与 main 行相撞（他批原样携锚病）
    with io.open(os.path.join(bdir, "branch.txt"), "a", encoding="utf-8") as fh:
        fh.write("Xn.v#R40-4444dddd\n")  # 与 main MainAdd 锚文本同
    out = os.path.join(bdir, "union.txt")
    rc, sout = run(["--base", os.path.join(bdir, "base.txt"),
                    "--main", os.path.join(bdir, "main.txt"),
                    "--branch", os.path.join(bdir, "branch.txt"),
                    "--kind", "order", "--out", out, "--apply"])
    assert rc == 2, "A3 应炸 exit 2 实测 %d\n%s" % (rc, sout)
    assert "A3" in sout and "4444dddd" in sout, sout
    assert not os.path.exists(out), "断言炸零写盘违例"
    return "A3 锚文本新增重复 exit 2 列文本零写盘"


def sec7_dryrun_apply_json(tmp):
    out = os.path.join(tmp, "dry_union.txt")
    js = os.path.join(tmp, "dry.json")
    rc, sout = run(three("order_trap_base.txt", "order_trap_main.txt",
                         "order_trap_branch.txt", "order",
                         ["--out", out, "--json", js]))
    assert rc == 0, sout
    assert not os.path.exists(out), "干跑写盘＝违例"
    assert "干跑未写盘" in sout, sout
    rep = json.loads(rd(js).decode("utf-8"))
    assert rep["schema"] == ru.SCHEMA and rep["mode"] == "DRY-RUN", rep
    # apply 落盘＋确定性：同输入重跑 json/union 稿字节恒同（同为 APPLY 态对比）
    rc2, sout2 = run(three("order_trap_base.txt", "order_trap_main.txt",
                           "order_trap_branch.txt", "order",
                           ["--out", out, "--json", js, "--apply"]))
    assert rc2 == 0 and os.path.exists(out), sout2
    first_j = rd(js)
    first_out = rd(out)
    assert json.loads(first_j.decode("utf-8"))["mode"] == "APPLY", first_j
    rc3, _ = run(three("order_trap_base.txt", "order_trap_main.txt",
                       "order_trap_branch.txt", "order",
                       ["--out", out, "--json", js, "--apply"]))
    assert rc3 == 0 and rd(js) == first_j, "json 字节漂移＝违例"
    run(three("order_trap_base.txt", "order_trap_main.txt",
              "order_trap_branch.txt", "order", ["--out", out, "--apply"]))
    assert rd(out) == first_out, "union 稿重跑字节漂移＝违例"
    return "干跑零写盘→apply 落盘→幂等字节恒同＋json 确定性"


def sec8_cli_usage():
    rc, out = run(["--help"])
    assert rc == 0 and "usage" in out, out[-200:]
    rc, _ = run(["--bogus"])
    assert rc == 2, "未知形参应 2 实测 %d" % rc
    rc, _ = run([])
    assert rc == 2, "无输入应 2 实测 %d" % rc
    rc, out = run(["--base", os.path.join(FIX, "nope.txt"),
                   "--main", os.path.join(FIX, "coq_main.txt"),
                   "--branch", os.path.join(FIX, "coq_branch.txt"),
                   "--kind", "coqproject"])
    assert rc == 9 and "nope.txt" in out, "缺件应 9：%s" % out
    # 用法对偶面：--apply 无 --out／--reanchor 无 --anchor-src／混给／reanchor×coq
    base3 = three("order_trap_base.txt", "order_trap_main.txt",
                  "order_trap_branch.txt", "order")
    rc, _ = run(base3 + ["--apply"])
    assert rc == 2, "--apply 无 --out 应 2"
    rc, _ = run(base3 + ["--reanchor", "C40"])
    assert rc == 2, "--reanchor 无 --anchor-src 应 2"
    rc, _ = run(base3 + ["--git", "bogus-repo", "--ref-base", "a",
                         "--ref-main", "b", "--ref-branch", "c"])
    assert rc == 2, "--git 与三文件混给应 2"
    rc, _ = run(three("coq_base.txt", "coq_main.txt", "coq_branch.txt",
                      "coqproject",
                      ["--reanchor", "ToyA",
                       "--anchor-src", os.path.join(FIX, "anchor_src")]))
    assert rc == 2, "--reanchor×coqproject 应 2"
    return "CLI 四码＋用法对偶四面全 2"


def sec9_git_direct(tmp):
    if shutil.which("git") is None:
        print("  （git 不在卷·SKIP 让席不充红）")
        return "git 直读 SKIP（git 缺卷）"
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    env = dict(os.environ)
    env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
                "GIT_AUTHOR_DATE": "2026-11-11T00:00:00 +0000",
                "GIT_COMMITTER_DATE": "2026-11-11T00:00:00 +0000"})

    def g(*a):
        p = subprocess.run(["git", "-C", repo] + list(a), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert p.returncode == 0, p.stdout
        return p.stdout.decode("utf-8", errors="replace").strip()

    def commit(text, msg):
        wf(os.path.join(repo, "order.txt"), text)
        g("add", "order.txt")
        g("commit", "-m", msg)

    g("init")
    main_ref = g("symbolic-ref", "--short", "HEAD")
    commit("A_Mod.v#R0-1111aaaa\n", "base")
    g("branch", "mb")
    commit("A_Mod.v#R0-1111aaaa\nMainAdd.v#R40-4444dddd\n", "main")
    g("checkout", "-b", "br")
    commit("A_Mod.v#R0-1111aaaa\nBrG.v#R41-7777eeee\n", "branch")
    out = os.path.join(tmp, "git_union.txt")
    rc, sout = run(["--git", repo, "--ref-base", "mb", "--ref-main", main_ref,
                    "--ref-branch", "br", "--kind", "order",
                    "--out", out, "--apply"])
    assert rc == 0, sout
    got = rd(out).decode("utf-8").splitlines()
    assert got == ["A_Mod.v#R0-1111aaaa", "MainAdd.v#R40-4444dddd",
                   "BrG.v#R41-7777eeee"], got
    rc, _ = run(["--git", repo, "--ref-base", "no-ref", "--ref-main",
                 main_ref, "--ref-branch", "br", "--kind", "order"])
    assert rc == 9, "坏 ref 应 9 实测 %d" % rc
    return "git 三 ref 直读 union 2+1=3＋坏 ref 9"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_ru_test_")
    try:
        secs = [
            ("1 selftest", sec1_selftest),
            ("2 coq 夹具组", lambda: sec2_coq_fixture(tmp)),
            ("3 陷阱夹具组", lambda: sec3_trap_fixture(tmp)),
            ("4 重锚冻结向量", lambda: sec4_reanchor_frozen(tmp)),
            ("5 A2 负判", lambda: sec5_a2_blast(tmp)),
            ("6 A3 负判", lambda: sec6_a3_blast(tmp)),
            ("7 干跑/apply/json", lambda: sec7_dryrun_apply_json(tmp)),
            ("8 CLI/用法面", lambda: sec8_cli_usage()),
            ("9 git 直读", lambda: sec9_git_direct(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/9] %-14s OK — %s" % (n, name, note))
        print("TEST-REGISTRY-UNION PASS: 9/9 节全过")
        return 0
    except AssertionError as e:
        print("TEST-REGISTRY-UNION FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
