#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_abl1_4b_compile.py v2: R4 4b ocamlc compiler (fixpoint rounds, mli
first, explicit cwd, fail-loud).

Purpose.  Compile the extracted OCaml module tree: module dependency order
  comes from ocamldep (its continuation lines are joined back into single
  records); modules are compiled in fixpoint rounds, a module compiling once
  its dependency set is a subset of the compiled set, each .mli before its
  .ml; the optional driver is linked last and executed.
Interface.  python3 _abl1_4b_compile.py <extract_dir> [driver.ml]
  <extract_dir> holds the .ml faces and any .mli faces; the optional second
  argument names the driver module, linked against all compiled modules and
  executed as ./runalive.exe inside that directory.
Dependencies.  ocamlc/ocamldep must already be on PATH (opam env activated or
  the opam bin exported); detected with shutil.which, detection failure is a
  FATAL exit with no hardcoded machine-path fallback. Python 3 stdlib only.
Evidence.  tests/test_clean_mode.py V16/V17 pin the ROCWASH_CLEAN=1
  report-and-refuse contract (exit 1) and the default-mode contract; a full
  compile prints COMPILED-ALL with the module count (mli-first, deps
  fixpoint).
Exit-codes.  0 = all modules compiled and the driver, when given, returned 0;
  1 = toolchain missing (FATAL toolchain), MLI-FAIL or ML-FAIL compile
  failure, DEP-STUCK dependency deadlock, or LINK-FAIL; when a driver runs,
  its own return code is propagated.
"""
import re, os, shutil, subprocess, sys

OCAMLC = shutil.which("ocamlc")
OCAMLDEP = shutil.which("ocamldep")
# Clean mode (ROCWASH_CLEAN=1) is report-not-execute and holds regardless
# of toolchain presence: on a canonical machine (ocamlc already on PATH)
# clean mode still reports and refuses instead of compiling (the exit-1
# report contract is kept; tests/test_clean_mode.py V16).
if os.environ.get("ROCWASH_CLEAN", "").strip() == "1":
    if OCAMLC is None or OCAMLDEP is None:
        sys.stderr.write("requires canonical environment: the OCaml "
                         "toolchain (ocamlc/ocamldep on PATH via opam env)\n")
        sys.stderr.write(
            "FATAL toolchain: ocamlc/ocamldep not found on PATH "
            f"(which ocamlc={OCAMLC!r}, which ocamldep={OCAMLDEP!r}). "
            "Activate the opam env first (e.g. eval \"$(opam env)\" or "
            "export PATH=<opam-switch-bin>:$PATH); no hardcoded machine-path fallback.\n")
    else:
        sys.stderr.write("requires canonical environment: clean mode is "
                         "report-not-execute; the OCaml toolchain is "
                         f"present (ocamlc={OCAMLC!r}, ocamldep={OCAMLDEP!r}) "
                         "and would compile in default mode\n")
    sys.exit(1)
if OCAMLC is None or OCAMLDEP is None:
    sys.stderr.write(
        "FATAL toolchain: ocamlc/ocamldep not found on PATH "
        f"(which ocamlc={OCAMLC!r}, which ocamldep={OCAMLDEP!r}). "
        "Activate the opam env first (e.g. eval \"$(opam env)\" or "
        "export PATH=<opam-switch-bin>:$PATH); no hardcoded machine-path fallback.\n")
    sys.exit(1)

def main():
    d = os.path.abspath(sys.argv[1])
    driver = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
    mods = sorted(f[:-3] for f in os.listdir(d)
                  if f.endswith(".ml") and f != os.path.basename(driver or ""))
    raw = subprocess.run([OCAMLDEP] + [m + ".ml" for m in mods],
                         capture_output=True, text=True, cwd=d).stdout
    joined, cur = [], ""
    for line in raw.split("\n"):
        if not line.strip():
            continue
        cur += " " + line.rstrip("\\")
        if not line.rstrip().endswith("\\"):
            joined.append(cur); cur = ""
    if cur.strip():
        joined.append(cur)
    deps = {m: set() for m in mods}
    for e in joined:
        m = re.match(r"\s*(\S+)\.cmo\s*:(.*)$", e)
        if not m:
            continue
        tgt = m.group(1)
        if tgt not in deps:
            continue
        ds = set(re.findall(r"(\S+)\.cmi", m.group(2)))
        deps[tgt] |= (ds - {tgt})
    compiled, order = set(), []
    def oc(args):
        return subprocess.run([OCAMLC] + args, capture_output=True, text=True, cwd=d)
    while len(compiled) < len(mods):
        progress = False
        for m in mods:
            if m in compiled or not deps[m] <= compiled:
                continue
            if os.path.exists(os.path.join(d, m + ".mli")):
                r = oc(["-c", m + ".mli"])
                if r.returncode != 0:
                    print(f"MLI-FAIL {m}: {r.stderr}"); sys.exit(1)
            r = oc(["-c", m + ".ml"])
            if r.returncode != 0:
                print(f"ML-FAIL {m}: {r.stderr}"); sys.exit(1)
            compiled.add(m); order.append(m); progress = True
        if not progress:
            rem = [m for m in mods if m not in compiled]
            print(f"DEP-STUCK remaining={rem}"); sys.exit(1)
    print(f"COMPILED-ALL {len(order)} modules (mli-first, deps fixpoint)")
    if driver:
        r = subprocess.run([OCAMLC, "-o", "runalive.exe", "-I", "."] +
                           [m + ".cmo" for m in order] + [driver],
                           capture_output=True, text=True, cwd=d)
        if r.returncode != 0:
            print(f"LINK-FAIL: {r.stderr}"); sys.exit(1)
        r = subprocess.run(["./runalive.exe"], capture_output=True, text=True, cwd=d)
        print(f"RUNALIVE RC={r.returncode}")
        print("RUNALIVE-OUT:", (r.stdout or r.stderr).strip()[:400])
        sys.exit(r.returncode)

if __name__ == "__main__":
    main()
