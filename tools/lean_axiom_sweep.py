#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lean_axiom_sweep.py - per-theorem axiom-closure classifier for Lean claim audits.
Purpose.  Make "0 sorry 0 axiom" claims mechanically reproducible per theorem:
  the declaration face of the target .lean file(s) is enumerated, one checker
  file per target imports the target and prints `#print axioms <decl>` per
  declaration, the checker runs in the target's own lake environment
  (`lake env lean`) or against a direct lean binary, and the output is
  parsed into axiom sets and classified: CLEAN / BENIGN-STANDARD (subset of
  propext, Classical.choice, Quot.sound) / SORRY-ALARM (sorryAx) /
  CUSTOM-AXIOM-ALARM (any other name, verbatim) / UNPARSED (honest).
Interface.  python -I tools/lean_axiom_sweep.py --root <file|dir> [--json OUT]
  [--allow-axiom NAME]... [--timeout SEC] | --selftest.  stdout carries one
  JSON line (schema rocqwash-axiom-sweep/1); --json additionally writes the
  same payload to OUT; --selftest runs the frozen offline vectors and exits.
Dependencies.  Python 3 standard library only; the probe face needs a usable
  Lean 4 toolchain (lean or lake on PATH passing a version probe, so an
  elan shim without a default toolchain does not pass), never downloaded or
  simulated; without one the sweep exits 112 judging nothing.
Evidence.  --selftest covers the parse and classify faces with canned
  `#print axioms` fixtures for all five classes, the report shape (every
  counter wrapped {value, basis}, scan_face four fields), the checker
  emission and module-derivation faces, and the gate vector (child PATH
  stripped -> rc 112); zero network, zero toolchain launch, zero real-repo
  touch.
Exit-codes.  0 green (every classified declaration CLEAN or BENIGN-STANDARD,
  zero UNPARSED rows, zero errors); 1 red (any SORRY-ALARM,
  CUSTOM-AXIOM-ALARM or UNPARSED row, or any recorded error: unjudgeable is
  not green); 2 usage error; 112 no usable Lean toolchain (the honest skip
  names the requirement; the axiom_guard rc 111 env-gate precedent family,
  code 112 per this tool's contract).
"""

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Declaration enumeration.  Byte-literal line-start regex face: optional
# Lean 4 prefix modifiers (private/protected/noncomputable/unsafe/partial/
# local/global/export) sharing the line, then theorem|lemma|def, then the
# name (ASCII identifiers with apostrophes; quoted «...» and unicode
# spellings are outside the face and surface as absence, not guesses).
# A line-start namespace/section/end stack builds the full probe name
# (namespace pushes its name, section pushes an empty frame, end pops one);
# section/variable scoping inside a namespace is not tracked.  Comment and
# string bodies are NOT masked (the tree_audit byte-literal convention): a
# block-comment line that starts with theorem/lemma/def enters the census
# and later surfaces as an UNPARSED row instead of being silently dropped.
#
# Probe face.  For each target the module name is derived from the nearest
# ancestor holding lakefile.lean / lakefile.toml / lean-toolchain (the
# project root; a head "src" segment is dropped per the lake srcDir
# convention; with no project root the bare stem is used).  The checker
# file lives in a private temp directory (the repository tree gains zero
# bytes) and carries one import line plus one `#print axioms <name>` line
# per declaration in enumeration order.  Run form: `lake env lean
# <checker>` with cwd = the project root when lake is usable and a project
# root exists; otherwise `lean <checker>` directly (cwd = project root or
# the target's directory).  The checker output is parsed regardless of the
# child exit code (info blocks and errors share the stream); a failed probe
# leaves its declarations UNPARSED with the error tail recorded, never
# judged.
#
# Toolchain gate.  lean and lake resolve from PATH and each is probed with
# `--version`: usable means the binary exists and the probe exits 0.  This
# is deliberate: on an elan-managed host without a configured default
# toolchain the shims exist and execute but exit 1, and existence alone
# would fake a gate pass.  Neither usable -> exit 112 before any work,
# with the requirement named on stderr (honest skip, nothing simulated).
#
# Output shape.  Every top-level key except "scan_face" and the plain
# "schema" string is {"value": ..., "basis": ...} (the v2 note-5 standard,
# the tree_audit calibration face): a consumer quoting a number quotes its
# counting rule with it.  scan_face carries exactly the four fixed English
# fields scanned / not_scanned / negative_finding / equivalents and cites
# the line-start regex limitation; all four strings are module constants
# pinned verbatim by the selftest.
#
# Classification precedence (per declaration axiom set).
#   1. sorryAx present -> SORRY-ALARM (sorryAx is never admissible to the
#      whitelist: the "0 sorry" claim is this tool's audit object).
#   2. any name outside the standard trio and outside --allow-axiom ->
#      CUSTOM-AXIOM-ALARM, the custom names listed verbatim.
#   3. empty set -> CLEAN; otherwise -> BENIGN-STANDARD (the "three
#      axioms" finding [propext, Classical.choice, Quot.sound] of the
#      earlier audit work stream and subsets adjudicate here; whitelist
#      hits ride along in "allowed").
#
# Determinism.  Sorted file walk, enumeration order per file, no wall
# clock in the report, fixed string caps; the same input tree with the
# same toolchain answers byte-identically.  Temp checker files are removed
# at exit (always; no retention flag exists on this tool).

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOL = "lean_axiom_sweep"
SCHEMA = "rocqwash-axiom-sweep/1"

# The three standard Lean axioms (the "three axioms" audit face).
BENIGN_STANDARD = ("propext", "Classical.choice", "Quot.sound")
SORRY_AX = "sorryAx"

# Line-start declaration enumeration (byte-literal; comment bodies unmasked).
DECL_MODIFIERS = (r"(?:(?:private|protected|noncomputable|unsafe|partial|"
                  r"local|global|export)[ \t]+)*")
DECL_RE = re.compile(
    r"(?m)^[ \t]*" + DECL_MODIFIERS +
    r"(theorem|lemma|def)[ \t]+([A-Za-z_][A-Za-z0-9_']*)")
NAMESPACE_RE = re.compile(r"(?m)^[ \t]*namespace[ \t]+([A-Za-z_][A-Za-z0-9_'.]*)")
SECTION_RE = re.compile(r"(?m)^[ \t]*section(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")
END_RE = re.compile(r"(?m)^[ \t]*end(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")

# `#print axioms` output faces (Lean 4 CLI info blocks; the message text
# rides a "<file>:<line>:<col>: info: " prefix, so nothing is line-anchored
# here).  Anything else parses UNPARSED - honest.
CLEAN_RE = re.compile(r"'([^']+)' does not depend on any axioms")
AXIOMS_RE = re.compile(r"'([^']+)' depends on axioms:[ \t]*\[([^\]]*)\]")

PROJECT_MARKERS = ("lakefile.lean", "lakefile.toml", "lean-toolchain")
RAW_CAP = 200          # per-declaration raw probe block cap (chars)
ERROR_TAIL_LINES = 12  # per-file error tail cap (lines)
READ_ERROR_CAP = 10    # report error list cap
PROBE_TIMEOUT_DEFAULT = 600
GATE_PROBE_TIMEOUT = 20

EXIT_OK = 0
EXIT_RED = 1
EXIT_USAGE = 2
EXIT_NO_TOOLCHAIN = 112

# The four fixed scan-face strings (pinned verbatim by the selftest; the
# equivalents field cites the line-start regex limitation per contract).
SCAN_SCANNED = (
    "Every .lean file under the root, walked recursively with .git"
    " directories skipped (or the single named file); declarations are the"
    " line-start theorem/lemma/def regex with the namespace/section/end"
    " stack for full names; each declaration is probed by `#print axioms`"
    " in one generated checker file that imports the target, run via the"
    " target's own lake environment (`lake env lean`) or a direct lean"
    " binary."
)
SCAN_NOT_SCANNED = (
    "Files with any other suffix, everything under .git, declarations whose"
    " keyword is not at a line start (attribute lines, non-line-start"
    " spellings), non-theorem/lemma/def declaration families, quoted"
    " <<..>> and non-ASCII identifier spellings, and anything the toolchain"
    " environment cannot compile: a failed or missing probe block leaves"
    " its declaration UNPARSED, never judged."
)
SCAN_NEGATIVE_FINDING = (
    "A zero count is a negative finding of this scan, not an absolute"
    " claim; CLEAN means `#print axioms` reported no axiom dependency under"
    " the probed environment."
)
SCAN_EQUIVALENTS = (
    "The declaration face is the fixed line-start keyword regex; equivalent"
    " constructs spelled differently (example, instance, abbrev, structure"
    " fields) are not enumerated, and comment or string lines that mimic"
    " declarations are enumerated too (bodies are not masked) and surface"
    " as UNPARSED rows rather than being silently dropped."
)


def enumerate_decls(text):
    """[(full_name, line_no)] in file order: line-start theorem/lemma/def
    names with the namespace/section/end stack applied; comment and string
    bodies are not masked (declared scan-face limitation)."""
    out = []
    stack = []  # namespace names (section frames push "")
    line_no = 0
    for line in text.splitlines():
        line_no += 1
        m = DECL_RE.match(line)
        if m:
            parts = [p for p in stack if p]
            parts.append(m.group(2))
            out.append((".".join(parts), line_no))
            continue
        m = NAMESPACE_RE.match(line)
        if m:
            stack.append(m.group(1))
            continue
        if SECTION_RE.match(line):
            stack.append("")
            continue
        if END_RE.match(line) and stack:
            stack.pop()
    return out


def derive_module(target):
    """(module_name, project_root_or_None) for the checker's import line.

    Project root = nearest ancestor of the target holding lakefile.lean,
    lakefile.toml or lean-toolchain; the module name is the target path
    relative to that root with separators dotted and '.lean' stripped
    (a head 'src' segment is dropped, the lake srcDir convention); with no
    project root the bare stem is used."""
    path = os.path.abspath(target)
    directory = os.path.dirname(path)
    root = None
    walker = directory
    while True:
        if any(os.path.exists(os.path.join(walker, mk))
               for mk in PROJECT_MARKERS):
            root = walker
            break
        parent = os.path.dirname(walker)
        if parent == walker:
            break
        walker = parent
    base = os.path.splitext(path)[0]
    if root and base.startswith(root + os.sep):
        rel = base[len(root) + 1:]
    else:
        rel = os.path.basename(base)
    parts = rel.split(os.sep)
    if len(parts) > 1 and parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts), root


def build_checker(module, names):
    """The checker program text: one import line plus one
    `#print axioms <name>` per declaration, in enumeration order."""
    lines = []
    if module:
        lines.append("import %s" % module)
    lines.append("")
    for nm in names:
        lines.append("#print axioms %s" % nm)
    lines.append("")
    return "\n".join(lines)


def classify_axioms(axioms, allow):
    """(classification, custom_names, allowed_used) with the precedence of
    the detail block: sorryAx first (never whitelisted, and accounted by
    the sorry counter, so it never rides the custom list), then verbatim
    custom names outside the standard trio and the whitelist, then
    CLEAN / BENIGN-STANDARD."""
    rest = [a for a in axioms if a != SORRY_AX]
    custom = sorted(a for a in rest
                    if a not in BENIGN_STANDARD and a not in allow)
    allowed = sorted(a for a in rest
                     if a not in BENIGN_STANDARD and a in allow)
    if SORRY_AX in axioms:
        return "SORRY-ALARM", custom, allowed
    if custom:
        return "CUSTOM-AXIOM-ALARM", custom, allowed
    if not axioms:
        return "CLEAN", [], []
    return "BENIGN-STANDARD", [], allowed


def parse_print_axioms(output, names):
    """Attribute ordered `#print axioms` blocks to the enumerated names.

    Returns one row per name: {"ok", "axioms", "reason", "raw"}; ok=False
    rows are UNPARSED (honest).  Attribution is positional (emission
    order) with name verification: equal counts pair one-to-one; fewer
    markers leave the tail UNPARSED (a mid-file compile failure face);
    more markers than declarations means the output does not correspond
    to the emission and nothing is judged."""
    markers = []
    for m in AXIOMS_RE.finditer(output):
        axioms = [a.strip() for a in m.group(2).split(",") if a.strip()]
        markers.append((m.start(), m.group(1), axioms))
    for m in CLEAN_RE.finditer(output):
        markers.append((m.start(), m.group(1), []))
    markers.sort()
    rows = []
    if len(markers) > len(names):
        for nm in names:
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": "marker count %d exceeds declaration"
                                   " count %d; nothing attributed"
                                   % (len(markers), len(names)),
                         "raw": output[:RAW_CAP]})
        return rows
    for idx, nm in enumerate(names):
        if idx >= len(markers):
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": "no probe block found (declaration"
                                   " count %d, marker count %d)"
                                   % (len(names), len(markers)),
                         "raw": output[:RAW_CAP]})
            continue
        pos, mname, axioms = markers[idx]
        if mname != nm:
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": "probe block names %r, expected %r"
                                   % (mname, nm),
                         "raw": output[pos:pos + RAW_CAP]})
            continue
        rows.append({"name": nm, "ok": True, "axioms": axioms,
                     "reason": "", "raw": ""})
    return rows


def probe_toolchain():
    """Resolve and probe the toolchain; returns (lean, lake, usable_lean,
    usable_lake).  Usable = found on PATH and a `--version` probe exits 0
    (the elan-shim face: the shim executes but exits 1 with 'no default
    toolchain configured', so existence alone is not usability)."""
    lean = shutil.which("lean")
    lake = shutil.which("lake")

    def version_ok(binary):
        if not binary:
            return False
        try:
            p = subprocess.run([binary, "--version"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               timeout=GATE_PROBE_TIMEOUT)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return p.returncode == 0

    return lean, lake, version_ok(lean), version_ok(lake)


def collect_targets(root):
    """[(abs_path, rel_path)] sorted; a file root scans that file, a
    directory root walks *.lean skipping .git."""
    if os.path.isfile(root):
        return [(os.path.abspath(root), os.path.basename(root))]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".lean"):
                abs_path = os.path.join(dirpath, fn)
                rel = os.path.relpath(abs_path, root).replace("\\", "/")
                out.append((abs_path, rel))
    out.sort()
    return out


def error_tail(output, lines=ERROR_TAIL_LINES):
    tail = [ln for ln in output.splitlines() if ln.strip()]
    return tail[-lines:]


def run_probe(argv, cwd, timeout):
    """Subprocess run with merged streams and a hard timeout; returns
    (rc, output, error) where error is None on a clean launch, "timeout"
    on a timeout, or the OS launch failure string."""
    try:
        p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace"), None
    except subprocess.TimeoutExpired as exc:
        partial = b""
        if exc.stdout:
            partial += exc.stdout
        if exc.stderr:
            partial += exc.stderr
        return None, partial.decode("utf-8", "replace"), "timeout"
    except OSError as exc:
        return None, "", str(exc)


def sweep(root, allow, timeout):
    """The run face; returns (exit_code, report).  Write faces: the private
    temp workdir (removed on exit) and the caller-named --json file handled
    by main.  The toolchain gate has already passed when this runs."""
    lean, lake, usable_lean, usable_lake = probe_toolchain()
    targets = collect_targets(root)
    work = tempfile.mkdtemp(prefix="rocqwash_axiom_sweep_")
    file_rows = []
    decl_rows = []
    errors = []
    try:
        for idx, (abs_path, rel) in enumerate(targets):
            try:
                with open(abs_path, "rb") as fh:
                    text = fh.read().decode("utf-8", "replace")
            except OSError as exc:
                errors.append("read %s: %s" % (rel, exc))
                continue
            decls = enumerate_decls(text)
            module, project_root = derive_module(abs_path)
            frow = {"file": rel, "declarations": len(decls),
                    "module": module, "probe": "", "rc": None,
                    "error_tail": []}
            if decls:
                checker = build_checker(module, [nm for nm, _ in decls])
                checker_path = os.path.join(work, "ck_%04d.lean" % idx)
                with open(checker_path, "w", encoding="utf-8",
                          newline="\n") as fh:
                    fh.write(checker)
                if usable_lake and project_root:
                    argv = [lake, "env", "lean", checker_path]
                    cwd = project_root
                    mode = "lake-env"
                elif usable_lean:
                    argv = [lean, checker_path]
                    cwd = project_root or os.path.dirname(abs_path)
                    mode = "lean-direct"
                else:
                    argv = [lake, "env", "lean", checker_path]
                    cwd = project_root or os.path.dirname(abs_path)
                    mode = "lake-env"
                rc, output, err = run_probe(argv, cwd, timeout)
                frow["probe"] = mode
                frow["rc"] = rc
                if err is not None:
                    frow["error_tail"] = [err][:ERROR_TAIL_LINES]
                    errors.append("probe %s: %s" % (rel, err))
                elif rc != 0:
                    frow["error_tail"] = error_tail(output)
                    errors.append("probe %s: lean exited %s" % (rel, rc))
                parsed = parse_print_axioms(output, [nm for nm, _ in decls])
                for (nm, ln), row in zip(decls, parsed):
                    klass, custom, allowed = classify_axioms(
                        row["axioms"] if row["ok"] else [], allow)
                    if not row["ok"]:
                        klass = "UNPARSED"
                        custom = []
                        allowed = []
                    decl_rows.append({
                        "file": rel, "line": ln, "name": nm,
                        "classification": klass,
                        "axioms": row["axioms"] if row["ok"] else [],
                        "custom": custom, "allowed": allowed,
                        "probe": mode,
                        "raw": "" if row["ok"] else row["raw"],
                        "unparsed_reason": row["reason"] if not row["ok"] else "",
                    })
            file_rows.append(frow)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    report = build_report(root, file_rows, decl_rows, errors, allow,
                          {"lean": lean, "lake": lake,
                           "usable_lean": usable_lean,
                           "usable_lake": usable_lake})
    return exit_code_for(report), report


def build_report(root, file_rows, decl_rows, errors, allow, toolchain_face):
    """Pure report assembly over the collected rows; the selftest schema
    vector feeds this with canned rows (offline, no toolchain)."""
    counts = {}
    for row in decl_rows:
        counts[row["classification"]] = \
            counts.get(row["classification"], 0) + 1
    clean = counts.get("CLEAN", 0)
    benign = counts.get("BENIGN-STANDARD", 0)
    sorry = counts.get("SORRY-ALARM", 0)
    custom = counts.get("CUSTOM-AXIOM-ALARM", 0)
    unparsed = counts.get("UNPARSED", 0)
    custom_names = sorted({c for row in decl_rows for c in row["custom"]})
    verdict = "RED" if (sorry or custom or unparsed) else "PASS"
    return {
        "schema": SCHEMA,
        "root": {"value": root,
                 "basis": "the scan root as given; a file root scans that"
                          " file, a directory root walks *.lean with .git"
                          " skipped"},
        "files": {"value": len(file_rows),
                  "basis": ".lean targets read (file root: 1; read failures"
                           " sit in errors, not here)"},
        "declarations": {"value": len(decl_rows),
                         "basis": "line-start theorem/lemma/def names"
                                  " enumerated per the scan_face regex"
                                  " (namespace/section/end stack applied)"},
        "classified": {"value": clean + benign + sorry + custom,
                       "basis": "declarations whose `#print axioms` block"
                                " parsed into an axiom set"},
        "clean": {"value": clean,
                  "basis": "axiom set empty: 'does not depend on any"
                           " axioms' under the probed environment"},
        "benign_standard": {"value": benign,
                            "basis": "axiom set a subset of the standard"
                                     " trio propext, Classical.choice,"
                                     " Quot.sound (the 'three axioms'"
                                     " finding of the earlier audit"
                                     " work stream adjudicates here)"
                                     " or admitted by --allow-axiom"
                                     " (admitted names ride in the"
                                     " declaration's allowed field)"},
        "sorry_alarm": {"value": sorry,
                        "basis": "sorryAx in the axiom set; never"
                                 " admissible to the whitelist"},
        "custom_axiom_alarm": {"value": custom,
                               "basis": "any axiom outside the standard"
                                        " trio and the whitelist; names"
                                        " listed verbatim in"
                                        " custom_axiom_names"},
        "unparsed": {"value": unparsed,
                     "basis": "probe output not understood (missing or"
                              " mismatched block); honest, never judged,"
                              " raw block capped in the row"},
        "custom_axiom_names": {"value": custom_names,
                               "basis": "sorted unique verbatim names"
                                        " outside the standard trio and"
                                        " the whitelist across alarm rows"
                                        " (sorryAx itself is accounted by"
                                        " the sorry counter, never"
                                        " here)"},
        "allow_axioms": {"value": sorted(allow),
                         "basis": "the --allow-axiom whitelist in force;"
                                  " sorryAx is never admitted"},
        "file_rows": {"value": file_rows,
                      "basis": "per target: file, declarations, module,"
                               " probe mode, lean rc, capped error tail"},
        "declarations_detail": {"value": decl_rows,
                                "basis": "per declaration: file, line,"
                                         " full probe name, classification"
                                         " (CLEAN / BENIGN-STANDARD /"
                                         " SORRY-ALARM /"
                                         " CUSTOM-AXIOM-ALARM / UNPARSED),"
                                         " verbatim axiom set, custom and"
                                         " whitelist names, probe mode,"
                                         " capped raw block for unparsed"
                                         " rows"},
        "errors": {"value": errors[:READ_ERROR_CAP],
                   "basis": "first %d read or probe failures, each naming"
                            " the target" % READ_ERROR_CAP},
        "error_count": {"value": len(errors),
                        "basis": "total recorded read and probe failures;"
                                 " errors is capped at %d"
                                 % READ_ERROR_CAP},
        "toolchain": {"value": toolchain_face,
                      "basis": "lean/lake PATH resolutions and their"
                               " --version usability probes; the probe"
                               " mode per file is lake-env or"
                               " lean-direct"},
        "verdict": {"value": verdict,
                    "basis": "RED when any SORRY-ALARM,"
                             " CUSTOM-AXIOM-ALARM or UNPARSED row exists"
                             " (unjudgeable is not green); read and probe"
                             " failures force exit 1 via error_count"
                             " without flipping this verdict"},
        "scan_face": {
            "scanned": SCAN_SCANNED,
            "not_scanned": SCAN_NOT_SCANNED,
            "negative_finding": SCAN_NEGATIVE_FINDING,
            "equivalents": SCAN_EQUIVALENTS,
        },
    }


def exit_code_for(report):
    """0 green; 1 when the verdict is RED or any error was recorded."""
    if report["verdict"]["value"] == "RED":
        return EXIT_RED
    if report["error_count"]["value"] > 0:
        return EXIT_RED
    return EXIT_OK


def write_json(path, payload):
    """Write the stdout payload (plus one newline) to path as UTF-8."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def summarize(report):
    """One stderr summary line (stdout stays the single JSON line)."""
    sys.stderr.write(
        "AXIOM-SWEEP: %s decls=%d clean=%d benign_standard=%d sorry=%d"
        " custom=%d unparsed=%d errors=%d\n"
        % (report["verdict"]["value"],
           report["declarations"]["value"],
           report["clean"]["value"],
           report["benign_standard"]["value"],
           report["sorry_alarm"]["value"],
           report["custom_axiom_alarm"]["value"],
           report["unparsed"]["value"],
           report["error_count"]["value"]))


# ---- selftest (frozen offline vectors on the parse, classify, report and
# gate faces; zero network, zero toolchain launch, zero real-repo touch) ----

# Canned `#print axioms` output fixtures in the Lean 4 CLI info-block face
# (position-prefixed message text; the parser must not line-anchor).
LEAN_OUT_CLEAN = ("ck.lean:2:0: info: 't_clean' does not depend on any"
                  " axioms\n")
LEAN_OUT_THREE = ("ck.lean:2:0: info: 't_three' depends on axioms: "
                  "[propext, Classical.choice, Quot.sound]\n")
LEAN_OUT_SUBSET = ("ck.lean:2:0: info: 't_subset' depends on axioms: "
                   "[propext]\n")
LEAN_OUT_SORRY = ("ck.lean:2:0: info: 't_sorry' depends on axioms:"
                  " [sorryAx]\n")
LEAN_OUT_CUSTOM = ("ck.lean:2:0: info: 't_custom' depends on axioms:"
                   " [my_axiom.rh]\n")
LEAN_OUT_MIXED = ("ck.lean:2:0: info: 'a' does not depend on any axioms\n"
                  "ck.lean:4:0: info: 'b' depends on axioms: "
                  "[propext, Classical.choice]\n"
                  "ck.lean:6:0: info: 'c' depends on axioms: [sorryAx]\n"
                  "ck.lean:8:0: info: 'd' depends on axioms: "
                  "[my_ax, propext]\n"
                  "ck.lean:9:0: error: declaration uses 'sorry'\n")
LEAN_OUT_GHOST = ("ck.lean:2:0: error: unknown identifier 't_ghost'\n")
LEAN_OUT_NAME_MISMATCH = (
    "ck.lean:2:0: info: 'some_other' depends on axioms: [sorryAx]\n")
LEAN_OUT_SURPLUS = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:3:0: info: 'b' depends on axioms: [sorryAx]\n")

# Declaration-enumeration fixtures.
SAMPLE_LEAN = (
    "namespace Foo\n"
    "theorem bar : True := trivial\n"
    "  lemma nested : True := trivial\n"
    "end Foo\n"
    "theorem baz : True := trivial\n"
    "private theorem priv_one : Nat := 1\n"
    "noncomputable def nc_def : Nat := 2\n"
    "-- theorem dashed_out : True := trivial\n"
    "/- block comment\n"
    "theorem in_block_comment : True := trivial\n"
    "-/\n"
    "def with_apostrophe : Nat := 3\n"
    "section\n"
    "theorem in_section : True := trivial\n"
    "end\n"
    "instance : Inhabited Nat := <something>\n"
    "example : True := trivial\n"
)
SAMPLE_LEAN_NAMES = [("Foo.bar", 2), ("Foo.nested", 3), ("baz", 5),
                     ("priv_one", 6), ("nc_def", 7), ("in_block_comment", 10),
                     ("with_apostrophe", 12), ("in_section", 14)]


def selftest():
    """Frozen offline vectors; 0 green, 1 red with the failing names on
    stdout.  Zero network, zero toolchain launch, zero real-repo touch."""
    fails = []
    total = [0]

    def vec(name, ok, detail=""):
        total[0] += 1
        print("[PASS] %s" % name if ok else "[FAIL] %s %s" % (name, detail))
        if not ok:
            fails.append(name)

    script = os.path.abspath(__file__)
    tmp = tempfile.mkdtemp(prefix="rocqwash_axiom_sweep_selftest_")
    try:
        # declaration enumeration: stack, modifiers, decoys, families out
        got = enumerate_decls(SAMPLE_LEAN)
        vec("decl-enumeration", got == SAMPLE_LEAN_NAMES, "got %s" % (got,))

        # parse faces: the five classes plus attribution faces
        rows = parse_print_axioms(LEAN_OUT_CLEAN, ["t_clean"])
        vec("parse-clean", rows[0]["ok"] and rows[0]["axioms"] == [],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_THREE, ["t_three"])
        vec("parse-benign-three",
            rows[0]["ok"] and rows[0]["axioms"] == list(BENIGN_STANDARD),
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SUBSET, ["t_subset"])
        vec("parse-benign-subset",
            rows[0]["ok"] and rows[0]["axioms"] == ["propext"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SORRY, ["t_sorry"])
        vec("parse-sorry", rows[0]["ok"] and rows[0]["axioms"] == ["sorryAx"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_CUSTOM, ["t_custom"])
        vec("parse-custom",
            rows[0]["ok"] and rows[0]["axioms"] == ["my_axiom.rh"],
            "got %s" % (rows,))
        names = ["a", "b", "c", "d"]
        rows = parse_print_axioms(LEAN_OUT_MIXED, names)
        ok = (len(rows) == 4 and rows[0]["ok"] and rows[0]["axioms"] == []
              and rows[1]["axioms"] == ["propext", "Classical.choice"]
              and rows[2]["axioms"] == ["sorryAx"]
              and rows[3]["axioms"] == ["my_ax", "propext"])
        vec("parse-mixed-attribution", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_MIXED, names + ["e"])
        ok = (rows[0]["ok"] and rows[3]["ok"]
              and not rows[4]["ok"]
              and "no probe block" in rows[4]["reason"])
        vec("parse-tail-no-block", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_GHOST, ["t_ghost"])
        vec("parse-unknown-identifier",
            not rows[0]["ok"] and "unknown identifier" in rows[0]["raw"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_NAME_MISMATCH, ["t_x"])
        vec("parse-name-mismatch",
            not rows[0]["ok"] and "probe block names" in rows[0]["reason"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SURPLUS, ["a"])
        vec("parse-surplus-markers",
            not rows[0]["ok"] and "exceeds" in rows[0]["reason"],
            "got %s" % (rows,))

        # classify faces: precedence, whitelist, sorryAx never allowed
        vec("classify-clean", classify_axioms([], []) == ("CLEAN", [], []),
            "got %s" % (classify_axioms([], []),))
        vec("classify-wave2-three-axioms",
            classify_axioms(list(BENIGN_STANDARD), [])
            == ("BENIGN-STANDARD", [], []),
            "got %s" % (classify_axioms(list(BENIGN_STANDARD), []),))
        vec("classify-sorry-precedence",
            classify_axioms(["sorryAx", "my_ax"], ["my_ax"])
            == ("SORRY-ALARM", [], ["my_ax"]),
            "got %s" % (classify_axioms(["sorryAx", "my_ax"], ["my_ax"]),))
        vec("classify-sorry-custom-verbatim",
            classify_axioms(["sorryAx", "my_ax"], [])
            == ("SORRY-ALARM", ["my_ax"], []),
            "got %s" % (classify_axioms(["sorryAx", "my_ax"], []),))
        vec("classify-sorry-never-allowed",
            classify_axioms(["sorryAx"], ["sorryAx"])[0] == "SORRY-ALARM",
            "got %s" % (classify_axioms(["sorryAx"], ["sorryAx"]),))
        vec("classify-custom-verbatim",
            classify_axioms(["propext", "my_ax", "zz_ax"], [])
            == ("CUSTOM-AXIOM-ALARM", ["my_ax", "zz_ax"], []),
            "got %s" % (classify_axioms(["propext", "my_ax", "zz_ax"], []),))
        vec("classify-allow-fold",
            classify_axioms(["my_ax"], ["my_ax"])
            == ("BENIGN-STANDARD", [], ["my_ax"]),
            "got %s" % (classify_axioms(["my_ax"], ["my_ax"]),))

        # checker emission and module derivation
        checker = build_checker("My.Mod", ["a", "b"])
        vec("checker-emission",
            checker == "import My.Mod\n\n#print axioms a\n#print axioms b\n",
            "got %r" % checker)
        vec("checker-no-module",
            build_checker("", ["x"]) == "\n#print axioms x\n",
            "got %r" % build_checker("", ["x"]))
        proj = os.path.join(tmp, "proj")
        src = os.path.join(proj, "src", "My")
        os.makedirs(src)
        with open(os.path.join(proj, "lakefile.toml"), "wb"):
            pass
        with open(os.path.join(src, "Mod.lean"), "wb"):
            pass
        module, root = derive_module(os.path.join(src, "Mod.lean"))
        vec("module-derivation-src",
            module == "My.Mod" and os.path.samefile(root, proj),
            "got module=%r root=%r" % (module, root))
        module2, root2 = derive_module(os.path.join(tmp, "bare.lean"))
        vec("module-derivation-bare",
            module2 == "bare" and root2 is None,
            "got module=%r root=%r" % (module2, root2))

        # report schema shape over canned rows (offline, no toolchain)
        canned_files = [{"file": "a.lean", "declarations": 2,
                         "module": "A", "probe": "lean-direct",
                         "rc": 0, "error_tail": []}]
        canned_decls = [
            {"file": "a.lean", "line": 2, "name": "t_one",
             "classification": "CLEAN", "axioms": [], "custom": [],
             "allowed": [], "probe": "lean-direct", "raw": "",
             "unparsed_reason": ""},
            {"file": "a.lean", "line": 5, "name": "t_two",
             "classification": "SORRY-ALARM", "axioms": ["sorryAx"],
             "custom": [], "allowed": [], "probe": "lean-direct",
             "raw": "", "unparsed_reason": ""},
        ]
        rep = build_report("TMP", canned_files, canned_decls, [],
                           [], {"lean": None, "lake": None,
                                "usable_lean": False, "usable_lake": False})
        bare = [k for k in rep
                if k not in ("scan_face", "schema")
                and not (isinstance(rep[k], dict)
                         and "value" in rep[k] and "basis" in rep[k])]
        vec("schema-value-basis", bare == [], "bare keys: %s" % bare)
        face = rep["scan_face"]
        vec("scan-face-fields",
            sorted(face) == ["equivalents", "negative_finding",
                             "not_scanned", "scanned"],
            "got %s" % (sorted(face),))
        vec("scan-face-verbatim",
            face.get("scanned") == SCAN_SCANNED
            and face.get("not_scanned") == SCAN_NOT_SCANNED
            and face.get("negative_finding") == SCAN_NEGATIVE_FINDING
            and face.get("equivalents") == SCAN_EQUIVALENTS
            and "line-start" in SCAN_EQUIVALENTS,
            "scan_face strings drifted from the constants")
        vec("verdict-red-face", rep["verdict"]["value"] == "RED"
            and exit_code_for(rep) == 1,
            "got %s / %s" % (rep["verdict"]["value"], exit_code_for(rep)))
        clean_decls = [dict(canned_decls[0], name="t_one")]
        rep2 = build_report("TMP", canned_files, clean_decls, [], [], {})
        vec("verdict-pass-face", rep2["verdict"]["value"] == "PASS"
            and exit_code_for(rep2) == 0,
            "got %s / %s" % (rep2["verdict"]["value"], exit_code_for(rep2)))
        vec("error-forces-red-exit",
            exit_code_for(build_report("TMP", canned_files, clean_decls,
                                       ["read a.lean: boom"], [], {})) == 1,
            "errors must force exit 1")
        vec("unparsed-forces-red",
            build_report("TMP", canned_files,
                         [dict(clean_decls[0],
                               classification="UNPARSED")], [], [],
                         {})["verdict"]["value"] == "RED",
            "unjudgeable is not green")
        three_decls = [
            dict(clean_decls[0], name="t_std",
                 classification="BENIGN-STANDARD",
                 axioms=list(BENIGN_STANDARD)),
        ]
        rep3 = build_report("TMP", canned_files, three_decls, [], [], {})
        vec("wave2-three-axioms-benign",
            rep3["benign_standard"]["value"] == 1
            and rep3["custom_axiom_names"]["value"] == []
            and rep3["verdict"]["value"] == "PASS",
            "got %s" % (rep3["benign_standard"],))
        payload = json.dumps(rep, ensure_ascii=False)
        vec("single-line-json", "\n" not in payload, "payload holds a newline")
        json_path = os.path.join(tmp, "out.json")
        write_json(json_path, payload)
        with open(json_path, "r", encoding="utf-8") as fh:
            round_trip = json.load(fh)
        vec("json-round-trip", round_trip == rep, "payload mismatch")

        # flag face: --selftest parses standalone; usage faces rc 2
        vec("selftest-flag-face",
            build_parser().parse_args(["--selftest"]).selftest is True
            and build_parser().parse_args([]).selftest is False,
            "--selftest defaults to False and parses without --root")

        def spawn(argv, env=None, cwd=None):
            try:
                p = subprocess.run([sys.executable, "-I", "-B", script]
                                   + argv, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, timeout=120,
                                   env=env, cwd=cwd)
            except subprocess.TimeoutExpired:
                return None, "", "timeout"
            out = p.stdout.decode("utf-8", "replace")
            errout = p.stderr.decode("utf-8", "replace")
            return p.returncode, out, errout

        rc, _out, _err = spawn([])
        vec("exit-usage-no-root-rc2", rc == 2,
            "no arguments exits %s (usage error)" % rc)
        rc, _out, _err = spawn(["--root", os.path.join(tmp, "absent")])
        vec("exit-root-absent-rc2", rc == 2,
            "absent --root exits %s (usage error)" % rc)

        # gate vector: child PATH stripped to an empty directory -> 112.
        # Runs on every host: absence is forced by the stripped child
        # environment, so the vector exercises the gate whether or not the
        # host toolchain is present; a host where stripping cannot force
        # absence reports red instead of passing dishonestly.
        fixture_dir = os.path.join(tmp, "fixture")
        os.makedirs(fixture_dir)
        with open(os.path.join(fixture_dir, "t.lean"), "wb") as fh:
            fh.write(b"theorem t_one : True := trivial\n")
        empty_dir = os.path.join(tmp, "empty_path")
        os.makedirs(empty_dir)
        gate_env = dict(os.environ)
        gate_env["PATH"] = empty_dir
        rc, out, err = spawn(["--root", fixture_dir],
                             env=gate_env, cwd=empty_dir)
        vec("gate-no-toolchain-rc112",
            rc == 112 and out.strip() == ""
            and "toolchain" in err,
            "rc=%s stdout=%r stderr=%r" % (rc, out[:120], err[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[SELFTEST] %s %s: %d vector(s), %d fail"
          % (TOOL, "green" if not fails else "red", total[0], len(fails)))
    if fails:
        print("[SELFTEST] red vectors: %s" % ", ".join(fails))
        return 1
    return 0


def build_parser():
    """The flag face; extracted so --selftest runs standalone (no --root
    required) and the usage face stays single-source."""
    ap = argparse.ArgumentParser(
        prog=TOOL,
        description="per-theorem axiom-closure classifier for Lean claim"
                    " audits (one JSON line; rc 112 without a usable"
                    " Lean toolchain)")
    ap.add_argument("--root", metavar="FILE|DIR",
                    help="target .lean file or directory (required unless"
                         " --selftest)")
    ap.add_argument("--json", metavar="OUT",
                    help="write the stdout JSON payload to OUT as well")
    ap.add_argument("--allow-axiom", action="append", default=[],
                    dest="allow_axioms",
                    help="extra axiom name admitted into BENIGN-STANDARD"
                         " (repeatable; sorryAx is never admitted)")
    ap.add_argument("--timeout", type=int, default=PROBE_TIMEOUT_DEFAULT,
                    help="per-probe subprocess timeout seconds"
                         " (default %d)" % PROBE_TIMEOUT_DEFAULT)
    ap.add_argument("--selftest", action="store_true",
                    help="run the frozen offline vector group and exit")
    return ap


def main(argv=None):
    """CLI entry; returns the process exit code (0/1/2/112)."""
    args = build_parser().parse_args(argv)
    if args.selftest:
        if args.root or args.json:
            build_parser().error("--selftest runs standalone; combine it"
                                 " with no scan flags")
        return selftest()
    if not args.root:
        build_parser().error("--root is required unless --selftest is given")
    if not os.path.exists(args.root):
        sys.stderr.write("%s: --root does not exist: %s\n"
                         % (TOOL, args.root))
        return EXIT_USAGE
    if args.timeout < 1:
        build_parser().error("--timeout must be >= 1")
    lean, lake, usable_lean, usable_lake = probe_toolchain()
    if not (usable_lean or usable_lake):
        sys.stderr.write(
            "SKIP: no usable Lean toolchain (need a working `lean` or"
            " `lake` on PATH with a configured default toolchain;"
            " found lean=%r lake=%r, both unusable by the version"
            " probe); the axiom sweep honestly skips and judges nothing"
            " (rc %d)\n" % (lean, lake, EXIT_NO_TOOLCHAIN))
        return EXIT_NO_TOOLCHAIN
    code, report = sweep(args.root, args.allow_axioms, args.timeout)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = json.dumps(report, ensure_ascii=False)
    print(payload)
    if args.json:
        try:
            write_json(args.json, payload)
        except OSError as exc:
            sys.stderr.write("%s: --json write failed: %s\n" % (TOOL, exc))
            return EXIT_RED
    summarize(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
