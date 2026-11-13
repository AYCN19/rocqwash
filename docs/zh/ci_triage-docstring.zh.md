# tools/ci_triage.py 中文原面留档（archive）


- 源文件：`tools/ci_triage.py`（英化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 prose 全文移此留档而非删除；英文正本见
  `tools/ci_triage.py`。本文件为历史存档（annotation-standard-v1.0 §5.2），内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。
- 覆盖面：模块 docstring／函数级 docstring／注释／CLI 输出字面（ast＋tokenize 逐字）。

## 模块 docstring（逐字）

```
ci_triage.py — failing-build triage tool for rocqwash CI (tools/).

[Classification taxonomy] — five failure families plus the all-passing state:
  A content failure (A-content-red) = the failing step points at concrete
    content: Build/COQCHK emits Error:/FAIL/ORDER-MISSING, or COQCHK exits
    nonzero (COQCHK_EXIT≠0, nonzero axiom total) → action=fix-content.
  B network window (B-netred) = checkout unable to access / port 443 /
    Connection was reset; upload-step ENOTFOUND / Upload progress stalled;
    403 Forbidden: job is completed. (Cancellation cascade: a cancelled job
    that has steps but zero failed steps also lands here.)
    → action=rerun-after-stable-window.
  C toolchain break (C-toolchain-break) = wholesale EXIT=134 / Abort trap: 6
    while every SKIP-marked file passes. Direct log evidence: the log contains
    EXIT=134 / Abort trap: 6 → the job is C. Run-level bulk rule: when two or
    more jobs show the same content-failure pattern (A), all are upgraded to C
    (confirm EXIT=134 via --logs) → action=restore-toolchain.
  D queue-resource wall (D-queue-wall) = cancelled with steps=[] (a job with
    zero steps; its logs 404) → action=queue-etiquette.
  E coqchk-skipped signature (E-coqchk-skipped) = the upload step failed and
    the coqchk step was skipped (with GATE-BANNER-ABSENT confirmable from the
    log) — a variant of family B; do not treat it as a content failure
    → action=rerun-after-stable-window.
  E variant (gate2-only cascade, banner-absent-restricted form) = the
    failed-step set is a subset of {gate2 + upload family} and at least one
    pure-gate2 failed step exists (a gate2 step name that is not an upload
    name — this guards against "Upload artifact (gate2 ledger)" being counted
    as a pure gate2 red through the gate2 substring), and the preceding
    build/coqchk steps are not content failures. Conclusion-position
    validation (judged on genuinely executed log lines after dump-line
    filtering):
    ① a genuinely executed GATE2-ATTEST-RED / 判定=CLEAN token is present =
       attested-red shape (the coqchk step completed with parser CLEAN and
       zero axioms) → the E variant does not hold; the job stays UNRECOGNIZED
       (manual identification takes precedence);
    ② the coqchk step succeeded = it ran to completion, so the "coqchk
       artifacts missing" cascade mechanism does not apply (the only
       corroborating signal when no log is available) → likewise stays
       UNRECOGNIZED;
    ③ a genuinely executed GATE-BANNER-ABSENT line is present = the
       banner-absent cascade applies (coqchk skipped/cancelled);
    ④ no log available and coqchk did not complete = the step-name rule keeps
       E (banner token unconfirmed; noted as such).
    → family=E-coqchk-skipped, action=rerun-after-stable-window. The
    run-level precedence order UNRECOGNIZED>C>A>E>B>D is unchanged (the E
    variant lives inside E).
  All passing = no failed jobs → family=none, action=watch-only. In-progress or
    conditionally skipped jobs (empty conclusion, or skipped/neutral) are also
    recorded as none, but the evidence explicitly notes "classification
    deferred, not a passing verdict" — they are never counted as passing.
  Failure shapes outside the taxonomy → family=UNRECOGNIZED, action=watch-only
    (never force-fitted into the taxonomy; takes top precedence at run level;
    manual log identification first; fail-loud).

  Classification precedence (per job, first match wins): passing / in-progress /
    conditionally skipped → D (cancelled, zero steps) → B cascade (cancelled,
    has steps, zero failed steps) → direct-log C (EXIT=134 / Abort trap: 6) →
    E signature (upload-step red + coqchk skipped) → E variant (gate2-only
    cascade: failed-step set ⊆ {gate2+upload}, build/coqchk not content red,
    banner-absent-restricted — attested-token and coqchk-completed shapes stay
    UNRECOGNIZED) → log B → step-name B (checkout/upload/artifact/cache/…) →
    log A (Error:/FAIL/ORDER-MISSING/COQCHK_EXIT≠0/nonzero axiom total) →
    step-name A (build/compile/coqchk/…) → UNRECOGNIZED.

Purpose:
  Triage the jobs of a GitHub Actions run into failing and passing: print a step-level
  table (step name/status/conclusion/start/end/duration in seconds), assign
  each job a family, and prescribe an action; with --baseline-seconds given a
  historical duration for the same sync, print a ratio table (example: coqchk
  561s vs 7480s = 13.3x — a likely local resource squeeze, not a hang). A failing
  result is data, not a tool failure: triage always exits 0 and reports the outcome explicitly on stdout.

Usage (all paths parameterized; zero hardcoded absolute paths):
  Online mode (read-only GET; the token is taken from the ~/.netrc machine
  github.com line's 6th-column password field; --netrc selects another path):
    python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs] [--netrc PATH]
        [--baseline-seconds N] [--baseline-step NAME] [--timeout S]
        [--retry-max N] [--json out.json]
    (GET /repos/{repo}/actions/runs/{run}/jobs?per_page=100&page=N, paginated
      to completion; with --logs, each failed job is additionally fetched via
      GET /repos/{repo}/actions/jobs/{job}/logs and key lines are recorded as
      evidence: COQCHK_EXIT / COQCHK_ALL_PASS / 判定=CLEAN / 公理总数 /
      GATE-BANNER-ABSENT / GATE2-ATTEST-RED / R4 覆盖划分 / appendix 缺 /
      ENOTFOUND / ORDER-MISSING / EXIT=134 and others. Dump-line filtering:
      evidence collection and token search first drop ANSI-cyan script echo
      lines ([36;1m) and ##[group]/##[endgroup] group-directive lines — script
      echo is not a real execution line, so "log confirmation" must be a real
      execution line (the filter rule is noted as-is: the number of dropped
      lines enters evidence); --no-dump-filter disables it (trap shapes then
      enter evidence verbatim, with an explicit run-level note). Two-hop log
      fetch (determined by probing): hop 1 sends Accept:
      application/vnd.github+json (text/plain is now rejected with 415) with
      automatic redirects disabled → 302 Location signed URL; hop 2 GETs the
      signed URL with no Authorization header (the signature carries the
      credentials — forwarding the token yields 403 Azure
      AuthenticationFailed). A logs GET 404/403/415 itself enters evidence —
      403 Forbidden: job is completed is a family-B cancellation-cascade
      token; after retries are exhausted the original status code enters
      evidence as before.)
  Resilience layer (rate-limit backoff): an online GET that meets 403/429/5xx
    retries with exponential backoff (base 2s, cap --retry-max default 3; a
    parseable Retry-After second count replaces the current exponential delay;
    an HTTP-date form is not guessed and falls back to exponential; when
    retries are exhausted, or on 4xx semantic errors (401/404 etc.), the
    original error propagates as 9 with no retry). Delay computation lives in
    the tools/_http_backoff.py pure functions backoff_delays()/
    parse_retry_after()/is_retry_status() (shared by three tools; imported by
    same-directory sys.path injection; no __init__ package layout).
  Offline mode (used by --selftest and in air-gapped environments; zero
  network):
    python3 tools/ci_triage.py --offline JOBS.json [--baseline-seconds N ...]
        [--no-dump-filter] [--json out.json]
    (canned jobs JSON in the same shape as the real API
      {"total_count":N,"jobs":[...]}, plus an optional top-level job_logs
      extension {"<job_id>": "log text"} dedicated to offline log injection —
      not a real API shape, noted as such. Fixtures:
      tests/fixtures/ci_triage_*.json — the six-file set, plus one main-shape
      coq93 real-form file ci_triage_main_coq93.json (a single Windows job
      "Main CI 9.3", 16 real step names, passing sample) and two gate2-only
      real-form files ci_triage_gate2_only_{cancelled,failure}.json — nine
      files in total.)
  python3 tools/ci_triage.py --selftest

Exit codes: 0 = triage completed (a red verdict is data, not a tool error;
  reported explicitly on stdout); 2 = usage error (missing / mutually
  exclusive / malformed arguments); 9 = API or file unreachable, or malformed
  (netrc missing, empty token, HTTP 4xx/5xx, connection failure, jobs file
  missing or malformed JSON, unrecognized timestamp shape). --selftest:
  0 = all pass / 2 = assertion failure.

Report schema (--json) = rocqwash-ci-triage/1:
  {"schema","mode","source",
   "run"{repo,run_id,total_count,jobs_total,red_job_ids,family,action,evidence},
   "jobs"[{id,name,status,conclusion,started_at,completed_at,duration_sec,
     "steps"[{number,name,status,conclusion,started_at,completed_at,duration_sec}],
     "classification"{family,action,evidence,red_steps}}],
   "family","action","evidence","baseline_note"?}
  family ∈ A-content-red / B-netred / C-toolchain-break / D-queue-wall /
    E-coqchk-skipped / none / UNRECOGNIZED;
  action ∈ rerun-after-stable-window / fix-content / restore-toolchain /
    queue-etiquette / watch-only;
  baseline_note (present only with --baseline-seconds): {applied,step_query,
    baseline_seconds,matched?,current_seconds?,ratio?,note|reason}
    (applied=false = the baseline step is absent or unfinished — reported
    explicitly, never silently; rc is still 0).

Honesty rules (per CONTRIBUTING §0): accept only mechanical evidence; never
  force-fit shapes outside the taxonomy; a failing result is data, not a tool
  failure (triage exits 0); --json is written sorted with sort_keys so reruns on
  the same input are byte-identical; stdout is fully data-driven (no now(), no
  randomness); zero third-party dependencies (pure stdlib); fail-loud, no
  silent degradation.

```

## 注释（逐字·按行序）

```
L169: # logs 端点 Accept 实测定值（20261112 415 修法）：text/plain 现 415 拒（探针 P1
L170: # 原词 {"message":"Unsupported 'Accept' header: 'text/plain'. Must accept
L171: # 'application/json'. ..."}）；application/vnd.github+json → 302 Location 签名
L172: # URL（探针 P2）；第二跳对签名 URL 零 Authorization → 200 实日志（探针 P4·
L173: # 1673483 bytes）；带 token 转发 → 403 Azure AuthenticationFailed（探针 P5
L174: # 对照·证两跳零认证必要面）。探针 /tmp/probe_logs_415.py·job 127903477736。
L176: # 签名 URL 重定向族（两跳手工续接）
L180: # 同目录共享退避小模块（无 __init__ 包结构）
L183: # ---- 判类谱词面（冻结向量·正负判见 --selftest）-----------------------------
L185: # 日志关键行抓取器（tag, regex）——命中行原样入 evidence（≤200 字符·去重保序·帽 60）。
L186: # 20261112 复核台账 §三候选五 token：GATE2-ATTEST-RED/R4 覆盖划分/appendix 缺
L187: # 三枚新增（逐 token 自 retro 真账——S6 raw log 真执行行/artifact gate2_attest.json
L188: # reasons/appendix 字段双形），判定=CLEAN/公理总数= 两枚开工态已在册复核咬合
L208: # 家族判定 regex（log 直证）
L217: # gate2-only 形结论位校验 token（复核台账 §四-2 token 二分·认证态红形判据——
L218: # GATE2-ATTEST-RED 真执行行 17:18:53Z／判定=CLEAN parser 结论行 17:18:52Z·任一
L219: # 真执行在册即认证态形·E 变体不成立留 UNRECOGNIZED 不充谱）
L221: # coqchk 步完走判据（复核台账 §四-2 分叉判据件二·run#10 形 coqchk success
L222: # 40398s＝非「产物缺」连坐机理）：步名起首 coqchk 方算——防「gate5 vo-binary
L223: # quarantine (pre-coqchk…)」「Upload coqchk logs」coqchk 子串词面搭便误判完走
L224: # （勘形 §3.1/retro §2.3-1 同款搭便暗礁律）
L226: # dump/telemetry 行滤除（复核台账 §三-2 证据陷阱·20261112）：GitHub 步日志以青色
L227: # 回显整段脚本（[36;1m…[0m·ESC 形或字面残留形）＋##[group]/##[endgroup] 组指令
L228: # 行——脚本回显非真执行行（run#10 形：banner-absent 分支实际未执行·仅 dump 行在）
L229: # ·「log 确证」须为真执行行。滤除规则如实注记（命中行数入 evidence）·
L230: # --no-dump-filter 可关（关闭时陷阱形原样入证据·run 级响亮注记）
L233: # 步名族 regex（步级推断·无日志时的兜底判面）
L238: # gate2-only 连坐形判据词（纯 gate2
L239: # 红步＝GATE2 命中且 UPLOAD 不命中——「Upload artifact (gate2 ledger)」gate2
L240: # 子串词面搭便不算纯 gate2·防误吞上传红·组合判据在 classify E 变体分支）
L244: # family → action（判类谱处置表）
L265: # run 级判类序（先到先取）：谱外红形置顶（人工指认优先·不被已识别族遮蔽）
L269: # 倍数≥此阈→「本机挤压嫌疑非卡死」（判例 13.3x 远超阈）
L270: # 单 job 日志证据行帽
L271: # --logs 红件日志抓取件数帽（超额响亮注记）
L292: # ---- 时间与时长 -------------------------------------------------------------
L339: # ---- 凭据（netrc machine github.com 第 6 列）--------------------------------
L376: # ---- 只读 GET（唯一网络动作）-------------------------------------------------
L522: # ---- 离线装载 ---------------------------------------------------------------
L559: # ---- 判类器 -----------------------------------------------------------------
L640: # D：cancelled 且零步骤（logs 404 形）
L645: # B 连坐形：cancelled·有步骤·零红步
L652: # log 直证 C：EXIT=134 / Abort trap: 6（判类谱 C·SKIP 件全过）
L660: # E 签名：上传步红＋coqchk 步 skipped（B 族变体·勿当内容红）
L676: # E 变体（gate2-only 连坐形·banner-absent 限形·20261112 Main retro 六事件
L677: # 证据人工指认入谱＋20261112 复核台账 token 二分限形——#10 假阳性清偿）：
L678: # 红步集 ⊆ {gate2＋上传族} 且纯 gate2 红步在册（gate2 名非上传名——防
L679: # 「Upload artifact (gate2 ledger)」gate2 子串词面搭便误吞上传红）＝前置
L680: # build/coqchk 非 content 红（Build/coqchk proper 步名既不沾 gate2 也不沾
L681: # 上传族·在红步集即破子集条件）。结论位校验（复核台账 §四-2 token 二分·
L682: # dump 行滤除后真执行 token 为准——run#7 job 127903477736 日志 200 实测
L683: # banner-absent 真执行行 13:22:43Z·run#10 job 128320751675 raw log 真执行
L684: # 判定=CLEAN(exit 0) 公理总数=0 17:18:52Z＋GATE2-ATTEST-RED 17:18:53Z）：
L685: #   ①GATE2-ATTEST-RED/判定=CLEAN 真执行 token 在＝认证态红形（run#10 判例
L686: #     coqchk success 40398s parser CLEAN 公理=0 R4 覆盖划分破）→ E 变体不
L687: #     成立·留 UNRECOGNIZED 不充谱（人工指认优先）；
L688: #   ②coqchk 步 success＝完走·非「coqchk 产物缺」连坐机理（复核台账 §四-2
L689: #     分叉判据件二·无日志时器面唯一旁证）→ 同留 UNRECOGNIZED；
L690: #   ③GATE-BANNER-ABSENT 真执行行在＝banner-absent 连坐 E（run#7/8/20/26
L691: #     四发·coqchk skipped/cancelled·log 确证第三件入账）；
L692: #   ④无日志且 coqchk 未完走＝步名规则维持 E（banner token 未确证·如实注记）。
L693: # → family=E-coqchk-skipped·action=rerun-after-stable-window（E 族内变体·
L694: #   判类谱序 UNRECOGNIZED>C>A>E>B>D 不动）。出处：retro 台账 §二主表 UNREC
L695: #   六事件中 #7/#8/#20/#26 四发 banner-absent 形入谱·#10 认证态形转正留
L696: #   UNREC＝复核判词（器判=复核判·验收判）·#3 runner 失联形（零红步）仍走
L697: #   UNRECOGNIZED 不充谱。
L809: # ---- 时长对表（--baseline-seconds）------------------------------------------
L844: # ---- 出账 -------------------------------------------------------------------
L918: # ---- 主流程 -----------------------------------------------------------------
L1072: # ---- 自测（--offline fixtures·零真网络零编译·纯逻辑向量）---------------------
L1112: # 〔一〕五族＋绿炉六样张全命中（family/action 逐张咬合）
L1132: # A：红步名入 evidence·且非 B/E（内容红正判）
L1137: # B：checkout 红步归 B；cancelled 连坐形（有步骤零红步）亦归 B
L1144: # C：run 级批量升 C（三红 job 全 C·绿控制件仍 none·批量注记在 per-job 证据）
L1150: # D：零步骤（steps=[]）在册·证据含 steps=0
L1155: # E：E 签名命中·且勿当内容红（family≠A·coqchk skipped 注记在册）
L1161: # 绿炉：family=none·action=watch-only
L1165: # 〔二〕基线对表：绿炉 COQCHK 7480s vs 基线 561s = 13.3x（判例）
L1174: # 基线步缺席（A 夹具 COQCHK skipped）→ applied=False 响亮注记·rc 仍 0
L1181: # 〔三〕确定性：C 夹具同输入重跑 --json 字节级恒同
L1189: # 〔四〕CLI 四码＋互斥形
L1207: # 〔五〕分类器单元（零网络·直接调）
L1262: # 〔六〕关键行 regex 正负判（判类谱词面冻结向量）
L1286: # 〔七〕netrc 解析单元（单行 6 列形＋多行形＋负例·零网络）
L1303: # 〔八〕韧性层：退避序列＋Retry-After 尊重＋http_get canned 重试 runner
L1304: # （零网络·_open/_sleep 注入位·判例 403×3→[2,4,8]）
L1338: # canned 错件须抛（urlopen 同语义）
L1347: # 403×3→[2,4,8] 判例
L1353: # Retry-After 头尊重（替指数）
L1371: # 〔九〕Main 形判读矢（v48 勘形小改①·勘形档 §3.1 兼容表的机检钉）：
L1372: # coq93.yml 真形（workflow「Main CI 9.3」·单 Windows job「Rocq 9.3
L1373: # build + coqchk (self-hosted seed cache, Windows)」）步名 16 枚逐枚
L1374: # 咬合＋五族判类对 Main 步名兼容逐行机械验证（真红不漏红·UNRECOGNIZED
L1375: # 兜底不误断）。机检与勘形 §3.1 散文一处不符如实登记：gate1 步名
L1376: # 「pre-build」含 build 子串→CONTENT 搭便归 A（fix-content·poison-token
L1377: # 红语义上属内容红·可接受同 gate5/attest 词面搭便）——非 §3.1 所记
L1378: # 「零命中→UNRECOGNIZED 兜底」；「五族骨架即用」判据不受影响（不漏红
L1379: # 不误断）。20261112 增注：gate2 行原钉 UNRECOGNIZED（v48 勘形兼容表
L1380: # 时点器面）——Main retro 六事件证据人工指认后 gate2-only 连坐形入谱
L1381: # （E 变体·见〔十〕）·本行现钉 E-coqchk-skipped·兜底行剩 gate3/RAM/
L1382: # tree-stats-gen 三枚（20261112 自查日志注记·与勘形 §八判读不追溯）。
L1419: # 确定性：Main 夹具同输入重跑 --json 字节级恒同
L1425: # 兼容表逐行机检（真形单红步形·无日志·判类序 步名 B 先于 步名 A）
L1456: # 词面暗礁/搭便机制钉：gate4=artifact 子串→步名 B 先判（勘形 §3.1
L1457: # 暗礁行·Set :120 同款非 Main 新增）；gate1=pre-build 子串→步名 A 搭便
L1467: # E 族 Main 形两件齐（勘形 §3.1 E 行：上传红＋coqchk skipped·
L1468: # Main 步名两件齐→E 可发）：Upload coqchk logs 红＋coqchk 步 skipped
L1482: # 〔十〕gate2-only E 变体判读矢（20261112 复核台账 token 二分验收线·
L1483: # banner-absent=E×4／ATTEST-RED=UNREC×1）＋logs 两跳 415 修法矢
L1484: # （全部 canned 零网络）
L1487: # 1) 两件 fixture 真形判读（canned job_logs 真执行行入判）：cancelled
L1488: #    （run#7·banner-absent 真执行行 13:22:43Z＋2 行 dump）→E 保持；
L1489: #    failure（run#10·GATE2-ATTEST-RED/判定=CLEAN 真执行行＋banner-absent
L1490: #    仅 dump 行·coqchk success）→UNRECOGNIZED 转正验收判（器判=复核判词·
L1491: #    E 假阳性清偿）
L1528: # 2) 四矢保持 E（复核台账 §四-2 ①相 banner-absent 形·classify 直调·
L1529: #    真执行行 canned）：#7（Build cancelled→coqchk skipped→gate2 红＋
L1530: #    banner 真行）／#8·#20 形（Build success→coqchk cancelled→gate2 红）／
L1531: #    #26 形（同 #7 步级·无日志→banner token 未确证如实注记仍 E）
L1563: # 3) #10 转正矢（认证态形·器判 UNREC=复核判词·复核台账 §四-2 ②相）：
L1564: #    a. token 直证形（canned 真执行行）→UNRECOGNIZED；b. 判据件二形
L1565: #    （无日志·coqchk success 完走＝非产物缺机理）→UNRECOGNIZED；
L1566: #    c. 认证态 token 零红词面机检（落 UNREC 兜底的前提）
L1590: # 4) dump 行滤除矢（复核台账 §三-2 证据陷阱·canned 零网络）：a. dump 行
L1591: #    与真执行行混在→滤除注记＋真执行行确证；b. S6 陷阱形（banner 仅
L1592: #    dump 行·#10 步真形 coqchk success）→不确证→UNREC（滤除生效）；
L1593: #    c. --no-dump-filter 同陷阱形（滤除关）→dump 行原样确证（陷阱如实再现）
L1612: # 5) 五 token 在册矢（复核台账 §三候选·逐 token 真账形正判·全员在册）＋
L1613: #    谱外候选不冒充在册负证
L1630: # 6) 规则负判五发：build/coqchk proper content 红→A（连坐被破）；
L1631: #    「Upload artifact (gate2 ledger)」gate2 子串搭便上传红→B（防误吞
L1632: #    既钉）；非 gate2/上传红步→UNRECOGNIZED；零红步 failure（runner
L1633: #    失联形＝出处六事件 #3）→UNRECOGNIZED 不充谱
L1659: # 7) CLI 矢：--no-dump-filter（#10 canned fixture·滤除关→dump 行 banner
L1660: #    入判据·认证态 token 与 banner dump 并存→判据件二兜底 UNREC·run 级
L1661: #    响亮注记）＋job_logs 形坏 fail-loud 9＋canned 日志确定性字节恒同
L1689: # 4) logs 两跳 415 修法矢（canned _open 注入·零网络）：
L1690: #    修后形 hop1 Accept=LOGS_ACCEPT（≠text/plain 415 债）→ 302 Location
L1691: #    → hop2 零 Authorization → 200 日志文本；旧形对照 415 原码入证据；
L1692: #    第二跳 403 Azure 形原码入证据；重定向无 Location 形坏入证据。
```

## 函数级 docstring（逐字）

### TriageError（L275-275）

```
带退出码的 fail-loud 异常（code: 2=用法错·9=API/文件不可达或形坏）。
```

### ApiHTTPError（L283-283）

```
只读 GET 的 HTTP 错误（body 头入账·由调用方决定转 9 还是入 evidence）。
```

### parse_iso（L295-295）

```
ISO8601 → aware datetime（UTC 缺省）；空/None → None；形不识别 → fail-loud 9。
```

### duration_sec（L321-321）

```
起止 → 整秒（None/未完 → None；负值钳 0）。
```

### netrc_token（L342-343）

```
netrc 手动解析：machine <m> login <l> password <p>（单行 6 列形与多行形
    通吃）→ password token。缺文件/无条目/空值 → fail-loud 9（token 永不回显）。
```

### http_get（L380-383）

```
只读 GET → bytes。403/429/5xx 指数退避重试（_http_backoff 纯函数：
    base 2s·帽 retry_max·Retry-After 秒数头优先替当次延迟）；重试耗尽或
    4xx 语义面原错上抛——HTTPError → ApiHTTPError（body 头随行）；连接失败
    → 9。_open/_sleep 注入位（selftest 零网络矢量·缺省真 urlopen/真 sleep）。
```

### fetch_jobs_online（L418-419）

```
GET jobs（per_page=100 分页到齐）→ (jobs, total_count)。HTTP 4xx/5xx
    → 9（403/429/5xx 先经 http_get 指数退避重试·耗尽才判 9）。
```

### _NoRedirect（L443-445）

```
禁自动重定向 handler（302 以 HTTPError 形上抛·供 fetch_job_log 两跳手工
    续接——urllib 缺省跟随时会把 Authorization 头一并转发签名 URL·Azure 侧
    403 AuthenticationFailed 实测形；两跳零认证第二跳即修）。
```

### _logs_error_note（L452-452）

```
logs HTTPError → 证据注记（body 头 120 字符·原码在册·同旧注记形）。
```

### fetch_job_log（L463-473）

```
GET 单 job 日志原文 → (text, None)；HTTP 4xx/5xx → (None, 证据注记)。

    两跳取日志（20261112 415 修法·实测定）：第一跳 GET logs 端点
    （Accept: application/vnd.github+json——text/plain 现 415 拒·禁自动重定向
    _NoRedirect opener）→ 302 Location 签名 URL；第二跳对签名 URL 零
    Authorization 再 GET（签名自带凭据——urllib 缺省随重定向转发 token 会
    403 Azure AuthenticationFailed·探针 P5 实测）。403/429/5xx 第一跳指数退避
    重试（_http_backoff 同款·Retry-After 秒数头尊重·耗尽落证据注记）；
    404/415 等语义面不重试原码照旧入证据；第二跳失败落证据注记不重试；
    连接失败仍 TriageError 9（API 不可达）。_open/_sleep 注入位（selftest
    零网络矢量·缺省真 opener/真 sleep）。
```

### load_jobs_offline（L525-529）

```
canned jobs JSON → (jobs, total, job_logs)。同 API 真形
    {"total_count":N,"jobs":[...]}＋可选顶层 job_logs 扩展位 {"<job_id>":
    "日志文本"}（离线日志注入专用·非 API 真形如实注记——复核台账 token 二分
    验收判的 canned 通路·数字键归一 int 咬合 job.id）。缺文件/解析败/形坏
    （jobs 形坏或 job_logs 非 {str: str} 形）→ fail-loud 9。
```

### filter_dump_lines（L562-568）

```
日志原文 → 滤除 dump/telemetry 行后文本（复核台账 §三-2 证据陷阱）。

    滤除规则（如实注记·DUMP_LINE_RE）：青色脚本回显行（[36;1m·ESC 形或字面
    残留形）＋##[group]/##[endgroup] 组指令行——脚本回显非真执行行，run#10 形
    banner-absent 分支实际未执行仅 dump 行在册，若不过滤则「log 确证」被 dump
    行冒充（S6 证据陷阱原形）。真执行行（mojibake GBK 实跑行/无色前缀行）全数
    保留。--no-dump-filter 可关（关闭时本函数不入链·陷阱形如实再现）。
```

### scan_log_evidence（L576-578）

```
日志原文 → 关键行证据表（tag＋命中行原样 ≤200 字符·去重保序·帽 60）。
    dump_filter=True（缺省）时先滤 dump/telemetry 行（青色脚本回显/组指令行·
    复核台账 §三-2 证据陷阱——「log 确证」须为真执行行）。
```

### classify（L602-605）

```
判类谱逐 job 判类 → {"family","action","evidence","red_steps"}（判类序见
    模块 docstring·失败步名与 redSteps 全入 evidence）。dump_filter=True（缺省）
    时 log_text 先滤 dump/telemetry 行（青色脚本回显/组指令·复核台账 §三-2 证据
    陷阱——滤除行数响亮入 evidence·滤后文本方入判据检索与 evidence 收集）。
```

### batch_upgrade_c（L775-776）

```
run 级批量判（判类谱 C）：同形内容红（A）≥2 件 → 全数升 C
    （判例：批量 EXIT=134/Abort trap: 6·SKIP 件全过·--logs 可确证）。
```

### run_verdict（L790-791）

```
run 级判类：按 RUN_FAMILY_PRECEDENCE 取先（谱外置顶）→ {family,action,
    evidence,red_job_ids}。
```

### build_baseline_note（L812-814）

```
基线对表：现值（--baseline-step 名含匹配·多命中取最长者·全部在册）
    vs 基线秒 → 倍数；≥BASELINE_SQUEEZE_RATIO → 本机挤压嫌疑非卡死注记。
    基线步未在场或未完（skipped/未跑）→ applied=false 响亮注记（rc 仍 0）。
```

### run_triage（L921-922）

```
装载（线上/离线）→ 逐 job 判类 → run 级批量判 C → run 判类 → 基线对表
    → (report, jobs, per, verdict, baseline, source_desc)。用法错 → 2·不可达 → 9。
```

### selftest（L1075-1090）

```
内嵌冻结向量组：五族＋绿炉六 canned 样张全命中＋基线 13.3x 判例＋基线步
    缺席响亮注记＋分类器单元（关键行 regex 正负判·连坐/在飞/UNRECOGNIZED 分流·
    E 勿当内容红负证）＋netrc 解析单元＋确定性字节恒同＋CLI 四码＋韧性层退避
    （403×3→[2,4,8]·Retry-After 尊重·耗尽上抛·401 不重试·_open/_sleep 注入
    零网络）＋〔九〕Main 形判读矢（v48 勘形小改①·coq93.yml 真形步名×五族
    判类兼容机检钉——勘形 §3.1「即用」判据的机械实证）＋〔十〕gate2-only
    E 变体矢（复核台账 token 二分验收线：#7 fixture banner-absent 真执行行
    canned →E 保持＋#8/#20/#26 形矢 E＋#10 fixture 认证态 token canned →
    UNRECOGNIZED 转正验收判（器判=复核判词）＋coqchk-success 旁证矢＋认证态
    token 零红词面机检＋规则负判四发·出处六事件四入一转一留）＋dump 行滤除矢
    （复核台账 §三-2 证据陷阱：dump-only banner 不确证·真执行行确证·
    --no-dump-filter 陷阱形如实再现）＋〔十一〕五 token 在册矢（复核台账 §三
    候选逐 token 真账形正判）＋job_logs 扩展位形坏 fail-loud 矢＋canned 日志
    确定性字节恒同矢＋logs 两跳 415 修法矢（302→零 Authorization 第二跳
    200·415/403/无 Location 原码入证据·canned 零网络）。
    全程 --offline fixtures 零真网络零编译。
```

### _Resp（L1317-1317）

```
canned 响应体（urlopen 假件·零网络·上下文管理器形）。
```

## 字符串常量（逐字·按行序）

```
L3: 'ci_triage.py — failing-build triage tool for rocqwash CI (tools/).\n\n[Classification taxonomy] — five failure families plus the all-passing state:\n  A content failure (A-content-red) = the failing step points at concrete\n    content: Build/COQCHK emits Error:/FAIL/ORDER-MISSING, or COQCHK exits\n    nonzero (COQCHK_EXIT≠0, nonzero axiom total) → action=fix-content.\n  B network window (B-netred) = checkout unable to access / port 443 /\n    Connection was reset; upload-step ENOTFOUND / Upload progress stalled;\n    403 Forbidden: job is completed. (Cancellation cascade: a cancelled job\n    that has steps but zero failed steps also lands here.)\n    → action=rerun-after-stable-window.\n  C toolchain break (C-toolchain-break) = wholesale EXIT=134 / Abort trap: 6\n    while every SKIP-marked file passes. Direct log evidence: the log contains\n    EXIT=134 / Abort trap: 6 → the job is C. Run-level bulk rule: when two or\n    more jobs show the same content-failure pattern (A), all are upgraded to C\n    (confirm EXIT=134 via --logs) → action=restore-toolchain.\n  D queue-resource wall (D-queue-wall) = cancelled with steps=[] (a job with\n    zero steps; its logs 404) → action=queue-etiquette.\n  E coqchk-skipped signature (E-coqchk-skipped) = the upload step failed and\n    the coqchk step was skipped (with GATE-BANNER-ABSENT confirmable from the\n    log) — a variant of family B; do not treat it as a content failure\n    → action=rerun-after-stable-window.\n  E variant (gate2-only cascade, banner-absent-restricted form) = the\n    failed-step set is a subset of {gate2 + upload family} and at least one\n    pure-gate2 failed step exists (a gate2 step name that is not an upload\n    name — this guards against "Upload artifact (gate2 ledger)" being counted\n    as a pure gate2 red through the gate2 substring), and the preceding\n    build/coqchk steps are not content failures. Conclusion-position\n    validation (judged on genuinely executed log lines after dump-line\n    filtering):\n    ① a genuinely executed GATE2-ATTEST-RED / 判定=CLEAN token is present =\n       attested-red shape (the coqchk step completed with parser CLEAN and\n       zero axioms) → the E variant does not hold; the job stays UNRECOGNIZED\n       (manual identification takes precedence);\n    ② the coqchk step succeeded = it ran to completion, so the "coqchk\n       artifacts missing" cascade mechanism does not apply (the only\n       corroborating signal when no log is available) → likewise stays\n       UNRECOGNIZED;\n    ③ a genuinely executed GATE-BANNER-ABSENT line is present = the\n       banner-absent cascade applies (coqchk skipped/cancelled);\n    ④ no log available and coqchk did not complete = the step-name rule keeps\n       E (banner token unconfirmed; noted as such).\n    → family=E-coqchk-skipped, action=rerun-after-stable-window. The\n    run-level precedence order UNRECOGNIZED>C>A>E>B>D is unchanged (the E\n    variant lives inside E).\n  All passing = no failed jobs → family=none, action=watch-only. In-progress or\n    conditionally skipped jobs (empty conclusion, or skipped/neutral) are also\n    recorded as none, but the evidence explicitly notes "classification\n    deferred, not a passing verdict" — they are never counted as passing.\n  Failure shapes outside the taxonomy → family=UNRECOGNIZED, action=watch-only\n    (never force-fitted into the taxonomy; takes top precedence at run level;\n    manual log identification first; fail-loud).\n\n  Classification precedence (per job, first match wins): passing / in-progress /\n    conditionally skipped → D (cancelled, zero steps) → B cascade (cancelled,\n    has steps, zero failed steps) → direct-log C (EXIT=134 / Abort trap: 6) →\n    E signature (upload-step red + coqchk skipped) → E variant (gate2-only\n    cascade: failed-step set ⊆ {gate2+upload}, build/coqchk not content red,\n    banner-absent-restricted — attested-token and coqchk-completed shapes stay\n    UNRECOGNIZED) → log B → step-name B (checkout/upload/artifact/cache/…) →\n    log A (Error:/FAIL/ORDER-MISSING/COQCHK_EXIT≠0/nonzero axiom total) →\n    step-name A (build/compile/coqchk/…) → UNRECOGNIZED.\n\nPurpose:\n  Triage the jobs of a GitHub Actions run into failing and passing: print a step-level\n  table (step name/status/conclusion/start/end/duration in seconds), assign\n  each job a family, and prescribe an action; with --baseline-seconds given a\n  historical duration for the same sync, print a ratio table (example: coqchk\n  561s vs 7480s = 13.3x — a likely local resource squeeze, not a hang). A failing\n  result is data, not a tool failure: triage always exits 0 and reports the outcome explicitly on stdout.\n\nUsage (all paths parameterized; zero hardcoded absolute paths):\n  Online mode (read-only GET; the token is taken from the ~/.netrc machine\n  github.com line\'s 6th-column password field; --netrc selects another path):\n    python3 tools/ci_triage.py --repo ORG/REPO --run ID [--logs] [--netrc PATH]\n        [--baseline-seconds N] [--baseline-step NAME] [--timeout S]\n        [--retry-max N] [--json out.json]\n    (GET /repos/{repo}/actions/runs/{run}/jobs?per_page=100&page=N, paginated\n      to completion; with --logs, each failed job is additionally fetched via\n      GET /repos/{repo}/actions/jobs/{job}/logs and key lines are recorded as\n      evidence: COQCHK_EXIT / COQCHK_ALL_PASS / 判定=CLEAN / 公理总数 /\n      GATE-BANNER-ABSENT / GATE2-ATTEST-RED / R4 覆盖划分 / appendix 缺 /\n      ENOTFOUND / ORDER-MISSING / EXIT=134 and others. Dump-line filtering:\n      evidence collection and token search first drop ANSI-cyan script echo\n      lines ([36;1m) and ##[group]/##[endgroup] group-directive lines — script\n      echo is not a real execution line, so "log confirmation" must be a real\n      execution line (the filter rule is noted as-is: the number of dropped\n      lines enters evidence); --no-dump-filter disables it (trap shapes then\n      enter evidence verbatim, with an explicit run-level note). Two-hop log\n      fetch (determined by probing): hop 1 sends Accept:\n      application/vnd.github+json (text/plain is now rejected with 415) with\n      automatic redirects disabled → 302 Location signed URL; hop 2 GETs the\n      signed URL with no Authorization header (the signature carries the\n      credentials — forwarding the token yields 403 Azure\n      AuthenticationFailed). A logs GET 404/403/415 itself enters evidence —\n      403 Forbidden: job is completed is a family-B cancellation-cascade\n      token; after retries are exhausted the original status code enters\n      evidence as before.)\n  Resilience layer (rate-limit backoff): an online GET that meets 403/429/5xx\n    retries with exponential backoff (base 2s, cap --retry-max default 3; a\n    parseable Retry-After second count replaces the current exponential delay;\n    an HTTP-date form is not guessed and falls back to exponential; when\n    retries are exhausted, or on 4xx semantic errors (401/404 etc.), the\n    original error propagates as 9 with no retry). Delay computation lives in\n    the tools/_http_backoff.py pure functions backoff_delays()/\n    parse_retry_after()/is_retry_status() (shared by three tools; imported by\n    same-directory sys.path injection; no __init__ package layout).\n  Offline mode (used by --selftest and in air-gapped environments; zero\n  network):\n    python3 tools/ci_triage.py --offline JOBS.json [--baseline-seconds N ...]\n        [--no-dump-filter] [--json out.json]\n    (canned jobs JSON in the same shape as the real API\n      {"total_count":N,"jobs":[...]}, plus an optional top-level job_logs\n      extension {"<job_id>": "log text"} dedicated to offline log injection —\n      not a real API shape, noted as such. Fixtures:\n      tests/fixtures/ci_triage_*.json — the six-file set, plus one main-shape\n      coq93 real-form file ci_triage_main_coq93.json (a single Windows job\n      "Main CI 9.3", 16 real step names, passing sample) and two gate2-only\n      real-form files ci_triage_gate2_only_{cancelled,failure}.json — nine\n      files in total.)\n  python3 tools/ci_triage.py --selftest\n\nExit codes: 0 = triage completed (a red verdict is data, not a tool error;\n  reported explicitly on stdout); 2 = usage error (missing / mutually\n  exclusive / malformed arguments); 9 = API or file unreachable, or malformed\n  (netrc missing, empty token, HTTP 4xx/5xx, connection failure, jobs file\n  missing or malformed JSON, unrecognized timestamp shape). --selftest:\n  0 = all pass / 2 = assertion failure.\n\nReport schema (--json) = rocqwash-ci-triage/1:\n  {"schema","mode","source",\n   "run"{repo,run_id,total_count,jobs_total,red_job_ids,family,action,evidence},\n   "jobs"[{id,name,status,conclusion,started_at,completed_at,duration_sec,\n     "steps"[{number,name,status,conclusion,started_at,completed_at,duration_sec}],\n     "classification"{family,action,evidence,red_steps}}],\n   "family","action","evidence","baseline_note"?}\n  family ∈ A-content-red / B-netred / C-toolchain-break / D-queue-wall /\n    E-coqchk-skipped / none / UNRECOGNIZED;\n  action ∈ rerun-after-stable-window / fix-content / restore-toolchain /\n    queue-etiquette / watch-only;\n  baseline_note (present only with --baseline-seconds): {applied,step_query,\n    baseline_seconds,matched?,current_seconds?,ratio?,note|reason}\n    (applied=false = the baseline step is absent or unfinished — reported\n    explicitly, never silently; rc is still 0).\n\nHonesty rules (per CONTRIBUTING §0): accept only mechanical evidence; never\n  force-fit shapes outside the taxonomy; a failing result is data, not a tool\n  failure (triage exits 0); --json is written sorted with sort_keys so reruns on\n  the same input are byte-identical; stdout is fully data-driven (no now(), no\n  randomness); zero third-party dependencies (pure stdlib); fail-loud, no\n  silent degradation.\n'
L192: '判定=CLEAN'
L192: '判定=CLEAN'
L193: '公理总数'
L193: '公理总数=(\\d+)'
L196: 'R4 覆盖划分'
L196: 'R4-覆盖划分'
L197: 'APPENDIX-缺'
L197: 'appendix 缺|appendix=\\{present:false\\}'
L210: '\\bError:|ORDER-MISSING|(?<![A-Za-z])FAIL(?![A-Za-z])|COQCHK_EXIT=(?!0\\b)\\d+|公理总数=(?!0\\b)\\d+'
L220: 'GATE2-ATTEST-RED|判定=CLEAN'
L256: '内容红'
L257: '网络窗'
L258: '环境断链'
L259: '排队资源墙'
L260: 'coqchk-skipped 签名（B 族变体）'
L261: '绿/无红'
L262: '判类谱外未识别红形'
L275: '带退出码的 fail-loud 异常（code: 2=用法错·9=API/文件不可达或形坏）。'
L283: '只读 GET 的 HTTP 错误（body 头入账·由调用方决定转 9 还是入 evidence）。'
L295: 'ISO8601 → aware datetime（UTC 缺省）；空/None → None；形不识别 → fail-loud 9。'
L314: '时间形不识别: %r'
L321: '起止 → 整秒（None/未完 → None；负值钳 0）。'
L342: 'netrc 手动解析：machine <m> login <l> password <p>（单行 6 列形与多行形\n    通吃）→ password token。缺文件/无条目/空值 → fail-loud 9（token 永不回显）。'
L345: 'netrc 缺失: %s（线上模式需 machine %s ... password 形凭据）'
L367: 'netrc machine %s password 为空'
L372: 'netrc 无 machine %s password 形条目（单行 6 列形：第 6 列=token）: %s'
L380: '只读 GET → bytes。403/429/5xx 指数退避重试（_http_backoff 纯函数：\n    base 2s·帽 retry_max·Retry-After 秒数头优先替当次延迟）；重试耗尽或\n    4xx 语义面原错上抛——HTTPError → ApiHTTPError（body 头随行）；连接失败\n    → 9。_open/_sleep 注入位（selftest 零网络矢量·缺省真 urlopen/真 sleep）。'
L410: 'API 不可达: %s (%s)'
L418: 'GET jobs（per_page=100 分页到齐）→ (jobs, total_count)。HTTP 4xx/5xx\n    → 9（403/429/5xx 先经 http_get 指数退避重试·耗尽才判 9）。'
L428: 'API 形坏（无 jobs 列表）: %s'
L438: 'jobs 分页超帽（50 页）·拒绝续拉'
L443: '禁自动重定向 handler（302 以 HTTPError 形上抛·供 fetch_job_log 两跳手工\n    续接——urllib 缺省跟随时会把 Authorization 头一并转发签名 URL·Azure 侧\n    403 AuthenticationFailed 实测形；两跳零认证第二跳即修）。'
L452: 'logs HTTPError → 证据注记（body 头 120 字符·原码在册·同旧注记形）。'
L457: 'logs-GET: HTTP %d %s（日志不可达·入证据）'
L463: 'GET 单 job 日志原文 → (text, None)；HTTP 4xx/5xx → (None, 证据注记)。\n\n    两跳取日志（20261112 415 修法·实测定）：第一跳 GET logs 端点\n    （Accept: application/vnd.github+json——text/plain 现 415 拒·禁自动重定向\n    _NoRedirect opener）→ 302 Location 签名 URL；第二跳对签名 URL 零\n    Authorization 再 GET（签名自带凭据——urllib 缺省随重定向转发 token 会\n    403 Azure AuthenticationFailed·探针 P5 实测）。403/429/5xx 第一跳指数退避\n    重试（_http_backoff 同款·Retry-After 秒数头尊重·耗尽落证据注记）；\n    404/415 等语义面不重试原码照旧入证据；第二跳失败落证据注记不重试；\n    连接失败仍 TriageError 9（API 不可达）。_open/_sleep 注入位（selftest\n    零网络矢量·缺省真 opener/真 sleep）。'
L501: 'logs-GET: HTTP %d 无 Location（重定向形坏）'
L519: 'API 不可达: %s (%s)'
L525: 'canned jobs JSON → (jobs, total, job_logs)。同 API 真形\n    {"total_count":N,"jobs":[...]}＋可选顶层 job_logs 扩展位 {"<job_id>":\n    "日志文本"}（离线日志注入专用·非 API 真形如实注记——复核台账 token 二分\n    验收判的 canned 通路·数字键归一 int 咬合 job.id）。缺文件/解析败/形坏\n    （jobs 形坏或 job_logs 非 {str: str} 形）→ fail-loud 9。'
L531: 'jobs JSON 缺失: %s'
L536: 'jobs JSON 形坏（解析失败）: %s (%s)'
L539: 'jobs JSON 形坏（须 {"total_count":N,"jobs":[...]} 同 API 形）: %s'
L543: 'jobs JSON 形坏（jobs[%d] 非 job 形）: %s'
L548: 'jobs JSON 形坏（job_logs 须 {"<job_id>": "日志文本"} 扩展位形）: %s'
L562: '日志原文 → 滤除 dump/telemetry 行后文本（复核台账 §三-2 证据陷阱）。\n\n    滤除规则（如实注记·DUMP_LINE_RE）：青色脚本回显行（[36;1m·ESC 形或字面\n    残留形）＋##[group]/##[endgroup] 组指令行——脚本回显非真执行行，run#10 形\n    banner-absent 分支实际未执行仅 dump 行在册，若不过滤则「log 确证」被 dump\n    行冒充（S6 证据陷阱原形）。真执行行（mojibake GBK 实跑行/无色前缀行）全数\n    保留。--no-dump-filter 可关（关闭时本函数不入链·陷阱形如实再现）。'
L576: '日志原文 → 关键行证据表（tag＋命中行原样 ≤200 字符·去重保序·帽 60）。\n    dump_filter=True（缺省）时先滤 dump/telemetry 行（青色脚本回显/组指令行·\n    复核台账 §三-2 证据陷阱——「log 确证」须为真执行行）。'
L602: '判类谱逐 job 判类 → {"family","action","evidence","red_steps"}（判类序见\n    模块 docstring·失败步名与 redSteps 全入 evidence）。dump_filter=True（缺省）\n    时 log_text 先滤 dump/telemetry 行（青色脚本回显/组指令·复核台账 §三-2 证据\n    陷阱——滤除行数响亮入 evidence·滤后文本方入判据检索与 evidence 收集）。'
L622: 'conclusion=success（绿）'
L625: '在飞/未完（status=%s conclusion=%s）·判类暂缓非绿判'
L630: 'conclusion=%s（条件跳过/中立·非红）'
L637: 'dump 行滤除 %d 行（青色脚本回显/组指令·非真执行行·复核台账 §三-2 证据陷阱·--no-dump-filter 可关）'
L642: 'steps=0（零步骤）·logs 404 形（排队资源墙判例）'
L647: 'cancelled·有步骤零红步＝中断连坐形（判类谱 B·403 Forbidden: job is completed 同族）'
L654: 'log 直证：EXIT=134/Abort trap: 6（判类谱 C·环境断链）'
L666: 'coqchk 步 skipped＝gate2 未达（E 签名·GATE-BANNER-ABSENT 同义·--logs 可确证）'
L670: 'log 确证：GATE-BANNER-ABSENT（E 签名第三件齐）'
L715: 'gate2-only 形·结论位校验：GATE2-ATTEST-RED/判定=CLEAN 真执行 token 在（dump 行滤除后）＝认证态红形（复核台账 §四-2 ②相·run#10 判例 coqchk success 40398s parser CLEAN 公理=0 R4 覆盖划分破）→ E 变体不成立·留 UNRECOGNIZED 不充谱（人工指认）'
L721: 'gate2-only 红步而 coqchk 步 success（完走）＝非「coqchk 产物缺」连坐机理（复核台账 §四-2 分叉判据件二·run#10 形·认证态红候选·token 面未证）→ E 变体不成立·留 UNRECOGNIZED 不充谱'
L726: 'gate2-only 连坐形（E 变体·banner-absent 限形）：红步集 ⊆ {gate2+上传族}·纯 gate2 红步在册·前置 build/coqchk 非 content 红＝coqchk 产物缺·gate2 连坐（20261112 Main retro #7/#8/#20/#26 四事件 banner-absent 真执行形入谱·#10 认证态形已除外）'
L731: 'log 确证：GATE-BANNER-ABSENT（banner-absent 真执行行·E 变体第三件）'
L734: 'banner token 未确证（无日志或真执行行缺·如实注记·步级形）'
L746: 'log 命中网络窗词面（判类谱 B）'
L751: '红步名∈网络邻接步（checkout/upload/artifact/cache/…）: %s'
L756: 'log 命中内容红词面（Error:/FAIL/ORDER-MISSING/EXIT≠0/公理≠0·判类谱 A）'
L761: '红步名∈内容步（build/compile/coqchk/…·判类谱 A·具体件见 --logs）: %s'
L769: '判类谱外红形·不充谱·人工看日志指认'
L775: 'run 级批量判（判类谱 C）：同形内容红（A）≥2 件 → 全数升 C\n    （判例：批量 EXIT=134/Abort trap: 6·SKIP 件全过·--logs 可确证）。'
L785: 'run 级批量判：同形内容红 %d 件（判例 C：批量 EXIT=134/Abort trap: 6·SKIP 件全过）·EXIT=134 确证建议 --logs'
L790: 'run 级判类：按 RUN_FAMILY_PRECEDENCE 取先（谱外置顶）→ {family,action,\n    evidence,red_job_ids}。'
L796: '全绿：0 红件（watch-only）'
L800: '红件 %d/%d：ids=%s'
L802: '在册族：%s（判类序取先）'
L804: 'UNRECOGNIZED 在册·判类谱外红形人工指认优先（不充谱）'
L812: '基线对表：现值（--baseline-step 名含匹配·多命中取最长者·全部在册）\n    vs 基线秒 → 倍数；≥BASELINE_SQUEEZE_RATIO → 本机挤压嫌疑非卡死注记。\n    基线步未在场或未完（skipped/未跑）→ applied=false 响亮注记（rc 仍 0）。'
L827: '基线步未在场或未完（skipped/未跑）·对表未施（响亮注记非静默）'
L830: '步 %s 现 %ds vs 基线 %ds = %.1fx'
L832: '（≥%.0fx＝本机挤压嫌疑非卡死·判例 coqchk 561s vs 7480s=13.3x）'
L835: '（＜%.0fx·时长量级如常）'
L884: '=== ROCQWASH CI-TRIAGE（20261110 判类谱·六幕实战代码化）==='
L904: '  判类: family=%s（%s） action=%s'
L915: '（分诊完成·红是数据非器红·exit 0）'
L921: '装载（线上/离线）→ 逐 job 判类 → run 级批量判 C → run 判类 → 基线对表\n    → (report, jobs, per, verdict, baseline, source_desc)。用法错 → 2·不可达 → 9。'
L925: '--offline 与 --repo/--run 互斥（二选一）'
L927: '须给 --offline JOBS.json（离线）或 --repo ORG/REPO --run ID（线上）'
L930: '线上模式须 --repo ORG/REPO 与 --run ID 成对'
L932: '--repo 形须 ORG/REPO'
L934: '--logs 仅线上模式（离线零网络·日志证据走 canned 形或 --selftest regex 单元）'
L937: '--baseline-seconds 须正整数'
L939: '--retry-max 须≥0 实测 %d'
L957: 'API HTTP %d: %s（GET jobs 失败·%s）'
L971: 'logs 抓取帽 %d：仅抓前 %d 红件（余 %d 件未抓·响亮非静默）'
L990: 'offline canned 日志 %d 件（job_logs 顶层扩展位·非 API 真形·同输入重跑字节恒同）'
L994: 'dump 行滤除已关（--no-dump-filter）·青色脚本回显/组指令行原样入证据与判据（复核台账 §三-2 证据陷阱形如实再现·缺省滤除开启）'
L1017: 'CI 红炉分诊器（20261110 判类谱代码化）——步级表＋五族＋绿炉判类＋处置 action＋可选时长基线对表'
L1020: '离线模式：canned jobs JSON（同 API 真形）——selftest 与断网环境走此路'
L1023: '线上模式：仓库形 ORG/REPO（与 --run 成对）'
L1025: '线上模式：Actions run id（与 --repo 成对）'
L1027: '线上模式加抓红件日志抓关键行入证据（仅线上·离线拒）'
L1029: '关 dump 行滤除（青色脚本回显 [36;1m／##[group] 行原样入证据与判据——复核台账 §三-2 证据陷阱形如实再现·缺省滤除开启·run 级响亮注记）'
L1035: 'netrc 路径（默认 ~/.netrc·machine github.com 第 6 列=token）'
L1038: '同 sync 历史时长秒（判例 coqchk 561s）→ 出倍数对表'
L1040: '对表步名（名含匹配·默认 coqchk=判例形）'
L1042: '单请求超时秒（默认 30）'
L1044: '403/429/5xx 退避重试帽（默认 3·指数 base 2s·Retry-After 秒数头尊重·耗尽原错 9）'
L1047: '分诊 report 出账（rocqwash-ci-triage/1·sort_keys）'
L1075: '内嵌冻结向量组：五族＋绿炉六 canned 样张全命中＋基线 13.3x 判例＋基线步\n    缺席响亮注记＋分类器单元（关键行 regex 正负判·连坐/在飞/UNRECOGNIZED 分流·\n    E 勿当内容红负证）＋netrc 解析单元＋确定性字节恒同＋CLI 四码＋韧性层退避\n    （403×3→[2,4,8]·Retry-After 尊重·耗尽上抛·401 不重试·_open/_sleep 注入\n    零网络）＋〔九〕Main 形判读矢（v48 勘形小改①·coq93.yml 真形步名×五族\n    判类兼容机检钉——勘形 §3.1「即用」判据的机械实证）＋〔十〕gate2-only\n    E 变体矢（复核台账 token 二分验收线：#7 fixture banner-absent 真执行行\n    canned →E 保持＋#8/#20/#26 形矢 E＋#10 fixture 认证态 token canned →\n    UNRECOGNIZED 转正验收判（器判=复核判词）＋coqchk-success 旁证矢＋认证态\n    token 零红词面机检＋规则负判四发·出处六事件四入一转一留）＋dump 行滤除矢\n    （复核台账 §三-2 证据陷阱：dump-only banner 不确证·真执行行确证·\n    --no-dump-filter 陷阱形如实再现）＋〔十一〕五 token 在册矢（复核台账 §三\n    候选逐 token 真账形正判）＋job_logs 扩展位形坏 fail-loud 矢＋canned 日志\n    确定性字节恒同矢＋logs 两跳 415 修法矢（302→零 Authorization 第二跳\n    200·415/403/无 Location 原码入证据·canned 零网络）。\n    全程 --offline fixtures 零真网络零编译。'
L1123: 'fixture 缺失（六件套须在卷）: %s'
L1141: '连坐形应归 B'
L1142: '连坐'
L1148: '批量'
L1173: '本机挤压嫌疑非卡死'
L1179: '响亮'
L1187: 'json 字节漂移＝违例'
L1193: '未知形参应 rc=2 实测 %d'
L1195: '缺模式应 rc=2 实测 %d'
L1197: '缺 jobs 文件应 rc=9 实测 %d'
L1199: '--logs 离线拒应 rc=2 实测 %d'
L1201: 'repo 缺 run 应 rc=2 实测 %d'
L1203: 'repo 形错应 rc=2 实测 %d'
L1205: '双模式互斥应 rc=2 实测 %d'
L1227: '在飞'
L1232: '连坐'
L1258: '上传红无 E 签名（coqchk 非 skipped）→B'
L1264: '公理总数=3'
L1265: '内容红正例应命中: %s'
L1266: '公理总数=0'
L1268: '内容红负例不应命中: %s'
L1275: '网络窗正例应命中: %s'
L1278: '网络窗负例不应命中: %s'
L1280: '断链正例应命中: %s'
L1282: '断链负例不应命中: %s'
L1291: '单行 6 列形应取 github.com 行第 6 列'
L1294: '多行形应同解析'
L1299: '无 github.com 条目应 fail-loud'
L1309: '负帽应 ValueError'
L1314: 'HTTP-date 不猜'
L1317: 'canned 响应体（urlopen 假件·零网络·上下文管理器形）。'
L1358: '403×4 重试耗尽应上抛'
L1366: '401 语义面应不重试直上抛'
L1369: '401 零重试零睡'
L1405: 'Main 形 fixture 缺失（真形七件套须在卷）: %s'
L1416: 'Main 真形步名咬合失守（16 枚·序按 coq93.yml 实取）'
L1418: 'Main 绿样张应全步 success'
L1424: 'Main 形 json 字节漂移＝违例'
L1455: 'Main 形判读矢失配'
L1462: '网络邻接步'
L1466: '内容步'
L1498: 'gate2-only fixture 缺失: %s'
L1509: 'offline canned 日志 1 件'
L1512: 'gate2-only 连坐'
L1513: 'log 确证：GATE-BANNER-ABSENT'
L1515: 'dump 行滤除 2 行'
L1517: '结论位校验'
L1517: '认证态红形'
L1521: 'log[判定=CLEAN]'
L1522: 'log[R4-覆盖划分]'
L1523: 'log[APPENDIX-缺]'
L1524: 'log 确证：GATE-BANNER-ABSENT'
L1526: 'banner 仅 dump 行不得确证（复核台账 §三-2 证据陷阱）'
L1527: 'dump 行滤除 1 行'
L1538: '2026-11-06T13:22:43Z GATE-BANNER-ABSENT _chk_all.log 不在盘——coqchk 未产出日志（上游 gate4/build 夭折连带，红因看上游步）·非 COQLIB 代际失守'
L1541: '2026-11-07T17:18:52Z 判定=CLEAN(exit 0) Axioms段数=14 公理总数=0 日志完整=True\n2026-11-07T17:18:53Z GATE2-ATTEST-RED: 认证态覆盖断言不备'
L1548: 'gate2-only 连坐'
L1549: 'log 确证：GATE-BANNER-ABSENT'
L1559: 'gate2-only 连坐'
L1562: 'banner token 未确证'
L1578: '结论位校验'
L1578: '认证态红形'
L1583: 'coqchk 步 success'
L1584: 'GATE2-ATTEST-RED: 认证态覆盖断言不备'
L1585: '判定=CLEAN(exit 0) Axioms段数=14 公理总数=0 日志完整=True'
L1586: 'R4 覆盖划分破: skipped∪sent != surface 或交集非空或面空'
L1589: '认证态 token 误入红词面: %s'
L1600: 'dump 行滤除 1 行'
L1604: 'log 确证：GATE-BANNER-ABSENT'
L1605: 'dump 行滤除 1 行'
L1609: 'log 确证：GATE-BANNER-ABSENT'
L1611: '滤除关时 dump 行原样入证据（陷阱如实再现）'
L1615: 'GATE2-ATTEST-RED: 认证态覆盖断言不备'
L1616: '判定=CLEAN'
L1617: '判定=CLEAN(exit 0) Axioms段数=14 公理总数=0 日志完整=True'
L1618: '公理总数'
L1618: '公理总数=0'
L1619: 'R4-覆盖划分'
L1620: 'R4 覆盖划分破: skipped∪sent != surface 或交集非空或面空'
L1621: 'APPENDIX-缺'
L1623: 'token 不在册或重册: %s'
L1624: 'token 正例不命中: %s'
L1629: '复核台账 §三-3 另三候选不在本轮五 token 清单·不冒充在册（不充册）'
L1648: 'gate2 子串搭便上传红仍归 B（防误吞）实测 %s'
L1658: 'runner 失联零红步形仍谱外不充谱实测 %s'
L1669: '滤除已关'
L1672: 'coqchk 步 success'
L1679: 'job_logs 形坏应 fail-loud 9 实测 %d'
L1688: 'canned 日志判类 json 字节漂移＝违例'
L1723: '第二跳须零 Authorization（带 token 转发 403 Azure 实测形）'
L1725: '两跳矢量零重试零睡'
L1738: '415 语义面不重试零睡'
L1753: '第二跳失败不重试零睡'
L1761: '无 Location'
L1763: 'CI-TRIAGE-SELFTEST PASS: 五族+绿炉六样张全命中/基线 13.3x 判例+缺席响亮注记/分类器单元（regex 正负·连坐·在飞·E 勿当内容红·UNRECOGNIZED）/netrc 解析/确定性字节恒同/CLI 四码/韧性层退避（403×3→[2,4,8]·Retry-After 尊重·403 耗尽 9·401 不重试）/Main 形判读矢（coq93 真形 16 步咬合+兼容表 15 行+E 两件齐）/〔十〕复核台账 token 二分矢（#7 fixture banner-absent canned→E·#8/#20/#26 形矢 E·#10 fixture 认证态 canned→UNREC 转正验收判（器判=复核判词）·coqchk-success 旁证·负判五发 #3 不充谱）+dump 行滤除矢（dump-only banner 不确证·真执行行确证·--no-dump-filter 陷阱形如实再现）+五 token 在册矢（复核台账 §三候选全员）+job_logs 形坏 9+canned 确定性+logs 两跳 415 修法矢（302→零 Authorization 第二跳 200·415/403/无 Location 原码入证据） 全过'
```
