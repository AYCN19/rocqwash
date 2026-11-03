#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_sync.py — probe 台账×状态台账 TSV 合并同步器（rocqwash tools/·v30 实战
判例工具化·承 20261103 台账 v2 底册工艺·20261103 入账；v2.1 20261103 承 W59 支撑
席合账草案发现增补：items 子键识别＋批量元数据键滤除＋双代分歧出账）

probe 台账（probe_engine 产出 rocqwash-probe-ledger/1「records」壳、席位冻结账
「items」子键壳、或 W13 式裸 {件名: 记录}）×状态台账 TSV（表头含 件名/行数/md5/
RED/状态/备注 列族）→逐件对账合并 → 新状态台账 TSV。五机制（战役 E1/E3 伤口码
工具化＋v2.1 分歧出账）：

  E1 去重      状态台账内同「件名」多行 → 去重保留首行（确定性·后现重复逐笔
              计数响亮入账·不静默丢弃）。
  E3 幽灵      probe 台账有名而状态台账无行 → 幽灵响亮出账（只记账不落行——
              台账缺行属底册完整性事件·禁静默补行）。
  MD5-DRIFT   probe 记录带 md5 且 ≠ 台账行 md5 → 该行**不升格**只注记（探针
              凭据不为此代源件作保·响亮计数）。
  NO-MD5      probe 记录无 md5 字段（W13 老式账/冻结账 washed_md5 记录）→
              只注记不升格·响亮计数。
  GEN-DIVERGENCE (v2.1)  probe 记录携带 divergence_with/divergence_md5（多源
              合成双代分歧）→ 该行注记 probe:gen-div:<dropped>＋逐笔响亮出
              账——dropped 代不弃账·候落位批裁定·禁静默吞分歧。

分歧优先序（v2.1 成文——W59 支撑席双代分歧判例工具化）：多源合成 probe 同名双
代（两席各自洗出不同代）→ kept 代＝下游冻结账 ledger_basis 榜系所引用的源席代
（下游消费代）；dropped 代不入 probe 但以分歧字段留痕（合成器职责），同步侧见
分歧字段即出账。两职分立：合成侧按优先序排 records；同步侧对携带分歧字段的记
录逐笔响亮——工具面永不静默裁决代际。

probe 台账形态识别（v2.1）：顶层「records」dict → 直用；顶层「items」dict（席
位冻结账形）→ 直用；其余裸 dict → 按记录形（携带 md5/rc/red/file/washed_md5
任一字段的 dict 值）滤取，非记录形键（batch_meta/schema 等元数据）逐键响亮计入
meta_skipped·滤后零记录 → fail-loud 拒同步。

同步动作（逐匹配行）：
  1 注记：备注列追加探针凭据 tag（幂等——tag 已在即不重复）：
      rc=0     → probe:rc0        rc=1     → probe:rc1[:红因分类]
      rc=124   → probe:timeout    NO_SRC   → probe:no-src
      分歧字段 → probe:gen-div:<dropped>（幂等同上）
  2 升格（--policy unprobed-only 缺省·仅当行状态=UNPROBED 且 md5 咬合）：
      probe rc0 → 状态=WASHABLE；probe rc1 → 状态=DRIFT-BLOCKED
      （承台账 v2 判定口径：WASHABLE＝探针 rc0 闭包相容·DRIFT-BLOCKED＝探针
       rc1 红因在账——LANDED/FROZEN/OCCUPIED/GIANT 等上级状态永不降格改写）
    --policy annotate-only：只注记不动状态列。

列校验（fail-loud·exit 2·不产出）：缺必需列（件名/md5/RED/状态/备注）／行宽
≠表头列数／probe 台账形态不识别——一律响亮拒同步。

幂等：同 probe×同台账重跑 → 新台账字节级恒同（tag 在盘即跳过＋确定性遍历）。

用法（全部路径参数化·零硬编码·零网络）：
  python3 tools/ledger_sync.py --probe probe_ledger.json --ledger status.tsv \
      --out new_status.tsv [--report sync_report.json] [--policy unprobed-only]
  python3 tools/ledger_sync.py --selftest

退出码：0=SYNC-CLEAN（零发现）；1=SYNC-FINDINGS（E1/E3/MD5-DRIFT/NO-MD5/
GEN-DIVERGENCE 任一非零·新台账仍已落盘）；2=列校验/用法错（--help rc=0／缺必需
参数）；9=输入文件缺失。报告 schema=rocqwash-ledger-sync/1（v2.1 增 meta_skipped
字段·增量兼容）。
"""
import argparse
import io
import json
import os
import re
import sys

PROG = "ledger_sync"
SCHEMA = "rocqwash-ledger-sync/1"

REQUIRED_COLS = ("件名", "md5", "RED", "状态", "备注")
POLICIES = ("unprobed-only", "annotate-only")

MISSING_LIB_RE = re.compile(r"(?:unable to locate library|cannot find library)"
                            r"\s+\|?\s*([A-Za-z0-9_']+)", re.IGNORECASE)
CLASS_RES = [
    ("MISSING_LIB", re.compile(r"unable to locate library|cannot find library", re.I)),
    ("ILLEGAL_APP", re.compile(r"illegal application", re.I)),
    ("NO_SUBTERM", re.compile(r"no subterm matching", re.I)),
    ("FACE", re.compile(r"expected to have type|is not convertible", re.I)),
]


RECORD_SHAPE_FIELDS = ("md5", "rc", "red", "red_class", "file", "washed_md5")


def _is_record_shape(v):
    return isinstance(v, dict) and any(f in v for f in RECORD_SHAPE_FIELDS)


def load_probe(path):
    """probe 台账 → (records, meta_skipped)。

    形态识别（v2.1 三形）：
      1 顶层「records」dict（rocqwash-probe-ledger/1 壳）→ 直用；
      2 顶层「items」dict（席位冻结账壳）→ 直用；
      3 其余裸 dict → 按记录形滤取（_is_record_shape），非记录形键逐键记入
        meta_skipped 响亮返回；滤后零记录 → ValueError（fail-loud 拒同步）。
    """
    with io.open(path, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    if isinstance(d, dict) and isinstance(d.get("records"), dict):
        return d["records"], []
    if isinstance(d, dict) and isinstance(d.get("items"), dict):
        return d["items"], []
    if isinstance(d, dict):
        records = {}
        meta_skipped = []
        for k, v in d.items():
            if _is_record_shape(v):
                records[k] = v
            else:
                meta_skipped.append(k)
        if not records:
            raise ValueError("probe 台账滤除元数据键后零记录（裸 dict 形态·"
                             "meta_skipped=%r）: %s" % (meta_skipped, path))
        return records, meta_skipped
    raise ValueError("probe 台账形态不识别（records 壳/items 壳/裸 dict 三形"
                     "皆不匹配）: %s" % path)


def load_status_tsv(path):
    """状态台账 TSV → (header, rows[dict])·列校验 fail-loud（ValueError）。"""
    with io.open(path, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    if not lines:
        raise ValueError("状态台账空文件: %s" % path)
    header = lines[0].split("\t")
    missing = [c for c in REQUIRED_COLS if c not in header]
    if missing:
        raise ValueError("状态台账缺必需列 %r（表头=%r）" % (missing, header))
    rows = []
    for i, ln in enumerate(lines[1:], start=2):
        f = ln.split("\t")
        if len(f) != len(header):
            raise ValueError("状态台账第 %d 行宽不齐（应 %d 列实 %d 列）"
                             % (i, len(header), len(f)))
        rows.append(dict(zip(header, f)))
    return header, rows


def red_class_of(rec):
    """probe 记录红因分类（red_class 字段直用·缺则 red 原文 regex）。"""
    cls = rec.get("red_class")
    if cls:
        return cls
    red = rec.get("red") or ""
    for name, rx in CLASS_RES:
        if rx.search(red):
            return name
    return ""


def tag_of(rec):
    """探针凭据 tag（幂等注记单元）。"""
    rc = rec.get("rc")
    if rc == "NO_SRC":
        return "probe:no-src"
    if rc == 124:
        return "probe:timeout"
    if rc == 0:
        return "probe:rc0"
    if isinstance(rc, int):
        cls = red_class_of(rec)
        return "probe:rc%d:%s" % (rc, cls) if cls else "probe:rc%d" % rc
    return "probe:rc%s" % rc


def sync(probe_path, ledger_path, policy):
    """主同步 → (header, out_rows, findings, meta_skipped)·findings 为 dict 列表。"""
    probe, meta_skipped = load_probe(probe_path)
    header, rows = load_status_tsv(ledger_path)
    findings = []

    # E1 去重（保首行·响亮计数）
    seen = set()
    deduped = []
    for r in rows:
        name = r["件名"]
        if name in seen:
            findings.append({"code": "E1-DUP", "name": name,
                             "detail": "台账同件名多行——保首行去本行"})
            continue
        seen.add(name)
        deduped.append(r)

    probe_names = set(probe.keys())
    tsv_names = set(seen)

    # E3 幽灵（probe 有名台账无行·只记账不落行）
    for name in sorted(probe_names - tsv_names):
        findings.append({"code": "E3-GHOST", "name": name,
                         "detail": "probe 台账有名而状态台账无行——只记账不落行"})

    # 逐行合并
    for r in deduped:
        name = r["件名"]
        rec = probe.get(name)
        if rec is None:
            continue
        tag = tag_of(rec)
        note = r.get("备注", "")
        if tag not in note:
            r["备注"] = (note + "·" + tag) if note else tag
        # v2.1 双代分歧出账（dropped 代不弃账·候落位批裁定·禁静默吞分歧）
        div_with = rec.get("divergence_with")
        if div_with:
            div_tag = "probe:gen-div:%s" % div_with
            note = r["备注"]
            if div_tag not in note:
                r["备注"] = (note + "·" + div_tag) if note else div_tag
            findings.append({
                "code": "GEN-DIVERGENCE", "name": name,
                "detail": "双代分歧：kept=%s（下游账 basis 榜系消费代）·"
                          "dropped=%s（md5 %s）——只注记不弃账·候落位批裁定"
                          % (",".join(rec.get("source_seats") or [name]),
                             div_with, rec.get("divergence_md5") or "?")})
        md5_p = rec.get("md5")
        can_upgrade = False
        if md5_p is None:
            findings.append({"code": "NO-MD5", "name": name,
                             "detail": "probe 记录无 md5（老式账）——只注记不升格"})
        elif md5_p != r["md5"]:
            findings.append({"code": "MD5-DRIFT", "name": name,
                             "detail": "probe md5=%s ≠ 台账 md5=%s——不升格只注记"
                                       % (md5_p, r["md5"])})
        else:
            can_upgrade = True
        if (policy == "unprobed-only" and can_upgrade
                and r["状态"] == "UNPROBED"):
            if rec.get("rc") == 0:
                r["状态"] = "WASHABLE"
            elif rec.get("rc") == 1:
                r["状态"] = "DRIFT-BLOCKED"
    return header, deduped, findings, meta_skipped


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """内嵌冻结向量组（临时合成账·零触真仓零网络）：E1 去重/E3 幽灵/MD5-DRIFT/
    NO-MD5/UNPROBED 升格与上级状态不降格/tag 幂等注记/字节恒同/CLI 四码。"""
    import shutil
    import tempfile

    def run(args):
        import subprocess
        p = subprocess.run([sys.executable, "-B",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         PROG + ".py")] + args,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.stdout = p.stdout.decode("utf-8", errors="replace") \
            if isinstance(p.stdout, bytes) else (p.stdout or "")
        return p

    tmp = tempfile.mkdtemp(prefix="rocqwash_lsync_self_")
    try:
        tsv = os.path.join(tmp, "status.tsv")
        with io.open(tsv, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "R1\t100\taaa\t0\tUNPROBED\t\n"
                     "R2\t200\tbbb\t3\tUNPROBED\t\n"
                     "R3\t300\tccc\t0\tLANDED\t已落位\n"
                     "R4\t50\tddd\t0\tWASHABLE\tprobe:rc0\n")
        probe = os.path.join(tmp, "probe.json")
        with io.open(probe, "w", encoding="utf-8") as fh:
            json.dump({"records": {
                "R1": {"file": "R1", "md5": "aaa", "rc": 0, "red": ""},
                "R2": {"file": "R2", "md5": "bbb", "rc": 1,
                       "red": "Error: Unable to locate library | Lx",
                       "red_class": "MISSING_LIB"},
                "R3": {"file": "R3", "md5": "zzz", "rc": 0, "red": ""},
                "R4": {"file": "R4", "md5": "ddd", "rc": 0, "red": ""},
                "GHOST1": {"file": "GHOST1", "md5": "ggg", "rc": 0, "red": ""},
            }}, fh)
        out = os.path.join(tmp, "new.tsv")
        p = run(["--probe", probe, "--ledger", tsv, "--out", out])
        assert p.returncode == 1 and "SYNC-FINDINGS" in p.stdout, p.stdout
        rows = [ln.split("\t") for ln in
                io.open(out, encoding="utf-8").read().rstrip("\n").split("\n")]
        by = {r[0]: r for r in rows[1:]}
        assert by["R1"][4] == "WASHABLE" and "probe:rc0" in by["R1"][5], by["R1"]
        assert by["R2"][4] == "DRIFT-BLOCKED", by["R2"]
        assert "probe:rc1:MISSING_LIB" in by["R2"][5], by["R2"]
        assert by["R3"][4] == "LANDED", "上级状态被降格＝违例"
        assert "probe:rc0" in by["R3"][5] and "MD5-DRIFT" in p.stdout, by["R3"]
        assert by["R4"][5].count("probe:rc0") == 1, "tag 重复注记＝违例"
        assert "E3-GHOST" in p.stdout and "GHOST1" in p.stdout, p.stdout
        # 幂等：重跑字节恒同
        before = io.open(out, "rb").read()
        p = run(["--probe", probe, "--ledger", tsv, "--out", out])
        assert p.returncode == 1, p.stdout
        assert io.open(out, "rb").read() == before, "重跑字节漂移＝违例"
        # annotate-only：不动状态列
        out2 = os.path.join(tmp, "new2.tsv")
        p = run(["--probe", probe, "--ledger", tsv, "--out", out2,
                 "--policy", "annotate-only"])
        rows2 = [ln.split("\t") for ln in
                 io.open(out2, encoding="utf-8").read().rstrip("\n").split("\n")]
        by2 = {r[0]: r for r in rows2[1:]}
        assert by2["R1"][4] == "UNPROBED" and "probe:rc0" in by2["R1"][5], by2["R1"]
        # 列校验 fail-loud：缺必需列 → rc2 不产出
        bad = os.path.join(tmp, "bad.tsv")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("件名\tmd5\nR1\taaa\n")
        out3 = os.path.join(tmp, "nope.tsv")
        p = run(["--probe", probe, "--ledger", bad, "--out", out3])
        assert p.returncode == 2 and "缺必需列" in p.stdout, p.stdout
        assert not os.path.exists(out3), "列校验红仍产出＝违例"
        # 行宽不齐 → rc2
        ragged = os.path.join(tmp, "ragged.tsv")
        with io.open(ragged, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\nR1\t1\ta\t0\tUNPROBED\n")
        p = run(["--probe", probe, "--ledger", ragged, "--out", out3])
        assert p.returncode == 2 and "行宽不齐" in p.stdout, p.stdout
        # CLI 四码
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺参数应 rc=2 实测 %d" % p.returncode
        p = run(["--probe", os.path.join(tmp, "no.json"), "--ledger", tsv,
                 "--out", out3])
        assert p.returncode == 9, "缺文件应 rc=9 实测 %d" % p.returncode
        # ---- v2.1 vectors ----
        # items-subkey probe (seat freeze-ledger shell): records consumed,
        # shell keys never become phantom probe names
        tsv2 = os.path.join(tmp, "v21.tsv")
        with io.open(tsv2, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "H1\t10\tmh1\t0\tUNPROBED\t\n")
        probe2 = os.path.join(tmp, "freeze_ledger.json")
        with io.open(probe2, "w", encoding="utf-8") as fh:
            json.dump({"schema": "seat-freeze/1",
                       "items": {"H1": {"file": "H1", "md5": "mh1",
                                        "rc": 0, "red": ""}},
                       "queue": [], "world": "/tmp/x"}, fh)
        out4 = os.path.join(tmp, "v21out.tsv")
        p = run(["--probe", probe2, "--ledger", tsv2, "--out", out4])
        assert p.returncode == 0 and "SYNC-CLEAN" in p.stdout, p.stdout
        by = dict((ln.split("\t")[0], ln.split("\t"))
                  for ln in io.open(out4, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert by["H1"][4] == "WASHABLE" and "probe:rc0" in by["H1"][5], by["H1"]
        assert "E3-GHOST" not in p.stdout, "items 壳键漏读为幽灵＝违例"
        # bare-dict form with batch_meta sibling: meta skipped loudly, record
        # synced, no phantom ghost for the meta key
        tsv3 = os.path.join(tmp, "v21b.tsv")
        with io.open(tsv3, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "J1\t10\tmj1\t0\tUNPROBED\t\n")
        probe3 = os.path.join(tmp, "bare_meta.json")
        with io.open(probe3, "w", encoding="utf-8") as fh:
            json.dump({"J1": {"file": "J1", "md5": "mj1", "rc": 0, "red": ""},
                       "batch_meta": {"seat": "W9", "date": "20261103"}}, fh)
        out5 = os.path.join(tmp, "v21bout.tsv")
        p = run(["--probe", probe3, "--ledger", tsv3, "--out", out5])
        assert p.returncode == 0 and "PROBE-META-SKIP" in p.stdout, p.stdout
        assert "batch_meta" in p.stdout, "元数据键应响亮留痕"
        assert "E3-GHOST" not in p.stdout, "元数据键不得误报幽灵"
        by3 = dict((ln.split("\t")[0], ln.split("\t"))
                   for ln in io.open(out5, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert by3["J1"][4] == "WASHABLE", by3
        # bare-dict all-meta (zero records): fail-loud rc2, no output file
        probe4 = os.path.join(tmp, "all_meta.json")
        with io.open(probe4, "w", encoding="utf-8") as fh:
            json.dump({"schema": "x/1", "batch_meta": {"seat": "W9"}}, fh)
        out6 = os.path.join(tmp, "v21cout.tsv")
        p = run(["--probe", probe4, "--ledger", tsv3, "--out", out6])
        assert p.returncode == 2 and "零记录" in p.stdout, p.stdout
        assert not os.path.exists(out6), "零记录拒同步仍产出＝违例"
        # divergence-carrying record: GEN-DIVERGENCE finding + gen-div tag,
        # rerun byte-stable (tag idempotent, finding re-fires loud)
        tsv4 = os.path.join(tmp, "v21d.tsv")
        with io.open(tsv4, "w", encoding="utf-8") as fh:
            fh.write("件名\t行数\tmd5\tRED\t状态\t备注\n"
                     "K1\t10\tmk1\t0\tUNPROBED\t\n")
        probe5 = os.path.join(tmp, "div.json")
        with io.open(probe5, "w", encoding="utf-8") as fh:
            json.dump({"records": {
                "K1": {"file": "K1", "md5": "mk1", "rc": 0, "red": "",
                       "source_seats": ["sA", "sB"],
                       "divergence_with": "sB",
                       "divergence_md5": "d5d5"}}}, fh)
        out7 = os.path.join(tmp, "v21dout.tsv")
        p = run(["--probe", probe5, "--ledger", tsv4, "--out", out7])
        assert p.returncode == 1 and "GEN-DIVERGENCE" in p.stdout, p.stdout
        by4 = dict((ln.split("\t")[0], ln.split("\t"))
                   for ln in io.open(out7, encoding="utf-8").read().rstrip("\n").split("\n")[1:])
        assert "probe:gen-div:sB" in by4["K1"][5], by4  # 注记在行备注列
        assert by4["K1"][4] == "WASHABLE", by4  # md5 咬合升格照常·分歧只注记 dropped 代
        before = io.open(out7, "rb").read()
        p = run(["--probe", probe5, "--ledger", tsv4, "--out", out7])
        assert p.returncode == 1, p.stdout
        assert io.open(out7, "rb").read() == before, "分歧注记重跑字节漂移＝违例"
        print("LEDGER-SYNC-SELFTEST PASS: E1 去重/E3 幽灵/MD5-DRIFT/上级不降格/"
              "tag 幂等/annotate-only/列校验 fail-loud/幂等字节恒同/CLI 四码/"
              "items 壳/元数据滤除/零记录拒同步/GEN-DIVERGENCE 出账与注记幂等 "
              "十三判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="probe 台账×状态台账 TSV 合并同步：E1 去重/"
                               "E3 幽灵/GEN-DIVERGENCE/列校验 fail-loud→新台账"
                               "（schema rocqwash-ledger-sync/1）")
    ap.add_argument("--probe", default=None, metavar="FILE",
                    help="probe 台账 JSON（records 壳或裸 dict）")
    ap.add_argument("--ledger", default=None, metavar="FILE",
                    help="状态台账 TSV（必需列 件名/md5/RED/状态/备注）")
    ap.add_argument("--out", default=None, metavar="FILE",
                    help="新状态台账 TSV 出账")
    ap.add_argument("--report", default=None, metavar="FILE",
                    help="同步报告 JSON 出账（计数＋逐笔发现）")
    ap.add_argument("--policy", default="unprobed-only", choices=POLICIES,
                    help="升格策略（缺省仅 UNPROBED 行可升格·annotate-only 只注记）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    for req in ("probe", "ledger", "out"):
        if not getattr(args, req):
            print("FAIL-LOUD: --%s 必给（--selftest 除外）" % req, file=sys.stderr)
            sys.exit(2)
    for label, val in (("probe", args.probe), ("ledger", args.ledger)):
        if not os.path.exists(val):
            print("FAIL-LOUD: --%s 文件缺失: %s" % (label, val), file=sys.stderr)
            sys.exit(9)

    try:
        header, rows, findings, meta_skipped = sync(args.probe, args.ledger,
                                                    args.policy)
    except ValueError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(header) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in header) + "\n")

    codes = {}
    for f in findings:
        codes[f["code"]] = codes.get(f["code"], 0) + 1
    n_synced = sum(1 for r in rows if "probe:" in r.get("备注", ""))
    print("=== LEDGER-SYNC ===")
    print("probe=%s ledger=%s policy=%s" % (args.probe, args.ledger, args.policy))
    print("rows=%d synced(注记)=%d findings=%d %s"
          % (len(rows), n_synced, len(findings),
             " ".join("%s=%d" % kv for kv in sorted(codes.items()))))
    if meta_skipped:
        print("PROBE-META-SKIP: %d 键非记录形已滤除（响亮留痕）: %s"
              % (len(meta_skipped), ",".join(sorted(meta_skipped))))
    for f in findings:
        print("FINDING %-9s %s — %s" % (f["code"], f["name"], f["detail"]))
    if args.report:
        acc = {"schema": SCHEMA, "probe": args.probe, "ledger": args.ledger,
               "policy": args.policy, "rows": len(rows), "synced": n_synced,
               "findings": findings, "counts": codes,
               "meta_skipped": sorted(meta_skipped)}
        with io.open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(acc, fh, indent=1, ensure_ascii=False, sort_keys=True)
        print("report ->", args.report)
    print("new ledger -> %s" % args.out)
    if findings:
        print("SYNC-FINDINGS: %d 笔（E1/E3/MD5-DRIFT/NO-MD5/GEN-DIVERGENCE·"
              "新台账已落盘）" % len(findings))
        sys.exit(1)
    print("SYNC-CLEAN: 零发现（去重 0 幽灵 0 漂移 0 分歧 0）")
    sys.exit(0)


if __name__ == "__main__":
    main()
