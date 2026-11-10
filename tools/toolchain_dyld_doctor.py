#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""toolchain_dyld_doctor.py — dyld 工具链断链诊断器（rocqwash tools/·20261110
实战判例工具化·20261111 入账）

背景判例（20261110）：CI 真编译件批量秒级 EXIT=134＝rocqworker 的 dyld 硬编码
外部库失配（本机实证＝libgmp.10.dylib 于 ConstructiveWorld/Live/toolchain/gmp/
lib/ 被移走）；SKIP 件全过＝环境非内容佐证。本器把判例固化为三步诊断——只诊断
＋只打印 restore 建议命令，禁代执行（还原动作归操作者亲笔）：
  1 otool -L 解析 worker 全部加载库引用：剔除 /usr/lib/ 与 /System/ 系统前缀，
    其余保留为「外部硬引用」（dyld 启动即需、失配即 134 的那一批）。
  2 逐条 exists/missing（os.path.exists 字面判定）；missing 件在 --donor DIR 下
    溯源：先按「引用路径中 Live/toolchain/ 之后相对段」同位命中，再按同名库
    （os.walk 每层 sorted·典序首个·确定性）兜底命中——命中只打印 cp 源→目标
    建议命令。诚实注记：@rpath 项按 spec 字面 os.path.exists 判定、不代 resolve
    LC_RPATH（判例机 worker 实证仅 libgmp＋libSystem 两条·无 @rpath 项）。
  3 --smoke 可选（缺省关）：经 cpu_guard 跑最小 coqc 冒烟（--coqc 显传），报
    SMOKERC 与 .vo 魔数前 8 字节 hex（期望前缀 436f7121＝9.3 代判据之一——
    魔数只报不判）。

worker 依序：--worker 显传 > env ROCWASH_ROCQWORKER > 缺省路径。缺省路径为本器
仅有的两处 sanctioned 判例机绝对缺省之一（另一处为 --guard 缺省；任务书指定·
全可参数化覆盖·selftest 零依赖）：
  /Users/apple/Desktop/mac93_install_work/opam93/rocq93/lib/rocq-runtime/rocqworker
显式指定（flag/env）不存在 → fail-loud 不回退缺省链（禁静默降级）；仅未显式
指定时才落缺省。

用法（除上述 sanctioned 缺省外零硬编码·零网络·selftest 零真 otool 零编译零网络）：
  python3 tools/toolchain_dyld_doctor.py [--worker PATH] [--donor DIR] [--json out.json]
  python3 tools/toolchain_dyld_doctor.py --smoke --coqc PATH [--guard PATH] [--json out.json]
  python3 tools/toolchain_dyld_doctor.py --selftest

退出码：0=healthy（外部硬引用全部在位）；1=missing-libs（红响亮·stderr 同报）；
2=用法错／otool 非零退出／otool 输出零引用断言失败／smoke 超时／报告落盘失败；
9=目标缺失（worker／otool 不在 PATH／--guard／--coqc／--donor）。--json 报告
schema=rocqwash-dyld-doctor/1：
  worker / external_refs[{path, exists, restore_source?}] / smoke?{rc, vo_magic}
  / verdict: healthy|missing-libs|worker-missing
落盘 json.dump(indent=1, ensure_ascii=False, sort_keys=True)＋newline="\\n"；
报告不含墙钟字段·同输入重跑字节级恒同。
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

PROG = "toolchain_dyld_doctor"
SCHEMA = "rocqwash-dyld-doctor/1"
ENV_WORKER = "ROCWASH_ROCQWORKER"
DEFAULT_WORKER = ("/Users/apple/Desktop/mac93_install_work/opam93/rocq93/"
                  "lib/rocq-runtime/rocqworker")
DEFAULT_GUARD = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"
LIVE_TOOLCHAIN_MARK = "Live/toolchain/"
SYSTEM_PREFIXES = ("/usr/lib/", "/System/")
SMOKE_SRC = "Definition dyld_smoke_unit : nat := 1.\n"
SMOKE_GUARD_WAIT = "120"
SMOKE_TIMEOUT = 180


def parse_otool_L(text):
    """otool -L 原文 → 全部加载库路径（保序去重）。以':'结尾的行＝二进制自身头
    剔除；其余行取首个空白前 token 为路径。"""
    refs = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.endswith(":"):
            continue
        tok = s.split()[0]
        if tok not in refs:
            refs.append(tok)
    return refs


def is_external_ref(path):
    """系统前缀（/usr/lib/、/System/）剔除·其余＝外部硬引用。"""
    return not path.startswith(SYSTEM_PREFIXES)


def donor_restore_source(ref, donor_dir):
    """missing 件在 donor 下的确定性溯源：先按 Live/toolchain/ 之后相对段同位
    命中（保 donor 结构），再按同名库兜底（os.walk 每层 sorted·典序首个）。
    无命中/donor 缺席 → None。"""
    if not donor_dir or not os.path.isdir(donor_dir):
        return None
    seg = None
    if LIVE_TOOLCHAIN_MARK in ref:
        seg = ref.rsplit(LIVE_TOOLCHAIN_MARK, 1)[-1]
    if seg:
        cand = os.path.join(donor_dir, seg)
        if os.path.isfile(cand):
            return cand
    base = os.path.basename(ref)
    for root, dirs, files in os.walk(donor_dir):
        dirs.sort()
        for fn in sorted(files):
            if fn == base:
                return os.path.join(root, fn)
    return None


def check_refs(refs, donor_dir=None):
    """逐条 exists 判定＋missing 件 donor 溯源 → [{path,exists,restore_source?}]
    （保序；restore_source 仅命中时在场）。"""
    out = []
    for r in refs:
        e = {"path": r, "exists": os.path.exists(r)}
        if not e["exists"] and donor_dir:
            src = donor_restore_source(r, donor_dir)
            if src:
                e["restore_source"] = src
        out.append(e)
    return out


def verdict_of(external_refs, worker_exists=True):
    """verdict 汇总：worker 缺席 → worker-missing；任一外部硬引用 missing →
    missing-libs；否则 healthy。"""
    if not worker_exists:
        return "worker-missing"
    if any(not e["exists"] for e in external_refs):
        return "missing-libs"
    return "healthy"


def restore_cmd(src, dst):
    """restore 建议命令行（只打印·禁代执行）。"""
    return "cp '%s' '%s'" % (src, dst)


def build_report(worker, external_refs, smoke, verdict):
    """schema=rocqwash-dyld-doctor/1 报告组装（smoke 仅 --smoke 时在场）。"""
    rep = {"schema": SCHEMA, "worker": worker,
           "external_refs": external_refs, "verdict": verdict}
    if smoke is not None:
        rep["smoke"] = smoke
    return rep


def write_report(path, report):
    """确定性落盘（indent=1·ensure_ascii=False·sort_keys·newline=\\n）。"""
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        print("FAIL-LOUD: 报告落盘失败 %s: %s" % (path, exc), file=sys.stderr)
        sys.exit(2)


def run_otool(worker):
    """真 otool -L（只诊断读）→ 原文。otool 不在 PATH → 9；非零退出 → 2。"""
    if shutil.which("otool") is None:
        print("FAIL-LOUD: otool 不在 PATH（macOS 需 Xcode CLT）", file=sys.stderr)
        sys.exit(9)
    p = subprocess.run(["otool", "-L", worker],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace") if isinstance(p.stderr, bytes) \
            else (p.stderr or "")
        sys.stderr.write("FAIL-LOUD: otool -L 非零退出 rc=%d worker=%s\n"
                         "--stderr--\n%s" % (p.returncode, worker, err))
        sys.exit(2)
    return p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")


def run_smoke(coqc, guard, wait_sec=SMOKE_GUARD_WAIT, timeout=SMOKE_TIMEOUT):
    """cpu_guard 包裹最小 coqc 冒烟（真编译·必经温控）→ {"rc", "vo_magic",
    "log"}。魔数只报不判；.vo 缺席 → vo_magic=None（如实）。guard/coqc 在位性
    由调用方预检（缺 → 9）。log 仅诊断 stdout 用·不入 JSON（含 tmp 路径）。"""
    tmp = tempfile.mkdtemp(prefix="rocqwash_dyld_smoke_")
    try:
        vfile = os.path.join(tmp, "smoke.v")
        with io.open(vfile, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(SMOKE_SRC)
        cmd = ["bash", guard, "-MaxWaitSec", wait_sec, "--", coqc, "smoke.v"]
        try:
            p = subprocess.run(cmd, cwd=tmp, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired:
            print("FAIL-LOUD: smoke 超时（>%ds）guard=%s coqc=%s"
                  % (timeout, guard, coqc), file=sys.stderr)
            sys.exit(2)
        out = p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
            else (p.stdout or "")
        vo = os.path.join(tmp, "smoke.vo")
        magic = None
        if os.path.isfile(vo):
            with io.open(vo, "rb") as fh:
                magic = fh.read(8).hex()
        return {"rc": p.returncode, "vo_magic": magic, "log": out}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv, env=None):
    """selftest 辅助：子进程跑本器（stdout+stderr 合流·env 可注入 PATH stub）。"""
    import subprocess
    e = dict(os.environ) if env is None else dict(env)
    p = subprocess.run([sys.executable, "-B",
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     PROG + ".py")] + list(argv),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    p.stdout = p.stdout.decode("utf-8", errors="replace") \
        if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


OTOL_SAMPLE = (
    "/fake/worker:\n"
    "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1319.0.0)\n"
    "\t/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"
    " (compatibility version 150.0.0, current version 2200.0.0)\n"
    "\t/Users/x/Live/toolchain/gmp/lib/libgmp.10.dylib (compatibility version 16.0.0,"
    " current version 16.0.0)\n"
    "\t/Users/x/Live/toolchain/gmp/lib/libgmp.10.dylib (compatibility version 16.0.0,"
    " current version 16.0.0)\n"
    "\t@rpath/libzmq.5.dylib (compatibility version 8.0.0, current version 8.0.0)\n"
)


def selftest():
    """内嵌冻结向量组（tmp 合成·零真 otool 零编译零网络·canned stub 注入 PATH）：
    V1 otool -L 样例解析（/usr/lib//System 剔除·外部保留·保序去重）
    V2 exists 判定（tmp 真件/假件）＋restore 路径计算（相对段同位/同名兜底/无命中）
    V3 verdict 汇总三分
    V4 CLI 全管线（canned otool stub）：healthy→0／missing-libs→1（红·restore
       建议只打印不执行实证）／--json 同输入两跑字节恒同
    V5 CLI 用法与目标码：--bogus→2·--smoke 缺 --coqc→2·--coqc 缺失→9·
       --donor 缺失→9·worker 缺失→9·otool 缺失（PATH 剥空）→9
    """
    import shutil as _shutil

    def wfile(path, data=b"x\n"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "wb") as fh:
            fh.write(data)

    tmp = tempfile.mkdtemp(prefix="rocqwash_dyld_self_")
    try:
        # ---- V1 纯解析：剔除 /usr/lib//System·保留外部·保序去重 ----
        refs = parse_otool_L(OTOL_SAMPLE)
        assert refs == ["/usr/lib/libSystem.B.dylib",
                        "/System/Library/Frameworks/CoreFoundation.framework/"
                        "Versions/A/CoreFoundation",
                        "/Users/x/Live/toolchain/gmp/lib/libgmp.10.dylib",
                        "@rpath/libzmq.5.dylib"], refs
        assert is_external_ref(refs[0]) is False, "系统前缀须剔除"
        assert is_external_ref(refs[1]) is False, "系统前缀须剔除"
        assert is_external_ref(refs[2]) is True, "Live 硬引用须保留"
        assert is_external_ref(refs[3]) is True, "@rpath 按 spec 保留"

        # ---- V2 exists＋restore ----
        real_lib = os.path.join(tmp, "fx", "real.dylib")
        wfile(real_lib)
        missing = os.path.join(tmp, "fx", "absent", "libfoo.dylib")
        got = check_refs([real_lib, missing])
        assert got[0]["exists"] is True and got[1]["exists"] is False, got
        assert "restore_source" not in got[1], "无 donor 不得有 restore_source"
        # 相对段同位：ref 含 Live/toolchain 标记 → donor/<seg>
        donor_a = os.path.join(tmp, "donorA")
        wfile(os.path.join(donor_a, "gmp", "lib", "libgmp.10.dylib"))
        mark_ref = os.path.join(tmp, "Live", "toolchain", "gmp", "lib",
                                "libgmp.10.dylib")
        assert donor_restore_source(mark_ref, donor_a) == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), "相对段同位未命中"
        # 同名兜底：ref 无标记 → donor 典序首同名
        donor_b = os.path.join(tmp, "donorB")
        wfile(os.path.join(donor_b, "nested", "dir", "libgmp.10.dylib"))
        plain_ref = "/opt/homebrew/opt/gmp/lib/libgmp.10.dylib"
        assert donor_restore_source(plain_ref, donor_b) == os.path.join(
            donor_b, "nested", "dir", "libgmp.10.dylib"), "同名兜底未命中"
        # donorA 在场：mark_ref 走相对段同位·plain_ref 走同名兜底·双双命中
        got2 = check_refs([mark_ref, plain_ref], donor_a)
        assert got2[0]["restore_source"] == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), got2
        assert got2[1]["restore_source"] == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), "同名兜底未命中"
        # 无命中：键不得在场；donor 缺席 → None
        nohit = check_refs([os.path.join(tmp, "nope", "libother.1.dylib")],
                           donor_a)
        assert "restore_source" not in nohit[0], nohit
        assert donor_restore_source(mark_ref,
                                    os.path.join(tmp, "nodir")) is None
        assert restore_cmd("s", "d") == "cp 's' 'd'"

        # ---- V3 verdict 三分 ----
        assert verdict_of([], False) == "worker-missing"
        assert verdict_of([{"exists": True}], True) == "healthy"
        assert verdict_of([{"exists": True}, {"exists": False}],
                          True) == "missing-libs"

        # ---- V4 CLI 全管线（canned otool stub 注入 PATH·零真 otool）----
        bin_dir = os.path.join(tmp, "bin")
        os.makedirs(bin_dir)
        stub = os.path.join(bin_dir, "otool")
        with io.open(stub, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(
                "#!/bin/bash\n"
                "# canned otool -L stub（rocqwash selftest 专用·零真 otool·离线）\n"
                "printf '%s:\\n' \"$2\"\n"
                "printf '\\t/usr/lib/libSystem.B.dylib (compatibility version"
                " 1.0.0, current version 1319.0.0)\\n'\n"
                "printf '\\t/System/Library/Frameworks/CoreFoundation.framework"
                "/Versions/A/CoreFoundation (compatibility version 150.0.0,"
                " current version 2200.0.0)\\n'\n"
                "printf '\\t%s (compatibility version 16.0.0, current version"
                " 16.0.0)\\n' \"$OTOOL_STUB_REF\"\n")
        os.chmod(stub, 0o755)
        wk = os.path.join(tmp, "wk", "rocqworker")
        wfile(wk, b"fake-mach-o-for-selftest\n")
        ok_lib = os.path.join(tmp, "okdir", "Live", "toolchain", "gmp", "lib",
                              "libgmp.10.dylib")
        wfile(ok_lib)
        env_ok = dict(os.environ)
        env_ok["PATH"] = bin_dir + os.pathsep + env_ok.get("PATH", "")
        env_ok["OTOOL_STUB_REF"] = ok_lib
        j1 = os.path.join(tmp, "r1.json")
        p = run_args(["--worker", wk, "--json", j1], env=env_ok)
        assert p.returncode == 0, p.stdout
        assert "verdict: healthy" in p.stdout, p.stdout
        rep = json.load(io.open(j1, encoding="utf-8"))
        assert rep["schema"] == SCHEMA and rep["worker"] == wk, rep
        assert rep["verdict"] == "healthy", rep
        assert rep["external_refs"] == [{"path": ok_lib, "exists": True}], rep
        assert set(rep) == {"schema", "worker", "external_refs", "verdict"}, rep
        # 确定性：同输入两跑字节恒同
        j2 = os.path.join(tmp, "r2.json")
        p = run_args(["--worker", wk, "--json", j2], env=env_ok)
        assert p.returncode == 0, p.stdout
        assert io.open(j1, "rb").read() == io.open(j2, "rb").read(), \
            "json 字节漂移＝违例"
        # missing-libs 红路径＋restore 建议只打印不执行
        miss_ref = os.path.join(tmp, "missdir", "Live", "toolchain", "gmp",
                                "lib", "libgmp.10.dylib")
        donor = os.path.join(tmp, "donor")
        wfile(os.path.join(donor, "gmp", "lib", "libgmp.10.dylib"))
        env_miss = dict(env_ok)
        env_miss["OTOOL_STUB_REF"] = miss_ref
        jm = os.path.join(tmp, "rm.json")
        p = run_args(["--worker", wk, "--donor", donor, "--json", jm],
                     env=env_miss)
        assert p.returncode == 1, "missing-libs 应红 exit=1 实测 %d" % p.returncode
        assert "missing-libs" in p.stdout and "cp '" in p.stdout, p.stdout
        repm = json.load(io.open(jm, encoding="utf-8"))
        assert repm["verdict"] == "missing-libs", repm
        assert repm["external_refs"][0]["path"] == miss_ref, repm
        assert repm["external_refs"][0]["exists"] is False, repm
        assert repm["external_refs"][0]["restore_source"] == os.path.join(
            donor, "gmp", "lib", "libgmp.10.dylib"), repm
        assert not os.path.exists(miss_ref), "cp 竟被执行＝禁代执行违例"

        # ---- V5 CLI 用法与目标码 ----
        empty_dir = os.path.join(tmp, "empty")
        os.makedirs(empty_dir)
        p = run_args(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run_args(["--worker", wk, "--smoke"])
        assert p.returncode == 2, "--smoke 缺 --coqc 应 rc=2 实测 %d" % p.returncode
        p = run_args(["--worker", wk, "--smoke", "--coqc",
                      os.path.join(tmp, "nocoqc")])
        assert p.returncode == 9, "--coqc 缺失应 rc=9 实测 %d" % p.returncode
        p = run_args(["--worker", wk, "--donor", os.path.join(tmp, "nodonor")])
        assert p.returncode == 9, "--donor 缺失应 rc=9 实测 %d" % p.returncode
        p = run_args(["--worker", os.path.join(tmp, "nope")])
        assert p.returncode == 9, "worker 缺失应 rc=9 实测 %d" % p.returncode
        assert "worker-missing" in p.stdout, p.stdout
        p = run_args(["--worker", wk], env={"PATH": empty_dir})
        assert p.returncode == 9, "otool 缺失应 rc=9 实测 %d" % p.returncode

        print("DYLD-DOCTOR-SELFTEST PASS: otool 样例解析（系统剔除/外部保留/去重）/"
              "exists 真假件/restore 同位＋同名兜底＋无命中/verdict 三分/"
              "CLI 全管线 healthy0＋missing1＋禁代执行/落盘字节恒同/用法目标六码 "
              "七节全过")
        return 0
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="dyld 工具链断链诊断器：otool -L 外部硬引用 exists/missing"
                    "＋donor 溯源 restore 建议（只打印禁代执行）＋可选 coqc 冒烟")
    ap.add_argument("--worker", default=None, metavar="PATH",
                    help="worker 二进制（缺省依序 env %s→判例机缺省）" % ENV_WORKER)
    ap.add_argument("--donor", default=None, metavar="DIR",
                    help="missing 件溯源目录（如抽取残面）；命中只打印 cp 建议")
    ap.add_argument("--smoke", action="store_true",
                    help="经 cpu_guard 跑最小 coqc 冒烟（需显传 --coqc）")
    ap.add_argument("--coqc", default=None, metavar="PATH",
                    help="coqc 可执行（--smoke 时必显传）")
    ap.add_argument("--guard", default=DEFAULT_GUARD, metavar="PATH",
                    help="cpu_guard.sh（--smoke 用·判例机缺省）")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="诊断报告出账（schema rocqwash-dyld-doctor/1）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.smoke:
        if not args.coqc:
            print("FAIL-LOUD: --smoke 需显传 --coqc PATH", file=sys.stderr)
            sys.exit(2)
        if not os.path.exists(args.coqc):
            print("FAIL-LOUD: --coqc 缺失: %s" % args.coqc, file=sys.stderr)
            sys.exit(9)
        if not os.path.isfile(args.guard):
            print("FAIL-LOUD: --guard 缺失: %s" % args.guard, file=sys.stderr)
            sys.exit(9)
    if args.donor is not None and not os.path.isdir(args.donor):
        print("FAIL-LOUD: --donor 目录缺失: %s" % args.donor, file=sys.stderr)
        sys.exit(9)

    if args.worker:
        worker, wsrc = args.worker, "flag"
    elif os.environ.get(ENV_WORKER):
        worker, wsrc = os.environ[ENV_WORKER], "env"
    else:
        worker, wsrc = DEFAULT_WORKER, "default"

    print("=== DYLD-DOCTOR ===")
    print("worker: %s（%s）" % (worker, wsrc))

    if not os.path.exists(worker):
        print("verdict: worker-missing")
        print("FAIL-LOUD: worker 缺失（来源=%s·显式指定不回退缺省链）: %s"
              % (wsrc, worker), file=sys.stderr)
        if args.json:
            write_report(args.json,
                         build_report(worker, [], None, "worker-missing"))
            print("json ->", args.json)
        sys.exit(9)

    text = run_otool(worker)
    refs = parse_otool_L(text)
    if not refs:
        print("FAIL-LOUD: otool -L 解析零引用（非 Mach-O 或形态异常）: %s"
              % worker, file=sys.stderr)
        sys.exit(2)
    external = [r for r in refs if is_external_ref(r)]
    checked = check_refs(external, args.donor)

    print("otool -L refs: total=%d external=%d system=%d"
          % (len(refs), len(external), len(refs) - len(external)))
    print("external refs:")
    for e in checked:
        print("  [%s] %s" % (" OK " if e["exists"] else "MISS", e["path"]))
        if "restore_source" in e:
            print("    restore（建议·禁代执行）: %s"
                  % restore_cmd(e["restore_source"], e["path"]))

    report_smoke = None
    if args.smoke:
        smoke = run_smoke(args.coqc, args.guard)
        report_smoke = {"rc": smoke["rc"], "vo_magic": smoke["vo_magic"]}
        print("smoke: SMOKERC=%d vo_magic=%s（期望前缀 436f7121·只报不判）"
              % (smoke["rc"],
                 smoke["vo_magic"] if smoke["vo_magic"] else "none"))
        if smoke["rc"] != 0:
            print("--- smoke log tail（SMOKERC=%d·诊断响亮）---" % smoke["rc"])
            for ln in smoke["log"].rstrip().splitlines()[-40:]:
                print("  | %s" % ln)

    verdict = verdict_of(checked, True)
    print("verdict: %s" % verdict)
    if args.json:
        write_report(args.json,
                     build_report(worker, checked, report_smoke, verdict))
        print("json ->", args.json)
    if verdict == "missing-libs":
        miss = [e["path"] for e in checked if not e["exists"]]
        print("FAIL: verdict=missing-libs 外部硬引用缺失 %d 条（红响亮）: %s"
              % (len(miss), ", ".join(miss)), file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
