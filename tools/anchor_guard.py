#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""anchor_guard.py - anchor and certificate guard for one module directory (rocqwash tools/).
Purpose.  A certificate that cannot fail proves nothing.  Two mechanical
  questions for one module directory: is every declared anchor actually
  anchored (compile, zero axioms, holds at the declared sample points), and
  is every certificate mutation-killing (an injected declared defect flips at
  least one verdict)?  Zero kills = VACUOUS and red; no axiom whitelist in v1.
Interface.  python -I tools/anchor_guard.py --repo DIR --manifest FILE
  [--out DIR] [--rocq BIN] [--coqchk BIN] [--timeout SEC] [--keep].
  Manifest schema rocqwash.anchor/1; mutant entries are copied into the
  manifest from mutants-v1.json (rocqwash.mutants/1), never loaded by this
  tool.  Binaries resolve per flag, then environment; --selftest runs the
  embedded vector suite, pre-argparse, never listed by --help.
Faces.  1 manifest load and census (rules V1-V10; masked scan, definitions
  included); 2 module compile tri-classification in a private temp workdir;
  3 heavy face, baseline only (coqchk -o kernel recheck); 4 certificate
  probe face per anchor (vm_compute checks plus Print Assumptions,
  marker-parsed); 5 mutation injection and kill judgment; 6 verdict exit.
Dependencies.  Python 3 standard library only; rocq and coqchk binaries from
  flags or environment (never downloaded, never simulated).  Zero network.
Evidence.  Deterministic: sorted inputs, no wall clock; same module bytes
  plus the same manifest give the byte-identical report on a double run.
  Write faces: the caller-named --out report plus the private temp workdir
  (removed unless --keep).  Thermal: guarded runs wrap in tools/cpu_guard.sh.
Exit-codes.  0 PASS; 1 red (an unanchored anchor, a VACUOUS certificate, or
  a module compile-broken); 2 usage; 9 fail-loud; 111 honest skip (SKIP).
Usage:
  python -I tools/anchor_guard.py --repo <module-dir> --manifest certificates.json --out /tmp/evid/anchor
  ROCWASH_ROCQ=/path/rocq ROCWASH_COQCHK=/path/coqchk python -I tools/anchor_guard.py --repo . --manifest certificates.json
"""
# Extended contract (moved from the docstring to hold the 30-line header
# budget; the docstring carries the field set, this block the detail):
# Interface detail.  --out DIR receives the deterministic report volume
#   (anchor-guard-report.json); without --out the summary goes to stdout
#   only and no file is written.  Binary paths resolve per flag, then
#   environment: --rocq / ROCWASH_ROCQ, --coqchk / ROCWASH_COQCHK.  Both
#   binaries are required for a run: either unconfigured = honest skip 111
#   before any work; a configured but nonexistent path = 9.
# Face detail.  1 the module bytes are read and hashed (md5) and the
#   statement census runs over the masked module text (nested comments
#   counted, string escapes honored), so rule V8 can check definition faces
#   against the census too.  2 compile-ok proceeds to judgment;
#   compile-broken (rc != 0 or timeout) is RED: the subject is unjudgeable
#   and nothing can be certified; a toolchain not configured exits 111
#   before any work.  3 the CONTEXT SUMMARY "* Axioms:" section is parsed;
#   clean proceeds, axioms is an unanchored module (red), no-summary or a
#   coqchk error is unjudgeable (red); mutant copies skip coqchk in v1 (the
#   kill channel is the probe face; one kernel pass on the pristine module
#   pins trust).  4 the probe copy appends one "Eval vm_compute in (<check>)."
#   line per sample point in declared order, then "Print Assumptions
#   <certificate_face>."; markers "^[ \t]*= (true|false)$" in order plus one
#   assumption marker ("Closed under the global context" or "^Axioms:$"); on
#   any marker-count mismatch the anchor falls back to one probe copy per
#   emitted line for exact attribution; a mismatch after the fallback is a
#   probe-error verdict and probe-error is not green.  5 per manifest mutant
#   a fresh pristine copy is injected (workdir m%03d_<id>, baseline b000),
#   recompiled, and on a clean compile the probe face re-runs for every
#   anchor; sites = len(re.findall(replacement, module_text)); one pass, the
#   mutated text is never rescanned; classifications injected /
#   not-applicable (sites = 0, debt register, never a kill) / stillborn
#   (compile-broken or timeout, debt register with the error tail).  A cell
#   is killed when any check computes false or the assumptions probe flips
#   closed to axioms; survived when all probes ran clean and true; an anchor
#   whose certificate kills zero mutants among the injected-and-judged pool
#   is flagged VACUOUS and is red.  6 red channels are collected
#   (unanchored anchors, vacuous certificates, module compile-broken,
#   heavy-face failure), the report is assembled, the summary printed, and
#   the run exits per the exit-code matrix.
# Evidence detail.  The v1 independence requirement (a certificate's
#   independent_derivation must not share the suspect series with the
#   referent's own derivation; the named exemplar is atanh versus Mercator)
#   is an authoring obligation: non-emptiness is machine-checked at load and
#   the text is recorded verbatim in the report; mechanical independence
#   checking is future work and is not claimed.  Temp paths never reach the
#   report: compiler output passes through a strip function that replaces
#   the workdir with <anguard-tmp>.  Thermal contract form:
#   verify/extract_magic_check.py (compile children stay inside the guard's
#   process tree).
# Exit-code detail.  0 = PASS (every anchor baseline hold; every certificate
#   kills at least one injected-and-judged mutant; not-applicable /
#   stillborn / survived mutants may sit in the debt register without
#   blocking PASS).  1 = red (any unanchored anchor, any VACUOUS
#   certificate, or module compile-broken).  2 = usage error (manifest
#   missing, unparsable, or a V1-V10 violation; --selftest combined with
#   other flags; selftest assertion failure).  9 = fail-loud (--repo
#   directory missing; a configured binary path nonexistent; report write
#   failure; probe infrastructure failure such as a subprocess launch error
#   or temp setup failure).  111 = honest skip (rocq or coqchk not
#   configured via flag or environment: the anchor guard honestly skips and
#   judges nothing, reported as a SKIP line, following the verify/ rc 111
#   skip convention; the selftest toolchain tier takes the same face).
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

PROG = "anchor_guard"
SCHEMA = "rocqwash-anchor-guard/1"      # this tool's own report volume
MANIFEST_SCHEMA = "rocqwash.anchor/1"   # ask-frozen dotted form (rule V1)
REPORT_NAME = "anchor-guard-report.json"
CLOSED_LINE = "Closed under the global context"
TMP_MARK = "<anguard-tmp>"
ERROR_TAIL_LINES = 12

# coqchk CONTEXT SUMMARY section heads (line-start anchored).
SUMMARY_RE = re.compile(r"^\* Axioms:(.*)$", re.M)
SUMMARY_NEXT_RE = re.compile(r"^\* ", re.M)

# Probe-face markers (frozen forms).
BOOL_RE = re.compile(r"^[ \t]*= (true|false)$", re.M)
AXIOMS_HEAD_RE = re.compile(r"^Axioms:$", re.M)

# Statement families the census reads (name-bearing vernaculars; the
# axiom_guard theorem families widened with the definition families so
# V8 can check definition faces too).
STMT_RE = re.compile(
    r"(?m)^[ \t]*(?:#\[[^\]]*\][ \t]*\r?\n?[ \t]*|"
    r"(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Theorem|Lemma|Corollary|Proposition|Remark|Fact|Example|Instance|"
    r"Definition|Fixpoint|Function)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")

ANCHOR_NAME_RE = re.compile(r"[A-Za-z0-9_]{1,64}\Z")
CORNERS = ("smallest", "boundary", "interior")
REQUIRED_CORNERS = ("smallest", "boundary")

# Frozen report shapes.
REPORT_KEYS = ("schema", "module", "module_md5", "rocq", "coqchk", "timeout",
               "anchors", "mutants", "vacuous_certificates",
               "unanchored_anchors", "debt_register", "red_reasons",
               "verdict")
ANCHOR_KEYS = ("name", "referent", "certificate_face", "sample_point_count",
               "corners", "independent_derivation", "baseline")
BASELINE_KEYS = ("assumptions", "checks", "verdict")
CHECK_KEYS = ("index", "label", "corner", "value")
MUTANT_KEYS = ("id", "class", "sites", "classification", "compile_rc",
               "error_tail", "verdict", "kills", "per_anchor")
CELL_KEYS = ("anchor", "verdict")

# Replacement-template escapes that are plain character escapes in a
# re.sub template (unknown ASCII-letter escapes are re.sub errors).
TEMPLATE_PLAIN_ESCAPES = set("abfnrtv")


class UsageError(Exception):
    """A manifest or flag violation: exit code 2, offending field named."""


class InfraError(Exception):
    """An environment-level failure the run cannot judge: exit code 9."""


def md5_of_bytes(raw):
    return hashlib.md5(raw).hexdigest()


def sanitize_fs(ident):
    """Filesystem-safe form of an identifier for temp workdir and log
    names only; report values keep the verbatim identifier."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", ident)


def mask_comments_strings(text):
    """Blank out comment and string literal bodies so name extraction only
    sees code positions (nested (* *) counted, backslash escapes
    honored)."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("(*", i):
            depth = 0
            start = i
            while i < n:
                if text.startswith("(*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*)", i):
                    depth -= 1
                    i += 2
                    if depth == 0:
                        break
                else:
                    i += 1
            out.append(" " * (i - start))
        elif text.startswith('"', i):
            start = i
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(" " * (i - start))
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def statement_names(text):
    """[(name, line_no)] of the censused statement families, comments and
    strings masked out first (comment decoys never enter the census)."""
    masked = mask_comments_strings(text)
    out = []
    for m in STMT_RE.finditer(masked):
        line = masked.count("\n", 0, m.start(2)) + 1
        out.append((m.group(2), line))
    return out


def template_backref_check(pattern_text, rx):
    """None when every backreference in the re.sub replacement template
    names an existing group of the search pattern, else the offending
    description.  Numeric (\\1, \\12) and named (\\g<name>) forms are
    recognized; unknown ASCII-letter escapes are rejected because re.sub
    treats them as errors."""
    groups = rx.groups
    names = rx.groupindex
    i = 0
    n = len(pattern_text)
    while i < n:
        ch = pattern_text[i]
        if ch != "\\":
            i += 1
            continue
        nxt = pattern_text[i + 1] if i + 1 < n else ""
        if nxt == "g":
            m = re.match(r"g<([A-Za-z_][A-Za-z0-9_]*|[0-9]+)>",
                         pattern_text[i + 2:])
            if m is None:
                return "\\g<...> form malformed at offset %d" % i
            ref = m.group(1)
            if ref.isdigit():
                if int(ref) > groups:
                    return "\\g<%s> exceeds the %d group(s) of the " \
                        "replacement pattern" % (ref, groups)
            elif ref not in names:
                return "\\g<%s> names no group of the replacement " \
                    "pattern" % ref
            i += 2 + m.end()
        elif nxt.isdigit() and nxt != "0":
            digits = re.match(r"[1-9][0-9]?", pattern_text[i + 1:]).group(0)
            if int(digits) > groups:
                return "\\%s exceeds the %d group(s) of the replacement " \
                    "pattern" % (digits, groups)
            i += 1 + len(digits)
        elif nxt in TEMPLATE_PLAIN_ESCAPES or nxt in "0xuN":
            i += 2
        elif nxt == "":
            return "template ends with a bare backslash"
        elif nxt.isalpha():
            return "unknown template escape \\%s at offset %d" % (nxt, i)
        else:
            i += 2
    return None


def load_manifest(path, repo_dir):
    """Parse and validate one rocqwash.anchor/1 manifest against rules
    V1-V10; returns the manifest object or raises UsageError with the
    offending field named."""
    if not os.path.isfile(path):
        raise UsageError("manifest file missing: %s" % path)
    with io.open(path, "r", encoding="utf-8") as fh:
        try:
            man = json.load(fh)
        except ValueError as exc:
            raise UsageError("manifest is not valid JSON: %s" % exc)
    if not isinstance(man, dict):
        raise UsageError("manifest is not a JSON object")            # V10
    if man.get("schema") != MANIFEST_SCHEMA:
        raise UsageError("manifest schema must be the exact string %r "
                         "(got %r)" % (MANIFEST_SCHEMA, man.get("schema")))
    module = man.get("module")
    if not isinstance(module, str) or not module:
        raise UsageError("manifest module must be a non-empty string")
    module_path = os.path.join(repo_dir, module)
    if not module.endswith(".v") or not os.path.isfile(module_path):
        raise UsageError("manifest module does not name an existing .v "
                         "file under --repo: %r" % module)           # V2
    anchors = man.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        raise UsageError("manifest anchors must be a non-empty array")
    mutants = man.get("mutants")
    if not isinstance(mutants, list) or not mutants:
        raise UsageError("manifest mutants must be a non-empty array")  # V3

    # V8 needs the module census (masked scan).
    with io.open(module_path, "r", encoding="utf-8", errors="replace") as fh:
        module_text = fh.read()
    census = set(name for name, _line in statement_names(module_text))

    seen_anchors = set()
    for idx, anchor in enumerate(anchors):
        where = "anchor #%d" % (idx + 1)
        if not isinstance(anchor, dict):
            raise UsageError("%s is not a JSON object" % where)
        name = anchor.get("name")
        if not isinstance(name, str) or not ANCHOR_NAME_RE.match(name):
            raise UsageError("%s name must match [A-Za-z0-9_]{1,64}: %r"
                             % (where, name))                        # V4
        if name in seen_anchors:
            raise UsageError("anchor name not unique: %r" % name)   # V4
        seen_anchors.add(name)
        for key in ("referent", "certificate_face"):
            val = anchor.get(key)
            if not isinstance(val, str) or not val:
                raise UsageError("anchor %s %s must be a non-empty "
                                 "string" % (name, key))
            if val not in census:
                raise UsageError("anchor %s %s not found in the module "
                                 "statement census: %r"
                                 % (name, key, val))                # V8
        points = anchor.get("sample_points")
        if not isinstance(points, list) or not points:
            raise UsageError("anchor %s sample_points must be a non-empty "
                             "array" % name)
        corners = set()
        for p_idx, point in enumerate(points):
            if not isinstance(point, dict):
                raise UsageError("anchor %s sample point #%d is not a JSON "
                                 "object" % (name, p_idx + 1))
            label = point.get("label")
            if not isinstance(label, str) or not label:
                raise UsageError("anchor %s sample point #%d label must be "
                                 "a non-empty string" % (name, p_idx + 1))
            corner = point.get("corner")
            if corner not in CORNERS:
                raise UsageError("anchor %s sample point #%d corner must be "
                                 "one of %s (got %r)"
                                 % (name, p_idx + 1, "/".join(CORNERS),
                                    corner))                        # V6
            corners.add(corner)
            check = point.get("check")
            if not isinstance(check, str) or not check:
                raise UsageError("anchor %s sample point #%d check must be "
                                 "a non-empty string" % (name, p_idx + 1))
            if check.rstrip().endswith("."):
                raise UsageError("anchor %s sample point #%d check must not "
                                 "end with a period (the driver appends "
                                 "it)" % (name, p_idx + 1))         # V6
        for needed in REQUIRED_CORNERS:
            if needed not in corners:
                raise UsageError("anchor %s corner coverage: the sample "
                                 "set must include %s (corners present: "
                                 "%s)" % (name, needed,
                                          ", ".join(sorted(corners))))
        deriv = anchor.get("independent_derivation")
        if not isinstance(deriv, str) or not deriv:
            raise UsageError("anchor %s independent_derivation must be a "
                             "non-empty string" % name)              # V7

    seen_ids = set()
    for m_idx, mut in enumerate(mutants):
        where = "mutant #%d" % (m_idx + 1)
        if not isinstance(mut, dict):
            raise UsageError("%s is not a JSON object" % where)
        mid = mut.get("id")
        if not isinstance(mid, str) or not mid:
            raise UsageError("%s id must be a non-empty string" % where)
        if mid in seen_ids:
            raise UsageError("mutant id not unique: %r" % mid)      # V9
        seen_ids.add(mid)
        if mut.get("class") != "semantic":
            raise UsageError("mutant %s class must be exactly \"semantic\" "
                             "(got %r); any other class value including "
                             "build is out of v1 scope and recorded as "
                             "future work" % (mid, mut.get("class")))  # V9
        for key in ("pattern", "replacement"):
            val = mut.get(key)
            if not isinstance(val, str) or not val:
                raise UsageError("mutant %s %s must be a non-empty "
                                 "string" % (mid, key))             # V9
        try:
            rx = re.compile(mut["replacement"])
        except re.error as exc:
            raise UsageError("mutant %s replacement does not compile as a "
                             "re pattern: %s" % (mid, exc))          # V9
        bad = template_backref_check(mut["pattern"], rx)
        if bad:
            raise UsageError("mutant %s pattern backreference out of "
                             "range: %s" % (mid, bad))               # V9
    return man


def run_cmd(argv, timeout):
    """Subprocess run with merged stdout/stderr and a hard timeout; the
    caller decides every verdict from (rc, output, error); no silent
    fallback.  error is None on a clean launch, "timeout" on a timeout,
    and an OS-level message string when the binary cannot be launched.
    Decoded output is LF-normalized once here: the rocq launcher emits
    CRLF on Windows and the frozen marker regexes anchor on "\\n". """
    try:
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, _decode_normalize(p.stdout), None
    except subprocess.TimeoutExpired as e:
        partial = b""
        if e.stdout:
            partial += e.stdout
        if e.stderr:
            partial += e.stderr
        return None, _decode_normalize(partial), "timeout"
    except OSError as e:
        return None, "", str(e)


def _decode_normalize(raw):
    return raw.decode("utf-8", "replace").replace("\r\n", "\n")


def error_tail(output, lines=ERROR_TAIL_LINES):
    tail = [ln for ln in output.splitlines() if ln.strip()]
    return tail[-lines:]


def strip_tmp(output, work):
    """Normalize the run's private temp directory out of compiler output
    so error tails (which embed the .v copy path) stay byte-stable
    across runs - determinism of the report volume."""
    return output.replace(work, TMP_MARK)


def compile_one(rocq, src_v, repo_dir, timeout, log_dir=None, name=None):
    """Compile one temp-side .v; returns (rc, output, error).  The .vo
    lands next to the copy (temp workdir), never in the repository."""
    argv = [rocq, "c", "-native-compiler", "no", "-q",
            "-Q", repo_dir, "", src_v]
    rc, out, err = run_cmd(argv, timeout)
    if log_dir and name:
        with io.open(os.path.join(log_dir, name + ".compile.log"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    return rc, out, err


def parse_axioms_summary(output):
    """Parse the coqchk CONTEXT SUMMARY axioms section.
    Returns (status, axiom_names): status in
    {"clean", "axioms", "no-summary"}.  Entries are module-qualified."""
    m = SUMMARY_RE.search(output)
    if m is None:
        return "no-summary", []
    first = m.group(1).strip()
    if first == "<none>":
        return "clean", []
    names = []
    if first:
        names.append(first)
    nxt = SUMMARY_NEXT_RE.search(output, m.end())
    body = output[m.end():nxt.start()] if nxt else output[m.end():]
    for ln in body.splitlines():
        ln = ln.strip()
        if ln:
            names.append(ln)
    return "axioms", names


def parse_probe_output(output, n_checks):
    """Attribute ordered probe markers.  Returns (checks, assumptions,
    axiom_names) with checks a list of n_checks booleans and assumptions
    "closed"|"axioms", or None when the marker counts do not match (the
    caller falls back to per-line probes)."""
    bools = [(m.start(), m.group(1) == "true") for m in BOOL_RE.finditer(output)]
    marks = []
    for m in re.finditer(re.escape(CLOSED_LINE), output):
        marks.append((m.start(), "closed"))
    for m in AXIOMS_HEAD_RE.finditer(output):
        marks.append((m.start(), "axioms"))
    marks.sort()
    if len(bools) != n_checks or len(marks) != 1:
        return None
    axiom_names = []
    pos, kind = marks[0]
    if kind == "axioms":
        for ln in output[pos:].splitlines()[1:]:
            ln = ln.strip()
            if ln:
                axiom_names.append(ln)
    return [b for _pos, b in bools], kind, axiom_names


def probe_write(probe_v, base_text, emitted_lines):
    """Write one probe copy (a separate _probe_ filename, so the base .vo
    of the module under judgment stays intact for the heavy face)."""
    text = base_text
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + "\n".join(emitted_lines) + "\n"
    with io.open(probe_v, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def probe_face(rocq, base_text, work_dir, stem, anchor, repo_dir, timeout,
               log_dir, tag, work_root):
    """Face 4 for one anchor.  Returns {"assumptions": "closed"|"axioms"|
    None, "axiom_names": [...], "checks": [bool|None per sample point],
    "compile_broken": bool, "error_tail": [...]}."""
    points = anchor["sample_points"]
    emitted = ["Eval vm_compute in (%s)." % sp["check"] for sp in points]
    emitted.append("Print Assumptions %s." % anchor["certificate_face"])
    probe_v = os.path.join(work_dir,
                           "%s_probe_%s.v" % (stem, anchor["name"]))
    probe_write(probe_v, base_text, emitted)
    rc, out, err = compile_one(rocq, probe_v, repo_dir, timeout, log_dir, tag)
    if err is not None and err != "timeout":
        raise InfraError("probe launch failure (%s): %s" % (tag, err))
    checks = [None] * len(points)
    result = {"assumptions": None, "axiom_names": [], "checks": checks,
              "compile_broken": False, "error_tail": []}
    if rc == 0 and err is None:
        parsed = parse_probe_output(out, len(points))
        if parsed is not None:
            result["checks"], result["assumptions"], \
                result["axiom_names"] = parsed
            return result
    # Fallback: one probe copy per emitted line (exact attribution).  The
    # verdict is then re-derived from the per-line data: the anchor is a
    # probe-error exactly when some emitted line produced no data.
    result["error_tail"] = error_tail(strip_tmp(out, work_root))
    with io.open(os.path.join(log_dir, tag + ".probe.log"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    for i, line in enumerate(emitted):
        probe_write(probe_v, base_text, [line])
        rc2, out2, err2 = compile_one(rocq, probe_v, repo_dir, timeout)
        if err2 is not None and err2 != "timeout":
            raise InfraError("probe launch failure (%s line %d): %s"
                             % (tag, i + 1, err2))
        with io.open(os.path.join(log_dir, "%s.probe.%02d.log"
                                  % (tag, i + 1)), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(out2)
        if rc2 != 0 or err2 is not None:
            continue
        if i < len(points):
            m = BOOL_RE.search(out2)
            if m is not None:
                result["checks"][i] = (m.group(1) == "true")
        else:
            m_ax = AXIOMS_HEAD_RE.search(out2)
            if m_ax is not None:
                result["assumptions"] = "axioms"
                result["axiom_names"] = [ln.strip()
                                         for ln in
                                         out2[m_ax.end():].splitlines()
                                         if ln.strip()]
            elif CLOSED_LINE in out2:
                result["assumptions"] = "closed"
    result["compile_broken"] = (result["assumptions"] is None
                                or any(v is None for v in result["checks"]))
    return result


def baseline_verdict(probe):
    """Baseline verdict per the frozen table: probe-error dominates, then
    axioms, then failing, then hold."""
    if probe["compile_broken"] or probe["assumptions"] is None \
            or any(v is None for v in probe["checks"]):
        return "probe-error"
    if probe["assumptions"] == "axioms":
        return "axioms"
    if any(v is False for v in probe["checks"]):
        return "failing"
    return "hold"


def cell_verdict(baseline_assumptions, probe):
    """Mutant cell verdict per the frozen table."""
    if probe["compile_broken"] or probe["assumptions"] is None \
            or any(v is None for v in probe["checks"]):
        return "probe-error"
    if any(v is False for v in probe["checks"]):
        return "killed"
    if baseline_assumptions == "closed" \
            and probe["assumptions"] == "axioms":
        return "killed"
    return "survived"


def classify_mutant(sites, compile_ok):
    """Frozen classification: sites = 0 -> not-applicable; clean compile
    -> injected; broken compile or timeout -> stillborn."""
    if sites == 0:
        return "not-applicable"
    return "injected" if compile_ok else "stillborn"


def apply_mutant(module_text, entry):
    """Inject one mutant: the applier searches for the CORRECT form
    (replacement) and writes the DEFECT form (pattern).  Returns
    (mutated_text, sites); sites is counted before substitution and the
    mutated text is never rescanned."""
    rx = re.compile(entry["replacement"])
    sites = len(rx.findall(module_text))
    if sites == 0:
        return module_text, 0
    try:
        mutated = rx.sub(entry["pattern"], module_text)
    except re.error as exc:
        raise InfraError("mutant %s applier failure (the manifest loader "
                        "accepted a template re.sub rejects): %s"
                        % (entry["id"], exc))
    return mutated, sites


def new_report(man, module_md5, rocq, coqchk, timeout):
    """The report skeleton; the write face fills anchors/mutants and the
    sorted red channels."""
    return {
        "schema": SCHEMA,
        "module": man["module"],
        "module_md5": module_md5,
        "rocq": rocq,
        "coqchk": coqchk,
        "timeout": timeout,
        "anchors": [],
        "mutants": [],
        "vacuous_certificates": [],
        "unanchored_anchors": [],
        "debt_register": [],
        "red_reasons": [],
        "verdict": "PASS",
    }


def anchor_report_entry(anchor, baseline):
    return {
        "name": anchor["name"],
        "referent": anchor["referent"],
        "certificate_face": anchor["certificate_face"],
        "sample_point_count": len(anchor["sample_points"]),
        "corners": sorted(sp["corner"] for sp in anchor["sample_points"]),
        "independent_derivation": anchor["independent_derivation"],
        "baseline": baseline,
    }


def baseline_report_entry(anchor, probe):
    return {
        "assumptions": probe["assumptions"],
        "checks": [
            {"index": i,
             "label": sp["label"],
             "corner": sp["corner"],
             "value": probe["checks"][i]}
            for i, sp in enumerate(anchor["sample_points"])],
        "verdict": baseline_verdict(probe),
    }


def mutant_report_entry(entry, sites, classification):
    return {
        "id": entry["id"],
        "class": entry["class"],
        "sites": sites,
        "classification": classification,
        "compile_rc": None,
        "error_tail": None,
        "verdict": None,
        "kills": [],
        "per_anchor": [],
    }


def guard(repo_dir, manifest_path, rocq, coqchk, timeout, out_dir, keep):
    """Full run; returns (exit_code, report_dict).  Write faces: the
    private temp workdir and (when given) the caller-named --out report
    file."""
    man = load_manifest(manifest_path, repo_dir)
    module_path = os.path.join(repo_dir, man["module"])
    with io.open(module_path, "rb") as fh:
        raw = fh.read()
    module_md5 = md5_of_bytes(raw)
    base_text = raw.decode("utf-8", "replace")
    stem = os.path.basename(man["module"])[:-2]

    work = tempfile.mkdtemp(prefix="rocqwash_anchor_guard_")
    log_dir = os.path.join(work, "logs")
    os.makedirs(log_dir)
    with io.open(os.path.join(log_dir, "manifest.log"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(man, ensure_ascii=False, indent=1,
                            sort_keys=True) + "\n")
    report = new_report(man, module_md5, rocq, coqchk, timeout)
    reds = []
    repo_dir_abs = os.path.abspath(repo_dir)
    try:
        # Baseline workdir b000: the pristine module copy (byte-identical).
        bdir = os.path.join(work, "b000")
        os.makedirs(bdir)
        base_v = os.path.join(bdir, stem + ".v")
        with io.open(base_v, "wb") as fh:
            fh.write(raw)
        rc, out, err = compile_one(rocq, base_v, repo_dir_abs, timeout,
                                   log_dir, "b000_base")
        if err is not None and err != "timeout":
            raise InfraError("module compile launch failure: %s" % err)
        module_compile_ok = (rc == 0 and err is None)
        if not module_compile_ok:
            reds.append("module compile-broken (subject unjudgeable; "
                        "rc %s)" % (rc if rc is not None else "timeout"))
        else:
            # Heavy face, baseline only, on the base .vo (the probe copies
            # never overwrite it); mutant copies skip coqchk in v1.
            chk_rc, chk_out, chk_err = run_cmd(
                [coqchk, "-o", "-Q", repo_dir_abs, "", "-Q", bdir, "", stem],
                timeout)
            with io.open(os.path.join(log_dir, "b000_heavy.coqchk.log"),
                         "w", encoding="utf-8", newline="\n") as fh:
                fh.write(chk_out)
            if chk_err is not None or chk_rc is None or chk_rc != 0:
                detail = chk_err or ("rc %s" % chk_rc)
                reds.append("heavy face coqchk-error (%s; tail: %s)"
                            % (detail,
                               "; ".join(error_tail(
                                   strip_tmp(chk_out, work), 3)) or "empty"))
            else:
                status, axiom_names = parse_axioms_summary(chk_out)
                if status == "axioms":
                    reds.append("heavy face axioms: %s"
                                % ", ".join(axiom_names))
                elif status == "no-summary":
                    reds.append("heavy face no-summary (unjudgeable is "
                                "not green)")

        # Face 4 baseline, per anchor, in b000.
        baselines = {}
        for anchor in man["anchors"]:
            tag = "b000_probe_%s" % anchor["name"]
            probe = probe_face(rocq, base_text, bdir, stem, anchor,
                               repo_dir_abs, timeout, log_dir, tag, work)
            verdict = baseline_verdict(probe)
            baselines[anchor["name"]] = verdict
            report["anchors"].append(anchor_report_entry(
                anchor, baseline_report_entry(anchor, probe)))
            if verdict != "hold":
                report["unanchored_anchors"].append(anchor["name"])
                reds.append("anchor %s baseline %s (unanchored)"
                            % (anchor["name"], verdict))

        # Face 5: per mutant, inject into a fresh pristine copy, recompile,
        # and on a clean compile re-run the probe face for every anchor.
        for m_idx, entry in enumerate(man["mutants"], start=1):
            tag = "m%03d_%s" % (m_idx, sanitize_fs(entry["id"]))
            mdir = os.path.join(work, tag)
            os.makedirs(mdir)
            mutated, sites = apply_mutant(base_text, entry)
            entry_report = mutant_report_entry(entry, sites,
                                               classify_mutant(sites, False))
            report["mutants"].append(entry_report)
            if sites == 0:
                report["debt_register"].append(entry["id"])
                continue
            mut_v = os.path.join(mdir, stem + ".v")
            with io.open(mut_v, "w", encoding="utf-8", newline="") as fh:
                fh.write(mutated)
            mrc, mout, merr = compile_one(rocq, mut_v, repo_dir_abs, timeout,
                                          log_dir, tag + "_module")
            if merr is not None and merr != "timeout":
                raise InfraError("mutant %s compile launch failure: %s"
                                 % (entry["id"], merr))
            compile_ok = (mrc == 0 and merr is None)
            entry_report["classification"] = classify_mutant(sites, compile_ok)
            if not compile_ok:
                entry_report["compile_rc"] = mrc if mrc is not None else -1
                entry_report["error_tail"] = error_tail(
                    strip_tmp(mout, work))
                report["debt_register"].append(entry["id"])
                continue
            cells = []
            for anchor in man["anchors"]:
                ptag = "%s_probe_%s" % (tag, anchor["name"])
                probe = probe_face(rocq, mutated, mdir, stem, anchor,
                                   repo_dir_abs, timeout, log_dir, ptag,
                                   work)
                cells.append({"anchor": anchor["name"],
                              "verdict": cell_verdict(
                                  baselines[anchor["name"]], probe)})
            entry_report["per_anchor"] = cells
            killed_names = [c["anchor"] for c in cells
                            if c["verdict"] == "killed"]
            if killed_names:
                entry_report["verdict"] = "killed"
                entry_report["kills"] = sorted(killed_names)
            elif any(c["verdict"] == "probe-error" for c in cells):
                entry_report["verdict"] = "probe-error"
            else:
                entry_report["verdict"] = "survived"

        # Face 6: verdict assembly.  The judged pool is the injected
        # mutants that produced a verdict; a certificate that kills zero
        # judged mutants is VACUOUS.
        judged = [m for m in report["mutants"]
                  if m["classification"] == "injected"
                  and m["verdict"] in ("killed", "survived")]
        killed_by = {}
        for m in judged:
            for name in m["kills"]:
                killed_by[name] = killed_by.get(name, 0) + 1
        vacuous = sorted(a["name"] for a in man["anchors"]
                         if killed_by.get(a["name"], 0) == 0)
        report["vacuous_certificates"] = vacuous
        for name in vacuous:
            reds.append("vacuous certificate: %s (kills 0 of %d judged)"
                        % (name, len(judged)))
        report["unanchored_anchors"] = sorted(report["unanchored_anchors"])
        report["debt_register"] = sorted(report["debt_register"])
        report["red_reasons"] = sorted(reds)
        report["verdict"] = "RED" if reds else "PASS"
        if out_dir:
            try:
                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)
                report_path = os.path.join(out_dir, REPORT_NAME)
                with io.open(report_path, "w", encoding="utf-8",
                             newline="\n") as fh:
                    json.dump(report, fh, ensure_ascii=False, indent=1,
                              sort_keys=True)
                    fh.write("\n")
                print("report -> %s" % re.sub(r"rocqwash_anchor_guard_[0-9a-z_]+", r"rocqwash_anchor_guard_<run>", report_path))
            except OSError as exc:
                raise InfraError("report write failure: %s" % exc)
        _summarize(report)
        return (1 if reds else 0), report
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def _summarize(report):
    print("ANCHOR-GUARD: %s" % report["verdict"])
    print("  module %s md5 %s" % (report["module"], report["module_md5"]))
    for a in report["anchors"]:
        b = a["baseline"]
        print("  anchor %-24s corners=%-24s baseline=%-11s checks=%s"
              % (a["name"], "/".join(a["corners"]), b["verdict"],
                 ",".join("true" if v else ("false" if v is False else "n/a")
                          for v in (c["value"] for c in b["checks"]))))
    for m in report["mutants"]:
        cells = ",".join("%s=%s" % (c["anchor"], c["verdict"])
                         for c in m["per_anchor"])
        print("  mutant %-9s sites=%-3d %-14s verdict=%-11s kills=%s%s"
              % (m["id"], m["sites"], m["classification"],
                 m["verdict"] or "-", "/".join(m["kills"]) or "-",
                 (" cells=%s" % cells) if cells else ""))
    for name in report["debt_register"]:
        print("  debt %s" % name)
    for name in report["vacuous_certificates"]:
        print("  VACUOUS %s" % name)
    for name in report["unanchored_anchors"]:
        print("  UNANCHORED %s" % name)
    for reason in report["red_reasons"]:
        print("  RED  %s" % reason)


def entry_gate(repo_dir, rocq, coqchk):
    """The shared pre-work gate, in the axiom_guard order: --repo missing
    = 9; a binary unconfigured = honest skip 111; a configured binary
    path nonexistent = 9.  Returns (exit_code, stderr_line); (0, None)
    means the run may proceed."""
    if not os.path.isdir(repo_dir):
        return 9, "FAIL-LOUD: --repo directory missing: %s" % repo_dir
    flags = (("--rocq", rocq), ("--coqchk", coqchk))
    missing = [flag for flag, path in flags if not path]
    if missing:
        return 111, ("SKIP: %s not configured (flag or environment); the "
                     "anchor guard honestly skips and judges nothing "
                     "(rc 111)" % " and ".join(missing))
    absent = [flag for flag, path in flags if not os.path.exists(path)]
    if absent:
        return 9, ("FAIL-LOUD: %s configured but binary missing: %s"
                   % (" and ".join(absent),
                      " and ".join(path for _flag, path
                                   in flags if not os.path.exists(path))))
    return 0, None


SELFTEST_MODULE_V = """Require Import QArith_base.

Fixpoint qpow_nat (t : Q) (k : nat) : Q :=
  match k with
  | O => 1%Q
  | S m => Qmult (qpow_nat t m) t
  end.

Fixpoint rcp (k : nat) : Q :=
  match k with
  | O => 1%Q
  | S m => Qmult (1 # 2)%Q (rcp m)
  end.

Definition odd_term (t : Q) (k : nat) : Q :=
  Qmult (qpow_nat t (2 * k + 1)) (rcp (2 * k)).

Fixpoint ss_sum (t : Q) (k : nat) : Q :=
  match k with
  | O => 0%Q
  | S m => Qplus (ss_sum t m) (odd_term t m)
  end.
"""

OB1_ENTRY = {
    "id": "OB1-001",
    "class": "semantic",
    "pattern": "\\1 (2 * \\2 + 1)",
    "replacement": "((?:rsT_)?(?:recipQ|rcp)) \\(2 \\* ([kK])\\)",
    "evidence": "selftest copy of the frozen library star entry",
}


def _selftest_manifest(module_name, anchors, mutants):
    return {
        "schema": MANIFEST_SCHEMA,
        "module": module_name,
        "anchors": anchors,
        "mutants": mutants,
    }


def _selftest_valid_anchors():
    return [
        {"name": "a1", "referent": "the_referent",
         "certificate_face": "cert_face",
         "sample_points": [
             {"label": "smallest", "corner": "smallest",
              "check": "cert_face"},
             {"label": "boundary", "corner": "boundary",
              "check": "Qle_bool false cert_face"}],
         "independent_derivation": "derivation text"},
    ]


def _write_manifest(dir_path, man):
    os.makedirs(dir_path, exist_ok=True)
    man_path = os.path.join(dir_path, "certificates.json")
    with io.open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(man, ensure_ascii=False, indent=1) + "\n")
    return man_path


def _t1_manifest_vectors(tmp):
    """T1: six malformed fixtures, each asserted to raise the exit-2
    error with the offending field named."""
    failures = []

    def expect_reject(label, dir_name, man, needle):
        d = os.path.join(tmp, "t1_" + dir_name)
        os.makedirs(d, exist_ok=True)
        with io.open(os.path.join(d, "mini.v"), "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write("Definition cert_face : bool := true.\n"
                     "Definition the_referent : bool := true.\n")
        man_path = _write_manifest(d, man)
        try:
            load_manifest(man_path, d)
            failures.append("T1 %s: manifest accepted, expected rejection"
                            % label)
        except UsageError as exc:
            if needle not in str(exc):
                failures.append("T1 %s: message names the wrong field "
                                "(want %r, got %r)"
                                % (label, needle, str(exc)))
        return

    bad_schema = _selftest_manifest("mini.v", _selftest_valid_anchors(),
                                    [dict(OB1_ENTRY)])
    bad_schema["schema"] = "rocqwash.anchor/2"
    expect_reject("bad-schema", "bad_schema", bad_schema, "schema")
    dup = _selftest_manifest("mini.v", [
        dict(_selftest_valid_anchors()[0]),
        dict(_selftest_valid_anchors()[0])], [dict(OB1_ENTRY)])
    expect_reject("duplicate-anchor-name", "dup_anchor", dup, "unique")
    missing_corner = _selftest_manifest("mini.v", [
        {"name": "a1", "referent": "the_referent",
         "certificate_face": "cert_face",
         "sample_points": [
             {"label": "smallest", "corner": "smallest",
              "check": "cert_face"},
             {"label": "interior", "corner": "interior",
              "check": "cert_face"}],
         "independent_derivation": "derivation text"}],
        [dict(OB1_ENTRY)])
    expect_reject("corner-missing-boundary", "no_boundary",
                  missing_corner, "boundary")
    build = dict(OB1_ENTRY)
    build["class"] = "build"
    expect_reject("class-build", "class_build",
                  _selftest_manifest("mini.v", _selftest_valid_anchors(),
                                     [build]),
                  "semantic")
    bad_rx = dict(OB1_ENTRY)
    bad_rx["replacement"] = "([unclosed"
    expect_reject("bad-replacement-regex", "bad_rx",
                  _selftest_manifest("mini.v", _selftest_valid_anchors(),
                                     [bad_rx]),
                  "replacement")
    dangling = dict(OB1_ENTRY)
    dangling["pattern"] = "\\2 x"
    dangling["replacement"] = "(cert_face)"
    expect_reject("dangling-group-ref", "dangling_ref",
                  _selftest_manifest("mini.v", _selftest_valid_anchors(),
                                     [dangling]),
                  "group")
    return failures


def _t2_injection_determinism(tmp):
    """T2: the applier run twice is byte-identical, the site count is
    asserted, and the zero-site mutant classifies not-applicable."""
    failures = []
    text = ("Definition rcp (k : nat) : bool := true.\n"
            "Fixpoint g (k : nat) : bool := rcp (2 * k).\n"
            "Definition h (k : nat) : bool := rcp (2 * k).\n")
    once, sites1 = apply_mutant(text, OB1_ENTRY)
    twice, sites2 = apply_mutant(text, OB1_ENTRY)
    if sites1 != 2 or sites2 != 2:
        failures.append("T2: site count want 2/2, got %d/%d"
                        % (sites1, sites2))
    if once != twice:
        failures.append("T2: applier run twice is not byte-identical")
    if "rcp (2 * k + 1)" not in once:
        failures.append("T2: defect form not injected")
    pairs = [(0, False, "not-applicable"), (2, True, "injected"),
             (2, False, "stillborn")]
    for sites, ok, want in pairs:
        got = classify_mutant(sites, ok)
        if got != want:
            failures.append("T2: classify_mutant(%d, %s) want %s got %s"
                            % (sites, ok, want, got))
    return failures


def _t3_star_sweep():
    """T3: one pass flips both star forms (rcp and rsT_recipQ)."""
    failures = []
    text = ("Definition a (k : nat) : bool := rcp (2 * k).\n"
            "Definition b (K : nat) : bool := rsT_recipQ (2 * K).\n")
    mutated, sites = apply_mutant(text, OB1_ENTRY)
    if sites != 2:
        failures.append("T3: site count want 2, got %d" % sites)
    if "rcp (2 * k + 1)" not in mutated:
        failures.append("T3: rcp site did not flip")
    if "rsT_recipQ (2 * K + 1)" not in mutated:
        failures.append("T3: rsT_recipQ site did not flip")
    if "rcp (2 * k)" in mutated or "rsT_recipQ (2 * K)" in mutated:
        failures.append("T3: a pristine form survived the pass")
    return failures


def _t6_report_shape():
    """T6: the JSON assembly path emits every frozen key, sort_keys, and
    the trailing newline."""
    failures = []
    man = _selftest_manifest("m.v", _selftest_valid_anchors(),
                             [dict(OB1_ENTRY)])
    report = new_report(man, "0" * 32, "rocq", "coqchk", 600)
    anchor = _selftest_valid_anchors()[0]
    probe = {"assumptions": "closed", "axiom_names": [],
             "checks": [True, None], "compile_broken": False,
             "error_tail": []}
    report["anchors"].append(anchor_report_entry(
        anchor, baseline_report_entry(anchor, probe)))
    entry = mutant_report_entry(OB1_ENTRY, 2, "injected")
    entry["per_anchor"] = [{"anchor": "a1", "verdict": "killed"}]
    report["mutants"].append(entry)
    blob = json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True)
    blob += "\n"
    if not blob.endswith("\n"):
        failures.append("T6: serialization lacks the trailing newline")
    back = json.loads(blob)
    for key in REPORT_KEYS:
        if key not in back:
            failures.append("T6: report key missing: %s" % key)
    if list(back.keys()) != sorted(back.keys()):
        failures.append("T6: serialized keys are not sorted")
    for key in ANCHOR_KEYS:
        if key not in back["anchors"][0]:
            failures.append("T6: anchor key missing: %s" % key)
    for key in BASELINE_KEYS:
        if key not in back["anchors"][0]["baseline"]:
            failures.append("T6: baseline key missing: %s" % key)
    for c in back["anchors"][0]["baseline"]["checks"]:
        for key in CHECK_KEYS:
            if key not in c:
                failures.append("T6: check key missing: %s" % key)
    for key in MUTANT_KEYS:
        if key not in back["mutants"][0]:
            failures.append("T6: mutant key missing: %s" % key)
    for c in back["mutants"][0]["per_anchor"]:
        for key in CELL_KEYS:
            if key not in c:
                failures.append("T6: cell key missing: %s" % key)
    return failures


def _t4_full_pipeline(tmp):
    """T4: the full pipeline on a synthetic module; baseline hold, the
    star mutant killed by the bracket certificate, the positivity-only
    dummy certificate VACUOUS, run exit 1, and the report byte-identical
    on a double run."""
    failures = []
    fx = os.path.join(tmp, "t4")
    os.makedirs(fx)
    with io.open(os.path.join(fx, "synth_star.v"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write(SELFTEST_MODULE_V)
    anchors = [
        {"name": "bracket_low", "referent": "ss_sum",
         "certificate_face": "ss_sum",
         "sample_points": [
             {"label": "k1_smallest", "corner": "smallest",
              "check": "Qle_bool (1 # 5)%Q (ss_sum (1 # 4)%Q 1)"},
             {"label": "k2_boundary", "corner": "boundary",
              "check": "Qle_bool (1 # 2)%Q (ss_sum (1 # 2)%Q 2)"},
             {"label": "k3_interior", "corner": "interior",
              "check": "Qle_bool (1 # 4)%Q (ss_sum (1 # 3)%Q 3)"}],
         "independent_derivation":
             "Lower bracket from direct Q computation of the three "
             "sample points, independent of the nat recursion in "
             "ss_sum"},
        {"name": "pos_dummy", "referent": "ss_sum",
         "certificate_face": "ss_sum",
         "sample_points": [
             {"label": "k1_smallest", "corner": "smallest",
              "check": "Qle_bool 0%Q (ss_sum (1 # 4)%Q 1)"},
             {"label": "k2_boundary", "corner": "boundary",
              "check": "Qle_bool 0%Q (ss_sum (1 # 2)%Q 2)"},
             {"label": "k3_interior", "corner": "interior",
              "check": "Qle_bool 0%Q (ss_sum (1 # 3)%Q 3)"}],
         "independent_derivation":
             "Positivity from the Q algebra of the addends, independent "
             "of the nat recursion in ss_sum"},
    ]
    man = _selftest_manifest("synth_star.v", anchors, [dict(OB1_ENTRY)])
    man_path = _write_manifest(fx, man)
    rocq = os.environ.get("ROCWASH_ROCQ", "")
    coqchk = os.environ.get("ROCWASH_COQCHK", "")
    out1 = os.path.join(tmp, "t4_out1")
    out2 = os.path.join(tmp, "t4_out2")
    code1, rep1 = guard(fx, man_path, rocq, coqchk, 600, out1, False)
    code2, rep2 = guard(fx, man_path, rocq, coqchk, 600, out2, False)
    if code1 != 1:
        failures.append("T4: run exit want 1 (vacuous red), got %d; "
                        "red_reasons=%r"
                        % (code1, rep1.get("red_reasons")))
    if rep1.get("verdict") != "RED":
        failures.append("T4: verdict want RED, got %r" % rep1.get("verdict"))
    anchors_rep = rep1.get("anchors", [])
    if len(anchors_rep) != 2:
        failures.append("T4: anchor count want 2, got %d"
                        % len(anchors_rep))
        return failures
    if anchors_rep[0]["baseline"]["verdict"] != "hold":
        failures.append("T4: bracket baseline want hold, got %r (checks "
                        "%r, assumptions %r)"
                        % (anchors_rep[0]["baseline"]["verdict"],
                           anchors_rep[0]["baseline"]["checks"],
                           anchors_rep[0]["baseline"]["assumptions"]))
    muts = rep1.get("mutants", [])
    if len(muts) != 1:
        failures.append("T4: mutant count want 1, got %d" % len(muts))
        return failures
    if muts[0]["classification"] != "injected":
        failures.append("T4: mutant want injected, got %r (tail %r)"
                        % (muts[0]["classification"],
                           muts[0]["error_tail"]))
        return failures
    if muts[0]["verdict"] != "killed":
        failures.append("T4: mutant want killed, got %r (cells %r)"
                        % (muts[0]["verdict"], muts[0]["per_anchor"]))
    if "bracket_low" not in muts[0]["kills"]:
        failures.append("T4: bracket certificate did not kill the star "
                        "(kills %r)" % muts[0]["kills"])
    if "pos_dummy" not in rep1.get("vacuous_certificates", []):
        failures.append("T4: positivity dummy not flagged VACUOUS "
                        "(vacuous %r)" % rep1.get("vacuous_certificates"))
    if code2 != 1 or rep2 != rep1:
        failures.append("T4: double run differs (code1 %d code2 %d)"
                        % (code1, code2))
    else:
        with io.open(os.path.join(out1, REPORT_NAME), "rb") as fh:
            b1 = fh.read()
        with io.open(os.path.join(out2, REPORT_NAME), "rb") as fh:
            b2 = fh.read()
        if b1 != b2:
            failures.append("T4: report bytes differ on the double run")
    return failures


def _t5_exit_codes(tmp):
    """T5: the exit-code face: unconfigured toolchain 111, missing --repo
    9, configured-but-absent binary 9, malformed manifest 2."""
    failures = []
    rocq = os.environ.get("ROCWASH_ROCQ", "")
    coqchk = os.environ.get("ROCWASH_COQCHK", "")
    cases = [
        ("missing-repo-9", os.path.join(tmp, "no_such_repo"), rocq,
         coqchk, 9),
        ("unconfigured-rocq-111", tmp, "", coqchk, 111),
        ("unconfigured-coqchk-111", tmp, rocq, "", 111),
        ("absent-binary-9", tmp, rocq, os.path.join(tmp, "absent_bin"),
         9),
    ]
    for label, repo, rq, ck, want in cases:
        code, _msg = entry_gate(repo, rq, ck)
        if code != want:
            failures.append("T5 %s: gate exit want %d got %d"
                            % (label, want, code))
    d = os.path.join(tmp, "t5_bad_manifest")
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, "mini.v"), "w", encoding="utf-8",
                 newline="\n") as fh:
        fh.write("Definition cert_face : bool := true.\n")
    man = _selftest_manifest("mini.v", _selftest_valid_anchors(),
                             [dict(OB1_ENTRY)])
    man["schema"] = "rocqwash.anchor/9"
    man_path = _write_manifest(d, man)
    try:
        load_manifest(man_path, d)
        failures.append("T5 malformed-manifest: accepted, expected the "
                        "exit-2 error")
    except UsageError:
        pass
    return failures


def selftest():
    """Embedded vector suite (two tiers).  Tier a is pure Python and
    always runs; the toolchain tier runs only when both binaries are
    configured through the environment.  Exits: 0 all vectors pass; 2
    any assertion failure; 111 toolchain tier skipped; 9 configured
    binaries missing.  All fixtures live in private temp dirs; zero
    network, zero real-repo touch, zero build step."""
    failures = []
    tmp = tempfile.mkdtemp(prefix="rocqwash_anchor_guard_selftest_")
    try:
        failures += _t1_manifest_vectors(tmp)
        failures += _t2_injection_determinism(tmp)
        failures += _t3_star_sweep()
        failures += _t6_report_shape()
        if failures:
            for msg in failures:
                print("SELFTEST-FAIL: %s" % msg, file=sys.stderr)
            return 2
        rocq = os.environ.get("ROCWASH_ROCQ", "")
        coqchk = os.environ.get("ROCWASH_COQCHK", "")
        if not rocq or not coqchk:
            unconfigured = [name for name, path
                            in (("rocq", rocq), ("coqchk", coqchk))
                            if not path]
            print("SKIP: %s not configured (flag or environment); the "
                  "anchor guard selftest honestly skips the toolchain "
                  "tier (rc 111)" % " and ".join(unconfigured),
                  file=sys.stderr)
            return 111
        if not os.path.exists(rocq) or not os.path.exists(coqchk):
            print("FAIL-LOUD: configured selftest binary missing",
                  file=sys.stderr)
            return 9
        try:
            failures += _t4_full_pipeline(tmp)
            failures += _t5_exit_codes(tmp)
        except InfraError as exc:
            print("FAIL-LOUD: selftest toolchain tier infrastructure "
                  "failure: %s" % exc, file=sys.stderr)
            return 9
        if failures:
            for msg in failures:
                print("SELFTEST-FAIL: %s" % msg, file=sys.stderr)
            return 2
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        if len(argv) != 1:
            print("FAIL: --selftest takes no other flags", file=sys.stderr)
            sys.exit(2)
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        description="Anchor and certificate guard (manifest validation, "
                    "compile tri-classification, coqchk kernel recheck, "
                    "per-anchor probe face, mutation kill matrix).")
    ap.add_argument("--repo", required=True, help="module directory")
    ap.add_argument("--manifest", required=True,
                    help="certificate manifest JSON (rocqwash.anchor/1)")
    ap.add_argument("--out",
                    help="report directory (anchor-guard-report.json "
                         "written here; absent = stdout only)")
    ap.add_argument("--rocq", default=os.environ.get("ROCWASH_ROCQ", ""),
                    help="rocq binary (default ROCWASH_ROCQ)")
    ap.add_argument("--coqchk",
                    default=os.environ.get("ROCWASH_COQCHK", ""),
                    help="coqchk binary (default ROCWASH_COQCHK)")
    ap.add_argument("--timeout", type=int, default=600,
                    help="per-subprocess timeout seconds (default 600)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp workdir (debug face)")
    args = ap.parse_args()

    code, message = entry_gate(args.repo, args.rocq, args.coqchk)
    if code:
        print(message, file=sys.stderr)
        sys.exit(code)
    try:
        code, _report = guard(args.repo, args.manifest, args.rocq,
                              args.coqchk, args.timeout, args.out,
                              args.keep)
    except UsageError as exc:
        print("USAGE: %s" % exc, file=sys.stderr)
        sys.exit(2)
    except InfraError as exc:
        print("FAIL-LOUD: %s" % exc, file=sys.stderr)
        sys.exit(9)
    sys.exit(code)


if __name__ == "__main__":
    main()
