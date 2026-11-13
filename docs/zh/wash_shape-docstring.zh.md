# tools/wash_shape.py 中文原面留档（archive）


- 源文件：`tools/wash_shape.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `tools/wash_shape.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 模块 docstring（逐字）

```
wash_shape.py — 洗形器·正典形五洗流水（rocqwash tools/·v37 三器共同接口·20261111）

正典形五洗（逐文件依序执行·各洗可 --only 选·判例出处逐洗标注）：
  ①词面洗 lexical   subprocess verify/gate4_comment_guard.py --file（五检项 v2.1
                    EXT·rc 0/1/2 分流承 tools/pushci.py gate4_prescan 先例）→
                    FAIL 项（hard 词面项）与 review 语境双义项对 wash/comment_pack.json
                    flag_words 查正典同义改写式（sidecar 自述 trigger＝「gate4
                    comment-guard review findings」；flag_word_note＝「Context-biaised
                    review words exchange to their neutral English term」——语境双义
                    复核项正是该包的交换靶面）。落刀＝wash/comment_sweep.py --apply
                    （comment_pack 消费器·嵌套注释/字符串感知状态机·代码行相等断言）。
                    无对应式→plan-miss（不硬造——comment_pack「never synthesized」
                    同律）。
  ②token 洗 token   scan/scan_v4_token.py --file 普查（token 级·W5 mixed-line 盲区
                    闭合）→wash/cure_applier.py 正典包（cure_pack v1.3）干跑（该器
                    缺省 dry-run）→--apply 落刀（二遍零残断言内建·rc 1 不落盘）。
                    有站无式→plan-miss；排他组冲突（rc 4）→plan-miss 须人工 --only
                    择一（cure_applier variant-choice 纪律）。
  ③头注形洗 header  两段式＋五字段缺检（gate4 即含：无头注/头注非首块/缺字段/头注
                    超标）→缺失字段方案＝comment_pack 式补写模板（--header-map 逐件
                    数据·comment_sweep --header-map 前导注释区整体替换·内容绝不
                    合成）；或 --header-map-preset 钦名模板（tests/fixtures/
                    header_map_v1.json 蒸馏库·schema rocqwash-header-map/1·占位
                    {name}/{deps_stdlib}/{deps_dev} 承目标件 Require 面与件名派生·
                    {bundle}/{summary}/{mission} 承既有头注逐字携带——任一绑不上
                    plan-miss 不硬造·渲染后仍经 comment_sweep --header-map 落刀）；
                    无模板→plan-miss 不硬造。模板源探测次序：--header-map >
                    --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径）>
                    无＝plan-miss 如实；--header-map 与 --header-map-preset 显传
                    互斥（同槽律 rc 2）。preset 源仅对 gate4 头注域硬项施刀·五字段
                    齐件不对齐改写（防人工 curated 面被机械卷改写·诚实账）。
  ④行尾洗 eol       CRLF→LF 归一（保末行换行形态；3KB 探测窗承 tools/
                    registry_union.py detect_eol EOL_PROBE_BYTES 形制）。前洗引擎
                    universal-newline 写回会附带归一——本洗 apply 以现盘实测为准·
                    零改如实出账。
  ⑤锚形洗 anchor    order.txt 行锚→registry_union.py --reanchor 正典形
                    （#R<序>-<md5 前 8 hex>·20261110 判例：顺序号形锚与跨批撞锚
                    皆此治愈；--reanchor 与 --anchor-src 成对·--apply 必配 --out
                    ——经临时稿 os.replace 回位）。coqproject 行无锚→不适用。
                    缺实体/实体歧义/行无锚→plan-miss（registry_union「缺件如实列
                    跳过」同律）。

两段制：plan（零写盘·逐文件逐洗 {kind,action,status:would-fix|clean|plan-miss,
detail} 清单＋统计）→--apply（执行 would-fix 项→**复跑五洗复核**→全净才 verdict
shaped；复跑不净＝verdict partial·如实列残项）。verdict：clean｜shaped｜partial｜
plan-miss（任一无对应式项在册即 plan-miss——非器力所能及·如实亮账）。

范围与禁触面：--file 多值／--dir 全树（.v＋order.txt/_CoqProject·.v `_*` 下划线
守卫承 gate4 scan_tree v2.1 同律）；certify/frozen8.py 在册八件自动排除（--ledger
账载常量·离线可用）·显式指认冻结件＝红拒命中 exit 2（禁触铁律）；更新账.md 同为
禁触面自动排除。

接口纪律（v37 三器共同）：JSON-in/JSON-out（--json report·schema rocqwash-shape/1·
sort_keys 确定性·无时间戳·同输入重跑字节恒同）；退出码 0=clean/shaped·1=partial/
plan-miss（洗未尽·响亮出账）·2=用法/断言（冻结件红拒·引擎形外退出·JSON 畸形）·
9=缺；--once/--loop 双模（--loop 实时哨态·--interval 可调·--max-rounds 界定·
--apply 可与 loop 并用逐轮落刀）；离线可测（--injector 子进程
调用层罐装 {rc,stdout,report}·--sleep-scale 缩睡·--selftest 全矢量零真网络零真
编译）；编排而非重造（五洗引擎全 subprocess 调用·先读各器 CLI 与 JSON schema 再
编排）。

--loop 事件流（同形对齐·承 cw_sentinel 事件形——三器共同事件解析面）：
  JSONL 逐行 schema=rocqwash-sentinel-event/1·键 sort_keys 规范式·seq 事件流
  内单调（--events 在位以现有行数为基跨进程续号·缺省进程内从 1）·kind∈
  {round,stop}·ts 由 time 钟出（--sleep-scale 0 时关 ts·note「ts=off」注记
  ——确定性同哨）；stdout 镜像恒流＋--events 追加落账（逐行 flush+fsync）。
  round 事件携 round/apply/verdict/五洗计数/n_applied/plan_cache_hit；
  stop 事件携 round/reason=max-rounds/verdict。
plan 缓存失效语义（--loop 跨轮·源件 md5 变→plan 重算）：失效域＝范围件
  （--file/--dir 收件）∪⑤锚实体件（order.txt 行锚实体·anchor_src 解析——
  实体 md5 变/实体出现消失/歧义化亦域变）的 {abspath: md5} 集；逐轮重测域
  （廉价 md5·引擎零重跑）：域恒同→复用上轮 plan（缓存命中·命中轮五洗引擎
  零重判）；任一源件 md5 变→失效重算并刷新域。首轮必重算；--once 单段不走
  缓存；rescan 恒直算（落刀后新鲜盘面·不复用）。响亮出账＝report["plan_cache"]
  {hit}（仅 loop 模式在账）＋round 事件 plan_cache_hit。

用法（全部路径参数化·零硬编码绝对路径）：
  python3 tools/wash_shape.py --file A.v [--file B.v ...] [--json OUT]   # plan 段
  python3 tools/wash_shape.py --dir TREE [--exclude 名 ...] [--only 1,3]
  python3 tools/wash_shape.py --file A.v --apply [--header-map M.json]       [--header-map-preset NAME] [--anchor-src DIR] [--json OUT]         # 两段全施
  python3 tools/wash_shape.py --dir TREE --loop [--interval 5]       [--max-rounds 0] [--events FILE] [--apply]                         # 哨态
  python3 tools/wash_shape.py --selftest

退出码：0=clean/shaped；1=partial/plan-miss（洗未尽·响亮出账）；2=用法错/断言炸
（冻结件红拒/引擎形外退出/JSON 畸形/--header-map 与 --header-map-preset 同槽
互斥）；9=路径缺失（--file/--dir/引擎件/--header-map/--header-map-preset 模板库/
env ROCWASH_HEADER_MAP/--injector/--events 出账写败）。schema=rocqwash-shape/1。

```

## 注释（逐字·按行序）

```
L108: # --loop 事件流同形承 cw_sentinel
L110: # 五洗 kind（正典序·--only 序号映射 1..5）
L111: # ①词面洗
L112: # ②token 洗
L113: # ③头注形洗
L114: # ④行尾洗
L115: # ⑤锚形洗
L133: # gate4 头注域硬项类型（归③头注形洗·词面洗不计）
L135: # comment_pack 交换靶面（flag_word_note 口径）
L137: # 锚正典 1:1 承 registry_union.ANCHOR_RE；行尾探测窗承 detect_eol
L142: # 铁律禁触面（自动排除·显式指认红拒）
L151: # ③头注模板源（探测次序 --header-map > --header-map-preset > env > 无=plan-miss）
L503: # ③头注模板源探测（互斥已在 main 前置 rc2·次序 map > preset > env > 无）
L516: # --loop 事件流 seq（跨进程续基在 run_loop 定）＋plan 跨轮缓存
L521: # ---- 数据面 ----
L682: # else 兜底装载已验·chosen 恒非 None
L687: # 卷行仅施字段身行（4 空格起）——L1 束语行与题行
L688: # 全战役语料恒单行（DecBridge6.v:1 103 列/:3 96 列·
L689: # abl_tail_supply_66.v:1 95 列皆单行）·不卷。
L749: # ---- 引擎调用层（注入点）----
L791: # ---- 收件 ----
L850: # ---- 逐洗判（plan·零写盘）----
L1024: # 纯注释行（registry_union key_of=None 同律）
L1059: # ---- plan 组装 ----
L1104: # ---- plan 缓存（--loop 跨轮·源件 md5 变→重算）----------------------------
L1127: # 件不可读已在范围域记 None
L1138: # 歧义集串本身入域（集变即域变）
L1160: # ---- 逐洗施（apply·两段第二段）----
L1298: # ---- verdict 与报告 ----
L1332: # --loop 跨轮 plan 缓存（响亮出账）
L1357: # ---- 主流程 ----
L1482: # ---- 内件 ----
L1562: # ---------- 自证 ----------
L1644: # 判13/14/16 preset 矢量夹具：战役 `**` 形头注缺 构造性/编译 两字段
L1645: # （gate4 缺字段硬项驱动）·Require 面 From Stdlib 一行＋bare 两行
L1669: # 判16 专用副本（判14 apply 会把 hdmap_fx.v 洗成五字段齐件——plan-miss
L1670: # 矢量须用未经施刀的缺字段件）
L1683: # 判1 plan 五洗逐判（脏件）
L1700: # 判2 正件对照
L1710: # 判3 plan 零写盘·--apply 缺省关
L1716: # 判4 plan-miss 如实（无式件＋混合件）
L1731: # 判5 apply→rescan clean→shaped（词面/CRLF/锚三面实证）
L1755: # 判6 幂等（二跑 plan 全 clean；再 apply 零 applied）
L1769: # 判7 锚缺实体 plan-miss
L1775: # 判8 冻结名排除（injector 罐装名册＋真 frozen8 名册）
L1802: # 判9 子进程调用层注入（gate4 罐装判面）
L1816: # 判10 CLI 四码
L1826: # 判11 --once/--loop 双模（哨态两轮＋stop 事件·事件流同形对齐：
L1827: # schema/seq/kind·sort_keys 规范式·ts=off 注记）
L1841: # stdout 镜像逐行（响亮）
L1852: # 判12 确定性（plan --json 两跑字节恒同）
L1863: # 判13 preset 链（装载在位·齐件不扰·探测次序 preset/--header-map 胜 env）
L1889: # 判14 preset 占位替换渲染→apply 端到端（缺字段件→补写→shaped→幂等）
L1925: # 判15 同槽互斥（双旗 rc2·preset 未知名 rc2）
L1935: # 判16 无源 plan-miss 如实＋模板库缺失 rc9（隔离 repo_root）
L1961: # 判17 --loop 事件流同形对齐（--events 落盘逐行范式·flush+fsync·seq
L1962: # 跨进程续号不重号）
L1983: # 判18 plan 缓存失效语义（源件 md5 变→plan 重算·恒同→命中复用）：
L1984: # a) 范围件 md5 变——loop --apply 三轮：轮1 miss→落刀 CRLF→LF（文件
L1985: #    变）→轮2 必 miss（重算后 eol clean）→轮3 恒同 hit 复用；
L1986: # b) ⑤锚实体件 md5 变亦源变——ToyE.v（实体）轮1 被 eol 落刀而
L1987: #    order_e.txt 未动→轮2 miss 纯实体域驱动（域缺实体即假 hit）→
L1988: #    轮2 落刀改 order_e.txt→轮3 miss→轮4 恒同 hit（序列 [F,F,F,T]）。
L2002: # 轮1 落刀 CRLF→LF
L2003: # 轮2 重算后已 clean
L2048: # ---------- 主流程 ----------
```

## 函数级 docstring（逐字）

### UsageError（L173-173）

```
用法错/断言炸（exit 2：冻结件红拒·引擎形外退出·JSON 畸形）。
```

### MissingInput（L177-177）

```
路径缺失（exit 9）。
```

### sleep_scaled（L189-189）

```
time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·承 pushci 同款）。
```

### now_iso（L194-194）

```
UTC ISO8601 秒精度 Z 形（事件 ts 字段·承 cw_sentinel.now_iso 同形）。
```

### make_event（L200-202）

```
--loop 事件组装（同形承 cw_sentinel.make_event）：schema/seq/kind 头＋
    fields；ts 由 time 钟出·ts_enabled=False（--sleep-scale 0）时关 ts 并以
    note「ts=off」注记（确定性·fields 自带 note 时并入不打架）。
```

### events_seq_base（L215-216）

```
--events 现有非空行数（seq 跨进程续基·承 cw_sentinel emit_seq_base
    同律——追加流以现有行数为基续号）。读败 → 9。
```

### first_code_offset（L225-227）

```
首个代码字符偏移（深度 0·非空白·注释/字符串感知）——前导头注区边界。
    1:1 本地重实现 wash/comment_sweep.py first_code_offset 形制（不 import——
    防引擎件漂移牵连·wash_engine.py 本地重实现同律）。
```

### resolve_entity（L268-269）

```
anchor_src 下（os.walk 递归）取同名 .v 实体。0 命中→None；多处→歧义串。
    1:1 承 registry_union.resolve_entity 形制。
```

### md5_8_of（L284-284）

```
实件 md5 前 8 hex（锚正典指纹源·承 registry_union.md5_8_of）。
```

### strip_comment_spans（L294-296）

```
注释域剥离（留换行·字符串感知）——Require 面抽取前置。
    1:1 本地重实现 wash/comment_sweep.py strip_comments 形制（不 import——
    防引擎件漂移牵连·first_code_offset 本地重实现同律）。
```

### wrap_long_line（L341-342）

```
贪心词卷（>width 且含空格才卷·续行缩 6·超长孤词整词保留）——preset
    渲染卷行形制（战役件卷行宽≈76 续行缩 6·DecBridge6.v:19-29 形制引据）。
```

### require_faces（L358-367）

```
Require 面双列抽取（③头注形洗 preset 占位 {deps_stdlib}/{deps_dev}
    数据源·目标件自身语句逐名·绝不合成）。注释感知剥离（strip_comment_spans）
    后仅取列 0 起顶层语句行：
      From Stdlib Require [Import|Export] A B.  → stdlib 列
      Require [Import|Export] A B.              → dev 列
      From <X> Require [Import|Export] A B.     → dev 列（全名 X.A——战役语料
        五件 grep 零命中·机械完备臂）。
    序＝件内出现序·去重保序。语料引据：ConstructiveWorld-Set @6e805d1
    LW3Kills.v:30-38（From Stdlib 三行＋bare 六行）对照其头注 :13-17 双列；
    abl_tail_supply_67.v:32-35 对照 :15-16。
```

### header_carry（L393-400）

```
既有前导头注区逐字携带抽取（preset 占位 {bundle}/{summary}/{mission}
    绑定源）。返回 dict——缺键即该占位绑不上（judge plan-miss 如实·不硬造）：
      bundle＝L1『(* ConstructiveWorld-Set -- <身>. *)』内文（终句号归模板行）；
      summary＝『(** * <名>: <身>.』题行内文（终句号归模板行）；
      mission＝Mission 字段身（标签行余文＋续行至次字段标签/收注符·换行缩进
      原样逐字携带）。
    语料引据：ConstructiveWorld-Set @6e805d1 DecBridge6.v:1/:3/:5-14 三身
    正典位；头注身内容绝不合成（comment_pack header_spec 同律）。
```

### Injector（L436-439）

```
--injector 场景：子进程调用层罐装（v37 离线可测纪律）。场景 JSON
    {引擎键: {"rc": int, "stdout": str, "report": obj?}}；命中键的引擎调用
    恒定返付 canned（逐调用同响应）·不真 subprocess。键集＝gate4/scan_v4/
    cure/sweep/registry_union/frozen8。
```

### WashShape（L469-469）

```
洗形器主体：收件→逐洗判（plan）→逐洗施（apply）→复跑复核。
```

### _resolve_header_source（L524-527）

```
③头注模板源探测（缺省探测路径次序）：--header-map >
        --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径·与
        --header-map 同构）> 无＝plan-miss 如实（judge_header 缺省臂）。
        --header-map 与 --header-map-preset 同槽互斥 rc2（main 前置）。
```

### _load_flag_words（L548-548）

```
comment_pack.json flag_words（正典同义改写式·数据驱动不硬造）。
```

### _load_header_map（L562-563）

```
头注 map 装载（comment_pack 式补写模板·逐件数据·{basename: text}）。
        缺失＝9·畸形＝2（label 标源：--header-map 或 env ROCWASH_HEADER_MAP）。
```

### _load_header_preset（L576-578）

```
钦名模板装载＋fail-loud 形检（schema rocqwash-header-map/1）：库缺失
        ＝9·JSON 畸形/schema 不识/preset 名不识/占位出白名单/variants 无 else
        兜底/任一模板行缺 evidence 金标引据＝2（金标纪律机械化——无据不铸）。
```

### render_preset_header（L649-654）

```
preset 渲染（③头注形洗·占位替换）：模板行逐行替换占位→超宽行贪心
        卷（wrap_long_line）。占位值全部承目标件自身——{name}＝basename 去 .v·
        {deps_stdlib}/{deps_dev}＝require_faces 双列·{bundle}/{summary}/
        {mission}＝header_carry 既有头注逐字携带——绝不合成。任一占位绑不上→
        (None, 缺位清单)（judge 记 plan-miss 如实）。缓存键＝(abspath, 文面
        md5)（loop 逐轮重判·同件同文恒同·件变即重渲）。
```

### header_map_entry（L699-700）

```
映射查得（basename 带/不带 .v 双试·承 comment_sweep.run 同款）。
        仅 map 源（--header-map/env）——preset 源走 render_preset_header。
```

### _load_frozen_roster（L711-713）

```
certify/frozen8.py --ledger → (abs 集, rel 集, 来源说明)。
        --ledger 只打账载常量（离线·零盘验）·injector 可罐装。行式
        「md5<空白>relpath」；绝对路径行按 abs 收·相对行对 repo_root 归位。
```

### is_forbidden（L745-745）

```
铁律禁触面：冻结八件在册∪更新账.md。
```

### run_engine（L752-755）

```
子进程调用层：injector 命中键→罐装恒定返付；否则真 subprocess
        [sys.executable, -B, tool] + cli（stdout+stderr 合流·承 pushci
        _run_py 形制）。want_json→附 --json tmp·解析后即删。返回
        (rc, stdout, report|None, canned_flag)。
```

### collect_files（L794-796）

```
--file 显式（存在性 9·禁触面红拒 2）＋ --dir 全树（.v 非 _·registry
        两名·隐目录跳过·禁触面与 --exclude 自动排除）。去重按 abspath·序按
        构造路径字符串（确定性）。返回 (files, excluded 记录)。
```

### gate4_report（L853-853）

```
gate4 单件报告（rc 0/1/2 正常·形外/JSON 畸形→器红 exit 2）。
```

### judge_lexical（L863-863）

```
①词面洗：gate4 hard 词面项＋review 语境双义项→flag_words 查式。
```

### judge_token（L901-901）

```
②token 洗：scan_v4 普查→cure_applier 正典包干跑。
```

### judge_header（L935-937）

```
③头注形洗：gate4 头注域硬项＋模板判（map 源＝逐件数据·对齐判与
        补写判并施；preset 源＝钦名模板渲染——仅对硬项施刀·五字段齐件不对齐
        改写（防人工 curated 面被机械卷改写·诚实账）；无源＝plan-miss 如实）。
```

### judge_eol（L982-982）

```
④行尾洗：CRLF→LF 归一（末行换行形态保全）。
```

### judge_anchor（L997-997）

```
⑤锚形洗：order.txt 行锚正典形判（#R<序>-<md5 前 8>）。
```

### plan_file（L1062-1062）

```
单件逐洗判（正典序①→⑤·零写盘）。
```

### compute_plan（L1100-1100）

```
全范围 plan（零写盘）→ {"files": [...], "stats": {...}}。
```

### plan_scope_md5s（L1107-1111）

```
plan 缓存失效域 {abspath: md5}：范围件（--file/--dir 收件）∪⑤锚
        实体件（order.txt 行锚实体·anchor_src 解析——实体 md5 变亦源变）。
        实体出现/消失/歧义化以记号键入域（域集变即失效）；件不可读记 None
        （态变触发重算·fail-soft 域账）。逐轮重测此域＝廉价 md5（五洗引擎
        零重跑）·域恒同→缓存命中。
```

### plan_cached（L1148-1151）

```
plan 跨轮缓存（--loop 哨态）：失效域（plan_scope_md5s）恒同→复用
        上轮 plan（缓存命中·五洗引擎零重判）；任一源件 md5 变→失效重算并
        刷新域（源件 md5 变→plan 重算·钦定语义）。首轮缓存空必重算。
        返回 (plan, hit)。
```

### apply_header（L1192-1195）

```
③落刀：comment_sweep --header-map <具体 map> --apply（引擎恒
        comment_sweep·编排零新引擎）。map 源＝显传/env 路径；preset 源＝现渲
        染单件 map 临时落盘（{basename: 渲染文}·用后即删——渲染值承件自身
        数据·编排不落常盘）。绑不上（件面在 plan 后漂移）→器红 rc2 fail-loud。
```

### apply_one（L1283-1283）

```
单洗落刀（按 plan 判面分发·正典序由调用方保证）。
```

### verdict_of（L1301-1302）

```
verdict：任一项级无式（洗级 plan-miss 或 _n_miss>0）→plan-miss；
        余 would-fix→partial；apply 模式有施→shaped；否则 clean。
```

### dump_report（L1341-1342）

```
确定性 JSON 落盘（sort_keys＋indent=1·与 registry_union.dump_json
        同律·原子写）。
```

### one_pass（L1360-1362）

```
一段完整流水：plan（--loop 走跨轮缓存·源件 md5 恒同命中复用/任一
        变重算；--once 直算不走缓存）→(--apply? 落刀→复跑五洗复核——rescan
        恒直算不复用缓存)→(verdict, report, n_applied)。
```

### _emit_event（L1392-1393）

```
事件出账（stdout 镜像＋--events 追加·sort_keys 规范式一行·逐行
        flush+fsync 承 cw_sentinel.emit_event 同律）。写败 → 9。
```

### run_loop（L1409-1412）

```
哨态：逐轮 one_pass（plan 跨轮缓存·源件 md5 变→重算）·JSONL 事件
        流同形对齐（rocqwash-sentinel-event/1·schema/seq/kind·sort_keys 规范
        式·seq 以 --events 现有行数为基跨进程续号·ts 承 --sleep-scale 0 关）·
        --events 追加落账·--max-rounds 界定（0=无限·到帽出 stop 事件）。
```

### _w（L1485-1486）

```
洗目条目：外显四键（kind/action/status/detail·schema 面）＋内部
        统计键（_ 前缀·落盘投影时剥除）。
```

### project_entry（L1506-1506）

```
洗目条目→schema 面四键（_ 内部键剥除）。
```

### stats_of（L1519-1520）

```
plan 统计：files/wash_entries/would_fix/clean/plan_miss（洗级）/
    plan_miss_items（项级）。
```

### exit_code_of（L1539-1539）

```
退出码口径：0=clean/shaped·1=partial/plan-miss。
```

### parse_only（L1544-1545）

```
--only 解析：逗号/空分·序号 1-5 与 kind 名双收·未知即用法炸·出参保
    正典序。
```

### selftest（L1565-1594）

```
内嵌冻结向量组（tmp 夹具·零真网络零真编译·真引擎离线驱动）：

    判1  plan 五洗逐判（脏件：词面 would-fix/token clean/header clean/
         eol would-fix/anchor 不适用）→partial rc1
    判2  正件对照全 clean→clean rc0
    判3  plan 零写盘·--apply 缺省关（md5 恒同）
    判4  plan-miss 如实（无式词面件→plan-miss；混合件→would-fix 修可修·
         plan-miss 亮无式）
    判5  apply→rescan clean→shaped rc0（词面交换/CRLF 归一/锚正典 md5_8 实证）
    判6  幂等（二跑 plan 全 clean→clean rc0；再 apply 零 applied）
    判7  锚缺实体 plan-miss
    判8  冻结名排除（injector 罐装名册：--dir 自动排除＋显式 --file 红拒 rc2；
         真 frozen8 --ledger 八件＋真在册件红拒）
    判9  子进程调用层注入（gate4 罐装判面）
    判10 CLI 四码（help0/bogus2/无输入面2/缺件9）
    判11 --once/--loop 双模（loop --max-rounds 2 事件流两轮＋stop）
    判12 确定性（plan --json 两跑字节恒同）
    判13 preset 链（--header-map-preset 装载在位·齐件不扰 rc0；探测次序：
         preset 胜 env·--header-map 胜 env——env ROCWASH_HEADER_MAP 双向）
    判14 preset 占位替换渲染→apply 端到端（缺字段件渲染整体补写→rescan
         clean→shaped rc0→二跑幂等 clean·渲染文逐名断言［name/deps 双列/
         bundle/build 命令/Axioms 豁免面］）
    判15 同槽互斥（--header-map＋--header-map-preset rc2；preset 未知名 rc2）
    判16 无源 plan-miss 如实（无旗无 env→缺字段件 header plan-miss）＋
         模板库缺失 rc9（--repo-root 隔离场·引擎件 symlink 七路）
    判17 --loop 事件流同形对齐（rocqwash-sentinel-event/1·--events 落盘逐行
         sort_keys 范式·seq 跨进程续号不重号·kind round/stop·ts=off 注记）
    判18 plan 缓存失效语义（a 范围件 md5 变→重算 miss/恒同→hit 复用
         [F,F,T]；b ⑤锚实体件 md5 变亦源变 [F,F,F,T]——实体域缺位即假 hit）
    
```

## 字符串常量（逐字·按行序）

```
L3: 'wash_shape.py — 洗形器·正典形五洗流水（rocqwash tools/·v37 三器共同接口·20261111）\n\n正典形五洗（逐文件依序执行·各洗可 --only 选·判例出处逐洗标注）：\n  ①词面洗 lexical   subprocess verify/gate4_comment_guard.py --file（五检项 v2.1\n                    EXT·rc 0/1/2 分流承 tools/pushci.py gate4_prescan 先例）→\n                    FAIL 项（hard 词面项）与 review 语境双义项对 wash/comment_pack.json\n                    flag_words 查正典同义改写式（sidecar 自述 trigger＝「gate4\n                    comment-guard review findings」；flag_word_note＝「Context-biaised\n                    review words exchange to their neutral English term」——语境双义\n                    复核项正是该包的交换靶面）。落刀＝wash/comment_sweep.py --apply\n                    （comment_pack 消费器·嵌套注释/字符串感知状态机·代码行相等断言）。\n                    无对应式→plan-miss（不硬造——comment_pack「never synthesized」\n                    同律）。\n  ②token 洗 token   scan/scan_v4_token.py --file 普查（token 级·W5 mixed-line 盲区\n                    闭合）→wash/cure_applier.py 正典包（cure_pack v1.3）干跑（该器\n                    缺省 dry-run）→--apply 落刀（二遍零残断言内建·rc 1 不落盘）。\n                    有站无式→plan-miss；排他组冲突（rc 4）→plan-miss 须人工 --only\n                    择一（cure_applier variant-choice 纪律）。\n  ③头注形洗 header  两段式＋五字段缺检（gate4 即含：无头注/头注非首块/缺字段/头注\n                    超标）→缺失字段方案＝comment_pack 式补写模板（--header-map 逐件\n                    数据·comment_sweep --header-map 前导注释区整体替换·内容绝不\n                    合成）；或 --header-map-preset 钦名模板（tests/fixtures/\n                    header_map_v1.json 蒸馏库·schema rocqwash-header-map/1·占位\n                    {name}/{deps_stdlib}/{deps_dev} 承目标件 Require 面与件名派生·\n                    {bundle}/{summary}/{mission} 承既有头注逐字携带——任一绑不上\n                    plan-miss 不硬造·渲染后仍经 comment_sweep --header-map 落刀）；\n                    无模板→plan-miss 不硬造。模板源探测次序：--header-map >\n                    --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径）>\n                    无＝plan-miss 如实；--header-map 与 --header-map-preset 显传\n                    互斥（同槽律 rc 2）。preset 源仅对 gate4 头注域硬项施刀·五字段\n                    齐件不对齐改写（防人工 curated 面被机械卷改写·诚实账）。\n  ④行尾洗 eol       CRLF→LF 归一（保末行换行形态；3KB 探测窗承 tools/\n                    registry_union.py detect_eol EOL_PROBE_BYTES 形制）。前洗引擎\n                    universal-newline 写回会附带归一——本洗 apply 以现盘实测为准·\n                    零改如实出账。\n  ⑤锚形洗 anchor    order.txt 行锚→registry_union.py --reanchor 正典形\n                    （#R<序>-<md5 前 8 hex>·20261110 判例：顺序号形锚与跨批撞锚\n                    皆此治愈；--reanchor 与 --anchor-src 成对·--apply 必配 --out\n                    ——经临时稿 os.replace 回位）。coqproject 行无锚→不适用。\n                    缺实体/实体歧义/行无锚→plan-miss（registry_union「缺件如实列\n                    跳过」同律）。\n\n两段制：plan（零写盘·逐文件逐洗 {kind,action,status:would-fix|clean|plan-miss,\ndetail} 清单＋统计）→--apply（执行 would-fix 项→**复跑五洗复核**→全净才 verdict\nshaped；复跑不净＝verdict partial·如实列残项）。verdict：clean｜shaped｜partial｜\nplan-miss（任一无对应式项在册即 plan-miss——非器力所能及·如实亮账）。\n\n范围与禁触面：--file 多值／--dir 全树（.v＋order.txt/_CoqProject·.v `_*` 下划线\n守卫承 gate4 scan_tree v2.1 同律）；certify/frozen8.py 在册八件自动排除（--ledger\n账载常量·离线可用）·显式指认冻结件＝红拒命中 exit 2（禁触铁律）；更新账.md 同为\n禁触面自动排除。\n\n接口纪律（v37 三器共同）：JSON-in/JSON-out（--json report·schema rocqwash-shape/1·\nsort_keys 确定性·无时间戳·同输入重跑字节恒同）；退出码 0=clean/shaped·1=partial/\nplan-miss（洗未尽·响亮出账）·2=用法/断言（冻结件红拒·引擎形外退出·JSON 畸形）·\n9=缺；--once/--loop 双模（--loop 实时哨态·--interval 可调·--max-rounds 界定·\n--apply 可与 loop 并用逐轮落刀）；离线可测（--injector 子进程\n调用层罐装 {rc,stdout,report}·--sleep-scale 缩睡·--selftest 全矢量零真网络零真\n编译）；编排而非重造（五洗引擎全 subprocess 调用·先读各器 CLI 与 JSON schema 再\n编排）。\n\n--loop 事件流（同形对齐·承 cw_sentinel 事件形——三器共同事件解析面）：\n  JSONL 逐行 schema=rocqwash-sentinel-event/1·键 sort_keys 规范式·seq 事件流\n  内单调（--events 在位以现有行数为基跨进程续号·缺省进程内从 1）·kind∈\n  {round,stop}·ts 由 time 钟出（--sleep-scale 0 时关 ts·note「ts=off」注记\n  ——确定性同哨）；stdout 镜像恒流＋--events 追加落账（逐行 flush+fsync）。\n  round 事件携 round/apply/verdict/五洗计数/n_applied/plan_cache_hit；\n  stop 事件携 round/reason=max-rounds/verdict。\nplan 缓存失效语义（--loop 跨轮·源件 md5 变→plan 重算）：失效域＝范围件\n  （--file/--dir 收件）∪⑤锚实体件（order.txt 行锚实体·anchor_src 解析——\n  实体 md5 变/实体出现消失/歧义化亦域变）的 {abspath: md5} 集；逐轮重测域\n  （廉价 md5·引擎零重跑）：域恒同→复用上轮 plan（缓存命中·命中轮五洗引擎\n  零重判）；任一源件 md5 变→失效重算并刷新域。首轮必重算；--once 单段不走\n  缓存；rescan 恒直算（落刀后新鲜盘面·不复用）。响亮出账＝report["plan_cache"]\n  {hit}（仅 loop 模式在账）＋round 事件 plan_cache_hit。\n\n用法（全部路径参数化·零硬编码绝对路径）：\n  python3 tools/wash_shape.py --file A.v [--file B.v ...] [--json OUT]   # plan 段\n  python3 tools/wash_shape.py --dir TREE [--exclude 名 ...] [--only 1,3]\n  python3 tools/wash_shape.py --file A.v --apply [--header-map M.json]       [--header-map-preset NAME] [--anchor-src DIR] [--json OUT]         # 两段全施\n  python3 tools/wash_shape.py --dir TREE --loop [--interval 5]       [--max-rounds 0] [--events FILE] [--apply]                         # 哨态\n  python3 tools/wash_shape.py --selftest\n\n退出码：0=clean/shaped；1=partial/plan-miss（洗未尽·响亮出账）；2=用法错/断言炸\n（冻结件红拒/引擎形外退出/JSON 畸形/--header-map 与 --header-map-preset 同槽\n互斥）；9=路径缺失（--file/--dir/引擎件/--header-map/--header-map-preset 模板库/\nenv ROCWASH_HEADER_MAP/--injector/--events 出账写败）。schema=rocqwash-shape/1。\n'
L134: '头注超标'
L134: '头注非首块'
L134: '无头注'
L134: '缺字段'
L135: '语境双义复核'
L142: '更新账.md'
L146: 'wash/comment_sweep.py --header-map <preset 渲染> --apply'
L173: '用法错/断言炸（exit 2：冻结件红拒·引擎形外退出·JSON 畸形）。'
L177: '路径缺失（exit 9）。'
L189: 'time.sleep(sec*scale)·scale=0 零真睡（selftest 矢量依赖·承 pushci 同款）。'
L194: 'UTC ISO8601 秒精度 Z 形（事件 ts 字段·承 cw_sentinel.now_iso 同形）。'
L200: '--loop 事件组装（同形承 cw_sentinel.make_event）：schema/seq/kind 头＋\n    fields；ts 由 time 钟出·ts_enabled=False（--sleep-scale 0）时关 ts 并以\n    note「ts=off」注记（确定性·fields 自带 note 时并入不打架）。'
L208: 'ts=off（--sleep-scale 0·确定性输出）'
L215: '--events 现有非空行数（seq 跨进程续基·承 cw_sentinel emit_seq_base\n    同律——追加流以现有行数为基续号）。读败 → 9。'
L221: '--events 读基失败: %s (%s)'
L225: '首个代码字符偏移（深度 0·非空白·注释/字符串感知）——前导头注区边界。\n    1:1 本地重实现 wash/comment_sweep.py first_code_offset 形制（不 import——\n    防引擎件漂移牵连·wash_engine.py 本地重实现同律）。'
L268: 'anchor_src 下（os.walk 递归）取同名 .v 实体。0 命中→None；多处→歧义串。\n    1:1 承 registry_union.resolve_entity 形制。'
L284: '实件 md5 前 8 hex（锚正典指纹源·承 registry_union.md5_8_of）。'
L294: '注释域剥离（留换行·字符串感知）——Require 面抽取前置。\n    1:1 本地重实现 wash/comment_sweep.py strip_comments 形制（不 import——\n    防引擎件漂移牵连·first_code_offset 本地重实现同律）。'
L341: '贪心词卷（>width 且含空格才卷·续行缩 6·超长孤词整词保留）——preset\n    渲染卷行形制（战役件卷行宽≈76 续行缩 6·DecBridge6.v:19-29 形制引据）。'
L358: 'Require 面双列抽取（③头注形洗 preset 占位 {deps_stdlib}/{deps_dev}\n    数据源·目标件自身语句逐名·绝不合成）。注释感知剥离（strip_comment_spans）\n    后仅取列 0 起顶层语句行：\n      From Stdlib Require [Import|Export] A B.  → stdlib 列\n      Require [Import|Export] A B.              → dev 列\n      From <X> Require [Import|Export] A B.     → dev 列（全名 X.A——战役语料\n        五件 grep 零命中·机械完备臂）。\n    序＝件内出现序·去重保序。语料引据：ConstructiveWorld-Set @6e805d1\n    LW3Kills.v:30-38（From Stdlib 三行＋bare 六行）对照其头注 :13-17 双列；\n    abl_tail_supply_67.v:32-35 对照 :15-16。'
L393: '既有前导头注区逐字携带抽取（preset 占位 {bundle}/{summary}/{mission}\n    绑定源）。返回 dict——缺键即该占位绑不上（judge plan-miss 如实·不硬造）：\n      bundle＝L1『(* ConstructiveWorld-Set -- <身>. *)』内文（终句号归模板行）；\n      summary＝『(** * <名>: <身>.』题行内文（终句号归模板行）；\n      mission＝Mission 字段身（标签行余文＋续行至次字段标签/收注符·换行缩进\n      原样逐字携带）。\n    语料引据：ConstructiveWorld-Set @6e805d1 DecBridge6.v:1/:3/:5-14 三身\n    正典位；头注身内容绝不合成（comment_pack header_spec 同律）。'
L436: '--injector 场景：子进程调用层罐装（v37 离线可测纪律）。场景 JSON\n    {引擎键: {"rc": int, "stdout": str, "report": obj?}}；命中键的引擎调用\n    恒定返付 canned（逐调用同响应）·不真 subprocess。键集＝gate4/scan_v4/\n    cure/sweep/registry_union/frozen8。'
L445: 'injector 场景缺失: %s'
L450: 'injector 场景 JSON 畸形: %s (%s)'
L452: 'injector 场景须 dict: %s'
L455: 'injector 场景键不识（须 %s）: %s'
L464: 'injector 罐装项须 dict: %s'
L469: '洗形器主体：收件→逐洗判（plan）→逐洗施（apply）→复跑复核。'
L498: '引擎件缺失（%s）: %s'
L500: '--anchor-src 目录缺失: %s'
L524: '③头注模板源探测（缺省探测路径次序）：--header-map >\n        --header-map-preset > env ROCWASH_HEADER_MAP（map 文件路径·与\n        --header-map 同构）> 无＝plan-miss 如实（judge_header 缺省臂）。\n        --header-map 与 --header-map-preset 同槽互斥 rc2（main 前置）。'
L548: 'comment_pack.json flag_words（正典同义改写式·数据驱动不硬造）。'
L553: 'comment_pack JSON 畸形: %s (%s)'
L557: 'comment_pack 缺 flag_words 表: %s'
L562: '头注 map 装载（comment_pack 式补写模板·逐件数据·{basename: text}）。\n        缺失＝9·畸形＝2（label 标源：--header-map 或 env ROCWASH_HEADER_MAP）。'
L565: '%s 缺失: %s'
L570: '%s JSON 畸形: %s (%s)'
L572: '%s 须 {basename: header text}: %s'
L576: '钦名模板装载＋fail-loud 形检（schema rocqwash-header-map/1）：库缺失\n        ＝9·JSON 畸形/schema 不识/preset 名不识/占位出白名单/variants 无 else\n        兜底/任一模板行缺 evidence 金标引据＝2（金标纪律机械化——无据不铸）。'
L581: '--header-map-preset 模板库缺失: %s'
L586: '模板库 JSON 畸形: %s (%s)'
L588: '模板库 schema 不识（须 %s）: %s'
L592: '模板库缺 presets 表: %s'
L595: 'preset 名不识（库 %s 在册: %s）: %s'
L600: '模板库缺 placeholders 白名单: %s'
L602: 'preset %r 缺金标 evidence（无据不铸）: %s'
L606: 'preset %r 缺 lines 模板行: %s'
L612: '占位出白名单（%s）: %s'
L616: '行式模板'
L620: 'variants 槽式模板形畸（须 {slot, variants}）: %s'
L625: 'variant 形畸（须 {when, line, evidence}）: %s'
L627: 'variants 式'
L630: 'variant 缺金标 evidence（无据不铸）: %s'
L639: 'when 键出白名单/非布尔: %s'
L642: "when 须 'else' 或非空 bool dict: %s"
L644: 'variants 无 else 兜底（渲染须全态可决）: %s'
L649: 'preset 渲染（③头注形洗·占位替换）：模板行逐行替换占位→超宽行贪心\n        卷（wrap_long_line）。占位值全部承目标件自身——{name}＝basename 去 .v·\n        {deps_stdlib}/{deps_dev}＝require_faces 双列·{bundle}/{summary}/\n        {mission}＝header_carry 既有头注逐字携带——绝不合成。任一占位绑不上→\n        (None, 缺位清单)（judge 记 plan-miss 如实）。缓存键＝(abspath, 文面\n        md5)（loop 逐轮重判·同件同文恒同·件变即重渲）。'
L699: '映射查得（basename 带/不带 .v 双试·承 comment_sweep.run 同款）。\n        仅 map 源（--header-map/env）——preset 源走 render_preset_header。'
L711: 'certify/frozen8.py --ledger → (abs 集, rel 集, 来源说明)。\n        --ledger 只打账载常量（离线·零盘验）·injector 可罐装。行式\n        「md5<空白>relpath」；绝对路径行按 abs 收·相对行对 repo_root 归位。'
L717: 'frozen8 --ledger 形外退出 rc=%d: %s'
L745: '铁律禁触面：冻结八件在册∪更新账.md。'
L752: '子进程调用层：injector 命中键→罐装恒定返付；否则真 subprocess\n        [sys.executable, -B, tool] + cli（stdout+stderr 合流·承 pushci\n        _run_py 形制）。want_json→附 --json tmp·解析后即删。返回\n        (rc, stdout, report|None, canned_flag)。'
L762: '引擎件缺失: %s'
L794: '--file 显式（存在性 9·禁触面红拒 2）＋ --dir 全树（.v 非 _·registry\n        两名·隐目录跳过·禁触面与 --exclude 自动排除）。去重按 abspath·序按\n        构造路径字符串（确定性）。返回 (files, excluded 记录)。'
L810: '--file 缺失: %s'
L812: 'FATAL 冻结件红拒: %s（certify/frozen8.py 在册/更新账·禁触铁律——洗形器拒不执行）'
L817: '--dir 缺失: %s'
L825: '更新账'
L853: 'gate4 单件报告（rc 0/1/2 正常·形外/JSON 畸形→器红 exit 2）。'
L857: 'gate4 形外退出 rc=%d: %s'
L859: 'gate4 JSON 出账缺失/畸形: %s'
L863: '①词面洗：gate4 hard 词面项＋review 语境双义项→flag_words 查式。'
L869: 'gate4 UNREADABLE（面不可读·无式可施）'
L884: '双义:%s→%s'
L886: '双义:%s（无对应式）'
L887: 'gate4=%s hard=%d(词面项=%d) review=%d(双义=%d 人工域=%d) 可改写=%d 无式=%d'
L892: ' 可改写['
L894: ' 无式['
L901: '②token 洗：scan_v4 普查→cure_applier 正典包干跑。'
L905: 'scan_v4 形外退出 rc=%d: %s'
L907: 'scan_v4 census JSON 缺失/畸形: %s'
L912: 'census 站=0（tracked=%s）'
L919: 'census 站=%d·正典包排他组冲突（两变体皆中·须人工 --only 择一）: %s'
L922: 'cure_applier 干跑形外退出 rc=%d: %s'
L928: 'census 站=%d·正典包干跑命中=%d'
L931: 'census 站=%d·正典包零命中（无对应式）'
L935: '③头注形洗：gate4 头注域硬项＋模板判（map 源＝逐件数据·对齐判与\n        补写判并施；preset 源＝钦名模板渲染——仅对硬项施刀·五字段齐件不对齐\n        改写（防人工 curated 面被机械卷改写·诚实账）；无源＝plan-miss 如实）。'
L950: 'comment_pack 式模板整体补写'
L951: '钦名模板渲染整体补写'
L953: '头注项=%d[%s]·%s'
L960: '头注形与模板差（整体补写对齐）'
L962: '头注正典形（模板已在位）'
L964: '头注无项（首块·五字段齐·preset 不对齐改写）'
L968: 'preset 渲染绑不上占位[%s]（承件缺既有头注身）·不硬造: [%s]'
L974: '无补写模板（模板源=%s 未配/缺条目）·不硬造: [%s]'
L979: '头注无项（首块·五字段齐）'
L982: '④行尾洗：CRLF→LF 归一（末行换行形态保全）。'
L985: '无'
L985: '有'
L987: 'CRLF=0·LF 已归一（末行换行=%s）'
L989: '·lone_CR=%d（非 CRLF 口径·不改）'
L992: 'CRLF 行尾=%d（末行换行形态保全）'
L997: '⑤锚形洗：order.txt 行锚正典形判（#R<序>-<md5 前 8>）。'
L1002: '非 registry（order.txt/_CoqProject）·此洗不适用'
L1005: 'coqproject 行无锚（registry_union 口径）·不适用'
L1012: 'registry 非 UTF-8 面: %s'
L1027: '行无锚不可重锚（无序号可承）: %s'
L1034: '缺实体（%s 下无 %s.v）: %s'
L1038: '实体歧义（registry_union 拒锚）: %s'
L1047: 'order 锚判：非正典=%d 无式=%d'
L1052: ' 无式['
L1062: '单件逐洗判（正典序①→⑤·零写盘）。'
L1069: '件不可读: %s'
L1088: '非 .v 源·词面洗不适用'
L1089: '非 .v 源·token 洗不适用'
L1090: '非 .v 源·头注形洗不适用'
L1100: '全范围 plan（零写盘）→ {"files": [...], "stats": {...}}。'
L1107: 'plan 缓存失效域 {abspath: md5}：范围件（--file/--dir 收件）∪⑤锚\n        实体件（order.txt 行锚实体·anchor_src 解析——实体 md5 变亦源变）。\n        实体出现/消失/歧义化以记号键入域（域集变即失效）；件不可读记 None\n        （态变触发重算·fail-soft 域账）。逐轮重测此域＝廉价 md5（五洗引擎\n        零重跑）·域恒同→缓存命中。'
L1148: 'plan 跨轮缓存（--loop 哨态）：失效域（plan_scope_md5s）恒同→复用\n        上轮 plan（缓存命中·五洗引擎零重判）；任一源件 md5 变→失效重算并\n        刷新域（源件 md5 变→plan 重算·钦定语义）。首轮缓存空必重算。\n        返回 (plan, hit)。'
L1167: 'comment_sweep --apply 器红 rc=%d: %s'
L1173: '（injector 罐装）'
L1181: 'cure_applier --apply 器红 rc=%d（不落盘·二遍零残断言）: %s'
L1188: '（injector 罐装）'
L1192: '③落刀：comment_sweep --header-map <具体 map> --apply（引擎恒\n        comment_sweep·编排零新引擎）。map 源＝显传/env 路径；preset 源＝现渲\n        染单件 map 临时落盘（{basename: 渲染文}·用后即删——渲染值承件自身\n        数据·编排不落常盘）。绑不上（件面在 plan 后漂移）→器红 rc2 fail-loud。'
L1204: 'preset 渲染绑不上占位[%s]（apply 时件面漂移）: %s'
L1224: 'comment_sweep --header-map --apply 器红 rc=%d: %s'
L1232: '（injector 罐装）'
L1239: 'crlf_converted=0 changed=False（前洗已附带归一·如实）'
L1244: 'crlf_converted=%d changed=True（末行换行形态保全）'
L1261: 'registry_union --reanchor 器红 rc=%d（零写盘）: %s'
L1267: 'rewrites=%d（injector 罐装·未回位）'
L1283: '单洗落刀（按 plan 判面分发·正典序由调用方保证）。'
L1296: '洗 kind 不识: %s'
L1301: 'verdict：任一项级无式（洗级 plan-miss 或 _n_miss>0）→plan-miss；\n        余 would-fix→partial；apply 模式有施→shaped；否则 clean。'
L1341: '确定性 JSON 落盘（sort_keys＋indent=1·与 registry_union.dump_json\n        同律·原子写）。'
L1345: '--json 出路径目录缺失: %s'
L1360: '一段完整流水：plan（--loop 走跨轮缓存·源件 md5 恒同命中复用/任一\n        变重算；--once 直算不走缓存）→(--apply? 落刀→复跑五洗复核——rescan\n        恒直算不复用缓存)→(verdict, report, n_applied)。'
L1392: '事件出账（stdout 镜像＋--events 追加·sort_keys 规范式一行·逐行\n        flush+fsync 承 cw_sentinel.emit_event 同律）。写败 → 9。'
L1405: '--events 出账失败: %s (%s)'
L1409: '哨态：逐轮 one_pass（plan 跨轮缓存·源件 md5 变→重算）·JSONL 事件\n        流同形对齐（rocqwash-sentinel-event/1·schema/seq/kind·sort_keys 规范\n        式·seq 以 --events 现有行数为基跨进程续号·ts 承 --sleep-scale 0 关）·\n        --events 追加落账·--max-rounds 界定（0=无限·到帽出 stop 事件）。'
L1476: '  残项 %s %s %s %s'
L1485: '洗目条目：外显四键（kind/action/status/detail·schema 面）＋内部\n        统计键（_ 前缀·落盘投影时剥除）。'
L1506: '洗目条目→schema 面四键（_ 内部键剥除）。'
L1519: 'plan 统计：files/wash_entries/would_fix/clean/plan_miss（洗级）/\n    plan_miss_items（项级）。'
L1539: '退出码口径：0=clean/shaped·1=partial/plan-miss。'
L1544: '--only 解析：逗号/空分·序号 1-5 与 kind 名双收·未知即用法炸·出参保\n    正典序。'
L1554: '--only 项不识（须 %s 或 1-5）: %s'
L1558: '--only 列空: %r'
L1565: '内嵌冻结向量组（tmp 夹具·零真网络零真编译·真引擎离线驱动）：\n\n    判1  plan 五洗逐判（脏件：词面 would-fix/token clean/header clean/\n         eol would-fix/anchor 不适用）→partial rc1\n    判2  正件对照全 clean→clean rc0\n    判3  plan 零写盘·--apply 缺省关（md5 恒同）\n    判4  plan-miss 如实（无式词面件→plan-miss；混合件→would-fix 修可修·\n         plan-miss 亮无式）\n    判5  apply→rescan clean→shaped rc0（词面交换/CRLF 归一/锚正典 md5_8 实证）\n    判6  幂等（二跑 plan 全 clean→clean rc0；再 apply 零 applied）\n    判7  锚缺实体 plan-miss\n    判8  冻结名排除（injector 罐装名册：--dir 自动排除＋显式 --file 红拒 rc2；\n         真 frozen8 --ledger 八件＋真在册件红拒）\n    判9  子进程调用层注入（gate4 罐装判面）\n    判10 CLI 四码（help0/bogus2/无输入面2/缺件9）\n    判11 --once/--loop 双模（loop --max-rounds 2 事件流两轮＋stop）\n    判12 确定性（plan --json 两跑字节恒同）\n    判13 preset 链（--header-map-preset 装载在位·齐件不扰 rc0；探测次序：\n         preset 胜 env·--header-map 胜 env——env ROCWASH_HEADER_MAP 双向）\n    判14 preset 占位替换渲染→apply 端到端（缺字段件渲染整体补写→rescan\n         clean→shaped rc0→二跑幂等 clean·渲染文逐名断言［name/deps 双列/\n         bundle/build 命令/Axioms 豁免面］）\n    判15 同槽互斥（--header-map＋--header-map-preset rc2；preset 未知名 rc2）\n    判16 无源 plan-miss 如实（无旗无 env→缺字段件 header plan-miss）＋\n         模板库缺失 rc9（--repo-root 隔离场·引擎件 symlink 七路）\n    判17 --loop 事件流同形对齐（rocqwash-sentinel-event/1·--events 落盘逐行\n         sort_keys 范式·seq 跨进程续号不重号·kind round/stop·ts=off 注记）\n    判18 plan 缓存失效语义（a 范围件 md5 变→重算 miss/恒同→hit 复用\n         [F,F,T]；b ⑤锚实体件 md5 变亦源变 [F,F,F,T]——实体域缺位即假 hit）\n    '
L1622: '(* 使命：洗形器自测夹具。\n   依赖：无。\n   对标：无。\n   构造性：全闭合。\n   编译配方：rocq c -Q . "" fixture.v。 *)\n'
L1627: 'Definition a := 1. (* 这里埋一个载体词 *)\nDefinition b := 2.\n'
L1634: 'Definition c := 3. (* 这是一个探针词面 *)\n'
L1636: 'Definition d := 4. (* 载体一词与探针词面并存 *)\n'
L1691: '载体'
L1696: '不适用'
L1697: '判1 plan 五洗逐判(脏件 partial):'
L1707: '判2 正件对照全 clean:'
L1713: '判3 plan 零写盘(--apply 缺省关):'
L1718: '禁词:探针'
L1719: '无对应式'
L1726: '无式[禁词:探针]'
L1728: '判4 plan-miss 如实(无式件/混合件):'
L1745: '载体'
L1752: '判5 apply→rescan clean→shaped(词面/CRLF/锚实证):'
L1766: '判6 幂等(二跑 plan 全 clean/再 apply 零 applied):'
L1771: '缺实体'
L1772: '判7 锚缺实体 plan-miss:'
L1796: '红拒'
L1797: '红拒'
L1799: '判8 冻结名排除(罐装 --dir 排除/显式红拒 rc2/真在册红拒):'
L1807: '体内散块'
L1807: '探针'
L1807: '禁词'
L1812: '禁词:探针'
L1813: '判9 子进程调用层注入(gate4 罐装判面):'
L1823: '判10 CLI 四码(help0/bogus2/无输入面2/缺件9):'
L1849: '判11 --loop 哨态(max-rounds 2/事件流同形 schema+seq+kind):'
L1860: '判12 确定性(plan --json 两跑字节恒同):'
L1884: '钦名模板渲染整体补写'
L1885: '无补写模板（模板源=map'
L1886: '判13 preset 链(装载在位/齐件不扰/preset>--header-map 胜 env):'
L1897: '钦名模板渲染整体补写'
L1898: '缺字段'
L1921: '判14 preset 占位替换渲染→apply 端到端(partial→shaped→幂等/渲染逐名断言):'
L1930: '互斥'
L1931: '名不识'
L1932: '判15 同槽互斥(双旗 rc2/未知名 rc2):'
L1956: '无补写模板（模板源=none'
L1957: '模板库缺失'
L1958: '判16 无源 plan-miss 如实/模板库缺失 rc9:'
L1980: '判17 事件流同形对齐(--events 逐行范式/seq 跨进程续号):'
L2007: '判18a plan 缓存（范围件 md5 变→重算 miss/恒同→hit 复用）:'
L2037: '判18b plan 缓存（锚实体件 md5 变→重算 miss·序列 [F,F,F,T]）:'
L2042: 'PASS（18 判全过）'
L2057: '洗形器·正典形五洗流水（gate4 词面/token 普查+正典包/头注模板/行尾归一/registry 重锚·两段 plan→apply 复跑复核·schema rocqwash-shape/1）'
L2061: '目标件（可多次；.v 走①②③·order.txt/_CoqProject 走⑤·任意文本件走④）'
L2064: '全树收件（.v＋order.txt/_CoqProject·可多次）'
L2065: '名'
L2066: '追加排除名（ basename 或路径段·冻结名册在册自动排除）'
L2068: '洗目子集（逗号分·lexical,token,header,eol,anchor 或 1-5·缺省全五洗）'
L2072: '③头注形洗补写模板（{basename: header text}·逐件数据·与 --header-map-preset 同槽互斥 rc2）'
L2076: '③头注形洗钦名模板（tests/fixtures/header_map_v1.json 蒸馏库内 preset 名·占位承目标件自身派生/既有头注逐字携带·缺省探测次序 --header-map > 本参 > env ROCWASH_HEADER_MAP > 无=plan-miss）'
L2082: '⑤锚形洗实件源目录（缺省=registry 件同目录）'
L2085: '引擎件根（缺省=本脚本上上级·全参数化）'
L2087: 'report 出账（schema rocqwash-shape/1）'
L2089: '两段第二段：执行 would-fix 项＋复跑五洗复核（缺省 plan 零写盘）'
L2092: '哨态：逐轮流水＋JSONL 事件流（缺省 --once 单段）'
L2094: 'loop 轮间秒（缺省 5·可调）'
L2097: 'sleep 缩放（0=零真睡·selftest 依赖）'
L2099: 'loop 轮数界定（0=无限）'
L2101: 'loop JSONL 事件追加账（stdout 恒流·此参另落盘）'
L2103: '子进程调用层罐装场景 {引擎键: {rc,stdout,report}}（键集 gate4/scan_v4/cure/sweep/registry_union/frozen8）'
L2115: 'FAIL-LOUD: --file/--dir 至少给一（收件面）'
L2118: 'FAIL-LOUD: --interval/--sleep-scale/--max-rounds 须≥0'
L2122: 'FAIL-LOUD: --header-map 与 --header-map-preset 同槽互斥（rc2 同槽律——③头注模板源二择一显传）'
```
