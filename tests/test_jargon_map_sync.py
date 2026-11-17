#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_jargon_map_sync.py: suite hookup shell for tools/jargon_map_sync.py
(tests/; P1 mapping-sync cast agent hookup, normwave59 work stream, 20261117).

Purpose.  Wires the md-to-JSON jargon map sync into the suite entry: the
  filter vectors (single-form derivation with the parenthetical-annotation
  stripping, the slash and fullwidth-slash alternation rejects, the six
  note-guard rejects, the em-dash rewrite-or-delete bucket, the upsert
  preserve rules for id/exempts/cross_track_note, the exact count label,
  rerun determinism) are attested by the tool's own --selftest; this shell
  drives the argparse faces and the exit-code convention, the live
  post-sync plan contract over the standing map, and one tmp end-to-end
  apply arc.

Interface.  python3 tests/test_jargon_map_sync.py  (suite entry via
  run_tests.sh t_jargon_map_sync; zero arguments).

Dependencies.  Python 3 standard library only; subprocess drives the real
  tools/jargon_map_sync.py CLI; the live check reads the standing
  seeds/jargon/jargon-map.json and docs/jargon-to-standard-mapping-v1.md
  read-only (absent standing faces are one loud SKIP, never a silent
  pass); zero network; zero writes outside the system temp dir.

Evidence.  Six checks: (1) --selftest rc=0 with the SYNC-SELFTEST PASS
  frozen marker; (2) --help rc=0 (the usage face); (3) --bogus=2;
  (4) a missing --map file =9; (5) the live plan face read-only IN-SYNC
  (rc=0, VERDICT IN-SYNC, map md5 unchanged, count label == entries) —
  the standing post-sync contract; (6) a tmp end-to-end arc: plan exits 1
  pending with zero bytes written, --apply writes once, a second --apply
  is a byte-identical no-op.

Exit-codes.  0 all checks pass (SKIP lines allowed for absent standing
  inputs); 1 any check red (fail-loud, listed).
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "jargon_map_sync.py")
MARK = "SYNC-SELFTEST PASS"
LIVE_MD = os.path.join(REPO, "docs", "jargon-to-standard-mapping-v1.md")
LIVE_MAP = os.path.join(REPO, "seeds", "jargon", "jargon-map.json")

# tmp end-to-end fixture: one pending update, one append, one alternation
# reject; the plan must report pending (rc 1) and write nothing
FX_MAP = {
    "schema": "rocqwash-jargon-map/1", "engine": "jargon",
    "seed_role": "tmp fixture for the suite hookup shell",
    "face_language": "zh", "count": 1,
    "selection_rule": "fixture", "boundary_note": "fixture",
    "provenance": {"sources": []},
    "entries": [
        {"id": "J001", "face": "\u6253\u5305", "standard": "\u65e7\u5f62",
         "standard_language": "zh", "standard_source": "fixture track",
         "source_line": 3, "disposition": "replace", "exempts": [],
         "cross_track_note": None, "note": None},
    ],
}
FX_MD = "\n".join([
    "| \u9ED1\u8BDD (jargon face) | s | n |",
    "|---|---|---|",
    "| \u6253\u5305 | \u5c01\u88c5 | pending update. 1 file. |",
    "| seat | agent | pending append. 1 file. |",
    "| \u76d8\u70b9 | keep / drop | alternation reject. 1 file. |",
]) + "\n"


def run(args):
    """One subprocess of the sync tool (stdout+stderr merged)."""
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def md5(path):
    with io.open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    fails = []
    # check 1: the tool's own frozen selftest vector group
    rc, out = run(["--selftest"])
    if rc != 0 or MARK not in out:
        fails.append("check 1 --selftest should be rc=0 with %r"
                     " (got rc=%d)" % (MARK, rc))
        print(out[-2000:])
    # check 2: the usage face
    rc, out = run(["--help"])
    if rc != 0:
        fails.append("check 2 --help should be rc=0 (got rc=%d)" % rc)
        print(out)
    # check 3: unknown flag = usage error
    rc, _out = run(["--bogus"])
    if rc != 2:
        fails.append("check 3 --bogus should be rc=2 (got rc=%d)" % rc)
    # check 4: a missing --map file = missing input
    rc, _out = run(["--map", "/nonexistent/jargon-map.json"])
    if rc != 9:
        fails.append("check 4 a missing --map should be rc=9 (got rc=%d)" % rc)
    # check 5: the live plan face is read-only IN-SYNC (standing post-sync
    # contract; absent standing faces are one loud SKIP, never a red)
    if os.path.isfile(LIVE_MD) and os.path.isfile(LIVE_MAP):
        before = md5(LIVE_MAP)
        rc, out = run(["--md", LIVE_MD, "--map", LIVE_MAP])
        with io.open(LIVE_MAP, encoding="utf-8") as fh:
            m = json.load(fh)
        ok = (rc == 0 and "VERDICT IN-SYNC" in out
              and md5(LIVE_MAP) == before
              and m.get("count") == len(m.get("entries") or []))
        if not ok:
            fails.append("check 5 live plan should be rc=0 IN-SYNC with the"
                         " map untouched and an exact count label (got rc=%d,"
                         " verdict=%s)" % (rc, out.splitlines()[:1]))
    else:
        print("SKIP check 5: standing map or md table absent (%s)" % LIVE_MAP)
    # check 6: tmp end-to-end arc - plan pending zero-write, apply writes
    # once, second apply byte-identical
    tmp = tempfile.mkdtemp(prefix="rqw_jargon_sync_shell_")
    try:
        fx_md = os.path.join(tmp, "fx.md")
        fx_map = os.path.join(tmp, "fx-map.json")
        with io.open(fx_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(FX_MD)
        with io.open(fx_map, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(FX_MAP, ensure_ascii=False, indent=2) + "\n")
        base = io.open(fx_map, "rb").read()
        rc, _out = run(["--md", fx_md, "--map", fx_map])
        plan_pending = rc == 1 and io.open(fx_map, "rb").read() == base
        rc, _out = run(["--md", fx_md, "--map", fx_map, "--apply"])
        written = rc == 0 and io.open(fx_map, "rb").read() != base
        once = io.open(fx_map, "rb").read()
        rc, _out = run(["--md", fx_md, "--map", fx_map, "--apply"])
        idempotent = rc == 0 and io.open(fx_map, "rb").read() == once
        if not (plan_pending and written and idempotent):
            fails.append("check 6 tmp arc: plan_pending=%s written=%s"
                         " idempotent=%s" % (plan_pending, written,
                                             idempotent))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("== test_jargon_map_sync: %d pass / %d red =="
          % (6 - len(fails), len(fails)))
    for f in fails:
        print("FAIL:", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
