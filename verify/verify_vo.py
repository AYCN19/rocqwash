#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_vo.py — 通用逐件绿判四件套机检入口（rocqwash verify/·20261031 席 rqwash）

把战役验证工装 verify/_parse_fin_mac.py 的绿判四件套并查（check_four_piece·
_parse_fin_mac.py:82-108）泛化为 argv 驱动的逐件机检：给一对 (.v, .vo) 与可选的
编译旁证（--rc/--exit-file/--log），机械判定四件套并出逐件账：

  ①exit      ：编译退出码 == 0（--rc 直接给，或 --exit-file 读首行）；
  ②log       ：编译 log 零 Error 行（承 _parse_fin_mac.py:76 `"Error" in ln` 口径）；
  ③vo 魔数   ：.vo 前 8 字节 hex == 436f712100015ff4（--magic 可覆写）；
  ④vo 新鲜度 ：.vo mtime 严格新于 .v mtime（陈 vo＝假绿通道）。

诚实律落地：
  - 缺旁证的一件＝NOT-RUN（显式出账，绝不计绿）——但 ③④ 为必检核心对
    （--v/--vo 缺一即 exit 9），判词永不全免检；
  - 判词只认机检证据（魔数/退出码/mtime/行扫描），出 PASS/FAIL＋逐件状态表；
  - 源/产物 md5 双双出账（落盘对照口径）。

与 verify/ 目录既有两件（gate4_comment_guard.py / retrofit_gate7_irr.py·历史命名
未带 _ 前缀·战役工装）并存：`cli/rocqwash verify` 按 §5 契约「通用入口不唯一」
exit 4 列清单人工指认（其改名涉本轮冻结件，统一待办）；本件直接
`python3 verify/verify_vo.py` 调用，或经 examples Makefile 等显式指名调用。

用法：
  python3 verify/verify_vo.py --v <file.v> --vo <file.vo>
                              [--rc N | --exit-file F] [--log build.log]
                              [--magic HEX] [--json out.json] [--selftest]
  python3 verify/verify_vo.py --require-fresh <file.v> <file.vo>  # fresh-compile 防线

fresh-compile 防线（--require-fresh·本轮实战判例工具化②·20261101 入账）：
  divmod_gen 陈旧 vo 假绿判例的工具化——编译「成功过」≠「盘上 vo 就是这次编的」：
  世界里躺着一件带真魔数的旧 vo（或同名假绿残骸）时，只查魔数即假绿。防线双判
  （全过 rc=0 FRESH-OK；任一不过 rc=9 fail-loud 不模拟）：
    ① 新鲜度 ：.vo mtime 严格新于 .v mtime（承 ④ 口径·严格大于）；
    ② 魔数   ：.vo 头 8 字节 hex == 436f712100015ff4（Rocq 9.1 冻结口径——
      本机工具链 rocq 9.1.0 产物 _reproPC2/S01_BaseRing.vo 头 8 字节实证）。
  与四件套形互斥（--v/--vo 同给 → rc=2）；路径缺失 → rc=9（fail-loud 同律）。

退出码：0=PASS（已检各件全绿；--require-fresh 形=FRESH-OK）；1=FAIL（任一已检件
红）；2=用法错（--rc/--exit-file 互斥、--require-fresh 与 --v/--vo 互斥等）；
9=--v/--vo/--log/--exit-file 路径缺失；--require-fresh 形任一判不过亦 9
（fail-loud——陈 vo 假绿通道必须按缺件级硬错处理，不与普通 FAIL 混流）。
"""
import argparse
import hashlib
import io
import json
import os
import sys

VO_MAGIC_HEX = "436f712100015ff4"  # 承 _parse_fin_mac.py:28 冻结口径
PROG = "verify_vo"


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_four_piece(v_path, vo_path, rc=None, exit_file=None, log=None, magic=VO_MAGIC_HEX):
    """四件套并查——判据 1:1 承 _parse_fin_mac.py:82-108（＋log 零 Error 一件）。

    返回 (verdict_ok, pieces)；每件 status ∈ pass/fail/NOT-RUN。
    """
    pieces = {}
    ok = True

    # ① exit
    if rc is not None:
        pieces["exit"] = {"status": "pass" if rc == 0 else "fail", "value": rc,
                          "source": "--rc"}
        ok = ok and (rc == 0)
    elif exit_file is not None:
        if not os.path.isfile(exit_file):
            print("FAIL-LOUD: --exit-file 路径缺失: %s" % exit_file, file=sys.stderr)
            sys.exit(9)
        code = io.open(exit_file, encoding="utf-8", errors="replace").read().strip()
        code = code.splitlines()[0].strip() if code else ""
        good = (code == "0")
        pieces["exit"] = {"status": "pass" if good else "fail", "value": code,
                          "source": "--exit-file"}
        ok = ok and good
    else:
        pieces["exit"] = {"status": "NOT-RUN", "value": None, "source": None}

    # ② log 零 Error
    if log is not None:
        if not os.path.isfile(log):
            print("FAIL-LOUD: --log 路径缺失: %s" % log, file=sys.stderr)
            sys.exit(9)
        lines = io.open(log, encoding="utf-8", errors="replace").read().splitlines()
        errs = [ln for ln in lines if "Error" in ln]
        good = (len(errs) == 0)
        pieces["log_no_error"] = {"status": "pass" if good else "fail",
                                  "value": len(errs), "head": errs[:5],
                                  "source": log}
        ok = ok and good
    else:
        pieces["log_no_error"] = {"status": "NOT-RUN", "value": None, "source": None}

    # ③ vo 魔数（必检）
    with open(vo_path, "rb") as f:
        head = f.read(8)
    head_hex = head.hex()
    magic_ok = (head_hex == magic)
    pieces["vo_magic"] = {"status": "pass" if magic_ok else "fail",
                          "value": head_hex, "expect": magic}
    ok = ok and magic_ok

    # ④ vo 新鲜度（必检）——判据承 _parse_fin_mac.py:95（严格大于）
    fresh = os.path.getmtime(vo_path) > os.path.getmtime(v_path)
    pieces["vo_fresher_than_v"] = {"status": "pass" if fresh else "fail",
                                   "value": [os.path.getmtime(v_path), os.path.getmtime(vo_path)]}
    ok = ok and fresh

    return ok, pieces


def require_fresh(v_path, vo_path):
    """fresh-compile 防线（divmod_gen 陈旧 vo 假绿判例工具化）：双判并查。

    ① .vo mtime 严格新于 .v；② .vo 头 8 字节 = VO_MAGIC_HEX（9.1 冻结口径）。
    全过 → 出账 FRESH-OK rc=0；任一不过 → FAIL-LOUD 逐件出账 rc=9（fail-loud
    不模拟——陈 vo 假绿通道按缺件级硬错处理）。
    """
    ok = True
    with open(vo_path, "rb") as f:
        head_hex = f.read(8).hex()
    magic_ok = (head_hex == VO_MAGIC_HEX)
    if not magic_ok:
        print("FAIL-LOUD: vo 魔数非 %s（实得 %s）——非本链编译产物（陈 vo/残骸·"
              "divmod_gen 假绿判例通道）" % (VO_MAGIC_HEX, head_hex), file=sys.stderr)
        ok = False
    fresh = os.path.getmtime(vo_path) > os.path.getmtime(v_path)
    if not fresh:
        print("FAIL-LOUD: vo mtime (%.3f) 不新于 v mtime (%.3f)——陈 vo 假绿通道"
              % (os.path.getmtime(vo_path), os.path.getmtime(v_path)), file=sys.stderr)
        ok = False
    print("REQUIRE-FRESH v=%s vo=%s magic=%s fresh=%s md5 v=%s vo=%s"
          % (v_path, vo_path, "PASS" if magic_ok else "FAIL",
             "PASS" if fresh else "FAIL", md5_of(v_path), md5_of(vo_path)))
    if not ok:
        print("FRESH-REJECT: 防线拦下（rc=9 fail-loud）", file=sys.stderr)
        sys.exit(9)
    print("FRESH-OK: vo 新鲜（mtime 严格新于 .v）且 9.1 魔数在头——fresh-compile 坐实")
    sys.exit(0)


def selftest():
    """内嵌冻结向量组（临时目录驱动）：魔数正/负·新鲜度负·log 双判·exit 双判·
    互斥用法·--require-fresh 防线四判（正/陈 vo 拦/坏魔数拦/与 --v 互斥）。"""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="rocqwash_verifyvo_self_")
    try:
        v = os.path.join(tmp, "probe.v")
        vo = os.path.join(tmp, "probe.vo")
        with io.open(v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma t : True.\nProof. exact I. Qed.\n")
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(VO_MAGIC_HEX) + b"\x00JUNK")

        # 正判：魔数对＋新鲜 → PASS（exit/log 缺席＝NOT-RUN 不计绿也不计红）
        rc = run_args(["--v", v, "--vo", vo])
        assert rc == 0, "魔数正判应 0 实测 %d" % rc

        # 负判①：坏魔数
        with open(vo, "wb") as f:
            f.write(b"\xde\xad\xbe\xef\x00\x01\x02\x03")
        rc = run_args(["--v", v, "--vo", vo])
        assert rc == 1, "坏魔数应 1 实测 %d" % rc

        # 负判②：陈 vo（v 拨到未来）
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(VO_MAGIC_HEX))
        stale = os.path.getmtime(vo) + 50
        os.utime(v, (stale, stale))
        rc = run_args(["--v", v, "--vo", vo])
        assert rc == 1, "陈 vo 应 1 实测 %d" % rc
        os.utime(v, None)
        with open(vo, "wb") as f:  # 重写 vo 保证新鲜（负判②的残效清账）
            f.write(bytes.fromhex(VO_MAGIC_HEX))

        # log 双判：带 Error 行 → 1；净 log → 0
        logbad = os.path.join(tmp, "bad.log")
        with io.open(logbad, "w", encoding="utf-8") as fh:
            fh.write("coqc ok\nError: foo\n")
        rc = run_args(["--v", v, "--vo", vo, "--log", logbad])
        assert rc == 1, "脏 log 应 1 实测 %d" % rc
        logok = os.path.join(tmp, "ok.log")
        with io.open(logok, "w", encoding="utf-8") as fh:
            fh.write("coqc ok\n")
        rc = run_args(["--v", v, "--vo", vo, "--log", logok])
        assert rc == 0, "净 log 应 0 实测 %d" % rc

        # exit 双判：--rc 2 → 1；--exit-file "0" → 0
        rc = run_args(["--v", v, "--vo", vo, "--rc", "2"])
        assert rc == 1, "--rc 2 应 1 实测 %d" % rc
        ef = os.path.join(tmp, "rc.txt")
        with io.open(ef, "w", encoding="utf-8") as fh:
            fh.write("0\n")
        rc = run_args(["--v", v, "--vo", vo, "--exit-file", ef])
        assert rc == 0, "--exit-file 0 应 0 实测 %d" % rc

        # 用法反判：--rc 与 --exit-file 互斥 → 2；缺 vo → 9
        rc = run_args(["--v", v, "--vo", vo, "--rc", "0", "--exit-file", ef])
        assert rc == 2, "互斥应 2 实测 %d" % rc
        rc = run_args(["--v", v, "--vo", os.path.join(tmp, "gone.vo")])
        assert rc == 9, "缺 vo 应 9 实测 %d" % rc

        # --require-fresh 防线四判（divmod_gen 陈旧 vo 假绿判例工具化）
        # 正判：魔数对＋新鲜 → 0 FRESH-OK
        rc = run_args(["--require-fresh", v, vo])
        assert rc == 0, "require-fresh 正判应 0 实测 %d" % rc
        # 负判①：陈 vo（v 拨到未来）→ 9 fail-loud
        stale = os.path.getmtime(vo) + 50
        os.utime(v, (stale, stale))
        rc = run_args(["--require-fresh", v, vo])
        assert rc == 9, "require-fresh 陈 vo 应 9 实测 %d" % rc
        os.utime(v, None)
        # 负判②：坏魔数（新鲜但非本链产物）→ 9
        with open(vo, "wb") as f:
            f.write(b"\xde\xad\xbe\xef\x00\x01\x02\x03")
        rc = run_args(["--require-fresh", v, vo])
        assert rc == 9, "require-fresh 坏魔数应 9 实测 %d" % rc
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(VO_MAGIC_HEX))
        # 用法反判③：与 --v/--vo 互斥 → 2；缺 vo → 9
        rc = run_args(["--require-fresh", v, vo, "--v", v])
        assert rc == 2, "require-fresh 与 --v 互斥应 2 实测 %d" % rc
        rc = run_args(["--require-fresh", v, os.path.join(tmp, "gone.vo")])
        assert rc == 9, "require-fresh 缺 vo 应 9 实测 %d" % rc

        print("VERIFY-VO-SELFTEST PASS: 魔数正负/陈vo负/log双判/exit双判/互斥/缺件/"
              "require-fresh防线四判 十三判全过")
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


def main():
    ap = argparse.ArgumentParser(prog=PROG, description="通用逐件绿判四件套机检（.v/.vo 对）")
    ap.add_argument("--v", default=None, help="源 .v 路径")
    ap.add_argument("--vo", default=None, help="编译产物 .vo 路径")
    ap.add_argument("--rc", type=int, default=None, help="编译退出码（与 --exit-file 互斥）")
    ap.add_argument("--exit-file", default=None, help="存退出码的文件（首行；与 --rc 互斥）")
    ap.add_argument("--log", default=None, help="编译 log（零 Error 行机检）")
    ap.add_argument("--magic", default=VO_MAGIC_HEX, help="期望魔数（默认冻结口径）")
    ap.add_argument("--require-fresh", nargs=2, default=None,
                    metavar=("<file.v>", "<file.vo>"),
                    help="fresh-compile 防线：.vo mtime 严格新于 .v 且头 8 字节="
                         "436f712100015ff4（9.1 魔数），否则 rc=9 fail-loud"
                         "（divmod_gen 陈旧 vo 假绿判例工具化）")
    ap.add_argument("--json", default=None, help="逐件账 JSON 出账路径")
    ap.add_argument("--selftest", action="store_true", help="内嵌冻结向量组自证")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.selftest:
        sys.exit(selftest())

    # fresh-compile 防线形（--require-fresh·独立于四件套 --v/--vo 形·互斥）
    if args.require_fresh:
        if args.v or args.vo:
            print("FAIL-LOUD: --require-fresh 与 --v/--vo 互斥（两形不可混用）",
                  file=sys.stderr)
            sys.exit(2)
        v_f, vo_f = args.require_fresh
        for label, path in (("--require-fresh <v>", v_f),
                            ("--require-fresh <vo>", vo_f)):
            if not os.path.isfile(path):
                print("FAIL-LOUD: %s 路径缺失: %s" % (label, path), file=sys.stderr)
                sys.exit(9)
        require_fresh(v_f, vo_f)

    if not args.v or not args.vo:
        ap.error("--v 与 --vo 必填（--selftest/--require-fresh 除外）")

    if args.rc is not None and args.exit_file is not None:
        print("FAIL-LOUD: --rc 与 --exit-file 互斥", file=sys.stderr)
        sys.exit(2)
    for label, path in (("--v", args.v), ("--vo", args.vo)):
        if not os.path.isfile(path):
            print("FAIL-LOUD: %s 路径缺失: %s" % (label, path), file=sys.stderr)
            sys.exit(9)

    ok, pieces = check_four_piece(args.v, args.vo, rc=args.rc, exit_file=args.exit_file,
                                  log=args.log, magic=args.magic)
    print("== verify_vo 四件套账（v=%s）==" % os.path.basename(args.v))
    for name, p in pieces.items():
        print("  %-18s %-8s %s" % (name, p["status"], p.get("value", "")))
    print("md5 v=%s vo=%s" % (md5_of(args.v), md5_of(args.vo)))
    print("VERDICT: %s" % ("PASS" if ok else "FAIL"))

    if args.json:
        acc = {"v": args.v, "vo": args.vo, "pieces": pieces,
               "verdict": "PASS" if ok else "FAIL",
               "md5": {"v": md5_of(args.v), "vo": md5_of(args.vo)}}
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, ensure_ascii=False, indent=1)
        print("json ->", args.json)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
