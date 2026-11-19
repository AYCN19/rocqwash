# step-pushci.md — 工作流嵌段②：单步推 CI（--dry-run 先行→真发→verdict 分流）

> rocqwash v37 嵌段正典样例三件之二。把 `README-cw.md:124-126`「pushci 嵌段」
> 展开为可整段复制执行的命令块＋真实输出样例＋verdict 分支表＋dynamic-workflow
> 嵌段伪码。器实况正本：`tools/pushci.py` docstring（v36 flagship·五段管线
> preflight→push→watch→heal→verdict±merge·pushci.py:5）与 `--help`。
> schema `rocqwash-pushci/1`·verdict 七态
> `success|fix-content|toolchain|unstable|heal-exhausted|gate4-block|dry-run`
> （README-cw.md:33 同册）。
>
> **纪律红线**：
> - **--dry-run 先行是嵌段正典序**——`--dry-run=只打计划零副作用 exit 0
>   （零 git 零 API 零工具子进程）`（tools/pushci.py:87）：真发前人审计划，
>   计划不对不开闸。
> - **verdict 是封册**——七态与退出码 0/1/2/9 一一封册（tools/pushci.py:91-93）；
>   分流动作见 §3 表。a failing result is data, not a tool failure：fix-content 是**内容红**数据，器面照常出账。
> - **离线演练须成对**——`--injector DIR` 与 `--git-caller FILE` 必须成对给出，
>   单边给出＝用法错 exit 2（injector 无 canned git＝真 push 危险，tools/pushci.py
>   docstring「--git-caller」条）。
> - pushci 的 preflight 发射闸只复跑 doctor＋net-probe 两闸（可选
>   `--pre-scan-gate4`）；套件绿/behind=0 等**推窗四判据不在此册**，双门并立见
>   `docs/workflow-integration-whitepaper-v1.0-20261111.md` §4（README-cw.md:57-60 同口径）。

## 1. 第一步：--dry-run 先行（零副作用·真发前人审）

```bash
# ── step-pushci 嵌段·第 1 步：干跑出计划（在 rocqwash 仓根执行）──────
BRANCH=feature/x                 # 要推送与观测的分支（按需改）
REPO_PATH=.                      # 目标仓库目录（零硬编码·全参数化）

bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --json pushci-dry.json --dry-run
echo "DRYRUN_RC=$?"              # 正典判据：0=计划已出·计划文本看 stdout
```

**实测样例**（2026-11-11 铸席真跑 `python3 tools/pushci.py --repo-path . --branch
main --dry-run --json …`，rc=0；stdout 计划原文）：

```text
=== ROCQWASH PUSHCI (post-fix push-CI one-shot pipeline) ===
mode=dry-run steps=preflight,push,watch,heal,verdict
PLAN [1] preflight.toolchain: python3 tools/toolchain_dyld_doctor.py (--worker probed by default, gate verdict=healthy)
PLAN [1] preflight.net: python3 tools/net_probe.py --rounds 2 --interval 60 --stable-window (gate STABLE)
PLAN [1] preflight.gate4: not enabled (--pre-scan-gate4 not given)
PLAN [2] push: git -C <repo> -c http.version=HTTP/1.1 push origin main (3 attempts x 45s wait; after three failures with remote host=github.com, ghproxy reroute 2 attempts)
PLAN [3] watch: GET /repos/<org/repo>/actions/runs?per_page=30 (head_branch=main and head_sha=<pushed_sha>, every 150s, status-only (a frozen updated_at is not a stall criterion; status is authoritative) until completed)
PLAN [4] heal: python3 tools/ci_triage.py --repo <org/repo> --run <id> (cap 3); B/E -> probe then rerun (403 accepted idempotently); A -> stop fix-content; C -> stop toolchain; out-of-table -> manual
PLAN [5] verdict: report schema rocqwash-pushci/1, exit codes 0/1/2/9
=== FINAL VERDICT: dry-run (exit 0) ===
```

对应 `--json` report（实测·rocqwash-pushci/1·计划入 `plan` 数组·零 stages 副作用）：

```json
{
 "args": { "base_ref": "main", "branch": "main", "max_heal": 3,
           "merge": false, "merge_method": "merge", "pr": null,
           "pre_scan_gate4": false, "probe_interval": 60.0,
           "remote": "origin", "watch_interval": 150.0 },
 "evidence": [],
 "final": { "conclusion": null, "verdict": "dry-run" },
 "mode": "dry-run",
 "plan": [ "[1] preflight.toolchain: …", "[2] push: …", "…（与 stdout 计划逐行同文）" ],
 "schema": "rocqwash-pushci/1",
 "stages": {},
 "steps": [ "preflight", "push", "watch", "heal", "verdict" ],
 "verdict": "dry-run"
}
```

## 2. 第二步：真发（dry-run 计划人审过才走这步）

```bash
# ── step-pushci 嵌段·第 2 步：真发（五段全跑）────────────────────────
# 可选追加：--pre-scan-gate4（preflight 加做 gate4 头注守卫预扫·FAIL=0 才放行）
#           --merge / --merge-method squash（绿后并 PR·无 open PR→9 目标缺失）
#           --watch-max-rounds N（watch 轮帽安全阀·超帽 fail-loud 9·长 watch 工作流建议给）
bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --json pushci-report.json
echo "PUSHCI_RC=$?"              # 七态封册按 §3 分流
```

诚实注记：**真发段本席未实跑**（需真远端凭据与真 push 权限，属用户面；本席只
实测了 `--dry-run` rc 0 与 `--selftest` 挂接面）。上块的旗标全部对账自
`tools/pushci.py --help`（2026-11-11 实取）。

## 3. verdict 分支表（七态×退出码×工作流动作）

verdict 与退出码封册正本：tools/pushci.py:91-93（README-cw.md:33、69 同册）。

| 退出码 | verdict | 含义 | 工作流动作 |
|---|---|---|---|
| 0 | `success` | 五段全绿（watch 到 completed 成功·heal 未耗帽） | 收尾；若带 `--merge` 此时 PR 已并 |
| 0 | `dry-run` | 只打了计划（§1 正典形） | 读 plan 人审·不视为真发 |
| 1 | `unstable` | net-probe 稳窗不过（push 或 heal 阶段双探不稳）→禁发射 | 网络修复后重跑；读 report.stages |
| 1 | `toolchain` | doctor verdict≠healthy（环境件） | 按器附带的 doctor 重跑建议处置环境 |
| 1 | `heal-exhausted` | 观测红·B/E 族重跑 `--max-heal`（默认 3）轮未绿 | 读 `stages.heal.last_triage`（family/action/evidence 全量在册）人工定夺 |
| 2 | `fix-content` | classification A 内容红（heal 分派停·**禁代修**——修复是席/人职责）或 merge 409 冲突（内容活） | 交修复席/人；family 原值响亮在册 |
| 2 | `gate4-block` | `--pre-scan-gate4` 预扫 FAIL≠0 | 读 report.stages.preflight.gate4.fail_files 逐件修头注 |
| 2 | （无 verdict） | argparse 用法错（段依赖 watch⇒push·heal⇒watch·--merge⇒watch 等） | 修命令行；对照 `bash cw.sh help pushci` |
| 9 | （无 verdict） | 目标缺失 fail-loud（repo/remote/分支/PR/工具链件缺失·netrc 缺·API 不可达·API 4xx/5xx 硬错·watch 轮帽达） | 人工补目标/凭据后重跑 |

README-cw.md:54 注记的同款快查：`pushci 透传 verdict 封册（success/dry-run=0·
heal-exhausted/unstable/toolchain=1·fix-content/gate4-block=2·9=目标缺失）`。

## 4. 离线演练形（工作流自测用·零真网络零真 push）

```bash
# injector（canned API+tools）与 git-caller（canned git 响应）必须成对——
# 单边给出即用法错 exit 2（防「injector 无 canned git」静默走真 push）
bash cw.sh pushci --repo-path "$REPO_PATH" --branch "$BRANCH" \
  --injector /path/to/injdir --git-caller /path/to/git-canned.json \
  --sleep-scale 0 --json pushci-inj.json
```

场景形与六场景 15 案正本见 `tests/test_pushci.py` 与 pushci docstring「离线可测」
节（steps 形／flat 形双通吃·API 调用流水落 `<injector>/api_calls.json` 供实证）。

## 5. dynamic-workflow 嵌段伪码

```text
// 嵌段②单步推 CI：dry-run 门→真发→verdict 分流（器：cw.sh pushci）
phase "pushci-step" {
  // 1) 干跑门：计划人审前的机械预检（退出码即确认·§10）
  const dry = await world.run("bash", ["cw.sh", "pushci",
      "--repo-path", ".", "--branch", "feature/x",
      "--json", "pushci-dry.json", "--dry-run"]);
  if (dry.exitCode !== 0) return { verdict: "plan-unusable", rc: dry.exitCode };

  // 2) 计划人审：子代理读 pushci-dry.json 的 plan 数组，只判「开不开闸」
  const review = await agent({ role: "gate-reviewer",
    ask: "读 pushci-dry.json plan 数组，答 开闸|不开闸 与理由（不修改任何文件）" });
  if (review.answer !== "开闸") return { verdict: "held", why: review.reason };

  // 3) 真发：世界已裁决的检查不叫子代理复述——退出码就是 verdict 封册索引
  const real = await world.run("bash", ["cw.sh", "pushci",
      "--repo-path", ".", "--branch", "feature/x",
      "--pre-scan-gate4", "--watch-max-rounds", "20",
      "--json", "pushci-report.json"]);
  switch (real.exitCode) {
    case 0: return { verdict: "success-or-dryrun" };            // 读 report.verdict 细分
    case 1: return { verdict: "env-red",                        // unstable/toolchain/heal-exhausted
                     next: "读 report.stages 人工定夺" };
    case 2: return { verdict: "content-red",                    // fix-content/gate4-block/用法错
                     next: "交修复席；gate4-block 读 fail_files 逐件修" };
    case 9: return { verdict: "target-missing",                 // fail-loud
                     next: "补目标/凭据后重跑" };
  }
}
```

## 6. 诚实注记

- §1 两份样例为 2026-11-11 铸席实跑 `--dry-run` 所产（rc=0·tmp 出账路径）；
  §2 真发块未实跑（凭据属用户面），其旗标对账自 `tools/pushci.py --help` 实取输出。
- verdict 分支表逐格锚 pushci docstring 退出码节（tools/pushci.py:91-93）与五段
  管线节（pushci.py:5-46）；未锚处（如「用法错归 2」）锚 argparse 段依赖条文
  （docstring「段依赖（用法错 2）」）。
- 推窗四判据（certify/push_gate.py window：c1 ci-idle／c2 local≥remote／
  c3 fetch-clean／c4 cert-green）与 pushci 发射闸是**两扇门**，互不替代——
  并立说明见白皮书 §4。

（English brief) Workflow block ②: single-step push-CI via `cw.sh pushci`.
Canonical order: `--dry-run` first (zero side effects, exit 0, plan printed +
report), human review of the plan, then the real run; branch on the seven-state
verdict封册 (success/dry-run=0, heal-exhausted/unstable/toolchain=1,
fix-content/gate4-block=2, target-missing=9). Offline drills require
`--injector` + `--git-caller` as a pair (single-sided = usage error exit 2).
pushci's preflight gate (doctor + net-probe ± gate4 pre-scan) is deliberately
NOT the push-window four-criteria gate — see the whitepaper §4.
