#!/bin/bash
# wrapper/push_gate_rq.sh — certify/push_gate.py 适配层（repo-anchor adapter · 新文件）
# 2026-10-31 席 rqadapt · 适配任务：组件 certify/push_gate.py
# gap：两件无席位调用；且 window 子命令 --repo 默认 '.'（push_gate.py:585
#      「default="."」）为 cwd 敏感——仓外运行即 git 判读失败。
#
# 定位 Positioning:
#   certify/push_gate.py 为在役组件（邻席实时引用·禁改）。本层为**新文件**适配面：
#   由本脚本自身位置上跳一级解析仓库根绝对路径（与 v2 接口 __file__ 解析同效），
#   显式注入 --repo <本仓绝对路径> 与 --suite <本仓>/tests/run_tests.sh，消灭 cwd
#   敏感；不复制、不重实现任何判窗/清单逻辑——解析权全在正本，退出码 1:1 透传。
#
# 注入契约 Injection contract:
#   1. 仅 window 子命令注入：`window --repo <REPO> --suite <REPO>/tests/run_tests.sh
#      <用户参...>`——注入在前、用户参在后；argparse 后值覆盖前值，用户显式
#      --repo/--suite 仍可覆盖（覆盖即回到 cwd 敏感语义·责任随显式指认转移）；
#   2. union-freeze / union-check / --selftest / -h 零注入 1:1 直通（无 --repo 形参）；
#   3. 无参调用＝用法错 exit 2——绝不默认 window（window 会触网 ls-remote/fetch，
#      禁 surprise 网络；开窗判断由调用方显式发起，环候窗纪律承战役推送窗铁律）；
#   4. --show 诊断面：打印将执行的 argv 与仓库锚，零网络零执行——注入正确性的
#      机检证据（只认机械证据承 CONTRIBUTING §0）；
#   5. fail-loud：正本缺失/仓库根解析失败 exit 9（口径承 cli/rocqwash 退出码表）。
#
# 用法 Usage:
#   wrapper/push_gate_rq.sh window [--branch B] [--runs-json f | --ci-capped-min N]
#                                  [--freeze-manifest m.json] [--json out]
#       （--repo/--suite 已锚定注入·用户仍可显式覆盖）
#   wrapper/push_gate_rq.sh --show          # 诊断：打印注入后 argv（零网络零执行）
#   wrapper/push_gate_rq.sh union-freeze --world name=path --out union.json   # 直通
#   wrapper/push_gate_rq.sh union-check --manifest union.json                 # 直通
#   wrapper/push_gate_rq.sh --selftest      # 直通（冻结向量组自证）
#
# 写域声明：本层零写盘——不写仓库树、不写沙箱，诊断仅 stdout；正本以 -B 调用
# （不产 __pycache__·防 certify/ 树冻结对账漂移）。一切编译/测试仍必经
# tools/cpu_guard.sh 温控包裹（本层零编译零网络）。
#
# 退出码 Exit codes:
#   9   = 正本/仓库根缺失（fail-loud）
#   2   = 用法错（未知子命令/无参）
#   0   = --show 诊断成功
#   其余 = 正本透传（window 0=OPEN／1=CLOSED 等·见正本头注退出码表）
set -u
HERE="$(cd "$(dirname "$0")" && pwd)" || { echo "FAIL-LOUD: 脚本位置解析失败" >&2; exit 9; }
REPO="$(cd "$HERE/.." && pwd)" || { echo "FAIL-LOUD: 仓库根解析失败: $HERE/.." >&2; exit 9; }
PY="${PYTHON3:-python3}"
TARGET="$REPO/certify/push_gate.py"
[ -f "$TARGET" ] || { echo "FAIL-LOUD: 正本缺失: $TARGET" >&2; exit 9; }

if [ $# -eq 0 ]; then
  echo "FAIL-LOUD: 无参调用禁绝（防 surprise 网络·见头注注入契约 3）" >&2
  echo "用法: $0 window [选项...] | union-freeze ... | union-check ... | --selftest | --show" >&2
  exit 2
fi
case "$1" in
  --show)
    echo "wrapper/push_gate_rq.sh --show（诊断·零网络零执行）"
    echo "  REPO    = $REPO"
    echo "  suite   = $REPO/tests/run_tests.sh"
    echo "  argv    = $PY -B $TARGET window --repo $REPO --suite $REPO/tests/run_tests.sh <用户参...>"
    echo "  passthru= union-freeze / union-check / --selftest（零注入直通）"
    exit 0 ;;
  window)
    shift
    exec "$PY" -B "$TARGET" window --repo "$REPO" --suite "$REPO/tests/run_tests.sh" "$@" ;;
  union-freeze|union-check|--selftest|-h|--help)
    exec "$PY" -B "$TARGET" "$@" ;;
  *)
    echo "FAIL-LOUD: 未知子命令: $1（合法: window | union-freeze | union-check | --selftest | --show）" >&2
    exit 2 ;;
esac
