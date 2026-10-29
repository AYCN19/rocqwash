#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_abl1_4b_compile.py v2 — R4 4b ocamlc 编译器（不动点轮·mli 先行·cwd 显式·fail-loud）

用法: python3 _abl1_4b_compile.py <extract_dir> [driver.ml]
依赖 ocamldep 续行拼接解析；逐轮编译 deps⊆done 的模；driver 链接+实跑。
"""
import re, os, subprocess, sys

OCAMLC = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live901/bin/ocamlc"
OCAMLDEP = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live901/bin/ocamldep"

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
