#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frozen8.py — certify 收口件：在役八组件冻结名单机检（rocqwash certify/·20261031 席 rqadapt）

缺口闭合：八件冻结口径 md5 表此前只存在于更新账.md 文档（§三「在役八组件冻结
自证」两轮在册），无机械对账在跑。本件把「文档表」变「机械账」——账载八值入
常量，以冻结件 freeze_manifest 的 v1 冻结机（tier1/tier2 口径）对八件正本出冻结名
单供推送轮对账；check 随认证套件在跑（tests/run_tests.sh t_frozen8*），推送轮
c4 套件绿即含八件对账绿。

与冻结件关系：certify/freeze_manifest.py 在役冻结禁改——本件零改动，只读 import
其 md5_bytes/tier1_lines 口径函数（tier2_of 承 v1「tier1 账文 md5」两层冻结语义；
push_gate.py 同款并存形·适配一律新文件）。名单 schema 自立门户
（rocqwash-frozen8-manifest/1）：误喂 v1 `check` 即 schema 不识 exit 2——口径分家
fail-closed，八件对账只走本件。

推送轮对账用法（certify 收口后·名单与侧册已随仓在册）：
  python3 certify/frozen8.py check --list certify/frozen8_manifest.json \
        --tier2 certify/frozen8_tier2.md5        # rc 0＝八件正本零漂移
  注：push_gate window c4 的 --freeze-manifest 形参走 v1 整仓清单；八件对账走本件。

命令：
  python3 certify/frozen8.py freeze [--repo DIR] --out LIST.json [--tier2 T2.md5]
      现盘八件逐件 md5 对照账载——全等方出名单（v1 形制：tier1 恰八行·relpath 排
      序·tier2=tier1 账文 md5·幂等重放逐字节恒同）；任一件漂移/缺失即 fail-closed
      拒绝出名单（rc 1·禁漂移洗账）。
  python3 certify/frozen8.py check [--repo DIR] --list LIST.json [--tier2 T2.md5]
        [--json OUT]
      四环咬合对账：①名单 tier2 自洽（动名单即现形）→ ②名单口径≡账载（名单非
      账载口径即漂移）→ ③tier2 侧册咬合（给了 --tier2 才咬·外置在册动侧册即现形）
      → ④现盘八件重算对照账载（changed/removed 逐件出账·八件制宇宙 added 恒无）。
      全咬合 exit 0；任一环破 exit 1；名单畸形 exit 2。
  python3 certify/frozen8.py --ledger   打印账载八行（`md5  relpath`·与更新账 §三同形）
  python3 certify/frozen8.py --selftest 账载四判自证（见下）

--selftest 账载四判（全部以账载常量为锚·对真仓只读）：
  判① 账载≡文档：机械收割更新账.md 内八件 relpath 的全部在册 md5 行（多表逐行
      收割·同件多值即账文档自矛盾），八件各见且与账载常量逐件全等——常量不漂于
      文档（文档表→机械账的正身）。
  判② 盘≡账：现盘八件逐件重算 md5 与账载全等（8/8）——文档口径首获盘面机证。
  判③ 名单≡账·幂等：freeze 产名单 tier1/tier2 与账载逐字咬合＋侧册同值；同盘面
      重产名单逐字节恒同。
  判④ 对账闭环·篡改现形：check 名单 rc=0；临时拷贝名单改一件 md5 → tier2 FAIL＋
      口径 FAIL rc=1；侧册篡改 → 咬合 FAIL rc=1——对账器真咬合，非橡皮图章。

诚实律（承 CONTRIBUTING §0，一票否决）：
  - 只认机械证据（退出码/md5/逐字节恒同），不出「未动过」口头判词——check 只出
    重算三分账，四环咬合是判定，不是保证；
  - fail-closed：盘≠账载拒出名单；名单缺件/畸形/口径不符一律非零＋响亮输出；
  - 幂等可重放：freeze 无时间戳无环境噪声，同盘面重产逐字节恒同。

写域声明：本器只写调用方显式指认的 --out/--tier2/--json 出路径，不碰仓库树其余
字节；selftest 只写 mkdtemp 临时目录（测毕即删）；全器零编译零网络。

退出码：freeze 0=成／1=盘≠账载拒出名单／2=用法错／9=路径缺失；
check 0=零漂移／1=有漂移／2=名单畸形／9=名单或侧册缺失；
--ledger 0；--selftest 0=四判绿／1=有判红（断言响亮）。
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

PROG = "frozen8"
SCHEMA = "rocqwash-frozen8-manifest/1"
LEDGER_DOC = "更新账.md"

# 账载八件（更新账.md §三「在役八组件冻结自证」两轮在册同值·20261031 席 rqadapt 抄册·
# relpath 排序=v1 tier1 同序）。八件在役冻结禁改；口径换代（解禁重冻）须随账文档
# 换代本常量——判① 会把文档与常量的任何脱钩当场现形。
LEDGER8 = (
    ("certify/freeze_manifest.py", "f5eeea458616e24f9867c074c954d267"),
    ("names/mac_stmt_names.py", "01dc635ce445b05628bdd6e728990ce3"),
    ("scan/mac_stmt_scan.py", "56ff0fb371f9684cc865023f6f5d0f4a"),
    ("seam/seam_probe.py", "7a01359a22b8960b352191f1a4490b37"),
    ("tools/cpu_guard.sh", "9c5392d6746260f7852fea6f8992fd52"),
    ("verify/gate4_comment_guard.py", "d7ab397c5f0243d0c7320f91d0f14481"),
    ("verify/verify_vo.py", "81524ed04c2fc7e82a4547972baa7b83"),
    ("wash/wash_engine.py", "664446bc717395d8496c8c30a5af9ccf"),
)
LEDGER_MAP = dict(LEDGER8)  # rel -> md5

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
try:
    import freeze_manifest as _v1  # noqa: E402  （在役冻结件·只 import 不改）
except Exception as _e:  # pragma: no cover
    print("FAIL-LOUD: 冻结同侪 certify/freeze_manifest.py 不可导入: %s" % _e,
          file=sys.stderr)
    sys.exit(9)

DEFAULT_REPO = os.path.dirname(_HERE)
MD5_LINE = re.compile(r"^([0-9a-f]{32})[ \t]+(\S+)[ \t]*$")


def run_out(argv):
    """子进程跑一条命令→(rc, stdout, stderr)。argv 直传零外壳注入。"""
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def disk_md5(repo, rel):
    """单件现盘 md5；正本缺失返回 None（不掩饰）。"""
    fp = os.path.join(repo, rel.replace("/", os.sep))
    if not os.path.isfile(fp):
        return None
    with open(fp, "rb") as f:
        return _v1.md5_bytes(f.read())


def disk_rows(repo):
    """现盘八件逐件 [(rel, md5|None)]（账载序）。"""
    return [(rel, disk_md5(repo, rel)) for rel, _ in LEDGER8]


def harvest_ledger_doc(repo):
    """判① 机械收割：账文档中八件 relpath 的全部在册 md5 行。
    返回 (doc_map, problems)——同件多值矛盾/八件缺收/文档缺失均入 problems。"""
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
            if rel not in LEDGER_MAP:  # 只收八件在册行·他件 md5 表不涉本判
                continue
            if rel in doc_map and doc_map[rel] != md5:
                problems.append("账文档内 %s 两值矛盾: %s vs %s"
                                % (rel, doc_map[rel], md5))
            doc_map.setdefault(rel, md5)
    missing = [rel for rel in LEDGER_MAP if rel not in doc_map]
    if missing:
        problems.append("账文档未见八件在册值: %s" % ", ".join(missing))
    return doc_map, problems


# ---------------- freeze：账载口径出冻结名单 ----------------

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
    if drifts:
        print("frozen8 freeze FAIL: 现盘八件≠账载（%d 件漂移）——拒出名单"
              "（fail-closed·禁漂移洗账）" % len(drifts))
        for d in drifts:
            print("  " + d)
        sys.exit(1)
    t2 = _v1.tier2_of(rows)
    doc = {"schema": SCHEMA, "root": repo,
           "ledger_source": LEDGER_DOC + " §三（在役八组件冻结自证·账载口径）",
           "n_files": len(rows), "tier1": [[r, m] for r, m in rows],
           "tier2_md5_of_tier1_text": t2}
    for path in [args.out] + ([args.tier2] if args.tier2 else []):
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(parent):
            print("FAIL-LOUD: 出路径父目录缺失: %s" % parent, file=sys.stderr)
            sys.exit(2)
    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("frozen8 freeze: 现盘八件≡账载（8/8 全等）——名单入册")
    for r, m in rows:
        print("  %s  %s" % (m, r))
    print("tier2=%s（tier1 账文 md5·两层冻结承 v1 口径）" % t2)
    if args.tier2:
        with io.open(args.tier2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t2 + "\n")
        print("tier2 侧册 ->", args.tier2)
    # 幂等自证：同盘面重产与在盘名单逐字节对照
    with io.open(args.out, encoding="utf-8", newline="") as fh:
        first = fh.read()
    again = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert first == again, "freeze 幂等自证失败（名单非确定性）"
    print("idempotent replay: 名单重产逐字节恒同 PASS")
    print("freeze OK: 名单 -> %s（供推送轮对账：check --list %s）" % (args.out, args.out))
    sys.exit(0)


# ---------------- check：四环咬合对账 ----------------

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
        tier1 = doc["tier1"]
        if (not isinstance(tier1, list) or len(tier1) != len(LEDGER8)
                or not all(isinstance(r, list) and len(r) == 2
                           and all(isinstance(x, str) for x in r) for r in tier1)):
            raise ValueError("tier1 须为 %d 行 [rel, md5]" % len(LEDGER8))
    except Exception as e:
        print("FAIL-LOUD: 名单畸形: %s" % e, file=sys.stderr)
        sys.exit(2)

    drift = False
    # 环① 名单 tier2 自洽（v1 口径：tier1 账文 md5——动名单即现形）
    t2_now = _v1.tier2_of([tuple(r) for r in doc["tier1"]])
    t2_ok = (t2_now == doc.get("tier2_md5_of_tier1_text"))
    print("名单 tier2 自洽（名单未被改）: %s" % ("PASS" if t2_ok else "FAIL"))
    drift = drift or not t2_ok
    # 环② 名单口径≡账载（名单非账载口径即漂移——防外来/换代旧名单蒙混）
    list_map = {r: m for r, m in doc["tier1"]}
    ledger_bad = []
    for rel, m in LEDGER8:
        if rel not in list_map:
            ledger_bad.append("DRIFT removed  名单缺在册件 %s" % rel)
        elif list_map[rel] != m:
            ledger_bad.append("DRIFT ledger   %s 名单 %s ≠ 账载 %s"
                              % (rel, list_map[rel], m))
    for rel in sorted(set(list_map) - set(LEDGER_MAP)):
        ledger_bad.append("DRIFT added    名单多出非八件 %s" % rel)
    print("名单口径≡账载（八件 in 册）: %s" % ("PASS" if not ledger_bad else "FAIL"))
    for b in ledger_bad:
        print("  " + b)
    drift = drift or bool(ledger_bad)
    # 环③ tier2 侧册咬合（外置在册·给了才咬）
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
    # 环④ 现盘八件重算对照账载（八件制宇宙：changed/removed·added 恒无）
    changed, removed = [], []
    for rel, md5_now in disk_rows(repo):
        if md5_now is None:
            removed.append(rel)
            print("  DRIFT removed  %s（正本缺失）" % rel)
        elif md5_now != LEDGER_MAP[rel]:
            changed.append(rel)
            print("  DRIFT changed  %s（现盘 %s ≠ 账载 %s）"
                  % (rel, md5_now, LEDGER_MAP[rel]))
    legs = "tier2 自洽/名单≡账载/盘≡账载" + ("/侧册" if args.tier2 else "")
    print("frozen8 check %s: %s · %d changed / %d removed"
          % ("OK" if not drift else "FAIL", legs, len(changed), len(removed)))
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"schema": SCHEMA, "repo": repo, "list": args.list,
                       "tier2_ok": t2_ok, "ledger_ok": not ledger_bad,
                       "side_ok": side_ok, "changed": changed,
                       "removed": removed,
                       "verdict": "PASS" if not drift else "FAIL"},
                      fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    sys.exit(1 if drift else 0)


# ---------------- --selftest：账载四判（真仓只读·临时目录落笔） ----------------

def selftest():
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_frozen8_self_")
    try:
        repo = DEFAULT_REPO
        me = os.path.abspath(__file__)

        # 判① 账载≡文档（机械收割·常量不漂于文档）
        doc_map, problems = harvest_ledger_doc(repo)
        assert not problems, "判① 账载≡文档红: %s" % "; ".join(problems)
        for rel, m in LEDGER8:
            assert doc_map.get(rel) == m, \
                "判① 账载≡文档红: %s 文档 %r ≠ 账载 %s" % (rel, doc_map.get(rel), m)
        print("判① 账载≡文档 PASS: %s 八件在册值逐件咬合（收割 %d/8 件）"
              % (LEDGER_DOC, len(doc_map)))

        # 判② 盘≡账（文档口径首获盘面机证）
        for rel, md5_now in disk_rows(repo):
            assert md5_now == LEDGER_MAP[rel], \
                "判② 盘≡账红: %s 现盘 %s ≠ 账载 %s" % (rel, md5_now, LEDGER_MAP[rel])
        print("判② 盘≡账 PASS: 现盘八件逐件 md5 与账载全等（8/8）")

        # 判③ 名单≡账·幂等（子进程驱动·-B 禁 __pycache__）
        lst = os.path.join(tmp, "f8.json")
        side = os.path.join(tmp, "f8.t2")
        rc, so, se = run_out([sys.executable, "-B", me, "freeze",
                              "--out", lst, "--tier2", side])
        assert rc == 0, "判③ freeze 应 0 实测 %d\n%s%s" % (rc, so, se)
        doc = json.load(io.open(lst, encoding="utf-8"))
        assert doc["tier1"] == [list(r) for r in LEDGER8], "判③ 名单 tier1 ≠ 账载"
        assert doc["tier2_md5_of_tier1_text"] == _v1.tier2_of(LEDGER8), \
            "判③ 名单 tier2 ≠ v1 口径"
        with io.open(side, encoding="utf-8") as fh:
            assert fh.read().strip() == doc["tier2_md5_of_tier1_text"], \
                "判③ 侧册 ≠ 名单 tier2"
        first = open(lst, "rb").read()
        rc, so, se = run_out([sys.executable, "-B", me, "freeze", "--out", lst])
        assert rc == 0 and open(lst, "rb").read() == first, \
            "判③ 幂等失守\n%s%s" % (so, se)
        print("判③ 名单≡账·幂等 PASS: freeze 名单 tier1/tier2 与账载逐字咬合·"
              "重产逐字节恒同")

        # 判④ 对账闭环·篡改现形（对账器真咬合）
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", lst, "--tier2", side])
        assert rc == 0 and "frozen8 check OK" in so, \
            "判④ 零漂移 check 应 0\n%s%s" % (so, se)
        bad = json.load(io.open(lst, encoding="utf-8"))
        bad["tier1"][0][1] = "0" * 32  # 名单内 md5 篡改（tier2 未随改）
        bad_path = os.path.join(tmp, "bad.json")
        with io.open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(bad, fh)
        rc, so, se = run_out([sys.executable, "-B", me, "check", "--list", bad_path])
        assert rc == 1, "判④ 名单篡改应 1 实测 %d\n%s%s" % (rc, so, se)
        assert "名单 tier2 自洽（名单未被改）: FAIL" in so, so
        assert "名单口径≡账载（八件 in 册）: FAIL" in so, so
        side_bad = os.path.join(tmp, "side_bad.t2")
        with io.open(side_bad, "w", encoding="utf-8") as fh:
            fh.write("0" * 32 + "\n")
        rc, so, se = run_out([sys.executable, "-B", me, "check",
                              "--list", lst, "--tier2", side_bad])
        assert rc == 1 and "tier2 侧册咬合: FAIL" in so, \
            "判④ 侧册篡改应现形\n%s%s" % (so, se)
        print("判④ 对账闭环·篡改现形 PASS: 零漂移 rc=0；名单 md5 篡改→tier2+口径 "
              "FAIL rc=1；侧册篡改→咬合 FAIL rc=1")

        print("FROZEN8-SELFTEST PASS: 账载四判绿（账载≡文档/盘≡账/名单≡账·幂等/"
              "对账闭环·篡改现形）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(
        prog=PROG,
        description="在役八组件冻结名单机检（账载口径·v1 冻结机只读复用）")
    sub = ap.add_subparsers(dest="cmd")
    fz = sub.add_parser("freeze", help="八件正本对照账载出冻结名单（漂移拒出）")
    fz.add_argument("--repo", default=None, help="仓库根（默认本件所在仓）")
    fz.add_argument("--out", default=None, help="名单出路径")
    fz.add_argument("--tier2", default=None, help="tier2 侧册出路径（可省·账面恒出）")
    ck = sub.add_parser("check", help="四环咬合对账（名单自洽→≡账载→[侧册]→盘≡账载）")
    ck.add_argument("--repo", default=None, help="仓库根（默认本件所在仓）")
    ck.add_argument("--list", default=None, help="在册冻结名单路径")
    ck.add_argument("--tier2", default=None, help="tier2 侧册（可省·给了就咬合）")
    ck.add_argument("--json", default=None, help="对账账目 JSON 出账路径")
    ap.add_argument("--ledger", action="store_true",
                    help="打印账载八行（md5  relpath·与更新账 §三同形）")
    ap.add_argument("--selftest", action="store_true", help="账载四判自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())
    if args.ledger:
        for r, m in LEDGER8:
            print("%s  %s" % (m, r))
        sys.exit(0)
    if args.cmd == "freeze":
        cmd_freeze(args)
    elif args.cmd == "check":
        cmd_check(args)
    else:
        ap.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
