# tools/unclog.py 中文原面留档（archive）


- 源文件：`tools/unclog.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `tools/unclog.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 注释（逐字·按行序）

```
L232: # --state-file 同形承 cw_sentinel
L254: # ---- 小件（确定性 helpers）---------------------------------------------------
L338: # ---- state（--loop 哨态 seen 持久层·与 cw_sentinel --state-file 同形）--------
L383: # ---- 注入点：probe/resprobe 两类探针调用 canned（离线零真编译）----------------
L423: # ---- 器件编排层（probe_engine/chain_graph/cure_applier/scan_v4_token）---------
L434: # -- probe_engine（①归集／④复探·可注入）--------------------------------
L447: # --probe-parallel 透传（缺省 1）
L454: # 每轮真探=当前红账（resume 会对未变件 skip 留陈账）
L467: # -- chain_graph（②链根·恒真跑）------------------------------------------
L479: # -- cure_applier（③落刀·恒真跑·干跑缺省 --apply 落刀）--------------------
L488: # -- scan_v4_token（④复扫·恒真跑）-----------------------------------------
L497: # ---- frozen 在册（certify/frozen8.py·预检红拒·缺册 fail-closed）---------------
L539: # ---- 闭环状态机（一轮＝①归集→②链根→③落刀→④复核；判定在①口）----------------
L583: # 同形哨态 seen 账（--state-file 在场时）
L603: # -- 墙账（按根去重·确定性）------------------------------------------------
L622: # washable 而已在墙（cure-miss/frozen）者因已在册·不重记
L624: # -- ①归集 -----------------------------------------------------------------
L646: # -- 红账差分（--state-file 同形哨态 seen·only-new）------------------------
L667: # -- ②链根挑根（frozen 预检红拒内嵌）---------------------------------------
L685: # -- 单轮 -------------------------------------------------------------------
L695: # 轮间红账差分事件 only-new（--state-file 在场时）
L697: # ⑤判定口：红账空＝疏通（终判探含轮尽后补探）
L707: # ⑤判定口：轮尽（终判探仍红）
L722: # 零链根（红账无一缺库分组·代差型/器因红）——墙账不得哑：
L723: # 补 no-chain-root 墙目逐件列红（verdict 仍 wall·禁硬凑）
L746: # ③落刀（只正典包·只对链根件）
L805: # ④复核（rescan 残差应零＋resprobe rc 应 0——如实出账不粉饰）
L839: # 下一轮
L865: # ---- --audit 只读审计（真树堵账基线·单遍·零落刀零写树）------------------------
L911: # 墙账（graph 判例全记·含 frozen 预检——数据入账非停机条件）
L936: # 零写盘硬保证（--src 全文件 md5 清单前后自证·违即 fail-loud 9）
L990: # ---- 总控（--once/--loop 哨态）------------------------------------------------
L993: # 值校验（2）
L999: # 缺省轮帽（--rounds 未给·once/loop 同值）
L1024: # 路径校验（9·器件先验）
L1048: # state 装载（--state-file 同形哨态 seen·损坏红拒 9 fail-loud）
L1062: # 候选面三源
L1082: # 注入器（probe/resprobe canned·零真编译）
L1094: # frozen 在册（fail-closed 预检）
L1099: # 事件流（JSONL）
L1111: # --audit 单遍只读基线（不进闭环·零落刀·--src md5 前后自证）
L1253: # ---- --selftest（内嵌冻结向量组·tmp fixture 树·零真编译零网络）-----------------
L1325: # A 可洗链根·B 缺 A
L1326: # 世界换代后全绿
L1327: # 世界未换代仍红
L1331: # 矢量① 绿径两轮疏通：round1 治根 A（正典 cure13 落刀）→round2 复探绿 exit 0
L1354: # 矢量② 诚实墙：self-unwashable（链中环）·零落刀·exit 1
L1374: # 矢量②b 零链根红账（代差型/器因红）→ 墙账补 no-chain-root 目（禁哑墙）
L1392: # 矢量③ cure-miss 入墙：可洗根但正典包零方案
L1408: # 矢量④ 轮尽：--apply 已落刀而世界仍红 → rounds-exhausted 附各轮账
L1426: # 矢量⑤ --apply 缺省关实证：有方案而零落刀 → tmp 树零字节动
L1455: # 矢量⑥ JSON 幂等：同输入重跑 --json 字节级恒同
L1475: # 矢量⑦ frozen 在册红拒：根名撞在册（wash_engine）→零落刀入墙
L1503: # 矢量⑧ --loop 哨态：JSONL 事件流＋终局即停（loop-max 1·sleep-scale 0）
L1523: # 矢量⑨ CLI 四码
L1547: # 矢量⑩ --audit 只读基线：全树 probe 干跑归集→chain_graph→基线报告
L1548: # （零写盘自证·final=audit·cures 恒空·墙账 graph 判例·exit 0）
L1562: # L1: B 缺 A
L1573: # 可洗非 frozen·墙空
L1583: # 矢量⑩b audit 墙账：self-unwashable 入墙（数据非停机·exit 0）
L1599: # Y 自身 rc1 亦红
L1602: # 矢量⑩c audit frozen 预检：可洗根撞在册 → frozen-in-service 入墙
L1623: # 矢量⑩d audit 互斥：--apply／--loop 同给 rc=2
L1633: # 矢量⑪ --state-file 同形哨态 seen：轮间红账差分事件 only-new 三连跑
L1634: # （新现红报／复现红不报／新红再报）＋state 跨进程续账＋损坏红拒 9
L1635: # （chain-ledgers 源·零注入零真编译：根 A NOMATCH→cure-miss 墙·零
L1636: # rescan/resprobe 路径）
L1656: # 跑 1：红账 {B} 全新 → red-new [B]·state 记 seen
L1660: # 红是数据非器红（wall）
L1672: # 跑 2：红账 {B,C}·B 已 seen → red-new 只 [C]（only-new）
L1681: # 跑 3：红账 {B,C} 全已 seen → 零 red-new（复现红不再报）
L1688: # 损坏 state 红拒 9（禁静默重建·原件不动）
L1702: # 矢量⑫ --rounds 与 --loop 互斥明义 rc=2＋--audit 与 --state-file 互斥
L1703: # ＋--probe-parallel<1 用法闸 rc=2（透传参数缺省 1·零漂移）
L1725: # 矢量⑬ --jobs 维度：audit timing 段记 jobs=K（--probe-parallel 实参·
L1726: # probe_engine --jobs 透传值·缺省 1）——同候选面异 K 前后跑可比
L1727: # （并行剖面采集口·injector 罐装模式本参旁路照记·零真编译）
```

## 函数级 docstring（逐字）

### UnclogError（L247-247）

```
带退出码的 fail-loud 异常（2=用法/场景形错·9=路径缺失/器红）。
```

### sleep_scaled（L269-269）

```
time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·pushci 同款）。
```

### emit（L287-287）

```
JSONL 事件流一行（sort_keys·零墙钟·确定性内容）。
```

### run_py（L295-295）

```
python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·pushci 同款）。缺件→9。
```

### write_cands_tsv（L306-306）

```
候选清单 TSV（件名/md5 双列·probe_engine 必需列形制）。
```

### enumerate_tree（L314-314）

```
--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·双排序）。
```

### tree_manifest（L327-328）

```
--src 全文件 {rel(POSIX 形): md5} 清单（audit 零写盘自证用·全文件非仅
    .v——增删改一字节即现形）。
```

### new_state（L341-341）

```
零态账（同形 cw_sentinel.new_state：三域 dict＋本器差分域 red_seen）。
```

### load_state（L347-350）

```
state 装载（同形 cw_sentinel.load_state）：缺省 None/文件缺失＝零态
    起步；损坏（JSON 解析失败/repos/ledgers/buildlogs 键缺 dict/red_seen 非
    list）→ fail-loud 9 红拒·禁静默重建（seen 是差分账·静默重建＝红事件
    重报面失守·损坏原件原样不动——恢复＝人工删件下轮零态起步）。
```

### save_state（L372-373）

```
state 落盘（sort_keys 规范式·差分事件先 emit 后存本函数——宁重复不
    丢件承哨纪律）。目录缺 → 9。
```

### Injector（L386-388）

```
--injector DIR/scenario.json＝{"probe":[ledger...],"resprobe":[ledger...]}
    按序严格消费（probe_engine canned 台账原样落 workdir 后仍喂真 chain_graph）；
    耗尽/缺列/形坏 fail-loud 2。
```

### Engines（L426-427）

```
四器子进程编排（probe/resprobe 可注入·chain/cure/scan 恒真跑——纯 stdlib
    零编译零网络·真编排非傀儡）。
```

### resprobe（L462-462）

```
④复探受治件：mini 候选清单 → probe_engine（fresh·world 同归集）。
```

### frozen8_rels（L500-500）

```
frozen8 --ledger 子进程实取在册八件 rel（fail-closed：rc!=0/零行→9）。
```

### build_frozen_hit（L516-517）

```
在册名单→红拒判定闭包：根名撞 rel/基名/去扩展名 或根件 realpath 撞在册
    文件（--src/--repo-path 双侧解析）即 True。→ (hit, 在册件数)。
```

### chain_top_of（L542-542）

```
链根 TOP 榜摘要（top_order 显式保秩·chain_graph 同秩）。
```

### args_summary（L552-552）

```
args → report["args"] 摘要（路径只出基名·零绝对路径·闭环/audit 共用）。
```

### UnclogRun（L570-571）

```
单周闭环。红账空→unclogged；无正典可洗根/全根碰壁→wall；轮尽红未清→
    rounds-exhausted（终判探在轮尽后补一发①）。
```

### wall_from_graph（L611-611）

```
TOP 榜不可洗根入墙（幂等·已有因者不重记）。
```

### collect（L626-626）

```
→ (graph, red_files, probe_summary)·红账=stats.rc1∪stats.other。
```

### red_diff（L648-652）

```
轮间红账差分事件 only-new：新现红件（不在 state.red_seen）→ emit
        {"event":"red-new", new_red:[...], red_total, seen_before}·seen 并账
        落盘（事件先 emit 后存 state——宁重复不丢件承哨纪律）。已 seen 红
        不再报（seen 单调只增·only-new 语义）；缺省无 --state-file＝差分关
        （零事件零写盘·行为不变）。
```

### pick_root（L669-670）

```
取 self.washable=true 之首（跳过已在墙者·frozen 红拒入墙续挑）。
        → (root|None, root_file|None)。
```

### run_audit（L869-880）

```
--audit 单遍只读基线（v38 真实树基线数据用）：全树 probe 干跑归集→
    chain_graph→堵账基线报告。schema 同 rocqwash-unclog/1：final.verdict=
    audit·rounds 单轮（probe_summary/chain_top 全在·cure/rescan/resprobe
    恒 None·cures_planned/cures_applied 恒 0）·墙账 graph 判例全记——
    unprobed/self-unwashable/frozen-in-service 逐根（数据入账非停机条件·
    audit 不挑根不落刀）·零链根红账补 no-chain-root 目禁哑墙·exit 0（红是
    基线数据非器红）。零写盘硬保证＝--src 全文件 md5 清单跑前跑后自证恒同
    （probe_engine 本就 copyfile 出树编译·wash/probe_engine.py:163·产物清场
    py:194——清单违同即 fail-loud 9·染污基线不出账）。耗时各段入
    report["timing"]＝实测墙钟·报告唯一非确定段；jobs 维度（--probe-parallel
    K 实参·probe_engine --jobs 透传值·缺省 1）同段入账——同候选面异 K
    前后跑可比（并行剖面采集口）。
```

### selftest（L1262-1273）

```
十四矢量（tmp fixture 树＋injector canned probe_ledger 序列·probe/resprobe
    注入零真编译·chain/cure/scan/frozen8 真跑）：①绿径两轮疏通（--apply 落刀→
    次轮红账空 exit 0）②诚实墙（self-unwashable·零落刀）＋②b 零链根红账
    （no-chain-root 墙目·禁哑墙）③cure-miss 入墙④轮尽（--apply 已落刀而世界
    仍红→rounds-exhausted 附各轮账）⑤--apply 缺省关实证（零字节动）⑥JSON 幂等
    （字节恒同）⑦frozen 在册红拒 ⑧--loop 哨态 JSONL ⑨CLI 四码 ⑩--audit 只读
    基线（零写盘自证/final=audit/cures 恒空/墙账 graph 判例/frozen 预检/互斥
    rc=2·真树 audit 活跑归主会话本席只证 fixture 级）⑪--state-file 同形哨态
    seen（轮间红账差分事件 only-new 三连跑：新现红报/复现红不报/新红再报·
    state red_seen 跨进程续账·损坏 state 红拒 9 禁静默重建）⑫--rounds 与
    --loop 互斥 rc=2＋--audit 与 --state-file 互斥 rc=2⑬--jobs 维度（audit
    timing 段 jobs=K 入账·缺省 1/--probe-parallel 2 各录其值·前后跑可比）。
```

## 字符串常量（逐字·按行序）

```
L247: '带退出码的 fail-loud 异常（2=用法/场景形错·9=路径缺失/器红）。'
L269: 'time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·pushci 同款）。'
L283: '%s JSON 形坏: %s (%s)'
L287: 'JSONL 事件流一行（sort_keys·零墙钟·确定性内容）。'
L295: 'python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·pushci 同款）。缺件→9。'
L297: '工具链件缺失: %s'
L306: '候选清单 TSV（件名/md5 双列·probe_engine 必需列形制）。'
L308: '件名\tmd5\n'
L314: '--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·双排序）。'
L327: '--src 全文件 {rel(POSIX 形): md5} 清单（audit 零写盘自证用·全文件非仅\n    .v——增删改一字节即现形）。'
L341: '零态账（同形 cw_sentinel.new_state：三域 dict＋本器差分域 red_seen）。'
L347: 'state 装载（同形 cw_sentinel.load_state）：缺省 None/文件缺失＝零态\n    起步；损坏（JSON 解析失败/repos/ledgers/buildlogs 键缺 dict/red_seen 非\n    list）→ fail-loud 9 红拒·禁静默重建（seen 是差分账·静默重建＝红事件\n    重报面失守·损坏原件原样不动——恢复＝人工删件下轮零态起步）。'
L359: 'state 文件形坏（解析失败·禁静默重建）: %s (%s)'
L363: 'state 文件形坏（缺 %s dict·禁静默重建）: %s'
L366: 'state 文件形坏（red_seen 须 list·禁静默重建）: %s'
L372: 'state 落盘（sort_keys 规范式·差分事件先 emit 后存本函数——宁重复不\n    丢件承哨纪律）。目录缺 → 9。'
L378: 'state 文件目录缺失: %s'
L386: '--injector DIR/scenario.json＝{"probe":[ledger...],"resprobe":[ledger...]}\n    按序严格消费（probe_engine canned 台账原样落 workdir 后仍喂真 chain_graph）；\n    耗尽/缺列/形坏 fail-loud 2。'
L393: 'injector 场景缺失: %s'
L394: 'injector 场景'
L396: 'injector 场景形坏（须 dict）: %s'
L399: 'injector 场景缺 canned probe 序列（离线零真编译纪律·probe 必给非空 list）: %s'
L410: 'injector 场景缺 canned %s 序列（第 %d 次 %s 调用）'
L413: 'injector canned %s 序列耗尽（第 %d 次调用）'
L418: 'injector canned %s 第 %d 项形坏（须含 records dict 的 probe_ledger）'
L426: '四器子进程编排（probe/resprobe 可注入·chain/cure/scan 恒真跑——纯 stdlib\n    零编译零网络·真编排非傀儡）。'
L442: '--world 必给（%s 真探针；离线请 --injector）'
L457: 'probe_engine 器红 rc=%d（%s）: %s'
L459: 'probe 台账'
L462: '④复探受治件：mini 候选清单 → probe_engine（fresh·world 同归集）。'
L472: 'chain_graph 器红 rc=%d: %s'
L473: '链根图'
L475: '链根图 schema 不识: %r（期待 %s）'
L485: 'cure 报告'
L493: 'scan_v4_token 器红 rc=%d: %s'
L494: 'token 普查'
L500: 'frozen8 --ledger 子进程实取在册八件 rel（fail-closed：rc!=0/零行→9）。'
L503: 'frozen8 在册不可得 rc=%d（fail-closed 禁落刀）: %s'
L511: 'frozen8 --ledger 输出无可解析在册行（fail-closed 禁落刀）'
L516: '在册名单→红拒判定闭包：根名撞 rel/基名/去扩展名 或根件 realpath 撞在册\n    文件（--src/--repo-path 双侧解析）即 True。→ (hit, 在册件数)。'
L542: '链根 TOP 榜摘要（top_order 显式保秩·chain_graph 同秩）。'
L552: 'args → report["args"] 摘要（路径只出基名·零绝对路径·闭环/audit 共用）。'
L570: '单周闭环。红账空→unclogged；无正典可洗根/全根碰壁→wall；轮尽红未清→\n    rounds-exhausted（终判探在轮尽后补一发①）。'
L611: 'TOP 榜不可洗根入墙（幂等·已有因者不重记）。'
L617: '根件未入候选集（UNPROBED·候补探）'
L620: '根件自身被阻 rc=%s verdict=%s（链中环·先治根的因）'
L626: '→ (graph, red_files, probe_summary)·红账=stats.rc1∪stats.other。'
L648: '轮间红账差分事件 only-new：新现红件（不在 state.red_seen）→ emit\n        {"event":"red-new", new_red:[...], red_total, seen_before}·seen 并账\n        落盘（事件先 emit 后存 state——宁重复不丢件承哨纪律）。已 seen 红\n        不再报（seen 单调只增·only-new 语义）；缺省无 --state-file＝差分关\n        （零事件零写盘·行为不变）。'
L669: '取 self.washable=true 之首（跳过已在墙者·frozen 红拒入墙续挑）。\n        → (root|None, root_file|None)。'
L680: '根名/根件撞 frozen8 在册（预检红拒·零落刀）'
L693: '[round %d/%d] 归集: %s 红账 %d: %s'
L725: '红账 %d 件无一缺库链根（代差型/器因红·禁硬凑）: %s'
L753: '链根件缺失: %s（红因所缺库无对应源件）'
L759: '变体须 --only 人择（禁自动代选）·groups=%s'
L762: 'cure_applier 器红 rc=%d（干跑 %s）: %s'
L776: '正典包干跑零方案（total_matches=0）'
L785: '落刀遇变体冲突（零写盘）'
L789: '落刀幂等断言败（cure_applier 拒写·文件未动）'
L792: 'cure_applier 器红 rc=%d（落刀 %s）: %s'
L831: ' resprobe-rc=%s（应 0 未达·如实入账）'
L869: '--audit 单遍只读基线（v38 真实树基线数据用）：全树 probe 干跑归集→\n    chain_graph→堵账基线报告。schema 同 rocqwash-unclog/1：final.verdict=\n    audit·rounds 单轮（probe_summary/chain_top 全在·cure/rescan/resprobe\n    恒 None·cures_planned/cures_applied 恒 0）·墙账 graph 判例全记——\n    unprobed/self-unwashable/frozen-in-service 逐根（数据入账非停机条件·\n    audit 不挑根不落刀）·零链根红账补 no-chain-root 目禁哑墙·exit 0（红是\n    基线数据非器红）。零写盘硬保证＝--src 全文件 md5 清单跑前跑后自证恒同\n    （probe_engine 本就 copyfile 出树编译·wash/probe_engine.py:163·产物清场\n    py:194——清单违同即 fail-loud 9·染污基线不出账）。耗时各段入\n    report["timing"]＝实测墙钟·报告唯一非确定段；jobs 维度（--probe-parallel\n    K 实参·probe_engine --jobs 透传值·缺省 1）同段入账——同候选面异 K\n    前后跑可比（并行剖面采集口）。'
L882: '=== AUDIT 只读基线（单遍 probe 归集→chain_graph·零落刀零写树）==='
L905: '[audit] 归集: %s 红账 %d: %s'
L922: '根件未入候选集（UNPROBED·候补探）'
L925: '根件自身被阻 rc=%s verdict=%s（链中环·先治根的因）'
L930: '根名/根件撞 frozen8 在册（预检红拒·人审域）'
L933: '红账 %d 件无一缺库链根（代差型/器因红·禁硬凑）: %s'
L944: 'audit 零写盘硬保证破：--src 树被动（改 %d/增 %d/删 %d: %s）'
L985: 'AUDIT: 红账 %d·墙 %d——基线报告零落刀零写树（exit 0）'
L995: '--rounds 与 --loop 互斥（--rounds 是单遍闭环轮帽·哨态周循环非其语义·周内轮帽恒缺省 5——同给 rc=2 禁静默择一）'
L1001: '--rounds 须≥1 实测 %d'
L1003: '--probe-parallel 须≥1 实测 %d（probe_engine --jobs 透传·缺省 1）'
L1006: '--top 须≥1 实测 %d'
L1008: '--interval 须≥0 实测 %s'
L1010: '--sleep-scale 须≥0 实测 %s'
L1012: '--loop-max 须≥0 实测 %d'
L1014: '--audit 与 --apply 互斥（审计只读零落刀·同给 rc=2）'
L1016: '--audit 与 --loop 互斥（审计单遍基线·哨态循环非审计语义）'
L1019: '--audit 与 --state-file 互斥（审计单遍基线·seen 哨态差分非审计语义）'
L1022: '--candidates 与 --chain-ledgers 互斥（候选面三源任选）'
L1029: '器件缺失: %s (%s)'
L1031: 'FAIL-LOUD: --src 必给'
L1033: '--src 路径缺失: %s'
L1035: '--candidates 路径缺失: %s'
L1038: '--chain-ledgers 路径缺失: %s'
L1040: '--pack 路径缺失: %s'
L1042: '--injector 目录缺失: %s'
L1046: '--state-file 目录缺失: %s'
L1051: 'state -> %s（seen %d 件·rocqwash-sentinel-state/1 同形）'
L1066: '候选面: --candidates %s'
L1069: '候选面: --chain-ledgers %s（merge 模式·无逐轮全量重探）'
L1076: '--src 全树枚举零 .v 候选: %s'
L1080: '候选面: --src 全树枚举 %d 件 -> %s'
L1085: 'injector: %s（probe canned %d 发·resprobe canned %s）'
L1088: '缺列'
L1090: 'ADVISE(温控): --probe-parallel %d>1＝机内多 rocqworker 并发·热负载↑（--guard 同给建议 K≤2·注记不强制·用户自裁）'
L1096: 'frozen 在册: %d 件（certify/frozen8.py --ledger 实取·预检红拒）'
L1131: '[cycle %d] %s — 哨态歇 %g s 后再巡'
L1160: '疏通堵塞闭环引擎（v37 旗舰）：probe 归集→chain_graph 链根→cure_applier 落刀→scan/probe 复核→判定·--rounds 帽自旋·--apply 缺省全干跑零写盘·离线可注入·schema rocqwash-unclog/1'
L1164: '源树根（根件 <根>.v 取自此·全树枚举源亦自此）'
L1166: '世界目录（probe_engine 探针 cwd·.vo 基座调用方按 world_hook 纪律播种·本器零写；merge 模式可省·真探针必给）'
L1169: '候选清单 TSV（源①·probe_engine 同款表头）'
L1172: '既有 probe 台账（源②·argv 序=合并序·后批覆盖前批）'
L1174: 'frozen 在册文件解析根（默认本件所在仓）'
L1176: '单遍闭环轮帽（缺省 5·轮尽红未清=rounds-exhausted·与 --loop 互斥同给 rc=2）'
L1179: '落刀开关（缺省关＝全干跑零写盘·单开关 --yes 不需要）'
L1181: '只读审计：单遍 probe 归集→chain_graph→堵账基线报告（final=audit·零落刀·--src 全文件 md5 前后自证恒同·cures 恒空·与 --apply/--loop 互斥）'
L1185: '链根 TOP 榜截断（默认 25·chain_graph 同款）'
L1187: 'scan_v4_token 跟踪标识（默认 S）'
L1189: '正典 cure_pack（默认 wash/cure_pack.json v1.3）'
L1191: 'probe_engine 用 resume（缺省每轮 --fresh 真探当前红账）'
L1194: 'probe_engine --jobs 并行度透传（缺省 1＝逐件串行零漂移·--audit 同享·--guard 同给建议 K≤2 温控自裁）'
L1198: '探针命令模板透传 probe_engine'
L1200: 'cpu_guard.sh 透传 probe_engine（真编译必给）'
L1207: 'probe_engine 单件超时秒透传'
L1209: '逐轮台账/报告工件目录（缺省 mkdtemp·stdout 响亮路径）'
L1211: 'report 出账（rocqwash-unclog/1·sort_keys）'
L1213: 'JSONL 事件流出账（--loop 缺省 <workdir>/events.jsonl）'
L1215: '单次闭环（缺省·与 --loop 双模接口纪律成对）'
L1217: '实时哨态：闭环周而复始至终局 verdict／--loop-max 帽'
L1219: '哨态周间歇秒（默认 60·乘 --sleep-scale）'
L1221: '哨态周帽（默认 0=不限）'
L1223: '全部 sleep 乘数（selftest 用 0＝零真睡）'
L1225: '离线注入：DIR/scenario.json（probe/resprobe canned probe_ledger 按序严格消费·零真编译）'
L1229: '哨态 seen 状态文件（rocqwash-sentinel-state/1·与 cw_sentinel --state-file 同形互读写·轮间红账差分事件 only-new·损坏红拒 9 禁静默重建）'
L1262: '十四矢量（tmp fixture 树＋injector canned probe_ledger 序列·probe/resprobe\n    注入零真编译·chain/cure/scan/frozen8 真跑）：①绿径两轮疏通（--apply 落刀→\n    次轮红账空 exit 0）②诚实墙（self-unwashable·零落刀）＋②b 零链根红账\n    （no-chain-root 墙目·禁哑墙）③cure-miss 入墙④轮尽（--apply 已落刀而世界\n    仍红→rounds-exhausted 附各轮账）⑤--apply 缺省关实证（零字节动）⑥JSON 幂等\n    （字节恒同）⑦frozen 在册红拒 ⑧--loop 哨态 JSONL ⑨CLI 四码 ⑩--audit 只读\n    基线（零写盘自证/final=audit/cures 恒空/墙账 graph 判例/frozen 预检/互斥\n    rc=2·真树 audit 活跑归主会话本席只证 fixture 级）⑪--state-file 同形哨态\n    seen（轮间红账差分事件 only-new 三连跑：新现红报/复现红不报/新红再报·\n    state red_seen 跨进程续账·损坏 state 红拒 9 禁静默重建）⑫--rounds 与\n    --loop 互斥 rc=2＋--audit 与 --state-file 互斥 rc=2⑬--jobs 维度（audit\n    timing 段 jobs=K 入账·缺省 1/--probe-parallel 2 各录其值·前后跑可比）。'
L1346: '落刀非正典形'
L1347: '非链根件被动＝违例'
L1352: '矢量① 绿径两轮疏通（--apply 落刀→次轮红账空 exit 0）: PASS'
L1368: 'wall 轮不得有落刀（禁硬凑）'
L1372: '矢量② 诚实墙（self-unwashable 零落刀 exit 1）: PASS'
L1390: '矢量②b 零链根红账（no-chain-root 墙目·禁哑墙）: PASS'
L1406: '矢量③ cure-miss 入墙（正典包零方案·禁硬凑）: PASS'
L1424: '矢量④ 轮尽（--apply 落刀而世界仍红·附各轮账 exit 1）: PASS'
L1443: '干跑应有方案'
L1450: '--apply 缺省关下源树字节被动＝违例'
L1452: '无 --apply 不得有落刀账'
L1453: '矢量⑤ --apply 缺省关实证（有方案而零字节动）: PASS'
L1472: '同输入重跑 --json 字节漂移＝违例\n%s\n%s'
L1473: '矢量⑥ JSON 幂等（同输入重跑字节恒同）: PASS'
L1495: 'frozen 红拒后不得落刀'
L1500: 'frozen 件被落刀＝违例'
L1501: '矢量⑦ frozen 在册红拒（frozen8 实取·零落刀）: PASS'
L1515: '事件流应含 round/cycle_end 等事件: %r'
L1521: '矢量⑧ --loop 哨态（JSONL 事件流·终局即停）: PASS'
L1528: '未知形参应 rc=2 实测 %d'
L1530: '缺 --src 应 rc=2 实测 %d'
L1533: '缺 src 应 rc=9 实测 %d'
L1535: '缺清单应 rc=9 实测 %d'
L1538: '--rounds 0 应 rc=2 实测 %d'
L1541: '三源互斥应 rc=2 实测 %d'
L1544: '缺 injector 场景应 rc=9 实测 %d'
L1545: '矢量⑨ CLI 四码（0/2/9·互斥·injector 缺场景）: PASS'
L1577: 'audit 源树字节被动＝违例'
L1579: '链根件被动＝违例'
L1580: '矢量⑩ audit 只读基线（零写盘自证·final=audit·cures 恒空·timing 段）: PASS'
L1600: '矢量⑩b audit 墙账（self-unwashable 入墙·exit 0 数据非停机）: PASS'
L1620: 'frozen 件被落刀＝违例'
L1621: '矢量⑩c audit frozen 预检（frozen8 实取入墙·零落刀）: PASS'
L1626: '--audit --apply 同给应 rc=2 实测 %d'
L1629: '--audit --loop 同给应 rc=2 实测 %d'
L1631: '矢量⑩d audit 互斥（--apply/--loop 同给 rc=2）: PASS'
L1685: '复现红应零差分事件: %s'
L1695: '损坏 state 应红拒 rc=9 实测 %d'
L1696: '形坏'
L1698: '损坏 state 被静默改写＝违例'
L1699: '矢量⑪ --state-file 同形哨态 seen（差分 only-new 三连跑/跨进程续账/损坏红拒 9 禁静默重建）: PASS'
L1706: '--rounds --loop 同给应 rc=2 实测 %d'
L1708: '互斥'
L1710: '--rounds 0 带 --loop 仍应 rc=2 实测 %d'
L1714: '--audit --state-file 同给应 rc=2 实测 %d'
L1716: '互斥'
L1719: '--probe-parallel 0 应 rc=2 实测 %d'
L1722: '矢量⑫ --rounds/--loop 互斥明义＋--audit/--state-file 互斥＋--probe-parallel 0 用法闸（同给/越界 rc=2）: PASS'
L1747: '矢量⑬ --jobs 维度（audit timing 段 jobs=K 入账·缺省 1/K=2 各录其值·前后跑可比）: PASS'
L1750: 'UNCLOG-SELFTEST PASS: 十四矢量全过（绿径/诚实墙＋零链根补判/cure-miss/轮尽/缺省关实证/JSON 幂等/frozen 红拒/loop 哨态/CLI 四码/audit 只读基线零写盘自证/state-file 差分 only-new/--rounds·--loop 互斥＋--probe-parallel 用法闸＋--jobs 维度）'
```
