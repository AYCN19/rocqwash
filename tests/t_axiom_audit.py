#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/t_axiom_audit.py -- axiom_audit tool suite hook (tests/).

Purpose.  Drives tools/axiom_audit.py (the beyond-platform axiom audit:
  transitive per-statement census, four-grade classification, reverse
  provenance map, machine-readable report with a Lean parity table)
  through its contract: offline classification and census-parse vectors,
  the CLI exit-code faces, and the engine-gated fixture faces over
  tests/fixtures/axiom_audit (the three known-axiom-set forms: a
  zero-axiom theorem, platform-sourced axioms, custom axioms).
Interface.  `python3 -B tests/t_axiom_audit.py` runs every segment
  (PASS / FAIL check lines; loud SKIP lines carry their reason and are
  never red) and exits 0 when no FAIL line was produced, 1 otherwise.
  Segments: offline_vectors (module import, no toolchain), cli_contract
  (self-spawn exit codes 2 / 9 / 111), engine_census and engine_report
  (compile engine required; skipped loudly when no engine resolves from
  the flag / ROCWASH_ROCQ / PATH).
Dependencies.  Python 3 standard library only; the tool under test
  loads by file path (importlib); the committed fixture corpus is read
  through the tool's own private temp workdir; zero network; writes
  only inside temporary directories.
Evidence.  Every engine segment asserts exact census sets and exact
  grades (classic / functional_extensionality_dep / Eq_rect_eq.eq_rect_eq
  / the two custom_axiom.v declarations; see the WANT_CENSUS note below
  for the CI-face anchoring of the custom pair), the reverse provenance
  map, both judgment directions (full allowlist green rc 0, empty
  allowlist red rc 1), the report JSON schema rocqwash.b-axiom-audit/1
  and the printed parity table.
Exit-codes.  0 = no FAIL line produced; 1 = at least one FAIL.
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
TOOL_PATH = REPO / "tools" / "axiom_audit.py"
FIXTURE_DIR = REPO / "tests" / "fixtures" / "axiom_audit"
EXPECTED_SCHEMA = "rocqwash.b-axiom-audit/1"
EXPECTED_SEGMENTS = ["offline_vectors", "cli_contract", "engine_census",
                     "engine_report"]

# Exact fixture expectations (measured on Rocq 9.1.0, the standing
# engine of every engine-bearing face of this repo -- the self-hosted
# CI lane installs no toolchain of its own).  The allowlist carries
# every fixture axiom (the census-allowed-green face judges the whole
# corpus green); the three measured stdlib expansion families
# (proof_irrelevance / propositional_extensionality /
# constructive_indefinite_description, the stdlib_axiom2.v corpus) are
# allowlisted alongside the original five, mirroring the tool's own
# selftest live group.
ALLOW_ALL = ["--allow-axiom", "classic",
             "--allow-axiom", "functional_extensionality_dep",
             "--allow-axiom", "Eq_rect_eq.eq_rect_eq",
             "--allow-axiom", "proof_irrelevance",
             "--allow-axiom", "propositional_extensionality",
             "--allow-axiom", "constructive_indefinite_description",
             "--allow-axiom", "ax_audit_custom",
             "--allow-axiom", "ax_audit_param"]
# t_axaudit_custom censuses BOTH custom_axiom.v declarations on the
# judging face.  The census surface for this statement is
# engine-dependent (both faces measured on the same host, 2026-11-22):
# CI evidence (run 45039174608, job 137259541458, LIVE-ROCQWASH runner,
# head 9332c2b) reports ('axioms', ['ax_audit_custom', 'ax_audit_param'])
# while an interactive dev-shell probe against the Rocq 9.1.0 platform
# install reports ('axioms', ['ax_audit_custom']).  Mechanism: the
# Parameter ax_audit_param (custom_axiom.v line 1) is carried in
# ax_audit_custom's TYPE ("ax_audit_param = ax_audit_param"); the
# runner-face census surfaces it in the assumption set, the dev-shell
# engine folds it away.  A single static expectation cannot match both
# engines, so the contract below splits the surface: WANT_CENSUS holds
# the engine-independent core (the declared Axiom) and
# WANT_CENSUS_OPTIONAL names the engine-dependent extras, which are
# tolerated but never required.  The Parameter stays visible on every
# face through the engine-independent declared-axiom sweep
# (WANT_DECLARED).
WANT_CENSUS = {
    ("axaudit_clean.v", "t_axaudit_closed"): ("closed", []),
    ("stdlib_axiom.v", "t_axaudit_classic"): ("axioms", ["classic"]),
    ("stdlib_axiom.v", "t_axaudit_funext"):
        ("axioms", ["functional_extensionality_dep"]),
    ("stdlib_axiom.v", "t_axaudit_k"):
        ("axioms", ["Eq_rect_eq.eq_rect_eq"]),
    ("custom_axiom.v", "t_axaudit_custom"):
        ("axioms", ["ax_audit_custom"]),
}
WANT_CENSUS_OPTIONAL = {
    ("custom_axiom.v", "t_axaudit_custom"): ["ax_audit_param"],
}
WANT_GRADES = {
    "classic": "classical",
    "functional_extensionality_dep": "funext",
    "Eq_rect_eq.eq_rect_eq": "stdlib",
    "ax_audit_custom": "custom",
    # ax_audit_param lands an inventory row wherever the census carries
    # it (the inventory is built from the census rows' axiom lists:
    # tools/axiom_audit.py maps every row axiom to consumers and one
    # inventory entry), and the CI face carries it (run 45039174608,
    # see the WANT_CENSUS note).  Its grade is the pure declared-name
    # rule -- a tree-declared Parameter grades custom; verified on this
    # host: `classify --name ax_audit_param` prints
    # "ax_audit_param custom".
    "ax_audit_param": "custom",
}
WANT_DECLARED = [
    {"name": "ax_audit_custom", "file": "custom_axiom.v", "line": 2,
     "form": "Axiom"},
    {"name": "ax_audit_param", "file": "custom_axiom.v", "line": 1,
     "form": "Parameter"},
]


def load_tool():
    """The tool module by file path (importlib; no package context)."""
    spec = importlib.util.spec_from_file_location("axiom_audit_module",
                                                  str(TOOL_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_engine():
    """The compile engine path, or None (mirrors the tool's order)."""
    env_bin = os.environ.get("ROCWASH_ROCQ", "")
    if env_bin:
        return env_bin
    for name in ("coqc", "rocq"):
        found = shutil.which(name)
        if found:
            return found
    return None


def spawn_tool(argv, env=None):
    """One tool run as (rc, merged stdout/stderr text)."""
    full_env = dict(os.environ) if env is None else env
    try:
        pr = subprocess.run([sys.executable, "-B", str(TOOL_PATH)] + argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300,
                            env=full_env)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    text = pr.stdout.decode("utf-8", "replace")
    return pr.returncode, text


# ---- segment 1: offline vectors (module import; no toolchain) ----

def run_segment_offline_vectors():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    tool = load_tool()
    table = [
        ("classic", set(), tool.GRADE_CLASSICAL),
        ("classic_dep", set(), tool.GRADE_CLASSICAL),
        ("Coq.Logic.Classical_Prop.classic", set(), tool.GRADE_CLASSICAL),
        ("Stdlib.Logic.Classical_Prop.classic", set(),
         tool.GRADE_CLASSICAL),
        ("functional_extensionality", set(), tool.GRADE_FUNEXT),
        ("functional_extensionality_dep", set(), tool.GRADE_FUNEXT),
        ("Stdlib.Logic.FunctionalExtensionality."
         "functional_extensionality_dep", set(), tool.GRADE_FUNEXT),
        ("Eq_rect_eq.eq_rect_eq", set(), tool.GRADE_STDLIB),
        ("Coq.Logic.Eqdep.EqdepFacts.eq_dep", set(), tool.GRADE_STDLIB),
        ("ax_audit_custom", {"ax_audit_custom"}, tool.GRADE_CUSTOM),
        ("undeclared_bare_name", set(), tool.GRADE_CUSTOM),
        ("classic", {"classic"}, tool.GRADE_CUSTOM),
    ]
    bad = [(nm, tool.classify_axiom(nm, decl), want)
           for nm, decl, want in table
           if tool.classify_axiom(nm, decl) != want]
    check("classify-table", not bad,
          "%d names graded exactly; mismatches=%s" % (len(table), bad))
    batch = ("warning line before any marker\n"
             "Closed under the global context\n"
             "Axioms:\n"
             "classic : forall P : Prop, P /\\ ~ P\n"
             "Axioms:\n"
             "functional_extensionality_dep :\n"
             "  forall (A : Type) (B : A -> Type) (f g : forall x : A, "
             "B x),\n"
             "  (forall x : A, f x = g x) -> f = g\n")
    blocks = tool.parse_census_blocks(batch, 3)
    check("census-batch-parse",
          blocks == [("closed", []), ("axioms", ["classic"]),
                     ("axioms", ["functional_extensionality_dep"])],
          "ordered markers map exactly (preamble skipped, wrapped entry "
          "carried); blocks=%s" % (blocks,))
    check("census-mismatch-falls-back",
          tool.parse_census_blocks("Closed under the global context\n",
                                   2) is None
          and tool.parse_census_blocks(batch, 4) is None,
          "marker count mismatch yields None (fallback trigger)")
    sample = ("(* Theorem decoy_in_comment : False. *)\n"
              "Theorem t_live_one : True.\n"
              "Proof. exact I. Qed.\n"
              "Definition hidden := \"Theorem decoy_in_string : False.\"\n"
              "Axiom ax_live_custom : True = True.\n")
    got = tool.statement_names(sample)
    check("statement-names-masked", got == [("t_live_one", 2)],
          "comment and string decoys never census; got=%s" % (got,))
    got = tool.declared_axioms(sample)
    check("declaration-sweep-masked",
          got == [("ax_live_custom", 5, "Axiom")],
          "live declaration carried with line and form; got=%s" % (got,))
    return lines


# ---- segment 2: CLI contract (self-spawn; engine-independent) ----

def run_segment_cli_contract():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    rc, _out = spawn_tool([])
    check("exit-usage-error-rc2", rc == 2,
          "no subcommand exits %s (usage error)" % rc)
    rc, _out = spawn_tool(["classify"])
    check("classify-missing-name-rc2", rc == 2,
          "classify without --name exits %s (usage error)" % rc)
    rc, _out = spawn_tool(["census", "--repo", str(REPO / "no-such-dir")])
    check("exit-repo-absent-rc9", rc == 9,
          "missing --repo exits %s (fail-loud)" % rc)
    rc, _out = spawn_tool(["census", "--repo", str(REPO), "--rocq",
                           str(Path(os.devnull).parent / "no-engine")])
    check("exit-binary-absent-rc9", rc == 9,
          "configured but missing engine exits %s (fail-loud)" % rc)
    bare = {"PATH": "/rocqwash-axiom-audit-no-such-path"}
    rc, out = spawn_tool(["census", "--repo", str(REPO)], env=bare)
    check("exit-unconfigured-rc111", rc == 111 and "SKIP" in out,
          "unconfigured engine exits %s with the loud skip line" % rc)
    rc, out = spawn_tool(["classify", "--name", "classic"])
    check("classify-lookup-rc0",
          rc == 0 and out.splitlines() == ["classic classical"],
          "the classify lookup answers one line and exits %s; out=%r"
          % (rc, out.splitlines()))
    return lines


# ---- segment 3: engine census faces (fixtures; engine required) ----

def run_segment_engine_census():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    engine = resolve_engine()
    if engine is None or not os.path.exists(engine):
        lines.append("SKIP engine_census - compile engine not configured "
                     "(flag / ROCWASH_ROCQ / PATH)")
        return lines
    if not FIXTURE_DIR.is_dir():
        check("fixture-corpus-present", False,
              "missing fixture corpus: %s" % FIXTURE_DIR)
        return lines
    with tempfile.TemporaryDirectory(
            prefix="t_axiom_audit_census_") as tmp:
        json_path = os.path.join(tmp, "census.json")
        rc, out = spawn_tool(["census", "--repo", str(FIXTURE_DIR),
                              "--json", json_path] + ALLOW_ALL)
        check("census-allowed-green",
              rc == 0 and "AXIOM-AUDIT: PASS" in out,
              "full allowlist judges the fixtures green (rc=%s)" % rc)
        with io_open(json_path) as fh:
            report = json.load(fh)
        rows = {}
        for f in report["files"]:
            for r in f["census"]:
                rows[(f["file"], r["statement"])] = r
        bad = []
        for key, want in sorted(WANT_CENSUS.items()):
            got = rows.get(key)
            have = (got["verdict"], got["axioms"]) if got else None
            optional = set(WANT_CENSUS_OPTIONAL.get(key, []))
            if have is None or got["verdict"] != want[0]:
                bad.append((key, have, want))
            else:
                missing = set(want[1]) - set(got["axioms"])
                extra = set(got["axioms"]) - set(want[1]) - optional
                if missing or extra:
                    bad.append((key, have, want))
        check("census-sets-contract", not bad,
              "%d statement axiom contracts (required set present, "
              "extras limited to the declared engine-dependent surface); "
              "mismatches=%s" % (len(WANT_CENSUS), bad))
        inv = {r["axiom"]: r for r in report["axiom_inventory"]}
        # ax_audit_param's inventory row is engine-dependent (see
        # WANT_CENSUS_OPTIONAL): when the census surfaces the row, its
        # grade must still match; its absence on an engine that folds
        # the Parameter away is tolerated, never graded.
        bad = [(nm, inv[nm]["grade"] if nm in inv else None, want)
               for nm, want in sorted(WANT_GRADES.items())
               if nm in inv and inv[nm]["grade"] != want]
        check("grades-contract", not bad,
              "%d grade contracts exact when the row is surfaced; "
              "mismatches=%s" % (len(WANT_GRADES), bad))
        cust = inv.get("ax_audit_custom", {})
        check("reverse-map-exact",
              cust.get("introducing_file") == "custom_axiom.v"
              and [(c["file"], c["statement"]) for c in
                   cust.get("consumers", [])]
              == [("custom_axiom.v", "t_axaudit_custom")],
              "axiom -> introducing file -> consuming statement edges "
              "exact; got=%s" % (cust,))
        check("declared-sweep-exact",
              report["declared_axioms"] == WANT_DECLARED,
              "Axiom/Parameter sweep with file, line and form; got=%s"
              % (report["declared_axioms"],))
        check("schema-constant", report["schema"] == EXPECTED_SCHEMA,
              "report carries %s" % report["schema"])
        rc, out = spawn_tool(["census", "--repo", str(FIXTURE_DIR)])
        check("census-default-red", rc == 1,
              "empty default allowlist judges red (rc=%s)" % rc)
        rc, out = spawn_tool(["report", "--repo", str(FIXTURE_DIR),
                              "--out", os.path.join(tmp, "rep.json")]
                             + ALLOW_ALL)
        parity_lines = [ln for ln in out.splitlines()
                        if ln.startswith("LEAN-PARITY")
                        or ln.startswith("  ")]
        with io_open(os.path.join(tmp, "rep.json")) as fh:
            rep = json.load(fh)
        check("report-face-green", rc == 0 and rep["verdict"] == "PASS",
              "report under the allowlist exits %s verdict=%s"
              % (rc, rep["verdict"]))
        check("report-parity-table",
              "LEAN-PARITY" in out
              and "report-form comparison" in out
              and len(rep.get("lean_parity", {}).get("rows", [])) == 5
              and "no Lean engine invoked"
              in rep.get("lean_parity", {}).get("form", ""),
              "parity table printed and landed in the JSON; stdout=%d "
              "lines" % len(parity_lines))
    return lines


def io_open(path):
    return open(path, "r", encoding="utf-8")


# ---- segment 4: engine report debt face (engine required) ----

def run_segment_engine_report():
    lines = []

    def check(name, ok, detail):
        lines.append(("PASS " if ok else "FAIL ") + name + " - " + detail)
        return ok

    engine = resolve_engine()
    if engine is None or not os.path.exists(engine):
        lines.append("SKIP engine_report - compile engine not configured "
                     "(flag / ROCWASH_ROCQ / PATH)")
        return lines
    with tempfile.TemporaryDirectory(
            prefix="t_axiom_audit_debt_") as tmp:
        broken = os.path.join(tmp, "debt_repo")
        os.makedirs(broken)
        with open(os.path.join(broken, "broken.v"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("Theorem t_broken : True.\nProof. apply nonsense. Qed.\n")
        json_path = os.path.join(tmp, "debt.json")
        rc, out = spawn_tool(["audit", "--repo", broken,
                              "--json", json_path])
        with io_open(json_path) as fh:
            rep = json.load(fh)
        check("debt-not-red", rc == 0 and rep["debt_register"]
              == ["broken.v"] and rep["red_files"] == [],
              "compile-broken lands in the debt register, never red "
              "(rc=%s debt=%s)" % (rc, rep["debt_register"]))
        check("debt-summary-loud", "debt broken.v" in out,
              "the stdout summary names the debt file")
    return lines


# ---- total selftest (t_engines_seeds form) ----

def _segment_functions():
    return dict((name[12:], obj) for name, obj in globals().items()
                if name.startswith("run_segment_") and callable(obj))


def run_total_selftest():
    """Run every segment; SKIP expected-but-absent segments loudly."""
    lines, passed, failed = [], 0, 0
    found = _segment_functions()
    for name in sorted(found):
        fn = found[name]
        try:
            seg_lines = fn()
        except Exception as exc:  # fail-loud: a raising segment is a fail
            failed += 1
            lines.append("FAIL segment %s: raised %r" % (name, exc))
            continue
        p = sum(1 for ln in seg_lines if ln.startswith("PASS "))
        f = sum(1 for ln in seg_lines if ln.startswith("FAIL "))
        passed += p
        failed += f
        lines.extend(seg_lines)
        lines.append("SEGMENT %s passed=%d failed=%d" % (name, p, f))
    missing = [s for s in EXPECTED_SEGMENTS if s not in found]
    for name in missing:
        lines.append("SKIP segment %s absent from this module (merge "
                     "pending or renamed)" % name)
    lines.append("SUMMARY segments=%d expected=%d passed=%d failed=%d "
                 "missing=%d" % (len(found), len(EXPECTED_SEGMENTS),
                                 passed, failed, len(missing)))
    return passed, failed, lines


def main():
    passed, failed, lines = run_total_selftest()
    for line in lines:
        print(line)
    if failed:
        print("TOTAL-SELFTEST RED (%d failed check(s))" % failed)
        return 1
    print("TOTAL-SELFTEST GREEN (%d passed check(s))" % passed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
