#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ledger_sync.py — self-test for tools/ledger_sync.py (tests/).

    Purpose.  Self-test for the probe-records-to-status-ledger merge sync,
      ten sections: (1) tool selftest, thirteen checks; (2) the CLEAN full
      chain — zero findings exit 0 (`SYNC-CLEAN`), `UNPROBED` promoted
      rc0 -> `WASHABLE` / rc1 -> `DRIFT-BLOCKED` row by row, full-field
      probe records consumed directly; (3) E1 dedup; (4) E3 ghosts;
      (5) special tags (`probe:timeout` / `probe:no-src`); (6) NO-MD5;
      (7) the `--report` JSON face; (8) CLI four codes, column validation,
      byte-identical reruns; (9) the `items` shell + `batch_meta` metadata;
      (10) wash-generation divergence (`GEN-DIVERGENCE`).

    Interface.  python3 tests/test_ledger_sync.py (no arguments); drives
      `tools/ledger_sync.py` via subprocess (`--selftest`, `--probe`,
      `--ledger`, `--out`, `--report`); prints `[n/10] <name> OK — <note>`
      per section and the `TEST-LEDGER-SYNC PASS` token.

    Dependencies.  Python 3 standard library only (importlib.util, io, json,
      os, shutil, subprocess, sys, tempfile); `tools/ledger_sync.py` resolved
      relative to this file's parent; fixtures synthesized under
      tempfile.mkdtemp, removed in finally; runs under `python3 -B` (no
      `__pycache__`); zero compilation, zero network, zero repository writes.

    Evidence.  Registered as lane `t_ledger_sync` in tests/run_tests.sh;
      asserts the sync output tokens (`SYNC-CLEAN`, `E1-DUP`, `E3-GHOST`,
      `NO-MD5`, `PROBE-META-SKIP`, `GEN-DIVERGENCE`), report JSON counts,
      byte-identical reruns.

    Exit-codes.  0 = all ten sections pass; 1 = any section failing
      (AssertionError caught, message printed, fail-loud)."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "ledger_sync.py")

_spec = importlib.util.spec_from_file_location("ledger_sync_mod", TOOL)
ls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ls)


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(path, text):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def read_rows(path):
    lines = io.open(path, encoding="utf-8").read().rstrip("\n").split("\n")
    rows = [ln.split("\t") for ln in lines]
    header = rows[0]
    return header, [dict(zip(header, r)) for r in rows[1:]]


def sec1_selftest():
    rc, out = run(["--selftest"])
    assert rc == 0, "selftest should exit rc=0, got %d\n%s" % (rc, out)
    assert "LEDGER-SYNC-SELFTEST PASS" in out, out
    assert "thirteen checks pass" in out, out
    return "selftest thirteen checks pass"


def sec2_clean(tmp):
    tsv = wf(os.path.join(tmp, "t2.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "A1\t10\tm1\t0\tUNPROBED\t\n"
             "A2\t20\tm2\t5\tUNPROBED\t\n"
             "A3\t30\tm3\t0\tUNPROBED\t\n")
    probe = os.path.join(tmp, "p2.json")
    with io.open(probe, "w", encoding="utf-8") as fh:
        json.dump({"schema": ls.SCHEMA, "records": {
            "A1": {"file": "A1", "md5": "m1", "rc": 0, "red": "",
                   "red_class": "", "verdict": "BORN-CLEAN",
                   "red_count": 0, "md5_match": True},
            "A2": {"file": "A2", "md5": "m2", "rc": 1,
                   "red": "Error: Illegal application (Non-functional "
                          "construction): boom",
                   "red_class": "ILLEGAL_APP", "verdict": "RED-ILLEGAL_APP",
                   "red_count": 5, "md5_match": True},
            "A3": {"file": "A3", "md5": "m3", "rc": 0, "red": "",
                   "red_class": "", "verdict": "WASHABLE",
                   "red_count": 1, "md5_match": True},
        }}, fh)
    out = os.path.join(tmp, "t2out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert by["A1"]["状态"] == "WASHABLE" and by["A1"]["备注"] == "probe:rc0", by["A1"]
    assert by["A2"]["状态"] == "DRIFT-BLOCKED" \
        and by["A2"]["备注"] == "probe:rc1:ILLEGAL_APP", by["A2"]
    assert by["A3"]["状态"] == "WASHABLE", by["A3"]
    return "CLEAN full chain exits 0 + UNPROBED promotion interlocked row by row + probe_engine full-field records consumed directly"


def sec3_e1_dedup(tmp):
    tsv = wf(os.path.join(tmp, "t3.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "B1\t10\tm1\t0\tUNPROBED\tfirst row\n"
             "B1\t99\tZZ\t9\tGIANT\tduplicate row must be dropped\n"
             "B2\t20\tm2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p3.json"),
               json.dumps({"records": {"B1": {"file": "B1", "md5": "m1",
                                              "rc": 0, "red": ""},
                                       "B2": {"file": "B2", "md5": "m2",
                                              "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t3out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "E1-DUP" in out_txt and "SYNC-FINDINGS" in out_txt, out_txt
    _, rows = read_rows(out)
    assert len(rows) == 2, "expected 2 rows after dedup, got %d" % len(rows)
    b1 = [r for r in rows if r["件名"] == "B1"][0]
    assert b1["行数"] == "10" and b1["备注"].startswith("first row"), b1
    return "E1 dedup keeps the first row + one FINDING per item + row counts correct"


def sec4_e3_ghost(tmp):
    tsv = wf(os.path.join(tmp, "t4.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "C1\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p4.json"),
               json.dumps({"records": {
                   "C1": {"file": "C1", "md5": "m1", "rc": 0, "red": ""},
                   "GhostA": {"file": "GhostA", "md5": "g1", "rc": 1, "red": "x"},
                   "GhostB": {"file": "GhostB", "md5": "g2", "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t4out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "E3-GHOST" in out_txt, out_txt
    assert "GhostA" in out_txt and "GhostB" in out_txt, "the ghost roster must be printed loudly"
    _, rows = read_rows(out)
    assert len(rows) == 1, "ghosts must not become rows, got %d rows" % len(rows)
    return "E3 ghosts are recorded only, never written as rows"


def sec5_special_tags(tmp):
    tsv = wf(os.path.join(tmp, "t5.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "D1\t10\tm1\t0\tUNPROBED\t\n"
             "D2\t20\tm2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p5.json"),
               json.dumps({"records": {
                   "D1": {"file": "D1", "md5": "m1", "rc": 124, "red": "TIMEOUT"},
                   "D2": {"file": "D2", "md5": "m2", "rc": "NO_SRC", "red": ""}}}))
    out = os.path.join(tmp, "t5out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert by["D1"]["备注"] == "probe:timeout" and by["D1"]["状态"] == "UNPROBED", by["D1"]
    assert by["D2"]["备注"] == "probe:no-src" and by["D2"]["状态"] == "UNPROBED", by["D2"]
    return "timeout/no-src special tags + UNPROBED stays unpromoted"


def sec6_no_md5(tmp):
    tsv = wf(os.path.join(tmp, "t6.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "E1x\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p6.json"),
               json.dumps({"E1x": {"file": "E1x", "rc": 0, "red": ""}}))  # W13 bare form, no md5
    out = os.path.join(tmp, "t6out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "NO-MD5" in out_txt, out_txt
    _, rows = read_rows(out)
    assert rows[0]["备注"] == "probe:rc0" and rows[0]["状态"] == "UNPROBED", rows[0]
    return "NO-MD5 old-style ledger annotated only, not promoted"


def sec7_report(tmp):
    tsv = wf(os.path.join(tmp, "t7.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "F1\t10\tm1\t0\tUNPROBED\t\n"
             "F2\t10\tWRONG\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p7.json"),
               json.dumps({"records": {
                   "F1": {"file": "F1", "md5": "m1", "rc": 0, "red": ""},
                   "F2": {"file": "F2", "md5": "m2", "rc": 0, "red": ""},
                   "F3": {"file": "F3", "md5": "m3", "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t7out.tsv")
    rep = os.path.join(tmp, "r7.json")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out,
                       "--report", rep])
    assert rc == 1, out_txt
    acc = json.load(io.open(rep, encoding="utf-8"))
    assert acc["schema"] == ls.SCHEMA, acc.get("schema")
    assert acc["counts"] == {"E3-GHOST": 1, "MD5-DRIFT": 1}, acc["counts"]
    codes = sorted(f["code"] for f in acc["findings"])
    assert codes == ["E3-GHOST", "MD5-DRIFT"], codes
    assert acc["rows"] == 2 and acc["synced"] == 2, acc
    return "report JSON schema/counts/per-item findings interlocked"


def sec8_cli_and_idempotent(tmp):
    tsv = wf(os.path.join(tmp, "t8.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "G1\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p8.json"),
               json.dumps({"records": {"G1": {"file": "G1", "md5": "m1",
                                              "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t8out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0, out_txt
    before = io.open(out, "rb").read()
    rc2, out2 = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc2 == 0 and io.open(out, "rb").read() == before, "idempotent rerun drifted"
    # CLI four exit codes
    rc, out_txt = run(["--help"])
    assert rc == 0 and "usage" in out_txt, out_txt[-200:]
    rc, out_txt = run(["--bogus"])
    assert rc == 2, "unknown flag should exit rc=2, got %d" % rc
    rc, out_txt = run([])
    assert rc == 2, "missing arguments should exit rc=2, got %d" % rc
    rc, out_txt = run(["--probe", os.path.join(tmp, "no.json"),
                       "--ledger", tsv, "--out", out])
    assert rc == 9, "missing file should exit rc=9, got %d" % rc
    # column validation two variants (missing column / ragged width) rc2, no output
    bad = wf(os.path.join(tmp, "bad8.tsv"), "件名\tmd5\nG1\tm1\n")
    o2 = os.path.join(tmp, "bad8out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", bad, "--out", o2])
    assert rc == 2 and "missing required columns" in out_txt \
        and not os.path.exists(o2), out_txt
    ragged = wf(os.path.join(tmp, "rag8.tsv"),
                "件名\t行数\tmd5\tRED\t状态\t备注\nG1\t1\tm1\t0\n")
    rc, out_txt = run(["--probe", probe, "--ledger", ragged, "--out", o2])
    assert rc == 2 and "width mismatch" in out_txt and not os.path.exists(o2), out_txt
    return "CLI four exit codes + column-validation variants rc2 with no output + byte-identical idempotent reruns"


def sec9_items_shell_and_meta(tmp):
    # 9a: agent freeze-ledger shell (items subkey) consumed directly;
    # shell keys (schema/queue/world) never become phantom probe names
    tsv = wf(os.path.join(tmp, "t9.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "I1\t10\tmi1\t0\tUNPROBED\t\n")
    probe = os.path.join(tmp, "freeze.json")
    with io.open(probe, "w", encoding="utf-8") as fh:
        json.dump({"schema": "seat-freeze/1",
                   "items": {"I1": {"file": "I1", "md5": "mi1",
                                    "rc": 0, "red": ""}},
                   "queue": [], "world": "/tmp/w"}, fh)
    out = os.path.join(tmp, "t9out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    assert "E3-GHOST" not in out_txt, "shell keys misread as probe names would raise phantom ghosts (the pre-v2.1 defect)"
    _, rows = read_rows(out)
    assert rows[0]["状态"] == "WASHABLE" and rows[0]["备注"] == "probe:rc0", rows[0]
    # 9b: bare-dict form with batch_meta sibling — meta skipped loudly,
    # zero phantom ghost, record synced
    tsv = wf(os.path.join(tmp, "t9b.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "I2\t10\tmi2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "bare_meta.json"),
               json.dumps({"I2": {"file": "I2", "md5": "mi2", "rc": 0,
                                  "red": ""},
                           "batch_meta": {"seat": "W9",
                                          "ledger_basis": "x.tsv"}}))
    out = os.path.join(tmp, "t9bout.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out,
                       "--report", os.path.join(tmp, "t9rep.json")])
    assert rc == 0 and "PROBE-META-SKIP" in out_txt, out_txt
    assert "batch_meta" in out_txt, "the metadata key must be reported loudly"
    assert "E3-GHOST" not in out_txt, out_txt
    acc = json.load(io.open(os.path.join(tmp, "t9rep.json"), encoding="utf-8"))
    assert acc["meta_skipped"] == ["batch_meta"], acc.get("meta_skipped")
    _, rows = read_rows(out)
    assert rows[0]["状态"] == "WASHABLE", rows[0]
    # 9c: bare-dict all-meta (zero records) — fail-loud rc2, no output
    probe = wf(os.path.join(tmp, "all_meta.json"),
               json.dumps({"schema": "x/1", "batch_meta": {"seat": "W9"}}))
    out = os.path.join(tmp, "t9cout.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger",
                       wf(os.path.join(tmp, "t9c.tsv"),
                          "件名\t行数\tmd5\tRED\t状态\t备注\n"
                          "I3\t1\tm\t0\tUNPROBED\t\n"),
                       "--out", out])
    assert rc == 2 and "zero records" in out_txt, out_txt
    assert not os.path.exists(out), "zero-records refusal must not produce output"
    return "items shell consumed directly + zero ghosts from shell keys + batch_meta filtered loudly + all-metadata rc2 sync refusal"


def sec10_gen_divergence(tmp):
    tsv = wf(os.path.join(tmp, "t10.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "D1\t10\tmd1\t0\tUNPROBED\t\n"
             "D2\t20\tmd2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "div.json"),
               json.dumps({"records": {
                   "D1": {"file": "D1", "md5": "md1", "rc": 0, "red": "",
                          "source_seats": ["sA", "sB"],
                          "divergence_with": "sB",
                          "divergence_md5": "dmd5"},
                   "D2": {"file": "D2", "md5": "DIFFERENT", "rc": 0,
                          "red": "",
                          "divergence_with": "sC",
                          "divergence_md5": "dmd6"}}}))
    out = os.path.join(tmp, "t10out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "GEN-DIVERGENCE" in out_txt, out_txt
    assert out_txt.count("GEN-DIVERGENCE") >= 2, "both divergence items must be reported loudly"
    assert "MD5-DRIFT" in out_txt, "the drifted row's md5 finding must still be recorded"
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert "probe:gen-div:sB" in by["D1"]["备注"], by["D1"]
    assert by["D1"]["状态"] == "WASHABLE", by["D1"]  # md5-interlock promotion unchanged
    assert "probe:gen-div:sC" in by["D2"]["备注"], by["D2"]
    assert by["D2"]["状态"] == "UNPROBED", by["D2"]  # the drifted row stays unpromoted
    # idempotent: rerun keeps the ledger byte-identical (a divergence tag already on disk is skipped)
    before = io.open(out, "rb").read()
    rc2, _ = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc2 == 1 and io.open(out, "rb").read() == before, "divergence annotation rerun drifted"
    return "GEN-DIVERGENCE reported per item + idempotent row annotations + promotion rule consistent with the drift rule"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_lsync_test_")
    try:
        secs = [
            ("1 selftest", sec1_selftest),
            ("2 CLEAN chain", lambda: sec2_clean(tmp)),
            ("3 E1 dedup", lambda: sec3_e1_dedup(tmp)),
            ("4 E3 ghosts", lambda: sec4_e3_ghost(tmp)),
            ("5 special tags", lambda: sec5_special_tags(tmp)),
            ("6 NO-MD5", lambda: sec6_no_md5(tmp)),
            ("7 report", lambda: sec7_report(tmp)),
            ("8 CLI+idempotent", lambda: sec8_cli_and_idempotent(tmp)),
            ("9 items shell+meta", lambda: sec9_items_shell_and_meta(tmp)),
            ("10 divergence", lambda: sec10_gen_divergence(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/10] %-12s OK — %s" % (n, name, note))
        print("TEST-LEDGER-SYNC PASS: 10/10 sections pass")
        return 0
    except AssertionError as e:
        print("TEST-LEDGER-SYNC FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
