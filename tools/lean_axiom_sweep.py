#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lean_axiom_sweep.py - per-theorem axiom-closure classifier for Lean claim audits.
Purpose.  Make "0 sorry 0 axiom" claims mechanically reproducible per theorem:
  the declaration face of the target .lean file(s) is enumerated and each
  declaration is probed with `#print axioms <decl>` via the copy-append
  form: the target file is copied to a private temp checker file and one
  probe line per declaration is appended to the copy, so private
  declarations are probed in their own file's context (the import-based
  checker form survives only for cross-file aggregated sweeps where
  copy-append is not applicable).  The checker runs in the target's own
  lake environment (`lake env lean`) or against a direct lean binary, and
  the output is parsed into axiom sets and classified: CLEAN /
  BENIGN-STANDARD (subset of propext, Classical.choice, Quot.sound) /
  SORRY-ALARM (sorryAx) / CUSTOM-AXIOM-ALARM (any other name, verbatim) /
  PRIVATE-COVERED (a private declaration successfully probed via the
  copy-append form; its axiom closure counts normally toward the verdict,
  it is not a pass-by-absence) / UNPARSED (honest).
Interface.  python -I tools/lean_axiom_sweep.py --root <file|dir> [--json OUT]
  [--allow-axiom NAME]... [--timeout SEC] [--snapshot OUT]
  [--baseline SNAPSHOT] | --selftest.  stdout carries one JSON line (schema
  rocqwash-axiom-sweep/1); --json additionally writes the same payload to
  OUT; --snapshot additionally writes a machine closure snapshot (schema
  rocqwash-axiom-closure-snapshot/1, deterministic); --baseline diffs the
  current closure against a previous snapshot into the closure_diff block;
  --selftest runs the frozen offline vectors and exits.
Dependencies.  Python 3 standard library only; the probe face needs a usable
  Lean 4 toolchain (lean or lake on PATH passing a version probe, so an
  elan shim without a default toolchain does not pass), never downloaded or
  simulated; without one the sweep exits 112 judging nothing.  The
  snapshot and diff faces are toolchain-independent: the diff reads only
  the two snapshot files' data, no Lean involvement.
Evidence.  --selftest covers the parse and classify faces with canned
  `#print axioms` fixtures for all six classes, the copy-append emission
  face (checker text plus the emitted probe list it is aligned by), the
  per-probe failure-isolation face (a failed or unresolved probe leaves
  ONLY its own declaration UNPARSED, no sibling cascade), a private- plus
  public-declaration fixture probed offline into PRIVATE-COVERED with its
  axiom set, the report shape (every counter wrapped {value, basis},
  scan_face four fields), the import-form checker emission and
  module-derivation faces, the gate vector (child PATH stripped -> rc
  112), the closure faces (snapshot determinism double-run
  byte-identical, all four diff verdict kinds, diff_alarm true and
  false, NEW-DEPENDENCY, baseline load error faces, the no-baseline
  backward-compat shape); zero network, zero toolchain launch, zero
  real-repo touch.
Exit-codes.  0 green (every classified declaration CLEAN, BENIGN-STANDARD
  or PRIVATE-COVERED, zero UNPARSED rows, zero errors); 1 red (any
  SORRY-ALARM,
  CUSTOM-AXIOM-ALARM or UNPARSED row, or any recorded error: unjudgeable is
  not green; unchanged by the diff face - diff_alarm rides the payload);
  2 usage error (including an unreadable or wrong-schema --baseline);
  112 no usable Lean toolchain (the honest skip names the requirement; the
  axiom_guard rc 111 env-gate precedent family, code 112 per this tool's
  contract).
"""

# Detail carried below the five-field header budget (the norm_lint
# header-budget rule keeps the docstring to the five fields):
#
# Declaration enumeration.  Byte-literal line-start regex face: optional
# Lean 4 prefix modifiers (private/protected/noncomputable/unsafe/partial/
# local/global/export) sharing the line, then theorem|lemma|def, then the
# name (ASCII identifiers with apostrophes; quoted «...» and unicode
# spellings are outside the face and surface as absence, not guesses).
# The captured modifier prefix is scanned token-wise for `private`, so a
# private declaration is flagged at enumeration time (this drives the
# PRIVATE-COVERED class: private names are invisible to import-based
# probes, the Euler pilot blind spot).  A line-start namespace/section/end
# stack builds the full probe name (namespace pushes its name, section
# pushes an empty frame, end pops one); section/variable scoping inside a
# namespace is not tracked.  Comment and string bodies are NOT masked (the
# tree_audit byte-literal convention): a block-comment line that starts
# with theorem/lemma/def enters the census and later surfaces as an
# UNPARSED row instead of being silently dropped.
#
# Probe face.  Primary form, copy-append: for each target the file text is
# copied into a checker file in a private temp directory (the repository
# tree gains zero bytes) and one probe line per declaration is APPENDED to
# the copy - `#print axioms <name> -- rocqwash-probe <name>`, one line per
# declaration in enumeration order with an exact-name marker comment.
# Because the probes run inside the file's own context, private
# declarations resolve (import-based probes cannot see them: unknown
# constant), and the file's own imports resolve exactly as the file itself
# resolves them.  Run form is unchanged: `lake env lean <copy>` with
# cwd = the project root (nearest ancestor holding lakefile.lean /
# lakefile.toml / lean-toolchain; a head "src" segment of the module path
# is dropped per the lake srcDir convention) when lake is usable and a
# project root exists; otherwise `lean <copy>` directly (cwd = project
# root or the target's directory).  The import-based checker form
# (build_checker: one import line plus one `#print axioms <name>` line per
# declaration) is kept for non-private declarations ONLY where copy-append
# is not applicable - a cross-file aggregated sweep, which this tool does
# not run today; no live caller emits it.  Marker alignment is derived
# from the emitted probe list (the checker line number of every probe
# line), never from positional counting: an output block is attributed to
# the declaration whose probe line carries the block's position, verified
# against the exact probe name.  A failed or unresolved probe maps ONLY to
# its own declaration as UNPARSED (no cascade to siblings); the checker
# output is parsed regardless of the child exit code (info blocks and
# errors share the stream), and a whole-file failure still records the
# capped error tail on the file row, never judged.
#
# Classification face.  Each parsed axiom set classifies by the precedence
# below.  A PRIVATE declaration whose probe succeeded and whose set
# adjudicates benign (empty or trio/whitelist subset) is classed
# PRIVATE-COVERED instead of CLEAN / BENIGN-STANDARD: the class marks that
# the declaration was actually seen through the copy-append probe (its
# axiom closure rides the row and counts normally toward the verdict), NOT
# a pass-by-absence.  Alarm classes keep their precedence over the marker:
# a private declaration with sorryAx is SORRY-ALARM, one with a custom
# axiom is CUSTOM-AXIOM-ALARM.
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
#   4. a private declaration (flagged by the enumeration modifiers scan)
#      adjudicating at step 3 is classed PRIVATE-COVERED instead of
#      CLEAN / BENIGN-STANDARD - probed through the copy-append form, its
#      axiom set rides the row normally (steps 1-2 keep their classes).
#
# Closure snapshot and diff faces (the beyond-platform capability: the
# platform tools give today's closure, nobody gives closure EVOLUTION).
#   --snapshot OUT writes a machine closure snapshot, schema
#   rocqwash-axiom-closure-snapshot/1: plain machine fields (schema, tool,
#   root, allow_axioms, counts) plus per classified declaration the full
#   probe name, file, line, class and the SORTED axiom set.  UNPARSED rows
#   carry no closure and stay out of declarations; they are recorded
#   honestly by name at snapshot level (unparsed_count/unparsed_names),
#   nothing silently dropped.  Deterministic: declaration rows sorted by
#   (name, file, line), name lists and axiom sets sorted, no wall clock -
#   the same sweep answers byte-identically, double-run byte-identical.
#   --baseline SNAPSHOT diffs the current closure against a previously
#   written snapshot into the closure_diff block, keyed by full
#   declaration name (a repeated name resolves to the last row in the
#   snapshot's sorted order).  Per declaration one verdict: UNCHANGED
#   (same axiom set), AXIOM-SET-CHANGED (from_axioms -> to_axioms listed),
#   NEW-THEOREM (name only in the current snapshot), LOST-THEOREM (name
#   absent from the current snapshot: a removal and a failed or unparsed
#   probe both surface here, snapshots record closures only).  A
#   previously-clean declaration (empty baseline axiom set) whose current
#   axiom set is non-empty is a NEW-DEPENDENCY, listed by name.  Any
#   AXIOM-SET-CHANGED verdict or any NEW-DEPENDENCY event sets the
#   top-level diff_alarm true (false otherwise; NEW-THEOREM and
#   LOST-THEOREM alone do not alarm; the flag rides the payload, the
#   sweep exit code stays the sweep's own green/red face).  closure_diff
#   and diff_alarm are {value, basis}-wrapped like every other top-level
#   report field; with no --baseline neither key exists and the report
#   shape is byte-for-byte today's (backward compatible, exit 0 as
#   today).  The diff reads ONLY the two snapshot files' data, so the
#   snapshot and diff faces are toolchain-independent; a baseline file
#   that is missing, unparseable, or not a rocqwash-axiom-closure-snapshot/1
#   document is a usage error (rc 2) named on stderr, never a guess.
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

# The PRIVATE-COVERED class: a private declaration successfully probed
# through the copy-append form.  Its axiom closure rides the row and
# counts normally toward the sweep verdict; it is NOT a pass-by-absence.
PRIVATE_COVERED = "PRIVATE-COVERED"
# Exact-name marker comment on every emitted probe line; the parser
# aligns output blocks via the emitted probe list, never positionally.
PROBE_MARKER = "rocqwash-probe"

# Line-start declaration enumeration (byte-literal; comment bodies unmasked).
# DECL_RE captures the modifier prefix as group 1 so the private flag is
# detectable at enumeration time (group 2 keyword, group 3 name).
DECL_MODIFIERS = (r"(?:(?:private|protected|noncomputable|unsafe|partial|"
                  r"local|global|export)[ \t]+)*")
DECL_RE = re.compile(
    r"(?m)^[ \t]*(" + DECL_MODIFIERS + r")"
    r"(theorem|lemma|def)[ \t]+([A-Za-z_][A-Za-z0-9_']*)")
NAMESPACE_RE = re.compile(r"(?m)^[ \t]*namespace[ \t]+([A-Za-z_][A-Za-z0-9_'.]*)")
SECTION_RE = re.compile(r"(?m)^[ \t]*section(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")
END_RE = re.compile(r"(?m)^[ \t]*end(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")

# `#print axioms` output faces (Lean 4 CLI message lines).  The message
# BODY regexes stay unanchored, but attribution keys the
# "<file>:<line>:<col>: <severity>: " position prefix against the emitted
# probe list: an axiom/clean block is attributed to the declaration whose
# emitted probe line carries the block's position, then name-verified.
# POSITION_RE tolerates Windows drive-letter paths (the non-greedy path
# piece can only end at a `:<digits>:<digits>: ` run followed by a
# severity word).  A probe line carrying anything other than its own
# axiom/clean block parses UNPARSED for that ONE declaration - honest, no
# sibling cascade; an unprefixed message line is attributable to no
# emitted probe line and is ignored.
CLEAN_RE = re.compile(r"'([^']+)' does not depend on any axioms")
AXIOMS_RE = re.compile(r"'([^']+)' depends on axioms:[ \t]*\[([^\]]*)\]")
POSITION_RE = re.compile(
    r"(?m)^(?P<path>.*?):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<sev>info|error|warning): (?P<msg>.*)$")

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
    " appended to a copy of the target file (the copy-append form, so"
    " private declarations are probed in their own file's context), run"
    " via the target's own lake environment (`lake env lean`) or a direct"
    " lean binary."
)
SCAN_NOT_SCANNED = (
    "Files with any other suffix, everything under .git, declarations whose"
    " keyword is not at a line start (attribute lines, non-line-start"
    " spellings), non-theorem/lemma/def declaration families, quoted"
    " <<..>> and non-ASCII identifier spellings, and anything the toolchain"
    " environment cannot compile: a failed or missing probe block leaves"
    " only its own declaration UNPARSED, never judged."
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

# Closure snapshot + diff faces (toolchain-independent: the diff reads
# only the two snapshots' data).
SNAPSHOT_SCHEMA = "rocqwash-axiom-closure-snapshot/1"

# The four per-declaration diff verdicts.
DIFF_UNCHANGED = "UNCHANGED"
DIFF_CHANGED = "AXIOM-SET-CHANGED"
DIFF_NEW = "NEW-THEOREM"
DIFF_LOST = "LOST-THEOREM"

# The summary/alarm basis strings (English, module constants so the
# selftest can pin them and consumers quote the counting rule verbatim).
DIFF_BASIS_UNCHANGED = (
    "same full declaration name in both snapshots with an identical axiom"
    " set")
DIFF_BASIS_CHANGED = (
    "same full declaration name whose axiom set differs; from_axioms and"
    " to_axioms list the two sets (a class drift without an axiom-set"
    " drift, for example a whitelist difference, stays UNCHANGED by this"
    " contract - both classes ride the row)")
DIFF_BASIS_NEW = (
    "full declaration name present only in the current snapshot")
DIFF_BASIS_LOST = (
    "full declaration name absent from the current snapshot: a removal and"
    " a failed or unparsed probe both surface here, snapshots record"
    " closures only")
DIFF_BASIS_NEWDEP = (
    "previously-clean declarations (empty baseline axiom set) whose"
    " current axiom set is non-empty; the names are listed in"
    " new_dependency_names")
DIFF_BASIS_ALARM = (
    "true when any AXIOM-SET-CHANGED verdict or any NEW-DEPENDENCY event"
    " exists, false otherwise; NEW-THEOREM and LOST-THEOREM alone do not"
    " alarm; the flag rides the payload, the sweep exit code stays the"
    " sweep's own green/red face")


def enumerate_decls(text):
    """[(full_name, line_no, is_private)] in file order: line-start
    theorem/lemma/def names with the namespace/section/end stack applied;
    is_private flags a declaration whose captured modifier prefix carries
    the `private` token (the prefix only ever holds the fixed modifier
    words, so a token-set membership test is exact).  Comment and string
    bodies are not masked (declared scan-face limitation)."""
    out = []
    stack = []  # namespace names (section frames push "")
    line_no = 0
    for line in text.splitlines():
        line_no += 1
        m = DECL_RE.match(line)
        if m:
            parts = [p for p in stack if p]
            parts.append(m.group(3))
            out.append((".".join(parts), line_no,
                        "private" in m.group(1).split()))
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
    """The import-based checker program text: one import line plus one
    `#print axioms <name>` per declaration, in enumeration order.  The
    FALLBACK probe form: import-based probes cannot see private names
    (unknown constant), so this form applies to non-private declarations
    ONLY where copy-append is not applicable - a cross-file aggregated
    sweep, which this tool does not run today; kept single-source here and
    pinned by the selftest emission vector."""
    lines = []
    if module:
        lines.append("import %s" % module)
    lines.append("")
    for nm in names:
        lines.append("#print axioms %s" % nm)
    lines.append("")
    return "\n".join(lines)


def build_copy_checker(text, names):
    """The primary copy-append probe form.  Returns (checker_text, probes)
    where checker_text is the target file's own text with one probe line
    per declaration APPENDED - `#print axioms <name> -- rocqwash-probe
    <name>`, enumeration order, exact-name marker comment - and probes is
    the emitted probe list [(checker_line_no, name)] the parser aligns
    output blocks by (never positional counting).  Running the probes in
    the file's own context makes private declarations resolvable (the
    import-based form cannot see them) and needs no module derivation; a
    leading decoded BOM is dropped (a zero-information decoding artifact,
    not content masking)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # drop the trailing empty piece of a final newline
    tail_start = len(lines) + 2  # +1 blank separator line, +1 for 1-based
    probes = [(tail_start + offset, nm) for offset, nm in enumerate(names)]
    lines.append("")
    for nm in names:
        lines.append("#print axioms %s -- %s %s" % (nm, PROBE_MARKER, nm))
    return "\n".join(lines) + "\n", probes


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


def parse_print_axioms(output, probes):
    """Attribute `#print axioms` output blocks to declarations via the
    emitted probe list [(checker_line_no, name)] - never positional
    counting.  Returns one row per probe, in probe order: {"name", "ok",
    "axioms", "reason", "raw"}; ok=False rows are UNPARSED (honest) and
    map ONLY to their own declaration (no sibling cascade).

    Alignment face: an axiom/clean block sitting on an emitted probe line
    attributes to that probe's declaration after exact-name verification;
    an error message on a probe line (unknown identifier, unresolved
    name) fails exactly that declaration; a probe line with no message at
    all (launch failure, mid-file elaboration failure) fails exactly that
    declaration.  Correspondence guard: an axiom/clean block quoting one
    of the probed names from a NON-probe line means the output is not
    this emission's (a displaced or duplicated response - the old
    positional surplus face) and nothing is judged; blocks quoting names
    that were never probed are not this emission's probes either (the
    target file may carry its own `#print` lines) and are ignored."""
    probe_names = {nm for _ln, nm in probes}
    probe_lines = {ln for ln, _nm in probes}
    msgs = []  # (line_no, severity, message) in stream order
    for m in POSITION_RE.finditer(output):
        msgs.append((int(m.group("line")), m.group("sev"),
                     m.group("msg")))
    by_line = {}
    for ln, sev, msg in msgs:
        by_line.setdefault(ln, []).append((sev, msg))
    # Correspondence guard first: a probed name answered from a line that
    # is not its emitted probe line breaks the emission correspondence.
    guard_reason = None
    for ln, _sev, msg in msgs:
        blk = AXIOMS_RE.search(msg) or CLEAN_RE.search(msg)
        if blk and blk.group(1) in probe_names and ln not in probe_lines:
            guard_reason = ("output does not correspond to the emitted"
                            " probe list: probed name %r answered at"
                            " non-probe line %d; nothing attributed"
                            % (blk.group(1), ln))
            break
    if guard_reason is not None:
        return [{"name": nm, "ok": False, "axioms": [],
                 "reason": guard_reason, "raw": output[:RAW_CAP]}
                for _ln, nm in probes]
    rows = []
    for ln, nm in probes:
        block = None    # message carrying this probe's own axiom/clean block
        mismatch = None # message carrying a block that quotes another name
        error = None    # first error message on the probe line
        for sev, msg in by_line.get(ln, []):
            blk = AXIOMS_RE.search(msg) or CLEAN_RE.search(msg)
            if blk is not None and blk.group(1) == nm:
                if block is None:
                    block = msg
            elif blk is not None:
                if mismatch is None:
                    mismatch = msg
            elif sev == "error" and error is None:
                error = msg
        if block is not None:
            ax = AXIOMS_RE.search(block)
            axioms = ([a.strip() for a in ax.group(2).split(",")
                       if a.strip()] if ax else [])
            rows.append({"name": nm, "ok": True, "axioms": axioms,
                         "reason": "", "raw": ""})
            continue
        if mismatch is not None:
            bad = (AXIOMS_RE.search(mismatch)
                   or CLEAN_RE.search(mismatch)).group(1)
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": "probe block names %r, expected %r"
                                   % (bad, nm),
                         "raw": mismatch[:RAW_CAP]})
            continue
        if error is not None:
            rows.append({"name": nm, "ok": False, "axioms": [],
                         "reason": error.strip()[:RAW_CAP],
                         "raw": error.strip()[:RAW_CAP]})
            continue
        context = (output[:RAW_CAP] if not by_line.get(ln) else
                   " ".join(m.strip() for _s, m in by_line[ln])[:RAW_CAP])
        rows.append({"name": nm, "ok": False, "axioms": [],
                     "reason": "no probe block found on emitted probe"
                               " line %d" % ln,
                     "raw": context})
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


def classify_decl_rows(rel, decls, parsed, allow, mode):
    """Pure per-declaration row assembly over the enumeration
    [(name, line, is_private)] and the parsed probe rows (aligned
    one-to-one by construction of the emitted probe list): each axiom set
    classifies by the detail-block precedence; a private declaration
    adjudicating benign (CLEAN / BENIGN-STANDARD) is classed
    PRIVATE-COVERED - probed through the copy-append form, its axiom
    closure rides the row and counts normally toward the verdict, not a
    pass-by-absence - while alarm classes keep their precedence over the
    marker; a failed or unresolved probe maps only to its own declaration
    as UNPARSED."""
    rows = []
    for (nm, ln, is_private), row in zip(decls, parsed):
        klass, custom, allowed = classify_axioms(
            row["axioms"] if row["ok"] else [], allow)
        if not row["ok"]:
            klass = "UNPARSED"
            custom = []
            allowed = []
        elif is_private and klass in ("CLEAN", "BENIGN-STANDARD"):
            klass = PRIVATE_COVERED
        rows.append({
            "file": rel, "line": ln, "name": nm,
            "classification": klass,
            "axioms": row["axioms"] if row["ok"] else [],
            "custom": custom, "allowed": allowed,
            "private": is_private,
            "probe": mode,
            "raw": "" if row["ok"] else row["raw"],
            "unparsed_reason": row["reason"] if not row["ok"] else "",
        })
    return rows


def sweep(root, allow, timeout):
    """The run face; returns (exit_code, report).  Every target is probed
    by the copy-append form (build_copy_checker): the file text plus the
    appended probe lines run in the target's own lake environment or
    against a direct lean binary, same cwd rules as ever.  Write faces:
    the private temp workdir (removed on exit) and the caller-named --json
    file handled by main.  The toolchain gate has already passed when this
    runs."""
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
            # The module name stays on the file row as honest metadata
            # (and feeds the module-derivation face); the copy-append
            # checker itself needs no import line.
            module, project_root = derive_module(abs_path)
            frow = {"file": rel, "declarations": len(decls),
                    "module": module, "probe": "", "form": "copy-append",
                    "rc": None, "error_tail": []}
            if decls:
                checker, probes = build_copy_checker(
                    text, [nm for nm, _ln, _p in decls])
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
                parsed = parse_print_axioms(output, probes)
                decl_rows.extend(classify_decl_rows(
                    rel, decls, parsed, allow, mode))
            file_rows.append(frow)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    report = build_report(root, file_rows, decl_rows, errors, allow,
                          {"lean": lean, "lake": lake,
                           "usable_lean": usable_lean,
                           "usable_lake": usable_lake})
    return exit_code_for(report), report


def build_report(root, file_rows, decl_rows, errors, allow, toolchain_face,
                 diff_face=None):
    """Pure report assembly over the collected rows; the selftest schema
    vector feeds this with canned rows (offline, no toolchain).  A
    diff_face (a diff_closures payload, or None without --baseline) is
    attached as the closure_diff + diff_alarm top-level fields; without
    one the report shape is byte-for-byte today's (backward compatible)."""
    counts = {}
    for row in decl_rows:
        counts[row["classification"]] = \
            counts.get(row["classification"], 0) + 1
    clean = counts.get("CLEAN", 0)
    benign = counts.get("BENIGN-STANDARD", 0)
    sorry = counts.get("SORRY-ALARM", 0)
    custom = counts.get("CUSTOM-AXIOM-ALARM", 0)
    unparsed = counts.get("UNPARSED", 0)
    private_covered = counts.get(PRIVATE_COVERED, 0)
    custom_names = sorted({c for row in decl_rows for c in row["custom"]})
    verdict = "RED" if (sorry or custom or unparsed) else "PASS"
    report = {
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
        "classified": {"value": clean + benign + sorry + custom
                                 + private_covered,
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
        "private_covered": {"value": private_covered,
                            "basis": "private declarations successfully"
                                     " probed via the copy-append form"
                                     " (private names are invisible to"
                                     " import-based probes) whose axiom"
                                     " set adjudicated benign; the"
                                     " closure rides the row and counts"
                                     " normally toward the verdict,"
                                     " this is NOT a pass-by-absence,"
                                     " and alarm classes keep their"
                                     " precedence over the marker"},
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
                               " probe mode, probe form (copy-append),"
                               " lean rc, capped error tail"},
        "declarations_detail": {"value": decl_rows,
                                "basis": "per declaration: file, line,"
                                         " full probe name, classification"
                                         " (CLEAN / BENIGN-STANDARD /"
                                         " SORRY-ALARM /"
                                         " CUSTOM-AXIOM-ALARM /"
                                         " PRIVATE-COVERED / UNPARSED),"
                                         " verbatim axiom set, custom and"
                                         " whitelist names, private flag,"
                                         " probe mode, capped raw block"
                                         " for unparsed rows"},
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
    if diff_face is not None:
        attach_closure_diff(report, diff_face)
    return report


def exit_code_for(report):
    """0 green; 1 when the verdict is RED or any error was recorded."""
    if report["verdict"]["value"] == "RED":
        return EXIT_RED
    if report["error_count"]["value"] > 0:
        return EXIT_RED
    return EXIT_OK


def build_snapshot(root, decl_rows, allow):
    """Machine closure snapshot (schema rocqwash-axiom-closure-snapshot/1)
    over a sweep's declaration rows: per classified declaration the full
    probe name, file, line, class and the sorted axiom set.  PRIVATE-COVERED
    rows are classified rows: their closure enters the snapshot under the
    PRIVATE-COVERED class like any other.  UNPARSED rows
    carry no closure and stay out of declarations; they are recorded
    honestly by name at snapshot level, nothing silently dropped.
    Deterministic: rows sorted by (name, file, line), name lists and
    axiom sets sorted, no wall clock - the same sweep answers
    byte-identically, double-run byte-identical."""
    decls = []
    unparsed = []
    for row in decl_rows:
        if row["classification"] == "UNPARSED":
            unparsed.append(row["name"])
            continue
        decls.append({"name": row["name"],
                      "file": row["file"],
                      "line": row["line"],
                      "classification": row["classification"],
                      "axioms": sorted(row["axioms"])})
    decls.sort(key=lambda d: (d["name"], d["file"], d["line"]))
    return {
        "schema": SNAPSHOT_SCHEMA,
        "tool": TOOL,
        "root": root,
        "allow_axioms": sorted(allow),
        "declaration_count": len(decl_rows),
        "classified_count": len(decls),
        "unparsed_count": len(unparsed),
        "unparsed_names": sorted(set(unparsed)),
        "declarations": decls,
    }


def load_snapshot(path):
    """Read a closure snapshot file; returns (snapshot, error) with error
    None on success.  A missing, unparseable or wrong-schema file is a
    usage error, never a guess (a sweep report is not a snapshot)."""
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
    except OSError as exc:
        return None, "cannot read --baseline snapshot %s: %s" % (path, exc)
    try:
        data = json.loads(text)
    except ValueError as exc:
        return None, ("--baseline snapshot %s is not valid JSON: %s"
                      % (path, exc))
    if not isinstance(data, dict) or data.get("schema") != SNAPSHOT_SCHEMA:
        found = data.get("schema") if isinstance(data, dict) else None
        return None, ("--baseline snapshot %s does not carry schema %s"
                      " (found %r); a sweep report (%s) is not a snapshot"
                      % (path, SNAPSHOT_SCHEMA, found, SCHEMA))
    if not isinstance(data.get("declarations"), list):
        return None, ("--baseline snapshot %s carries no declarations"
                      " list" % path)
    return data, None


def diff_closures(baseline, current):
    """Pure per-declaration closure diff of two snapshot dicts; reads only
    the two snapshots' data, so the diff face is toolchain-independent
    (no Lean involvement).  Rows are keyed by full declaration name (a
    repeated name resolves to the last row in the snapshot's sorted
    order) and sorted by name; each carries one verdict - UNCHANGED /
    AXIOM-SET-CHANGED (from_axioms -> to_axioms listed) / NEW-THEOREM /
    LOST-THEOREM - plus new_dependency for a previously-clean declaration
    (empty baseline axiom set) whose current axiom set is non-empty.
    diff_alarm: true when any AXIOM-SET-CHANGED verdict or any
    NEW-DEPENDENCY event exists, false otherwise."""
    base_map = {}
    for decl in baseline["declarations"]:
        base_map[decl["name"]] = decl
    cur_map = {}
    for decl in current["declarations"]:
        cur_map[decl["name"]] = decl
    rows = []
    counts = {DIFF_UNCHANGED: 0, DIFF_CHANGED: 0,
              DIFF_NEW: 0, DIFF_LOST: 0}
    new_dep = []
    for nm in sorted(set(base_map) | set(cur_map)):
        b = base_map.get(nm)
        c = cur_map.get(nm)
        if b is None:
            rows.append({"name": nm, "verdict": DIFF_NEW,
                         "from_axioms": [], "to_axioms": sorted(c["axioms"]),
                         "from_classification": "",
                         "to_classification": c["classification"],
                         "new_dependency": False})
            counts[DIFF_NEW] += 1
            continue
        if c is None:
            rows.append({"name": nm, "verdict": DIFF_LOST,
                         "from_axioms": sorted(b["axioms"]),
                         "to_axioms": [],
                         "from_classification": b["classification"],
                         "to_classification": "",
                         "new_dependency": False})
            counts[DIFF_LOST] += 1
            continue
        from_ax = sorted(b["axioms"])
        to_ax = sorted(c["axioms"])
        dep = (not from_ax) and bool(to_ax)
        verdict = DIFF_CHANGED if from_ax != to_ax else DIFF_UNCHANGED
        rows.append({"name": nm, "verdict": verdict,
                     "from_axioms": from_ax, "to_axioms": to_ax,
                     "from_classification": b["classification"],
                     "to_classification": c["classification"],
                     "new_dependency": dep})
        counts[verdict] += 1
        if dep:
            new_dep.append(nm)
    alarm = counts[DIFF_CHANGED] > 0 or bool(new_dep)
    return {
        "baseline_root": baseline.get("root", ""),
        "rows": rows,
        "summary": {
            "unchanged": {"value": counts[DIFF_UNCHANGED],
                          "basis": DIFF_BASIS_UNCHANGED},
            "axiom_set_changed": {"value": counts[DIFF_CHANGED],
                                  "basis": DIFF_BASIS_CHANGED},
            "new_theorem": {"value": counts[DIFF_NEW],
                            "basis": DIFF_BASIS_NEW},
            "lost_theorem": {"value": counts[DIFF_LOST],
                             "basis": DIFF_BASIS_LOST},
            "new_dependency": {"value": len(new_dep),
                               "basis": DIFF_BASIS_NEWDEP},
        },
        "new_dependency_names": sorted(new_dep),
        "diff_alarm": {"value": alarm, "basis": DIFF_BASIS_ALARM},
    }


def attach_closure_diff(report, diff_face):
    """Insert the closure faces into a built report: closure_diff as a
    {value, basis} top-level field and diff_alarm as the top-level
    {value, basis} alarm flag (the schema-value-basis law; no --baseline
    leaves both keys out, the report shape stays today's)."""
    report["closure_diff"] = {
        "value": diff_face,
        "basis": "per-declaration closure diff of the current sweep against"
                 " the --baseline snapshot (schema %s): rows keyed by full"
                 " declaration name with verdict UNCHANGED /"
                 " AXIOM-SET-CHANGED (from_axioms -> to_axioms listed) /"
                 " NEW-THEOREM / LOST-THEOREM, a {value, basis} summary per"
                 " verdict kind and the NEW-DEPENDENCY names; computed from"
                 " the two snapshots' data only, no toolchain involvement"
                 % SNAPSHOT_SCHEMA,
    }
    report["diff_alarm"] = {
        "value": diff_face["diff_alarm"]["value"],
        "basis": DIFF_BASIS_ALARM,
    }
    return report


def write_json(path, payload):
    """Write the stdout payload (plus one newline) to path as UTF-8."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.write("\n")


def summarize(report):
    """One stderr summary line (stdout stays the single JSON line); with a
    --baseline run the closure-diff counts ride the same line's tail."""
    sys.stderr.write(
        "AXIOM-SWEEP: %s decls=%d clean=%d benign_standard=%d sorry=%d"
        " custom=%d private_covered=%d unparsed=%d errors=%d"
        % (report["verdict"]["value"],
           report["declarations"]["value"],
           report["clean"]["value"],
           report["benign_standard"]["value"],
           report["sorry_alarm"]["value"],
           report["custom_axiom_alarm"]["value"],
           report["private_covered"]["value"],
           report["unparsed"]["value"],
           report["error_count"]["value"]))
    if "closure_diff" in report:
        sumry = report["closure_diff"]["value"]["summary"]
        sys.stderr.write(
            " closure_diff unchanged=%d changed=%d new=%d lost=%d"
            " new_dependency=%d diff_alarm=%s"
            % (sumry["unchanged"]["value"],
               sumry["axiom_set_changed"]["value"],
               sumry["new_theorem"]["value"],
               sumry["lost_theorem"]["value"],
               sumry["new_dependency"]["value"],
               report["diff_alarm"]["value"]))
    sys.stderr.write("\n")


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
LEAN_OUT_STRAY = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:3:0: info: 'b' depends on axioms: [sorryAx]\n")

# Copy-append attribution fixtures: LEAN_OUT_DISPLACED answers a probed
# name from a non-probe line (the emission-correspondence guard face);
# LEAN_OUT_ISOLATED has a failed middle probe whose siblings still parse
# (the no-cascade face the design freezes).
LEAN_OUT_DISPLACED = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:3:0: info: 'a' depends on axioms: [sorryAx]\n")
LEAN_OUT_ISOLATED = (
    "ck.lean:2:0: info: 'a' does not depend on any axioms\n"
    "ck.lean:4:0: error: unknown identifier 'b'\n"
    "ck.lean:6:0: info: 'c' does not depend on any axioms\n")

# The design-4 offline fixture: one public and one private declaration;
# copy-append probes both (the private one classes PRIVATE-COVERED with
# its axiom set, the public one classes CLEAN).
PRIVATE_PUBLIC_LEAN = (
    "theorem pub_one : True := trivial\n"
    "\n"
    "private theorem priv_one : Nat := 1\n")

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
SAMPLE_LEAN_NAMES = [("Foo.bar", 2, False), ("Foo.nested", 3, False),
                     ("baz", 5, False), ("priv_one", 6, True),
                     ("nc_def", 7, False), ("in_block_comment", 10, False),
                     ("with_apostrophe", 12, False),
                     ("in_section", 14, False)]


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
        # declaration enumeration: stack, modifiers, decoys, families out;
        # the private flag rides every row
        got = enumerate_decls(SAMPLE_LEAN)
        vec("decl-enumeration", got == SAMPLE_LEAN_NAMES, "got %s" % (got,))
        vec("decl-enumeration-name-line-face",
            [(nm, ln) for nm, ln, _p in got]
            == [("Foo.bar", 2), ("Foo.nested", 3), ("baz", 5),
                ("priv_one", 6), ("nc_def", 7), ("in_block_comment", 10),
                ("with_apostrophe", 12), ("in_section", 14)],
            "got %s" % (got,))
        got2 = enumerate_decls("private noncomputable def pn : Nat := 1\n"
                               "protected theorem pt : True := trivial\n")
        vec("decl-enumeration-private-modifier-chain",
            got2 == [("pn", 1, True), ("pt", 2, False)],
            "got %s" % (got2,))

        # parse faces: the six classes plus attribution faces; alignment
        # is keyed to the emitted probe list [(line, name)], never
        # positional counting
        rows = parse_print_axioms(LEAN_OUT_CLEAN, [(2, "t_clean")])
        vec("parse-clean", rows[0]["ok"] and rows[0]["axioms"] == [],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_THREE, [(2, "t_three")])
        vec("parse-benign-three",
            rows[0]["ok"] and rows[0]["axioms"] == list(BENIGN_STANDARD),
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SUBSET, [(2, "t_subset")])
        vec("parse-benign-subset",
            rows[0]["ok"] and rows[0]["axioms"] == ["propext"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_SORRY, [(2, "t_sorry")])
        vec("parse-sorry", rows[0]["ok"] and rows[0]["axioms"] == ["sorryAx"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_CUSTOM, [(2, "t_custom")])
        vec("parse-custom",
            rows[0]["ok"] and rows[0]["axioms"] == ["my_axiom.rh"],
            "got %s" % (rows,))
        probes_mixed = [(2, "a"), (4, "b"), (6, "c"), (8, "d")]
        rows = parse_print_axioms(LEAN_OUT_MIXED, probes_mixed)
        ok = (len(rows) == 4 and rows[0]["ok"] and rows[0]["axioms"] == []
              and rows[1]["axioms"] == ["propext", "Classical.choice"]
              and rows[2]["axioms"] == ["sorryAx"]
              and rows[3]["axioms"] == ["my_ax", "propext"])
        vec("parse-mixed-attribution", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_MIXED, probes_mixed + [(10, "e")])
        ok = (rows[0]["ok"] and rows[3]["ok"]
              and not rows[4]["ok"]
              and "no probe block" in rows[4]["reason"])
        vec("parse-tail-no-block", ok, "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_GHOST, [(2, "t_ghost")])
        vec("parse-unknown-identifier",
            not rows[0]["ok"] and "unknown identifier" in rows[0]["raw"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_NAME_MISMATCH, [(2, "t_x")])
        vec("parse-name-mismatch",
            not rows[0]["ok"] and "probe block names" in rows[0]["reason"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_STRAY, [(2, "a")])
        vec("parse-stray-unknown-block-ignored",
            len(rows) == 1 and rows[0]["ok"] and rows[0]["axioms"] == [],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_DISPLACED, [(2, "a")])
        vec("parse-displaced-probed-name-guard",
            all(not r["ok"] for r in rows)
            and "does not correspond" in rows[0]["reason"],
            "got %s" % (rows,))
        rows = parse_print_axioms(LEAN_OUT_ISOLATED,
                                  [(2, "a"), (4, "b"), (6, "c")])
        vec("parse-failed-probe-isolated",
            rows[0]["ok"] and rows[2]["ok"] and not rows[1]["ok"]
            and "unknown identifier" in rows[1]["reason"]
            and "unknown identifier" in rows[1]["raw"],
            "got %s" % (rows,))
        rows = parse_print_axioms("", [(3, "t_any")])
        vec("parse-empty-output-per-probe",
            not rows[0]["ok"]
            and "no probe block" in rows[0]["reason"],
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

        # declaration-classification face: the PRIVATE-COVERED marker
        # class (private declarations probed through the copy-append
        # form), alarm precedence over the marker, and the design-4
        # private-plus-public offline fixture probed end to end
        decls_prec = [("p_sorry", 2, True), ("p_custom", 4, True),
                      ("p_ok", 6, True), ("pub", 8, False)]
        parsed_prec = [
            {"name": "p_sorry", "ok": True, "axioms": ["sorryAx"],
             "reason": "", "raw": ""},
            {"name": "p_custom", "ok": True, "axioms": ["my_ax"],
             "reason": "", "raw": ""},
            {"name": "p_ok", "ok": True, "axioms": [], "reason": "",
             "raw": ""},
            {"name": "pub", "ok": True, "axioms": [], "reason": "",
             "raw": ""},
        ]
        rows = classify_decl_rows("x.lean", decls_prec, parsed_prec, [],
                                  "lake-env")
        vec("private-alarm-precedence",
            [r["classification"] for r in rows]
            == ["SORRY-ALARM", "CUSTOM-AXIOM-ALARM", "PRIVATE-COVERED",
                "CLEAN"],
            "got %s" % (rows,))
        rows = classify_decl_rows(
            "x.lean", [("p_allow", 8, True)],
            [{"name": "p_allow", "ok": True, "axioms": ["my_ax"],
              "reason": "", "raw": ""}], ["my_ax"], "lake-env")
        vec("private-covered-allow-fold",
            rows[0]["classification"] == "PRIVATE-COVERED"
            and rows[0]["allowed"] == ["my_ax"]
            and rows[0]["axioms"] == ["my_ax"],
            "got %s" % (rows,))
        rows = classify_decl_rows("x.lean", [("u", 3, False)],
                                  [{"name": "u", "ok": False, "axioms": [],
                                    "reason": "boom", "raw": "boom"}],
                                  [], "lean-direct")
        vec("unparsed-single-row-isolation",
            rows[0]["classification"] == "UNPARSED"
            and rows[0]["unparsed_reason"] == "boom",
            "got %s" % (rows,))
        fixture_decls = enumerate_decls(PRIVATE_PUBLIC_LEAN)
        fixture_probes = build_copy_checker(
            PRIVATE_PUBLIC_LEAN, ["pub_one", "priv_one"])[1]
        answers = {"pub_one": "'pub_one' does not depend on any axioms",
                   "priv_one": "'priv_one' depends on axioms: [propext]"}
        fixture_out = "".join(
            "ck.lean:%d:0: info: %s\n" % (ln, answers[nm])
            for ln, nm in fixture_probes)
        rows = classify_decl_rows(
            "priv_pub.lean", fixture_decls,
            parse_print_axioms(fixture_out, fixture_probes), [],
            "lean-direct")
        vec("private-covered-fixture",
            [r["classification"] for r in rows]
            == ["CLEAN", "PRIVATE-COVERED"]
            and rows[1]["axioms"] == ["propext"]
            and rows[1]["private"] is True
            and rows[0]["private"] is False,
            "got %s" % (rows,))

        # checker emission and module derivation: the import form is the
        # FALLBACK face (cross-file aggregated sweeps only), pinned
        # verbatim; the copy-append form is the primary face
        checker = build_checker("My.Mod", ["a", "b"])
        vec("checker-emission",
            checker == "import My.Mod\n\n#print axioms a\n#print axioms b\n",
            "got %r" % checker)
        vec("checker-no-module",
            build_checker("", ["x"]) == "\n#print axioms x\n",
            "got %r" % build_checker("", ["x"]))
        checker_ca, probes_ca = build_copy_checker(
            PRIVATE_PUBLIC_LEAN, ["pub_one", "priv_one"])
        vec("copy-append-emission",
            checker_ca == (
                PRIVATE_PUBLIC_LEAN
                + "\n#print axioms pub_one -- rocqwash-probe pub_one\n"
                + "#print axioms priv_one -- rocqwash-probe priv_one\n")
            and probes_ca == [(5, "pub_one"), (6, "priv_one")],
            "got %r / %s" % (checker_ca, probes_ca))
        checker_empty, probes_empty = build_copy_checker("", ["x"])
        vec("copy-append-empty-file",
            checker_empty == "\n#print axioms x -- rocqwash-probe x\n"
            and probes_empty == [(2, "x")],
            "got %r / %s" % (checker_empty, probes_empty))
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
                         "form": "copy-append",
                         "rc": 0, "error_tail": []}]
        canned_decls = [
            {"file": "a.lean", "line": 2, "name": "t_one",
             "classification": "CLEAN", "axioms": [], "custom": [],
             "allowed": [], "private": False, "probe": "lean-direct",
             "raw": "", "unparsed_reason": ""},
            {"file": "a.lean", "line": 5, "name": "t_two",
             "classification": "SORRY-ALARM", "axioms": ["sorryAx"],
             "custom": [], "allowed": [], "private": False,
             "probe": "lean-direct",
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
        priv_decls = [dict(clean_decls[0], name="t_priv",
                           classification="PRIVATE-COVERED",
                           axioms=["propext"], private=True)]
        rep4 = build_report("TMP", canned_files, priv_decls, [], [], {})
        vec("private-covered-report-face",
            rep4["private_covered"]["value"] == 1
            and rep4["classified"]["value"] == 1
            and rep4["verdict"]["value"] == "PASS"
            and exit_code_for(rep4) == 0,
            "got %s / %s" % (rep4["private_covered"], rep4["classified"]))
        payload = json.dumps(rep, ensure_ascii=False)
        vec("single-line-json", "\n" not in payload, "payload holds a newline")
        json_path = os.path.join(tmp, "out.json")
        write_json(json_path, payload)
        with open(json_path, "r", encoding="utf-8") as fh:
            round_trip = json.load(fh)
        vec("json-round-trip", round_trip == rep, "payload mismatch")

        # closure snapshot + diff faces: pure functions over canned rows,
        # offline, zero toolchain launch (the diff face reads only the two
        # snapshots' data, so toolchain independence is by construction)
        def mk_row(name, klass, axioms, file="a.lean", line=1,
                   private=False):
            return {"file": file, "line": line, "name": name,
                    "classification": klass, "axioms": list(axioms),
                    "custom": [], "allowed": [], "private": private,
                    "probe": "lean-direct",
                    "raw": "", "unparsed_reason": ""}

        base_rows = [
            mk_row("t_unchanged", "CLEAN", [], line=2),
            mk_row("t_changed", "BENIGN-STANDARD", ["propext"], line=5),
            mk_row("t_lost", "CLEAN", [], line=7),
            mk_row("t_newdep", "CLEAN", [], line=9),
        ]
        cur_rows = [
            mk_row("t_unchanged", "CLEAN", [], line=2),
            mk_row("t_changed", "BENIGN-STANDARD",
                   ["propext", "Classical.choice"], line=5),
            mk_row("t_new", "CLEAN", [], file="b.lean", line=4),
            mk_row("t_newdep", "SORRY-ALARM", ["sorryAx"], line=9),
        ]

        # snapshot determinism: shuffled input rows must give
        # byte-identical snapshots (the sort normalizes the order)
        snap1 = build_snapshot("TMP", base_rows, [])
        snap2 = build_snapshot("TMP", list(reversed(base_rows)), [])
        vec("snapshot-determinism",
            json.dumps(snap1, ensure_ascii=False)
            == json.dumps(snap2, ensure_ascii=False),
            "shuffled input rows changed the snapshot bytes")
        vec("snapshot-shape",
            snap1["schema"] == SNAPSHOT_SCHEMA
            and snap1["tool"] == TOOL
            and [d["name"] for d in snap1["declarations"]]
                == ["t_changed", "t_lost", "t_newdep", "t_unchanged"]
            and snap1["declaration_count"] == 4
            and snap1["classified_count"] == 4
            and snap1["unparsed_count"] == 0
            and snap1["unparsed_names"] == [],
            "got %s" % (snap1,))
        snap3 = build_snapshot("TMP", [
            mk_row("t_a", "BENIGN-STANDARD",
                   ["propext", "Classical.choice"], line=2),
            mk_row("t_u", "UNPARSED", [], line=4),
        ], [])
        vec("snapshot-axioms-sorted-unparsed-honest",
            snap3["declarations"][0]["axioms"]
            == ["Classical.choice", "propext"]
            and snap3["declaration_count"] == 2
            and snap3["classified_count"] == 1
            and snap3["unparsed_count"] == 1
            and snap3["unparsed_names"] == ["t_u"]
            and all(d["name"] != "t_u" for d in snap3["declarations"]),
            "got %s" % (snap3,))
        snap_pc = build_snapshot("TMP", [
            mk_row("t_priv", "PRIVATE-COVERED", ["propext"], line=3,
                   private=True)], [])
        vec("snapshot-private-covered-closure",
            snap_pc["classified_count"] == 1
            and snap_pc["unparsed_count"] == 0
            and snap_pc["declarations"][0]["classification"]
                == "PRIVATE-COVERED"
            and snap_pc["declarations"][0]["axioms"] == ["propext"],
            "got %s" % (snap_pc,))

        # diff faces: all four verdict kinds in one pair
        base_snap = build_snapshot("BASE", base_rows, [])
        cur_snap = build_snapshot("CUR", cur_rows, [])
        diff = diff_closures(base_snap, cur_snap)
        by_verdict = {}
        for row in diff["rows"]:
            by_verdict.setdefault(row["verdict"], []).append(row["name"])
        vec("diff-all-four-verdicts",
            sorted(by_verdict.get(DIFF_UNCHANGED, [])) == ["t_unchanged"]
            and sorted(by_verdict.get(DIFF_CHANGED, []))
                == ["t_changed", "t_newdep"]
            and by_verdict.get(DIFF_NEW, []) == ["t_new"]
            and by_verdict.get(DIFF_LOST, []) == ["t_lost"],
            "got %s" % (by_verdict,))
        changed_row = next(r for r in diff["rows"]
                           if r["name"] == "t_changed")
        vec("diff-changed-from-to-listed",
            changed_row["verdict"] == DIFF_CHANGED
            and changed_row["from_axioms"] == ["propext"]
            and changed_row["to_axioms"] == ["Classical.choice", "propext"]
            and changed_row["from_classification"] == "BENIGN-STANDARD"
            and changed_row["to_classification"] == "BENIGN-STANDARD"
            and changed_row["new_dependency"] is False,
            "got %s" % (changed_row,))
        newdep_row = next(r for r in diff["rows"] if r["name"] == "t_newdep")
        vec("diff-new-dependency-alarm-true",
            newdep_row["new_dependency"] is True
            and diff["new_dependency_names"] == ["t_newdep"]
            and diff["summary"]["new_dependency"]["value"] == 1
            and diff["diff_alarm"]["value"] is True
            and diff["diff_alarm"]["basis"] == DIFF_BASIS_ALARM,
            "got %s / %s" % (newdep_row, diff["diff_alarm"]))
        vec("diff-summary-shape",
            diff["summary"]["unchanged"]["value"] == 1
            and diff["summary"]["axiom_set_changed"]["value"] == 2
            and diff["summary"]["new_theorem"]["value"] == 1
            and diff["summary"]["lost_theorem"]["value"] == 1
            and all(set(v) == {"value", "basis"}
                    for v in diff["summary"].values()),
            "got %s" % (diff["summary"],))
        vec("diff-rows-sorted-by-name",
            [r["name"] for r in diff["rows"]]
            == sorted(r["name"] for r in diff["rows"]),
            "got %s" % ([r["name"] for r in diff["rows"]],))
        calm = diff_closures(base_snap, build_snapshot("CUR", base_rows + [
            mk_row("t_extra", "CLEAN", [], file="c.lean", line=1)], []))
        vec("diff-alarm-false-face",
            calm["diff_alarm"]["value"] is False
            and calm["summary"]["axiom_set_changed"]["value"] == 0
            and calm["summary"]["new_dependency"]["value"] == 0
            and calm["summary"]["new_theorem"]["value"] == 1,
            "got %s" % (calm["diff_alarm"],))
        same = diff_closures(base_snap, build_snapshot("BASE", base_rows, []))
        vec("diff-identical-all-unchanged",
            len(same["rows"]) == 4
            and all(r["verdict"] == DIFF_UNCHANGED for r in same["rows"])
            and same["diff_alarm"]["value"] is False
            and same["summary"]["unchanged"]["value"] == 4,
            "got %s" % (same["rows"],))

        # baseline load faces: missing, unparseable, wrong-schema, and the
        # write/read round trip
        bad_json_path = os.path.join(tmp, "bad.json")
        with open(bad_json_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{not json")
        err_bad = load_snapshot(bad_json_path)[1]
        vec("baseline-load-bad-json",
            err_bad is not None and "not valid JSON" in err_bad,
            "got %r" % (err_bad,))
        err_absent = load_snapshot(os.path.join(tmp, "absent.json"))[1]
        vec("baseline-load-absent",
            err_absent is not None and "cannot read" in err_absent,
            "got %r" % (err_absent,))
        wrong_path = os.path.join(tmp, "wrong.json")
        write_json(wrong_path, json.dumps({"schema": SCHEMA},
                                          ensure_ascii=False))
        err_wrong = load_snapshot(wrong_path)[1]
        vec("baseline-load-wrong-schema",
            err_wrong is not None and SNAPSHOT_SCHEMA in err_wrong
            and SCHEMA in err_wrong,
            "got %r" % (err_wrong,))
        good_path = os.path.join(tmp, "good.json")
        write_json(good_path, json.dumps(base_snap, ensure_ascii=False))
        loaded, err_load = load_snapshot(good_path)
        vec("baseline-load-round-trip",
            err_load is None and loaded == base_snap,
            "got %r" % (err_load,))

        # report faces: no --baseline leaves the shape untouched (backward
        # compatible); a diff face attaches {value, basis}-wrapped
        rep_nodiff = build_report("TMP", canned_files, clean_decls, [], [],
                                  {})
        vec("no-baseline-backward-compat",
            "closure_diff" not in rep_nodiff
            and "diff_alarm" not in rep_nodiff
            and rep_nodiff["verdict"]["value"] == "PASS"
            and exit_code_for(rep_nodiff) == 0,
            "got keys %s" % (sorted(rep_nodiff),))
        rep_diff = attach_closure_diff(
            build_report("TMP", canned_files, clean_decls, [], [], {}),
            diff)
        bare_diff = [k for k in rep_diff
                     if k not in ("scan_face", "schema")
                     and not (isinstance(rep_diff[k], dict)
                              and "value" in rep_diff[k]
                              and "basis" in rep_diff[k])]
        vec("diff-report-value-basis-wrap",
            bare_diff == []
            and rep_diff["closure_diff"]["value"] is diff
            and rep_diff["diff_alarm"]["value"] is True,
            "bare keys: %s" % bare_diff)
        vec("build-report-diff-face-param",
            "closure_diff" in build_report("TMP", canned_files, clean_decls,
                                           [], [], {}, diff_face=diff)
            and "closure_diff" in build_report("TMP", canned_files,
                                               clean_decls, [], [], {},
                                               diff_face=calm),
            "build_report must accept and attach a diff face")

        # closure flag face: --snapshot/--baseline parse as values
        parsed_flags = build_parser().parse_args(
            ["--root", "x", "--snapshot", "s.json", "--baseline", "b.json"])
        vec("closure-flag-face",
            parsed_flags.snapshot == "s.json"
            and parsed_flags.baseline == "b.json",
            "got %r %r" % (parsed_flags.snapshot, parsed_flags.baseline))

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
        rc, _out, _err = spawn(["--selftest", "--snapshot",
                                os.path.join(tmp, "s.json")])
        vec("exit-selftest-with-snapshot-rc2", rc == 2,
            "--selftest with a scan flag exits %s (usage error)" % rc)

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
    ap.add_argument("--snapshot", metavar="OUT",
                    help="additionally write a machine closure snapshot"
                         " (schema %s) of the sweep to OUT: per classified"
                         " declaration the full probe name, the sorted"
                         " axiom set and the class; deterministic (sorted,"
                         " double-run byte-identical) and"
                         " toolchain-independent" % SNAPSHOT_SCHEMA)
    ap.add_argument("--baseline", metavar="SNAPSHOT",
                    help="diff the current closure against this previously"
                         " written snapshot file (schema %s) and add the"
                         " closure_diff block plus the top-level diff_alarm"
                         " flag; the diff reads only the two snapshots'"
                         " data, no Lean needed (the beyond-platform"
                         " closure-evolution audit face)"
                         % SNAPSHOT_SCHEMA)
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
        if args.root or args.json or args.snapshot or args.baseline:
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
    # --baseline is validated up front (a missing, unparseable or
    # wrong-schema file is a usage error, fail fast before any probing).
    baseline_snap = None
    if args.baseline:
        baseline_snap, baseline_err = load_snapshot(args.baseline)
        if baseline_err is not None:
            sys.stderr.write("%s: %s\n" % (TOOL, baseline_err))
            return EXIT_USAGE
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
    # Closure faces: build the current snapshot once when either flag is
    # given; with a baseline, attach the closure_diff + diff_alarm fields
    # (the exit code stays the sweep's own green/red face - diff_alarm
    # rides the payload).  A red sweep still snapshots: the evolution
    # audit wants every closure state, judged or not.
    closure_snap = None
    if args.snapshot or args.baseline:
        closure_snap = build_snapshot(args.root,
                                      report["declarations_detail"]["value"],
                                      args.allow_axioms)
    if baseline_snap is not None:
        attach_closure_diff(
            report, diff_closures(baseline_snap, closure_snap))
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
    if args.snapshot:
        try:
            write_json(args.snapshot,
                       json.dumps(closure_snap, ensure_ascii=False))
        except OSError as exc:
            sys.stderr.write("%s: --snapshot write failed: %s\n"
                             % (TOOL, exc))
            return EXIT_RED
    summarize(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
