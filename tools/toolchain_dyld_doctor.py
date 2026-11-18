#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""toolchain_dyld_doctor.py — dyld toolchain linkage-failure diagnostician (rocqwash tools/).
Purpose.  Diagnoses dyld external-library breakage in the rocqworker binary; diagnose-only:
  restore advice is printed, never executed (the restore action belongs to the operator).
  Precedent: real CI compile jobs exiting 134 within seconds = rocqworker's hardcoded external
  dylib references gone stale (machine-verified: libgmp.10.dylib moved away from
  ConstructiveWorld/Live/toolchain/gmp/lib/; SKIP-only runs all passing pinned the environment,
  not the content).  Steps: (1) parse every `otool -L` load-library reference, drop the
  /usr/lib/ and /System/ system prefixes, keep the rest as external hard references (needed at
  dyld startup; a mismatch is the 134 class); (2) per-entry exists/missing (literal
  os.path.exists), missing entries under --donor DIR get a deterministic restore-source lookup;
  (3) --smoke (default off) runs a minimal coqc smoke under cpu_guard (--coqc explicit),
  reporting SMOKERC and the .vo magic's first 8 bytes as hex (expected prefix 436f7121, reported,
  never judged); @rpath entries follow the literal os.path.exists per spec, LC_RPATH never resolved.
Interface.  Worker resolution: --worker explicit > env ROCWASH_ROCQWORKER > default path; the
  default path and --guard are the tool's only two sanctioned reference-machine absolute defaults
  (parameterizable, the selftest depends on neither); an explicitly set (flag/env) worker that
  does not exist fails loud at 9, no fallback.  Usage (zero network):
  python3 tools/toolchain_dyld_doctor.py [--worker PATH] [--donor DIR] [--json out.json] | --smoke --coqc PATH [--guard PATH] | --selftest
  --json schema rocqwash-dyld-doctor/1: worker / external_refs[{path, exists, restore_source?}] / smoke?{rc,
  vo_magic} / verdict: healthy|missing-libs|worker-missing; deterministic write (json.dump indent=1,
  ensure_ascii=False, sort_keys=True, newline="\\n"), byte-identical rerun on identical input.
Dependencies.  Python 3 stdlib only (argparse, io, json, os, shutil, subprocess, sys, tempfile); macOS otool
  (Xcode CLT) on PATH for live runs; bash plus cpu_guard.sh for --smoke; zero network.
Evidence.  --selftest frozen vector group on tmp-synthesized fixtures (parse dedup / exists plus restore /
  verdict three-way / full CLI via a canned otool stub, print-only restore proven / byte-identical --json
  reruns / usage target codes; zero real otool, zero compiles, zero network); suite: tests/test_toolchain_dyld_doctor.py (t_toolchain_dyld_doctor).
Exit-codes.  0 = healthy (all external hard references present); 1 = missing-libs (loud, stderr mirrored);
  2 = usage error / otool nonzero exit / zero-reference otool output / smoke timeout / report write failure;
  9 = target missing (worker or otool not in PATH, --guard, --coqc, --donor).
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


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (the clean-mode manual under docs/). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"


DEFAULT_WORKER = ("/Users/apple/Desktop/mac93_install_work/opam93/rocq93/"
                  "lib/rocq-runtime/rocqworker")
DEFAULT_GUARD = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"
LIVE_TOOLCHAIN_MARK = "Live/toolchain/"
SYSTEM_PREFIXES = ("/usr/lib/", "/System/")
SMOKE_SRC = "Definition dyld_smoke_unit : nat := 1.\n"
SMOKE_GUARD_WAIT = "120"
SMOKE_TIMEOUT = 180


def parse_otool_L(text):
    """otool -L raw output -> all load-library paths (order preserved, dedup).
    Lines ending in ':' are the binary's own header and are dropped; every
    other line contributes its first whitespace-delimited token as a path."""
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
    """System prefixes (/usr/lib/, /System/) are dropped; everything else is
    an external hard reference."""
    return not path.startswith(SYSTEM_PREFIXES)


def donor_restore_source(ref, donor_dir):
    """Deterministic restore-source lookup for a missing entry under the donor
    directory: first a same-relative-path hit on the segment after
    Live/toolchain/ (donor structure preserved), then a same-basename fallback
    (os.walk with each level sorted, first in canonical order).  No hit or an
    absent donor -> None."""
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
    """Per-entry exists check plus donor restore-source lookup for missing
    entries -> [{path, exists, restore_source?}] (order preserved;
    restore_source present only on a hit)."""
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
    """Verdict roll-up: worker absent -> worker-missing; any external hard
    reference missing -> missing-libs; otherwise healthy."""
    if not worker_exists:
        return "worker-missing"
    if any(not e["exists"] for e in external_refs):
        return "missing-libs"
    return "healthy"


def restore_cmd(src, dst):
    """Restore advice command line (print-only, never executed)."""
    return "cp '%s' '%s'" % (src, dst)


def build_report(worker, external_refs, smoke, verdict):
    """rocqwash-dyld-doctor/1 report assembly (smoke present only under
    --smoke)."""
    rep = {"schema": SCHEMA, "worker": worker,
           "external_refs": external_refs, "verdict": verdict}
    if smoke is not None:
        rep["smoke"] = smoke
    return rep


def write_report(path, report):
    """Deterministic report write (indent=1, ensure_ascii=False, sort_keys,
    newline="\\n")."""
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        print("FAIL-LOUD: report write failed %s: %s" % (path, exc), file=sys.stderr)
        sys.exit(2)


def run_otool(worker):
    """Real otool -L (read-only diagnosis) -> raw output.  otool not in PATH
    -> 9; nonzero exit -> 2."""
    if shutil.which("otool") is None:
        print("FAIL-LOUD: otool not in PATH (macOS needs the Xcode CLT)", file=sys.stderr)
        sys.exit(9)
    p = subprocess.run(["otool", "-L", worker],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace") if isinstance(p.stderr, bytes) \
            else (p.stderr or "")
        sys.stderr.write("FAIL-LOUD: otool -L nonzero exit rc=%d worker=%s\n"
                         "--stderr--\n%s" % (p.returncode, worker, err))
        sys.exit(2)
    return p.stdout.decode("utf-8", "replace") if isinstance(p.stdout, bytes) \
        else (p.stdout or "")


def run_smoke(coqc, guard, wait_sec=SMOKE_GUARD_WAIT, timeout=SMOKE_TIMEOUT):
    """Minimal coqc smoke wrapped in cpu_guard (real compile, temperature
    guarded) -> {"rc", "vo_magic", "log"}.  The magic is reported, never
    judged; a missing .vo -> vo_magic=None (honest).  Guard/coqc presence is
    pre-checked by the caller (missing -> 9).  The log serves diagnostic
    stdout only and never enters the JSON (it carries tmp paths)."""
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
            print("FAIL-LOUD: smoke timed out (> %ds) guard=%s coqc=%s"
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
    """Selftest helper: run this tool in a subprocess (stdout+stderr merged;
    env can inject a PATH stub)."""
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
    """Embedded frozen vector group (tmp-synthesized; zero real otool, zero
    compiles, zero network; canned stub injected into PATH):
    V1 otool -L sample parsing (/usr/lib/ and /System/ dropped, external kept,
       order-preserving dedup)
    V2 exists check (real and fake tmp fixtures) plus restore-source
       computation (relative-segment hit / same-basename fallback / no hit)
    V3 verdict roll-up, three-way
    V4 full CLI pipeline (canned otool stub): healthy -> 0 / missing-libs -> 1
       (failing; restore advice proven print-only) / --json byte-identical
       across two runs on the same input
    V5 CLI usage and target codes: --bogus -> 2 / --smoke without --coqc -> 2 /
       --coqc missing -> 9 / --donor missing -> 9 / worker missing -> 9 /
       otool missing (PATH stripped) -> 9
    """
    import shutil as _shutil

    if os.name != "posix":
        # The canned otool stub is a POSIX shell script: a Windows host cannot
        # execute it (chmod does not set the execute bit there), so the CLI
        # vector would fail for a reason that has nothing to do with the
        # tool. Report the honest skip instead of a false red.
        print("DYLD-DOCTOR-SELFTEST SKIP: POSIX host required (the canned "
              "otool stub is a shell script)")
        return 111

    def wfile(path, data=b"x\n"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "wb") as fh:
            fh.write(data)

    tmp = tempfile.mkdtemp(prefix="rocqwash_dyld_self_")
    try:
        # ---- V1 pure parsing: /usr/lib/ and /System/ dropped, external kept,
        # order-preserving dedup ----
        refs = parse_otool_L(OTOL_SAMPLE)
        assert refs == ["/usr/lib/libSystem.B.dylib",
                        "/System/Library/Frameworks/CoreFoundation.framework/"
                        "Versions/A/CoreFoundation",
                        "/Users/x/Live/toolchain/gmp/lib/libgmp.10.dylib",
                        "@rpath/libzmq.5.dylib"], refs
        assert is_external_ref(refs[0]) is False, "system prefixes must be dropped"
        assert is_external_ref(refs[1]) is False, "system prefixes must be dropped"
        assert is_external_ref(refs[2]) is True, "Live hard reference must be kept"
        assert is_external_ref(refs[3]) is True, "@rpath kept per spec"

        # ---- V2 exists plus restore ----
        real_lib = os.path.join(tmp, "fx", "real.dylib")
        wfile(real_lib)
        missing = os.path.join(tmp, "fx", "absent", "libfoo.dylib")
        got = check_refs([real_lib, missing])
        assert got[0]["exists"] is True and got[1]["exists"] is False, got
        assert "restore_source" not in got[1], "no donor means no restore_source key"
        # relative-segment hit: a ref carrying the Live/toolchain mark resolves
        # to donor/<seg>
        donor_a = os.path.join(tmp, "donorA")
        wfile(os.path.join(donor_a, "gmp", "lib", "libgmp.10.dylib"))
        mark_ref = os.path.join(tmp, "Live", "toolchain", "gmp", "lib",
                                "libgmp.10.dylib")
        assert donor_restore_source(mark_ref, donor_a) == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), "relative-segment hit missed"
        # same-basename fallback: a ref without the mark resolves to the first
        # same-named library in donor canonical order (the ref must be truly
        # missing: the GitHub macos-15 runner preinstalls Homebrew gmp, which
        # makes the hardcoded /opt/... path exist and breaks the fixture;
        # synthetic tmp fixtures keep the selftest free of environment
        # dependencies)
        donor_b = os.path.join(tmp, "donorB")
        wfile(os.path.join(donor_b, "nested", "dir", "libgmp.10.dylib"))
        plain_ref = os.path.join(tmp, "absentbrew", "opt", "gmp", "lib",
                                 "libgmp.10.dylib")
        assert donor_restore_source(plain_ref, donor_b) == os.path.join(
            donor_b, "nested", "dir", "libgmp.10.dylib"), "same-basename fallback missed"
        # with donorA present: mark_ref takes the relative-segment hit,
        # plain_ref the same-basename fallback, both hit
        got2 = check_refs([mark_ref, plain_ref], donor_a)
        assert got2[0]["restore_source"] == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), got2
        assert got2[1]["restore_source"] == os.path.join(
            donor_a, "gmp", "lib", "libgmp.10.dylib"), "same-basename fallback missed"
        # no hit: the key must stay absent; an absent donor -> None
        nohit = check_refs([os.path.join(tmp, "nope", "libother.1.dylib")],
                           donor_a)
        assert "restore_source" not in nohit[0], nohit
        assert donor_restore_source(mark_ref,
                                    os.path.join(tmp, "nodir")) is None
        assert restore_cmd("s", "d") == "cp 's' 'd'"

        # ---- V3 verdict three-way ----
        assert verdict_of([], False) == "worker-missing"
        assert verdict_of([{"exists": True}], True) == "healthy"
        assert verdict_of([{"exists": True}, {"exists": False}],
                          True) == "missing-libs"

        # ---- V4 full CLI pipeline (canned otool stub injected into PATH, zero real otool) ----
        bin_dir = os.path.join(tmp, "bin")
        os.makedirs(bin_dir)
        stub = os.path.join(bin_dir, "otool")
        with io.open(stub, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(
                "#!/bin/bash\n"
                "# canned otool -L stub (rocqwash selftest only; no real otool; offline)\n"
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
        # determinism: two runs on the same input are byte-identical
        j2 = os.path.join(tmp, "r2.json")
        p = run_args(["--worker", wk, "--json", j2], env=env_ok)
        assert p.returncode == 0, p.stdout
        assert io.open(j1, "rb").read() == io.open(j2, "rb").read(), \
            "json byte drift = violation"
        # missing-libs failing path plus restore advice proven print-only
        # (never executed)
        miss_ref = os.path.join(tmp, "missdir", "Live", "toolchain", "gmp",
                                "lib", "libgmp.10.dylib")
        donor = os.path.join(tmp, "donor")
        wfile(os.path.join(donor, "gmp", "lib", "libgmp.10.dylib"))
        env_miss = dict(env_ok)
        env_miss["OTOOL_STUB_REF"] = miss_ref
        jm = os.path.join(tmp, "rm.json")
        p = run_args(["--worker", wk, "--donor", donor, "--json", jm],
                     env=env_miss)
        assert p.returncode == 1, "missing-libs must exit 1, got %d" % p.returncode
        assert "missing-libs" in p.stdout and "cp '" in p.stdout, p.stdout
        repm = json.load(io.open(jm, encoding="utf-8"))
        assert repm["verdict"] == "missing-libs", repm
        assert repm["external_refs"][0]["path"] == miss_ref, repm
        assert repm["external_refs"][0]["exists"] is False, repm
        assert repm["external_refs"][0]["restore_source"] == os.path.join(
            donor, "gmp", "lib", "libgmp.10.dylib"), repm
        assert not os.path.exists(miss_ref), "cp was executed = forbidden-execution violation"

        # ---- V5 CLI usage and target codes ----
        empty_dir = os.path.join(tmp, "empty")
        os.makedirs(empty_dir)
        p = run_args(["--bogus"])
        assert p.returncode == 2, "unknown flag must exit 2, got %d" % p.returncode
        p = run_args(["--worker", wk, "--smoke"])
        assert p.returncode == 2, "--smoke without --coqc must exit 2, got %d" % p.returncode
        p = run_args(["--worker", wk, "--smoke", "--coqc",
                      os.path.join(tmp, "nocoqc")])
        assert p.returncode == 9, "--coqc missing must exit 9, got %d" % p.returncode
        p = run_args(["--worker", wk, "--donor", os.path.join(tmp, "nodonor")])
        assert p.returncode == 9, "--donor missing must exit 9, got %d" % p.returncode
        p = run_args(["--worker", os.path.join(tmp, "nope")])
        assert p.returncode == 9, "worker missing must exit 9, got %d" % p.returncode
        assert "worker-missing" in p.stdout, p.stdout
        p = run_args(["--worker", wk], env={"PATH": empty_dir})
        assert p.returncode == 9, "otool missing must exit 9, got %d" % p.returncode

        print("DYLD-DOCTOR-SELFTEST PASS: otool sample parsing (system dropped/"
              "external kept/dedup)/exists true and false fixtures/restore "
              "relative-segment plus same-basename fallback plus no-hit/"
              "verdict three-way/full CLI pipeline healthy0 plus missing1 plus "
              "print-only restore/report bytes identical/usage target codes "
              "all seven sections passing")
        return 0
    finally:
        _shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="dyld toolchain linkage-failure diagnostician: otool -L "
                    "external hard-reference exists/missing plus donor "
                    "restore-source lookup with restore advice (print-only, "
                    "never executed) plus optional coqc smoke")
    ap.add_argument("--worker", default=None, metavar="PATH",
                    help="worker binary (default resolution: env %s, then the "
                         "sanctioned-machine default)" % ENV_WORKER)
    ap.add_argument("--donor", default=None, metavar="DIR",
                    help="restore-source lookup directory for missing entries "
                         "(e.g. extracted leftovers); a hit only prints the cp advice")
    ap.add_argument("--smoke", action="store_true",
                    help="run a minimal coqc smoke under cpu_guard (requires "
                         "explicit --coqc)")
    ap.add_argument("--coqc", default=None, metavar="PATH",
                    help="coqc executable (required with --smoke)")
    ap.add_argument("--guard", default=DEFAULT_GUARD, metavar="PATH",
                    help="cpu_guard.sh (used by --smoke; sanctioned-machine default)")
    ap.add_argument("--json", default=None, metavar="out.json",
                    help="write the diagnostic report (schema rocqwash-dyld-doctor/1)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.smoke:
        if not args.coqc:
            print("FAIL-LOUD: --smoke requires explicit --coqc PATH", file=sys.stderr)
            sys.exit(2)
        if not os.path.exists(args.coqc):
            print("FAIL-LOUD: --coqc missing: %s" % args.coqc, file=sys.stderr)
            sys.exit(9)
        if not os.path.isfile(args.guard):
            print("FAIL-LOUD: --guard missing: %s" % args.guard, file=sys.stderr)
            sys.exit(9)
    if args.donor is not None and not os.path.isdir(args.donor):
        print("FAIL-LOUD: --donor directory missing: %s" % args.donor, file=sys.stderr)
        sys.exit(9)

    if args.worker:
        worker, wsrc = args.worker, "flag"
    elif os.environ.get(ENV_WORKER):
        worker, wsrc = os.environ[ENV_WORKER], "env"
    else:
        # Clean mode: the sanctioned-machine worker default is a canonical
        # face; report and refuse (explicit --worker / env stays available).
        if _clean_mode():
            print("requires canonical environment: the sanctioned-machine "
                  "rocqworker default (%s); pass --worker or env %s to "
                  "analyze a specific binary" % (DEFAULT_WORKER, ENV_WORKER))
            sys.exit(9)
        worker, wsrc = DEFAULT_WORKER, "default"

    print("=== DYLD-DOCTOR ===")
    print("worker: %s (%s)" % (worker, wsrc))

    if not os.path.exists(worker):
        print("verdict: worker-missing")
        print("FAIL-LOUD: worker missing (source=%s; explicit setting never "
              "falls back to the default chain): %s"
              % (wsrc, worker), file=sys.stderr)
        if args.json:
            write_report(args.json,
                         build_report(worker, [], None, "worker-missing"))
            print("json ->", args.json)
        sys.exit(9)

    text = run_otool(worker)
    refs = parse_otool_L(text)
    if not refs:
        print("FAIL-LOUD: otool -L parsed zero references (not a Mach-O or "
              "unexpected shape): %s" % worker, file=sys.stderr)
        sys.exit(2)
    external = [r for r in refs if is_external_ref(r)]
    checked = check_refs(external, args.donor)

    print("otool -L refs: total=%d external=%d system=%d"
          % (len(refs), len(external), len(refs) - len(external)))
    print("external refs:")
    for e in checked:
        print("  [%s] %s" % (" OK " if e["exists"] else "MISS", e["path"]))
        if "restore_source" in e:
            print("    restore (advice; never executed): %s"
                  % restore_cmd(e["restore_source"], e["path"]))

    report_smoke = None
    if args.smoke:
        smoke = run_smoke(args.coqc, args.guard)
        report_smoke = {"rc": smoke["rc"], "vo_magic": smoke["vo_magic"]}
        print("smoke: SMOKERC=%d vo_magic=%s (expected prefix 436f7121; "
              "reported, never judged)"
              % (smoke["rc"],
                 smoke["vo_magic"] if smoke["vo_magic"] else "none"))
        if smoke["rc"] != 0:
            print("--- smoke log tail (SMOKERC=%d; loud diagnosis) ---" % smoke["rc"])
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
        print("FAIL: verdict=missing-libs, %d external hard reference(s) "
              "missing (loud failure): %s"
              % (len(miss), ", ".join(miss)), file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
