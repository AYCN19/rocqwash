# unclog.py 模块 docstring 中文原档（留档）

- 源文件：`tools/unclog.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/unclog.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

unclog.py — 疏通堵塞闭环引擎（rocqwash tools/·v37 旗舰·20261111 入账）

把 W59-W88 实时支撑席的堵链疏通**手工五步**闭成自旋（编排而非重造——probe_engine/
chain_graph/cure_applier/scan_v4_token/frozen8 全 subprocess 调用·本器只做胶水与
状态机·承 v36 pushci 编排判例 tools/pushci.py:544 _run_py 同款）：

  手工五步（判例：wash 战役实时支撑席·W59-W88）      本器闭环（--rounds 帽·缺省 5）
  ① probe 归集红账              →  ① 归集：候选面三源任选 → probe_engine 出当前红账
  ② chain_graph 链根图挑根      →  ② 链根：chain_graph 合并 TOP 榜 → 取 self.washable=true
                                    之首（全 false＝无正典可洗根→诚实墙·禁硬凑）
  ③ cure_applier 落刀           →  ③ 落刀：对根件干跑出方案 → 有方案且 --apply 才落刀
                                    （只正典包 cure_pack v1.3·禁 freeform 编辑）；
                                    无方案→该根记 cure-miss 入墙账
  ④ re-scan/re-probe 复核       →  ④ 复核：scan_v4_token 复扫受治件（cured token 残差
                                    应零）＋ probe_engine 复探受治件（rc 应 0）
  ⑤ 人工判定                    →  ⑤ 判定：红账空=verdict unclogged exit 0；未空且轮
                                    未尽→下一轮；轮尽→verdict rounds-exhausted exit 1
                                    （附各轮账＋终判探）

候选面三源任选（互斥）：
  --candidates TSV      候选清单直喂 probe_engine（表头列名定位·probe_engine 同款）
  --chain-ledgers JSON  既有 probe 台账并入（argv 序＝合并序·后批覆盖前批·chain_graph
                        同款）；后续轮的复探台账逐轮并入（resprobe 后批覆盖——洗后
                        状态入账）。此模式无逐轮全量重探（零 world 依赖可跑）。
  （两者缺省）          --src 全树枚举：walk --src 收 *.v 逐件 md5 → 生成 TSV（RED 列
                        不申报·probe_engine 对 rc0 如实出 RC0——链根可洗性判据是
                        self.rc 非 verdict·chain_graph.py:109 同款口径）

红账口径：probe 记录 rc!=0（rc1 红件／rc124 TIMEOUT／NO-SRC）＝红；chain_graph
stats.rc1＋stats.other 并集即红账（chain_graph.py:116-121）。verdict 判定只认红账
（红是数据非器红·probe_engine rc1 候选是产出数据非器红）。

诚实墙（禁硬凑）：TOP 榜全 self.washable=false（链中环 self-unwashable／根未入
候选集 unprobed）或可洗根全部碰壁（cure-miss 正典包零方案／root-file-missing 缺
根件／frozen-in-service 在册红拒／exclusive-group-conflict 变体须人择／
idempotence-fail 落刀幂等断言拒写）→ verdict=wall exit 1，墙账逐根列不可洗因，
零落刀零硬凑。

安全律：
  --apply 缺省关＝全干跑零写盘（单开关·--yes 不需要）；落刀只经 cure_applier
  正典包（--pack 缺省 wash/cure_pack.json v1.3）；落刀对象恒为链根件
  （<src>/<根>.v——pick 之外无 cure 调用路径·对非链根件禁落刀系结构性保证）；
  frozen 在册（certify/frozen8.py --ledger 八件·子进程实取·缺册 fail-closed 9）
  预检红拒：根名撞在册 rel／基名／去扩展名，或根件 realpath 撞在册文件
  （--src 与 --repo-path 双侧解析）即拒——入墙账 reason=frozen-in-service·零落刀。

--audit 只读审计（真树堵账基线·20261111 任务书）：
  单遍 probe 干跑归集→chain_graph→出「堵账基线报告」供 v38 真实树基线
  （schema 同 rocqwash-unclog/1：final.verdict=audit·rounds 单轮
  probe_summary/chain_top 全在·墙账 graph 判例全记——unprobed/self-unwashable
  /frozen-in-service 逐根·零链根红账补 no-chain-root 目禁哑墙·
  cures_planned/cures_applied 恒 0＝零落刀零复核·exit 0 红是基线数据非器红）。
  互斥：--audit 与 --apply 同给 rc=2（审计只读）·与 --loop 同给 rc=2（单遍
  基线·哨态循环非审计语义）·与 --state-file 同给 rc=2（seen 哨态差分非审计
  语义）·--rounds 不适用单遍。
  零写盘硬保证＝--src 全文件 md5 清单跑前跑后自证恒同（probe_engine 本就
  copyfile 出树编译·wash/probe_engine.py:163·产物清场 py:194——清单违同即
  fail-loud 9·染污基线不出账）；workdir/--json/events 出账系审计本职不在保域。
  耗时各段（enumerate/manifest/probe+chain/total）入 report["timing"]＝实测
  墙钟·报告唯一非确定段（「同输入重跑字节恒同」除 timing 段外仍全成立）；
  timing 段另录 jobs 维度＝--probe-parallel K 实参（probe_engine --jobs 透传
  值·缺省 1）入账——同候选面异 K 前后跑 timing 段可比（并行剖面采集口·
  examples/baselines/perf-README.md 规程；injector 罐装模式本参旁路照记）。
  离线可测同闭环：--injector canned probe 即 audit 探针罐装（selftest 矢量⑩）；
  **真树 audit 活跑归主会话**（本器只证 fixture 级）。

--probe-parallel K（probe_engine --jobs 并行度透传·缺省 1＝逐件串行零漂移）：
  ①归集真探针/④复探 resprobe/--audit 同享同参——候选件分片 ThreadPool 并行
  （台账记录序恒按候选典序·并行完成序不改变输出序·确定性铁律；md5_match/
  verdict 逻辑零改·per-件 build log 仍独立落 logdir；真编译仍逐件经 --guard
  cpu_guard 包裹·guard FRONT 档自带钳位）。K>1＝机内多 rocqworker 并发＝热
  负载↑——--guard 同给时建议 K≤2（注记不强制·用户自裁·温控警示详见
  wash/probe_engine.py docstring 并行节）。injector 罐装模式零真编译·本参
  旁路（canned 直落 workdir）。

--once/--loop 双模（v37 三器共同接口纪律③）：
  --once（缺省）单次闭环；--loop 实时哨态：闭环周而复始（--interval 秒间隔·
  --sleep-scale 乘数·selftest 用 0＝零真睡），轮事件＋周事件 JSONL 流写
  --events（缺省 <workdir>/events.jsonl）；终局 verdict（unclogged/wall）即停
  即退；rounds-exhausted 非终局 → 歇 --interval 再下一周（--loop-max 帽·0=不限）。
  互斥明义：--rounds 与 --loop 同给 rc=2（--rounds 是单遍闭环轮帽·哨态周循环
  非其语义·周内轮帽恒缺省 5——同 --audit/--loop 同给律·禁静默择一）。
--state-file 哨态 seen 状态（rocqwash-sentinel-state/1·与 cw_sentinel
  --state-file 同形——同 schema 同键形 repos/ledgers/buildlogs·互读写兼容）：
  轮间红账差分事件 only-new——每轮归集红账对 state.red_seen 差分，新现红件
  emit {"event":"red-new", new_red:[...]}（已 seen 红不再报·seen 单调只增）；
  事件先 emit 后存 state（宁重复不丢件·承哨纪律）；缺省 None＝差分关（零行
  为变）；损坏 state（解析失败/键形坏）→ fail-loud 9 红拒禁静默重建（恢复＝
  人工删件·器不吞）。

离线可测（硬要求·子进程调用层可注入·零真网络零真编译于 selftest）：
  --injector DIR  DIR/scenario.json＝{"probe":[probe_ledger...],
                  "resprobe":[probe_ledger...]}——probe/resprobe 两类 probe_engine
                  调用按序严格消费 canned 台账（原样落 workdir 后仍喂**真**
                  chain_graph·耗尽/缺列/形坏 fail-loud 2·零真编译）；chain_graph/
                  cure_applier/scan_v4_token/frozen8 纯 stdlib 零编译零网络·注入
                  模式下照旧真跑（真编排非傀儡）。
  --sleep-scale F 全部 sleep 乘 F（selftest 用 0＝零真睡）。

输出（确定性·sort_keys·同输入重跑 --json 字节级恒同·报告零墙钟零绝对路径——
路径只出基名·全路径走 stdout 响亮；audit 模式 timing 段例外＝实测墙钟逐跑
必异·余段仍恒同）：
  --json report·schema=rocqwash-unclog/1：
    {schema, mode{source,apply,injector,loop[,audit]}, args, cycles?,
     rounds[{round, probe_summary{source,n_records,n_red,red_files,ledgers},
             chain_top[{lib,n,dependents,self{probed,rc,verdict,washable}}],
             root, root_file, cure{stage,rc,total_matches,patterns,md5_before,
             md5_after,on_disk_md5_match,reason}?, cures_planned, cures_applied,
             rescan{rc,ids,station_count,residual_zero}?,
             resprobe{rc,rc_ok,n_records,md5_match}?}],
     wall{root:{root,reason,detail}}, timing?（audit·耗时各段＋jobs 维度）,
     final{verdict,rounds_run,red_files,
     cures_planned_total,cures_applied_total,wall_count}, verdict}
  verdict ∈ unclogged|wall|rounds-exhausted|audit（audit=只读基线·exit 0）。
  每轮进度 log 行（响亮 stdout）：[round k/N] root=X cures=Y。

用法（路径全参数化·零硬编码绝对路径；器件路径由本件所在仓派生·pushci 判例）：
  python3 tools/unclog.py --src DIR --world DIR \
      [--candidates TSV | --chain-ledgers LEDGER.json ...] \
      [--repo-path DIR] [--rounds 5] [--apply] [--top 25] [--scan-ids S]
      [--probe-resume] [--probe-parallel K] [--rocq-cmd TPL] [--guard PATH
      --guard-reg DIR --guard-front N --guard-mid N --guard-maxwait N
      --timeout S]
      [--pack cure_pack.json] [--workdir DIR] [--json out.json] [--events out.jsonl]
      [--once | --loop [--interval 60] [--loop-max 0]] [--sleep-scale 1.0]
      [--injector DIR] [--state-file STATE.json]
  python3 tools/unclog.py --src DIR [--world DIR] --audit [--injector DIR] \
      [--repo-path DIR] [--top 25] [--probe-parallel K] [--workdir DIR] \
      [--json out.json]
  python3 tools/unclog.py --selftest

退出码：0=unclogged／audit；1=wall／rounds-exhausted（红是数据非器红·响亮
stdout）；2=用法错／注入场景形错（--rounds 与 --loop 同给/--audit 与
--apply·--loop·--state-file 同给/--probe-parallel<1/--state-file 目录缺）；
9=fail-loud（路径缺失／器红：引擎子进程非数据性非零退／frozen 在册不可得／
全树枚举零候选／audit 零写盘自证破／state 文件损坏红拒禁静默重建）。
--selftest：0=全过／2=断言失败。

世界纪律：本器零写 --world（世界 .vo 基座由调用方按 wash/world_hook.py 认证代
纪律播种；洗后复探红是否清账取决于世界换代·本器如实出账禁硬凑）。
