#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world_hook.py — wash_engine 世界基校验钩子（rocqwash wash/·20261101 agent rqsupport）

五课反馈轮打磨件①（nw5 课工具化）：**born 世界必须=RUNTREE 认证代 cp·禁自带旧代**。
判例源：`sandbox/seat_nw5ver/账/world_md5_assert*.txt`（树世界 md5 对源断言 manifest·
20261031 15:08 定格）＋`world_md5_assert_npw.txt` ASSERT4（seat_nw5 自带旧代 world 副本
对 tree 副本 WDIFF×14／WMISS×2 实录——自带旧代即雷）。本钩子把该纪律接到洗刀 born 前：
**洗产物落盘（born）之前**，先机械断言目标世界目录的 .vo 基座与认证代锚逐件全等；
断言不过＝exit 9 fail-loud，洗引擎一步都不跑（零半态）。

冻结边界（在役八组件冻结禁改·支撑一律新文件或配置层）：
  - `wash/wash_engine.py` md5 `664446bc717395d8496c8c30a5af9ccf`＝在役冻结件，本件
    **零字节不触**；经 sys.path＋`import wash_engine` **只读复用**其 run_args/main
    （push_gate→freeze_manifest 同款只读 import 判例·certify/push_gate.py:81-86）；
  - 旁注：`wrapper/born_world.sh`（rqadapt 轮）已在 born 层固化 .v 源侧三防线（现拷/
    --assert-md5/清陈产物）；本件补的是**洗刀侧**（wash_engine 台账洗 born 前）的
    世界基 .vo 断言——两层并存不互代：born_world 管世界怎么建，本件管洗产物能不能落。

认证代锚（参数化可配）：
  - 缺省＝nw5ver 判例在册五锚（20261031 15:08 复拍定格·.vo 口径）：
      S01_BaseRing=7c769ae31caa921d214d74484e1e962a
      S02_CauchyComplete=b8c5df6c1a77bbfb3af3ac3bc4699a0c
      S03_QExp=2a7427f01873e4aa63cd062316a69763
      UpReqLpoEquiv=7c15280b116da4f63323c45dc95a6377
      EntropyUnsatMark=4792cb7c7c0f66e9f72850d85e81b24d
  - `--manifest <file>` 整表换锚（两行形皆收：「<md5>␠␠<名>.vo…」表列形＝
    world_md5_assert.txt 实盘形；「MD5 (<名>.vo) = <md5>」默认形。只认 .vo 行——
    世界基是编译产物面；#注释行忽略；无可解析 .vo 锚行＝畸形 exit 2）；
  - `--anchor 名=md5` 单点加锚/覆锚（覆盖缺省同名锚）。
  世界若重建过新代，锚必随代换——禁拿旧代锚冒充认证代（判例：Set 树 S01 vo
  07dccf47 系 Oct18 旧代·候批账-nw6批.md §三实录）。

用法：
  # ① 断言-only（born 前世界基闸·可独立于洗刀用）：
  python3 wash/world_hook.py --world <目录> [--manifest M | --anchor 名=md5 …]
  # ② 洗刀钩子：`--` 前＝钩子形参，`--` 后＝wash_engine 形参逐字透传：
  python3 wash/world_hook.py --world <目录> [--manifest M] -- \\
      --file <in.v> --patch <ledger.json> --out <out.v> [--dry-run] [--json …]
  # ③ 自证：
  python3 wash/world_hook.py --selftest

退出码：0=断言过（透传形再透传引擎 rc）；1=引擎判 FAIL 透传（文件未落盘·引擎口径）；
        2=钩子用法错/manifest 畸形；3=引擎 SKIP 语义透传（无台账·引擎口径）；
        9=世界基断言不过（WDIFF/WMISS）或路径缺失（fail-loud·引擎未跑·零落盘）。
写隔离：本件自身零写盘（只读断言＋出账 stdout）；透传形的写盘面全归引擎契约
（--out 显式才落·永不回写 --file）。
"""
import argparse
import hashlib
import io
import os
import re
import sys

PROG = "world_hook"

# —— nw5ver 判例在册五锚（world_md5_assert.txt 15:08 复拍定格·.vo 口径）——————
BUILTIN_ANCHORS = {
    "S01_BaseRing": "7c769ae31caa921d214d74484e1e962a",
    "S02_CauchyComplete": "b8c5df6c1a77bbfb3af3ac3bc4699a0c",
    "S03_QExp": "2a7427f01873e4aa63cd062316a69763",
    "UpReqLpoEquiv": "7c15280b116da4f63323c45dc95a6377",
    "EntropyUnsatMark": "4792cb7c7c0f66e9f72850d85e81b24d",
}

_MD5_RE = re.compile(r"[0-9a-fA-F]{32}")
# 全词匹配 <名>.vo——防 UpReqBanach 误咬 UpReqBanachExp（born_world assert_md5 同律）
_ROW_RE = lambda name: re.compile(r"(^|[^A-Za-z0-9_])" + re.escape(name) + r"\.vo([^A-Za-z0-9_]|$)")


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path):
    """manifest → {名: md5}（只认 .vo 行·#注释忽略·两行形兼容）。

    行形 A（world_md5_assert.txt 实盘表列形）: "7c769ae…  S01_BaseRing.vo  OK"
    行形 B（md5 默认形）:                     "MD5 (S01_BaseRing.vo) = 7c769ae…"
    无任何 .vo 锚行＝畸形，raise HookError（宁 fail-loud 不哑比——world 断言面
    拿错账比没账更危险·nw5 雷防线②同律「只认源行」的 .vo 镜像）。
    """
    anchors = {}
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.search(r"([A-Za-z_][A-Za-z0-9_']*)\.vo", line)
            if not m:
                continue
            name = m.group(1)
            hexes = _MD5_RE.findall(line)
            if not hexes:
                raise HookError("manifest 第 %d 行有 .vo 名无 32-hex md5: %s"
                                % (lineno, stripped))
            if name in anchors and anchors[name] != hexes[0].lower():
                raise HookError("manifest 内 %s.vo 锚值自相矛盾: %s vs %s"
                                % (name, anchors[name], hexes[0].lower()))
            anchors[name] = hexes[0].lower()
    if not anchors:
        raise HookError("manifest 无可解析 .vo 锚行（只认 .vo 行）: %s" % path)
    return anchors


def parse_anchor_args(pairs):
    """--anchor 名=md5 逐项解析（单点加锚/覆锚）。"""
    out = {}
    for p in pairs:
        if "=" not in p:
            raise HookError("--anchor 形参须 名=md5（实测 %r）" % p)
        name, _, val = p.partition("=")
        name, val = name.strip(), val.strip().lower()
        if not name or not re.fullmatch(r"[0-9a-f]{32}", val):
            raise HookError("--anchor 值须 32-hex md5（实测 %r）" % p)
        out[name] = val
    return out


def assert_world_base(world_dir, anchors):
    """世界基断言：逐锚对 world/<名>.vo 现拍 md5。返回 (ok, rows)。

    rows 三态（判例词面）：
      MATCH  — md5 全等（判例形「ANCHOR <名>.vo <md5> MATCH」）
      WDIFF  — 在场但 md5 不等（自带旧代＝nw5 雷·npw ASSERT4 WDIFF 判例词）
      WMISS  — 缺件（npw ASSERT4 WMISS 判例词）
    ok=False 当且仅当存在 WDIFF/WMISS。
    """
    rows, ok = [], True
    for name in sorted(anchors):
        want = anchors[name]
        vo = os.path.join(world_dir, name + ".vo")
        if not os.path.isfile(vo):
            rows.append({"code": "WMISS", "name": name + ".vo", "want": want, "got": None})
            ok = False
            continue
        got = md5_of(vo)
        if got == want:
            rows.append({"code": "MATCH", "name": name + ".vo", "want": want, "got": got})
        else:
            rows.append({"code": "WDIFF", "name": name + ".vo", "want": want, "got": got})
            ok = False
    return ok, rows


class HookError(Exception):
    pass


def selftest():
    """内嵌向量组（临时目录驱动·零真仓零真世界）：
    pos／WDIFF 负（nw5 雷·引擎拦截零落盘）／WMISS 负／manifest 双形＋畸形负／
    --anchor 覆锚／透传正判（born 前·engine rc 透传）／断言-only／缺目录 9。
    """
    import json
    import shutil
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    hook = os.path.join(here, "world_hook.py")
    engine = os.path.join(here, "wash_engine.py")
    for f in (hook, engine):
        if not os.path.isfile(f):
            print("FAIL-LOUD: 同侪件缺失: %s" % f, file=sys.stderr)
            return 9

    tmp = tempfile.mkdtemp(prefix="rocqwash_worldhook_self_")

    def run(args):
        p = subprocess_run([sys.executable, "-B", hook] + args)
        return p

    try:
        A = "a" * 32
        # —— 世界夹具：内置五锚名各一 .vo（内容互异·现拍 md5 为「认证代」）——
        world = os.path.join(tmp, "world")
        os.makedirs(world)
        s = {}
        for k, name in enumerate(sorted(BUILTIN_ANCHORS)):
            fp = os.path.join(world, name + ".vo")
            with io.open(fp, "wb") as fh:
                fh.write(("VO-%02d-%s\n" % (k, name)).encode())
            s[name] = md5_of(fp)
        anchor_args = []
        for name in sorted(s):
            anchor_args += ["--anchor", "%s=%s" % (name, s[name])]

        # ① pos：断言-only（--anchor 五锚逐点覆内置）→ rc 0·MATCH 词面
        p = run(["--world", world] + anchor_args)
        assert p.returncode == 0, "pos 应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        assert "MATCH" in p.stdout and "WORLD-BASE-OK" in p.stdout, p.stdout

        # ② nw5 雷负判：锚值=旧代（≠现拍）→ rc 9·WDIFF 词面·零写盘
        p = run(["--world", world] + anchor_args[:2] + ["--anchor", "S01_BaseRing=" + A])
        assert p.returncode == 9, "WDIFF 应 rc=9 实测 %d" % p.returncode
        assert "WDIFF" in p.stdout and "WORLD-BASE-RED" in p.stdout, p.stdout

        # ③ WMISS 负判：锚名在盘无件 → rc 9·WMISS 词面
        p = run(["--world", world, "--anchor", "Absent_Mod=00000000000000000000000000000000"])
        assert p.returncode == 9, "WMISS 应 rc=9 实测 %d" % p.returncode
        assert "WMISS" in p.stdout, p.stdout

        # ④ manifest 表列形（world_md5_assert.txt 实盘形·五锚全表）→ rc 0
        man = os.path.join(tmp, "man_table.txt")
        with io.open(man, "w", encoding="utf-8") as fh:
            fh.write("# 注释行忽略\n")
            for name in sorted(s):
                fh.write("%s  %s.vo  OK\n" % (s[name], name))
        p = run(["--world", world, "--manifest", man])
        assert p.returncode == 0, "manifest 表列形应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)

        # ⑤ manifest 默认形（MD5 (名.vo) = …）→ rc 0
        man2 = os.path.join(tmp, "man_default.txt")
        with io.open(man2, "w", encoding="utf-8") as fh:
            for name in sorted(s):
                fh.write("MD5 (%s.vo) = %s\n" % (name, s[name]))
        p = run(["--world", world, "--manifest", man2])
        assert p.returncode == 0, "manifest 默认形应 rc=0 实测 %d" % p.returncode

        # ⑥ manifest 畸形负判：有 .vo 名无 hex / 全注释 → rc 2
        bad = os.path.join(tmp, "man_bad.txt")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("# 只注释\n")
        p = run(["--world", world, "--manifest", bad])
        assert p.returncode == 2, "全注释 manifest 应 rc=2 实测 %d" % p.returncode

        # ⑦ --anchor 畸形负判（非 32-hex）→ rc 2
        p = run(["--world", world, "--anchor", "S01=xyz"])
        assert p.returncode == 2, "畸形 anchor 应 rc=2 实测 %d" % p.returncode

        # ⑧ 缺 world 目录 → rc 9
        p = run(["--world", os.path.join(tmp, "nope")])
        assert p.returncode == 9, "缺目录应 rc=9 实测 %d" % p.returncode

        # ⑨ 透传正判：世界绿 → 引擎真跑（washEngine 幂等账 rc 0·产物落盘）
        src_v = os.path.join(tmp, "vec.v")
        with io.open(src_v, "w", encoding="utf-8", newline="") as fh:
            fh.write("Lemma vec_a : forall x : nat, x = x.\nProof.\n  intros x. reflexivity.\nQed.\n")
        ledger = {"patches": [{"tag": "eq2id", "expect": 1,
                               "old": "Lemma vec_a : forall x : nat, x = x.\n",
                               "new": "Lemma vec_a : forall x : nat, Id nat x x.\n"}]}
        ledger_p = os.path.join(tmp, "ledger.json")
        with io.open(ledger_p, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh)
        out_v = os.path.join(tmp, "vec_washed.v")
        p = run(["--world", world, "--manifest", man, "--",
                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        assert p.returncode == 0, "透传正判应 rc=0 实测 %d\n%s" % (p.returncode, p.stdout)
        assert os.path.isfile(out_v), "世界绿时引擎应真跑落盘"
        assert "WORLD-BASE-OK" in p.stdout and "APPLY" in p.stdout, p.stdout

        # ⑩ 透传负判（nw5 雷拦截）：世界偏斜 → rc 9·引擎未跑·--out 零落盘
        os.remove(out_v)
        stale = os.path.join(tmp, "world_stale")
        os.makedirs(stale)
        with io.open(os.path.join(stale, "S01_BaseRing.vo"), "wb") as fh:
            fh.write(b"OLD-GENERATION-VO\n")  # 自带旧代
        p = run(["--world", stale, "--manifest", man, "--",
                 "--file", src_v, "--patch", ledger_p, "--out", out_v])
        assert p.returncode == 9, "偏斜世界应 rc=9 实测 %d" % p.returncode
        assert not os.path.exists(out_v), "born 前断言败：引擎竟已落盘（零半态失守）"
        assert "WDIFF" in p.stdout, p.stdout

        # ⑪ 透传形引擎侧透传（缺 --patch → 引擎 exit 3 SKIP 语义原样上浮）
        p = run(["--world", world, "--manifest", man, "--", "--file", src_v])
        assert p.returncode == 3, "引擎 SKIP 语义应透传 rc=3 实测 %d" % p.returncode

        # ⑫ 引擎只读复用旁证：冻结件 wash_engine.py md5 出账（不改字节·导入面复用）
        print("WORLD-HOOK-SELFTEST PASS: pos/wdiff-nw5雷/wmiss/manifest双形/畸形×2/"
              "缺目录/透传正/born拦截/引擎透传3/冻结件只读复用 十二判全过")
        print("  engine_md5=%s (冻结在册 664446bc717395d8496c8c30a5af9ccf·零字节复用)"
              % md5_of(engine))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def subprocess_run(argv):
    """subprocess 实跑包装（selftest 用·stdout/stderr 捕获为文本）。"""
    import subprocess
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.stdout = p.stdout.decode("utf-8", errors="replace") if isinstance(p.stdout, bytes) else (p.stdout or "")
    return p


def split_engine_argv(argv):
    """首个 `--` 切分：前段＝钩子形参，后段＝wash_engine 形参逐字透传。"""
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1:]
    return argv, None


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())

    hook_args, engine_args = split_engine_argv(argv)
    ap = argparse.ArgumentParser(
        prog=PROG, description="wash_engine 世界基校验钩子（born 前断言 world=认证代）")
    ap.add_argument("--world", "-w", required=True, help="目标世界目录（born 落点基座）")
    ap.add_argument("--manifest", "-m", default=None,
                    help="认证代锚 manifest（两行形皆收·只认 .vo 行·整表换锚）")
    ap.add_argument("--anchor", "-a", action="append", default=[], metavar="名=md5",
                    help="单点锚（可重复·覆盖缺省/manifest 同名锚）")
    args = ap.parse_args(hook_args)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not os.path.isdir(args.world):
        print("FAIL-LOUD: --world 目录缺失: %s" % args.world, file=sys.stderr)
        sys.exit(9)

    # —— 锚装配：缺省判例五锚 ← manifest 整表 ← --anchor 单点（后者逐层覆前者）——
    try:
        anchors = dict(BUILTIN_ANCHORS)
        if args.manifest:
            if not os.path.isfile(args.manifest):
                print("FAIL-LOUD: --manifest 缺失: %s" % args.manifest, file=sys.stderr)
                sys.exit(9)
            anchors = parse_manifest(args.manifest)
        anchors.update(parse_anchor_args(args.anchor))
    except HookError as e:
        print("FAIL-LOUD: %s" % e, file=sys.stderr)
        sys.exit(2)

    # —— born 前断言（引擎一步未跑·零半态）——
    print("WORLD-BASE-ASSERT world=%s anchors=%d source=%s" %
          (args.world, len(anchors),
           "manifest" if args.manifest else ("anchors+builtin" if args.anchor else "builtin-nw5判例")))
    ok, rows = assert_world_base(args.world, anchors)
    for r in rows:
        if r["code"] == "MATCH":
            print("ANCHOR %s %s MATCH" % (r["name"], r["want"]))
        elif r["code"] == "WDIFF":
            print("WDIFF %s want=%s got=%s （自带旧代＝nw5 雷·禁 born）" % (r["name"], r["want"], r["got"]))
        else:
            print("WMISS %s want=%s （认证代基座缺件·禁 born）" % (r["name"], r["want"]))
    if not ok:
        bad = sum(1 for r in rows if r["code"] != "MATCH")
        print("WORLD-BASE-RED: %d/%d 锚不过（exit 9·洗引擎未跑·--out 零落盘）" % (bad, len(rows)))
        sys.exit(9)
    print("WORLD-BASE-OK: %d/%d 锚全等（认证代）" % (len(rows), len(rows)))

    # —— 透传形：断言过才交引擎（只读 import·冻结件零字节复用）——
    if engine_args is None:
        sys.exit(0)
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import wash_engine  # noqa: E402（在役冻结件·只 import 不改）
    except Exception as e:  # pragma: no cover
        print("FAIL-LOUD: 冻结同侪 wash/wash_engine.py 不可导入: %s" % e, file=sys.stderr)
        sys.exit(9)
    sys.exit(wash_engine.run_args(list(engine_args)))


if __name__ == "__main__":
    main()
