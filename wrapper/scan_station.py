#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_station.py - canonical identification station for the frozen scanner `scan/mac_stmt_scan.py` (rocqwash wrapper/).
Purpose.  The in-service component `scan/mac_stmt_scan.py` is frozen against edits (pinned md5 in
  PINNED_MD5); adaptations land as new files under `wrapper/`, so this wrapper is the canonical
  identification station for the frozen scanner: (1) identify - locate the canonical copy and
  present it (path, md5, byte count, pin comparison); identification proves which copy is canonical
  only and endorses no scan verdict (scan semantics stay with the canonical tool); (2) assert
  (optional) - `--expect-md5 <hex>` (repeatable, all must match) and `--check-pin` (the
  adaptation-time pin); a failed assertion exits 2 and nothing is forwarded in a failing state;
  (3) pass through - arguments beyond the station flags go verbatim in original order to
  `python3 -B scan/mac_stmt_scan.py`, the child exit code propagating unchanged (fail-loud, never
  rewritten; cli/rocqwash routing contract).
Interface.  python3 wrapper/scan_station.py [station flags] [forwarded arguments...]
  Station flags (kept by the wrapper, never forwarded): --root DIR (canonical repository root;
  default = the repository root holding this wrapper; missing value exits 2) | --identify
  (identification card only, no forwarding; exit 0 on pass, 2 on fail) | --expect-md5 HEX
  (repeatable, 32 hex characters) | --check-pin | --station-selftest (seven in-process judgments,
  zero writes, canonical untouched) | -h/--help (the canonical tool's help stays reachable through
  `scan_station -- --help`).  The canonical flags --file/--json/--manifest/--hits-csv/--baseline/
  --selftest pass through; arguments after `--` (station-flag spellings included) pass through
  verbatim as the explicit forwarding boundary; a bare call prints the card without forwarding.
Dependencies.  Python 3 standard library only (hashlib, io, os, subprocess, sys); assumes the canonical
  copy at `scan/mac_stmt_scan.py` under the resolved repository root; the wrapper writes nothing
  (run_tests.sh idempotence-compatible; smoke output paths belong to the caller's own sandbox).
Evidence.  --station-selftest runs seven in-process judgments (md5 helper agreement, canonical location,
  order-preserving flag stripping, inline-form stripping, `--` boundary verbatim forwarding, assertion
  accept and reject, pin format); `tests/test_scan_station.py` adds nine subprocess checks.
Exit-codes.  0 = pass; 2 = failed assertion or station usage error; 9 = canonical copy missing;
  otherwise = the canonical tool's exit code passed through unchanged (its --selftest vector
  failures exit 2 and a missing --file target exits 9, all reachable as is).
"""
import hashlib
import io
import os
import subprocess
import sys

WRAP_NAME = "wrapper/scan_station.py"
CANONICAL_REL = "scan/mac_stmt_scan.py"

# The pin is the md5 measured against the canonical copy at adaptation time (also printed on
# the identification card through PINNED_NOTE).  If the canonical copy is ever revised under the
# freeze authority, the pin must be re-measured against the live copy; this wrapper never edits
# the canonical copy, nor any in-service file beyond the pin itself.
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
    """Default canonical repository root: the grandparent directory of this wrapper file (the
    parent of `wrapper/`)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_canonical(root):
    """Locate the canonical copy: return the absolute path of `scan/mac_stmt_scan.py` under
    `root` when the file exists, else None."""
    if not root:
        return None
    p = os.path.join(os.path.abspath(root), *CANONICAL_REL.split("/"))
    return p if os.path.isfile(p) else None


def split_station_args(argv):
    """Strip the station flags; keep every other argument verbatim in original order
    (1:1 forwarding faithfulness).

    Returns (station, forwarded).  A value-less --root/--expect-md5 raises ValueError
    (station usage error).
    """
    st = dict(root=None, identify=False, expect_md5=[], check_pin=False,
              help=False, selftest=False)
    fwd = []
    i, n = 0, len(argv)
    while i < n:
        a = argv[i]
        if a == "--":
            fwd.extend(argv[i:])          # explicit forwarding boundary: everything after passes through
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
    """Assertion-value format check: strip whitespace and quotes, lowercase; return None for
    anything that is not 32 hex characters (invalid assertion format)."""
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def assert_md5(actual, expects, check_pin):
    """md5 assertion core: every expectation must match (plus the optional pin); returns
    (ok, [(want, match), ...])."""
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
    """Identification card lines (plain text, nothing written to disk).  forward_argv=None
    marks no forwarding (--identify)."""
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
    """This wrapper's own selftest (seven judgments, zero disk writes, canonical copy
    untouched).  Returns the pass boolean."""
    ok = True
    root = default_root()

    # judge1 md5_of and md5_bytes agree on the same source (object = this wrapper itself, zero writes)
    v1 = md5_of(os.path.abspath(__file__))
    with io.open(os.path.abspath(__file__), "rb") as f:
        v2 = md5_bytes(f.read())
    j = (v1 == v2)
    print("  judge1 md5_of==md5_bytes(__file__):", "PASS" if j else "FAIL")
    ok = ok and j

    # judge2 the canonical copy is located under the default repository root
    c = find_canonical(root)
    j = (c is not None and os.path.isfile(c)
         and os.path.relpath(c, root).replace(os.sep, "/") == CANONICAL_REL)
    print("  judge2 find_canonical(default_root) 在位:", "PASS" if j else "FAIL")
    ok = ok and j

    # judge3 order preservation with interleaved flags: station flags stripped, the rest verbatim in order
    st, fwd = split_station_args(["--file", "x.v", "--check-pin", "--json", "o.json", "y"])
    j = (st["check_pin"] is True and st["identify"] is False
         and fwd == ["--file", "x.v", "--json", "o.json", "y"])
    print("  judge3 混排剥离保序:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # judge4 the inline form --root=X is stripped, not forwarded
    st, fwd = split_station_args(["--root=/tmp/x", "--file", "x.v"])
    j = (st["root"] == "/tmp/x" and fwd == ["--file", "x.v"])
    print("  judge4 --root=X inline 剥离:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # judge5 the -- boundary: everything after it (station-flag spellings included) passes through verbatim
    tail = ["--", "--identify", "--file", "x.v"]
    _, fwd = split_station_args(["--check-pin"] + tail)
    j = (fwd == tail)
    print("  judge5 `--` 边界全透传:", "PASS" if j else "FAIL", fwd)
    ok = ok and j

    # judge6 assertion core: a correct md5 passes, a fake md5 is rejected
    act = md5_of(os.path.abspath(__file__))
    ok_t, w_t = assert_md5(act, [act], False)
    ok_f, _ = assert_md5(act, ["0123456789abcdef0123456789abcdef"], False)
    j = (ok_t is True and ok_f is False and w_t[0][1] is True)
    print("  judge6 断言核正过伪拒:", "PASS" if j else "FAIL")
    ok = ok and j

    # judge7 pin format: 32 hex characters (judge6 substitutes __file__ when the canonical copy is
    # absent; the pin format check stands alone)
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
        # bare call = identification card (no forwarding)
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
        # failed assertion: the card still prints (stderr); nothing is forwarded in a failing state
        lines, _ = station_card(canonical, actual, st["expect_md5"], st["check_pin"],
                                forward_argv=fwd)
        print("\n".join(lines), file=sys.stderr)
        sys.exit(2)

    # Clean mode: the --baseline face targets the canonical work-stream
    # workspace; report and refuse before routing the frozen scanner
    # (the generic --file scan stays available).
    if _clean_mode() and "--baseline" in fwd:
        print("requires canonical environment: the campaign-workspace S09 "
              "baseline target (scan/mac_stmt_scan.py --baseline); use "
              "--file for a generic scan")
        sys.exit(9)

    # forwarding: the station banner goes to stderr (the canonical tool owns stdout exclusively;
    # pipes stay clean)
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
