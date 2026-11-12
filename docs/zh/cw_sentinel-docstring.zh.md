# cw_sentinel.py 模块 docstring 中文原档（留档）

- 源文件：`tools/cw_sentinel.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/cw_sentinel.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

cw_sentinel.py — 实时动态哨（rocqwash tools/·v37 用户令：配合工作流实时动态
提供清洗、洗形、排障、疏通堵塞——哨是三路信号源的巡检事件流·判类与链根全编排
既有引擎·零新引擎零重造·20261111 入账）

三路信号源（可组合·至少一路）：
  ① CI 路＝--watch-repo ORG/REPO [--branch B]...（可重复多组）：
       GET /repos/{repo}/actions/runs?per_page=30（RUNS_QUERY 承 pushci.py:141
       同款惯例；token 取 ~/.netrc machine github.com 行第 6 列 password——
       netrc_token 与 ci_triage.py:226 同款副本·tools/ 无包结构故随 pushci
       先例各带一份·--netrc 参数化）→ 新 completed run（--state-file 记 seen
       run id·幂等）→ 哨取 jobs（GET .../runs/{id}/jobs?per_page=100&page=1，
       落盘 tmp）→ subprocess ci_triage --offline（pushci.py:969 run_triage
       injector 同款「真子进程真判类·零网络」）→ run 级 family/action 取自
       rocqwash-ci-triage/1 报告 → family≠none 出事件
       {kind:ci-red, repo, run, family, action}。判类谱五族＋绿炉全权在
       ci_triage（20261110 判类谱·ci_triage.py docstring 判类序）·哨不判。
  ② 本地账路＝--watch-ledgers DIR：
       新 probe/ledger JSON 落盘（mtime+名字 seen·同件 mtime/size 变亦视新）
       → subprocess chain_graph.py 新件 --json tmp（chain_graph.py:21 CLI）→
       top_order 首名即 TOP 链根 → 事件 {kind:blocking, top_root, dependents}
       （附 n 与 self 可洗性三分——chain_graph.py:88 build_graph 判例）。
  ③ 本地堵路＝--watch-buildlog FILE：
       tail 增量 grep（字节 offset 记 state·只认完整行防半行误报）→ 词面
       BUILD-FAIL／EXIT=134（判类谱 C 环境断链 token·ci_triage.py:118）／
       Error:（判类谱 A 内容红 token·ci_triage.py:108）→ 事件
       {kind:build-signal, hits[]}。日志文件未在卷＝编译未开写·零事件非红
       （report 响亮注记 present=false·非静默）。

事件流：--emit FILE（JSONL append·逐行 flush+fsync）＋stdout 镜像（响亮）。
事件行 schema=rocqwash-sentinel-event/1·键 sort_keys·行序＝产出序·seq 事件流
内单调（--emit 在位时以本体＋轮转代现有行数为基跨进程续号·缺省时进程内单调）
——消费方按 seq 排序即恢复全局序。ts 由 time 钟出·--sleep-scale 0 时关 ts
（selftest 确定性依赖）·事件以 note「ts=off」注记。
JSONL 轮转（--emit-max-bytes N·长驻盘面防无界）：追加前查——emit 本体现有
字节＋新行字节＞N → 先轮转再追加：FILE.1→FILE.2（旧 FILE.2 覆盖弃·保留 2
代）→FILE→FILE.1→新 FILE 空。单行本身超 N＝行不可分割·空档直写（轮转后
仍可能单行超帽·下轮追加前即再轮转）；轮转走 stdout 响亮注记＋report
emit_rotations 计数·rename 失败 → 9。seq 跨代续号（本体＋.1/.2 行数和为基
——轮转代同属一条事件流·按 seq 排序跨代恢复全局序）。

--on-red 'CMD 模板'：{family}／{run}／{repo} 占位替换（事件字段直替·缺字段
替空串）→ subprocess shell 执行（超时帽 60s·rc≠0/超时响亮入 actions 账与
stdout·不改哨退出码——on-red 是旁路动作非器面）。须 --emit（旁路动作必伴
随事件流落盘——触发证据与动作账可审计·无 --emit → 2·与 --on-red-preset
同款守卫·v41 矩阵判据转正）。缺省无＝report-only·**零动作是缺省**（承
cure_applier 干跑缺省同纪律）。

--on-red-preset NAME：红事件预设动作（**可重复＝链式**·见下）——预设即模板
sugar：展开为内部命令模板后走与 --on-red **同一执行器**（60s 帽·rc≠0/超时
响亮入 actions 账·不改哨退出码·占位替换复用现有 --on-red 路径·零新执行
路径）。与 --on-red 互斥（同给 rc=2 fail-loud·禁静默择一——「preset 优先」
＝preset 在场即占 on-red 动作槽·同给即用法歧义报错）。预设五件
（ON_RED_PRESETS 表·程序路径按哨自身相对定位承 TOOLS_DIR 先例）：
  unclog＝python3 -B tools/unclog.py --src {src} --json {emit_dir}/unclog_{run}.json
    （**--apply 缺省不加＝疏通只干跑·人审后再 apply——自动接驳缺省干跑是
    铁律**）
  pushci＝python3 -B tools/pushci.py --repo-path {repo_path} --branch {branch}
    --json {emit_dir}/pushci_{run}.json --dry-run（--dry-run 缺省＝只打计划
    零副作用）
  wash-shape＝python3 -B tools/wash_shape.py --dir {src} --json
    {emit_dir}/wash_shape_{run}.json（**--apply 不入模板＝洗形只出 plan·
    plan 零写盘·人审后再 apply——缺省干跑同铁律**）
  triage＝python3 -B tools/ci_triage.py --repo {repo} --run {run} --json
    {emit_dir}/triage_{run}.json（红事件自带 repo/run 事件直替流入＝对本
    红 run 复诊重判类）
  cw-doctor＝python3 -B tools/cw_doctor.py --json {emit_dir}/doctor_{run}.json
    （零参面＝全缺省体检）
必传参数表（PRESET_REQUIRED_ARGS·声明化）：{unclog:[src]·pushci:[repo_path,
branch]·wash-shape:[src]·triage:[repo,run]·cw-doctor:[]}。占位两族：静态族
{src}/{repo_path}/{branch} 展开时由 --on-red-arg K=V 实替；动态族
{family}/{run}/{repo}（＝fire_on_red 事件直替既有键）原样留给事件直替
（缺字段替空串·既有语义）。必传守卫逐键判（同款 fail-loud）：--on-red-arg
已给即静态实替·未给而键属动态族即事件直替（triage 的 repo/run 即此——
红事件出值·展开期无可查非缺）·二者皆非 → 缺 rc=2；无 '='/空 K·V/重键/
未知键（键不在参数面——链式＝全链参数面并集）/孤儿 --on-red-arg → 2；
{emit_dir} 取 --emit 所在目录（预设出账与事件流同盘·--emit 必给否则 2）。
预设器件缺失 → 9。
链式：--on-red-preset 可重复（如 --on-red-preset unclog --on-red-preset
triage）＝链式同触发——按给定序逐个展开·红事件逐件**按序执行·一败续行**
（某条 rc≠0/超时只响亮入账不裁停后条·旁路动作非器面·哨退出码不变）；
actions 账每条模板一笔（链 N 条=N 笔·schema 同单条）；--on-red-arg 命名
空间全链共享（未知键判全链并集面·必传缺逐预设判）。report on_red_preset
＝单预设名串·链式名列表（按给定序）。

双模：--once（单轮巡检出账退出·工作流步骤用）｜--loop --interval S（长驻·
JSONL 追加·工作流后台 bash 任务用）·--max-rounds N 轮帽（0=无限·selftest
矢量⑤三轮序贯依赖）。

韧性层（v37·承任务书①②）：真 urllib CI GET 403/429/5xx → 指数退避重试
（--retry-max 缺省 3·base 2s·Retry-After 秒数头优先替当次延迟·HTTP-date 形
不猜落回指数；耗尽原错 9·4xx 语义面 401/404 等不重试；延迟计算抽公共件
tools/_http_backoff.py 纯函数·三器共享·同目录 sys.path 注入 import·无
__init__ 包结构；injector canned 路径零真网络一律不重试——离线可测铁律）。
子进程防挂＝--subproc-timeout S（缺省 120s）：ci_triage／chain_graph run_py
调用超时=子进程杀＋fail-loud 9 报调用名（--timeout 另承 HTTP 单请求超时
缺省 30——两钟不同物不并铃）；on-red 旁路动作（含 --on-red-preset 展开·
同一执行器）仍承 ON_RED_TIMEOUT 60s 帽不改哨退出码（v37 既约口径不动）。

韧性层 v51（承任务书①②·哨长驻 round10 IncompleteRead 崩器修——更新账 v50
在案＝http.client.IncompleteRead(371261 read, 72721 expected) 自 api_get_json
resp.read() 抛出·loop 全驻崩：v38 backoff 只护 HTTPError 状态码面·传输层
断流类不护＝器债第二类）：①传输层瞬态类（TRANSIENT_TRANSPORT_ERRORS＝
IncompleteRead／RemoteDisconnected／BadStatusLine／ConnectionError 全族／
socket.timeout·区别于 HTTPError 状态码类）→ 有界重试（--net-retries 缺省
3 发·退避 5s/15s/45s＝net_backoff_delays 纯函数·继承 v38 backoff 语义＝
有界表按 attempt 取延迟·每发全新 Request+urlopen 半读残体弃）；重试耗尽才
上抛 9（fail-loud 保持·上抛后由②兜底）；非瞬态（HTTPError 状态码语义面/
URLError 连接建立面/其余未知异常）零重试原样上抛——禁吞非瞬态错误。
②loop 层兜底（宁跳轮不崩驻）：poll_round 逐信号源经 poll_source_guarded
异常捕获（loop 模式限定）→ 该源本轮 skip＋事件流 {kind:source-error} 注记
（响亮非静默）·下轮再试——异常路径 seen 幂等账未记＝下轮自然重报（宁重复
不丢件判例同源）；once 模式不兜底直通 run_sentry fail-loud rc 9（工作流步骤
语义保持）。

退出码：0=巡检完成（红是数据非器红·响亮 stdout）；2=用法错（缺模式/双模
同给/三源全缺/--branch 先于 --watch-repo/repo 形坏/负参/once 带 loop 专属
参/--on-red-preset 与 --on-red 同给/preset 不识别/预设参数缺·重·形坏
〔链式未知键判全链并集面〕/--emit 缺/--on-red 缺 --emit（plain 与 preset
双路同守卫）/--on-red-arg 孤儿/
--emit-max-bytes 须与 --emit 同给或 N<1/
--rebuild-state 缺 --state-file）；9=信号源不可达（CI HTTP 4xx/5xx·传输层瞬断重试耗尽〔--net-retries〕·netrc 缺·
token 空·runs/jobs 形坏·预设器件缺·
injector 缺失/形坏/canned 未覆盖·ledgers 目录缺·state 形坏·ci_triage/
chain_graph 子进程 rc≠0·子进程超时被杀〔--subproc-timeout〕·事件流轮转
rename 失败）。
--selftest：0=全过／2=断言失败。

report schema（--json·每轮覆盖写·rocqwash-sentinel/1）：
  {"schema","mode","round","sources"{ci[],ledgers{},buildlog{}},"events"[],
   "actions"[](on-red 执行账),"state_file"?,"state_rebuilt"?,"interval"?,
   "sleep_scale","ts_enabled","injector"?,"on_red_preset"?(单预设串·链式
   列表),"emit_max_bytes"?,"emit_rotations"?}
  events/actions 元素与事件流逐字节同源（确定性：--sleep-scale 0 时同输入
  重跑字节级恒同）。

injector 文件（--injector·schema=rocqwash-sentinel-injector/1）＝canned API
响应表·离线可测（铁律④零真网络）：
  {"schema":"rocqwash-sentinel-injector/1","responses":[
     {"url_contains":"/actions/runs?","status":200,"body":{...workflow_runs...}},
     {"url_contains":"/runs/178/jobs","status":200,"body":{...jobs...}}]}
  按序首中即用·可循环复用（哨轮询幂等语义·非 pushci steps 形按序耗尽）；
  未命中 fail-loud 9——canned 表须全覆盖·**绝不静默走真网络**。runs body
  同 GitHub API 真形 {"total_count":N,"workflow_runs":[...]}（兼收 "runs" 键
  承 pushci watch 证据形·pushci.py:880）。

state 文件（--state-file·schema=rocqwash-sentinel-state/1）：seen 幂等持久层
  {"repos":{"ORG/REPO":{"seen_runs":{"<id>":{conclusion,run_number,family}}}},
   "ledgers":{"<名>":{"mtime_ns","size"}},"buildlogs":{"<路径>":{"offset"}}}
  缺省 None=内存态（once 单轮无跨轮幂等·loop 须给）。
崩溃恢复语义（禁静默重建）：state 损坏（JSON 解析失败/键形坏）→ fail-loud 9
  红拒——器不吞不重建（seen 是幂等账·静默重建＝红事件重报面失守·原件原样
  不动）；恢复唯二路＝人工删件（下轮零态起步）或 --rebuild-state 显式重建
  （弃既有 seen 从零起·stdout 响亮 STATE-REBUILD 注记＋report
  state_rebuilt=true；须与 --state-file 同给否则 rc=2——无 state 即无物可
  重建）。

编排律（承 v37 用户令⑤）：ci_triage／chain_graph 全 subprocess 直调（pushci
_run_py 同款·py:591——纯逻辑零编译故不经 cpu_guard·真编译才须 guard 包裹，
probe_engine.py:10 判例）；哨自身零编译零网络（injector 缺席线上模式除外）。

诚实律（承 CONTRIBUTING §0）：只认机械证据；红是数据非器红（巡检 exit 0）；
fail-loud 禁静默降级（源不可达 9·injector 未覆盖 9·子进程 rc≠0 9）；零
第三方依赖（纯 stdlib）；--json 落盘 sort_keys·--sleep-scale 0 同输入重跑
字节级恒同；零硬编码绝对路径（--netrc/--state-file/--emit/--injector 全
参数化·引擎件按哨自身相对定位承 pushci TOOLS_DIR 先例）。
