#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wash_fixture.py - exact-string/count selftest for `wash/_abl1_wash.py` (rocqwash tests/).

Purpose.  Drives the real `main()` of `wash/_abl1_wash.py` over temporary
  fixture directories (module import plus `ROOT` patch; the tool has no CLI
  and its `ROOT` is a hardcoded absolute path).  Entries are seeded from the
  tool's own `PATCHES` ledger (each `old` written `expect` times), then
  three cases run: positive - fully seeded tree, every entry APPLY
  (`applied=N skipped=0 fail=NO`, exit 0) with on-disk checks
  count(new)==expect and count(old)==0 (entries with `old` contained in
  `new` stay at expect); replay - same-directory rerun, entries with `old`
  not contained in `new` SKIP while the one entry whose `new` extends its
  `old` (`abl_audit_base_v7.v:require`) reapplies - the measured consequence
  of the skip criterion (skip only when c_old==0), exit still 0; negative -
  the first tag's `old` corrupted after seeding, that tag FAILs, its file
  stays byte-identical, every other file still APPLYs, exit 1.  Only temp
  directories are written; the hardcoded `ROOT` is never touched.

Interface.  `python3 tests/test_wash_fixture.py` - no flags; prints `WASH-POS PASS`
  and `WASH-NEG PASS` lines on success, aborts on the first failed assert.
  Suite registration: `tests/run_tests.sh:336`.

Dependencies.  Python 3 standard library only (contextlib, importlib.util, io, os,
  shutil, sys, tempfile); writes only under `tempfile.mkdtemp` directories.

Evidence.  Runs on every suite pass through the registration above; the replay
  exception is documented in `tests/README.md` (c_old==0 makes an old-inside-new entry reapply).

Exit-codes.  0 = all three cases pass; nonzero = a failed assert (tool exit codes
  asserted per case: 0 positive and replay, 1 negative).
"""
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "wash", "_abl1_wash.py")


def load_tool():
    spec = importlib.util.spec_from_file_location("abl1_wash", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # main() runs only under __main__, so import is safe
    return mod


def run_main(mod):
    """Run the tool under test's main(); return (exit_code, stdout)."""
    out = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out):
        try:
            mod.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue()


def seed_dir(mod, root, corrupt_first_tag=False):
    """Seed from the PATCHES ledger: write each tag's `old` expect times; optionally corrupt the first tag's `old`."""
    total = 0
    for fname, plist in mod.PATCHES.items():
        blocks = []
        for tag, old, new, expect in plist:
            blocks.append((old + "\n") * expect)
            total += 1
        content = "(* rocqwash wash selftest fixture *)\n" + "".join(blocks)
        if corrupt_first_tag and fname == next(iter(mod.PATCHES)):
            tag0, old0, _new0, expect0 = plist[0]
            bad = old0[: len(old0) // 2] + "#" + old0[len(old0) // 2:]
            assert old0 in content and content.count(old0) == expect0
            content = content.replace(old0, bad, 1)
            assert content.count(old0) == expect0 - 1, "corruption did not take effect"
        with io.open(os.path.join(root, fname), "w", encoding="utf-8") as fh:
            fh.write(content)
    return total


def parse_tags(stdout):
    """Parse main()'s per-line output into {(fname, tag): status} (APPLY/SKIP/FAIL)."""
    status = {}
    for line in stdout.splitlines():
        for prefix in ("APPLY ", "SKIP  ", "FAIL  "):
            if line.startswith(prefix):
                head = line[len(prefix):].split()[0]
                fname, tag = head.split(":", 1)
                status[(fname, tag)] = prefix.strip()
    return status


def main():
    mod = load_tool()
    orig_root = mod.ROOT
    total = sum(len(p) for p in mod.PATCHES.values())

    # ---------- positive case ----------
    root = tempfile.mkdtemp(prefix="rocqwash_wash_pos_")
    try:
        assert root != orig_root
        seeded1 = seed_dir(mod, root)
        mod.ROOT = root
        rc1, out1 = run_main(mod)
        assert rc1 == 0, "positive case exit must be 0, got %s\n%s" % (rc1, out1)
        assert "applied=%d skipped=0 fail=NO" % total in out1, out1[-300:]
        st1 = parse_tags(out1)
        assert len(st1) == total and all(v == "APPLY" for v in st1.values()), out1
        # on-disk count check: count(new)==expect; count(old)==0
        # (entries with old inside new keep the expect count instead)
        for fname, plist in mod.PATCHES.items():
            with io.open(os.path.join(root, fname), encoding="utf-8") as fh:
                content = fh.read()
            for tag, old, new, expect in plist:
                assert content.count(new) == expect, \
                    "%s:%s count(new)=%d expect=%d" % (fname, tag, content.count(new), expect)
                want_old = expect if old in new else 0
                assert content.count(old) == want_old, \
                    "%s:%s count(old)=%d want=%d" % (fname, tag, content.count(old), want_old)

        # ---------- idempotent replay (same directory) ----------
        rc2, out2 = run_main(mod)
        assert rc2 == 0, "replay exit must be 0, got %s\n%s" % (rc2, out2)
        assert "fail=NO" in out2
        st2 = parse_tags(out2)
        reapplicable = {(f, t) for f, pl in mod.PATCHES.items()
                        for t, old, new, _e in pl if old in new}
        for key, st in st2.items():
            want = "APPLY" if key in reapplicable else "SKIP"
            assert st == want, \
                "replay %s got %s expected %s (old-inside-new set=%s)\n%s" % (key, st, want, reapplicable, out2)
        assert len(st2) == total
        print("WASH-POS PASS: seeded %d tags, all APPLY, on-disk count asserts pass; "
              "replay all SKIP (the %d tags with old inside new reapply: measured "
              "behavior of the tool's SKIP criterion)"
              % (total, len(reapplicable)))
    finally:
        mod.ROOT = orig_root
        shutil.rmtree(root, ignore_errors=True)

    # ---------- negative case ----------
    root = tempfile.mkdtemp(prefix="rocqwash_wash_neg_")
    try:
        mod.ROOT = root
        seed_dir(mod, root, corrupt_first_tag=True)
        bad_fname = next(iter(mod.PATCHES))
        bad_tag = mod.PATCHES[bad_fname][0][0]
        with io.open(os.path.join(root, bad_fname), encoding="utf-8") as fh:
            seeded_bad = fh.read()
        rc3, out3 = run_main(mod)
        assert rc3 == 1, "negative case exit must be 1, got %s\n%s" % (rc3, out3)
        assert "FAIL  %s:%s" % (bad_fname, bad_tag) in out3, out3
        assert "NOT WRITTEN" in out3 and bad_fname in out3, out3
        assert "fail=YES" in out3
        with io.open(os.path.join(root, bad_fname), encoding="utf-8") as fh:
            after = fh.read()
        assert after == seeded_bad, "negative case wrote the corrupted file (fail-loud broken)"
        # the other files still APPLY (selective fail-loud)
        applied_n = sum(1 for k, v in parse_tags(out3).items() if v == "APPLY")
        assert applied_n == total - 1, "all other tags must APPLY, got %d/%d" % (applied_n, total - 1)
        print("WASH-NEG PASS: after corrupting %s:%s that tag FAILs, the file stays "
              "byte-identical, the other %d tags still APPLY, exit 1" % (bad_fname, bad_tag, total - 1))
    finally:
        mod.ROOT = orig_root
        shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
