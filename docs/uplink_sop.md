# uplink_sop.md — uplink 回传包上行门规程 / the uplink intake gate SOP for return packages.

> **UplinkSop**: the bilingual SOP card for the uplink intake gate (`tools/uplink.py`) of this repository.
>
> Purpose.  Freeze the intake craft for return packages produced outside this repository: a
> package zip plus its md5 sidecar is compared member by member by machine, a green comparison
> appends exactly one register row to `docs/uplink-intake.jsonl`, and a PR description draft is
> rendered from that row for a human-opened pull request. Every finding is data with a
> fail-loud exit contract; nothing is silently skipped.
>
> Interface.  The three CLI faces of `tools/uplink.py` (`verify` / `intake` / `pr-prep`) as
> fixed by specification `GD-20261115-RQWPLUG-02` §1.2; the register schema `rocqwash-uplink/1`;
> the read-only pledge. Faces sit in §一, schema in §二, digest semantics in §三, write
> boundary in §四, PR preparation in §五. The only flag cited by name is `--register` (§0.1);
> other flag spellings belong to the implementation and its `--help`.
>
> Dependencies.  Grounded in the same specification §1.2 (field names and face names verbatim);
> prose-face law `docs/annotation-standard-v1.0-20261113.md`; companion surfaces
> `docs/periscope_sop.md` (SOP form template) and `docs/exp-bus-backlog.md` (bus prototype).
> Every face is offline file work: zero network by design.
>
> Evidence.  The register file `docs/uplink-intake.jsonl` carries the schema header comment and
> holds no real row by design (§二); the schema string and the six field names appear verbatim
> in the specification named above.
>
> Exit-codes.  This card is a document and exits nothing itself; it documents the 0/1/2/9
> contract of `tools/uplink.py` exactly as specified in §一 (0 = success, 1 = fail-loud red,
> 2 = usage or IO, 9 = structural refusal or missing input), described, never redesigned.

---

## 〇、适用域与前置检查 Scope and Pre-Flight Checks

### 0.1 适用域 Scope

- **上行门是什么 What the gate is**: `tools/uplink.py` 是外产回传包（zip＋md5 旁证＋逐文件
  manifest）进入本 repository 的唯一正形通道；三个 face 全部为离线文件作业，工具内零网络
  调用（NETRED 面：no network by design）。
- **输入面 Inputs**: 回传包 zip、md5 旁证文件（`md5sum` 行格式：摘要＋两空格＋相对路径）、
  登记面 `docs/uplink-intake.jsonl`（缺省路径，`--register` 可改指）、产出方标签与
  `landed-ref`。
- **输出面 Outputs**: `verify` 向 stdout 出逐文件比对清单；`intake` 向登记面追加恰一行；
  `pr-prep` 向调用方指定路径写 PR 描述草稿文件。

### 0.2 前置检查（fail-loud）Pre-Flight Checks (fail-loud)

1. 包 zip 缺席 → exit 9（禁隐式扫描：不给输入就拒绝运行）；
2. md5 旁证缺席或行格式非法 → exit 9；
3. 登记面不可读或行非法 JSON → exit 9（fail-loud，禁静默重建）；
4. 无 face 或未知 face（含裸跑）→ exit 2（usage 面）；`--help` 出三 face 名单；
5. 写面只有两处（登记面 append 与 pr-prep 草稿路径），其余 repository 树零字节（§四）；
6. 判定语义：失配、缺件、草稿不变量违者皆按其 exit 码响亮终态，属数据非可跳过项。

## 一、三 face 契约 The Three CLI Faces

| Face | Input | Output | Side effect | Exit codes |
|---|---|---|---|---|
| `verify` | package zip + md5 sidecar | per-member comparison listing on stdout | none (read-only) | `0` all members match; `1` any MISMATCH/MISSING; `2` usage or IO; `9` missing input |
| `intake` | verify-green package + producer label + landed-ref | one appended register row | append to `docs/uplink-intake.jsonl` only | `0` row appended; `1` verification red, no row; `2` usage or IO; `9` missing input or unreadable register |
| `pr-prep` | a verified register row + draft output path | PR description draft file | write to the given draft path only | `0` draft written; `1` row not verified, no draft; `2` usage or IO; `9` register or row missing |

- **verify**: 对包 zip 成员与 md5 旁证逐文件摘要比对（进程内 `hashlib` 计算，不调外部
  二进制）；stdout 逐文件行 `path | expected | actual | MATCH | MISMATCH | MISSING` 全量
  出证；零写副作用。
- **intake**: 先内置重跑 verify 比对面（red 即拒绝，无登记行落笔）；green 才向登记面
  append 恰一行（§二字段形）。登记面 append-only：行永不改写、永不删除；重复 intake 同包
  追加新行，重复行是诚实记录（去重非本 face 职责）。
- **pr-prep**: 只接受 `verified=true` 的登记行（不变量，违者 exit 1）；渲染草稿文件（§五
  内容形）；零 git 调用、零 push、绝不开 PR（开 PR 由人显式执行）。

## 二、schema rocqwash-uplink/1 The Intake Register Schema

登记面文件 `docs/uplink-intake.jsonl`：每行一个 JSON 对象；首行可为 `#` 开头的 schema 注释
行，读取面必须跳过首字符为 `#` 的行（本 repository 的 `docs/exp-ledger.jsonl` 无注释行先
行，首行注释是本 schema 的显式设计）；append-only，唯一写入口＝`intake` face。

| Field | Meaning | Form |
|---|---|---|
| `schema` | schema self-identification | constant string `rocqwash-uplink/1` |
| `package` | return-package zip path as ingested | non-empty string |
| `source-seat` | producer label carried with the package | non-empty string (spec-frozen field name) |
| `md5` | md5 sidecar digest of the package zip | 32-character lowercase hex |
| `verified` | every member digest matched at intake time | boolean, `true` only on a green intake |
| `landed-ref` | branch or PR reference the package content maps to | non-empty string |
| `exit` | the intake face exit code recorded at intake time | integer, `0` on a green intake |

登记面当前形＝空档（仅 schema 注释头＋占位示例行，零真实条目）；首条真实行由下一次真实
intake 落笔。

## 三、md5 摘要比对与 fail-loud 语义 MD5 Digest Comparison and Fail-Loud Semantics

比对两层，任一层失配即 fail-loud：

| Layer | Compared | Mismatch verdict | Exit |
|---|---|---|---|
| 包级 package-level | sidecar zip digest vs in-process recomputed digest | fail-loud, full listing printed | `1` |
| 成员级 member-level | manifest member list and per-member digests vs zip members | every member compared; a manifest-named member absent from the zip is `MISSING` | `1` |

- **fail-loud 出证面**: 失配或缺件时 stdout 全量打印逐文件清单（expected/actual 摘要并
  列）；无登记行、无草稿、无部分写入；失配不可跳过、不可降级、不重试，`1` 即终态。
- **缺件 MISSING**: manifest 声称的成员在 zip 内缺席＝`MISSING`＝exit 1，禁静默跳过。
- **构造性纪律接口**: 零 `eval`/`exec`/`compile`；零静默 fallback（每条失败路径显式 rc）；
  stdlib only（`argparse` / `hashlib` / `json` / `os` / `pathlib` / `re` / `sys` / `typing`
  allowlist）；确定性：摘要只取自文件内容，登记 schema 无时间字段，运行时时钟不进逻辑。

## 四、只读誓言与登记面边界 The Read-Only Pledge and the Register Boundary

- **写面恰好两处**: `docs/uplink-intake.jsonl`（intake append）与 pr-prep 草稿路径（调用方
  指定）。两处之外 repository 树零字节：intake 前后 repository 树 checksum 不变（shape
  测试断言面）。
- **零网络 by design（NETRED 面）**: 全部输入为本地文件；工具体内无 fetch/socket/urllib
  调用面。
- **只读誓言例外登记制**: 两处写面之外任何写动作＝违规；exit 契约之外的静默吞错＝违规
  （每条失败路径显式 rc 退出）。

## 五、PR 准备交接面 The PR-Prep Handoff

- **草稿内容形**: 建议标题行＝本 repository 的 supply 前缀 `supply(symbiosis-uplink):`＋
  `landed-ref`；正文逐字引用登记行字段（`package` / `source-seat` / `md5` / `verified` /
  `landed-ref`）＋verify 比对清单摘要＋包内件指针。
- **禁自动开 PR**: `pr-prep` 零 git 调用、零 push；草稿文件是交接物，开 PR 由人或后续
  工作流显式执行。
- **交接清单三查**: 草稿引用行 `verified=true`；该行 intake 当时 exit `0`；草稿路径在调用
  方指定位置且只此一处写入。
