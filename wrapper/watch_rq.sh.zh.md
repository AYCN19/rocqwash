#!/bin/bash
# wrapper/watch_rq.sh — watch/watch.py 适配层（repo-anchor adapter · 新文件）
# 2026-10-31 席 rqadapt · 适配任务：组件 watch/watch.py
# gap：两件无席位调用；且 push/confirm 子命令 --repo 默认 '.'（watch.py:429、
#      watch.py:440「default="."」）为 cwd 敏感——仓外运行即 git 判读失败。
#
# 定位 Positioning:
#   watch/watch.py 为在役组件（邻席实时引用·禁改）。本层为**新文件**适配面：
#   由本脚本自身位置上跳一级解析仓库根绝对路径（与 v2 接口 __file__ 解析同效），
#   对 push/confirm 显式注入 --repo <本仓绝对路径>，消灭 cwd 敏感；不复制、不重
#   实现任何推送/确证/监控逻辑——解析权全在正本，退出码 1:1 透传。
#
# 注入契约 Injection contract:
#   1. push / confirm 注入 --repo <REPO>（注入在前、用户参在后；argparse 后值覆盖
#      前值，用户显式 --repo 仍可覆盖——覆盖即回到 cwd 敏感语义·责任随显式转移）；
#   2. ci 零注入直通——其 --repo 语义是 owner/name（在线查询模式），注入仓库
#      目录反而毁义；离线证据模式 --runs-json 路径由调用方自给；
#   3. push 不代设 --yes——正本默认即 DRY-RUN（干跑零网络零执行）；真推永由
#      调用方在 push_gate window OPEN（环候窗四判据）后显式发起，推后跑 confirm
#      做 ls-remote N 读确证（「真 rc＋ls-remote 复核」纪律由正本承担·本层不代包）；
#   4. --show 诊断面：打印将执行的 argv 与仓库锚，零网络零执行——注入正确性机检证据；
#   5. fail-loud：正本缺失/仓库根解析失败 exit 9；无参/未知子命令 exit 2。
#
# 用法 Usage:
#   wrapper/watch_rq.sh push [--remote origin] [--pin-ip IP --url-host HOST]
#                            [--mask STR]... [--yes|--dry-run] [-- refspecs...]
#       （--repo 已锚定注入·用户仍可显式覆盖）
#   wrapper/watch_rq.sh confirm --remote origin --branch main --sha <sha> [--reads 2 --gap 2]
#       （--repo 已锚定注入）
#   wrapper/watch_rq.sh ci --runs-json f | ci --repo owner/name --online      # 直通
#   wrapper/watch_rq.sh --show          # 诊断：打印注入后 argv（零网络零执行）
#   wrapper/watch_rq.sh --selftest      # 直通（冻结向量组自证）
#
# 写域声明：本层零写盘——不写仓库树、不写沙箱，诊断仅 stdout；正本以 -B 调用
# （不产 __pycache__）。本层结构性零 dispatch、零编译；结构性零 dispatch 由正本
# 保证（watch.py 无 rerun/cancel/workflow_dispatch 代码路径），CI 停手律不在本层
# 重复实现（防双源漂移）。
#
# 退出码 Exit codes:
#   9   = 正本/仓库根缺失（fail-loud）
#   2   = 用法错（未知子命令/无参）
#   0   = --show 诊断成功
#   其余 = 正本透传（push 0=DRY-RUN/其余=git push rc；confirm 0=CONFIRMED/1=不一致；
#          ci 0=idle/1=在飞>0 等·见正本头注退出码表）
set -u
HERE="$(cd "$(dirname "$0")" && pwd)" || { echo "FAIL-LOUD: 脚本位置解析失败" >&2; exit 9; }
REPO="$(cd "$HERE/.." && pwd)" || { echo "FAIL-LOUD: 仓库根解析失败: $HERE/.." >&2; exit 9; }
PY="${PYTHON3:-python3}"
TARGET="$REPO/watch/watch.py"
[ -f "$TARGET" ] || { echo "FAIL-LOUD: 正本缺失: $TARGET" >&2; exit 9; }

if [ $# -eq 0 ]; then
  echo "FAIL-LOUD: 无参调用禁绝（ci 需证据源·push 需子命令·见头注注入契约 5）" >&2
  echo "用法: $0 push [选项...] | confirm --remote R --branch B --sha S | ci ... | --selftest | --show" >&2
  exit 2
fi
case "$1" in
  --show)
    echo "wrapper/watch_rq.sh --show（诊断·零网络零执行）"
    echo "  REPO    = $REPO"
    echo "  argv    = $PY -B $TARGET push --repo $REPO <用户参...>"
    echo "            $PY -B $TARGET confirm --repo $REPO <用户参...>"
    echo "  passthru= ci / --selftest（零注入直通·ci 的 --repo 是 owner/name 非目录）"
    exit 0 ;;
  push)
    shift
    exec "$PY" -B "$TARGET" push --repo "$REPO" "$@" ;;
  confirm)
    shift
    exec "$PY" -B "$TARGET" confirm --repo "$REPO" "$@" ;;
  ci|--selftest|-h|--help)
    exec "$PY" -B "$TARGET" "$@" ;;
  *)
    echo "FAIL-LOUD: 未知子命令: $1（合法: push | confirm | ci | --selftest | --show）" >&2
    exit 2 ;;
esac
