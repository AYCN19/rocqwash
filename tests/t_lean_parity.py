#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/t_lean_parity.py -- the Lean/Rocq parity crosswalk suite hook.

Purpose.  Drives tools/lean_parity_crosswalk.py (the crosswalk engine:
  both parent tools' frozen vectors crosswalked row by row on the five
  mirror proposition keys, the bilingual mirror fixture group under
  tests/fixtures/lean_parity, the mapping read verbatim from
  axiom_audit.LEAN_PARITY_ROWS) through its three-leg contract: leg A
  the offline frozen-vector crosswalk (always runs, no engine), leg B
  the real Rocq census over the mirror .v files (compile-engine gated),
  leg C the real Lean sweep over the mirror .lean files (gated).
Interface.  `python3 -B tests/t_lean_parity.py` runs the three legs
  (PASS / FAIL / SKIP lines; SKIP lines carry their reason and are
  never red by themselves) and exits 0 when every leg that ran judged
  green and no leg was skipped, 1 on any FAIL (red outranks skip), 111
  when a gated leg was skipped for its absent engine and nothing
  failed (the suite's environment-absent SKIP code).
Dependencies.  Python 3 standard library only; the crosswalk tool (and
  through it both parent tools) loads by file path; the committed
  fixture corpus is read through the tool's private temp workdirs; zero
  network; writes only inside temporary directories.
Evidence.  Leg A asserts the crosswalk selftest rc 0, the offline
  payload verdict MATCH with all five pairs matched, the mapping source
  verbatim face and the parity-map identity against the audit tool's
  own table; leg B asserts the live census leg ran and the matrix stays
  MATCH over the live Rocq side; leg C asserts the live sweep leg ran
  and the matrix stays MATCH over the live Lean side; a gated leg with
  no engine prints one loud SKIP line, never a silent pass.
Exit-codes.  0 = every leg ran green; 1 = at least one FAIL; 111 = a
  gated leg skipped and no FAIL.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL_PATH = REPO / "tools" / "lean_parity_crosswalk.py"
FIXTURE_DIR = REPO / "tests" / "fixtures" / "lean_parity"
EXPECTED_SCHEMA = "rocqwash.parity.lean-census/1"
MIRROR_KEYS = ("clean", "classical", "funext", "custom", "sorry")


def load_tool():
    """The crosswalk module by file path (importlib; no package context);
    it in turn loads both parent tools by file path."""
    spec = importlib.util.spec_from_file_location(
        "lean_parity_crosswalk_module", str(TOOL_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def spawn_tool(argv, env=None):
    """One crosswalk run as (rc, merged stdout/stderr text)."""
    full_env = dict(os.environ) if env is None else env
    try:
        pr = subprocess.run([sys.executable, "-I", "-B", str(TOOL_PATH)]
                            + argv, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300,
                            env=full_env)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    return pr.returncode, pr.stdout.decode("utf-8", "replace")


def resolve_engine():
    """The Rocq compile engine path, or None (the audit tool's order)."""
    env_bin = os.environ.get("ROCWASH_ROCQ", "")
    if env_bin:
        return env_bin
    for name in ("coqc", "rocq"):
        found = shutil.which(name)
        if found:
            return found
    return None


# ---- leg A: the offline frozen-vector crosswalk (no engine, always) ----

def run_leg_a():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    with tempfile.TemporaryDirectory(
            prefix="t_lean_parity_leg_a_") as tmp:
        rc, out = spawn_tool(["--selftest"])
        check("crosswalk-selftest-rc0", rc == 0,
              "the crosswalk's own frozen offline vector group exits %s"
              % rc)
        json_path = os.path.join(tmp, "offline.json")
        rc, out = spawn_tool(["--json", json_path])
        if not check("offline-run-rc0", rc == 0,
                     "the offline trunk exits %s; out=%r"
                     % (rc, out.strip()[:160])):
            return lines
        with open(json_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        check("offline-schema",
              payload["schema"] == EXPECTED_SCHEMA,
              "payload carries %s" % payload["schema"])
        check("offline-verdict-match",
              payload["verdict"]["value"] == "MATCH",
              "verdict=%s" % payload["verdict"]["value"])
        pairs = payload["pairs"]["value"]
        check("offline-five-pairs-matched",
              [p["proposition"] for p in pairs] == list(MIRROR_KEYS)
              and all(p["verdict"] == "MATCH" for p in pairs),
              "%d pairs over the mirror roster, all matched: %r"
              % (len(pairs), [p["verdict"] for p in pairs]))
        check("offline-counts-equal",
              payload["counts"]["value"]["lean_enumerated"]
              == payload["counts"]["value"]["rocq_enumerated"] == 5,
              "counts=%r" % (payload["counts"]["value"],))
        check("mapping-source-verbatim",
              payload["mapping_source"]["value"]
              == "axiom_audit.LEAN_PARITY_ROWS/1",
              "mapping_source=%r" % payload["mapping_source"]["value"])
        sorry_pair = next(p for p in pairs if p["proposition"] == "sorry")
        check("admitted-mirror-rule-face",
              sorry_pair["lean_class"] == "SORRY-ALARM"
              and sorry_pair["rocq_axioms"] == ["lp_mirror_admitted"]
              and "LEAN_PARITY_NOTE" in sorry_pair["basis"],
              "the sorry pair rides the design-frozen Admitted <->"
              " sorryAx mirror rule with its provenance basis")
        # module-level: the mapping in the crosswalk is the audit tool's
        # own table read verbatim (no second table may ever appear here)
        tool = load_tool()
        expected_map = {g: lc for g, lc, _b in tool.AUDIT.LEAN_PARITY_ROWS}
        check("parity-map-no-second-table",
              tool.parity_map() == expected_map
              and len(expected_map) == 5,
              "the crosswalk's only grade->class map is the audit tool's"
              " 5-row table: %r" % (expected_map,))
    return lines


# ---- leg B: the real Rocq census over the mirror .v files ----

def run_leg_b():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    engine = resolve_engine()
    if engine is None or not os.path.exists(engine):
        lines.append("SKIP leg_b_rocq_census - compile engine not"
                     " configured (flag / ROCWASH_ROCQ / PATH); the real"
                     " census leg is not run (rc 111)")
        return lines
    if not FIXTURE_DIR.is_dir():
        check("mirror-fixture-dir", False,
              "missing mirror fixture group: %s" % FIXTURE_DIR)
        return lines
    with tempfile.TemporaryDirectory(
            prefix="t_lean_parity_leg_b_") as tmp:
        json_path = os.path.join(tmp, "live.json")
        rc, out = spawn_tool(["--rocq-face", "--rocq", engine,
                              "--json", json_path])
        if not check("rocq-face-rc0", rc == 0,
                     "the crosswalk with the live census leg exits %s;"
                     " out=%r" % (rc, out.strip()[:200])):
            return lines
        with open(json_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        legs = payload["legs"]["value"]
        check("rocq-leg-ran",
              str(legs.get("fixture_rocq", "")).startswith("ran"),
              "fixture_rocq leg record: %r" % legs.get("fixture_rocq"))
        check("rocq-live-verdict-match",
              payload["verdict"]["value"] == "MATCH"
              and all(p["verdict"] == "MATCH"
                      for p in payload["pairs"]["value"]),
              "verdict=%s over %d pairs with the live Rocq side"
              % (payload["verdict"]["value"],
                 len(payload["pairs"]["value"])))
        admitted = next(p for p in payload["pairs"]["value"]
                        if p["proposition"] == "sorry")
        check("rocq-admitted-live-face",
              admitted["rocq_axioms"] == ["lp_mirror_admitted"]
              and admitted["lean_class"] == "SORRY-ALARM",
              "the live census surfaces the Admitted statement's own"
              " name and the mirror rule maps it: %r / %r"
              % (admitted["rocq_axioms"], admitted["lean_class"]))
    return lines


# ---- leg C: the real Lean sweep over the mirror .lean files ----

def run_leg_c():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    tool = load_tool()
    _lean, _lake, usable_lean, usable_lake = tool.SWEEP.probe_toolchain()
    if not (usable_lean or usable_lake):
        lines.append("SKIP: Lean toolchain absent - leg C not run"
                     " (rc 111); a usable `lean` or `lake` on PATH is the"
                     " requirement, nothing is simulated")
        return lines
    with tempfile.TemporaryDirectory(
            prefix="t_lean_parity_leg_c_") as tmp:
        json_path = os.path.join(tmp, "live.json")
        rc, out = spawn_tool(["--lean-face", "--json", json_path])
        if not check("lean-face-rc0", rc == 0,
                     "the crosswalk with the live sweep leg exits %s;"
                     " out=%r" % (rc, out.strip()[:200])):
            return lines
        with open(json_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        legs = payload["legs"]["value"]
        check("lean-leg-ran",
              str(legs.get("lean_live", "")).startswith("ran"),
              "lean_live leg record: %r" % legs.get("lean_live"))
        check("lean-live-verdict-match",
              payload["verdict"]["value"] == "MATCH"
              and all(p["verdict"] == "MATCH"
                      for p in payload["pairs"]["value"]),
              "verdict=%s over %d pairs with the live Lean side"
              % (payload["verdict"]["value"],
                 len(payload["pairs"]["value"])))
    return lines


# ---- total (the t_axiom_audit segment form) ----

def _leg_functions():
    return dict((name[8:], obj) for name, obj in globals().items()
                if name.startswith("run_leg_") and callable(obj))


def run_total():
    lines, passed, failed = [], 0, 0
    skipped = False
    legs = _leg_functions()
    for name in sorted(legs):
        fn = legs[name]
        try:
            leg_lines = fn()
        except Exception as exc:  # fail-loud: a raising leg is a fail
            failed += 1
            lines.append("FAIL leg %s: raised %r" % (name, exc))
            continue
        p = sum(1 for ln in leg_lines if ln.startswith("PASS "))
        f = sum(1 for ln in leg_lines if ln.startswith("FAIL "))
        passed += p
        failed += f
        if any(ln.startswith("SKIP") for ln in leg_lines):
            skipped = True
        lines.extend(leg_lines)
        lines.append("LEG %s passed=%d failed=%d" % (name, p, f))
    lines.append("SUMMARY legs=%d passed=%d failed=%d skipped=%s"
                 % (len(legs), passed, failed, skipped))
    return passed, failed, skipped, lines


def main():
    _passed, failed, skipped, lines = run_total()
    for line in lines:
        print(line)
    if failed:
        print("TOTAL-LEAN-PARITY RED (%d failed check(s))" % failed)
        return 1
    if skipped:
        print("TOTAL-LEAN-PARITY SKIP-FACE (a gated leg skipped loudly;"
              " the engines-present machine runs the full sweep)")
        return 111
    print("TOTAL-LEAN-PARITY GREEN (all legs ran and matched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
