#!/bin/bash
# wrapper/gate6_census.sh — gate6 语句面 Prop 普查闸正典启动层（canonical gate6 census launcher）
# 2026-10-31 席 rqadapt · 适配任务：组件 gate6 仓外件（
#   ConstructiveWorld-Set/scripts/gates/gate6_statement_census.py · 在其仓只读禁改）
#
# gap（本轮补齐对象）：七席循环核心闸 gate6/gate7 正本全在 ConstructiveWorld-Set/
#   scripts/gates/（仓外·本仓无任何入口）；各战役席要用只能裸调仓外路径。本件与
#   wrapper/gate7_probe.sh 配对，把 gate6 也正典化为仓内唯一启动面。
#
# 定位 Positioning:
#   gate6 正本＝红线律 II（白皮书 v2.4+）语句面 Prop 普查预筛闸（三通道 ch1 语句面/
#   ch2 字段-节面/ch3 全局假设面；语义终审归 gate7 提取差——正本头注原文）。纯静态
#   词面扫描：**零网络零编译**（正本全文件无 subprocess/无 socket·read-only 树扫描）。
#   本层零判据零逻辑：census/gate 红绿、baseline 比对全归正本唯一出处，本件只是其
#   仓内新入口（防双源漂移）。
#
# 用法 Usage:
#   bash wrapper/gate6_census.sh --tree <.v 树目录>
#        [--json <出账>] [--text]
#        [--gate --baseline <B>] [--baseline-out <O>]
#        [--gate-script <gate6.py>] [--dry-run]
#        [-- <gate6 其余形参逐字透传（前向兼容）>]
#   例 Example:
#     bash wrapper/gate6_census.sh --tree "$WORLD" --json "$SB/logs/gate6.json"
#     bash wrapper/gate6_census.sh --tree "$WORLD" --gate \
#          --baseline gate6_baseline.json --baseline-out "$SB/logs/gate6_new_baseline.json"
#
# 环境旋钮 Env knobs:
#   GATE6_CENSUS_SCRIPT  gate6 正本路径（缺省 ConstructiveWorld-Set 仓外正典路径）
#   GATE6_CENSUS_REG     guard 登记表目录（缺省 /tmp/cw_reg_gate6_census；席位惯例
#                        自设如 /tmp/cw_reg_<seat>，双车道与其它席位互不排队）
#   GATE6_CENSUS_FRONT/-MID/-MAXWAIT  guard 档位（缺省 0/1/600＝战役正典形）
#
# 契约 Contract:
#   1. guard 接线内建：`exec wrapper/guard.sh -Reg … -Front 0 -Mid 1 -MaxWaitSec 600
#      -- python3 -B <gate6.py> …`（正本冻结件 tools/cpu_guard.sh 直通层·与本机
#      ConstructiveWorld/cpu_guard.sh md5 全等 9c5392d6… 实测 20261031）。**调用者
#      禁再外套 guard**（同注册表死锁判例·nw8 20261031）。
#   2. python 一律 `python3 -B`——禁向只读正本仓（ConstructiveWorld-Set）落
#      __pycache__（承 gate7_probe 同律）。
#   3. 形参 1:1 对齐正本 argparse（--tree/--json/--text/--gate/--baseline/
#      --baseline-out·正本 gate6_statement_census.py:158-163 实读）；本件不代设
#      业务缺省值——census 报告-only 还是 --gate 闸判由调用者显式选择。
#   4. 写盘面 ROOT 声明（CONTRIBUTING §3.5）：仅用户显式指定的 --json/--
#      baseline-out 路径；**不写两仓正本与各 seat 域任何路径**；不指定＝纯报告
#      stdout 零写盘。
#   5. 退出码 1:1 透传：0=census 报告/闸绿；1=闸红（growth/new-file 回归·R15
#      存量冻结只罚增长）；2=正本用法-IO 错（含 tree 缺失）。
#
# 退出码 Exit codes:
#   0   = gate6 census 报告/闸绿（或 --dry-run 出账后）
#   2   = 本层用法错（未知形参/缺 --tree）
#   9   = 文件缺失（gate6 正本/--tree 目录/python3——fail-loud 不模拟任何行为）
#   其余 = guard 透传＝gate6 自身退出码（含 1 闸红）
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/wrapper/guard.sh"

GATE6_SCRIPT="${GATE6_CENSUS_SCRIPT:-/Users/apple/Desktop/ConstructiveWorld-Set/scripts/gates/gate6_statement_census.py}"
REG="${GATE6_CENSUS_REG:-/tmp/cw_reg_gate6_census}"
FRONT="${GATE6_CENSUS_FRONT:-0}"
MID="${GATE6_CENSUS_MID:-1}"
MAXWAIT="${GATE6_CENSUS_MAXWAIT:-600}"

usage() {
  sed -n '2,44p' "$0" | grep -E '^#' | sed 's/^# \{0,1\}//'
}

TREE=""; JSONOUT=""; TEXT=0; GATE=0; BASELINE=""; BASEOUT=""; GATE6OVR=""; DRYRUN=0
EXTRA=()
AFTER="--args"
while [ $# -gt 0 ]; do
  case "$1" in
    --tree) TREE="${2-}"; shift 2 ;;
    --json) JSONOUT="${2-}"; shift 2 ;;
    --text) TEXT=1; shift ;;
    --gate) GATE=1; shift ;;
    --baseline) BASELINE="${2-}"; shift 2 ;;
    --baseline-out) BASEOUT="${2-}"; shift 2 ;;
    --gate-script) GATE6OVR="${2-}"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) AFTER="--extra"; shift; EXTRA=("$@"); break ;;
    *) echo "wrapper/gate6_census.sh: 未知形参 unknown arg: $1" >&2
       echo "  (-h|--help 看用法; gate6 原生形参请置于 -- 之后逐字透传)" >&2; exit 2 ;;
  esac
done
[ -n "$GATE6OVR" ] && GATE6_SCRIPT="$GATE6OVR"

fail9() { echo "wrapper/gate6_census.sh: $1" >&2; echo "  (fail-loud exit 9：文件缺失不模拟任何行为)" >&2; exit 9; }

# --- 用法/文件面 fail-loud（先于任何 guard 行为） ----------------------------
[ -n "$TREE" ] || { echo "wrapper/gate6_census.sh: 缺 --tree <.v 树目录>" >&2; exit 2; }
[ -d "$TREE" ] || fail9 "--tree 目录缺失: $TREE"
[ -f "$GATE6_SCRIPT" ] || fail9 "gate6 正本缺失: $GATE6_SCRIPT (可用 GATE6_CENSUS_SCRIPT/--gate-script 覆写)"
[ -x "$GUARD" ] || fail9 "guard 直通层缺失: $GUARD"
command -v python3 >/dev/null 2>&1 || fail9 "python3 不在 PATH"
if [ "$GATE" = "1" ] && [ -z "$BASELINE" ]; then
  echo "wrapper/gate6_census.sh: --gate 需配 --baseline（正本 GATE6-USAGE 同律·此处前置 fail-loud）" >&2
  exit 2
fi
[ -z "$BASELINE" ] || [ -f "$BASELINE" ] || fail9 "--baseline 文件缺失: $BASELINE"

# -- gate6 形参装配（判据零复制·形参 1:1 对齐正本 argparse:158-163） -----------
CMD=(python3 -B "$GATE6_SCRIPT"
     --tree "$TREE")
[ "$TEXT" = "1" ] && CMD+=(--text)
[ "$GATE" = "1" ] && CMD+=(--gate)
[ -n "$BASELINE" ] && CMD+=(--baseline "$BASELINE")
[ -n "$JSONOUT" ] && CMD+=(--json "$JSONOUT")
[ -n "$BASEOUT" ] && CMD+=(--baseline-out "$BASEOUT")
[ ${#EXTRA[@]} -gt 0 ] && CMD+=("${EXTRA[@]}")

if [ "$DRYRUN" = "1" ]; then
  printf 'GATE6-CENSUS-DRYRUN guard: bash %q -Reg %q -Front %q -Mid %q -MaxWaitSec %q --\n' \
    "$GUARD" "$REG" "$FRONT" "$MID" "$MAXWAIT"
  printf 'GATE6-CENSUS-DRYRUN cmd:'
  printf ' %q' "${CMD[@]}"
  printf '\n'
  exit 0
fi

# -- guard 接线（退出码 exec 透传·无改写） ------------------------------------
exec bash "$GUARD" -Reg "$REG" -Front "$FRONT" -Mid "$MID" -MaxWaitSec "$MAXWAIT" -- "${CMD[@]}"
