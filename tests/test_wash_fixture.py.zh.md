#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_wash_fixture.py — wash/_abl1_wash.py exact-string+count 断言自测（rocqwash tests/）。

被测件形制：_abl1_wash.py 无 CLI 参数，ROOT 硬编码战役席位路径（_abl1_wash.py:10）。
本测以模块导入＋ROOT 补丁方式，把其真实 main() 驱动到临时 fixture 目录上
（按 mod.PATCHES 账本逐 tag 以 old×expect 播种），三判：

  正判 pos ：全账本播种 → APPLY 全量（applied=N skipped=0 fail=NO·exit 0），
             逐 tag 落盘核 count(new)==expect 且 count(old)==0（old⊂new 的 tag 除外）；
  幂等 idem：同一目录重放 → old⊄new 的 tag 全 SKIP；old⊂new 的 tag（实测恰
             abl_audit_base_v7.v:require——new 以 old 为前缀）会再 APPLY；
             exit 仍 0、fail=NO。此为工具 SKIP 判据（c_old==0 才 skip）的实测行为，
             非猜测；
  反判 neg ：播种后破坏首个 tag 的 old 精确串 → 该 tag FAIL、该文件不落盘
             （逐字节恒等）、其余文件照常 APPLY、exit 1。

全程只写临时目录（mkdtemp，测毕即删）；硬编码席位 ROOT 永不被触碰。
用法：python3 tests/test_wash_fixture.py   # 全过 exit 0
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
    spec.loader.exec_module(mod)  # main() 仅在 __main__ 下执行，导入安全
    return mod


def run_main(mod):
    """跑被测 main()，返回 (exit_code, stdout)。"""
    out = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(out):
        try:
            mod.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue()


def seed_dir(mod, root, corrupt_first_tag=False):
    """按 PATCHES 账本播种：每 tag 以 old×expect 写入；可选破坏首个 tag 的 old。"""
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
            assert content.count(old0) == expect0 - 1, "破坏未生效"
        with io.open(os.path.join(root, fname), "w", encoding="utf-8") as fh:
            fh.write(content)
    return total


def parse_tags(stdout):
    """解析 main() 逐行账目 → {(fname, tag): 状态}（APPLY/SKIP/FAIL）。"""
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

    # ---------- 正判 pos ----------
    root = tempfile.mkdtemp(prefix="rocqwash_wash_pos_")
    try:
        assert root != orig_root
        seeded1 = seed_dir(mod, root)
        mod.ROOT = root
        rc1, out1 = run_main(mod)
        assert rc1 == 0, "正判 exit 应 0，实测 %s\n%s" % (rc1, out1)
        assert "applied=%d skipped=0 fail=NO" % total in out1, out1[-300:]
        st1 = parse_tags(out1)
        assert len(st1) == total and all(v == "APPLY" for v in st1.values()), out1
        # 落盘核数：count(new)==expect；count(old)==0（old⊂new 者例外，恒等 expect）
        for fname, plist in mod.PATCHES.items():
            with io.open(os.path.join(root, fname), encoding="utf-8") as fh:
                content = fh.read()
            for tag, old, new, expect in plist:
                assert content.count(new) == expect, \
                    "%s:%s count(new)=%d expect=%d" % (fname, tag, content.count(new), expect)
                want_old = expect if old in new else 0
                assert content.count(old) == want_old, \
                    "%s:%s count(old)=%d want=%d" % (fname, tag, content.count(old), want_old)

        # ---------- 幂等 idem（同目录重放）----------
        rc2, out2 = run_main(mod)
        assert rc2 == 0, "重放 exit 应 0，实测 %s\n%s" % (rc2, out2)
        assert "fail=NO" in out2
        st2 = parse_tags(out2)
        reapplicable = {(f, t) for f, pl in mod.PATCHES.items()
                        for t, old, new, _e in pl if old in new}
        for key, st in st2.items():
            want = "APPLY" if key in reapplicable else "SKIP"
            assert st == want, \
                "重放 %s 实测 %s 预期 %s（old⊂new 集合=%s）\n%s" % (key, st, want, reapplicable, out2)
        assert len(st2) == total
        print("WASH-POS PASS: 播种 %d tag 全 APPLY·落盘 count 断言全过；"
              "重放全 SKIP（old⊂new 的 %d 个 tag 再 APPLY 为工具 SKIP 判据实测行为）"
              % (total, len(reapplicable)))
    finally:
        mod.ROOT = orig_root
        shutil.rmtree(root, ignore_errors=True)

    # ---------- 反判 neg ----------
    root = tempfile.mkdtemp(prefix="rocqwash_wash_neg_")
    try:
        mod.ROOT = root
        seed_dir(mod, root, corrupt_first_tag=True)
        bad_fname = next(iter(mod.PATCHES))
        bad_tag = mod.PATCHES[bad_fname][0][0]
        with io.open(os.path.join(root, bad_fname), encoding="utf-8") as fh:
            seeded_bad = fh.read()
        rc3, out3 = run_main(mod)
        assert rc3 == 1, "反判 exit 应 1，实测 %s\n%s" % (rc3, out3)
        assert "FAIL  %s:%s" % (bad_fname, bad_tag) in out3, out3
        assert "NOT WRITTEN" in out3 and bad_fname in out3, out3
        assert "fail=YES" in out3
        with io.open(os.path.join(root, bad_fname), encoding="utf-8") as fh:
            after = fh.read()
        assert after == seeded_bad, "反判中坏文件被写盘（fail-loud 失守）"
        # 其余文件照常 APPLY（选择性 fail-loud）
        applied_n = sum(1 for k, v in parse_tags(out3).items() if v == "APPLY")
        assert applied_n == total - 1, "其余 tag 应全 APPLY，实测 %d/%d" % (applied_n, total - 1)
        print("WASH-NEG PASS: 破坏 %s:%s 后该 tag FAIL·该文件逐字节未动·"
              "其余 %d tag 照常 APPLY·exit 1" % (bad_fname, bad_tag, total - 1))
    finally:
        mod.ROOT = orig_root
        shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
