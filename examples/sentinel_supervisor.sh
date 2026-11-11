#!/bin/bash
# sentinel_supervisor.sh — 监督壳：哨长驻（--loop）崩溃自动重启补偿壳（正典部署形）
#
# 出处与判例（rocqwash v50·更新账.md:3999）：哨长驻 round10 IncompleteRead 崩
# （读 371261／欠 72721 字节·传输层断流——api_get_json 传输层 read 位
# tools/cw_sentinel.py:373 抛 http.client.IncompleteRead·非 URLError/OSError
# 子类逃逸 :387 捕获面与 v38 退避重试面〔该重试只罩 HTTPError 状态码 :375-386〕
# → 未捕获 traceback rc=1 崩）＝器债第二类；处置两轨：器修＝韧性层 v51 传输层
# 瞬断有界重试（并发在飞落盘·tools/cw_sentinel.py 现势）＋监督壳运行态补偿
# （本件——壳是进程级兜底：补一切器内不护崩形〔emit/rename/OOM/机器重启等〕
# 与已部署旧形运行态）。state 零损失判例（20261112 实读）：崩后重启续接
# report round=3·state seen 双仓咬合·events.jsonl 33 行 seq 1-33 单调无重报
# ——seen 幂等账跨崩零损失（承 ops-sentinel 手册 §3.1 禁静默重建·§3.3 宁重复
# 不丢件——壳补崩溃进程不补数据）。
#
# 泛化点（自本机 /tmp 运行态版 1:1 泛化·路径全参数化零硬编码绝对路径）：
#   重启帽         SUPERVISOR_MAX_RESTARTS（判例 40）
#   退避           SUPERVISOR_BACKOFF_BASE ×2 指数·帽 SUPERVISOR_BACKOFF_MAX
#                  （判例固定 sleep 60）
#   state 续接注记  spawn 前 echo 注记（seen 幂等·跨重启零损失续接·禁静默重建）
#   定时收兵钩位    supervisor_withdraw_hook 留空（缺省 return 0·示例 09:00 形
#                  见函数上注释·收兵粒度＝spawn 边界）
#   rc 分诊（泛化新增） 0=轮尽自停 exit 0；2=用法错不进重启环 fail-loud exit 2
#                  （重启无义·承手册 §1.2 spawn 前预检同律）；9／其余（含传输层
#                  崩 rc=1·IncompleteRead 判例形）→ 退避重启计帽。
#
# 用法（部署形·nohup 同 ops-sentinel 手册 §1.3 形 A；先 --once 预检再挂壳承
# 手册 §1.2）：
#   SENTINEL_WORK=/path/to/_log/sentinel_v50 \
#   SENTINEL_WATCH_REPOS="ORG/REPO-A ORG/REPO-B" \
#   [SENTINEL_GUARD=/path/to/cpu_guard.sh SENTINEL_GUARD_ARGS="-MaxWaitSec 120"] \
#   nohup bash examples/sentinel_supervisor.sh >/dev/null 2>&1 &
#
# 监督壳自身退出码：0=正常收兵（子轮尽 rc=0／钩位收兵）；1=重启预算耗尽；
# 2=用法错（必给配置缺·子 rc=2）；9=环境不可达（repo root／哨本体／工作目录缺）。

set -u

# ---- 配置（全环境变量·必给项 fail-loud·零硬编码绝对路径）----------------------
SENTINEL_REPO_ROOT="${SENTINEL_REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SENTINEL_WORK="${SENTINEL_WORK:-}"                  # 三件套落位目录（必给·手册 §1.1）
SENTINEL_WATCH_REPOS="${SENTINEL_WATCH_REPOS:-}"    # 空格分隔多仓（必给·至少一路信号源）
SENTINEL_BRANCH="${SENTINEL_BRANCH:-}"              # 可选·逐仓各归一组（先 repo 后 branch）
SENTINEL_INTERVAL="${SENTINEL_INTERVAL:-600}"       # 轮间隔秒（判例 600）
SENTINEL_MAX_ROUNDS="${SENTINEL_MAX_ROUNDS:-60}"    # 轮帽（判例 60·0=无限）
SENTINEL_GUARD="${SENTINEL_GUARD:-}"                # 缺省直跑（哨本体纯逻辑零编译·手册 §1.4）；本机运行态判例＝CW 侧 cpu_guard.sh 温控包裹
SENTINEL_GUARD_ARGS="${SENTINEL_GUARD_ARGS:--MaxWaitSec 120}"   # 判例形
SUPERVISOR_MAX_RESTARTS="${SUPERVISOR_MAX_RESTARTS:-40}"        # 重启帽（判例 40）
SUPERVISOR_BACKOFF_BASE="${SUPERVISOR_BACKOFF_BASE:-60}"        # 退避基秒（判例 60）
SUPERVISOR_BACKOFF_MAX="${SUPERVISOR_BACKOFF_MAX:-600}"         # 退避帽秒
SENTINEL_EXTRA_ARGS="${SENTINEL_EXTRA_ARGS:-}"                  # 追加旗标（如 --emit-max-bytes 104857600）

# ---- 用法 fail-loud（监督壳自身 2=用法错·9=环境不可达）------------------------
[ -n "$SENTINEL_WORK" ] || { echo "[supervisor] FAIL-LOUD 2: SENTINEL_WORK 必给（三件套落位·手册 §1.1）" >&2; exit 2; }
[ -n "$SENTINEL_WATCH_REPOS" ] || { echo "[supervisor] FAIL-LOUD 2: SENTINEL_WATCH_REPOS 必给（至少一路信号源）" >&2; exit 2; }
[ -d "$SENTINEL_REPO_ROOT" ] || { echo "[supervisor] FAIL-LOUD 9: SENTINEL_REPO_ROOT 目录缺: $SENTINEL_REPO_ROOT" >&2; exit 9; }
[ -f "$SENTINEL_REPO_ROOT/tools/cw_sentinel.py" ] || { echo "[supervisor] FAIL-LOUD 9: 哨本体缺: $SENTINEL_REPO_ROOT/tools/cw_sentinel.py" >&2; exit 9; }
[ -d "$SENTINEL_WORK" ] || { echo "[supervisor] FAIL-LOUD 9: SENTINEL_WORK 目录缺（先按手册 §1.1 落位建目录）: $SENTINEL_WORK" >&2; exit 9; }
cd "$SENTINEL_REPO_ROOT" || { echo "[supervisor] FAIL-LOUD 9: cd 失败: $SENTINEL_REPO_ROOT" >&2; exit 9; }

# ---- 定时收兵钩位（留空·部署方按需填形）--------------------------------------
# 钩位契约：每次 spawn 前评估一次；收兵＝函数内 exit 0（整壳退出·三件套出账
# 照常可消费）；不收兵＝return 0。收兵粒度＝spawn 边界（哨子进程运行中不中断
# ——运行中收兵用人工 kill 承手册 §1.5）。示例形（09:00 收兵·「持续迭代到
# 9 点」类·09:00-12:00 窗内不再派新轮）：
#   supervisor_withdraw_hook() { h=$(date +%H); [ "$h" -ge 9 ] && [ "$h" -lt 12 ] && exit 0; return 0; }
supervisor_withdraw_hook() {
  return 0   # 留空（缺省恒不收兵·收兵唯 --max-rounds 自停或人工 kill）
}

# ---- state 续接注记（崩后重启零损失续接的响亮声明·每壳一记）--------------------
echo "[supervisor] state 续接：--state-file 在位（seen 幂等账跨重启零损失续接·宁重复不丢件·禁静默重建——ops-sentinel 手册 §3.1/§3.3）"
echo "[supervisor] work=$SENTINEL_WORK repos=[$SENTINEL_WATCH_REPOS] interval=${SENTINEL_INTERVAL}s max_rounds=$SENTINEL_MAX_ROUNDS restarts≤$SUPERVISOR_MAX_RESTARTS backoff=${SUPERVISOR_BACKOFF_BASE}s×2帽${SUPERVISOR_BACKOFF_MAX}s"

backoff=$SUPERVISOR_BACKOFF_BASE
attempt=0
while :; do
  supervisor_withdraw_hook
  attempt=$((attempt + 1))
  if [ "$attempt" -gt "$SUPERVISOR_MAX_RESTARTS" ]; then
    echo "[supervisor] 重启预算耗尽（帽 ${SUPERVISOR_MAX_RESTARTS}）" >&2
    exit 1
  fi
  echo "[supervisor restart $attempt] $(date -u +%H:%M:%SZ)"
  cmd=(python3 -B tools/cw_sentinel.py --loop \
    --interval "$SENTINEL_INTERVAL" --max-rounds "$SENTINEL_MAX_ROUNDS")
  for r in $SENTINEL_WATCH_REPOS; do
    cmd+=(--watch-repo "$r")
    [ -n "$SENTINEL_BRANCH" ] && cmd+=(--branch "$SENTINEL_BRANCH")
  done
  cmd+=(--state-file "$SENTINEL_WORK/state.json" \
    --emit "$SENTINEL_WORK/events.jsonl" --json "$SENTINEL_WORK/report.json")
  [ -n "$SENTINEL_EXTRA_ARGS" ] && cmd+=($SENTINEL_EXTRA_ARGS)
  if [ -n "$SENTINEL_GUARD" ]; then
    bash "$SENTINEL_GUARD" $SENTINEL_GUARD_ARGS -- "${cmd[@]}"
  else
    "${cmd[@]}"
  fi
  RC=$?
  echo "[supervisor] exit=$RC at $(date -u +%H:%M:%SZ)"
  if [ "$RC" -eq 0 ]; then
    echo "[supervisor] 子轮尽（--max-rounds 跑满自停）＝正常收兵"
    exit 0
  fi
  if [ "$RC" -eq 2 ]; then
    echo "[supervisor] rc=2 用法错·重启无义·fail-loud 收兵（不烧重启帽）" >&2
    exit 2
  fi
  # rc=9（信号源不可达）与其余 rc（含传输层崩 rc=1·IncompleteRead 判例形）→ 退避重启计帽
  # （注意：$VAR 后紧贴全角字会被本机 bash 3.2 吞进变量名——变量一律 ${} 括起）
  echo "[supervisor] 退避 ${backoff}s 后重启（rc=${RC}）"
  sleep "$backoff"
  backoff=$((backoff * 2))
  if [ "$backoff" -gt "$SUPERVISOR_BACKOFF_MAX" ]; then
    backoff=$SUPERVISOR_BACKOFF_MAX
  fi
done
