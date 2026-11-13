#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_engine.py — batch closure-compatibility probe engine (rocqwash wash/).

    Purpose.  Probes closure compatibility in batch: for each candidate in the TSV manifest, copy
      `<name>.v` from --src into the seeded world directory (read-only seeded .vo closure) and run
      one real `rocq c` compile there, verdict read from the subprocess returncode (never through a
      pipe); only --out and --logdir are written, the five probe artifacts move into --logdir as
      evidence afterwards (world purity kept); real compiles run wrapped through cpu_guard under
      --guard; resume by default (same-md5 --out records are skipped; --fresh re-probes everything).

    Interface.  python3 wash/probe_engine.py --candidates TSV --src DIR --world DIR --out ledger.json
      --logdir DIR [--rocq-cmd TPL] [--guard PATH --guard-reg DIR --guard-front N --guard-mid N
      --guard-maxwait N] [--timeout S] [--ulimit-stack N] [--jobs K] [--fresh] | --selftest;
      manifest columns located by name: `件名`/`md5` required, `RED` optional (statement-face RED
      line count; without it an rc0 record is reported as RC0 — the three-way split is undecidable);
      verdict ∈ {`WASHABLE`, `BORN-CLEAN`, `RC0`, `TIMEOUT`, `NO-SRC`} ∪ {`RED-MISSING_LIB`,
      `RED-ILLEGAL_APP`, `RED-NO_SUBTERM`, `RED-FACE`, `RED-OTHER`, `RED-UNKNOWN`}; failure-class
      regexes apply in order, first match wins (MISSING_LIB captures the library name); ledger
      schema rocqwash-probe-ledger/1, records keyed by candidate name (--jobs K > 1: the main
      thread records in dictionary order, completion order never reorders output).

    Dependencies.  Python 3 standard library only; bash for the inner compile command and the cpu_guard wrapper; all paths parameterized.

    Evidence.  --selftest frozen vector groups (temporary directory, stub probe, zero real compiles):
      rc three-way split, missing-library capture, resume byte-identity, --jobs K=1/K=3 parallel
      output-equivalence vectors, --jobs 0 rc=2, four CLI codes; tests/test_probe_engine.py reruns them.

    Exit-codes.  0 = batch complete, ledger written (rc1 candidates are probe output data, not a tool
      failure; counts printed loudly); 1 = --selftest assertion failure; 2 = usage error (--help rc=0,
      missing required arguments, --jobs < 1, duplicate candidate names under --jobs > 1);
      9 = --candidates/--src/--world/--guard path missing."""
import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

PROG = "probe_engine"
SCHEMA = "rocqwash-probe-ledger/1"
DEFAULT_ROCQ_CMD = 'rocq c -Q . "" {name}.v'


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (docs/clean-mode-manual-20261114.md). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"

# failure-class regexes (first match in order wins, IGNORECASE)
MISSING_LIB_RE = re.compile(r"(?:unable to locate library|cannot find library)\s+\|?\s*"
                            r"([A-Za-z0-9_']+)", re.IGNORECASE)
CLASS_RES = [
    ("MISSING_LIB", re.compile(r"unable to locate library|cannot find library", re.I)),
    ("ILLEGAL_APP", re.compile(r"illegal application", re.I)),
    ("NO_SUBTERM", re.compile(r"no subterm matching", re.I)),
    ("FACE", re.compile(r"expected to have type|is not convertible", re.I)),
]
RED_LINE_RE = re.compile(r"Error|Cannot find library|Anomaly")

ARTIFACT_EXTS = (".v", ".vo", ".glob", ".vos", ".vok")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_candidates(path):
    """Candidate manifest TSV → [(name, md5, red_or_None)] (columns located
    by header names, not positions; fail-loud)."""
    with io.open(path, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    if not lines:
        raise ValueError("candidate manifest is an empty file: %s" % path)
    header = lines[0].split("\t")
    for req in ("件名", "md5"):
        if req not in header:
            raise ValueError("candidate manifest missing required column "
                             "'%s' (header=%r)" % (req, header))
    i_name = header.index("件名")
    i_md5 = header.index("md5")
    i_red = header.index("RED") if "RED" in header else None
    out = []
    for ln in lines[1:]:
        f = ln.split("\t")
        if len(f) < len(header):
            raise ValueError("candidate manifest row width mismatch (expected "
                             "%d columns, got %d): %r" % (len(header), len(f), ln))
        red = None
        if i_red is not None:
            v = f[i_red].strip()
            if v != "":
                red = int(v)
        out.append((f[i_name].strip(), f[i_md5].strip(), red))
    return out


def classify_red(red_text):
    """Failure-class triage: returns (red_class, missing_lib_or_None);
    first match in order wins."""
    m = MISSING_LIB_RE.search(red_text or "")
    missing = m.group(1) if m else None
    for cls, rx in CLASS_RES:
        if rx.search(red_text or ""):
            return cls, missing
    return (None, missing)


def extract_red(err, out):
    """First Error/Cannot find library/Anomaly line plus its continuation line
    (library names and details usually sit on the next line)."""
    lines_all = (err + "\n" + out).split("\n")
    for i, ln in enumerate(lines_all):
        if RED_LINE_RE.search(ln):
            nxt = lines_all[i + 1].strip() if i + 1 < len(lines_all) else ""
            return (ln.strip() + " | " + nxt)[:300]
    return ""


def verdict_rc1(red_text):
    """rc1 failure verdict: RED-<class>, RED-OTHER (failure text with no class
    hit), RED-UNKNOWN (no failure text at all)."""
    cls, _ = classify_red(red_text)
    if cls:
        return "RED-" + cls
    return "RED-OTHER" if (red_text or "").strip() else "RED-UNKNOWN"


def verdict_of_rc(rc, red_count):
    """rc0/124/NO_SRC verdict split (without the RED column an rc0 record is
    reported as RC0 — the three-way split is undecidable)."""
    if rc == "NO_SRC":
        return "NO-SRC"
    if rc == 124:
        return "TIMEOUT"
    if red_count is None:
        return "RC0"
    return "WASHABLE" if red_count > 0 else "BORN-CLEAN"


def probe_one(name, src_dir, world_dir, logdir, rocq_cmd, guard, guard_reg,
              guard_front, guard_mid, guard_maxwait, timeout, ulimit_stack):
    """One probe: copy → compile → real exit code → failure extraction →
    cleanup.  Returns the record dict."""
    src = os.path.join(src_dir, name + ".v")
    if not os.path.exists(src):
        return {"file": name, "md5": None, "rc": "NO_SRC", "red": "",
                "missing": None, "red_class": "", "verdict": "NO-SRC",
                "red_count": None, "md5_match": None}
    dst = os.path.join(world_dir, name + ".v")
    shutil.copyfile(src, dst)
    inner = ""
    if ulimit_stack:
        inner += "ulimit -s %d; " % ulimit_stack
    inner += rocq_cmd.replace("{name}", name)
    if guard:
        cmd = ["bash", guard, "-Reg", guard_reg,
               "-Front", str(guard_front), "-Mid", str(guard_mid),
               "-MaxWaitSec", str(guard_maxwait), "--", "bash", "-c", inner]
    else:
        cmd = ["bash", "-c", inner]
    try:
        p = subprocess.run(cmd, cwd=world_dir, capture_output=True,
                           text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = e.stdout.decode("utf-8", errors="replace") \
            if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", errors="replace") \
            if isinstance(e.stderr, bytes) else (e.stderr or "")
    with io.open(os.path.join(logdir, name + ".stderr.log"), "w",
                 encoding="utf-8") as f:
        f.write(err + "\n===STDOUT===\n" + out)
    red = extract_red(err, out)
    cls, missing = classify_red(red)
    rec = {"file": name, "md5": md5_of(src), "rc": rc, "red": red,
           "missing": missing, "red_class": cls,
           "verdict": "TIMEOUT" if rc == 124 else
           (verdict_rc1(red) if rc != 0 else "RC0"),
           "red_count": None, "md5_match": None}
    # cleanup: move the five artifacts out of the world into logdir as evidence
    # (the world keeps its seeded purity)
    for ext in ARTIFACT_EXTS:
        f = os.path.join(world_dir, name + ext)
        if os.path.exists(f):
            shutil.move(f, os.path.join(logdir, name + ext))
    return rec


def save_ledger(out_path, args, records):
    acc = {"schema": SCHEMA,
           "candidates": args.candidates, "src": args.src, "world": args.world,
           "n_records": len(records),
           "n_washable": sum(1 for r in records.values()
                             if r.get("verdict") == "WASHABLE"),
           "n_born_clean": sum(1 for r in records.values()
                               if r.get("verdict") == "BORN-CLEAN"),
           "n_rc0": sum(1 for r in records.values() if r.get("rc") == 0),
           "n_rc1": sum(1 for r in records.values() if r.get("rc") == 1),
           "records": records}
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(acc, fh, indent=1, ensure_ascii=False, sort_keys=True)


def _run_batch_parallel(cands, src_dir, world_dir, logdir, args, records):
    """--jobs K > 1 sharded parallel batch (K=1 always takes the original
    serial loop in run_batch, zero behavior drift).

    Resume skips run first → the remaining candidates go into a
    concurrent.futures.ThreadPool (max_workers=K, one probe_one per
    candidate; real compiles still run wrapped through --guard one by one;
    the guard FRONT tier clamps concurrency on its own under the same -Reg
    registry) → the main thread records in candidate dictionary order and
    writes to disk (fut order = pending order = candidate dictionary order;
    completion order never reorders output — determinism invariant;
    records/skipped/probes carry the same meaning and shape as the serial
    path, with the same incremental per-candidate ledger write).  Duplicate
    candidate names fail loud rc=2 (concurrent copyfile/compile/cleanup
    world-write races between same-name files are refused)."""
    skipped, probes = 0, 0
    pending = []
    for name, md5_decl, red_count in cands:
        prev = records.get(name)
        if prev is not None and prev.get("md5") == md5_decl and not args.fresh:
            skipped += 1
            print("SKIP(done) %s rc=%s verdict=%s"
                  % (name, prev.get("rc"), prev.get("verdict")))
            continue
        pending.append((name, md5_decl, red_count))
    seen, dupes = set(), []
    for n in (t[0] for t in pending):
        if n in seen and n not in dupes:
            dupes.append(n)
        seen.add(n)
    if dupes:
        print("FAIL-LOUD: --jobs %d parallel sharding rejects duplicate "
              "candidate names (concurrent same-name world-write race): %s"
              % (args.jobs, ",".join(sorted(set(dupes)))),
              file=sys.stderr)
        sys.exit(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(probe_one, name, src_dir, world_dir, logdir,
                          args.rocq_cmd, args.guard, args.guard_reg,
                          args.guard_front, args.guard_mid, args.guard_maxwait,
                          args.timeout, args.ulimit_stack)
                for name, _md5_decl, _red in pending]
        try:
            # the main thread records in candidate dictionary order (completion
            # order never invades output order; record order stays dictionary
            # order)
            for (name, md5_decl, red_count), fut in zip(pending, futs):
                rec = fut.result()
                rec["red_count"] = red_count
                rec["md5_match"] = (md5_decl == rec["md5"]) if rec["md5"] \
                    else None
                if rec["rc"] == 0:
                    rec["verdict"] = verdict_of_rc(0, red_count)
                records[name] = rec
                probes += 1
                print("PROBE %-42s rc=%s verdict=%s%s"
                      % (name, rec["rc"], rec["verdict"],
                         (" RED: " + rec["red"]) if rec["red"] else ""))
                # incremental per-candidate ledger write (resumable after an
                # interruption; same as the serial path)
                save_ledger(args.out, args, records)
        except BaseException:
            for f in futs:
                f.cancel()          # cancel not-yet-started futures; running ones finish naturally (fail-loud, nothing swallowed)
            raise
    return records, skipped, probes


def run_batch(cands, src_dir, world_dir, logdir, args):
    """Batch probe (resume idempotent) → (records, skipped, probes).

    --jobs K (default 1): K=1 takes the original serial loop below (kept
    verbatim, zero behavior drift); K > 1 shards the batch into
    _run_batch_parallel (dictionary-order recording, output order never
    drifts with completion order; thermal caution in the parallelism
    paragraph of the module docstring)."""
    records = {}
    if not args.fresh and os.path.exists(args.out):
        with io.open(args.out, "r", encoding="utf-8") as fh:
            records = json.load(fh).get("records", {})
    if args.jobs > 1:
        return _run_batch_parallel(cands, src_dir, world_dir, logdir, args,
                                   records)
    skipped, probes = 0, 0
    for name, md5_decl, red_count in cands:
        prev = records.get(name)
        if prev is not None and prev.get("md5") == md5_decl and not args.fresh:
            skipped += 1
            print("SKIP(done) %s rc=%s verdict=%s"
                  % (name, prev.get("rc"), prev.get("verdict")))
            continue
        rec = probe_one(name, src_dir, world_dir, logdir, args.rocq_cmd,
                        args.guard, args.guard_reg, args.guard_front,
                        args.guard_mid, args.guard_maxwait, args.timeout,
                        args.ulimit_stack)
        rec["red_count"] = red_count
        rec["md5_match"] = (md5_decl == rec["md5"]) if rec["md5"] else None
        if rec["rc"] == 0:
            rec["verdict"] = verdict_of_rc(0, red_count)
        records[name] = rec
        probes += 1
        print("PROBE %-42s rc=%s verdict=%s%s"
              % (name, rec["rc"], rec["verdict"],
                 (" RED: " + rec["red"]) if rec["red"] else ""))
        # incremental per-candidate ledger write (resumable after an
        # interruption)
        save_ledger(args.out, args, records)
    return records, skipped, probes


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """Embedded frozen vector groups (temporary directory + stub probe; zero
    real compiles, zero real repository touches): rc three-way split
    (`BORN-CLEAN`/`RED-MISSING_LIB`/`WASHABLE`) + resume idempotence
    byte-identical ledger + --jobs parallel vectors (K=1 differential
    comparison byte-identical to the default serial output / K=3 result
    equivalence with order unchanged, canned stub injected into the parallel
    path / --jobs 0 rc=2) + four CLI codes."""
    import tempfile

    def run(args):
        import subprocess
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    tmp = tempfile.mkdtemp(prefix="rocqwash_probe_self_")
    try:
        src = os.path.join(tmp, "src")
        world = os.path.join(tmp, "world")
        logdir = os.path.join(tmp, "logs")
        for d in (src, world, logdir):
            os.makedirs(d)
        with io.open(os.path.join(src, "PassMe.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma ok : True.\n")
        with io.open(os.path.join(src, "RedMe.v"), "w", encoding="utf-8") as fh:
            fh.write("Require Import Nope.\n")
        with io.open(os.path.join(src, "Third.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma Third_ok : True.\n")
        stub = os.path.join(tmp, "stub.sh")
        with io.open(stub, "w", encoding="utf-8") as fh:
            fh.write('#!/bin/bash\ncase "$1" in PassMe*|Third*) exit 0;; *)\n'
                     'echo "Error: Unable to locate library | Nope (while'
                     ' searching for a .vos file)." >&2; exit 1;; esac\n')
        os.chmod(stub, 0o755)
        cands = os.path.join(tmp, "cands.tsv")
        with io.open(cands, "w", encoding="utf-8") as fh:
            fh.write("件名\tmd5\tRED\nPassMe\t%s\t0\nRedMe\t%s\t3\nThird\t%s\t2\n"
                     % (md5_of(os.path.join(src, "PassMe.v")),
                        md5_of(os.path.join(src, "RedMe.v")),
                        md5_of(os.path.join(src, "Third.v"))))
        led = os.path.join(tmp, "ledger.json")
        tpl = stub + " {name}.v"
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl])
        assert p.returncode == 0, p.stdout
        acc = json.load(io.open(led, encoding="utf-8"))
        assert acc["records"]["PassMe"]["verdict"] == "BORN-CLEAN", acc
        assert acc["records"]["RedMe"]["verdict"] == "RED-MISSING_LIB", acc
        assert acc["records"]["RedMe"]["missing"] == "Nope", acc
        # resume idempotence: rerun the same manifest → SKIP lines and a
        # byte-identical ledger
        before = io.open(led, "rb").read()
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl])
        assert p.returncode == 0 and "SKIP(done)" in p.stdout, p.stdout
        assert io.open(led, "rb").read() == before, "ledger byte drift on rerun is a violation"
        # --jobs parallel vectors (canned stub injected into the parallel path,
        # zero real compiles): explicit K=1 differential comparison against the
        # default serial output → byte-identical (default = current behavior,
        # zero-drift proof); K=3 result equivalence (parallel completion order
        # never changes the ledger bytes; record order stays dictionary order;
        # the three-way verdict split merges into one pool)
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl,
                 "--jobs", "1", "--fresh"])
        assert p.returncode == 0, p.stdout
        assert io.open(led, "rb").read() == before, \
            "K=1 differential comparison against the default serial output drifted byte-wise, a violation"
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl,
                 "--jobs", "3", "--fresh"])
        assert p.returncode == 0, p.stdout
        assert io.open(led, "rb").read() == before, \
            "K=3 result equivalence broken (ledger byte drift means completion order invaded output order)"
        acc3 = json.load(io.open(led, encoding="utf-8"))
        assert acc3["records"]["Third"]["verdict"] == "WASHABLE" \
            and acc3["records"]["Third"]["red_count"] == 2 \
            and acc3["records"]["Third"]["md5_match"] is True, \
            "K=3 merged pool missing the WASHABLE arm of the three-way split: %r" % acc3["records"]["Third"]
        assert acc3["records"]["PassMe"]["verdict"] == "BORN-CLEAN" \
            and acc3["records"]["RedMe"]["verdict"] == "RED-MISSING_LIB", acc3
        # --jobs < 1 is a usage error, rc=2 (fail-loud)
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", os.path.join(tmp, "j0.json"), "--logdir", logdir,
                 "--jobs", "0"])
        assert p.returncode == 2, "--jobs 0 must exit rc=2, got %d" % p.returncode
        # four CLI codes
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown argument must exit rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing arguments must exit rc=2, got %d" % p.returncode
        p = run(["--candidates", os.path.join(tmp, "nope.tsv"), "--src", src,
                 "--world", world, "--out", os.path.join(tmp, "x.json"),
                 "--logdir", logdir])
        assert p.returncode == 9, "missing manifest must exit rc=9, got %d" % p.returncode
        print("PROBE-ENGINE-SELFTEST PASS: rc three-way split (BORN-CLEAN/"
              "RED-MISSING_LIB/WASHABLE merged pool)/missing-library capture/"
              "resume idempotence with byte-identical ledger/--jobs K=1 "
              "differential comparison byte-identical to the default serial "
              "output + K=3 result equivalence with order unchanged (canned "
              "stub parallel path) + --jobs 0 rc=2/four CLI codes — six "
              "criteria all pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="Batch closure-compatibility probe engine: "
                               "candidate manifest x world directory -> "
                               "per-candidate cp -> rocq c real exit code -> "
                               "rc-split ledger (schema rocqwash-probe-ledger/1, "
                               "resume idempotent)")
    ap.add_argument("--candidates", default=None, metavar="FILE",
                    help="candidate manifest TSV (required columns 件名/md5, "
                         "optional column RED = statement-face RED line count)")
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="source tree root (candidate <name>.v files are taken from here)")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="world directory (seeded .vo closure; probe cwd)")
    ap.add_argument("--out", default=None, metavar="FILE", help="ledger JSON output")
    ap.add_argument("--logdir", default=None, metavar="DIR",
                    help="probe logs + post-probe artifact evidence directory (defaults to --out.logs)")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd",
                    default=DEFAULT_ROCQ_CMD, metavar="TPL",
                    help="probe command template (contains the {name} placeholder, default 'rocq c -Q . \"\" {name}.v')")
    ap.add_argument("--guard", default=None, metavar="PATH",
                    help="cpu_guard.sh path (when given, every probe runs wrapped through it; required for real compiles)")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_probe_engine", metavar="DIR")
    ap.add_argument("--guard-front", dest="guard_front", type=int, default=0)
    ap.add_argument("--guard-mid", dest="guard_mid", type=int, default=1)
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int, default=600)
    ap.add_argument("--timeout", type=int, default=1500,
                    help="per-candidate subprocess timeout seconds (on expiry rc=124 TIMEOUT)")
    ap.add_argument("--ulimit-stack", dest="ulimit_stack", type=int, default=None,
                    help="inner ulimit -s value (unset by default; canonical-machine convention 65532)")
    ap.add_argument("--jobs", type=int, default=1, metavar="K",
                    help="parallel shard degree (default 1 = per-candidate serial, "
                         "zero drift; K > 1 runs a ThreadPool in parallel with "
                         "dictionary-order recording; real compiles still run "
                         "wrapped through --guard one by one; with --guard given, "
                         "K <= 2 advised for thermal reasons, caller decides)")
    ap.add_argument("--fresh", action="store_true",
                    help="re-probe from scratch (default resume: existing records with the same md5 are skipped)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.jobs < 1:
        print("FAIL-LOUD: --jobs must be >= 1, got %d" % args.jobs, file=sys.stderr)
        sys.exit(2)
    for req, val in (("candidates", args.candidates), ("src", args.src),
                     ("world", args.world), ("out", args.out)):
        if not val:
            print("FAIL-LOUD: --%s is required (except --selftest)" % req, file=sys.stderr)
            sys.exit(2)
    # Clean mode: the canonical face is the default --rocq-cmd template
    # (the PATH rocq toolchain); report and refuse. An explicit --rocq-cmd
    # override (the stub selftest driver, zero real compiles) is a
    # caller-owned face and stays available, as does --selftest.
    if _clean_mode() and args.rocq_cmd == DEFAULT_ROCQ_CMD:
        print("requires canonical environment: a rocq toolchain for real "
              "compile probes (default --rocq-cmd %r); pass an explicit "
              "--rocq-cmd stub or use --selftest for the zero-compile face"
              % DEFAULT_ROCQ_CMD)
        sys.exit(9)
    for label, val in (("candidates", args.candidates), ("src", args.src),
                       ("world", args.world)):
        if not os.path.exists(val):
            print("FAIL-LOUD: --%s path missing: %s" % (label, val), file=sys.stderr)
            sys.exit(9)
    if args.guard and not os.path.exists(args.guard):
        print("FAIL-LOUD: --guard path missing: %s" % args.guard, file=sys.stderr)
        sys.exit(9)
    logdir = args.logdir or (args.out + ".logs")
    os.makedirs(logdir, exist_ok=True)
    if args.jobs > 1:
        print("ADVISE(thermal): --jobs %d > 1 means multiple concurrent "
              "rocqworker processes on this machine and a higher thermal load "
              "(with --guard, K <= 2 advised; advisory, not enforced — the "
              "caller decides)" % args.jobs)

    try:
        cands = load_candidates(args.candidates)
    except ValueError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    records, skipped, probes = run_batch(cands, args.src, args.world,
                                         logdir, args)
    n_wash = sum(1 for r in records.values() if r.get("verdict") == "WASHABLE")
    n_clean = sum(1 for r in records.values() if r.get("verdict") == "BORN-CLEAN")
    n_rc1 = sum(1 for r in records.values() if r.get("rc") == 1)
    n_other = len(records) - n_wash - n_clean - n_rc1
    drift = sorted(n for n, r in records.items() if r.get("md5_match") is False)
    print("== PROBE-ENGINE DONE: candidates %d (probed this run %d / "
          "resume-skipped %d) ==" % (len(cands), probes, skipped))
    print("verdict summary: WASHABLE=%d BORN-CLEAN=%d rc1=%d other=%d"
          % (n_wash, n_clean, n_rc1, n_other))
    if drift:
        print("MD5-DRIFT candidates (manifest md5 != current source md5): %s"
              % ",".join(drift))
    print("ledger -> %s" % args.out)
    sys.exit(0)


if __name__ == "__main__":
    main()
