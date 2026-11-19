#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""axiom_guard.py — repo-wide axiom guard over every .v file (rocqwash tools/).

    Purpose.  The community-standard trust question for a proof corpus is
      "what does each theorem actually rest on?" (kernel recheck plus a
      Print Assumptions census; the audit report section 3.2 names the
      absence of exactly this as the repo's most serious misalignment).
      This guard answers it mechanically for the whole repository: every .v
      file is compiled and classified, and every file that compiles is
      judged at two levels.  The repo standard is strict: every statement
      must be Closed (zero axioms) and the axiom whitelist is empty by
      default.

    Interface.  python3 tools/axiom_guard.py --repo DIR [--out DIR]
      [--rocq BIN] [--coqchk BIN] [--allow-axiom NAME]... [--timeout SEC]
      [--keep].  Compiler and kernel-checker paths resolve per flag, then
      environment: --rocq / ROCWASH_ROCQ, --coqchk / ROCWASH_COQCHK.
      --out DIR receives the deterministic report volume
      (axiom-guard-report.json); without --out the summary goes to stdout
      only and no file is written.

    Faces.
      1. Inventory: every .v under the repo except .git, sorted by relative
         path (POSIX form in the report).  23 files at the reference HEAD.
      2. Compile classification (three ways): each file is copied
         byte-identical into a private temp workdir and compiled there
         (rocq c -native-compiler no -q -Q <source dir> ""), so the .vo
         output face is temp-only and the repository tree is never written:
           compile-ok         rc 0 -> proceeds to detection;
           compile-broken     rc != 0 (or timeout) -> recorded in the debt
                              register with the error tail (judged no
                              further: assumptions cannot be printed for a
                              file that does not compile);
           skip-no-toolchain  toolchain not configured -> the whole run
                              exits 111 before any work (see exit codes).
         The -Q mapping of the source directory makes sibling .vo worlds
         resolvable when they are built; an unbuilt Require is an honest
         compile-broken entry whose error tail names the missing library.
      3. Light face (pre-screen, per theorem): statement names are extracted
         from the file with a comment/string masking scanner; census copies
         of the file plus one "Print Assumptions <name>." line per statement
         compile under a separate _census filename (the base .vo stays
         intact for the heavy face); each output block maps back to its
         statement in order (batched pass; on any marker-count mismatch the
         file falls back to one compile per statement for exact
         attribution).  Verdicts: closed / axioms / census-error (recorded,
         not judged).
      4. Heavy face (authority): coqchk -o -Q <source dir> "" -Q <workdir>
         "" <module> on the base .vo of the temp copy; the CONTEXT SUMMARY
         "* Axioms:" section is parsed (stdlib index-relaxation entries live
         in other sections and are never judged).  This is the authoritative
         judgment per the graded-detection design; the token-quarantine face
         is intentionally NOT implemented: token-level .vo scanning can
         quarantine suspicious artifacts but cannot decide closedness (the
         gate5 precedent), so it would add verdicts it cannot back.
      5. Verdict: a compile-ok file is red when either face reports an axiom
         outside the whitelist, or the heavy face cannot deliver a summary
         (unjudgeable is not green).  Compile-broken files are debt, not
         red.  Run verdict PASS = zero red files.

    Dependencies.  Python 3 standard library only; rocq and coqchk binaries
      from the environment or flags (never downloaded, never simulated).

    Evidence.  Deterministic: sorted inputs, no wall clock in report or
      logic, same input tree yields the byte-identical report.  The write
      face is exactly: caller-named --out report file + private temp workdir
      (removed unless --keep).  The destructive matrix pins this contract.
      Thermal contract: this tool does not embed a guard; wrap the whole
      invocation in tools/cpu_guard.sh for guarded runs — compile children
      stay inside the guard's process tree (the
      verify/extract_magic_check.py contract form).

    Exit-codes.  0 = PASS (zero red files; compile-broken files recorded as
      debt); 1 = red (axiom found outside the whitelist, or an unjudgeable
      heavy face); 2 = usage error; 9 = fail-loud environment (a configured
      binary path does not exist, or --repo is missing); 111 = honest skip
      (rocq or coqchk not configured via flag or environment — reported,
      not simulated, following the verify/ rc 111 skip convention).

    Usage:
      python3 tools/axiom_guard.py --repo . --out /tmp/evid/t0-2
      ROCWASH_ROCQ=/path/rocq ROCWASH_COQCHK=/path/coqchk python3 tools/axiom_guard.py --repo .
"""
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

PROG = "axiom_guard"
SCHEMA = "rocqwash-axiom-guard/1"

# Statement families the light face censuses (name-bearing vernaculars).
STMT_RE = re.compile(
    r"(?m)^[ \t]*(?:#\[[^\]]*\][ \t]*\r?\n?[ \t]*|"
    r"(?:Local|Global|Export|Declare)[ \t]+)*"
    r"(Theorem|Lemma|Corollary|Proposition|Remark|Fact|Example|Instance)"
    r"[ \t]+([A-Za-z_'][A-Za-z0-9_']*)")
# coqchk CONTEXT SUMMARY section heads (line-start anchored).
SUMMARY_RE = re.compile(r"^\* Axioms:(.*)$", re.M)
SUMMARY_NEXT_RE = re.compile(r"^\* ", re.M)
CLOSED_LINE = "Closed under the global context"
ERROR_TAIL_LINES = 12


def md5_of_bytes(raw):
    return hashlib.md5(raw).hexdigest()


def mask_comments_strings(text):
    """Blank out comment and string literal bodies so name extraction only
    sees code positions (same discipline as the wash-side masking state
    machines: nested (* *) counted, backslash escapes honored)."""
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
    """[(name, line_no)] of the theorem-family statements, comments and
    strings masked out first (comment decoys never enter the census)."""
    masked = mask_comments_strings(text)
    out = []
    for m in STMT_RE.finditer(masked):
        line = masked.count("\n", 0, m.start(2)) + 1
        out.append((m.group(2), line))
    return out


def run_cmd(argv, timeout):
    """Subprocess run with merged stdout/stderr and a hard timeout; the
    caller decides every verdict from (rc, output, error) — no silent
    fallback.  error is None on a clean launch, "timeout" on a timeout,
    and an OS-level message string when the binary cannot be launched."""
    try:
        p = subprocess.run(argv, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace"), None
    except subprocess.TimeoutExpired as e:
        partial = b""
        if e.stdout:
            partial += e.stdout
        if e.stderr:
            partial += e.stderr
        return None, partial.decode("utf-8", "replace"), "timeout"
    except OSError as e:
        return None, "", str(e)


def error_tail(output, lines=ERROR_TAIL_LINES):
    tail = [ln for ln in output.splitlines() if ln.strip()]
    return tail[-lines:]


def strip_tmp(output, work):
    """Normalize the run's private temp directory out of compiler output so
    error tails (which embed the .v copy path) stay byte-stable across
    runs — determinism of the report volume (same input tree, same bytes)."""
    return output.replace(work, "<axguard-tmp>")


def compile_one(rocq, src_v, timeout, log_dir=None, name=None):
    """Compile one temp-side .v; returns (rc, output, error).  The .vo lands
    next to the copy (temp workdir), never in the repository."""
    argv = [rocq, "c", "-native-compiler", "no", "-q",
            "-Q", os.path.dirname(src_v) or ".", "", src_v]
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


def parse_census_blocks(output, statements):
    """Attribute ordered Print Assumptions blocks to statements.
    Returns a list of verdict dicts in statement order, or None when the
    marker count does not match (caller falls back to per-statement runs)."""
    markers = []  # (pos, kind)
    for m in re.finditer(re.escape(CLOSED_LINE), output):
        markers.append((m.start(), "closed"))
    for m in re.finditer(r"^Axioms:$", output, re.M):
        markers.append((m.start(), "axioms"))
    markers.sort()
    if len(markers) != len(statements):
        return None
    verdicts = []
    for k, (pos, kind) in enumerate(markers):
        end = markers[k + 1][0] if k + 1 < len(markers) else len(output)
        axioms = []
        if kind == "axioms":
            body = output[pos:end]
            for ln in body.splitlines()[1:]:
                ln = ln.strip()
                if ln and not ln.startswith(CLOSED_LINE):
                    axioms.append(ln)
        verdicts.append({"statement": statements[k][0],
                         "line": statements[k][1],
                         "verdict": kind,
                         "axioms": axioms})
    return verdicts


def census_write(census_v, base_text, statement=None):
    """Write one census copy (a separate _census filename, so the base .vo
    of the file under judgment stays intact for the heavy face)."""
    appended = (""
                if statement is None
                else "\nPrint Assumptions %s.\n" % statement)
    with io.open(census_v, "w", encoding="utf-8", newline="") as fh:
        fh.write(base_text + appended)


def light_face(rocq, base_text, work_dir, stem, statements, timeout,
               log_dir, tag):
    """Per-theorem Print Assumptions census: one batched compile first
    (ordered attribution), per-statement compiles as the exact fallback
    (a section-local name fails only its own statement, not the file)."""
    census_v = os.path.join(work_dir, stem + "_census.v")
    census_write(census_v, base_text)
    rc, out, err = compile_one(rocq, census_v, timeout, log_dir, tag)
    verdicts = None
    if rc == 0:
        verdicts = parse_census_blocks(out, statements)
    if verdicts is not None:
        return verdicts
    # fallback: one compile per statement (exact attribution, partial-tolerant)
    verdicts = []
    for nm, ln in statements:
        census_write(census_v, base_text, nm)
        rc2, out2, err2 = compile_one(rocq, census_v, timeout)
        if err2 is not None:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error",
                             "axioms": [err2]})
        elif rc2 != 0:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error",
                             "axioms": error_tail(strip_tmp(out2, work_dir),
                                                  4)})
        elif re.search(r"^Axioms:$", out2, re.M):
            block = out2[out2.index("Axioms:"):]
            axioms = [ln2.strip() for ln2 in block.splitlines()[1:]
                      if ln2.strip()]
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "axioms", "axioms": axioms})
        elif CLOSED_LINE in out2:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "closed", "axioms": []})
        else:
            verdicts.append({"statement": nm, "line": ln,
                             "verdict": "census-error", "axioms": []})
    with io.open(os.path.join(log_dir, tag + ".census.log"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    return verdicts


def guard(repo, rocq, coqchk, allow_axioms, timeout, out_dir, keep):
    """Full run; returns (exit_code, report_dict).  Write faces: the private
    temp workdir and (when given) the caller-named --out report file."""
    v_files = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in (".git",)]
        for fn in filenames:
            if fn.endswith(".v"):
                rel = os.path.relpath(os.path.join(dirpath, fn),
                                      repo).replace(os.sep, "/")
                v_files.append((rel, os.path.join(dirpath, fn)))
    v_files.sort()

    work = tempfile.mkdtemp(prefix="rocqwash_axiom_guard_")
    log_dir = os.path.join(work, "logs")
    os.makedirs(log_dir)
    report = {
        "schema": SCHEMA,
        "repo": os.path.abspath(repo),
        "rocq": rocq,
        "coqchk": coqchk,
        "allow_axioms": sorted(allow_axioms),
        "files_scanned": len(v_files),
        "standard": "Closed zero axioms (default whitelist empty)",
        "files": [],
        "debt_register": [],
        "red_files": [],
        "verdict": "PASS",
    }
    reds = []
    try:
        for idx, (rel, abs_path) in enumerate(v_files):
            tag = "%03d_%s" % (idx, os.path.basename(abs_path)[:-2])
            fdir = os.path.dirname(abs_path)
            wdir = os.path.join(work, "f%03d" % idx)
            os.makedirs(wdir)
            stem = os.path.basename(abs_path)[:-2]
            work_v = os.path.join(wdir, stem + ".v")
            with io.open(abs_path, "rb") as fh:
                raw = fh.read()
            with io.open(work_v, "wb") as fh:
                fh.write(raw)
            entry = {"file": rel, "md5": md5_of_bytes(raw)}
            rc, out, err = compile_one(rocq, work_v, timeout, log_dir, tag)
            if err is not None:
                entry["classification"] = "compile-broken"
                entry["compile_rc"] = -1
                entry["compile_error"] = err
                report["debt_register"].append(rel)
                report["files"].append(entry)
                continue
            if rc != 0:
                entry["classification"] = "compile-broken"
                entry["compile_rc"] = rc
                entry["error_tail"] = error_tail(strip_tmp(out, work))
                report["debt_register"].append(rel)
                report["files"].append(entry)
                continue
            entry["classification"] = "compile-ok"
            entry["compile_rc"] = 0
            base_text = raw.decode("utf-8", "replace")
            stmts = statement_names(base_text)
            entry["statements"] = len(stmts)
            entry["light_census"] = light_face(
                rocq, base_text, wdir, stem, stmts, timeout, log_dir, tag) \
                if stmts else []
            # heavy face on the base .vo (the census copies never overwrite it)
            chk_rc, chk_out, chk_err = run_cmd(
                [coqchk, "-o", "-Q", fdir, "", "-Q", wdir, "", stem],
                timeout)
            with io.open(os.path.join(log_dir, tag + ".coqchk.log"), "w",
                         encoding="utf-8", newline="\n") as fh:
                fh.write(chk_out)
            if chk_err is not None or chk_rc is None or chk_rc != 0:
                entry["heavy"] = {"verdict": "coqchk-error",
                                  "detail": chk_err or "rc %s" % chk_rc,
                                  "tail": error_tail(strip_tmp(chk_out, work),
                                                     4)}
                if rel not in reds:
                    reds.append(rel)
            else:
                status, axioms = parse_axioms_summary(chk_out)
                axioms = [a for a in axioms if a not in allow_axioms]
                entry["heavy"] = {"verdict": status,
                                  "axioms": axioms,
                                  "coqchk_rc": chk_rc}
                if status == "no-summary" or axioms:
                    if rel not in reds:
                        reds.append(rel)
            # light-face judgment (pre-screen; the heavy face stays
            # authoritative — a light red alone still fails the file)
            for v in entry.get("light_census", []):
                v["axioms"] = [a for a in v.get("axioms", [])
                               if a not in allow_axioms]
                if v["verdict"] == "axioms" and v["axioms"] \
                        and rel not in reds:
                    reds.append(rel)
            report["files"].append(entry)
        report["red_files"] = reds
        report["verdict"] = "RED" if reds else "PASS"
        if out_dir:
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            report_path = os.path.join(out_dir, "axiom-guard-report.json")
            with io.open(report_path, "w", encoding="utf-8",
                         newline="\n") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=1,
                          sort_keys=True)
                fh.write("\n")
            print("report -> %s" % report_path)
        _summarize(report)
        return (1 if reds else 0), report
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def _summarize(report):
    ok = [f for f in report["files"] if f["classification"] == "compile-ok"]
    broken = [f for f in report["files"]
              if f["classification"] == "compile-broken"]
    print("AXIOM-GUARD: %s" % report["verdict"])
    print("  files scanned: %d (compile-ok %d / compile-broken %d)"
          % (report["files_scanned"], len(ok), len(broken)))
    for f in ok:
        lc = f.get("light_census", [])
        closed = sum(1 for v in lc if v["verdict"] == "closed")
        hv = f.get("heavy", {}).get("verdict")
        print("  ok   %s statements=%d closed=%d heavy=%s"
              % (f["file"], len(lc), closed, hv))
    for f in broken:
        print("  debt %s (rc %s)" % (f["file"], f.get("compile_rc")))
    for rel in report.get("red_files", []):
        print("  RED  %s" % rel)


def main():
    ap = argparse.ArgumentParser(
        description="Repo-wide axiom guard (compile tri-classification, "
                    "per-theorem assumption census, coqchk kernel recheck).")
    ap.add_argument("--repo", required=True, help="repository root")
    ap.add_argument("--out", help="report directory (report JSON written "
                                  "here; absent = stdout only)")
    ap.add_argument("--rocq", default=os.environ.get("ROCWASH_ROCQ", ""),
                    help="rocq binary (default ROCWASH_ROCQ)")
    ap.add_argument("--coqchk", default=os.environ.get("ROCWASH_COQCHK", ""),
                    help="coqchk binary (default ROCWASH_COQCHK)")
    ap.add_argument("--allow-axiom", action="append", default=[],
                    dest="allow_axioms", help="whitelisted axiom name "
                    "(repeatable; default whitelist is empty)")
    ap.add_argument("--timeout", type=int, default=600,
                    help="per-subprocess timeout seconds (default 600)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp workdir (debug face)")
    args = ap.parse_args()

    if not os.path.isdir(args.repo):
        print("FAIL-LOUD: --repo directory missing: %s" % args.repo,
              file=sys.stderr)
        sys.exit(9)
    missing = [flag for flag, path in (("--rocq", args.rocq),
                                       ("--coqchk", args.coqchk))
               if not path]
    if missing:
        print("SKIP: %s not configured (flag or environment); the axiom "
              "guard honestly skips and judges nothing (rc 111)"
              % " and ".join(missing), file=sys.stderr)
        sys.exit(111)
    absent = [flag for flag, path in (("--rocq", args.rocq),
                                      ("--coqchk", args.coqchk))
              if not os.path.exists(path)]
    if absent:
        print("FAIL-LOUD: %s configured but binary missing: %s"
              % (" and ".join(absent),
                 " and ".join(p for p in (args.rocq, args.coqchk)
                              if not os.path.exists(p))),
              file=sys.stderr)
        sys.exit(9)

    code, _report = guard(args.repo, args.rocq, args.coqchk,
                          args.allow_axioms, args.timeout, args.out,
                          args.keep)
    sys.exit(code)


if __name__ == "__main__":
    main()
