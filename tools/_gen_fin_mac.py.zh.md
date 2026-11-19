#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_gen_fin_mac.py — censusFIN 模板 Mac 适配生成器（S 系 Prop 清除战役·工具链 Mac 适配席·20261022）

模板血统：censusFIN/SortAlive_Probe_FIN1640.v（_set1640_S10FIN_sbx·S10 五证第④关 censusFIN
对表器）——SortAlive __-census 检验：语句名清单→具名透明别名→**单命令多名一轮全提**
Separate Extraction（§1·E 律 1 单命令多名全提律：逐命令重置输出 last-write-wins，多目标
必须单命令全提）→解析 `(** val alive_N : ... **)` 型注与 let 体——RED iff "__"（提取擦除
语义·词表无关内核级判定，non-negotiable constraint②第六关）。

Mac 适配三件：
  ①本生成器——模块名/世界路径/依赖链全参数化（FIN1640 模板系 S10 专用死形，本器改活形）；
  ②驱动 _fire_fin_<W>.sh——cpu_guard v3 Mac 形包裹（bash guard·-Front 1 -Mid 0）＋SW2 全字面
    双 export COQLIB/ROCQLIB（Mac 形）＋cmd/exit/log 三件落箱（箱册纪律）；
  ③解析 _parse_fin_mac.py——ann 正则 `:\\s*` 冒号-空格/换行双形容忍（§1·E 律 3 ann 正则
    双形律·1572 伤），vo 魔数 436f712100015ff4 咬合＋新鲜度并查（绿判四件套复用）。

用法：
  python3 _gen_fin_mac.py --source <Module.v> --module <ModuleName> \
      --world <worldT_dir> --world-name <W> --outdir <dir> [--requires S01_BaseRing,...]
  # 缺省 --requires＝梯世界链 S01_BaseRing..S09_EntropyReal（至 --module 为止）

干跑验证（S10.vo 未绿·禁实跑 S10——用 worldT_mac S09 dry run，census 100/100 已证为期望底）：
  cd <outdir> && bash _fire_fin_<W>.sh && python3 _parse_fin_mac.py \
      SortAlive_Probe_<W>.ml --manifest manifest_<W>.json \
      --vo SortAlive_Probe_<W>.vo --source-v <source.v> --transcript _fin_<W>_build.log
"""
import argparse
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))  # mac_stmt_names.py 在箱根
# mac_stmt_names.py 的提取核（同一 token 走法＝census 口径语句清单）复用：清单一致性由同器保证
import mac_stmt_names  # noqa: E402

LADDER = ["S01_BaseRing", "S02_CauchyComplete", "S03_QExp", "S04_RealExpLogConv",
          "S05_AlignmentGRPO", "S06_DiffSamplingGibbs", "S07_RealSetoidExpLog",
          "S08_RealMainlineDPO", "S09_EntropyReal", "S10_KVQuantTrig",
          "S11_TP3B5", "S12_B5RecycleSF", "S13_NLiveAudit", "S14_B5BatchBlock"]

COQC_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq"
OPAM_ENV_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/bin/opam env --switch live --root /Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam --set-root"
COQ_ARG = "c"  # rocq c = coqc 相容子命令（Rocq 9.1）
COQLIB_MAC_DEFAULT = "/Users/apple/actions-runner/mac_rocq/lib/coq"
GUARD_MAC_DEFAULT = "/Users/apple/Desktop/ConstructiveWorld/cpu_guard.sh"

DRIVER_TMPL = r"""#!/bin/bash
# censusFIN_mac fire driver — world <WNAME> (Mac form, guard-wrapped, SW2 double export)
# 箱册纪律：cmd(本件)+exit+log 三件落箱；exit 码＝coqc 真码（guard 透传·无管道真取）。
#
# Mac 坑位注记（20261022 本席实测）：mac_rocq/bin/coqc 系 shim——内部 `source env.sh` 重跑
# `opam env`（0.2s CPU·常规档瞬时·nice19 拥挤窗即冻）再 exec rocq——把环境解析带进 guard
# nice19 进程＝饥饿陷阱。本驱动改：env 预解析在驱动壳（常规档·非编译）＋guard 包真身
# `rocq c`。编译本体仍全 guard 包裹（§R2 铁律不变）。
set -u
COQC="${{COQC:-{coqc}}}"
COQARG="{coqarg}"
export COQLIB="${{COQLIB:-{coqlib}}}"
export ROCQLIB="${{ROCQLIB:-{coqlib}}}"
GUARD="${{GUARD:-{guard}}}"
WORLD="{world}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
echo "[fin-mac] guard=$GUARD world=$WORLD coqc=$COQC $COQARG" >&2
# 环境预解析（非编译·常规档·~0.2s；失败 fail-loud）
if [ -x /Users/apple/Desktop/ConstructiveWorld/Live/toolchain/bin/opam ]; then
  eval "$({opam_env} 2>/dev/null)" || {{ echo "FAIL-LOUD: opam env pre-resolve failed" >&2; exit 9; }}
fi
# 拥挤窗注记（20261022 二次修正）：nice19 BACK 档对 rocq c 本体可用（piu_zz 判例 worker
# 实得 24-33% CPU）——真坑是 shim 内 opam env 根锁（已由 env 预解析根治）。MaxWaitSec 维持
# guard 默认 900s：候窗 15 min 后 BACK 发炮约 1-2 min 完成。勿拉长 MaxWaitSec——前有长件
# 占位时候格队永不推进（slots 随命令全程持有·seq1 巨件＋seq3 冻结 coqchk 占位判例）。
"$GUARD" -Front "${{FRONT:-{front}}}" -Mid "${{MID:-{mid}}}" -MaxWaitSec "${{MAXWAIT:-900}}" -- \
  "$COQC" "$COQARG" -native-compiler no -q -Q "$WORLD" "" SortAlive_Probe_{wname}.v \
  > _fin_{wname}_build.log 2>&1
rc=$?
echo "$rc" > _fin_{wname}.exit
tail -8 _fin_{wname}_build.log >&2
exit $rc
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="目标模块 .v 源（语句清单提取底）")
    ap.add_argument("--module", required=True, help="目标模块名（如 S09_EntropyReal）")
    ap.add_argument("--world", required=True, help="世界目录（-Q <world> \"\"）")
    ap.add_argument("--world-name", required=True, help="探针件后缀（如 S09DRT）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--requires", help="逗号分 Require 链；缺省＝梯世界链至 --module 为止")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not os.path.exists(args.source):
        print("FAIL-LOUD: source missing:", args.source)
        sys.exit(9)
    if not os.path.isdir(args.world):
        print("FAIL-LOUD: world dir missing:", args.world)
        sys.exit(9)
    requires = ([r.strip() for r in args.requires.split(",") if r.strip()]
                if args.requires else LADDER[:LADDER.index(args.module) + 1])
    if args.module not in requires:
        requires.append(args.module)

    inv = mac_stmt_names.extract_statements(args.source, include_let=False)
    stmts = inv["statements"]
    if inv["anomalies"]:
        print("ANOMALIES（fail-loud 逐笔·禁静默）:", inv["anomalies"])
    if not stmts:
        print("FAIL-LOUD: zero statements extracted from", args.source)
        sys.exit(9)

    os.makedirs(args.outdir, exist_ok=True)
    w = args.world_name
    lines = []
    lines.append("(* SortAlive Probe %s -- censusFIN_mac (Mac form; template lineage "
                 "SortAlive_Probe_FIN1640.v) *)" % w)
    lines.append("(* spec source: E-STAGING-1484-PROPCLEAN-RECIPEBOOK section 5.1; "
                 "single-command multi-name Separate Extraction per cw-ci-sop §1·E law1 *)")
    lines.append("From Stdlib Require Import Extraction.")
    for mod in requires:
        lines.append("Require Import %s." % mod)
    for k, s in enumerate(stmts):
        lines.append("Definition alive_%d := %s.%s." % (k, args.module, s["name"]))
    names = " ".join("alive_%d" % k for k in range(len(stmts)))
    lines.append("Separate Extraction %s." % names)
    probe_v = os.path.join(args.outdir, "SortAlive_Probe_%s.v" % w)
    with io.open(probe_v, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    manifest = {"world": w, "source": os.path.abspath(args.source),
                "module": args.module, "requires": requires,
                "statements": [{"idx": k, "name": s["name"], "kind": s["kind"],
                                "decl_line": s["decl_line"]}
                               for k, s in enumerate(stmts)],
                "skips": inv["skips"], "anomalies": inv["anomalies"]}
    manifest_j = os.path.join(args.outdir, "manifest_%s.json" % w)
    with io.open(manifest_j, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=1))

    driver = os.path.join(args.outdir, "_fire_fin_%s.sh" % w)
    with io.open(driver, "w", encoding="utf-8", newline="\n") as f:
        f.write(DRIVER_TMPL.format(
            wname=w, world=os.path.abspath(args.world),
            coqc=COQC_MAC_DEFAULT, coqarg=COQ_ARG, opam_env=OPAM_ENV_MAC_DEFAULT,
            coqlib=COQLIB_MAC_DEFAULT,
            guard=GUARD_MAC_DEFAULT, front=1, mid=0))
    os.chmod(driver, 0o755)

    print(json.dumps({"probe": probe_v, "manifest": manifest_j, "driver": driver,
                      "statements": len(stmts), "requires": requires,
                      "let_skipped": inv["let_skipped"],
                      "anomalies_n": len(inv["anomalies"]),
                      "note": "编译必经驱动内 cpu_guard 包裹（-Front 1 -Mid 0）；"
                              "解析用 _parse_fin_mac.py（ann :\\s* 双形律）"},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
