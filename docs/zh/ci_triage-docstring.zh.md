# ci_triage.py 模块 docstring 中文原档（留档）

- 源文件：`tools/ci_triage.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/ci_triage.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

ci_triage.py — CI 红炉分诊器（rocqwash tools/·20261110 判类谱代码化·六幕实战判例工具化）

[判类谱]（20261110 六幕实战判例·全部代码化；五族＋绿炉）：
  A 内容红 A-content-red＝失败步指向具体件：Build/COQCHK 出 Error:/FAIL/
    ORDER-MISSING/Axioms 非零（COQCHK_EXIT≠0·公理总数≠0）→ action=fix-content。
  B 网络窗 B-netred＝checkout unable to access / port 443 / Connection was reset；
    上传步 ENOTFOUND / Upload progress stalled；403 Forbidden: job is completed
    （中断连坐形：cancelled 有步骤零红步同归此族）→ action=rerun-after-stable-window。
  C 环境断链 C-toolchain-break＝批量 EXIT=134 / Abort trap: 6（SKIP 件全过）。
    log 直证：日志抓到 EXIT=134/Abort trap: 6 → 该 job 即 C；run 级批量判：
    同形内容红（A）≥2 件 → 全数升 C（EXIT=134 日志确证建议 --logs）
    → action=restore-toolchain。
  D 排队资源墙 D-queue-wall＝cancelled 且 steps=[]（job 零步骤·logs 404）
    → action=queue-etiquette。
  E coqchk-skipped 签名 E-coqchk-skipped＝上传步红＋coqchk 步 skipped（＋gate2
    GATE-BANNER-ABSENT 日志确证）＝B 族变体·勿当内容红
    → action=rerun-after-stable-window。
  E 变体（gate2-only 连坐形·banner-absent 限形·20261112 Main retro 六事件证据
    人工指认入谱＋20261112 复核台账 token 二分限形）＝红步集 ⊆ {gate2＋上传族}
    且纯 gate2 红步在册（gate2 名非上传名——防「Upload artifact (gate2 ledger)」
    gate2 子串词面搭便误吞上传红）·前置 build/coqchk 非 content 红，结论位校验
    （复核台账 §四-2 token 二分·dump 行滤除后真执行 token 为准）：
    ①GATE2-ATTEST-RED/判定=CLEAN 真执行 token 在＝认证态红形（run#10 判例：
    coqchk success 40398s·parser CLEAN 公理=0·R4 覆盖划分破）→ E 变体不成立·
    留 UNRECOGNIZED 不充谱（人工指认优先）；②coqchk 步 success＝完走·非
    「coqchk 产物缺」连坐机理（分叉判据件二·无日志时器面唯一旁证）→ 同留
    UNRECOGNIZED；③GATE-BANNER-ABSENT 真执行行在＝banner-absent 连坐 E
    （run#7/8/20/26 四发·log 确证第三件入账）；④无日志且 coqchk 未完走＝
    步名规则维持 E（banner token 未确证·如实注记）。
    → family=E-coqchk-skipped·action=rerun-after-stable-window。
    判类谱序 UNRECOGNIZED>C>A>E>B>D 不动（E 变体在 E 内·出处六事件中
    #7/#8/#20/#26 四发 banner-absent 形入谱·#10 认证态形转正留 UNREC＝
    复核判词·#3 runner 失联形仍谱外不充谱）。
  绿炉＝无红件 → family=none·action=watch-only。在飞/条件跳过（conclusion 空或
    skipped/neutral）同记 none·但 evidence 显式注记「判类暂缓非绿判」·绝不充绿。
  判类谱外红形 → family=UNRECOGNIZED·action=watch-only（不充谱·run 级判类序
    置顶·人工指认优先·fail-loud）。

  判类序（逐 job·先到先归）：绿/在飞/条件跳过 → D（cancelled·零步骤）→ B 连坐形
  （cancelled·有步骤零红步）→ log 直证 C（EXIT=134/Abort trap: 6）→ E 签名
  （上传红＋coqchk skipped）→ E 变体（gate2-only 连坐：红步集 ⊆ {gate2+上传族}·
  build/coqchk 非 content 红·banner-absent 限形——认证态 token/coqchk 完走形
  留 UNRECOGNIZED 不充谱·复核台账 token 二分）→ log B → 步名 B
  （checkout/upload/artifact/cache/…）→ log A（Error:/FAIL/ORDER-MISSING/
  COQCHK_EXIT≠0/公理总数≠0）→ 步名 A（build/compile/coqchk/…）→ UNRECOGNIZED。

用途：
  对 GitHub Actions run 的 jobs 做红/绿分诊：打印步级表（步名/status/conclusion/
  起止/时长秒），逐 job 归族（family）并给处置（action）；--baseline-seconds 给
  同 sync 历史时长值则出倍数对表（判例 coqchk 561s vs 7480s=13.3x＝本机挤压
  嫌疑非卡死）。红是数据非器红：分诊恒 exit 0 响亮出账。

用法（路径全参数化·零硬编码绝对路径）：
  线上模式（只读 GET·token 取 ~/.netrc machine github.com 行第 6 列 password，
  --netrc 可换路径）：
    python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs] [--netrc PATH]
        [--baseline-seconds N] [--baseline-step NAME] [--timeout S]
        [--retry-max N] [--json out.json]
    （GET /repos/{repo}/actions/runs/{run}/jobs?per_page=100&page=N 分页到齐；
      --logs 时对红件再 GET /repos/{repo}/actions/jobs/{job}/logs 抓关键行入证据：
      COQCHK_EXIT/COQCHK_ALL_PASS/判定=CLEAN/公理总数/GATE-BANNER-ABSENT/
      GATE2-ATTEST-RED/R4 覆盖划分/appendix 缺/ENOTFOUND/ORDER-MISSING/
      EXIT=134 等（20261112 复核台账 §三候选 token 增补：GATE2-ATTEST-RED/
      R4 覆盖划分/appendix 缺 三枚新增·判定=CLEAN/公理总数= 两枚开工态已在册
      咬合复核——五 token 全员在册）；dump 行滤除（复核台账 §三-2 证据陷阱）：
      evidence 收集与判据 token 检索前先滤青色脚本回显（[36;1m）与
      ##[group]/##[endgroup] 组指令行——脚本回显非真执行行·「log 确证」须为
      真执行行（滤除规则如实注记：命中行数入 evidence）；--no-dump-filter 可关
      （关闭时陷阱形原样入证据·run 级响亮注记）；取日志两跳形（20261112 415 修法·
      实测定）：第一跳 Accept: application/vnd.github+json（text/plain 现 415 拒）
      禁自动重定向 GET → 302 Location 签名 URL；第二跳对签名 URL 零 Authorization
      再 GET（签名自带凭据——带 token 转发 403 Azure AuthenticationFailed·实测）；
      logs GET 404/403/415 本身入证据——403 Forbidden: job is completed 即判类谱
      B 中断连坐 token·重试耗尽后原码照旧入证据）
  韧性层（v37 限流退避·承任务书①）：线上 GET 遇 403/429/5xx → 指数退避重试
    （base 2s·帽 --retry-max 缺省 3·Retry-After 秒数头尊重——可解析秒数替当
    次指数延迟·HTTP-date 形不猜落回指数；重试耗尽或 4xx 语义面（401/404 等）
    原错原样上抛 9 不重试）。延迟计算抽公共件 tools/_http_backoff.py 纯函数
    backoff_delays()/parse_retry_after()/is_retry_status()（三器共享·同目录
    sys.path 注入 import·无 __init__ 包结构）。
  离线模式（selftest 与断网环境走此路·零网络）：
    python3 tools/ci_triage.py --offline JOBS.json [--baseline-seconds N ...]
        [--no-dump-filter] [--json out.json]
    （canned jobs JSON 同 API 真形 {"total_count":N,"jobs":[...]}＋可选顶层
      job_logs 扩展位 {"<job_id>": "日志文本"}＝离线日志注入专用·非 API 真形
      如实注记·复核台账 token 二分验收判的 canned 通路·形坏 fail-loud 9；
      fixtures 见 tests/fixtures/ci_triage_*.json 六件套＋Main 形 coq93
      真形一件 ci_triage_main_coq93.json（v48 勘形小改①·单 Windows job
      「Main CI 9.3」16 步真名·绿样张）＋gate2-only 真形两件
      ci_triage_gate2_only_{cancelled,failure}.json（20261112 retro 台账
      run#7/#10 逐字段誊录＋复核台账真执行行 canned job_logs 誊录）＝九件）
  python3 tools/ci_triage.py --selftest

退出码：0=分诊完成（红是数据非器红·响亮 stdout）；2=用法错（参数缺失/互斥/
  形不对）；9=API/文件不可达或形坏（netrc 缺失·token 空·HTTP 4xx/5xx·连接
  失败·jobs 文件缺失或 JSON 形坏·时间戳形不识别）。--selftest：0=全过／2=断言
  失败。

report schema（--json）= rocqwash-ci-triage/1：
  {"schema","mode","source",
   "run"{repo,run_id,total_count,jobs_total,red_job_ids,family,action,evidence},
   "jobs"[{id,name,status,conclusion,started_at,completed_at,duration_sec,
     "steps"[{number,name,status,conclusion,started_at,completed_at,duration_sec}],
     "classification"{family,action,evidence,red_steps}}],
   "family","action","evidence","baseline_note"?}
  family ∈ A-content-red / B-netred / C-toolchain-break / D-queue-wall /
    E-coqchk-skipped / none / UNRECOGNIZED；
  action ∈ rerun-after-stable-window / fix-content / restore-toolchain /
    queue-etiquette / watch-only；
  baseline_note（仅 --baseline-seconds 时在册）：{applied,step_query,
    baseline_seconds,matched?,current_seconds?,ratio?,note|reason}
    （applied=false＝基线步未在场或未完·响亮注记非静默·rc 仍 0）。

诚实律（承 CONTRIBUTING §0）：只认机械证据；判类谱外不充谱；红是数据非器红
  （分诊 exit 0）；--json 落盘 sorted+sort_keys·同输入重跑字节级恒同；stdout 全
  数据驱动（零 now() 零随机）；零第三方依赖（纯 stdlib）；fail-loud 禁静默降级。
