# probe_engine.py 模块 docstring 中文原档（留档）

- 源文件：wash/probe_engine.py 模块 docstring（英文化前的中文原文，程序化逐字提取（ast.get_docstring），未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见 wash/probe_engine.py 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---
probe_engine.py — 批量闭包相容探针引擎（rocqwash wash/·v30 实战判例工具化·
承 seat_wash13/probe_batch.py 1:1 泛化·20261103 入账）

探针法（闭包相容判定）：把候选件 `<件名>.v` 从源树 cp 入世界目录（世界含播种
.vo 闭包·只读语义），在世界 cwd 直接 `rocq c` 编译一发。退出码即判据：
  rc=0  Require 闭包可装载＋语句面可 elaboration ＝ 相容（可洗可落）；
  rc!=0 记红因原文（世界接口代差/缺依赖族候选）。
一切真编译必经 cpu_guard 包裹（--guard 给出即包裹），退出码无管道真取
（subprocess returncode 直读）。探针后清场：候选件五件产物
(.v/.vo/.glob/.vos/.vok) 移出世界入 --logdir 留证（世界保持播种态纯度）。

输入候选清单 TSV（首行表头·列名定位不按列序）：
  必需列  件名  md5          （md5＝枚举时源件指纹·逐件实测回填 md5_match）
  可选列  RED  行数          （RED＝语句面 RED 站数·rc0 分流必需；缺列时 rc0
                              不作 washable/born-clean 三分·如实出 RC0）

rc 分流（verdict 字段）：
  rc0 + RED>0  → WASHABLE     （闭包相容＋语句面有 RED＝洗形候选）
  rc0 + RED=0  → BORN-CLEAN   （闭包相容＋语句面零 RED＝born-clean 落位候选）
  rc0 + RED缺  → RC0          （RED 未申报·三分不可判·报清单不报清白）
  rc1          → RED-<红因>   （regex 分类，见下）
  rc=124       → TIMEOUT      （--timeout 到点·subprocess.TimeoutExpired）
  源件缺失     → NO-SRC       （--src 下无 <件名>.v·不编译如实出账）

红因分类（rc1·按序首中即断·大小写不敏感）：
  MISSING_LIB  /unable to locate library|cannot find library/   （缺库型·
                捕获库名入 missing 字段）
  ILLEGAL_APP  /illegal application/                             （代差型）
  NO_SUBTERM   /no subterm matching/                             （代差型）
  FACE         /expected to have type|is not convertible/        （面错·载体
                接口代差错配族）
  其余 rc1     → OTHER（有红因原文无分类命中）／UNKNOWN（零红因原文）

幂等（CONTRIBUTING §0 律三）：--out 已在盘时默认 resume——候选件与既有记录
md5 同 ⇒ skip 不重炮；--fresh 推倒重探。同候选集重跑产出同账（记录无时间戳/
无绝对路径·sort_keys 落盘·字节级可复现）。

并行（--jobs K·缺省 1＝逐件串行·零行为漂移）：
  K>1 时候选件分片 concurrent.futures.ThreadPool 并行探针（真编译仍逐件经
  --guard cpu_guard 包裹·guard FRONT 档自带并发钳位——同 -Reg 登记表下 FRONT/
  MID 槽位天然限流·K 超出槽位的排队件 MaxWaitSec 到点降 BACK 档放行不占 FRONT
  全速位）。台账记录序恒按候选典序（主线程按典序收账落盘·并行完成序不改变
  输出序·确定性铁律；sort_keys 落盘同输入重跑字节恒同）；md5_match/verdict
  逻辑零改；per-件 build log 仍独立落 logdir（<件名>.stderr.log 逐件异名互不
  撞）。resume 幂等语义不变（skip 先行·余件入池）。候选重名＋K>1 → fail-loud
  rc=2（同名件并发 copyfile/编译清场世界写竞争禁入）。
  ⚠ 温控警示（显著·注记不强制·用户自裁）：K>1 时机内多 rocqworker 并发＝热
  负载↑——机内同时活跃编译进程即 K 路（无 --guard 时零钳位全速并发·尤须自
  裁）；--jobs 与 --guard 同给时建议 K≤2（guard FRONT 档缺省 2 槽·K 超出部分
  排队降档·热负载受钳但仍在机内）。

用法（全部路径参数化·零硬编码）：
  python3 wash/probe_engine.py --candidates cands.tsv --src <源树> --world <世界目录>       --out probe_ledger.json --logdir probe_logs/       [--rocq-cmd 'rocq c -Q . "" {name}.v'] [--guard tools/cpu_guard.sh        --guard-reg /tmp/cw_reg_probe_engine --guard-front 0 --guard-mid 1        --guard-maxwait 600] [--timeout 1500] [--ulimit-stack 65532]       [--jobs 1] [--fresh]
  python3 wash/probe_engine.py --selftest

退出码：0=批完成台账落盘（rc1 候选是探针产出数据非器红·计数响亮入 stdout）；
2=用法错（--help rc=0／缺必需参数／--jobs<1／K>1 候选重名）；9=--candidates/
--src/--world/--guard 路径缺失；1=--selftest 红处。台账 schema=
rocqwash-probe-ledger/1。
