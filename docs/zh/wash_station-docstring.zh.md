# wrapper/wash_station.py 中文原面留档（archive）


- 源文件：`wrapper/wash_station.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `wrapper/wash_station.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 模块 docstring（逐字）

```
wash_station.py — 洗形⑤⑥⑦三步组合器（rocqwash wrapper/·适配席 rqadapt·20261031）

在役冻结件零改适配（各在飞席位实时引用·适配一律新文件 wrapper/）：本站把 nw8+ 洗形席
候批账「三、born／R4／对表／gate4／探针（⑤⑥⑦）」节里的三步 ad-hoc 手工循环——
  ⑤对表  names/mac_stmt_names.py  work/X.v --compare src/X.v   （N=N 有序全等断言）
  ⑥gate4 verify/gate4_comment_guard.py --file work/X.v          （头注五字段机检 v2.1 EXT）
  ⑦探针  seam/seam_probe.py --file work/X.v                     （W13 四机制指纹候选）
1:1 组合为一条站命令，全部直调冻结正本（subprocess `python3 -B <正本绝对路径>`），
零改冻结、判据零复制——三步红绿唯一判据源仍为各冻结正本自身退出码；本站只组合、
出站账、聚合退出码（对齐 scan_station.py「只指认＋透传」与 gate7_probe.sh
「判据零复制」适配纪律）。

域注记（双域各安其位·承 seam 补齐轮判定）：⑦＝W13 源面代际缝**指纹候选**探针
（E364 盲区律：命中=候选非定谳、0 命中=无候选出账非「无缝」——报清单不报清白），
供洗形②分诊 probe-first 与续洗台账驱动；它不是 gate7 提取执行闸
（ConstructiveWorld-Set scripts/gates/gate7_extract_run.py·仓外正本只读）的替代，
提取闸红绿仍走 wrapper/gate7_probe.sh 链。

九步洗形中的位置（承 seat_nw8 候批账小节编号）：⑤对表→⑥gate4→⑦探针，顺序固定；
--steps 可减步不可重排（组合器契约）。

用法：
  python3 wrapper/wash_station.py --washed work/X.v --baseline src/X.v [站级旗标]

站级旗标：
  --washed FILE            洗后件（⑤⑥⑦ 共同靶·必填）
  --baseline FILE          ⑤对表基准（洗前源·names 在步时必填）
  --root DIR               冻结正本仓根（默认＝本包装所在仓根）
  --steps LIST             步子集逗号分（names,gate4,probe·默认三步全开·可减不可重排）
  --include-let            ⑤会师口径（Let 计入）·1:1 透传 names --include-let
  --kinds LIST             ⑤kind 过滤·1:1 透传 names --kinds
  --expect-names N         ⑤计数断言·1:1 透传 names --expect
  --gate4-json PATH        ⑥gate4 --json 落盘（由冻结件自写·站只转交路径）
  --gate4-no-principle     ⑥关判定原则启发式（默认开·承 nw8 v2.1 EXT principle=on 口径）
  --gate4-length-fail      ⑥头注超标升格硬违规（默认复核级）
  --gate4-length-cap N     ⑥头注行数帽（默认 30＝冻结件默认）
  --probe-json PATH        ⑦探针 --json 落盘（站读其 hits 出站账）
  --probe-csv PATH         ⑦探针 --hits-csv 落盘
  --check-pin              三正本嵌记 md5 断言（20261031 适配时实测·任一不符 exit 2 不开步）
  --expect-names-md5 HEX / --expect-gate4-md5 HEX / --expect-probe-md5 HEX
                           外附 md5 断言（各自对应正本·可并用）
  --station-json PATH      站账 JSON（三步 rc/verdict/摘要·站唯一写面·缺省零写盘）
  --station-selftest       本站自检（九判·零写盘·不执行任何冻结件）
  -h / --help              本站帮助

退出码（聚合律·硬者胜）：0=三步全绿（⑤ rc=0 ∧ ⑥ rc=0 ∧ ⑦ rc=0——探针命中是候选
非失败·E364 律）；1=硬红（⑤ rc≠0 名面 N≠N／⑥ rc=1 硬违规／⑦ rc≠0 出账失败）；
2=复核级或站级（⑥ rc=2 REVIEW 项／站级用法错／md5 断言败——断言败绝不带病开步）；
9=文件或正本缺失（washed/baseline/任一正本·预检不过零开步）。

幂等律：本包装自身零写盘（不写正本、不写仓、不写临时）——唯一写面＝用户显式指定的
--station-json（及转交各冻结件的用户显式 --gate4-json/--probe-json/--probe-csv）。
子进程一律 `python3 -B`（禁 __pycache__ 落只读面）；站内禁套 cpu_guard（嵌套死锁
判例 seat_nw8——包裹义务在调用席，席位纪律同 nw8「零裸调」惯例）。

```

## 注释（逐字·按行序）

```
L71: # —— 冻结正本指认（相对仓根路径＋20261031 适配时实测嵌记 md5）——
L72: # 正本若经冻终权威改版，须由适配席对实盘重嵌记；本站不擅改正本。
L82: # ⑤⑥⑦ 固定序（可减不可重排）
L85: # 各冻结件退出码→站内 verdict 判表（判据零复制：verdict 唯一源自正本自身 rc）
L86: # 其余（2=不等 9=缺件）→ FAIL
L87: # nw8 口径：REVIEW=0 才算净
L88: # 命中=候选非失败（E364 律）；rc≠0=出账失败
L93: # 站账信息抽取（仅出账·永不覆判——verdict 唯一源自 rc；抽取失败=字段 null 如实出）
L286: # 判1 三正本在位（默认仓根）
L292: # 判2 三嵌记 32-hex 形制
L297: # 判3 --steps 解析：子集固定序（可减不可重排）＋未知步名拒
L312: # 判4 聚合律硬者胜
L323: # 判5 三判表
L331: # 判6 三步 cmd 装配（子进程直调形·[python, -B, 正本, ...透传]）
L344: # 判7 预检形制：baseline 依存＋同件拒绝
L353: # 判8 站账抽取：三冻结件样例行各抽出＋非匹配行如实 None
L370: # 判9 断言形制核：32-hex 正过、伪值拒
L427: # —— 预检：正本/靶件存在性（不过零开步·exit 9）——
L442: # —— 嵌记/外附 md5 断言（败→卡出 stderr·exit 2·绝不带病开步）——
L462: # —— 开步：⑤→⑥→⑦ 固定序·全步出账（组合器＝全账聚合·不短路）——
L489: # —— 站账信息抽取（出账·永不覆判）——
```

## 函数级 docstring（逐字）

### default_root（L134-134）

```
默认正本仓根＝本包装文件的上上级目录（wrapper/ 的父目录）。
```

### norm_hex（L143-143）

```
断言值形制核：剥空白/引号、小写；非 32 位 hex 回 None。
```

### parse_steps（L151-152）

```
--steps 解析：逗号分＋重复旗标合并；未知步名 raise ValueError；
    重排丢弃——恒归 ⑤⑥⑦ 固定序（组合器契约：可减不可重排）。
```

### check_inputs（L168-168）

```
预检形制：返回错误串或 None（文件存在性由 main 预检·此处只查组合形制）。
```

### child_argv（L179-179）

```
子进程直调形：[python, -B, 冻结正本绝对路径, ...透传参]。-B 禁 __pycache__。
```

### gate_step（L218-218）

```
判表查 verdict；表外 rc 一律 FAIL（fail-loud 不放水）。
```

### aggregate（L223-223）

```
聚合律·硬者胜：MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)。
```

### run_child（L231-231）

```
直调冻结件：子进程捕获→逐字回显（操作手可见性同 ad-hoc 循环）；rc 原样上呈。
```

### extract_info（L244-244）

```
站账信息抽取（出账用·永不覆判；抽不到=None 如实出）。
```

### station_selftest（L282-282）

```
本站自检九判（零写盘·不执行任何冻结件）。回 pass 布尔。
```

## 字符串常量（逐字·按行序）

```
L3: 'wash_station.py — 洗形⑤⑥⑦三步组合器（rocqwash wrapper/·适配席 rqadapt·20261031）\n\n在役冻结件零改适配（各在飞席位实时引用·适配一律新文件 wrapper/）：本站把 nw8+ 洗形席\n候批账「三、born／R4／对表／gate4／探针（⑤⑥⑦）」节里的三步 ad-hoc 手工循环——\n  ⑤对表  names/mac_stmt_names.py  work/X.v --compare src/X.v   （N=N 有序全等断言）\n  ⑥gate4 verify/gate4_comment_guard.py --file work/X.v          （头注五字段机检 v2.1 EXT）\n  ⑦探针  seam/seam_probe.py --file work/X.v                     （W13 四机制指纹候选）\n1:1 组合为一条站命令，全部直调冻结正本（subprocess `python3 -B <正本绝对路径>`），\n零改冻结、判据零复制——三步红绿唯一判据源仍为各冻结正本自身退出码；本站只组合、\n出站账、聚合退出码（对齐 scan_station.py「只指认＋透传」与 gate7_probe.sh\n「判据零复制」适配纪律）。\n\n域注记（双域各安其位·承 seam 补齐轮判定）：⑦＝W13 源面代际缝**指纹候选**探针\n（E364 盲区律：命中=候选非定谳、0 命中=无候选出账非「无缝」——报清单不报清白），\n供洗形②分诊 probe-first 与续洗台账驱动；它不是 gate7 提取执行闸\n（ConstructiveWorld-Set scripts/gates/gate7_extract_run.py·仓外正本只读）的替代，\n提取闸红绿仍走 wrapper/gate7_probe.sh 链。\n\n九步洗形中的位置（承 seat_nw8 候批账小节编号）：⑤对表→⑥gate4→⑦探针，顺序固定；\n--steps 可减步不可重排（组合器契约）。\n\n用法：\n  python3 wrapper/wash_station.py --washed work/X.v --baseline src/X.v [站级旗标]\n\n站级旗标：\n  --washed FILE            洗后件（⑤⑥⑦ 共同靶·必填）\n  --baseline FILE          ⑤对表基准（洗前源·names 在步时必填）\n  --root DIR               冻结正本仓根（默认＝本包装所在仓根）\n  --steps LIST             步子集逗号分（names,gate4,probe·默认三步全开·可减不可重排）\n  --include-let            ⑤会师口径（Let 计入）·1:1 透传 names --include-let\n  --kinds LIST             ⑤kind 过滤·1:1 透传 names --kinds\n  --expect-names N         ⑤计数断言·1:1 透传 names --expect\n  --gate4-json PATH        ⑥gate4 --json 落盘（由冻结件自写·站只转交路径）\n  --gate4-no-principle     ⑥关判定原则启发式（默认开·承 nw8 v2.1 EXT principle=on 口径）\n  --gate4-length-fail      ⑥头注超标升格硬违规（默认复核级）\n  --gate4-length-cap N     ⑥头注行数帽（默认 30＝冻结件默认）\n  --probe-json PATH        ⑦探针 --json 落盘（站读其 hits 出站账）\n  --probe-csv PATH         ⑦探针 --hits-csv 落盘\n  --check-pin              三正本嵌记 md5 断言（20261031 适配时实测·任一不符 exit 2 不开步）\n  --expect-names-md5 HEX / --expect-gate4-md5 HEX / --expect-probe-md5 HEX\n                           外附 md5 断言（各自对应正本·可并用）\n  --station-json PATH      站账 JSON（三步 rc/verdict/摘要·站唯一写面·缺省零写盘）\n  --station-selftest       本站自检（九判·零写盘·不执行任何冻结件）\n  -h / --help              本站帮助\n\n退出码（聚合律·硬者胜）：0=三步全绿（⑤ rc=0 ∧ ⑥ rc=0 ∧ ⑦ rc=0——探针命中是候选\n非失败·E364 律）；1=硬红（⑤ rc≠0 名面 N≠N／⑥ rc=1 硬违规／⑦ rc≠0 出账失败）；\n2=复核级或站级（⑥ rc=2 REVIEW 项／站级用法错／md5 断言败——断言败绝不带病开步）；\n9=文件或正本缺失（washed/baseline/任一正本·预检不过零开步）。\n\n幂等律：本包装自身零写盘（不写正本、不写仓、不写临时）——唯一写面＝用户显式指定的\n--station-json（及转交各冻结件的用户显式 --gate4-json/--probe-json/--probe-csv）。\n子进程一律 `python3 -B`（禁 __pycache__ 落只读面）；站内禁套 cpu_guard（嵌套死锁\n判例 seat_nw8——包裹义务在调用席，席位纪律同 nw8「零裸调」惯例）。\n'
L81: '20261031 rqadapt 适配时嵌记'
L83: '⑤对表'
L83: '⑦探针'
L94: '断言 (\\d+)=(\\d+) 有序全等 : (PASS|FAIL)'
L97: '件数=(\\d+)\\s+PASS=(\\d+)\\s+FAIL=(\\d+)\\s+REVIEW\\(人工复核\\)=(\\d+)\\s+UNREADABLE=(\\d+)'
L98: '^TOTAL: (\\d+) 候选'
L100: 'wash_station — 洗形⑤⑥⑦三步组合器（wrapper/）\n\n用法 Usage:\n  python3 wrapper/wash_station.py --washed WORK.v --baseline SRC.v [站级旗标]\n\n站级旗标 Station flags:\n  --washed FILE         洗后件（三步共同靶·必填）\n  --baseline FILE       ⑤对表基准（names 在步时必填）\n  --root DIR            冻结正本仓根（默认＝本包装所在仓根）\n  --steps LIST          步子集逗号分（names,gate4,probe·默认全开·可减不可重排）\n  --include-let/--kinds LIST/--expect-names N     ⑤透传 names\n  --gate4-json PATH / --gate4-no-principle / --gate4-length-fail / --gate4-length-cap N\n                        ⑥透传 gate4\n  --probe-json PATH / --probe-csv PATH            ⑦透传 seam_probe\n  --check-pin           三正本嵌记 md5 断言（20261031）\n  --expect-names-md5/--expect-gate4-md5/--expect-probe-md5 HEX   外附断言\n  --station-json PATH   站账 JSON（站唯一写面·缺省零写盘）\n  --station-selftest    本站自检（九判·零写盘·不执行冻结件）\n  -h / --help           本帮助\n\n退出码: 0=三步全绿  1=硬红（对表不等/gate4 硬违/探针出账败）  2=REVIEW/站级用法·断言败\n        9=文件或正本缺失\n'
L134: '默认正本仓根＝本包装文件的上上级目录（wrapper/ 的父目录）。'
L143: '断言值形制核：剥空白/引号、小写；非 32 位 hex 回 None。'
L151: '--steps 解析：逗号分＋重复旗标合并；未知步名 raise ValueError；\n    重排丢弃——恒归 ⑤⑥⑦ 固定序（组合器契约：可减不可重排）。'
L160: '未知步名 %r（合法：names,gate4,probe）'
L163: '--steps 解析为空'
L168: '预检形制：返回错误串或 None（文件存在性由 main 预检·此处只查组合形制）。'
L170: '--washed 必填（三步共同靶）'
L172: '--baseline 必填（⑤对表基准·names 在步时）'
L174: '洗后件与对表基准同件（对表退化为恒真·拒绝）：%s'
L179: '子进程直调形：[python, -B, 冻结正本绝对路径, ...透传参]。-B 禁 __pycache__。'
L218: '判表查 verdict；表外 rc 一律 FAIL（fail-loud 不放水）。'
L223: '聚合律·硬者胜：MISSING(9) > FAIL(1) > REVIEW(2) > PASS(0)。'
L231: '直调冻结件：子进程捕获→逐字回显（操作手可见性同 ad-hoc 循环）；rc 原样上呈。'
L244: '站账信息抽取（出账用·永不覆判；抽不到=None 如实出）。'
L282: '本站自检九判（零写盘·不执行任何冻结件）。回 pass 布尔。'
L289: '  judge1 三正本在位(default root):'
L294: '  judge2 三嵌记 32-hex 形制:'
L303: '  judge3 steps 子集固定序:'
L309: '  judge3b 未知步名拒:'
L319: '  judge4 聚合律硬者胜:'
L328: '  judge5 判表 names/gate4/probe:'
L341: '  judge6 cmd 装配:'
L350: '  judge7 预检形制:'
L354: 'file: x\nmd5: ab\ntotal: 7  let_skipped: 0\n断言 7=7 有序全等 : PASS'
L355: '[gate4ext] v2.1 扫描时点=T  件数=1  PASS=1  FAIL=0  REVIEW(人工复核)=0  UNREADABLE=0  length_cap=30(review)  principle=on  deep_files=0'
L357: 'TOTAL: 3 候选'
L361: '没有可抽行'
L367: '  judge8 站账抽取正/负:'
L373: '  judge9 断言形制核正过伪拒:'
L387: '洗形⑤⑥⑦三步组合器（直调冻结件·零改冻结）'
L389: '洗后件（三步共同靶）'
L390: '⑤对表基准（洗前源）'
L391: '冻结正本仓根（默认=本包装所在仓根）'
L393: '步子集逗号分（names,gate4,probe·默认全开·可减不可重排）'
L394: '⑤会师口径（Let 计入）'
L395: '⑤kind 过滤（透传 names --kinds）'
L396: '⑤计数断言（透传 --expect）'
L397: '⑥gate4 --json 落盘路径'
L398: '⑥关判定原则启发式'
L399: '⑥头注超标升格硬违规'
L400: '⑥头注行数帽（默认 30）'
L401: '⑦探针 --json 落盘路径'
L402: '⑦探针 --hits-csv 落盘路径'
L403: '三正本嵌记 md5 断言'
L407: '站账 JSON（站唯一写面）'
L408: '本站自检九判'
L413: 'WASH-STATION-SELFTEST (wrapper 自身九判·零写盘·不执行冻结件):'
L420: 'wash_station: 站级用法错: %s'
L424: 'wash_station: 站级用法错: %s'
L433: 'wash_station: 正本缺失: %s（%s·于仓根 %s）'
L439: 'wash_station: 文件缺失: %s=%s'
L456: 'wash_station: md5 断言不符 [%s] want=%s actual=%s'
L458: 'wash_station: 断言败·不带病开步（正本若经冻终权威改版须由适配席重嵌记）'
L463: '== wash_station 洗形⑤⑥⑦ 三步组合（%s）=='
L465: '—（names 不在步）'
L482: '-- %s 直调 %s'
L501: '--- 站账：steps=%s'
L506: '（断言 %s·total=%s）'
L509: '（件数=%d PASS=%d FAIL=%d REVIEW=%d）'
L512: '（TOTAL %d 候选·E364 候选非定谳）'
```
