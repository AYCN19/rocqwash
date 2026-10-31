#!/bin/bash
# wrapper/guard.sh — 冻结件 tools/cpu_guard.sh 适配直通层（frozen-component adapter · pass-through）
# 2026-10-31 席 rqadapt · 适配任务：组件 tools/cpu_guard.sh（在役冻结禁改）
#
# 定位 Positioning:
#   tools/cpu_guard.sh 为在役冻结件（各在飞席位实时引用），禁改。本层为**新文件**
#   适配面——不复制、不重实现任何温控/梯队列逻辑，仅将 argv 1:1 直通给**本仓正本**
#   tools/cpu_guard.sh 并原样透传退出码。契约承 docs/zh/architecture.md §6：
#   「退出码＝被包裹命令退出码」；一切编译/测试仍必经温控包裹，本层只是其新入口，
#   不是第二套实现（防双源漂移——正本唯一，本层零逻辑）。
#
# 用法 Usage（与正本逐字同 · byte-identical interface）:
#   wrapper/guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct]
#                    [-ThrottleFloor 90] [-ThermalMaxWait 3600] [-Reg <dir>] [--] <命令...>
#   例 Example:
#     wrapper/guard.sh -Reg /tmp/cw_reg_x -Front 0 -Mid 1 -MaxWaitSec 600 -- <命令...>
#     wrapper/guard.sh -Direct -- <小探针...>
#
# 直通律 Pass-through contract:
#   1. 不拦截不解析任何参数——全部原样递给正本（含 `--`，解析权全在正本）；
#   2. 不注入默认值/不代设 -Reg——缺省行为与直接调用 tools/cpu_guard.sh 逐字节同；
#   3. 退出码＝正本退出码＝被包裹命令退出码（exec 透传，无改写）；
#   4. fail-loud：正本缺失 exit 9（口径承 cli/rocqwash 退出码表「文件缺失=9」），
#      不模拟温控/队列任何行为（禁假绿承 CONTRIBUTING §0 三诚实律）。
#
# 退出码 Exit codes:
#   9   = 本仓正本 tools/cpu_guard.sh 缺失（fail-loud）
#   其余 = 正本透传（即被包裹命令自身退出码）
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GUARD="$ROOT/tools/cpu_guard.sh"

if [ ! -f "$GUARD" ]; then
  echo "wrapper/guard.sh: 本仓正本缺失 frozen original missing: $GUARD" >&2
  echo "  (fail-loud：直通层不模拟温控/队列任何行为 — pass-through layer simulates nothing)" >&2
  exit 9
fi

exec bash "$GUARD" "$@"
