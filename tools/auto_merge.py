#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto_merge.py: X5 auto-merge gate judge and safety rail (rocqwash tools/).

    Purpose.  Judges one pull request against the six-verdict mergeability
      enum (merge-ok / hold-red / hold-conflict / already-landed /
      superseded-landed-elsewhere / escalate-unknown) from caller-gathered
      facts, then runs the safety rail: only merge-ok with a supply/* head
      branch is auto-execution eligible, under a daily budget cap (default
      3) against the append-only merge ledger; post-merge red prescribes
      revert (content) / rerun window (transient) / escalation (unknown).
    Interface.  python3 tools/auto_merge.py --facts F.json [--head-branch
      BR] [--allow-prefix P] [--daily-cap N] [--ledger P] [--merge-sha SHA]
      [--post-merge FAM] [--apply] [--json OUT] | --selftest; schemas
      rocqwash-automerge-facts/1 (facts) and rocqwash-automerge/1 (report,
      ledger); zero network: CI verdict, mergeability and containment
      signals are caller-gathered (git rev-list base...head plus a
      tree-level containment check).
    Dependencies.  Python 3 standard library only; zero third-party
      imports; no subprocess; no writes outside the --apply ledger append.
    Evidence.  --selftest frozen vectors: calibration samples S-1..S-5
      pinned to their verdicts, the unrecognized-family escalation, the
      ordering pins (merged anchor over red, containment over conflict),
      whitelist both ways, budget cap, dry-run zero-write, duplicate
      refusals, the revert arc four families, byte-identical reruns, CLI
      codes.
    Exit-codes.  0 completed (verdicts are data); 1 refused (rail refusal
      or duplicate); 2 usage; 9 missing or malformed input; --selftest
      0 all vectors pass / 2 assertion failure.
"""

import argparse
import json
import os
import sys
import tempfile
import time

PROG = "auto-merge"
SCHEMA = "rocqwash-automerge/1"
FACTS_SCHEMA = "rocqwash-automerge-facts/1"
MARK = "AUTO-MERGE-SELFTEST PASS"

VERDICTS = (
    "merge-ok",
    "hold-red",
    "hold-conflict",
    "already-landed",
    "superseded-landed-elsewhere",
    "escalate-unknown",
)

DEFAULT_ALLOW_PREFIX = "supply/"
DEFAULT_DAILY_CAP = 3
DEFAULT_LEDGER = "docs/auto-merge-ledger.jsonl"

REQUIRED_FACT_KEYS = ("pr", "merged", "ci", "compare")
REQUIRED_COMPARE_KEYS = ("ahead", "behind", "head_in_base", "content_landed_in_base")
CI_FAMILIES = ("green", "transient", "content", "unrecognized", "none")
POST_MERGE_FAMILIES = ("green", "transient", "content", "unrecognized")


# ---------------------------------------------------------------- facts I/O

def load_facts(path):
    """Read and shape-check one facts file; structural faults are rc 9."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except OSError:
        sys.stderr.write("FAIL-LOUD: facts file unreadable: %s\n" % path)
        raise SystemExit(9)
    except ValueError as exc:
        sys.stderr.write("FAIL-LOUD: facts file is not valid JSON: %s (%s)\n"
                         % (path, exc))
        raise SystemExit(9)
    if not isinstance(raw, dict):
        sys.stderr.write("FAIL-LOUD: facts root must be a JSON object: %s\n" % path)
        raise SystemExit(9)
    for key in REQUIRED_FACT_KEYS:
        if key not in raw:
            sys.stderr.write("FAIL-LOUD: facts missing required key: %s\n" % key)
            raise SystemExit(9)
    ci = raw["ci"]
    compare = raw["compare"]
    if not isinstance(ci, dict) or "family" not in ci:
        sys.stderr.write("FAIL-LOUD: facts ci must be an object with family\n")
        raise SystemExit(9)
    if ci["family"] not in CI_FAMILIES:
        sys.stderr.write("FAIL-LOUD: ci.family must be one of %s, got: %r\n"
                         % (", ".join(CI_FAMILIES), ci["family"]))
        raise SystemExit(9)
    if not isinstance(compare, dict):
        sys.stderr.write("FAIL-LOUD: facts compare must be an object\n")
        raise SystemExit(9)
    for key in REQUIRED_COMPARE_KEYS:
        if key not in compare:
            sys.stderr.write("FAIL-LOUD: facts compare missing key: %s\n" % key)
            raise SystemExit(9)
    if not isinstance(raw["merged"], bool):
        sys.stderr.write("FAIL-LOUD: facts merged must be a boolean\n")
        raise SystemExit(9)
    return raw


# -------------------------------------------------------------------- judge

def judge(facts):
    """Six-verdict decision over observed facts; ordered screens.

    Order rationale (the X5 gate calibration sample sheet, batch 3):
    the ancestor and cross-absorption screens outrank the red hold because a
    PR whose content already sits in base must be closed, not merged,
    whatever its CI color says (S-2: gate4 red for rounds plus content
    landed elsewhere still judges superseded, never hold-red); the merged
    anchor outranks the absorption screens because a merged head is by then
    an ancestor of base and must stay the merge-ok positive anchor (S-3).
    """
    reasons = []
    family = facts["ci"]["family"]
    compare = facts["compare"]
    ahead = int(compare["ahead"])
    if family == "unrecognized":
        reasons.append("head CI red resists every known failure family "
                       "(UNRECOGNIZED); unknown families escalate to the "
                       "human desktop, never force-fit")
        return "escalate-unknown", reasons
    if facts["merged"] is True:
        reasons.append("landed through its own merge (positive anchor of "
                       "the standard path); a post-merge red is the revert "
                       "arc's input, not this gate's hold")
        return "merge-ok", reasons
    if ahead == 0 or bool(compare["head_in_base"]):
        reasons.append("head commits are reachable from base (ahead=%d, "
                       "head_in_base=%s): content reachability is not the "
                       "PR merge boolean; recommend closing the PR" %
                       (ahead, compare["head_in_base"]))
        return "already-landed", reasons
    if bool(compare["content_landed_in_base"]):
        reasons.append("head still has %d ahead commit(s) but its content "
                       "is already achieved in base by other commits "
                       "(cross direct-push detection); the freshness guard "
                       "fails when base advanced past the repair target "
                       "(behind=%s)" % (ahead, compare["behind"]))
        return "superseded-landed-elsewhere", reasons
    if family in ("transient", "content"):
        reasons.append("head CI red with recognized family '%s': hold, "
                       "never fake green; transient reruns in a stable "
                       "window, content goes to fix-content" % family)
        return "hold-red", reasons
    mergeable = facts.get("mergeable")
    state = facts.get("mergeable_state", "none")
    if mergeable is None or state == "unknown":
        reasons.append("mergeability cannot be told (mergeable=%r, "
                       "mergeable_state=%r); insufficient evidence is an "
                       "escalation, never an automatic merge" %
                       (mergeable, state))
        return "escalate-unknown", reasons
    if mergeable is False or state in ("dirty", "blocked"):
        reasons.append("not mergeable now (mergeable=%s, state=%s): merge "
                       "mechanics hold, rebase or review first" %
                       (mergeable, state))
        return "hold-conflict", reasons
    reasons.append("green head, mergeable, no containment screen fired: the "
                   "standard mergeable path")
    return "merge-ok", reasons


# --------------------------------------------------------------- merge ledger

def utc_today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def utc_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_ledger(path):
    """Read the append-only JSONL ledger; a corrupt line is fail-loud rc 9."""
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                sys.stderr.write("FAIL-LOUD: corrupt ledger line %d in %s "
                                 "(%s)\n" % (lineno, path, exc))
                raise SystemExit(9)
    return rows


def allowed_merges_today(rows, today):
    return [r for r in rows
            if r.get("kind") == "authorize"
            and r.get("decision") == "allowed"
            and r.get("date") == today]


def append_row(path, row):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


# ------------------------------------------------------------ safety rail

def run_rail(facts, verdict, branch, allow_prefix, daily_cap, ledger_path,
             apply_mode):
    """Authorization decision for a merge-ok verdict; hold faces never
    authorize.  Returns (outcome, would_row, wrote_row)."""
    base = {"schema": SCHEMA, "kind": "authorize",
            "pr": facts.get("pr"), "repo": facts.get("repo", ""),
            "head_branch": branch, "verdict": verdict,
            "merge_sha": facts.get("merge_sha")}
    if verdict != "merge-ok":
        return "not-eligible:%s" % verdict, None, False
    if not branch:
        # no authorization was sought: loud data, not a refusal
        return "not-authorizable:missing-branch", None, False
    if not (branch == allow_prefix.rstrip("/")
            or branch.startswith(allow_prefix)):
        return "refused:branch-whitelist(head=%s not under %s)" % (
            branch, allow_prefix), None, False
    rows = read_ledger(ledger_path)
    today = utc_today()
    if len(allowed_merges_today(rows, today)) >= daily_cap:
        return "refused:daily-budget(cap=%d reached on %s)" % (
            daily_cap, today), None, False
    dup = [r for r in rows
           if r.get("kind") == "authorize" and r.get("decision") == "allowed"
           and r.get("date") == today and r.get("pr") == facts.get("pr")]
    if dup:
        return "refused:duplicate-authorization(pr=%s already allowed on %s)" % (
            facts.get("pr"), today), None, False
    row = dict(base)
    row["decision"] = "allowed"
    row["date"] = today
    row["ts"] = utc_ts()
    if apply_mode:
        append_row(ledger_path, row)
        return "allowed", row, True
    return "allowed", row, False


# ------------------------------------------------------- post-merge revert arc

def run_post_merge(family, ledger_path, merge_sha, apply_mode):
    """Post-merge red arc: content prescribes the revert, transient a
    rerun window, unrecognized an escalation, green no action."""
    rows = read_ledger(ledger_path)
    landed = [r for r in rows
              if r.get("kind") == "authorize" and r.get("decision") == "allowed"]
    if not landed:
        sys.stderr.write("FAIL-LOUD: post-merge arc needs one recorded "
                         "merge in the ledger (--ledger), found none\n")
        raise SystemExit(9)
    target = landed[-1]
    if family == "green":
        return "no-action", None, False, target
    if family == "transient":
        return "rerun-window", None, False, target
    if family == "unrecognized":
        return "escalate", None, False, target
    # content family: only a revert prescription needs the merge sha
    sha = merge_sha or target.get("merge_sha")
    if not sha:
        sys.stderr.write("FAIL-LOUD: the target merge row carries no "
                         "merge_sha and --merge-sha does not override it; "
                         "a revert prescription without the sha is refused\n")
        raise SystemExit(9)
    pr = target.get("pr")
    prescription = "git revert -m 1 %s" % sha
    dup = [r for r in rows
           if r.get("kind") == "revert-prescription"
           and r.get("merge_sha") == sha]
    if dup:
        return ("refused:duplicate-prescription(merge_sha=%s already "
                "prescribed)" % sha), None, False, target
    row = {"schema": SCHEMA, "kind": "revert-prescription", "pr": pr,
           "merge_sha": sha, "post_merge_family": family,
           "prescription": prescription, "date": utc_today(), "ts": utc_ts()}
    if apply_mode:
        append_row(ledger_path, row)
        return "revert-prescribed", row, True, target
    return "revert-prescribed", row, False, target


# ------------------------------------------------------------------ report

def emit(facts, verdict, reasons, rail_outcome, rail_row, wrote, out_path):
    report = {
        "schema": SCHEMA,
        "pr": facts.get("pr"),
        "repo": facts.get("repo", ""),
        "verdict": verdict,
        "reasons": reasons,
        "rail": {"outcome": rail_outcome,
                 "ledger_row_written": wrote},
    }
    payload = json.dumps(report, sort_keys=True, ensure_ascii=True)
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
    return payload


# ---------------------------------------------------------------- selftest

def _fact(pr, repo, merged, family, ahead, behind, head_in_base,
          content_landed, mergeable, state, branch=None, note=""):
    return {
        "schema": FACTS_SCHEMA, "pr": pr, "repo": repo, "merged": merged,
        "mergeable": mergeable, "mergeable_state": state,
        "ci": {"family": family},
        "compare": {"ahead": ahead, "behind": behind,
                    "head_in_base": head_in_base,
                    "content_landed_in_base": content_landed},
        "head_branch": branch, "note": note,
    }


# The five calibration samples, transcribed from the calibration document
# (the cross-line calibration sample sheet of this batch's techdocs); each
# pins its verdict.
CALIBRATION = (
    ("S-1", _fact(14, "ConstructiveWorld-Main", False, "green", 0, 4,
                  True, True, None, "none", note="content landed by direct "
                  "push 1c526b2; PR closed unmerged"), "already-landed"),
    ("S-2", _fact(15, "ConstructiveWorld-Main", False, "content", 3, 6,
                  False, True, False, "dirty", note="three head pushes, "
                  "gate4 red rounds, closed unmerged, content landed via "
                  "the SL25 piece"), "superseded-landed-elsewhere"),
    ("S-3", _fact(3, "rocqwash", True, "green", 0, 0, True, True, None,
                  "none", note="eight-seat pack, merged=True (1befa27), "
                  "CI green"), "merge-ok"),
    ("S-4", _fact(16, "ConstructiveWorld-Main", False, "none", 2, 9,
                  False, True, False, "dirty", note="sandbox SL supply "
                  "tests branch, closed unmerged, content landed via "
                  "75404d9/8e70342; base advanced; CI color not recorded"),
     "superseded-landed-elsewhere"),
    ("S-5", _fact(None, "any", False, "content", 1, 0, False, False, True,
                  "unstable", note="constructed: head CI red with a "
                  "recognized family plus mergeable=true"), "hold-red"),
)


def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        if cond:
            print("  ok  %-42s %s" % (name, detail))
        else:
            ok = False
            print("  RED %-42s %s" % (name, detail))

    # V1: the five calibration samples judge to their pinned verdicts.
    for name, facts, want in CALIBRATION:
        verdict, _ = judge(facts)
        check("calibration-%s" % name, verdict == want,
              "want=%s got=%s" % (want, verdict))

    # V2: unrecognized family escalates even when mergeable (the S-5
    # teaching line: UNRECOGNIZED failure family escalates to the desktop).
    f = _fact(77, "any", False, "unrecognized", 1, 0, False, False, True,
              "unstable")
    verdict, reasons = judge(f)
    check("unrecognized-escalates", verdict == "escalate-unknown"
          and "UNRECOGNIZED" in reasons[0], verdict)

    # V3: the merged anchor outranks a red family (post-merge red belongs
    # to the revert arc, not the gate hold).
    f = _fact(3, "rocqwash", True, "content", 0, 0, True, True, None, "none")
    verdict, _ = judge(f)
    check("merged-anchor-beats-red", verdict == "merge-ok", verdict)

    # V4: containment screens outrank conflict mechanics (S-1 form with a
    # dirty state still judges already-landed).
    f = _fact(14, "ConstructiveWorld-Main", False, "green", 0, 4, True,
              True, False, "dirty")
    verdict, _ = judge(f)
    check("containment-beats-conflict", verdict == "already-landed", verdict)

    # V5: null mergeability at the conflict step escalates, never merges.
    f = _fact(9, "any", False, "green", 2, 0, False, False, None, "unknown")
    verdict, _ = judge(f)
    check("untellable-mergeable-escalates", verdict == "escalate-unknown",
          verdict)

    # V6: conflict mechanics on a clean-green head hold as hold-conflict.
    f = _fact(10, "any", False, "green", 2, 3, False, False, False, "dirty")
    verdict, _ = judge(f)
    check("conflict-holds", verdict == "hold-conflict", verdict)

    # V7-V16: rail and ledger vectors live in a sandbox directory.
    sandbox = tempfile.mkdtemp(prefix="auto_merge_selftest_")
    try:
        ledger = os.path.join(sandbox, "ledger.jsonl")
        green_facts = _fact(3, "rocqwash", False, "green", 1, 0, False,
                            False, True, "clean", branch="supply/seat-pack")

        # V7: whitelist accepts a supply/* head, dry-run writes nothing.
        out, row, wrote = run_rail(green_facts, "merge-ok", "supply/seat-pack",
                                   DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                                   ledger, False)
        check("rail-allows-supply", out == "allowed" and not wrote
              and not os.path.exists(ledger), out)

        # V8: whitelist refuses a foreign head.
        out, _, _ = run_rail(green_facts, "merge-ok", "feature/quick-fix",
                             DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                             ledger, False)
        check("rail-refuses-foreign-branch",
              out.startswith("refused:branch-whitelist"), out)

        # V9: a missing branch is not authorizable (loud data, rc 0),
        # never auto-authorized and never a guessed authorization.
        out, _, _ = run_rail(green_facts, "merge-ok", None,
                             DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                             ledger, False)
        check("rail-not-authorizable-missing-branch",
              out == "not-authorizable:missing-branch", out)

        # V10: --apply appends exactly one ledger row.
        out, row, wrote = run_rail(green_facts, "merge-ok", "supply/seat-pack",
                                   DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                                   ledger, True)
        lines = [l for l in open(ledger, encoding="utf-8").read().splitlines()
                 if l.strip()]
        check("apply-appends-one-row", out == "allowed" and wrote
              and len(lines) == 1
              and json.loads(lines[0])["kind"] == "authorize", out)

        # V11: a same-day re-authorization of the same PR is a refusal.
        out, _, wrote = run_rail(green_facts, "merge-ok", "supply/seat-pack",
                                 DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                                 ledger, True)
        lines2 = [l for l in open(ledger, encoding="utf-8").read()
                  .splitlines() if l.strip()]
        check("duplicate-authorization-refused",
              out.startswith("refused:duplicate-authorization")
              and not wrote and len(lines2) == 1, out)

        # V12: the daily budget cap refuses the fourth authorization.
        for i in (2, 3, 4):
            f_i = _fact(100 + i, "rocqwash", False, "green", 1, 0, False,
                        False, True, "clean", branch="supply/seat-%d" % i)
            out_i, _, w_i = run_rail(f_i, "merge-ok", "supply/seat-%d" % i,
                                     DEFAULT_ALLOW_PREFIX, 3, ledger, True)
        rows = read_ledger(ledger)
        check("daily-budget-cap", out_i.startswith("refused:daily-budget")
              and not w_i
              and len(allowed_merges_today(rows, utc_today())) == 3, out_i)

        # V13: hold verdicts never authorize; --apply writes nothing.
        hold = _fact(15, "ConstructiveWorld-Main", False, "content", 3, 6,
                     False, True, False, "dirty", branch="supply/old-head")
        verdict, _ = judge(hold)
        out, _, wrote = run_rail(hold, verdict, "supply/old-head",
                                 DEFAULT_ALLOW_PREFIX, DEFAULT_DAILY_CAP,
                                 ledger, True)
        check("hold-never-authorizes",
              out == "not-eligible:superseded-landed-elsewhere" and not wrote,
              out)

        # V14: the revert arc, content family.  The latest allowed row
        # carries no merge_sha, so a bare arc is a loud rc 9 refusal; the
        # --merge-sha override prescribes the revert once and the second
        # prescription for the same sha is refused.
        try:
            run_post_merge("content", ledger, None, False)
            check("revert-arc-without-sha-loud", False, "no exit raised")
        except SystemExit as exc:
            check("revert-arc-without-sha-loud", exc.code == 9,
                  "rc=%s" % exc.code)
        out, row, wrote, target = run_post_merge("content", ledger,
                                                 "1befa27", False)
        check("revert-arc-content-prescribes",
              out == "revert-prescribed" and not wrote
              and row["prescription"] == "git revert -m 1 1befa27"
              and target.get("pr") == 103, out)
        out, _, wrote, _ = run_post_merge("content", ledger, "1befa27",
                                          True)
        out2, _, wrote2, _ = run_post_merge("content", ledger, "1befa27",
                                            True)
        check("revert-arc-duplicate-refused",
              out == "revert-prescribed" and wrote and not wrote2
              and out2.startswith("refused:duplicate-prescription"), out2)

        # V15: the revert arc, other three families.
        out_t, row_t, _, _ = run_post_merge("transient", ledger, None, False)
        out_u, _, _, _ = run_post_merge("unrecognized", ledger, None, False)
        out_g, _, _, _ = run_post_merge("green", ledger, None, False)
        check("revert-arc-families",
              out_t == "rerun-window" and row_t is None
              and out_u == "escalate" and out_g == "no-action",
              "%s/%s/%s" % (out_t, out_u, out_g))

        # V16: post-merge with an empty ledger is fail-loud rc 9.
        empty_ledger = os.path.join(sandbox, "empty.jsonl")
        try:
            run_post_merge("content", empty_ledger, None, False)
            check("post-merge-empty-ledger-loud", False, "no exit raised")
        except SystemExit as exc:
            check("post-merge-empty-ledger-loud", exc.code == 9,
                  "rc=%s" % exc.code)

        # V17: the report face is deterministic (byte-identical rerun).
        p1 = emit(green_facts, "merge-ok", ["r"], "allowed", None, False,
                  None)
        p2 = emit(green_facts, "merge-ok", ["r"], "allowed", None, False,
                  None)
        check("report-byte-identical", p1 == p2, "")

        # V18: facts shape faults are rc 9.
        bad = os.path.join(sandbox, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump({"pr": 1, "merged": False, "ci": {"family": "green"},
                       "compare": {"ahead": 0}}, fh)
        try:
            load_facts(bad)
            check("facts-shape-fail-loud", False, "no exit raised")
        except SystemExit as exc:
            check("facts-shape-fail-loud", exc.code == 9, "rc=%s" % exc.code)
    finally:
        import shutil
        shutil.rmtree(sandbox, ignore_errors=True)

    if ok:
        print(MARK)
        return 0
    print("AUTO-MERGE-SELFTEST RED (see the vectors above)")
    return 2


# --------------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="X5 auto-merge gate judge (six-verdict enum) plus the "
                    "safety rail (supply/* whitelist, daily budget cap, "
                    "append-only merge ledger) and the post-merge revert "
                    "arc; zero network, dry run by default.")
    ap.add_argument("--facts", metavar="F",
                    help="facts JSON (rocqwash-automerge-facts/1) gathered "
                         "by the caller from the API and git compare")
    ap.add_argument("--head-branch", metavar="BR",
                    help="head branch name (wins over facts.head_branch)")
    ap.add_argument("--allow-prefix", default=DEFAULT_ALLOW_PREFIX,
                    metavar="P",
                    help="head branch whitelist prefix (default %s)"
                         % DEFAULT_ALLOW_PREFIX)
    ap.add_argument("--daily-cap", type=int, default=DEFAULT_DAILY_CAP,
                    metavar="N",
                    help="daily auto-merge authorization budget (default "
                         "%d)" % DEFAULT_DAILY_CAP)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, metavar="P",
                    help="append-only merge ledger JSONL (default %s)"
                         % DEFAULT_LEDGER)
    ap.add_argument("--merge-sha", metavar="SHA",
                    help="merge commit sha for the post-merge arc target "
                         "when the ledger row carries none")
    ap.add_argument("--post-merge", choices=list(POST_MERGE_FAMILIES),
                    metavar="FAM",
                    help="post-merge CI family observation; runs the "
                         "revert arc against the ledger instead of the "
                         "judge")
    ap.add_argument("--apply", action="store_true",
                    help="the only write face: append one ledger row (an "
                         "authorization or a revert prescription)")
    ap.add_argument("--json", dest="json_out", metavar="OUT",
                    help="also write the report JSON to OUT")
    ap.add_argument("--selftest", action="store_true",
                    help="frozen vector group on tmp fixtures")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        if args.facts or args.post_merge or args.apply:
            ap.error("--selftest runs alone")
        raise SystemExit(selftest())
    if args.daily_cap < 0:
        ap.error("--daily-cap must be >= 0")
    if args.post_merge:
        family = args.post_merge
        outcome, row, wrote, target = run_post_merge(
            family, args.ledger, args.merge_sha, args.apply)
        print("AUTO-MERGE-POST-MERGE: %s" % outcome)
        print("  target: pr=%s merge_sha=%s" % (
            target.get("pr"), args.merge_sha or target.get("merge_sha")))
        if row is not None:
            print("  prescription: %s" % row["prescription"])
            print("  ledger: %s (%s)" % (
                args.ledger, "row appended" if wrote else "dry run, row "
                "not written; pass --apply to record it"))
        else:
            print("  action: %s" % outcome)
        return 0
    if not args.facts:
        ap.error("--facts is required (or --selftest)")
    facts = load_facts(args.facts)
    verdict, reasons = judge(facts)
    branch = args.head_branch or facts.get("head_branch")
    rail_outcome, rail_row, wrote = run_rail(
        facts, verdict, branch, args.allow_prefix, args.daily_cap,
        args.ledger, args.apply)
    print("AUTO-MERGE-VERDICT: %s" % verdict)
    for reason in reasons:
        print("  reason: %s" % reason)
    print("AUTO-MERGE-RAIL: %s" % rail_outcome)
    if rail_row is not None:
        print("  ledger: %s (%s)" % (
            args.ledger, "row appended" if wrote else "dry run, row not "
            "written; pass --apply to record the authorization"))
    if verdict not in ("merge-ok",):
        print("  hold faces never merge; the recommendation rides the "
              "verdict, not the rail")
    emit(facts, verdict, reasons, rail_outcome, rail_row, wrote,
         args.json_out)
    if rail_outcome.startswith("refused:"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
