#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""netname_normalize.py - the .v.v double-suffix clean-name normalizer (rocqwash tools/).

Purpose.  A `.v` file mis-saved with the doubled `.v.v` suffix (editor append or
  script concatenation) makes the Require face resolve nothing under the clean
  name, a false gap in the dependency net.  This tool walks the input directory,
  collects every `*.v.v` file and emits the map `<clean>.v.v -> <clean>.v` (one
  strip per run: `X.v.v.v` -> `X.v.v`; rerun strips again; never silently iterated).

Interface.  python3 tools/netname_normalize.py --dir <world-dir> [--apply]
  [--map out.tsv] [--json out.json] | --selftest.  Dry run (default) prints the
  map and findings and writes zero bytes (write surfaces: explicit --map/--json
  report paths only); --apply renames via os.rename with an md5 before-and-after
  check (a rename changes no bytes).  Findings (any is failing, exit 1):
  PENDING `.v.v` files await normalization; COLLIDE target `<clean>.v` already on
  disk (refuse, no overwrite, manual adjudication); DEGENERATE stripped name
  empty (file name exactly `.v.v`); MD5-MISMATCH md5 differs across the rename
  (unreachable through os.rename, fail loud).

Dependencies.  Python 3 standard library only (argparse, hashlib, io, json, os,
  sys); zero network, zero compiles; --selftest drives temp-directory fixtures.

Evidence.  --selftest vectors: dry-run zero writes; apply rename + md5 verify;
  COLLIDE refusal; DEGENERATE; clean world CLEAN; CLI codes (help 0, unknown
  flag 2, missing --dir 2, --dir absent 9); --map/--json reports interlock;
  one-strip-per-run form.  Suite: tests/test_netname_normalize.py (nine sections).

Exit-codes.  0 = CLEAN (no `.v.v` files) or APPLIED (all renamed, md5 verified);
  1 = failing (PENDING / COLLIDE / MD5-MISMATCH, or pending entries in a dry run);
  2 = usage error (help 0, unknown flag 2, missing --dir flag 2); 9 = --dir absent.
"""
import argparse
import hashlib
import io
import json
import os
import sys

PROG = "netname_normalize"
DOUBLE_SUFFIX = ".v.v"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_entry(rel):
    """Relative path (os.sep normalized to "/") -> (clean_name, src_rel,
    dst_rel), or None for a non `.v.v` file.

    `X.v.v` gives clean_name=X, dst=X.v; `sub/X.v.v` gives
    clean_name=sub/X, dst=sub/X.v.
    """
    rel = rel.replace(os.sep, "/")
    if not rel.endswith(DOUBLE_SUFFIX):
        return None
    netname = rel[: -len(DOUBLE_SUFFIX)]
    return (netname, rel, netname + ".v")


def scan_world(world_dir):
    """Full index of world_dir -> a sorted list of (clean_name, src_rel,
    dst_rel) tuples (os.walk, "/"-normalized paths, stable sort by source
    path)."""
    out = []
    for dirpath, _dirs, fnames in os.walk(world_dir):
        for fn in fnames:
            rel = os.path.relpath(os.path.join(dirpath, fn), world_dir)
            e = normalize_entry(rel)
            if e is not None:
                out.append(e)
    out.sort(key=lambda t: t[1])
    return out


def audit(world_dir):
    """Clean-name audit: scan `.v.v` files into a (entry, finding) record
    list.

    COLLIDE = the target `<clean>.v` already exists on disk (refuse, no
    overwrite); DEGENERATE = the stripped clean name is empty.  Returns
    (entries, findings); entries are the legitimately renamable files,
    findings is a list of dicts.
    """
    entries = []
    findings = []
    for netname, src, dst in scan_world(world_dir):
        if netname == "":
            findings.append({"code": "DEGENERATE", "name": src,
                             "detail": "clean name stripped empty (the file name is exactly .v.v) - skipped, no name"})
            continue
        if os.path.exists(os.path.join(world_dir, dst)):
            findings.append({"code": "COLLIDE", "name": netname,
                             "detail": "target %s already exists on disk - refuse to rename, no overwrite (manual adjudication)" % dst})
            continue
        entries.append((netname, src, dst))
    return entries, findings


def apply_renames(world_dir, entries):
    """--apply disk phase: rename each entry, then verify the md5 before and
    after.  Returns (applied, findings)."""
    applied = []
    findings = []
    for netname, src, dst in entries:
        sp = os.path.join(world_dir, src)
        dp = os.path.join(world_dir, dst)
        if os.path.exists(dp):  # the target appeared during the rename window (concurrent write) - still refuse to overwrite
            findings.append({"code": "COLLIDE", "name": netname,
                             "detail": "target %s appeared at rename time - refuse to overwrite" % dst})
            continue
        before = md5_of(sp)
        os.rename(sp, dp)
        after = md5_of(dp)
        if before != after:
            findings.append({"code": "MD5-MISMATCH", "name": netname,
                             "detail": "%s md5 differs before and after the rename (before=%s after=%s)"
                                       % (dst, before, after)})
            continue
        applied.append((netname, src, dst, before))
    return applied, findings


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """Embedded frozen vector set (temp-directory driven): dry-run double
    verdict (zero bytes written); apply normalize + md5 verification; COLLIDE
    refuse-overwrite; DEGENERATE; clean-world CLEAN; CLI four codes (--help 0,
    unknown flag 2, missing --dir flag 2, --dir absent 9); --map/--json report
    paths.  Zero real-repository touch."""
    import shutil
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

    tmp = tempfile.mkdtemp(prefix="rocqwash_netname_self_")
    try:
        # 1. dry run default: map rows emitted, zero bytes written (files stay) -> rc 1 PENDING
        w = os.path.join(tmp, "world")
        os.makedirs(os.path.join(w, "sub"))
        body_a = "Lemma a : True.\nProof. exact I. Qed.\n"
        body_b = "Definition b := 1.\n"
        with io.open(os.path.join(w, "A.v.v"), "w", encoding="utf-8") as fh:
            fh.write(body_a)
        with io.open(os.path.join(w, "sub", "B.v.v"), "w", encoding="utf-8") as fh:
            fh.write(body_b)
        p = run(["--dir", w])
        assert p.returncode == 1 and "PENDING" in p.stdout and "2" in p.stdout, p.stdout
        assert "A.v.v -> A.v" in p.stdout and "sub/B.v.v -> sub/B.v" in p.stdout, p.stdout
        assert os.path.isfile(os.path.join(w, "A.v.v")), "dry run renamed on disk - violation"
        assert not os.path.exists(os.path.join(w, "A.v")), "dry run created the target - violation"

        # 2. --apply: normalize on disk + md5 verification -> rc 0, bytes identical
        p = run(["--dir", w, "--apply"])
        assert p.returncode == 0 and "APPLY" in p.stdout, p.stdout
        assert "VERIFY-OK" in p.stdout and "md5" in p.stdout, p.stdout
        assert not os.path.exists(os.path.join(w, "A.v.v")), p.stdout
        assert not os.path.exists(os.path.join(w, "sub", "B.v.v")), p.stdout
        with io.open(os.path.join(w, "A.v"), encoding="utf-8") as fh:
            assert fh.read() == body_a, "rename changed bytes - violation"
        with io.open(os.path.join(w, "sub", "B.v"), encoding="utf-8") as fh:
            assert fh.read() == body_b, "rename changed bytes - violation"

        # 3. COLLIDE refuses overwrite: X.v and X.v.v coexist -> rc 1, other side preserved
        w2 = os.path.join(tmp, "world2")
        os.makedirs(w2)
        with io.open(os.path.join(w2, "X.v"), "w", encoding="utf-8") as fh:
            fh.write("ORIGINAL-TARGET\n")
        with io.open(os.path.join(w2, "X.v.v"), "w", encoding="utf-8") as fh:
            fh.write("DOUBLE-SUFFIX\n")
        p = run(["--dir", w2, "--apply"])
        assert p.returncode == 1 and "COLLIDE" in p.stdout, p.stdout
        assert os.path.isfile(os.path.join(w2, "X.v.v")), "colliding file silently discarded - violation"
        with io.open(os.path.join(w2, "X.v"), encoding="utf-8") as fh:
            assert fh.read() == "ORIGINAL-TARGET\n", "target name overwritten - violation"

        # 4. DEGENERATE: the file name is exactly .v.v -> skipped, no name produced
        w3 = os.path.join(tmp, "world3")
        os.makedirs(w3)
        with io.open(os.path.join(w3, ".v.v"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        p = run(["--dir", w3])
        assert p.returncode == 1 and "DEGENERATE" in p.stdout, p.stdout

        # 5. clean world -> rc 0 CLEAN
        p = run(["--dir", tmp])  # the tmp root still holds world*/ fixtures, so scan a purpose-built clean domain
        w4 = os.path.join(tmp, "world4")
        os.makedirs(w4)
        with io.open(os.path.join(w4, "Clean.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma c : True.\nProof. exact I. Qed.\n")
        p = run(["--dir", w4])
        assert p.returncode == 0 and "NORMALIZE-CLEAN" in p.stdout, p.stdout

        # 6. CLI four codes: --help 0 / unknown flag 2 / missing --dir flag 2 / --dir absent 9
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should exit rc=2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing --dir should exit rc=2, got %d" % p.returncode
        p = run(["--dir", os.path.join(tmp, "nowhere")])
        assert p.returncode == 9, "absent dir should exit rc=9, got %d" % p.returncode

        # 7. --map/--json reports: the TSV map and the audit JSON interlock row by row
        w5 = os.path.join(tmp, "world5")
        os.makedirs(w5)
        with io.open(os.path.join(w5, "M.v.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma m : True.\nProof. exact I. Qed.\n")
        mapf = os.path.join(tmp, "map.tsv")
        jsonf = os.path.join(tmp, "acc.json")
        p = run(["--dir", w5, "--map", mapf, "--json", jsonf])
        assert p.returncode == 1, p.stdout
        with io.open(mapf, encoding="utf-8") as fh:
            rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
        assert rows == [["M.v.v", "M.v"]], repr(rows)
        with io.open(jsonf, encoding="utf-8") as fh:
            acc = json.load(fh)
        assert acc["dir"] == w5 and acc["verdict"] == "PENDING", repr(acc)
        assert [e["src"] for e in acc["entries"]] == ["M.v.v"], repr(acc)

        # 8. the X.v.v.v form: one strip per run (one layer down per run, reported as-is)
        w6 = os.path.join(tmp, "world6")
        os.makedirs(w6)
        with io.open(os.path.join(w6, "N.v.v.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma n : True.\nProof. exact I. Qed.\n")
        p = run(["--dir", w6])
        assert p.returncode == 1 and "N.v.v.v -> N.v.v" in p.stdout, p.stdout

        print("NETNAME-NORMALIZE-SELFTEST PASS: dry-run zero writes / apply normalize md5 verified / "
              "COLLIDE refuse overwrite / DEGENERATE / clean world CLEAN / CLI four codes / help 0 / "
              "map+json reports / vvv one strip per run - all eight vectors passing")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="the .v.v double-suffix clean-name normalizer: emit the "
                               "clean-name map (<clean>.v.v -> <clean>.v) plus --apply rename "
                               "on disk (md5 verified)")
    ap.add_argument("--dir", default=None, help="world directory (full os.walk index, required)")
    ap.add_argument("--apply", action="store_true",
                    help="rename on disk (default dry run: print the table only, zero writes)")
    ap.add_argument("--map", default=None, metavar="out.tsv",
                    help="clean-name map TSV report path (<src>\\t<dst>)")
    ap.add_argument("--json", default=None, help="audit JSON report path")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not args.dir:
        print("FAIL-LOUD: --dir <world-dir> is required (except --selftest)", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(args.dir):
        print("FAIL-LOUD: --dir path does not exist: %s" % args.dir, file=sys.stderr)
        sys.exit(9)

    entries, findings = audit(args.dir)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print("NETNAME-NORMALIZE dir=%s mode=%s double_suffix=%d pending=%d findings=%d"
          % (args.dir, mode, len(entries) + sum(1 for f in findings
                                                if f["code"] in ("COLLIDE", "DEGENERATE")),
             len(entries), len(findings)))
    for f in findings:
        print("FINDING %-12s %s - %s" % (f["code"], f["name"], f["detail"]))
    applied = []
    if args.apply:
        applied, af = apply_renames(args.dir, entries)
        findings.extend(af)
        for netname, src, dst, md5 in applied:
            print("RENAME %-40s -> %-40s md5=%s VERIFY-OK" % (src, dst, md5))
    else:
        for netname, src, dst in entries:
            print("MAP %s -> %s" % (src, dst))

    if findings:
        print("NORMALIZE-RED: %d findings (PENDING awaits --apply / COLLIDE needs manual "
              "adjudication / MD5-MISMATCH fail loud)" % len(findings))
        verdict = "RED" if not args.apply else "APPLY-RED"
    elif args.apply:
        print("APPLY-DONE: %d entries renamed with md5 verified before and after (a rename changes no bytes)"
              % len(applied))
        verdict = "APPLIED"
    elif entries:
        print("NORMALIZE-PENDING: %d entries await normalization (dry run writes zero bytes; "
              "--apply renames on disk)" % len(entries))
        verdict = "PENDING"
    else:
        print("NORMALIZE-CLEAN: the clean-name face is fully closed (no .v.v double-suffix files in the world)")
        verdict = "CLEAN"

    if args.map:
        with io.open(args.map, "w", encoding="utf-8", newline="\n") as fh:
            for netname, src, dst in entries:
                fh.write("%s\t%s\n" % (src, dst))
        print("map ->", args.map)
    if args.json:
        acc = {"dir": args.dir, "mode": mode, "verdict": verdict,
               "entries": [{"netname": n, "src": s, "dst": d}
                           for n, s, d in entries],
               "applied": [{"src": s, "dst": d, "md5": m}
                           for n, s, d, m in applied],
               "findings": findings}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    ok = (not findings) and (not (entries and not args.apply))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
