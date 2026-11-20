#!/bin/bash
# wrapper/coqc_shim.sh — gate7 探针链 coqc 形参适配层（canonical coqc shim）
# 2026-10-31 席 rqadapt · 适配任务：组件 gate7 探针链（仓外件
#   ConstructiveWorld-Set/scripts/gates/gate7_extract_run.py · 在其仓只读禁改）
#
# 定位 Positioning:
#   gate7 正本以 `--coqc <coqc 形参>` 调编译器，且默认值是 Windows 形路径
#   （`DEFAULT_COQC = C:/Rocq-Platform~9.1~2026.01/bin/coqc.exe`·本机不存在）。
#   各战役席（nw4/nw6/nw7/nw8/v34/gclver…）各在自己的 seat 域手造了一份 shim：
#   `exec <Live toolchain rocq> c "$@"`（gate7 argv 契约 coqc <args> → Rocq 9.1
#   `rocq c <args>`）。本文件将其**正典化**为仓内唯一适配面——正本 gate7 零改动，
#   本层零判零逻辑（不解析不拦截任何 argv，1:1 透传）。
#
# 用法 Usage:
#   wrapper/coqc_shim.sh <coqc 形参...>
#   例（gate7 正典接线，由 wrapper/gate7_probe.sh 自动完成）:
#     ... gate7_extract_run.py --coqc wrapper/coqc_shim.sh --tree <world> ...
#
# 环境旋钮 Env knob:
#   GATE7_PROBE_ROCQ  覆写 rocq 绝对路径（缺省＝本机 Live toolchain 正典路径，
#                     与各席 shim 判例逐字节同源）。probe 与 shim 共用同一旋钮。
#
# 直通律 Pass-through contract:
#   1. argv 1:1 透传——只在前面注入子命令 `c`，其余逐字后传（`rocq c` 同 coqc 形参面）；
#   2. 退出码＝rocq 退出码（exec 透传，无改写）；
#   3. **禁套 guard**：gate7 对每个模块以子进程调本 shim；guard 若在此再包一层，
#      与外层 probe 的 guard 同注册表争位＝死锁（seat_nw8 判例 20261031：
#      「guard 只包 python 进程，shim 内再套 guard 会同注册表死锁」）。
#      温控由外层 wrapper/gate7_probe.sh 的 guard 对 python 进程树整包承担。
#   4. fail-loud：rocq 缺失 exit 9（口径承 cli/rocqwash 退出码表「文件缺失=9」），
#      不模拟编译任何行为（禁假绿承 CONTRIBUTING §0 三诚实律）。
#
# 退出码 Exit codes:
#   9   = rocq 二进制缺失/不可执行（fail-loud）
#   其余 = rocq 自身退出码（exec 透传）
set -u

ROCQ_BIN="${GATE7_PROBE_ROCQ:-/Users/apple/Desktop/ConstructiveWorld/Live/toolchain/opam/live/bin/rocq}"

if [ ! -x "$ROCQ_BIN" ]; then
  echo "wrapper/coqc_shim.sh: rocq 缺失 missing: $ROCQ_BIN" >&2
  echo "  (fail-loud：不模拟编译任何行为 — shim simulates nothing; 可用 GATE7_PROBE_ROCQ=<bin> 覆写)" >&2
  exit 9
fi

exec "$ROCQ_BIN" c "$@"
