#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frozen8.py — frozen-anchor list check + four-piece trust-anchor hardening.

Header fields (annotation standard, five fields):
  Ticket           GD-20261115-SUBSTRATE-01, task A1: T0-1 ring-4 repair plus
                   T0-8 trust-anchor hardening (audit findings P0-1 and P1-5).
  Statement faces  check ring 1 manifest tier2 self-consistency; ring 2 manifest
                   equals ledger; ring 3 tier2 side roster; ring 4 disk equals
                   manifest (drift assignment repaired per P0-1); ring 5 git
                   history anchor; ring 6 detached GPG signature; ring 7 artifact
                   attestation (opt-in); ring 8 RFC 3161 timestamp (opt-in);
                   freeze face; roster listing face; RFC 3161 request face;
                   four-judgment-plus selftest.
  Source routing   the in-service eight-component constants stay sourced from
                   the ledger document 更新账.md §三 (read-only harvest); the v1
                   freeze functions are imported read-only from
                   certify/freeze_manifest.py (frozen file, byte-untouched).
  Run command      py -B certify/frozen8.py check --list
                   certify/frozen8_manifest.json --tier2 certify/frozen8_tier2.md5
  Registry         tests/test_destructive_matrix.py rows F1 and F2 (write
                   faces); EVID/t0-8/ (demo logs, NETRED ledger, post-merge
                   SOP); NETRED whitelist face: the RFC 3161 TSA fetch in the
                   timestamp face (each use is ledgered).

Purpose
-------
Machine check of the frozen-component list, in two anchored families:

  (1) In-service eight components (LEDGER8): ledger-anchored. The constants
      must equal the 更新账.md §三 rows (judgment 1) and the disk bytes
      (judgment 2). The roster is closed: exactly these eight.
  (2) Checker family (CHECKERS, meta-freeze): manifest-anchored. certify
      checkers cannot certify themselves out of their own roster — a checker
      edit lands in tier1 at the next freeze, and any later edit diverges from
      tier1, so ring 4 turns red. Sentinel immutability: the tool that judges
      the tree is itself judged by the same list. freeze_manifest.py is
      already anchored as LEDGER8 row 1 (frozen in service, byte-untouched
      here); the checker family adds certify/frozen8.py and
      certify/push_gate.py, so the manifest roster holds ten entries
      (eight → ten per the work order).

History of the ring-4 repair (audit P0-1)
-----------------------------------------
Rings used to print changed/removed lines without folding them into the
drift flag, so a tampered verify/verify_vo.py printed "DRIFT changed" and
still exited 0 (a fake green; CI's t_frozen8_check ran exactly this face).
Ring 4 now ends with a mandatory assignment; selftest judgment 5 re-runs a
one-byte disk tamper inside a scratch skeleton on every suite pass.

Trust-anchor hardening (audit P1-5: three anchors shared one writable tree)
---------------------------------------------------------------------------
  Ring 5  git history anchor. freeze records freeze_commit = HEAD at
          generation time. check asserts the current HEAD descends from it
          (git merge-base --is-ancestor), so rewriting history no longer
          launders a washed roster.
  Ring 6  detached GPG signature. The post-merge SOP signs the manifest
          (gpg --detach-sign → <manifest>.asc) and the freeze commit
          (annotated tag rocqwash-freeze-<date>, Steward key). check verifies
          the signature when one is reachable. Auto-detected <manifest>.asc
          that cannot be verified because the Steward public key is absent is
          an honest downgrade (CI runners never hold the key); an explicitly
          requested --gpg-sig that cannot be verified exits rc=9 honestly
          (fail-loud, never a fake green), per the GPG RC=9 precedent. A
          signature that verifies BAD is drift.
  Ring 7  artifact attestation (opt-in --attest). gh attestation verify
          against the origin repository; absent tooling or unreachable
          service is a registered downgrade, not a hard fail.
  Ring 8  external timestamp (opt-in --tsr PATH). RFC 3161 receipt from the
          freetsa.org TSA (timestamp face, below). check re-derives the
          manifest sha256 and compares it with the receipt's messageImprint
          digest binding. A present-but-invalid receipt is drift (fail
          closed); absence is a registered downgrade. Chain verification of
          the TSA signature itself is a post-merge SOP step (openssl ts
          -verify with the freetsa CA); this face pins the digest binding
          only and says so.

Determinism
-----------
freeze and check are offline and deterministic: no wall clock in the logic,
same tree plus same HEAD reproduces a byte-identical manifest. The timestamp
face touches the network once per explicit invocation (whitelisted face);
its output is a receipt, never a logic input.

Write-surface declaration
-------------------------
freeze writes only the caller-named --out and --tier2 paths. timestamp writes
only the caller-named --out path. check writes only the caller-named --json
path. Nothing else in the repository tree is touched; selftest writes only a
mkdtemp scratch directory and removes it. Matrix rows F1 and F2 in
tests/test_destructive_matrix.py pin these surfaces (who writes, enters the
matrix).

Commands
--------
  py -B certify/frozen8.py freeze [--repo DIR] --out LIST.json [--tier2 T2.md5]
      Recompute the ten roster entries. The eight in-service entries must
      equal the ledger constants and the disk bytes (any drift refuses the
      manifest, fail-closed); the two checker entries are taken from disk and
      must exist. freeze_commit = git HEAD is mandatory: without a usable git
      anchor the manifest is refused (rc=9 honest exit — an unanchored roster
      must not be issued). Idempotent replay: the same tree and HEAD produce
      byte-identical output (self-asserted).
  py -B certify/frozen8.py check [--repo DIR] --list LIST.json [--tier2 T2.md5]
        [--json OUT] [--gpg-sig SIG.asc] [--attest [--attest-repo SLUG]]
        [--tsr TSRC]
      Rings 1–4 as before (ring 4 repaired), plus rings 5–8 above. Exit
      precedence: any drift → 1; an honest-unavailable trust face reached via
      an explicit request (git anchor unusable on this machine; explicit
      --gpg-sig without a usable key or binary) → 9; otherwise 0. Malformed
      manifest → 2. Downgrades are printed and recorded in --json, never
      silent.
  py -B certify/frozen8.py timestamp --list MANIFEST --out TSRC
      RFC 3161 request face. sha256 of the manifest file, DER TimeStampReq to
      the freetsa.org TSA (endpoint overridable via ROCWASH_TSA_URL for
      offline tests), reachability self-check first, receipt written to the
      explicit --out only after its digest binding re-verifies locally.
      Unreachable TSA → rc=9 with a registered downgrade note (non-fatal per
      contract). Each network use is ledgered (NETRED whitelist: trust-anchor
      TSA fetch).
  py -B certify/frozen8.py --ledger
      Print the ten roster lines (`md5  relpath`); the eight ledger rows and
      the two checker rows (checker md5 computed from disk). A missing
      checker file is a loud rc=9, not a short list.
  py -B certify/frozen8.py --selftest
      Judgments 1–9 (all offline; scratch repos only):
        1 ledger constants ≡ ledger document (harvest, no conflict, no gap)
        2 disk ≡ ledger constants (8/8)
        3 manifest ≡ ledger + checkers, freeze_commit ≡ HEAD, tier2 side
          roster agrees, byte-identical replay
        4 reconciliation closure: clean rc=0; tampered manifest tier2 FAIL
          rc=1; tampered side roster FAIL rc=1
        5 disk-tamper visibility (P0-1 regression): scratch skeleton, one
          byte of verify/verify_vo.py flipped → ring 4 drives exit 1;
          restored → exit 0
        6 clean check shows every opt-in ring status visibly (no silent
          faces)
        7 present-but-corrupt .tsr receipt → rc=1 (fail closed)
        8 manifest without/malformed freeze_commit → rc=2
        9 history rewrite (git commit --amend under the anchor) → ring 5
          drift rc=1

Exit codes (per-face contract)
------------------------------
  freeze    0 issued / 1 roster drift, refuse to issue / 2 usage or output
            path unusable / 9 repo dir missing or git anchor unavailable
  check     0 all rings pass (downgrades registered on stdout and in --json) /
            1 any ring reports drift / 2 manifest malformed / 9 honest
            unavailable (git anchor unusable here; explicit --gpg-sig without
            a usable key or gpg binary)
  timestamp 0 receipt stored and binding verified / 1 TSA reply fails the
            local binding check (no receipt written) / 2 usage / 9 TSA
            unreachable or status not granted
  --ledger  0 / 9 a roster file is missing from disk
  --selftest 0 all judgments green / 1 any judgment red (loud assertion)
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
import urllib.request

PROG = "frozen8"
SCHEMA = "rocqwash-frozen8-manifest/2"
LEDGER_DOC = "更新账.md"

# In-service eight components (更新账.md §三, two rounds on record, values
# identical; relpath order equals the v1 tier1 order). In-service frozen: any
# value change requires a ledger-document generation change, which judgment 1
# surfaces mechanically.
LEDGER8 = (
    ("certify/freeze_manifest.py", "f5eeea458616e24f9867c074c954d267"),
    ("names/mac_stmt_names.py", "9e26c0db2c60ced3629a13a821bdf615"),
    ("scan/mac_stmt_scan.py", "56ff0fb371f9684cc865023f6f5d0f4a"),
    ("seam/seam_probe.py", "7a01359a22b8960b352191f1a4490b37"),
    ("tools/cpu_guard.sh", "442be5a2cb24af0a6847036f8c0cf5c5"),
    ("verify/gate4_comment_guard.py", "d7ab397c5f0243d0c7320f91d0f14481"),
    ("verify/verify_vo.py", "9d061d679dcceb0dcbbeb24e165eac7f"),
    ("wash/wash_engine.py", "664446bc717395d8496c8c30a5af9ccf"),
)
LEDGER_MAP = dict(LEDGER8)  # rel -> md5

# Checker family (meta-freeze, audit P1-5 answer "the sentinel must not be
# buyable"): the certify checkers freeze themselves into the roster they
# enforce. Manifest-anchored, not constant-anchored — a fixed point (a file
# embedding its own md5 as a constant) is computationally infeasible, so the
# checker md5 values live in tier1 at freeze time and tier2 self-hashing plus
# the trust anchors (rings 5–8) protect them. freeze_manifest.py already sits
# in LEDGER8 (row 1); the two rows here bring the roster to ten entries.
# push_gate.py is the third certify trust-face tool and supplies the tenth
# row mandated by the eight→ten roster instruction (the 8+2 arithmetic would
# double-count freeze_manifest.py, which is already one of the eight).
CHECKERS = (
    "certify/frozen8.py",
    "certify/push_gate.py",
)
CHECKER_SET = frozenset(CHECKERS)

# RFC 3161 trust-anchor TSA (freetsa.org, free public service). ROCWASH_TSA_URL
# overrides the endpoint for offline tests (matrix row F2 points it at a closed
# loopback port; the override is explicit, never a fallback).
TSA_HOST = "freetsa.org"
TSA_PORT = 80
TSA_URL = "http://freetsa.org/tsr"
TSA_TIMEOUT_CONNECT = 10
TSA_TIMEOUT_REQUEST = 30
SHA256_OID = "2.16.840.1.101.3.4.2.1"
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MD5_RE = re.compile(r"^[0-9a-f]{32}$")

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
try:
    import freeze_manifest as _v1  # noqa: E402  (frozen peer, import-only)
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 冻结同侪 certify/freeze_manifest.py 不可导入: %s" % _e,
          file=sys.stderr)
    sys.exit(9)

DEFAULT_REPO = os.path.dirname(_HERE)
MD5_LINE = re.compile(r"^([0-9a-f]{32})[ \t]+(\S+)[ \t]*$")


def run_out(argv):
    """Run one command, no shell → (rc, stdout, stderr); argv passed straight
    through, no injection surface."""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def disk_md5(repo, rel):
    """md5 of one file on disk; a missing original returns None (no masking)."""
    fp = os.path.join(repo, rel.replace("/", os.sep))
    if not os.path.isfile(fp):
        return None
    with open(fp, "rb") as f:
        return _v1.md5_bytes(f.read())


def disk_rows(repo):
    """The eight in-service entries from disk, ledger order → [(rel, md5|None)]."""
    return [(rel, disk_md5(repo, rel)) for rel, _ in LEDGER8]


def checker_rows(repo):
    """The checker-family entries from disk → [(rel, md5|None)]; a missing
    checker is an honest None (callers fail closed)."""
    return [(rel, disk_md5(repo, rel)) for rel in CHECKERS]


def roster_rows(repo):
    """Full ten-entry roster: eight ledger rows (constants, drift-checked by
    the caller) plus two checker rows from disk."""
    return disk_rows(repo) + checker_rows(repo)


def git_head(repo):
    """HEAD sha of the repo → (sha|None, detail). None means no usable git
    anchor here (not a work tree, no HEAD, git missing)."""
    if shutil.which("git") is None:
        return None, "git executable not found in PATH"
    rc, so, _ = run_out(["git", "-C", repo, "rev-parse", "--is-inside-work-tree"])
    if rc != 0 or so.strip() != "true":
        return None, "not a git work tree: %s" % repo
    rc, so, se = run_out(["git", "-C", repo, "rev-parse", "HEAD"])
    if rc != 0 or not GIT_SHA_RE.match(so.strip()):
        return None, "git rev-parse HEAD failed: %s" % se.strip()
    return so.strip(), ""


def harvest_ledger_doc(repo):
    """Judgment 1 harvest: every md5 row of the eight roster relpaths found in
    the ledger document. Returns (doc_map, problems) — two values for one file,
    a missing file, or a missing document all land in problems."""
    path = os.path.join(repo, LEDGER_DOC)
    doc_map, problems = {}, []
    if not os.path.isfile(path):
        return doc_map, ["账文档缺失: %s" % path]
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh:
            m = MD5_LINE.match(ln.rstrip("\n"))
            if not m:
                continue
            md5, rel = m.group(1), m.group(2)
            if rel not in LEDGER_MAP:  # harvest the eight rows only
                continue
            if rel in doc_map and doc_map[rel] != md5:
                problems.append("账文档内 %s 两值矛盾: %s vs %s"
                                % (rel, doc_map[rel], md5))
            doc_map.setdefault(rel, md5)
    missing = [rel for rel in LEDGER_MAP if rel not in doc_map]
    if missing:
        problems.append("账文档未见八件在册值: %s" % ", ".join(missing))
    return doc_map, problems


# ---------------- Section 1: freeze — issue the manifest (fail closed) -------

def cmd_freeze(args):
    repo = os.path.abspath(args.repo) if args.repo else DEFAULT_REPO
    if not os.path.isdir(repo):
        print("FAIL-LOUD: 仓库目录缺失: %s" % repo, file=sys.stderr)
        sys.exit(9)
    if not args.out:
        print("FAIL-LOUD: freeze 需 --out 名单出路径", file=sys.stderr)
        sys.exit(2)
    if args.tier2 and os.path.abspath(args.out) == os.path.abspath(args.tier2):
        print("FAIL-LOUD: --out 与 --tier2 同路径（侧册须独立在册）", file=sys.stderr)
        sys.exit(2)
    rows, drifts = [], []
    for rel, md5_now in disk_rows(repo):
        if md5_now is None:
            drifts.append("DRIFT removed  %s（正本缺失）" % rel)
        elif md5_now != LEDGER_MAP[rel]:
            drifts.append("DRIFT changed  %s\n    账载 %s\n    现盘 %s"
                          % (rel, LEDGER_MAP[rel], md5_now))
        else:
            rows.append((rel, md5_now))
    for rel, md5_now in checker_rows(repo):
        if md5_now is None:
            drifts.append("DRIFT removed  %s（检查器正本缺失）" % rel)
        else:
            rows.append((rel, md5_now))
    if drifts:
        print("frozen8 freeze FAIL: 名单面≠在册口径（%d 件漂移）——拒出名单"
              "（fail-closed·禁漂移洗账）" % len(drifts))
        for d in drifts:
            print("  " + d)
        sys.exit(1)
    head, detail = git_head(repo)
    if head is None:
        print("FAIL-LOUD: git 历史锚不可用（%s）——拒发无锚名单（rc=9 诚实退·"
              "无锚名单不得出册）" % detail, file=sys.stderr)
        sys.exit(9)
    rows = sorted(rows)
    t2 = _v1.tier2_of([tuple(r) for r in rows])
    doc = {"schema": SCHEMA, "root": repo,
           "ledger_source": LEDGER_DOC + " §三（在役八组件冻结自证·账载口径）",
           "n_files": len(rows), "tier1": [[r, m] for r, m in rows],
           "tier2_md5_of_tier1_text": t2,
           "freeze_commit": head,
           "checkers": list(CHECKERS)}
    for path in [args.out] + ([args.tier2] if args.tier2 else []):
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: 出路径父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("frozen8 freeze: 现盘名单面≡在册口径（8 账载＋2 检查器）——名单入册")
    for r, m in rows:
        print("  %s  %s" % (m, r))
    print("tier2=%s（tier1 账文 md5·两层冻结承 v1 口径）" % t2)
    print("freeze_commit=%s（生成时 HEAD·git 历史锚）" % head)
    if args.tier2:
        with io.open(args.tier2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t2 + "\n")
        print("tier2 侧册 ->", args.tier2)
    # Idempotency self-proof: re-serialize and compare byte for byte
    with io.open(args.out, encoding="utf-8", newline="") as fh:
        first = fh.read()
    again = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert first == again, "freeze 幂等自证失败（名单非确定性）"
    print("idempotent replay: 名单重产逐字节恒同 PASS")
    print("freeze OK: 名单 -> %s（供推送轮对账：check --list %s）" % (args.out, args.out))
    sys.exit(0)


# ---------------- Section 2: check — rings 1–8 -------------------------------

def cmd_check(args):
    repo = os.path.abspath(args.repo) if args.repo else DEFAULT_REPO
    if not os.path.isdir(repo):
        print("FAIL-LOUD: 仓库目录缺失: %s" % repo, file=sys.stderr)
        sys.exit(9)
    if not args.list:
        print("FAIL-LOUD: check 需 --list 在册名单", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.list):
        print("FAIL-LOUD: 名单缺失: %s" % args.list, file=sys.stderr)
        sys.exit(9)
    try:
        with io.open(args.list, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("schema") != SCHEMA:
            raise ValueError("schema 不识: %r（期望 %s；v1 整仓清单请走 "
                             "freeze_manifest.py check）" % (doc.get("schema"), SCHEMA))
        n_expect = len(LEDGER8) + len(CHECKERS)
        tier1 = doc["tier1"]
        if (not isinstance(tier1, list) or len(tier1) != n_expect
                or not all(isinstance(r, list) and len(r) == 2
                           and all(isinstance(x, str) for x in r) for r in tier1)):
            raise ValueError("tier1 须为 %d 行 [rel, md5]" % n_expect)
        fc = doc.get("freeze_commit")
        if not (isinstance(fc, str) and GIT_SHA_RE.match(fc)):
            raise ValueError("freeze_commit 缺失或非 40-hex（git 历史锚必载）")
    except Exception as e:
        print("FAIL-LOUD: 名单畸形: %s" % e, file=sys.stderr)
        sys.exit(2)

    drift = False
    unavailable = []   # honest-unavailable faces → rc=9 (never silent, never fake green)
    downgrades = []    # registered downgrades → rc untouched, visible on stdout + json
    rings = {}

    # Ring 1 manifest tier2 self-consistency (v1 rule: md5 of the tier1 text —
    # any manifest edit surfaces here)
    t2_now = _v1.tier2_of([tuple(r) for r in doc["tier1"]])
    t2_ok = (t2_now == doc.get("tier2_md5_of_tier1_text"))
    print("名单 tier2 自洽（名单未被改）: %s" % ("PASS" if t2_ok else "FAIL"))
    drift = drift or not t2_ok
    rings["tier2_ok"] = t2_ok

    # Ring 2 manifest face ≡ ledger face (the eight rows must equal the
    # constants; the checker set must be exactly CHECKERS; nothing else)
    list_map = {r: m for r, m in doc["tier1"]}
    ledger_bad = []
    for rel, m in LEDGER8:
        if rel not in list_map:
            ledger_bad.append("DRIFT removed  名单缺在册件 %s" % rel)
        elif list_map[rel] != m:
            ledger_bad.append("DRIFT ledger   %s 名单 %s ≠ 账载 %s"
                              % (rel, list_map[rel], m))
    for rel in CHECKERS:
        if rel not in list_map:
            ledger_bad.append("DRIFT removed  名单缺检查器 %s" % rel)
        elif not MD5_RE.match(list_map[rel]):
            ledger_bad.append("DRIFT malformed %s 检查器行非 md5 形" % rel)
    if doc.get("checkers") != list(CHECKERS):
        ledger_bad.append("DRIFT checkers  名单检查器集 %r ≠ 在册检查器族 %r"
                          % (doc.get("checkers"), list(CHECKERS)))
    for rel in sorted(set(list_map) - set(LEDGER_MAP) - CHECKER_SET):
        ledger_bad.append("DRIFT added    名单多出非在册面 %s" % rel)
    print("名单口径≡账载（8 账载＋检查器族）: %s" % ("PASS" if not ledger_bad else "FAIL"))
    for b in ledger_bad:
        print("  " + b)
    drift = drift or bool(ledger_bad)
    rings["ledger_ok"] = not ledger_bad

    # Ring 3 tier2 side roster (external file; bites only when given)
    side_ok = None
    if args.tier2:
        if not os.path.isfile(args.tier2):
            print("FAIL-LOUD: 侧册缺失: %s" % args.tier2, file=sys.stderr)
            sys.exit(9)
        with io.open(args.tier2, encoding="utf-8") as fh:
            side = fh.read().strip()
        side_ok = (side == doc.get("tier2_md5_of_tier1_text"))
        print("tier2 侧册咬合: %s" % ("PASS" if side_ok else "FAIL"))
        drift = drift or not side_ok
    rings["side_ok"] = side_ok

    # Ring 4 disk recomputation against the manifest roster (closed universe
    # of ten: changed/removed). Audit P0-1: this loop used to print drift
    # lines without folding them into the verdict — the assignment below is
    # the repair, and selftest judgment 5 re-proves it every suite pass.
    changed, removed = [], []
    for rel, md5_now in roster_rows(repo):
        if md5_now is None:
            removed.append(rel)
            print("  DRIFT removed  %s（正本缺失）" % rel)
        elif md5_now != list_map.get(rel):
            changed.append(rel)
            print("  DRIFT changed  %s（现盘 %s ≠ 名单 %s）"
                  % (rel, md5_now, list_map.get(rel)))
    drift = drift or bool(changed or removed)
    rings["disk_ok"] = not (changed or removed)

    # Ring 5 git history anchor: current HEAD must descend from freeze_commit
    # (merge-base assertion — rewritten history can no longer launder a
    # washed roster; a rollback below the anchor is drift too).
    fc = doc["freeze_commit"]
    head, detail = git_head(repo)
    if head is None:
        print("FAIL-LOUD: git 历史锚不可验（%s）——rc=9 诚实退（不假绿）" % detail,
              file=sys.stderr)
        unavailable.append("git-anchor: %s" % detail)
        rings["git_anchor"] = "unavailable"
    else:
        rc, _, _ = run_out(["git", "-C", repo, "merge-base", "--is-ancestor",
                            fc, head])
        if rc == 0 or head == fc:
            print("git 历史锚（HEAD 为 freeze_commit 后代）: PASS (%s)" % fc[:12])
            rings["git_anchor"] = "pass"
        elif rc == 1:
            # S2 v2 (20261117 user order): squash landings carry no parent
            # chain, so a non-descendant HEAD with all four content faces green
            # is the squash shape, not a rewrite.  Content equivalence
            # (tier2/ledger/side/disk all green) downgrades to a registration;
            # any content drift still fails loud below the rollback backstop.
            content_ok = (rings.get("tier2_ok") and rings.get("ledger_ok")
                          and rings.get("side_ok") and rings.get("disk_ok"))
            if content_ok:
                print("  git-anchor: DOWNGRADED（HEAD %s 非 freeze_commit %s 后代"
                      "——squash 落岸无父链·四内容面全绿=内容等价·降档登记"
                      "不硬败；追责在 S1 台账与回滚弧）" % (head[:12], fc[:12]))
                downgrades.append("git-anchor: squash-shape (content-equivalent; freeze_commit=%s head=%s)"
                                  % (fc[:12], head[:12]))
                rings["git_anchor"] = "downgraded"
            else:
                print("  DRIFT git锚   HEAD %s 非 freeze_commit %s 后代"
                      "（改史/回滚现形）" % (head[:12], fc[:12]))
                drift = True
                rings["git_anchor"] = "drift"
        else:
            # Object missing etc. — shallow fetch or pruned history: cannot
            # verify here (CI shallow clones), honest downgrade, re-verify in
            # a full clone (SOP step 6).
            print("git 历史锚: DOWNGRADED（历史不完整·浅克隆?——本机不可验，"
                  "全量克隆复核；降档登记不硬败）")
            downgrades.append("git-anchor: history incomplete (merge-base rc=%d)" % rc)
            rings["git_anchor"] = "downgraded"

    # Ring 6 detached GPG signature. Auto-detect <manifest>.asc: verification
    # failure caused by a missing Steward public key is a registered downgrade
    # (CI never holds the key); an explicitly requested --gpg-sig is strict —
    # unverifiable exits rc=9 honestly (GPG RC=9 precedent), a BAD signature
    # is drift.
    sig = args.gpg_sig
    strict = sig is not None
    if sig is None:
        cand = args.list + ".asc"
        if os.path.isfile(cand):
            sig = cand
    if sig is None:
        print("GPG-SIG: 未在册（<名单>.asc 缺席·合并前状态属预期；post-merge "
              "SOP 签 manifest＋freeze tag）——降档登记不硬败")
        downgrades.append("gpg-sig: no detached signature in tree")
        rings["gpg_sig"] = "downgraded-absent"
    elif shutil.which("gpg") is None:
        print("FAIL-LOUD: 签名在册而 gpg 可执行缺失——rc=9 诚实退（不假绿）",
              file=sys.stderr)
        unavailable.append("gpg-sig: gpg executable missing")
        rings["gpg_sig"] = "unavailable"
    else:
        rc, so, se = run_out(["gpg", "--verify", sig, args.list])
        blob = so + se
        if rc == 0 and "Good signature" in blob:
            print("GPG-SIG: PASS（%s）" % os.path.basename(sig))
            rings["gpg_sig"] = "pass"
        elif "No public key" in blob or "public key not found" in blob:
            note = ("gpg-sig: Steward public key not in this keyring "
                    "(strict=%s)" % strict)
            if strict:
                print("FAIL-LOUD: 显式 --gpg-sig 而公钥不在钥匙环——rc=9 诚实退"
                      "（SOP＋升格注记·非硬败不假绿）", file=sys.stderr)
                unavailable.append(note)
            else:
                print("GPG-SIG: DOWNGRADED（Steward 公钥不在本机钥匙环——"
                      "Steward 侧按 SOP 验签；降档登记不硬败）")
                downgrades.append(note)
            rings["gpg_sig"] = "unavailable"
        else:
            print("  DRIFT gpg签   签名验败 rc=%d（BAD/改动现形）" % rc)
            drift = True
            rings["gpg_sig"] = "drift"

    # Ring 7 artifact attestation (opt-in; gh attestation against the origin
    # repository). Absent tooling or an unreachable/not-yet-attested state is
    # a registered downgrade, never a hard fail.
    if args.attest:
        slug = args.attest_repo
        gh = shutil.which("gh")
        if gh is None:
            print("ATTEST: DOWNGRADED（gh CLI 不在本机——gh attestation 不可达；"
                  "降档登记不硬败）")
            downgrades.append("attest: gh CLI unavailable")
            rings["attest"] = "downgraded"
        else:
            rc, so, se = run_out([gh, "attestation", "verify", args.list,
                                  "-R", slug])
            if rc == 0:
                print("ATTEST: PASS（gh attestation %s）" % slug)
                rings["attest"] = "pass"
            else:
                print("ATTEST: DOWNGRADED（gh attestation rc=%d——未出证/不可达；"
                      "post-merge SOP 出证后复验；降档登记不硬败）" % rc)
                downgrades.append("attest: gh attestation rc=%d" % rc)
                rings["attest"] = "downgraded"
    else:
        print("ATTEST: 未请求（opt-in --attest）")
        rings["attest"] = "not-requested"

    # Ring 8 external RFC 3161 timestamp (opt-in). The receipt pins the
    # sha256 of the manifest file; a present receipt must match, otherwise
    # drift (fail closed). Absence is a registered downgrade. TSA chain
    # verification is a post-merge SOP step with the freetsa CA.
    if args.tsr:
        if not os.path.isfile(args.tsr):
            print("FAIL-LOUD: 时间戳回执缺失: %s" % args.tsr, file=sys.stderr)
            sys.exit(9)
        with open(args.list, "rb") as f:
            digest = hashlib.sha256(f.read()).digest()
        try:
            bound = tsr_message_digest(io.open(args.tsr, "rb").read())
        except Exception as e:
            bound = None
            print("  DRIFT rfc3161 回执解析失败（%s）" % e)
        if bound is not None and bound == digest:
            print("RFC3161: PASS（回执 digest 绑定≡名单 sha256；TSA 链验证按 "
                  "SOP 用 freetsa CA）")
            rings["tsr"] = "pass"
        else:
            if bound is not None:
                print("  DRIFT rfc3161 回执绑定≠现名单 sha256（名单晚于回执"
                      "被改/回执陈旧现形）")
            drift = True
            rings["tsr"] = "drift"
    else:
        print("RFC3161: 未请求（opt-in --tsr PATH）")
        rings["tsr"] = "not-requested"

    legs = "tier2 自洽/名单≡账载/盘≡账载" + ("/侧册" if args.tier2 else "")
    print("frozen8 check %s: %s · %d changed / %d removed"
          % ("OK" if not drift else "FAIL", legs, len(changed), len(removed)))
    if downgrades:
        print("降档登记（%d 项·不硬败不假绿）:" % len(downgrades))
        for d in downgrades:
            print("  " + d)
    if unavailable:
        print("诚实不可用（%d 项·rc=9）:" % len(unavailable))
        for u in unavailable:
            print("  " + u)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"schema": SCHEMA, "repo": repo, "list": args.list,
                       "tier2_ok": t2_ok, "ledger_ok": not ledger_bad,
                       "side_ok": side_ok, "changed": changed,
                       "removed": removed,
                       "rings": rings,
                       "downgrades": downgrades,
                       "unavailable": unavailable,
                       "verdict": "PASS" if not drift else "FAIL"},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    if drift:
        sys.exit(1)
    if unavailable:
        sys.exit(9)
    sys.exit(0)


# ---------------- Section 3: RFC 3161 minimal DER codec + timestamp face -----

def _der_len(n):
    if n < 0x80:
        return bytes([n])
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(body)]) + body


def _der_tlv(tag, content):
    return bytes([tag]) + _der_len(len(content)) + content


def _der_oid(dotted):
    parts = [int(x) for x in dotted.split(".")]
    out = bytearray([parts[0] * 40 + parts[1]])
    for v in parts[2:]:
        chunk = [v & 0x7F]
        v >>= 7
        while v:
            chunk.append((v & 0x7F) | 0x80)
            v >>= 7
        out.extend(reversed(chunk))
    return bytes(out)


def _der_one(buf, off=0):
    """Parse one TLV at offset → (tag, content, next_offset)."""
    tag = buf[off]
    off += 1
    first = buf[off]
    off += 1
    if first & 0x80:
        n = first & 0x7F
        length = int.from_bytes(buf[off:off + n], "big")
        off += n
    else:
        length = first
    return tag, buf[off:off + length], off + length


def _der_children(content):
    out, off = [], 0
    while off < len(content):
        tag, body, nxt = _der_one(content, off)
        out.append((tag, body))
        off = nxt
    return out


def build_tsreq(digest):
    """DER TimeStampReq: SEQUENCE { version 1, messageImprint{sha256, digest},
    certReq TRUE }. certReq makes the TSA embed its certificate chain in the
    receipt, so the SOP chain-verification step (openssl ts -verify with the
    freetsa CA) has the signer certificate on hand. No nonce: identical input
    yields identical request bytes (determinism rule)."""
    alg = _der_tlv(0x30, _der_tlv(0x06, _der_oid(SHA256_OID)))
    imprint = _der_tlv(0x30, alg + _der_tlv(0x04, digest))
    return _der_tlv(0x30, _der_tlv(0x02, b"\x01") + imprint
                    + _der_tlv(0x01, b"\xff"))


def tsr_message_digest(tsr):
    """Extract messageImprint.hashedMessage from a TimeStampResp DER blob.
    Raises ValueError on any structural mismatch (callers fail closed)."""
    _, content, _ = _der_one(tsr)                       # TimeStampResp
    kids = _der_children(content)
    if len(kids) < 2 or kids[1][0] != 0x30:
        raise ValueError("TimeStampResp lacks a TimeStampToken")
    ci = _der_children(kids[1][1])                      # ContentInfo
    if len(ci) < 2 or ci[1][0] != 0xA0:
        raise ValueError("ContentInfo lacks explicit content")
    sd = _der_one(ci[1][1])                             # SignedData (explicit)
    fields = _der_children(sd[1])
    if len(fields) < 3 or fields[2][0] != 0x30:
        raise ValueError("SignedData lacks encapContentInfo")
    ec = _der_children(fields[2][1])
    if len(ec) < 2 or ec[1][0] != 0xA0:
        raise ValueError("encapContentInfo lacks eContent")
    octets = _der_one(ec[1][1])                         # OCTET STRING → TSTInfo
    tst = _der_one(octets[1])
    tf = _der_children(tst[1])
    if len(tf) < 3 or tf[2][0] != 0x30:
        raise ValueError("TSTInfo lacks messageImprint")
    mi = _der_children(tf[2][1])
    if len(mi) < 2 or mi[1][0] != 0x04:
        raise ValueError("messageImprint lacks hashedMessage")
    return mi[1][1]


def tsr_status(tsr):
    """PKIStatusInfo.status integer from a TimeStampResp (0=granted,
    1=grantedWithMods). Raises ValueError on structural mismatch."""
    _, content, _ = _der_one(tsr)
    kids = _der_children(content)
    if not kids or kids[0][0] != 0x30:
        raise ValueError("TimeStampResp lacks PKIStatusInfo")
    st = _der_children(kids[0][1])
    if not st or st[0][0] != 0x02:
        raise ValueError("PKIStatusInfo lacks status INTEGER")
    return int.from_bytes(st[0][1], "big")


def cmd_timestamp(args):
    """RFC 3161 request face. NETRED whitelist: trust-anchor TSA fetch; every
    use is ledgered in the run's NETRED record. Write face: the explicit --out
    only, and only after the receipt re-verifies its digest binding locally."""
    print("NETRED: trust-anchor TSA fetch face (whitelisted; ledgered per use)")
    if not args.list:
        print("FAIL-LOUD: timestamp 需 --list 名单路径", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(args.list):
        print("FAIL-LOUD: 名单缺失: %s" % args.list, file=sys.stderr)
        sys.exit(9)
    if not args.out:
        print("FAIL-LOUD: timestamp 需 --out 回执出路径（显式指认唯一写面）",
              file=sys.stderr)
        sys.exit(2)
    parent = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(parent):
        print("FAIL-LOUD: 回执出路径父目录缺失: %s" % parent, file=sys.stderr)
        sys.exit(2)
    url = os.environ.get("ROCWASH_TSA_URL") or TSA_URL
    target = urllib.parse.urlsplit(url)
    host = target.hostname or TSA_HOST
    port = target.port or TSA_PORT
    with open(args.list, "rb") as f:
        blob = f.read()
    digest = hashlib.sha256(blob).digest()
    req = build_tsreq(digest)
    # Reachability self-check first, aimed at the endpoint that is about to be
    # used (a connect that fails is a registered downgrade, never a fake
    # receipt).
    try:
        probe = socket.create_connection((host, port),
                                         timeout=TSA_TIMEOUT_CONNECT)
        probe.close()
    except OSError as e:
        print("FAIL-LOUD: TSA 可达性自勘失败（%s:%s: %s）——rc=9 诚实退；"
              "降档登记不硬败（SOP 记录补打时间戳）" % (host, port, e),
              file=sys.stderr)
        sys.exit(9)
    request = urllib.request.Request(
        url, data=req,
        headers={"Content-Type": "application/timestamp-query",
                 "Accept": "application/timestamp-reply"})
    try:
        with urllib.request.urlopen(request, timeout=TSA_TIMEOUT_REQUEST) as resp:
            tsr = resp.read()
    except Exception as e:
        print("FAIL-LOUD: TSA 请求失败（%s: %s）——rc=9 诚实退；降档登记不硬败"
              % (url, e), file=sys.stderr)
        sys.exit(9)
    try:
        status = tsr_status(tsr)
    except Exception as e:
        print("FAIL-LOUD: TSA 回执解析失败（%s）——rc=9 诚实退" % e, file=sys.stderr)
        sys.exit(9)
    if status not in (0, 1):
        print("FAIL-LOUD: TSA 状态未授予（status=%d）——rc=9 诚实退" % status,
              file=sys.stderr)
        sys.exit(9)
    try:
        bound = tsr_message_digest(tsr)
    except Exception as e:
        print("FAIL-LOUD: TSA 回执缺 messageImprint（%s）——拒写回执 rc=1"
              % e, file=sys.stderr)
        sys.exit(1)
    if bound != digest:
        print("FAIL-LOUD: TSA 回执 digest 绑定≠名单 sha256——拒写回执 rc=1",
              file=sys.stderr)
        sys.exit(1)
    with io.open(args.out, "wb") as fh:
        fh.write(tsr)
    print("RFC3161: 回执入册 -> %s（digest 绑定已本地复验：%s…）"
          % (args.out, digest.hex()[:16]))
    print("时间戳外部锚出证（TSA 链验证按 SOP 用 freetsa CA 复核）")
    sys.exit(0)


# ---------------- Section 4: --ledger ----------------------------------------

def cmd_ledger():
    """Print the ten roster lines (`md5  relpath`): the eight ledger rows plus
    the two checker rows computed from disk (a missing checker is a loud rc=9,
    not a short list)."""
    lines = []
    for rel, md5_now in roster_rows(DEFAULT_REPO):
        if md5_now is None:
            print("FAIL-LOUD: 在册件缺失: %s" % rel, file=sys.stderr)
            sys.exit(9)
        lines.append("%s  %s" % (md5_now, rel))
    for ln in lines:
        print(ln)
    sys.exit(0)


# ---------------- Section 5: --selftest (offline, scratch trees only) --------

def _copy_skeleton(dst):
    """Copy the ten roster files from the real repo into dst, preserving
    relpaths; init a scratch git repo with one commit; return its HEAD."""
    for rel in [r for r, _ in LEDGER8] + list(CHECKERS):
        src = os.path.join(DEFAULT_REPO, rel.replace("/", os.sep))
        fp = os.path.join(dst, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(src, "rb") as f:
            data = f.read()
        with open(fp, "wb") as f:
            f.write(data)
    run_out(["git", "-C", dst, "init", "-q"])
    run_out(["git", "-C", dst, "-c", "user.name=frozen8-selftest",
             "-c", "user.email=frozen8@selftest.invalid", "add", "-A"])
    rc, so, se = run_out(["git", "-C", dst, "-c", "user.name=frozen8-selftest",
                          "-c", "user.email=frozen8@selftest.invalid",
                          "commit", "-q", "-m", "frozen8 selftest anchor"])
    assert rc == 0, "scratch commit failed: %s%s" % (so, se)
    head, detail = git_head(dst)
    assert head is not None, "scratch git anchor unavailable: %s" % detail
    return head


def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_frozen8_self_")
    try:
        repo = DEFAULT_REPO
        me = os.path.abspath(__file__)

        # Judgment 1 ledger constants ≡ ledger document (mechanical harvest)
        doc_map, problems = harvest_ledger_doc(repo)
        assert not problems, "判① 账载≡文档红: %s" % "; ".join(problems)
        for rel, m in LEDGER8:
            assert doc_map.get(rel) == m, \
                "判① 账载≡文档红: %s 文档 %r ≠ 账载 %s" % (rel, doc_map.get(rel), m)
        print("判① 账载≡文档 PASS: %s 八件在册值逐件咬合（收割 %d/8 件）"
              % (LEDGER_DOC, len(doc_map)))

        # Judgment 2 disk ≡ ledger constants (first machine proof of the doc face)
        for rel, md5_now in disk_rows(repo):
            assert md5_now == LEDGER_MAP[rel], \
                "判② 盘≡账红: %s 现盘 %s ≠ 账载 %s" % (rel, md5_now, LEDGER_MAP[rel])
        print("判② 盘≡账 PASS: 现盘八件逐件 md5 与账载全等（8/8）")

        # Judgment 3 manifest ≡ ledger + checkers, anchor ≡ HEAD, idempotent
        lst = os.path.join(tmp, "f8.json")
        side = os.path.join(tmp, "f8.t2")
        rc, so, se = run_out([sys.executable, "-B", me, "freeze",
                              "--out", lst, "--tier2", side])
        assert rc == 0, "判③ freeze 应 0 实测 %d\n%s%s" % (rc, so, se)
        doc = json.load(io.open(lst, encoding="utf-8"))
        checker_md5s = [(rel, disk_md5(repo, rel)) for rel in CHECKERS]
        assert all(m is not None for _, m in checker_md5s), "判③ 检查器缺盘"
        expected = sorted([(r, m) for r, m in LEDGER8] + checker_md5s)
        assert doc["tier1"] == [list(r) for r in expected], "判③ 名单 tier1 ≠ 账载+检查器族"
        assert doc["n_files"] == len(LEDGER8) + len(CHECKERS), "判③ 名单面数 ≠ 十件"
        assert doc["tier2_md5_of_tier1_text"] == _v1.tier2_of(
            [tuple(r) for r in expected]), "判③ 名单 tier2 ≠ v1 口径"
        head_real, _ = git_head(repo)
        assert doc["freeze_commit"] == head_real, "判③ freeze_commit ≠ 现 HEAD"
        with io.open(side, encoding="utf-8") as fh:
            assert fh.read().strip() == doc["tier2_md5_of_tier1_text"], \
                "判③ 侧册 ≠ 名单 tier2"
        first = open(lst, "rb").read()
        rc, so, se = run_out([sys.executable, "-B", me, "freeze", "--out", lst])
        assert rc == 0 and open(lst, "rb").read() == first, \
            "判③ 幂等失守\n%s%s" % (so, se)
        print("判③ 名单≡账·检查器族入册·锚≡HEAD·幂等 PASS: 十行名单与盘面"
              "逐字咬合·重产逐字节恒同")

        # Judgment 4 reconciliation closure + manifest/side tamper surfacing
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", lst, "--tier2", side])
        assert rc == 0 and "frozen8 check OK" in so, \
            "判④ 零漂移 check 应 0\n%s%s" % (rc, so, se)
        bad = json.load(io.open(lst, encoding="utf-8"))
        bad["tier1"][0][1] = "0" * 32  # tamper one manifest md5 (tier2 stale)
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        rc, so, se = run_out([sys.executable, "-B", me, "check", "--list", bad_path])
        assert rc == 1, "判④ 名单篡改应 1 实测 %d\n%s%s" % (rc, so, se)
        assert "名单 tier2 自洽（名单未被改）: FAIL" in so, so
        assert "名单口径≡账载（8 账载＋检查器族）: FAIL" in so, so
        side_bad = os.path.join(tmp, "side_bad.t2")
        with io.open(side_bad, "w", encoding="utf-8") as fh:
            fh.write("0" * 32 + "\n")
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", lst, "--tier2", side_bad])
        assert rc == 1 and "tier2 侧册咬合: FAIL" in so, \
            "判④ 侧册篡改应现形\n%s%s" % (rc, so, se)
        print("判④ 对账闭环·篡改现形 PASS: 零漂移 rc=0；名单 md5 篡改→tier2+口径 "
              "FAIL rc=1；侧册篡改→咬合 FAIL rc=1")

        # Judgment 5 disk-tamper visibility (audit P0-1 regression): scratch
        # skeleton, flip one byte of verify/verify_vo.py → ring 4 must drive
        # exit 1 (pre-repair this printed DRIFT and exited 0); restore → 0.
        skel = os.path.join(tmp, "skel")
        os.makedirs(skel)
        head_skel = _copy_skeleton(skel)
        skel_lst = os.path.join(tmp, "skel.json")
        rc, so, se = run_out([sys.executable, "-B", me, "freeze",
                              "--repo", skel, "--out", skel_lst])
        assert rc == 0, "判⑤ skeleton freeze 应 0 实测 %d\n%s%s" % (rc, so, se)
        vo = os.path.join(skel, "verify", "verify_vo.py")
        with open(vo, "rb") as f:
            orig = f.read()
        tampered = bytearray(orig)
        tampered[len(tampered) // 2] ^= 0x01  # flip exactly one byte
        with open(vo, "wb") as f:
            f.write(bytes(tampered))
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--repo", skel, "--list", skel_lst])
        assert rc == 1, "判⑤ 盘面一字节篡改应 rc=1 实测 %d（P0-1 回归）\n%s%s" \
            % (rc, so, se)
        assert "DRIFT changed  verify/verify_vo.py" in so, so
        with open(vo, "wb") as f:
            f.write(orig)
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--repo", skel, "--list", skel_lst])
        assert rc == 0 and "frozen8 check OK" in so, \
            "判⑤ 还原后应 rc=0\n%s%s" % (rc, so, se)
        print("判⑤ 盘面篡改现形（P0-1 回归）PASS: verify/verify_vo.py 一字节"
              "→环④驱动 rc=1；还原→rc=0")

        # Judgment 6 clean check surfaces every opt-in ring visibly (no
        # silent faces): gpg downgrade (no .asc), attest/timestamp not
        # requested.
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--repo", skel, "--list", skel_lst])
        assert rc == 0, "判⑥ 净面 check 应 0\n%s%s" % (rc, so, se)
        assert "GPG-SIG: 未在册" in so, so
        assert "ATTEST: 未请求" in so, so
        assert "RFC3161: 未请求" in so, so
        assert "降档登记" in so, so
        print("判⑥ 降档可见性 PASS: 无 .asc→GPG-SIG 降档登记；opt-in 环显式"
              "示未请求；零静默面")

        # Judgment 7 present-but-corrupt timestamp receipt → rc=1 (fail closed)
        junk = os.path.join(tmp, "junk.tsr")
        with io.open(junk, "wb") as fh:
            fh.write(b"\x30\x03\x02\x01\x02garbage")
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--repo", skel, "--list", skel_lst, "--tsr", junk])
        assert rc == 1, "判④/⑦ 坏回执应 rc=1 实测 %d\n%s%s" % (rc, so, se)
        assert "DRIFT rfc3161" in so and "解析失败" in so, so
        print("判⑦ 坏回执 fail-closed PASS: 在册而损坏的 .tsr → rc=1")

        # Judgment 8 manifest without / malformed freeze_commit → rc=2
        nofc = json.load(io.open(skel_lst, encoding="utf-8"))
        del nofc["freeze_commit"]
        nofc_path = os.path.join(tmp, "nofc.json")
        with io.open(nofc_path, "w", encoding="utf-8") as fh:
            json.dump(nofc, fh)
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", nofc_path])
        assert rc == 2, "判⑧ 缺 freeze_commit 应 rc=2 实测 %d\n%s%s" % (rc, so, se)
        badfc = json.load(io.open(skel_lst, encoding="utf-8"))
        badfc["freeze_commit"] = "zz-not-a-sha"
        badfc_path = os.path.join(tmp, "badfc.json")
        with io.open(badfc_path, "w", encoding="utf-8") as fh:
            json.dump(badfc, fh)
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", badfc_path])
        assert rc == 2, "判⑧ 畸形 freeze_commit 应 rc=2 实测 %d\n%s%s" % (rc, so, se)
        print("判⑧ 历史锚字段必载 PASS: 缺/畸形 freeze_commit → rc=2")

        # Judgment 9 history rewrite surfaces: amend the scratch commit under
        # the anchor → current HEAD no longer descends from freeze_commit →
        # ring 5 drift rc=1.
        # Pin the amended commit's author date so the new commit SHA cannot
        # collide with the original: an amend landing inside the same
        # commit-timestamp granularity as the original reproduces the very
        # same SHA (same tree, same message, same author and committer
        # second), which reads as "no drift" and fails this judgment on fast
        # machines (observed on the CI runners).
        rc, so, se = run_out(["git", "-C", skel, "-c", "user.name=frozen8-selftest",
                              "-c", "user.email=frozen8@selftest.invalid",
                              "commit", "--amend", "--no-edit", "--quiet",
                              "--date=2001-01-01T00:00:00"])
        assert rc == 0, "判⑨ scratch amend 失败\n%s%s" % (so, se)
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--repo", skel, "--list", skel_lst])
        assert rc == 1, "判⑨ 改史后应 rc=1 实测 %d\n%s%s" % (rc, so, se)
        assert "DRIFT git锚" in so, so
        print("判⑨ 改史现形 PASS: amend 换史→HEAD 非 freeze_commit 后代→"
              "环⑤ rc=1（防改史洗白）")

        print("FROZEN8-SELFTEST PASS: 九判绿（账载≡文档/盘≡账/名单≡账·检查器族·"
              "锚≡HEAD·幂等/对账闭环/盘面篡改现形 P0-1 回归/降档可见/坏回执 "
              "fail-closed/锚字段必载/改史现形）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- Section 6: CLI ---------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="frozen-anchor list check + trust-anchor hardening "
                    "(ten-entry roster; rings 1-8)")
    sub = ap.add_subparsers(dest="cmd")
    fz = sub.add_parser("freeze",
                        help="issue the manifest (fail-closed; requires a git anchor)")
    fz.add_argument("--repo", default=None, help="repository root (default: this repo)")
    fz.add_argument("--out", default=None, help="manifest output path")
    fz.add_argument("--tier2", default=None,
                    help="tier2 side roster output path (optional)")
    ck = sub.add_parser("check",
                        help="rings 1-8 reconciliation (manifest, side roster, disk, "
                             "git anchor, gpg, attest, timestamp)")
    ck.add_argument("--repo", default=None, help="repository root (default: this repo)")
    ck.add_argument("--list", default=None, help="manifest path")
    ck.add_argument("--tier2", default=None,
                    help="tier2 side roster (optional; bites when given)")
    ck.add_argument("--json", default=None, help="reconciliation JSON output path")
    ck.add_argument("--gpg-sig", default=None,
                    help="detached signature path (strict mode: unverifiable → rc=9); "
                         "default auto-detects <manifest>.asc with downgrade semantics")
    ck.add_argument("--attest", action="store_true",
                    help="ring 7: gh attestation verify (opt-in)")
    ck.add_argument("--attest-repo", default="hy7pc8gfmf-dotcom/rocqwash",
                    help="repository slug for gh attestation")
    ck.add_argument("--tsr", default=None,
                    help="ring 8: RFC 3161 receipt path (opt-in; present receipt "
                         "must match the manifest sha256)")
    ts = sub.add_parser("timestamp",
                        help="RFC 3161 timestamp face (freetsa.org; NETRED "
                             "whitelisted; explicit --out only)")
    ts.add_argument("--list", default=None, help="manifest to timestamp")
    ts.add_argument("--out", default=None, help="receipt output path (.tsr)")
    ap.add_argument("--ledger", action="store_true",
                    help="print the ten roster lines (md5  relpath)")
    ap.add_argument("--selftest", action="store_true",
                    help="nine-judgment self-proof (offline, scratch trees)")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    if args.ledger:
        cmd_ledger()
    if args.cmd == "freeze":
        cmd_freeze(args)
    elif args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "timestamp":
        cmd_timestamp(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
