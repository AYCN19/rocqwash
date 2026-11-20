#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""scan_station.py — scan/mac_stmt_scan.py 正本指认包装（rocqwash wrapper/·Mac 适配席 rqadapt·20261031）

在役组件 scan/mac_stmt_scan.py 冻结禁改（嵌记 md5 见 PINNED_MD5·各在飞席位实时引用）——
本席适配一律新文件落 wrapper/，本包装即正本指认站（canonical identification station）：

  1. 指认：定位并出示正本（绝对路径＋md5＋字节数＋嵌记 pin 比对）。指认只证「哪份是
     正本」，不背书任何扫描判词——扫描口径仍以正本为准（报清单不报清白口径原样继承）。
  2. 断言（可附）：--expect-md5 <hex>（外部附断言·可重复·全部须等）／--check-pin
     （比对适配时嵌记 PINNED_MD5）。断言失败 exit 2，绝不带病透传。
  3. 透传：站级旗标之外的一切参数逐字原序转发 `python3 -B scan/mac_stmt_scan.py`，
     退出码原样传播（fail-loud，不改写——对齐 cli/rocqwash 路由契约）。

站级旗标（本包装自留·不转发）：
  --root DIR         正本仓根（默认＝本包装文件所在仓根；缺目录参数 exit 2）
  --identify         只出指认卡不透传（断言过 exit 0／败 exit 2）
  --expect-md5 HEX   外部 md5 断言（可重复·32 位 hex）
  --check-pin        嵌记断言（PINNED_MD5·20261031 适配时实测）
  --station-selftest 本包装自身自检（七判·零写盘·不动正本）
  -h / --help        本站帮助（正本帮助经 `scan_station -- --help` 可达）

正本自有旗标（--file/--json/--manifest/--hits-csv/--baseline/--selftest）全数透传；
`--` 之后的参数（含站级字样）亦全数透传（显式转发边界）。
裸调（零参数）＝出指认卡不透传。

退出码：0=过；2=断言失败/站级用法错；9=正本缺失；其余＝正本口径透传
（正本 --selftest 向量失败 exit 2、--file 靶缺失 exit 9 等原样可达）。

幂等律：本包装零写盘——不写正本、不写仓、不写临时（run_tests.sh 幂等口径兼容；
smoke 验证输出由调用者显式指定到自席沙箱）。
"""
import hashlib
import io
import os
import subprocess
import sys

WRAP_NAME = "wrapper/scan_station.py"
CANONICAL_REL = "scan/mac_stmt_scan.py"

# 嵌记（pin）＝20261031 适配席 rqadapt 对正本实测的 md5——正本若经冻终权威改版，
# 须由适配席对实盘重嵌记，本包装不擅改正本也不擅改嵌记以外的任何在役件。
PINNED_MD5 = "56ff0fb371f9684cc865023f6f5d0f4a"
PINNED_NOTE = "20261031 rqadapt 适配时嵌记"


def _clean_mode():
    # Clean mode (ROCWASH_CLEAN=1) declares the canonical environment absent:
    # canonical-dependency faces report "requires canonical environment" and
    # refuse instead of probing (docs/clean-mode-manual-20261114.md). Default
    # (env unset) keeps historical behavior byte-identical.
    return os.environ.get("ROCWASH_CLEAN", "").strip() == "1"

STATION_USAGE = """scan_station — scan/mac_stmt_scan.py 正本指认包装（wrapper/）

用法 Usage:
  python3 wrapper/scan_station.py [站级旗标] [透传给正本的参数...]

站级旗标 Station flags:
  --root DIR         正本仓根（默认＝本包装所在仓根）
  --identify         只出指认卡，不透传
  --expect-md5 HEX   md5 断言（可重复·全部须等·败则 exit 2 不透传）
  --check-pin        比对嵌记 PINNED_MD5
  --station-selftest 本包装自检（七判）
  -h / --help        本帮助

透传 Pass-through: 其余参数逐字原序转发 python3 -B scan/mac_stmt_scan.py；
  正本 --file/--json/--manifest/--hits-csv/--baseline/--selftest 照常用；
  `--` 之后全数透传（含站级字样）。例：
    python3 wrapper/scan_station.py --selftest
    python3 wrapper/scan_station.py --file x.v --json out.json
    python3 wrapper/scan_station.py --check-pin --file x.v
    python3 wrapper/scan_station.py -- --help        # 正本帮助

退出码: 0=过  2=断言败/站级用法错  9=正本缺失  其余=正本口径透传
"""


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def default_root():
    """默认正本仓根＝本包装文件的上上级目录（wrapper/ 的父目录）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_canonical(root):
    """指认正本：root/scan/mac_stmt_scan.py 存在则返回绝对路径，否则 None。"""
    if not root:
        return None
    p = os.path.join(os.path.abspath(root), *CANONICAL_REL.split("/"))
    return p if os.path.isfile(p) else None


def split_station_args(argv):
    """站级旗标剥离；其余逐字原序保留（1:1 透传 faithfulness）。

    返回 (station, forwarded)。--root/--expect-md5 缺值 raise ValueError（站级用法错）。
    """
    st = dict(root=None, identify=False, expect_md5=[], check_pin=False,
              help=False, selftest=False)
    fwd = []
    i, n = 0, len(argv)
    while i < n:
        a = argv[i]
        if a == "--":
            fwd.extend(argv[i:])          # 显式转发边界：之后全数透传
            break
        if a in ("-h", "--help"):
            st["help"] = True; i += 1; continue
        if a == "--identify":
            st["identify"] = True; i += 1; continue
        if a == "--check-pin":
            st["check_pin"] = True; i += 1; continue
        if a == "--station-selftest":
            st["selftest"] = True; i += 1; continue
        if a == "--root" or a.startswith("--root="):
            if "=" in a:
                st["root"] = a.split("=", 1)[1]
            else:
                i += 1
                if i >= n:
                    raise ValueError("--root 需要目录参数")
                st["root"] = argv[i]
            i += 1; continue
        if a == "--expect-md5" or a.startswith("--expect-md5="):
            if "=" in a:
                st["expect_md5"].append(a.split("=", 1)[1])
            else:
                i += 1
                if i >= n:
                    raise ValueError("--expect-md5 需要断言值（32 位 hex）")
                st["expect_md5"].append(argv[i])
            i += 1; continue
        fwd.append(a); i += 1
    return st, fwd


def norm_hex(s):
    """断言值形制核：剥空白/引号、小写；非 32 位 hex 回 None（断言形制非法）。"""
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def assert_md5(actual, expects, check_pin):
    """md5 断言核：expects 全部须等（＋可选嵌记）；回 (ok, [(want, match), ...])。"""
    wants = []
    for e in expects:
        v = norm_hex(e)
        if v is None:
            wants.append((e, False))
        else:
            wants.append((v, v == actual))
    if check_pin:
        wants.append((PINNED_MD5, PINNED_MD5 == actual))
    ok = all(m for _, m in wants)
    return ok, wants


def station_card(canonical, actual, expects, check_pin, forward_argv=None):
    """指认卡行列（纯文本·不落盘）。forward_argv=None 表未透传（--identify）。"""
    ok, wants = assert_md5(actual, expects, check_pin)
    lines = []
    lines.append("== scan_station 正本指认卡（%s）==" % WRAP_NAME)
    lines.append("canonical: %s" % canonical)
    lines.append("md5:       %s" % actual)
    lines.append("bytes:     %d" % os.path.getsize(canonical))
    lines.append("pin:       %s（%s）" % (PINNED_MD5, PINNED_NOTE))
    lines.append("pin_match: %s" % (PINNED_MD5 == actual))
    if wants:
        for (w, m) in wants:
            lines.append("expect-md5: %s → match=%s" % (w, m))
    else:
        lines.append("expect-md5: （无附断言）")
    lines.append("frozen:    正本冻结禁改——本站只指认＋透传，禁写正本")
    if forward_argv is None:
        lines.append("dispatch:  未透传（--identify）")
    else:
        lines.append("dispatch:  -> python3 -B %s %s" % (canonical, " ".join(forward_argv)))
    lines.append("verdict:   %s" % ("PASS" if ok else "FAIL（md5 断言不符·不带病透传）"))
    return lines, ok


def station_selftest():
    """本包装自身自检（七判·零写盘·不动正本）。回 pass 布尔。"""
    ok = True
    root = default_root()

    # 判1 md5_of 与 md5_bytes 同源一致（对象＝本包装自身·零写盘）
    v1 = md5_of(os.path.abspath(__file__))
    with io.open(os.path.abspath(__file__), "rb") as f:
        v2 = md5_bytes(f.read())
    j = (v1 == v2)
    print("  judge1 md5_of==md5_bytes(__file__):", "PASS" if j else "FAIL")
    ok = ok and j

    # 判2 默认仓根指认正本在位
    c = find_canonical(root)
    j = (c is not None and os.path.isfile(c)
         and os.path.relpath(c, root).replace(os.sep, "/") == CANONICAL_REL)
    print("  judge2 find_canonical(default_root) 在位:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判3 混排转发保序：站级旗标剥离·余者逐字原序
    st, fwd = split_station_args(["--file", "x.v", "--check-pin", "--json", "o.json", "y"])
    j = (st["check_pin"] is True and st["identify"] is False
         and fwd == ["--file", "x.v", "--json", "o.json", "y"])
    print("  judge3 混排剥离保序:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # 判4 inline 形制 --root=X 不透传
    st, fwd = split_station_args(["--root=/tmp/x", "--file", "x.v"])
    j = (st["root"] == "/tmp/x" and fwd == ["--file", "x.v"])
    print("  judge4 --root=X inline 剥离:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # 判5 `--` 边界：其后（含站级字样）全数透传且逐字不增不减
    tail = ["--", "--identify", "--file", "x.v"]
    _, fwd = split_station_args(["--check-pin"] + tail)
    j = (fwd == tail)
    print("  judge5 `--` 边界全透传:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # 判6 断言核：正 md5 过、伪 md5 拒
    act = md5_of(os.path.abspath(__file__))
    ok_t, w_t = assert_md5(act, [act], False)
    ok_f, _ = assert_md5(act, ["0123456789abcdef0123456789abcdef"], False)
    j = (ok_t is True and ok_f is False and w_t[0][1] is True)
    print("  judge6 断言核正过伪拒:", "PASS" if j else "FAIL")
    ok = ok and j

    # 判7 嵌记形制：32 位 hex（正本缺位时判6 已用 __file__ 代测·嵌记形制独立在判）
    j = norm_hex(PINNED_MD5) == PINNED_MD5
    print("  judge7 PINNED_MD5 形制 32-hex:", "PASS" if j else "FAIL")
    ok = ok and j

    return ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not argv:
        # 裸调＝指认卡（不透传）
        canonical = find_canonical(default_root())
        if canonical is None:
            print("scan_station: 正本缺失: %s（于仓根 %s）" % (CANONICAL_REL, default_root()),
                  file=sys.stderr)
            sys.exit(9)
        lines, ok = station_card(canonical, md5_of(canonical), [], False, forward_argv=None)
        print("\n".join(lines))
        sys.exit(0 if ok else 2)

    try:
        st, fwd = split_station_args(argv)
    except ValueError as e:
        print("scan_station: 站级用法错: %s" % e, file=sys.stderr)
        print(STATION_USAGE, file=sys.stderr)
        sys.exit(2)

    if st["help"]:
        print(STATION_USAGE, end="")
        sys.exit(0)

    if st["selftest"]:
        p = station_selftest()
        print("STATION-SELFTEST (wrapper 自身七判·不动正本):", "PASS" if p else "FAIL")
        sys.exit(0 if p else 2)

    root = st["root"] if st["root"] else default_root()
    canonical = find_canonical(root)
    if canonical is None:
        print("scan_station: 正本缺失: %s（于仓根 %s）" % (CANONICAL_REL, root),
              file=sys.stderr)
        sys.exit(9)

    actual = md5_of(canonical)
    ok, _ = assert_md5(actual, st["expect_md5"], st["check_pin"])

    if st["identify"]:
        lines, ok2 = station_card(canonical, actual, st["expect_md5"], st["check_pin"],
                                  forward_argv=None)
        print("\n".join(lines))
        sys.exit(0 if ok2 else 2)

    if not ok:
        # 断言失败：卡照出（stderr），绝不带病透传
        lines, _ = station_card(canonical, actual, st["expect_md5"], st["check_pin"],
                                forward_argv=fwd)
        print("\n".join(lines), file=sys.stderr)
        sys.exit(2)

    # Clean mode: the --baseline face targets the canonical campaign
    # workspace; report and refuse before dispatching the frozen scanner
    # (the generic --file scan stays available).
    if _clean_mode() and "--baseline" in fwd:
        print("requires canonical environment: the campaign-workspace S09 "
              "baseline target (scan/mac_stmt_scan.py --baseline); use "
              "--file for a generic scan")
        sys.exit(9)

    # 透传：站级横幅走 stderr（正本 stdout 独占·管道口径不污染）
    print("[scan_station] 正本指认 md5=%s（%s）→ 透传 %d 参" % (actual, PINNED_NOTE, len(fwd)),
          file=sys.stderr)
    cmd = [sys.executable or "python3", "-B", canonical] + fwd
    try:
        rc = subprocess.call(cmd)
    except OSError as e:
        print("scan_station: 透传失败（OSError）: %s" % e, file=sys.stderr)
        sys.exit(127)
    sys.exit(rc)


if __name__ == "__main__":
    main()
