#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ledger_sync.py — tools/ledger_sync.py 自测（tests/·v30 实战判例工具化·
20261103 台账 v2 底册工艺工具化轮；v2.1 20261103 承 W59 支撑席合账草案发现增补
九/十两节）

probe×状态台账合并同步十节判：
  1 工具自证    --selftest 十三判全过（rc 0）
  2 CLEAN 全链  全覆盖 probe＋零发现 → exit 0 SYNC-CLEAN·UNPROBED 升格
                （rc0→WASHABLE／rc1→DRIFT-BLOCKED）逐行咬合
  3 E1 去重     同件名多行 → 保首行＋逐笔 FINDING 计数＋去重后行数正确
  4 E3 幽灵     probe 有名台账无行 → 只记账不落行·幽灵名单响亮
  5 特异 tag    rc=124 → probe:timeout／NO_SRC → probe:no-src·UNPROBED 行
                遇之不升格（升格唯 rc0/rc1）
  6 NO-MD5      W13 老式记录（无 md5）→ 只注记不升格·NO-MD5 计数
  7 报告面      --report JSON schema/counts/逐笔发现咬合＋probe_engine 全字段
                记录（red_count/md5_match）直吞
  8 CLI＋列校验 四码（help0/bogus2/缺参2/缺件9）＋缺必需列 rc2 不产出＋
                行宽不齐 rc2＋幂等重跑字节恒同
  9 items 壳    席位冻结账形（items 子键）直吞——records 消费、壳键零幽灵；
                裸 dict 形 batch_meta 元数据键响亮滤除（PROBE-META-SKIP·零
                幽灵误报）；全元数据零记录 → rc2 fail-loud 不产出
  10 分歧出账   divergence_with 记录 → GEN-DIVERGENCE 逐笔响亮＋行注记
                probe:gen-div:<dropped>（幂等）＋md5 咬合升格照常；重跑
                字节恒同（发现重fire·台账字节稳定）

零触律：全部夹具临时合成（TSV/JSON 即写即清）·零真编译零网络零触真仓。
幂等：python3 -B 禁 __pycache__。退出码：0=十节全过；1=任一红。
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "tools", "ledger_sync.py")

_spec = importlib.util.spec_from_file_location("ledger_sync_mod", TOOL)
ls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ls)


def run(args):
    p = subprocess.run([sys.executable, "-B", TOOL] + args,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", errors="replace")


def wf(path, text):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def read_rows(path):
    lines = io.open(path, encoding="utf-8").read().rstrip("\n").split("\n")
    rows = [ln.split("\t") for ln in lines]
    header = rows[0]
    return header, [dict(zip(header, r)) for r in rows[1:]]


def sec1_selftest():
    rc, out = run(["--selftest"])
    assert rc == 0, "selftest 应 rc=0 实测 %d\n%s" % (rc, out)
    assert "LEDGER-SYNC-SELFTEST PASS" in out, out
    assert "十三判全过" in out, out
    return "selftest 十三判绿"


def sec2_clean(tmp):
    tsv = wf(os.path.join(tmp, "t2.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "A1\t10\tm1\t0\tUNPROBED\t\n"
             "A2\t20\tm2\t5\tUNPROBED\t\n"
             "A3\t30\tm3\t0\tUNPROBED\t\n")
    probe = os.path.join(tmp, "p2.json")
    with io.open(probe, "w", encoding="utf-8") as fh:
        json.dump({"schema": ls.SCHEMA, "records": {
            "A1": {"file": "A1", "md5": "m1", "rc": 0, "red": "",
                   "red_class": "", "verdict": "BORN-CLEAN",
                   "red_count": 0, "md5_match": True},
            "A2": {"file": "A2", "md5": "m2", "rc": 1,
                   "red": "Error: Illegal application (Non-functional "
                          "construction): boom",
                   "red_class": "ILLEGAL_APP", "verdict": "RED-ILLEGAL_APP",
                   "red_count": 5, "md5_match": True},
            "A3": {"file": "A3", "md5": "m3", "rc": 0, "red": "",
                   "red_class": "", "verdict": "WASHABLE",
                   "red_count": 1, "md5_match": True},
        }}, fh)
    out = os.path.join(tmp, "t2out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert by["A1"]["状态"] == "WASHABLE" and by["A1"]["备注"] == "probe:rc0", by["A1"]
    assert by["A2"]["状态"] == "DRIFT-BLOCKED" \
        and by["A2"]["备注"] == "probe:rc1:ILLEGAL_APP", by["A2"]
    assert by["A3"]["状态"] == "WASHABLE", by["A3"]
    return "CLEAN 全链 exit 0＋UNPROBED 升格逐行咬合＋probe_engine 全字段直吞"


def sec3_e1_dedup(tmp):
    tsv = wf(os.path.join(tmp, "t3.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "B1\t10\tm1\t0\tUNPROBED\t首行\n"
             "B1\t99\tZZ\t9\tGIANT\t重复行应弃\n"
             "B2\t20\tm2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p3.json"),
               json.dumps({"records": {"B1": {"file": "B1", "md5": "m1",
                                              "rc": 0, "red": ""},
                                       "B2": {"file": "B2", "md5": "m2",
                                              "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t3out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "E1-DUP" in out_txt and "SYNC-FINDINGS" in out_txt, out_txt
    _, rows = read_rows(out)
    assert len(rows) == 2, "去重后应 2 行·实测 %d" % len(rows)
    b1 = [r for r in rows if r["件名"] == "B1"][0]
    assert b1["行数"] == "10" and b1["备注"].startswith("首行"), b1
    return "E1 去重保首行＋逐笔 FINDING＋行数正确"


def sec4_e3_ghost(tmp):
    tsv = wf(os.path.join(tmp, "t4.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "C1\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p4.json"),
               json.dumps({"records": {
                   "C1": {"file": "C1", "md5": "m1", "rc": 0, "red": ""},
                   "GhostA": {"file": "GhostA", "md5": "g1", "rc": 1, "red": "x"},
                   "GhostB": {"file": "GhostB", "md5": "g2", "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t4out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "E3-GHOST" in out_txt, out_txt
    assert "GhostA" in out_txt and "GhostB" in out_txt, "幽灵名单应响亮"
    _, rows = read_rows(out)
    assert len(rows) == 1, "幽灵禁落行·实测 %d 行" % len(rows)
    return "E3 幽灵只记账不落行"


def sec5_special_tags(tmp):
    tsv = wf(os.path.join(tmp, "t5.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "D1\t10\tm1\t0\tUNPROBED\t\n"
             "D2\t20\tm2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p5.json"),
               json.dumps({"records": {
                   "D1": {"file": "D1", "md5": "m1", "rc": 124, "red": "TIMEOUT"},
                   "D2": {"file": "D2", "md5": "m2", "rc": "NO_SRC", "red": ""}}}))
    out = os.path.join(tmp, "t5out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert by["D1"]["备注"] == "probe:timeout" and by["D1"]["状态"] == "UNPROBED", by["D1"]
    assert by["D2"]["备注"] == "probe:no-src" and by["D2"]["状态"] == "UNPROBED", by["D2"]
    return "timeout/no-src 特异 tag＋UNPROBED 不升格"


def sec6_no_md5(tmp):
    tsv = wf(os.path.join(tmp, "t6.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "E1x\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p6.json"),
               json.dumps({"E1x": {"file": "E1x", "rc": 0, "red": ""}}))  # W13 裸形无 md5
    out = os.path.join(tmp, "t6out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "NO-MD5" in out_txt, out_txt
    _, rows = read_rows(out)
    assert rows[0]["备注"] == "probe:rc0" and rows[0]["状态"] == "UNPROBED", rows[0]
    return "NO-MD5 老式账只注记不升格"


def sec7_report(tmp):
    tsv = wf(os.path.join(tmp, "t7.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "F1\t10\tm1\t0\tUNPROBED\t\n"
             "F2\t10\tWRONG\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p7.json"),
               json.dumps({"records": {
                   "F1": {"file": "F1", "md5": "m1", "rc": 0, "red": ""},
                   "F2": {"file": "F2", "md5": "m2", "rc": 0, "red": ""},
                   "F3": {"file": "F3", "md5": "m3", "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t7out.tsv")
    rep = os.path.join(tmp, "r7.json")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out,
                       "--report", rep])
    assert rc == 1, out_txt
    acc = json.load(io.open(rep, encoding="utf-8"))
    assert acc["schema"] == ls.SCHEMA, acc.get("schema")
    assert acc["counts"] == {"E3-GHOST": 1, "MD5-DRIFT": 1}, acc["counts"]
    codes = sorted(f["code"] for f in acc["findings"])
    assert codes == ["E3-GHOST", "MD5-DRIFT"], codes
    assert acc["rows"] == 2 and acc["synced"] == 2, acc
    return "report JSON schema/counts/逐笔发现咬合"


def sec8_cli_and_idempotent(tmp):
    tsv = wf(os.path.join(tmp, "t8.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "G1\t10\tm1\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "p8.json"),
               json.dumps({"records": {"G1": {"file": "G1", "md5": "m1",
                                              "rc": 0, "red": ""}}}))
    out = os.path.join(tmp, "t8out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0, out_txt
    before = io.open(out, "rb").read()
    rc2, out2 = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc2 == 0 and io.open(out, "rb").read() == before, "幂等重跑漂移"
    # CLI 四码
    rc, out_txt = run(["--help"])
    assert rc == 0 and "usage" in out_txt, out_txt[-200:]
    rc, out_txt = run(["--bogus"])
    assert rc == 2, "未知形参应 rc=2 实测 %d" % rc
    rc, out_txt = run([])
    assert rc == 2, "缺参数应 rc=2 实测 %d" % rc
    rc, out_txt = run(["--probe", os.path.join(tmp, "no.json"),
                       "--ledger", tsv, "--out", out])
    assert rc == 9, "缺文件应 rc=9 实测 %d" % rc
    # 列校验两变体（缺列/行宽）rc2 不产出
    bad = wf(os.path.join(tmp, "bad8.tsv"), "件名\tmd5\nG1\tm1\n")
    o2 = os.path.join(tmp, "bad8out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", bad, "--out", o2])
    assert rc == 2 and "缺必需列" in out_txt and not os.path.exists(o2), out_txt
    ragged = wf(os.path.join(tmp, "rag8.tsv"),
                "件名\t行数\tmd5\tRED\t状态\t备注\nG1\t1\tm1\t0\n")
    rc, out_txt = run(["--probe", probe, "--ledger", ragged, "--out", o2])
    assert rc == 2 and "行宽不齐" in out_txt and not os.path.exists(o2), out_txt
    return "CLI 四码＋列校验两变体 rc2 不产出＋幂等重跑字节恒同"


def sec9_items_shell_and_meta(tmp):
    # 9a: seat freeze-ledger shell (items subkey) consumed directly;
    # shell keys (schema/queue/world) never become phantom probe names
    tsv = wf(os.path.join(tmp, "t9.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "I1\t10\tmi1\t0\tUNPROBED\t\n")
    probe = os.path.join(tmp, "freeze.json")
    with io.open(probe, "w", encoding="utf-8") as fh:
        json.dump({"schema": "seat-freeze/1",
                   "items": {"I1": {"file": "I1", "md5": "mi1",
                                    "rc": 0, "red": ""}},
                   "queue": [], "world": "/tmp/w"}, fh)
    out = os.path.join(tmp, "t9out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 0 and "SYNC-CLEAN" in out_txt, "%d %s" % (rc, out_txt)
    assert "E3-GHOST" not in out_txt, "壳键漏读误报幽灵＝v2.1 前缺陷复现"
    _, rows = read_rows(out)
    assert rows[0]["状态"] == "WASHABLE" and rows[0]["备注"] == "probe:rc0", rows[0]
    # 9b: bare-dict form with batch_meta sibling — meta skipped loudly,
    # zero phantom ghost, record synced
    tsv = wf(os.path.join(tmp, "t9b.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "I2\t10\tmi2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "bare_meta.json"),
               json.dumps({"I2": {"file": "I2", "md5": "mi2", "rc": 0,
                                  "red": ""},
                           "batch_meta": {"seat": "W9",
                                          "ledger_basis": "x.tsv"}}))
    out = os.path.join(tmp, "t9bout.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out,
                       "--report", os.path.join(tmp, "t9rep.json")])
    assert rc == 0 and "PROBE-META-SKIP" in out_txt, out_txt
    assert "batch_meta" in out_txt, "元数据键应响亮留痕"
    assert "E3-GHOST" not in out_txt, out_txt
    acc = json.load(io.open(os.path.join(tmp, "t9rep.json"), encoding="utf-8"))
    assert acc["meta_skipped"] == ["batch_meta"], acc.get("meta_skipped")
    _, rows = read_rows(out)
    assert rows[0]["状态"] == "WASHABLE", rows[0]
    # 9c: bare-dict all-meta (zero records) — fail-loud rc2, no output
    probe = wf(os.path.join(tmp, "all_meta.json"),
               json.dumps({"schema": "x/1", "batch_meta": {"seat": "W9"}}))
    out = os.path.join(tmp, "t9cout.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger",
                       wf(os.path.join(tmp, "t9c.tsv"),
                          "件名\t行数\tmd5\tRED\t状态\t备注\n"
                          "I3\t1\tm\t0\tUNPROBED\t\n"),
                       "--out", out])
    assert rc == 2 and "零记录" in out_txt, out_txt
    assert not os.path.exists(out), "零记录拒同步仍产出＝违例"
    return "items 壳直吞＋壳键零幽灵＋batch_meta 响亮滤除＋全元数据 rc2 拒同步"


def sec10_gen_divergence(tmp):
    tsv = wf(os.path.join(tmp, "t10.tsv"),
             "件名\t行数\tmd5\tRED\t状态\t备注\n"
             "D1\t10\tmd1\t0\tUNPROBED\t\n"
             "D2\t20\tmd2\t0\tUNPROBED\t\n")
    probe = wf(os.path.join(tmp, "div.json"),
               json.dumps({"records": {
                   "D1": {"file": "D1", "md5": "md1", "rc": 0, "red": "",
                          "source_seats": ["sA", "sB"],
                          "divergence_with": "sB",
                          "divergence_md5": "dmd5"},
                   "D2": {"file": "D2", "md5": "DIFFERENT", "rc": 0,
                          "red": "",
                          "divergence_with": "sC",
                          "divergence_md5": "dmd6"}}}))
    out = os.path.join(tmp, "t10out.tsv")
    rc, out_txt = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc == 1 and "GEN-DIVERGENCE" in out_txt, out_txt
    assert out_txt.count("GEN-DIVERGENCE") >= 2, "两笔分歧均应响亮"
    assert "MD5-DRIFT" in out_txt, "分歧行 md5 漂移应照常出账"
    _, rows = read_rows(out)
    by = {r["件名"]: r for r in rows}
    assert "probe:gen-div:sB" in by["D1"]["备注"], by["D1"]
    assert by["D1"]["状态"] == "WASHABLE", by["D1"]  # md5 咬合升格照常
    assert "probe:gen-div:sC" in by["D2"]["备注"], by["D2"]
    assert by["D2"]["状态"] == "UNPROBED", by["D2"]  # 漂移行不升格
    # 幂等：重跑台账字节恒同（分歧 tag 在盘即跳过）
    before = io.open(out, "rb").read()
    rc2, _ = run(["--probe", probe, "--ledger", tsv, "--out", out])
    assert rc2 == 1 and io.open(out, "rb").read() == before, "分歧注记重跑漂移"
    return "GEN-DIVERGENCE 逐笔响亮＋行注记幂等＋升格口径与漂移一致"


def main():
    tmp = tempfile.mkdtemp(prefix="rocqwash_lsync_test_")
    try:
        secs = [
            ("1 selftest", sec1_selftest),
            ("2 CLEAN 全链", lambda: sec2_clean(tmp)),
            ("3 E1 去重", lambda: sec3_e1_dedup(tmp)),
            ("4 E3 幽灵", lambda: sec4_e3_ghost(tmp)),
            ("5 特异 tag", lambda: sec5_special_tags(tmp)),
            ("6 NO-MD5", lambda: sec6_no_md5(tmp)),
            ("7 报告面", lambda: sec7_report(tmp)),
            ("8 CLI＋幂等", lambda: sec8_cli_and_idempotent(tmp)),
            ("9 items 壳＋元数据", lambda: sec9_items_shell_and_meta(tmp)),
            ("10 分歧出账", lambda: sec10_gen_divergence(tmp)),
        ]
        n = 0
        for name, fn in secs:
            note = fn()
            n += 1
            print("  [%d/10] %-12s OK — %s" % (n, name, note))
        print("TEST-LEDGER-SYNC PASS: 10/10 节全过")
        return 0
    except AssertionError as e:
        print("TEST-LEDGER-SYNC FAIL: %s" % e)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
