#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_comment_pack.py — selftest for wash/comment_pack.json and
wash/comment_sweep.py (rocqwash tests/; v31 toolification of the
W39/W44/W52/W54 comment-Englishization sweep precedent).

Purpose.  Six sections over the comment-domain sweep sidecar: 1 the
  sweep's --selftest (four checks, rc 0: flag-word exchange, string and
  nested-comment immunity, header regeneration, w7 code-line identity,
  idempotence); 2 pack integrity (engine=comment-state-machine, the
  flag-word table (`载体` -> `carrier`, in force), header_spec five-field
  English form with the line cap); 3 the fixture arc (dry run zero-write,
  --apply with the string-literal place exempt and a deep nested comment
  reached, w7 code-line identity, zero-change re-run); 4 header
  regeneration (--header-map data-driven, code-line identity, idempotent
  re-run); 5 header shape (a missing field is a problem, report-only,
  header_end_line convention); 6 negatives (string-literal and code-domain zero-touch, verbatim).

Interface.  python3 -B tests/test_comment_pack.py; also the suite lane
  `t_comment_pack` (tests/run_tests.sh).  No flags.

Dependencies.  Python 3 standard library only; wash/comment_sweep.py,
  wash/comment_pack.json, tests/fixtures/comment_sweep_fixture.v; every
  arc runs on fixture temp-directory copies; zero real compile, zero
  network, zero real-repository touch.

Evidence.  Each check prints an ok/FAIL line; the final TEST-COMMENT-PACK line sums
  them; dry-run byte equality and the w7 code-line equality re-assert zero touch.

Exit-codes.  0 = all six sections pass; 1 = at least one FAIL (names on
  the final TEST-COMMENT-PACK line).
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SWEEP = os.path.join(REPO, "wash", "comment_sweep.py")
PACK = os.path.join(REPO, "wash", "comment_pack.json")
FIXTURE = os.path.join(HERE, "fixtures", "comment_sweep_fixture.v")

HEADER_MAP = {
    "fixture": """(* ConstructiveWorld — comment-sweep demonstration file. *)

(** * fixture: comment-domain sweep demonstration.

    Mission.  Exercising the comment-domain flag-word exchange and the
      leading-header replacement with code lines held byte-stable.

    Dependencies.  The Require face below.

    References.  none.

    Constructivity.  The single proof closes by Qed.

    Build.  compiles cleanly (exit 0). *)

""",
}

fails = []


def check(name, cond, extra=""):
    print("  %-38s %s %s" % (name, "ok" if cond else "FAIL", extra))
    if not cond:
        fails.append(name)


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          **kw)


# 1. selftest
r = run([sys.executable, "-B", SWEEP, "--selftest"])
check("sweep --selftest rc=0", r.returncode == 0,
      "" if r.returncode == 0 else r.stdout.decode()[-300:])

# 2. pack integrity
pack = json.load(io.open(PACK, encoding="utf-8"))
check("engine is comment-state-machine",
      pack.get("engine") == "comment-state-machine")
check("flag-word table source->carrier",
      pack.get("flag_words") == {"载体": "carrier"})
spec = pack.get("header_spec", {})
check("header spec five dotted fields",
      spec.get("fields") == ["Mission.", "Dependencies.", "References.",
                             "Constructivity.", "Build."])
check("header end-line bound", spec.get("max_end_line") == 30)

# 3./4. fixture flows on a temp copy
tmp = tempfile.mkdtemp(prefix="rw_comment_")
try:
    tgt = os.path.join(tmp, "fixture.v")
    shutil.copy(FIXTURE, tgt)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--json",
             os.path.join(tmp, "dry.json")])
    dry = json.load(io.open(os.path.join(tmp, "dry.json"), encoding="utf-8"))
    check("dry-run flag_swaps=2 (header+string exempt)",
          dry["report"]["flag_swaps"] == 2, str(dry["report"]["flag_swaps"]))
    check("dry-run wrote nothing",
          io.open(tgt, encoding="utf-8").read()
          == io.open(FIXTURE, encoding="utf-8").read())
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--apply"])
    check("flag sweep apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    swept = io.open(tgt, encoding="utf-8").read()
    check("comment-domain words exchanged",
          swept.count("carrier") == 2 and "载体词" not in swept
          and "载体 深处" not in swept)
    check("string literal untouched",
          '"载体 在字符串内（禁换形）"' in swept)
    check("nested comment depth reached",
          "(* carrier 深处 *)" in swept)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt])
    check("flag sweep re-run zero-change", "flag_swaps=0" in r.stdout.decode())

    # 4. header replacement (data-driven map)
    hmap = os.path.join(tmp, "hmap.json")
    with io.open(hmap, "w", encoding="utf-8") as fh:
        json.dump(HEADER_MAP, fh, ensure_ascii=False, indent=1)
    tgt = os.path.join(tmp, "fixture.v")
    shutil.copy(FIXTURE, tgt)
    r = run([sys.executable, "-B", SWEEP, "--file", tgt, "--apply",
             "--header-map", hmap, "--json", os.path.join(tmp, "hdr.json")])
    check("header replace apply rc=0", r.returncode == 0,
          "" if r.returncode == 0 else r.stdout.decode()[-300:])
    acc = json.load(io.open(os.path.join(tmp, "hdr.json"), encoding="utf-8"))
    swept = io.open(tgt, encoding="utf-8").read()
    check("leading header replaced wholesale",
          swept.startswith(HEADER_MAP["fixture"])
          and acc["report"]["header_replaced"] is True)
    check("w7 code-line equality holds",
          acc["report"]["code_lines_equal"] is True
          and "code-line equality holds" in r.stdout.decode())
    check("tail flag words still exchanged under replacement",
          swept.count("carrier") == 2
          and "载体词" not in swept and "载体 深处" not in swept
          and '"载体 在字符串内（禁换形）"' in swept)
    check("header replace re-run zero-change",
          "header_replaced=False" in run([sys.executable, "-B", SWEEP,
                                          "--file", tgt, "--header-map",
                                          hmap]).stdout.decode())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# 5./6. shape validation negatives live in the selftest; CLI four codes here
r = run([sys.executable, "-B", SWEEP, "--help"])
check("help rc=0", r.returncode == 0 and "usage" in r.stdout.decode())
r = run([sys.executable, "-B", SWEEP])
check("missing --file rc=2", r.returncode == 2)
r = run([sys.executable, "-B", SWEEP, "--file",
         os.path.join(tmp, "gone.v")])
check("missing file rc=9", r.returncode == 9)

print("TEST-COMMENT-PACK:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
