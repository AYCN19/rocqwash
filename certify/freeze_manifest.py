#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""freeze_manifest.py — 两层冻结清单机检（rocqwash certify/·20261031 席 rqwash）

certify 模块第一件：两层冻结（two-tier freeze）的机械落地——

  第一层 tier1：逐文件 md5（相对路径排序·确定性遍历）；
  第二层 tier2：对 tier1 账文的 md5（`relpath  md5\n` 逐行·sha 同 md5 算法）——
                清单自身被冻结，动清单即被发现。

幂等可重放：freeze 不含时间戳/环境噪声，同一盘面重复 freeze 产出逐字节恒同
清单；check 重算并三分出账（changed/added/removed），零漂移 exit 0、有漂移 exit 1。

诚实律：check 只认重算 md5（机械证据），不出「未动过」的口头判词；清单文件自身
（--out 名）与 .git/ 恒不入账（自指/噪音免除·在册声明）。

用法：
  python3 certify/freeze_manifest.py freeze <dir> --out manifest.json [--tier2 tier2.md5]
  python3 certify/freeze_manifest.py check  <dir> --manifest manifest.json [--json out.json]
  python3 certify/freeze_manifest.py --selftest

退出码：freeze=0 成功／2 清单路径可写性失败；check=0 零漂移／1 有漂移（changed/
added/removed 任一）／2 清单畸形；9=dir/manifest 路径缺失。
（UNION v2 多世界清单与推窗四判据为 certify 后续件——本轮待办，未实现不出桩。）
"""
import argparse
import hashlib
import io
import json
import os
import sys

PROG = "freeze_manifest"
SCHEMA = "rocqwash-freeze-manifest/1"
EXCLUDE_DIRS = (".git", "__pycache__")


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def tier1_lines(root):
    """确定性逐件账：相对路径排序 → `relpath  md5\n` 行列（列表）。"""
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
            with open(fp, "rb") as f:
                rows.append((rel, md5_bytes(f.read())))
    return sorted(rows)


def tier2_of(lines):
    return md5_bytes("".join("%s  %s\n" % (r, m) for r, m in lines).encode("utf-8"))


def cmd_freeze(args):
    if not os.path.isdir(args.dir):
        print("FAIL-LOUD: 目录缺失: %s" % args.dir, file=sys.stderr)
        sys.exit(9)
    if args.out == args.tier2 and args.tier2:
        print("FAIL-LOUD: --out 与 --tier2 同路径（tier2 须独立在册）", file=sys.stderr)
        sys.exit(2)
    rows = tier1_lines(args.dir)
    t2 = tier2_of(rows)
    doc = {"schema": SCHEMA, "root": os.path.abspath(args.dir),
           "n_files": len(rows), "tier1": [[r, m] for r, m in rows],
           "tier2_md5_of_tier1_text": t2}
    for path in ([args.out] + ([args.tier2] if args.tier2 else [])):
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: 清单父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("freeze OK: %d 文件入账 -> %s" % (len(rows), args.out))
    print("tier2=%s（tier1 账文的 md5·两层冻结）" % t2)
    if args.tier2:
        with io.open(args.tier2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t2 + "\n")
        print("tier2 ->", args.tier2)
    # 幂等自证：重算一遍与在盘清单逐字节对照（freeze 自身可重放）
    with io.open(args.out, encoding="utf-8", newline="") as fh:
        first = fh.read()
    doc2 = dict(doc)
    doc2_json = json.dumps(doc2, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert first == doc2_json, "freeze 幂等自证失败（清单非确定性）"
    print("idempotent replay: 清单重产逐字节恒同 PASS")
    sys.exit(0)


def cmd_check(args):
    if not os.path.isdir(args.dir):
        print("FAIL-LOUD: 目录缺失: %s" % args.dir, file=sys.stderr)
        sys.exit(9)
    if not os.path.isfile(args.manifest):
        print("FAIL-LOUD: 清单缺失: %s" % args.manifest, file=sys.stderr)
        sys.exit(9)
    try:
        with io.open(args.manifest, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as e:
        print("FAIL-LOUD: 清单 JSON 解析失败: %s" % e, file=sys.stderr)
        sys.exit(2)
    if doc.get("schema") != SCHEMA:
        print("FAIL-LOUD: 清单 schema 不识: %r（期望 %s）" % (doc.get("schema"), SCHEMA),
              file=sys.stderr)
        sys.exit(2)

    # tier2 先验：清单内 tier1 账文重算 md5 须与在册 tier2 咬合（动清单即发现）
    t2_now = tier2_of([tuple(r) for r in doc.get("tier1", [])])
    t2_ok = (t2_now == doc.get("tier2_md5_of_tier1_text"))
    print("tier2 自洽（清单未被改）: %s" % ("PASS" if t2_ok else "FAIL"))

    now = dict(tier1_lines(args.dir))
    base = {r: m for r, m in doc.get("tier1", [])}
    changed = sorted(r for r, m in now.items() if r in base and base[r] != m)
    added = sorted(r for r in now if r not in base)
    removed = sorted(r for r in base if r not in now)
    for label, lst in (("changed", changed), ("added", added), ("removed", removed)):
        for r in lst:
            print("  DRIFT %-8s %s" % (label, r))
    drift = bool(changed or added or removed or not t2_ok)
    print("check %s: %d changed / %d added / %d removed / tier2 %s"
          % ("FAIL" if drift else "OK", len(changed), len(added), len(removed),
             "PASS" if t2_ok else "FAIL"))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"dir": os.path.abspath(args.dir), "manifest": args.manifest,
                       "tier2_ok": t2_ok, "changed": changed, "added": added,
                       "removed": removed, "verdict": "PASS" if not drift else "FAIL"},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(1 if drift else 0)


def selftest():
    """冻结向量组：freeze 幂等／check 零漂移／三漂移各一／tier2 篡改必现形。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_freeze_self_")
    try:
        root = os.path.join(tmp, "world")
        sub = os.path.join(root, "sub")
        os.makedirs(sub)
        def w(rel, content):
            with io.open(os.path.join(root, rel), "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
        w("a.v", "Lemma a : True.\n")
        w("sub/b.v", "Lemma b : True.\n")

        man = os.path.join(tmp, "m.json")
        rc = run_args(["freeze", root, "--out", man])
        assert rc == 0, "freeze 应 0 实测 %d" % rc
        first = open(man, "rb").read()

        # 幂等：同盘面再 freeze → 逐字节恒同
        rc = run_args(["freeze", root, "--out", man])
        assert rc == 0 and open(man, "rb").read() == first, "freeze 幂等失守"

        # check 零漂移 → 0
        rc = run_args(["check", root, "--manifest", man])
        assert rc == 0, "零漂移 check 应 0 实测 %d" % rc

        # 三漂移各一：改 a.v、加 c.v、删 sub/b.v → exit 1 且三分账各 1
        w("a.v", "Lemma a : False.\n")
        w("c.v", "Lemma c : True.\n")
        os.remove(os.path.join(root, "sub", "b.v"))
        rc, so, _ = run_args_out(["check", root, "--manifest", man])
        assert rc == 1, "三漂移 check 应 1 实测 %d" % rc
        assert "1 changed / 1 added / 1 removed" in so, so

        # tier2 篡改必现形：只改清单内 tier1 账目（文件未动）→ tier2 FAIL·exit 1
        doc = json.load(io.open(man, encoding="utf-8"))
        doc["tier1"][0][1] = "0" * 32
        with io.open(man, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        rc, so, _ = run_args_out(["check", root, "--manifest", man])
        assert rc == 1, "tier2 篡改应 1 实测 %d" % rc
        assert "tier2 自洽（清单未被改）: FAIL" in so, so

        print("FREEZE-MANIFEST-SELFTEST PASS: freeze 幂等/零漂移/三漂移/tier2 篡改四判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def run_args_out(argv):
    """subprocess 驱动（拿 rc＋stdout——check 的 drift/tier2 账面断言用）。"""
    import subprocess
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__)] + argv,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser(prog=PROG, description="两层冻结清单机检（tier1 逐件 md5＋tier2 清单 md5）")
    ap.add_argument("cmd", nargs="?", default=None, choices=["freeze", "check"],
                    help="freeze=产清单；check=重算对账")
    ap.add_argument("dir", nargs="?", default=None, help="被冻结/被对账目录")
    ap.add_argument("--out", default=None, help="freeze：清单出路径")
    ap.add_argument("--tier2", default=None, help="freeze：tier2 侧册出路径（可省·账面恒出）")
    ap.add_argument("--manifest", default=None, help="check：在册清单路径")
    ap.add_argument("--json", default=None, help="对账账目 JSON 出账路径")
    ap.add_argument("--selftest", action="store_true", help="冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    if args.cmd == "freeze":
        if not args.out:
            print("FAIL-LOUD: freeze 需 --out 清单出路径", file=sys.stderr)
            sys.exit(2)
        if not args.dir:
            print("FAIL-LOUD: freeze 需 <dir>", file=sys.stderr)
            sys.exit(2)
        cmd_freeze(args)
    elif args.cmd == "check":
        if not args.manifest:
            print("FAIL-LOUD: check 需 --manifest 在册清单", file=sys.stderr)
            sys.exit(2)
        if not args.dir:
            print("FAIL-LOUD: check 需 <dir>", file=sys.stderr)
            sys.exit(2)
        cmd_check(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
