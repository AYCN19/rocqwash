# tools/cw_doctor.py 中文原面留档（archive）


- 源文件：`tools/cw_doctor.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `tools/cw_doctor.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 模块 docstring（逐字）

```
cw_doctor.py — 综合体检器·四域聚合（rocqwash tools/·v37 工装席任务书·
20261111 入账）

一键全面健康评估：四域逐域 subprocess 编排**既有一器**（编排而非重造——先读
各器 CLI 与 JSON schema 再接线·器红/形坏 fail-loud·零新引擎），聚合为综合
健康分 0-100＋per-domain verdict＋advice 处置清单（每非绿域一条·指向对应器）：
  ①环境域(40)＝subprocess toolchain_dyld_doctor（worker 缺省探测：flag/env
    ROCWASH_ROCQWORKER/判例机缺省·器内自决）→ 报告 verdict healthy|
    missing-libs|worker-missing → healthy=100 分·余=0 分（红是数据非器红）。
  ②网络域(20)＝subprocess net_probe --rounds 1 --interval 0（缺省四端点）→
    报告 verdict all-up|partial|all-down（无 --stable-window 时 net_probe
    exit 0 仅＝探完成——可达性读报告 verdict 字段非退出码）→ score=可达率×100。
  ③注册域(25)＝--registry PATH 显传（缺册 fail-loud 9）> env CW_SET/
    ConstructiveWorld_Live/order.txt 探测（缺册如实 skip）> 全无 skip →
    锚正典形审计：#R<序>-<md5_8> 形合规率（正典指纹＝md5 前 8 位小写 hex·
    registry_union.md5_8_of 产物形；ANCHOR_RE 1:1 承 registry_union.py:81；
    注释行/空行不审计——key_of 同款语义；无锚表体行计入 no_anchor 不入合规
    率分母；非形清单帽 20·总数如实）→ score=合规率×100。
  ④堵账域(15)＝--src DIR（缺省跳过）＋--sample N（缺省 0=不抽样→域如实
    skip；域活须 --src 且 --sample>0）→ 全树典序枚举 .v（unclog 同款）→
    --sample N 等距抽样（i*total//N 索引·N≥树大＝全量普查）→ 候选 TSV →
    subprocess probe_engine --fresh（真探必 --world·--guard 缺省
    ConstructiveWorld cpu_guard.sh 温控——sanctioned 缺省承
    toolchain_dyld_doctor 同款·可 --guard 覆盖）→ 台账 → chain_graph --top 1
    恒真跑（纯 stdlib 零编译零网络·真编排非傀儡·unclog 同款）→ 红账率
    （stats.rc1∪stats.other）→ score=(1-红账率)×100 → 有缺库链根时附 TOP
    一名（top_order 首名·n＋self 可洗性）。

综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）；
verdict healthy(≥90)｜degraded(<90)。advice：env→toolchain_dyld_doctor 溯源
还原（只建议·禁代执行）·net→net_probe --stable-window 双探稳窗·registry→
registry_union --reanchor 重锚正典形·clog→unclog 闭环疏通·skip 域→显传
对应开关后重跑体检。

离线可测（v37 纪律·全 subprocess 层 canned 注入）：--injector 场景 JSON
（DIR/scenario.json）＝{引擎键: {"rc": int, "stdout": str, "report": dict}}·
键集固定 dyld/net/probe（wash_shape Injector 同款契约·键不识 2）·canned 表
须覆盖本次将发的全部器件调用（dyld/net 恒需·probe 须于堵账域活时——缺键
9·绝不静默走真器真网·cw_sentinel 同律）。canned rc 语义随真器：dyld rc∈
{0,1,9} 带报告可解析（1/9=数据红）·rc=2/报告缺/形坏=器红 9；net/probe
rc≠0=器红 9。probe canned 台账原样落 workdir 后仍喂真 chain_graph（真编排
非傀儡·unclog 同款）。本器自身零 sleep 零 loop（--sleep-scale 无涉·net 轮
间隔恒 0）。

确定性：report 无墙钟字段·路径一律 basename（绝对路径证据在 stdout 与
workdir 工件）·sort_keys 落盘·同输入同环境重跑字节级恒同。

用法（全部路径参数化·除 --guard sanctioned 缺省外零硬编码）：
  python3 tools/cw_doctor.py [--json OUT] [--workdir DIR]
      [--registry PATH] [--src DIR --sample N [--world DIR]]
      [--worker PATH] [--donor DIR] [--endpoints URL[,URL...]]
      [--guard PATH] [--guard-reg DIR] [--guard-maxwait S] [--timeout S]
      [--rocq-cmd TPL] [--injector DIR]
  python3 tools/cw_doctor.py --selftest

退出码：0=healthy（综合分 ≥90）；1=degraded（<90·红响亮出账——域红是数据
非器红）；2=用法错（argparse/--sample 负/--timeout 非/injector 场景形坏·键
不识）；9=缺（器件缺失/--registry 显传缺册/--src 缺目录/--world 真探缺/
--guard 缺/--src 零候选/injector 场景缺·canned 未覆盖/子进程器红/报告
schema 不识/注册册解码失败）。--json report schema=rocqwash-cwdoctor/1。

```

## 注释（逐字·按行序）

```
L95: # 锚形 1:1 承 registry_union.py:81 ANCHOR_RE；正典形＝#R<序>-<md5 前 8 位
L96: # 小写 hex（registry_union.md5_8_of=hexdigest()[:8] 产物形·:80 注记「重锚后
L97: # 恒为 #R<序号>-<md5 前 8 hex>」）
L103: # sanctioned 判例机缺省（toolchain_dyld_doctor.py DEFAULT_GUARD 同款·任务书
L104: # 钦定路径·--guard 可覆盖）
L120: # ---- 小件（确定性 helpers·unclog/wash_shape 同款本地副本·无包结构不互 import）--
L196: # ---- 注入点：子进程调用层罐装（v37 离线可测纪律·wash_shape Injector 同款）----
L245: # ---- ①环境域 -----------------------------------------------------------------
L291: # ---- ②网络域 -----------------------------------------------------------------
L341: # ---- ③注册域 -----------------------------------------------------------------
L381: # 注释行（首 # 前空·key_of 同款语义·非表体）
L423: # ---- ④堵账域 -----------------------------------------------------------------
L442: # canned 台账原样落 workdir·仍喂真 chain_graph
L474: # 链根图恒真跑（纯 stdlib·零编译零网络·真编排非傀儡）·TOP 一名
L507: # ---- 聚合：综合分＋verdict＋advice ---------------------------------------------
L578: # ---- 总控 ---------------------------------------------------------------------
L597: # 值校验（2）
L604: # 器件先验（9·编排零新引擎——四器在位性先验）
L644: # stdout 响亮（确定性域序）
L692: # ---- --selftest（内嵌冻结向量组·tmp fixture 树·全 subprocess 层 canned 注入）----
L759: # canned 报告（冻结向量·路径全假·零机器依赖）
L796: # 红账向量：A 可洗链根·B/C 缺 A·D 缺 B → TOP1=A(n=2)·红 3/4
L818: # 正典
L819: # 正典
L820: # 非形·裸序号
L821: # 非形·5 位
L822: # 非形·大写 8 位（md5_8 恒小写）
L823: # 非形·9 位
L824: # 表体无锚→no_anchor
L825: # 注释行→不审计
L826: # 空行→不审计
L831: # ---- V1 四域全绿 100 分 ----
L854: # 域名固定四键（确定性形制）
L857: # ---- V2 环境红降分（0×40 → 60.0·degraded·advice 指 dyld）----
L873: # ---- V3 注册缺册 skip 归一（CW_SET 剥离·net partial→86.67）----
L887: # CW_SET 设而缺册→如实 skip（reason 含「缺册」）
L898: # ---- V4 堵账 TOP 注入（红 3/4→clog 25.0→88.75·TOP1=A）----
L917: # ---- V6 JSON 幂等：同场景两跑异 workdir 字节恒同 ----
L934: # ---- V7 CLI 四码 ----
L958: # --src 在册而 --sample 0（缺省不抽样）→堵账域如实 skip 不真探
L967: # ---- V8 注册审计单元 ----
L975: # 帽 20：25 条非形→清单 20·总数 25
L981: # 零锚册→rate 0·non-canonical
L988: # CW_SET 正探：册在 CW_SET/ConstructiveWorld_Live/order.txt
```

## 函数级 docstring（逐字）

### UsageError（L109-109）

```
用法错/场景形坏（exit 2）。
```

### MissingInput（L113-113）

```
输入缺失（exit 9）。
```

### ToolError（L117-117）

```
编排器件器红/报告形坏（exit 9·fail-loud 禁静默降级）。
```

### run_py（L148-149）

```
python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·unclog 同款）。
    缺件→9。
```

### write_cands_tsv（L160-160）

```
候选清单 TSV（件名/md5 双列·probe_engine 必需列形制·unclog 同款）。
```

### enumerate_tree（L168-169）

```
--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·
    双排序·unclog 同款）。
```

### sample_pairs（L182-183）

```
确定性等距抽样：典序枚举上取 i*total//N 索引（span 长 total>n 必含
    n 的倍数→索引严格递增不重复）；N≥total 时全量普查（不抽样）。
```

### Injector（L199-203）

```
--injector DIR：子进程调用层罐装（DIR/scenario.json·unclog 同款形）。
    场景 JSON {引擎键: {"rc": int, "stdout": str, "report": dict}}；键集＝
    dyld/net/probe；命中键的器件调用恒定返付 canned·不真 subprocess。canned
    表须覆盖本次将发的全部器件调用（run() 预检·缺键 9——绝不静默走真器真
    网·cw_sentinel 同律）。
```

### require（L233-233）

```
canned 全覆盖预检（缺键 9·防半罐装静默走真器真网）。
```

### domain_env（L248-250）

```
①环境域：subprocess toolchain_dyld_doctor --json（worker 缺省探测器
    内自决·--worker/--donor 可透传）。verdict healthy=100 分·余=0 分；
    rc∈{0,1,9} 带报告＝数据（1/9 数据红）·rc=2/报告缺/形坏=器红 9。
```

### domain_net（L294-296）

```
②网络域：subprocess net_probe --rounds 1 --interval 0（缺省四端点·
    --endpoints 可覆盖）。无 --stable-window 时 net_probe exit 0 仅＝探完成
    ——可达性读报告 verdict 字段；score=可达率×100。
```

### resolve_registry（L344-346）

```
注册册三择：--registry 显传（缺册 fail-loud 9·显传输入禁静默 skip）
    > env CW_SET 探测（缺册如实 skip）> 全无 skip。
    → (path|None, source|None, skip_reason|None)。
```

### audit_registry（L362-365）

```
册锚正典形审计（纯读零子进程）：非空非注释行（registry_union key_of
    同款语义——首 # 前空＝注释/空行跳过）上取 ANCHOR_RE 首锚（anchor_of 同款
    逐行首中）→ 正典形 #R<序>-<md5_8> 全match判定。非形清单帽 NON_FORM_CAP
    条·总数如实。
```

### domain_registry（L402-403）

```
③注册域：锚正典形审计→合规率×100。anchored==0（册内零锚）＝rate 0
    如实 non-canonical；skip 域权重剔除归一。
```

### domain_clog（L426-428）

```
④堵账域：--src 且 --sample>0 才活（缺省 0=不抽样→如实 skip）。
    全树典序枚举→等距抽样→候选 TSV→probe_engine --fresh（真探必 --world·
    --guard 温控）→台账→chain_graph --top 1 恒真跑→红账率→TOP 一名。
```

### compute_score（L510-511）

```
综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）。
    env/net 恒跑→分母 ≥60；全 skip 为内部不变量炸（fail-loud）。
```

### advice_of（L526-527）

```
advice 清单：每非绿域一条处置建议（固定域序·指向对应器·skip 域指
    开关）。全绿→空表。
```

### args_summary（L581-581）

```
args 摘要（路径一律 basename——绝对路径不进 report·确定性纪律）。
```

### run（L595-596）

```
总控：值校验（2）→器件先验（9）→注册册三择→canned 全覆盖预检→
    四域逐域跑→综合分→verdict→advice→report（0=healthy/1=degraded）。
```

### selftest（L695-709）

```
矢量组（tmp fixture＋injector 子进程调用层罐装·零真 otool 零真网络
    零真编译·chain_graph/注册审计真跑——纯 stdlib 零编译零网络）：
    V1 四域全绿 100 分（exit 0·advice 空·active weight 100）
    V2 环境红降分（missing-libs→env 0 分→60.0·degraded·advice 指 dyld）
    V3 注册缺册 skip 归一（CW_SET 剥离＋net partial→86.67·active weight 75·
       advice 含 net＋registry 两条）＋CW_SET 缺册如实 skip
    V4 堵账 TOP 注入（canned 红账 3/4→clog 25.0→88.75·chain TOP1=A(n=2)·
       advice 指 unclog）
    V5 advice 生成（V2/V3/V4 逐条断言·全绿空表已在 V1）
    V6 JSON 幂等（同场景两跑异 workdir 字节恒同）
    V7 CLI 四码（--help 0·--bogus 2·--sample 负 2·--registry 缺册 9·--src
       缺目录 9·--injector 场景缺 9·场景键不识 2·canned 未覆盖 9）
    V8 注册审计单元（混形 rate 2/6·注释/空行/无锚行计数·帽 25→20·7/8/9 位
       指纹与大写 hex 皆非形·零锚册·CW_SET 正探 source=CW_SET）
    
```

## 字符串常量（逐字·按行序）

```
L3: 'cw_doctor.py — 综合体检器·四域聚合（rocqwash tools/·v37 工装席任务书·\n20261111 入账）\n\n一键全面健康评估：四域逐域 subprocess 编排**既有一器**（编排而非重造——先读\n各器 CLI 与 JSON schema 再接线·器红/形坏 fail-loud·零新引擎），聚合为综合\n健康分 0-100＋per-domain verdict＋advice 处置清单（每非绿域一条·指向对应器）：\n  ①环境域(40)＝subprocess toolchain_dyld_doctor（worker 缺省探测：flag/env\n    ROCWASH_ROCQWORKER/判例机缺省·器内自决）→ 报告 verdict healthy|\n    missing-libs|worker-missing → healthy=100 分·余=0 分（红是数据非器红）。\n  ②网络域(20)＝subprocess net_probe --rounds 1 --interval 0（缺省四端点）→\n    报告 verdict all-up|partial|all-down（无 --stable-window 时 net_probe\n    exit 0 仅＝探完成——可达性读报告 verdict 字段非退出码）→ score=可达率×100。\n  ③注册域(25)＝--registry PATH 显传（缺册 fail-loud 9）> env CW_SET/\n    ConstructiveWorld_Live/order.txt 探测（缺册如实 skip）> 全无 skip →\n    锚正典形审计：#R<序>-<md5_8> 形合规率（正典指纹＝md5 前 8 位小写 hex·\n    registry_union.md5_8_of 产物形；ANCHOR_RE 1:1 承 registry_union.py:81；\n    注释行/空行不审计——key_of 同款语义；无锚表体行计入 no_anchor 不入合规\n    率分母；非形清单帽 20·总数如实）→ score=合规率×100。\n  ④堵账域(15)＝--src DIR（缺省跳过）＋--sample N（缺省 0=不抽样→域如实\n    skip；域活须 --src 且 --sample>0）→ 全树典序枚举 .v（unclog 同款）→\n    --sample N 等距抽样（i*total//N 索引·N≥树大＝全量普查）→ 候选 TSV →\n    subprocess probe_engine --fresh（真探必 --world·--guard 缺省\n    ConstructiveWorld cpu_guard.sh 温控——sanctioned 缺省承\n    toolchain_dyld_doctor 同款·可 --guard 覆盖）→ 台账 → chain_graph --top 1\n    恒真跑（纯 stdlib 零编译零网络·真编排非傀儡·unclog 同款）→ 红账率\n    （stats.rc1∪stats.other）→ score=(1-红账率)×100 → 有缺库链根时附 TOP\n    一名（top_order 首名·n＋self 可洗性）。\n\n综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）；\nverdict healthy(≥90)｜degraded(<90)。advice：env→toolchain_dyld_doctor 溯源\n还原（只建议·禁代执行）·net→net_probe --stable-window 双探稳窗·registry→\nregistry_union --reanchor 重锚正典形·clog→unclog 闭环疏通·skip 域→显传\n对应开关后重跑体检。\n\n离线可测（v37 纪律·全 subprocess 层 canned 注入）：--injector 场景 JSON\n（DIR/scenario.json）＝{引擎键: {"rc": int, "stdout": str, "report": dict}}·\n键集固定 dyld/net/probe（wash_shape Injector 同款契约·键不识 2）·canned 表\n须覆盖本次将发的全部器件调用（dyld/net 恒需·probe 须于堵账域活时——缺键\n9·绝不静默走真器真网·cw_sentinel 同律）。canned rc 语义随真器：dyld rc∈\n{0,1,9} 带报告可解析（1/9=数据红）·rc=2/报告缺/形坏=器红 9；net/probe\nrc≠0=器红 9。probe canned 台账原样落 workdir 后仍喂真 chain_graph（真编排\n非傀儡·unclog 同款）。本器自身零 sleep 零 loop（--sleep-scale 无涉·net 轮\n间隔恒 0）。\n\n确定性：report 无墙钟字段·路径一律 basename（绝对路径证据在 stdout 与\nworkdir 工件）·sort_keys 落盘·同输入同环境重跑字节级恒同。\n\n用法（全部路径参数化·除 --guard sanctioned 缺省外零硬编码）：\n  python3 tools/cw_doctor.py [--json OUT] [--workdir DIR]\n      [--registry PATH] [--src DIR --sample N [--world DIR]]\n      [--worker PATH] [--donor DIR] [--endpoints URL[,URL...]]\n      [--guard PATH] [--guard-reg DIR] [--guard-maxwait S] [--timeout S]\n      [--rocq-cmd TPL] [--injector DIR]\n  python3 tools/cw_doctor.py --selftest\n\n退出码：0=healthy（综合分 ≥90）；1=degraded（<90·红响亮出账——域红是数据\n非器红）；2=用法错（argparse/--sample 负/--timeout 非/injector 场景形坏·键\n不识）；9=缺（器件缺失/--registry 显传缺册/--src 缺目录/--world 真探缺/\n--guard 缺/--src 零候选/injector 场景缺·canned 未覆盖/子进程器红/报告\nschema 不识/注册册解码失败）。--json report schema=rocqwash-cwdoctor/1。\n'
L109: '用法错/场景形坏（exit 2）。'
L113: '输入缺失（exit 9）。'
L117: '编排器件器红/报告形坏（exit 9·fail-loud 禁静默降级）。'
L144: '%s JSON 形坏: %s (%s)'
L148: 'python3 -B <tool> <cli> 子进程单点（stdout+stderr 合流·unclog 同款）。\n    缺件→9。'
L151: '工具链件缺失: %s'
L160: '候选清单 TSV（件名/md5 双列·probe_engine 必需列形制·unclog 同款）。'
L162: '件名\tmd5\n'
L168: '--src 全树枚举 *.v → [(件名(相对路径·/分隔·去 .v), md5)]（确定性·\n    双排序·unclog 同款）。'
L182: '确定性等距抽样：典序枚举上取 i*total//N 索引（span 长 total>n 必含\n    n 的倍数→索引严格递增不重复）；N≥total 时全量普查（不抽样）。'
L199: '--injector DIR：子进程调用层罐装（DIR/scenario.json·unclog 同款形）。\n    场景 JSON {引擎键: {"rc": int, "stdout": str, "report": dict}}；键集＝\n    dyld/net/probe；命中键的器件调用恒定返付 canned·不真 subprocess。canned\n    表须覆盖本次将发的全部器件调用（run() 预检·缺键 9——绝不静默走真器真\n    网·cw_sentinel 同律）。'
L210: 'injector 场景缺失: %s'
L215: 'injector 场景 JSON 畸形: %s (%s)'
L217: 'injector 场景须 dict: %s'
L220: 'injector 场景键不识（须 %s）: %s'
L228: 'injector 罐装项 %r 形坏（须 {rc:int, stdout?:str, report?:dict}）: %r'
L233: 'canned 全覆盖预检（缺键 9·防半罐装静默走真器真网）。'
L236: 'injector canned 未覆盖 %s（canned 表须全覆盖将发的器件调用·绝不静默走真器真网）'
L248: '①环境域：subprocess toolchain_dyld_doctor --json（worker 缺省探测器\n    内自决·--worker/--donor 可透传）。verdict healthy=100 分·余=0 分；\n    rc∈{0,1,9} 带报告＝数据（1/9 数据红）·rc=2/报告缺/形坏=器红 9。'
L262: 'dyld 报告'
L265: 'toolchain_dyld_doctor 器红 rc=%d（报告未落盘）: %s'
L268: 'toolchain_dyld_doctor 器红 rc=%d: %s'
L270: 'dyld 报告 schema 不识: %r（期待 %s）'
L275: 'dyld 报告 verdict 不识: %r'
L278: 'dyld 报告 external_refs 形坏: %r'
L282: 'dyld 报告 external_refs 项形坏: %r'
L294: '②网络域：subprocess net_probe --rounds 1 --interval 0（缺省四端点·\n    --endpoints 可覆盖）。无 --stable-window 时 net_probe exit 0 仅＝探完成\n    ——可达性读报告 verdict 字段；score=可达率×100。'
L306: 'net 报告'
L309: 'net_probe 器红 rc=%d: %s'
L311: 'net 报告 schema 不识: %r（期待 %s）'
L316: 'net 报告 verdict 不识: %r'
L319: 'net 报告 rounds 形坏: %r'
L323: 'net 报告轮形坏: %r'
L327: 'net 报告端点项形坏: %r'
L331: 'net 报告零端点探针'
L344: '注册册三择：--registry 显传（缺册 fail-loud 9·显传输入禁静默 skip）\n    > env CW_SET 探测（缺册如实 skip）> 全无 skip。\n    → (path|None, source|None, skip_reason|None)。'
L349: '--registry 显传册缺失: %s'
L356: 'env %s=%s 下缺册（%s 不在盘）'
L358: '--registry 未显传且 env %s 未设'
L362: '册锚正典形审计（纯读零子进程）：非空非注释行（registry_union key_of\n    同款语义——首 # 前空＝注释/空行跳过）上取 ANCHOR_RE 首锚（anchor_of 同款\n    逐行首中）→ 正典形 #R<序>-<md5_8> 全match判定。非形清单帽 NON_FORM_CAP\n    条·总数如实。'
L371: '注册册不可读/解码失败: %s (%s)'
L402: '③注册域：锚正典形审计→合规率×100。anchored==0（册内零锚）＝rate 0\n    如实 non-canonical；skip 域权重剔除归一。'
L426: '④堵账域：--src 且 --sample>0 才活（缺省 0=不抽样→如实 skip）。\n    全树典序枚举→等距抽样→候选 TSV→probe_engine --fresh（真探必 --world·\n    --guard 温控）→台账→chain_graph --top 1 恒真跑→红账率→TOP 一名。'
L431: '--src 未给（堵账域缺省跳过）'
L434: '--src 在册但 --sample 0（缺省不抽样·真探须 --sample N>0）'
L446: '--src 全树枚举零 .v 候选: %s'
L450: '堵账候选面: 全树枚举抽样 %d 件（--sample %d）-> %s'
L453: '--world 必给（堵账真探针；离线请 --injector）'
L455: '--guard 缺失: %s'
L466: 'probe_engine 器红 rc=%d: %s'
L467: 'probe 台账'
L470: 'probe 台账 schema/形不识: %r（期待 %s＋records dict）'
L478: 'chain_graph 器红 rc=%d: %s'
L479: '链根图'
L481: '链根图 schema 不识: %r（期待 %s）'
L488: '链根图 stats 形坏: %r'
L510: '综合分＝Σ(域分×权重)/Σ(在域权重)（skip 域权重剔除归一·round 2 位）。\n    env/net 恒跑→分母 ≥60；全 skip 为内部不变量炸（fail-loud）。'
L521: '内部不变量炸：四域全 skip（env/net 恒跑不应发生）'
L526: 'advice 清单：每非绿域一条处置建议（固定域序·指向对应器·skip 域指\n    开关）。全绿→空表。'
L533: '环境域 verdict=%s（外部硬引用缺 %d 条）——运行 python3 tools/toolchain_dyld_doctor.py [--donor DIR] 溯源缺失库并按 restore 建议手工还原（只建议·禁代执行）'
L541: '网络域 %s（%d/%d up）——发射前运行 python3 tools/net_probe.py --rounds 2 --stable-window 取双探稳窗'
L548: '注册域 skip（%s）——显传 --registry PATH（如 $CW_SET/ConstructiveWorld_Live/order.txt）后重跑体检'
L553: '注册域锚形合规率 %.4f（非形 %d 条·帽 %d 已列）——运行 python3 tools/registry_union.py --reanchor <件名> --anchor-src <DIR> 重锚 #R<序>-<md5_8> 正典形'
L562: '堵账域 skip（%s）——显传 --src DIR --sample N 真探（受 cpu_guard 温控）后重跑体检'
L568: 'TOP1=无（红无缺库链根）'
L570: '堵账域红账率 %.4f（红 %d/%d·链根 %s）——运行 python3 tools/unclog.py --src <DIR> --world <DIR> 闭环疏通'
L581: 'args 摘要（路径一律 basename——绝对路径不进 report·确定性纪律）。'
L595: '总控：值校验（2）→器件先验（9）→注册册三择→canned 全覆盖预检→\n    四域逐域跑→综合分→verdict→advice→report（0=healthy/1=degraded）。'
L599: '--sample 须≥0（0=不抽样）实测 %d'
L601: '--timeout 须≥1 实测 %d'
L603: '--guard-maxwait 须≥1 实测 %d'
L610: '器件缺失: %s (%s)'
L612: '--src 目录缺失: %s'
L614: '--world 目录缺失: %s'
L620: 'injector: %s（canned %s·子进程调用层罐装不真 subprocess）'
L645: '=== CW-DOCTOR（综合体检·四域聚合）==='
L674: '无'
L675: '--- 评分 ---'
L679: '--- advice（每非绿域一条）---'
L684: '--- advice：全绿零处置 ---'
L695: '矢量组（tmp fixture＋injector 子进程调用层罐装·零真 otool 零真网络\n    零真编译·chain_graph/注册审计真跑——纯 stdlib 零编译零网络）：\n    V1 四域全绿 100 分（exit 0·advice 空·active weight 100）\n    V2 环境红降分（missing-libs→env 0 分→60.0·degraded·advice 指 dyld）\n    V3 注册缺册 skip 归一（CW_SET 剥离＋net partial→86.67·active weight 75·\n       advice 含 net＋registry 两条）＋CW_SET 缺册如实 skip\n    V4 堵账 TOP 注入（canned 红账 3/4→clog 25.0→88.75·chain TOP1=A(n=2)·\n       advice 指 unclog）\n    V5 advice 生成（V2/V3/V4 逐条断言·全绿空表已在 V1）\n    V6 JSON 幂等（同场景两跑异 workdir 字节恒同）\n    V7 CLI 四码（--help 0·--bogus 2·--sample 负 2·--registry 缺册 9·--src\n       缺目录 9·--injector 场景缺 9·场景键不识 2·canned 未覆盖 9）\n    V8 注册审计单元（混形 rate 2/6·注释/空行/无锚行计数·帽 25→20·7/8/9 位\n       指纹与大写 hex 皆非形·零锚册·CW_SET 正探 source=CW_SET）\n    '
L811: '# 正典册 fixture（全 #R<序>-<md5_8> 形）'
L825: '# 注释 #R9-d66910ab'
L896: '缺册'
L930: 'json 字节漂移＝违例'
L938: '未知形参应 rc=2 实测 %d'
L940: '--sample 负应 rc=2 实测 %d'
L942: '显传缺册应 rc=9 实测 %d'
L944: '--src 缺目录应 rc=9 实测 %d'
L946: 'injector 场景缺应 rc=9 实测 %d'
L951: '场景键不识应 rc=2 实测 %d'
L956: 'canned 未覆盖应 rc=9 实测 %d'
L1003: 'CW-DOCTOR-SELFTEST PASS: 四域全绿100/环境红降60/注册skip归一86.67＋CW_SET缺册/堵账TOP注入88.75/advice 生成/JSON 幂等字节恒同/CLI 四码＋罐装全覆盖/注册审计单元（混形2of6·帽20·零锚·CW_SET 正探） 九节全过'
L1022: '综合体检器·四域聚合：环境/网络/注册/堵账 逐域 subprocess 编排既有一器→综合健康分 0-100＋per-domain verdict＋advice（schema rocqwash-cwdoctor/1）'
L1026: '体检报告出账（rocqwash-cwdoctor/1·sort_keys 确定性）'
L1028: '工件目录（dyld/net 报告·probe 台账·链根图·缺省 mkdtemp·stdout 响亮路径）'
L1031: '注册册显传（order.txt 形；缺省探测 env %s/ConstructiveWorld_Live/order.txt·均无→注册域 skip）'
L1035: '堵账域源树（缺省跳过堵账域）'
L1037: '堵账抽样帽（缺省 0=不抽样→堵账域 skip·N>0 等距抽样·N≥树大=全量普查）'
L1040: '堵账真探世界目录（真探必给·离线请 --injector）'
L1042: '透传 toolchain_dyld_doctor --worker（缺省器内探测 flag/env/判例机缺省）'
L1045: '透传 toolchain_dyld_doctor --donor（missing 件溯源）'
L1047: '透传 net_probe --endpoints（缺省四端点）'
L1049: 'cpu_guard.sh 透传 probe_engine（堵账真探温控·sanctioned 判例机缺省）'
L1056: 'probe_engine 单件超时秒透传'
L1058: '探针命令模板透传 probe_engine（缺省用其内置默认）'
L1060: '离线罐装场景（DIR/scenario.json·键 dyld/net/probe·子进程调用层罐装 {rc,stdout,report}·canned 表须全覆盖将发的器件调用）'
```
