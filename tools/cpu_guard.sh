#!/bin/bash
# cpu_guard.sh v3 — 动态梯队列温控协议（20260920 用户令：先占高位/后排候补/前完成后排上位）
# 用法: bash cpu_guard.sh [-Front 2] [-Mid 2] [-MaxWaitSec 900] [-Direct] [-ThrottleFloor 90] [-ThermalMaxWait 3600] -- <命令...>
# 规则:
#   1. 注册位次（FIFO=先占者优先）：进场即登记；位次<Front(默认2)=FRONT 档 nice0 全速；
#      位次<Front+Mid(默认+2)=MID 档 nice10；位次更靠后=队列等待轮询，前位完成即按当前位次上位，
#      MaxWaitSec 到点降级 BACK（nice19+后台）放行不饿死。
#   2. 温控门（全档适用，硬件现实永不 ABORT）：pmset CPU_Speed_Limit<ThrottleFloor → 冷却，
#      ThermalMaxWait 到点警告放行。
#   3. -Direct 探针直通：不排队不注册，nice19+后台立即执行（小探针专用防饿死）。
#   4. 并发由队列梯度天然约束（FRONT+MID 活跃上限 4），vm.loadavg 不再设门（v2 的负载门退役）。
#   5. 注册槽 PID 存活校验自动清陈旧。退出码=命令退出码。v2 备份: cpu_guard.sh.bak2-20260920-本机适配版
set -u
REG=/tmp/cpu_guard.reg; mkdir -p "$REG"
# 20261023 双车道制（用户令）：-Reg 参数分道登记表——S/M 两线各自独立队列互不排队，
# 两线合计并发=每线 Front+Mid 槽位之和；缺省不传 -Reg 时行为与旧版逐字节同。
RegOverride=0
FrontSlots=2; MidSlots=2; MaxWaitSec=900; Direct=0
ThrottleFloor=90; ThermalMaxWait=3600
while [[ $# -gt 0 ]]; do case "$1" in
  -Front) FrontSlots="$2"; shift 2;;
  -Mid) MidSlots="$2"; shift 2;;
  -MaxWaitSec) MaxWaitSec="$2"; shift 2;;
  -Direct) Direct=1; shift;;
  -ThrottleFloor) ThrottleFloor="$2"; shift 2;;
  -ThermalMaxWait) ThermalMaxWait="$2"; shift 2;;
  -Reg) REG="$2"; RegOverride=1; shift 2;;
  -LoadLimit|-CoolSec) shift 2;;   # 旧参兼容吞掉（负载门已退役）
  --) shift; break;;
  *) break;;
esac; done
if [ "$Direct" = "1" ]; then
  echo "[cpu_guard] DIRECT bypass" >&2
  taskpolicy -b nice -n 19 "$@"; exit $?
fi
ts=$(date +%s)
seq=0; [ -f "$REG/.seq" ] && seq=$(cat "$REG/.seq" 2>/dev/null || echo 0)
seq=$((seq+1)); echo "$seq" > "$REG/.seq" 2>/dev/null
mkdir -p "$REG" 2>/dev/null  # 双车道补丁：-Reg 解析后补建目录
SLOT="$REG/${ts}_$(printf '%06d' $seq)_$$"
echo "$$|$(date '+%H:%M:%S')" > "$SLOT" 2>/dev/null
trap 'rm -f "$SLOT"' EXIT INT TERM
pos(){ local n=0 f base p mybase
  mybase=${SLOT##*/}
  for f in "$REG"/[0-9]*; do
    [ -f "$f" ] || continue
    [ "$f" = "$SLOT" ] && continue
    base=${f##*/}; p=${base##*_}
    kill -0 "$p" 2>/dev/null || { rm -f "$f"; continue; }
    [[ "$base" < "$mybase" ]] && n=$((n+1))
  done
  echo $n; }
TIER=""; waited=0; P=-1
while :; do
  P=$(pos)
  if [ "$P" -lt "$FrontSlots" ]; then TIER=FRONT; break; fi
  if [ "$P" -lt $((FrontSlots+MidSlots)) ]; then TIER=MID; break; fi
  sleep 3; waited=$((waited+3))
  if [ $((waited % 30)) -eq 0 ]; then echo "[cpu_guard] queued pos=$P waited=${waited}s" >&2; fi
  if [ $waited -ge $MaxWaitSec ]; then TIER=BACK; break; fi
done
twait=0
while :; do
  spd=$(pmset -g therm 2>/dev/null | awk -F'= *' '/CPU_Speed_Limit/{gsub(/[ \t\r]/,"",$2); print $2; exit}')
  [ -z "$spd" ] && break
  hot=$(awk -v s="$spd" -v t="$ThrottleFloor" 'BEGIN{print (s<t)?1:0}')
  [ "$hot" = "0" ] && break
  sleep 3; twait=$((twait+3))
  if [ $((twait % 30)) -eq 0 ]; then echo "[cpu_guard] thermal cooling ${twait}s (limit=${spd}%)" >&2; fi
  if [ $twait -ge $ThermalMaxWait ]; then echo "[cpu_guard] thermal cap ${ThermalMaxWait}s → proceed degraded" >&2; break; fi
done
case $TIER in
  FRONT) echo "[cpu_guard] FRONT launch pos=$P waited=${waited}s tlevel=$(sysctl -n machdep.xcpm.cpu_thermal_level 2>/dev/null || echo ?)" >&2; "$@" ;;
  MID)   echo "[cpu_guard] MID launch pos=$P nice10 waited=${waited}s" >&2; nice -n 10 "$@" ;;
  BACK)  echo "[cpu_guard] BACK degraded queued=${waited}s" >&2; taskpolicy -b nice -n 19 "$@" ;;
  *)     echo "[cpu_guard] tier anomaly" >&2; taskpolicy -b nice -n 19 "$@" ;;
esac
rc=$?
exit $rc
