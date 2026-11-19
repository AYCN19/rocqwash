#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gate7_wrapper.py — selftest for wrapper/gate7_probe.sh and
wrapper/coqc_shim.sh (tests/; 13 subprocess judges, positive/negative
pairs first).

Purpose.  Exercises the coqc shim and the gate7 probe wrapper through
  their real CLI contracts by subprocess: syntax, help, unknown-argument
  and missing-required-flag failures, missing inputs, order/module mutual
  exclusion and absence cases, the shim argv contract, fail-loud on a
  missing rocq target, and the zero-write --dry-run canonical form.
Interface.  Invokes `wrapper/coqc_shim.sh` under GATE7_PROBE_ROCQ (set to
  /bin/echo and to a missing path) and `wrapper/gate7_probe.sh` with
  bash -n, -h, --bogus, --tree, --module, --order, --workdir, --json,
  --gate-script and --dry-run; each judge prints "judge<n> <desc>:
  PASS|FAIL" and asserts exit codes plus stdout/stderr markers.
Dependencies.  bash 3.2-compatible scripts plus Python 3 standard library
  only; every fixture lives in a tempfile directory cleaned in finally;
  neither canonical wrapper is touched and no agent domain is entered;
  no rocq binary is actually invoked.
Evidence.  The judge roster with per-judge expectations is the extended
  contract comment below; judge 3 pins the shim argv contract byte-exactly
  (subcommand injection plus verbatim pass-through, stdout == "c A B --x\\n"),
  and judge 13 pins the GATE7-PROBE-DRYRUN banner with the guard knobs
  "-Front 0 -Mid 1 -MaxWaitSec 600", the python3 -B / --tree / --coqc
  pass-through, and the order file staged in the workdir with content
  "DemoMod\\n".
Exit-codes.  0 = all 13 judges pass; 1 = any judge failed (printed as
  judge<n> ... FAIL).
"""

# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard).  Judge roster,
# positive/negative pairs first, zero compilation / zero network / zero
# repository writes, temp stage cleaned in finally:
#    1 shim syntax          bash -n wrapper/coqc_shim.sh -> rc 0
#    2 probe syntax         bash -n wrapper/gate7_probe.sh -> rc 0
#    3 shim argv contract   GATE7_PROBE_ROCQ=/bin/echo shim A B -> stdout
#                           identical to "c A B\n" (coqc <args> gets the `c`
#                           subcommand injected and every other arg verbatim)
#    4 shim fail-loud       GATE7_PROBE_ROCQ=<missing> -> rc 9, loud stderr
#    5 probe help           -h -> rc 0 with the Usage header
#    6 probe unknown arg    --bogus -> rc 2
#    7 probe missing --tree -> rc 2
#    8 probe tree missing   --tree <missing> --module M -> rc 9
#    9 probe one of order/module missing -> rc 2
#   10 probe order/module both given (ambiguous) -> rc 2
#   11 probe module .v not in the world copy -> rc 9
#   12 probe canonical script missing GATE7_PROBE_SCRIPT=<missing> -> rc 9
#   13 probe --dry-run     -> rc 0; stdout carries the guard-knob canonical
#                           form with the python3 -B / --tree / --coqc
#                           pass-through; the order file is assembled inside
#                           the workdir (temp stage, cleaned in finally)
import os
import subprocess
import sys
import tempfile
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIM = os.path.join(REPO, "wrapper", "coqc_shim.sh")
PROBE = os.path.join(REPO, "wrapper", "gate7_probe.sh")
MISSING = os.path.join(os.sep, "tmp", "rqadapt_nonexistent_gate7_probe_target")


def sh(args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def main():
    ok = True
    tmp = tempfile.mkdtemp(prefix="rqadapt_g7wrap_")
    try:
        def judge(n, desc, cond, detail=""):
            nonlocal ok
            print("  judge%d %s: %s%s" % (n, desc, "PASS" if cond else "FAIL",
                                         ("" if cond else "  " + detail)))
            ok = ok and cond

        rc, out, err = sh(["bash", "-n", SHIM])
        judge(1, "shim 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", "-n", PROBE])
        judge(2, "probe 语法 bash -n", rc == 0, "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", SHIM, "A B", "--x"], env={"GATE7_PROBE_ROCQ": "/bin/echo"})
        judge(3, "shim argv 契约 c 注入＋逐字透传", rc == 0 and out == "c A B --x\n",
              "rc=%s out=%r" % (rc, out))

        rc, out, err = sh(["bash", SHIM, "--version"],
                          env={"GATE7_PROBE_ROCQ": os.path.join(tmp, "no_rocq")})
        judge(4, "shim fail-loud rc=9", rc == 9 and "missing" in err and "rocq" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "-h"])
        judge(5, "probe 子帮助 -h rc=0", rc == 0 and "Usage" in out,
              "rc=%s out=%r" % (rc, out[:120]))

        rc, out, err = sh(["bash", PROBE, "--bogus"])
        judge(6, "probe 未知形参 rc=2", rc == 2 and "unknown arg" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE])
        judge(7, "probe 缺 --tree rc=2", rc == 2 and "--tree" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", MISSING, "--module", "M"])
        judge(8, "probe tree 缺失 rc=9", rc == 9 and MISSING in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp])
        judge(9, "probe order/module 缺一 rc=2", rc == 2 and "--order" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--order", MISSING, "--module", "M"])
        judge(10, "probe order/module 同给 rc=2", rc == 2,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--module", "NoSuchMod"])
        judge(11, "probe module .v 不在副本 rc=9", rc == 9 and "NoSuchMod" in err,
              "rc=%s err=%r" % (rc, err[:200]))

        rc, out, err = sh(["bash", PROBE, "--tree", tmp, "--module", "M",
                           "--workdir", os.path.join(tmp, "w12"),
                           "--gate-script", MISSING])
        judge(12, "probe gate7 正本缺失 rc=9", rc == 9 and MISSING in err,
              "rc=%s err=%r" % (rc, err[:200]))

        world = os.path.join(tmp, "world")
        work = os.path.join(tmp, "w13")
        os.makedirs(world)
        with open(os.path.join(world, "DemoMod.v"), "w") as f:
            f.write("Definition demo_id (x:nat) := x.\n")
        jout = os.path.join(tmp, "j13.json")
        rc, out, err = sh(["bash", PROBE, "--tree", world, "--module", "DemoMod",
                           "--workdir", work, "--json", jout, "--dry-run"])
        order_path = os.path.join(work, "order_gate7_probe.txt")
        order_txt = ""
        if os.path.isfile(order_path):
            with open(order_path) as f:
                order_txt = f.read()
        judge(13, "probe --dry-run 出账＋order 装配",
              rc == 0
              and "GATE7-PROBE-DRYRUN guard:" in out
              and "-Front 0 -Mid 1 -MaxWaitSec 600" in out
              and "python3 -B" in out
              and "--tree" in out and world in out
              and "--coqc" in out and SHIM in out
              and jout in out
              and os.path.isfile(order_path) and order_txt == "DemoMod\n",
              "rc=%s out=%r order=%r" % (rc, out[:300], order_txt[:60]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("TEST-GATE7-WRAPPER:", "PASS (13/13)" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
