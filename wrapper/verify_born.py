#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""verify_born.py — verify/verify_vo.py born 轮判绿接线（rocqwash wrapper/·Mac 适配席 rqadapt·20261031）

gap（本轮补齐对象）：各席 born 轮判绿只读裸 rc 文件（logs/*.born.rc，born 脚本
`echo "$RC" > logs/<名>.born.rc` 一行即收），无人接绿判四件套——exit/rc 一件独大，
log 零 Error／vo 魔数／vo 新鲜度三件缺席（陈 vo 假绿通道敞开）。

fix（本件）：born 轮后接 verify_vo --v/--vo/--exit-file/--log 判绿。verify_vo.py
冻结禁改（嵌记 md5 见 PINNED_MD5·各在飞席位实时引用）——适配一律新文件落 wrapper/，
本件即 born 工件 → verify_vo 的接线器（dispatcher）：

  1. 指认：定位正本 verify/verify_vo.py（绝对路径＋md5＋字节数＋嵌记/附断言比对）。
  2. born rc 形核：读 logs/*.born.rc（strip 后首行，算法 1:1 承 verify_vo
     --exit-file 口径）——
       裸形   `^-?\d+$`            → 原件直喂 --exit-file（口径天然对齐·零改写）；
       前缀形 `KEY=INT`（BORN_RC=0／EXIT=0／BORN_COMPILE_RC=0 等实盘形）→ 首行
              归一化为裸形暂存件（系统临时目录·判后即清）仍走 --exit-file；
       余形                          → FAIL-LOUD exit 2（形不识别绝不判绿）。
  3. 判绿：dispatch `python3 -B verify/verify_vo.py --v V --vo VO --exit-file EF
     [--log LOG] [--json J]`，退出码原样传播（0=PASS／1=FAIL／9=缺件）——判词
     只出正本，本件不背书不代判。

实盘文件形普查（20261031·work_Main_full/sandbox 59 件 *.born.rc 首行）：
  裸 `0`×41（天然对齐面）；前缀 BORN_RC=0×12／BORN_RC=1×2／TN_BORN_RC=0×1／
  PADE_BORN_RC=0×1／EXIT=0×1／BORN_COMPILE_RC=0×1（归一化面·含 2 件真失败件）。

旗标（本件自留）：
  --v PATH           born 轮源 .v（必填）
  --vo PATH          born 轮产物 .vo（必填）
  --rc-file PATH     born rc 文件（必填·别名 --born-rc／--exit-file 同槽·异值双给 exit 2）
  --log PATH         born compile log（可选·透传正本 --log 零 Error 机检）
  --json PATH        正本逐件账 JSON 出账（可选·透传）
  --root DIR         正本仓根（默认＝本件所在仓根）
  --expect-md5 HEX   外部 md5 断言（可重复·全部须等）
  --check-pin        比对嵌记 PINNED_MD5
  --identify         只出指认卡＋rc 形卡，不判绿（断言过 exit 0／败 exit 2）
  --station-selftest 本件自身自检（九判·临时目录驱动零仓写）
  -h / --help        本帮助

裸调（零参数）＝用法＋exit 2（判绿三路径 --v/--vo/--rc-file 必填·不做哑成功）。
断言失败（--check-pin/--expect-md5）＝卡照出（stderr）·绝不带病判绿 exit 2。

退出码：0=四件套 PASS（正本口径）；1=FAIL（正本口径透传）；2=本件用法错/
rc 形不识别/断言败；9=路径缺失（--v/--vo/--rc-file/--log/正本）；127=dispatch OSError。

幂等律：不写正本、不写仓、不写 seat 域——归一化暂存件只落系统临时目录且判后
即清（finally 兜底）；smoke 出账由调用者显式指定到自席沙箱。
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

WRAP_NAME = "wrapper/verify_born.py"
CANONICAL_REL = "verify/verify_vo.py"

# 嵌记（pin）＝20261031 适配席 rqadapt 对正本实测 md5（与更新账 20261031 轮嵌记
# 81524ed0… 全等复核）——正本若经冻终权威改版，须由适配席对实盘重嵌记。
PINNED_MD5 = "81524ed04c2fc7e82a4547972baa7b83"
PINNED_NOTE = "20261031 rqadapt 适配时嵌记"

# 正本 --exit-file 读法（承 verify_vo.py:69-70）：全文 strip → 首行 strip。
# 本件 rc 形核用同一算法，保证裸形原件直喂时正本读数与本件读数恒同。
BARE_RE = re.compile(r"^-?\d+$")
PREFIXED_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(-?\d+)$")

STATION_USAGE = """verify_born — verify/verify_vo.py born 轮判绿接线（wrapper/）

用法 Usage:
  python3 wrapper/verify_born.py --v <file.v> --vo <file.vo> --rc-file <file.born.rc>
                                 [--log <compile.log>] [--json out.json]
                                 [站级旗标...]

born 判绿例（承接 born 脚本 `echo "$RC" > logs/<名>.born.rc` 产物面）:
  python3 wrapper/verify_born.py --v work/S01_BaseRing.v --vo work/S01_BaseRing.vo \\
      --rc-file logs/s01_en.born.rc --log logs/s01_en.born.compile.log

站级旗标 Station flags:
  --root DIR         正本仓根（默认＝本件所在仓根）
  --rc-file PATH     born rc（别名 --born-rc／--exit-file 同槽·异值双给 exit 2）
  --expect-md5 HEX   正本 md5 断言（可重复·全部须等·败则 exit 2 不判绿）
  --check-pin        比对嵌记 PINNED_MD5
  --identify         只出指认卡＋rc 形卡，不判绿
  --station-selftest 本件自检（九判）
  -h / --help        本帮助

退出码: 0=四件套 PASS  1=FAIL（正本口径透传）  2=用法错/rc 形不识别/断言败
  9=路径缺失  其余=正本口径透传
"""


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_hex(s):
    """断言值形制核：剥空白/引号、小写；非 32 位 hex 回 None（承 scan_station 同款）。"""
    t = s.strip().strip("'\"").lower()
    if len(t) == 32 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def default_root():
    """默认正本仓根＝本件文件的上上级目录（wrapper/ 的父目录）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_canonical(root):
    """指认正本：root/verify/verify_vo.py 存在则返回绝对路径，否则 None。"""
    if not root:
        return None
    p = os.path.join(os.path.abspath(root), *CANONICAL_REL.split("/"))
    return p if os.path.isfile(p) else None


def assert_md5(actual, expects, check_pin):
    """md5 断言核：expects 全部须等（＋可选嵌记）；回 (ok, [(want, match), ...])。"""
    wants = []
    for e in expects:
        v = norm_hex(e)
        wants.append((e if v is None else v, (v if v is not None else e) == actual))
    if check_pin:
        wants.append((PINNED_MD5, PINNED_MD5 == actual))
    ok = all(m for _, m in wants)
    return ok, wants


def read_born_rc_first_line(path):
    """born rc 首行读法——1:1 承正本 --exit-file 算法（verify_vo.py:69-70）：
    全文 strip → 首行 strip。"""
    content = io.open(path, encoding="utf-8", errors="replace").read().strip()
    if not content:
        return ""
    return content.splitlines()[0].strip()


def classify_born_rc(path):
    """born rc 形核。回 (shape, value, first_line)：
      shape ∈ bare（裸形·原件直喂）| prefixed（前缀形·归一化暂存）| unrecognized。
    """
    first = read_born_rc_first_line(path)
    if BARE_RE.match(first):
        return "bare", first, first
    m = PREFIXED_RE.match(first)
    if m:
        return "prefixed", m.group(2), first
    return "unrecognized", None, first


def parse_args(argv):
    """本件旗标解析。缺值/冲突 raise ValueError（站级用法错 exit 2）。"""
    st = {"v": None, "vo": None, "rc_file": None, "log": None, "json": None,
          "root": None, "expect_md5": [], "check_pin": False,
          "identify": False, "selftest": False, "help": False}
    i, n = 0, len(argv)
    while i < n:
        a = argv[i]
        if a in ("-h", "--help"):
            st["help"] = True; i += 1; continue
        if a == "--station-selftest":
            st["selftest"] = True; i += 1; continue
        if a == "--identify":
            st["identify"] = True; i += 1; continue
        if a == "--check-pin":
            st["check_pin"] = True; i += 1; continue
        if a == "--" :  # 显式边界：此后不再收本件旗标（防吞正本侧同名参）
            raise ValueError("`--` 不在本件契约内（判绿三路径请显式给 --v/--vo/--rc-file）")
        val_flags = ["--v", "--vo", "--log", "--json", "--root",
                     "--rc-file", "--born-rc", "--exit-file"]
        hit = None
        if a == "--expect-md5" or a.startswith("--expect-md5="):
            if "=" in a:
                st["expect_md5"].append(a.split("=", 1)[1])
            else:
                i += 1
                if i >= n:
                    raise ValueError("--expect-md5 需要断言值（32 位 hex）")
                st["expect_md5"].append(argv[i])
            i += 1; continue
        for f in val_flags:
            if a == f or a.startswith(f + "="):
                hit = f; break
        if hit is None:
            raise ValueError("未知旗标: %s" % a)
        if "=" in a:
            val = a.split("=", 1)[1]
        else:
            i += 1
            if i >= n:
                raise ValueError("%s 需要路径参数" % hit)
            val = argv[i]
        slot = {"--rc-file": "rc_file", "--born-rc": "rc_file",
                "--exit-file": "rc_file"}.get(hit)
        if slot is None:
            slot = {"--v": "v", "--vo": "vo", "--log": "log",
                    "--json": "json", "--root": "root"}[hit]
        if st[slot] is not None and st[slot] != val:
            raise ValueError("%s 与已给值 %s 同槽异值冲突" % (a, st[slot]))
        st[slot] = val
        i += 1
    return st


def station_card(canonical, actual, expects, check_pin, st, shape=None):
    """指认卡＋born rc 形卡（纯文本·不落盘）。"""
    ok, wants = assert_md5(actual, expects, check_pin)
    lines = []
    lines.append("== verify_born 指认卡（%s）==" % WRAP_NAME)
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
    lines.append("frozen:    正本冻结禁改——本件只指认＋born rc 形核＋dispatch，禁写正本")
    if st is not None and st.get("rc_file"):
        lines.append("rc_file:   %s" % st["rc_file"])
        if shape:
            lines.append("rc_shape:  %s（首行=%r%s）" % (
                shape[0], shape[2],
                "→ 原件直喂 --exit-file" if shape[0] == "bare"
                else "→ 归一化 %s 暂存件 --exit-file" % shape[1] if shape[0] == "prefixed"
                else "→ FAIL-LOUD exit 2"))
    if st is not None and st.get("identify"):
        lines.append("dispatch:  未判绿（--identify）")
    lines.append("verdict:   %s" % ("PASS" if ok else "FAIL（md5 断言不符·不带病判绿）"))
    return lines, ok


def dispatch(canonical, st, shape):
    """判绿 dispatch：python3 -B 正本 --v/--vo/--exit-file [--log/--json]，
    退出码原样传播。回正本退出码。"""
    tmpdir = None
    try:
        if shape[0] == "bare":
            ef = st["rc_file"]           # 天然对齐：born rc 即正本口径的 exit-file
            banner = "rc形=裸形 rc=%s → 原件直喂 --exit-file" % shape[1]
        elif shape[0] == "prefixed":
            tmpdir = tempfile.mkdtemp(prefix="verify_born_norm_")
            ef = os.path.join(tmpdir, "born.rc.normalized")
            with io.open(ef, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(shape[1] + "\n")
            banner = "rc形=前缀形 首行=%r → 归一化 rc=%s（暂存判后即清）" % (shape[2], shape[1])
        else:
            print("FAIL-LOUD: born rc 形不识别（首行=%r）——绝不判绿" % shape[2],
                  file=sys.stderr)
            return 2
        cmd = [sys.executable or "python3", "-B", canonical,
               "--v", st["v"], "--vo", st["vo"], "--exit-file", ef]
        if st["log"]:
            cmd += ["--log", st["log"]]
        if st["json"]:
            cmd += ["--json", st["json"]]
        print("[verify_born] 正本指认 md5=%s（%s）｜%s｜dispatch %d 参 → %s"
              % (md5_of(canonical), PINNED_NOTE, banner, len(cmd) - 3,
                 os.path.relpath(canonical, default_root())),
              file=sys.stderr)
        try:
            return subprocess.call(cmd)
        except OSError as e:
            print("verify_born: dispatch 失败（OSError）: %s" % e, file=sys.stderr)
            return 127
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)   # 归一化暂存件判后即清


def station_selftest():
    """本件自身自检（九判·临时目录驱动·零仓写）。回 pass 布尔。

    向量组：裸形正/负·前缀形正/负·陈 vo 负·脏 log 负·缺件 9·形不识别 2·嵌记断言。
    魔数取正本冻结口径 verify_vo.py:40 VO_MAGIC_HEX="436f712100015ff4"——正判向量
    须经正本实判 rc=0，故本自检同时耦合证明正本魔数口径未漂。
    """
    ok = True
    tmp = tempfile.mkdtemp(prefix="verify_born_self_")
    try:
        MAGIC = "436f712100015ff4"   # 承 verify_vo.py:40 冻结口径
        v = os.path.join(tmp, "probe.v")
        vo = os.path.join(tmp, "probe.vo")
        with io.open(v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma t : True.\nProof. exact I. Qed.\n")
        with open(vo, "wb") as f:
            f.write(bytes.fromhex(MAGIC) + b"\x00JUNK")
        t_v, t_vo = 1000000000, 1000000100
        os.utime(v, (t_v, t_v))
        os.utime(vo, (t_vo, t_vo))

        def run(args):
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__)] + args,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return (p.returncode,
                    p.stdout.decode("utf-8", "replace"),
                    p.stderr.decode("utf-8", "replace"))

        def rc_file(name, text):
            p = os.path.join(tmp, name)
            with io.open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            return p

        base = ["--v", v, "--vo", vo]

        # 判1 裸形正判：born.rc "0\n" 原件直喂 → 0（天然对齐面·横幅含「裸形」）
        rf = rc_file("bare0.born.rc", "0\n")
        rc, _, err = run(base + ["--rc-file", rf])
        j = (rc == 0 and "裸形" in err and "原件直喂" in err)
        print("  judge1 裸形 born.rc 原件直喂正判 rc=0:", "PASS" if j else "FAIL",
              "" if j else "rc=%s err=%r" % (rc, err[:200]))
        ok = ok and j

        # 判2 前缀形正判：BORN_RC=0 → 归一化暂存 → 0（横幅含归一化 rc=0）
        rf = rc_file("pre0.born.rc", "BORN_RC=0\n")
        rc, _, err = run(base + ["--born-rc", rf])
        j = (rc == 0 and "前缀形" in err and "归一化 rc=0" in err)
        print("  judge2 前缀形 BORN_RC=0 归一化正判 rc=0:", "PASS" if j else "FAIL",
              "" if j else "rc=%s err=%r" % (rc, err[:200]))
        ok = ok and j

        # 判3 前缀形负判：BORN_RC=1（实盘真失败形）→ 1（正本 FAIL 口径透传）
        rf = rc_file("pre1.born.rc", "BORN_RC=1\n")
        rc, _, _ = run(base + ["--rc-file", rf])
        j = (rc == 1)
        print("  judge3 前缀形 BORN_RC=1 负判 rc=1:", "PASS" if j else "FAIL", "rc=%s" % rc)
        ok = ok and j

        # 判4 裸形负判：born.rc "2" → 1
        rf = rc_file("bare2.born.rc", "2\n")
        rc, _, _ = run(base + ["--exit-file", rf])
        j = (rc == 1)
        print("  judge4 裸形 rc=2 负判 rc=1:", "PASS" if j else "FAIL", "rc=%s" % rc)
        ok = ok and j

        # 判5 陈 vo 负判（四件套新鲜度经本件可达）：v 拨未来 → 1
        stale = os.path.getmtime(vo) + 50
        os.utime(v, (stale, stale))
        rf = rc_file("fresh.born.rc", "0\n")
        rc, _, _ = run(base + ["--rc-file", rf])
        j = (rc == 1)
        print("  judge5 陈 vo 假绿通道负判 rc=1:", "PASS" if j else "FAIL", "rc=%s" % rc)
        ok = ok and j
        os.utime(v, (t_v, t_v))   # 残效清账

        # 判6 脏 log 负判（--log 透传零 Error 机检）：带 Error 行 → 1
        rf = rc_file("ok.born.rc", "0\n")
        logbad = os.path.join(tmp, "bad.compile.log")
        with io.open(logbad, "w", encoding="utf-8") as fh:
            fh.write("[cpu_guard] MID launch\nError: foo\n")
        rc, _, _ = run(base + ["--rc-file", rf, "--log", logbad])
        j = (rc == 1)
        print("  judge6 脏 compile log 负判 rc=1:", "PASS" if j else "FAIL", "rc=%s" % rc)
        ok = ok and j

        # 判7 缺件 9：--v 指向不存在路径
        rf = rc_file("any.born.rc", "0\n")
        rc, _, err = run(["--v", os.path.join(tmp, "gone.v"), "--vo", vo,
                          "--rc-file", rf])
        j = (rc == 9 and "路径缺失" in err)
        print("  judge7 缺 .v 路径 rc=9:", "PASS" if j else "FAIL",
              "" if j else "rc=%s err=%r" % (rc, err[:200]))
        ok = ok and j

        # 判8 形不识别 2：首行非裸形非 KEY=INT → FAIL-LOUD 绝不判绿
        rf = rc_file("junk.born.rc", "hello born\n")
        rc, _, err = run(base + ["--rc-file", rf])
        j = (rc == 2 and "形不识别" in err)
        print("  judge8 rc 形不识别 rc=2:", "PASS" if j else "FAIL",
              "" if j else "rc=%s err=%r" % (rc, err[:200]))
        ok = ok and j

        # 判9 嵌记断言核：--check-pin 正过（identify 面）；伪 --expect-md5 败拒 rc=2
        rc, out, _ = run(["--check-pin", "--identify"])
        j1 = (rc == 0 and "pin_match: True" in out)
        rc2, out2, _ = run(["--expect-md5", "0123456789abcdef0123456789abcdef",
                            "--identify"] + base + ["--rc-file",
                            rc_file("id.born.rc", "0\n")])
        j2 = (rc2 == 2 and "FAIL（md5 断言不符" in out2)
        j = (j1 and j2)
        print("  judge9 嵌记正过＋伪断言败拒 rc=2:", "PASS" if j else "FAIL",
              "" if j else "j1 rc=%s j2 rc=%s" % (rc, rc2))
        ok = ok and j

        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        st = parse_args(argv)
    except ValueError as e:
        print("verify_born: 用法错: %s" % e, file=sys.stderr)
        print(STATION_USAGE, file=sys.stderr)
        sys.exit(2)

    if st["help"]:
        print(STATION_USAGE, end="")
        sys.exit(0)

    if st["selftest"]:
        p = station_selftest()
        print("STATION-SELFTEST (verify_born 九判·零仓写):", "PASS" if p else "FAIL")
        sys.exit(0 if p else 2)

    root = st["root"] if st["root"] else default_root()
    canonical = find_canonical(root)
    if canonical is None:
        print("verify_born: 正本缺失: %s（于仓根 %s）" % (CANONICAL_REL, root),
              file=sys.stderr)
        sys.exit(9)

    actual = md5_of(canonical)

    if st["identify"]:
        shape = None
        if st["rc_file"]:
            if not os.path.isfile(st["rc_file"]):
                print("FAIL-LOUD: --rc-file 路径缺失: %s" % st["rc_file"], file=sys.stderr)
                sys.exit(9)
            shape = classify_born_rc(st["rc_file"])
        lines, ok2 = station_card(canonical, actual, st["expect_md5"],
                                  st["check_pin"], st, shape=shape)
        print("\n".join(lines))
        sys.exit(0 if ok2 else 2)

    # 判绿面：三路径必填（裸调＝哑成功禁律）
    missing = [f for f, k in (("--v", "v"), ("--vo", "vo"), ("--rc-file", "rc_file"))
               if not st[k]]
    if missing:
        print("verify_born: 判绿三路径必填，缺: %s" % " ".join(missing), file=sys.stderr)
        print(STATION_USAGE, file=sys.stderr)
        sys.exit(2)

    # 路径预核（fail-loud 9·正本 dispatch 前置·不浪费一次空跑）
    for label, path in (("--v", st["v"]), ("--vo", st["vo"]),
                        ("--rc-file", st["rc_file"])):
        if not os.path.isfile(path):
            print("FAIL-LOUD: %s 路径缺失: %s" % (label, path), file=sys.stderr)
            sys.exit(9)
    if st["log"] and not os.path.isfile(st["log"]):
        print("FAIL-LOUD: --log 路径缺失: %s" % st["log"], file=sys.stderr)
        sys.exit(9)

    # 断言核：败则卡照出（stderr）·绝不带病判绿
    ok, _ = assert_md5(actual, st["expect_md5"], st["check_pin"])
    shape = classify_born_rc(st["rc_file"])
    if not ok or shape[0] == "unrecognized":
        lines, _ = station_card(canonical, actual, st["expect_md5"],
                                st["check_pin"], st, shape=shape)
        print("\n".join(lines), file=sys.stderr)
        if not ok:
            sys.exit(2)
        # 形不识别的 FAIL-LOUD 由 dispatch 出（exit 2 口径一致）

    sys.exit(dispatch(canonical, st, shape))


if __name__ == "__main__":
    main()
