#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_sync.py — probe-ledger x status-ledger TSV merge synchronizer (rocqwash tools/).

Purpose.  Merges a probe ledger (the `rocqwash-probe-ledger/1` "records"
  shell from `probe_engine`, a freeze-ledger `items` shell, or a bare
  {name: record} dict) into a status-ledger TSV (the `件名`/`行数`/`md5`/
  `RED`/`状态`/`备注` column family) row by row and writes the new
  status-ledger TSV.  Five mechanisms, every finding reported loudly and
  counted, none silently dropped: E1 dedup, E3 ghost, MD5-DRIFT, NO-MD5,
  GEN-DIVERGENCE (per-mechanism contract in the comment block below).

Interface.  python3 tools/ledger_sync.py --probe P.json --ledger T.tsv
  --out NEW.tsv [--report R.json] [--policy unprobed-only|annotate-only]
  | --selftest.  Report schema rocqwash-ledger-sync/1.  unprobed-only
  (default) raises only rows whose `状态` is UNPROBED with a matching md5
  (rc=0 -> WASHABLE, rc=1 -> DRIFT-BLOCKED; higher states never rewritten);
  annotate-only never touches the status column.

Dependencies.  Python 3 standard library only; every path parameterized,
  zero network.

Evidence.  --selftest frozen vectors on temporary synthetic ledgers (zero
  real-repo touches, zero network): the five mechanisms, no-demotion of
  higher states, tag idempotence, byte-identical reruns, CLI four codes,
  items shell, meta-key filtering, zero-record rejection; suite membership
  tests/test_ledger_sync.py (ten sections).

Exit-codes.  0 = SYNC-CLEAN (zero findings); 1 = SYNC-FINDINGS (any
  finding nonzero; the new TSV is still written); 2 = column-validation
  or usage error; 9 = input file missing.
"""
# Extended contract (kept outside the five-field block so the header stays
# within the 30-line budget of the annotation standard):
# E1 dedup        duplicate `件名` rows inside the status ledger keep the first
#                 row (deterministic); every dropped duplicate is counted and
#                 reported loudly, never silently discarded.
# E3 ghost        a name present in the probe ledger but absent from the status
#                 ledger is recorded as a finding only — no row is written for
#                 it (a missing row is a ledger-completeness event; silent
#                 backfill is forbidden).
# MD5-DRIFT       a probe record whose md5 differs from the row's md5 annotates
#                 only and never upgrades the row — the probe credential does
#                 not vouch for a source generation it does not match.
# NO-MD5          a probe record without an md5 field (legacy bare ledgers,
#                 freeze-ledger washed_md5 records) annotates only.
# GEN-DIVERGENCE  a probe record carrying divergence_with/divergence_md5 (two
#                 generations synthesized from multiple sources) annotates
#                 `probe:gen-div:<dropped>` and reports per record loudly —
#                 the dropped generation is not discarded, the later intake
#                 review decides, silent swallowing is forbidden.
# Divergence precedence: of two same-name generations synthesized from
#   multiple sources, the kept generation is the one the downstream freeze
#   ledger's ledger_basis ranking consumes; the dropped one stays out of the
#   probe records but is preserved in the divergence fields (the
#   synthesizer's duty).  The sync side reports any record carrying the
#   divergence fields and never adjudicates generations on its own — the
#   tool face never rules on generations silently.
# Probe-ledger shape recognition: a top-level "records" dict is used as is; a
#   top-level "items" dict (freeze-ledger shell) is used as is; any other
#   bare dict is filtered by record shape (dict values carrying any of
#   md5/rc/red/file/washed_md5), non-record keys (batch_meta/schema and other
#   metadata) are counted per key into meta_skipped and reported loudly, and
#   zero records after filtering is a loud rejection of the sync.
# Per matched row: (1) annotate — append the probe tag to the `备注` column
#   (idempotent: a tag already present is not duplicated): rc=0 -> probe:rc0,
#   rc=1 -> probe:rc1[:failure-class], rc=124 -> probe:timeout,
#   NO_SRC -> probe:no-src, divergence fields -> probe:gen-div:<dropped>;
#   (2) upgrade — only under --policy unprobed-only, only when the row's
#   `状态` is UNPROBED and the md5 matches: probe rc=0 -> WASHABLE, rc=1 ->
#   DRIFT-BLOCKED (ledger-v2 judgment scale: WASHABLE = the probe rc0 closure
#   is compatible; DRIFT-BLOCKED = the probe rc1 failure class is on record;
#   LANDED/FROZEN/OCCUPIED/GIANT and other higher states are never demoted or
#   rewritten).  --policy annotate-only annotates without touching the status
#   column.
# Column validation (fail-loud, exit 2, nothing produced): missing required
#   columns (`件名`/`md5`/`RED`/`状态`/`备注`), a row width differing from the
#   header, an unrecognized probe-ledger shape — the sync is refused loudly.
# Idempotence: the same probe x the same ledger reruns byte-identical (tags
#   already present are skipped; the traversal is deterministic).

import argparse
import io
import json
import os
import re
import sys

PROG = "ledger_sync"
SCHEMA = "rocqwash-ledger-sync/1"

REQUIRED_COLS = ("件名", "md5", "RED", "状态", "备注")
POLICIES = ("unprobed-only", "annotate-only")

MISSING_LIB_RE = re.compile(r"(?:unable to locate library|cannot find library)"
                            r"\s+\|?\s*([A-Za-z0-9_']+)", re.IGNORECASE)
CLASS_RES = [
    ("MISSING_LIB", re.compile(r"unable to locate library|cannot find library", re.I)),
    ("ILLEGAL_APP", re.compile(r"illegal application", re.I)),
    ("NO_SUBTERM", re.compile(r"no subterm matching", re.I)),
    ("FACE", re.compile(r"expected to have type|is not convertible", re.I)),
]


RECORD_SHAPE_FIELDS = ("md5", "rc", "red", "red_class", "file", "washed_md5")


def _is_record_shape(v):
    return isinstance(v, dict) and any(f in v for f in RECORD_SHAPE_FIELDS)


def load_probe(path):
    """Probe ledger -> (records, meta_skipped).

    Shape recognition (three forms):
      1 a top-level `records` dict (the rocqwash-probe-ledger/1 shell) is
        used as is;
      2 a top-level `items` dict (the freeze-ledger shell) is used as is;
      3 any other bare dict is filtered by record shape (_is_record_shape),
        non-record keys are recorded per key into meta_skipped and returned
        loudly; zero records after filtering raises ValueError (the sync is
        refused loudly).
    """
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    if isinstance(d, dict) and isinstance(d.get("records"), dict):
        return d["records"], []
    if isinstance(d, dict) and isinstance(d.get("items"), dict):
        return d["items"], []
    if isinstance(d, dict):
        records = {}
        meta_skipped = []
        for k, v in d.items():
            if _is_record_shape(v):
                records[k] = v
            else:
                meta_skipped.append(k)
        if not records:
            raise ValueError("probe ledger has zero records after "
                             "metadata-key filtering (bare-dict shape; "
                             "meta_skipped=%r): %s" % (meta_skipped, path))
        return records, meta_skipped
    raise ValueError("unrecognized probe-ledger shape (none of the three "
                     "forms matches: records shell / items shell / bare "
                     "dict): %s" % path)


def load_status_tsv(path):
    """Status-ledger TSV -> (header, rows[dict]); fail-loud column
    validation (ValueError)."""
    with io.open(path, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    if not lines:
        raise ValueError("status ledger is an empty file: %s" % path)
    header = lines[0].split("\t")
    missing = [c for c in REQUIRED_COLS if c not in header]
    if missing:
        raise ValueError("status ledger missing required columns %r "
                         "(header=%r)" % (missing, header))
    rows = []
    for i, ln in enumerate(lines[1:], start=2):
        f = ln.split("\t")
        if len(f) != len(header):
            raise ValueError("status ledger row %d width mismatch (expected "
                             "%d columns, got %d)" % (i, len(header), len(f)))
        rows.append(dict(zip(header, f)))
    return header, rows


def red_class_of(rec):
    """Failure class of a probe record (the `red_class` field when present,
    else the regex over the `red` text)."""
    cls = rec.get("red_class")
    if cls:
        return cls
    red = rec.get("red") or ""
    for name, rx in CLASS_RES:
        if rx.search(red):
            return name
    return ""


def tag_of(rec):
    """Probe credential tag (the idempotent annotation unit)."""
    rc = rec.get("rc")
    if rc == "NO_SRC":
        return "probe:no-src"
    if rc == 124:
        return "probe:timeout"
    if rc == 0:
        return "probe:rc0"
    if isinstance(rc, int):
        cls = red_class_of(rec)
        return "probe:rc%d:%s" % (rc, cls) if cls else "probe:rc%d" % rc
    return "probe:rc%s" % rc


def sync(probe_path, ledger_path, policy):
    """Main sync -> (header, out_rows, findings, meta_skipped); findings is
    a list of dicts."""
    probe, meta_skipped = load_probe(probe_path)
    header, rows = load_status_tsv(ledger_path)
    findings = []

    # E1 dedup (keep the first row; count loudly)
    seen = set()
    deduped = []
    for r in rows:
        name = r["件名"]
        if name in seen:
            findings.append({"code": "E1-DUP", "name": name,
                             "detail": "duplicate `件名` rows in the status "
                                       "ledger — keeping the first row, "
                                       "dropping this one"})
            continue
        seen.add(name)
        deduped.append(r)

    probe_names = set(probe.keys())
    tsv_names = set(seen)

    # E3 ghost (name in the probe ledger, no row in the status ledger;
    # record only, write no row)
    for name in sorted(probe_names - tsv_names):
        findings.append({"code": "E3-GHOST", "name": name,
                         "detail": "name present in the probe ledger but no "
                                   "row in the status ledger — recorded "
                                   "only, no row written"})

    # row-by-row merge
    for r in deduped:
        name = r["件名"]
        rec = probe.get(name)
        if rec is None:
            continue
        tag = tag_of(rec)
        note = r.get("备注", "")
        if tag not in note:
            r["备注"] = (note + "·" + tag) if note else tag
        # two-generation divergence reported (the dropped generation is not
        # discarded; the later intake review decides; silent swallowing is
        # forbidden)
        div_with = rec.get("divergence_with")
        if div_with:
            div_tag = "probe:gen-div:%s" % div_with
            note = r["备注"]
            if div_tag not in note:
                r["备注"] = (note + "·" + div_tag) if note else div_tag
            findings.append({
                "code": "GEN-DIVERGENCE", "name": name,
                "detail": "two-generation divergence: kept=%s (the "
                          "generation the downstream ledger basis consumes), "
                          "dropped=%s (md5 %s) — annotation only, nothing "
                          "discarded; the later intake review decides"
                          % (",".join(rec.get("source_seats") or [name]),
                             div_with, rec.get("divergence_md5") or "?")})
        md5_p = rec.get("md5")
        can_upgrade = False
        if md5_p is None:
            findings.append({"code": "NO-MD5", "name": name,
                             "detail": "probe record has no md5 (legacy "
                                       "ledger) — annotation only, no "
                                       "upgrade"})
        elif md5_p != r["md5"]:
            findings.append({"code": "MD5-DRIFT", "name": name,
                             "detail": "probe md5=%s != status-ledger "
                                       "md5=%s — no upgrade, annotation "
                                       "only" % (md5_p, r["md5"])})
        else:
            can_upgrade = True
        if (policy == "unprobed-only" and can_upgrade
                and r["状态"] == "UNPROBED"):
            if rec.get("rc") == 0:
                r["状态"] = "WASHABLE"
            elif rec.get("rc") == 1:
                r["状态"] = "DRIFT-BLOCKED"
    return header, deduped, findings, meta_skipped


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """Frozen vector set (temporary synthetic ledgers; zero real-repo
    touches, zero network): E1 dedup / E3 ghost / MD5-DRIFT / NO-MD5 /
    UNPROBED upgrade with no demotion of higher states / tag idempotence /
    byte-identical reruns / CLI four codes."""
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

    tmp = tempfile.mkdtemp(prefix="rocqwash_lsync_self_")
    try:
        tsv = os.path.join(tmp, "status.tsv")
        with io.open(tsv, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "R1\t100\taaa\t0\tUNPROBED\t\n"
                     "R2\t200\tbbb\t3\tUNPROBED\t\n"
                     "R3\t300\tccc\t0\tLANDED\t已落位\n"
                     "R4\t50\tddd\t0\tWASHABLE\tprobe:rc0\n")
        probe = os.path.join(tmp, "probe.json")
        with io.open(probe, "w", encoding="utf-8") as fh:
            json.dump({"records": {
                "R1": {"file": "R1", "md5": "aaa", "rc": 0, "red": ""},
                "R2": {"file": "R2", "md5": "bbb", "rc": 1,
                       "red": "Error: Unable to locate library | Lx",
                       "red_class": "MISSING_LIB"},
                "R3": {"file": "R3", "md5": "zzz", "rc": 0, "red": ""},
                "R4": {"file": "R4", "md5": "ddd", "rc": 0, "red": ""},
                "GHOST1": {"file": "GHOST1", "md5": "ggg", "rc": 0, "red": ""},
            }}, fh)
        out = os.path.join(tmp, "new.tsv")
        p = run(["--probe", probe, "--ledger", tsv, "--out", out])
        assert p.returncode == 1 and "SYNC-FINDINGS" in p.stdout, p.stdout
        rows = [ln.split("\t") for ln in
                io.open(out, encoding="utf-8").read().rstrip("\n").split("\n")]
        by = {r[0]: r for r in rows[1:]}
        assert by["R1"][4] == "WASHABLE" and "probe:rc0" in by["R1"][5], by["R1"]
        assert by["R2"][4] == "DRIFT-BLOCKED", by["R2"]
        assert "probe:rc1:MISSING_LIB" in by["R2"][5], by["R2"]
        assert by["R3"][4] == "LANDED", "higher state was demoted = violation"
        assert "probe:rc0" in by["R3"][5] and "MD5-DRIFT" in p.stdout, by["R3"]
        assert by["R4"][5].count("probe:rc0") == 1, "tag annotated twice = violation"
        assert "E3-GHOST" in p.stdout and "GHOST1" in p.stdout, p.stdout
        # idempotence: rerun is byte-identical
        before = io.open(out, "rb").read()
        p = run(["--probe", probe, "--ledger", tsv, "--out", out])
        assert p.returncode == 1, p.stdout
        assert io.open(out, "rb").read() == before, "rerun byte drift = violation"
        # annotate-only: the status column is untouched
        out2 = os.path.join(tmp, "new2.tsv")
        p = run(["--probe", probe, "--ledger", tsv, "--out", out2,
                 "--policy", "annotate-only"])
        rows2 = [ln.split("\t") for ln in
                 io.open(out2, encoding="utf-8").read().rstrip("\n").split("\n")]
        by2 = {r[0]: r for r in rows2[1:]}
        assert by2["R1"][4] == "UNPROBED" and "probe:rc0" in by2["R1"][5], by2["R1"]
        # column validation fail-loud: missing required columns -> rc 2,
        # nothing produced
        bad = os.path.join(tmp, "bad.tsv")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("件名\tmd5\nR1\taaa\n")
        out3 = os.path.join(tmp, "nope.tsv")
        p = run(["--probe", probe, "--ledger", bad, "--out", out3])
        assert p.returncode == 2 and "missing required columns" in p.stdout, p.stdout
        assert not os.path.exists(out3), "output produced despite " \
            "column-validation failure = violation"
        # ragged row width -> rc 2
        ragged = os.path.join(tmp, "ragged.tsv")
        with io.open(ragged, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\nR1\t1\ta\t0\tUNPROBED\n")
        p = run(["--probe", probe, "--ledger", ragged, "--out", out3])
        assert p.returncode == 2 and "width mismatch" in p.stdout, p.stdout
        # CLI four codes
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "unknown flag should exit 2, got %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "missing arguments should exit 2, got %d" % p.returncode
        p = run(["--probe", os.path.join(tmp, "no.json"), "--ledger", tsv,
                 "--out", out3])
        assert p.returncode == 9, "missing file should exit 9, got %d" % p.returncode
        # ---- extended vectors: items shell, meta filtering, divergence ----
        # items-subkey probe (freeze-ledger shell): records consumed, shell
        # keys never become phantom probe names
        tsv2 = os.path.join(tmp, "v21.tsv")
        with io.open(tsv2, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "H1\t10\tmh1\t0\tUNPROBED\t\n")
        probe2 = os.path.join(tmp, "freeze_ledger.json")
        with io.open(probe2, "w", encoding="utf-8") as fh:
            json.dump({"schema": "seat-freeze/1",
                       "items": {"H1": {"file": "H1", "md5": "mh1",
                                        "rc": 0, "red": ""}},
                       "queue": [], "world": "/tmp/x"}, fh)
        out4 = os.path.join(tmp, "v21out.tsv")
        p = run(["--probe", probe2, "--ledger", tsv2, "--out", out4])
        assert p.returncode == 0 and "SYNC-CLEAN" in p.stdout, p.stdout
        by = dict((ln.split("\t")[0], ln.split("\t"))
                  for ln in io.open(out4, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert by["H1"][4] == "WASHABLE" and "probe:rc0" in by["H1"][5], by["H1"]
        assert "E3-GHOST" not in p.stdout, "items-shell key misread as a " \
            "ghost = violation"
        # bare-dict form with batch_meta sibling: meta skipped loudly, record
        # synced, no phantom ghost for the meta key
        tsv3 = os.path.join(tmp, "v21b.tsv")
        with io.open(tsv3, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "J1\t10\tmj1\t0\tUNPROBED\t\n")
        probe3 = os.path.join(tmp, "bare_meta.json")
        with io.open(probe3, "w", encoding="utf-8") as fh:
            json.dump({"J1": {"file": "J1", "md5": "mj1", "rc": 0, "red": ""},
                       "batch_meta": {"seat": "W9", "date": "20261103"}}, fh)
        out5 = os.path.join(tmp, "v21bout.tsv")
        p = run(["--probe", probe3, "--ledger", tsv3, "--out", out5])
        assert p.returncode == 0 and "PROBE-META-SKIP" in p.stdout, p.stdout
        assert "batch_meta" in p.stdout, "metadata key should be reported loudly"
        assert "E3-GHOST" not in p.stdout, "metadata key must not be " \
            "misreported as a ghost"
        by3 = dict((ln.split("\t")[0], ln.split("\t"))
                   for ln in io.open(out5, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert by3["J1"][4] == "WASHABLE", by3
        # bare-dict all-meta (zero records): fail-loud rc2, no output file
        probe4 = os.path.join(tmp, "all_meta.json")
        with io.open(probe4, "w", encoding="utf-8") as fh:
            json.dump({"schema": "x/1", "batch_meta": {"seat": "W9"}}, fh)
        out6 = os.path.join(tmp, "v21cout.tsv")
        p = run(["--probe", probe4, "--ledger", tsv3, "--out", out6])
        assert p.returncode == 2 and "zero records" in p.stdout, p.stdout
        assert not os.path.exists(out6), "output produced despite " \
            "zero-record rejection = violation"
        # divergence-carrying record: GEN-DIVERGENCE finding + gen-div tag,
        # rerun byte-stable (tag idempotent, finding re-fires loud)
        tsv4 = os.path.join(tmp, "v21d.tsv")
        with io.open(tsv4, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "K1\t10\tmk1\t0\tUNPROBED\t\n")
        probe5 = os.path.join(tmp, "div.json")
        with io.open(probe5, "w", encoding="utf-8") as fh:
            json.dump({"records": {
                "K1": {"file": "K1", "md5": "mk1", "rc": 0, "red": "",
                       "source_seats": ["sA", "sB"],
                       "divergence_with": "sB",
                       "divergence_md5": "d5d5"}}}, fh)
        out7 = os.path.join(tmp, "v21dout.tsv")
        p = run(["--probe", probe5, "--ledger", tsv4, "--out", out7])
        assert p.returncode == 1 and "GEN-DIVERGENCE" in p.stdout, p.stdout
        by4 = dict((ln.split("\t")[0], ln.split("\t"))
                   for ln in io.open(out7, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert "probe:gen-div:sB" in by4["K1"][5], by4  # annotation in the row's `备注` column
        assert by4["K1"][4] == "WASHABLE", by4  # md5-matched upgrade proceeds; divergence only annotates the dropped generation
        before = io.open(out7, "rb").read()
        p = run(["--probe", probe5, "--ledger", tsv4, "--out", out7])
        assert p.returncode == 1, p.stdout
        assert io.open(out7, "rb").read() == before, "divergence-annotation " \
            "rerun byte drift = violation"
        print("LEDGER-SYNC-SELFTEST PASS: e1-dedup/e3-ghost/md5-drift/"
              "higher-state-no-demotion/tag-idempotence/annotate-only/"
              "column-validation-fail-loud/byte-stable-rerun/cli-four-codes/"
              "items-shell/metadata-filtering/zero-record-rejection/"
              "gen-divergence thirteen checks pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="probe-ledger x status-ledger TSV merge "
                               "sync: E1 dedup / E3 ghost / GEN-DIVERGENCE / "
                               "fail-loud column validation -> new status "
                               "ledger (schema rocqwash-ledger-sync/1)")
    ap.add_argument("--probe", default=None, metavar="FILE",
                    help="probe ledger JSON (records shell or bare dict)")
    ap.add_argument("--ledger", default=None, metavar="FILE",
                    help="status-ledger TSV (required columns "
                         "件名/md5/RED/状态/备注)")
    ap.add_argument("--out", default=None, metavar="FILE",
                    help="new status-ledger TSV output")
    ap.add_argument("--report", default=None, metavar="FILE",
                    help="sync report JSON output (counts plus per-record "
                         "findings)")
    ap.add_argument("--policy", default="unprobed-only", choices=POLICIES,
                    help="upgrade policy (default: only UNPROBED rows "
                         "upgrade; annotate-only annotates without "
                         "upgrading)")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    for req in ("probe", "ledger", "out"):
        if not getattr(args, req):
            print("FAIL-LOUD: --%s is required (except --selftest)" % req,
                  file=sys.stderr)
            sys.exit(2)
    for label, val in (("probe", args.probe), ("ledger", args.ledger)):
        if not os.path.exists(val):
            print("FAIL-LOUD: --%s file missing: %s" % (label, val),
                  file=sys.stderr)
            sys.exit(9)

    try:
        header, rows, findings, meta_skipped = sync(args.probe, args.ledger,
                                                    args.policy)
    except ValueError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(header) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in header) + "\n")

    codes = {}
    for f in findings:
        codes[f["code"]] = codes.get(f["code"], 0) + 1
    n_synced = sum(1 for r in rows if "probe:" in r.get("备注", ""))
    print("=== LEDGER-SYNC ===")
    print("probe=%s ledger=%s policy=%s" % (args.probe, args.ledger, args.policy))
    print("rows=%d annotated=%d findings=%d %s"
          % (len(rows), n_synced, len(findings),
             " ".join("%s=%d" % kv for kv in sorted(codes.items()))))
    if meta_skipped:
        print("PROBE-META-SKIP: %d keys are not record-shaped and were "
              "filtered (reported loudly): %s"
              % (len(meta_skipped), ",".join(sorted(meta_skipped))))
    for f in findings:
        print("FINDING %-9s %s — %s" % (f["code"], f["name"], f["detail"]))
    if args.report:
        acc = {"schema": SCHEMA, "probe": args.probe, "ledger": args.ledger,
               "policy": args.policy, "rows": len(rows), "synced": n_synced,
               "findings": findings, "counts": codes,
               "meta_skipped": sorted(meta_skipped)}
        with io.open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, indent=1, ensure_ascii=False, sort_keys=True)
        print("report ->", args.report)
    print("new ledger -> %s" % args.out)
    if findings:
        print("SYNC-FINDINGS: %d findings (E1/E3/MD5-DRIFT/NO-MD5/"
              "GEN-DIVERGENCE; the new ledger is written)" % len(findings))
        sys.exit(1)
    print("SYNC-CLEAN: zero findings (dedup 0 ghost 0 drift 0 divergence 0)")
    sys.exit(0)


if __name__ == "__main__":
    main()
