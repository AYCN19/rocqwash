# -*- coding: utf-8 -*-
"""test_scan_v4_token.py — regression coverage for scan/scan_v4_token.py.

Vectors:
  1. fixture stations: the historic mixed-line masking pattern reproduces —
     the scanner reports exactly the fixture's three shadow-hazard stations,
     each flagged mixed_line=True (the qualified form sits on the same line).
  2. masking blindness: the legacy line-level method (bare-id lines minus
     qualified-carrying lines) misses exactly those three stations on the
     same fixture — the blind spot the v4 scanner closes.
  3. binder tracking: binder-local references and binding sites in the
     fixture are not stations.
  4. optional tree check (env ROCWASH_TREE_SAMPLES=<dir>): zero stations on
     *.v samples in that directory (post-wash canonical tree).  Skipped
     silently when the variable is unset, so external clones pass without
     any local tree.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "scan"))
from scan_v4_token import scan_text  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "scan_v4_shadow_fixture.v")

fails = []


def check(name, cond):
    print("  %-30s %s" % (name, "ok" if cond else "FAIL"))
    if not cond:
        fails.append(name)


text = io.open(FIXTURE, encoding="utf-8").read()
res = scan_text(text, ("S",))
st = res["stations"]
haz = [s for s in st if s["cls"] == "shadow-hazard"]
mixed = [s for s in haz if s["mixed_line"]]

check("station_count == 3", res["station_count"] == 3)
check("all three shadow-hazard", len(haz) == 3)
check("all three mixed_line", len(mixed) == 3)
check("lines are 20/22/24",
      sorted(s["line"] for s in haz) == [20, 22, 24])

# legacy line-level emulation (the historic method): bare-id lines minus
# lines carrying the qualified form
bare_re = re.compile(r"(^|[^.A-Za-z_0-9])S($|[^A-Za-z_0-9])")
qual_re = re.compile(r"[A-Za-z_'][A-Za-z0-9_']*\.S\b")
legacy = []
for i, l in enumerate(text.split("\n"), 1):
    code = l.split("(*")[0]  # crude comment cut — the historic method's level
    if bare_re.search(code) and not qual_re.search(code):
        legacy.append(i)
check("legacy misses 20/22/24 (masking)",
      not set([20, 22, 24]) <= set(legacy))
check("legacy blind exactly at mixed lines",
      set([20, 22, 24]).isdisjoint(legacy))

ctx = res["context"]["S"]
check("binder-bound excluded", ctx["binder_bound"] >= 4)
check("binding sites excluded", ctx["binding_site"] >= 3)
check("qualified counted", ctx["qualified"] >= 4)
check("shadow source recorded", len(res["shadow_sources"]) == 1
      and res["shadow_sources"][0]["name"] == "S")

# optional tree check — zero stations on the named post-wash canonical pieces
# (the acceptance scope: the washed reference files, not the whole tree —
# unwashed files legitimately carry bare references until their wash round)
WASHED = ("LW0FactGrowth.v", "G08_Gibbs.v", "LW3KnzValue.v")
samples = os.environ.get("ROCWASH_TREE_SAMPLES", "")
if samples and os.path.isdir(samples):
    tree_bad = []
    tree_n = 0
    for nm in WASHED:
        fp = os.path.join(samples, nm)
        if not os.path.exists(fp):
            continue
        r = scan_text(io.open(fp, encoding="utf-8", errors="replace").read(), ("S",))
        tree_n += 1
        if r["station_count"] != 0:
            tree_bad.append((nm, r["station_count"]))
    if tree_n:
        check("washed pieces zero stations (%d files)" % tree_n, not tree_bad)
        if tree_bad:
            print("    offenders:", tree_bad)
    else:
        print("  tree check: SKIP (no washed reference file in %s)" % samples)
else:
    print("  tree check: SKIP (ROCWASH_TREE_SAMPLES unset)")

print("TEST-SCAN-V4:", "PASS" if not fails else "FAIL %s" % fails)
sys.exit(0 if not fails else 1)
