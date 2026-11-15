#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""t_symbiosis_shape.py — tests/ suite shell for tools/symbiosis_bus.py.

    Purpose.  Smoke the cross-repository symbiosis bus offline: the CLI face
      naming, the export schema matrix (rocqwash-symbio/1 envelope with the
      sourceRepo/anchor fields plus verbatim entry lines), import through
      the single exp_port append face (rocqwash-exp/1 rows, carrier and
      content-borne ts preservation, deterministic replay), idempotent
      re-import (byte-identical zero delta, id-axis collision skip), the
      status and diff faces, the exit-code convention, and dry-run
      zero-write.

    Interface.  `py tests/t_symbiosis_shape.py` (rostered in
      tests/run_tests.sh as case t_symbiosis_shape on 20261115, audit
      finding P0-6; the roster count is derived one-way from the CASES
      block in tests/run_tests.sh by doc_lint's second check, and the
      README count lines follow that derived count).  Seven checks total,
      each driving the tool's real argparse face in a subprocess:
      `export --ledger L --out P [--source-repo NAME] [--anchor HEX]
      [--dry-run]` | `import --swap P --ledger L [--dry-run]` |
      `status [--ledger L] [--swap F]` | `diff --a A --b B`, plus
      `--selftest` (ten frozen vectors, asserted by the tool itself and not
      duplicated here).

    Dependencies.  Python 3 stdlib only; every check runs on temporary
      fixtures under one mkdtemp root; nothing in the repository is
      written; zero network — all four faces run on offline files by
      design (NETRED: no network by construction).

    Evidence.  Every check runs the tool in a subprocess and asserts the
      exit code, the output face, or the fixture bytes on this machine;
      every package fed to import is produced by the tool's own export
      face, so the test assumes no package shape beyond the tool's own
      contract; the single-port oath is attested behaviorally (the
      rocqwash-exp/1 row plus the 64-hex fingerprint that only the
      exp_port append face mints, byte-identical re-import, id-axis skip).

    Exit-codes.  0 = all seven checks pass; 1 = any check red (fail-loud,
      the red check is printed; no silent downgrade).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "symbiosis_bus.py")
SWAP_SCHEMA = "rocqwash-symbio/1"
SWAP_KIND = "symbiosis-swap-envelope"
EXP_SCHEMA = "rocqwash-exp/1"
FIELDS = ("Purpose.", "Interface.", "Dependencies.", "Evidence.",
          "Exit-codes.")
FACES = ("export", "import", "status", "diff")
FLAGS = ("--dry-run", "--ledger", "--out", "--swap", "--source-repo",
         "--anchor", "--a", "--b")
ANCHOR = "2b" * 20
SRC_REPO = "srcShape"
SEP = "\x1f"


def run(args):
    """Run the tool in a subprocess (stdout+stderr merged).  `-X utf8`
    pins the stdio encoding, and `-I` isolates the child from inherited
    interpreter state, mirroring the t_periscope_shape.py runner."""
    p = subprocess.run([sys.executable, "-B", "-I", "-X", "utf8", TOOL]
                       + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=REPO)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def fingerprint(tool, points, evidence, batch):
    """Content key over the four carrier fields, matching the exp_port
    append-face algorithm so seeded rows look like port-written rows."""
    payload = SEP.join([tool, points, evidence, batch])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def entry(eid, tool, points, evidence, batch, ts="2026-11-14T10:00:00Z"):
    """A full rocqwash-exp/1 row (fixed ts: content-borne, so every
    derived expectation stays deterministic)."""
    return {
        "schema": EXP_SCHEMA,
        "id": eid,
        "ts": ts,
        "tool": tool,
        "points": points,
        "evidence": evidence,
        "batch": batch,
        "fingerprint": fingerprint(tool, points, evidence, batch),
    }


def canonical(obj):
    """The repo-wide canonical JSON line form (same bytes as the tools)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def seed_ledger(path, rows):
    """Write a JSONL ledger fixture (parent dirs included)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def seed_raw(path, lines):
    """Write raw text lines (corrupt-ledger fixture)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def read_objects(path):
    """Parse a JSONL file into objects; an absent file reads as empty."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_bytes(path):
    """Byte content of a file; an absent file reads as empty so a red
    tool run records a fail line instead of crashing the shell."""
    if not os.path.isfile(path):
        return b""
    with open(path, "rb") as handle:
        return handle.read()


def rewrite_envelope_schema(src_path, dst_path, schema_value):
    """Copy a package line-by-line with only the envelope line's schema
    field replaced (the entry lines keep their rocqwash-exp/1 schema)."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    rows = read_objects(src_path)
    rows[0] = dict(rows[0], schema=schema_value)
    with open(dst_path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def normalized(path):
    """Rows sorted by canonical form: order-insensitive ledger compare."""
    rows = read_objects(path)
    return sorted(canonical(row) for row in rows)


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="t_symbiosis_shape_")
    try:
        # Check 1: CLI face smoke - --help is rc=0 and names the four
        # faces plus the real flags; the tool source carries the
        # five-field header of the annotation standard.
        rc, out = run(["--help"])
        flat = re.sub(r"-\s*\n\s*", "-", out)
        if rc != 0:
            fails.append("check1 --help should be rc=0 (rc=%d)\n%s"
                         % (rc, out))
        for name in FACES + FLAGS:
            if name not in flat:
                fails.append("check1 --help should name %s\n%s"
                             % (name, flat))
        if os.path.isfile(TOOL):
            with open(TOOL, "r", encoding="utf-8") as handle:
                src = handle.read()
            for field in FIELDS:
                if field not in src:
                    fails.append("check1 tool header misses %s" % field)
        else:
            fails.append("check1 tool file absent: %s" % TOOL)

        # Fixture ledgers: source with two entries, and one entry per
        # side for the diff face.
        src_ledger = os.path.join(tmp, "src", "exp-ledger.jsonl")
        seed_ledger(src_ledger,
                    [entry("S-1", "toolA", "point one", "ev://a", "batch-1"),
                     entry("S-2", "toolB", "point two", "ev://b", "batch-1")])
        ledger_a = os.path.join(tmp, "sideA", "exp-ledger.jsonl")
        seed_ledger(ledger_a,
                    [entry("S-1", "toolA", "point one", "ev://a", "batch-1"),
                     entry("S-2", "toolB", "point two", "ev://b", "batch-1")])
        ledger_b = os.path.join(tmp, "sideB", "exp-ledger.jsonl")
        seed_ledger(ledger_b,
                    [entry("S-2", "toolB", "point two", "ev://b", "batch-1"),
                     entry("S-3", "toolC", "point three", "ev://c",
                           "batch-2")])

        # Check 2: export schema matrix - the package is rocqwash-symbio/1
        # JSONL: line 1 is the envelope (schema, kind, sourceRepo, anchor,
        # entryCount==2), then one verbatim entry line per ledger entry
        # carrying the carrier fields and the append-face fingerprint; a
        # zero-entry ledger exports the envelope alone with entryCount=0;
        # a corrupt source ledger fails loud rc=9 before the package
        # exists.
        swap_dir = os.path.join(tmp, "swap")
        os.makedirs(swap_dir, exist_ok=True)
        pkg = os.path.join(swap_dir, "round1.jsonl")
        rc, out = run(["export", "--ledger", src_ledger, "--out", pkg,
                       "--source-repo", SRC_REPO, "--anchor", ANCHOR])
        if rc != 0 or "wrote 2 entries" not in out:
            fails.append("check2 export should write 2 entries rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        rows = read_objects(pkg)
        if len(rows) != 3:
            fails.append("check2 package should hold 1 envelope + 2 "
                         "entries, got %d" % len(rows))
        envelope = rows[0] if rows else {}
        if envelope.get("schema") != SWAP_SCHEMA:
            fails.append("check2 envelope schema should be %s: %r"
                         % (SWAP_SCHEMA, envelope.get("schema")))
        if envelope.get("kind") != SWAP_KIND:
            fails.append("check2 envelope kind should be %s: %r"
                         % (SWAP_KIND, envelope.get("kind")))
        if (envelope.get("sourceRepo"), envelope.get("anchor"),
                envelope.get("entryCount")) != (SRC_REPO, ANCHOR, 2):
            fails.append("check2 envelope sourceRepo/anchor/entryCount "
                         "mismatch: %r" % sorted(envelope))
        for row in rows[1:]:
            if not all(k in row for k in ("tool", "points", "evidence",
                                          "batch", "fingerprint")):
                fails.append("check2 entry line misses carrier or "
                             "fingerprint fields: %r" % sorted(row))
        ids = [row.get("id") for row in rows[1:]]
        if ids != ["S-1", "S-2"]:
            fails.append("check2 entry lines should keep ledger order "
                         "S-1, S-2: %r" % (ids,))
        empty_ledger = os.path.join(tmp, "empty", "exp-ledger.jsonl")
        seed_ledger(empty_ledger, [])
        empty_pkg = os.path.join(swap_dir, "empty.jsonl")
        rc, out = run(["export", "--ledger", empty_ledger, "--out",
                       empty_pkg, "--source-repo", SRC_REPO,
                       "--anchor", ANCHOR])
        empty_rows = read_objects(empty_pkg)
        if rc != 0 or len(empty_rows) != 1 \
                or empty_rows[0].get("entryCount") != 0:
            fails.append("check2 export of a zero-entry ledger should be "
                         "rc=0 with an envelope-only package (rc=%d "
                         "rows=%r)\n%s" % (rc, empty_rows, out))
        bad_ledger = os.path.join(tmp, "bad", "exp-ledger.jsonl")
        seed_raw(bad_ledger, ['{"id": "ok-1", "fingerprint": "f"}',
                              "not-json{"])
        bad_pkg = os.path.join(swap_dir, "bad.jsonl")
        rc, out = run(["export", "--ledger", bad_ledger, "--out", bad_pkg,
                       "--source-repo", SRC_REPO, "--anchor", ANCHOR])
        if rc != 9:
            fails.append("check2 export of a corrupt ledger should exit 9, "
                         "got %d" % rc)
        if os.path.exists(bad_pkg):
            fails.append("check2 corrupt-ledger export must not write its "
                         "package")

        # Check 3: import single-port round trip - entries land through
        # the exp_port append face (rocqwash-exp/1 rows with a 64-hex
        # fingerprint), carriers and content-borne ts survive, ids are
        # carried verbatim, the route rides a synthesized correlationId,
        # and the same package into a fresh ledger replays identically
        # (determinism: no wall-clock value enters the rows).
        target_dir = os.path.join(tmp, "target")
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, "exp-ledger.jsonl")
        rc, out = run(["import", "--swap", pkg, "--ledger", target])
        if rc != 0 or "appended=2 skipped=0 total=2" not in out:
            fails.append("check3 import should append 2 rc=0 (rc=%d)\n%s"
                         % (rc, out))
        landed = {row.get("id"): row for row in read_objects(target)}
        if len(landed) != 2:
            fails.append("check3 import should land 2 entries, got %d"
                         % len(landed))
        carriers = {"S-1": ("toolA", "point one", "ev://a"),
                    "S-2": ("toolB", "point two", "ev://b")}
        for eid, (tool, points, evidence) in carriers.items():
            row = landed.get(eid)
            if row is None:
                fails.append("check3 entry %s missing after import" % eid)
                continue
            if row.get("schema") != EXP_SCHEMA:
                fails.append("check3 %s schema should be %s: %r"
                             % (eid, EXP_SCHEMA, row.get("schema")))
            mark = row.get("fingerprint")
            if not (isinstance(mark, str) and len(mark) == 64
                    and all(c in "0123456789abcdef" for c in mark)):
                fails.append("check3 %s misses the append-face 64-hex "
                             "fingerprint: %r" % (eid, mark))
            if (row.get("tool"), row.get("points"),
                    row.get("evidence")) != (tool, points, evidence):
                fails.append("check3 %s carriers not preserved: %r"
                             % (eid, row))
            if row.get("ts") != "2026-11-14T10:00:00Z":
                fails.append("check3 %s ts should be carried from entry "
                             "content, got %r" % (eid, row.get("ts")))
            if "batch" not in row:
                fails.append("check3 %s misses the batch field" % eid)
            if row.get("correlationId") != \
                    "symbio:%s@%s" % (SRC_REPO, ANCHOR):
                fails.append("check3 %s misses the synthesized route "
                             "marker: %r" % (eid, row.get("correlationId")))
        replay_target = os.path.join(tmp, "replay", "exp-ledger.jsonl")
        os.makedirs(os.path.dirname(replay_target), exist_ok=True)
        rc, out = run(["import", "--swap", pkg, "--ledger", replay_target])
        if rc != 0:
            fails.append("check3 replay import should be rc=0 (rc=%d)"
                         % rc)
        if normalized(target) != normalized(replay_target):
            fails.append("check3 same package into two fresh ledgers must "
                         "replay identically (determinism)")

        # Check 4: idempotent re-import - the same package again is a
        # zero-delta no-op (byte-identical ledger); an id collision
        # against different content skips on the id axis (no duplicate
        # line, existing row intact).
        before = read_bytes(target)
        rc, out = run(["import", "--swap", pkg, "--ledger", target])
        if rc != 0 or "appended=0 skipped=2" not in out:
            fails.append("check4 re-import should skip 2 rc=0 (rc=%d)\n%s"
                         % (rc, out))
        if read_bytes(target) != before:
            fails.append("check4 re-import must leave the ledger "
                         "byte-identical (idempotent skip)")
        src2 = os.path.join(tmp, "src2", "exp-ledger.jsonl")
        seed_ledger(src2, [entry("S-2", "toolD", "other points",
                                 "ev://d", "batch-2")])
        pkg2 = os.path.join(swap_dir, "round2.jsonl")
        rc, out = run(["export", "--ledger", src2, "--out", pkg2,
                       "--source-repo", SRC_REPO, "--anchor", ANCHOR])
        if rc != 0:
            fails.append("check4 second export should be rc=0 (rc=%d)"
                         % rc)
        coll_dir = os.path.join(tmp, "collision")
        os.makedirs(coll_dir, exist_ok=True)
        coll = os.path.join(coll_dir, "exp-ledger.jsonl")
        seed_ledger(coll, [entry("S-2", "toolX", "kept points",
                                 "ev://x", "batch-x")])
        rc, out = run(["import", "--swap", pkg2, "--ledger", coll])
        if rc != 0 or "appended=0 skipped=1" not in out:
            fails.append("check4 collision import should skip rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        rows = read_objects(coll)
        if len(rows) != 1 or rows[0].get("points") != "kept points":
            fails.append("check4 id collision must skip without touching "
                         "the existing row, got %r" % rows)

        # Check 5: status and diff faces - status answers rc=0 with the
        # inbound bus count and, for a given package, the present/new
        # counts; diff --a/--b lists the asymmetric entries of both
        # sides; identical ledgers are a zero-difference data face at
        # rc=0.
        rc, out = run(["status", "--ledger", target])
        if rc != 0 or "inboundBus=2" not in out or not out.strip():
            fails.append("check5 status should be rc=0 with the inbound "
                         "count (rc=%d)\n%s" % (rc, out))
        rc, out = run(["status", "--ledger", target, "--swap", pkg])
        if rc != 0 or "presentInLedger=2" not in out or "new=0" not in out:
            fails.append("check5 status with --swap should count "
                         "present=2 new=0 (rc=%d)\n%s" % (rc, out))
        rc, out = run(["diff", "--a", ledger_a, "--b", ledger_b])
        if rc != 0:
            fails.append("check5 diff should be rc=0 (rc=%d)\n%s"
                         % (rc, out))
        for eid in ("S-1", "S-3"):
            if eid not in out:
                fails.append("check5 diff should list asymmetric entry %s\n"
                             "%s" % (eid, out))
        rc, out = run(["diff", "--a", ledger_a, "--b", ledger_a])
        if rc != 0 or "only-a=0 only-b=0 common=2" not in out:
            fails.append("check5 diff of identical ledgers should be a "
                         "zero-difference rc=0 (rc=%d)\n%s" % (rc, out))

        # Check 6: exit-code convention spot checks (scratch paths only):
        # usage faces 2, missing input 9, damaged input 9 with zero
        # writes; the envelope-schema drift belongs to the damaged-input
        # bucket of the implemented contract (exit 9, nothing written).
        rc, out = run([])
        if rc != 2:
            fails.append("check6 a bare run should exit 2, got %d" % rc)
        rc, out = run(["bogus"])
        if rc != 2:
            fails.append("check6 an unknown face should exit 2, got %d"
                         % rc)
        rc, out = run(["import", "--ledger", target])
        if rc != 2:
            fails.append("check6 import without --swap should exit 2, "
                         "got %d" % rc)
        rc, out = run(["import", "--swap", pkg, "--swap", pkg,
                       "--ledger", target])
        if rc != 2:
            fails.append("check6 import with two --swap flags should "
                         "exit 2, got %d" % rc)
        rc, out = run(["export", "--ledger", src_ledger])
        if rc != 2:
            fails.append("check6 export without --out should exit 2, "
                         "got %d" % rc)
        absent_pkg = os.path.join(swap_dir, "absent.jsonl")
        no_dir = os.path.join(tmp, "nodir6", "exp-ledger.jsonl")
        rc, out = run(["import", "--swap", absent_pkg, "--ledger",
                       no_dir])
        if rc != 9:
            fails.append("check6 import on an absent package should exit "
                         "9, got %d" % rc)
        if os.path.exists(no_dir):
            fails.append("check6 absent-package import must not create "
                         "its ledger")
        drift_pkg = os.path.join(swap_dir, "drift.jsonl")
        corrupt_pkg = os.path.join(swap_dir, "corrupt.jsonl")
        if os.path.isfile(pkg):
            drift_dir = os.path.join(tmp, "drift6", "exp-ledger.jsonl")
            rewrite_envelope_schema(pkg, drift_pkg, "some-other-schema/9")
            rc, out = run(["import", "--swap", drift_pkg,
                           "--ledger", drift_dir])
            if rc != 9:
                fails.append("check6 import of a schema-drifted package "
                             "should exit 9 (the implemented damaged-input "
                             "contract), got %d\n%s" % (rc, out))
            if os.path.exists(drift_dir):
                fails.append("check6 schema-drifted import must not create "
                             "its ledger")
            shutil.copyfile(pkg, corrupt_pkg)
            with open(corrupt_pkg, "a", encoding="utf-8",
                      newline="\n") as h:
                h.write("not-json{\n")
            corrupt_dir = os.path.join(tmp, "corrupt6", "exp-ledger.jsonl")
            rc, out = run(["import", "--swap", corrupt_pkg,
                           "--ledger", corrupt_dir])
            if rc != 9:
                fails.append("check6 import of a corrupt package should "
                             "exit 9, got %d\n%s" % (rc, out))
            if os.path.exists(corrupt_dir):
                fails.append("check6 corrupt-package import must not create "
                             "its ledger")
        else:
            fails.append("check6 export package missing, the drift/corrupt "
                         "import faces are not exercised: %s" % pkg)
        absent_ledger = os.path.join(tmp, "absent6", "exp-ledger.jsonl")
        rc, out = run(["status", "--ledger", absent_ledger])
        if rc != 9:
            fails.append("check6 status on an absent ledger should exit 9, "
                         "got %d" % rc)
        rc, out = run(["diff", "--a", ledger_a, "--b",
                       os.path.join(tmp, "absent6b", "exp-ledger.jsonl")])
        if rc != 9:
            fails.append("check6 diff with an absent side should exit 9, "
                         "got %d" % rc)

        # Check 7: dry-run zero-write - import --dry-run validates and
        # reports without materializing its ledger, and holds bytes on a
        # live ledger.
        dry_dir = os.path.join(tmp, "dry7", "exp-ledger.jsonl")
        rc, out = run(["import", "--swap", pkg, "--ledger", dry_dir,
                       "--dry-run"])
        if rc != 0 or "would-append=2" not in out:
            fails.append("check7 import --dry-run should be rc=0 with a "
                         "report (rc=%d)\n%s" % (rc, out))
        if os.path.exists(dry_dir):
            fails.append("check7 import --dry-run must not create its "
                         "ledger")
        coll_before = read_bytes(coll)
        rc, out = run(["import", "--swap", pkg2, "--ledger", coll,
                       "--dry-run"])
        if rc != 0:
            fails.append("check7 dry-run on a live ledger should be rc=0 "
                         "(rc=%d)\n%s" % (rc, out))
        if read_bytes(coll) != coll_before:
            fails.append("check7 dry-run on a live ledger changed bytes")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for line in fails:
            sys.stderr.write("T-SYMBIOSIS-SHAPE FAIL %s\n" % line)
        return 1
    sys.stdout.write("T-SYMBIOSIS-SHAPE SUITE SHELL PASS (7 checks)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
