#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_probe_engine.py — selftest for wash/probe_engine.py, the batch
closure-compatibility probe engine (tests/; eleven sections, numbered by
execution order).

Purpose.  Machine-checks the batch probe engine end to end: tool selftest;
  the stubbed full-chain three-way split; NO-SRC; TIMEOUT; resume
  idempotence; guard wrapping with exit-code pass-through; a candidates
  list without the RED column; the four CLI exit codes; Windows
  drive-letter path normalization; whole-process-tree reaping on timeout;
  and the environment-gated real-rocq section.
Interface.  Drives `wash/probe_engine.py` as a python3 -B subprocess with
  --selftest and --candidates/--src/--world/--out/--logdir/--rocq-cmd/
  --timeout/--fresh/--guard/--guard-reg/--guard-maxwait; the real-rocq
  section runs only when ROCWASH_ROCQ is set and wraps every compile in
  `tools/cpu_guard.sh`; unset means the section SKIPs by default and adds
  no failure.
Dependencies.  Python 3 standard library only; every fixture (stub probe
  scripts plus mini source trees/worlds) is built in a temp directory and
  removed in finally; the repository fixtures probe_pass_sample.v and
  probe_red_sample.v are copied read-only; the stub sections perform zero
  real compilation and zero network.
Evidence.  Each section asserts concrete ledger outcomes; the per-section
  roster with expectations is the extended contract comment below; key
  vectors: byte-identical ledgers across resume and --fresh, the rc=7
  guard pass-through read back from the captured log banner, RC0 on a
  missing RED column, the 127-regression path-normalization vector with
  its keep-list, timeout truncation under 20s and tree reaping under 15s,
  and world purity (five products moved to logdir, zero residue).
Exit-codes.  0 = all eleven sections pass; 1 = any section failed (AssertionError printed).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  Section roster,
# numbered by execution order:
#    1 tool selftest        --selftest four vectors all pass (rc 0)
#    2 stub full chain      the stub probe splits three ways: WASHABLE
#                           (rc 0, RED>0), BORN-CLEAN (rc 0, RED=0),
#                           RED-MISSING_LIB (rc 1, missing-library name
#                           captured, red_count/md5_match recorded)
#    3 NO-SRC               a listed name without a source file ->
#                           rc=NO_SRC verdict=NO-SRC (reported honestly
#                           without compiling)
#    4 TIMEOUT              stub sleeps -> --timeout 2 -> rc=124
#                           verdict=TIMEOUT
#    5 resume idempotence   rerunning the same candidate set -> SKIP(done)
#                           lines and a byte-identical ledger (--fresh
#                           agrees byte for byte)
#    6 guard wrapping       --guard tools/cpu_guard.sh (queue discipline)
#                           plus a stub exiting rc 7 -> rc 7 recorded
#                           verbatim (exit-code pass-through, no rewrite,
#                           no pipe)
#    7 RED column missing   a candidates list without the RED column ->
#                           rc 0 verdict=RC0 (the three-way split cannot
#                           judge, reported honestly)
#    8 the four CLI codes   --help 0 / unknown arg 2 / missing arg 2 /
#                           missing path 9
#    9 drive-letter paths   drive-letter paths in the --rocq-cmd template
#                           must become forward slashes (backslash is an
#                           escape inside bash -c text and folds the command
#                           word to exit 127 -- regression vector)
#   10 TIMEOUT tree reap    the timeout must reap the whole process tree
#                           (the compiler is a grandchild still holding the
#                           pipe write end; killing only the direct child
#                           drags the 2s timeout to 30s -- regression vector)
#   11 real rocq, gated     ROCWASH_ROCQ-gated, SKIP by default and no
#                           failure added: repository fixtures
#                           probe_pass_sample.v (passing) and
#                           probe_red_sample.v (missing-library red) run the
#                           full chain -- guard wrapping plus world purity
#                           (the five products move out after the probe,
#                           zero world residue) plus logdir evidence
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "wash", "probe_engine.py")
GUARD = os.path.join(REPO, "tools", "cpu_guard.sh")
FIX_PASS = os.path.join(REPO, "tests", "fixtures", "probe_pass_sample.v")
FIX_RED = os.path.join(REPO, "tests", "fixtures", "probe_red_sample.v")

_spec = importlib.util.spec_from_file_location("probe_engine_mod", TOOL)
pe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pe)


def run(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=e)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(dirpath, name, text):
    fp = os.path.join(dirpath, name)
    with io.open(fp, "w", encoding="utf-8") as fh:
        fh.write(text)
    return fp


def md5_of(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_stage(tmp, tag, files, red_names, cands_md5_real=True):
    """Stub-probe stage: mini source tree plus a name-routed stub (names in
    red_names exit 1 with a missing-library error, the rest exit 0)."""
    stage = os.path.join(tmp, tag)
    src = os.path.join(stage, "src")
    world = os.path.join(stage, "world")
    logdir = os.path.join(stage, "logs")
    for d in (src, world, logdir):
        os.makedirs(d)
    for name, red in files:
        wf(src, name + ".v", "Lemma %s_ok : True.\n" % name)
    stub = os.path.join(stage, "stub.sh")
    cases = "".join('%s) exit 0;;\n        ' % n for n, _ in files
                    if n not in red_names)
    with io.open(stub, "w", encoding="utf-8") as fh:
        fh.write('#!/bin/bash\nn="${1%%.v}"\ncase "$n" in\n        '
                 + cases +
                 '*) echo "Error: Unable to locate library | DeepDep (while '
                 'searching for a .vos file)." >&2; exit 1;; esac\n')
    os.chmod(stub, 0o755)
    rows = ["件名\tmd5\tRED"]
    for name, red in files:
        m = md5_of(os.path.join(src, name + ".v")) if cands_md5_real \
            else "0" * len(md5_of(os.path.join(src, files[0][0] + ".v")))
        rows.append("%s\t%s\t%s" % (name, m, red))
    cands = os.path.join(stage, "cands.tsv")
    wf(stage, "cands.tsv", "\n".join(rows) + "\n")
    return stage, src, world, logdir, stub, cands


def sec1_selftest():
    rc, out = run(["--selftest"])
    assert rc == 0, "selftest 应 rc=0 实测 %d\n%s" % (rc, out)
    assert "PROBE-ENGINE-SELFTEST PASS" in out, out
    return "selftest 四判绿"


def sec2_stub_pipeline(tmp):
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s2",
        files=[("WashCand", "5"), ("CleanCand", "0"), ("RedCand", "2")],
        red_names={"RedCand"})
    led = os.path.join(stage, "ledger.json")
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    assert acc["schema"] == pe.SCHEMA, acc.get("schema")
    r_w = acc["records"]["WashCand"]
    r_c = acc["records"]["CleanCand"]
    r_r = acc["records"]["RedCand"]
    assert r_w["verdict"] == "WASHABLE" and r_w["rc"] == 0, r_w
    assert r_w["red_count"] == 5 and r_w["md5_match"] is True, r_w
    assert r_c["verdict"] == "BORN-CLEAN" and r_c["red_count"] == 0, r_c
    assert r_r["verdict"] == "RED-MISSING_LIB" and r_r["rc"] == 1, r_r
    assert r_r["missing"] == "DeepDep", r_r
    assert r_r["red"].startswith("Error: Unable to locate library"), r_r
    assert acc["n_washable"] == 1 and acc["n_born_clean"] == 1 \
        and acc["n_rc1"] == 1, acc
    # cleanup: the five products go to logdir, zero candidate residue in
    # the world
    assert not os.path.exists(os.path.join(world, "WashCand.v")), "清场违例"
    assert os.path.exists(os.path.join(logdir, "RedCand.stderr.log")), "留证缺"
    return "stub 三分 WASHABLE/BORN-CLEAN/RED-MISSING_LIB＋missing 捕获＋清场留证"


def sec3_no_src(tmp):
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s3", files=[("GhostCand", "0")], red_names=set())
    led = os.path.join(stage, "ledger.json")
    # remove the source file to produce NO-SRC
    os.remove(os.path.join(src, "GhostCand.v"))
    # the stub exits 0 for every other name -- the list contains only
    # GhostCand (no source)
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["GhostCand"]
    assert r["rc"] == "NO_SRC" and r["verdict"] == "NO-SRC", r
    return "NO-SRC 不编译如实出账"


def sec4_timeout(tmp):
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s4", files=[("SlowCand", "0")], red_names=set())
    with io.open(stub, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/bash\nsleep 30\nexit 0\n")
    os.chmod(stub, 0o755)
    led = os.path.join(stage, "ledger.json")
    t0 = time.time()
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v", "--timeout", "2"])
    dt = time.time() - t0
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["SlowCand"]
    assert r["rc"] == 124 and r["verdict"] == "TIMEOUT", r
    assert dt < 20, "超时应 2s 级截断·实测 %.1fs" % dt
    return "TIMEOUT rc=124（--timeout 2 到点截断）"


def sec5_resume_idempotent(tmp):
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s5", files=[("IdemCand", "1")], red_names=set())
    led = os.path.join(stage, "ledger.json")
    tpl = ["--candidates", cands, "--src", src, "--world", world,
           "--out", led, "--logdir", logdir, "--rocq-cmd", stub + " {name}.v"]
    rc, out = run(tpl)
    assert rc == 0 and "PROBE" in out, out
    before = io.open(led, "rb").read()
    rc2, out2 = run(tpl)
    assert rc2 == 0 and "SKIP(done)" in out2, out2
    assert io.open(led, "rb").read() == before, "resume 重跑台账字节漂移＝违例"
    # --fresh re-probes from scratch: results are deterministic, so the
    # ledger bytes still agree
    rc3, out3 = run(tpl + ["--fresh"])
    assert rc3 == 0 and "SKIP(done)" not in out3 and "PROBE" in out3, out3
    assert io.open(led, "rb").read() == before, "fresh 重探台账字节漂移＝违例"
    return "resume SKIP＋同账字节恒同＋fresh 确定性"


def sec6_guard_wrap(tmp):
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s6", files=[("GuardCand", "0")], red_names=set())
    # stub rc=7: the guard queue wraps it, so the exit code passes through
    # unrewritten (read back as 7)
    with io.open(stub, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/bash\nexit 7\n")
    os.chmod(stub, 0o755)
    led = os.path.join(stage, "ledger.json")
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v",
                   "--guard", GUARD, "--guard-reg", os.path.join(stage, "reg"),
                   "--guard-maxwait", "30"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["GuardCand"]
    assert r["rc"] == 7, "guard 透传 rc 应真取 7·实测 %r" % r["rc"]
    # the guard banner sits in the captured probe stream (the engine writes
    # it to logdir) -- read the evidence log to verify the wrapping
    with io.open(os.path.join(logdir, "GuardCand.stderr.log"),
                 encoding="utf-8") as fh:
        plog = fh.read()
    assert "[cpu_guard]" in plog and "launch" in plog, \
        "guard 包裹横幅缺（未经包裹？）：%r" % plog[:300]
    return "guard 队列制包裹＋rc=7 真取透传＋留证日志横幅"


def sec7_no_red_col(tmp):
    stage, src, world, logdir, stub, _ = make_stage(
        tmp, "s7", files=[("NoRedCand", "0")], red_names=set())
    # the candidates list has no RED column
    cands = os.path.join(stage, "cands2.tsv")
    wf(stage, "cands2.tsv", "件名\tmd5\nNoRedCand\t%s\n"
       % md5_of(os.path.join(src, "NoRedCand.v")))
    led = os.path.join(stage, "ledger.json")
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["NoRedCand"]
    assert r["rc"] == 0 and r["verdict"] == "RC0" and r["red_count"] is None, r
    return "RED 缺列→RC0 三分不可判如实出"


def sec8_win_path_normalized(tmp):
    """Windows path normalization: drive-letter paths in the --rocq-cmd
    template must become forward slashes.

    Regression vector (defect root cause): backslash is an escape character
    inside bash -c text, so MSYS bash folds the command word C:\\a\\b.sh into
    C:ab.sh, the command is not found (exit 127), and the probe records
    every candidate as RED-UNKNOWN.  The tool must convert drive-letter
    paths to forward slashes before handing the template to the shell
    (MSYS converts argv paths automatically, text arguments it does not).
    """
    bs = chr(92)
    win = "C:" + bs + "dir" + bs + "sub" + bs + "stub.sh {name}.v"
    posix = "C:/dir/sub/stub.sh {name}.v"
    got = pe.win_path_to_posix(win)
    assert got == posix, "盘符路径须转正斜杠·实测 %r" % got
    # no collateral damage: POSIX paths, shell escapes, and non-path "C:"
    # text all stay untouched
    for keep in ("/usr/bin/rocq {name}.v",
                 "echo " + bs + "n",
                 '"C: is a drive"',
                 "ABC:" + bs + "x"):
        assert pe.win_path_to_posix(keep) == keep, \
            "归一误伤 %r -> %r" % (keep, pe.win_path_to_posix(keep))
    # end to end: put a drive-letter path in the template, the stub must
    # really be found (rc=0), not exit 127
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s10", files=[("WinPathCand", "0")], red_names=set())
    tpl = stub.replace("/", bs) if os.name == "nt" else stub
    led = os.path.join(stage, "ledger.json")
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", tpl + " {name}.v"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["WinPathCand"]
    assert r["rc"] == 0 and r["verdict"] == "BORN-CLEAN", \
        "盘符路径模板须真找到桩·实测 %r" % r
    return "盘符路径模板归一（bash -c 文本反斜杠折叠·127 回归）"


def sec9_timeout_reaps_tree(tmp):
    """TIMEOUT visibility at the deadline: a timeout must reap the whole
    process tree, not wait for the grandchild to release the pipe.

    Regression vector (defect root cause): the probe command is a shell
    line, so the compiler is a grandchild; killing only the direct child
    leaves the grandchild holding the write end of the capture pipe, and on
    Windows the interpreter waits for pipe EOF before returning, so the 2s
    timeout was dragged out to the grandchild's own lifetime (30s).
    """
    stage, src, world, logdir, stub, cands = make_stage(
        tmp, "s11", files=[("SlowCand", "0")], red_names=set())
    with io.open(stub, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/bash\nsleep 30\nexit 0\n")
    os.chmod(stub, 0o755)
    led = os.path.join(stage, "ledger.json")
    t0 = time.time()
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", stub + " {name}.v", "--timeout", "2"])
    dt = time.time() - t0
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r = acc["records"]["SlowCand"]
    assert r["rc"] == 124 and r["verdict"] == "TIMEOUT", r
    assert dt < 15, "超时应到点可见（进程树收割）·实测 %.1fs" % dt
    return "TIMEOUT rc=124 到点可见（进程树收割·不被孙进程拖住）"


def sec8_cli_codes(tmp):
    rc, out = run(["--help"])
    assert rc == 0 and "usage" in out, out[-200:]
    rc, out = run(["--bogus"])
    assert rc == 2, "未知形参应 rc=2 实测 %d" % rc
    rc, out = run([])
    assert rc == 2, "缺参数应 rc=2 实测 %d" % rc
    rc, out = run(["--candidates", os.path.join(tmp, "no.tsv"), "--src", tmp,
                   "--world", tmp, "--out", os.path.join(tmp, "x.json")])
    assert rc == 9, "缺清单应 rc=9 实测 %d" % rc
    # broken list (missing the required md5 column) -> rc 2 fail-loud
    stage, src, world, logdir, stub, _ = make_stage(
        tmp, "s8", files=[("BadCand", "0")], red_names=set())
    bad = wf(stage, "bad.tsv", "件名\nBadCand\n")
    rc, out = run(["--candidates", bad, "--src", src, "--world", world,
                   "--out", os.path.join(stage, "x.json"), "--logdir", logdir])
    assert rc == 2 and "missing required column" in out, "%d %s" % (rc, out)
    return "CLI 四码（help0/bogus2/缺参2/缺件9）＋坏清单 rc2"


def sec9_real_rocq(tmp):
    rocq = os.environ.get("ROCWASH_ROCQ", "").strip()
    if not rocq:
        print("  （真 rocq 节 SKIP：ROCWASH_ROCQ 未设·缺省不充红——真编译归席位"
              "沙箱/门控轮）")
        return "真 rocq 门控节 SKIP（未门控）"
    stage = os.path.join(tmp, "s9")
    src = os.path.join(stage, "src")
    world = os.path.join(stage, "world")
    logdir = os.path.join(stage, "logs")
    for d in (src, world, logdir):
        os.makedirs(d)
    for f in (FIX_PASS, FIX_RED):
        shutil.copyfile(f, os.path.join(src, os.path.basename(f)))
    stem_pass = os.path.basename(FIX_PASS)[:-2]
    stem_red = os.path.basename(FIX_RED)[:-2]
    cands = os.path.join(stage, "cands.tsv")
    with io.open(cands, "w", encoding="utf-8") as fh:
        fh.write("件名\tmd5\tRED\n%s\t%s\t0\n%s\t%s\t1\n"
                 % (stem_pass, md5_of(os.path.join(src, stem_pass + ".v")),
                    stem_red, md5_of(os.path.join(src, stem_red + ".v"))))
    led = os.path.join(stage, "ledger.json")
    rc, out = run(["--candidates", cands, "--src", src, "--world", world,
                   "--out", led, "--logdir", logdir,
                   "--rocq-cmd", '%s c -Q . "" {name}.v' % rocq,
                   "--guard", GUARD,
                   "--guard-reg", os.path.join(stage, "reg"),
                   "--timeout", "600"])
    assert rc == 0, out
    acc = json.load(io.open(led, encoding="utf-8"))
    r_p = acc["records"][stem_pass]
    r_r = acc["records"][stem_red]
    assert r_p["rc"] == 0 and r_p["verdict"] == "BORN-CLEAN", r_p
    assert r_r["rc"] == 1 and r_r["verdict"] == "RED-MISSING_LIB", r_r
    assert r_r["missing"] == "RocqwashDeliberatelyAbsentLib", r_r
    # world purity: the five products are moved out, zero residue (the world
    # keeps only seeded files, zero in this case)
    leftovers = [f for f in os.listdir(world)
                 if f.startswith((stem_pass, stem_red))]
    assert not leftovers, "世界残留 %r＝清场违例" % leftovers
    for stem in (stem_pass, stem_red):
        assert os.path.exists(os.path.join(logdir, stem + ".stderr.log")), \
            "logdir 留证缺 %s" % stem
    return "真 rocq 全链：绿 BORN-CLEAN＋红 RED-MISSING_LIB＋世界纯度＋guard 包裹"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_probe_test_")
    try:
        secs = [
            ("1 selftest", lambda: sec1_selftest()),
            ("2 stub 全链三分", lambda: sec2_stub_pipeline(tmp)),
            ("3 NO-SRC", lambda: sec3_no_src(tmp)),
            ("4 TIMEOUT", lambda: sec4_timeout(tmp)),
            ("5 resume 幂等", lambda: sec5_resume_idempotent(tmp)),
            ("6 guard 包裹真取", lambda: sec6_guard_wrap(tmp)),
            ("7 RED 缺列 RC0", lambda: sec7_no_red_col(tmp)),
            ("8 CLI 四码", lambda: sec8_cli_codes(tmp)),
            ("9 盘符路径归一", lambda: sec8_win_path_normalized(tmp)),
            ("10 TIMEOUT 树收割", lambda: sec9_timeout_reaps_tree(tmp)),
            ("11 真 rocq 门控节", lambda: sec9_real_rocq(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/11] %-22s OK — %s" % (n, name, note))
        print("TEST-PROBE-ENGINE PASS: 11/11 节全过")
        return 0
    except AssertionError as e:
        print("TEST-PROBE-ENGINE FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
