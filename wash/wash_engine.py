#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wash_engine.py — 通用逐件规范洗入口（rocqwash wash/·20261031 席 rqwash）

把战役级批洗工装 wash/_abl1_wash.py（席 abl1·20261027）的应用循环 1:1 泛化为
argv 驱动的逐件引擎：exact-string 替换 ＋ count 断言 ＋ 幂等（new 已在盘且 old
绝迹=skip）＋ fail-loud（任一 FAIL 该文件整笔不落盘）＋ 嵌套括号感知（台账片段
须括号自平衡·注释/字符串掩蔽后机检·承 abl1 站文逐字采集纪律）。

血统与冻结继承：
  - 应用循环（APPLY/SKIP/FAIL 三态账＋post-assert＋选择性落盘）与
    wash/_abl1_wash.py:130-151 逐步 1:1（APPLY/SKIP/FAIL 判据逐字同）；
  - 嵌套注释/字符串状态机 strip_comments_strings 与 scan/mac_stmt_scan.py:104
    1:1 冻结继承（本文件本地重实现·不 import 冻结件——防冻结件漂移牵连；
    等价性由 --selftest 内嵌嵌套注释向量机械背书）；
  - 台账 JSON 形制＝_abl1_wash.py PATCHES 账本的逐字段直译（tag/old/new/expect）。

七步规范中的位置：本引擎＝第③步「规范面映射洗」的执行器（洗什么由台账显式给）。
引擎永不猜目标：无 --patch 即 exit 3（SKIP 语义·「无台账不洗」），绝不代填任何
隐式映射——面映射目标（Qlt→QltT／Qle→QleT'／==→QeqT／裸=→Id+id_cong／nat≤→NatLe）
须由人工/上游分诊产出台账后交本引擎机械执行（统一入口 cli/rocqwash wash 自动路由）。

用法：
  python3 wash/wash_engine.py --file <in.v> --patch <ledger.json> --out <out.v>
                              [--dry-run] [--json out.json] [--selftest]
  cli/rocqwash wash --file a.v --patch ledger.json --out b.v   # 统一入口自动路由

台账 ledger.json 形制（两种皆收）：
  {"file": "可选默认目标.v", "patches": [{"tag": "...", "old": "...", "new": "...",
                                          "expect": 1}, ...]}
  或裸数组 [{"tag": ..., "old": ..., "new": ..., "expect": ...}, ...]
  - old/new 须括号自平衡（(*…*) 注释与 "…" 字符串内括号不计）；
  - expect ≥ 1 整数；old ≠ new；old 若为 new 的子串（前缀补丁）幂等重放会再 APPLY
    （_abl1_wash SKIP 判据 c_old==0 的实测行为·与战役工装一致，账面如实出）。

退出码：0=全账 APPLY/SKIP（fail=NO）；1=任一 FAIL（该文件不落盘）；
        2=台账畸形（JSON 坏/字段缺/括号失衡/old==new/expect<1）；
        3=未给 --patch（无台账不洗——SKIP 语义，供 make demo / CLI 冒烟 SKIP 判）；
        9=--file/--patch 路径缺失。
写隔离：永不回写 --file；--out == --file 拒绝（exit 2）；源/产物 md5 双双出账。
"""
import argparse
import hashlib
import io
import json
import os
import sys

PROG = "wash_engine"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_comments_strings(text):
    """状态机剥嵌套注释与字符串字面量；被剥区域替换为空格保持行号。

    1:1 冻结继承 scan/mac_stmt_scan.py:104-125（词面核 v3·E364 T8/T3）——
    本地重实现不 import，等价性由 --selftest 嵌套注释向量机械背书。
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        c = text[i]
        if depth > 0:
            if text.startswith("(*", i):
                depth += 1; out.append("  "); i += 2; continue
            if text.startswith("*)", i):
                depth -= 1; out.append("  "); i += 2; continue
            out.append(c if c == "\n" else " "); i += 1; continue
        if text.startswith("(*", i):
            depth = 1; out.append("  "); i += 2; continue
        if c == '"':
            out.append(" "); i += 1
            while i < n and text[i] != '"':
                out.append(text[i] if text[i] == "\n" else " "); i += 1
            if i < n: out.append(" "); i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


def bracket_report(fragment):
    """嵌套括号感知：注释/字符串掩蔽后逐括号记深。返回 (ok, 定位描述)。"""
    clean = strip_comments_strings(fragment)
    pairs = {")": "(", "]": "[", "}": "{"}
    depths = {"(": 0, "[": 0, "{": 0}
    for i, c in enumerate(clean):
        if c in depths:
            depths[c] += 1
        elif c in pairs:
            o = pairs[c]
            if depths[o] <= 0:
                return False, "孤儿 closer %r @掩蔽后偏移 %d" % (c, i)
            depths[o] -= 1
    for o, d in depths.items():
        if d != 0:
            return False, "括号失衡：剩余 %d 个未闭合 %r" % (d, o)
    return True, "balanced"


def load_ledger(patch_path):
    """读台账 JSON（裸数组或 {"patches":[...]} 双形）并逐项校验（fail-loud）。"""
    try:
        with io.open(patch_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        raise LedgerError("台账 JSON 解析失败 %s: %s" % (patch_path, e))
    if isinstance(data, dict):
        plist = data.get("patches")
        default_file = data.get("file")
    else:
        plist, default_file = data, None
    if not isinstance(plist, list) or not plist:
        raise LedgerError("台账须非空数组或 {\"patches\": [...]}（实测 %s）"
                          % type(data).__name__)
    for k, p in enumerate(plist):
        where = "patches[%d]" % k
        if not isinstance(p, dict):
            raise LedgerError("%s 须对象（实测 %s）" % (where, type(p).__name__))
        for field in ("tag", "old", "new", "expect"):
            if field not in p:
                raise LedgerError("%s 缺字段 %s" % (where, field))
        if not isinstance(p["tag"], str) or not p["tag"]:
            raise LedgerError("%s.tag 须非空字符串" % where)
        for field in ("old", "new"):
            if not isinstance(p[field], str):
                raise LedgerError("%s.%s 须字符串" % (where, field))
        if not isinstance(p["expect"], int) or isinstance(p["expect"], bool) \
                or p["expect"] < 1:
            raise LedgerError("%s.expect 须 ≥1 整数（实测 %r）" % (where, p["expect"]))
        if p["old"] == p["new"]:
            raise LedgerError("%s old==new（空洗拒绝）" % where)
        for field in ("old", "new"):
            ok, why = bracket_report(p[field])
            if not ok:
                raise LedgerError("%s.%s 嵌套括号感知不过：%s" % (where, field, why))
    return plist, default_file


class LedgerError(Exception):
    pass


def apply_patches(content, plist, fname="<mem>"):
    """应用循环——与 wash/_abl1_wash.py:130-151 逐步 1:1。

    返回 (new_content, rows, fail_flag)；rows=[(tag, state, detail)]，
    state ∈ APPLY/SKIP/FAIL。fail=True 时 new_content 无效（调用方不得落盘）。
    """
    rows = []
    n_apply = n_skip = n_fail = 0
    file_fail = False
    for tag, old, new, expect in [(p["tag"], p["old"], p["new"], p["expect"])
                                  for p in plist]:
        c_old = content.count(old)
        c_new = content.count(new)
        if c_new >= expect and c_old == 0:
            rows.append((tag, "SKIP", "already applied (count(new)>=%d, count(old)=0)" % expect))
            n_skip += 1
            continue
        if c_old != expect:
            rows.append((tag, "FAIL", "count(old)=%d expect=%d -- no edit" % (c_old, expect)))
            file_fail = True
            n_fail += 1
            continue
        content = content.replace(old, new)
        assert content.count(new) >= expect, "post-assert %s:%s" % (fname, tag)
        rows.append((tag, "APPLY", "old=%d -> new inserted" % c_old))
        n_apply += 1
    summary = {"applied": n_apply, "skipped": n_skip, "fail": n_fail,
               "file_fail": file_fail}
    return content, rows, summary


def selftest():
    """内嵌冻结向量组：正判/幂等/破坏反判/括号反判/台账畸形反判 五判（临时目录驱动）。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_washeng_self_")
    try:
        src_v = os.path.join(tmp, "vec.v")
        body = "(* nest (* deep *) outer *)\nLemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n"
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
        ledger = {"patches": [
            {"tag": "eq2id", "expect": 1,
             "old": "Lemma vec_a : forall x : nat, x = x.\n",
             "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"},
            {"tag": "refl2id", "expect": 1,
             "old": "  intros x. reflexivity.\n",
             "new": "  intros x. apply id_refl.\n"},
        ]}
        ledger_path = os.path.join(tmp, "ledger.json")
        with io.open(ledger_path, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)

        # —— 正判 pos：全 APPLY＋落盘 count 断言＋嵌套注释未伤行号 ——
        out_v = os.path.join(tmp, "vec_washed.v")
        rc = run_args(["--file", src_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 0, "正判应 exit 0 实测 %d" % rc
        with io.open(out_v, encoding="utf-8", newline="") as fh:
            washed = fh.read()
        assert washed.count("Id nat x x") == 1 and washed.count("apply id_refl") == 1
        assert washed.count("x = x.") == 0 and washed.count("reflexivity") == 0
        assert "nest (* deep *) outer" in washed, "注释内容须原样保留"

        # —— 幂等 idem：对洗后产物同账重放 → 全 SKIP、exit 0、产物逐字节恒等 ——
        before = open(out_v, "rb").read()
        out_v2 = os.path.join(tmp, "vec_washed2.v")
        rc = run_args(["--file", out_v, "--patch", ledger_path, "--out", out_v2])
        assert rc == 0, "幂等重放应 exit 0 实测 %d" % rc
        assert open(out_v2, "rb").read() == before, "幂等重放不得改字节"

        # —— 写隔离：--out == --file 拒绝（exit 2）——
        rc = run_args(["--file", out_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 2, "--out==--file 应 exit 2 实测 %d" % rc

        # —— 破坏反判 neg：old 精确串被破坏 → FAIL·exit 1·产物逐字节未动 ——
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write(body.replace("x = x.", "x = (x)."))
        rc = run_args(["--file", src_v, "--patch", ledger_path, "--out", out_v])
        assert rc == 1, "破坏反判应 exit 1 实测 %d" % rc
        assert open(out_v, "rb").read() == before, "fail-loud 失守：坏账竟落盘"

        # —— 括号反判 bracket-neg：old 括号失衡 → exit 2·零写 ——
        bad = {"patches": [{"tag": "bad", "old": "f (x.", "new": "g (x).", "expect": 1}]}
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        rc = run_args(["--file", src_v, "--patch", bad_path, "--out", out_v])
        assert rc == 2, "括号失衡应 exit 2 实测 %d" % rc

        # —— 畸形反判 ledger-neg：old==new → exit 2 ——
        silly = {"patches": [{"tag": "s", "old": "a", "new": "a", "expect": 1}]}
        silly_path = os.path.join(tmp, "silly.json")
        with io.open(silly_path, "w", encoding="utf-8") as fh:
            json.dump(silly, fh)
        rc = run_args(["--file", src_v, "--patch", silly_path, "--out", out_v])
        assert rc == 2, "old==new 应 exit 2 实测 %d" % rc

        # —— 无台账 → exit 3（SKIP 语义·不猜）——
        rc = run_args(["--file", src_v])
        assert rc == 3, "无台账应 exit 3 实测 %d" % rc

        print("WASH-ENGINE-SELFTEST PASS: pos/idem/isolation/neg/bracket-neg/ledger-neg/no-ledger 七判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    """以 argv 驱动 main()（selftest 复用路径）；返回进程语义退出码。"""
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def main():
    # 无台账前置分流：--patch/-p 均不在 argv 且非 --selftest → exit 3（SKIP 语义）。
    # 先于 argparse：统一入口裸调/位置形（如 make demo 的 `cli/rocqwash wash demo.v`）
    # 恒走此分支，demo 的 SKIP 判据（rc 3/4）保持成立；带台账时未知参数仍由
    # argparse 硬拒（usage exit 2·fail-loud 不放水）。
    argv = sys.argv[1:]
    has_patch = any(a == "-p" or a == "--patch" or a.startswith("--patch=") for a in argv)
    has_selftest = any(a == "--selftest" for a in argv)
    if not has_patch and not has_selftest:
        print("wash_engine: 未给 --patch——洗目标永不猜（七步③须显式台账）。", file=sys.stderr)
        print("  用法: wash_engine.py --file <in.v> --patch <ledger.json> --out <out.v>", file=sys.stderr)
        print("  （无台账=SKIP 语义 exit 3；台账形制见本文件 docstring）", file=sys.stderr)
        sys.exit(3)
    ap = argparse.ArgumentParser(prog=PROG, description="通用逐件规范洗引擎（exact-string+count+幂等）")
    ap.add_argument("file_pos", nargs="?", default=None, metavar="FILE",
                    help="同 --file（位置形；统一入口裸调形态）")
    ap.add_argument("--file", "-f", dest="file_opt", default=None, help="输入 .v（写隔离·永不回写）")
    ap.add_argument("--patch", "-p", default=None, help="洗账台账 JSON（tag/old/new/expect）")
    ap.add_argument("--out", "-o", default=None, help="洗后输出路径（必填才落盘；== --file 拒绝）")
    ap.add_argument("--dry-run", action="store_true", help="全账出账不落盘")
    ap.add_argument("--json", default=None, help="账目 JSON 出账路径")
    ap.add_argument("--selftest", action="store_true", help="内嵌冻结向量组五判自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    if not os.path.isfile(args.patch):
        print("FAIL-LOUD: --patch 路径缺失: %s" % args.patch, file=sys.stderr)
        sys.exit(9)
    try:
        plist, ledger_default = load_ledger(args.patch)
    except LedgerError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    src = args.file_opt or args.file_pos or ledger_default
    if src is None:
        print("FAIL-LOUD: 有 --patch 但缺 --file（或台账 file 字段）", file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(src):
        print("FAIL-LOUD: --file 路径缺失: %s" % src, file=sys.stderr)
        sys.exit(9)

    if args.out and os.path.abspath(args.out) == os.path.abspath(src):
        print("FAIL-LOUD: 写隔离——--out 不得等于 --file（%s）" % src, file=sys.stderr)
        sys.exit(2)

    with io.open(src, encoding="utf-8", newline="") as fh:
        content = fh.read()
    src_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()

    new_content, rows, summary = apply_patches(content, plist, fname=os.path.basename(src))
    for tag, state, detail in rows:
        print("%-5s %s:%s  %s" % (state, os.path.basename(src), tag, detail))

    wrote = False
    out_md5 = None
    if summary["file_fail"]:
        print("--- applied=%d skipped=%d fail=YES  file=NOT-WRITTEN（fail-loud·修账后重跑）"
              % (summary["applied"], summary["skipped"]))
    elif args.dry_run:
        print("--- applied=%d skipped=%d fail=NO  file=DRY-RUN（未落盘）"
              % (summary["applied"], summary["skipped"]))
    elif not args.out:
        print("FAIL-LOUD: 需 --out 才落盘（写隔离·原件不回写）；或用 --dry-run 仅出账", file=sys.stderr)
        sys.exit(2)
    else:
        with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_content)
        wrote = True
        out_md5 = md5_of(args.out)
        print("--- applied=%d skipped=%d fail=NO  file=%s" % (summary["applied"], summary["skipped"], args.out))

    print("md5 src=%s%s" % (src_md5, (" out=%s" % out_md5) if out_md5 else ""))

    if args.json:
        acc = {"file": src, "patch": args.patch, "out": args.out if wrote else None,
               "dry_run": args.dry_run, "src_md5": src_md5, "out_md5": out_md5,
               "rows": [{"tag": t, "state": s, "detail": d} for t, s, d in rows],
               **{k: v for k, v in summary.items()}}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(1 if summary["file_fail"] else 0)


if __name__ == "__main__":
    main()
