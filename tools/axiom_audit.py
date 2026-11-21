#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""axiom_audit.py - beyond-platform axiom audit over a .v tree (rocqwash tools/).
Purpose.  One machine-readable transitive axiom census: each .v file
  compiles in a private temp workdir and every statement is driven
  through Print Assumptions; the tree-wide axiom surface lands as a
  reverse provenance map (axiom -> introducing file -> consuming
  statements), every axiom carries a four-level grade (stdlib /
  classical / funext / custom), and the report lands under schema
  rocqwash.b-axiom-audit/1 with a Lean parity table (report form, no
  Lean engine).  Complements axiom_guard (the coqchk kernel authority):
  this tool owns the graded census face; the exit contract is the gate
  form.
Interface.  audit --repo DIR [--rocq BIN] [--timeout SEC]
  [--allow-axiom NAME]... [--json OUT] [--keep] | census --repo DIR
  [same flags] | report --repo DIR --out FILE [same flags minus --json]
  | classify --name NAME [--name NAME]... [--declared NAME]... |
  --selftest.
Dependencies.  Python 3 standard library only; the compile engine from
  the flags, ROCWASH_ROCQ or PATH (coqc legacy form, then rocq unified
  form); never downloaded, never simulated; zero network.
Evidence.  Deterministic: sorted inputs, no wall clock in the report or
  the judgment logic, the same tree yields byte-identical JSON; write
  faces = caller-named report files plus a private temp workdir
  (removed unless --keep); --selftest runs frozen offline vectors plus,
  only when an engine resolves, the committed fixture corpus read-only.
Exit-codes.  0 green (zero non-allowlisted axioms; compile-broken is
  debt, not red); 1 red (a non-allowlisted axiom, or a selftest FAIL);
  2 usage error; 9 fail-loud environment; 111 honest skip (engine
  unconfigured; --selftest skips the live group loudly).
Usage:  python3 tools/axiom_audit.py census --repo . | --selftest
"""
# Extended contract (kept outside the five-field block per the 30-line
# annotation budget).
# Subcommand faces:
#   audit    per-module transitive axiom census over every .v under the
#            repo (except .git), sorted by relative path; stdout summary;
#            --json OUT writes the census JSON artifact.
#   census   audit plus the whole-tree aggregate: axiom inventory with
#            grade, introducing file and consumers (the reverse
#            provenance map), classification counts, run verdict.
#   report   census plus --out FILE JSON emission and the printed Lean
#            parity table; --out is required.
#   classify offline grade lookup for axiom name strings: --name NAME...
#            with the optional --declared NAME... tree-declaration face;
#            prints one "NAME grade" line per name; a lookup, not a
#            judgment (exit 0 on any answer, 2 on missing --name).
# Census mechanics: statement names come from a comment/string masking
#   scanner (decoys never census); the batched face compiles one census
#   copy carrying one "Print Assumptions <name>." line per statement and
#   maps output blocks back in order; on any marker mismatch the file
#   falls back to one census compile per statement for exact
#   attribution; a statement whose census still cannot be mapped is
#   census-error (recorded, not judged).  Statement verdicts: closed
#   (the printed "Closed under the global context" line) or axioms.
# Classification (in precedence order; grades, not a whitelist):
#   1. the name (exact or last component) matches a tree-declared
#      Axiom/Parameter/Conjecture -> custom, with the introducing file
#      recorded; a tree shadow of a platform name grades custom.
#   2. classical table hit (classic, classic_dep) or a dotted
#      ".Classical" segment -> classical.
#   3. functional extensionality table hit (functional_extensionality,
#      functional_extensionality_dep) or a dotted
#      "FunctionalExtensionality" segment -> funext.
#   4. grounded stdlib table hit (eq_rect_eq) -> stdlib.
#   5. dotted platform namespace (first segment Coq or Stdlib) ->
#      stdlib.
#   6. everything else (bare unknown, dotted non-platform unknown) ->
#      custom.  Unrecognized grades alarm: a missed platform grade is a
#      report-shape concern, never a silence face.  The tables are the
#      grounded minimum measured on Rocq 9.3.0 (Print Assumptions prints
#      bare short names for platform axioms; rocqchk prints the dotted
#      Stdlib.-prefixed forms); extend by data as new faces appear,
#      never by guess.
# Debt: a file that fails to compile (or overruns --timeout) is recorded
#   in the debt register with an error tail and is never red; the debt
#   register is loud in every summary.  Section-Variable caveat: the
#   declaration sweep grounds Axiom/Parameter/Conjecture only; a
#   Variable still open at file end is not swept (ungrounded faces are
#   disclosed, not guessed).
# Lean parity: static knowledge-face rows mapping the audit grades to
#   the rocqwash-axiom-sweep/1 Lean classes and the Lean builtin axiom
#   trio; a report-form comparison only, no Lean binary is ever invoked.
# Engine resolution order: the --rocq flag, then ROCWASH_ROCQ, then
#   PATH (coqc legacy form first, then the rocq unified CLI; the form
#   decides the compile argv: coqc -q ... versus rocq c -q ...).  An
#   unconfigured engine is an honest skip (rc 111), a configured but
#   missing binary is fail-loud (rc 9), never a simulation.
# Selftest exit face: 1 on any FAIL (red outranks skip); 111 when the
#   whole live group was skipped for the missing engine (the suite's
#   environment-absent code, rendered SKIP by the meta enumerator);
#   else 0.  The skip form was measured: 13 offline vectors PASS, 6
#   loud SKIP lines, rc 111.

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROG = "axiom_audit"
SCHEMA = "rocqwash.b-axiom-audit/1"
CLOSED_LINE = "Closed under the global context"
ERROR_TAIL_LINES = 12
GRADE_CLOSED = "closed"
GRADE_STDLIB = "stdlib"
GRADE_CLASSICAL = "classical"
GRADE_FUNEXT = "funext"
GRADE_CUSTOM = "custom"
GRADES = (GRADE_STDLIB, GRADE_CLASSICAL, GRADE_FUNEXT, GRADE_CUSTOM)

# Grounded minimum name tables (measured on Rocq 9.3.0; see the
# classification contract above).  Bare short names as Print Assumptions
# prints them; dotted faces match by segment substring.
CLASSICAL_AXIOM_NAMES = ("classic", "classic_dep")
FUNEXT_AXIOM_NAMES = ("functional_extensionality",
                      "functional_extensionality_dep")
STDLIB_AXIOM_NAMES = ("eq_rect_eq",)
PLATFORM_PREFIXES = ("Coq", "Stdlib")

# Statement families the census extracts (name-bearing vernaculars).
STMT_RE = re.compile(
    r"(?m)^[ \t]*(?:#\[[^\]]*\][ \t]*\r?\n?[ \t]*|"
    r"(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Theorem|Lemma|Corollary|Proposition|Remark|Fact|Example|Instance)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")
# Module-level assumption declarations (the provenance face).
DECL_RE = re.compile(
    r"(?m)^[ \t]*(Axiom|Parameter|Conjecture)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")

# Lean parity rows (report form; see the extended contract note).
LEAN_PARITY_ROWS = (
    (GRADE_CLOSED, "CLEAN", "(no builtin axiom needed)"),
    (GRADE_STDLIB, "BENIGN-STANDARD",
     "platform builtin trio faces (propext / Quot.sound / "
     "Classical.choice)"),
    (GRADE_CLASSICAL, "BENIGN-STANDARD", "Classical.choice"),
    (GRADE_FUNEXT, "BENIGN-STANDARD",
     "Quot.sound + propext (functional extensionality is derived)"),
    (GRADE_CUSTOM, "CUSTOM-AXIOM-ALARM",
     "(declared axiom; no Lean builtin equivalent)"),
)
LEAN_PARITY_NOTE = ("report-form comparison only; no Lean binary is "
                    "invoked; the Lean SORRY-ALARM face (sorryAx) has no "
                    "direct counterpart here because a Rocq Admitted "
                    "surfaces in the census as the admitted statement's "
                    "own name.")


# ---- static scanner faces (no engine needed) ----

def mask_comments_strings(text):
    """Blank comment and string literal bodies, keeping line structure.

    Comment contents (nested (* ... *) forms) and string literal bodies
    (with the "" escape) become spaces so line numbers survive; the
    delimiters stay.  Everything outside those faces passes through.
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    out.append("  ")
                    i += 2
                    continue
                in_str = False
                out.append(c)
                i += 1
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if depth:
            if text.startswith("(*", i):
                depth += 1
                out.append("  ")
                i += 2
                continue
            if text.startswith("*)", i):
                depth -= 1
                out.append("  ")
                i += 2
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("(*", i):
            depth += 1
            out.append("  ")
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def statement_names(text):
    """[(name, line)] for censusable statements, live faces only (1-based)."""
    masked = mask_comments_strings(text)
    return [(m.group(2), masked[:m.start()].count("\n") + 1)
            for m in STMT_RE.finditer(masked)]


def declared_axioms(text):
    """[(name, line, form)] for Axiom/Parameter/Conjecture declarations."""
    masked = mask_comments_strings(text)
    return [(m.group(2), masked[:m.start()].count("\n") + 1, m.group(1))
            for m in DECL_RE.finditer(masked)]


def classify_axiom(name, declared_names):
    """One grade for one axiom name (precedence contract in the header).

    declared_names: the set of tree-declared assumption names (exact
    forms).  Returns one of the GRADES strings.
    """
    last = name.rsplit(".", 1)[-1]
    if name in declared_names or last in declared_names:
        return GRADE_CUSTOM
    if last in CLASSICAL_AXIOM_NAMES or ".Classical" in "." + name:
        return GRADE_CLASSICAL
    if last in FUNEXT_AXIOM_NAMES or "FunctionalExtensionality" in name:
        return GRADE_FUNEXT
    if last in STDLIB_AXIOM_NAMES:
        return GRADE_STDLIB
    if "." in name and name.split(".", 1)[0] in PLATFORM_PREFIXES:
        return GRADE_STDLIB
    return GRADE_CUSTOM


def lean_parity_block():
    """The static parity rows plus the honesty note (deterministic)."""
    return {
        "form": "report-form comparison; no Lean engine invoked",
        "rows": [{"grade": g, "lean_class": lc, "lean_builtin": lb}
                 for g, lc, lb in LEAN_PARITY_ROWS],
        "note": LEAN_PARITY_NOTE,
    }


def parse_census_blocks(out_text, count):
    """Map one batched census output onto `count` ordered markers.

    Returns a list of (verdict, [axiom names]) with len == count, or
    None on any marker mismatch (the per-statement fallback trigger).
    Block grammar measured on Rocq 9.3.0: the closed statement prints
    exactly CLOSED_LINE; an assumption-bearing statement prints an
    "Axioms:" section whose entry lines start at column zero (the name
    ends at the first colon) and whose wrapped type lines are indented.
    """
    entries = []
    current = None
    for raw in out_text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped == CLOSED_LINE:
            if current is not None:
                return None
            entries.append((GRADE_CLOSED, []))
            continue
        if stripped.startswith("Axioms:"):
            # a new section head opens the next statement's block (the
            # batched output carries one "Axioms:" head per statement)
            current = []
            entries.append(("axioms", current))
            continue
        if current is not None:
            if raw[0].isspace():
                continue
            if stripped.startswith("Section Variables:"):
                current = None
                continue
            name = stripped.split(":", 1)[0].strip()
            if not name:
                return None
            current.append(name)
    if len(entries) != count:
        return None
    return entries


# ---- engine faces ----

def resolve_engine(flag_value):
    """The compile engine binary, or None when unconfigured.

    Order: the flag / environment value, then PATH (coqc legacy form,
    then rocq unified form).  Never downloads, never simulates.
    """
    if flag_value:
        return flag_value
    for name in ("coqc", "rocq"):
        found = shutil.which(name)
        if found:
            return found
    return None


def engine_form(engine):
    """The invocation form: "rocq" for the unified CLI, else "coqc"."""
    base = os.path.basename(engine).lower()
    if base.startswith("rocq"):
        return "rocq"
    return "coqc"


def engine_command(engine, work_v, src_dir, wdir):
    """The full compile argv for one census work copy."""
    form = engine_form(engine)
    if form == "rocq":
        return [engine, "c", "-q", "-Q", src_dir, "", "-Q", wdir, "",
                work_v]
    return [engine, "-q", "-Q", src_dir, "", "-Q", wdir, "", work_v]


def run_cmd(argv, timeout):
    """One subprocess run as (rc, out, err, failure).

    failure is None on a completed run (rc carries the exit code; err
    the decoded stderr) and the timeout or launch-failure message
    otherwise (rc None, out and err empty) - the axiom_guard form.
    """
    try:
        pr = subprocess.run(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", "", "timeout after %ss" % timeout
    except OSError as exc:
        return None, "", "", "engine launch failed: %s" % exc
    return (pr.returncode, pr.stdout.decode("utf-8", "replace"),
            pr.stderr.decode("utf-8", "replace"), None)


def error_tail(text, lines=ERROR_TAIL_LINES):
    """The last `lines` non-empty lines of a log, bounded."""
    kept = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    return kept[-lines:]


# ---- per-file census ----

def census_file(engine, abs_path, rel, timeout, work, log_dir, tag):
    """One file's transitive census entry (compile, batch, fallback)."""
    stem = os.path.basename(abs_path)[:-2]
    wdir = os.path.join(work, tag)
    os.makedirs(wdir)
    src_dir = os.path.dirname(abs_path)
    with io.open(abs_path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", "replace")
    masked = mask_comments_strings(text)
    stmts = statement_names(text)
    entry = {"file": rel,
             "md5": hashlib.md5(raw).hexdigest(),
             "statements": [{"name": nm, "line": ln} for nm, ln in stmts],
             "census": []}
    work_v = os.path.join(wdir, stem + ".v")
    with io.open(work_v, "wb") as fh:
        fh.write(raw)
    rc, cout, cerr, failure = run_cmd(
        engine_command(engine, work_v, src_dir, wdir), timeout)
    with io.open(os.path.join(log_dir, tag + ".compile.log"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(cout)
        fh.write(cerr)
    if failure is not None:
        entry["classification"] = "compile-broken"
        entry["compile_rc"] = None
        entry["error_tail"] = error_tail(failure)
        return entry
    if rc != 0:
        entry["classification"] = "compile-broken"
        entry["compile_rc"] = rc
        entry["error_tail"] = error_tail(cout + "\n" + cerr)
        return entry
    entry["classification"] = "compile-ok"
    entry["compile_rc"] = 0

    def census_parse(census_text, names):
        blocks = parse_census_blocks(census_text, len(names))
        if blocks is None:
            return None
        return [(names[k][0], names[k][1], blocks[k][0], blocks[k][1])
                for k in range(len(names))]

    results = None
    if stmts:
        census_v = os.path.join(wdir, stem + "_axcensus.v")
        probe = "".join("Print Assumptions %s.\n" % nm for nm, _ in stmts)
        with io.open(census_v, "wb") as fh:
            fh.write(raw)
            fh.write(probe.encode("utf-8"))
        rc2, out2, err2, fail2 = run_cmd(
            engine_command(engine, census_v, src_dir, wdir), timeout)
        with io.open(os.path.join(log_dir, tag + ".census.log"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(out2)
            fh.write(err2)
        if fail2 is None and rc2 == 0:
            results = census_parse(out2, stmts)
        if results is None:
            # per-statement fallback: one census compile per statement
            results = []
            for k, (nm, ln) in enumerate(stmts):
                one_v = os.path.join(wdir, "%s_c%03d.v" % (stem, k))
                with io.open(one_v, "wb") as fh:
                    fh.write(raw)
                    fh.write(("Print Assumptions %s.\n" % nm)
                             .encode("utf-8"))
                rck, outk, errk, failk = run_cmd(
                    engine_command(engine, one_v, src_dir, wdir), timeout)
                with io.open(os.path.join(
                        log_dir, "%s.c%03d.log" % (tag, k)), "w",
                        encoding="utf-8", newline="\n") as fh:
                    fh.write(outk)
                    fh.write(errk)
                block = None
                if failk is None and rck == 0:
                    block = parse_census_blocks(outk, 1)
                if block is None:
                    results.append((nm, ln, "census-error", []))
                else:
                    results.append((nm, ln, block[0][0], block[0][1]))
    else:
        results = []
    entry["census"] = [{"statement": nm, "line": ln, "verdict": vd,
                        "axioms": sorted(set(axs))}
                       for nm, ln, vd, axs in results]
    return entry


# ---- tree faces ----

def v_files_under(repo):
    """[(rel, abs)] for every .v under repo except .git, sorted."""
    found = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames
                       if d != ".git" and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".v"):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, repo).replace(os.sep, "/")
                found.append((rel, abs_path))
    found.sort()
    return found


def base_report(repo, engine, allow_axioms):
    """The report skeleton shared by every judgment face (deterministic)."""
    return {
        "schema": SCHEMA,
        "tool": PROG,
        "repo": os.path.abspath(repo),
        "engine": {"binary": engine, "form": engine_form(engine)},
        "standard": "zero non-allowlisted axioms in any judged statement "
                    "(default allowlist empty)",
        "allow_axioms": sorted(set(allow_axioms)),
        "files_scanned": 0,
        "files": [],
        "declared_axioms": [],
        "axiom_inventory": [],
        "classification_counts": {g: 0 for g in GRADES},
        "debt_register": [],
        "red_files": [],
        "verdict": "PASS",
    }


def run_audit(repo, engine, allow_axioms, timeout, out_json, keep,
              with_parity=False):
    """The shared census face: returns (exit_code, report).

    with_parity (the report face) embeds the static Lean parity block
    in the emitted JSON; the audit / census faces stay lean.
    """
    pairs = v_files_under(repo)
    work = tempfile.mkdtemp(prefix="rocqwash_axiom_audit_")
    log_dir = os.path.join(work, "logs")
    os.makedirs(log_dir)
    report = base_report(repo, engine, allow_axioms)
    report["files_scanned"] = len(pairs)
    reds = []
    try:
        # provenance pre-pass: the whole-tree declaration map (pure text)
        declared = {}
        for rel, abs_path in pairs:
            with io.open(abs_path, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
            for nm, ln, form in declared_axioms(text):
                declared.setdefault(nm, {"file": rel, "line": ln,
                                         "form": form})
        report["declared_axioms"] = [
            {"name": nm, "file": declared[nm]["file"],
             "line": declared[nm]["line"], "form": declared[nm]["form"]}
            for nm in sorted(declared)]
        declared_names = set(declared)
        allowed = set(report["allow_axioms"])
        consumers = {}
        for idx, (rel, abs_path) in enumerate(pairs):
            tag = "f%03d_%s" % (idx, os.path.basename(abs_path)[:-2])
            entry = census_file(engine, abs_path, rel, timeout, work,
                                log_dir, tag)
            if entry["classification"] == "compile-broken":
                report["debt_register"].append(rel)
                report["files"].append(entry)
                continue
            for row in entry["census"]:
                for ax in row["axioms"]:
                    consumers.setdefault(ax, []).append(
                        {"file": rel, "statement": row["statement"],
                         "line": row["line"]})
                alarm = [ax for ax in row["axioms"]
                         if ax not in allowed]
                if alarm and rel not in reds:
                    reds.append(rel)
            report["files"].append(entry)
        inventory = []
        counts = {g: 0 for g in GRADES}
        for ax in sorted(consumers):
            grade = classify_axiom(ax, declared_names)
            counts[grade] += 1
            intro = declared.get(ax)
            inventory.append({
                "axiom": ax,
                "grade": grade,
                "allowed": ax in allowed,
                "introducing_file": intro["file"] if intro else None,
                "consumers": sorted(
                    consumers[ax],
                    key=lambda c: (c["file"], c["statement"], c["line"])),
            })
        report["axiom_inventory"] = inventory
        report["classification_counts"] = counts
        report["red_files"] = reds
        report["verdict"] = "RED" if reds else "PASS"
        if with_parity:
            report["lean_parity"] = lean_parity_block()
        if out_json:
            out_dir = os.path.dirname(os.path.abspath(out_json))
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with io.open(out_json, "w", encoding="utf-8",
                         newline="\n") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=1,
                          sort_keys=True)
                fh.write("\n")
            print("report -> %s" % out_json)
        summarize(report)
        return (1 if reds else 0), report
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def summarize(report):
    """The stdout summary face (loud; deterministic line forms)."""
    print("AXIOM-AUDIT: %s" % report["verdict"])
    print("  schema %s" % report["schema"])
    print("  files scanned: %d (debt %d)"
          % (report["files_scanned"], len(report["debt_register"])))
    for f in report["files"]:
        if f["classification"] == "compile-broken":
            print("  debt %s (rc %s)" % (f["file"], f.get("compile_rc")))
            continue
        closed = sum(1 for r in f["census"]
                     if r["verdict"] == GRADE_CLOSED)
        print("  ok   %s statements=%d closed=%d"
              % (f["file"], len(f["census"]), closed))
        for r in f["census"]:
            if r["verdict"] == "axioms":
                print("       axiom-set %s:%d %s"
                      % (r["statement"], r["line"],
                         ",".join(r["axioms"])))
    for d in report.get("declared_axioms", []):
        print("  declared %s %s:%d (%s)"
              % (d["name"], d["file"], d["line"], d["form"]))
    for row in report.get("axiom_inventory", []):
        print("  axiom %s grade=%s%s introduced_by=%s consumers=%d"
              % (row["axiom"], row["grade"],
                 " allowed" if row["allowed"] else "",
                 row["introducing_file"] or "(platform face)",
                 len(row["consumers"])))
    counts = report.get("classification_counts")
    if counts:
        print("  grades stdlib=%d classical=%d funext=%d custom=%d"
              % (counts[GRADE_STDLIB], counts[GRADE_CLASSICAL],
                 counts[GRADE_FUNEXT], counts[GRADE_CUSTOM]))
    for rel in report.get("red_files", []):
        print("  RED  %s" % rel)


def print_parity_table():
    """The Lean parity table face (report form)."""
    print("LEAN-PARITY (report form; no Lean engine invoked):")
    block = lean_parity_block()
    for row in block["rows"]:
        print("  %-10s -> %-18s %s"
              % (row["grade"], row["lean_class"], row["lean_builtin"]))
    print("  note: %s" % block["note"])


# ---- classify face ----

def run_classify(names, declared_names):
    """Print one "NAME grade" line per name; a lookup, not a judgment."""
    for nm in names:
        print("%s %s" % (nm, classify_axiom(nm, set(declared_names))))
    return 0


# ---- selftest ----

# Frozen offline vectors (zero network, zero toolchain launch).

CENSUS_BATCH_TEXT = (
    "warning line before any marker\n"
    "Closed under the global context\n"
    "Axioms:\n"
    "classic : forall P : Prop, P /\\ ~ P\n"
    "Axioms:\n"
    "functional_extensionality_dep :\n"
    "  forall (A : Type) (B : A -> Type) (f g : forall x : A, B x),\n"
    "  (forall x : A, f x = g x) -> f = g\n")
CENSUS_BATCH_STMTS = [("t_one", 2), ("t_two", 5), ("t_three", 8)]

SAMPLE_V_TEXT = (
    "(* Theorem decoy_in_comment : False. *)\n"
    "Theorem t_live_one : True.\n"
    "Proof. exact I. Qed.\n"
    "\n"
    "Definition hidden := \"Theorem decoy_in_string : False.\"\n"
    "\n"
    "Axiom ax_live_custom : True = True.\n"
    "(* Axiom decoy_axiom_in_comment : False. *)\n")

CLASSIFY_TABLE = [
    ("classic", (), GRADE_CLASSICAL),
    ("classic_dep", (), GRADE_CLASSICAL),
    ("Coq.Logic.Classical_Prop.classic", (), GRADE_CLASSICAL),
    ("Stdlib.Logic.Classical_Prop.classic", (), GRADE_CLASSICAL),
    ("functional_extensionality", (), GRADE_FUNEXT),
    ("functional_extensionality_dep", (), GRADE_FUNEXT),
    ("Stdlib.Logic.FunctionalExtensionality.functional_extensionality_dep",
     (), GRADE_FUNEXT),
    ("Eq_rect_eq.eq_rect_eq", (), GRADE_STDLIB),
    ("Coq.Logic.Eqdep.EqdepFacts.eq_dep", (), GRADE_STDLIB),
    ("ax_audit_custom", ("ax_audit_custom",), GRADE_CUSTOM),
    ("totally_unknown_axiom", (), GRADE_CUSTOM),
    ("classic", ("classic",), GRADE_CUSTOM),
]


def selftest():
    """Frozen offline vectors plus the engine-gated live fixture group.

    Offline vectors always run (zero network, zero toolchain launch).
    The live group drives the committed tests/fixtures/axiom_audit
    corpus (read-only repo touch) and needs a compile engine; with no
    engine it prints loud SKIP lines and the run carries the suite skip
    code 111.  Returns 1 on any FAIL, 111 when every live vector was
    skipped for the missing engine, else 0.
    """
    failures = []
    total = [0]

    def vec(name, ok, detail):
        total[0] += 1
        print(("PASS " if ok else "FAIL ") + name + " - " + detail)
        if not ok:
            failures.append(name)

    def skip(name, detail):
        print("SKIP " + name + " - " + detail)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_axiom_audit_selftest_")
    try:
        # classification table (the graded enum, precedence included)
        ok = True
        for nm, decl, want in CLASSIFY_TABLE:
            got = classify_axiom(nm, set(decl))
            if got != want:
                ok = False
                vec("classify-table", False,
                    "%s -> %s (want %s)" % (nm, got, want))
                break
        if ok:
            vec("classify-table", True,
                "%d names graded exactly (%d precedence rows included)"
                % (len(CLASSIFY_TABLE), 2))
        # census batch parse (ordered markers, wrapped entries, preamble)
        blocks = parse_census_blocks(CENSUS_BATCH_TEXT, 3)
        ok = (blocks is not None and blocks[0] == (GRADE_CLOSED, [])
              and blocks[1] == ("axioms", ["classic"])
              and blocks[2] == ("axioms",
                                ["functional_extensionality_dep"]))
        vec("census-batch-parse", ok, "blocks=%s" % (blocks,))
        vec("census-mismatch-falls-back",
            parse_census_blocks(CLOSED_LINE + "\n", 2) is None
            and parse_census_blocks(CENSUS_BATCH_TEXT, 4) is None,
            "marker count mismatch yields None (fallback trigger)")
        # masking scanner (decoys never census; live faces intact)
        got_stmts = statement_names(SAMPLE_V_TEXT)
        vec("statement-names-masked", got_stmts == [("t_live_one", 2)],
            "got=%s" % (got_stmts,))
        got_decls = declared_axioms(SAMPLE_V_TEXT)
        vec("declaration-sweep-masked",
            got_decls == [("ax_live_custom", 7, "Axiom")],
            "got=%s" % (got_decls,))
        masked = mask_comments_strings(SAMPLE_V_TEXT)
        vec("masking-blanks-decoys",
            "decoy" not in masked
            and masked.splitlines()[1].startswith("Theorem t_live_one")
            and masked.splitlines()[6].startswith("Axiom ax_live_custom"),
            "comment and string bodies blanked; live faces intact")
        # schema assembly (deterministic, parity block present)
        rep_a = base_report("/tmp/x", "/bin/coqc", [])
        rep_b = base_report("/tmp/x", "/bin/coqc", [])
        vec("schema-determinism",
            json.dumps(rep_a, sort_keys=True) == json.dumps(
                rep_b, sort_keys=True)
            and rep_a["schema"] == SCHEMA
            and set(rep_a["classification_counts"]) == set(GRADES),
            "byte-identical skeletons; schema constant; grade keys fixed")
        vec("parity-block-shape",
            [r["grade"] for r in lean_parity_block()["rows"]]
            == [GRADE_CLOSED, GRADE_STDLIB, GRADE_CLASSICAL,
                GRADE_FUNEXT, GRADE_CUSTOM]
            and "no Lean engine invoked" in lean_parity_block()["form"]
            and "sorryAx" in lean_parity_block()["note"],
            "five rows cover closed plus the four grades; honesty notes "
            "carry the report-form disclosure and the sorryAx caveat")
        # exit-code contract (self-spawn; the documented 0/1/2 plus the
        # 9 fail-loud and 111 honest-skip environment faces)
        def spawn(argv, env=None):
            try:
                p = subprocess.run([sys.executable, "-B", script] + argv,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=60,
                                   env=env)
            except subprocess.TimeoutExpired:
                return None, "timeout"
            out = p.stdout.decode("utf-8", "replace") \
                if isinstance(p.stdout, bytes) else (p.stdout or "")
            return p.returncode, out

        rc, _out = spawn([])
        vec("exit-usage-error-rc2", rc == 2,
            "no subcommand exits %s (usage error)" % rc)
        rc, _out = spawn(["classify"])
        vec("classify-missing-name-rc2", rc == 2,
            "classify without --name exits %s (usage error)" % rc)
        absent_repo = os.path.join(tmp, "absent-repo")
        rc, _out = spawn(["census", "--repo", absent_repo])
        vec("exit-repo-absent-rc9", rc == 9,
            "missing --repo exits %s (fail-loud)" % rc)
        rc, _out = spawn(["census", "--repo", tmp,
                          "--rocq", os.path.join(tmp, "no-engine")])
        vec("exit-binary-absent-rc9", rc == 9,
            "configured but missing engine exits %s (fail-loud)" % rc)
        bare_env = dict(os.environ)
        bare_env.pop("ROCWASH_ROCQ", None)
        bare_env["PATH"] = "/rocqwash-axiom-audit-no-such-path"
        rc, out = spawn(["census", "--repo", tmp], env=bare_env)
        vec("exit-unconfigured-rc111", rc == 111 and "SKIP" in out,
            "unconfigured engine exits %s with the loud skip line; "
            "stdout=%r" % (rc, out[:80]))
        # live group: the committed fixture corpus (read-only repo
        # touch), only when a compile engine resolves.
        engine = resolve_engine(os.environ.get("ROCWASH_ROCQ", ""))
        fixture_dir = os.path.join(
            os.path.dirname(os.path.dirname(script)),
            "tests", "fixtures", "axiom_audit")
        if engine is None or not os.path.exists(engine):
            for live in ("live-run-green", "live-judgment-red",
                         "live-clean-closed", "live-platform-grades",
                         "live-custom-reverse-map", "live-report-schema"):
                skip(live, "compile engine not configured "
                           "(coqc legacy / rocq unified; rc 111 suite "
                           "skip)")
            print("selftest: %d vector(s), %d FAIL, 6 SKIP (engine "
                  "absent)" % (total[0], len(failures)))
            if failures:
                print("selftest RED: %s" % ", ".join(failures))
                return 1
            return 111
        if not os.path.isdir(fixture_dir):
            vec("live-fixture-dir", False,
                "engine present but fixture corpus missing: %s"
                % fixture_dir)
        else:
            # judgment face, both directions: the full allowlist lands
            # green, the empty default allowlist lands red (the fixtures
            # deliberately carry five axioms)
            allows = ["--allow-axiom", "classic",
                      "--allow-axiom", "functional_extensionality_dep",
                      "--allow-axiom", "Eq_rect_eq.eq_rect_eq",
                      "--allow-axiom", "ax_audit_custom",
                      "--allow-axiom", "ax_audit_param"]
            rc, _out = spawn(["census", "--repo", fixture_dir,
                              "--json", os.path.join(tmp, "live.json")]
                             + allows)
            with io.open(os.path.join(tmp, "live.json"), "r",
                         encoding="utf-8") as fh:
                live = json.load(fh)
            vec("live-run-green", rc == 0 and live["verdict"] == "PASS",
                "census under the full allowlist rc=%s verdict=%s"
                % (rc, live["verdict"]))
            rc, _out = spawn(["census", "--repo", fixture_dir])
            vec("live-judgment-red", rc == 1,
                "empty default allowlist judges the fixture axioms red "
                "(rc=%s)" % rc)
            rows = {}
            for f in live["files"]:
                for r in f["census"]:
                    rows[(f["file"], r["statement"])] = r
            clean = rows.get(("axaudit_clean.v", "t_axaudit_closed"))
            vec("live-clean-closed",
                clean is not None and clean["verdict"] == GRADE_CLOSED
                and clean["axioms"] == [],
                "the zero-axiom theorem censuses closed; %s" % (clean,))
            want = {("stdlib_axiom.v", "t_axaudit_classic"):
                    ["classic"],
                    ("stdlib_axiom.v", "t_axaudit_funext"):
                    ["functional_extensionality_dep"],
                    ("stdlib_axiom.v", "t_axaudit_k"):
                    ["Eq_rect_eq.eq_rect_eq"]}
            ok = all(key in rows
                     and rows[key]["verdict"] == "axioms"
                     and rows[key]["axioms"] == want[key]
                     for key in want)
            vec("live-platform-grades", ok,
                "classical/funext/stdlib axiom sets match exactly; %s"
                % sorted(k for k in want if k not in rows
                         or rows[k]["axioms"] != want[k]))
            inv = {r["axiom"]: r for r in live["axiom_inventory"]}
            cust = inv.get("ax_audit_custom")
            vec("live-custom-reverse-map",
                cust is not None and cust["grade"] == GRADE_CUSTOM
                and cust["introducing_file"] == "custom_axiom.v"
                and [(c["file"], c["statement"])
                     for c in cust["consumers"]]
                == [("custom_axiom.v", "t_axaudit_custom")]
                and inv["classic"]["grade"] == GRADE_CLASSICAL
                and inv["functional_extensionality_dep"]["grade"]
                == GRADE_FUNEXT
                and inv["Eq_rect_eq.eq_rect_eq"]["grade"]
                == GRADE_STDLIB,
                "custom axiom carries the reverse map "
                "(introducing file + consumer statement); platform "
                "grades land classical/funext/stdlib")
            vec("live-report-schema",
                live["schema"] == SCHEMA
                and live["declared_axioms"]
                == [{"name": "ax_audit_custom", "file": "custom_axiom.v",
                     "line": 2, "form": "Axiom"},
                    {"name": "ax_audit_param", "file": "custom_axiom.v",
                     "line": 1, "form": "Parameter"}]
                and live["classification_counts"]
                == {GRADE_STDLIB: 1, GRADE_CLASSICAL: 1,
                    GRADE_FUNEXT: 1, GRADE_CUSTOM: 2},
                "schema constant, declaration sweep, grade counts")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d vector(s), %d FAIL" % (total[0], len(failures)))
    if failures:
        print("selftest RED: %s" % ", ".join(failures))
        return 1
    return 0


# ---- flag face ----

def build_parser():
    """The flag face (extracted so --selftest runs standalone)."""
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="Beyond-platform axiom audit: transitive per-statement "
                    "census, four-grade classification, reverse provenance "
                    "map, machine-readable report with a Lean parity table.")
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group plus the "
                         "engine-gated live fixture group and exit")
    sub = ap.add_subparsers(dest="cmd")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", required=True,
                        help="repository or tree root holding the .v files")
    common.add_argument("--rocq",
                        default=os.environ.get("ROCWASH_ROCQ", ""),
                        help="compile engine binary (default ROCWASH_ROCQ, "
                             "then PATH coqc / rocq)")
    common.add_argument("--timeout", type=int, default=600,
                        help="per-subprocess timeout seconds (default 600)")
    common.add_argument("--allow-axiom", action="append", default=[],
                        dest="allow_axioms",
                        help="allowlisted axiom name (repeatable; default "
                             "allowlist empty)")
    common.add_argument("--keep", action="store_true",
                        help="keep the private temp workdir (debug face)")
    pa = sub.add_parser("audit", parents=[common],
                        help="per-module transitive axiom census")
    pa.add_argument("--json", default=None,
                    help="write the census JSON artifact here")
    pc = sub.add_parser("census", parents=[common],
                        help="whole-tree census plus the reverse map")
    pc.add_argument("--json", default=None,
                    help="write the census JSON artifact here")
    pr = sub.add_parser("report", parents=[common],
                        help="census plus the JSON report and the Lean "
                             "parity table")
    pr.add_argument("--out", required=True,
                    help="report JSON path (required)")
    pcl = sub.add_parser("classify",
                         help="offline grade lookup for axiom names")
    pcl.add_argument("--name", action="append", default=[],
                     dest="names", help="axiom name to grade (repeatable)")
    pcl.add_argument("--declared", action="append", default=[],
                     dest="declared",
                     help="tree-declared assumption name (repeatable)")
    return ap


def main():
    args = build_parser().parse_args()
    if args.selftest:
        sys.exit(selftest())
    if args.cmd is None:
        build_parser().error("a subcommand (audit / census / report / "
                             "classify) or --selftest is required")
    if args.cmd == "classify":
        if not args.names:
            build_parser().error("classify needs --name NAME (repeatable)")
        sys.exit(run_classify(args.names, args.declared))
    if not os.path.isdir(args.repo):
        print("FAIL-LOUD: --repo directory missing: %s" % args.repo,
              file=sys.stderr)
        sys.exit(9)
    engine = resolve_engine(args.rocq)
    if engine is None:
        print("SKIP: no compile engine configured (flag --rocq, "
              "environment ROCWASH_ROCQ, or PATH coqc / rocq); the axiom "
              "audit honestly skips and judges nothing (rc 111)",
              file=sys.stderr)
        sys.exit(111)
    if not os.path.exists(engine):
        print("FAIL-LOUD: engine configured but binary missing: %s"
              % engine, file=sys.stderr)
        sys.exit(9)
    if args.cmd == "report":
        code, _report = run_audit(args.repo, engine, args.allow_axioms,
                                  args.timeout, args.out, args.keep,
                                  with_parity=True)
        print_parity_table()
        sys.exit(code)
    code, _report = run_audit(args.repo, engine, args.allow_axioms,
                              args.timeout, args.json, args.keep)
    sys.exit(code)


if __name__ == "__main__":
    main()
