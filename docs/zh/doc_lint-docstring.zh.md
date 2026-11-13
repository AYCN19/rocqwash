# tools/doc_lint.py 中文原面留档（archive）


- 源文件：`tools/doc_lint.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `tools/doc_lint.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 模块 docstring（逐字）

```
doc_lint.py — 文档←→实现一致性三查器（docs↔tools 对账·防文档漂移·rocqwash
tools/·v38 工装席任务书·20261111 入账）

三查（全部纯本地·零网络零编译·python3 纯 stdlib·编排零新引擎——解析规则逐条
锚在盘件现行行，不发明新形）：
  ①工具表查＝cw.sh 头注/usage/hint/case 四处工具清单互检＋与 tools/ 目录实有
    通用入口对账（路由缺/表多/表少逐条列）。四处＝头注工具表（cw.sh:10-50·name
    desc -> path·两行折行体 cw.sh:25-26 doctor 等同形）、usage() heredoc 工具表
    （cw.sh:83-124）、hint_for() 一行提示（cw.sh:133-153·echo 串尾缀 -> path）、
    case 分派（cw.sh:170-186·run_tool <name> "<rel>"）。互检＝有路由者四处俱在
    （缺一处即表少·逐器逐处列）＋四处路径逐器咬合（不符/缺 -> 路径即列）；
    对账＝case 路由目标缺盘即「表多（悬路由）」、tools/ 非 _ 前缀 .py（通用
    入口·定义锚 cli/rocqwash:9「模块目录下唯一一个不带前导下划线的 .py」）
    无 case 路由即「路由缺」。help 为伪路由不参赛（cw.sh:49 头注行＋
    cw.sh:187 help|-h|--help 特例分派·hint_for 无分支——四处本就不对称）。
  ②计数查＝tests/run_tests.sh CASES 数（run_tests.sh:140-192 静态在册例·
    t_fail_probe 为 FAIL_PROBE 自检注入例不计·run_tests.sh:194-197）vs
    tests/README.md 计数行（:12「预期 52 过」＋:15「## 覆盖面（52 例）」）vs
    README.md 例数行（:59「自测套件（52 例）— test suite (52 cases)」）——
    数值三处一致·漂移即列；计数行形未现＝计数行缺失亦列。README.md:83/92/
    101/112/123/139/156「扩至 N 例」等增补史行为版本化历史非现势计数（逐轮
    累进属设计内·v38 轮 cw.sh:2「共十六」同款史行）·不在对账面——只锚上述
    四形，宁缺毋滥不造新计数形。
  ③旗标查＝README-cw.md/README.md/examples/workflows/*.md/docs/*.md（docs/
    递归·*.zh.md 与 docs/zh/ 归档面免扫——注释规范卡 §5.2 归档件非正本面）
    中引用的器旗标（--xxx 形）逐枚对照各器 --help 实出输出
    （subprocess 真跑 --help·rc!=0/超时=器红 fail-loud 9·帽 --help-cap 25 器）。
    器集＝cw.sh 路由 ∪ tools/ 非 _ 前缀 .py＝25 器（现势·帽 25 有余）；
    超帽按典序截断·溢出器如实列「未实跑 --help·引用 N 处未证」。归账规则＝
    器引用两级（一级强引用＝盘路径形/cli/rocqwash/cw.sh 路由形·二级弱引用＝
    裸名形——路由名/器 stem/在盘 oos 器 stem），旗标归其逻辑行最近前驱一级
    引用·无则二级（README.md:232「cli/rocqwash certify push_gate union-freeze
    --world…」内 union-freeze 裸名 union 不得咬走 primary 的实证律）；旗标
    token 先掩码再找器引用（防 --probe-resume 内 probe 误吞）。池兜底三
    路：散文段＝空行/围栏/标题界整段引用两遍收集（段首旗标如 README-cw.md:77
    「① --once/--loop 双模」实证）；代码围栏命令行＝反斜杠续行拼行后严格
    只在命令自身内归账（幻引判定最强面）；代码围栏注释行＝块池归账
    （step-pushci.md:75-77「# 可选追加：--pre-scan-gate4／--merge…」实形）。漂移两向＝
    缺旗标（幻引/多余引用·同面两词：doc 侧引用为多余·器侧实出缺此旗标——
    primary 器 help 实出无＋池内 registry 器全缺＋池内无可证 oos/unknown 器；
    「同一旗标 token 重复≥2 即多余」的机械判据被 README.md:232 union-freeze
    --world wa=… --world wb=… 合法多值实证否弃·不采）＋悬引（primary 引用
    不识——cw.sh 非路由/路由目标缺盘而旗标无器可证；cw.sh bogus 等退出码
    示例行无旗标故不误咬）。无主旗标与池含 oos/unknown 器者＝unresolved
    如实计不判漂（不可证≠漂——docs/zh/architecture.md:54 台账行「--json/
    --hits-csv」属 scan 阶段件 mac_stmt_scan、上下文在文档节层·机检不可归账
    不作漂判的实证律）。cli/rocqwash 及 registry 外器（certify/watch/wrapper/
    战役件等）旗标非本查对象——计入 out_of_scope 如实出账（cli/rocqwash 为
    v29 前路由层·旗标属子工具·cli/rocqwash:8-11 路由契约）。
    argparse 折行复原：break_on_hyphens 断词实出「--on-red-<LF>arg」（cw_sentinel
    --help 实证）——(--tok)-
<ws>(cont) 复原后再取 token；registry_union --help:14
    「--ref-*」词面为 glob 散文·截断 token 属噪音不害幻引判定（本查只单向
    doc→help：help 散文多收旗标仅致漏报不致误报——精度换零误报·宁缺毋滥）。

输出：--json report schema=rocqwash-doclint/1（checks[{kind,target,status,
detail}]·verdict consistent|drift·counts·out_of_scope·registry·args·sort_keys
落盘·无墙钟字段·路径一律仓相对——同输入重跑字节恒同）。checks 逐条列：
kind∈{tool_table,count,flag}·status∈{ok,drift}·detail 单行（截 300 字符）。

退出码：0=consistent（三查零漂）；1=drift（任一条 drift·红是数据非器红·
响亮 stdout）；2=用法错（argparse/--help-cap<1）；9=缺（--repo 缺目录/被审
仓必需输入缺失：cw.sh·README.md·README-cw.md·tests/run_tests.sh·
tests/README.md·docs/·examples/workflows/·--json 父目录缺·器 --help 器红/
超时·doc 件不可解码）。

本器一次性静态对账·无巡检环——--once/--loop 无涉（cw_doctor 同例）；子进程
仅本地 --help 真跑（毫秒级·零网络零编译零睡）——--injector/--sleep-scale 无涉
·离线天然可测（--selftest 全 tmp 迷你仓夹具）。

--selftest 矢量（tmp 迷你仓 fixture·四判＋CLI 三码＋幂等一判）：
  V1 一致迷你仓（2 路由四处齐·计数 2 三处一致·旗标实引全证）→ rc0·verdict
     consistent·checks 零 drift。
  V2 工具表缺一（hint_for 摘 b 行）→ rc1·tool_table drift 指向 cw.sh:hint。
  V3 计数漂（tests/README.md 覆盖面改 3）→ rc1·count drift 数值 3≠2。
  V4 旗标幻引（docs/note.md 增 --bogus-flag 引用）→ rc1·flag drift 幻引。
  V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9）＋--help-cap 0→2。
  V6 JSON 幂等（同仓两跑异 --json 路径字节恒同——report 不嵌 json 路径）。

用法（全部路径参数化·零硬编码）：
  python3 tools/doc_lint.py [--repo DIR] [--json OUT] [--help-cap N]
  python3 tools/doc_lint.py --selftest

```

## 注释（逐字·按行序）

```
L98: # ③ --help 真跑器帽（v38 波 20→24 换代·v46 时点 23 器有余——集成席登记帽溢出 cure_applier/probe_engine 后主会话裁决换代·注释面规范化波 tools/norm_lint.py 入册后 25 器——帽溢出 wash/probe_engine.py 同 precedent 换代 24→25）— tools/registry_regen.py registered as the 26th tool: cap raised 25->26, same precedent as the 24->25 bump at the norm-lint registration — tools/contrib_intake.py registered as the 27th tool: cap raised 26->27, same precedent (registry_rel sorted order again puts wash/probe_engine.py last; its doc-flag references need the real --help run to stay phantom-free) — tools/evolve.py registered as the 28th tool: cap raised 27->28, same precedent (registry_rel sorted order again puts wash/probe_engine.py last)
L99: # --help 子进程秒帽（本地件防挂·fail-loud）
L100: # checks[].detail 截断（cw_doctor non_form ln[:120] 同款）
L101: # ③ 每文件幻引/悬引列帽（总数如实·cw_doctor 帽 20 同款）
L102: # out_of_scope/registry 溢出清单帽（总数如实）
L104: # 伪路由（cw.sh:49 头注行·cw.sh:187 特例分派）
L106: # 仓级通用器旗标（不入幻引判定）：--help 恒有；--selftest 承套件纪律——
L107: # run_tests.sh 在册各器例全数真跑 --selftest（t_scan_selftest:t_cw_doctor
L108: # 十二器直跑＋t_cw_sentinel/t_wash_shape/t_unclog 同），部分器以 pre-argparse
L109: # 形处理（cw_doctor.py:1014 `if "--selftest" in argv` 先于 argparse 同款）
L110: # 致 --help 输出不列——按 help 缺失判幻引即误报，故恒认。
L115: # ---- ① cw.sh 四处解析正则（1:1 锚 cw.sh 现行行·见 docstring 引据）----
L126: # ---- ② 计数行形（1:1 锚 tests/README.md:12/:15·README.md:59 现行行）----
L136: # ---- ③ doc 扫描正则 ----
L138: # argparse break_on_hyphens 折行复原：(--tok)-\n<ws>(cont) → --tok-cont
L161: # ---- 小件（确定性 helpers·cw_doctor 同款本地副本·无包结构不互 import）----
L193: # ---- ① 工具表查 ----------------------------------------------------------------
L292: # 四处互检：有路由者四处俱在（表少/悬名逐器逐处列）
L306: # 路径逐器咬合（case 路径为正·他处缺失/不符即列）
L327: # 对账：case 路由目标缺盘＝表多（悬路由）
L338: # 对账：tools/ 非 _ 前缀 .py 无 case 路由＝路由缺（cli/rocqwash:9 定义）
L363: # ---- ② 计数查 -----------------------------------------------------------------
L376: # bash 引号串内反斜杠续行（run_tests.sh:140 `CASES="\`＋逐行尾 `\`）还原
L377: # 成空白后再取 token——字面 `\` 不是用例名
L413: # ---- ③ 旗标查 -----------------------------------------------------------------
L448: # 在盘 oos 器 stem（模块目录非 _ 前缀 .py＋tools/*.sh·registry 除外）——
L449: # 令「wash_engine.py」等裸件名引用可归账为 oos（不可证但可归·非无主）
L534: # 注释规范卡 §5.2：归档件非正本面——*.zh.md 同目录留档形与
L535: # docs/zh/ 追认形为冻结历史存档（声明不随代码演进维护），
L536: # 对活实现的一致性查在其上无意义，免扫
L565: # 散文段缓冲 [(line_no, seg)]
L566: # 代码块逻辑行缓冲 [(line_no, joined)]
L567: # 代码续行拼装缓冲 [(line_no, seg)]
L719: # 散文：标题行独立成段（防池跨节泄漏）·空行收段
L787: # ---- 总控 ---------------------------------------------------------------------
L803: # ①工具表查
L811: # ②计数查
L815: # ③旗标查
L863: # ---- --selftest（tmp 迷你仓 fixture·四判＋CLI 三码＋幂等一判）-------------------
L1040: # ---- V1 一致迷你仓 0 漂 ----
L1056: # 引用旗标确已逐枚对账：a 器 --file/--json＋b 器 --dir/--apply
L1061: # 无器上下文旗标引用＝unresolved 如实计·不判漂（V1 仍 consistent）
L1066: # ---- V2 工具表缺一（hint 摘 b）----
L1080: # ---- V3 计数漂（覆盖面 3≠2）----
L1091: # 其余两查仍零漂（漂移只在计数域·不连带）
L1095: # ---- V4 旗标幻引（docs/note.md --bogus-flag）----
L1107: # 其余两查仍零漂
L1111: # ---- V5 CLI 三码＋--help-cap 值校验 ----
L1121: # ---- V6 JSON 幂等：同仓两跑异 --json 路径字节恒同 ----
```

## 函数级 docstring（逐字）

### UsageError（L150-150）

```
用法错/值校验败（exit 2）。
```

### MissingInput（L154-154）

```
输入缺失（exit 9）。
```

### ToolError（L158-158）

```
器红/--help 失败（exit 9·fail-loud 禁静默降级）。
```

### rel_of（L180-180）

```
仓相对路径（确定性·报告零绝对路径纪律）。
```

### parse_table_rows（L196-199）

```
表体行 → {name: {"path": str|None, "line": int}}（仅认路由名形
    ^[a-z0-9][a-z0-9-]*$·三体：单行 name desc -> path／续行 -> path／折行
    pending name 待续行赋 path·cw.sh:25-26 doctor 折行体 1:1）。
    路由契约/退出码等段界行截停（TABLE_STOP_RE）。
```

### parse_cw_sh（L234-237）

```
cw.sh 四处清单解析 → {place: {name: {"path", "line"}}}。
    区域界锚：头注至首个 set -u（cw.sh:73）；usage 至首 EOF（heredoc 终）；
    hint_for 至首个列 0 }；case 至 EOF（case "${1:-}" in 唯一分派 case·
    hint_for 内 case "$1" in 不误咬）。
```

### check_tool_table（L289-289）

```
①四处互检＋tools/ 通用入口对账 → checks 列表（逐条·kind=tool_table）。
```

### check_counts（L366-366）

```
②CASES 数 vs tests/README.md 计数行 vs README.md 例数行 → checks。
```

### run_help_flags（L416-416）

```
subprocess 真跑 --help → 实出旗标集（含折行复原）。rc!=0/超时=器红 9。
```

### LintCtx（L434-438）

```
③扫描上下文：器集映射＋help 实出集＋账面。
    器引用两级：一级强引用（盘路径形/cli/rocqwash/cw.sh 路由形）·二级弱引用
    （裸名形——路由名/器 stem/在盘 oos 器 stem）。primary 取行内最近前驱一级
    引用·无则二级（防 README.md:232「cli/rocqwash certify push_gate
    union-freeze --world…」内 union-freeze 的裸名 union 咬走 primary）。
```

### load_helps（L484-485）

```
逐器真跑 --help（典序·帽内）→ help 集（并集仓级通用旗标——
        UNIVERSAL_FLAGS 注）。
```

### doc_files（L518-518）

```
③ 对账面文件序（README 系→examples/workflows/*.md→docs/ 递归·典序）。
```

### scan_doc（L544-557）

```
单文件 ③ 扫描 → (item, drift_n, refs_n)。
    三路归账：①散文段＝空行/围栏/标题界的整段两遍处理（一遍收全段引用池·
    二遍逐行归账——段首旗标如 README-cw.md:77「① --once/--loop 双模」前驱
    无器引用，段池兜底）；②代码围栏命令行＝反斜杠续行拼行后逐命令严格归账
    （池＝命令自身引用·幻引判定最强面）；③代码围栏注释行（step-pushci.md:75-77
    「# 可选追加：--pre-scan-gate4…」实形）＝块池归账（全块引用两遍收集）。
    引用两级：一级（路径/cli/路由）＞二级（裸名）——primary 取最近前驱一级·
    无则二级。漂移两向：缺旗标（幻引/多余引用——primary 器 help 实出无此
    旗标＋池内 registry 器全缺＋池内无可证 oos/unknown 器）；悬引（primary
    引用不识——cw.sh 非路由/路由目标缺盘）。无主旗标与池含 oos/unknown 者
    ＝unresolved 如实计（不可证≠漂——zh/en architecture 台账行「--json/
    --hits-csv」属 scan 阶段件 mac_stmt_scan 实证：上下文在文档节层·机检
    不可归账不作漂判）。旗标 token 先掩码再找器引用（防 --probe-resume 内
    \bprobe\b 误吞）。
```

### mentions_of（L571-573）

```
→ (mentions 有序[(pos, tier, (kind,key))], flag_hits[(pos,tok)])。
        tier 1＝路径/cli/路由强引用·2＝裸名弱引用。旗标 token 先掩码（同长
        空格·位置不漂）再找器引用。
```

### account（L593-594）

```
单逻辑行归账 → (drifts, refs, unresolved)。primary＝行内最近前驱
        一级引用·无则二级；pool＝兜底池（kind-tagged·tool/oos/unknown）。
```

### flush_code_block（L637-638）

```
代码块两遍：一遍收全块引用池（注释行用）·二遍逐逻辑行归账
        （命令行严格自身池·注释行块池）。
```

### flush_para（L662-662）

```
散文段两遍：一遍收全段引用池·二遍逐行归账（段池兜底）。
```

### flush_join（L683-683）

```
续行拼装收口 → 逻辑行入代码块缓冲。
```

### check_flags（L752-752）

```
③旗标查总控：help 真跑→逐件扫描→checks（每文件一项＋溢出器未证项）。
```

### _refs_for（L773-773）

```
溢出器在 doc 面的引用计数（重扫轻量：仅器引用不跑旗标判定）。
```

### run（L790-790）

```
总控：值校验（2）→被审仓先验（9）→①②③逐查→report（0/1）。
```

### make_mini_repo（L891-892）

```
tmp 迷你仓 fixture（形制 1:1 仿真仓四处：头注表/usage heredoc/hint_for/
    case 分派＋CASES 块＋三计数行＋doc 面）。落盘即返（None）。
```

### selftest（L1018-1025）

```
矢量组（tmp 迷你仓 fixture·全离线·真 subprocess --help 于夹具小器）：
    V1 一致迷你仓 0 漂（rc0·verdict consistent·三查全 ok）
    V2 工具表缺一（hint 摘 b）→ rc1·tool_table drift 指 cw.sh:hint
    V3 计数漂（覆盖面 3≠2）→ rc1·count drift
    V4 旗标幻引（docs/note.md --bogus-flag）→ rc1·flag drift
    V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9·--help-cap 0→2）
    V6 JSON 幂等（同仓两跑异 --json 路径字节恒同）
    
```

## 字符串常量（逐字·按行序）

```
L3: 'doc_lint.py — 文档←→实现一致性三查器（docs↔tools 对账·防文档漂移·rocqwash\ntools/·v38 工装席任务书·20261111 入账）\n\n三查（全部纯本地·零网络零编译·python3 纯 stdlib·编排零新引擎——解析规则逐条\n锚在盘件现行行，不发明新形）：\n  ①工具表查＝cw.sh 头注/usage/hint/case 四处工具清单互检＋与 tools/ 目录实有\n    通用入口对账（路由缺/表多/表少逐条列）。四处＝头注工具表（cw.sh:10-50·name\n    desc -> path·两行折行体 cw.sh:25-26 doctor 等同形）、usage() heredoc 工具表\n    （cw.sh:83-124）、hint_for() 一行提示（cw.sh:133-153·echo 串尾缀 -> path）、\n    case 分派（cw.sh:170-186·run_tool <name> "<rel>"）。互检＝有路由者四处俱在\n    （缺一处即表少·逐器逐处列）＋四处路径逐器咬合（不符/缺 -> 路径即列）；\n    对账＝case 路由目标缺盘即「表多（悬路由）」、tools/ 非 _ 前缀 .py（通用\n    入口·定义锚 cli/rocqwash:9「模块目录下唯一一个不带前导下划线的 .py」）\n    无 case 路由即「路由缺」。help 为伪路由不参赛（cw.sh:49 头注行＋\n    cw.sh:187 help|-h|--help 特例分派·hint_for 无分支——四处本就不对称）。\n  ②计数查＝tests/run_tests.sh CASES 数（run_tests.sh:140-192 静态在册例·\n    t_fail_probe 为 FAIL_PROBE 自检注入例不计·run_tests.sh:194-197）vs\n    tests/README.md 计数行（:12「预期 52 过」＋:15「## 覆盖面（52 例）」）vs\n    README.md 例数行（:59「自测套件（52 例）— test suite (52 cases)」）——\n    数值三处一致·漂移即列；计数行形未现＝计数行缺失亦列。README.md:83/92/\n    101/112/123/139/156「扩至 N 例」等增补史行为版本化历史非现势计数（逐轮\n    累进属设计内·v38 轮 cw.sh:2「共十六」同款史行）·不在对账面——只锚上述\n    四形，宁缺毋滥不造新计数形。\n  ③旗标查＝README-cw.md/README.md/examples/workflows/*.md/docs/*.md（docs/\n    递归·*.zh.md 与 docs/zh/ 归档面免扫——注释规范卡 §5.2 归档件非正本面）\n    中引用的器旗标（--xxx 形）逐枚对照各器 --help 实出输出\n    （subprocess 真跑 --help·rc!=0/超时=器红 fail-loud 9·帽 --help-cap 25 器）。\n    器集＝cw.sh 路由 ∪ tools/ 非 _ 前缀 .py＝25 器（现势·帽 25 有余）；\n    超帽按典序截断·溢出器如实列「未实跑 --help·引用 N 处未证」。归账规则＝\n    器引用两级（一级强引用＝盘路径形/cli/rocqwash/cw.sh 路由形·二级弱引用＝\n    裸名形——路由名/器 stem/在盘 oos 器 stem），旗标归其逻辑行最近前驱一级\n    引用·无则二级（README.md:232「cli/rocqwash certify push_gate union-freeze\n    --world…」内 union-freeze 裸名 union 不得咬走 primary 的实证律）；旗标\n    token 先掩码再找器引用（防 --probe-resume 内 \x08probe\x08 误吞）。池兜底三\n    路：散文段＝空行/围栏/标题界整段引用两遍收集（段首旗标如 README-cw.md:77\n    「① --once/--loop 双模」实证）；代码围栏命令行＝反斜杠续行拼行后严格\n    只在命令自身内归账（幻引判定最强面）；代码围栏注释行＝块池归账\n    （step-pushci.md:75-77「# 可选追加：--pre-scan-gate4／--merge…」实形）。漂移两向＝\n    缺旗标（幻引/多余引用·同面两词：doc 侧引用为多余·器侧实出缺此旗标——\n    primary 器 help 实出无＋池内 registry 器全缺＋池内无可证 oos/unknown 器；\n    「同一旗标 token 重复≥2 即多余」的机械判据被 README.md:232 union-freeze\n    --world wa=… --world wb=… 合法多值实证否弃·不采）＋悬引（primary 引用\n    不识——cw.sh 非路由/路由目标缺盘而旗标无器可证；cw.sh bogus 等退出码\n    示例行无旗标故不误咬）。无主旗标与池含 oos/unknown 器者＝unresolved\n    如实计不判漂（不可证≠漂——docs/zh/architecture.md:54 台账行「--json/\n    --hits-csv」属 scan 阶段件 mac_stmt_scan、上下文在文档节层·机检不可归账\n    不作漂判的实证律）。cli/rocqwash 及 registry 外器（certify/watch/wrapper/\n    战役件等）旗标非本查对象——计入 out_of_scope 如实出账（cli/rocqwash 为\n    v29 前路由层·旗标属子工具·cli/rocqwash:8-11 路由契约）。\n    argparse 折行复原：break_on_hyphens 断词实出「--on-red-<LF>arg」（cw_sentinel\n    --help 实证）——(--tok)-\n<ws>(cont) 复原后再取 token；registry_union --help:14\n    「--ref-*」词面为 glob 散文·截断 token 属噪音不害幻引判定（本查只单向\n    doc→help：help 散文多收旗标仅致漏报不致误报——精度换零误报·宁缺毋滥）。\n\n输出：--json report schema=rocqwash-doclint/1（checks[{kind,target,status,\ndetail}]·verdict consistent|drift·counts·out_of_scope·registry·args·sort_keys\n落盘·无墙钟字段·路径一律仓相对——同输入重跑字节恒同）。checks 逐条列：\nkind∈{tool_table,count,flag}·status∈{ok,drift}·detail 单行（截 300 字符）。\n\n退出码：0=consistent（三查零漂）；1=drift（任一条 drift·红是数据非器红·\n响亮 stdout）；2=用法错（argparse/--help-cap<1）；9=缺（--repo 缺目录/被审\n仓必需输入缺失：cw.sh·README.md·README-cw.md·tests/run_tests.sh·\ntests/README.md·docs/·examples/workflows/·--json 父目录缺·器 --help 器红/\n超时·doc 件不可解码）。\n\n本器一次性静态对账·无巡检环——--once/--loop 无涉（cw_doctor 同例）；子进程\n仅本地 --help 真跑（毫秒级·零网络零编译零睡）——--injector/--sleep-scale 无涉\n·离线天然可测（--selftest 全 tmp 迷你仓夹具）。\n\n--selftest 矢量（tmp 迷你仓 fixture·四判＋CLI 三码＋幂等一判）：\n  V1 一致迷你仓（2 路由四处齐·计数 2 三处一致·旗标实引全证）→ rc0·verdict\n     consistent·checks 零 drift。\n  V2 工具表缺一（hint_for 摘 b 行）→ rc1·tool_table drift 指向 cw.sh:hint。\n  V3 计数漂（tests/README.md 覆盖面改 3）→ rc1·count drift 数值 3≠2。\n  V4 旗标幻引（docs/note.md 增 --bogus-flag 引用）→ rc1·flag drift 幻引。\n  V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9）＋--help-cap 0→2。\n  V6 JSON 幂等（同仓两跑异 --json 路径字节恒同——report 不嵌 json 路径）。\n\n用法（全部路径参数化·零硬编码）：\n  python3 tools/doc_lint.py [--repo DIR] [--json OUT] [--help-cap N]\n  python3 tools/doc_lint.py --selftest\n'
L120: '^(路由契约|退出码|路由说明|覆盖面注)'
L128: '覆盖面（(\\d+) 例）'
L128: '覆盖面（N 例）'
L129: '预期 (\\d+) 过'
L129: '预期 N 过'
L130: '自测套件（(\\d+) 例）'
L130: '自测套件（N 例）'
L150: '用法错/值校验败（exit 2）。'
L154: '输入缺失（exit 9）。'
L158: '器红/--help 失败（exit 9·fail-loud 禁静默降级）。'
L168: '%s 不可读/解码失败: %s (%s)'
L176: '--json 落盘失败: %s (%s)'
L180: '仓相对路径（确定性·报告零绝对路径纪律）。'
L196: '表体行 → {name: {"path": str|None, "line": int}}（仅认路由名形\n    ^[a-z0-9][a-z0-9-]*$·三体：单行 name desc -> path／续行 -> path／折行\n    pending name 待续行赋 path·cw.sh:25-26 doctor 折行体 1:1）。\n    路由契约/退出码等段界行截停（TABLE_STOP_RE）。'
L234: 'cw.sh 四处清单解析 → {place: {name: {"path", "line"}}}。\n    区域界锚：头注至首个 set -u（cw.sh:73）；usage 至首 EOF（heredoc 终）；\n    hint_for 至首个列 0 }；case 至 EOF（case "${1:-}" in 唯一分派 case·\n    hint_for 内 case "$1" in 不误咬）。'
L240: '被审仓缺 cw.sh: %s'
L252: 'cw.sh 形不识（无 set -u 界）: %s'
L261: 'cw.sh 形不识（usage/hint_for/case 界缺一）: %s'
L267: '工具表 Tools'
L269: '工具 Tools:'
L289: '①四处互检＋tools/ 通用入口对账 → checks 列表（逐条·kind=tool_table）。'
L298: '工具 %s 于 case 路由在册而 %s 表缺行（互检表少）'
L304: '工具 %s 仅 %s 表在册而 case 无路由（互检悬名）'
L316: '工具 %s 于 %s 行缺 -> 路径（折行体断裂）'
L322: '工具 %s 路径不一：%s=%s vs case=%s'
L330: '被审仓缺 tools/ 目录: %s'
L336: '路由目标缺盘 %s（表多·悬路由）'
L349: 'tools/ 通用入口（cli/rocqwash:9 非 _ 前缀 .py 定义）无 cw.sh case 路由（路由缺）'
L353: 'cw.sh 四处＋tools/'
L355: '互检一致（%d 器四处齐·路径咬合）＋对账零缺口（tools/ 通用入口 %d 全路由）'
L366: '②CASES 数 vs tests/README.md 计数行 vs README.md 例数行 → checks。'
L371: '被审仓缺 %s: %s'
L375: 'run_tests.sh 形不识（CASES=" 块缺）: %s'
L383: 'CASES 在册 %d 例（静态在册·t_fail_probe 为 FAIL_PROBE 注入例不计）'
L388: '被审仓缺 %s: %s'
L393: '计数行形「%s」未现（计数行缺失）'
L402: '「%s」＝%d 与 CASES %d 一致'
L408: '「%s」＝%d ≠ CASES %d（计数漂）'
L416: 'subprocess 真跑 --help → 实出旗标集（含折行复原）。rc!=0/超时=器红 9。'
L423: '--help 超时（>%ds）: %s (%s)'
L427: '--help 器红 rc=%d: %s (%s)'
L434: '③扫描上下文：器集映射＋help 实出集＋账面。\n    器引用两级：一级强引用（盘路径形/cli/rocqwash/cw.sh 路由形）·二级弱引用\n    （裸名形——路由名/器 stem/在盘 oos 器 stem）。primary 取行内最近前驱一级\n    引用·无则二级（防 README.md:232「cli/rocqwash certify push_gate\n    union-freeze --world…」内 union-freeze 的裸名 union 咬走 primary）。'
L484: '逐器真跑 --help（典序·帽内）→ help 集（并集仓级通用旗标——\n        UNIVERSAL_FLAGS 注）。'
L502: 'cw.sh %s（非路由）'
L504: 'cw.sh %s（路由目标缺盘 %s）'
L518: '③ 对账面文件序（README 系→examples/workflows/*.md→docs/ 递归·典序）。'
L522: '被审仓缺 examples/workflows/: %s'
L527: '被审仓缺 docs/: %s'
L544: '单文件 ③ 扫描 → (item, drift_n, refs_n)。\n    三路归账：①散文段＝空行/围栏/标题界的整段两遍处理（一遍收全段引用池·\n    二遍逐行归账——段首旗标如 README-cw.md:77「① --once/--loop 双模」前驱\n    无器引用，段池兜底）；②代码围栏命令行＝反斜杠续行拼行后逐命令严格归账\n    （池＝命令自身引用·幻引判定最强面）；③代码围栏注释行（step-pushci.md:75-77\n    「# 可选追加：--pre-scan-gate4…」实形）＝块池归账（全块引用两遍收集）。\n    引用两级：一级（路径/cli/路由）＞二级（裸名）——primary 取最近前驱一级·\n    无则二级。漂移两向：缺旗标（幻引/多余引用——primary 器 help 实出无此\n    旗标＋池内 registry 器全缺＋池内无可证 oos/unknown 器）；悬引（primary\n    引用不识——cw.sh 非路由/路由目标缺盘）。无主旗标与池含 oos/unknown 者\n    ＝unresolved 如实计（不可证≠漂——zh/en architecture 台账行「--json/\n    --hits-csv」属 scan 阶段件 mac_stmt_scan 实证：上下文在文档节层·机检\n    不可归账不作漂判）。旗标 token 先掩码再找器引用（防 --probe-resume 内\n    \\bprobe\\b 误吞）。'
L571: '→ (mentions 有序[(pos, tier, (kind,key))], flag_hits[(pos,tok)])。\n        tier 1＝路径/cli/路由强引用·2＝裸名弱引用。旗标 token 先掩码（同长\n        空格·位置不漂）再找器引用。'
L593: '单逻辑行归账 → (drifts, refs, unresolved)。primary＝行内最近前驱\n        一级引用·无则二级；pool＝兜底池（kind-tagged·tool/oos/unknown）。'
L617: '缺旗标（幻引/多余引用）：%s 前最近器 %s help 实出无此旗标（实出 %d 枚）·池 %s 亦无'
L621: '空'
L628: '悬引：旗标 %s 前最近器引用不识（%s）——无器可证'
L637: '代码块两遍：一遍收全块引用池（注释行用）·二遍逐逻辑行归账\n        （命令行严格自身池·注释行块池）。'
L662: '散文段两遍：一遍收全段引用池·二遍逐行归账（段池兜底）。'
L683: '续行拼装收口 → 逻辑行入代码块缓冲。'
L741: '另 %d 条未列（帽 %d）'
L752: '③旗标查总控：help 真跑→逐件扫描→checks（每文件一项＋溢出器未证项）。'
L766: 'help 帽 %d 溢出未实跑 --help·doc 引用 %d 处未证（旗标查未竟）'
L773: '溢出器在 doc 面的引用计数（重扫轻量：仅器引用不跑旗标判定）。'
L790: '总控：值校验（2）→被审仓先验（9）→①②③逐查→report（0/1）。'
L792: '--help-cap 须≥1 实测 %d'
L795: '--repo 缺目录: %s'
L799: '被审仓必需输入缺失: %s'
L800: '=== DOC-LINT（文档←→实现一致性三查）=== repo=%s'
L809: '无'
L818: '[flag] docs=%d help_run=%d/%d（帽 %d）drift=%d'
L865: '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""tool_a.py — 演示器甲（doc_lint --selftest 迷你仓夹具·旗标形制仿\nscan_v4_token --file/--json 形）"""\nimport argparse\nap = argparse.ArgumentParser(prog="tool_a",\n                             description="演示器甲：--file/--json 两旗标")\nap.add_argument("--file", metavar="F", help="目标件")\nap.add_argument("--json", metavar="OUT", help="报告出账")\nap.parse_args()\n'
L877: '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""tool_b.py — 演示器乙（doc_lint --selftest 迷你仓夹具·旗标形制仿\ncure_applier --dir/--apply 形）"""\nimport argparse\nap = argparse.ArgumentParser(prog="tool_b",\n                             description="演示器乙：--dir/--apply 两旗标")\nap.add_argument("--dir", metavar="DIR", help="目标目录")\nap.add_argument("--apply", action="store_true", help="落刀")\nap.parse_args()\n'
L891: 'tmp 迷你仓 fixture（形制 1:1 仿真仓四处：头注表/usage heredoc/hint_for/\n    case 分派＋CASES 块＋三计数行＋doc 面）。落盘即返（None）。'
L898: '    b) echo "cw.sh b --dir DIR [--apply]   # 演示器乙 -> tools/tool_b.py" ;;\n'
L901: '#!/usr/bin/env bash\n# cw.sh — mini fixture 统一入口（a/b 两器）\n#\n# 用法 Usage: bash cw.sh <tool> [args...]\n#\n# 工具表 Tools:\n#   a           演示器甲 -> tools/tool_a.py\n#               cw.sh a --file <f.v> [--json out.json]\n#   b           演示器乙 -> tools/tool_b.py\n#               cw.sh b --dir DIR [--apply]\n#   help        本帮助（help <tool> = 该工具一行提示）\n#\n# 路由契约 Routing contract:\n#   1. 参数与退出码 1:1 透传。\nset -u\nROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\nusage() {\n  cat <<\'EOF\'\ncw.sh — mini fixture\n用法 Usage: bash cw.sh <tool> [args...]\n工具 Tools:\n  a           演示器甲 -> tools/tool_a.py\n  b           演示器乙 -> tools/tool_b.py\n  help        本帮助\n退出码 Exit codes: 0=pass 2=unknown-tool 9=missing\nEOF\n}\nhint_for() {\n  case "$1" in\n    a) echo "cw.sh a --file <f.v> [--json out.json]   # 演示器甲 -> tools/tool_a.py" ;;\n'
L933: '    *) return 1 ;;\n  esac\n}\nrun_tool() {\n  local tool="$1" rel="$2"\n  shift 2\n  exec python3 "$ROOT/$rel" "$@"\n}\ncase "${1:-}" in\n  a) shift; run_tool a "tools/tool_a.py" "$@" ;;\n  b) shift; run_tool b "tools/tool_b.py" "$@" ;;\n  help|-h|--help)\n    usage\n    exit 0 ;;\n  *)\n    echo "cw.sh: 未知工具 unknown tool: $1" >&2\n    exit 2 ;;\nesac\n'
L958: '#!/bin/bash\n# run_tests.sh — mini fixture 套件\nset -u\nREPO="$(cd "$(dirname "$0")/.." && pwd)"\nCASES="\\\nt_a \\\nt_b"\nt_a() { python3 -B "$REPO/tools/tool_a.py" --help >/dev/null; }\nt_b() { python3 -B "$REPO/tools/tool_b.py" --help >/dev/null; }\nfor c in $CASES; do "$c" || exit 1; done\n'
L972: '# tests/ — mini\n套件自检（注入一恒红例）：\nROCQWASH_TESTS_FAIL_PROBE=1 bash tests/run_tests.sh   # 预期 2 过 / 1 红 / EXIT 1\n\n## 覆盖面（%s 例）\n'
L978: '| # | 用例 |\n|---|------|\n| 1 | `t_a` |\n| 2 | `t_b` |\n'
L982: '# mini repo\n```\n├── tests/  # 自测套件（2 例）— test suite (2 cases)\n```\n'
L989: '# cw.sh mini 速查\n| 工具 | 目标脚本 | 一行示例 |\n|------|----------|----------|\n| `a` | `tools/tool_a.py` | `bash cw.sh a --file demo.v --json out.json` |\n| `b` | `tools/tool_b.py` | `bash cw.sh b --dir src/ --apply` |\n'
L995: 'python3 tools/tool_a.py --bogus-flag demo.v 幻引判例。\n'
L1001: '# note\n普查用 python3 tools/tool_a.py --file demo.v --json out.json。\n收哨按 --max-rounds 界定（无器上下文·unresolved 不判漂判例）。\n'
L1018: '矢量组（tmp 迷你仓 fixture·全离线·真 subprocess --help 于夹具小器）：\n    V1 一致迷你仓 0 漂（rc0·verdict consistent·三查全 ok）\n    V2 工具表缺一（hint 摘 b）→ rc1·tool_table drift 指 cw.sh:hint\n    V3 计数漂（覆盖面 3≠2）→ rc1·count drift\n    V4 旗标幻引（docs/note.md --bogus-flag）→ rc1·flag drift\n    V5 CLI 三码（--help 0·--bogus 2·--repo 缺 9·--help-cap 0→2）\n    V6 JSON 幂等（同仓两跑异 --json 路径字节恒同）\n    '
L1104: '幻引'
L1115: '未知形参应 rc=2 实测 %d'
L1117: '--repo 缺目录应 rc=9 实测 %d'
L1119: '--help-cap 0 应 rc=2 实测 %d'
L1130: 'json 字节漂移＝违例'
L1134: 'DOC-LINT-SELFTEST PASS: 一致仓0漂/工具表缺一(hint)/计数漂(3≠2)/旗标幻引(--bogus-flag)/CLI 三码＋cap 值校验/JSON 幂等字节恒同 六节全过'
L1152: '文档←→实现一致性三查器：工具表查（cw.sh 四处互检＋tools/ 通用入口对账）＋计数查（CASES vs tests/README.md vs README.md）＋旗标查（doc 引用旗标 vs --help 实出·帽 20 器）（schema rocqwash-doclint/1）'
L1158: '被审仓根（缺省＝本件所在 tools/ 的上一级）'
L1160: '报告出账（rocqwash-doclint/1·sort_keys 确定性）'
L1163: '③ --help 真跑器帽（缺省 25·溢出典序截断如实列）'
```
