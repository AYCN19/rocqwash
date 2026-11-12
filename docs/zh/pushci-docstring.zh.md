# pushci.py 模块 docstring 中文原档（留档）

- 源文件：`tools/pushci.py` 模块 docstring（英文化前的中文原文，程序化逐字提取，未删改一字）
- 留档日期：2026-11-13
- 纪律：双语过渡期——原中文 docstring 全文移此留档而非删除；英文正本见
  `tools/pushci.py` 模块 docstring。本文件为历史存档，内容不再随代码演进维护。
- 代码接口不受影响：标识符、CLI 旗标、JSON schema 字段、退出码语义零改动。

---

pushci.py — 修复后推送 CI 一键流水线编排器（rocqwash tools/·v36 旗舰·20261111 入账）

五段管线（承 v35 四器判例·编排而非重造——doctor/net_probe/ci_triage/gate4 守卫
一律 subprocess 调用·本器只做胶水与状态机；每段可 --steps 独选·缺省全跑）：
  1 preflight（发射闸·禁发射律代码化）：
      ① toolchain：subprocess tools/toolchain_dyld_doctor.py --json <tmp>
        （--worker 缺省探测）→ verdict≠healthy 即停 verdict=toolchain；
      ② net：subprocess tools/net_probe.py --rounds 2 --interval <probe-interval>
        --stable-window --json <tmp> → UNSTABLE 即停 verdict=unstable
        （双探稳窗·单探禁发射的发射闸由四器自带·本器只认其裁决）；
      ③ 可选 --pre-scan-gate4：git -C <repo> diff --name-only <base>...<branch>
        取 .v 变更件 → verify/gate4_comment_guard.py 逐件（--file）→ FAIL=0 才放行
        （FAIL 清单入 report·verdict=gate4-block；REVIEW 件响亮入账不拦——
        守卫 rc 口径 0=PASS/1=FAIL/2=复核·形外退出 fail-loud）。
  2 push：git -C <repo> -c http.version=HTTP/1.1 push <remote> <branch>
      （重试 3 发×45s 间隔；三败且 remote URL 为 https://github.com/ 形→取前缀
      https://ghproxy.net/ 换路再试 2 发·非该形响亮注记跳过）；全败→verdict=
      unstable exit 1。pushed_sha＝push 成功后 ls-remote <remote>
      refs/heads/<branch> 取**远端 tip**（承 watch.py「真 rc＋ls-remote 复核」
      纪律·第 4 git 调·CI 构的是远端 tip·远端为准；与本地 rev-parse tip 异则
      响亮注记；rev-parse 先行只作分支在位性 fail-loud 9 预检·git 调序＝
      get-url→rev-parse→push→ls-remote 恒 4 调〔非 dry-run〕）。
  3 resolve+watch：轮询 GET /repos/{repo}/actions/runs?per_page=30（repo 由
      remote URL 推导·host 须 github.com）取 head_branch=<branch> 且
      head_sha==pushed_sha 最新 run（按 (run_number,id) 取 max·API 序无关）；
      每 --watch-interval 秒（默认 150）一询至 completed。**updated_at 冻结≠
      僵尸判例**——以 status 为准（status-only 口径·连续 N 轮 in_progress 属
      长步正常不误判·本器代码路径零 updated_at 判读）。
  4 heal（观测红时）：subprocess tools/ci_triage.py --repo --run（线上取 jobs
      分类）→ family 分派：B/E（NETRED/coqchk-skipped）→ net_probe
      --stable-window 过→POST /runs/{id}/rerun（403 already running 幂等接受）
      →回 watch（计 heal_round·帽 --max-heal 默认 3·超帽 verdict=heal-exhausted
      exit 1；probe UNSTABLE→禁发射 verdict=unstable exit 1）；
      A（内容红）→verdict=fix-content 停 exit 2（禁代修——修复是席/人职责）；
      C→verdict=toolchain 停 exit 1（附 doctor 重跑建议）；
      分派表外族（D-queue-wall/UNRECOGNIZED 等）→禁自动 rerun→人工指认
      （verdict=fix-content exit 2·family 原值响亮在册）。
      heal.rounds 语义＝**fired 重跑账**（probe+rerun 实动的轮才入册·A/C/表外
      裁停零轮入册＝零 rerun 实证）；历次判类 outcomes 全量在
      stages.heal.last_triage（family/action/evidence）。
  5 verdict＋可选 --merge：--merge 时先 GET /repos/{repo}/pulls?head=<owner>:
      <branch>&state=open 解 PR 号（或 --pr 显传·无 open PR→9 目标缺失）→
      PUT /pulls/{n}/merge（--merge-method merge|squash·缺省 merge〔分支含
      merge commit 判例〕；409→GET branches/main 重拉 tip 歇 60s 重试 ≤3·
      仍 409→verdict=fix-content exit 2〔merge 冲突＝内容活〕；其余 HTTP→
      fail-loud 9）。

离线可测（硬要求）：核心循环全注入——
  --injector DIR    注入场景·**双形通吃**：
      〔steps 形〕DIR/scenario.json＝{"steps":[{at_round,responses:[{method,path,
        status,body}...]}...], "tools":{doctor,probe canned}, "jobs"|"jobs_list"}
        ——responses 按轮按序严格消费（method+path 子串·失配 fail-loud）；
        tools canned 接 {"verdict":str,"rc":int} 或 {"report":{...}}（verdict 取
        report.verdict）；jobs 单 dict 复用或 jobs_list 逐判类调用消费。
      〔flat 形·承 tests/fixtures/pushci_scenarios 并行席契约〕DIR/scenario.json
        为夹具原件（含 "canned" 键即认）或 DIR 下 runs/NNNN.json+jobs/NNNN.json
        +rerun/NNNN.json+probe/NNNN.json+merge.json 平铺：canned.runs 逐 poll 消
        耗（体键 runs|workflow_runs 双认）·canned.probe 逐 heal 探针消耗（含
        net_probe 报告真形取 verdict）·canned.rerun[{"run_id","status"}] 逐 rerun
        消耗（run_id 与路径咬合校验）·canned.merge{"status","body"} 供 PUT·
        canned.jobs 逐判类调用消耗·canned.logs 不消费（测试席证据面）。flat 形
        未携闸 canned（doctor/probe）→preflight 双闸按缺省绿施·响亮注记在册
        （测试契约形·真发射闸以 steps 形或真模式为准）；merge 无 pulls canned→
        须 --pr 显传。
      API 调用流水落 <DIR>/api_calls.json 供实证。
  --git-caller FILE canned git 响应场景（responses[].args_contains 按序严格
                    匹配·同上 fail-loud）；调用流水落 <FILE 去展>.calls.json。
                    须与 --injector 成对（injector 无 canned git＝真 push 危险·
                    单边给出即用法错 exit 2）。
  --sleep-scale F   全部 sleep 乘 F（selftest 用 0＝零真睡）。
  _api(method,path,body) 单函数化（ApiClient.__call__）便于注入替换。
  --selftest        八矢量＋单元向量＋韧性层退避/超时杀矢量＋CLI 四码＋确定性
                    （零真网络零真 push 零编译；--netrc 故意指向不存在路径——
                    凭据惰性读证）。

用法（路径全参数化·零硬编码绝对路径·env 兜底只认 ROCQWASH_MASK〔遮蔽串·
承 watch.py 惯例〕）：
  python3 tools/pushci.py --repo-path DIR --branch B [--base-ref main]
      [--remote origin] [--pre-scan-gate4] [--pr N] [--merge]
      [--merge-method merge|squash] [--max-heal 3] [--watch-interval 150]
      [--probe-interval 60] [--watch-max-rounds 0] [--timeout 120]
      [--retry-max 3]
      [--steps preflight,push,watch,heal,verdict]
      [--injector DIR] [--git-caller FILE] [--sleep-scale 1.0] [--netrc PATH]
      [--json out] [--dry-run]
  python3 tools/pushci.py --selftest
  --dry-run=只打计划零副作用 exit 0（零 git 零 API 零工具子进程）。
  --watch-max-rounds（增补安全阀·默认 0=不限）＝轮询轮帽·超帽 fail-loud 9。
  --timeout S（韧性层 v37·缺省 120）＝全部真子进程防挂帽（git 四调＋四器工具
  _run_py）：超时=子进程杀＋fail-loud 9 报调用名（零悬挂）；canned 注入路径
  零真子进程不受此帽。
  --retry-max N（韧性层 v37·缺省 3）＝真 urllib _api 403/429/5xx 指数退避重试
  帽（base 2s·Retry-After 秒数头优先替当次延迟·HTTP-date 不猜落回指数；耗尽
  原码上交语义裁决·4xx 语义面 401/404/409 等不重试；延迟计算抽公共件
  tools/_http_backoff.py 纯函数·三器共享·同目录 sys.path 注入 import·
  无 __init__ 包结构；injector canned 路径零真网络一律不重试——离线可测铁律）。
  段依赖（用法错 2）：watch⇒push·heal⇒watch·--merge⇒watch。

退出码：0=success/dry-run；1=heal-exhausted/unstable/toolchain〔toolchain 停＝
  环境件·任务书退出码表未钦·比照 unstable 归 1 响亮入档〕；2=fix-content/
  gate4-block/用法错；9=目标缺失（repo/remote/分支/PR/工具链件缺失·netrc 缺·
  API 不可达·API 4xx/5xx 硬错·watch 轮帽达·真子进程超时被杀〔--timeout〕）。
  --selftest：0=全过／2=断言失败。

report schema（--json）= rocqwash-pushci/1：
  {schema, mode: online|injector|dry-run, steps, args,
   stages{preflight{toolchain{verdict,rc}, net{verdict,rc},
                    gate4?{files,pass_files,fail_files,review_files,
                           skipped_missing,fail_count}},
          push{sha,remote,url_masked,attempts[{target,rc}],ghproxy_used},
          watch{run_tag,run_id,rounds,conclusion,policy},
          heal{rounds[{round,family,action,probe,fired,http,evidence}],
               fired_total},
          merge?{pr,method,merged,attempts,main_tip?,merge_sha?}},
   plan?（仅 dry-run）, evidence, final{conclusion,verdict}, verdict}
  verdict ∈ success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|
  dry-run。

诚实律（承 CONTRIBUTING §0）：只认机械证据；分派表外不充谱不代 heal；A 族禁
代修；token 永不回显（netrc 解析承 ci_triage 同款口径：machine github.com 行
第 6 列·单行 6 列形与多行形通吃）；远端 URL 内嵌凭据与 ROCQWASH_MASK 串遮蔽
后出账；--json 落盘 sorted+sort_keys·同输入重跑字节级恒同（报告零墙钟字段）；
stdout 全数据驱动；零第三方依赖（纯 stdlib）；fail-loud 禁静默降级。
