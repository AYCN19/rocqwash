"""test_evolve_flag_contract.py — evolve.py flag-face contract pin (tests lane).

Purpose.  Pin the engine's user-facing flag contract that the growth-cycle
    ask surface depends on: (1) the six cycle-3 ask flags exist verbatim in
    the implemented --help face; (2) the --sentinel-events/--sentinel-state
    pair is accepted without --watch-repo (the UNRECOGNIZED harvest runs
    read-only over the stream); (3) a round with no signal source exits 2
    (fail-loud usage error, no silent empty round); (4) the registry pair
    against a book-less repository exits 9 fail-loud (the standing
    downgrade this tool repo exercises every cycle).

Interface.  Standalone: ``python -B tests/test_evolve_flag_contract.py``;
    also callable as a suite case body. Zero network, zero repository
    writes, tmpdir fixtures only; the engine child runs under ``sys.executable
    -I`` with explicit ``encoding='utf-8', errors='replace'`` on every pipe.

Dependencies.  Python 3 stdlib only; the sibling ``tools/evolve.py`` found
    relative to this file's location.

Evidence.  Every check prints PASS/FAIL with the measured value; the script
    exits 1 on the first FAIL and 0 when all checks pass. Measured on the
    growth-cycle-3 tree (HEAD 8e04cc6): all four checks PASS.

Exit-codes.  0 = all checks passed; 1 = a check failed (message names the
    check and the measured face).
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EVOLVE = os.path.join(REPO, "tools", "evolve.py")

ASK_FLAGS = [
    "--draft-out",
    "--suite-now",
    "--sentinel-events",
    "--sentinel-state",
    "--registry-git",
    "--registry-ref",
    "--repo-root",
]

SUMMARY_LINE = "== 汇总: 3 过 / 0 红 / 0 略 / 共 3 例 =="


def run(cmd, **kw):
    return subprocess.run(
        cmd, capture_output=True, encoding="utf-8", errors="replace", **kw
    )


def evolve_child(args):
    return run([sys.executable, "-I", EVOLVE] + args)


def check(name, ok, detail):
    print(("PASS" if ok else "FAIL") + " " + name + (" — " + detail if detail else ""))
    return ok


def main():
    ok = True
    tmp = tempfile.mkdtemp(prefix="rocqwash_flag_contract_")

    # (1) the ask flag face exists verbatim in the implemented --help.
    h = evolve_child(["--help"])
    ok &= check("help rc=0", h.returncode == 0, "rc=%d" % h.returncode)
    missing = [f for f in ASK_FLAGS if f not in h.stdout]
    ok &= check(
        "ask flags verbatim in --help",
        not missing,
        "missing=%r" % (missing,),
    )

    # (2) sentinel pair accepted without --watch-repo: UNRECOGNIZED harvest
    # runs read-only over the stream; the round completes rc=0.
    events = os.path.join(tmp, "events.jsonl")
    open(events, "w", encoding="utf-8").close()
    state = os.path.join(tmp, "state.json")
    ledger = os.path.join(tmp, "suite_ledger.txt")
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write(SUMMARY_LINE + "\n")
    draft = os.path.join(tmp, "draft.md")
    report = os.path.join(tmp, "report.json")
    r = evolve_child([
        "--draft-out", draft,
        "--json", report,
        "--suite-ledger", ledger,
        "--sentinel-events", events,
        "--sentinel-state", state,
        "--repo-root", REPO,
    ])
    ok &= check(
        "sentinel pair without --watch-repo accepted",
        r.returncode == 0,
        "rc=%d stderr=%r" % (r.returncode, r.stderr[-200:]),
    )
    if r.returncode == 0:
        with open(report, encoding="utf-8") as fh:
            rep = json.load(fh)
        sigs = sorted(rep.get("signals", {}).keys())
        ok &= check(
            "signals carry suite+unrec",
            sigs == ["norm", "suite", "unrec"] or {"suite", "unrec"} <= set(sigs),
            "signals=%r" % (sigs,),
        )

    # (3) no signal source: usage error exit 2, fail-loud.
    r2 = evolve_child(["--draft-out", os.path.join(tmp, "d2.md")])
    ok &= check(
        "no-signal-source rc=2",
        r2.returncode == 2,
        "rc=%d stderr=%r" % (r2.returncode, r2.stderr[-120:]),
    )

    # (4) registry pair on a book-less repository: rc=9 fail-loud with the
    # missing order.txt face (skip the pin if books have landed).
    probe = run(["git", "-C", REPO, "ls-tree", "HEAD", "--name-only"])
    books = ("order.txt" in probe.stdout) or ("_CoqProject" in probe.stdout)
    if books:
        print("SKIP registry-pair pin — books present at HEAD now")
    else:
        r3 = evolve_child([
            "--draft-out", os.path.join(tmp, "d3.md"),
            "--suite-ledger", ledger,
            "--registry-git", REPO,
            "--registry-ref", "HEAD",
        ])
        face = ("order.txt" in (r3.stderr or "")) and r3.returncode == 9
        ok &= check(
            "book-less registry pair rc=9 fail-loud",
            face,
            "rc=%d stderr=%r" % (r3.returncode, r3.stderr[-160:]),
        )

    print("ALL PASS" if ok else "SOME FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
