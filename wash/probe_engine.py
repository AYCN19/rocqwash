#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_engine.py — 批量闭包相容探针引擎（rocqwash wash/·v30 实战判例工具化·
承 seat_wash13/probe_batch.py 1:1 泛化·20261103 入账）

探针法（闭包相容判定）：把候选件 `<件名>.v` 从源树 cp 入世界目录（世界含播种
.vo 闭包·只读语义），在世界 cwd 直接 `rocq c` 编译一发。退出码即判据：
  rc=0  Require 闭包可装载＋语句面可 elaboration ＝ 相容（可洗可落）；
  rc!=0 记红因原文（世界接口代差/缺依赖族候选）。
一切真编译必经 cpu_guard 包裹（--guard 给出即包裹），退出码无管道真取
（subprocess returncode 直读）。探针后清场：候选件五件产物
(.v/.vo/.glob/.vos/.vok) 移出世界入 --logdir 留证（世界保持播种态纯度）。

输入候选清单 TSV（首行表头·列名定位不按列序）：
  必需列  件名  md5          （md5＝枚举时源件指纹·逐件实测回填 md5_match）
  可选列  RED  行数          （RED＝语句面 RED 站数·rc0 分流必需；缺列时 rc0
                              不作 washable/born-clean 三分·如实出 RC0）

rc 分流（verdict 字段）：
  rc0 + RED>0  → WASHABLE     （闭包相容＋语句面有 RED＝洗形候选）
  rc0 + RED=0  → BORN-CLEAN   （闭包相容＋语句面零 RED＝born-clean 落位候选）
  rc0 + RED缺  → RC0          （RED 未申报·三分不可判·报清单不报清白）
  rc1          → RED-<红因>   （regex 分类，见下）
  rc=124       → TIMEOUT      （--timeout 到点·subprocess.TimeoutExpired）
  源件缺失     → NO-SRC       （--src 下无 <件名>.v·不编译如实出账）

红因分类（rc1·按序首中即断·大小写不敏感）：
  MISSING_LIB  /unable to locate library|cannot find library/   （缺库型·
                捕获库名入 missing 字段）
  ILLEGAL_APP  /illegal application/                             （代差型）
  NO_SUBTERM   /no subterm matching/                             （代差型）
  FACE         /expected to have type|is not convertible/        （面错·载体
                接口代差错配族）
  其余 rc1     → OTHER（有红因原文无分类命中）／UNKNOWN（零红因原文）

幂等（CONTRIBUTING §0 律三）：--out 已在盘时默认 resume——候选件与既有记录
md5 同 ⇒ skip 不重炮；--fresh 推倒重探。同候选集重跑产出同账（记录无时间戳/
无绝对路径·sort_keys 落盘·字节级可复现）。

用法（全部路径参数化·零硬编码）：
  python3 wash/probe_engine.py --candidates cands.tsv --src <源树> --world <世界目录> \
      --out probe_ledger.json --logdir probe_logs/ \
      [--rocq-cmd 'rocq c -Q . "" {name}.v'] [--guard tools/cpu_guard.sh \
       --guard-reg /tmp/cw_reg_probe_engine --guard-front 0 --guard-mid 1 \
       --guard-maxwait 600] [--timeout 1500] [--ulimit-stack 65532] [--fresh]
  python3 wash/probe_engine.py --selftest

退出码：0=批完成台账落盘（rc1 候选是探针产出数据非器红·计数响亮入 stdout）；
2=用法错（--help rc=0／缺必需参数）；9=--candidates/--src/--world/--guard
路径缺失；1=--selftest 红处。台账 schema=rocqwash-probe-ledger/1。
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

PROG = "probe_engine"
SCHEMA = "rocqwash-probe-ledger/1"

# 红因分类 regex（按序首中即断·IGNORECASE）
MISSING_LIB_RE = re.compile(r"(?:unable to locate library|cannot find library)\s+\|?\s*"
                            r"([A-Za-z0-9_']+)", re.IGNORECASE)
CLASS_RES = [
    ("MISSING_LIB", re.compile(r"unable to locate library|cannot find library", re.I)),
    ("ILLEGAL_APP", re.compile(r"illegal application", re.I)),
    ("NO_SUBTERM", re.compile(r"no subterm matching", re.I)),
    ("FACE", re.compile(r"expected to have type|is not convertible", re.I)),
]
RED_LINE_RE = re.compile(r"Error|Cannot find library|Anomaly")

ARTIFACT_EXTS = (".v", ".vo", ".glob", ".vos", ".vok")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_candidates(path):
    """候选清单 TSV → [(name, md5, red_or_None)]（表头列名定位·fail-loud）。"""
    with io.open(path, "r", encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    if not lines:
        raise ValueError("候选清单空文件: %s" % path)
    header = lines[0].split("\t")
    for req in ("件名", "md5"):
        if req not in header:
            raise ValueError("候选清单缺必需列「%s」（表头=%r）" % (req, header))
    i_name = header.index("件名")
    i_md5 = header.index("md5")
    i_red = header.index("RED") if "RED" in header else None
    out = []
    for ln in lines[1:]:
        f = ln.split("\t")
        if len(f) < len(header):
            raise ValueError("候选清单行宽不齐（应 %d 列实 %d 列）: %r"
                             % (len(header), len(f), ln))
        red = None
        if i_red is not None:
            v = f[i_red].strip()
            if v != "":
                red = int(v)
        out.append((f[i_name].strip(), f[i_md5].strip(), red))
    return out


def classify_red(red_text):
    """红因分类：返回 (red_class, missing_lib_or_None)·按序首中即断。"""
    m = MISSING_LIB_RE.search(red_text or "")
    missing = m.group(1) if m else None
    for cls, rx in CLASS_RES:
        if rx.search(red_text or ""):
            return cls, missing
    return (None, missing)


def extract_red(err, out):
    """首个 Error/Cannot find library/Anomaly 行＋续行（库名/细节常在续行）。"""
    lines_all = (err + "\n" + out).split("\n")
    for i, ln in enumerate(lines_all):
        if RED_LINE_RE.search(ln):
            nxt = lines_all[i + 1].strip() if i + 1 < len(lines_all) else ""
            return (ln.strip() + " | " + nxt)[:300]
    return ""


def verdict_rc1(red_text):
    """rc1 红因 verdict：RED-<分类>／RED-OTHER（有原文无命中）／RED-UNKNOWN（无原文）。"""
    cls, _ = classify_red(red_text)
    if cls:
        return "RED-" + cls
    return "RED-OTHER" if (red_text or "").strip() else "RED-UNKNOWN"


def verdict_of_rc(rc, red_count):
    """rc0/124/NO_SRC 面分流（RED 缺列时 rc0 不作三分·如实出 RC0）。"""
    if rc == "NO_SRC":
        return "NO-SRC"
    if rc == 124:
        return "TIMEOUT"
    if red_count is None:
        return "RC0"
    return "WASHABLE" if red_count > 0 else "BORN-CLEAN"


def probe_one(name, src_dir, world_dir, logdir, rocq_cmd, guard, guard_reg,
              guard_front, guard_mid, guard_maxwait, timeout, ulimit_stack):
    """单件探针：cp→编译→真退出码→红因提取→清场。返回记录 dict。"""
    src = os.path.join(src_dir, name + ".v")
    if not os.path.exists(src):
        return {"file": name, "md5": None, "rc": "NO_SRC", "red": "",
                "missing": None, "red_class": "", "verdict": "NO-SRC",
                "red_count": None, "md5_match": None}
    dst = os.path.join(world_dir, name + ".v")
    shutil.copyfile(src, dst)
    inner = ""
    if ulimit_stack:
        inner += "ulimit -s %d; " % ulimit_stack
    inner += rocq_cmd.replace("{name}", name)
    if guard:
        cmd = ["bash", guard, "-Reg", guard_reg,
               "-Front", str(guard_front), "-Mid", str(guard_mid),
               "-MaxWaitSec", str(guard_maxwait), "--", "bash", "-c", inner]
    else:
        cmd = ["bash", "-c", inner]
    try:
        p = subprocess.run(cmd, cwd=world_dir, capture_output=True,
                           text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = e.stdout.decode("utf-8", errors="replace") \
            if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", errors="replace") \
            if isinstance(e.stderr, bytes) else (e.stderr or "")
    with io.open(os.path.join(logdir, name + ".stderr.log"), "w",
                 encoding="utf-8") as f:
        f.write(err + "\n===STDOUT===\n" + out)
    red = extract_red(err, out)
    cls, missing = classify_red(red)
    rec = {"file": name, "md5": md5_of(src), "rc": rc, "red": red,
           "missing": missing, "red_class": cls,
           "verdict": "TIMEOUT" if rc == 124 else
           (verdict_rc1(red) if rc != 0 else "RC0"),
           "red_count": None, "md5_match": None}
    # 清场：五件移出世界入 logdir 留证（世界保持播种态纯度）
    for ext in ARTIFACT_EXTS:
        f = os.path.join(world_dir, name + ext)
        if os.path.exists(f):
            shutil.move(f, os.path.join(logdir, name + ext))
    return rec


def save_ledger(out_path, args, records):
    acc = {"schema": SCHEMA,
           "candidates": args.candidates, "src": args.src, "world": args.world,
           "n_records": len(records),
           "n_washable": sum(1 for r in records.values()
                             if r.get("verdict") == "WASHABLE"),
           "n_born_clean": sum(1 for r in records.values()
                               if r.get("verdict") == "BORN-CLEAN"),
           "n_rc0": sum(1 for r in records.values() if r.get("rc") == 0),
           "n_rc1": sum(1 for r in records.values() if r.get("rc") == 1),
           "records": records}
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(acc, fh, indent=1, ensure_ascii=False, sort_keys=True)


def run_batch(cands, src_dir, world_dir, logdir, args):
    """批量探针（resume 幂等）→ (records, skipped, probes)。"""
    records = {}
    if not args.fresh and os.path.exists(args.out):
        with io.open(args.out, "r", encoding="utf-8") as fh:
            records = json.load(fh).get("records", {})
    skipped, probes = 0, 0
    for name, md5_decl, red_count in cands:
        prev = records.get(name)
        if prev is not None and prev.get("md5") == md5_decl and not args.fresh:
            skipped += 1
            print("SKIP(done) %s rc=%s verdict=%s"
                  % (name, prev.get("rc"), prev.get("verdict")))
            continue
        rec = probe_one(name, src_dir, world_dir, logdir, args.rocq_cmd,
                        args.guard, args.guard_reg, args.guard_front,
                        args.guard_mid, args.guard_maxwait, args.timeout,
                        args.ulimit_stack)
        rec["red_count"] = red_count
        rec["md5_match"] = (md5_decl == rec["md5"]) if rec["md5"] else None
        if rec["rc"] == 0:
            rec["verdict"] = verdict_of_rc(0, red_count)
        records[name] = rec
        probes += 1
        print("PROBE %-42s rc=%s verdict=%s%s"
              % (name, rec["rc"], rec["verdict"],
                 (" RED: " + rec["red"]) if rec["red"] else ""))
        # 逐件增量落盘（中断可续·承原型工艺）
        save_ledger(args.out, args, records)
    return records, skipped, probes


def run_args(argv):
    sys.argv = [PROG] + list(argv)
    try:
        main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def selftest():
    """内嵌冻结向量组（临时目录＋桩探针·零真编译零触真仓）：rc 分流三分
    （BORN-CLEAN/RED-MISSING_LIB）＋resume 幂等同账字节恒同＋CLI 四码。"""
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

    tmp = tempfile.mkdtemp(prefix="rocqwash_probe_self_")
    try:
        src = os.path.join(tmp, "src")
        world = os.path.join(tmp, "world")
        logdir = os.path.join(tmp, "logs")
        for d in (src, world, logdir):
            os.makedirs(d)
        with io.open(os.path.join(src, "PassMe.v"), "w", encoding="utf-8") as fh:
            fh.write("Lemma ok : True.\n")
        with io.open(os.path.join(src, "RedMe.v"), "w", encoding="utf-8") as fh:
            fh.write("Require Import Nope.\n")
        stub = os.path.join(tmp, "stub.sh")
        with io.open(stub, "w", encoding="utf-8") as fh:
            fh.write('#!/bin/bash\ncase "$1" in PassMe*) exit 0;; *)\n'
                     'echo "Error: Unable to locate library | Nope (while'
                     ' searching for a .vos file)." >&2; exit 1;; esac\n')
        os.chmod(stub, 0o755)
        cands = os.path.join(tmp, "cands.tsv")
        with io.open(cands, "w", encoding="utf-8") as fh:
            fh.write("件名\tmd5\tRED\nPassMe\t%s\t0\nRedMe\t%s\t3\n"
                     % (md5_of(os.path.join(src, "PassMe.v")),
                        md5_of(os.path.join(src, "RedMe.v"))))
        led = os.path.join(tmp, "ledger.json")
        tpl = stub + " {name}.v"
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl])
        assert p.returncode == 0, p.stdout
        acc = json.load(io.open(led, encoding="utf-8"))
        assert acc["records"]["PassMe"]["verdict"] == "BORN-CLEAN", acc
        assert acc["records"]["RedMe"]["verdict"] == "RED-MISSING_LIB", acc
        assert acc["records"]["RedMe"]["missing"] == "Nope", acc
        # resume 幂等：重跑同候选集→SKIP 且台账字节恒同
        before = io.open(led, "rb").read()
        p = run(["--candidates", cands, "--src", src, "--world", world,
                 "--out", led, "--logdir", logdir, "--rocq-cmd", tpl])
        assert p.returncode == 0 and "SKIP(done)" in p.stdout, p.stdout
        assert io.open(led, "rb").read() == before, "重跑同账字节漂移＝违例"
        # CLI 四码
        p = run(["--help"])
        assert p.returncode == 0 and "usage" in p.stdout, p.stdout[-200:]
        p = run(["--bogus"])
        assert p.returncode == 2, "未知形参应 rc=2 实测 %d" % p.returncode
        p = run([])
        assert p.returncode == 2, "缺参数应 rc=2 实测 %d" % p.returncode
        p = run(["--candidates", os.path.join(tmp, "nope.tsv"), "--src", src,
                 "--world", world, "--out", os.path.join(tmp, "x.json"),
                 "--logdir", logdir])
        assert p.returncode == 9, "缺清单应 rc=9 实测 %d" % p.returncode
        print("PROBE-ENGINE-SELFTEST PASS: rc 三分(BORN-CLEAN/RED-MISSING_LIB)/"
              "missing 捕获/resume 幂等同账字节恒同/CLI 四码 四判全过")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    ap = argparse.ArgumentParser(
        prog=PROG, description="批量闭包相容探针引擎：候选清单×世界目录→逐件 "
                               "cp→rocq c 真退出码→rc 分流台账（schema "
                               "rocqwash-probe-ledger/1·resume 幂等）")
    ap.add_argument("--candidates", default=None, metavar="FILE",
                    help="候选清单 TSV（必需列 件名/md5·可选列 RED/行数）")
    ap.add_argument("--src", default=None, metavar="DIR",
                    help="源树根（候选件 <件名>.v 取自此）")
    ap.add_argument("--world", default=None, metavar="DIR",
                    help="世界目录（播种 .vo 闭包·探针 cwd）")
    ap.add_argument("--out", default=None, metavar="FILE", help="台账 JSON 出账")
    ap.add_argument("--logdir", default=None, metavar="DIR",
                    help="探针日志＋清场五件留证目录（缺则 --out.logs）")
    ap.add_argument("--rocq-cmd", dest="rocq_cmd",
                    default='rocq c -Q . "" {name}.v', metavar="TPL",
                    help="探针命令模板（含 {name} 占位·默认 'rocq c -Q . \"\" {name}.v'）")
    ap.add_argument("--guard", default=None, metavar="PATH",
                    help="cpu_guard.sh 路径（给则一切探针经其包裹·真编译必给）")
    ap.add_argument("--guard-reg", dest="guard_reg",
                    default="/tmp/cw_reg_probe_engine", metavar="DIR")
    ap.add_argument("--guard-front", dest="guard_front", type=int, default=0)
    ap.add_argument("--guard-mid", dest="guard_mid", type=int, default=1)
    ap.add_argument("--guard-maxwait", dest="guard_maxwait", type=int, default=600)
    ap.add_argument("--timeout", type=int, default=1500,
                    help="单件探针 subprocess 超时秒（到点 rc=124 TIMEOUT）")
    ap.add_argument("--ulimit-stack", dest="ulimit_stack", type=int, default=None,
                    help="内层 ulimit -s 值（缺省不设·正本机惯例 65532）")
    ap.add_argument("--fresh", action="store_true",
                    help="推倒重探（缺省 resume：既有记录 md5 同即 skip）")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    for req, val in (("candidates", args.candidates), ("src", args.src),
                     ("world", args.world), ("out", args.out)):
        if not val:
            print("FAIL-LOUD: --%s 必给（--selftest 除外）" % req, file=sys.stderr)
            sys.exit(2)
    for label, val in (("candidates", args.candidates), ("src", args.src),
                       ("world", args.world)):
        if not os.path.exists(val):
            print("FAIL-LOUD: --%s 路径缺失: %s" % (label, val), file=sys.stderr)
            sys.exit(9)
    if args.guard and not os.path.exists(args.guard):
        print("FAIL-LOUD: --guard 路径缺失: %s" % args.guard, file=sys.stderr)
        sys.exit(9)
    logdir = args.logdir or (args.out + ".logs")
    os.makedirs(logdir, exist_ok=True)

    try:
        cands = load_candidates(args.candidates)
    except ValueError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    records, skipped, probes = run_batch(cands, args.src, args.world,
                                         logdir, args)
    n_wash = sum(1 for r in records.values() if r.get("verdict") == "WASHABLE")
    n_clean = sum(1 for r in records.values() if r.get("verdict") == "BORN-CLEAN")
    n_rc1 = sum(1 for r in records.values() if r.get("rc") == 1)
    n_other = len(records) - n_wash - n_clean - n_rc1
    drift = sorted(n for n, r in records.items() if r.get("md5_match") is False)
    print("== PROBE-ENGINE DONE: 候选 %d（本轮 probe %d / resume skip %d）=="
          % (len(cands), probes, skipped))
    print("verdict 汇总: WASHABLE=%d BORN-CLEAN=%d rc1=%d 其他=%d"
          % (n_wash, n_clean, n_rc1, n_other))
    if drift:
        print("MD5-DRIFT 候选（清单 md5≠源件现测）: %s" % ",".join(drift))
    print("ledger -> %s" % args.out)
    sys.exit(0)


if __name__ == "__main__":
    main()
